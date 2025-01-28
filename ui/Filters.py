import ast
import json

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QRect, Qt, QEventLoop, QRegularExpression
from PyQt6.QtGui import QFontMetrics, QColor, QAction, QRegularExpressionValidator, \
    QDoubleValidator
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QGroupBox, QLabel,
    QInputDialog, QMessageBox, QScrollArea, QSizePolicy, QListWidget, QDialog, QColorDialog, QTextEdit, QListWidgetItem
)
from PyQt6.uic import loadUi

from Functions import SQLUtils
from ui.DataViewerWidget import DataViewerWidget


def process_json_to_sql(json_string, scope):
    """
    Converts a structured JSON string representing a filter group to a SQL WHERE clause.
    """
    json_string = json_string.replace("'", "\"")
    group = json.loads(json_string)
    where = process_group(group)

    table_names = process_table_names(group)
    join = SQLUtils.get_join_from_table(table_names)
    if scope == 'Samples':
        return f"SELECT * FROM Samples {join} WHERE {where};"
    elif scope == 'Aliquots':
        join = SQLUtils.get_join_from_table(['Aliquots'])
        return f"SELECT * FROM Aliquots {join} WHERE {where};"
    elif scope == 'Spots':
        join = SQLUtils.get_join_from_table(['Spots'])
        return f"SELECT * FROM Spots {join} WHERE {where};"
    elif scope == 'UPbData':
        join = SQLUtils.get_join_from_table(['UPbAnalyses'])
        return f"SELECT * FROM UPbAnalyses {join} WHERE {where};"


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
    return table_names


def extract_table_name(field):
    if '.' in field:
        parts = field.split('.')
        return parts[0]
    else:
        return None


def process_group(group):
    """
    Recursively process a group of conditions and subgroups to create a SQL WHERE clause.
    """
    if not group.get('conditions') and not group.get('subgroups'):
        return ''

    # Process conditions in the current group
    condition_strings = []
    for condition in group.get('conditions', []):
        field, operator, value, unit = condition['field'].replace(' ', ''), condition['operator'], condition['value'], condition['unit']
        if unit == 'None':
            pass
        elif unit == 'Ga':
            value = f"{float(value) * 1000000000}"
        elif unit == 'Ma':
            value = f"{float(value) * 1000000}"
        elif unit == 'ka':
            value = f"{float(value) * 1000}"
        else:
            raise ValueError(f"Unknown unit: {unit}")

        if operator.lower() == "is" or operator.lower() == "is on":
            operator = "="
        elif operator.lower() == "is not" or operator.lower() == "is not on":
            operator = "!="
        elif operator.lower() == "is greater than" or operator.lower() == "is after":
            operator = ">"
        elif operator.lower() == "is less than" or operator.lower() == "is before":
            operator = "<"
        elif operator.lower() == "is blank":
            operator = "IS NULL"
            condition_string = f"{field} {operator}"
            condition_strings.append(condition_string)
            continue
        elif operator.lower() == "is not blank":
            operator = "NOT NULL"
            condition_string = f"{field} {operator}"
            condition_strings.append(condition_string)
            continue
        elif operator.lower() == "contains":
            operator = "LIKE"
            condition_string = f"{field} {operator} '%{value}%'"
            condition_strings.append(condition_string)
            continue
        elif operator.lower() == "does not contain":
            operator = "NOT LIKE"
            condition_string = f"{field} {operator} '%{value}%'"
            condition_strings.append(condition_string)
            continue
        elif operator.lower() == "starts with":
            operator = "LIKE"
            condition_string = f"{field} {operator} '{value}%'"
            condition_strings.append(condition_string)
            continue
        elif operator.lower() == "ends with":
            operator = "LIKE"
            condition_string = f"{field} {operator} '%{value}'"
            condition_strings.append(condition_string)
            continue
        elif operator.lower() == "is between":
            operator = "BETWEEN"
            value1, value2 = value.split(',')
            condition_string = f"{field} {operator} '{value1}' AND '{value2}'"
            condition_strings.append(condition_string)
            continue
        elif operator.lower() == "is not between":
            operator = "NOT BETWEEN"
            value1, value2 = value.split(',')
            condition_string = f"{field} {operator} '{value1}' AND '{value2}'"
            condition_strings.append(condition_string)
            continue

        condition_string = f"{field} {operator} '{value}'"
        condition_strings.append(condition_string)

    # Process subgroups recursively
    for subgroup in group.get('subgroups', []):
        subgroup_string = process_group(subgroup)
        if subgroup_string:
            condition_strings.append(subgroup_string)

    # Combine conditions with the appropriate logical operator
    if group['type'].lower() == "match all":
        return f"({' AND '.join(condition_strings)})"
    elif group['type'].lower() == "match any":
        return f"({' OR '.join(condition_strings)})"
    elif group['type'].lower() == "match none":
        return f"NOT ({' AND '.join(condition_strings)})"
    else:
        raise ValueError(f"Unknown group type: {group['type']}")


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


