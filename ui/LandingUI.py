import sys
from pathlib import Path

import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QSettings, QEventLoop
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
import qtawesome
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QStyle, QMessageBox, QWidget, \
    QListWidget
import webbrowser
from Functions.Create_database import create_tables

from ui.QPropertiesDialog import QPropertiesDialog


class LandingPage(QWidget):
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        sources_ui_file = "landingpage.ui"
        loadUi(sources_ui_file, self)

        self.settings = QSettings("CSUF", "GeoChron")
        self.settings.setValue("ui/LandingPage/pos", self.pos())
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

    def closeEvent(self, a0):
        super().closeEvent(a0)

    def clicked_file(self):
        self.selected_files = self.listWidget.currentItem().text()[2:-2]
        self.close()

    def new_database_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Database Files(*.db)",
                                                   options=options)
        if file_name:
            create_tables(file_name + ".db")
            self.selected_files = file_name
            self.list_recents.append(self.selected_files)
            self.settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            self.close()

    def open_github(self):
        webbrowser.open('http://github.com')
    def showFileDialog(self):
        file_dialog = QFileDialog(self, 'Open Database File', str(Path.home()), 'Database Files(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.selected_files = file_dialog.selectedFiles()[0]
            self.list_recents.append(self.selected_files)
            self.settings.setValue("ui/LandingPage/recentlist", self.list_recents)
            self.close()

    def showSettings(self):
        properties_dialog = QPropertiesDialog()

        if properties_dialog.exec():
            self.close()

    def get_filename(self):
        return self.selected_files

def main():
    app = QApplication(sys.argv)
    window = LandingPage()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
