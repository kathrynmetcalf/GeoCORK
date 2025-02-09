from PyQt6.QtSql import QSqlDatabase, QSqlTableModel

import Functions.Database_views as DB_views
import logger_setup
from Functions import Create_database as Create_db, Create_indexes
from Functions import Alter_database as Alter_db
from Functions.Settings_manager import settings
import time

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
    if not db.close():
        if 'no transaction is active' not in db.lastError().text():
            logger_setup.get_logger().critical(f"Error closing database: {db.lastError().text()}")
    if not db.open():
        logger_setup.get_logger().critical(f"Error opening database: {db.lastError().text()}")

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

