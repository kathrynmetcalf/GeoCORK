import datetime
import os
import sqlite3
from datetime import datetime
from typing import override

from PyQt6.QtCore import QStandardPaths, QEventLoop
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import QProgressDialog
from tzlocal import get_localzone

from util import logger
from util.database.Savepoint_manager import SavepointManager


def backup_database(database: QSqlDatabase) -> None | str:
    """
    Backs up the current database or provided database. Returns either None if there was no backup created
    or returns the file path as string for the backup file.
    :param database: QSqlDatabase or None
    :return: None if failure, file path as a string if success
    """
    if database is None:
        db = QSqlDatabase.database()
    else:
        db = database
    db_file = db.databaseName()
    logger.get_logger().info(f'Creating backup of {db.connectionName()}:')
    local_timezone = get_localzone()
    current_time = datetime.now(local_timezone)
    formatted_timestamp = current_time.strftime('%Y-%m-%d %H.%M.%S')

    backup_file = (QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) +
                   rf"/backups/{os.path.basename(db_file).replace('.db', '')}/{os.path.basename(db_file).replace('.db', '')}-{formatted_timestamp}.db")

    backup_dir = os.path.dirname(backup_file)
    if backup_dir and not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)

    logger.get_logger().info(f'Backing up to {backup_file}')

    if not SavepointManager.get_instance().active_savepoints():
        progressBar = QProgressDialog()
        progressBar.setLabelText('Backing up database...')
        progressBar.setCancelButtonText(None)
        progressBar.show()

        # Create and start the backup thread
        thread = BackupThread(db_file, backup_file)
        thread.progress_updated.connect(progressBar.setValue)

        loop = QEventLoop()

        def on_finished():
            loop.quit()

        thread.backup_finished.connect(on_finished)
        thread.start()

        # Block the current function until the thread is done
        loop.exec()  # This keeps UI responsive

        progressBar.close()
        return backup_file

    else:
        logger.get_logger().critical(
            'Uncommitted changes: cannot backup\nPlease commit or discard changes before creating a backup.')
        logger.get_logger().debug(f"Savepoints: {SavepointManager.get_instance().active_savepoints_names()}")
        return None


class BackupThread(QThread):
    progress_updated = pyqtSignal(int)
    backup_finished = pyqtSignal()

    def __init__(self, source_db, backup_db):
        super().__init__()
        self.source_db = source_db
        self.backup_db = backup_db
        self.last_percent = 0

    @override
    def run(self):
        src = sqlite3.connect(self.source_db)
        backup = sqlite3.connect(self.backup_db)

        logger.get_logger().info('Beginning Backup Thread')

        def progress(status, remaining, total):
            # Calculate progress percentage
            percent = 100 - int((remaining / total) * 100)
            if percent != self.last_percent:
                logger.get_logger().info(f'Backup Progress: {percent}')
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

    @override
    def run(self):
        src = sqlite3.connect(self.source_db, timeout=10)
        backup = sqlite3.connect(self.backup_db, timeout=10)

        logger.get_logger().info('Beginning Restore Thread')

        def progress(status, remaining, total):
            # Calculate progress percentage
            percent = 100 - int((remaining / total) * 100)
            if percent != self.last_percent:
                logger.get_logger().info(f'Backup Progress: {percent}')
                self.last_percent = percent

            self.progressBar.setValue(percent)

        backup.backup(src, pages=5, progress=progress)
        src.commit()
        backup.commit()
        backup.close()
        src.close()

        self.restore_finished.emit()
