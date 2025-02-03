import os
import sys
from collections import Counter

import pandas
from PyQt6 import QtCore
from PyQt6.QtCore import QSettings, QSortFilterProxyModel
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableView,
    QGridLayout, QLabel, QCheckBox, QSpacerItem,
    QSizePolicy, QTabWidget, QInputDialog, QDialog, QListWidget, QHBoxLayout, QMessageBox, QComboBox, QErrorMessage,
    QGroupBox, QScrollArea
)
from PyQt6.uic import loadUi
from openpyxl import Workbook

from ui.FlowLayout import FlowLayout, ScrollableFlowWidget
from Functions import ExportDatabase
from Functions import FilterDatabase
from Functions import SQLUtils
from Functions.Table_classes import CheckableSqlTableModel, CheckableComboBox
from ui import Filters


class ExportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "ExporterUI.ui")
        loadUi(sources_ui_file, self)

        self.checked_filter_list = []

        self.checked_sample_list = []
        self.checked_aliquot_list = []
        self.checked_spot_list = []

        self.checked_sample_names = '()'
        self.checked_aliquot_names = '()'
        self.checked_spot_names = '()'

        # Initialize a dictionary to store data for each workbook tab
        self.worksheet_tabs_dict = {}

        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.db_file = widget.db_file

        self.settings = QSettings("CSUF", "GeoChron")

        self.samplesincluded_comboBox: CheckableComboBox()

        # Connect buttons to methods
        self.add_workbook_button.clicked.connect(lambda: self.add_worksheet_tab(None, False, False, None))
        self.remove_workbook_button.clicked.connect(self.remove_current_worksheet_tab)
        self.export_pushbutton.clicked.connect(self.export_button)

        self.columnselection_comboBox.addItems(SQLUtils.table_attributes_dict)

        self.samples_model = CheckableSqlTableModel()
        self.samples_model = self.set_table(self.samples_model, 'Samples')

        self.aliquots_model = CheckableSqlTableModel()
        self.aliquots_model = self.set_table(self.aliquots_model, 'Aliquots')

        self.spots_model = CheckableSqlTableModel()
        self.spots_model = self.set_table(self.spots_model, 'Spots')

        self.filter_model = CheckableSqlTableModel()
        self.filter_model = self.set_table(self.filter_model, 'FilterGroups')
        self.filterselection_comboBox.setModel(self.filter_model)

        # Fix for updating the filter list when the filter model is updated
        self.filter_model.dataChanged.connect(lambda: self.update_filter_list(self.filter_model))

        self.update_step_2_list()
        self.populate_stack()
        self.export_format()

        self.editorder_pushbutton.clicked.connect(self.open_column_order_dialog)

        self.exportformat_comboBox.currentIndexChanged.connect(self.export_format)
        self.selectionscope_comboBox.currentIndexChanged.connect(self.update_step_2_list)
        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)

        self.filterselection_comboBox.closing.connect(lambda: self.update_checked_list(self.filter_model, 'FilterGroups'))

        self.samplesincluded_comboBox.clearEditText()

    def update_checked_list(self, table_model: CheckableSqlTableModel, table_name: str):
        items = []
        for row in range(table_model.rowCount()):
            index = table_model.index(row, 1)
            if table_model.data(index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                items.append(table_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole))
        if len(items) == 0:
            if table_name == 'Samples':
                self.samplesincluded_comboBox.set_line_edit_text('None')
            if table_name == 'FilterGroups':
                self.filterselection_comboBox.set_line_edit_text('None')
        else:
            if table_name == 'Samples':
                self.samplesincluded_comboBox.set_line_edit_text(', '.join(items))
            if table_name == 'FilterGroups':
                self.filterselection_comboBox.set_line_edit_text(', '.join(items))


    def showEvent(self, a0):
        super().showEvent(a0)
        self.samples_model = CheckableSqlTableModel()
        self.samples_model = self.set_table(self.samples_model, 'Samples')

        self.aliquots_model = CheckableSqlTableModel()
        self.aliquots_model = self.set_table(self.aliquots_model, 'Aliquots')

        self.spots_model = CheckableSqlTableModel()
        self.spots_model = self.set_table(self.spots_model, 'Spots')

        self.filter_model = CheckableSqlTableModel()
        self.filter_model = self.set_table(self.filter_model, 'FilterGroups')
        self.filterselection_comboBox.setModel(self.filter_model)

        self.filter_model.dataChanged.connect(lambda: self.update_filter_list(self.filter_model))

        self.update_step_2_list()

    def tab_changed(self):
        if self.workbooktabs.tabText(self.workbooktabs.currentIndex()) == 'Database':
            return
        self.save_checkbox_states(self.previous_worksheet)
        self.load_checkbox_states()
        self.previous_worksheet = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        self.update_table_view()

    def rename_worksheet_tab(self, index):
        if index == -1:
            return  # No tab was double-clicked

        current_worksheet_name = self.workbooktabs.tabText(index)

        # Prompt the user for a new name
        new_name, ok = QInputDialog.getText(self, "Rename Worksheet", "Enter new worksheet name:",
                                            text=current_worksheet_name)
        if not ok or not new_name:
            return  # User canceled or didn't enter a name

        if new_name in self.worksheet_tabs_dict:
            QMessageBox.warning(self, "Duplicate Name", "A worksheet with that name already exists.")
            return

        # Update the workbook_tabs dictionary
        self.worksheet_tabs_dict[new_name] = self.worksheet_tabs_dict.pop(current_worksheet_name)

        # Update the tab text
        self.workbooktabs.setTabText(index, new_name)

    def create_first_worksheet_tab(self):
        # Create the first workbook tab using the existing tableView
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        tab1_layout.setContentsMargins(0, 0, 0, 0)
        tab1_layout.setSpacing(0)
        tab1.setLayout(tab1_layout)
        tableView = QTableView()

        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)

        distinct_checkbox = QCheckBox("Distinct Rows")
        distinct_checkbox.setToolTip("Check this box to only show distinct or unique rows a single time")
        distinct_checkbox.setChecked(False)
        distinct_checkbox.setFixedSize(150,20)
        horizontal_layout.addWidget(distinct_checkbox)

        pivot_checkbox = QCheckBox("Pivot Table")
        pivot_checkbox.setToolTip("Check this box to pivot the table based on first column")
        pivot_checkbox.setChecked(False)
        pivot_checkbox.setFixedSize(150, 20)
        horizontal_layout.addWidget(pivot_checkbox)

        counter_label = QLabel("Number of Rows: ")
        counter_label.setFixedSize(200,20)
        horizontal_layout.addWidget(counter_label)

        tab1_layout.addLayout(horizontal_layout)
        tab1_layout.addWidget(tableView)

        # Create a data model for this tableView
        model = QSqlQueryModel()

        self.worksheet_tabs_dict["Worksheet 1"] = {
            'tableView': tableView,
            'model': model,
            'distinct': False,
            'pivot': False,
            'selected_columns': {},
            'ordered_columns': {},
            'label': counter_label
        }

        self.workbooktabs.blockSignals(True)
        self.workbooktabs.addTab(tab1, "Worksheet 1")
        self.workbooktabs.blockSignals(False)

        self.load_checkbox_states('Worksheet 1')

        distinct_checkbox.stateChanged.connect(self.update_distinct_checkbox)
        pivot_checkbox.stateChanged.connect(self.update_pivottable_checkbox)
        self.update_table_view()
        self.repaint()

    def delete_all_worksheet_tabs(self):
        self.workbooktabs.setParent(None)
        self.verticalLayout_7.removeWidget(self.workbooktabs)
        self.workbooktabs.deleteLater()

        self.workbooktabs = QTabWidget()

        self.workbooktabs.currentChanged.connect(self.tab_changed)
        self.workbooktabs.tabBarDoubleClicked.connect(self.rename_worksheet_tab)
        self.previous_worksheet = self.workbooktabs.tabText(self.workbooktabs.currentIndex())

        self.verticalLayout_7.addWidget(self.workbooktabs)

        self.worksheet_tabs_dict = {}
        self.previous_worksheet = None



    def add_worksheet_tab(self, worksheet_name=None, distinct=False, pivot=False, selected_columns=None, ordered_columns=None):
        # Determine the new workbook name
        if ordered_columns is None:
            ordered_columns = {}
        if selected_columns is None:
            selected_columns = {}
        if worksheet_name is None:
            worksheet_name, ok = QInputDialog.getText(self, "New Worksheet", "Enter worksheet name:")
            if not ok or not worksheet_name:
                return  # User canceled or didn't enter a name

            if worksheet_name in self.worksheet_tabs_dict:
                QMessageBox.warning(self, "Duplicate Name", "A worksheet with that name already exists.")
                return


        # Create a new tableView
        new_tableView = QTableView()

        # Create a new data model for the new tableView
        model = QSqlQueryModel()

        # Create a new tab
        new_tab = QWidget()
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        new_tab.setLayout(tab_layout)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)

        distinct_checkbox = QCheckBox("Distinct Rows")
        distinct_checkbox.setToolTip("Check this box to only show distinct or unique rows a single time")
        distinct_checkbox.setChecked(distinct)
        horizontal_layout.addWidget(distinct_checkbox)

        pivot_checkbox = QCheckBox("Pivot Table")
        pivot_checkbox.setToolTip("Check this box to pivot the table based on first column")
        pivot_checkbox.setChecked(pivot)
        pivot_checkbox.setFixedSize(150, 20)
        horizontal_layout.addWidget(pivot_checkbox)

        counter_label = QLabel("Number of Rows: ")
        counter_label.setFixedSize(200, 20)
        horizontal_layout.addWidget(counter_label)

        tab_layout.addLayout(horizontal_layout)
        tab_layout.addWidget(new_tableView)


        # Store the tableView and model in the worksheet_tabs_dict
        self.worksheet_tabs_dict[worksheet_name] = {
            'tableView': new_tableView,
            'model': model,
            'distinct': distinct,
            'pivot': pivot,
            'selected_columns': selected_columns,
            'ordered_columns': ordered_columns,
            'label': counter_label
        }
        self.workbooktabs.blockSignals(True)
        self.workbooktabs.addTab(new_tab, worksheet_name)

        self.workbooktabs.blockSignals(False)
        self.load_checkbox_states(worksheet_name)
        self.workbooktabs.setCurrentWidget(new_tab)

        distinct_checkbox.stateChanged.connect(self.update_distinct_checkbox)
        pivot_checkbox.stateChanged.connect(self.update_pivottable_checkbox)
        # Update the table view
        self.update_table_view()
        # self.repaint()

    def update_distinct_checkbox(self):
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        distinct_checkbox = self.worksheet_tabs_dict[current_worksheet_name]['distinct']
        self.worksheet_tabs_dict[current_worksheet_name]['distinct'] = not distinct_checkbox
        self.update_table_view()

    def update_pivottable_checkbox(self):
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        pivottable_checkbox = self.worksheet_tabs_dict[current_worksheet_name]['pivot']
        self.worksheet_tabs_dict[current_worksheet_name]['pivot'] = not pivottable_checkbox
        self.update_table_view()

    def remove_current_worksheet_tab(self):
        if self.workbooktabs.count() <= 1:
            QMessageBox.warning(self, "Cannot Remove Worksheet", "At least one worksheet must remain.")
            return

        # Get the current workbook name
        current_index = self.workbooktabs.currentIndex()
        current_worksheet_name = self.workbooktabs.tabText(current_index)

        reply = QMessageBox.question(self, 'Remove Worksheet',
                                     f"Are you sure you want to remove '{current_worksheet_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Remove the tab from the tabWidget
        self.workbooktabs.removeTab(current_index)

        # Remove the workbook from the dictionary
        del self.worksheet_tabs_dict[current_worksheet_name]

    def populate_stack(self):
        while self.columnattributes_stack.count():
            widget = self.columnattributes_stack.widget(0)
            self.columnattributes_stack.removeWidget(widget)
            widget.deleteLater()

        for table_name, field_items in SQLUtils.table_attributes_dict.items():
            # Create container widget with QVBoxLayout
            container_widget = QWidget()
            # container_widget.setFixedSize(450, 500)
            container_layout = QVBoxLayout(container_widget)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)

            # Create a scroll area that expands vertically within vertical_layout9
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)  # Ensures the content resizes dynamically
            scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # Create a widget to hold the FlowLayout
            table_widget = QWidget()
            flow_layout = FlowLayout()
            flow_layout.setSpacing(0)
            flow_layout.setContentsMargins(0, 0, 0, 0)

            for field in field_items:
                label = QLabel(field)
                checkbox = QCheckBox()

                # Prevent expanding
                label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

                # Group label and checkbox
                group_widget = QGroupBox()
                hbox_layout = QHBoxLayout()
                hbox_layout.setContentsMargins(0, 0, 0, 0)
                hbox_layout.setSpacing(8)
                hbox_layout.addWidget(checkbox)
                hbox_layout.addWidget(label)
                group_widget.setLayout(hbox_layout)

                flow_layout.addWidget(group_widget)

                # Save field metadata
                checkbox.setProperty("field_name", field)
                checkbox.setProperty("table_name", table_name)
                checkbox.checkStateChanged.connect(lambda: self.update_table_view(deleted=False))

            # Add a vertical spacer to push content up
            vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            flow_layout.addItem(vertical_spacer)

            # Set the layout to the table_widget and add it to the scroll area
            table_widget.setLayout(flow_layout)
            scroll_area.setWidget(table_widget)  # Attach scroll area to table_widget

            # Add the scroll area to the container layout
            container_layout.addWidget(scroll_area)

            # Add container widget to the main layout stack
            self.columnattributes_stack.addWidget(container_widget)


    def switch_table_layout(self):
        # Switch the stack widget to show the layout corresponding to the selected table
        selected_table_index = self.columnselection_comboBox.currentIndex()
        self.columnattributes_stack.setCurrentIndex(selected_table_index)
        # Save and load checkbox states for each table
        self.save_checkbox_states()
        self.load_checkbox_states()

        self.update_table_view()

    def save_checkbox_states(self, previous_worksheet=None):
        # Save the state of checkboxes for all tables
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        checkbox_states = {}

        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            table_name = self.columnselection_comboBox.itemText(index)
            if table_widget:
                for widget in table_widget.findChildren(QCheckBox,
                                                        options=QtCore.Qt.FindChildOption.FindChildrenRecursively):
                    if isinstance(widget, QCheckBox):
                        field_name = widget.property('field_name')
                        checked = widget.isChecked()
                        checkbox_states[(table_name, field_name)] = checked
        # Store checkbox_states in the workbook's data
        if previous_worksheet is None:
            self.worksheet_tabs_dict[current_worksheet_name]['selected_columns'] = checkbox_states
        else:
            self.worksheet_tabs_dict[previous_worksheet]['selected_columns'] = checkbox_states

    def load_checkbox_states(self, worksheet_name=None):
        # Load the state of checkboxes for all tables

        if worksheet_name is not None:
            current_worksheet_name = worksheet_name
        else:
            current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        checkbox_states = self.worksheet_tabs_dict[current_worksheet_name].get('selected_columns', {})

        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            table_name = self.columnselection_comboBox.itemText(index)
            if table_widget:

                for widget in table_widget.findChildren(QCheckBox, options=QtCore.Qt.FindChildOption.FindChildrenRecursively):
                    if widget is None:
                        continue
                    if isinstance(widget, QCheckBox):
                        field_name = widget.property('field_name')

                        checked = checkbox_states.get((table_name, field_name), False)

                        widget.blockSignals(True)  # Prevent signals during state change
                        widget.setChecked(checked)
                        widget.blockSignals(False)

    def get_selected_values(self):
        selected_columns = {}
        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            table_name = self.columnselection_comboBox.itemText(index)
            if table_widget:
                for widget in table_widget.findChildren(QCheckBox,
                                                        options=QtCore.Qt.FindChildOption.FindChildrenRecursively):
                    if isinstance(widget, QCheckBox) and widget.isChecked():
                        print('get_selected_values is checked', widget.property('field_name'))
                        field_name = widget.property('field_name')
                        # Ensure table_name is associated with the checkbox
                        widget_table_name = widget.property('table_name')
                        print(field_name, widget_table_name)
                        if widget_table_name is None:
                            widget.setProperty('table_name', table_name)
                            widget_table_name = table_name
                        selected_columns[(widget_table_name, field_name)] = True
        # Store selected_columns in the current workbook
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        self.worksheet_tabs_dict[current_worksheet_name]['selected_columns'] = selected_columns
        print(selected_columns)
        return selected_columns

    def select_checkboxes(self, values):
        # Values should be tuple format ('table_name', 'field_name')
        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            if table_widget:
                for widget in table_widget.findChildren(QCheckBox,
                                                        options=QtCore.Qt.FindChildOption.FindChildrenRecursively):
                    if isinstance(widget, QCheckBox):
                        table_name = widget.property('table_name')
                        field_name = widget.property('field_name')

                        if (table_name, field_name) in values:
                            widget.setChecked(True)
        self.update_table_view()

    def update_table_view(self, deleted=False, worksheet_name=None):
        # Get the current workbook
        if worksheet_name is None:
            current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        else:
            current_worksheet_name = worksheet_name
        tableView = self.worksheet_tabs_dict[current_worksheet_name]['tableView']

        if deleted:
            self.worksheet_tabs_dict[current_worksheet_name]['selected_columns'] = self.worksheet_tabs_dict[current_worksheet_name].get('ordered_columns', {})
            ordered_columns = self.worksheet_tabs_dict[current_worksheet_name].get('ordered_columns', {})

        else:
            # # update selected columns
            self.get_selected_values()

            # Get the selected columns for the current workbook
            selected_columns = self.worksheet_tabs_dict[current_worksheet_name].get('selected_columns', {})
            ordered_columns = self.worksheet_tabs_dict[current_worksheet_name].get('ordered_columns', {})

            print('selected columns', selected_columns)
            print('ordered columns', ordered_columns)

            if Counter(selected_columns) != Counter(ordered_columns):
                ordered_columns = selected_columns
                self.worksheet_tabs_dict[current_worksheet_name]['ordered_columns'] = ordered_columns


        if not ordered_columns:
            # No columns selected, clear the table view
            tableView.setModel(None)
            return

        # Build the SQL query
        tables = set()
        columns_str = ''
        for table, field in ordered_columns:
            tables.add(table)

            columns_str += f'[{field}], '

        columns_str = columns_str[0:-2]

        tables.add('Samples')

        join = SQLUtils.get_join_from_table(list(tables))

        filtered_where_clause = ''
        ids = []
        for filter_id, filter_json in self.checked_filter_list:
            if len(self.checked_filter_list) > 0:
                filtered_where_clause = Filters.process_json_to_sql(filter_json[1:-1], scope='UPbData')
                filtered_where_clause = filtered_where_clause[0:-1]

            sql_query = ''
            join += SQLUtils.get_join_from_table(['UPbAnalyses'])

            sql_query = f"SELECT DISTINCT UPbAnalysisID FROM ({filtered_where_clause});"
            query = QSqlQuery()

            # Execute the query
            if not query.exec(sql_query):
                # Handle query execution error
                print("Failed to execute query:", query.lastError().text())

            # Fetch all results
            while query.next():
                ids.append(query.value(0))

        if len(self.checked_filter_list) == 1:
            ids = f"({', '.join(map(str, ids))})"
        else:
            # Count the occurrences of each ID
            id_counts = Counter(ids)
            # Extract IDs that appear more than once
            ids_more_than_once = [id for id, count in id_counts.items() if count > 1]

            ids = f"({', '.join(map(str, ids_more_than_once))})"

        # todo Maybe change to pagination

        if len(self.checked_sample_names) > 2:
            query_str = f"SELECT {'DISTINCT' if self.worksheet_tabs_dict[current_worksheet_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} LIMIT 250"
            if len(filtered_where_clause) > 0:
                query_str = f"SELECT {'DISTINCT' if self.worksheet_tabs_dict[current_worksheet_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} AND UPbAnalysisID IN {ids} LIMIT 250"
        else:
            query_str = f"SELECT {'DISTINCT' if self.worksheet_tabs_dict[current_worksheet_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE FALSE"


        # code to transform the query into a pivot table
        if self.worksheet_tabs_dict[current_worksheet_name]['pivot']:
            query_str = query_str.replace('LIMIT 250', '')

            db = QSqlDatabase.database()
            db.commit()
            db.close()
            db.open()

            drop_table_qry = QSqlQuery()
            if not drop_table_qry.exec('DROP TABLE IF EXISTS TempPivotTable'):
                print("Failed to execute query:", drop_table_qry.lastError().text())
                errmsg = QErrorMessage()
                errmsg.setWindowTitle('Error')
                errmsg.showMessage(drop_table_qry.lastError().text())
                errmsg.exec()

            create_table_qry = QSqlQuery()
            if not create_table_qry.exec('CREATE TEMP TABLE TempPivotTable AS SELECT * FROM (' + query_str + ')'):
                print("Failed to execute query:", create_table_qry.lastError().text())

            first_tuple = next(iter(ordered_columns))
            pivot_col = first_tuple[1]

            distinct_first_column_query = QSqlQuery()
            first_column_list = []
            if distinct_first_column_query.exec(f'SELECT DISTINCT {pivot_col} FROM TempPivotTable ORDER BY {pivot_col}'):
                if distinct_first_column_query.next():
                    while distinct_first_column_query.isValid():
                        first_column_list.append(distinct_first_column_query.value(0))
                        distinct_first_column_query.next()
                else:
                    print("No rows returned.")
            else:
                print("Failed to execute query:", distinct_first_column_query.lastError().text())
            case_expressions = []

            for name in first_column_list:
                for table, field in ordered_columns:
                    if field == pivot_col:
                        continue
                    case_expressions.append(f'MAX(CASE WHEN {pivot_col} = \'{name}\' THEN {field} END) AS [{name + "_" + field}]')

            case_list_sql = '\n, '.join(case_expressions)

            query_str = (f"""With cte AS (SELECT {columns_str}, ROW_NUMBER() OVER (
            PARTITION BY {pivot_col}
            ORDER BY rowid) AS RowNum
            FROM TempPivotTable)
            SELECT {case_list_sql}
            FROM cte c
            GROUP BY c.RowNum
            ORDER BY c.RowNum""")

        print(query_str)

        model = QSqlQueryModel()
        model.setQuery(query_str)
        self.worksheet_tabs_dict[current_worksheet_name]['model'] = model

        # # Remove LIMIT 250 from the original query string and build the COUNT query
        # counter_sql_query = f"SELECT COUNT(*) FROM ({query_str.replace('LIMIT 250', '')}) AS SubQuery"
        #
        # # Prepare and execute the query
        # counter_query = QSqlQuery()
        # if not counter_query.exec(counter_sql_query):
        #     # Handle query execution error
        #     print("Failed to execute query:", counter_query.lastError().text())
        # else:
        #     # Move to the first record to retrieve the count
        #     if counter_query.next():
        #         count = counter_query.value(0)
        #         self.workbook_tabs[current_worksheet_name]['label'].setText(f"Number of Rows: {count}")
        #     else:
        #         # Handle case where query doesn't return a result
        #         print("Query executed successfully but returned no results.")

        # for col, (table, field) in enumerate(ordered_columns):
        #     header = f"{table}.{field}"
        #     model.setHeaderData(col, QtCore.Qt.Orientation.Horizontal, header, QtCore.Qt.ItemDataRole.DisplayRole)

        tableView.setModel(model)

        # QSqlDatabase().commit()


    def export_button(self):
        match self.exportformat_comboBox.currentText():
            case 'detritalPy':
                self.export_to_excel()
            case 'IsoplotR':
                self.export_to_excel()
            case 'DZStats':
                # todo requires csv not excel, all without headers
                # intersample requires each sample to represented by a pair of columns
                # for each pair of columns per sample, col 1 is grain mean age, col 2 is grain age error

                # twosample compare, 2 csvs one per sample
                # col 1 = grain mean age, col 2 = grain age error
                self.export_to_excel()
            case 'Database':
                self.export_to_datbase()
                pass
            case 'Custom':
                self.export_to_excel()
                pass
    def export_to_datbase(self):
        fileName, _ = QFileDialog.getSaveFileName(
            None,
            "Save Database File",
            "",
            "Database Files (*.db)"
        )

        if not fileName:
            return

        if not fileName.lower().endswith(".db"):
            fileName += ".db"

        ExportDatabase.subset_database(self.db_file, fileName, self.checked_sample_list)

        # QDesktopServices.openUrl(QtCore.QUrl(QtCore.QUrl.fromLocalFile(fileName).path().replace(fileName, '')[0:-1]))

    def export_to_excel(self):
        # Prompt user for where to save the Excel file
        fileName, _ = QFileDialog.getSaveFileName(
            None,
            "Save Excel File",
            "",
            "Excel Files (*.xlsx)"
        )

        if not fileName:
            return

        # Ensure the filename ends with .xlsx
        if not fileName.lower().endswith(".xlsx"):
            fileName += ".xlsx"

        # Create a new workbook
        wb = Workbook()

        # The first sheet is created by default. We'll rename or replace it as we go.
        first_sheet = True

        for sheet_name, info in self.worksheet_tabs_dict.items():
            self.update_table_view(worksheet_name=sheet_name)
            model = info['model']
            if first_sheet:
                ws = wb.active
                ws.title = sheet_name
                first_sheet = False
            else:
                ws = wb.create_sheet(title=sheet_name)

            # Write headers
            headers = []
            for col in range(model.columnCount()):
                header_text = model.headerData(col, QtCore.Qt.Orientation.Horizontal)
                headers.append(header_text if header_text is not None else "")
            for col_idx, header in enumerate(headers, start=1):
                ws.cell(row=1, column=col_idx, value=header)

            # Write data rows
            for row in range(model.rowCount()):
                for col in range(model.columnCount()):
                    cell_value = model.data(model.index(row, col), QtCore.Qt.ItemDataRole.DisplayRole)
                    ws.cell(row=row + 2, column=col + 1, value=cell_value)

        # Attempt to save the workbook
        try:
            wb.save(fileName)
        except Exception as e:
            QMessageBox.warning(None, "Save Failed", f"Could not save the Excel file.\n{e}")
            return

        # Open the file using the system's default application
        QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(fileName))

    def export_format(self):
        self.delete_all_worksheet_tabs()
        self.selectionscope_comboBox.setEnabled(True)
        self.columnattributes_stack.setEnabled(True)
        self.columnselection_comboBox.setEnabled(True)
        self.editorder_pushbutton.setEnabled(True)
        self.add_workbook_button.setEnabled(True)
        self.remove_workbook_button.setEnabled(True)
        self.fileformat_comboBox.setEnabled(True)
        match self.exportformat_comboBox.currentText():
            case 'detritalPy':
                self.fileformat_comboBox.setCurrentText('Excel (.xlsx)')
                Samples_columns= {
                    ('Samples', 'SampleName'): True,
                    ('Units', 'UnitName'): True,
                    ('Samples', 'Latitude'): True,
                    ('Samples', 'Longitude'): True,
                    ('Sources', 'ShortCitation'): True
                }
                self.add_worksheet_tab('Samples', True, False, Samples_columns, Samples_columns)

                ZrUPb_columns = {
                    ('Samples', 'SampleName'): True,
                    ('Spots', 'SpotName'): True,
                    ('UPbAnalyses', 'Uppm'): True,
                    ('UPbAnalyses', 'CalculatedU/Th'): True,
                    ('UPbAnalyses', 'CalculatedBestAge'): True,
                    ('UPbAnalyses', 'CalculatedBestAgeError'): True,
                    ('UPbAnalyses', 'CalculatedConcordance'): True
                } # todo not inputting as the correct order

                self.add_worksheet_tab('ZrUPb', False, False, ZrUPb_columns, ZrUPb_columns)
                return
            case 'IsoplotR - 07/35, 06/38, 04/38, 07/06, 04/07, 04/06':
                # modeled after UPb6.csv in IsoplotR
                # 207/235
                # 206/238
                # 204/238
                # 207/206
                # 204/207
                # 204/206
                self.fileformat_comboBox.setCurrentText('Excel (.xlsx)')
                UPb_columns = {
                    ('UPbAnalyses', 'Calculated207Pb/235U'): True,
                    ('UPbAnalyses', 'Calculated207Pb/235UError'): True,
                    ('UPbAnalyses', 'Calculated206Pb/238U'): True,
                    ('UPbAnalyses', 'Calculated206Pb/238UError'): True,
                    ('UPbAnalyses', 'Calculated204Pb/238U'): True,
                    ('UPbAnalyses', 'Calculated204Pb/238UError'): True,
                    ('UPbAnalyses', 'Calculated207Pb/206Pb'): True,
                    ('UPbAnalyses', 'Calculated207Pb/206PbError'): True,
                    ('UPbAnalyses', 'Calculated204Pb/207Pb'): True,
                    ('UPbAnalyses', 'Calculated204Pb/207PbError'): True,
                    ('UPbAnalyses', 'Calculated204Pb/206Pb'): True,
                    ('UPbAnalyses', 'Calculated204Pb/206PbError'): True
                }
                self.add_worksheet_tab('IsoplotR', False, False, UPb_columns, UPb_columns)

            case 'IsoplotR - 38/06, 07/06':
                # modeled after UPb2.csv in IsoplotR
                # 238/206
                # 207/206
                self.fileformat_comboBox.setCurrentText('Excel (.xlsx)')
                UPb_columns = {
                    ('UPbAnalyses', 'Calculated238U/206Pb'): True,
                    ('UPbAnalyses', 'Calculated238U/206PbError'): True,
                    ('UPbAnalyses', 'Calculated207Pb/206Pb'): True,
                    ('UPbAnalyses', 'Calculated207Pb/206PbError'): True
                }
                self.add_worksheet_tab('IsoplotR', False, False, UPb_columns, UPb_columns)

            case 'DZStats - Intersample':
                # todo requires csv not excel, all without headers
                # intersample requires each sample to represented by a pair of columns
                # for each pair of columns per sample, col 1 is grain mean age, col 2 is grain age error

                # twosample compare, 2 csvs one per sample
                # col 1 = grain mean age, col 2 = grain age error

                self.fileformat_comboBox.setCurrentText('Comma-Separated Value (.csv)')
                UPb_columns = {
                    ('Samples', 'SampleName'): True,
                    ('UPbAnalyses', 'CalculatedBestAge'): True,
                    ('UPbAnalyses', 'CalculatedBestAgeError'): True
                }
                self.add_worksheet_tab('DZStats - Intersample', False, True, UPb_columns, UPb_columns)

            case 'Database':
                self.fileformat_comboBox.setEnabled(False)
                if self.findChild(QSqlTableModel, 'database_QSqlTableModel') is not None:
                    self.findChild(QSqlTableModel, 'database_QSqlTableModel').clear()
                    self.findChild(QSqlTableModel, 'database_QSqlTableModel').setParent(None)
                    QSqlDatabase.removeDatabase('temp')
                    self.findChild(QWidget, 'database_tab').setParent(None)

                self.selectionscope_comboBox.setCurrentText('Samples')
                self.selectionscope_comboBox.setEnabled(False)
                self.columnattributes_stack.setEnabled(False)
                self.columnselection_comboBox.setEnabled(False)
                self.editorder_pushbutton.setEnabled(False)
                self.add_workbook_button.setEnabled(False)
                self.remove_workbook_button.setEnabled(False)
                if self.checked_sample_list == []:
                    return

                if os.path.isfile("temp.db"):
                    os.remove("temp.db")
                tgt_db_file = "temp.db"

                sample_id_to_subset = self.checked_sample_list
                # if 'temp' in QSqlDatabase().addDatabase('QSQLITE', 'temp').connectionNames():
                #     QSqlDatabase().removeDatabase('temp')

                db_id_subset = FilterDatabase.gather_ids_for_subset(QSqlDatabase(), sample_id_to_subset)

                # tgt_db = QSqlDatabase().addDatabase('QSQLITE', 'temp')
                # tgt_db.setDatabaseName(tgt_db_file)
                # tgt_db.open()

                # Create a new tableView

                # Create a new tab
                new_tab = QWidget(self)
                new_tab.setObjectName('database_tab')
                tab_layout = QVBoxLayout(self)
                new_tab.setLayout(tab_layout)

                database_model = QSqlTableModel(parent=self)
                database_model.setObjectName('database_QSqlTableModel')

                table_filterproxy = QSortFilterProxyModel()
                table_filterproxy.setSourceModel(database_model)

                table_view = QTableView()
                table_view.setModel(table_filterproxy)

                table_swtcher_combobox = QComboBox(new_tab)
                table_swtcher_combobox.addItems(SQLUtils.user_viewable_alltables)
                table_swtcher_combobox.setObjectName('database_table_switcher')
                table_swtcher_combobox.currentIndexChanged.connect(lambda: self.table_switcher(db_id_subset))

                tab_layout.addWidget(table_swtcher_combobox)
                database_model.setTable('Ages')
                database_model.select()
                tab_layout.addWidget(table_view)

                self.workbooktabs.addTab(new_tab, 'Database')

                # todo create combobox changer, connect to new table view switcher
                # merge over exporter code to this
                # add logic to ensure db is closed/not locked
                # temp file save to memory
                # populate table view based on combobox selection

                pass
            case 'Custom':
                self.create_first_worksheet_tab()
                pass

    def table_switcher(self, db_id_subset):
        table = self.findChild(QComboBox, 'database_table_switcher').currentText()
        table = table.replace(' ', '')
        tableView: QSqlTableModel = self.findChild(QSqlTableModel, 'database_QSqlTableModel')
        tableView.setTable(table)
        tableView.select()
        db_id_subset= f"({', '.join(map(str, db_id_subset[table]))})"
        if table == 'UPbData':
            tableView.setFilter(f'UPbAnalysisID IN ' + db_id_subset)
        elif table == 'LabFacilities':
            tableView.setFilter(f'LabFacilityID IN ' + db_id_subset)
        else:
            tableView.setFilter(f'{table[0:-1]}ID IN ' + db_id_subset)

    def update_step_2_list(self):
        if self.selectionscope_comboBox.currentText() == 'Samples':
            self.samplesincluded_comboBox.setModel(self.samples_model)
            self.samples_model.dataChanged.connect(lambda: self.update_sample_list(self.samples_model))
            self.samplesincluded_comboBox.closing.connect(
                lambda: self.update_checked_list(self.samples_model, 'Samples'))
            self.update_checked_list(self.samples_model, 'Samples')
        elif self.selectionscope_comboBox.currentText() == 'Aliquots':
            self.samplesincluded_comboBox.setModel(self.aliquots_model)
            self.aliquots_model.dataChanged.connect(lambda: self.update_sample_list(self.aliquots_model))
            self.samplesincluded_comboBox.closing.connect(
                lambda: self.update_checked_list(self.aliquots_model, 'Samples'))
            self.update_checked_list(self.aliquots_model, 'Samples')
        elif self.selectionscope_comboBox.currentText() == 'Spots':
            self.samplesincluded_comboBox.setModel(self.spots_model)
            self.spots_model.dataChanged.connect(lambda: self.update_sample_list(self.spots_model))
            self.samplesincluded_comboBox.closing.connect(
                lambda: self.update_checked_list(self.spots_model, 'Samples'))
            self.update_checked_list(self.spots_model, 'Samples')
        self.update_checked_list(self.filter_model, 'FilterGroups')

    def closeEvent(self, a0):
        # self.saveWindowState()
        super().closeEvent(a0)

    def set_table(self, model, table: str):
        model.setTable(table)
        model.select()
        return model

    def update_sample_list(self, model):
        if self.selectionscope_comboBox.currentText() == 'Samples':
            self.checked_sample_list = []
            for row in range(model.rowCount()):
                name_index = model.index(row, 1, QtCore.QModelIndex())
                if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                    # Add the sample ID to the list
                    id_index = model.index(row, 0, QtCore.QModelIndex())
                    self.checked_sample_list.append(model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))

            self.checked_sample_names = f"({', '.join(map(str, self.checked_sample_list))})"

        elif self.selectionscope_comboBox.currentText() == 'Aliquots':
            self.checked_aliquot_list = []
            for row in range(model.rowCount()):
                name_index = model.index(row, 1, QtCore.QModelIndex())
                if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                    # Add the aliquot ID to the list
                    id_index = model.index(row, 0, QtCore.QModelIndex())
                    self.checked_aliquot_list.append(model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))

            self.checked_aliquot_names = f"({', '.join(map(str, self.checked_aliquot_list))})"

        elif self.selectionscope_comboBox.currentText() == 'Spots':
            self.checked_spot_list = []
            for row in range(model.rowCount()):
                name_index = model.index(row, 1, QtCore.QModelIndex())
                if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                    # Add the spot ID to the list
                    id_index = model.index(row, 0, QtCore.QModelIndex())
                    self.checked_spot_list.append(model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))

            self.checked_spot_names = f"({', '.join(map(str, self.checked_spot_list))})"
        if self.exportformat_comboBox.currentText() != 'Database':

            self.update_table_view()
        else:
            self.export_format()

    def update_filter_list(self, model):
        self.checked_filter_list = []
        for row in range(model.rowCount()):
            name_index = model.index(row, 1, QtCore.QModelIndex())
            if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                # Add the filter ID and JSON to the list
                id_index = model.index(row, 0, QtCore.QModelIndex())
                filter_json = model.index(row, 2, QtCore.QModelIndex())
                self.checked_filter_list.append((model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole),
                                                 model.data(filter_json, QtCore.Qt.ItemDataRole.DisplayRole)))
        if self.exportformat_comboBox.currentText() != 'Database':
            self.update_table_view()
        else:
            self.export_format()

    def open_column_order_dialog(self):
        # Get current selected columns
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        ordered_columns = self.worksheet_tabs_dict[current_worksheet_name].get('ordered_columns', [])

        if not ordered_columns:
            QMessageBox.warning(self, "No Columns Selected", "Please select columns before editing their order.")
            return

        # Open the dialog
        dialog = ColumnOrderDialog(ordered_columns, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get adjusted columns
            adjusted_columns = dialog.get_adjusted_columns()
            # Update the selected columns
            self.worksheet_tabs_dict[current_worksheet_name]['ordered_columns'] = adjusted_columns
            # Update the table view with the new column order
            self.update_table_view(deleted=True)

class ColumnOrderDialog(QDialog):
    def __init__(self, ordered_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Column Order")
        self.resize(300, 400)
        self.ordered_columns = ordered_columns

        # Create widgets
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)

        for table_name, field_name in self.ordered_columns:
            self.list_widget.addItem(f"{table_name}.{field_name}")

        self.delete_button = QPushButton("Delete Selected")
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Connect signals
        self.delete_button.clicked.connect(self.delete_selected_item)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def delete_selected_item(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.list_widget.takeItem(current_row)
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")

    def get_adjusted_columns(self):
        adjusted_columns = []
        for index in range(self.list_widget.count()):
            item_text = self.list_widget.item(index).text()
            table_name, field_name = item_text.split('.', 1)
            adjusted_columns.append((table_name, field_name))
        return tuple(adjusted_columns)