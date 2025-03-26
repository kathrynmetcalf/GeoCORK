import os
import sqlite3
import sys
from pathlib import Path

from PyQt6.QtWidgets import QDialogButtonBox, QPushButton, QLabel, QFileDialog, QWidget, QDialog, QMessageBox
from PyQt6.uic import loadUi

import logger_setup
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Settings_manager import settings
from Functions.MergeDatabase import merge_database


class MergeDatabaseDialog(QDialog):
    def __init__(self):
        super().__init__()
        logger_setup.get_logger().info("Starting MergeDatabase UI Page...")
        self.loading_manager = LoadingDialogManager.get_instance()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file =os.path.join(base_path,  "MergeDatabase.ui")
        loadUi(sources_ui_file, self)
        self.setWindowTitle('Merge Database')
        self.buttonBox: QDialogButtonBox
        self.buttonBox.button(QDialogButtonBox.StandardButton.Abort).setDefault(True)

        self.source_db_file = None
        self.incoming_db_file = None

        self.source_db_pushButton.clicked.connect(self.open_source_dialog)
        self.incoming_db_pushButton.clicked.connect(self.open_incoming_dialog)

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.show()

    def open_source_dialog(self, filepath):
        file_dialog = QFileDialog(self, 'Select Source Database File', str(Path.home()), 'Database Files(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.source_db_file = file_dialog.selectedFiles()[0]
            self.update_source_stats()

    def open_incoming_dialog(self):
        file_dialog = QFileDialog(self, 'Select Incoming Database File', str(Path.home()), 'Database Files(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.incoming_db_file = file_dialog.selectedFiles()[0]
            self.update_incoming_stats()

    def update_source_stats(self):
        self.validate()
        self.source_db_filepath.setText(self.source_db_file)

        source_conn = sqlite3.connect(self.source_db_file)
        with source_conn:
            database_name = source_conn.execute('SELECT Name, Authors FROM About WHERE AboutID=1').fetchall()
            self.source_db_label.setText(f'Source Database {database_name[0][0]} BY {database_name[0][1]}')

            sample_count = source_conn.execute('SELECT COUNT(*) FROM Samples').fetchall()
            self.source_db_sample_label.setText(f'Samples: {sample_count[0][0]}')

            upb_count = source_conn.execute('SELECT COUNT(*) FROM UPbAnalyses').fetchall()
            self.source_db_upb_label.setText(f'UPbAnalyses: {upb_count[0][0]}')

    def update_incoming_stats(self):
        self.validate()
        self.incoming_db_filepath.setText(self.incoming_db_file)

        incoming_conn = sqlite3.connect(self.incoming_db_file)
        with incoming_conn:
            database_name = incoming_conn.execute('SELECT Name, Authors FROM About WHERE AboutID=1').fetchall()
            self.incoming_db_label.setText(f'Source Database {database_name[0][0]} BY {database_name[0][1]}')

            sample_count = incoming_conn.execute('SELECT COUNT(*) FROM Samples').fetchall()
            self.incoming_db_sample_label.setText(f'Samples: {sample_count[0][0]}')

            upb_count = incoming_conn.execute('SELECT COUNT(*) FROM UPbAnalyses').fetchall()
            self.incoming_db_upb_label.setText(f'UPbAnalyses: {upb_count[0][0]}')

    def validate(self):
        if self.source_db_file is not None and self.incoming_db_file is not None:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def accept(self):
        if QMessageBox.StandardButton.Yes == QMessageBox.question(self, 'Confirm merge database',
                                'Are you sure you wish to merge these databases \n and have created backups?',
                                buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                defaultButton=QMessageBox.StandardButton.No):
            merge_database(self.source_db_file, self.incoming_db_file)
        super().accept()

    def closeEvent(self, a0):
        super().closeEvent(a0)