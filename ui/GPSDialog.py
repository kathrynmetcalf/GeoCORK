import PyQt6
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.uic import loadUi
import ui.GPSFields
from Functions.Savepoint_manager import create_savepoint, rollback_savepoint, release_savepoint
from Functions.Settings_manager import settings


class GPSDialog(QtW.QDialog):
    def __init__(self, table: str, item_ids: list, parent=None):
        super().__init__(parent)
        self.loadWindowState()

        self.gps_fields = ui.GPSFields.GPSFields(table, item_ids)
        self.setLayout(QtW.QVBoxLayout())
        self.layout().addWidget(self.gps_fields)
        self.commit_button = QtW.QPushButton('Commit')
        self.cancel_button = QtW.QPushButton('Cancel')
        self.clear_button = QtW.QPushButton('Clear')
        self.button_layout = QtW.QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.clear_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.commit_button)
        self.layout().addLayout(self.button_layout)
        self.close_by_dialog = False
        self.setModal(True)
        self.setWindowTitle('Edit GPS')

        self.msg_box = QtW.QMessageBox()
        self.msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        self.msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        self.msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)

        create_savepoint('before_edit_gps')

        self.commit_button.clicked.connect(self.commit_question)
        self.cancel_button.clicked.connect(self.discard_question)
        self.clear_button.clicked.connect(self.gps_fields.clear_fields)

    def commit_question(self):
        self.msg_box.setText('Are you sure you want to commit all changes to the database?')
        response = self.msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            self.commit()
        else:
            pass

    def discard_question(self):
        self.msg_box.setText('Are you sure you want to discard all changes?')
        response = self.msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            rollback_savepoint('before_edit_gps')
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False
        else:
            pass

    def commit(self):
        if not self.gps_fields.update_gps():
            print('Error updating GPS fields')
        else:
            self.accept()
            release_savepoint('before_edit_gps')
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def close(self):
        self.saveWindowState()
        if not self.close_by_dialog:
            self.discard_question()
        else:
            super().close()

    def saveWindowState(self):
        settings.setValue("ui/GPSDialog/pos", self.pos())
        settings.setValue("ui/GPSDialog/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/GPSDialog/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/GPSDialog/size", defaultValue=QSize(810, 569)))
