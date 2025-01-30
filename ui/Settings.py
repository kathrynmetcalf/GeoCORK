import sys

from PyQt6.uic import loadUi
from PyQt6.QtSql import QSqlTableModel, QSqlQueryModel, QSqlQuery
from PyQt6 import QtWidgets as QtW
from PyQt6.QtGui import QFont

from Functions.Settings_manager import settings

def populate_app_defaults():
    app = QtW.QApplication.instance()
    settings.setValue('default_font_family', app.font().family())
    settings.setValue('default_font_size', app.font().pointSize())
    settings.setValue('default_table_font_size', app.font().pointSize())

    # If other settings have been set, update the font and stylesheet
    if bool(settings.value('default_settings')) is False:
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
    # get the default settings from the QSettings object
    if bool(settings.value('default_settings')) is True:
        # Unit and Format settings
        settings.setValue('age_unit_id', 2) # Ma
        update_abbreviation('age_unit_id')
        settings.setValue('elevation_unit_id', 2) # m
        update_abbreviation('elevation_unit_id')
        settings.setValue('gps_format_id', 1) # DD +/-
        update_abbreviation('gps_format_id')
        settings.setValue('heightdepth_unit_id', 2) # m
        update_abbreviation('heightdepth_unit_id')
        settings.setValue('spotsize_unit_id', 5) # um
        update_abbreviation('spotsize_unit_id')
        settings.setValue('age_error_format_id', 1) # 1 sigma abs
        update_abbreviation('age_error_format_id')
        settings.setValue('ratio_error_format_id', 3) # 1 sigma %
        update_abbreviation('age_error_format_id')
        settings.setValue('concordance_format_id', 2) # Con%
        update_abbreviation('concordance_format_id')
        settings.setValue('reference_format', '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
        settings.setValue('decimals_to_show', 2)

        # Column display settings
        settings.setValue('sample_view_columns', [
            'Samples.SampleID', 'Samples.SampleIGSN', 'Samples.SampleName', 'Samples.SampleDescription',
            'GPSLocations.GPSLocationConverted', 'GPSLocations.CalculatedGPSElev || "±" || GPSLocations.CalculatedGPSElevError',
            'SampleAges.SampleAgeDisplay', 'GROUP_CONCAT(DISTINCT AgeConstraintName)', 'GROUP_CONCAT(DISTINCT AgeInterpretationName)',
            'GROUP_CONCAT(DISTINCT AgeReferences.ReferenceDisplay)', 'Columns.ColumnName', 'HeightDepth || "±" || HeightDepthError',
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
        settings.setValue('aliquot_columns', [
            'Aliquots.AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'Samples.SampleName',
            'GROUP_CONCAT(DISTINCT AliquotContextName)', 'COUNT(DISTINCT Spots.SpotID)', 'GROUP_CONCAT(DISTINCT SpotCompositionName)',
            'GROUP_CONCAT(DISTINCT SpotContextName)', 'SUM(CASE WHEN Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID)',
            'GROUP_CONCAT(DISTINCT LabFacilityName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)', 'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)',
            'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)', 'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)',
            'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT CalculatedSpotSize)',
            'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)', 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)',
            'AliquotCreated', 'AliquotModified'
        ])
        settings.setValue('aliquot_edit_columns', [
            'Aliquots.AliquotID', 'ParentAliquotID', 'AliquotParentRow', 'AliquotName', 'Samples.SampleName',
            'GROUP_CONCAT(DISTINCT AliquotContextName)', 'AliquotCreated', 'AliquotModified'
        ])
        settings.setValue('spot_columns', [
            'Spots.SpotID', 'GROUP_CONCAT(DISTINCT SpotName)', 'Samples.SampleName', 'AliquotName',
            'GROUP_CONCAT(DISTINCT SpotCompositionName)', 'GROUP_CONCAT(DISTINCT SpotContextName)',
            'SUM(CASE WHEN Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID)',
            'GROUP_CONCAT(DISTINCT LabFacilityName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)',
            'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)',
            'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)', 'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)',
            'GROUP_CONCAT(DISTINCT CalculatedSpotSize)', 'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)',
            'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)', 'SpotCreated', 'SpotModified'
        ])
        settings.setValue('spot_edit_columns', [
            'Spots.SpotID', 'GROUP_CONCAT(DISTINCT SpotName)', 'Samples.SampleName', 'AliquotName',
            'GROUP_CONCAT(DISTINCT SpotCompositionName)', 'GROUP_CONCAT(DISTINCT SpotContextName)', 'SpotCreated', 'SpotModified'
        ])
        settings.setValue('upb_analysis_columns', [
            'UPbAnalyses.UPbAnalysisID', 'SpotName', 'AliquotName', 'Samples.SampleName', 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)',
            'GROUP_CONCAT(DISTINCT LabFacilityName)', 'GROUP_CONCAT(DISTINCT InstrumentName)', 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)',
            'UPbAnalyses."Pb207cps"', 'UPbAnalyses."Pb208cps"', 'UPbAnalyses."Pb*cps"', 'UPbAnalyses."Th232cps"',
            'UPbAnalyses."U235cps"', 'UPbAnalyses."U238cps"', 'UPbAnalyses."Uppm"', 'UPbAnalyses."Thppm"',
            'UPbAnalyses."CalculatedU/Th"', 'UPbAnalyses."CalculatedTh/U"',
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
            'UPbAnalyses."CalculatedConcordance"', 'UPbAnalyses."GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)"',
            'UPbAnalyses.UPbAnalysisCreated', 'UPbAnalyses.UPbAnalysisModified'
        ])
        settings.setValue('upb_analysis_edit_columns', [
            'UPbAnalyses.UPbAnalysisID', 'SpotName', 'AliquotName', 'Samples.SampleName',
            'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)', 'GROUP_CONCAT(DISTINCT LabFacilityName)',
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
            'UPbAnalyses."ErrorCorr/Rho"', 'UPbAnalyses."207Pb/206PbAge"', 'UPbAnalyses."207Pb/206PbAgeError"',
            'UPbAnalyses."207Pb/235UAge"', 'UPbAnalyses."207Pb/235UAgeError"', 'UPbAnalyses."206Pb/238UAge"',
            'UPbAnalyses."206Pb/238UAgeError"', 'UPbAnalyses."208Pb/232ThAge"', 'UPbAnalyses."208Pb/232ThAgeError"',
            'UPbAnalyses."BestAge"', 'UPbAnalyses."BestAgeError"', 'UPbAnalyses."Concordance"', 'UPbAnalyses."SpotSize"',
            'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)', 'UPbAnalysisCreated', 'UPbAnalysisModified'
        ])
        settings.setValue('column_view_columns', [
            'Columns.ColumnID', 'Columns.ColumnName', 'Columns.CalculatedTotalHeightDepth', 'ColumnGPS.GPSLocationConverted',
            'ColumnDescription', 'ColumnCreated', 'ColumnModified'
        ])
        settings.setValue('column_edit_view_columns', [
            'Columns.ColumnID', 'Columns.ColumnName', 'Columns.ColumnTotalHeightDepth', 'ColumnUnits.DistanceUnitAbbreviation',
            'ColumnGPS.GPSLocationDisplay', 'ColumnDescription', 'ColumnCreated', 'ColumnModified'
        ])

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