def parse_sql_to_structure(sql):
    """
    (Demonstration) Parses a SQL WHERE clause into a structured format.
    """
    import re

    sql = sql.strip()

    def parse_expression(expression):
        expression = expression.strip()
        if '(' in expression:
            depth, start = 0, None
            for i, char in enumerate(expression):
                if char == '(':
                    if depth == 0:
                        start = i
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        subgroup = parse_expression(expression[start + 1:i])
                        return [subgroup] + parse_expression(expression[i + 1:])
        return [parse_conditions(expression)]

    def parse_conditions(conditions):
        conditions = re.split(r'\s(AND|OR)\s', conditions)
        structured_conditions = []
        operator = None
        for condition in conditions:
            if condition.upper() in ['AND', 'OR']:
                operator = condition
            else:
                parts = condition.split()
                if len(parts) >= 3:
                    field = parts[0]
                    op = parts[1]
                    value = ' '.join(parts[2:]).strip("'")
                    structured_conditions.append({'field': field, 'operator': op, 'value': value, 'logic': operator})
                    operator = None
        return structured_conditions

    return parse_expression(sql)

class Filters(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        sources_ui_file = "ui/Filters.ui"
        loadUi(sources_ui_file, self)
        self.querybuilder = QueryBuilder(self)
        self.horizontalLayout_2.addWidget(self.querybuilder)

class InsertFilterGroupDialog(QDialog):
    def __init__(self, sql_structure, db_file, parent=None):
        super().__init__(parent)
        self.db_file = db_file
        self.sql_structure = sql_structure

        self.setWindowTitle("Insert New Filter Group")

        layout = QVBoxLayout()
        self.name_label = QLabel("Filter Group Name:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        self.warning_label = QLabel()
        layout.addWidget(self.warning_label)

        self.color_label = QLabel("Default Color:")
        self.color_display = QLabel(" ")
        self.color_display.setStyleSheet("background-color: white;")
        self.color_picker_button = QPushButton("Pick Color")
        # todo set default color to be transparent so it shows regardless of user dark/light mode
        self.color_picker_button.clicked.connect(self.pick_color)
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(self.color_picker_button)
        layout.addWidget(self.color_label)
        layout.addLayout(color_layout)

        self.description_label = QLabel("Filter Group Description:")
        self.description_input = QTextEdit()
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_input)

        self.insert_button = QPushButton("Insert")
        self.insert_button.clicked.connect(self.insert_data)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.insert_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_display.setStyleSheet(f"background-color: {color.name()};")
            self.color = color.name()

    def insert_data(self):
        name = self.name_input.text()
        color = getattr(self, 'color', '#FFFFFF')
        description = self.description_input.toPlainText()

        db = QSqlDatabase.database()
        if not db.isOpen():
            self.warning_label.show()
            self.warning_label.setText('<font color="red">Database is not open</font>')
            self.warning_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return

        query = QSqlQuery()

        check_query = "SELECT FilterGroupName FROM FilterGroups WHERE FilterGroupName = :name"
        query.prepare(check_query)
        query.bindValue(":name", name)
        if not query.exec():
            self.warning_label.show()
            self.warning_label.setText('<font color="red">Failed to execute query</font>')
            self.warning_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return

        if query.next():
            self.warning_label.show()
            self.warning_label.setText('<font color="red">Name must be unique</font>')
            self.warning_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            insert_query = """
                INSERT INTO FilterGroups (FilterGroupName, SQLQuery, DefaultColor, FilterGroupDescription)
                VALUES (:name, :sql_query, :color, :description)
            """
            query.prepare(insert_query)
            query.bindValue(":name", name)
            query.bindValue(":sql_query", f'\'{self.sql_structure}\'')
            query.bindValue(":color", color)
            query.bindValue(":description", description)

            if not query.exec():
                self.warning_label.show()
                self.warning_label.setText('<font color="red">Failed to insert data</font>')
                self.warning_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                self.accept()
        db.commit()


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
    def __init__(self, field=None, operator=None, value=None, unit=None):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumSize(100, 50)

        # Table combo
        self.table_combo = FocusWheelComboBox()
        self.table_combo.addItems(SQLUtils.user_viewable_tables)
        self.table_combo.setCurrentIndex(0)
        self.layout.addWidget(self.table_combo)
        self.table_combo.currentIndexChanged.connect(self.table_switcher)

        # Attribute combo
        self.attribute_combo = FocusWheelComboBox()
        self.layout.addWidget(self.attribute_combo)
        self.table_switcher()
        self.attribute_combo.currentIndexChanged.connect(self.attribute_switcher)

        # Operator combo
        self.operator_combo = FocusWheelComboBox()
        self.attribute_switcher()
        self.layout.addWidget(self.operator_combo)
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
        if field is not None:
            self.attribute_combo.setCurrentText(field.split('.')[1][1:-1])
        if operator is not None:
            self.operator_combo.setCurrentText(operator)
        if value is not None:
            self.value_input.setText(value)
        if unit is not None:
            self.unit_combo.setCurrentText(unit)

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
            if "Created" in self.attribute_combo.currentText() or "Modified" in self.attribute_combo.currentText():
                date_range_regex = QRegularExpression(
                    r"^(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01]),"
                    r"(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$"
                )
                date_range_validator = QRegularExpressionValidator(date_range_regex)
                self.value_input.setValidator(date_range_validator)
                self.value_input.setPlaceholderText("e.g. YYYY-MM-DD,YYYY-MM-DD")
            else:
                # Numeric fields
                double_comma_double_regex = QRegularExpression(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")
                double_comma_double_validator = QRegularExpressionValidator(double_comma_double_regex)
                self.value_input.setValidator(double_comma_double_validator)
                self.value_input.setPlaceholderText("e.g. 0.0,0.0")
                # Because it's numeric, let's allow the user to pick units (e.g. for an age)
                self.unit_combo.show()
        else:
            # Single value conditions
            if "Created" in self.attribute_combo.currentText() or "Modified" in self.attribute_combo.currentText():
                # Date-based
                date_range_regex = QRegularExpression(
                    r"^(?:(?:19|20)\d{2})-(?:(?:0[1-9]|1[0-2]))-(?:0[1-9]|[12][0-9]|3[01])$"
                )
                date_range_validator = QRegularExpressionValidator(date_range_regex)
                self.value_input.setPlaceholderText("e.g. YYYY-MM-DD")
                self.value_input.setValidator(date_range_validator)
            elif (("Description" in self.attribute_combo.currentText() or
                   "Name" in self.attribute_combo.currentText() or
                   "ErrorSigma" in self.attribute_combo.currentText() or
                   "Unit" in self.attribute_combo.currentText()) or
                  self.table_combo.currentText() == '"References"'):
                # Text-based
                self.value_input.setPlaceholderText("e.g. abc123")
                self.value_input.setValidator(None)  # No numeric validator
            else:
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

    def attribute_switcher(self):
        """
        Based on the attribute selected, populate the operator combo.
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
            return
        elif ("Description" in self.attribute_combo.currentText() or
              "Name" in self.attribute_combo.currentText() or
              "ErrorSigma" in self.attribute_combo.currentText() or
              "Unit" in self.attribute_combo.currentText() or
              self.table_combo.currentText() == "Sources"):
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
            return
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
            return

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
        self.add_rule_button.clicked.connect(lambda: self.add_rule(None, None, None, None))

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
                self.add_rule(condition['field'], condition['operator'], condition['value'], condition['unit'])
            for subgroup in group.get('subgroups', []):
                self.add_group(subgroup)
        else:
            self.add_rule(None, None, None, None)

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

    def add_rule(self, field, operator, value, unit):
        #todo not populating line edit with value
        rule_widget = RuleWidget(field, operator, value, unit)
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
                "unit": condition_widget.unit_combo.currentText()
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
            if not query.exec():
                print("Failed to execute query:", query.lastError().text())
            else:
                print(f"Filter group '{item.text()}' successfully deleted.")

    def populate_filters(self, filter_name):
        query = QSqlQuery()
        sql_query = """
                SELECT SQLQuery, FilterGroupName 
                FROM FilterGroups 
                WHERE FilterGroupName = :filter_name;
            """
        query.prepare(sql_query)
        query.bindValue(":filter_name", filter_name.text())

        if query.exec():
            if query.next():
                sql_query_result = query.value(0)
                filter_group_name = query.value(1)

                # Rebuild UI
                self.main_group_box.deleteLater()
                self.main_group_box = GroupBox(ast.literal_eval(sql_query_result[1:-1]))
                self.main_group_box.setParent(self)
                self.layout1.insertWidget(0, self.scrollarea)
                self.scrollarea.setWidget(self.main_group_box)
                self.show()
            else:
                print("No matching filter group found.")
        else:
            print("Failed to execute query:", query.lastError().text())

    def view_analysis(self):
        filtered_ids = self.get_filtered_ids('upbdata')
        if filtered_ids is None:
            self.display_no_ids_error('upb data')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'upbdata')
        dataviewer.setWindowTitle("Filtered Analysis View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_spots(self):
        filtered_ids = self.get_filtered_ids('spot')
        if filtered_ids is None:
            self.display_no_ids_error('spot')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'spot')
        dataviewer.setWindowTitle("Filtered Spot View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_aliquots(self):
        filtered_ids = self.get_filtered_ids('aliquot')
        if filtered_ids is None:
            self.display_no_ids_error('aliquot')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'aliquot')
        dataviewer.setWindowTitle("Filtered Aliquot View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_samples(self):
        filtered_ids = self.get_filtered_ids('sample')
        if filtered_ids is None:
            self.display_no_ids_error('sample')
            return
        dataviewer = DataViewerWidget(filtered_ids, 'sample')
        dataviewer.setWindowTitle("Filtered Sample View")
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def get_filtered_ids(self, type):
        sql_query = self.get_sql(type)
        query = QSqlQuery()
        if not query.exec(sql_query):
            print("Failed to execute query:", query.lastError().text())
            return None

        results = []
        while query.next():
            results.append(tuple(query.value(i) for i in range(query.record().count())))

        return results if results else None

    def get_sql(self, type=None):
        structure = self.main_group_box.get_structure()
        where_clause = process_group(structure)
        join = ""
        join += SQLUtils.get_join_from_table(self.main_group_box.get_tables())
        print('join is, ', join)


        if type == 'sample':
            sql_query = (
                f"SELECT DISTINCT SampleID FROM ("
                f"SELECT Samples.SampleID, {self.main_group_box.get_selects()} "
                f"FROM Samples {join} "
                f"WHERE {where_clause});"
            )
        elif type == 'aliquot':
            join += SQLUtils.get_join_from_table(['Aliquots'])
            sql_query = (
                f"SELECT DISTINCT AliquotID FROM ("
                f"SELECT Aliquots.AliquotID, {self.main_group_box.get_selects()} "
                f"FROM Samples {join} "
                f"WHERE {where_clause}) "
                f"WHERE AliquotID IS NOT NULL;"
            )
        elif type == 'spot':
            join += SQLUtils.get_join_from_table(['Spots'])
            sql_query = (
                f"SELECT DISTINCT SpotID FROM ("
                f"SELECT Spots.SpotID, {self.main_group_box.get_selects()} "
                f"FROM Samples {join} "
                f"WHERE {where_clause}) "
                f"WHERE SpotID IS NOT NULL;"
            )
        elif type == 'upbdata':
            join += SQLUtils.get_join_from_table(['UPbAnalyses'])
            sql_query = (
                f"SELECT DISTINCT UPbAnalysisID FROM ("
                f"SELECT UPbAnalyses.UPbAnalysisID, {self.main_group_box.get_selects()} "
                f"FROM Samples {join} "
                f"WHERE {where_clause}) "
                f"WHERE UPbAnalysisID IS NOT NULL;"
            )
        else:
            print("Unknown Type Given")
            return None

        print(sql_query)
        return sql_query

    def display_no_ids_error(self, type):
        QMessageBox.critical(self, "No IDs Found", f"No {type} IDs were found matching the criteria.")

    def update_filter_list(self):
        self.listWidget.clear()
        query = QSqlQuery()
        sql_query = "SELECT * FROM FilterGroups;"
        if query.exec(sql_query):
            while query.next():
                item = QListWidgetItem()
                item.setForeground(QColor(query.value(3)))  # color
                item.setToolTip(query.value(4))  # description
                item.setText(query.value(1))     # FilterGroupName
                self.listWidget.addItem(item)
        else:
            print("Failed to execute query:", query.lastError().text())

    def save_filter(self):
        InsertFilterGroupDialog(self.main_group_box.get_structure(), self).exec()

        self.listWidget.clear()
        self.update_filter_list()