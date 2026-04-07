from PyQt6 import QtWidgets as QtW
from PyQt6 import QtGui as QtG

import logger_setup
from Functions.Widget_classes import (show_loading_dialog, close_loading_dialog)
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
import ui.ColumnFields

settings = SettingsManager().settings

class ColumnDialog(QtW.QDialog):
    def __init__(self, sample_ids: list, parent=None):
        super().__init__(parent)
        if not sample_ids:
            return
        self.checked_sample_list = sample_ids

        self.column_fields = ui.ColumnFields.ColumnFields(sample_ids)
        self.setLayout(QtW.QVBoxLayout())
        self.layout().addWidget(self.column_fields)
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
        self.setWindowTitle("Edit Sample Column Information")

        self.commit_button.setAutoDefault(False)
        self.cancel_button.setAutoDefault(False)
        self.clear_button.setAutoDefault(False)
        self.close_by_dialog = False

        self.commit_button.clicked.connect(self.commit_clicked)
        self.cancel_button.clicked.connect(self.discard_clicked)
        self.clear_button.clicked.connect(self.column_fields.clear_fields)

        create_savepoint('before_edit_columns')

        close_loading_dialog('Loading', f'Opening column editor...')

    def discard_clicked(self):
        logger_setup.get_logger().info("Discard clicked")
        self.discard_question()

    def commit_clicked(self):
        logger_setup.get_logger().info("Commit clicked")
        self.commit_question()

    def discard_question(self):
        logger_setup.get_logger().info("Discard question called")
        if self.column_fields.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to discard all changes?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            logger_setup.get_logger().info("Showing discard question")
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                logger_setup.get_logger().info("Discarding changes")
                rollback_savepoint('before_edit_columns')
                self.reject()
                self.close_by_dialog = True
                self.close()
                self.close_by_dialog = False
            else:
                self.cancel_button.blockSignals(False)
                pass
        else:
            self.column_fields.updated = False
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def commit_question(self):
        if not self.column_fields.update_column_info():
            return
        if self.column_fields.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to commit all changes to the database?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                self.column_fields.updated = True
                self.commit()
            else:
                pass
        else:
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def commit(self):
        release_savepoint('before_edit_columns')
        # Edit occurred in the dialog
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.column_fields.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info("Closing Column dialog")
                event.accept()
        else:
            logger_setup.get_logger().info("Closing Column dialog")
            event.accept()