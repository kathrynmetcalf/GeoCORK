from PyQt6.uic import loadUi
from PyQt6.QtSql import QSqlTableModel, QSqlQueryModel, QSqlQuery
from PyQt6 import QtWidgets as QtW
from Functions.Settings_manager import settings


def default_settings():
    # get the default settings from the QSettings object
    if bool(settings.value('default_settings')) is True:
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
        settings.setValue('age_unit_id', 4)
        settings.setValue('elevation_unit_id', 8)
        settings.setValue('gps_format_id', 7)
        settings.setValue('heightdepth_unit_id', 2)
        settings.setValue('spotsize_unit_id', 5)
        settings.setValue('age_error_format_id', 1)
        settings.setValue('ratio_error_format_id', 3)
        settings.setValue('concordance_format_id', 2)
        settings.setValue('reference_format', '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
        settings.setValue('decimals_to_show', 2)
        set_abbreviations()

        # Column display settings
        settings.setValue('column_view_columns', [])
        settings.setValue('column_edit_view_columns', [])
        settings.setValue('sample_view_columns', [])
        settings.setValue('aliquot_columns', [])
        settings.setValue('spot_columns', [])
        settings.setValue('upb_analysis_columns', [])
        settings.setValue('upb_analysis_edit_columns', [])

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

class SettingsDialog(QtW.QDialog):
    def __init__(self):
        super().__init__()
        settings_ui_file = "ui/Settings.ui"
        loadUi(settings_ui_file, self)
        self.setWindowTitle('Settings')

        self.gps_format_model = QSqlQueryModel()
        self.elevation_unit_model = QSqlQueryModel()
        self.column_unit_model = QSqlQueryModel()
        self.spot_size_unit_model = QSqlQueryModel()
        self.age_unit_model = QSqlQueryModel()
        self.age_error_format_model = QSqlQueryModel()
        self.ratio_error_format_model = QSqlQueryModel()
        self.concordance_format_model = QSqlQueryModel()
        self.table_columns_model = QSqlQueryModel()
        self.about_db_model = QSqlQueryModel()

        self.populate_fields()

    def populate_fields(self):
        abbreviations = return_abbreviations()

        self.gps_format_model.setQuery('SELECT GPSFormatAbbreviation FROM GPSFormats')
        self.gps_format_comboBox.setModel(self.gps_format_model)
        self.gps_format_comboBox.setCurrentText(abbreviations['gps_format'])

        self.elevation_unit_model.setQuery('SELECT DistanceUnitAbbreviation FROM DistanceUnits')
        self.elev_unit_comboBox.setModel(self.elevation_unit_model)
        self.elev_unit_comboBox.setCurrentText(abbreviations['elevation_unit'])

        self.column_unit_model.setQuery('SELECT DistanceUnitAbbreviation FROM DistanceUnits')
        self.column_unit_comboBox.setModel(self.column_unit_model)
        self.column_unit_comboBox.setCurrentText(abbreviations['heightdepth_unit'])

        self.spot_size_unit_model.setQuery('SELECT DistanceUnitAbbreviation FROM DistanceUnits')
        self.spot_size_unit_comboBox.setModel(self.spot_size_unit_model)
        self.spot_size_unit_comboBox.setCurrentText(abbreviations['spotsize_unit'])

        self.age_unit_model.setQuery('SELECT AgeUnitAbbreviation FROM AgeUnits')
        self.age_unit_comboBox.setModel(self.age_unit_model)
        self.age_unit_comboBox.setCurrentText(abbreviations['age_unit'])

        self.age_error_format_model.setQuery('SELECT ErrorFormatAbbreviation FROM ErrorFormats')
        self.age_error_format_comboBox.setModel(self.age_error_format_model)
        self.age_error_format_comboBox.setCurrentText(abbreviations['age_error_format'])

        self.ratio_error_format_model.setQuery('SELECT ErrorFormatAbbreviation FROM ErrorFormats')
        self.upb_ratio_error_format_comboBox.setModel(self.ratio_error_format_model)
        self.upb_ratio_error_format_comboBox.setCurrentText(abbreviations['ratio_error_format'])

        self.concordance_format_model.setQuery('SELECT ConcordanceFormatAbbreviation FROM ConcordanceFormats')
        self.upb_concordance_format_comboBox.setModel(self.concordance_format_model)
        self.upb_concordance_format_comboBox.setCurrentText(abbreviations['concordance_format'])