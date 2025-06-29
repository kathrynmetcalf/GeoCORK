import ast
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from typing import Literal, Dict, Tuple, List

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QRect, Qt, QEventLoop, QRegularExpression
from PyQt6.QtGui import QFontMetrics, QAction, QRegularExpressionValidator, \
    QDoubleValidator
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QGroupBox, QLabel,
    QInputDialog, QMessageBox, QScrollArea, QSizePolicy, QListWidget, QDialog, QTextEdit, QListWidgetItem
)
from PyQt6.uic import loadUi

import logger_setup
from Functions import SQLUtils
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.Widget_classes import get_id_from_name, get_headers, get_name_column, get_name_from_id, \
    show_loading_dialog, close_loading_dialog
from ui.DataViewerWidget import DataViewerWidget


def process_json_to_sql(json_string, scope):
    """
    Converts a structured JSON string representing a filter group to a SQL WHERE clause.
    """
    logger_setup.get_logger().debug(f'Processing with scope: {scope}: {json_string}')
    json_string = json_string.replace("'", "\"")
    group = json.loads(json_string)
    where_clause, ctes = process_group(group)

    sql = ''
    if len(ctes) > 0:
        sql += "WITH " + ",\n".join(ctes) + "\n"

    table_names = process_table_names(group)
    join = SQLUtils.get_join_from_table("", table_names)

    def extract_as_tables(join):
        as_tables = None
        select_tables = None
        where_tables = None
        if ' AS ' in join:
            pattern = r'\s+\bAS\s+(\w+)'  # regex pattern to match ' AS ' and return the table name right after it
            as_tables = re.findall(pattern, join)
        if '.[' in where_clause:
            pattern = r'\b(\w+)\.\['  # regex pattern to match the table name before '.['
            where_tables = re.findall(pattern, where_clause)
        return as_tables, select_tables, where_tables

    as_tables, select_tables, where_tables = extract_as_tables(join)
    if as_tables is not None:
        for as_table in as_tables:
            replace_table = SQLUtils.as_table_dict[as_table]
            if replace_table in where_tables:
                where_clause = where_clause.replace(replace_table, as_table)

    if scope == 'Samples':
        sql += f"SELECT * FROM Samples {join} WHERE {where_clause};"
    elif scope == 'Aliquots':
        join = SQLUtils.get_join_from_table(join, ['Aliquots'])
        sql += f"SELECT * FROM Samples {join} WHERE {where_clause};"
    elif scope == 'Spots':
        join = SQLUtils.get_join_from_table(join, ['Spots'])
        sql += f"SELECT * FROM Samples {join} WHERE {where_clause};"
    elif scope == 'UPbAnalyses':
        join = SQLUtils.get_join_from_table(join, ['UPbAnalyses'])
        sql += f"SELECT * FROM Samples {join} WHERE {where_clause};"
    else:
        logger_setup.get_logger().critical(f"Unknown scope: {scope}")
    logger_setup.get_logger().debug(f"SQL generated successfully: {sql}")
    return sql, ctes


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


def extract_table_name(field: str):
    """
    Helper function to extract the table name from a field string.
    :param str field: field in the format of table_name.[attribute_name]
    :return:
    """
    if '.' in field:
        parts = field.split('.')
        return parts[0]
    else:
        return None


