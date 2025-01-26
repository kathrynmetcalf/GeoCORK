from PyQt6.QtSql import QSqlTableModel, QSqlQuery
from Functions.Settings_manager import settings


def default_settings():
    # get the default settings from the QSettings object
    if settings.value('default_settings') is True:
        # Database settings
        settings.setValue('db_name', 'untitled')
        settings.setValue('db_author', 'unknown')
        settings.setValue('db_description', '')
        settings.setValue('db_source_link', '')

        # Display settings, figure out how to get the default QApplication font
        # settings.setValue('font_family',)
        # settings.setValue('font_size')
        # settings.setValue('table_font_size')

        # Unit and Format settings
        settings.setValue('age_unit_id', 2)
        settings.setValue('elevation_unit_id', 8)
        settings.setValue('gps_format_id', 7)
        settings.setValue('heightdepth_unit_id', 2)
        settings.setValue('spotsize_unit_id', 5)
        settings.setValue('age_error_format_id', 1)
        settings.setValue('ratio_error_format_id', 3)
        settings.setValue('reference_format', '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
        settings.setValue('decimals_to_show', 2)
        set_abbreviations()

        # Column display settings
        settings.setValue('column_view_columns', [0, 1, 2, 3, 4, 5, 6])
        settings.setValue('column_edit_view_columns', [0, 1, 2, 3, 4, 5, 6, 7])
        settings.setValue('sample_view_columns', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34])


def update_setting(key, value):
    # pass the key to update and user input, then change the value in settings
    settings.setValue(key, value)
    if settings.default_settings is True:
        settings.setValue('default_settings', False)

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

settings_tables = ['AgeUnits', 'DistanceUnits', 'GPSFormats', 'ErrorFormats', 'ConcordanceFormats']
settings_ids = ['age_unit_id', 'elevation_unit_id', 'gps_format_id', 'heightdepth_unit_id', 'spotsize_unit_id',
                'age_error_format_id', 'ratio_error_format_id', 'concordance_format_id']
settings_ids_tables = [['age_unit_id', 'AgeUnits'], ['elevation_unit_id', 'DistanceUnits'],
                       ['gps_format_id', 'GPSFormats'], ['heightdepth_unit_id', 'DistanceUnits'],
                       ['spotsize_unit_id', 'DistanceUnits'], ['age_error_format_id', 'ErrorFormats'],
                       ['ratio_error_format_id', 'ErrorFormats'], ['concordance_format_id', 'ConcordanceFormats']]