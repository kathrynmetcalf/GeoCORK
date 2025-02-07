import sys
import re
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
        'SampleID', 'SampleIGSN', 'SampleName', 'SampleDescription', 'GPSSampleLocationCalculated',
        'SampleElevationCalculated', 'SampleAgeCalculated', 'SampleAgeConstraint', 'SampleAgeInterpretation',
        'SampleAgeReference', 'ColumnName', 'ColumnHeightDepthCalculated', 'SampleAgeSignature', 'RegionName',
        'RockTypeName', 'SampleContextName', 'SamplingMethodName', 'SettingName', 'UnitName', 'AliquotName',
        'AliquotContextName', 'SpotCount', 'SpotCompositionName', 'SpotContextName', '"Accepted/TotalUPbAnalayses"',
        'LabFacilityName', 'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation', 'AgeUnitAbbreviation',
        'AgeErrorFormatAbbreviation', 'ConcordanceFormatAbbreviation', 'CalculatedSpotSize', 'RejectionReasonName',
        'UPbReference', 'SampleCreated', 'SampleModified'
    ])
    settings.setValue('default_sample_edit_columns', [
        'SampleID', 'SampleIGSN', 'SampleName', 'SampleDescription', 'SampleGPSLocationDisplay', 'SampleElevation',
        'SampleElevationUnitAbbreviation', 'SampleAgeCalculated', 'SampleAgeConstraint', 'SampleAgeInterpretation',
        'SampleAgeReference', 'ColumnName', 'ColumnHeightDepth', 'ColumnHeightDepthUnitAbbreviation',
        'SampleAgeSignature', 'RegionName', 'RockTypeName', 'SampleContextName', 'SamplingMethodName', 'SettingName',
        'UnitName', 'AliquotName', 'AliquotContextName', 'SpotCount', 'SpotCompositionName', 'SpotContextName',
        '"Accepted/TotalUPbAnalayses"', 'LabFacilityName', 'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation',
        'AgeUnitAbbreviation', 'AgeErrorFormatAbbreviation', 'ConcordanceFormatAbbreviation', 'CalculatedSpotSize',
        'RejectionReasonName', 'UPbReference', 'SampleCreated', 'SampleModified'
    ])
    settings.setValue('default_aliquot_view_columns', [
        'AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'SampleID', 'SampleName',
        'AliquotContextName', 'SpotCount', 'SpotCompositionName', 'SpotContextName', '"Accepted/TotalUPbAnalayses"',
        'LabFacilityName', 'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation', 'AgeUnitAbbreviation',
        'AgeErrorFormatAbbreviation', 'ConcordanceFormatAbbreviation', 'CalculatedSpotSize', 'RejectionReasonName',
        'UPbReference', 'AliquotCreated', 'AliquotModified'
    ])
    settings.setValue('default_aliquot_edit_columns', [
        'AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'SampleID', 'SampleName', 'AliquotContextName',
        'AliquotCreated', 'AliquotModified'
    ])
    settings.setValue('default_spot_view_columns', [
        'SpotID', 'SampleID', 'AliquotID', 'SpotName', 'SampleName', 'AliquotName', 'SpotCompositionName',
        'SpotContextName', 'LabFacilityName', 'UPbAnalysisMethodName', 'RatioErrorFormatAbbreviation',
        'AgeUnitAbbreviation', 'AgeErrorFormatAbbreviation', 'ConcordanceFormatAbbreviation', 'CalculatedSpotSize',
        'Rejected', 'RejectionReasonName', 'UPbReference', 'SpotCreated', 'SpotModified'
    ])
    settings.setValue('default_spot_edit_columns', [
        'SpotID', 'SampleID', 'AliquotID', 'SpotName', 'SampleName', 'AliquotName', 'SpotCompositionName',
        'SpotContextName', 'SpotCreated', 'SpotModified'
    ])
    settings.setValue('default_upb_analysis_view_columns', [
        '"UPbAnalysisID"', '"SampleID"', '"AliquotID"', '"SpotID"', '"SpotName"', '"AliquotName"', '"SampleName"', '"UPbReference"',
        '"LabFacilityName"', '"InstrumentName"', '"UPbAnalysisMethodName"', '"Pb204cps"', '"Pb206cps"', '"Pb207cps"', '"Pb208cps"',
        '"Pb*cps"', '"Th232cps"', '"U235cps"', '"U238cps"', '"Uppm"', '"Thppm"', '"CalculatedU/Th"', '"CalculatedTh/U"',
        '"Calculated206Pb/207Pb"', '"Calculated206Pb/207PbError"', '"Calculated207Pb/206Pb"', '"Calculated207Pb/206PbError"',
        '"Calculated207Pb/235U"', '"Calculated207Pb/235UError"', '"Calculated235U/207Pb"', '"Calculated235U/207PbError"',
        '"Calculated206Pb/238U"', '"Calculated206Pb/238UError"', '"Calculated238U/206Pb"', '"Calculated238U/206PbError"',
        '"Calculated208Pb/232Th"', '"Calculated208Pb/232ThError"', '"Calculated232Th/208Pb"', '"Calculated232Th/208PbError"',
        '"Calculated238U/232Th"', '"Calculated238U/232ThError"', '"Calculated232Th/238U"', '"Calculated232Th/238UError"',
        '"Calculated204Pb/238U"', '"Calculated204Pb/238UError"', '"Calculated238U/204Pb"', '"Calculated238U/204PbError"',
        '"Calculated206Pb/204Pb"', '"Calculated206Pb/204PbError"', '"Calculated204Pb/206Pb"', '"Calculated204Pb/206PbError"',
        '"Calculated207Pb/204Pb"', '"Calculated207Pb/204PbError"', '"Calculated204Pb/207Pb"', '"Calculated204Pb/207PbError"',
        '"Calculated208Pb/204Pb"', '"Calculated208Pb/204PbError"', '"Calculated204Pb/208Pb"', '"Calculated204Pb/208PbError"',
        '"ErrorCorr/Rho"', '"Calculated207Pb/206PbAge"', '"Calculated207Pb/206PbAgeError"', '"Calculated206Pb/238UAge"',
        '"Calculated206Pb/238UAgeError"', '"Calculated207Pb/235UAge"', '"Calculated207Pb/235UAgeError"',
        '"Calculated208Pb/232ThAge"', '"Calculated208Pb/232ThAgeError"', '"CalculatedBestAge"', '"CalculatedBestAgeError"',
        '"CalculatedSpotSize"', '"CalculatedConcordance"', '"Calculated207Pb/206PbAgeError"',
        '"Calculated207Pb/235UAgeError"', '"Calculated206Pb/238UAgeError"', '"Calculated208Pb/232ThAgeError"',
        '"CalculatedBestAgeError"', '"Calculated206Pb/207PbError"', '"Calculated207Pb/206PbError"',
        '"Calculated207Pb/235UError"', '"Calculated235U/207PbError"', '"Calculated206Pb/238UError"',
        '"Calculated238U/206PbError"', '"Calculated208Pb/232ThError"', '"Calculated232Th/208PbError"',
        '"Calculated238U/232ThError"', '"Calculated232Th/238UError"', '"Calculated204Pb/238UError"',
        '"Calculated238U/204PbError"', '"Calculated206Pb/204PbError"', '"Calculated204Pb/206PbError"',
        '"Calculated207Pb/204PbError"', '"Calculated204Pb/207PbError"', '"Calculated208Pb/204PbError"',
        '"Calculated204Pb/208PbError"', '"Rejected"', '"RejectionReasonName"', '"UPbAnalysisCreated"', '"UPbAnalysisModified"'
    ])
    settings.setValue('default_upb_analysis_edit_columns', [
        '"UPbAnalysisID"', '"SampleID"', '"AliquotID"', '"SpotID"', '"SpotName"', '"AliquotName"', '"SampleName"', '"UPbReference"',
        '"LabFacilityName"', '"InstrumentName"', '"UPbAnalysisMethodName"', '"Pb204cps"', '"Pb206cps"', '"Pb207cps"', '"Pb208cps"',
        '"Pb*cps"', '"Th232cps"', '"U235cps"', '"U238cps"', '"Uppm"', '"Thppm"', '"U/Th"', '"Th/U"', '"206Pb/207Pb"', '"206Pb/207PbError"',
        '"206Pb/207PbError"', '"207Pb/206Pb"', '"207Pb/206PbError"', '"207Pb/206PbError"', '"207Pb/235U"', '"207Pb/235UError"',
        '"207Pb/235UError"', '"235U/207Pb"', '"235U/207PbError"', '"235U/207PbError"', '"206Pb/238U"', '"206Pb/238UError"',
        '"206Pb/238UError"', '"238U/206Pb"', '"238U/206PbError"', '"238U/206PbError"', '"208Pb/232Th"', '"208Pb/232ThError"',
        '"208Pb/232ThError"', '"232Th/208Pb"', '"232Th/208PbError"', '"232Th/208PbError"', '"238U/232Th"', '"238U/232ThError"',
        '"238U/232ThError"', '"232Th/238U"', '"232Th/238UError"', '"232Th/238UError"', '"204Pb/238U"', '"204Pb/238UError"',
        '"204Pb/238UError"', '"238U/204Pb"', '"238U/204PbError"', '"238U/204PbError"', '"206Pb/204Pb"', '"206Pb/204PbError"',
        '"206Pb/204PbError"', '"204Pb/206Pb"', '"204Pb/206PbError"', '"204Pb/206PbError"', '"207Pb/204Pb"',
        '"207Pb/204PbError"', '"207Pb/204PbError"', '"204Pb/207Pb"', '"204Pb/207PbError"', '"204Pb/207PbError"',
        '"208Pb/204Pb"', '"208Pb/204PbError"', '"208Pb/204PbError"', '"204Pb/208Pb"', '"204Pb/208PbError"',
        '"204Pb/208PbError"', '"ErrorCorr/Rho"', '"207Pb/206PbAge"', '"207Pb/206PbAgeError"', '"207Pb/206PbAgeError"',
        '"207Pb/235UAge"', '"207Pb/235UAgeError"', '"207Pb/235UAgeError"', '"206Pb/238UAge"', '"206Pb/238UAgeError"',
        '"206Pb/238UAgeError"', '"208Pb/232ThAge"', '"208Pb/232ThAgeError"', '"208Pb/232ThAgeError"', '"BestAge"',
        '"BestAgeError"', '"BestAgeError"', '"Concordance"', '"SpotSize"', '"Rejected"', '"RejectionReasonName"',
        '"UPbAnalysisCreated"', '"UPbAnalysisModified"'
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

        self.authors_pushButton.clicked.connect(self.add_reference_element)
        self.year_pushButton.clicked.connect(self.add_reference_element)
        self.title_pushButton.clicked.connect(self.add_reference_element)
        self.source_pushButton.clicked.connect(self.add_reference_element)
        self.doi_pushButton.clicked.connect(self.add_reference_element)

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
        self.set_combobox(self.upb_ratio_error_format_comboBox, self.ratio_error_format_model)
        self.upb_ratio_error_format_comboBox.setCurrentText(settings.value('ratio_error_format_abbreviation'))
        self.set_combobox(self.upb_concordance_format_comboBox, self.concordance_format_model)
        self.upb_concordance_format_comboBox.setCurrentText(settings.value('concordance_format_abbreviation'))
        self.set_combobox(self.age_unit_comboBox, self.age_unit_model)
        self.age_unit_comboBox.setCurrentText(settings.value('age_unit_abbreviation'))
        self.set_combobox(self.age_error_format_comboBox, self.age_error_format_model)
        self.age_error_format_comboBox.setCurrentText(settings.value('age_error_format_abbreviation'))

        reference_format = settings.value('reference_format')
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
        self.reference_display_lineEdit.setText(reference_format)
        # '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))'''

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

        settings.setValue('reference_format', self.update_reference_format())

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

    def add_reference_element(self):
        # Add the selected reference element to the reference format lineEdit at the current cursor position
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
        reference_format = self.reference_display_lineEdit.text()
        if '{' and '}' in reference_format:
            # identify any text between curly braced elements and replace with || "text" ||
            pattern = r'(?<=\})([^{}]+)(?=\{)'
            def replace_match(match):
                return f' || "{match.group(0)}" || '
            reference_format = re.sub(pattern, replace_match, reference_format)

        if '{Authors}' in reference_format:
            reference_format = reference_format.replace('{Authors}', 'ifnull(Authors, "")')
        if '{Year}' in reference_format:
            reference_format = reference_format.replace('{Year}', 'ifnull(Year, "")')
        if '{Title}' in reference_format:
            reference_format = reference_format.replace('{Title}', 'ifnull(Title, "")')
        if '{Source}' in reference_format:
            reference_format = reference_format.replace('{Source}', 'ifnull(Source, "")')
        if '{DOI}' in reference_format:
            reference_format = reference_format.replace('{DOI}', 'ifnull(DOI, "")')
        return reference_format

    def close(self):
        self.saveWindowState()
        return super().close()

    def saveWindowState(self):
        settings.setValue("ui/SettingDialog/pos", self.pos())
        # settings.setValue("ui/SettingDialog/size", self.size())

    def loadWindowState(self):
        self.move(settings.value("ui/SettingDialog/pos", defaultValue=QPoint(410, 241)))
        self.resize(settings.value("ui/SettingDialog/size", defaultValue=QSize(810, 569)))