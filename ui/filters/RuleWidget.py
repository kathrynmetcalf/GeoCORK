from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QDoubleValidator, QRegularExpressionValidator
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QLineEdit, QPushButton

import logger_setup
from Functions import SQLUtils
from Functions.Widget_classes import get_name_column, TableToolTipModel
from ui.widgets.FocusWheelComboBox import FocusWheelComboBox


class RuleWidget(QWidget):
    """
    Rulewidget contains the table and attribute comboboxes, operator combobox, value lineedit, and unit combobox.
    """

    def __init__(self, field=None, operator=None, value=None, unit=None, datatype=None):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumSize(100, 50)

        self.datatype = datatype
        self._age_names = []  # cache of AgeName list for SampleAges/Age
        query = QSqlQuery("SELECT AgeName FROM Ages ORDER BY AgeName COLLATE NOCASE ASC")

        age_list = []
        while query.next():
            val = query.value(0)
            if val is not None:
                age_list.append(str(val))

        # Table combo
        self.table_combo = FocusWheelComboBox()
        self.table_combo.setModel(TableToolTipModel())
        self.table_combo.addItems(
            [k for k in SQLUtils.table_attributes_dict if k.lower() != "ages"]
        )
        self.table_combo.setCurrentIndex(0)
        self.layout.addWidget(self.table_combo)
        self.table_combo.currentIndexChanged.connect(self.table_switcher)

        # Attribute combo
        self.attribute_combo = FocusWheelComboBox()
        self.layout.addWidget(self.attribute_combo)

        self.attribute_combo.setMinimumWidth(250)
        self.attribute_combo.currentIndexChanged.connect(self.attribute_switcher)

        # Sample Age type combo (hidden unless SampleAges)
        self.age_type_combo = FocusWheelComboBox()
        self.age_type_combo.addItems(["Direct", "Relative", "Both"])
        self.age_type_combo.setMinimumWidth(120)
        self.age_type_combo.setVisible(False)  # hidden by default
        self.layout.addWidget(self.age_type_combo)
        self.age_type_combo.currentIndexChanged.connect(self.sampleage_switcher)

        # Operator combo
        self.operator_combo = FocusWheelComboBox()
        self.layout.addWidget(self.operator_combo)
        self.operator_combo.setMinimumWidth(150)
        self.operator_combo.currentIndexChanged.connect(self.lineedit_switcher)

        # Value input
        self.value_input = QLineEdit()
        self.layout.addWidget(self.value_input)

        # Unit combo (hidden unless numeric/time-based)
        self.unit_combo = FocusWheelComboBox()
        self.unit_combo.addItems(['None', 'Ga', 'Ma', 'ka'])
        self.layout.addWidget(self.unit_combo)

        # Initially configure widgets based on operator/attribute
        self.table_switcher()
        self.attribute_switcher()
        self.sampleage_switcher()
        self.lineedit_switcher()

        if field is not None:
            self.table_combo.setCurrentText(field.split('.')[0])
            self.attribute_combo.setCurrentText(field.split('.')[1][1:-1])
            self.attribute_switcher()
        else:
            self.table_switcher()
            self.attribute_switcher()
        if operator is not None:
            self.operator_combo.setCurrentText(operator)
            self.lineedit_switcher()
        if value is not None:
            self.value_input.setText(value)
        else:
            self.lineedit_switcher()
        if unit is not None:
            self.unit_combo.setCurrentText(unit)

        self.lineedit_completer()

        # Delete button
        self.delete_button = QPushButton('Delete')
        self.delete_button.setToolTip('Remove condition from group')
        self.delete_button.clicked.connect(lambda: self.deleteLater())
        self.layout.addWidget(self.delete_button)

    def table_switcher(self) -> None:
        """
        Slot to change the attribute combobox values based on the current text of table combo.
        """
        self.attribute_combo.clear()
        if self.table_combo.currentText() == 'SampleAges':
            self.attribute_combo.addItems(['SampleAge', 'SampleAgeOldest', 'SampleAgeYoungest', 'SampleAgeError',
                                           'SampleAgeDescription', 'SampleAgeCreated', 'SampleAgeModified'])
        elif self.table_combo.currentText() == 'GPSLocations':
            gps_fields = SQLUtils.table_attributes_dict[self.table_combo.currentText()]
            if logger_setup.settings.value('gps_format_id') == 7:
                # UTM format, remove Lat and Lon fields
                gps_fields = [field for field in gps_fields if not any(latlon in field for latlon in ['Lat', 'Lon'])]
            else:
                # Not UTM format, remove UTM fields
                gps_fields = [field for field in gps_fields if not any(utm in field for utm in ['Zone', 'Easting', 'Northing'])]
            self.attribute_combo.addItems(gps_fields)
        else:
            self.attribute_combo.addItems(SQLUtils.table_attributes_dict[self.table_combo.currentText()])
        self.attribute_switcher()

    def attribute_switcher(self) -> None:
        """
        Slot to change the operator combobox values based on the current text of attribute combo.
        """
        if (self.table_combo.currentText() == 'SampleAges' and
                self.attribute_combo.currentText() in ("SampleAgeOldest", "SampleAgeYoungest")):
            self.age_type_combo.setVisible(True)
            # Optionally set default to "Both"
            idx = self.age_type_combo.findText("Both")
            if idx >= 0:
                self.age_type_combo.setCurrentIndex(idx)
        else:
            self.age_type_combo.setVisible(False)

        if (self.table_combo.currentText() == 'SampleAges' and
            self.attribute_combo.currentText() in ("SampleAge", "SampleAgeOldest", "SampleAgeYoungest")):
            operator_items = [
                "is",
                "is not",
                "starts with",
                "ends with",
                "contains",
                "does not contain",
                "is between",
                "is not between",
                "is blank",
                "is not blank"
            ]
            self.operator_combo.clear()
            self.operator_combo.addItems(operator_items)
            idx = self.age_type_combo.findText("Both")
            if idx >= 0:
                self.age_type_combo.setCurrentIndex(idx)
            else:
                self.age_type_combo.setVisible(False)

        elif "Created" in self.attribute_combo.currentText() or "Modified" in self.attribute_combo.currentText():
            operator_items = [
                "is on",
                "is not on",
                "is after",
                "is before",
                "is between",
                "is not between"
            ]
            self.operator_combo.clear()
            self.operator_combo.addItems(operator_items)
            self.datatype = "date"
        elif (("Description" in self.attribute_combo.currentText() or
               "Name" in self.attribute_combo.currentText() or
               "ErrorSigma" in self.attribute_combo.currentText() or
               "Unit" in self.attribute_combo.currentText()) or
              'References' in self.table_combo.currentText()):
            operator_items = [
                "is",
                "is not",
                "starts with",
                "ends with",
                "contains",
                "does not contain",
                "is blank",
                "is not blank"
            ]
            self.operator_combo.clear()
            self.operator_combo.addItems(operator_items)
            self.datatype = "string"
        elif "Rejected" in self.attribute_combo.currentText():
            operator_items = [
                "is",
                "is not"
            ]
            self.operator_combo.clear()
            self.operator_combo.addItems(operator_items)
            self.datatype = "boolean"
        else:
            # Numeric fields (e.g. Ages, numeric measurements)
            operator_items = [
                "is",
                "is not",
                "is less than",
                "is greater than",
                "is between",
                "is not between",
                "is blank",
                "is not blank"
            ]
            self.operator_combo.clear()
            self.operator_combo.addItems(operator_items)
            self.datatype = 'number'
        self.lineedit_switcher()
        self.lineedit_completer()

    def sampleage_switcher(self):
        match self.age_type_combo.currentText():
            case "Direct":
                self.datatype = "directage"
            case "Relative":
                self.datatype = "relativeage"
            case "Both":
                self.datatype = "bothage"

    def lineedit_switcher(self):
        """
        Show or hide the unit combo (Ga, Ma, ka) and set up appropriate validators
        based on the chosen operator/attribute.
        """
        # Hide the unit combo by default, show only for numeric/time-based fields
        self.unit_combo.hide()
        self.value_input.clear()

        is_sampleages_age = (
                            self.attribute_combo.currentText() == 'SampleAge' or
                            self.attribute_combo.currentText() == 'SampleAgeOldest' or
                            self.attribute_combo.currentText() == 'SampleAgeYoungest'
        )

        if 'between' in self.operator_combo.currentText():
            if is_sampleages_age:
                # Between: TWO tokens, each AgeName OR double
                age_names = getattr(self, "_age_names", [])
                if age_names:
                    escaped = [QRegularExpression.escape(a) for a in age_names]
                    ages_pattern = "|".join(escaped)
                    pattern = rf"^({ages_pattern}|-?\d+(\.\d+)?),({ages_pattern}|-?\d+(\.\d+)?)$"
                else:
                    # Fallback: numeric-only if ages not yet loaded
                    pattern = r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$"

                regex = QRegularExpression(pattern)
                regex.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
                validator = QRegularExpressionValidator(regex, self.value_input)
                self.value_input.setValidator(validator)
                self.value_input.setPlaceholderText("e.g. Holocene,Pleistocene or 0.0,1.0")
                self.value_input.setToolTip(
                    "Enter two age names or numeric values, separated by a comma"
                )
                return
        else:
            if is_sampleages_age:
                # Single value: ONE AgeName OR double
                age_names = getattr(self, "_age_names", [])
                if age_names:
                    escaped = [QRegularExpression.escape(a) for a in age_names]
                    ages_pattern = "|".join(escaped)
                    pattern = rf"^({ages_pattern}|-?\d+(\.\d+)?)$"
                else:
                    # Fallback: numeric-only
                    pattern = r"^-?\d+(\.\d+)?$"

                regex = QRegularExpression(pattern)
                regex.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
                validator = QRegularExpressionValidator(regex, self.value_input)
                self.value_input.setValidator(validator)
                self.value_input.setPlaceholderText("e.g. Holocene or 0.0")
                self.value_input.setToolTip("Enter an age name or numeric value")
                return

        # ─────────────────────────────────────────────
        # Default behaviour (unchanged)
        # ─────────────────────────────────────────────
        if 'between' in self.operator_combo.currentText():
            match self.datatype:
                case 'date':
                    # todo: Change this to a date selector
                    date_range_regex = QRegularExpression(
                        r"^(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01]),"
                        r"(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$"
                    )
                    date_range_validator = QRegularExpressionValidator(date_range_regex)
                    self.value_input.setValidator(date_range_validator)
                    self.value_input.setPlaceholderText("e.g. YYYY-MM-DD,YYYY-MM-DD")
                    self.value_input.setToolTip("Enter two dates in any order separated by a comma")
                case 'number':
                    double_comma_double_regex = QRegularExpression(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")
                    double_comma_double_validator = QRegularExpressionValidator(double_comma_double_regex)
                    self.value_input.setValidator(double_comma_double_validator)
                    self.value_input.setPlaceholderText("e.g. 0.0,0.0")
                    self.value_input.setToolTip("Enter two numeric values in any order separated by a comma")
        else:
            match self.datatype:
                case 'date':
                    date_range_regex = QRegularExpression(
                        r"^(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$"
                    )
                    date_range_validator = QRegularExpressionValidator(date_range_regex)
                    self.value_input.setPlaceholderText("e.g. YYYY-MM-DD")
                    self.value_input.setValidator(date_range_validator)
                    self.value_input.setToolTip("Enter date as YYYY-MM-DD")
                case 'string':
                    self.value_input.setPlaceholderText("e.g. abc123")
                    self.value_input.setValidator(None)
                    self.value_input.setToolTip("")
                case 'boolean':
                    self.value_input.setPlaceholderText("e.g. True/False")
                    self.value_input.setValidator(
                        QRegularExpressionValidator(QRegularExpression("^(True|False)$"))
                    )
                    self.value_input.setToolTip("")
                case 'number':
                    float_validator = QDoubleValidator(bottom=-999999999999.0, top=999999999999.0, decimals=2)
                    float_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
                    self.value_input.setPlaceholderText("e.g. 0.0")
                    self.value_input.setValidator(float_validator)
                    self.value_input.setToolTip("Enter a numeric value")

    def lineedit_completer(self) -> None:
        """
        Adds a line edit completer based on the current attribute in the combobox.
        """
        # escape if attribute combo is not set
        if self.attribute_combo.currentText() == "":
            self.value_input.setCompleter(None)
            self._age_names = []  # reset cache
            return

        name_column = get_name_column(self.table_combo.currentText())
        if not name_column:
            self.value_input.setCompleter(None)
            self._age_names = []  # reset cache
            return

        is_sampleages_age = (
                self.attribute_combo.currentText() == 'SampleAge' or
                self.attribute_combo.currentText() == 'SampleAgeOldest' or
                self.attribute_combo.currentText() == 'SampleAgeYoungest'
        )

        if self.value_input.placeholderText() == "e.g. abc123" or is_sampleages_age:

            value_completer = QtWidgets.QCompleter()
            query = QSqlQuery()

            sql_query = f'SELECT DISTINCT {self.attribute_combo.currentText()} FROM "{self.table_combo.currentText()}"'
            if is_sampleages_age:
                # Special: drive from Ages table
                sql_query = "SELECT AgeName FROM Ages"

            if not query.exec(sql_query):
                logger_setup.get_logger().critical('Error creating the completer for input')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL command: {sql_query}')

            values = set()
            while query.next():
                values.add(query.value(0))

            if is_sampleages_age:
                self._age_names = sorted(
                    [str(v) for v in values if v is not None],
                    key=str.lower
                )
            else:
                self._age_names = []

            value_completer.setModel(QtCore.QStringListModel(values))
            value_completer.model().sort(0, QtCore.Qt.SortOrder.AscendingOrder)
            value_completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
            value_completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            value_completer.setModelSorting(QtWidgets.QCompleter.ModelSorting.CaseInsensitivelySortedModel)
            value_completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
            self.value_input.setCompleter(value_completer)
        else:
            self.value_input.setCompleter(None)
            self._age_names = []  # reset cache
