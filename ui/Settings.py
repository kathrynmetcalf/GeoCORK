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
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import get_headers, loading_manager
from ui.SelectColumns import SelectColumns

settings_list = [
    'default_settings', 'age_unit_id', 'age_unit_abbreviation', 'elevation_unit_id', 'elevation_unit_abbreviation',
    'gps_format_id',
    'gps_format_abbreviation', 'heightdepth_unit_id', 'heightdepth_unit_abbreviation', 'spotsize_unit_id',
    'spotsize_unit_abbreviation', 'age_error_format_id', 'age_error_format_abbreviation', 'ratio_error_format_id',
    'ratio_error_format_abbreviation', 'concordance_format_id', 'concordance_format_abbreviation', 'reference_format',
    'decimals_to_show', 'sample_view_columns', 'sample_view_freeze', 'sample_edit_columns', 'sample_edit_freeze',
    'aliquot_view_columns', 'aliquot_view_freeze', 'aliquot_edit_columns', 'aliquot_edit_freeze',
    'spot_view_columns', 'spot_view_freeze', 'spot_edit_columns', 'spot_edit_freeze',
    'upb_analysis_view_columns', 'upb_analysis_view_freeze', 'upb_analysis_edit_columns', 'upb_analysis_edit_freeze',
    'column_view_columns', 'column_view_freeze', 'column_edit_columns', 'column_edit_freeze', 'reference_view_columns',
    'reference_view_freeze', 'checkable_combobox_height_scaler',
    'checkable_combobox_width_scaler', 'font_family', 'font_size', 'table_font_size', 'debug_level', 'show_per_page',
    'autofill_best_age', 'young_fill_best_age', 'old_fill_best_age', 'best_age_cutoff'
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
    settings.setValue('default_age_unit_id', 2)  # Ma
    settings.setValue('default_age_unit_abbreviation', 'Ma')
    settings.setValue('default_elevation_unit_id', 2)  # m
    settings.setValue('default_elevation_unit_abbreviation', 'm')
    settings.setValue('default_gps_format_id', 1)  # DD +/-
    settings.setValue('default_gps_format_abbreviation', 'DD +/-')
    settings.setValue('default_heightdepth_unit_id', 2)  # m
    settings.setValue('default_heightdepth_unit_abbreviation', 'm')
    settings.setValue('default_spotsize_unit_id', 5)  # µm
    settings.setValue('default_spotsize_unit_abbreviation', 'µm')
    settings.setValue('default_age_error_format_id', 1)  # 1 sigma abs
    settings.setValue('default_age_error_format_abbreviation', '1σ abs')
    settings.setValue('default_ratio_error_format_id', 3)  # 1 sigma %
    settings.setValue('default_ratio_error_format_abbreviation', '1σ %')
    settings.setValue('default_concordance_format_id', 2)  # Con%
    settings.setValue('default_concordance_format_abbreviation', 'Con%')
    # Reference format settings, sets to "Authors, Year, Source"
    settings.setValue('default_reference_format',
                      '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
    settings.setValue('default_decimals_to_show', 2)

    # Column display settings
    settings.setValue('default_sample_view_columns', [
        'SampleID', 'SampleName', 'SampleIGSN', 'SampleDescription', 'GPSSampleLocationCalculated',
        'SampleElevationCalculated', 'SampleAgeCalculated', 'SampleAgeConstraintName', 'SampleAgeInterpretationName',
        'SampleAgeReferenceDisplay', 'ColumnName', 'ColumnHeightDepthCalculated', 'SampleAgeSignatureName',
        'RegionName', 'RockTypeName', 'SampleContextName', 'SamplingMethodName', 'SettingName', 'UnitName',
        'AliquotName', 'AliquotContextName', 'SpotCount', 'SpotCompositionName', 'SpotContextName',
        '"Accepted/TotalUPbAnalyses"', 'LabFacilityName', 'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation',
        'AgeUnitAbbreviation', 'AgeErrorFormatAbbreviation', 'ConcordanceFormatAbbreviation', 'CalculatedSpotSize',
        'RejectionReasonName', 'UPbAnalysisContextName', 'UPbAgeInterpretationName', 'UPbReference', 'SampleCreated',
        'SampleModified'
    ])

    settings.setValue('default_sample_edit_columns', [
        'SampleID', 'SampleName', 'SampleIGSN', 'SampleDescription', 'SampleGPSLocationDisplay', 'SampleElevation',
        'SampleElevationUnitAbbreviation', 'SampleAgeCalculated', 'SampleAgeConstraintName',
        'SampleAgeInterpretationName', 'SampleAgeReferenceDisplay', 'ColumnName', 'ColumnHeightDepth',
        'ColumnHeightDepthUnitAbbreviation','SampleAgeSignatureName', 'RegionName', 'RockTypeName', 'SampleContextName',
        'SamplingMethodName', 'SettingName', 'UnitName', 'AliquotName', 'AliquotContextName', 'SpotCount',
        'SpotCompositionName', 'SpotContextName', '"Accepted/TotalUPbAnalyses"', 'LabFacilityName',
        'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation', 'AgeUnitAbbreviation', 'AgeErrorFormatAbbreviation',
        'ConcordanceFormatAbbreviation', 'SpotSize', 'SpotSizeUnitAbbreviation', 'RejectionReasonName', 'UPbReference',
        'UPbAnalysisContextName', 'UPbAgeInterpretationName', 'SampleCreated', 'SampleModified'
    ])

    settings.setValue('default_aliquot_view_columns', [
        'AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'SampleID', 'SampleName',
        'AliquotContextName', 'SpotCount', 'SpotCompositionName', 'SpotContextName', '"Accepted/TotalUPbAnalyses"',
        'LabFacilityName', 'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation', 'AgeUnitAbbreviation',
        'AgeErrorFormatAbbreviation', 'ConcordanceFormatAbbreviation', 'CalculatedSpotSize', 'RejectionReasonName',
        'UPbAnalysisContextName', 'UPbAgeInterpretationName', 'UPbReference', 'AliquotCreated', 'AliquotModified'
    ])

    settings.setValue('default_aliquot_edit_columns', [
        'AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'SampleID', 'SampleName',
        'AliquotContextName', 'AliquotCreated', 'AliquotModified'
    ])

    settings.setValue('default_spot_view_columns', [
        'SpotID', 'AliquotID', 'SampleID', 'SpotName', 'AliquotName', 'SampleName', 'SpotCompositionName',
        'SpotContextName', 'LabFacilityName', 'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation',
        'AgeUnitAbbreviation', 'AgeErrorFormatAbbreviation', 'ConcordanceFormatAbbreviation', 'CalculatedSpotSize',
        'Rejected', 'UPbAnalysisContextName', 'UPbAgeInterpretationName', 'RejectionReasonName', 'UPbReference',
        'SpotCreated', 'SpotModified'
    ])

    settings.setValue('default_spot_edit_columns', [
        'SpotID', 'AliquotID', 'SampleID', 'SpotName', 'AliquotName', 'SampleName', 'SpotCompositionName',
        'SpotContextName', 'SpotCreated', 'SpotModified'
    ])

    settings.setValue('default_upb_analysis_view_columns', [
        'UPbAnalysisID', 'SpotID', 'AliquotID', 'SampleID', 'SpotName', 'AliquotName', 'SampleName', 'UPbReference',
        'LabFacilityName', 'InstrumentName', 'UPbAnalysisMethodName', '"Pb204cps"', '"Pb206cps"', '"Pb207cps"',
        '"Pb208cps"',
        '"Pb*cps"', '"Th232cps"', '"U235cps"', '"U238cps"', '"Uppm"', '"Thppm"', '"CalculatedU/Th"', '"CalculatedTh/U"',
        '"Calculated206Pb/207Pb"', '"Calculated206Pb/207PbError"', '"Calculated207Pb/206Pb"',
        '"Calculated207Pb/206PbError"',
        '"Calculated207Pb/235U"', '"Calculated207Pb/235UError"', '"Calculated235U/207Pb"',
        '"Calculated235U/207PbError"',
        '"Calculated206Pb/238U"', '"Calculated206Pb/238UError"', '"Calculated238U/206Pb"',
        '"Calculated238U/206PbError"',
        '"Calculated208Pb/232Th"', '"Calculated208Pb/232ThError"', '"Calculated232Th/208Pb"',
        '"Calculated232Th/208PbError"',
        '"Calculated238U/232Th"', '"Calculated238U/232ThError"', '"Calculated232Th/238U"',
        '"Calculated232Th/238UError"',
        '"Calculated204Pb/238U"', '"Calculated204Pb/238UError"', '"Calculated238U/204Pb"',
        '"Calculated238U/204PbError"',
        '"Calculated206Pb/204Pb"', '"Calculated206Pb/204PbError"', '"Calculated204Pb/206Pb"',
        '"Calculated204Pb/206PbError"',
        '"Calculated207Pb/204Pb"', '"Calculated207Pb/204PbError"', '"Calculated204Pb/207Pb"',
        '"Calculated204Pb/207PbError"',
        '"Calculated208Pb/204Pb"', '"Calculated208Pb/204PbError"', '"Calculated204Pb/208Pb"',
        '"Calculated204Pb/208PbError"',
        '"ErrorCorr/Rho"', '"Calculated207Pb/206PbAge"', '"Calculated207Pb/206PbAgeError"', '"Calculated206Pb/238UAge"',
        '"Calculated206Pb/238UAgeError"', '"Calculated207Pb/235UAge"', '"Calculated207Pb/235UAgeError"',
        '"Calculated208Pb/232ThAge"', '"Calculated208Pb/232ThAgeError"', '"CalculatedBestAgeFilled"',
        '"CalculatedBestAgeErrorFilled"',
        '"CalculatedSpotSize"', '"CalculatedConcordance"', 'Rejected', 'RejectionReasonName', 'UPbAnalysisContextName',
        'UPbAgeInterpretationName', 'UPbAnalysisCreated', 'UPbAnalysisModified'
    ])

    settings.setValue('default_upb_analysis_edit_columns', [
        'UPbAnalysisID', 'SpotID', 'AliquotID', 'SampleID', 'SpotName', 'AliquotName', 'SampleName', 'UPbReference',
        'LabFacilityName', 'InstrumentName', 'UPbAnalysisMethodName', '"Pb204cps"', '"Pb206cps"', '"Pb207cps"',
        '"Pb208cps"',
        '"Pb*cps"', '"Th232cps"', '"U235cps"', '"U238cps"', '"Uppm"', '"Thppm"', '"U/Th"', '"Th/U"',
        '"206Pb/207Pb"', '"206Pb/207PbError"', '"207Pb/206Pb"', '"207Pb/206PbError"',
        '"207Pb/235U"', '"207Pb/235UError"', '"235U/207Pb"', '"235U/207PbError"',
        '"206Pb/238U"', '"206Pb/238UError"', '"238U/206Pb"', '"238U/206PbError"',
        '"208Pb/232Th"', '"208Pb/232ThError"', '"232Th/208Pb"', '"232Th/208PbError"',
        '"238U/232Th"', '"238U/232ThError"', '"232Th/238U"', '"232Th/238UError"',
        '"204Pb/238U"', '"204Pb/238UError"', '"238U/204Pb"', '"238U/204PbError"',
        '"206Pb/204Pb"', '"206Pb/204PbError"', '"204Pb/206Pb"', '"204Pb/206PbError"',
        '"207Pb/204Pb"', '"207Pb/204PbError"', '"204Pb/207Pb"', '"204Pb/207PbError"',
        '"208Pb/204Pb"', '"208Pb/204PbError"', '"204Pb/208Pb"', '"204Pb/208PbError"',
        '"204Pb/208PbError"', 'RatioErrorFormatAbbreviation', '"ErrorCorr/Rho"',
        '"207Pb/206PbAge"', '"207Pb/206PbAgeError"', '"207Pb/235UAge"', '"207Pb/235UAgeError"',
        '"206Pb/238UAge"', '"206Pb/238UAgeError"', '"208Pb/232ThAge"', '"208Pb/232ThAgeError"',
        '"BestAge"', '"BestAgeError"', '"BestAgeFilled"', '"BestAgeErrorFilled"',
        'AgeUnitAbbreviation', 'AgeErrorFormatAbbreviation', '"Concordance"', 'ConcordanceFormatAbbreviation',
        '"SpotSize"', 'SpotSizeUnitAbbreviation', 'Rejected', 'RejectionReasonName', 'UPbAnalysisContextName',
        'UPbAgeInterpretationName', 'UPbAnalysisCreated', 'UPbAnalysisModified'
    ])

    settings.setValue('default_column_view_columns', [
        'ColumnID', 'ColumnName', 'ColumnTotalHeightDepthCalculated', 'ColumnGPSLocationCalculated',
        'ColumnElevationCalculated', 'ColumnDescription', 'ColumnCreated', 'ColumnModified'
    ])

    settings.setValue('default_column_edit_columns', [
        'ColumnID', 'ColumnName', 'ColumnTotalHeightDepth', 'ColumnTotalHeightDepthUnitAbbreviation',
        'ColumnGPSLocationDisplay', 'ColumnElevation', 'ColumnElevationUnitAbbreviation', 'ColumnDescription',
        'ColumnCreated', 'ColumnModified'
    ])

    settings.setValue('default_reference_view_columns', [
        'ReferenceID', 'ReferenceDisplay', 'Authors', 'Year', 'Title', 'Source', 'DOI', 'ReferenceDescription',
        'ReferenceCreated', 'ReferenceModified'
    ])

    settings.setValue('default_checkable_combobox_height_scaler', 1.0)
    settings.setValue('default_checkable_combobox_width_scaler', 1.0)

    settings.setValue('default_debug_level', 'INFO')
    settings.setValue('default_show_per_page', 100)

    settings.setValue('default_autofill_best_age', 'true')
    settings.setValue('default_young_fill_best_age', '"206Pb/238UAge"')
    settings.setValue('default_old_fill_best_age', '"207Pb/206PbAge"')
    settings.setValue('default_best_age_cutoff', 1000)

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

        self.loading_manager = LoadingDialogManager.get_instance()

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

        self.autofill_best_checkBox.checkStateChanged.connect(self.populate_best_age_fields)

        self.authors_pushButton.clicked.connect(self.add_reference_element)
        self.year_pushButton.clicked.connect(self.add_reference_element)
        self.title_pushButton.clicked.connect(self.add_reference_element)
        self.source_pushButton.clicked.connect(self.add_reference_element)
        self.doi_pushButton.clicked.connect(self.add_reference_element)

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
        self.set_combobox(self.gps_format_comboBox, self.gps_format_model)
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
        self.db_name_lineEdit.setText(self.about_db_model.record(0).value('Name'))
        self.db_authors_lineEdit.setText(self.about_db_model.record(0).value('Authors'))
        self.db_description_lineEdit.setText(self.about_db_model.record(0).value('Description'))
        self.db_reference_link_lineEdit.setText(self.about_db_model.record(0).value('ReferenceLink'))
        self.db_created_by_lineEdit.setText(self.about_db_model.record(0).value('CreatedBy'))
        self.db_reference_lineEdit.setText(self.about_db_model.record(0).value('Citation'))
        self.geocork_version_text.setText(self.about_db_model.record(0).value('Version'))

        self.select_columns.populate_stack()

        self.combobox_height_scaler_spinbox.setValue(float(settings.value('checkable_combobox_height_scaler')))
        self.combobox_width_scaler_spinbox.setValue(float(settings.value('checkable_combobox_width_scaler')))

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

    def update_settings(self):
        """
        Updates the settings to current values within the various comboboxes and lineedits. Updates the database
        with new values of the About table.
        """
        # No longer using default settings
        logger_setup.get_logger().info('Updating settings')
        self.loading_manager.show_loading_dialog('Updating', 'Updating settings...')
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

        self.combobox_height_scaler_spinbox: QDoubleSpinBox
        update_setting('checkable_combobox_height_scaler', self.combobox_height_scaler_spinbox.value())
        update_setting('checkable_combobox_width_scaler', self.combobox_width_scaler_spinbox.value())

        update_setting('font_size', float(self.font_size_comboBox.currentText()))
        update_setting('table_font_size', float(self.table_font_size_comboBox.currentText()))
        update_setting('font_family', self.fontComboBox.currentFont().family())

        update_stylesheet()

        self.populate_fields()
        self.loading_manager.close_loading_dialog('Updating', 'Updating settings...')
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
        self.loading_manager.show_loading_dialog('Restoring Default Settings', 'Currently updating settings...')
        logger_setup.get_logger().info('Restoring default settings')
        settings.setValue('default_settings', 'true')
        reset_to_default_settings()
        self.populate_fields()
        self.loading_manager.close_loading_dialog('Restoring Default Settings', 'Currently updating settings...')

    def set_combobox(self, comboBox: QtW.QComboBox, model: QSqlQueryModel):
        """
        Sets the combobox to the current value of the setting. This is called when the settings dialog is opened.
        :param QComboBox comboBox: combobox to set
        :param QSqlQueryModel model: model to the value from
        """
        table, column, id_header, setting_key = self.variables_from_combobox(comboBox)

        model.setQuery(f'SELECT {column} FROM {table} WHERE {id_header} = {settings.value(setting_key)}')
        if model.rowCount() == 0:
            comboBox.setCurrentIndex(0)
        else:
            current_value = model.record(0).value(column)
            model.setQuery(f'SELECT {column} FROM {table} ORDER BY {id_header}')
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
