import os
import sys
import typing

import PyQt6
from PyQt6 import QtGui
from PyQt6.QtCore import QSettings, Qt, QPoint, QSize
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QDialog, QDialogButtonBox
from PyQt6.uic import loadUi


class QPropertiesDialog(QDialog):
    def __init__(self):
        super().__init__()
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "ui_Settings.ui")
        loadUi(sources_ui_file, self)

        self.settings = QSettings("CSUF", "GeoChron")
        self.loadWindowState()

        self.buttonBox: QDialogButtonBox
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.connect(self.cancel)
        self.buttonBox.helpRequested.connect(self.help)

    def saveSettings(self):
        self.settings.setValue("app/font_size", 12)
        self.settings.setValue("app/theme", "Dark")

    def saveWindowState(self):
        self.settings.setValue("ui/SettingsPage/pos", self.pos())
        self.settings.setValue("ui/SettingsPage/size", self.size())

    def loadWindowState(self):
        self.move(self.settings.value("ui/SettingsPage/pos", defaultValue=QPoint(410, 241)))
        self.resize(self.settings.value("ui/SettingsPage/size", defaultValue=QSize(810, 569)))


        # font_size = self.settings.value("app/font_size", defaultValue=12, type=int)
        # table_font_size = self.settings.value("app/table_font_size", defaultValue=12, type=int)

    @PyQt6.QtCore.pyqtSlot()
    def apply(self) -> None:
        self.saveWindowState()
        super().done(0)

    @PyQt6.QtCore.pyqtSlot()
    def accepted(self) -> None:
        self.saveWindowState()
        super().done(0)

    @PyQt6.QtCore.pyqtSlot()
    def cancel(self) -> None:
        self.saveWindowState()
        super().done(0)

    @PyQt6.QtCore.pyqtSlot()
    def help(self) -> None:
        self.saveWindowState()
        super().done(0)

    def closeEvent(self, a0: typing.Optional[QtGui.QCloseEvent]) -> None:
        self.saveWindowState()
        super().closeEvent(a0)

