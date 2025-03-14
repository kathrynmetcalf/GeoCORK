import csv
import os
import sys
from collections import Counter

import pandas
import qtawesome
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QSettings, QSortFilterProxyModel, QTimer, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableView,
    QGridLayout, QLabel, QCheckBox, QSpacerItem,
    QSizePolicy, QTabWidget, QInputDialog, QDialog, QListWidget, QHBoxLayout, QMessageBox, QComboBox, QErrorMessage,
    QGroupBox, QScrollArea, QHeaderView, QAbstractItemView, QListWidgetItem
)
from PyQt6.uic import loadUi
from openpyxl import Workbook

import logger_setup
from ui.DisplayTables import DisplayTables
from ui.DisplayTablesSimplified import DisplayTablesSimplified
from ui.FlowLayout import FlowLayout, ScrollableFlowWidget
from Functions import ExportDatabase
from Functions import FilterDatabase
from Functions import SQLUtils
from Functions.Widget_classes import CheckableSqlTableModel, CheckableComboBox, SQLiteTableModel
from ui import Filters


class ExportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "ExporterUI.ui")
        loadUi(sources_ui_file, self)

        self.refreshbutton.setIcon(qtawesome.icon('fa6s.rotate-right', color='green', scale_factor=1.0))
        self.refreshbutton.clicked.connect(self.refresh_button)

        self.checked_filter_list = []

        self.checked_grouped_filter_list = []

        self.checked_sample_list = []
        self.checked_aliquot_list = []
        self.checked_spot_list = []

        self.checked_sample_names = '()'
        self.checked_aliquot_names = '()'
        self.checked_spot_names = '()'

        self.column_name_mappings = dict()

        # Initialize a dictionary to store data for each workbook tab
        self.worksheet_tabs_dict = {}

        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.db_file = widget.db_file

        self.settings = QSettings("CSUF", "GeoCORK")

        self.samplesincluded_comboBox: CheckableComboBox()

        # Connect buttons to methods
        self.add_workbook_button.clicked.connect(lambda: self.add_worksheet_tab(None, False, False, {}, {}))
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

        self.groupedfilter_model = CheckableSqlTableModel()
        self.groupedfilter_model = self.set_table(self.groupedfilter_model, 'FilterGroups')
        self.groupedfilter_comboBox.setModel(self.groupedfilter_model)

        # Fix for updating the filter list when the filter model is updated
        self.filter_model.dataChanged.connect(lambda: self.update_filter_list(self.filter_model))
        self.filterselection_comboBox.closing.connect(
            lambda: self.update_checked_list(self.filter_model, 'FilterGroups'))

        self.groupedfilter_model.dataChanged.connect(lambda: self.update_groupedfilter_list(self.groupedfilter_model))
        self.groupedfilter_comboBox.closing.connect(
            lambda: self.update_checked_list(self.groupedfilter_model, 'GroupedFilterGroups'))

        self.update_step_2_list()
        self.populate_stack()
        self.export_format()

        self.editorder_pushbutton.clicked.connect(self.open_column_order_dialog)
        self.edit_columnnames_pushButton.clicked.connect(self.open_columnname_mapping_dialog)

        self.exportformat_comboBox.currentIndexChanged.connect(self.export_format)
        self.selectionscope_comboBox.currentIndexChanged.connect(self.update_step_2_list)
        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)

        self.samplesincluded_comboBox.clearEditText()

    def refresh_button(self):
        logger_setup.get_logger().info('Refresh Button Clicked')
        self.update_table_view()

    def update_checked_list(self, table_model: CheckableSqlTableModel, table_name: str):
        items = []
        for row in range(table_model.rowCount()):
            index = table_model.index(row, 1)
            if table_model.data(index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                items.append(table_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole))
        if len(items) == 0:
            match table_name:
                case 'Samples':
                    self.samplesincluded_comboBox.set_line_edit_text('None')
                case 'FilterGroups':
                    self.filterselection_comboBox.set_line_edit_text('None')
                case 'GroupedFilterGroups':
                    self.groupedfilter_comboBox.set_line_edit_text('None')
        else:
            match table_name:
                case 'Samples':
                    self.samplesincluded_comboBox.set_line_edit_text(', '.join(items))
                case 'FilterGroups':
                    self.filterselection_comboBox.set_line_edit_text(', '.join(items))
                case 'GroupedFilterGroups':
                    self.groupedfilter_comboBox.set_line_edit_text(', '.join(items))


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

        self.groupedfilter_model = CheckableSqlTableModel()
        self.groupedfilter_model = self.set_table(self.groupedfilter_model, 'FilterGroups')
        self.groupedfilter_comboBox.setModel(self.groupedfilter_model)

        self.groupedfilter_model.dataChanged.connect(lambda: self.update_groupedfilter_list(self.groupedfilter_model))

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

        headers_checkbox = QCheckBox("Include Headers")
        headers_checkbox.setToolTip("Check this box include headers in output files")
        headers_checkbox.setChecked(True)
        headers_checkbox.setFixedSize(150, 20)
        horizontal_layout.addWidget(headers_checkbox)

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
            'label': counter_label,
            'headers': True,
            'sql': ''
        }

        self.workbooktabs.blockSignals(True)
        self.workbooktabs.addTab(tab1, "Worksheet 1")
        self.workbooktabs.blockSignals(False)

        self.load_checkbox_states('Worksheet 1')

        distinct_checkbox.stateChanged.connect(self.update_distinct_checkbox)
        headers_checkbox.stateChanged.connect(self.update_header_checkbox)
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

    def rename_column(self, column_index, model):
        """Show an input dialog to rename a column header."""
        current_name = str(model.headerData(column_index, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))

        new_name, ok = QInputDialog.getText(self, "Rename Column",
                                            f"Enter new name for '{current_name}':",
                                            text=current_name)
        if ok and new_name.strip():
            model.setHeaderData(column_index, Qt.Orientation.Horizontal, new_name)

    def add_worksheet_tab(self, worksheet_name=None, distinct=False, pivot=False, selected_columns=None,
                          ordered_columns=None, headers=False):
        # Determine the new workbook name
        if ordered_columns is None:
            ordered_columns = {}
        if selected_columns is None:
            selected_columns = {}
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
        new_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

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

        headers_checkbox = QCheckBox("Include Headers")
        headers_checkbox.setToolTip("Check this box include headers in output files")
        headers_checkbox.setChecked(headers)
        headers_checkbox.setFixedSize(150, 20)
        horizontal_layout.addWidget(headers_checkbox)

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
            'label': counter_label,
            'headers': headers,
            'sql': ''
        }
        self.workbooktabs.blockSignals(True)
        self.workbooktabs.addTab(new_tab, worksheet_name)

        self.workbooktabs.blockSignals(False)
        self.load_checkbox_states(worksheet_name)
        # self.workbooktabs.setCurrentWidget(new_tab)

        distinct_checkbox.stateChanged.connect(self.update_distinct_checkbox)
        headers_checkbox.stateChanged.connect(self.update_header_checkbox)
        pivot_checkbox.stateChanged.connect(self.update_pivottable_checkbox)
        # Update the table view
        self.update_table_view()
        # self.repaint()

    def update_distinct_checkbox(self):
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        distinct_checkbox = self.worksheet_tabs_dict[current_worksheet_name]['distinct']
        self.worksheet_tabs_dict[current_worksheet_name]['distinct'] = not distinct_checkbox
        self.update_table_view()

    def update_header_checkbox(self):
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        headers_checkbox = self.worksheet_tabs_dict[current_worksheet_name]['headers']
        self.worksheet_tabs_dict[current_worksheet_name]['headers'] = not headers_checkbox

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
                checkbox = QCheckBox(field)

                # Prevent expanding
                checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

                # Group label and checkbox
                group_widget = QGroupBox()
                hbox_layout = QHBoxLayout()
                hbox_layout.setContentsMargins(0, 0, 0, 0)
                hbox_layout.setSpacing(8)
                hbox_layout.addWidget(checkbox)
                group_widget.setLayout(hbox_layout)

                flow_layout.addWidget(group_widget)

                # Save field metadata
                checkbox.setProperty("field_name", field)
                checkbox.setProperty("table_name", table_name)
                checkbox.checkStateChanged.connect(lambda: self.update_table_view())

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
                        # print('get_selected_values is checked', widget.property('field_name'))
                        field_name = widget.property('field_name')
                        # Ensure table_name is associated with the checkbox
                        widget_table_name = widget.property('table_name')
                        # print(field_name, widget_table_name)
                        if widget_table_name is None:
                            widget.setProperty('table_name', table_name)
                            widget_table_name = table_name
                        selected_columns[(widget_table_name, field_name)] = True
        # Store selected_columns in the current workbook
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        self.worksheet_tabs_dict[current_worksheet_name]['selected_columns'] = selected_columns
        for column in selected_columns:
            if column[1] not in self.column_name_mappings:
                self.column_name_mappings[column[1]] = column[1]

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
                        else:
                            widget.setChecked(False)
        self.update_table_view()

    def update_table_view(self, order_changed=False, worksheet_name=None):
        # Get the current workbook
        if worksheet_name is None:
            current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        else:
            current_worksheet_name = worksheet_name
        #Get the current TableView
        tableView: QTableView = self.worksheet_tabs_dict[current_worksheet_name]['tableView']

        #If column order has changed, set selected columns to ordered_columns, select checkboxes based on ordered columns
        # This removes potentially deleted columns from the column dialog
        if order_changed:
            self.worksheet_tabs_dict[current_worksheet_name]['selected_columns'] = self.worksheet_tabs_dict[current_worksheet_name].get('ordered_columns', {})
            ordered_columns = self.worksheet_tabs_dict[current_worksheet_name].get('ordered_columns', {})
            self.select_checkboxes(ordered_columns)
        else:
            # # update selected columns
            self.get_selected_values()
            # Get the selected columns for the current workbook
            selected_columns = self.worksheet_tabs_dict[current_worksheet_name]['selected_columns']
            ordered_columns = self.worksheet_tabs_dict[current_worksheet_name]['ordered_columns']
            #checks to make sure the items in selected_columns and ordered_columns match. If they do not match then
            #default to selected columns, means new column could be selected, therefore ordered_columns is out of date
            if selected_columns == ordered_columns:
                ordered_columns = selected_columns
                self.worksheet_tabs_dict[current_worksheet_name]['ordered_columns'] = ordered_columns
        # prevents necessary compute time
        if not ordered_columns:
            # No columns selected, clear the table view
            tableView.setModel(None)
            return

        # Build the SQL query
        tables = set()
        #always ensures UPbAnalyses in the resulting query, prevents edge cases
        tables.add('UPbAnalyses')
        columns_str = ''
        #creates column select string in format [SampleID], [CalculatedU/Th], etc...
        for table, field in ordered_columns:
            tables.add(table)
            if field in self.column_name_mappings:
                columns_str += f"[{field}] AS '{self.column_name_mappings[field]}', "
            else:
                columns_str += f'[{field}], '


        # removes final ", "
        columns_str = columns_str[0:-2]
        #always ensures samples is included, since tables is a set only one copy will exist
        tables.add('Samples')

        #gets final join from all found tables.
        join = SQLUtils.get_join_from_table("", list(tables))

        filtered_where_clause = ''
        ids = set()
        # Filters for additional filters step, so if Samples1,2,3 are selected but only want bestage<500ma this
        # section finds the UPbAnalysisID that match the criteria.
        for filter_id, filter_json in self.checked_filter_list:

            #loops through each filter in the checked filter list, processes the json to sql
            filtered_where_clause = Filters.process_json_to_sql(filter_json[1:-1], scope='UPbAnalyses')
            filtered_where_clause = filtered_where_clause[0:-1]

            sql_query = f"SELECT DISTINCT UPbAnalysisID FROM ({filtered_where_clause});"
            query = QSqlQuery()

            # Execute the query
            logger_setup.get_logger().info(f'Fetching distinct UPbAnalyisIDs from FilterID: {filter_id}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            if not query.exec(sql_query):
                logger_setup.get_logger().critical(
                    f'Error fetching distinct UPbAnalysisID using Filter ID: {filter_id}: {query.lastError().text()}')
                logger_setup.get_logger().critical(f'SQL command: {sql_query}')
            logger_setup.get_logger().info(f'Fetched distinct UPbAnalysisIDs from FilterID: {filter_id} sucessfully')
            # Fetch all results, add found IDs to the list.
            while query.next():
                ids.add(query.value(0))
        logger_setup.get_logger().info(f'Number of Filtered UPbAnalysis IDs Found: {len(ids)}')

        # due to how the above logic is, the filters are added with an OR clause, therefore it full unions Filters 1 and 2
        ids = f"({', '.join(map(str, ids))})"

        # checks for logic to see what kind of SQL query is needed.
        # self.checked_sample_names defaults to '()', so length of 2,
        # if a sample is checked then len > 2, so UPbAnalysisID are needed, so we limit to LIMIT 250 so its quicker and
        # still shows example data to be exported.
        # if filtered where clause is not blank, len > 0, then we need to filter by UPbAnalysisID
        if len(self.checked_sample_names) > 2:
            if len(filtered_where_clause) > 0:
                query_str = f"SELECT {'DISTINCT' if self.worksheet_tabs_dict[current_worksheet_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} AND UPbAnalysisID IN {ids} LIMIT 250"
            else:
                query_str = f"SELECT {'DISTINCT' if self.worksheet_tabs_dict[current_worksheet_name]['distinct'] is True else ''} {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} LIMIT 250"
        else:
            if len(filtered_where_clause) > 0:
                query_str = f"SELECT {'DISTINCT' if self.worksheet_tabs_dict[current_worksheet_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE UPbAnalysisID IN {ids} LIMIT 250"
            else:
                query_str = f"SELECT {'DISTINCT' if self.worksheet_tabs_dict[current_worksheet_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE FALSE"

        logger_setup.get_logger().debug(f'Final TableView SQL command: {query_str}')


        # code to add optional grouped filters as a new Sample, unions all
        for filter_id, name, filter_json in self.checked_grouped_filter_list:
            ids = set()
            logger_setup.get_logger().info('Fetching Filters for Grouped Filter List')
            # loops through each filter in the checked filter list, processes the json to sql
            filtered_where_clause = Filters.process_json_to_sql(filter_json[1:-1], scope='UPbAnalyses')
            filtered_where_clause = filtered_where_clause[0:-1]

            sql_query = f"SELECT DISTINCT UPbAnalysisID FROM ({filtered_where_clause});"
            query = QSqlQuery()

            # Execute the query
            logger_setup.get_logger().info(f'Fetching distinct UPbAnalyisIDs from FilterID: {filter_id}')
            logger_setup.get_logger().debug(f'SQL command: {sql_query}')
            if not query.exec(sql_query):
                logger_setup.get_logger().critical(
                    f'Error fetching distinct UPbAnalysisID using Filter ID: {filter_id}: {query.lastError().text()}')
                logger_setup.get_logger().critical(f'SQL command: {sql_query}')
            logger_setup.get_logger().info(f'Fetched distinct UPbAnalysisIDs from FilterID: {filter_id} sucessfully')
            # Fetch all results, add found IDs to the list.
            while query.next():
                ids.add(query.value(0))
            ids = f"({', '.join(map(str, ids))})"

            # remove LIMIT 250 from original query_str, can only have one of those
            query_str = query_str.replace('LIMIT 250', '')
            # take the original query_str and only the content before WHERE CLAUSE
            modified_query_str = query_str.split('WHERE')[0]
            # replace SampleName with filter name AS
            modified_query_str = modified_query_str.replace('[SampleName]', f'\'{name}\'')
            modified_query_str = modified_query_str.replace('SELECT', 'SELECT DISTINCT')
            modified_query_str = modified_query_str.replace('LIMIT 250', '')
            modified_query_str = modified_query_str.replace('DISTINCT DISTINCT', 'DISTINCT')

            query_str = f"{query_str} \n UNION ALL \n {modified_query_str} WHERE UPbAnalysisID IN {ids} LIMIT 250 \n"
            logger_setup.get_logger().debug(f'SQL command: {query_str}')


        # code to transform the query into a pivot table
        # SQLite doesn't have a builtin Pivot function, so it must be done manually.
        if self.worksheet_tabs_dict[current_worksheet_name]['pivot']:
            query_str = query_str.replace('LIMIT 250', '')

            # Any transactions shouldn't be present at this time, but just in case
            db = QSqlDatabase.database()
            db.commit()
            db.close()
            db.open()

            drop_table_qry = QSqlQuery()
            logger_setup.get_logger().info('Dropping TempPivotTable')
            if not drop_table_qry.exec('DROP TABLE IF EXISTS TempPivotTable'):
                logger_setup.get_logger().critical(
                    f'Error dropping TempPivotTable: {query.lastError().text()}')
                logger_setup.get_logger().critical(f'SQL command: {sql_query}')

            create_table_qry = QSqlQuery()
            # creating new TempPivotTable from existing query string data
            sql_temptable_create = 'CREATE TEMP TABLE TempPivotTable AS SELECT * FROM (' + query_str + ')'
            logger_setup.get_logger().info('Creating table TempPivotTable')
            if not create_table_qry.exec(sql_temptable_create):
                logger_setup.get_logger().critical(
                    f'Error creating TempPivotTable: {query.lastError().text()}')
                logger_setup.get_logger().critical(f'SQL command: {sql_query}')
                return
            logger_setup.get_logger().info('Created table TempPivotTable successfully')

            #defaults to pivot based on the first column in the exporter.
            first_tuple = next(iter(ordered_columns))
            pivot_col = first_tuple[1]
            pivot_col = self.column_name_mappings[pivot_col]

            # finds distinct list of first column values.
            distinct_first_column_query = QSqlQuery()
            first_column_list = []
            sql_distinct_first_column = f'SELECT DISTINCT {pivot_col} FROM TempPivotTable ORDER BY {pivot_col}'
            if distinct_first_column_query.exec(sql_distinct_first_column):
                if distinct_first_column_query.next():
                    while distinct_first_column_query.isValid():
                        first_column_list.append(distinct_first_column_query.value(0))
                        distinct_first_column_query.next()
                else:
                    # if no columns/values are found then could be an error, check if items are checked, if there are
                    # then something went wrong.
                    if not (len(self.checked_sample_list) == 0 and
                        len(self.checked_aliquot_list) == 0 and
                        len(self.checked_spot_list) == 0):

                        logger_setup.get_logger().critical('No rows returned for distinct first column')
                        model = QSqlQueryModel()
                        tableView.setModel(model)
                    return
            else:
                logger_setup.get_logger().critical(
                    f'Error selecting distinct values in table: {query.lastError().text()}')
                logger_setup.get_logger().critical(f'SQL command: {sql_query}')
                return
            case_expressions = []

            # Creates the column names for the first col and other columns, so if SampleID, BestAge is being pivot
            # with samples in the list as S1, S2, S3, then:
            # end result should be S1_BestAge, S2_BestAge, S3_BestAge
            for name in first_column_list:
                for table, field in ordered_columns:

                    if self.column_name_mappings[field] == pivot_col:
                        continue
                    case_expressions.append(f'MAX(CASE WHEN [{pivot_col}] = \'{name}\' THEN [{field}] END) AS [{name + "_" + self.column_name_mappings[field]}]')

            case_list_sql = '\n, '.join(case_expressions)

            # final pivot string, takes the data from TempPivotTable and modifies it.
            query_str = (f"""With cte AS (SELECT {columns_str}, ROW_NUMBER() OVER (
            PARTITION BY {pivot_col}
            ORDER BY rowid) AS RowNum
            FROM TempPivotTable)
            SELECT {case_list_sql}
            FROM cte c
            GROUP BY c.RowNum
            ORDER BY c.RowNum""")


        # At this point the final query_str is complete, either with or without pivot.
        # saves final string used for exporting, removed LIMIT, and saved model for future use.
        model = QSqlQueryModel()
        model.setQuery(query_str)
        self.worksheet_tabs_dict[current_worksheet_name]['sql'] = query_str.replace('LIMIT 250', '')
        self.worksheet_tabs_dict[current_worksheet_name]['model'] = model

        # Remove LIMIT 250 from the original query string and build the COUNT query, for the count label
        counter_sql_query = f"SELECT COUNT('UPbAnalyses') FROM ({self.worksheet_tabs_dict[current_worksheet_name]['sql']}) AS SubQuery"

        # Prepare and execute the query
        counter_query = QSqlQuery()
        logger_setup.get_logger().debug(f"SQL Command: {counter_sql_query}")
        if not counter_query.exec(counter_sql_query):
            logger_setup.get_logger().critical(
                f'Error fetching total records: {counter_query.lastError().text()}')
            logger_setup.get_logger().critical(f'SQL command: {counter_sql_query}')
            return
        else:
            # Move to the first record to retrieve the count
            if counter_query.next():
                count = counter_query.value(0)
                if count >= 250:
                    self.worksheet_tabs_dict[current_worksheet_name]['label'].setText(f"Showing 250/{count} rows")
                else:
                    self.worksheet_tabs_dict[current_worksheet_name]['label'].setText(f"Showing {count} rows")
            else:
                # Handle case where query doesn't return a result
                self.worksheet_tabs_dict[current_worksheet_name]['label'].setText(f"Number of Rows: 0")

        tableView.setModel(model)


    def export_button(self):
        match self.exportformat_comboBox.currentText():
            case 'detritalPy':
                self.export_to_excel()
            case 'IsoplotR - 07/35, 06/38, 04/38, 07/06, 04/07, 04/06':
                self.export_to_csv()
            case 'IsoplotR - 38/06, 07/06':
                self.export_to_csv()
            case 'DZStats - Intersample':
                self.export_to_csv()
            case 'DZStats - Two Sample Compare':
                # Requires 2 samples be in two csv files.
                self.export_to_csv(one_file=False)
            case 'Database':
                self.export_to_datbase()
            case 'Custom':
                if self.fileformat_comboBox.currentText() == 'Excel (.xlsx)':
                    self.export_to_excel()
                elif self.fileformat_comboBox.currentText() == 'Comma-Separated Value (.csv)':
                    self.export_to_csv()

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

        sample_id_to_subset = self.checked_sample_list

        if 'target_connection' in QSqlDatabase().connectionNames():
            QSqlDatabase.database('temp').close()
            QSqlDatabase().removeDatabase('temp')
            os.remove("temp.db")

        tgt_db = QSqlDatabase().addDatabase('QSQLITE', 'target_connection')
        tgt_db.setDatabaseName(fileName)
        tgt_db.open()

        src_db = QSqlDatabase()

        ExportDatabase.subset_database(src_db, tgt_db, sample_id_to_subset)
        tgt_db.commit()
        tgt_db.close()

        QSqlDatabase().removeDatabase('target_connection')

        msg = QMessageBox.information(self, "Database Export", "Database has exported successfully", None, buttons=QMessageBox.StandardButton.Ok)
        msg.exec()
        QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.dirname(fileName)))

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
            sql = info['sql']
            if first_sheet:
                ws = wb.active
                ws.title = sheet_name
                first_sheet = False
            else:
                ws = wb.create_sheet(title=sheet_name)

            query = QSqlQuery()
            query.prepare(sql)

            if not query.exec():
                logger_setup.get_logger().critical(
                    f'Error exporting query to excel: {query.lastError().text()}')
                logger_setup.get_logger().critical(f'SQL command: {sql}')
                return

            # Retrieve column names
            column_count = query.record().count()

            if bool(self.worksheet_tabs_dict[sheet_name]['headers']):
                headers = [query.record().fieldName(i) for i in range(column_count)]

                # Write headers to the first row
                for col_idx, header in enumerate(headers, start=1):
                    ws.cell(row=1, column=col_idx, value=header)

            # Write data rows
            row_idx = 2  # Start from the second row
            while query.next():
                for col in range(column_count):
                    ws.cell(row=row_idx, column=col + 1, value=query.value(col))
                row_idx += 1

        # Attempt to save the workbook
        try:
            wb.save(fileName)
        except Exception as e:
            QMessageBox.warning(None, "Save Failed", f"Could not save the Excel file.\n{e}")
            return

        # Open the file using the system's default application
        QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(fileName))

    def export_to_csv(self, one_file=True):
        # Prompt user for where to save the CSV file
        if one_file:
            fileName, _ = QFileDialog.getSaveFileName(
                None,
                "Save CSV File",
                "",
                "Comma-Separated Values Files (*.csv)"
            )

            if not fileName:
                return

            # Ensure the filename ends with .xlsx
            if not fileName.lower().endswith(".csv"):
                fileName += ".csv"
        else:
            directory = QFileDialog.getExistingDirectory(None, "Select Directory to Save CSV Files", "")

            if not directory:
                return

        for sheet_name, info in self.worksheet_tabs_dict.items():
            if not one_file:
                fileName = os.path.join(directory, f"{sheet_name}.csv")
            try:
                with open(fileName, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)

                    self.update_table_view(worksheet_name=sheet_name)
                    sql = info['sql']

                    query = QSqlQuery()
                    query.prepare(sql)

                    if not query.exec():
                        QMessageBox.warning(None, "Query Failed",
                                            f"Query execution failed for {sheet_name}: {query.lastError().text()}")
                        continue

                    column_count = query.record().count()

                    if self.worksheet_tabs_dict[sheet_name]['headers']:
                        headers = [query.record().fieldName(i) for i in range(column_count)]
                        # Write headers
                        writer.writerow(headers)

                    # Write data rows
                    while query.next():
                        row = [query.value(col) for col in range(column_count)]
                        writer.writerow(row)

            except Exception as e:
                QMessageBox.warning(None, "Save Failed", f"Could not save the CSV file.\n{e}")
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
        self.column_name_mappings.clear()
        match self.exportformat_comboBox.currentText():
            # DetritalPy requires an excel file, with multiple sheets
            # sheet 1 (Samples) is a distinct list of sample, units, basins(), age, lat, long, and source
            # sheet 2 (ZrUPb) is list of samples, grains, analysis, and upb data

            case 'detritalPy':
                self.fileformat_comboBox.setCurrentText('Excel (.xlsx)')
                Samples_columns= {
                    ('Samples', 'SampleName'): True,
                    ('Units', 'UnitName'): True,
                    ('Regions', 'RegionName'): True,
                    # ('GPSLocations', 'Latitude'): True,
                    # ('Samples', 'Longitude'): True,
                    ('References', 'ReferenceDisplay'): True
                }
                self.add_worksheet_tab('Samples', True, False, Samples_columns, Samples_columns, True)

                ZrUPb_columns = {
                    ('Samples', 'SampleName'): True,
                    ('Aliquots', 'AliquotName'): True,
                    ('Spots', 'SpotName'): True,

                    ('UPbAnalyses', "Calculated206Pb/204Pb"): True,
                    ('UPbAnalyses', "Uppm"): True,
                    ('UPbAnalyses', "CalculatedU/Th"): True,
                    ('UPbAnalyses', "CalculatedTh/U"): True,

                    ('UPbAnalyses', "Calculated207Pb/206Pb"): True,
                    ('UPbAnalyses', "Calculated207Pb/206PbError"): True,
                    ('UPbAnalyses', "Calculated207Pb/235U"): True,
                    ('UPbAnalyses', "Calculated207Pb/235UError"): True,
                    ('UPbAnalyses', "Calculated206Pb/238U"): True,
                    ('UPbAnalyses', "Calculated206Pb/238UError"): True,

                    ('UPbAnalyses', "ErrorCorr/Rho"): True,

                    ('UPbAnalyses', "Calculated207Pb/235UAge"): True,
                    ('UPbAnalyses', "Calculated207Pb/235UAgeError"): True,

                    ('UPbAnalyses', "Calculated206Pb/238UAge"): True,
                    ('UPbAnalyses', "Calculated206Pb/238UAgeError"): True,

                    ('UPbAnalyses', "Calculated207Pb/206PbAge"): True,
                    ('UPbAnalyses', "Calculated207Pb/206PbAgeError"): True,

                    ('UPbAnalyses', "CalculatedBestAge"): True,
                    ('UPbAnalyses', "CalculatedBestAgeError"): True,

                    ('UPbAnalyses', "CalculatedConcordance"): True
                }

                self.column_name_mappings = {
                    "SampleName": "Sample_ID",
                    "UnitName": "Unit",
                    "RegionName": "Basin",
                    "Latitude": "Latitude",
                    "Longitude": "Longitude",
                    "ReferenceDisplay": "Source",

                    "AliquotName": "Grain_ID",
                    "SpotName": "Analysis_ID",

                    "Calculated206Pb/204Pb": "206Pb_204Pb",
                    "Uppm": "U_ppm",
                    "CalculatedU/Th": "U_Th",
                    "CalculatedTh/U": "Th_U",

                    "Calculated207Pb/206Pb": "207Pb_206Pb",
                    "Calculated207Pb/206PbError": "207Pb_206Pb_err",
                    "Calculated207Pb/235U": "207Pb_235Pb",
                    "Calculated207Pb/235UError": "207Pb_235Pb_err",
                    "Calculated206Pb/238U": "206Pb_238Pb",
                    "Calculated206Pb/238UError": "206Pb_238Pb_err",

                    "ErrorCorr/Rho": "RHO",

                    "Calculated207Pb/235UAge": "75Age",
                    "Calculated207Pb/235UAgeError": "75Age_err",

                    "Calculated206Pb/238UAge": "68Age",
                    "Calculated206Pb/238UAgeError": "68Age_err",

                    "Calculated207Pb/206PbAge": "76Age",
                    "Calculated207Pb/206PbAgeError": "76Age_err",

                    "CalculatedBestAge": "BestAge",
                    "CalculatedBestAgeError": "BestAge_err",

                    "CalculatedConcordance": "Disc"
                }

                self.add_worksheet_tab('ZrUPb', False, False, ZrUPb_columns, ZrUPb_columns, True)
                return
            case 'IsoplotR - 07/35, 06/38, 04/38, 07/06, 04/07, 04/06':
                # modeled after UPb6.csv in IsoplotR
                # 207/235
                # 206/238
                # 204/238
                # 207/206
                # 204/207
                # 204/206
                self.fileformat_comboBox.setCurrentText('Comma-Separated Value (.csv)')
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
                    ('UPbAnalyses', 'Calculated204Pb/206PbError'): True,
                }
                self.add_worksheet_tab('IsoplotR', False, False, UPb_columns, UPb_columns, True)

            case 'IsoplotR - 38/06, 07/06':
                # modeled after UPb2.csv in IsoplotR
                # 238/206
                # 207/206
                self.fileformat_comboBox.setCurrentText('Comma-Separated Value (.csv)')
                UPb_columns = {
                    ('UPbAnalyses', 'Calculated207Pb/206Pb'): True,
                    ('UPbAnalyses', 'Calculated207Pb/206PbError'): True,
                    ('UPbAnalyses', 'Calculated238U/206Pb'): True,
                    ('UPbAnalyses', 'Calculated238U/206PbError'): True,
                }
                self.add_worksheet_tab('IsoplotR', False, False, UPb_columns, UPb_columns, True)

            case 'DZStats - Intersample':
                self.fileformat_comboBox.setCurrentText('Comma-Separated Value (.csv)')
                UPb_columns = {
                    ('Samples', 'SampleName'): True,
                    ('UPbAnalyses', 'CalculatedBestAge'): True,
                    ('UPbAnalyses', 'CalculatedBestAgeError'): True
                }
                self.add_worksheet_tab('DZStats - Intersample', False, True, UPb_columns, UPb_columns, False)
            # case 'DZStats - Two Sample Compare':
            #     self.fileformat_comboBox.setCurrentText('Comma-Separated Value (.csv)')
            #     UPb_columns = {
            #         ('Samples', 'SampleName'): True,
            #         ('UPbAnalyses', 'CalculatedBestAge'): True,
            #         ('UPbAnalyses', 'CalculatedBestAgeError'): True
            #     }
            #     self.add_worksheet_tab('DZStats - Two Sample Compare', False, True, UPb_columns, UPb_columns, False)
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
                    if 'temp' in QSqlDatabase().connectionNames():
                        QSqlDatabase.database('temp').close()
                        QSqlDatabase().removeDatabase('temp')
                        os.remove("temp.db")
                tgt_db_file = "temp.db"

                sample_id_to_subset = self.checked_sample_list

                tgt_db = QSqlDatabase().addDatabase('QSQLITE', 'temp')
                tgt_db.setDatabaseName(tgt_db_file)
                tgt_db.open()

                src_db = QSqlDatabase()

                ExportDatabase.subset_database(src_db, tgt_db, sample_id_to_subset)
                tgt_db.commit()
                tgt_db.close()

                # Create a new tab
                new_tab = DisplayTablesSimplified(self, tgt_db_file)
                tab_layout = QVBoxLayout(self)
                new_tab.setLayout(tab_layout)

                self.workbooktabs.addTab(new_tab, 'Database')
            case 'Custom':
                self.create_first_worksheet_tab()
                pass

    def update_step_2_list(self):
        # self.samplesincluded_comboBox.disconnect()

        self.updatetimer = QTimer()
        self.updatetimer.setSingleShot(True)

        self.samplesincluded_comboBox.setEnabled(True)
        self.step_2_label.show()
        self.samplesincluded_comboBox.show()
        self.filters_label.show()
        self.filters_label.setText("Select Additional Filters (optional):")
        self.filters_label.setToolTip("Additional filters to filter the samples, multiple filters union their sets together.")
        if self.selectionscope_comboBox.currentText() == 'Samples':
            self.samplesincluded_comboBox.setModel(self.samples_model)
            self.updatetimer.timeout.connect(lambda: self.update_sample_list(self.samples_model))
            self.samples_model.dataChanged.connect(lambda: self.updatetimer.start(1500))
            self.samplesincluded_comboBox.closing.connect(
                lambda: self.update_checked_list(self.samples_model, 'Samples'))
            self.update_checked_list(self.samples_model, 'Samples')
        elif self.selectionscope_comboBox.currentText() == 'Aliquots':
            self.samplesincluded_comboBox.setModel(self.aliquots_model)
            self.updatetimer.timeout.connect(lambda: self.update_sample_list(self.aliquots_model))
            self.aliquots_model.dataChanged.connect(lambda: self.updatetimer.start(1500))
            self.samplesincluded_comboBox.closing.connect(
                lambda: self.update_checked_list(self.aliquots_model, 'Samples'))
            self.update_checked_list(self.aliquots_model, 'Samples')
        elif self.selectionscope_comboBox.currentText() == 'Spots':
            self.samplesincluded_comboBox.setModel(self.spots_model)
            self.updatetimer.timeout.connect(lambda: self.update_sample_list(self.spots_model))
            self.spots_model.dataChanged.connect(lambda: self.updatetimer.start(1500))
            self.samplesincluded_comboBox.closing.connect(
                lambda: self.update_checked_list(self.spots_model, 'Samples'))
            self.update_checked_list(self.spots_model, 'Samples')
        elif self.selectionscope_comboBox.currentText() == 'Filter Groups':
            self.step_2_label.hide()
            self.samplesincluded_comboBox.hide()
            self.samples_model.clear_checks()
            self.checked_sample_list = []
            for row in range(self.samples_model.rowCount()):
                name_index = self.samples_model.index(row, 1, QtCore.QModelIndex())
                if self.samples_model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                    # Add the sample ID to the list
                    id_index = self.samples_model.index(row, 0, QtCore.QModelIndex())
                    self.checked_sample_list.append(self.samples_model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))

            self.checked_sample_names = f"({', '.join(map(str, self.checked_sample_list))})"
            self.filters_label.setText("Select Filters:")
            self.filters_label.setToolTip("")

        self.update_checked_list(self.filter_model, 'FilterGroups')
        self.update_checked_list(self.groupedfilter_model, 'GroupedFilterGroups')

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

    def update_groupedfilter_list(self, model):
        self.checked_grouped_filter_list = []
        for row in range(model.rowCount()):
            name_index = model.index(row, 1, QtCore.QModelIndex())
            if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                # Add the filter ID and JSON to the list
                id_index = model.index(row, 0, QtCore.QModelIndex())
                filter_json = model.index(row, 2, QtCore.QModelIndex())
                self.checked_grouped_filter_list.append((model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole),
                                                         model.data(name_index, QtCore.Qt.ItemDataRole.DisplayRole),
                                                         model.data(filter_json, QtCore.Qt.ItemDataRole.DisplayRole)))
        if self.exportformat_comboBox.currentText() != 'Database':
            self.update_table_view()
        else:
            self.export_format()
    def open_columnname_mapping_dialog(self):
        # Get current selected columns
        current_worksheet_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        ordered_columns = self.worksheet_tabs_dict[current_worksheet_name].get('ordered_columns', [])

        if not ordered_columns:
            QMessageBox.warning(self, "No Columns Selected", "Please select columns before editing their name.")
            return

        # Open the dialog
        dialog = ColumnNamesDialog(self.column_name_mappings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get adjusted columns
            self.column_name_mappings = dialog.get_adjusted_columns()
            self.update_table_view()

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
            self.update_table_view(order_changed=True)

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

class ColumnNamesDialog(QDialog):
    def __init__(self, mapped_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Column Names")
        self.resize(350, 450)
        self.mapped_columns = mapped_columns

        # Create widgets
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)

        # Populate list with columns
        for original, field_name in self.mapped_columns.items():
            item = QListWidgetItem(f"{original}: {field_name}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)  # Make items editable
            self.list_widget.addItem(item)

        # Buttons
        self.rename_button = QPushButton("Rename Selected")
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Connect signals
        self.rename_button.clicked.connect(self.rename_selected_item)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.rename_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def rename_selected_item(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.list_widget.editItem(current_item)
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to rename.")

    def delete_selected_item(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.list_widget.takeItem(current_row)
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")

    def get_adjusted_columns(self):
        adjusted_columns = {}
        for index, (original_name, field_name) in enumerate(self.mapped_columns.items()):
            item_text = self.list_widget.item(index).text()

            # Extract the new name from the list item text (assuming format: "original: new_name")
            if ": " in item_text:
                _, new_name = item_text.split(": ", 1)
            else:
                new_name = item_text  # Fallback if formatting isn't as expected

            # Store in dictionary
            adjusted_columns[original_name] = new_name  # Mapping original field to new name

        return adjusted_columns
