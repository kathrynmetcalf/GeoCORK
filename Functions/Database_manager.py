from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery

import Functions.Database_views as DB_views
import logger_setup
from Functions.Settings_manager import settings
import time

def turn_on_foreign_keys(pyqt_connection: str='default'):
    """
    Turn on foreign keys for the database connection
    :param pyqt_connection: Name of the PyQt connection to use, default is 'default'
    :return: True or False
    """
    query = QSqlQuery(pyqt_connection)
    if not query.exec('PRAGMA foreign_keys=ON'):
        logger_setup.get_logger().critical(f'Could not turn on foreign keys: {query.lastError().text()}')
        return False
    if not query.exec('PRAGMA foreign_keys'):
        logger_setup.get_logger().critical(f'Could not check foreign keys: {query.lastError().text()}')
        return False
    if query.next():
        if query.value(0) == 1:
            logger_setup.get_logger().info('Foreign keys are on')
            return True
        else:
            logger_setup.get_logger().critical('Failed to re-enable foreign keys')
            return False

def turn_off_foreign_keys(pyqt_connection: str='default'):
    """
    Turn off foreign keys for the database connection
    :param pyqt_connection: Name of the PyQt connection to use, default is 'default'
    :return: True or False
    """
    query = QSqlQuery(pyqt_connection)
    if not query.exec('PRAGMA foreign_keys=OFF'):
        logger_setup.get_logger().critical(f'Could not turn off foreign keys: {query.lastError().text()}')
        return False
    if not query.exec('PRAGMA foreign_keys'):
        logger_setup.get_logger().critical(f'Could not check foreign keys: {query.lastError().text()}')
        return False
    if query.next():
        if query.value(0) == 0:
            logger_setup.get_logger().info('Foreign keys are off')
            return True
        else:
            logger_setup.get_logger().critical('Failed to disable foreign keys')
            return False

def update_database():
    """
    Run this on startup and when settings are changed.
    The database has generated columns that set display values based on units and formats in settings. These need to be
    updated if the settings are changed. This function will drop and recreate the generated columns.
    Uses the default connection established with the database file in GeoCORKMain.py
    """
    start_time = time.time()
    logger_setup.get_logger().info("Updating database")
    # Check if the database exists and all tables are present
    model = QSqlTableModel()
    db = model.database()
    if not db.commit():
        if 'no transaction is active' not in db.lastError().text():
            logger_setup.get_logger().critical(f"Error committing database: {db.lastError().text()}")
            return
    if not db.close():
        if 'no transaction is active' not in db.lastError().text():
            logger_setup.get_logger().critical(f"Error closing database: {db.lastError().text()}")
            return
    if not db.open():
        logger_setup.get_logger().critical(f"Error opening database: {db.lastError().text()}")
        return
    if not turn_on_foreign_keys():
        return

    from Functions import Create_database as Create_db, Create_indexes
    from Functions import Alter_database as Alter_db
    Create_db.create_tables()
    Create_indexes.create_indexes()
    # Need to drop views before dropping and regenerating generated columns
    DB_views.drop_all_views()
    # Drop and regenerate the generated columns
    Alter_db.settings_reset()
    # Recreate the views
    DB_views.create_all_views()

    end_time = time.time()
    logger_setup.get_logger().info(f"Database updated in {end_time - start_time} seconds")

