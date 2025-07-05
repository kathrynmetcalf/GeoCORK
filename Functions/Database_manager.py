import time

from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery

import Functions.Database_views as DB_views
from Functions.LoadingDialog_manager import LoadingDialogManager
import logger_setup


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
    loading_manager.show_loading_dialog('Loading', 'Updating database...')
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
            loading_manager.close_loading_dialog('Loading', 'Updating database...')
            return False
    if not db.close():
        if 'no transaction is active' not in db.lastError().text():
            logger_setup.get_logger().critical(f"Error closing database")
            logger_setup.get_logger().debug(f'Error: {db.lastError().text()}')
            loading_manager.close_loading_dialog('Loading', 'Updating database...')
            return False
    if not db.open():
        logger_setup.get_logger().critical(f"Error opening database")
        logger_setup.get_logger().debug(f'Error: {db.lastError().text()}')
        loading_manager.close_loading_dialog('Loading', 'Updating database...')
        return False
    if not turn_on_foreign_keys():
        loading_manager.close_loading_dialog('Loading', 'Updating database...')
        return False

    from Functions import Create_database as Create_db, Create_indexes
    from Functions import Alter_database as Alter_db
    if not Create_db.create_tables(db):
        logger_setup.get_logger().critical(f"Error creating database tables")
        loading_manager.close_loading_dialog('Loading', 'Updating database...')
        return False
    if not Create_indexes.create_indexes(db):
        logger_setup.get_logger().critical(f"Error creating database indexes")
        loading_manager.close_loading_dialog('Loading', 'Updating database...')
        return False
    # Drop and regenerate the generated columns
    if not Alter_db.settings_reset(db):
        logger_setup.get_logger().critical(f"Error resetting settings")
        loading_manager.close_loading_dialog('Loading', 'Updating database...')
        return False
    end_time = time.time()
    loading_manager.close_loading_dialog('Loading', 'Updating database...')
    logger_setup.get_logger().info(f"Database updated in {end_time - start_time} seconds")
    db.commit()
    return True
