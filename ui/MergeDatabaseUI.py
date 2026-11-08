import os
import sqlite3
import sys
from pathlib import Path

from PyQt6.QtWidgets import QDialogButtonBox, QFileDialog, QDialog, QMessageBox
from PyQt6.uic import loadUi

import logger_setup
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.MergeDatabase import merge_database


class MergeDatabaseDialog(QDialog):
    """
    Dialog to assist the user in merging two SQLite database files together. Dialog should be used when both databases
    are not opened or in use by other applications.
    """

    def __init__(self):
        super().__init__()
        logger_setup.get_logger().info("Starting MergeDatabase UI Page...")
        self.loading_manager = LoadingDialogManager.get_instance()

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "MergeDatabase.ui")
        loadUi(sources_ui_file, self)
        self.setWindowTitle('Merge Database')

        self.source_db_file = None
        """Source database file is the SQLite database that will accept incoming data from another database"""
        self.incoming_db_file = None
        """Incoming database file is the SQLite database that will transfer data to another database"""

        # connect pushButton signals to their slots
        self.source_db_pushButton.clicked.connect(self.open_source_dialog)
        self.incoming_db_pushButton.clicked.connect(self.open_incoming_dialog)

        # sets the ok button to disabled, enabled later when both files are selected
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        # sets the default button to abort to prevent misclicks
        self.buttonBox.button(QDialogButtonBox.StandardButton.Abort).setDefault(True)
        self.show()

    def open_source_dialog(self) -> None:
        """
        Slot to select the source database file with a file dialog.
        """
        file_dialog = QFileDialog(self, 'Select Source Database File', str(Path.home()), 'Database Files(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.source_db_file = file_dialog.selectedFiles()[0]
            self.update_source_stats()

    def open_incoming_dialog(self) -> None:
        """
        Slot to select the incoming database file with a file dialog.
        """
        file_dialog = QFileDialog(self, 'Select Incoming Database File', str(Path.home()), 'Database Files(*.db)')
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if file_dialog.exec():
            self.incoming_db_file = file_dialog.selectedFiles()[0]
            self.update_incoming_stats()

    def update_source_stats(self) -> None:
        """
        Updates the source labels and stats from the selected source file.
        """
        self.validate()
        self.source_db_filepath.setText(self.source_db_file)
        logger_setup.get_logger().info(f'Source database file: {self.source_db_file}')

        source_conn = sqlite3.connect(self.source_db_file)
        with source_conn:
            database_name = source_conn.execute('SELECT Name, Authors FROM About WHERE AboutID=1').fetchall()
            self.source_db_label.setText(f'Source Database {database_name[0][0]} BY {database_name[0][1]}')

            sample_count = source_conn.execute('SELECT COUNT(*) FROM Samples').fetchall()
            self.source_db_sample_label.setText(f'Samples: {sample_count[0][0]}')

            upb_count = source_conn.execute('SELECT COUNT(*) FROM UPbAnalyses').fetchall()
            self.source_db_upb_label.setText(f'UPbAnalyses: {upb_count[0][0]}')
        source_conn.close()

    def update_incoming_stats(self):
        """
        Updates the incoming labels and stats from the selected incoming file.
        """
        self.validate()
        self.incoming_db_filepath.setText(self.incoming_db_file)
        logger_setup.get_logger().info(f'Incoming database file: {self.incoming_db_file}')

        incoming_conn = sqlite3.connect(self.incoming_db_file)
        with incoming_conn:
            database_name = incoming_conn.execute('SELECT Name, Authors FROM About WHERE AboutID=1').fetchall()
            self.incoming_db_label.setText(f'Source Database {database_name[0][0]} BY {database_name[0][1]}')

            sample_count = incoming_conn.execute('SELECT COUNT(*) FROM Samples').fetchall()
            self.incoming_db_sample_label.setText(f'Samples: {sample_count[0][0]}')

            upb_count = incoming_conn.execute('SELECT COUNT(*) FROM UPbAnalyses').fetchall()
            self.incoming_db_upb_label.setText(f'UPbAnalyses: {upb_count[0][0]}')
        incoming_conn.close()

    def validate(self) -> bool:
        """
        Validates to make sure source and incoming databases are both set and valid read/write connections can be
        established.
        :return: True if both source and incoming databases are valid. False otherwise.
        """
        if self.source_db_file is not None and self.incoming_db_file is not None:
            if self.source_db_file == self.incoming_db_file:
                logger_setup.get_logger().critical('Database files must be different.')

            try:
                source_conn = sqlite3.connect(self.source_db_file)
            except sqlite3.Error as e:
                logger_setup.get_logger().critical(f"Error opening source database: {e.sqlite_errorname}")
                logger_setup.get_logger().debug(f"Error: {e}")
                return False
            try:
                incoming_conn = sqlite3.connect(self.incoming_db_file)
            except sqlite3.Error as e:
                logger_setup.get_logger().critical(f"Error opening incoming database: {e.sqlite_errorname}")
                logger_setup.get_logger().debug(f"Error: {e}")
                return False
            with source_conn:
                try:
                    source_conn.execute('BEGIN;')
                    source_conn.execute('CREATE TABLE IF NOT EXISTS _access_test (id INTEGER);')
                    source_conn.execute('INSERT INTO _access_test (id) VALUES (1);')
                    source_conn.execute('DELETE FROM _access_test;')
                    source_conn.execute('DROP TABLE _access_test;')
                    source_conn.execute('COMMIT;')
                except sqlite3.Error as e:
                    if 'database is locked' in e.__str__():
                        logger_setup.get_logger().critical('Source connection database is locked.')
                    else:
                        logger_setup.get_logger().critical('Source connection could not be established.')
                    logger_setup.get_logger().info(f'SQL error: {e}')
                    return False

            with incoming_conn:
                try:
                    source_conn.execute('BEGIN;')
                    source_conn.execute('CREATE TABLE IF NOT EXISTS _access_test (id INTEGER);')
                    source_conn.execute('INSERT INTO _access_test (id) VALUES (1);')
                    source_conn.execute('DELETE FROM _access_test;')
                    source_conn.execute('DROP TABLE _access_test;')
                    source_conn.execute('COMMIT;')
                except sqlite3.Error as e:
                    if 'database is locked' in e.__str__():
                        logger_setup.get_logger().critical('Incoming connection database is locked.')
                    else:
                        logger_setup.get_logger().critical('Incoming connection could not be established.')
                    logger_setup.get_logger().info(f'SQL error: {e}')
                    return False
            source_conn.close()
            incoming_conn.close()
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            return True
        return False

    def accept(self):
        """
        Slot for when the OK button is clicked/accepted within the MergeDatabaseDialog.
        """
        if QMessageBox.StandardButton.Yes == QMessageBox.question(self, 'Confirm merge database',
                                                                  'Are you sure you wish to merge these databases \n and have created backups?',
                                                                  buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                                                  defaultButton=QMessageBox.StandardButton.No):
            logger_setup.get_logger().info(
                f"Source database: {self.source_db_file} will be merged with incoming database: {self.incoming_db_file}")
            if not merge_database(self.source_db_file, self.incoming_db_file):
                logger_setup.get_logger().critical("Databases could not be merged")
            logger_setup.get_logger().info("Databases have been merged successfully")
            QMessageBox.information(QMessageBox(), "Success", "Databases merged successfully")
        super().accept()
