import time
import os
from datetime import datetime

from tzlocal import get_localzone

from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt6.QtCore import QStandardPaths, QEventLoop

from Functions.BackupDatabase import BackupThread
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Savepoint_manager import SavepointManager
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
import logger_setup
import Functions.SQLUtils as SQLUtils


def turn_on_foreign_keys(database: QSqlDatabase = QSqlDatabase()) -> bool:
    """
    Turn on foreign keys for a given database connection, if no database is provided the default database will be used.
    :param QSqlDatabase database: QSqlDatabase instance to enable foreign keys
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QSqlQuery(database)
    logger_setup.get_logger().debug(f'Turning on foreign keys for database: {database.connectionName()}')
    if not query.exec('PRAGMA foreign_keys=ON'):
        logger_setup.get_logger().critical(f'Could not turn on foreign keys')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec('PRAGMA foreign_keys'):
        logger_setup.get_logger().critical(f'Could not check foreign keys')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if query.next():
        if query.value(0) == 1:
            logger_setup.get_logger().info('Foreign keys are on')
            return True
        else:
            logger_setup.get_logger().critical('Failed to re-enable foreign keys')
            logger_setup.get_logger().info(f'Foreign keys status: {query.value(0)}')
            return False

    return False


def turn_off_foreign_keys(database: QSqlDatabase = QSqlDatabase()) -> bool:
    """
    Turn off foreign keys for a given database connection, if no database is provided the default database will be used.
    :param QSqlDatabase database: QSqlDatabase instance to enable foreign keys
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QSqlQuery(database)
    logger_setup.get_logger().debug(f'Turning off foreign keys for database: {database.connectionName()}')
    if not query.exec('PRAGMA foreign_keys=OFF'):
        logger_setup.get_logger().critical(f'Could not turn off foreign keys')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec('PRAGMA foreign_keys'):
        logger_setup.get_logger().critical(f'Could not check foreign keys')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if query.next():
        if query.value(0) == 0:
            logger_setup.get_logger().info('Foreign keys are off')
            return True
        else:
            logger_setup.get_logger().critical('Failed to disable foreign keys')
            return False

    return False


def update_database(database=None) -> bool:
    """
    Run this on startup and when settings are changed.
    The database has generated columns that set display values based on units and formats in settings. These need to be
    updated if the settings are changed. This function will drop and recreate the generated columns.
    Uses the default connection established with the database file in GeoCORKMain.py if no database is provided.
    :param database: QSqlDatabase instance to use, if None the default database is used
    :return: True for success, False for failure
    :rtype: bool
    """
    start_time = time.time()
    loading_manager = LoadingDialogManager.get_instance()
    loading_manager.show_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
    logger_setup.get_logger().info("Updating database")
    # Check if the database exists and all tables are present
    if database is None:
        db = QSqlDatabase.database()
    else:
        db = database
    if not db.commit():
        if 'no transaction is active' not in db.lastError().text():
            logger_setup.get_logger().critical(f"Error committing database")
            logger_setup.get_logger().debug(f'Error: {db.lastError().text()}')
            loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
    if not db.close():
        if 'no transaction is active' not in db.lastError().text():
            logger_setup.get_logger().critical(f"Error closing database")
            logger_setup.get_logger().debug(f'Error: {db.lastError().text()}')
            loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
    if not db.open():
        logger_setup.get_logger().critical(f"Error opening database")
        logger_setup.get_logger().debug(f'Error: {db.lastError().text()}')
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    if not turn_on_foreign_keys():
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    if database is None:
        database = QSqlDatabase.database()
    query = QSqlQuery(db=database)

    '''Backup database before any changes.
    Restore the backup before returning if the update fails'''

    from Functions import Create_database as Create_db, Create_indexes
    from Functions import Alter_database as Alter_db

    # Update database schema
    if not query.exec('SELECT Version FROM About WHERE AboutID = 1'):
        db_version = None
    else:
        if not query.next():
            logger_setup.get_logger().critical('Error retrieving database version')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
        else:
            db_version = query.value(0)
            logger_setup.get_logger().info(f'Database version: {db_version}')
    # if db_version != settings.value('geocork_version'):
    if not turn_off_foreign_keys():
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    schema_success = Create_db.update_schema(db_version, database=db)
    if schema_success == 'False':
        logger_setup.get_logger().debug(f"Error updating schema from {db_version} to {settings.value('geocork_version')}")
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setText(f"Error updating schema from {db_version} to {settings.value('geocork_version')}\nWould you like to try to open the database anyway? \n \n This will likely cause issues with your data and is not recommended.")
        dialog.setWindowTitle("Error updating database")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        ret = dialog.exec()
        if ret != QMessageBox.StandardButton.Yes:
            loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
        logger_setup.get_logger().info('Trying to open the database anyway')
    elif schema_success == 'Cancel':
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    elif schema_success != 'True':
        # A backup file was returned to restore
        backup_file = schema_success
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setText(
            f"Error updating schema from v.{db_version} to v.{settings.value('geocork_version')}\nWould you like to restore from the backup file?")
        dialog.setWindowTitle("Error updating database")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        ret = dialog.exec()
        if ret != QMessageBox.StandardButton.Yes:
            loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
            for widget in QApplication.allWidgets():
                if widget.objectName() == 'LandingPage':
                    widget.restore_backup(database.databaseName(), backup_file)
                    return False

    if not turn_on_foreign_keys():
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    if not Create_db.create_tables(database):
        logger_setup.get_logger().critical(f"Error creating database tables")
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    if not Create_indexes.create_indexes(db):
        logger_setup.get_logger().critical(f"Error creating database indexes")
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    # Make sure the view column settings do not have any leftover old column names
    from ui import Settings
    if not Settings.update_column_settings():
        logger_setup.get_logger().critical(f"Error updating database settings")
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    # Drop and regenerate the generated columns
    if not Alter_db.settings_reset(database):
        logger_setup.get_logger().critical(f"Error resetting settings")
        loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    end_time = time.time()
    loading_manager.close_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
    logger_setup.get_logger().info(f"Database updated in {end_time - start_time} seconds")
    database.commit()

    '''Delete backup made at the beginning of the update if it exists'''

    return True


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
    logger_setup.get_logger().info(f'Creating backup of {db.connectionName()}:')
    local_timezone = get_localzone()
    current_time = datetime.now(local_timezone)
    formatted_timestamp = current_time.strftime('%Y-%m-%d %H.%M.%S')

    backup_file = (QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) +
                   rf"/backups/{os.path.basename(db_file).replace('.db', '')}/{os.path.basename(db_file).replace('.db', '')}-{formatted_timestamp}.db")

    backup_dir = os.path.dirname(backup_file)
    if backup_dir and not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)

    logger_setup.get_logger().info(f'Backing up to {backup_file}')

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
        logger_setup.get_logger().critical(
            'Uncommitted changes: cannot backup\nPlease commit or discard changes before creating a backup.')
        logger_setup.get_logger().debug(f"Savepoints: {SavepointManager.get_instance().active_savepoints_names()}")
        return None