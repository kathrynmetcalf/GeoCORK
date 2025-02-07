import Functions.Database_views as DB_views
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

    # Check if the database exists and all tables are present
    Create_db.create_tables()
    Create_indexes.create_indexes()
    # Need to drop views before dropping and regenerating generated columns
    DB_views.drop_all_views()
    # Drop and regenerate the generated columns
    Alter_db.settings_reset()
    create_view_begin = time.time()
    print("Creating views")
    # Recreate the views
    DB_views.create_all_views()
    create_view_end = time.time()
    print(f"Create views time: {create_view_end - create_view_begin}")

