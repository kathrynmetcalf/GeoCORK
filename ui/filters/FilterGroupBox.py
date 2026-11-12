from typing import Literal

from PyQt6 import QtCore
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QGroupBox, QSizePolicy, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QInputDialog

from filters.RuleWidget import RuleWidget
from ui.widgets.FocusWheelComboBox import FocusWheelComboBox

class FilterGroupBox(QGroupBox):
    """
    A GroupBox contains RuleWidgets that either need to Match all, any, or none. A GroupBox can contain other
    GroupBoxes.
    """

    def __init__(self, group=None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.conditions = []
        """RuleWidgets found within this GroupBox"""
        self.subgroups = []
        """Other GroupBoxes found within this GroupBox"""

        self.setTitle('Group')
        self.dummy_label = QLabel(self.title())
        self.updateDummyLabelFont()
        self.layout = QVBoxLayout(self)

        # Group logical operator
        self.group_operator_combo = FocusWheelComboBox()
        self.group_operator_combo.addItems(['Match all', 'Match any', 'Match none'])

        #Adding tooltips
        tooltips = [
            "Returns data fulfilling all rules and subgroup rules",
            "Returns data fulfilling any rule or subgroup rules",
            "Returns data that do not fulfill all rules and subgroup rules"
        ]

        for index, tooltip in enumerate(tooltips):
            self.group_operator_combo.setItemData(index, tooltip, Qt.ItemDataRole.ToolTipRole)

        self.layout.addWidget(self.group_operator_combo)



        # Buttons to add rule or group
        buttons_layout = QHBoxLayout()
        self.add_rule_button = QPushButton('Add rule')
        self.add_rule_button.setToolTip('Add new condition to group')
        self.add_rule_button.clicked.connect(lambda: self.add_rule(None, None, None, None, None))

        self.add_group_button = QPushButton('Add group')
        self.add_group_button.setToolTip('Add new group of rules')
        self.add_group_button.clicked.connect(lambda: self.add_group(None))

        self.delete_button = QPushButton('Delete')
        self.delete_button.setToolTip('Remove group and all rules in it')

        buttons_layout.addWidget(self.add_rule_button)
        buttons_layout.addWidget(self.add_group_button)
        buttons_layout.addWidget(self.delete_button)

        self.layout.addLayout(buttons_layout)
        self.layout.addStretch(1)
        self.populate_from_group(group)

    def populate_from_group(self, group: dict):
        """
        Populates the GroupBox from a given group json dict. If none is provided then add a blank rule by default.
        Group in the format of dict['type': 'Match all|Match any|Match none', 'conditions': list, 'subgroups': list]
        :param group: Group to populate from
        """
        if group is not None:
            self.group_operator_combo.setCurrentText(group['type'])
            # if there are conditions then add them with provided values
            for condition in group.get('conditions', []):
                self.add_rule(condition['field'], condition['operator'], condition['value'], condition['unit'],
                              condition['datatype'])
            for subgroup in group.get('subgroups', []):
                self.add_group(subgroup)
        else:
            self.add_rule(None, None, None, None, None)

    def mouseDoubleClickEvent(self, a0):
        """
        Overridden double click event and test for if the click was on the title of the groupbox to allow
        the user to rename the groupbox
        """
        super().mouseDoubleClickEvent(a0)
        if self.isDoubleClickOnTitle(a0.pos()):
            new_title, ok = QInputDialog.getText(self, "Edit Title", "Enter new title:")
            if ok and new_title:
                self.setTitle(new_title)
                self.updateDummyLabelFont()

    def isDoubleClickOnTitle(self, pos: QtCore.QPoint) -> bool:
        """
        Checks if the given pos is within 10 pixels (width) and 5 pixels (height) of the GroupBox title.
        :param QPoint: pos:
        :return: True if within bounds, False if not
        :rtype: bool
        """
        titleSize = QFontMetrics(self.dummy_label.font()).size(QtCore.Qt.TextFlag.TextSingleLine, self.title())
        titleRect = QRect(0, 0, titleSize.width() + 10, titleSize.height() + 5)
        self.setObjectName(self.title())
        return titleRect.contains(pos)

    def updateDummyLabelFont(self):
        font = self.font()
        font.setBold(True)
        self.dummy_label.setFont(font)

    def add_rule(self, field, operator, value, unit, datatype: Literal['number', 'boolean', 'string', 'date']):
        """
        Adds a rule widget to the GroupBox with provided values.
        :param field: table and attribute in the format of 'table.[attribute]'
        :param operator: operator to set the combobox to
        :param value: value of the line edit
        :param str unit: Not currently used.
        :param str datatype: type of data being inputted
        """
        rule_widget = RuleWidget(field, operator, value, unit, datatype)
        self.layout.insertWidget(self.layout.count() - 1, rule_widget)
        self.conditions.append(rule_widget)
        rule_widget.delete_button.clicked.connect(lambda: self.delete_condition(rule_widget))

    def add_group(self, group):
        """
        Adds a group widget to the GroupBox with provided GroupBox dict.
        :param dict group: dictionary containing groupbox type, conditions, and subgroups
        """
        group_widget = FilterGroupBox(group)
        self.layout.insertWidget(self.layout.count() - 1, group_widget)
        self.subgroups.append(group_widget)
        group_widget.delete_button.clicked.connect(lambda: self.delete_group(group_widget))

    def delete_condition(self, rule_widget):
        """
        Deletes a given RuleWidget object and removes from the list
        :param rule_widget:
        :return:
        """
        rule_widget.deleteLater()
        self.conditions.remove(rule_widget)

    def delete_group(self, group_widget):
        """
        Deletes a given GroupBox object and removes from the list
        :param group_widget:
        :return:
        """
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

    def get_selects(self) -> str:
        """
        Returns a comma-separated string of fields for SELECT statements.
        The format is table.[attribute], table.[attribute].
        """
        list_of_fields = ''
        for ruleWidget in self.findChildren(RuleWidget):
            combined = (ruleWidget.table_combo.currentText().replace(' ', '')
                        + '.[' + ruleWidget.attribute_combo.currentText() + ']')
            if combined not in list_of_fields:
                list_of_fields += combined + ', \n'
        return list_of_fields[0:-3] + '\n'

    def get_tables(self) -> list:
        """
        Returns all unique table names from conditions in this group (and nested subgroups).
        :return: table names
        :rtype: list
        """
        tables = []
        for ruleWidget in self.findChildren(RuleWidget):
            if ruleWidget.table_combo.currentText() not in tables:
                tables.append(ruleWidget.table_combo.currentText())
        return tables