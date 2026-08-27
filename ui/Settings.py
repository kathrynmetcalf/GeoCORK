import os
import re
import sys

from PyQt6 import QtWidgets as QtW, QtCore
from PyQt6.QtCore import QPoint, QSize, QStandardPaths, QRegularExpression
from PyQt6.QtGui import QFont, QFontDatabase, QDesktopServices, QRegularExpressionValidator, QAction
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery
from PyQt6.QtWidgets import QDoubleSpinBox
from PyQt6.uic import loadUi

import logger_setup
import Functions.SQLUtils as SQLUtils
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import get_headers, show_loading_dialog, close_loading_dialog, populate_combo_box
from ui.SelectColumns import SelectColumns

settings_list = [
    'default_settings', 'age_unit_id', 'age_unit_abbreviation', 'elevation_unit_id', 'elevation_unit_abbreviation',
    'gps_format_id',
    'gps_format_abbreviation', 'heightdepth_unit_id', 'heightdepth_unit_abbreviation', 'spotsize_unit_id',
    'spotsize_unit_abbreviation', 'age_error_format_id', 'age_error_format_abbreviation', 'ratio_error_format_id',
    'ratio_error_format_abbreviation', 'concordance_format_id', 'concordance_format_abbreviation', 'reference_format',
    'geochem_error_format_id', 'geochem_error_format_abbreviation', 'decimals_to_show', 'sample_view_columns',
    'sample_edit_columns', 'aliquot_view_columns', 'aliquot_edit_columns', 'grain_view_columns', 'grain_edit_columns',
    'spot_view_columns', 'spot_edit_columns', 'upb_analysis_view_columns', 'upb_analysis_edit_columns',
    'geochem_analysis_view_columns', 'geochem_analysis_edit_columns', 'column_view_columns', 'column_edit_columns',
    'reference_view_columns', 'checkable_combobox_height_scalar', 'checkable_combobox_width_scalar', 'font_family',
    'font_size', 'table_font_size', 'debug_level', 'show_per_page', 'autofill_best_age', 'young_fill_best_age',
    'old_fill_best_age', 'best_age_cutoff', 'geocork_version', 'current_db_path', 'display_tooltips',
    'show_items_missing_data', 'display_analyses'
]
"""List of all setting keys used by GeoCORK. This list is used to check for missing settings and to reset settings to default values."""

def update_stylesheet():
    """
    Updates the stylesheet of the application based on the current settings.
    """
    # Apply the stylesheet to the active QApplication object
    app = QtW.QApplication.instance()
    set_font = QFont(settings.value('font_family'), int(settings.value('font_size')))
    app.setFont(set_font)
    # setting the font size and family, by setting to lower class QAbstractItemView
    # subclasses QTableView, QTreeView, QListView and created ones in Widget_classes.py are still affected
    app.setStyleSheet(f'''
        QAbstractItemView {{
            font-size: {settings.value('table_font_size')}pt;
        }}
        ''')


def populate_app_defaults():
    """
    Populate the application with default settings. This is called when the application starts up.
    """
    app = QtW.QApplication.instance()
    settings.setValue('default_font_family', app.font().family())
    settings.setValue('default_font_size', app.font().pointSize())
    settings.setValue('default_table_font_size', app.font().pointSize())

    # If other settings have been set, update the font and stylesheet
    if settings.value('default_settings') == 'false':
        update_stylesheet()