def update_setting(key, value):
    # pass the key to update and user input, then change the value in settings
    settings.setValue(key, value)
    if bool(settings.value('default_settings')) is True:
        settings.setValue('default_settings', False)

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

        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Ok).clicked.connect(self.update_settings_close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.Apply).clicked.connect(self.update_settings)
        self.buttonBox.button(QtW.QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)

    def populate_fields(self):

        self.set_combobox(self.gps_format_comboBox, self.gps_format_model)
        self.set_combobox(self.elev_unit_comboBox, self.elevation_unit_model)
        self.set_combobox(self.column_unit_comboBox, self.column_unit_model)
        self.set_combobox(self.spot_size_unit_comboBox, self.spot_size_unit_model)
        self.set_combobox(self.age_unit_comboBox, self.age_unit_model)
        self.set_combobox(self.age_error_format_comboBox, self.age_error_format_model)
        self.set_combobox(self.upb_ratio_error_format_comboBox, self.ratio_error_format_model)
        self.set_combobox(self.upb_concordance_format_comboBox, self.concordance_format_model)

        self.about_db_model.setQuery('SELECT * FROM About')
        self.db_name_lineEdit.setText(self.about_db_model.record(0).value('Name'))
        self.db_authors_lineEdit.setText(self.about_db_model.record(0).value('Authors'))
        self.db_description_lineEdit.setText(self.about_db_model.record(0).value('Description'))
        self.db_reference_link_lineEdit.setText(self.about_db_model.record(0).value('ReferenceLink'))
        self.db_created_by_lineEdit.setText(self.about_db_model.record(0).value('CreatedBy'))
        self.db_reference_lineEdit.setText(self.about_db_model.record(0).value('Citation'))

        # List of font sizes to populate the font size comboboxes
        font_sizes = []
        font_sizes = [str(i) for i in range(6, 21)]
        self.font_size_comboBox.addItems(font_sizes)
        self.font_size_comboBox.setCurrentText(str(settings.value('font_size')))
        self.table_font_size_comboBox.addItems(font_sizes)
        self.table_font_size_comboBox.setCurrentText(str(settings.value('table_font_size')))
        self.fontComboBox.setCurrentFont(self.fontComboBox.font())

    def update_settings(self):
        # No longer using default settings
        settings.setValue('default_settings', False)

        # Save the settings to the QSettings object
        # Do not assume that the index is the same as the ID
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
        settings.setValue('default_settings', True)
        default_settings()
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