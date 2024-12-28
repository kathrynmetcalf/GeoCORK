import sqlite3
import sys
from pathlib import Path

import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSettings, QEventLoop, Qt, QPoint, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtSql import QSqlDatabase
from PyQt6.uic import loadUi
import qtawesome
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QStyle, QMessageBox, QWidget, \
    QListWidget
import webbrowser
from Functions.Create_database import create_tables
from ui.GeoChronMain import GeoChron

from ui.QPropertiesDialog import QPropertiesDialog
import os, sys

class LandingPage(QWidget):
    def __init__(self):
        super().__init__()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file =os.path.join(base_path,  "landingpage.ui")
        loadUi(sources_ui_file, self)

        self.settings = QSettings("CSUF", "GeoChron")
        self.loadWindowState()

        self.list_recents = self.settings.value("ui/LandingPage/recentlist", defaultValue=[])

        for (i, item) in enumerate(self.list_recents):
            #todo make this clickable & deletable
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


        pixmap = QPixmap(os.path.join(base_path, './geocork.png'))
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
            connection = sqlite3.connect(database_path, timeout=2)  # Set timeout to 1 second
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
                self.settings.setValue("ui/LandingPage/recentlist", self.list_recents)
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
                self.settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            self.hide()
            self.open_geo_chron()

    def showSettings(self):
        properties_dialog = QPropertiesDialog()

        if properties_dialog.exec():
            self.hide()

    def get_filename(self):
        return self.selected_files

    def saveWindowState(self):
        self.settings.setValue("ui/LandingPage/pos", self.pos())
        self.settings.setValue("ui/LandingPage/size", self.size())

    def loadWindowState(self):
        self.move(self.settings.value("ui/LandingPage/pos", defaultValue=QPoint(410, 241)))
        self.resize(self.settings.value("ui/LandingPage/size", defaultValue=QSize(750, 701)))