def default_settings():
    """
    Sets the default settings for the application. Every setting has a default variant with the prefix 'default_'.
    """
    # set the default settings values
    # Unit and Format settings
    default_dict = {'default_geocork_version': 'v1.0.5',
                    'default_age_unit_id': 2,
                    'default_age_unit_abbreviation': 'Ma',
                    'default_elevation_unit_id': 2,
                    'default_elevation_unit_abbreviation': 'm',
                    'default_gps_format_id': 1,
                    'default_gps_format_abbreviation': 'DD +/-',
                    'default_heightdepth_unit_id': 2,
                    'default_heightdepth_unit_abbreviation': 'm',
                    'default_spotsize_unit_id': 5,
                    'default_spotsize_unit_abbreviation': 'µm',
                    'default_age_error_format_id': 1,
                    'default_age_error_format_abbreviation': '1σ abs',
                    'default_ratio_error_format_id': 3,
                    'default_ratio_error_format_abbreviation': '1σ %',
                    'default_concordance_format_id': 2,
                    'default_concordance_format_abbreviation': 'Con%',
                    'default_reference_format': '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''',
                    'default_geochem_error_format_id': 1,
                    'default_geochem_error_format_abbreviation': '1σ abs',
                    'default_round_values': 'false',
                    'default_decimals_to_show': 4,
                    'default_db_file': '',
                    'default_checkable_combobox_height_scalar': 1.0,
                    'default_checkable_combobox_width_scalar': 1.0,
                    'default_debug_level': 'INFO',
                    'default_show_per_page': 100,
                    'default_autofill_best_age': 'true',
                    'default_young_fill_best_age': '"206Pb/238UAge"',
                    'default_old_fill_best_age': '"207Pb/206PbAge"',
                    'default_best_age_cutoff': 1000,
                    'default_display_tooltips': 'true',
                    'default_show_items_missing_data': 'true',
                    'default_display_analyses': ['UPbAnalyses', 'GeoChemicalAnalyses']}
    for default_key, default_value in default_dict.items():
        custom_key = default_key.split('default_')[1]
        if not settings.contains(default_key) or (settings.contains(default_key) and settings.value(default_key) != default_value):
            settings.setValue(default_key, default_value)
            settings.setValue(custom_key, default_value)
        if not settings.contains(custom_key):
            settings.setValue(custom_key, default_value)

    default_sample_view_columns = []
    sample_view_columns = SQLUtils.view_attributes_dict['SampleView']
    for column in sample_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_sample_view_columns.append(column_name)
    # Column display settings
    if (not settings.contains('default_sample_view_columns') or
            (settings.contains('default_sample_view_columns') and
            set(settings.value('default_sample_view_columns')) != set(default_sample_view_columns))):
        settings.setValue('default_sample_view_columns', default_sample_view_columns)
        settings.setValue('sample_view_columns', default_sample_view_columns)

    default_sample_edit_columns = []
    sample_edit_columns = SQLUtils.view_attributes_dict['SampleEditView']
    for column in sample_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_sample_edit_columns.append(column_name)
    if (not settings.contains('default_sample_edit_columns') or
            (settings.contains('default_sample_edit_columns') and
            set(settings.value('default_sample_edit_columns')) != set(default_sample_edit_columns))):
        settings.setValue('default_sample_edit_columns', default_sample_edit_columns)
        settings.setValue('sample_edit_columns', default_sample_edit_columns)

    default_aliquot_view_columns = []
    aliquot_view_columns = SQLUtils.view_attributes_dict['AliquotView']
    for column in aliquot_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_aliquot_view_columns.append(column_name)
    if (not settings.contains('default_aliquot_view_columns') or
            (settings.contains('default_aliquot_view_columns') and
            set(settings.value('default_aliquot_view_columns')) != set(default_aliquot_view_columns))):
        settings.setValue('default_aliquot_view_columns', default_aliquot_view_columns)
        settings.setValue('aliquot_view_columns', default_aliquot_view_columns)

    default_aliquot_edit_columns = []
    aliquot_edit_columns = SQLUtils.view_attributes_dict['AliquotEditView']
    for column in aliquot_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_aliquot_edit_columns.append(column_name)
    if (not settings.contains('default_aliquot_edit_columns') or
            (settings.contains('default_aliquot_edit_columns') and
            set(settings.value('default_aliquot_edit_columns')) != set(default_aliquot_edit_columns))):
        settings.setValue('default_aliquot_edit_columns', default_aliquot_edit_columns)
        settings.setValue('aliquot_edit_columns', default_aliquot_edit_columns)

    default_grain_view_columns = []
    grain_view_columns = SQLUtils.view_attributes_dict['GrainView']
    for column in grain_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_grain_view_columns.append(column_name)
    if (not settings.contains('default_grain_view_columns') or
            (settings.contains('default_grain_view_columns') and
             set(settings.value('default_grain_view_columns')) != set(default_grain_view_columns))):
        settings.setValue('default_grain_view_columns', default_grain_view_columns)

    default_grain_edit_columns = []
    grain_edit_columns = SQLUtils.view_attributes_dict['GrainEditView']
    for column in grain_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_grain_edit_columns.append(column_name)
    if (not settings.contains('default_grain_edit_columns') or
            (settings.contains('default_grain_edit_columns') and
            set(settings.value('default_grain_edit_columns')) != set(default_grain_edit_columns))):
        settings.setValue('default_grain_edit_columns', default_grain_edit_columns)
        settings.setValue('grain_edit_columns', default_grain_edit_columns)

    default_spot_view_columns = []
    spot_view_columns = SQLUtils.view_attributes_dict['SpotView']
    for column in spot_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_spot_view_columns.append(column_name)
    if (not settings.contains('default_spot_view_columns') or
            (settings.contains('default_spot_view_columns') and
            set(settings.value('default_spot_view_columns')) != set(default_spot_view_columns))):
        settings.setValue('default_spot_view_columns', default_spot_view_columns)

    default_spot_edit_columns = []
    spot_edit_columns = SQLUtils.view_attributes_dict['SpotEditView']
    for column in spot_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_spot_edit_columns.append(column_name)
    if (not settings.contains('default_spot_edit_columns') or
            (settings.contains('default_spot_edit_columns') and
            set(settings.value('default_spot_edit_columns')) != set(default_spot_edit_columns))):
        settings.setValue('default_spot_edit_columns', default_spot_edit_columns)
        settings.setValue('spot_edit_columns', default_spot_edit_columns)

    default_upb_analysis_view_columns = []
    upb_analysis_view_columns = SQLUtils.view_attributes_dict['UPbView']
    for column in upb_analysis_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_upb_analysis_view_columns.append(column_name)
    if (not settings.contains('default_upb_analysis_view_columns') or
            (settings.contains('default_upb_analysis_view_columns') and
            set(settings.value('default_upb_analysis_view_columns')) != set(default_upb_analysis_view_columns))):
        settings.setValue('default_upb_analysis_view_columns', default_upb_analysis_view_columns)
        settings.setValue('upb_analysis_view_columns', default_upb_analysis_view_columns)

    default_upb_analysis_edit_columns = []
    upb_analysis_edit_columns = SQLUtils.view_attributes_dict['UPbEditView']
    for column in upb_analysis_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_upb_analysis_edit_columns.append(column_name)
    if (not settings.contains('default_upb_analysis_edit_columns') or
            (settings.contains('default_upb_analysis_edit_columns') and
            set('default_upb_analysis_edit_columns') == set(default_upb_analysis_edit_columns))):
        settings.setValue('default_upb_analysis_edit_columns', default_upb_analysis_edit_columns)
        settings.setValue('upb_analysis_edit_columns', default_upb_analysis_edit_columns)

    default_geochem_analysis_view_columns = []
    geochem_analysis_view_columns = SQLUtils.view_attributes_dict['GeoChemView']
    for column in geochem_analysis_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        if 'Created' in column:
            # Retrieve all analyte abbreviations from the database and include columns for value, error, and unit
            query = QSqlQuery()
            if not query.exec(f'SELECT GeoChemAnalyteAbbreviation FROM GeoChemicalAnalytes') and 'Driver' not in query.lastError().text():
                logger_setup.get_logger().critical(f'Error fetching geochemical analytes for settings')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                continue
            if 'Driver' not in query.lastError().text():
                while query.next():
                    default_geochem_analysis_view_columns.append(query.value('GeoChemAnalyteAbbreviation'))
        default_geochem_analysis_view_columns.append(column_name)
    if (not settings.contains('default_geochem_analysis_view_columns') or
            (settings.contains('default_geochem_analysis_view_columns') and
             set(settings.value('default_geochem_analysis_view_columns')) != set(default_geochem_analysis_view_columns))):
        settings.setValue('default_geochem_analysis_view_columns', default_geochem_analysis_view_columns)
        settings.setValue('geochem_analysis_view_columns', default_geochem_analysis_view_columns)

    default_geochem_analysis_edit_columns = []
    geochem_analysis_edit_columns = SQLUtils.view_attributes_dict['GeoChemEditView']
    for column in geochem_analysis_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        if 'Created' in column:
            # Retrieve all analyte abbreviations from the database and include columns for value, error, and unit
            query = QSqlQuery()
            if not query.exec(f'SELECT GeoChemAnalyteAbbreviation FROM GeoChemicalAnalytes') and 'Driver' not in query.lastError().text():
                logger_setup.get_logger().critical(f'Error fetching geochemical analytes for settings')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                continue
            analyte_abbreviations = []
            if 'Driver' not in query.lastError().text():
                while query.next():
                    analyte_abbreviations.append(query.value('GeoChemAnalyteAbbreviation'))
                for abbreviation in analyte_abbreviations:
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}Value')
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}Error')
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}Unit')
                    default_geochem_analysis_edit_columns.append(f'{abbreviation}ErrorFormat')
        default_geochem_analysis_edit_columns.append(column_name)
    if (not settings.contains('default_geochem_analysis_edit_columns') or
            (settings.contains('default_geochem_analysis_edit_columns') and
             set('default_geochem_analysis_edit_columns') != set(default_geochem_analysis_edit_columns))):
        settings.setValue('default_geochem_analysis_edit_columns', default_geochem_analysis_edit_columns)
        settings.setValue('geochem_analysis_edit_columns', default_geochem_analysis_edit_columns)

    default_column_view_columns = []
    column_view_columns = SQLUtils.view_attributes_dict['ColumnView']
    for column in column_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_column_view_columns.append(column_name)
    if (not settings.contains('default_column_view_columns') or
            (settings.contains('default_column_view_columns') and
            set(settings.value('default_column_view_columns')) != set(default_column_view_columns))):
        settings.setValue('default_column_view_columns', default_column_view_columns)
        settings.setValue('column_view_columns', default_column_view_columns)

    default_column_edit_columns = []
    column_edit_columns = SQLUtils.view_attributes_dict['ColumnEditView']
    for column in column_edit_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_column_edit_columns.append(column_name)
    if (not settings.contains('default_column_edit_columns') or
            (settings.contains('default_column_edit_columns') and
            set(settings.value('default_column_edit_columns')) != set(default_column_edit_columns))):
        settings.setValue('default_column_edit_columns', default_column_edit_columns)
        settings.setValue('column_edit_columns', default_column_edit_columns)

    default_reference_view_columns = []
    reference_view_columns = SQLUtils.view_attributes_dict['ReferenceView']
    for column in reference_view_columns:
        if ' AS ' in column:
            column_name = column.split(' AS ')[1].strip('"')
        else:
            column_name = column.strip('"')
        default_reference_view_columns.append(column_name)
    if (not settings.contains('default_reference_view_columns') or
            (settings.contains('default_reference_view_columns') and
            set(settings.value('default_reference_view_columns')) != set(default_reference_view_columns))):
        settings.setValue('default_reference_view_columns', default_reference_view_columns)
        settings.setValue('reference_view_columns', default_reference_view_columns)

