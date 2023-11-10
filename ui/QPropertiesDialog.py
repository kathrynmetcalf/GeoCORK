import sys
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi

class QPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__()

        loadUi("ui_Settings.ui", self)

        # Initialize QSettings
        self.settings = QSettings("CSUF", "Geochron")

    def saveSettings(self):
        self.settings.setValue("app/font_size", 12)

    def loadSettings(self):
        font_size = self.settings.value("app/font_size", defaultValue=12, type=int)

        print(f"Font Size: {font_size}")
