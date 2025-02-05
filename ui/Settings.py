import sys

from PyQt6.QtCore import QSettings, QPoint, QSize
from PyQt6.QtWidgets import QDoubleSpinBox
from PyQt6.uic import loadUi
from PyQt6.QtSql import QSqlTableModel, QSqlQueryModel, QSqlQuery
from PyQt6 import QtWidgets as QtW
from PyQt6.QtGui import QFont, QFontDatabase

from Functions.Settings_manager import settings
from ui.SelectColumns import SelectColumns

settings_list = [
    'default_settings', 'age_unit_id', 'age_unit_abbreviation', 'elevation_unit_id', 'elevation_unit_abbreviation', 'gps_format_id',
    'gps_format_abbreviation', 'heightdepth_unit_id', 'heightdepth_unit_abbreviation', 'spotsize_unit_id',
    'spotsize_unit_abbreviation', 'age_error_format_id', 'age_error_format_abbreviation', 'ratio_error_format_id',
    'ratio_error_format_abbreviation', 'concordance_format_id', 'concordance_format_abbreviation', 'reference_format',
    'decimals_to_show', 'sample_view_columns', 'sample_edit_columns', 'aliquot_view_columns', 'aliquot_edit_columns',
    'spot_view_columns', 'spot_edit_columns', 'upb_analysis_view_columns', 'upb_analysis_edit_columns',
    'column_view_columns', 'column_edit_columns', 'checkable_combobox_height_scaler', 'checkable_combobox_width_scaler',
    'font_family', 'font_size', 'table_font_size'
]

def populate_app_defaults():
    app = QtW.QApplication.instance()
    settings.setValue('default_font_family', app.font().family())
    settings.setValue('default_font_size', app.font().pointSize())
    settings.setValue('default_table_font_size', app.font().pointSize())

    # If other settings have been set, update the font and stylesheet
    if settings.value('default_settings') == 'false':
        app.setFont(QFont(f'{settings.value('font_family')}, {settings.value('font_size')}'))
        app.setStyleSheet(f'''
                QTableView {{
                    font-size: {settings.value('table_font_size')}pt;
                }}
                QTreeView {{
                    font-size: {settings.value('table_font_size')}pt;
                }}
                ''')