def reset_to_default_settings():
    """
    Reset the settings to utilize default_settings.
    """
    if settings.value('default_settings') == 'true':
        for setting in settings_list:
            if setting == 'default_settings':
                pass
            else:
                # Set the value of setting to default_setting, e.g. sets 'decimals_to_show' to 'default_decimals_to_show'
                # effectively resetting the setting to default, the rest of the app uses 'decimals_to_show'
                settings.setValue(setting, settings.value(f'default_{setting}'))

        # Apply the stylesheet to the active QApplication object
        update_stylesheet()


def check_missing_settings():
    """
    Check if any of the settings are missing, if so, set them to the default
    """
    for setting in settings_list:
        if settings.value(setting) is None:
            settings.setValue(setting, settings.value(f'default_{setting}'))

def update_column_settings() -> bool:
    """
    Check the current column settings against the default settings. If a column does not exist in the default settings,
    remove it. This is a column name from an older version that is no longer in use.
    :return:
    """
    from Functions import SQLUtils
    column_settings_dict = SQLUtils.view_setting_dict.copy()
    for view, column_settings in column_settings_dict.items():
        # remove any duplicates
        current_columns = list(dict.fromkeys(settings.value(column_settings)))
        default_columns = settings.value(f'default_{column_settings}')
        for column in current_columns:
            # Remove any columns that are not in the default list
            if column not in default_columns:
                try:
                    # Some columns had 'Name' appended from previous versions
                    if f'{column}Name' in default_columns:
                        index = current_columns.index(column)
                        current_columns[index] = f'{column}Name'
                    else:
                        current_columns.remove(column)
                except Exception as e:
                    logger_setup.get_logger().debug(f'Remove column error: {e}')
                    return False
        settings.setValue(column_settings, current_columns)
    return True

