import sqlite3

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QProgressDialog

import logger_setup


class BackupThread(QThread):
    progress_updated = pyqtSignal(int)
    backup_finished = pyqtSignal()
    def __init__(self, source_db, backup_db):
        super().__init__()
        self.source_db = source_db
        self.backup_db = backup_db
        self.last_percent = 0

    def run(self):
        src = sqlite3.connect(self.source_db)
        backup = sqlite3.connect(self.backup_db)

        logger_setup.get_logger().info('Beginning Backup Thread')

        def progress(status, remaining, total):
            # Calculate progress percentage
            percent = 100 - int((remaining / total) * 100)
            if percent != self.last_percent:
                logger_setup.get_logger().info(f'Backup Progress: {percent}')
                self.last_percent = percent

            self.progress_updated.emit(percent)

        src.backup(backup, pages=5, progress=progress)
        backup.close()
        src.close()
        self.backup_finished.emit()


class RestoreThread(QThread):
    progress_updated = pyqtSignal(int)
    restore_finished = pyqtSignal()

    def __init__(self, source_db, backup_db):
        super().__init__()

        self.source_db = source_db
        self.backup_db = backup_db
        self.last_percent = 0
        self.progressBar = QProgressDialog()
        self.progressBar.setLabelText('Restoring database...')
        self.progressBar.setCancelButtonText(None)
        self.progressBar.show()

    def run(self):
        src = sqlite3.connect(self.source_db, timeout=10)
        backup = sqlite3.connect(self.backup_db, timeout=10)

        logger_setup.get_logger().info('Beginning Restore Thread')

        def progress(status, remaining, total):
            # Calculate progress percentage
            percent = 100 - int((remaining / total) * 100)
            if percent != self.last_percent:
                logger_setup.get_logger().info(f'Backup Progress: {percent}')
                self.last_percent = percent

            self.progressBar.setValue(percent)

        backup.backup(src, pages=5, progress=progress)
        src.commit()
        backup.commit()
        backup.close()
        src.close()

        self.restore_finished.emit()
