import ast
import json
import re

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QRect, Qt, QEventLoop, QRegularExpression
from PyQt6.QtGui import QFontMetrics, QColor, QAction, QRegularExpressionValidator, \
    QDoubleValidator, QGuiApplication
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QGroupBox, QLabel,
    QInputDialog, QMessageBox, QScrollArea, QSizePolicy, QListWidget, QDialog, QColorDialog, QTextEdit, QListWidgetItem
)
from PyQt6.uic import loadUi

import logger_setup
from Functions import SQLUtils
from Functions.Widget_classes import get_id_from_name, get_headers, get_name_column
from ui.DataViewerWidget import DataViewerWidget


def process_json_to_sql(json_string, scope):
    """
    Converts a structured JSON string representing a filter group to a SQL WHERE clause.
    """
    logger_setup.get_logger().debug(f'Processing with scope: {scope}: {json_string}')
    json_string = json_string.replace("'", "\"")
    group = json.loads(json_string)
    where = process_group(group)

    table_names = process_table_names(group)
    join = SQLUtils.get_join_from_table("", table_names)
    sql = None
    if scope == 'Samples':
        sql = f"SELECT * FROM Samples {join} WHERE {where};"
    elif scope == 'Aliquots':
        join = SQLUtils.get_join_from_table(join, ['Aliquots'])
        sql = f"SELECT * FROM Samples {join} WHERE {where};"
    elif scope == 'Spots':
        join = SQLUtils.get_join_from_table(join, ['Spots'])
        sql = f"SELECT * FROM Samples {join} WHERE {where};"
    elif scope == 'UPbAnalyses':
        join = SQLUtils.get_join_from_table(join, ['UPbAnalyses'])
        sql = f"SELECT * FROM Samples {join} WHERE {where};"
    else:
        logger_setup.get_logger().critical(f"Unknown scope: {scope}")
    logger_setup.get_logger().debug(f"SQL generated successfully: {sql}")
    return sql


def process_table_names(data):
    table_names = set()
    def collect_table_names(group):
        conditions = group.get('conditions', [])
        subgroups = group.get('subgroups', [])
        for condition in conditions:
            field = condition['field']
            table_name = extract_table_name(field)
            if table_name:
                table_names.add(table_name)
        for subgroup in subgroups:
            collect_table_names(subgroup)

    collect_table_names(data)
    logger_setup.get_logger().debug(f'Collected table names: {table_names}')
    return table_names


def extract_table_name(field):
    if '.' in field:
        parts = field.split('.')
        return parts[0]
    else:
        return None


def process_group(group):
    condition_strings, ctes = _process_group_inner(group)
    return ' AND '.join(condition_strings), ctes

# Developer-specified recursive targets
RECURSIVE_TABLES = {
    'Regions.RegionName': {
        'id_column': 'RegionID',
        'name_column': 'RegionName',
        'parent_column': 'ParentRegionID',
        'cte_name': 'RecursiveRegions'
    },
    'RockTypes.RockTypeName': {
        'id_column': 'RockTypeID',
        'name_column': 'RockTypeName',
        'parent_column': 'ParentRockTypeID',
        'cte_name': 'RecursiveRockTypes'
    }
}