def default_settings():
    # set the default settings values
    # Unit and Format settings
    settings.setValue('default_age_unit_id', 2) # Ma
    settings.setValue('default_age_unit_abbreviation', 'Ma')
    settings.setValue('default_elevation_unit_id', 2) # m
    settings.setValue('default_elevation_unit_abbreviation', 'm')
    settings.setValue('default_gps_format_id', 1) # DD +/-
    settings.setValue('default_gps_format_abbreviation', 'DD +/-' )
    settings.setValue('default_heightdepth_unit_id', 2) # m
    settings.setValue('default_heightdepth_unit_abbreviation', 'm')
    settings.setValue('default_spotsize_unit_id', 5) # µm
    settings.setValue('default_spotsize_unit_abbreviation', 'µm')
    settings.setValue('default_age_error_format_id', 1) # 1 sigma abs
    settings.setValue('default_age_error_format_abbreviation', '1σ abs')
    settings.setValue('default_ratio_error_format_id', 3) # 1 sigma %
    settings.setValue('default_ratio_error_format_abbreviation', '1σ %')
    settings.setValue('default_concordance_format_id', 2) # Con%
    settings.setValue('default_concordance_format_abbreviation', 'Con%')
    settings.setValue('default_reference_format', '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
    settings.setValue('default_decimals_to_show', 2)

    # Column display settings
    settings.setValue('default_sample_view_columns', [
        'Samples.SampleID', 'Samples.SampleIGSN', 'Samples.SampleName', 'Samples.SampleDescription',
        'GPSLocations.GPSLocationConverted', 'GPSLocations.CalculatedGPSElev || "±" || GPSLocations.CalculatedGPSElevError',
        'SampleAges.SampleAgeDisplay', 'GROUP_CONCAT(DISTINCT AgeConstraintName)', 'GROUP_CONCAT(DISTINCT AgeInterpretationName)',
        'GROUP_CONCAT(DISTINCT AgeReferences.ReferenceDisplay)', 'Columns.ColumnName', 'Samples.CalculatedHeightDepth || "±" || Samples.CalculatedHeightDepthError',
        'GROUP_CONCAT(DISTINCT AgeSignatureName)', 'GROUP_CONCAT(DISTINCT RegionName)', 'GROUP_CONCAT(DISTINCT RockTypeName)',
        'GROUP_CONCAT(DISTINCT SampleContextName)', 'GROUP_CONCAT(DISTINCT SamplingMethodName)', 'GROUP_CONCAT(DISTINCT SettingName)',
        'GROUP_CONCAT(DISTINCT UnitName)', 'GROUP_CONCAT(DISTINCT AliquotName)', 'GROUP_CONCAT(DISTINCT AliquotContextName)',
        'COUNT(DISTINCT Spots.SpotID)', 'GROUP_CONCAT(DISTINCT SpotCompositionName)', 'GROUP_CONCAT(DISTINCT SpotContextName)',
        'SUM(CASE WHEN Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID)',
        'GROUP_CONCAT(DISTINCT LabFacilityName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)',
        'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)',
        'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)',
        'GROUP_CONCAT(DISTINCT CalculatedSpotSize)', 'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)',
        'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)', 'Samples.SampleCreated', 'Samples.SampleModified'
    ])
    settings.setValue('default_sample_edit_columns', [
        'Samples.SampleID', 'Samples.SampleIGSN', 'Samples.SampleName', 'Samples.SampleDescription', 'GPSLocations.GPSLocationDisplay',
        'GPSLocations.GPSElev || "±" || GPSLocations.GPSElevError', 'SampleElevationUnits.DistanceUnitAbbreviation',
        'SampleAges.SampleAgeDisplay', 'GROUP_CONCAT(DISTINCT AgeConstraintName)', 'GROUP_CONCAT(DISTINCT AgeInterpretationName)',
        'GROUP_CONCAT(DISTINCT AgeReferences.ReferenceDisplay)', 'Columns.ColumnName',
        'Samples.HeightDepth || "±" || Samples.HeightDepthError', 'ColumnHeightDepthUnits.DistanceUnitAbbreviation',
        'GROUP_CONCAT(DISTINCT AgeSignatureName)', 'GROUP_CONCAT(DISTINCT RegionName)', 'GROUP_CONCAT(DISTINCT RockTypeName)',
        'GROUP_CONCAT(DISTINCT SampleContextName)', 'GROUP_CONCAT(DISTINCT SamplingMethodName)', 'GROUP_CONCAT(DISTINCT SettingName)',
        'GROUP_CONCAT(DISTINCT UnitName)', 'GROUP_CONCAT(DISTINCT AliquotName)', 'GROUP_CONCAT(DISTINCT AliquotContextName)',
        'COUNT(DISTINCT Spots.SpotID)', 'GROUP_CONCAT(DISTINCT SpotCompositionName)', 'GROUP_CONCAT(DISTINCT SpotContextName)',
        'SUM(CASE WHEN Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID)',
        'GROUP_CONCAT(DISTINCT LabFacilityName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)',
        'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)',
        'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)',
        'GROUP_CONCAT(DISTINCT CalculatedSpotSize)', 'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)',
        'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)', 'Samples.SampleCreated', 'Samples.SampleModified'
    ])
    settings.setValue('default_aliquot_view_columns', [
        'Aliquots.AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'Samples.SampleID', 'Samples.SampleName',
        'GROUP_CONCAT(DISTINCT AliquotContextName)', 'COUNT(DISTINCT Spots.SpotID)', 'GROUP_CONCAT(DISTINCT SpotCompositionName)',
        'GROUP_CONCAT(DISTINCT SpotContextName)', 'SUM(CASE WHEN Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID)',
        'GROUP_CONCAT(DISTINCT LabFacilityName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)', 'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)',
        'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)', 'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)',
        'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT CalculatedSpotSize)',
        'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)', 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)',
        'AliquotCreated', 'AliquotModified'
    ])
    settings.setValue('default_aliquot_edit_columns', [
        'Aliquots.AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'Samples.SampleID', 'Samples.SampleName',
        'GROUP_CONCAT(DISTINCT AliquotContextName)', 'AliquotCreated', 'AliquotModified'
    ])
    settings.setValue('default_spot_view_columns', [
        'Spots.SpotID', 'Samples.SampleID', 'Aliquots.AliquotID', 'GROUP_CONCAT(DISTINCT SpotName)', 'Samples.SampleName',
        'AliquotName', 'GROUP_CONCAT(DISTINCT SpotCompositionName)', 'GROUP_CONCAT(DISTINCT SpotContextName)',
        'GROUP_CONCAT(DISTINCT LabFacilityName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)',
        'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)',
        'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)',
        'GROUP_CONCAT(DISTINCT CalculatedSpotSize)', 'CASE WHEN UPbAnalyses.Rejected = 1 THEN "Rejected" ELSE "Accepted" END',
        'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)', 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)',
        'SpotCreated', 'SpotModified'
    ])
    settings.setValue('default_spot_edit_columns', [
        'Spots.SpotID', 'Samples.SampleID', 'Aliquots.AliquotID', 'GROUP_CONCAT(DISTINCT SpotName)', 'Samples.SampleName', 'AliquotName',
        'GROUP_CONCAT(DISTINCT SpotCompositionName)', 'GROUP_CONCAT(DISTINCT SpotContextName)', 'SpotCreated', 'SpotModified'
    ])
    settings.setValue('default_upb_analysis_view_columns', [
        'UPbAnalyses.UPbAnalysisID', 'Samples.SampleID', 'Aliquots.AliquotID', 'Spots.SpotID', 'SpotName', 'AliquotName',
        'Samples.SampleName', 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)', 'GROUP_CONCAT(DISTINCT LabFacilityName)',
        'GROUP_CONCAT(DISTINCT InstrumentName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)',
        'UPbAnalyses."Pb204cps"', 'UPbAnalyses."Pb206cps"', 'UPbAnalyses."Pb207cps"', 'UPbAnalyses."Pb208cps"',
        'UPbAnalyses."Pb*cps"', 'UPbAnalyses."Th232cps"', 'UPbAnalyses."U235cps"', 'UPbAnalyses."U238cps"',
        'UPbAnalyses."Uppm"', 'UPbAnalyses."Thppm"', 'UPbAnalyses."CalculatedU/Th"', 'UPbAnalyses."CalculatedTh/U"',
        'UPbAnalyses."Calculated206Pb/207Pb"', 'UPbAnalyses."Calculated206Pb/207PbError"',
        'UPbAnalyses."Calculated207Pb/206Pb"', 'UPbAnalyses."Calculated207Pb/206PbError"',
        'UPbAnalyses."Calculated207Pb/235U"', 'UPbAnalyses."Calculated207Pb/235UError"',
        'UPbAnalyses."Calculated235U/207Pb"', 'UPbAnalyses."Calculated235U/207PbError"',
        'UPbAnalyses."Calculated206Pb/238U"', 'UPbAnalyses."Calculated206Pb/238UError"',
        'UPbAnalyses."Calculated238U/206Pb"', 'UPbAnalyses."Calculated238U/206PbError"',
        'UPbAnalyses."Calculated208Pb/232Th"', 'UPbAnalyses."Calculated208Pb/232ThError"',
        'UPbAnalyses."Calculated232Th/208Pb"', 'UPbAnalyses."Calculated232Th/208PbError"',
        'UPbAnalyses."Calculated238U/232Th"', 'UPbAnalyses."Calculated238U/232ThError"',
        'UPbAnalyses."Calculated232Th/238U"', 'UPbAnalyses."Calculated232Th/238UError"',
        'UPbAnalyses."Calculated204Pb/238U"', 'UPbAnalyses."Calculated204Pb/238UError"',
        'UPbAnalyses."Calculated238U/204Pb"', 'UPbAnalyses."Calculated238U/204PbError"',
        'UPbAnalyses."Calculated206Pb/204Pb"', 'UPbAnalyses."Calculated206Pb/204PbError"',
        'UPbAnalyses."Calculated204Pb/206Pb"', 'UPbAnalyses."Calculated204Pb/206PbError"',
        'UPbAnalyses."Calculated207Pb/204Pb"', 'UPbAnalyses."Calculated207Pb/204PbError"',
        'UPbAnalyses."Calculated204Pb/207Pb"', 'UPbAnalyses."Calculated204Pb/207PbError"',
        'UPbAnalyses."Calculated208Pb/204Pb"', 'UPbAnalyses."Calculated208Pb/204PbError"',
        'UPbAnalyses."Calculated204Pb/208Pb"', 'UPbAnalyses."Calculated204Pb/208PbError"', 'UPbAnalyses."ErrorCorr/Rho"',
        'UPbAnalyses."Calculated207Pb/206PbAge"', 'UPbAnalyses."Calculated207Pb/206PbAgeError"',
        'UPbAnalyses."Calculated206Pb/238UAge"', 'UPbAnalyses."Calculated206Pb/238UAgeError"',
        'UPbAnalyses."Calculated207Pb/235UAge"', 'UPbAnalyses."Calculated207Pb/235UAgeError"',
        'UPbAnalyses."Calculated208Pb/232ThAge"', 'UPbAnalyses."Calculated208Pb/232ThAgeError"',
        'UPbAnalyses."CalculatedBestAge"', 'UPbAnalyses."CalculatedBestAgeError"', 'UPbAnalyses."CalculatedSpotSize"',
        'UPbAnalyses."CalculatedConcordance"', 'CASE WHEN UPbAnalyses.Rejected = 1 THEN "Rejected" ELSE "Accepted" END',
        'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)',
        'UPbAnalysisCreated', 'UPbAnalysisModified'
    ])
    settings.setValue('default_upb_analysis_edit_columns', [
        'UPbAnalyses.UPbAnalysisID', 'Samples.SampleID', 'Aliquots.AliquotID', 'Spots.SpotID', 'SpotName', 'AliquotName',
        'Samples.SampleName', 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)', 'GROUP_CONCAT(DISTINCT LabFacilityName)',
        'GROUP_CONCAT(DISTINCT InstrumentName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)',
        'UPbAnalyses."Pb204cps"', 'UPbAnalyses."Pb206cps"', 'UPbAnalyses."Pb207cps"', 'UPbAnalyses."Pb208cps"',
        'UPbAnalyses."Pb*cps"', 'UPbAnalyses."Th232cps"', 'UPbAnalyses."U235cps"', 'UPbAnalyses."U238cps"',
        'UPbAnalyses."Uppm"', 'UPbAnalyses."Thppm"', 'UPbAnalyses."U/Th"', 'UPbAnalyses."Th/U"',
        'UPbAnalyses."206Pb/207Pb"', 'UPbAnalyses."206Pb/207PbError"', 'UPbAnalyses."207Pb/206Pb"', 'UPbAnalyses."207Pb/206PbError"',
        'UPbAnalyses."207Pb/235U"', 'UPbAnalyses."207Pb/235UError"', 'UPbAnalyses."235U/207Pb"', 'UPbAnalyses."235U/207PbError"',
        'UPbAnalyses."206Pb/238U"', 'UPbAnalyses."206Pb/238UError"', 'UPbAnalyses."238U/206Pb"', 'UPbAnalyses."238U/206PbError"',
        'UPbAnalyses."208Pb/232Th"', 'UPbAnalyses."208Pb/232ThError"', 'UPbAnalyses."232Th/208Pb"', 'UPbAnalyses."232Th/208PbError"',
        'UPbAnalyses."238U/232Th"', 'UPbAnalyses."238U/232ThError"', 'UPbAnalyses."232Th/238U"', 'UPbAnalyses."232Th/238UError"',
        'UPbAnalyses."204Pb/238U"', 'UPbAnalyses."204Pb/238UError"', 'UPbAnalyses."238U/204Pb"', 'UPbAnalyses."238U/204PbError"',
        'UPbAnalyses."206Pb/204Pb"', 'UPbAnalyses."206Pb/204PbError"', 'UPbAnalyses."204Pb/206Pb"', 'UPbAnalyses."204Pb/206PbError"',
        'UPbAnalyses."207Pb/204Pb"', 'UPbAnalyses."207Pb/204PbError"', 'UPbAnalyses."204Pb/207Pb"', 'UPbAnalyses."204Pb/207PbError"',
        'UPbAnalyses."208Pb/204Pb"', 'UPbAnalyses."208Pb/204PbError"', 'UPbAnalyses."204Pb/208Pb"', 'UPbAnalyses."204Pb/208PbError"',
        'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)', 'UPbAnalyses."ErrorCorr/Rho"',
        'UPbAnalyses."207Pb/206PbAge"', 'UPbAnalyses."207Pb/206PbAgeError"', 'UPbAnalyses."207Pb/235UAge"', 'UPbAnalyses."207Pb/235UAgeError"',
        'UPbAnalyses."206Pb/238UAge"', 'UPbAnalyses."206Pb/238UAgeError"', 'UPbAnalyses."208Pb/232ThAge"', 'UPbAnalyses."208Pb/232ThAgeError"',
        'UPbAnalyses."BestAge"', 'UPbAnalyses."BestAgeError"', 'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)',
        'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)', 'UPbAnalyses."Concordance"',
        'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)', 'UPbAnalyses."SpotSize"', 'GROUP_CONCAT(DISTINCT SpotSizeUnit.DistanceUnitAbbreviation)',
        'CASE WHEN UPbAnalyses.Rejected = 1 THEN "Rejected" ELSE "Accepted" END', 'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)',
        'UPbAnalysisCreated', 'UPbAnalysisModified'
    ])
    settings.setValue('default_column_view_columns', [
        'Columns.ColumnID', 'Columns.ColumnName', 'Columns.CalculatedColumnTotalHeightDepth', 'ColumnGPS.GPSLocationConverted',
        'ColumnGPS.CalculatedGPSElev || "±" || ColumnGPS.CalculatedGPSElevError', 'ColumnDescription', 'ColumnCreated', 'ColumnModified'
    ])
    settings.setValue('default_column_edit_columns', [
        'Columns.ColumnID', 'Columns.ColumnName', 'Columns.ColumnTotalHeightDepth', 'ColumnUnits.DistanceUnitAbbreviation',
        'ColumnGPS.GPSLocationDisplay', 'ColumnGPS.GPSElev || "±" || ColumnGPS.GPSElevError', 'ColumnElevationUnits.DistanceUnitAbbreviation',
        'ColumnDescription', 'ColumnCreated', 'ColumnModified'
    ])

    settings.setValue('default_checkable_combobox_height_scaler', 1.0)
    settings.setValue('default_checkable_combobox_width_scaler', 1.0)

