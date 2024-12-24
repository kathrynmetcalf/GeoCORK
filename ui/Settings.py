from PyQt6.QtSql import QSqlTableModel
from Functions.Settings_manager import settings


def default_settings():
    # get the default settings from the QSettings object
    if settings.value('default_settings') is True:
        settings.setValue('age_unit_id', 2)
        settings.setValue('elevation_unit_id', 8)
        settings.setValue('gps_format_id', 1)
        settings.setValue('heightdepth_unit_id', 2)
        settings.setValue('spotsize_unit_id', 5)
        settings.setValue('age_error_type_id', 1)
        settings.setValue('ratio_error_type_id', 3)
        settings.setValue('reference_format', '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
        settings.setValue('decimals_to_show', 2)
        set_abbreviations()

def user_settings():
    # get the user settings from the QSettings object
    pass
    # set_abbreviations(settings)


def update_settings():
    # get user input and change the values in user_settings
    pass


def set_abbreviations():
    # get the abbreviations based on ids in the QSettings object
    for pair in settings_ids_tables:
        id = settings.value(pair[0])
        setting_base = pair[0][:-3]
        table = pair[1]
        id_header = table[:-1] + 'ID'
        model = QSqlTableModel()
        model.setTable(table)
        model.setFilter(f'{id_header} = {id}')
        model.select()
        settings.setValue(f'{setting_base}_abbreviation', model.record(0).value(f'{table[:-1]}Abbreviation'))

def return_abbreviations():
    abbreviations = {}
    for setting in settings_ids:
        setting_base = setting[:-3]
        abbreviations[setting_base] = settings.value(f'{setting_base}_abbreviation')
    return abbreviations

settings_tables = ['AgeUnits', 'DistanceUnits', 'GPSFormats', 'ErrorTypes']
settings_ids = ['age_unit_id', 'elevation_unit_id', 'gps_format_id', 'heightdepth_unit_id', 'spotsize_unit_id',
                'age_error_type_id', 'ratio_error_type_id']
settings_ids_tables = [['age_unit_id', 'AgeUnits'], ['elevation_unit_id', 'DistanceUnits'],
                       ['gps_format_id', 'GPSFormats'], ['heightdepth_unit_id', 'DistanceUnits'],
                       ['spotsize_unit_id', 'DistanceUnits'], ['age_error_type_id', 'ErrorTypes'],
                       ['ratio_error_type_id', 'ErrorTypes']]