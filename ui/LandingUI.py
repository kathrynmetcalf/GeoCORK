import sys
from pathlib import Path

import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSettings, QEventLoop, Qt, QPoint, QSize
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
import qtawesome
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QStyle, QMessageBox, QWidget, \
    QListWidget
import webbrowser
from Functions.Create_database import create_tables
from ui.GeoChronMain import GeoChron

from ui.QPropertiesDialog import QPropertiesDialog


class LandingPage(QWidget):
    def __init__(self):
        super().__init__()
        sources_ui_file = "ui/landingpage.ui"
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
        self.show()

    def closeEvent(self, a0):
        self.saveWindowState()
        super().closeEvent(a0)

    def open_geo_chron(self):
        geo_chron = GeoChron(self)
        geo_chron.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()

        geo_chron.destroyed.connect(loop.quit)
        loop.exec()
        self.show()

    def clicked_file(self):
        self.selected_files = self.listWidget.currentItem().text()
        self.hide()
        self.open_geo_chron()


    def new_database_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Database Files(*.db)",
                                                   options=options)
        if file_name:
            create_tables(file_name + ".db")
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