def reset_to_default_settings():
    # get the default settings from the QSettings object
    if settings.value('default_settings') == 'true':
        for setting in settings_list:
            settings.setValue(setting, settings.value(f'default_{setting}'))

        # Apply the stylesheet to the active QApplication object
        app = QtW.QApplication.instance()
        app.setFont(QFont(settings.value('default_font_family'), settings.value('default_font_size')))
        app.setStyleSheet(f'''
            QTableView {{
                font-size: {settings.value('default_table_font_size')}pt;
            }}
            QTreeView {{
                font-size: {settings.value('default_table_font_size')}pt;
            }}
            ''')

def check_missing_settings():
    # Check if any of the settings are missing, if so, set them to the default
    for setting in settings_list:
        if settings.value(setting) is None:
            settings.setValue(setting, settings.value(f'default_{setting}'))

def update_setting(key, value):
    # pass the key to update and user input, then change the value in settings
    settings.setValue(key, value)
    if settings.value('default_settings') == 'true':
        settings.setValue('default_settings', 'false')

def update_abbreviation(id_key: str):
    # Update the abbreviations in the settings file
    model = QSqlQueryModel()
    if id_key == 'age_unit_id':
        model.setQuery(f"SELECT AgeUnitAbbreviation FROM AgeUnits WHERE AgeUnitID = {settings.value(id_key)}")
    elif id_key == 'elevation_unit_id':
        model.setQuery(f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'gps_format_id':
        model.setQuery(f"SELECT GPSFormatAbbreviation FROM GPSFormats WHERE GPSFormatID = {settings.value(id_key)}")
    elif id_key == 'heightdepth_unit_id':
        model.setQuery(f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'spotsize_unit_id':
        model.setQuery(f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {settings.value(id_key)}")
    elif id_key == 'age_error_format_id':
        model.setQuery(f"SELECT ErrorFormatAbbreviation FROM ErrorFormats WHERE ErrorFormatID = {settings.value(id_key)}")
    elif id_key == 'ratio_error_format_id':
        model.setQuery(f"SELECT ErrorFormatAbbreviation FROM ErrorFormats WHERE ErrorFormatID = {settings.value(id_key)}")
    elif id_key == 'concordance_format_id':
        model.setQuery(f"SELECT ConcordanceFormatAbbreviation FROM ConcordanceFormats WHERE ConcordanceFormatID = {settings.value(id_key)}")

    if model.rowCount() == 0:
        print(f"Error: No results found for {id_key}")
        print(f"{model.lastError().text()}")
        return False
    abbreviation_key = id_key.replace('_id', '_abbreviation')
    settings.setValue(abbreviation_key, model.record(0).value(0))
    return True



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
        self.loadWindowState()

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

        self.populate_fields()

        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Ok).clicked.connect(self.update_settings_close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.update_settings)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)

    def display_tab(self, index):
        self.settings_tabWidget.setCurrentIndex(index)

    def populate_fields(self):

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
        self.set_combobox(self.age_unit_comboBox, self.age_unit_model)
        self.age_unit_comboBox.setCurrentText(settings.value('age_unit_abbreviation'))
        self.set_combobox(self.age_error_format_comboBox, self.age_error_format_model)
        self.age_error_format_comboBox.setCurrentText(settings.value('age_error_format_abbreviation'))
        self.set_combobox(self.upb_ratio_error_format_comboBox, self.ratio_error_format_model)
        self.upb_ratio_error_format_comboBox.setCurrentText(settings.value('ratio_error_format_abbreviation'))
        self.set_combobox(self.upb_concordance_format_comboBox, self.concordance_format_model)
        self.upb_concordance_format_comboBox.setCurrentText(settings.value('concordance_format_abbreviation'))

        self.about_db_model.setQuery('SELECT * FROM About')
        self.db_name_lineEdit.setText(self.about_db_model.record(0).value('Name'))
        self.db_authors_lineEdit.setText(self.about_db_model.record(0).value('Authors'))
        self.db_description_lineEdit.setText(self.about_db_model.record(0).value('Description'))
        self.db_reference_link_lineEdit.setText(self.about_db_model.record(0).value('ReferenceLink'))
        self.db_created_by_lineEdit.setText(self.about_db_model.record(0).value('CreatedBy'))
        self.db_reference_lineEdit.setText(self.about_db_model.record(0).value('Citation'))

        self.combobox_height_scaler_spinbox.setValue(float(settings.value('checkable_combobox_height_scaler')))
        print(float(settings.value('checkable_combobox_height_scaler')))
        self.combobox_width_scaler_spinbox.setValue(float(settings.value('checkable_combobox_width_scaler')))

        # List of font sizes to populate the font size comboboxes
        font_sizes = [str(i) for i in range(6, 21)]
        self.font_size_comboBox.addItems(font_sizes)
        self.font_size_comboBox.setCurrentText(str(settings.value('font_size')))
        self.table_font_size_comboBox.addItems(font_sizes)
        self.table_font_size_comboBox.setCurrentText(str(settings.value('table_font_size')))
        # If the default font is not in the font family list, add it
        if settings.value('font_family') not in QFontDatabase.families():
            self.fontComboBox.addItems([settings.value('font_family')])
        if settings.value('default_font_family') not in QFontDatabase.families():
            self.fontComboBox.addItems([settings.value('default_font_family')])
        self.fontComboBox.setCurrentFont(QFont(settings.value('font_family')))

    # def

    def update_settings(self):
        # No longer using default settings
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

        query = QSqlQuery()
        query.prepare('''UPDATE About SET (Name, Authors, Description, Citation, CreatedBy, Citation) = (?, ?, ?, ?, ?, ?)
                            WHERE AboutID = 1''' )
        query.bindValue(0, self.db_name_lineEdit.text())
        query.bindValue(1, self.db_authors_lineEdit.text())
        query.bindValue(2, self.db_description_lineEdit.text())
        query.bindValue(3, self.db_reference_link_lineEdit.text())
        query.bindValue(4, self.db_created_by_lineEdit.text())
        query.bindValue(5, self.db_reference_lineEdit.text())
        if not query.exec():
            print(query.lastError().text())

        self.select_columns.save_list_states()

        self.combobox_height_scaler_spinbox: QDoubleSpinBox
        update_setting('checkable_combobox_height_scaler', self.combobox_height_scaler_spinbox.value())
        update_setting('checkable_combobox_width_scaler', self.combobox_width_scaler_spinbox.value())


        update_setting('font_size', self.font_size_comboBox.currentText())
        update_setting('table_font_size', self.table_font_size_comboBox.currentText())
        update_setting('font_family', self.fontComboBox.currentFont().family())

        app = QtW.QApplication.instance()
        new_font = QFont(self.fontComboBox.currentFont().family(), int(self.font_size_comboBox.currentText()))
        app.setFont(new_font)
        app.setStyleSheet(f'''
            QTableView {{
                font-size: {self.table_font_size_comboBox.currentText()}pt;
            }}
            QTreeView {{
                font-size: {self.table_font_size_comboBox.currentText()}pt;
            }}
            ''')

        self.populate_fields()

    def update_settings_close(self):
        self.update_settings()
        self.close()

    def restore_defaults(self):
        settings.setValue('default_settings', 'true')
        reset_to_default_settings()
        self.populate_fields()

    def set_combobox(self, comboBox: QtW.QComboBox, model: QSqlQueryModel):
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
        table, column, id_header, setting_key = self.variables_from_combobox(comboBox)

        selected_text = comboBox.currentText()
        model.setQuery(f'SELECT {id_header} FROM {table} WHERE {column} = "{selected_text}"')
        if model.rowCount() == 1:
            update_setting(setting_key, model.record(0).value(id_header))
            update_abbreviation(setting_key)

    def variables_from_combobox(self, comboBox: QtW.QComboBox):
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

    def close(self):
        self.saveWindowState()
        return super().close()

    def saveWindowState(self):
        settings.setValue("ui/SettingDialog/pos", self.pos())
        # settings.setValue("ui/SettingDialog/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/SettingDialog/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/SettingDialog/size", defaultValue=QSize(810, 569)))