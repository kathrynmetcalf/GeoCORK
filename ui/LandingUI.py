import os
import sqlite3
import sys
import webbrowser
from pathlib import Path

import qtawesome
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QSettings, QEventLoop, Qt, QPoint, QSize
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import QFileDialog, QPushButton, QMessageBox, QWidget, \
    QListWidget, QListWidgetItem
from PyQt6.uic import loadUi

from Functions.Settings_manager import settings
from Functions.Create_database import create_tables
from ui.GeoChronMain import GeoChron
from ui.Settings import SettingsDialog, settings_ids


class LandingPage(QWidget):
    def __init__(self):
        super().__init__()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file =os.path.join(base_path,  "landingpage.ui")
        loadUi(sources_ui_file, self)

        self.loadWindowState()

        self.list_recents = settings.value("ui/LandingPage/recentlist", defaultValue=[])

        print(self.list_recents)

        for (i, item) in enumerate(self.list_recents):
            self.listWidget.addItem(str(item))


        self.newdatabase_button.clicked.connect(self.new_database_dialog)

        self.opendatabase_button.clicked.connect(self.showFileDialog)

        self.settings_button.clicked.connect(self.showSettings)

        self.github_button: QPushButton
        self.github_button.setIcon(qtawesome.icon('fa.github', color='white', scale_factor=1.5))
        self.github_button.clicked.connect(self.open_github)
        self.selected_files = None

        self.listWidget: QListWidget
        self.listWidget.itemDoubleClicked.connect(self.clicked_file)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.recents_context_menu)

        # pixmap = QPixmap(os.path.join(base_path, './geocork.png'))
        pixmap = QPixmap(os.path.join(base_path, './Logo_draft.svg'))
        # pixmap = QPixmap(os.path.join(base_path, './Logo_draft.png'))
        scaled_pixmap = pixmap.scaled(500, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)
        self.show()

    def closeEvent(self, a0):
        self.saveWindowState()
        super().closeEvent(a0)

    def open_geo_chron(self):
        if not self.test_database_lock():
            self.hide()
            geo_chron = GeoChron(self)
            geo_chron.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            loop = QEventLoop()

            geo_chron.destroyed.connect(loop.quit)
            loop.exec()
            self.show()
        else:
            self.show()

    def test_database_lock(self):
        database_path = self.get_filename()
        try:
            # Attempt to connect and perform a simple query
            connection = sqlite3.connect(database_path, timeout=1)  # Set timeout to 1 second
            cursor = connection.cursor()
            cursor.execute("PRAGMA schema_version")  # Simple query to test access
            connection.close()
        except sqlite3.OperationalError as e:
            # Handle the specific database lock error
            if "database is locked" in str(e):
                self.show_message("Database Locked", "The database is currently locked. Please try again later.")
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
        self.selected_files = self.listWidget.currentItem().text()
        self.open_geo_chron()


    def new_database_dialog(self):
        file_name, _ = QFileDialog.getSaveFileName(
            None,
            "Save Database File",
            "",
            "Database Files (*.db)"
        )
        if not file_name:
            return

        # Ensure the filename ends with .xlsx
        if not file_name.lower().endswith(".db"):
            file_name += ".db"

        if file_name:
            QSqlDatabase.addDatabase("QSQLITE")
            QSqlDatabase.database().setDatabaseName(file_name)
            create_tables()
            self.selected_files = file_name
            if self.selected_files not in self.list_recents:
                self.list_recents.append(self.selected_files)
                settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            self.open_geo_chron()
            self.setVisible(False)

    def open_github(self):
        webbrowser.open('http://github.com')


    def showFileDialog(self):
        file_dialog = QFileDialog(self, 'Open Database File', str(Path.home()), 'Database Files(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.selected_files = file_dialog.selectedFiles()[0]
            if self.selected_files not in self.list_recents:
                self.list_recents.append(self.selected_files)
                settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            self.hide()
            self.open_geo_chron()

    def showSettings(self):
        settings_dialog = SettingsDialog()

        if settings_dialog.exec():
            self.hide()

    def recents_context_menu(self, pos):
        item = self.listWidget.itemAt(pos)
        if item:
            context_menu = QtWidgets.QMenu()
            delete_action = QAction("Delete", self.listWidget)
            delete_action.triggered.connect(lambda: self.remove_db_from_recent(item))
            context_menu.addAction(delete_action)
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
            print(str(item.text()))
            for x in self.list_recents:
                print(x == str(item.text()))
            self.list_recents.remove(str(item.text()))
            settings.setValue('ui/LandingPage/recentlist', self.list_recents)

        row = self.listWidget.row(item)
        self.listWidget.takeItem(row)


    def get_filename(self):
        return self.selected_files

    def saveWindowState(self):
        settings.setValue("ui/LandingPage/pos", self.pos())
        settings.setValue("ui/LandingPage/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/LandingPage/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/LandingPage/size", defaultValue=QSize(750, 701)))