def _process_group_inner(group):
    condition_strings = []
    ctes = []

    for condition in group.get('conditions', []):
        field_key = condition['field'].replace(' ', '')
        value = condition['value']
        operator = condition['operator'].lower()
        datatype = condition['datatype']
        unit = condition['unit']

        if unit == 'Ga':
            value = f"{float(value) * 1_000_000_000}"
        elif unit == 'Ma':
            value = f"{float(value) * 1_000_000}"
        elif unit == 'ka':
            value = f"{float(value) * 1_000}"
        elif unit != 'None':
            raise ValueError(f"Unknown unit: {unit}")

        # If this field requires recursion
        if field_key in RECURSIVE_TABLES and operator in ['is', 'is on', '=']:
            meta = RECURSIVE_TABLES[field_key]
            cte = f"""
            {meta['cte_name']} AS (
                SELECT {meta['id_column']}, {meta['name_column']}
                FROM {field_key.split('.')[0]}
                WHERE {meta['name_column']} = '{value}'
                UNION ALL
                SELECT t.{meta['id_column']}, t.{meta['name_column']}
                FROM {field_key.split('.')[0]} t
                INNER JOIN {meta['cte_name']} r ON t.{meta['parent_column']} = r.{meta['id_column']}
            )
            """
            condition_strings.append(
                f"{meta['id_column']} IN (SELECT {meta['id_column']} FROM {meta['cte_name']})"
            )
            ctes.append(cte.strip())
        else:
            # Normal condition
            if operator in ['is', 'is on']:
                operator = '='
            elif operator in ['is not', 'is not on']:
                operator = '!='
            elif operator in ['is greater than', 'is after']:
                operator = '>'
            elif operator in ['is less than', 'is before']:
                operator = '<'
            elif operator == 'is blank':
                condition_strings.append(f"{field_key} IS NULL")
                continue
            elif operator == 'is not blank':
                condition_strings.append(f"{field_key} IS NOT NULL")
                continue
            elif operator == 'contains':
                condition_strings.append(f"{field_key} LIKE '%{value}%'")
                continue
            elif operator == 'does not contain':
                condition_strings.append(f"{field_key} NOT LIKE '%{value}%'")
                continue
            elif operator == 'starts with':
                condition_strings.append(f"{field_key} LIKE '{value}%'")
                continue
            elif operator == 'ends with':
                condition_strings.append(f"{field_key} LIKE '%{value}'")
                continue
            elif operator == 'is between':
                value1, value2 = value.split(',')
                condition_strings.append(
                    f"{field_key} BETWEEN {' AND '.join([value1, value2])}" if datatype == 'number'
                    else f"{field_key} BETWEEN '{value1}' AND '{value2}'"
                )
                continue
            elif operator == 'is not between':
                value1, value2 = value.split(',')
                condition_strings.append(
                    f"{field_key} NOT BETWEEN {' AND '.join([value1, value2])}" if datatype == 'number'
                    else f"{field_key} NOT BETWEEN '{value1}' AND '{value2}'"
                )
                continue

            # Regular condition
            condition = f"{field_key} {operator} {value}" if datatype == 'number' else f"{field_key} {operator} '{value}'"
            condition_strings.append(condition)

    for subgroup in group.get('subgroups', []):
        sub_conditions, sub_ctes = _process_group_inner(subgroup)
        if sub_conditions:
            logic = group['type'].lower()
            if logic == "match all":
                condition_strings.append(f"({' AND '.join(sub_conditions)})")
            elif logic == "match any":
                condition_strings.append(f"({' OR '.join(sub_conditions)})")
            elif logic == "match none":
                condition_strings.append(f"NOT ({' AND '.join(sub_conditions)})")
        ctes.extend(sub_ctes)

    return condition_strings, ctes


def process_selects(group):
    """
    Recursively process a group of conditions and subgroups to create a list of fields for SELECT.
    """
    if not group.get('conditions') and not group.get('subgroups'):
        return ''

    # Process conditions in the current group
    fields = []
    for condition in group.get('conditions', []):
        field = condition['field']
        fields.append(field)

    # Process subgroups recursively
    for subgroup in group.get('subgroups', []):
        subgroup_string = process_selects(subgroup)
        if subgroup_string:
            fields.append(subgroup_string)

    return fields


# def parse_sql_to_structure(sql):
#     """
#     (Demonstration) Parses a SQL WHERE clause into a structured format.
#     """
#     import re
#
#     sql = sql.strip()
#
#     def parse_expression(expression):
#         expression = expression.strip()
#         if '(' in expression:
#             depth, start = 0, None
#             for i, char in enumerate(expression):
#                 if char == '(':
#                     if depth == 0:
#                         start = i
#                     depth += 1
#                 elif char == ')':
#                     depth -= 1
#                     if depth == 0:
#                         subgroup = parse_expression(expression[start + 1:i])
#                         return [subgroup] + parse_expression(expression[i + 1:])
#         return [parse_conditions(expression)]
#
#     def parse_conditions(conditions):
#         conditions = re.split(r'\s(AND|OR)\s', conditions)
#         structured_conditions = []
#         operator = None
#         for condition in conditions:
#             if condition.upper() in ['AND', 'OR']:
#                 operator = condition
#             else:
#                 parts = condition.split()
#                 if len(parts) >= 3:
#                     field = parts[0]
#                     op = parts[1]
#                     value = ' '.join(parts[2:]).strip("'")
#                     structured_conditions.append({'field': field, 'operator': op, 'value': value, 'logic': operator})
#                     operator = None
#         return structured_conditions
#
#     return parse_expression(sql)