def process_group(group: dict) -> Tuple[str, List[str]]:
    """Recursively walk the *group tree* and return (WHERE‑SQL, list‑of‑CTEs)."""

    recursive_tables_counter: Dict[str, int] = defaultdict(int)

    condition_strings, ctes = _process_group_inner(group, recursive_tables_counter)

    match group["type"].lower():
        case "match all":
            glue = " AND "
            where_sql = glue.join(condition_strings)
        case "match any":
            glue = " OR "
            where_sql = glue.join(condition_strings)
        case "match none":
            glue = " AND "
            where_sql = f"NOT {glue.join(condition_strings)}"
        case _:
            raise ValueError(f"Unknown group type: {group['type']}")

    return where_sql, ctes


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _process_group_inner(group: dict, recursive_tables: Dict[str, int]) -> Tuple[List[str], List[str]]:
    """Return (*condition list*, *cte list*) for **one** group (recursive)."""

    # 1) Split conditions: identical field → bucket; else → other list
    identical_field_buckets: Dict[str, List[str]] = defaultdict(list)
    other_conditions: List[str] = []
    ctes: List[str] = []

    for condition in group.get("conditions", []):
        sql_fragment, new_ctes, field_key = _build_single_condition(condition, recursive_tables)
        ctes.extend(new_ctes)

        if group["type"].lower() == "match all" or group["type"].lower() == "match none":
            identical_field_buckets[field_key].append(sql_fragment)
        else:
            other_conditions.append(sql_fragment)

    # 2) Collapse *identical‑field* buckets
    for field_key, conds in identical_field_buckets.items():
        if len(conds) == 1:
            other_conditions.append(conds[0])
            continue

        # --------- special handling: need **all** values on same many‑to‑many
        meta = SQLUtils.tree_tables_schema.get(field_key)
        if meta is None:
            # Non‑tree flat table – fallback to HAVING technique
            collapsed = _collapse_same_field_basic(conds, len(conds))
        else:
            # Tree table (RockTypes, etc.) – build EXISTS per value to enforce AND
            collapsed = f" {'OR' if group["type"].lower() == "match any" else 'AND'} ".join(conds)
        other_conditions.append(collapsed)

    # 3) Sub‑groups ----------------------------------------------------------
    for subgroup in group.get("subgroups", []):
        sub_conds, sub_ctes = _process_group_inner(subgroup, recursive_tables)
        if sub_conds:
            sub_sql = f" {'OR' if subgroup["type"].lower() == "match any" else 'AND'} ".join(sub_conds)
            logic = subgroup["type"].lower()
            if logic == "match all":
                other_conditions.append(f"({sub_sql})")
            elif logic == "match any":
                other_conditions.append(f"({sub_sql})")
            elif logic == "match none":
                other_conditions.append(f"NOT ({sub_sql})")
        ctes.extend(sub_ctes)

    return other_conditions, ctes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_single_condition(condition: dict, recursive_tables: Dict[str, int]) -> Tuple[str, List[str], str]:
    """Return (sql_fragment, new_ctes_list, field_key)."""

    field_key: str = condition["field"].replace(" ", "")
    value = condition["value"]
    operator_raw: str = condition["operator"].lower()
    datatype: str = condition["datatype"]

    operator_sql: str | List[str]
    # ---------- operator mapping (trimmed to the set used in UI) ----------
    if operator_raw in {"is", "is on"}:
        operator_sql = "="
    elif operator_raw in {"is not", "is not on"}:
        operator_sql = "!="
    elif operator_raw == "is blank":
        operator_sql = "IS NULL"
    elif operator_raw == "is not blank":
        operator_sql = "IS NOT NULL"
    elif operator_raw == "contains":
        operator_sql = f"LIKE '%{value}%' COLLATE NOCASE"
    elif operator_raw == "does not contain":
        operator_sql = f"NOT LIKE '%{value}%' COLLATE NOCASE"
    elif operator_raw == "starts with":
        operator_sql = f"LIKE '{value}%' COLLATE NOCASE"
    elif operator_raw == "ends with":
        operator_sql = f"LIKE '%{value}' COLLATE NOCASE"
    elif operator_raw == "is less than":
        operator_sql = "<"
    elif operator_raw == "is greater than":
        operator_sql = ">"
    elif operator_raw == "is between":
        # Range operator – return a list of two conditions
        if datatype == "date":
            operator_sql = [f">= '{value.split(',')[0]}'", f"<= '{value.split(',')[1]}'"]
        elif datatype == "number":
            operator_sql = [f">= {value.split(',')[0]}", f"<= {value.split(',')[1]}"]
        else:
            raise ValueError(f"Unsupported datatype for range operator: {datatype}")
    elif operator_raw == "is not between":
        # Range operator – return a list of two conditions
        if datatype == "date":
            operator_sql = [f"< '{value.split(',')[0]}'", f"> '{value.split(',')[1]}'"]
        elif datatype == "number":
            operator_sql = [f"< {value.split(',')[0]}", f"> {value.split(',')[1]}"]
        else:
            raise ValueError(f"Unsupported datatype for range operator: {datatype}")
    else:
        # … expand as required …
        operator_sql = "="

    # ---------- TREE TABLE? ----------------------------------------------
    if field_key in SQLUtils.tree_tables_schema:
        meta = SQLUtils.tree_tables_schema[field_key]
        table = field_key.split(".")[0]

        # Build *WHERE* on the tree table (equal, like, etc.)
        if isinstance(operator_sql, list):
            raise NotImplementedError("Range operators on tree tables not yet supported")
        elif "NULL" in operator_sql or "LIKE" in operator_sql:
            where = f"{table}.{meta['name_column']} {operator_sql.replace('NOT ','')}"
        elif '!=' in operator_sql:
            where = f"{table}.{meta['name_column']} = '{value}'"
        else:
            where = f"{table}.{meta['name_column']} {operator_sql} '{value}' COLLATE NOCASE"

        # Increment per‑field counter so CTE names stay unique per query
        recursive_tables[field_key] += 1
        cte_name = f"{meta['cte_name']}{recursive_tables[field_key]}"

        cte_sql = f"""
        {cte_name} AS (
            SELECT {meta['id_column']} 
              FROM {table}
             WHERE {where}
            UNION ALL
            SELECT t.{meta['id_column']}
              FROM {table} t
              JOIN {cte_name} r ON t.{meta['parent_column']} = r.{meta['id_column']}
        )""".strip()

        if meta['bridge_table'].split('_')[0] == 'UPbAnalyses':
            # If this is an analysis tag, using EXISTS to much too slow with a large database
            # Instead, we use an IN check
            exists_sql = f"""{meta['bridge_table']}.{meta['bridge_to_column']} {'NOT ' if (operator_sql=='!=' or 'NOT' in operator_sql) else ''}IN 
            (SELECT {meta['bridge_to_column']} FROM {cte_name})"""
        else:
            # ----- AND‑logic uses *EXISTS* to demand **this value present** -----
            exists_sql = f"""{'NOT ' if (operator_sql=='!=' or 'NOT' in operator_sql) else ''}EXISTS (
                SELECT 1
                  FROM {meta['bridge_table']}
                  JOIN {cte_name} ON {meta['bridge_table']}.{meta['bridge_to_column']} = {cte_name}.{meta['bridge_to_column']}
                 WHERE {meta['bridge_table']}.{meta['bridge_from_column']} = {meta['bridge_table'].split('_')[0]}.{meta['bridge_from_column']}
            )"""

        return exists_sql, [cte_sql], field_key

    if isinstance(operator_sql, list):
        # range – not covered in this stub
        raise NotImplementedError("List operators not implemented in stub")
    elif "NULL" in operator_sql or "LIKE" in operator_sql:
        cond_sql = f"{field_key} {operator_sql}"
    else:
        if datatype == "number":
            cond_sql = f"{field_key} {operator_sql} {value}"
        elif datatype == "boolean":
            cond_sql = f"{field_key} {operator_sql} {1 if value == 'True' else 0}"
        else:
            cond_sql = f"{field_key} {operator_sql} '{value}'"

    return cond_sql, [], field_key


