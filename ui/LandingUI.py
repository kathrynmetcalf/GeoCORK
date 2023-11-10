import sys
from pathlib import Path

import PyQt6
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
import qtawesome
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QStyle, QMessageBox, QWidget
import webbrowser

from ui.QPropertiesDialog import QPropertiesDialog


class LandingPage(QWidget):
    def __init__(self):
        super().__init__()

        sources_ui_file = "landingpage.ui"
        loadUi(sources_ui_file, self)
        self.pushButton_2.clicked.connect(self.showFileDialog)

        self.pushButton_3.clicked.connect(self.showSettings)

        self.pushButton_4: QPushButton
        self.pushButton_4.setIcon(qtawesome.icon('fa.github', color='white', scale_factor=1.5))
        self.pushButton_4.clicked.connect(self.open_github)
        self.selected_files = None

    def open_github(self):
        webbrowser.open('http://github.com')
    def showFileDialog(self):
        file_dialog = QFileDialog(self, 'Open Database File', str(Path.home()), 'db(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.selected_files = file_dialog.selectedFiles()
            self.close()

    def showSettings(self):
        properties_dialog = QPropertiesDialog()

        if properties_dialog.exec():
            self.close()

    def get_filename(self):
        return self.selected_files[0]

def main():
    app = QApplication(sys.argv)
    window = LandingPage()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
