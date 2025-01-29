from ui.Settings import default_settings
import Functions.Database_views as DB_views
from Functions import Create_database as Create_db
from Functions import Alter_database as Alter_db
from Functions.Settings_manager import settings

def update_database():
    Create_db.create_tables()
    DB_views.drop_all_views()
    if bool(settings.value('default_settings')) is True:
        default_settings()
    Alter_db.settings_reset()

