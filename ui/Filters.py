import ast
import json
import random
import re
import sqlite3

import PyQt6
from PyQt6 import QtCore
from PyQt6.QtCore import QRect, Qt, QEvent, QCoreApplication
from PyQt6.QtGui import QFontMetrics, QScrollEvent, QColor, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QCheckBox, QPushButton, QGroupBox, QLabel,
    QStyleOptionGroupBox, QStyle, QInputDialog, QErrorMessage, QMessageBox, QScrollArea, QSizePolicy, QLayout,
    QListView, QListWidget, QDialog, QColorDialog, QTextEdit, QListWidgetItem, QMainWindow
)


def get_widget(w, d, depth=0, doPrint=False):
    '''
        Recursively searches through all widgets down the tree and prints if desired.
    :param w: the widget to search from
    :param d: the dictionary to add it to
    :param depth: current depth we are at
    :param doPrint: if we need to print
    :return:
    '''
    n = w.objectName()
    n = n if n else str(w)
    if doPrint: print("\t" * depth, n)
    newD = {}
    for widget in w.children():
        get_widget(widget, newD, depth + 1)
    d[n] = newD


def process_group(group):
    """
    Recursively process a group of conditions and subgroups to create a SQL WHERE clause.

    :param group: A dictionary representing the group with keys 'type' and 'conditions'
    :return: A SQL WHERE clause string
    """
    if not group.get('conditions') and not group.get('subgroups'):
        return ''

    # Process conditions in the current group
    condition_strings = []
    for condition in group.get('conditions', []):
        field, operator, value = condition['field'].replace(' ', ''), condition['operator'], condition['value']
        if operator.lower() == "equal":
            operator = "="
        elif operator.lower() == "not equal":
            operator = "!="
        elif operator.lower() == "greater":
            operator = ">"
        elif operator.lower() == "less":
            operator = "<"
        elif operator.lower() == "contains":
            operator = "LIKE"
            condition_string = f"{field} {operator} '%{value}%'"
            condition_strings.append(condition_string)
            continue
        #todo add other operators like 'greater or equal', 'less or equal', etc.
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
    Recursively process a group of conditions and subgroups to create a SQL WHERE clause.

    :param group: A dictionary representing the group with keys 'type' and 'conditions'
    :return: A SQL WHERE clause string
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

    # Combine conditions with the appropriate logical operator
    return fields


# Generate the SQL WHERE clause


# Handling nested expressions with recursion
def parse_sql_to_structure(sql):
    """
    Parses a SQL WHERE clause into a structured format that identifies nested groups and conditions.
    This is a naive implementation intended for demonstration purposes.
    """
    import re

    # Removing leading and trailing parentheses for simplicity in parsing
    sql = sql.strip()

    # Handling nested expressions with recursion
    def parse_expression(expression):
        expression = expression.strip()
        if '(' in expression:
            # Find the first complete group
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
        # Base case: no more nested groups
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


