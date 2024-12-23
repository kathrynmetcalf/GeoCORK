from PyQt6.QtCore import QSettings
from PyQt6.QtSql import QSqlTableModel
from Functions.Table_classes import set_table
import Functions.SQLUtils as SQLUtils


def default_settings(settings: QSettings):
    # get the default settings from the QSettings object
    if settings.value('default_settings', True):
        settings.setValue('age_unit_id', 3)
        settings.setValue('elevation_unit_id', 2)
        settings.setValue('gps_format_id', 1)
        settings.setValue('heightdepth_unit_id', 2)
        settings.setValue('spotsize_unit_id', 5)
        settings.setValue('age_error_type_id', 1)
        settings.setValue('ratio_error_type_id', 3)
        settings.setValue('reference_format', '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
        set_abbreviations(settings)

def user_settings(settings: QSettings):
    # get the user settings from the QSettings object
    pass
    # set_abbreviations(settings)


def update_settings(settings: QSettings):
    # get user input and change the values in user_settings
    pass


def set_abbreviations(settings: QSettings):
    # get the abbreviations based on ids in the QSettings object
    settings_ids_tables = SQLUtils.settings_ids_tables
    for pair in settings_ids_tables:
        id = settings.value(pair[0])
        setting_base = pair[0][:-3]
        table = pair[1]
        id_header = table[:-1] + 'ID'
        model = QSqlTableModel()
        set_table(model, table)
        model.setFilter(f'{id_header} = {id}')
        settings.setValue(f'{setting_base}_abbreviation', model.record(0).value(f'{table[:-1]}Abbreviation'))

def return_abbreviations(settings: QSettings):
    settings_ids = SQLUtils.settings_ids
    abbreviations = {}
    for setting in settings_ids:
        setting_base = setting[:-3]
        abbreviations[setting_base] = settings.value(f'{setting_base}_abbreviation')
    return abbreviations
