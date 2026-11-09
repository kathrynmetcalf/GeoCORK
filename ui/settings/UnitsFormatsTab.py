"""'Units and Formats' tab of the Settings dialog."""
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtSql import QSqlQueryModel

import logger_setup
from Functions.Widget_classes import get_headers, populate_combo_box, FormatComboBox
from ui.settings.SettingsCore import settings, update_setting, update_abbreviation

MAX_SIZE = 16777215


def fixed_height(widget: QtW.QWidget, height: int = 25) -> QtW.QWidget:
    """Applies the minimum/maximum height used throughout the original Settings.ui"""
    widget.setMinimumSize(0, height)
    widget.setMaximumSize(MAX_SIZE, height)
    return widget


class UnitsFormatsTab(QtW.QWidget):
    """
    Decimals, GPS format, distance units, U-Pb formats, age units, U-Pb best age and reference display settings.
    """
    title = 'Units and Formats'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('units_formats_tab')

        self.gps_format_model = QSqlQueryModel()
        self.elevation_unit_model = QSqlQueryModel()
        self.column_unit_model = QSqlQueryModel()
        self.spot_size_unit_model = QSqlQueryModel()
        self.age_unit_model = QSqlQueryModel()
        self.age_error_format_model = QSqlQueryModel()
        self.ratio_error_format_model = QSqlQueryModel()
        self.concordance_format_model = QSqlQueryModel()

        self.build_ui()

        double_comma_double_regex = QRegularExpression(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")
        double_comma_double_validator = QRegularExpressionValidator(double_comma_double_regex)
        self.cutoff_age_lineEdit.setValidator(double_comma_double_validator)

    # ------------------------------------------------------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------------------------------------------------------
    def build_ui(self):
        layout = QtW.QVBoxLayout(self)
        layout.setObjectName('verticalLayout_6')

        # Row 1: decimals, GPS format, distance units
        row1 = QtW.QHBoxLayout()
        row1.setObjectName('horizontalLayout_4')

        self.decimals_groupBox = QtW.QGroupBox('Decimals to show', self)
        self.decimals_groupBox.setObjectName('decimals_groupBox')
        decimals_layout = QtW.QVBoxLayout(self.decimals_groupBox)
        self.view_rounded_checkBox = QtW.QCheckBox('View rounded', self.decimals_groupBox)
        self.view_rounded_checkBox.setObjectName('view_rounded_checkBox')
        self.decimals_comboBox = fixed_height(QtW.QComboBox(self.decimals_groupBox))
        self.decimals_comboBox.setObjectName('decimals_comboBox')
        decimals_layout.addWidget(self.view_rounded_checkBox)
        decimals_layout.addWidget(self.decimals_comboBox)
        row1.addWidget(self.decimals_groupBox)

        self.gps_format_groupBox = QtW.QGroupBox('GPS Format', self)
        self.gps_format_groupBox.setObjectName('gps_format_groupBox')
        gps_layout = QtW.QVBoxLayout(self.gps_format_groupBox)
        self.gps_format_comboBox = fixed_height(QtW.QComboBox(self.gps_format_groupBox))
        self.gps_format_comboBox.setObjectName('gps_format_comboBox')
        gps_layout.addWidget(self.gps_format_comboBox)
        row1.addWidget(self.gps_format_groupBox)

        self.distance_units_groupBox = QtW.QGroupBox('Distance Units', self)
        self.distance_units_groupBox.setObjectName('distance_units_groupBox')
        distance_grid = QtW.QGridLayout(self.distance_units_groupBox)
        self.elev_label = QtW.QLabel('Elevation:', self.distance_units_groupBox)
        self.elev_label.setObjectName('elev_label')
        self.elev_unit_comboBox = fixed_height(FormatComboBox(self.distance_units_groupBox))
        self.elev_unit_comboBox.setObjectName('elev_unit_comboBox')
        self.column_unit_label = QtW.QLabel('Column height/depth:', self.distance_units_groupBox)
        self.column_unit_label.setObjectName('column_unit_label')
        self.column_unit_comboBox = fixed_height(QtW.QComboBox(self.distance_units_groupBox))
        self.column_unit_comboBox.setObjectName('column_unit_comboBox')
        self.spot_size_unit_label = QtW.QLabel('Spot size:', self.distance_units_groupBox)
        self.spot_size_unit_label.setObjectName('spot_size_unit_label')
        self.spot_size_unit_comboBox = fixed_height(QtW.QComboBox(self.distance_units_groupBox))
        self.spot_size_unit_comboBox.setObjectName('spot_size_unit_comboBox')
        distance_grid.addWidget(self.elev_label, 0, 0)
        distance_grid.addWidget(self.elev_unit_comboBox, 0, 1)
        distance_grid.addWidget(self.column_unit_label, 1, 0)
        distance_grid.addWidget(self.column_unit_comboBox, 1, 1)
        distance_grid.addWidget(self.spot_size_unit_label, 2, 0)
        distance_grid.addWidget(self.spot_size_unit_comboBox, 2, 1)
        row1.addWidget(self.distance_units_groupBox)
        layout.addLayout(row1)

        # Row 2: U-Pb formats, age units
        row2 = QtW.QHBoxLayout()
        row2.setObjectName('horizontalLayout_5')

        self.upb_formats_groupBox = QtW.QGroupBox('U-Pb Data Formats', self)
        self.upb_formats_groupBox.setObjectName('upb_formats_groupBox')
        upb_grid = QtW.QGridLayout(self.upb_formats_groupBox)
        self.upb_ratio_error_format_label = QtW.QLabel('U-Pb ratio error format:', self.upb_formats_groupBox)
        self.upb_ratio_error_format_label.setObjectName('upb_ratio_error_format_label')
        self.upb_ratio_error_format_comboBox = fixed_height(QtW.QComboBox(self.upb_formats_groupBox))
        self.upb_ratio_error_format_comboBox.setObjectName('upb_ratio_error_format_comboBox')
        self.upb_concordance_format_label = QtW.QLabel('U-Pb concordance format:', self.upb_formats_groupBox)
        self.upb_concordance_format_label.setObjectName('upb_concordance_format_label')
        self.upb_concordance_format_comboBox = fixed_height(QtW.QComboBox(self.upb_formats_groupBox))
        self.upb_concordance_format_comboBox.setObjectName('upb_concordance_format_comboBox')
        upb_grid.addWidget(self.upb_ratio_error_format_label, 0, 0)
        upb_grid.addWidget(self.upb_ratio_error_format_comboBox, 0, 1)
        upb_grid.addWidget(self.upb_concordance_format_label, 1, 0)
        upb_grid.addWidget(self.upb_concordance_format_comboBox, 1, 1)
        row2.addWidget(self.upb_formats_groupBox)

        self.age_units_groupBox = QtW.QGroupBox('Age Units and Formats', self)
        self.age_units_groupBox.setObjectName('age_units_groupBox')
        age_grid = QtW.QGridLayout(self.age_units_groupBox)
        self.age_units_label = QtW.QLabel('Age unit:', self.age_units_groupBox)
        self.age_units_label.setObjectName('age_units_label')
        self.age_unit_comboBox = fixed_height(QtW.QComboBox(self.age_units_groupBox))
        self.age_unit_comboBox.setObjectName('age_unit_comboBox')
        self.age_error_format_label = QtW.QLabel('Age error format:', self.age_units_groupBox)
        self.age_error_format_label.setObjectName('age_error_format_label')
        self.age_error_format_comboBox = fixed_height(QtW.QComboBox(self.age_units_groupBox))
        self.age_error_format_comboBox.setObjectName('age_error_format_comboBox')
        age_grid.addWidget(self.age_units_label, 0, 0)
        age_grid.addWidget(self.age_unit_comboBox, 0, 1)
        age_grid.addWidget(self.age_error_format_label, 1, 0)
        age_grid.addWidget(self.age_error_format_comboBox, 1, 1)
        row2.addWidget(self.age_units_groupBox)
        layout.addLayout(row2)

        # U-Pb best age
        self.upb_best_age_groupBox = QtW.QGroupBox('U-Pb Best Age', self)
        self.upb_best_age_groupBox.setObjectName('upb_best_age_groupBox')
        best_layout = QtW.QVBoxLayout(self.upb_best_age_groupBox)
        self.autofill_best_checkBox = QtW.QCheckBox('Auto fill display when Best Age is blank',
                                                    self.upb_best_age_groupBox)
        self.autofill_best_checkBox.setObjectName('autofill_best_checkBox')
        best_layout.addWidget(self.autofill_best_checkBox)
        best_grid = QtW.QGridLayout()
        self.young_age_label = QtW.QLabel('Young ages', self.upb_best_age_groupBox)
        self.young_age_label.setObjectName('young_age_label')
        self.cutof_age_label = QtW.QLabel('Cutoff age (Ma)', self.upb_best_age_groupBox)
        self.cutof_age_label.setObjectName('cutof_age_label')
        self.old_age_label = QtW.QLabel('Old ages', self.upb_best_age_groupBox)
        self.old_age_label.setObjectName('old_age_label')
        self.young_age_fill_comboBox = QtW.QComboBox(self.upb_best_age_groupBox)
        self.young_age_fill_comboBox.setObjectName('young_age_fill_comboBox')
        self.cutoff_age_lineEdit = QtW.QLineEdit(self.upb_best_age_groupBox)
        self.cutoff_age_lineEdit.setObjectName('cutoff_age_lineEdit')
        self.cutoff_age_lineEdit.setSizePolicy(QtW.QSizePolicy.Policy.Preferred, QtW.QSizePolicy.Policy.Fixed)
        self.old_age_fill_comboBox = QtW.QComboBox(self.upb_best_age_groupBox)
        self.old_age_fill_comboBox.setObjectName('old_age_fill_comboBox')
        best_grid.addWidget(self.young_age_label, 0, 0)
        best_grid.addWidget(self.cutof_age_label, 0, 1)
        best_grid.addWidget(self.old_age_label, 0, 2)
        best_grid.addWidget(self.young_age_fill_comboBox, 1, 0)
        best_grid.addWidget(self.cutoff_age_lineEdit, 1, 1)
        best_grid.addWidget(self.old_age_fill_comboBox, 1, 2)
        best_layout.addLayout(best_grid)
        layout.addWidget(self.upb_best_age_groupBox)

        # Reference display
        self.reference_display_groupBox = QtW.QGroupBox('Reference Display', self)
        self.reference_display_groupBox.setObjectName('reference_display_groupBox')
        reference_layout = QtW.QVBoxLayout(self.reference_display_groupBox)
        self.reference_display_lineEdit = QtW.QLineEdit(self.reference_display_groupBox)
        self.reference_display_lineEdit.setObjectName('reference_display_lineEdit')
        reference_layout.addWidget(self.reference_display_lineEdit)
        buttons_layout = QtW.QHBoxLayout()
        for name, text in (('authors', 'Authors'), ('year', 'Year'), ('title', 'Title'), ('source', 'Source'),
                           ('doi', 'DOI')):
            button = QtW.QPushButton(text, self.reference_display_groupBox)
            button.setObjectName(f'{name}_pushButton')
            setattr(self, f'{name}_pushButton', button)
            buttons_layout.addWidget(button)
        reference_layout.addLayout(buttons_layout)
        layout.addWidget(self.reference_display_groupBox)

    def tab_order(self) -> list[QtW.QWidget]:
        return [self.decimals_comboBox, self.gps_format_comboBox, self.elev_unit_comboBox, self.column_unit_comboBox,
                self.spot_size_unit_comboBox, self.upb_ratio_error_format_comboBox,
                self.upb_concordance_format_comboBox, self.age_unit_comboBox, self.age_error_format_comboBox,
                self.autofill_best_checkBox, self.young_age_fill_comboBox, self.cutoff_age_lineEdit,
                self.old_age_fill_comboBox, self.reference_display_lineEdit, self.authors_pushButton,
                self.year_pushButton, self.title_pushButton, self.source_pushButton, self.doi_pushButton]

    def connect_signals(self):
        """Connected after the first populate, as in the original dialog"""
        self.view_rounded_checkBox.checkStateChanged.connect(self.set_rounding)

        self.autofill_best_checkBox.checkStateChanged.connect(self.populate_best_age_fields)

        self.authors_pushButton.clicked.connect(self.add_reference_element)
        self.year_pushButton.clicked.connect(self.add_reference_element)
        self.title_pushButton.clicked.connect(self.add_reference_element)
        self.source_pushButton.clicked.connect(self.add_reference_element)
        self.doi_pushButton.clicked.connect(self.add_reference_element)

    # ------------------------------------------------------------------------------------------------------------------
    # Populate / save
    # ------------------------------------------------------------------------------------------------------------------
    def populate(self):
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

    def save(self) -> bool:
        """
        Saves decimals, unit/format combo boxes, best age and reference format.
        :return: False if the best age cutoff is not a number (the original update_settings stopped there)
        """
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
                    return False
            settings.setValue('best_age_cutoff', best_age_cutoff)
        else:
            settings.setValue('autofill_best_age', 'false')

        settings.setValue('reference_format', self.update_reference_format())
        return True

    # ------------------------------------------------------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------------------------------------------------------
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
