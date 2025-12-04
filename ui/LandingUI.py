import os
import sqlite3
import sys
import webbrowser
from pathlib import Path

import qtawesome
from PyQt6 import QtCore, QtWidgets, QtSql
from PyQt6.QtCore import QEventLoop, Qt, QPoint, QSize, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QAction, QDesktopServices
from PyQt6.QtSql import QSqlDatabase
# from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import QFileDialog, QPushButton, QMessageBox, QWidget, \
    QListWidget, QListWidgetItem, QMainWindow, QApplication, QHBoxLayout, QLabel
from PyQt6.uic import loadUi

import logger_setup
from Functions import Savepoint_manager
from Functions.BackupDatabase import RestoreThread
from Functions.Create_database import create_tables
from Functions.Database_manager import update_database, turn_on_foreign_keys
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Text_manipulations import shrink_home, expand_home
from Functions.Widget_classes import show_loading_dialog, close_loading_dialog
from ui.MergeDatabaseUI import MergeDatabaseDialog
# from Functions.Create_database import create_tables
from ui.Settings import update_stylesheet


class LandingPage(QWidget):
    def __init__(self, start_filepath=None):
        super().__init__()
        logger_setup.get_logger().info("Starting Landing Page...")
        self.loading_manager = LoadingDialogManager.get_instance()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file =os.path.join(base_path,  "LandingPage.ui")
        loadUi(sources_ui_file, self)
        self.setWindowTitle('GeoCORK')
        update_stylesheet()

        self.db = None

        self.loadWindowState()

        self.newdatabase_button = QPushButton('New Database')
        self.newdatabase_button.setObjectName("newdatabase_button")
        self.opendatabase_button = QPushButton('Open Database')
        self.opendatabase_button.setObjectName("opendatabase_button")
        self.mergedatabase_button = QPushButton('Merge Database')
        self.mergedatabase_button.setObjectName("mergedatabase_button")

        self.verticalLayout.insertWidget(1, self.mergedatabase_button)
        self.verticalLayout.insertWidget(1, self.opendatabase_button)
        self.verticalLayout.insertWidget(1, self.newdatabase_button)

        self.newdatabase_button.clicked.connect(self.new_database_dialog)
        self.opendatabase_button.clicked.connect(self.showFileDialog)
        self.mergedatabase_button.clicked.connect(self.show_merge_db)

        self.github_button: QPushButton
        self.github_button.setIcon(qtawesome.icon('fa6b.github', color='black', scale_factor=1.0))
        self.github_button.setIconSize(QSize(35,35))
        self.github_button.clicked.connect(self.open_github)
        self.selected_files = None

        self.citation = LinkLabel(text = 'Metcalf, K., & Burges, J. (2025). kathrynmetcalf/GeoCORK: GeoCORK v1.0.3 (v1.0.3). Zenodo. https://doi.org/10.5281/zenodo.15833658',
                                  url = 'https://doi.org/10.5281/zenodo.15833658')
        self.citation.setObjectName("citation")
        self.horizontalLayout_4.insertWidget(0, self.citation)

        self.listWidget = UnselectableListWidget()
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setMinimumSize(QtCore.QSize(400, 500))
        self.listWidget.setMaximumSize(QtCore.QSize(400, 1000))
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.recents_context_menu)
        self.horizontalLayout_2.insertWidget(0, self.listWidget)
        self.listWidget.itemDoubleClicked.connect(self.clicked_file)

        self.list_recents = settings.value("ui/LandingPage/recentlist", defaultValue=[], type=list)

        for path in self.list_recents:
            self.listWidget.addItem(shrink_home(path))

        pixmap = QPixmap(os.path.join(base_path, 'GeoCORK_Logo.png'))
        scaled_pixmap = pixmap.scaled(500, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)



        self.show()

        if start_filepath:
            self.selected_files = start_filepath
            # Move the selected database to the top of the list

            if self.selected_files not in self.list_recents:
                self.list_recents.insert(0, self.selected_files) # Add the new database to the top of the list
            else:
                self.list_recents.remove(self.selected_files)
                self.list_recents.insert(0, self.selected_files)
            settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            settings.setValue('db_file', self.selected_files)
            self.db = None
            self.open_geo_cork()

        QTimer.singleShot(1, self.clear_selection)

    def closeEvent(self, a0):
        self.saveWindowState()
        logger_setup.get_logger().info("Closing Landing Page...")
        super().closeEvent(a0)

    def open_about_db(self):
        # This is a new database, so prompt the user to fill in the About Database form
        if not self.test_database_lock():
            if not update_database():
                logger_setup.get_logger().critical('Error updating and displaying database')
                return
            from ui.Settings import SettingsDialog
            settings_dialog = SettingsDialog()
            settings_dialog.settings_tabWidget.setCurrentIndex(2)
            # Set the current tab to the About Database tab
            settings_dialog.exec()

    def open_geo_cork(self, skip_update=False):
        if not self.test_database_lock():
            if '/' in self.selected_files:
                self.loading_manager.show_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
            elif '\\' in self.selected_files:
                self.loading_manager.show_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('\\')[-1]}... \n(GeoCORK may be slower for large databases)")
            QtWidgets.QApplication.processEvents()
            from ui.GeoCORKMain import GeoCORK
            for widget in QApplication.allWidgets():
                if widget.objectName() == 'GeoCORKMain':
                    Savepoint_manager.SavepointManager.reset()
                    widget.close()
                    break

            Savepoint_manager.SavepointManager.reset()
            Savepoint_manager.SavepointManager().get_instance()
            if self.db is None:
                for connectionName in QSqlDatabase.connectionNames():
                    QSqlDatabase().removeDatabase(connectionName)
                self.db = QSqlDatabase.addDatabase("QSQLITE")
                self.db.setDatabaseName(self.get_filename())
                self.db.open()
                if not self.db.isOpen():
                    logger_setup.get_logger().critical(f"Error opening database: {self.db.lastError().text()}")
                    self.loading_manager.close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
                    self.show()
                    return
                if not turn_on_foreign_keys():
                    self.loading_manager.close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
                    self.show()
                    return
                Savepoint_manager.SavepointManager()
            if not skip_update:
                if not update_database():
                    logger_setup.get_logger().critical('Error updating and displaying database')
                    self.loading_manager.close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
                    self.show()
                    return
            self.hide()
            geo_cork = GeoCORK(self)
            geo_cork.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            loop = QEventLoop()

            geo_cork.destroyed.connect(loop.quit)
            loop.exec()

            self.show()

        self.listWidget: QListWidget

        # Clear all items in the QListWidget
        while self.listWidget.count() > 0:
            self.listWidget.takeItem(0)

        # Repopulate the QListWidget with new items
        for path in self.list_recents:
            self.listWidget.addItem(shrink_home(path))
        self.listWidget.setCurrentItem(None)

    def restore_backup(self, db_file, backup_file):
        self.selected_files = db_file
        self.db = None
        QtWidgets.QApplication.processEvents()
        from ui.GeoCORKMain import GeoCORK
        for widget in QApplication.allWidgets():
            if widget.objectName() == 'GeoCORKMain':
                Savepoint_manager.SavepointManager.reset()
                widget.close()

        # Create and start the backup thread
        # self.thread = RestoreThread(db_file, backup_file)
        # self.thread.start()
        # self.thread.restore_finished.connect(lambda: self.open_geo_cork(skip_update=False))

        src = sqlite3.connect(db_file, timeout=10)
        backup = sqlite3.connect(backup_file, timeout=10)

        logger_setup.get_logger().info('Beginning Restore')
        self.last_percent = 0
        def progress(status, remaining, total):
            # Calculate progress percentage
            percent = 100 - int((remaining / total) * 100)
            if percent != self.last_percent:
                logger_setup.get_logger().info(f'Backup Progress: {percent}')
                self.last_percent = percent
        backup.backup(src, pages=5, progress=progress)
        src.commit()
        backup.commit()
        backup.close()
        src.close()

        self.open_geo_cork()


    def cancel_open(self):
        if '/' in self.selected_files:
            self.loading_manager.close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
        elif '\\' in self.selected_files:
            self.loading_manager.close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('\\')[-1]}... \n(GeoCORK may be slower for large databases)")
        self.db.close()
        self.db = None

    def test_database_lock(self):
        logger_setup.get_logger().info("Testing Database Lock...")
        database_path = self.get_filename()
        try:
            # Attempt to connect and perform a simple query
            connection = sqlite3.connect(database_path, timeout=1)  # Set timeout to 1 second
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")  # Simple query to test access
            # Try write access by creating a temporary table, will be deleted when the connection is closed
            cursor.execute("CREATE TABLE temp (tempID INTEGER PRIMARY KEY)")
            cursor.execute("DROP TABLE IF EXISTS temp")  # Clean up the temporary table
            connection.close()
        except Exception as e:
            # Handle the specific database lock error
            logger_setup.get_logger().debug(
                f"Error testing for database lock: {e}")
            if "database is locked" in str(e):
                logger_setup.get_logger().debug(
                    f"Database lock error: {e}")
                self.show_message("Database Locked", "The database is currently locked. Make sure it is not in use elsewhere.")
                return True
            else:
                self.show_message("Error", f"An error occurred: {e}")
        return False


    def show_message(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

    def clicked_file(self):
        if self.listWidget.currentItem() is None:
            return
        display_path = self.listWidget.currentItem().text()
        full_path = expand_home(display_path)
        self.selected_files = full_path

        # Check if the file exists
        if not os.path.exists(full_path):
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("File Not Found")
            msg_box.setText(f"The file '{full_path}' does not exist. Would you like to create a new empty database?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response != QMessageBox.StandardButton.Yes:
                return
            else:
                # Move the selected database to the top of the list
                self.list_recents.remove(full_path)
                self.list_recents.insert(0, full_path)
                settings.setValue("ui/LandingPage/recentlist", self.list_recents)
                # Create a new empty database
                self.db = QSqlDatabase.addDatabase("QSQLITE")
                self.db.setDatabaseName(full_path)
                if not self.db.open():
                    logger_setup.get_logger().critical(f"Error opening database: {self.db.lastError().text()}")
                    return
                if not turn_on_foreign_keys():
                    return
                Savepoint_manager.SavepointManager()
                settings.setValue('db_file', full_path)
                self.open_about_db()
                self.open_geo_cork(skip_update=True)
        else:
            # Move the selected database to the top of the list
            self.list_recents.remove(full_path)
            self.list_recents.insert(0, full_path)
            settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            settings.setValue('db_file', full_path)
            self.db = None
            self.open_geo_cork()


    def new_database_dialog(self):
        file_name, _ = QFileDialog.getSaveFileName(
            None,
            "Save Database File",
            "",
            "Database Files (*.db)"
        )
        if not file_name:
            return

        # Ensure the filename ends with .db
        if not file_name.lower().endswith(".db"):
            if '.' in file_name:
                # If there's already an extension, replace it with .db
                file_name = file_name.split('.')[0] + ".db"

        if file_name:
            self.selected_files = file_name
            self.db = QSqlDatabase.addDatabase("QSQLITE")
            self.db.setDatabaseName(self.get_filename())
            self.db.open()
            if not self.db.isOpen():
                logger_setup.get_logger().critical(f"Error opening database: {self.db.lastError().text()}")
                return
            if not turn_on_foreign_keys():
                return
            Savepoint_manager.SavepointManager()
            self.selected_files = file_name
            if self.selected_files not in self.list_recents:
                self.list_recents.insert(0, self.selected_files) # Add the new database to the top of the list
                settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            settings.setValue('db_file', file_name)
            self.open_about_db()
            self.open_geo_cork(skip_update=True)

    def open_github(self):
        webbrowser.open('https://github.com/kathrynmetcalf/GeoCORK')


    def showFileDialog(self):
        if self.listWidget.currentItem() is not None:
            self.clicked_file()
            return

        self.db = None

        file_dialog = QFileDialog(self, 'Open Database File', str(Path.home()), 'Database Files(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.selected_files = file_dialog.selectedFiles()[0]
            if self.selected_files not in self.list_recents:
                self.list_recents.insert(0, self.selected_files)
                settings.setValue("ui/LandingPage/recentlist", self.list_recents)
                self.listWidget.clear()
                for path in self.list_recents:
                    self.listWidget.addItem(shrink_home(path))
                self.listWidget.setCurrentItem(None)
            self.hide()
            settings.setValue('db_file', self.selected_files)
            self.open_geo_cork()

    def show_merge_db(self):
        merge_dialog = MergeDatabaseDialog()
        if merge_dialog.exec():
            return

    def recents_context_menu(self, pos):
        """

        :param pos:
        :return:
        """
        item = self.listWidget.itemAt(pos)
        if item:
            context_menu = QtWidgets.QMenu()
            delete_action = QAction("Remove from list", self.listWidget)
            delete_action.triggered.connect(lambda: self.remove_db_from_recent(item))
            context_menu.addAction(delete_action)

            delete_all_action = QAction("Remove all from list", self.listWidget)
            delete_all_action.triggered.connect(lambda: self.remove_all_db_from_recent())
            context_menu.addAction(delete_all_action)

            context_menu.exec(self.listWidget.mapToGlobal(pos))

    def remove_db_from_recent(self, item):
        """
        Remove the given database path from the recent list,
        then update QSettings and refresh the UI.
        """
        item: QListWidgetItem
        msg = QMessageBox.question(
            self,
            "Remove Database",
            f"Are you sure you want to remove '{item.text()}' from recent databases?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if msg == QMessageBox.StandardButton.Yes:
            full_path = expand_home(item.text())
            self.list_recents.remove(full_path)
            settings.setValue('ui/LandingPage/recentlist', self.list_recents)

            row = self.listWidget.row(item)
            self.listWidget.takeItem(row)

    def remove_all_db_from_recent(self):
        """
        Removes all databases from the recent list.
        """
        item: QListWidgetItem
        msg = QMessageBox.question(
            self,
            "Remove All Databases",
            f"Are you sure you want to remove all databases from recent databases?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if msg == QMessageBox.StandardButton.Yes:
            self.list_recents = []
            settings.setValue('ui/LandingPage/recentlist', self.list_recents)
            self.listWidget.clear()


    def get_filename(self):
        return self.selected_files

    def saveWindowState(self):
        settings.setValue("ui/LandingPage/pos", self.pos())
        settings.setValue("ui/LandingPage/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/LandingPage/pos", defaultValue=QPoint(410, 241), type=QPoint))
        self.resize(settings.value("ui/LandingPage/size", defaultValue=QSize(750, 701), type=QSize))

    def clear_selection(self):
        self.listWidget.setCurrentItem(None)

class UnselectableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.previous_item = None

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is not None:
            if item is self.currentItem():
                self.selectionModel().clearSelection()
                self.setCurrentIndex(QtCore.QModelIndex())
                self.clearSelection()
                event.accept()
                return
            else:
                self.previous_item = item
                super().mousePressEvent(event)
                return

        self.selectionModel().clearSelection()
        self.setCurrentIndex(QtCore.QModelIndex())
        self.clearSelection()
        event.accept()


class LinkLabel(QLabel):
    def __init__(self, text, url, parent=None):
        super().__init__(text, parent)
        self.url = url
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Double-click to open doi")
        self.setWordWrap(True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(QUrl(self.url))
        super().mouseDoubleClickEvent(event)