class InsertFilterGroupDialog(QDialog):
    def __init__(self, sql_structure, db_file, parent=None):
        super().__init__(parent)
        self.db_file = db_file
        self.sql_structure = sql_structure

        self.setWindowTitle("Insert New Filter Group")

        # Layout
        layout = QVBoxLayout()

        # Filter Group Name
        self.name_label = QLabel("Filter Group Name:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        # Default Color
        self.color_label = QLabel("Default Color:")
        self.color_display = QLabel(" ")
        self.color_display.setStyleSheet("background-color: white;")
        self.color_picker_button = QPushButton("Pick Color")
        self.color_picker_button.clicked.connect(self.pick_color)
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(self.color_picker_button)
        layout.addWidget(self.color_label)
        layout.addLayout(color_layout)

        # Filter Group Description
        self.description_label = QLabel("Filter Group Description:")
        self.description_input = QTextEdit()
        layout.addWidget(self.description_label)
        layout.addWidget(self.description_input)

        # Buttons
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
        # Collect data from inputs
        name = self.name_input.text()
        color = getattr(self, 'color', '#FFFFFF')  # Default to white if no color selected
        description = self.description_input.toPlainText()

        conn = sqlite3.connect(self.db_file)


        with conn:
            sql_query = f"""
                            INSERT INTO FilterGroups (FilterGroupName, SQLQuery, DefaultColor, FilterGroupDescription)
                            VALUES ('{name}', "'{self.sql_structure}'", '{color}', '{description}');
                            """
            c = conn.cursor()
            c.execute(sql_query)

        conn = sqlite3.connect(self.db_file)
        listWidget: QListWidget = self.parentWidget().parentWidget().findChild(QListWidget, 'listWidget')

        for x in range(len(listWidget.items(None))):
            listWidget.takeItem(x)

        with conn:
            sql_query = """SELECT * FROM FilterGroups;"""
            c = conn.cursor()
            for row in c.execute(sql_query):
                item = QListWidgetItem()
                item.setForeground(QColor(row[3]))
                item.setStatusTip(row[4])
                item.setText(row[1])
                listWidget.addItem(item)

        # Close the dialog
        self.accept()


class FocusWheelComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()


class RuleWidget(QWidget):
    def __init__(self, field=None, operator=None, value=None):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumSize(100, 50)

        # table
        self.table_combo = FocusWheelComboBox()
        self.table_combo.addItems(
            ['Ages', 'Age Signatures', 'Aliquots', 'Aliquot Context', 'Columns', 'Lab Facilities', 'Instruments',
             'Regions', 'RockTypes', 'Sample Context', 'Samples', 'Sampling Methods', 'Settings', 'Sources',
             'Spot Compositions', 'Spot Context', 'UPb Data', 'UPb Analysis Methods', 'Units'])
        self.table_combo.setCurrentIndex(0)
        self.layout.addWidget(self.table_combo)
        if field is not None:
            print(field)
            self.table_combo.setCurrentText(field.split('.')[0])
        self.table_combo.currentIndexChanged.connect(self.table_switcher)

        # attribute
        self.attribute_combo = FocusWheelComboBox()
        self.layout.addWidget(self.attribute_combo)
        self.table_switcher()
        if field is not None:
            self.attribute_combo.setCurrentText(field.split('.')[1])

        # Conditions
        self.operator_combo = FocusWheelComboBox()
        self.operator_combo.addItems(['equal', 'not equal', 'less', 'greater', 'contains'])
        self.layout.addWidget(self.operator_combo)
        if operator is not None:
            self.operator_combo.setCurrentText(operator)

        # Value input
        self.value_input = QLineEdit()
        self.layout.addWidget(self.value_input)
        if value is not None:
            self.value_input.setText(value)

        # Delete button
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(lambda: self.deleteLater())
        self.layout.addWidget(self.delete_button)

    def table_switcher(self):
        print('switched')

        items = list()
        match self.table_combo.currentText():
            case 'Age Signature':
                items = ["SampleContextName",
                         "SampleContextDescription",
                         "SampleContextCreated",
                         "SampleContextModified"]
            case 'Ages':
                items = ["AgeName",
                         "MaxMa",
                         "MinMa",
                         "AgeCreated",
                         "AgeModified"]
            case 'Aliquot Context':
                items = ["AliquotContextName",
                         "AliquotContextDescription",
                         "AliquotContextCreated",
                         "AliquotContextModified"]
            case 'Aliquots':
                items = ["AliquotName",
                         "AliquotCreated",
                         "AliquotModified"]
            case 'Analysis Methods':
                items = ["AnalysisMethodsName",
                         "AnalysisMethodsDescription",
                         "AnalysisMethodsCreated",
                         "AnalysisMethodsModified"]
            case 'Columns':
                items = ["ColumnName",
                         "ColumnDescription",
                         "ColumnCreated",
                         "ColumnModified"]
            case 'Instruments':
                items = ["InstrumentName",
                         "InstrumentDescription",
                         "InstrumentCreated",
                         "InstrumentModified"]
            case 'Lab Facilities':
                items = ["LabFacilityName",
                         "LabFacilityDescription",
                         "LabFacilityCreated",
                         "LabFacilityModified"]
            case 'Regions':
                items = ["RegionName",
                         "RegionDescription",
                         "RegionCreated",
                         "RegionModified"]
            case 'RockTypes':
                items = ["RockTypeName",
                         "RockTypeDescription",
                         "RockTypeCreated",
                         "RockTypeModified"]
            case 'Sample Context':
                items = ["SampleContextName",
                         "SampleContextDescription",
                         "SampleContextCreated",
                         "SampleContextModified"]
            case 'Samples':
                items = ["SampleName",
                         "AverageAge",
                         "AverageAgeError",
                         "ErrorSigma",
                         "OldestAge",
                         "YoungestAge",
                         "OldestAgeID",
                         "YoungestAgeID",
                         "HeightDepth",
                         "HeightDepthError",
                         "HeightDepthUnit",
                         "LatDeg",
                         "LatMin",
                         "LatSec",
                         "LonDeg",
                         "LonMin",
                         "LonSec",
                         "UTMZone",
                         "UTMN",
                         "UTME",
                         "Elev",
                         "ElevError",
                         "ElevUnit",
                         "Description"]
            case 'Sampling Methods':
                items = ["SamplingMethodName",
                         "SamplingMethodDescription",
                         "SamplingMethodCreated",
                         "SamplingMethodModified"]
            case 'Settings':
                items = ["SettingName",
                         "SettingDescription",
                         "SettingCreated",
                         "SettingModified"]
            case 'Sources':
                items = ["Authors",
                         "Year",
                         "Title",
                         "Source",
                         "doi",
                         "ShortCitation",
                         "SourceCreated",
                         "SourceModified"]
            case 'Spot Compositions':
                items = ["SpotCompositionName",
                         "SpotCompositionDescription",
                         "SpotCompositionCreated",
                         "SpotCompositionModified"]
            case 'Spot Context':
                items = ["SpotContextName",
                         "SpotContextDescription",
                         "SpotContextCreated",
                         "SpotContextModified"]
            case 'Spot':
                items = ["SpotName",
                         "SpotCreated",
                         "SpotModified"]
            case 'UPb Analysis Methods':
                items = ["UPbAnalysisMethodName",
                         "UPbAnalysisMethodDescription",
                         "UPbAnalysisMethodCreated",
                         "UPbAnalysisMethodModified"]
            case 'UPb Data':
                items = ["U/Th",
                         "206Pb/204Pb",
                         "206Pb/207Pb",
                         "206Pb/207Pberror",
                         "207Pb/235U",
                         "207Pb/235Uerror",
                         "206Pb/238U",
                         "206Pb/238Uerror",
                         "ErrorCorr",
                         "206Pb/207PbAge",
                         "206Pb/207PbAgeError",
                         "207Pb/235UAge",
                         "207Pb/235UAgeError",
                         "206Pb/238UAge",
                         "206Pb/238UAgeError"]
            case 'Units':
                items = ["UnitName",
                         "UnitDescription",
                         "UnitCreated",
                         "UnitModified"]
        self.attribute_combo.clear()
        self.attribute_combo.addItems(items)


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
        self.add_rule_button.clicked.connect(lambda: self.add_rule(None, None, None))

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
        # Add first rule by default
        if group is not None:
            self.group_operator_combo.setCurrentText(group['type'])
            for condition in group.get('conditions', []):
                self.add_rule(condition['field'], condition['operator'], condition['value'])
            for subgroup in group.get('subgroups', []):
                self.add_group(subgroup)
        else:
            self.add_rule(None, None, None)

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
        # Update dummy label font to match the QGroupBox title font
        font = self.font()
        font.setBold(True)  # Assuming the title is bold; adjust as necessary
        self.dummy_label.setFont(font)

    def add_rule(self, field, operator, value):
        rule_widget = RuleWidget(field, operator, value)
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
        structure = {
            "type": self.group_operator_combo.currentText(),
            "conditions": [],
            "subgroups": [subgroup.get_structure() for subgroup in self.subgroups]
        }
        for condition_widget in self.conditions:
            condition_widget: RuleWidget
            condition = {
                "field": condition_widget.table_combo.currentText() + '.[' + condition_widget.attribute_combo.currentText() + ']',
                "operator": condition_widget.operator_combo.currentText(),
                "value": condition_widget.value_input.text()
            }
            structure["conditions"].append(condition)
        return structure

    def get_selects(self):
        list = ''
        for ruleWidget in self.findChildren(RuleWidget):
            if (ruleWidget.table_combo.currentText().replace(' ',
                                                             '') + '.' + ruleWidget.attribute_combo.currentText()) not in list:
                list = (list + (
                        ruleWidget.table_combo.currentText().replace(' ',
                                                                     '') + '.[' + ruleWidget.attribute_combo.currentText()) +
                        '], \n')
        return list[0:-3] + '\n'

    def get_tables(self):
        list = []
        for ruleWidget in self.findChildren(RuleWidget):
            if (ruleWidget.table_combo.currentText().replace(' ',
                                                             '') + '.' + ruleWidget.attribute_combo.currentText()) not in list:
                list.append(ruleWidget.table_combo.currentText())
        return list


class QueryBuilder(QWidget):
    #todo swap this whole code to QListWidget
    def __init__(self, parent):
        super().__init__(parent)
        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):

                self.db_file = widget.db_file
        conn = sqlite3.connect(self.db_file)
        listWidget: QListWidget = self.parentWidget().findChild(QListWidget, 'listWidget')

        for x in range(len(listWidget.items(None))):
            listWidget.takeItem(x)

        # todo update list widget from sql

        with conn:
            sql_query = """SELECT * FROM FilterGroups;"""
            c = conn.cursor()
            for row in c.execute(sql_query):
                item = QListWidgetItem()
                item.setForeground(QColor(row[3]))
                item.setToolTip(row[4])
                item.setText(row[1])
                listWidget.addItem(item)

        listWidget.itemDoubleClicked.connect(lambda state: self.populate_filters(state))

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

        buttons_layout = QHBoxLayout(self)

        # Apply button
        self.apply_button = QPushButton('Apply')
        buttons_layout.addWidget(self.apply_button)
        self.apply_button.clicked.connect(self.get_sql)

        # Save filter button
        self.save_filter_button = QPushButton('Save Filter')
        buttons_layout.addWidget(self.save_filter_button)
        self.save_filter_button.clicked.connect(self.save_filter)

        self.layout1.addLayout(buttons_layout)

        self.qsample_id = 'S.SampleID'
        self.qsample_name = 'SampleName AS "Sample Name"'
        self.qage = 'AverageAge || "±" || COALESCE(AverageAgeError, " ") as "Age (Ma)"'
        self.qage_range = 'COALESCE(OldestAge, " ") || "-" || COALESCE(YoungestAge, " ") as "Age Range (Ma)"'
        self.qgeo_age = 'COALESCE(OldA.AgeName, " ") || "-" || COALESCE(YoungA.AgeName, " ") as "Geologic Age"'
        self.qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures"'
        self.qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) as "Measured Column Name"'
        self.qcolumn_data = 'HeightDepth || "±" || COALESCE(HeightDepthError, " " || HeightDepthUnit) as "Column Data"'
        self.qlat = f'''LatDeg || "°" || LatMin || "'" || LatSec || '"' as "Latitude"'''
        self.qlon = f'''LonDeg || "°" || LonMin || "'" || LonSec || '"' as "Longitude"'''
        self.qutm_zone = 'UTMZone As "UTM Zone"'
        self.qutm_n = 'UTMN As "UTM Northing"'
        self.qutm_e = 'UTME As "UTM Easting"'
        self.qelev = 'Elev || "±" || COALESCE(ElevError, " " || ElevUnit) as "Elevation"'
        self.qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots"'
        self.qspots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        self.qreferences = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        self.qcontext = 'GROUP_CONCAT(DISTINCT SampleContextName) as "Sample Context"'
        self.qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) as "Sampling Method"'
        self.qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"'
        self.qregions = 'GROUP_CONCAT(DISTINCT RegionName) as "Regions"'
        self.qsettings = 'GROUP_CONCAT(DISTINCT SettingName) as "Settings"'
        self.qunits = 'GROUP_CONCAT(DISTINCT UnitName) as "Units"'
        self.qupb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        self.qlabs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'
        self.qspot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Context"'
        self.qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        self.qaliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Context"'

        # Join lines
        self.old_age_join = 'LEFT JOIN Ages ON Samples.OldestAgeID=Ages.AgeID'
        self.young_age_join = 'LEFT JOIN Ages ON Samples.YoungestAgeID=Ages.AgeID'
        self.age_signature_join = '''LEFT JOIN Samples_AgeSignatures ON Samples.SampleID=Samples_AgeSignatures.SampleID
                                            LEFT JOIN AgeSignatures ON AgeSignatures.AgeSignatureID=Samples_AgeSignatures.AgeSignatureID'''
        self.column_join = '''LEFT JOIN Samples_Columns ON Samples.SampleID=Samples_Columns.SampleID
                                            LEFT JOIN Columns ON Columns.ColumnID=Samples_Columns.ColumnID'''
        self.rock_type_join = '''LEFT JOIN Samples_RockTypes ON Samples.SampleID=Samples_RockTypes.SampleID
                                        LEFT JOIN RockTypes ON RockTypes.RockTypeID=Samples_RockTypes.RockTypeID'''
        self.region_join = '''LEFT JOIN Samples_Regions ON Samples.SampleID=Samples_Regions.SampleID
                                        LEFT JOIN Regions ON Regions.RegionID=Samples_Regions.RegionID'''
        self.setting_join = '''LEFT JOIN Samples_Settings ON Samples.SampleID=Samples_Settings.SampleID
                                        LEFT JOIN Settings ON Settings.SettingID=Samples_Settings.SettingID'''
        self.unit_join = '''LEFT JOIN Samples_Units ON Samples.SampleID=Samples_Units.SampleID
                                        LEFT JOIN Units ON Units.UnitID=Samples_Units.UnitID'''
        self.sample_context_join = '''LEFT JOIN Samples_SampleContext ON Samples.SampleID=Samples_SampleContext.SampleID
                                        LEFT JOIN SampleContext ON SampleContext.SampleContextID=Samples_SampleContext.SampleContextID'''
        self.sampling_method_join = '''LEFT JOIN Samples_SamplingMethods ON Samples.SampleID=Samples_SamplingMethods.SampleID
                                        LEFT JOIN SamplingMethods ON SamplingMethods.SamplingMethodID=Samples_SamplingMethods.SamplingMethodID'''

        self.aliquot_join = 'LEFT JOIN Aliquots ON Aliquots.SampleID=Samples.SampleID'
        self.spot_join = 'LEFT JOIN Spots ON Spots.AliquotID=Aliquots.AliquotID'
        self.upb_data_join = 'LEFT JOIN UPbData ON UPbData.SpotID=Spots.SpotID'
        self.source_join = 'LEFT JOIN Sources ON Sources.SourceID=UPbData.SourceID'
        self.upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalysisMethods.UPbAnalysisMethodID=UPbData.UPbAnalysisMethodID'
        self.instruments_join = 'LEFT JOIN Instruments ON Instruments.InstrumentID=UPbData.InstrumentID'
        self.labs_join = 'LEFT JOIN LabFacilities ON LabFacilities.LabFacilityID=UPbData.LabFacilityID'
        self.spot_context_join = '''LEFT JOIN Spots_SpotContext ON Spots.SpotID=Spots_SpotContext.SpotID
                                        LEFT JOIN SpotContext ON SpotContext.SpotContextID=Spots_SpotContext.SpotContextID'''
        self.spot_composition_join = '''LEFT JOIN SpotCompositions ON SpotCompositions.SpotCompositionID=Spots.SpotCompositionID'''
        self.aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContext ON Aliquots.AliquotID=Aliquots_AliquotContext.AliquotID
                                        LEFT JOIN AliquotContext ON AliquotContext.AliquotContextID=Aliquots_AliquotContext.AliquotContextID'''

    def populate_filters(self, filter_name):
        conn = sqlite3.connect(self.db_file)
        with conn:
            sql_query = f"""SELECT SQLQuery, FilterGroupName FROM FilterGroups WHERE FilterGroupName = '{filter_name.text()}';"""
            c = conn.cursor()
            row = c.execute(sql_query).fetchall()
            self.main_group_box.deleteLater()
            self.main_group_box = GroupBox(ast.literal_eval(row[0][0][1:-1]))
            self.main_group_box.setParent(self)
            self.layout1.insertWidget(0, self.scrollarea)
            self.scrollarea.setWidget(self.main_group_box)
            self.show()

    def get_sql(self):
        structure = self.main_group_box.get_structure()
        where_clause = process_group(structure)

        join = ""

        for table in self.main_group_box.get_tables():
            match (table):
                case 'Ages':
                    if self.old_age_join not in join:
                        join += self.old_age_join + '\n'
                case 'Age Signatures':
                    if self.age_signature_join not in join:
                        join += self.age_signature_join + '\n'
                case 'Aliquots':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                case 'Aliquot Context':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.aliquot_context_join not in join:
                        join += self.aliquot_context_join + '\n'
                case 'Columns':
                    if self.column_join not in join:
                        join += self.column_join + '\n'
                case 'Lab Facilities':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.spot_join not in join:
                        join += self.spot_join + '\n'
                    if self.upb_data_join not in join:
                        join += self.upb_data_join + '\n'
                    if self.labs_join not in join:
                        join += self.labs_join + '\n'
                case 'Instruments':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.spot_join not in join:
                        join += self.spot_join + '\n'
                    if self.upb_data_join not in join:
                        join += self.upb_data_join + '\n'
                    if self.instruments_join not in join:
                        join += self.instruments_join + '\n'
                case 'Regions':
                    if self.region_join not in join:
                        join += self.region_join + '\n'
                case 'RockTypes':
                    if self.rock_type_join not in join:
                        join += self.rock_type_join + '\n'
                case 'Sample Context':
                    if self.sample_context_join not in join:
                        join += self.sample_context_join + '\n'
                case 'Samples':
                    pass
                case 'Sampling Methods':
                    if self.sampling_method_join not in join:
                        join += self.sampling_method_join + '\n'
                case 'Settings':
                    if self.setting_join not in join:
                        join += self.setting_join + '\n'
                case 'Sources':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.spot_join not in join:
                        join += self.spot_join + '\n'
                    if self.upb_data_join not in join:
                        join += self.upb_data_join + '\n'
                    if self.source_join not in join:
                        join += self.source_join + '\n'
                case 'Spot Compositions':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.spot_join not in join:
                        join += self.spot_join + '\n'
                    if self.spot_composition_join not in join:
                        join += self.spot_composition_join + '\n'
                case 'Spot Context':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.spot_join not in join:
                        join += self.spot_join + '\n'
                    if self.spot_context_join not in join:
                        join += self.spot_context_join + '\n'
                case 'UPb Data':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.spot_join not in join:
                        join += self.spot_join + '\n'
                    if self.upb_data_join not in join:
                        join += self.upb_data_join + '\n'
                case 'UPb Analysis Methods':
                    if self.aliquot_join not in join:
                        join += self.aliquot_join + '\n'
                    if self.spot_join not in join:
                        join += self.spot_join + '\n'
                    if self.upb_data_join not in join:
                        join += self.upb_data_join + '\n'
                    if self.upb_method_join not in join:
                        join += self.upb_method_join + '\n'
                case 'Units':
                    if self.unit_join not in join:
                        join += self.unit_join + '\n'
        # Final SQL query

        sql_query = f"SELECT DISTINCT SampleID FROM (SELECT Samples.SampleID, {self.main_group_box.get_selects()} FROM Samples {join} WHERE {where_clause});"
        return sql_query

    def save_filter(self):
        InsertFilterGroupDialog(self.main_group_box.get_structure(), self.db_file, self).exec()