class Filters(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        sources_ui_file = "ui/Filters.ui"
        loadUi(sources_ui_file, self)
        self.querybuilder = QueryBuilder(self)
        self.horizontalLayout_2.addWidget(self.querybuilder)

class InsertFilterGroupDialog(QDialog):
    def __init__(self, sql_structure, update_id=None, parent=None):
        super().__init__(parent)
        self.sql_structure = sql_structure
        self.update_id = update_id

        if self.update_id:
            self.setWindowTitle("Update Filter Group")
        else:
            self.setWindowTitle("Insert New Filter Group")

        layout = QVBoxLayout()
        self.name_label = QLabel("Filter Group Name:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        self.warning_label = QLabel()
        layout.addWidget(self.warning_label)

        self.description_label = QLabel("Filter Group Description:")
        self.description_input = QTextEdit()
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_input)

        if self.update_id:
            self.update_button = QPushButton("Update")
            self.update_button.clicked.connect(self.update_data)
        else:
            self.insert_button = QPushButton("Insert")
            self.insert_button.clicked.connect(self.insert_data)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout = QHBoxLayout()
        if self.update_id:
            buttons_layout.addWidget(self.update_button)
        else:
            buttons_layout.addWidget(self.insert_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        if self.update_id:
            self.populate_fields()

    def populate_fields(self):
        query = QSqlQuery()
        sql_query = """
            SELECT FilterGroupName, FilterGroupDescription 
            FROM FilterGroups 
            WHERE FilterGroupID = :filter_id;
        """
        query.prepare(sql_query)
        query.bindValue(":filter_id", self.update_id)
        logger_setup.get_logger().info(f'Populating fields for filter: {self.update_id}')
        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        if query.exec():
            if query.next():
                self.name_input.setText(query.value(0))
                self.description_input.setText(query.value(2))
            else:
                logger_setup.get_logger().critical(
                    f'No matching filter group for: {self.update_id}')
        else:
            logger_setup.get_logger().critical(
                f'Error in populating existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

    def insert_data(self):
        name = self.name_input.text()
        description = self.description_input.toPlainText()

        query = QSqlQuery()

        check_query = "SELECT FilterGroupName FROM FilterGroups WHERE FilterGroupName = :name"
        query.prepare(check_query)
        query.bindValue(":name", name)
        logger_setup.get_logger().info(f'Checking if name: {name} already exists in FilterGroups table')
        logger_setup.get_logger().debug(f'SQL command: {check_query}')
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error in checking for existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {check_query}')
            return

        if query.next():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText(f"Filter {name} already exists. Do you want to update it?")
            msg.setWindowTitle("Duplicate Filter Name")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            reply = msg.exec()
            if reply == QMessageBox.StandardButton.Yes:
                self.update_id = get_id_from_name('FilterGroups', name)
                self.update_data()
            else:
                return
            # self.warning_label.show()
            # self.warning_label.setText('<font color="red">Name must be unique</font>')
            # self.warning_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            insert_query = """
                INSERT INTO FilterGroups (FilterGroupName, SQLQuery, FilterGroupDescription)
                VALUES (:name, :sql_query, :description)
            """
            query.prepare(insert_query)
            query.bindValue(":name", name)
            query.bindValue(":sql_query", f'\'{self.sql_structure}\'')
            query.bindValue(":description", description)

            if not query.exec():
                logger_setup.get_logger().critical(
                    f'Error could not add filter')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL command: {check_query}')
            else:
                logger_setup.get_logger().info(f'Filter {name} added')
                self.accept()

    def update_data(self):
        name = self.name_input.text()
        description = self.description_input.toPlainText()

        query = QSqlQuery()
        update_query = """
            UPDATE FilterGroups
            SET FilterGroupName = :name, SQLQuery = :sql_query, FilterGroupDescription = :description
            WHERE FilterGroupID = :id
        """
        query.prepare(update_query)
        query.bindValue(":name", name)
        query.bindValue(":sql_query", f'\'{self.sql_structure}\'')
        query.bindValue(":description", description)
        query.bindValue(":id", self.update_id)
        if not query.exec():
            logger_setup.get_logger().critical(
                f'Error could not update filter')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {update_query}')
        else:
            logger_setup.get_logger().info(f'Filter {name} updated')
            self.accept()


class FocusWheelComboBox(QComboBox):
    """
    A QComboBox that ignores mouse wheel events when focused, so the user can't accidentally
    scroll away from the intended selection.
    """
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()


class RuleWidget(QWidget):
    """
    A single condition row in the query builder, comprising:
      - A table selection
      - An attribute selection
      - An operator selection
      - A value input
      - A unit combobox (Ga, Ma, ka)
      - A delete button
    """
    def __init__(self, field=None, operator=None, value=None, unit=None, datatype=None):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumSize(100, 50)

        self.datatype = datatype
        # Table combo
        self.table_combo = FocusWheelComboBox()
        self.table_combo.addItems(SQLUtils.table_attributes_dict.keys())
        self.table_combo.setCurrentIndex(0)
        self.layout.addWidget(self.table_combo)
        self.table_combo.currentIndexChanged.connect(self.table_switcher)

        # Attribute combo
        self.attribute_combo = FocusWheelComboBox()
        self.layout.addWidget(self.attribute_combo)
        self.table_switcher()
        self.attribute_combo.setMinimumWidth(250)
        self.attribute_combo.currentIndexChanged.connect(self.attribute_switcher)

        # Operator combo
        self.operator_combo = FocusWheelComboBox()
        # self.attribute_switcher()
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
        self.lineedit_switcher()

        if field is not None:
            self.table_combo.setCurrentText(field.split('.')[0])
            self.attribute_combo.setCurrentText(field.split('.')[1][1:-1])
        else:
            self.table_switcher()
            self.attribute_switcher()
        if operator is not None:
            self.operator_combo.setCurrentText(operator)
        if value is not None:
            self.value_input.setText(value)
        else:
            self.lineedit_switcher()
        if unit is not None:
            self.unit_combo.setCurrentText(unit)

        self.lineedit_completer()

        # Delete button
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(lambda: self.deleteLater())
        self.layout.addWidget(self.delete_button)


    def lineedit_switcher(self):
        """
        Show or hide the unit combo (Ga, Ma, ka) and set up appropriate validators
        based on the chosen operator/attribute.
        """
        # Hide the unit combo by default, show only for numeric/time-based fields
        self.unit_combo.hide()
        self.value_input.clear()

        if 'between' in self.operator_combo.currentText():
            # Date-based fields
            match self.datatype:
                case 'date':
                    date_range_regex = QRegularExpression(
                        r"^(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01]),"
                        r"(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$"
                    )
                    date_range_validator = QRegularExpressionValidator(date_range_regex)
                    self.value_input.setValidator(date_range_validator)
                    self.value_input.setPlaceholderText("e.g. YYYY-MM-DD,YYYY-MM-DD")
                case 'number':
                    # Numeric fields
                    double_comma_double_regex = QRegularExpression(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")
                    double_comma_double_validator = QRegularExpressionValidator(double_comma_double_regex)
                    self.value_input.setValidator(double_comma_double_validator)
                    self.value_input.setPlaceholderText("e.g. 0.0,0.0")
                    # Because it's numeric, let's allow the user to pick units (e.g. for an age)
                    self.unit_combo.show()
        else:
            # Single value conditions
            match self.datatype:
                case 'date':
                    # Date-based
                    date_range_regex = QRegularExpression(
                        r"^(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$"
                    )
                    date_range_validator = QRegularExpressionValidator(date_range_regex)
                    self.value_input.setPlaceholderText("e.g. YYYY-MM-DD")
                    self.value_input.setValidator(date_range_validator)
                case 'string':
                    # Text-based
                    self.value_input.setPlaceholderText("e.g. abc123")
                    self.value_input.setValidator(None)  # No numeric validator
                case 'boolean':
                    self.value_input.setPlaceholderText("e.g. True/False")
                    self.value_input.setValidator(QRegularExpressionValidator(QRegularExpression("^(True|False)$")))
                case 'number':
                    # Numeric fields, e.g. Ages
                    float_validator = QDoubleValidator(
                        bottom=-999999999999.0,
                        top=999999999999.0,
                        decimals=2
                    )
                    float_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
                    self.value_input.setPlaceholderText("e.g. 0.0")
                    self.value_input.setValidator(float_validator)
                    # Show units if it's numeric
                    if "Age" in self.attribute_combo.currentText():
                        self.unit_combo.show()

    def lineedit_completer(self):
        if self.attribute_combo.currentText() == "":
            self.value_input.setCompleter(None)
            return
        name_column = get_name_column(self.table_combo.currentText())
        if not name_column:
            self.value_input.setCompleter(None)
            return
        name_header = get_headers(self.table_combo.currentText())[name_column]
        if self.attribute_combo.currentText() == name_header and self.value_input.placeholderText() == "e.g. abc123":
            # Populate the value input with a completer based on the selected attribute
            value_completer = QtWidgets.QCompleter()
            query = QSqlQuery()
            sql_query = f"SELECT DISTINCT {self.attribute_combo.currentText()} FROM {self.table_combo.currentText()}"
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            if not query.exec(sql_query):
                logger_setup.get_logger().info(f'Error creating the completer for input')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            values = []
            while query.next():
                values.append(query.value(0))
            value_completer.setModel(QtCore.QStringListModel(values))
            value_completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
            value_completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            value_completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
            self.value_input.setCompleter(value_completer)

    def attribute_switcher(self):
        """
        Based on the attribute selected, populate the operator combo and the value line edit completer.
        """
        if "Created" in self.attribute_combo.currentText() or "Modified" in self.attribute_combo.currentText():
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
             self.table_combo.currentText() == '"References"'):
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
                # Numeric fields (e.g. Ages, numeric measurements)
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

    def table_switcher(self):
        """
        When the table changes, re-populate the attribute combo with valid fields from SQLUtils.table_attributes_dict.
        """
        self.attribute_combo.clear()
        self.attribute_combo.addItems(SQLUtils.table_attributes_dict[self.table_combo.currentText()])


class GroupBox(QGroupBox):
    def __init__(self, group=None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.conditions = []
        self.subgroups = []

        self.setTitle('Group')
        self.dummy_label = QLabel(self.title())
        self.updateDummyLabelFont()
        self.layout = QVBoxLayout(self)

        # Group logical operator
        self.group_operator_combo = FocusWheelComboBox()
        self.group_operator_combo.addItems(['Match all', 'Match any', 'Match none'])
        self.layout.addWidget(self.group_operator_combo)

        # Buttons to add rule or group
        buttons_layout = QHBoxLayout()
        self.add_rule_button = QPushButton('Add rule')
        self.add_rule_button.clicked.connect(lambda: self.add_rule(None, None, None, None, None))

        self.add_group_button = QPushButton('Add group')
        self.add_group_button.clicked.connect(lambda: self.add_group(None))

        self.delete_button = QPushButton('Delete')
        # self.delete_button.clicked.connect(self.delete_group)

        buttons_layout.addWidget(self.add_rule_button)
        buttons_layout.addWidget(self.add_group_button)
        buttons_layout.addWidget(self.delete_button)

        self.layout.addLayout(buttons_layout)
        self.layout.addStretch(1)
        self.populate_from_group(group)

    def populate_from_group(self, group):
        """
        If 'group' is provided, load existing conditions/subgroups.
        Otherwise, add one empty rule by default.
        """
        if group is not None:
            self.group_operator_combo.setCurrentText(group['type'])
            for condition in group.get('conditions', []):
                self.add_rule(condition['field'], condition['operator'], condition['value'], condition['unit'], condition['datatype'])
            for subgroup in group.get('subgroups', []):
                self.add_group(subgroup)
        else:
            self.add_rule(None, None, None, None, None)

    def mouseDoubleClickEvent(self, a0):
        super().mouseDoubleClickEvent(a0)
        if self.isDoubleClickOnTitle(a0.pos()):
            new_title, ok = QInputDialog.getText(self, "Edit Title", "Enter new title:")
            if ok and new_title:
                self.setTitle(new_title)
                self.updateDummyLabelFont()

    def isDoubleClickOnTitle(self, pos):
        titleSize = QFontMetrics(self.dummy_label.font()).size(QtCore.Qt.TextFlag.TextSingleLine, self.title())
        titleRect = QRect(0, 0, titleSize.width() + 10, titleSize.height() + 5)
        self.setObjectName(self.title())
        return titleRect.contains(pos)

    def updateDummyLabelFont(self):
        font = self.font()
        font.setBold(True)
        self.dummy_label.setFont(font)

    def add_rule(self, field, operator, value, unit, datatype):
        #todo not populating line edit with value
        rule_widget = RuleWidget(field, operator, value, unit, datatype)
        self.layout.insertWidget(self.layout.count() - 1, rule_widget)
        self.conditions.append(rule_widget)
        rule_widget.delete_button.clicked.connect(lambda: self.delete_condition(rule_widget))

    def add_group(self, group):
        group_widget = GroupBox(group)
        self.layout.insertWidget(self.layout.count() - 1, group_widget)
        self.subgroups.append(group_widget)
        group_widget.delete_button.clicked.connect(lambda: self.delete_group(group_widget))

    def delete_condition(self, condition_widget):
        condition_widget.deleteLater()
        self.conditions.remove(condition_widget)

    def delete_group(self, group_widget):
        group_widget.deleteLater()
        self.subgroups.remove(group_widget)

    def get_structure(self):
        """
        Builds a dictionary describing this group's logical type,
        conditions (including unit selection), and nested subgroups.
        """
        structure = {
            "type": self.group_operator_combo.currentText(),
            "conditions": [],
            "subgroups": [subgroup.get_structure() for subgroup in self.subgroups]
        }
        for condition_widget in self.conditions:
            condition_widget: RuleWidget
            structure["conditions"].append({
                "field": condition_widget.table_combo.currentText()
                         + '.['
                         + condition_widget.attribute_combo.currentText()
                         + ']',
                "operator": condition_widget.operator_combo.currentText(),
                "value": condition_widget.value_input.text(),
                "unit": condition_widget.unit_combo.currentText(),
                "datatype": condition_widget.datatype
            })
        return structure

    def get_selects(self):
        """
        Returns a comma-separated list of fields for SELECT statements.
        """
        list_of_fields = ''
        for ruleWidget in self.findChildren(RuleWidget):
            combined = (ruleWidget.table_combo.currentText().replace(' ', '')
                        + '.[' + ruleWidget.attribute_combo.currentText() + ']')
            if combined not in list_of_fields:
                list_of_fields += combined + ', \n'
        return list_of_fields[0:-3] + '\n'

    def get_tables(self):
        """
        Returns all unique table names from conditions in this group (and nested subgroups).
        """
        tables = []
        for ruleWidget in self.findChildren(RuleWidget):
            if ruleWidget.table_combo.currentText() not in tables:
                tables.append(ruleWidget.table_combo.currentText())
        return tables


class QueryBuilder(QWidget):
    """
    Main Query Builder widget that uses a GroupBox as the root group.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.listWidget: QListWidget = self.parentWidget().findChild(QListWidget, 'listWidget')

        self.update_filter_list()
        self.listWidget.itemDoubleClicked.connect(lambda state: self.populate_filters(state))
        self.listWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.filter_context_menu)

        self.layout1 = QVBoxLayout(self)
        self.setLayout(self.layout1)

        self.scrollarea = QScrollArea(self)
        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.main_group_box = GroupBox()
        self.main_group_box.setParent(self)
        self.layout1.addWidget(self.scrollarea)
        self.scrollarea.setWidget(self.main_group_box)

        self.layout1.addWidget(QLabel('Note: Select which view based on desired filtered subset'))

        buttons_layout = QHBoxLayout(self)
        self.view_samples_button = QPushButton('View Samples')
        buttons_layout.addWidget(self.view_samples_button)
        self.view_samples_button.clicked.connect(self.view_samples)

        self.view_aliquots_button = QPushButton('View Aliquots')
        buttons_layout.addWidget(self.view_aliquots_button)
        self.view_aliquots_button.clicked.connect(self.view_aliquots)

        self.view_spots_button = QPushButton('View Spots')
        buttons_layout.addWidget(self.view_spots_button)
        self.view_spots_button.clicked.connect(self.view_spots)

        self.view_analysis_button = QPushButton('View Analysis')
        buttons_layout.addWidget(self.view_analysis_button)
        self.view_analysis_button.clicked.connect(self.view_analysis)

        self.save_filter_button = QPushButton('Save Filter')
        buttons_layout.addWidget(self.save_filter_button)
        self.save_filter_button.clicked.connect(self.save_filter)

        self.layout1.addLayout(buttons_layout)

        self.search_bar: QLineEdit = self.parentWidget().findChild(QLineEdit, 'filter_search_lineEdit')
        self.search_bar.textChanged.connect(self.filter_items)

    def filter_items(self, text):
        # Loop through all items in the list widget
        for row in range(self.listWidget.count()):
            item = self.listWidget.item(row)
            # Show or hide items based on the search text
            item.setHidden(text.lower() not in item.text().lower())

    def filter_context_menu(self, pos):
        item = self.listWidget.itemAt(pos)
        if item:
            context_menu = QtWidgets.QMenu()
            delete_action = QAction("Delete", self.listWidget)
            delete_action.triggered.connect(lambda: self.delete_filter(item))
            context_menu.addAction(delete_action)
            context_menu.exec(self.listWidget.mapToGlobal(pos))

    def delete_filter(self, item):
        reply = QMessageBox.question(
            self.listWidget,
            "Confirm Deletion",
            f"Are you sure you want to delete '{item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            row = self.listWidget.row(item)
            self.listWidget.takeItem(row)

            query = QSqlQuery()
            sql_query = """
                    DELETE FROM FilterGroups 
                    WHERE FilterGroupName = :filter_name;
                """
            query.prepare(sql_query)
            query.bindValue(":filter_name", item.text())
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            if not query.exec():
                logger_setup.get_logger().critical(
                    f'Could not delete filter')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            else:
                logger_setup.get_logger().info(f'Filter {item.text()} deleted')

    def populate_filters(self, filter_name):
        query = QSqlQuery()
        sql_query = """
                SELECT SQLQuery, FilterGroupName 
                FROM FilterGroups 
                WHERE FilterGroupName = :filter_name;
            """
        query.prepare(sql_query)
        query.bindValue(":filter_name", filter_name.text())
        logger_setup.get_logger().info(f'Populating QueryBuilder from stored filter: {filter_name.text()}')
        if query.exec():
            if query.next():
                sql_query_result = query.value(0)

                # Rebuild UI
                self.main_group_box.deleteLater()
                self.main_group_box = GroupBox(ast.literal_eval(sql_query_result[1:-1]))
                self.main_group_box.setParent(self)
                self.layout1.insertWidget(0, self.scrollarea)
                self.scrollarea.setWidget(self.main_group_box)
                self.show()
            else:
                logger_setup.get_logger().critical(
                    f'No matching filter group for: {filter_name.text()}')
        else:
            logger_setup.get_logger().critical(
                f'Error in populating existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

    def view_analysis(self):
        filtered_ids = self.get_filtered_ids('UPbAnalyses')
        if filtered_ids is None:
            logger_setup.get_logger().critical(
                f'No matching UPb Analyses for given filter(s)')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'UPbAnalyses')
        dataviewer.setWindowTitle("Filtered Analysis View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_spots(self):
        filtered_ids = self.get_filtered_ids('Spots')
        if filtered_ids is None:
            logger_setup.get_logger().critical(
                f'No matching Spots for given filter(s)')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'Spots')
        dataviewer.setWindowTitle("Filtered Spot View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_aliquots(self):
        filtered_ids = self.get_filtered_ids('Aliquots')
        if filtered_ids is None:
            logger_setup.get_logger().critical(
                f'No matching Aliquots for given filter(s)')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'Aliquots')
        dataviewer.setWindowTitle("Filtered Aliquot View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_samples(self):
        filtered_ids = self.get_filtered_ids('Samples')
        if filtered_ids is None:
            logger_setup.get_logger().critical(
                f'No matching Samples for given filter(s)')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'Samples')
        dataviewer.setWindowTitle("Filtered Sample View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def get_filtered_ids(self, type):
        sql_query = self.get_sql(type)
        query = QSqlQuery()
        logger_setup.get_logger().info('Gathering filtered ids')
        logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        if not query.exec(sql_query):
            logger_setup.get_logger().critical(f'Failed to get filtered ids')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            return None

        results = []
        while query.next():
            results.append(query.value(0))
        logger_setup.get_logger().debug(f'Filtered ids: {results}')
        logger_setup.get_logger().info('Gathered filtered ids successfully')
        return results if results else None

    def get_sql(self, type=None):
        structure = self.main_group_box.get_structure()
        where_clause, cte_list = process_group(my_group)
        full_sql = ""

        if cte_list:
            full_sql += "WITH " + ",\n".join(cte_list) + "\n"



        join = SQLUtils.get_join_from_table("", self.main_group_box.get_tables())
        selects = self.main_group_box.get_selects()

        def extract_as_tables(join):
            as_tables = None
            select_tables = None
            where_tables = None
            if ' AS ' in join:
                pattern = r'\s+\bAS\s+(\w+)'  # regex pattern to match ' AS ' and return the table name right after it
                as_tables = re.findall(pattern, join)
            if '.[' in selects:
                pattern = r'\b(\w+)\.\['  # regex pattern to match the table name before '.['
                select_tables = re.findall(pattern, selects)
            if '.[' in where_clause:
                pattern = r'\b(\w+)\.\['  # regex pattern to match the table name before '.['
                where_tables = re.findall(pattern, where_clause)
            return as_tables, select_tables, where_tables

        as_tables, select_tables, where_tables = extract_as_tables(join)
        if as_tables is not None:
            for as_table in as_tables:
                replace_table = SQLUtils.as_table_dict[as_table]
                if replace_table in select_tables:
                    selects = selects.replace(replace_table, as_table)
                if replace_table in where_tables:
                    where_clause = where_clause.replace(replace_table, as_table)

        if type == 'Samples':
            sql_query = full_sql + f"""
            SELECT DISTINCT SampleID
            FROM Samples
            {join}
            WHERE {where_clause}
            """
        elif type == 'Aliquots':
            join = SQLUtils.get_join_from_table(join, ['Aliquots'])
            sql_query = (
                f"SELECT DISTINCT AliquotID FROM ("
                f"SELECT Aliquots.AliquotID, {selects} "
                f"FROM Samples {join} "
                f"WHERE {where_clause}) "
                f"WHERE AliquotID IS NOT NULL;"
            )
        elif type == 'Spots':
            join = SQLUtils.get_join_from_table(join, ['Spots'])
            sql_query = (
                f"SELECT DISTINCT SpotID FROM ("
                f"SELECT Spots.SpotID, {selects} "
                f"FROM Samples {join} "
                f"WHERE {where_clause}) "
                f"WHERE SpotID IS NOT NULL;"
            )
        elif type == 'UPbAnalyses':
            join = SQLUtils.get_join_from_table(join, ['UPbAnalyses'])
            sql_query = (
                f"SELECT DISTINCT UPbAnalysisID FROM ("
                f"SELECT UPbAnalyses.UPbAnalysisID, {selects} "
                f"FROM Samples {join} "
                f"WHERE {where_clause}) "
                f"WHERE UPbAnalysisID IS NOT NULL;"
            )
        else:
            logger_setup.get_logger().critical(f'Unknown Type Given: {type}')
            return None

        logger_setup.get_logger().debug(f'Filtered SQL command: {sql_query}')
        return sql_query


    def update_filter_list(self):
        self.listWidget.clear()
        query = QSqlQuery()
        sql_query = "SELECT * FROM FilterGroups;"
        logger_setup.get_logger().debug(f'Updating filter list')
        if query.exec(sql_query):
            while query.next():
                item = QListWidgetItem()
                item.setToolTip(query.value(4))  # description
                item.setText(query.value(1))     # FilterGroupName
                self.listWidget.addItem(item)
        else:
            logger_setup.get_logger().info(f'Failed to get all filters from the database')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

    def save_filter(self):
        # if a filter is already selected to the left, ask if the user wants to update it or create a new filter
        if self.listWidget.currentItem():
            filter_name = self.listWidget.currentItem().text()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText(f"Update {filter_name} or create a new filter?")
            msg.setWindowTitle("Update or New")
            cancel_button = QPushButton("Cancel")
            new_button = QPushButton("New")
            update_button = QPushButton("Update")
            msg.addButton(cancel_button, QMessageBox.ButtonRole.RejectRole)
            msg.addButton(new_button, QMessageBox.ButtonRole.AcceptRole)
            msg.addButton(update_button, QMessageBox.ButtonRole.AcceptRole)
            msg.exec()
            reply = msg.clickedButton()
            if reply == cancel_button:
                return
            elif reply == new_button:
                filter_id = None
            elif reply == update_button:
                filter_id = get_id_from_name('FilterGroups', filter_name)
        InsertFilterGroupDialog(self.main_group_box.get_structure(), parent=self).exec()

        self.listWidget.clear()
        self.update_filter_list()