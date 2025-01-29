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
        settings.setValue('age_unit_id', 1)
        settings.setValue('elevation_unit_id', 8)
        settings.setValue('gps_format_id', 7)
        settings.setValue('heightdepth_unit_id', 2)
        settings.setValue('spotsize_unit_id', 5)
        settings.setValue('age_error_format_id', 1)
        settings.setValue('ratio_error_format_id', 3)
        settings.setValue('concordance_format_id', 2)
        settings.setValue('reference_format', '''(ifnull(Authors, "") || ", " || ifnull(Year, "") || ", " || ifnull(Source, ""))''')
        settings.setValue('decimals_to_show', 2)

        # Column display settings
        settings.setValue('column_view_columns', [])
        settings.setValue('column_edit_view_columns', [])
        settings.setValue('sample_view_columns', [])
        settings.setValue('aliquot_columns', [])
        settings.setValue('spot_columns', [])
        settings.setValue('upb_analysis_columns', [])
        settings.setValue('upb_analysis_edit_columns', [])

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