def update_setting(key: str, value: str):
    """
    Sets the given setting key to the given value. Sets default_settings to false if it is true, since default settings
    are no longer being utilized.
    :param str key: setting key
    :param value: setting value to set
    """
    settings.setValue(key, value)
    if settings.value('default_settings') == 'true':
        settings.setValue('default_settings', 'false')


def update_abbreviation(id_key: str) -> bool:
    """
    Update the abbreviation for the given id_key in the settings.
    :param str id_key: the id_key to update the setting to
    :return: True for success, False for failure
    :rtype: bool
    """
    # Update the abbreviations in the settings file
    model = QSqlQueryModel()
    if id_key == 'age_unit_id':
        model.setQuery(f"SELECT AgeUnitAbbreviation FROM AgeUnits WHERE AgeUnitID = {settings.value(id_key)}")
    # if id_key == 'analytical_unit_id':
    #     model.setQuery(f"SELECT AgeUnitAbbreviation FROM AgeUnits WHERE AgeUnitID = {settings.value(id_key)}")
    elif id_key == 'elevation_unit_id':
        model.setQuery(
            f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'gps_format_id':
        model.setQuery(f"SELECT GPSFormatAbbreviation FROM GPSFormats WHERE GPSFormatID = {settings.value(id_key)}")
    elif id_key == 'heightdepth_unit_id':
        model.setQuery(
            f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'spotsize_unit_id':
        model.setQuery(
            f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'age_error_format_id':
        model.setQuery(
            f"SELECT ErrorFormatAbbreviation FROM ErrorFormats WHERE ErrorFormatID = {settings.value(id_key)}")
    elif id_key == 'ratio_error_format_id':
        model.setQuery(
            f"SELECT ErrorFormatAbbreviation FROM ErrorFormats WHERE ErrorFormatID = {settings.value(id_key)}")
    elif id_key == 'concordance_format_id':
        model.setQuery(
            f"SELECT ConcordanceFormatAbbreviation FROM ConcordanceFormats WHERE ConcordanceFormatID = {settings.value(id_key)}")
    while model.canFetchMore():
        model.fetchMore()
    if model.rowCount() == 0:
        logger_setup.get_logger().critical(f"Error: No results found for {id_key}: {model.lastError().text()}")
        return False
    abbreviation_key = id_key.replace('_id', '_abbreviation')
    settings.setValue(abbreviation_key, model.record(0).value(0))
    return True


class SettingsDialog(QtW.QDialog):
    """
    SettingsDialog class allows the user to change the settings of the application. Contains other helper
    functions/buttons that could be useful for the user.
    """
    def __init__(self):
        super().__init__()
        logger_setup.get_logger().info('Opening settings dialog')

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "Settings.ui")
        loadUi(sources_ui_file, self)

        self.setWindowTitle('Settings')
        self.loadWindowState()
        self.settings_tabWidget.setCurrentIndex(0)
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
        self.select_columns = SelectColumns()
        self.column_verticalLayout.addWidget(self.select_columns)

        double_comma_double_regex = QRegularExpression(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")
        double_comma_double_validator = QRegularExpressionValidator(double_comma_double_regex)
        self.cutoff_age_lineEdit.setValidator(double_comma_double_validator)

        self.updated = False

        self.populate_fields()

        self.view_rounded_checkBox.checkStateChanged.connect(self.set_rounding)

        self.autofill_best_checkBox.checkStateChanged.connect(self.populate_best_age_fields)

        self.authors_pushButton.clicked.connect(self.add_reference_element)
        self.year_pushButton.clicked.connect(self.add_reference_element)
        self.title_pushButton.clicked.connect(self.add_reference_element)
        self.source_pushButton.clicked.connect(self.add_reference_element)
        self.doi_pushButton.clicked.connect(self.add_reference_element)

        self.upb_checkBox.stateChanged.connect(self.update_analysis_display)
        self.geochem_checkBox.stateChanged.connect(self.update_analysis_display)

        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Ok).clicked.connect(self.update_settings_close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.update_settings)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self.restore_defaults)

        self.openlogs_pushButton.clicked.connect(self.open_logs)
        self.openbackup_pushButton.clicked.connect(self.open_backups)

    def display_tab(self, index):
        self.settings_tabWidget.setCurrentIndex(index)

    def populate_fields(self):
        """
        Populates all the fields with the current settings. This is called when the settings dialog is opened.
        """
        logger_setup.get_logger().info('Populating fields with the current settings')
        decimals = [str(i) for i in range(0, 10)]
        self.decimals_comboBox.addItems(decimals)
        self.decimals_comboBox.setCurrentText(str(settings.value('decimals_to_show')))
        view_rounded = settings.value('round_values')
        if view_rounded == 'true':
            self.view_rounded_checkBox.setChecked(True)
            self.decimals_comboBox.setEnabled(True)
        else:
            self.view_rounded_checkBox.setChecked(False)
            self.decimals_comboBox.setEnabled(False)
        populate_combo_box(self.gps_format_comboBox, **{'table': 'GPSFormats', 'column': 2})
        # self.set_combobox(self.gps_format_comboBox, self.gps_format_model)
        self.gps_format_comboBox.setCurrentText(settings.value('gps_format_abbreviation'))
        self.set_combobox(self.elev_unit_comboBox, self.elevation_unit_model)
        self.elev_unit_comboBox.setCurrentText(settings.value('elevation_unit_abbreviation'))
        self.set_combobox(self.column_unit_comboBox, self.column_unit_model)
        self.column_unit_comboBox.setCurrentText(settings.value('heightdepth_unit_abbreviation'))
        self.set_combobox(self.spot_size_unit_comboBox, self.spot_size_unit_model)
        self.spot_size_unit_comboBox.setCurrentText(settings.value('spotsize_unit_abbreviation'))
        self.set_combobox(self.upb_ratio_error_format_comboBox, self.ratio_error_format_model)
        self.upb_ratio_error_format_comboBox.setCurrentText(settings.value('ratio_error_format_abbreviation'))
        self.set_combobox(self.upb_concordance_format_comboBox, self.concordance_format_model)
        self.upb_concordance_format_comboBox.setCurrentText(settings.value('concordance_format_abbreviation'))
        self.set_combobox(self.age_unit_comboBox, self.age_unit_model)
        self.age_unit_comboBox.setCurrentText(settings.value('age_unit_abbreviation'))
        self.set_combobox(self.age_error_format_comboBox, self.age_error_format_model)
        self.age_error_format_comboBox.setCurrentText(settings.value('age_error_format_abbreviation'))

        self.populate_best_age_fields()

        reference_format = settings.value('reference_format')
        # converts stored SQL code to user-friendly format
        if 'ifnull(Authors, "")' in reference_format:
            reference_format = reference_format.replace('ifnull(Authors, "")', '{Authors}')
        if 'ifnull(Year, "")' in reference_format:
            reference_format = reference_format.replace('ifnull(Year, "")', '{Year}')
        if 'ifnull(Title, "")' in reference_format:
            reference_format = reference_format.replace('ifnull(Title, "")', '{Title}')
        if 'ifnull(Source, "")' in reference_format:
            reference_format = reference_format.replace('ifnull(Source, "")', '{Source}')
        if 'ifnull(DOI, "")' in reference_format:
            reference_format = reference_format.replace('ifnull(DOI, "")', '{DOI}')
        if ' || "' in reference_format:
            reference_format = reference_format.replace(' || "', '')
        if '" || ' in reference_format:
            reference_format = reference_format.replace('" || ', '')
        if '"' in reference_format:
            reference_format = reference_format.replace('"', '')
        self.reference_display_lineEdit.setText(reference_format)

        self.about_db_model.setQuery('SELECT * FROM About WHERE AboutID = 1')
        while self.about_db_model.canFetchMore():
            self.about_db_model.fetchMore()
        self.db_name_lineEdit.setText(self.about_db_model.record(0).value('Name'))
        self.db_authors_lineEdit.setText(self.about_db_model.record(0).value('Authors'))
        self.db_description_lineEdit.setText(self.about_db_model.record(0).value('Description'))
        self.db_reference_link_lineEdit.setText(self.about_db_model.record(0).value('ReferenceLink'))
        self.db_created_by_lineEdit.setText(self.about_db_model.record(0).value('CreatedBy'))
        self.db_reference_lineEdit.setText(self.about_db_model.record(0).value('Citation'))
        self.geocork_version_text.setText(self.about_db_model.record(0).value('Version'))

        if 'UPbAnalyses' in settings.value('display_analyses'):
            self.upb_checkBox.setChecked(True)
        else:
            self.upb_checkBox.setChecked(False)
        if 'GeoChemicalAnalyses' in settings.value('display_analyses'):
            self.geochem_checkBox.setChecked(True)
        else:
            self.geochem_checkBox.setChecked(False)

        self.select_columns.populate_stack()

        self.combobox_height_scalar_spinbox.setValue(float(settings.value('checkable_combobox_height_scalar')))
        self.combobox_width_scalar_spinbox.setValue(float(settings.value('checkable_combobox_width_scalar')))

        # List of font sizes to populate the font size comboboxes
        font_sizes = [str(i) for i in range(6, 21)]
        self.font_size_comboBox.addItems(font_sizes)
        self.font_size_comboBox.setCurrentText(str(int(settings.value('font_size'))))
        self.table_font_size_comboBox.addItems(font_sizes)
        self.table_font_size_comboBox.setCurrentText(str(int(settings.value('table_font_size'))))

        # If the default font is not in the font family list, add it
        if settings.value('font_family') not in QFontDatabase.families():
            self.fontComboBox.addItems([settings.value('font_family')])
        if settings.value('default_font_family') not in QFontDatabase.families():
            self.fontComboBox.addItems([settings.value('default_font_family')])
        self.fontComboBox.setCurrentFont(QFont(settings.value('font_family')))

        # self.lazy_batch_comboBox.addItems(['100', '250', '500', '1000', '2500', '5000', '10000'])
        # self.lazy_batch_comboBox.setCurrentText(str(settings.value('lazy_loading_batch_size')))
        # if settings.value('lazy_loading_enabled') == 'true':
        #     self.lazy_checkBox.setChecked(True)
        #     self.lazy_batch_comboBox.setEnabled(True)
        # else:
        #     self.lazy_checkBox.setChecked(False)
        #     self.lazy_batch_comboBox.setEnabled(False)

        self.display_tooltips_checkBox.setChecked(settings.value('display_tooltips', type=bool))

    def update_analysis_display(self):
        display_analyses = settings.value('display_analyses')
        if self.upb_checkBox.isChecked() and 'UPbAnalyses' not in display_analyses:
            display_analyses.append('UPbAnalyses')
        elif not self.upb_checkBox.isChecked() and 'UPbAnalyses' in display_analyses:
            display_analyses.remove('UPbAnalyses')
        if self.geochem_checkBox.isChecked() and 'GeoChemicalAnalyses' not in display_analyses:
            display_analyses.append('GeoChemicalAnalyses')
        elif not self.geochem_checkBox.isChecked() and 'GeoChemicalAnalyses' in display_analyses:
            display_analyses.remove('GeoChemicalAnalyses')
        if display_analyses != settings.value('display_analyses'):
            settings.setValue('display_analyses', display_analyses)

    def populate_best_age_fields(self):
        if settings.value('autofill_best_age') == 'true':
            self.autofill_best_checkBox.setChecked(True)
            self.young_age_fill_comboBox.setEnabled(True)
            self.old_age_fill_comboBox.setEnabled(True)
            self.cutoff_age_lineEdit.setEnabled(True)
            self.young_age_fill_comboBox.clear()
            self.old_age_fill_comboBox.clear()
            self.cutoff_age_lineEdit.setText(str(settings.value('best_age_cutoff')))
            upb_headers = get_headers('UPbAnalyses')
            for header in upb_headers:
                if ('Age' in header and
                        'Calculated' not in header and
                        'Filled' not in header and
                        'Error' not in header and
                        'ID' not in header and
                        'BestAge' not in header):
                    self.young_age_fill_comboBox.addItem(header.replace('"', ''))
                    self.old_age_fill_comboBox.addItem(header.replace('"', ''))
            self.young_age_fill_comboBox.setCurrentText(settings.value('young_fill_best_age').replace('"', ''))
            self.old_age_fill_comboBox.setCurrentText(settings.value('old_fill_best_age').replace('"', ''))
        else:
            self.autofill_best_checkBox.setChecked(False)
            self.young_age_fill_comboBox.clear()
            self.old_age_fill_comboBox.clear()
            self.cutoff_age_lineEdit.setText('')
            self.young_age_fill_comboBox.setEnabled(False)
            self.old_age_fill_comboBox.setEnabled(False)
            self.cutoff_age_lineEdit.setEnabled(False)

    def set_rounding(self):
        if self.view_rounded_checkBox.isChecked():
            settings.setValue('round_values', 'true')
            self.decimals_comboBox.setEnabled(True)
        else:
            settings.setValue('round_values', 'false')
            self.decimals_comboBox.setEnabled(False)

    def update_settings(self):
        """
        Updates the settings to current values within the various comboboxes and lineedits. Updates the database
        with new values of the About table.
        """
        # No longer using default settings
        logger_setup.get_logger().info('Updating settings')
        show_loading_dialog('Updating', 'Updating settings...')
        settings.setValue('default_settings', 'false')

        # Save the settings to the QSettings object
        # Do not assume that the index is the same as the ID
        settings.setValue('decimals_to_show', int(self.decimals_comboBox.currentText()))
        self.update_from_combobox(self.gps_format_comboBox, self.gps_format_model)
        self.update_from_combobox(self.elev_unit_comboBox, self.elevation_unit_model)
        self.update_from_combobox(self.column_unit_comboBox, self.column_unit_model)
        self.update_from_combobox(self.spot_size_unit_comboBox, self.spot_size_unit_model)
        self.update_from_combobox(self.age_unit_comboBox, self.age_unit_model)
        self.update_from_combobox(self.age_error_format_comboBox, self.age_error_format_model)
        self.update_from_combobox(self.upb_ratio_error_format_comboBox, self.ratio_error_format_model)
        self.update_from_combobox(self.upb_concordance_format_comboBox, self.concordance_format_model)

        if self.autofill_best_checkBox.isChecked():
            settings.setValue('autofill_best_age', 'true')
            settings.setValue('young_fill_best_age', self.young_age_fill_comboBox.currentText())
            settings.setValue('old_fill_best_age', self.old_age_fill_comboBox.currentText())
            try: best_age_cutoff = int(self.cutoff_age_lineEdit.text())
            except ValueError:
                try: best_age_cutoff = float(self.cutoff_age_lineEdit.text())
                except ValueError:
                    logger_setup.get_logger().error('Cutoff must be a number')
                    return
            settings.setValue('best_age_cutoff', best_age_cutoff)
        else:
            settings.setValue('autofill_best_age', 'false')

        settings.setValue('reference_format', self.update_reference_format())

        about_values = [self.db_name_lineEdit.text(), self.db_authors_lineEdit.text(),
                        self.db_description_lineEdit.text(), self.db_reference_link_lineEdit.text(),
                        self.db_created_by_lineEdit.text(), self.db_reference_lineEdit.text()]
        query = QSqlQuery()
        about_qry = f"""UPDATE About SET (Name, Authors, Description, ReferenceLink, CreatedBy, Citation) = 
            ({', '.join('?'*len(about_values))}) WHERE AboutID = 1"""
        query.prepare(about_qry)
        for value in about_values:
            query.addBindValue(value)
        if not query.exec():
            logger_setup.get_logger().critical(f'Error updating About table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')

        self.select_columns.save_list_states()

        # Style sheet related values
        self.combobox_height_scalar_spinbox: QDoubleSpinBox
        style_settings = {'checkable_combobox_height_scalar': self.combobox_height_scalar_spinbox.value(),
                          'checkable_combobox_width_scalar': self.combobox_width_scalar_spinbox.value(),
                          'font_size': float(self.font_size_comboBox.currentText()),
                          'table_font_size': float(self.table_font_size_comboBox.currentText()),
                          'font_family': self.fontComboBox.currentFont().family()}
        # Updating the style sheet takes time, so only do it if necessary
        for key, value in style_settings.items():
            if settings.value(key) != value:
                update_setting('checkable_combobox_height_scalar', self.combobox_height_scalar_spinbox.value())
                update_setting('checkable_combobox_width_scalar', self.combobox_width_scalar_spinbox.value())

                update_setting('font_size', float(self.font_size_comboBox.currentText()))
                update_setting('table_font_size', float(self.table_font_size_comboBox.currentText()))
                update_setting('font_family', self.fontComboBox.currentFont().family())

                show_loading_dialog('Updating', 'Updating style...')
                update_stylesheet()
                close_loading_dialog('Updating', 'Updating style...')
                break

        # if self.lazy_checkBox.isChecked():
        #     update_setting('lazy_loading_enabled', 'true')
        #     update_setting('lazy_loading_batch_size', int(self.lazy_batch_comboBox.currentText()))
        # else:
        #     update_setting('lazy_loading_enabled', 'false')
        #
        # update_setting('display_tooltips', self.display_tooltips_checkBox.isChecked())

        self.populate_fields()
        close_loading_dialog('Updating', 'Updating settings...')
        logger_setup.get_logger().info('Updated settings successfully')
        self.updated = True


    def update_settings_close(self):
            """
            Updates the settings and closes the dialog.
            """
            self.update_settings()
            self.close()

    def restore_defaults(self):
        """
        Restores the default settings for the application. This is called when the user clicks the Restore Defaults
        """
        show_loading_dialog('Restoring Default Settings', 'Currently updating settings...')
        logger_setup.get_logger().info('Restoring default settings')
        settings.setValue('default_settings', 'true')
        reset_to_default_settings()
        self.populate_fields()
        close_loading_dialog('Restoring Default Settings', 'Currently updating settings...')

    def set_combobox(self, comboBox: QtW.QComboBox, model: QSqlQueryModel):
        """
        Sets the combobox to the current value of the setting. This is called when the settings dialog is opened.
        :param QComboBox comboBox: combobox to set
        :param QSqlQueryModel model: model to the value from
        """
        table, column, id_header, setting_key = self.variables_from_combobox(comboBox)

        model.setQuery(f'SELECT {column} FROM {table} WHERE {id_header} = {settings.value(setting_key)}')
        while model.canFetchMore():
            model.fetchMore()
        if model.rowCount() == 0:
            comboBox.setCurrentIndex(0)
        else:
            current_value = model.record(0).value(column)
            model.setQuery(f'SELECT {column} FROM {table} ORDER BY {id_header}')
            while model.canFetchMore():
                model.fetchMore()
            comboBox.setModel(model)
            comboBox.setCurrentText(current_value)

    def update_from_combobox(self, comboBox: QtW.QComboBox, model: QSqlQueryModel):
        """
        Updates the settings to the value from the
        :param QComboBox comboBox: combobox to get value from
        :param QSqlQueryModel model:
        :return:
        """
        table, column, id_header, setting_key = self.variables_from_combobox(comboBox)

        selected_text = comboBox.currentText()
        model.setQuery(f'SELECT {id_header} FROM {table} WHERE {column} = "{selected_text}"')
        while model.canFetchMore():
            model.fetchMore()
        if model.rowCount() == 1:
            update_setting(setting_key, model.record(0).value(id_header))
            update_abbreviation(setting_key)

    def variables_from_combobox(self, comboBox: QtW.QComboBox):
        """
        Returns the table, column, id_header and setting_key for the given combobox.
        :param QComboBox comboBox:
        :return:
        """
        if comboBox.objectName() == 'gps_format_comboBox':
            table = 'GPSFormats'
            column = 'GPSFormatAbbreviation'
            id_header = 'GPSFormatID'
            setting_key = 'gps_format_id'
        elif comboBox.objectName() in ['elev_unit_comboBox', 'column_unit_comboBox', 'spot_size_unit_comboBox']:
            table = 'DistanceUnits'
            column = 'DistanceUnitAbbreviation'
            id_header = 'DistanceUnitID'
            if comboBox.objectName() == 'elev_unit_comboBox':
                setting_key = 'elevation_unit_id'
            elif comboBox.objectName() == 'column_unit_comboBox':
                setting_key = 'heightdepth_unit_id'
            elif comboBox.objectName() == 'spot_size_unit_comboBox':
                setting_key = 'spotsize_unit_id'
        elif comboBox.objectName() == 'age_unit_comboBox':
            table = 'AgeUnits'
            column = 'AgeUnitAbbreviation'
            id_header = 'AgeUnitID'
            setting_key = 'age_unit_id'
        elif comboBox.objectName() in ['age_error_format_comboBox', 'upb_ratio_error_format_comboBox']:
            table = 'ErrorFormats'
            column = 'ErrorFormatAbbreviation'
            id_header = 'ErrorFormatID'
            if comboBox.objectName() == 'age_error_format_comboBox':
                setting_key = 'age_error_format_id'
            elif comboBox.objectName() == 'upb_ratio_error_format_comboBox':
                setting_key = 'ratio_error_format_id'
        elif comboBox.objectName() == 'upb_concordance_format_comboBox':
            table = 'ConcordanceFormats'
            column = 'ConcordanceFormatAbbreviation'
            id_header = 'ConcordanceFormatID'
            setting_key = 'concordance_format_id'
        else:
            return
        return table, column, id_header, setting_key

    def add_reference_element(self):
        """
        Add the selected reference element to the reference format lineEdit at the current cursor position
        :return:
        """
        button = self.sender()
        if button.objectName() == 'authors_pushButton':
            text = '{Authors}'
        elif button.objectName() == 'year_pushButton':
            text = '{Year}'
        elif button.objectName() == 'title_pushButton':
            text = '{Title}'
        elif button.objectName() == 'source_pushButton':
            text = '{Source}'
        elif button.objectName() == 'doi_pushButton':
            text = '{DOI}'
        else:
            return
        self.reference_display_lineEdit.insert(text)

    def update_reference_format(self):
        """
        Updates the reference format, converts from user-friendly format to SQL format.
        :return:
        """
        import re

        def format_reference_sql(raw_text: str) -> str:
            # Define replacements
            replacements = {
                '{Authors}': 'ifnull(Authors, "")',
                '{Year}': 'ifnull(Year, "")',
                '{Title}': 'ifnull(Title, "")',
                '{Source}': 'ifnull(Source, "")',
                '{DOI}': 'ifnull(DOI, "")',
            }

            # Split into segments of {tokens} or literal text
            parts = re.split(r'(\{[^{}]+\})', raw_text)

            formatted_parts = []

            for part in parts:
                if part.startswith('{') and part.endswith('}'):
                    formatted_parts.append(replacements.get(part, ''))
                elif part.strip() != '':
                    # Escape double quotes and wrap static text in quotes
                    escaped = part.replace('"', '""')  # escape double quotes in SQL
                    formatted_parts.append(f'"{escaped}"')

            # Join all parts with SQL concatenation operator
            return ' || '.join(p for p in formatted_parts if p)

        # Usage
        reference_format = self.reference_display_lineEdit.text()
        return format_reference_sql(reference_format)

    def open_logs(self):
        """
        Opens the logs directory in the file explorer.
        """
        dirname = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) + f"/logs/"
        QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(dirname))

    def open_backups(self):
        """
        Opens the backups directory in the file explorer.
        """
        dirname = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation) + f"/backups/"
        QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(dirname))

    def close(self):
        self.saveWindowState()
        return super().close()

    def saveWindowState(self):
        settings.setValue("ui/SettingDialog/pos", self.pos())
        # settings.setValue("ui/SettingDialog/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/SettingDialog/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/SettingDialog/size", defaultValue=QSize(810, 569)))
