import os
import sqlite3
import sys
import webbrowser
from pathlib import Path

import qtawesome
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QEvent, QEventLoop, Qt, QPoint, QSize, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QAction, QDesktopServices, QGuiApplication, QPainter, QPalette
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QFileDialog, QPushButton, QMessageBox, QMainWindow, \
    QListWidget, QListWidgetItem, QApplication, QLabel, QSplitter, QWidget, QVBoxLayout, QHBoxLayout
import logger_setup
from Functions import Savepoint_manager
from Functions.Database_manager import update_database, turn_on_foreign_keys
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Text_manipulations import shrink_home, expand_home
from Functions.Widget_classes import show_loading_dialog, close_loading_dialog
from ui.MergeDatabaseUI import MergeDatabaseDialog
from ui.settings.SettingsCore import update_stylesheet


LOGO_BOX = QSize(500, 100)
"""Maximum size of the landing page logo; the logo is scaled to fit while keeping its aspect ratio."""

THEME_EVENTS = (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange, QEvent.Type.StyleChange)
"""Widget events that may mean the light/dark appearance changed (stylesheet swap, palette swap, OS theme)."""


class LandingPage(QMainWindow):
    def __init__(self, start_filepath=None):
        super().__init__()
        logger_setup.get_logger().info("Starting Landing Page...")
        from ui.menus.StaticMenuGuard import install_static_menus
        install_static_menus(self)

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.base_path = base_path
        self._applied_theme = None  # (is_dark, device_pixel_ratio, text_color) last applied
        self._logo_cache = {}  # (is_dark, device_pixel_ratio) -> QPixmap

        self.setWindowTitle('GeoCORK')
        update_stylesheet()

        self.db = None

        self.central_widget = QWidget()
        self.central_widget.setLayout(QVBoxLayout())
        self.setCentralWidget(self.central_widget)

        self.logo = QLabel()
        self.central_widget.layout().addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.center_widget = QWidget()
        self.center_widget.setLayout(QHBoxLayout())

        # list widget for recent databases
        self.listWidget = UnselectableListWidget()
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setMinimumSize(QtCore.QSize(400, 500))
        self.listWidget.setMaximumSize(QtCore.QSize(400, 1000))
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        self.listWidget.customContextMenuRequested.connect(self.recents_context_menu)
        self.listWidget.itemDoubleClicked.connect(self.clicked_file)

        self.center_widget.layout().addWidget(self.listWidget)

        # buttons for new, open, merge, restore default settings
        buttons_widget = QWidget()
        buttons_widget.setLayout(QVBoxLayout())
        buttons_widget.layout().addStretch(1)

        self.newdatabase_button = QPushButton('New Database')
        self.newdatabase_button.setObjectName("newdatabase_button")
        buttons_widget.layout().addWidget(self.newdatabase_button)
        self.newdatabase_button.clicked.connect(self.new_database_dialog)

        self.opendatabase_button = QPushButton('Open Database')
        self.opendatabase_button.setObjectName("opendatabase_button")
        buttons_widget.layout().addWidget(self.opendatabase_button)
        self.opendatabase_button.clicked.connect(self.showFileDialog)

        self.mergedatabase_button = QPushButton('Merge Database')
        self.mergedatabase_button.setObjectName("mergedatabase_button")
        buttons_widget.layout().addWidget(self.mergedatabase_button)
        self.mergedatabase_button.clicked.connect(self.show_merge_db)

        buttons_widget.layout().addStretch(1)  # Add stretch to push the Restore Default Settings button to the bottom

        self.defaultsetting_button = QPushButton('Restore Default Settings')
        self.defaultsetting_button.setObjectName("defaultsetting_button")
        buttons_widget.layout().addWidget(self.defaultsetting_button)
        self.defaultsetting_button.clicked.connect(self.restore_settings)
        buttons_widget.layout().addStretch(1)

        self.center_widget.layout().addWidget(buttons_widget)

        self.central_widget.layout().addWidget(self.center_widget)

        bottom_info = QWidget()
        bottom_info.setLayout(QHBoxLayout())

        self.citation = LinkLabel(text = f'Metcalf, K., & Burges, J. 2026. kathrynmetcalf/GeoCORK: GeoCORK {settings.value('default_geocork_version')}. Zenodo. https://doi.org/10.5281/zenodo.15833658',
                                  url = 'https://doi.org/10.5281/zenodo.15833658')
        self.citation.setObjectName("citation")
        self.citation.setToolTip("Double-click to open the GeoCORK publication citation")
        bottom_info.layout().addWidget(self.citation)

        self.github_button = QPushButton()
        self.github_button.setObjectName("github_button")
        self.github_button.setFixedSize(QSize(35, 35))
        self.github_button.setIconSize(QSize(35, 35))
        self.github_button.setStyleSheet("QPushButton { border: none; background: none; }")
        self.github_button.setToolTip("Double-click to open the GeoCORK GitHub repository")
        self.github_button.clicked.connect(self.open_github)
        bottom_info.layout().addWidget(self.github_button)

        self.selected_files = None

        self.central_widget.layout().addWidget(bottom_info)

        self.list_recents = settings.value("ui/LandingPage/recentlist", defaultValue=[], type=list)

        for path in self.list_recents:
            self.listWidget.addItem(shrink_home(path))

        # Logo and GitHub icon follow the light/dark appearance of the current stylesheet
        self.apply_theme()
        style_hints = QGuiApplication.styleHints()
        if hasattr(style_hints, 'colorSchemeChanged'):  # Qt 6.5+: OS light/dark switch
            style_hints.colorSchemeChanged.connect(lambda _scheme: self.queue_theme_update())

        self.show()
        self.loadWindowState()

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

    # ------------------------------------------------------------------ theme
    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in THEME_EVENTS:
            self.queue_theme_update()

    def showEvent(self, event):
        # The theme may have changed in Settings while GeoCORKMain was open and this page was hidden
        super().showEvent(event)
        self.queue_theme_update()

    def queue_theme_update(self):
        """
        Defer the theme update to the next event-loop pass so Qt has finished re-polishing the widget
        with the new stylesheet before the colours are read. Repeated calls are harmless.
        """
        QTimer.singleShot(0, self.apply_theme)

    def is_dark_mode(self) -> bool:
        """
        Determine whether the landing page is currently displayed in dark mode, using the colours actually
        applied by the stylesheet/palette rather than a stored setting, so any theme mechanism is supported.
        :return: True if the window background is dark
        """
        self.ensurePolished()
        background = self.palette().color(self.backgroundRole())
        text = self.palette().color(QPalette.ColorRole.WindowText)
        # Dark mode = light text on a dark background
        return background.lightness() < text.lightness()

    def apply_theme(self):
        """
        Update theme-dependent elements (logo and GitHub icon) to match the current light/dark appearance.
        """
        is_dark = self.is_dark_mode()
        dpr = self.devicePixelRatioF()
        text_color = self.palette().color(QPalette.ColorRole.WindowText).name()
        theme_key = (is_dark, dpr, text_color)
        if theme_key == self._applied_theme:
            return
        self._applied_theme = theme_key
        logger_setup.get_logger().debug(f"Landing page theme: {'dark' if is_dark else 'light'}")

        pixmap = self.get_logo_pixmap(is_dark, dpr)
        if pixmap is not None and not pixmap.isNull():
            self.logo.setPixmap(pixmap)

        # Match the GitHub icon to the stylesheet's text colour
        self.github_button.setIcon(qtawesome.icon('fa6b.github', color=text_color, scale_factor=1.0))

    def get_logo_pixmap(self, is_dark: bool, dpr: float):
        """
        Render the light or dark GeoCORK SVG logo, scaled to LOGO_BOX, at the screen's pixel density.
        Falls back to GeoCORK_Logo.png if the SVG is missing or invalid.
        :param bool is_dark: whether to use the dark mode logo
        :param float dpr: device pixel ratio of the screen showing the landing page
        :return: QPixmap of the logo, or None if no logo could be loaded
        """
        cache_key = (is_dark, dpr)
        if cache_key in self._logo_cache:
            return self._logo_cache[cache_key]

        svg_name = 'GeoCORKLogo_Darkmode.svg' if is_dark else 'GeoCORKLogo_Lightmode.svg'
        renderer = QSvgRenderer(os.path.join(self.base_path, svg_name))
        if renderer.isValid():
            size = renderer.defaultSize().scaled(LOGO_BOX, Qt.AspectRatioMode.KeepAspectRatio)
            pixmap = QPixmap(QSize(round(size.width() * dpr), round(size.height() * dpr)))
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter)
            painter.end()
            pixmap.setDevicePixelRatio(dpr)
        else:
            logger_setup.get_logger().debug(f"Could not load {svg_name}, falling back to GeoCORK_Logo.png")
            pixmap = QPixmap(os.path.join(self.base_path, 'GeoCORK_Logo.png'))
            if pixmap.isNull():
                return None
            pixmap = pixmap.scaled(LOGO_BOX, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)

        self._logo_cache[cache_key] = pixmap
        return pixmap

    def open_about_db(self):
        # This is a new database, so prompt the user to fill in the About Database form
        if not self.test_database_lock():
            if not update_database():
                logger_setup.get_logger().critical('Error updating and displaying database')
                return
            from ui.settings.Settings import SettingsDialog
            settings_dialog = SettingsDialog()
            settings_dialog.settings_tabWidget.setCurrentIndex(2)
            # Set the current tab to the About Database tab
            settings_dialog.exec()

    def open_geo_cork(self, skip_update=False):
        if not self.test_database_lock():
            if '/' in self.selected_files:
                show_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
            elif '\\' in self.selected_files:
                show_loading_dialog("Opening",
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
                    close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
                    self.show()
                    return
                if not turn_on_foreign_keys():
                    close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
                    self.show()
                    return
                Savepoint_manager.SavepointManager()
            if not skip_update:
                if not update_database():
                    logger_setup.get_logger().critical('Error updating and displaying database')
                    close_loading_dialog("Opening",
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
            close_loading_dialog("Opening",
                         f"Opening {self.selected_files.split('/')[-1]}... \n(GeoCORK may be slower for large databases)")
        elif '\\' in self.selected_files:
            close_loading_dialog("Opening",
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

    def restore_settings(self):
        from Functions.Settings_manager import SettingsManager
        settings = SettingsManager().settings
        settings.setValue('default_settings', 'true')
        from ui.settings.SettingsCore import reset_to_default_settings
        reset_to_default_settings()
        msg = QMessageBox(QMessageBox.Icon.Information, 'Restored', 'Default settings restored')
        msg.exec()

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