def _collapse_same_field_basic(conds: List[str], expected_count: int) -> str:
    """Fallback for flat tables – require **all** values via COUNT‑HAVING.

    Returns a 2‑step SQL fragment:
        1. RockTypeID IN (values …)  (placed in WHERE)
        2. HAVING COUNT(DISTINCT RockTypeID) >= expected_count

    The caller is responsible for appending the HAVING part inside the
    *outermost* SELECT when this helper is used.  In GeoCORK the root SELECT is
    *always* ``Samples`` so we can inline it directly here for simplicity.
    """
    values_block = " OR ".join(conds)  # conds already like "col = 4"
    return f"(({values_block}) GROUP BY Samples.SampleID HAVING COUNT(DISTINCT {get_headers(conds[0].split('.')[0])[0]}) >= {expected_count})"



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


class Filters(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "Filters.ui")
        loadUi(sources_ui_file, self)
        self.querybuilder = QueryBuilder(self)
        self.horizontalLayout_2.addWidget(self.querybuilder)


class InsertFilterGroupDialog(QDialog):
    """
    Assists the user with inserting or updating FilterGroups within the database
    """

    def __init__(self, sql_structure, update_id=None, parent=None):
        """
        :param sql_structure: json dict structure for the filter group
        :param update_id: id of the filter group to update, None if inserting a new one
        :param parent:
        """
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
        """
        Populates the fields with the existing filter group data.
        :return:
        """
        query = QSqlQuery()
        sql_query = """
            SELECT FilterGroupName, FilterGroupDescription 
            FROM FilterGroups 
            WHERE FilterGroupID = :filter_id;
        """
        query.prepare(sql_query)
        query.bindValue(":filter_id", self.update_id)
        logger_setup.get_logger().info(f'Populating fields for filter: {self.update_id}')
        if query.exec():
            if query.next():
                self.name_input.setText(query.value(0))
                self.description_input.setText(query.value(1))
            else:
                filter_name = get_name_from_id('FilterGroups', self.update_id)
                logger_setup.get_logger().critical(f'No filter group "{filter_name}" found.')
                logger_setup.get_logger().debug(f'SQL command: {sql_query}')
        else:
            logger_setup.get_logger().critical(
                f'Error in populating existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

    def insert_data(self):
        """
        Inserts a new filter group into the database. If the name already exists, it prompts the user to update
        the existing one
        """
        name = self.name_input.text()
        description = self.description_input.toPlainText()

        query = QSqlQuery()

        check_query = "SELECT FilterGroupName FROM FilterGroups WHERE FilterGroupName = :name"
        query.prepare(check_query)
        query.bindValue(":name", name)
        logger_setup.get_logger().info(f'Checking if name: {name} already exists in FilterGroups table')
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
        else:
            insert_query = """
                INSERT INTO FilterGroups (FilterGroupName, SQLQuery, FilterGroupDescription)
                VALUES (:name, :sql_query, :description)
            """
            query.prepare(insert_query)
            query.bindValue(":name", name)
            query.bindValue(":sql_query", f'\'{self.sql_structure}\'')
            query.bindValue(":description", None if description=='' else description)

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
    Rulewidget contains the table and attribute comboboxes, operator combobox, value lineedit, and unit combobox.
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
        self.delete_button.clicked.connect(lambda: self.deleteLater())
        self.layout.addWidget(self.delete_button)

    def table_switcher(self) -> None:
        """
        Slot to change the attribute combobox values based on the current text of table combo. E.g. if a
        Samples table is in the table combo, then Samples columns from SQLUtils.table_attributes_dict
        """
        self.attribute_combo.clear()
        self.attribute_combo.addItems(SQLUtils.table_attributes_dict[self.table_combo.currentText()])

    def attribute_switcher(self) -> None:
        """
        Slot to change the operator combobox values based on the current text of attribute combo. E.g. if a
        date column is in the attribute combo, then date operators 'is on, before...' should be visible. Calls
        lineedit switchers and validators so they update.
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

    def lineedit_switcher(self):
        """
        Show or hide the unit combo (Ga, Ma, ka) and set up appropriate validators
        based on the chosen operator/attribute.
        :return:
        """
        # Hide the unit combo by default, show only for numeric/time-based fields
        self.unit_combo.hide()
        self.value_input.clear()

        if 'between' in self.operator_combo.currentText():
            # Date-based fields
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
                case 'number':
                    # Numeric fields
                    double_comma_double_regex = QRegularExpression(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")
                    double_comma_double_validator = QRegularExpressionValidator(double_comma_double_regex)
                    self.value_input.setValidator(double_comma_double_validator)
                    self.value_input.setPlaceholderText("e.g. 0.0,0.0")
                    # Because it's numeric, let's allow the user to pick units (e.g. for an age)
                    # currently not implemented as filters used CalculatedAge values rather than actual values.
                    # the user should know what unit to search in.
                    # self.unit_combo.show()
        else:
            # Single value conditions
            match self.datatype:
                case 'date':
                    # Date-based
                    # todo: Change this to a date selector
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
                    # todo: Change this to a combobox for True/False
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
                    # currently not implemented as filters used CalculatedAge values rather than actual values.
                    # the user should know what unit to search in.
                    # Show units if it's numeric
                    # if "Age" in self.attribute_combo.currentText():
                    # self.unit_combo.show()

    def lineedit_completer(self) -> None:
        """
        Adds a line edit completer based on the current attribute in the combobox. The completer only is created for
        name columns, e.g. SampleName, RockTypeName,... this allows the user to easily select values within the
        database without having to memorize specifics.
        """
        # escape if attribute combo is not set
        if self.attribute_combo.currentText() == "":
            self.value_input.setCompleter(None)
            return
        name_column = get_name_column(self.table_combo.currentText())
        if not name_column:
            self.value_input.setCompleter(None)
            return
        name_header = get_headers(self.table_combo.currentText())[name_column]
        # only add completer if the attribute is a Name header and placeholder text is for strings
        if self.attribute_combo.currentText() == name_header and self.value_input.placeholderText() == "e.g. abc123":
            # Populate the value input with a completer based on the selected attribute
            value_completer = QtWidgets.QCompleter()
            query = QSqlQuery()
            sql_query = f'SELECT DISTINCT {self.attribute_combo.currentText()} FROM "{self.table_combo.currentText()}"'
            if not query.exec(sql_query):
                logger_setup.get_logger().critical(f'Error creating the completer for input')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            values = set()
            while query.next():
                values.add(query.value(0))
            value_completer.setModel(QtCore.QStringListModel(values))
            value_completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
            value_completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            value_completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
            self.value_input.setCompleter(value_completer)


class GroupBox(QGroupBox):
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
        self.layout.addWidget(self.group_operator_combo)

        # Buttons to add rule or group
        buttons_layout = QHBoxLayout()
        self.add_rule_button = QPushButton('Add rule')
        self.add_rule_button.clicked.connect(lambda: self.add_rule(None, None, None, None, None))

        self.add_group_button = QPushButton('Add group')
        self.add_group_button.clicked.connect(lambda: self.add_group(None))

        self.delete_button = QPushButton('Delete')

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
        group_widget = GroupBox(group)
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


class QueryBuilder(QWidget):
    """
    Main Query Builder widget that allows the user to filter and display data. The query builder allows nested
    GroupBoxes to allow full customization. A single root GroupBox is created on initialization and build beneath.
    """

    def __init__(self, parent):
        super().__init__(parent)

        # Filter list widget that stores current filters found in FilterGroups
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

        # the root level GroupBox that all filters are within
        self.main_group_box = GroupBox()
        self.main_group_box.setParent(self)
        self.layout1.addWidget(self.scrollarea)
        self.scrollarea.setWidget(self.main_group_box)

        self.layout1.addWidget(QLabel('Note: Select which view based on desired filtered subset'))

        # views Samples that match the criteria
        buttons_layout = QHBoxLayout(self)
        self.view_samples_button = QPushButton('View Samples')
        buttons_layout.addWidget(self.view_samples_button)
        self.view_samples_button.clicked.connect(self.view_samples)

        # views Aliquots that match the criteria
        self.view_aliquots_button = QPushButton('View Aliquots')
        buttons_layout.addWidget(self.view_aliquots_button)
        self.view_aliquots_button.clicked.connect(self.view_aliquots)

        # views Spots that match the criteria
        self.view_spots_button = QPushButton('View Spots')
        buttons_layout.addWidget(self.view_spots_button)
        self.view_spots_button.clicked.connect(self.view_spots)

        # views UPbAnalyses that match the criteria
        self.view_analyses_button = QPushButton('View Analyses')
        buttons_layout.addWidget(self.view_analyses_button)
        self.view_analyses_button.clicked.connect(self.view_analyses)

        # Saves the current filter
        self.save_filter_button = QPushButton('Save Filter')
        buttons_layout.addWidget(self.save_filter_button)
        self.save_filter_button.clicked.connect(self.save_filter)

        self.layout1.addLayout(buttons_layout)

        self.search_bar: QLineEdit = self.parentWidget().findChild(QLineEdit, 'filter_search_lineEdit')
        self.search_bar.textChanged.connect(self.filter_items)

    def filter_items(self, text: str):
        """
        Filters the list widget of Filters by a given text value
        :param str text:
        """
        # todo: Change this regex
        # Loop through all items in the list widget
        for row in range(self.listWidget.count()):
            item = self.listWidget.item(row)
            # Show or hide items based on the search text
            item.setHidden(text.lower() not in item.text().lower())

    def filter_context_menu(self, pos: QtCore.QPoint):
        """
        Shows the context menu for filters list widget. Allows the user to delete the selected filter.
        :param pos:
        """
        item: QListWidgetItem = self.listWidget.itemAt(pos)
        if item:
            context_menu = QtWidgets.QMenu()
            delete_action = QAction("Delete", self.listWidget)
            delete_action.triggered.connect(lambda: self.delete_filter(item))
            context_menu.addAction(delete_action)
            context_menu.exec(self.listWidget.mapToGlobal(pos))

    def delete_filter(self, item: QListWidgetItem) -> None:
        """
        Deletes a filter from the database and filter list widget given a ListWidgetItem
        :param QListWidgetItem item:
        """
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
                logger_setup.get_logger().critical(
                    f'Could not delete filter')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            else:
                logger_setup.get_logger().info(f'Filter {item.text()} deleted')

    def populate_filters(self, item: QListWidgetItem) -> None:
        """
        Populates the QueryBuilder based on a given filter name.
        :param item: QListWidgetItem containing the name of the filter to populate from
        """
        # query for the SQLQuery and name for a given name
        filter_name = item.text()
        query = QSqlQuery()
        sql_query = """
                SELECT SQLQuery, FilterGroupName 
                FROM FilterGroups 
                WHERE FilterGroupName = :filter_name;
            """
        query.prepare(sql_query)
        query.bindValue(":filter_name", filter_name)
        logger_setup.get_logger().info(f'Populating QueryBuilder from stored filter: {filter_name}')
        if query.exec():
            if query.next():
                sql_query_result = query.value(0)

                # Rebuild UI, delete old groupbox
                self.main_group_box.deleteLater()
                # give the groupbox a sql query to build from
                self.main_group_box = GroupBox(ast.literal_eval(sql_query_result[1:-1]))
                self.main_group_box.setParent(self)
                self.layout1.insertWidget(0, self.scrollarea)
                self.scrollarea.setWidget(self.main_group_box)
                self.show()
            else:
                logger_setup.get_logger().error(
                    f'No matching filter group for: {filter_name}')
        else:
            logger_setup.get_logger().critical(
                f'Error in populating existing Filters')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

    def view_samples(self):
        """
        Opens a DataviewerWidget with Samples filtered IDs.
        """
        filtered_ids = self.get_filtered_ids('Samples')
        if filtered_ids is None:
            QMessageBox.information(self, "No results", f'No matching Samples for given filter(s)')
            return
        if len(set(filtered_ids)) > 1000:
            if not self.view_many_results(len(set(filtered_ids))):
                return
        dataviewer = DataViewerWidget(self, set(filtered_ids), 'Samples')
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_aliquots(self):
        """
        Opens a DataviewerWidget with Aliquots filtered IDs.
        """
        filtered_ids = self.get_filtered_ids('Aliquots')
        if filtered_ids is None:
            QMessageBox.information(self, "No results", f'No matching Aliquots for given filter(s)')
            return
        if len(set(filtered_ids)) > 1000:
            if not self.view_many_results(len(set(filtered_ids))):
                return
        dataviewer = DataViewerWidget(self, set(filtered_ids), 'Aliquots', )
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_spots(self):
        """
        Opens a DataviewerWidget with Spots filtered IDs.
        """
        filtered_ids = self.get_filtered_ids('Spots')
        if filtered_ids is None:
            QMessageBox.information(self, "No results", f'No matching Spots for given filter(s)')
            return
        if len(set(filtered_ids)) > 1000:
            if not self.view_many_results(len(set(filtered_ids))):
                return
        dataviewer = DataViewerWidget(self, set(filtered_ids), 'Spots')
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_analyses(self):
        """
        Opens a DataviewerWidget with UPbAnalyses filtered IDs.
        """
        filtered_ids = self.get_filtered_ids('UPbAnalyses')
        if filtered_ids is None:
            QMessageBox.information(self, "No results", f'No matching UPb Analyses for given filter(s)')
            return
        if len(set(filtered_ids)) > 1000:
            if not self.view_many_results(len(set(filtered_ids))):
                return
        dataviewer = DataViewerWidget(self, set(filtered_ids), 'UPbAnalyses')
        dataviewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        loop = QEventLoop()
        dataviewer.destroyed.connect(loop.quit)
        loop.exec()

    def view_many_results(self, number: int) -> bool:
        """
        Prompts the user if they want to view many results. If they do, it returns True, otherwise False.
        :param number: number of filtered ids
        :return: bool
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle('Many results')
        msg.setText(f'Would you like to view {number} results? This may take a while to load.')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        reply = msg.exec()
        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def get_filtered_ids(self, type) -> list | None:
        """
        Queries the database with the generated filter sql query at the given type scope
        :param str type: Samples, Aliquots, Spots, or UPbAnalyses to query the database for
        :return: list of ids of given type or None
        """
        show_loading_dialog('Filtering', f'Filtering {type} based on current criteria...')
        sql_query = self.get_sql(type)
        uri = f'file:{settings.value('db_file', type=str)}?mode=ro&immutable=1'
        try:
            conn = sqlite3.connect(uri, uri=True)
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                results = [row[0] for row in cursor.fetchall()]
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f"Failed to get filtered ids")
            logger_setup.get_logger().debug(f"Error: {e}")
            logger_setup.get_logger().debug(f"SQL query: {sql_query}")
            return None
        logger_setup.get_logger().debug(f'Filtered ids: {results}')
        logger_setup.get_logger().info('Gathered filtered ids successfully')
        close_loading_dialog('Filtering', f'Filtering {type} based on current criteria...')
        return results if results else None

    def get_sql(self, type: str) -> str:
        """
        Generates a full SQL query based on the given main group box structuree of RuleWidgets and GroupBoxes
        :param type: Samples, Aliquots, Spots, or UPbAnalyses to query the database for
        :return: final SQL query
        :rtype str
        """
        # json dict containing the nested filters
        structure = self.main_group_box.get_structure()
        # converts json to sql
        where_clause, cte_list = process_group(structure)
        full_sql = ""

        # code to allow for tree like tables to work as expected. If a parent item is being filtered, then child
        # items should be included.
        if cte_list:
            full_sql += "WITH " + ",\n".join(cte_list) + "\n"

        # gathers the join statements with found tables
        join = SQLUtils.get_join_from_table("", self.main_group_box.get_tables())
        logger_setup.get_logger().debug(f'SQL Join: {join}')
        selects = self.main_group_box.get_selects()
        logger_setup.get_logger().debug(f'SQL Selects: {selects}')

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

        # final code to determine the scope of query based on type, also ensures the selected type's table is found
        # in the join code
        where = where_clause.replace('Items', 'Samples').replace('ItemID', 'SampleID')

        if type == 'Samples':
            # where = where_clause.replace('Items', 'Samples').replace('ItemID', 'SampleID')
            sql_query = full_sql + f"""
            SELECT DISTINCT Samples.SampleID
            FROM Samples
            {join}
            WHERE {where}
            """
        elif type == 'Aliquots':
            # where = where_clause.replace('Items', 'Aliquots').replace('ItemID', 'AliquotID')
            # Generate join string
            join = SQLUtils.get_join_from_table(join, ['Aliquots'])

            # Recursive CTE: start from records matching `where_clause`, then gather parents
            cte = f"""
            WITH RECURSIVE Aliquots_cte AS (
                SELECT Aliquots.AliquotID, Aliquots.ParentAliquotID
                FROM Samples
                {join}
                WHERE {where}

                UNION ALL

                SELECT a.AliquotID, a.ParentAliquotID
                FROM Aliquots a
                INNER JOIN Aliquots_cte r ON a.AliquotID = r.ParentAliquotID
            )
            """

            aliquot_select = f"""
            SELECT DISTINCT AliquotID FROM (
                SELECT Aliquots.AliquotID, {selects}
                FROM Samples
                {join}
                WHERE Aliquots.AliquotID IN (SELECT AliquotID FROM Aliquots_cte)
            )
            WHERE AliquotID IS NOT NULL;
            """

            # Main query using the CTE
            if cte_list:
                if 'WITH RECURSIVE' in full_sql:
                    sql_query = cte + ',\n' + full_sql.split('WITH RECURSIVE')[1] + aliquot_select
                else:
                    sql_query = cte + ',\n' + full_sql.split('WITH ')[1] + aliquot_select
            else:
                sql_query = cte + aliquot_select
        elif type == 'Spots':
            # where = where_clause.replace('Items', 'Spots').replace('ItemID', 'SpotID')
            join = SQLUtils.get_join_from_table(join, ['Spots'])
            sql_query = full_sql + f"""SELECT DISTINCT SpotID FROM (
                SELECT Spots.SpotID, {selects}
                FROM Samples {join}
                WHERE {where})
                WHERE SpotID IS NOT NULL;"""
        elif type == 'UPbAnalyses':
            # where = where_clause.replace('Items', 'UPbAnalyses').replace('ItemID', 'UPbAnalysisID')
            join = SQLUtils.get_join_from_table(join, ['UPbAnalyses'])
            sql_query = full_sql + f"""SELECT DISTINCT UPbAnalysisID FROM (
                SELECT UPbAnalyses.UPbAnalysisID, {selects}
                FROM Samples {join}
                WHERE {where})
                WHERE UPbAnalysisID IS NOT NULL;"""

        else:
            logger_setup.get_logger().critical(f'Unknown Type Given: {type}')
            return None

        logger_setup.get_logger().debug(f'Filtered SQL command: {sql_query}')

        return sql_query

    def update_filter_list(self):
        """
        Updates the filter list widget by querying the database for filters and repopulating the listwidget.
        """
        self.listWidget.clear()
        query = QSqlQuery()
        sql_query = "SELECT * FROM FilterGroups;"
        logger_setup.get_logger().debug(f'Updating filter list')
        if query.exec(sql_query):
            while query.next():
                item = QListWidgetItem()
                item.setToolTip(query.value(4))  # description
                item.setText(query.value(1))  # FilterGroupName
                self.listWidget.addItem(item)
            self.listWidget.sortItems()
        else:
            logger_setup.get_logger().info(f'Failed to get all filters from the database')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')

    def save_filter(self):
        """
        Saves a filter from the QueryBuilder to the database
        """
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
            InsertFilterGroupDialog(self.main_group_box.get_structure(), update_id=filter_id, parent=self).exec()
        else:
            InsertFilterGroupDialog(self.main_group_box.get_structure(), parent=self).exec()

        self.listWidget.clear()
        self.update_filter_list()
