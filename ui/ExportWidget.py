import os
import sqlite3
import sys
from collections import Counter

from PyQt6 import uic, QtCore
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableView,
    QGridLayout, QLabel, QCheckBox, QSpacerItem,
    QSizePolicy, QTabWidget, QInputDialog, QDialog, QListWidget, QHBoxLayout, QMessageBox
)
from PyQt6.uic import loadUi

from openpyxl import Workbook
from ui import Filters
from Functions import SQLUtils

from Functions.Table_classes import CheckableSqlTableModel, CheckableComboBox


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
        self.workbook_tabs = {}

        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.db_file = widget.db_file

        self.settings = QSettings("CSUF", "GeoChron")

        # self.loadWindowState()

        self.samplesincluded_comboBox: CheckableComboBox()

        # Connect buttons to methods
        self.add_workbook_button.clicked.connect(lambda: self.add_workbook_tab(None, None, None))
        self.remove_workbook_button.clicked.connect(self.remove_current_workbook_tab)
        self.export_pushbutton.clicked.connect(self.export_to_excel)

        # List of all user-viewable tables in the database
        self.user_view_tables = ['Ages',
                                 'Age Signatures', 'Aliquots', 'Aliquot Contexts', 'Analysis Methods', 'Columns',
                                 'Instruments', 'Lab Facilities',
                                 'Regions', 'Rock Types', 'Sample Contexts', 'Samples', 'Sampling Methods', 'Settings',
                                 'Sources', 'Spots',
                                 'Spot Compositions', 'Spot Contexts', 'Units', 'UPb Data', 'UPb Analysis Methods'
                                 ]

        self.table_fields = {
            'Ages': [
                "AgeName", "MaxMa", "MinMa", "AgeCreated", "AgeModified"
            ],
            'Age Signatures': [
                "AgeSignatureName", "AgeSignatureDescription", "AgeSignatureCreated", "AgeSignatureModified"
            ],
            'Aliquots': [
                "AliquotName", "AliquotCreated", "AliquotModified"
            ],
            'Aliquot Contexts': [
                "AliquotContextName", "AliquotContextDescription", "AliquotContextCreated", "AliquotContextModified"
            ],
            'Analysis Methods': [
                "AnalysisMethodsName", "AnalysisMethodsDescription", "AnalysisMethodsCreated", "AnalysisMethodsModified"
            ],
            'Columns': [
                "ColumnName", "ColumnDescription", "ColumnCreated", "ColumnModified"
            ],
            'Instruments': [
                "InstrumentName", "InstrumentDescription", "InstrumentCreated", "InstrumentModified"
            ],
            'Lab Facilities': [
                "LabFacilityName", "LabFacilityDescription", "LabFacilityCreated", "LabFacilityModified"
            ],
            'Regions': [
                "RegionName", "RegionDescription", "RegionCreated", "RegionModified"
            ],
            'RockTypes': [
                "RockTypeName", "RockTypeDescription", "RockTypeCreated", "RockTypeModified"
            ],
            'Sample Contexts': [
                "SampleContextName", "SampleContextDescription", "SampleContextCreated", "SampleContextModified"
            ],
            'Samples': [
                "SampleName", "AverageAge", "AverageAgeError", "ErrorSigma", "OldestAge", "YoungestAge",
                "OldestAgeID", "YoungestAgeID", "HeightDepth", "HeightDepthError", "HeightDepthUnit",
                "LatDeg", "LatMin", "LatSec", "LonDeg", "LonMin", "LonSec", "UTMZone", "UTMN", "UTME",
                "Elev", "ElevError", "ElevUnit", "Description", "SampleCreated", "SampleModified"
            ],
            'Sampling Methods': [
                "SamplingMethodName", "SamplingMethodDescription", "SamplingMethodCreated", "SamplingMethodModified"
            ],
            'Settings': [
                "SettingName", "SettingDescription", "SettingCreated", "SettingModified"
            ],
            'Sources': [
                "Authors", "Year", "Title", "Source", "doi", "ShortCitation", "SourceCreated", "SourceModified"
            ],
            'Spots': [
                "SpotName", "SpotCreated", "SpotModified"
            ],
            'Spot Compositions': [
                "SpotCompositionName", "SpotCompositionDescription", "SpotCompositionCreated", "SpotCompositionModified"
            ],
            'Spot Contexts': [
                "SpotContextName", "SpotContextDescription", "SpotContextCreated", "SpotContextModified"
            ],
            'Units': [
                "UnitName", "UnitDescription", "UnitCreated", "UnitModified"
            ],
            'UPb Data': [
                "U/Th", "206Pb/204Pb", "206Pb/207Pb", "206Pb/207Pberror", "207Pb/235U", "207Pb/235Uerror",
                "206Pb/238U", "206Pb/238Uerror", "ErrorCorr", "206Pb/207PbAge", "206Pb/207PbAgeError",
                "207Pb/235UAge", "207Pb/235UAgeError", "206Pb/238UAge", "206Pb/238UAgeError", "BestAge", "Error",
                "Conc",
                "UPbAnalysisCreated", "UPbAnalysisModified"
            ],
            'UPb Analysis Methods': [
                "UPbAnalysisMethodName", "UPbAnalysisMethodDescription", "UPbAnalysisMethodCreated",
                "UPbAnalysisMethodModified"
            ]
        }

        self.columnselection_comboBox.addItems(self.user_view_tables)

        self.samples_model = CheckableSqlTableModel()
        self.samples_model = self.set_table(self.samples_model, 'Samples')

        self.aliquots_model = CheckableSqlTableModel()
        self.aliquots_model = self.set_table(self.aliquots_model, 'Aliquots')

        self.spots_model = CheckableSqlTableModel()
        self.spots_model = self.set_table(self.spots_model, 'Spots')

        self.filter_model = CheckableSqlTableModel()
        self.filter_model = self.set_table(self.filter_model, 'FilterGroups')
        self.filterselection_comboBox.setModel(self.filter_model)
        self.filterselection_comboBox.currentIndexChanged.connect(lambda: self.update_filter_list(self.filter_model))

        # Fix for updating the filter list when the filter model is updated
        self.filter_model.dataChanged.connect(lambda: self.update_filter_list(self.filter_model))

        self.update_step_2_list()
        self.populate_stack()
        self.export_format()

        self.editorder_pushbutton.clicked.connect(self.open_column_order_dialog)

        self.exportformat_comboBox.currentIndexChanged.connect(self.export_format)
        self.selectionscope_comboBox.currentIndexChanged.connect(self.update_step_2_list)
        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)


    def tab_changed(self):
        self.save_checkbox_states(self.previous_workbook)
        self.load_checkbox_states()
        self.previous_workbook = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        self.update_table_view()

    def rename_workbook_tab(self, index):
        if index == -1:
            return  # No tab was double-clicked

        current_workbook_name = self.workbooktabs.tabText(index)

        # Prompt the user for a new name
        new_name, ok = QInputDialog.getText(self, "Rename Workbook", "Enter new workbook name:",
                                            text=current_workbook_name)
        if not ok or not new_name:
            return  # User canceled or didn't enter a name

        if new_name in self.workbook_tabs:
            QMessageBox.warning(self, "Duplicate Name", "A workbook with that name already exists.")
            return

        # Update the workbook_tabs dictionary
        self.workbook_tabs[new_name] = self.workbook_tabs.pop(current_workbook_name)

        # Update the tab text
        self.workbooktabs.setTabText(index, new_name)

    def create_first_workbook_tab(self):
        # Create the first workbook tab using the existing tableView
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        tab1.setLayout(tab1_layout)
        tableView = QTableView()
        distinct_checkbox = QCheckBox("Distinct Rows")
        distinct_checkbox.setToolTip("Check this box to only show distinct or unique rows a single time")
        distinct_checkbox.setChecked(False)
        tab1_layout.addWidget(distinct_checkbox)
        tab1_layout.addWidget(tableView)

        # Create a data model for this tableView
        model = QSqlQueryModel()

        self.workbook_tabs["Workbook 1"] = {
            'tableView': tableView,
            'model': model,
            'distinct': False,
            'selected_columns': {},
            'ordered_columns': {}
        }

        self.workbooktabs.blockSignals(True)
        self.workbooktabs.addTab(tab1, "Workbook 1")
        self.workbooktabs.blockSignals(False)

        self.load_checkbox_states('Workbook 1')

        distinct_checkbox.stateChanged.connect(self.update_distinct_checkbox)
        self.update_table_view()
        self.repaint()

    def delete_all_workbook_tabs(self):
        self.workbooktabs.setParent(None)
        self.verticalLayout_7.removeWidget(self.workbooktabs)
        self.workbooktabs.deleteLater()

        self.workbooktabs = QTabWidget()

        self.workbooktabs.currentChanged.connect(self.tab_changed)
        self.workbooktabs.tabBarDoubleClicked.connect(self.rename_workbook_tab)
        self.previous_workbook = self.workbooktabs.tabText(self.workbooktabs.currentIndex())

        self.verticalLayout_7.addWidget(self.workbooktabs)

        self.workbook_tabs = {}
        self.previous_workbook = None


    def add_workbook_tab(self, workbook_name=None, distinct=False, selected_columns=None, ordered_columns=None):
        # Determine the new workbook name
        if ordered_columns is None:
            ordered_columns = {}
        if selected_columns is None:
            selected_columns = {}
        if workbook_name is None:
            workbook_name, ok = QInputDialog.getText(self, "New Workbook", "Enter workbook name:")
            if not ok or not workbook_name:
                return  # User canceled or didn't enter a name

            if workbook_name in self.workbook_tabs:
                QMessageBox.warning(self, "Duplicate Name", "A workbook with that name already exists.")
                return


        # Create a new tableView
        new_tableView = QTableView()

        # Create a new data model for the new tableView
        model = QSqlQueryModel()

        # Create a new tab
        new_tab = QWidget()
        tab_layout = QVBoxLayout()
        new_tab.setLayout(tab_layout)
        distinct_checkbox = QCheckBox("Distinct Rows")
        distinct_checkbox.setToolTip("Check this box to only show distinct or unique rows a single time")
        distinct_checkbox.setChecked(distinct)
        tab_layout.addWidget(distinct_checkbox)
        tab_layout.addWidget(new_tableView)

        # Store the tableView and model in the workbook_tabs dictionary
        self.workbook_tabs[workbook_name] = {
            'tableView': new_tableView,
            'model': model,
            'distinct': distinct,
            'selected_columns': selected_columns,
            'ordered_columns': ordered_columns
        }
        self.workbooktabs.blockSignals(True)
        self.workbooktabs.addTab(new_tab, workbook_name)

        self.workbooktabs.blockSignals(False)
        self.load_checkbox_states(workbook_name)
        self.workbooktabs.setCurrentWidget(new_tab)

        #todo change to method so it actually works
        distinct_checkbox.stateChanged.connect(self.update_distinct_checkbox)
        # Update the table view
        self.update_table_view()
        self.repaint()

    def update_distinct_checkbox(self):
        current_workbook_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        distinct_checkbox = self.workbook_tabs[current_workbook_name]['distinct']
        self.workbook_tabs[current_workbook_name]['distinct'] = not distinct_checkbox
        self.update_table_view()
        print('checkbox state  ', distinct_checkbox)

    def remove_current_workbook_tab(self):
        if self.workbooktabs.count() <= 1:
            QMessageBox.warning(self, "Cannot Remove Workbook", "At least one workbook must remain.")
            return

        # Get the current workbook name
        current_index = self.workbooktabs.currentIndex()
        current_workbook_name = self.workbooktabs.tabText(current_index)

        reply = QMessageBox.question(self, 'Remove Workbook',
                                     f"Are you sure you want to remove '{current_workbook_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Remove the tab from the tabWidget
        self.workbooktabs.removeTab(current_index)

        # Remove the workbook from the dictionary
        del self.workbook_tabs[current_workbook_name]

    def populate_stack(self):
        for table_name, field_items in self.table_fields.items():
            # Create a widget and layout for each table
            table_widget = QWidget()
            layout = QGridLayout()
            layout.setSpacing(8)  # Set minimal spacing between rows and columns
            layout.setContentsMargins(0, 0, 0, 0)  # Remove any outer margins

            # Populate the layout with labels and checkboxes for each field
            row, col = 0, 0
            for field in field_items:
                label = QLabel(field)
                checkbox = QCheckBox()

                # Set size policies to prevent expanding
                label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

                layout.addWidget(label, row, col * 2, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
                layout.addWidget(checkbox, row, col * 2 + 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

                if col == 1:  # After two columns are filled, move to the next row
                    row += 1
                col = (col + 1) % 2

                # Set the field name as a property of the checkbox to save and restore state
                checkbox.setProperty("field_name", field)
                checkbox.setProperty('table_name', table_name)
                checkbox.checkStateChanged.connect(lambda: self.update_table_view(deleted=False))
                # checkbox.checkStateChanged.connect(lamd)
            # Add a vertical spacer at the bottom to push content upwards
            vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            layout.addItem(vertical_spacer, row + 1, 0, 1, 2)  # Add spacer across both columns

            # Set the layout for this table's widget and add it to the stack
            table_widget.setLayout(layout)
            self.columnattributes_stack.addWidget(table_widget)

    def switch_table_layout(self):
        # Switch the stack widget to show the layout corresponding to the selected table
        selected_table_index = self.columnselection_comboBox.currentIndex()
        self.columnattributes_stack.setCurrentIndex(selected_table_index)
        # Save and load checkbox states for each table
        self.save_checkbox_states()
        self.load_checkbox_states()

        self.update_table_view()

    def save_checkbox_states(self, previous_workbook=None):
        # Save the state of checkboxes for all tables
        current_workbook_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        checkbox_states = {}

        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            table_name = self.columnselection_comboBox.itemText(index)
            if table_widget:
                layout = table_widget.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item is None:
                        continue
                    widget = item.widget()
                    if isinstance(widget, QCheckBox):
                        field_name = widget.property('field_name')
                        checked = widget.isChecked()
                        checkbox_states[(table_name, field_name)] = checked
        # Store checkbox_states in the workbook's data
        if previous_workbook is None:
            self.workbook_tabs[current_workbook_name]['selected_columns'] = checkbox_states
        else:
            self.workbook_tabs[previous_workbook]['selected_columns'] = checkbox_states

    def load_checkbox_states(self, workbook_name=None):
        # Load the state of checkboxes for all tables

        if workbook_name is not None:
            current_workbook_name = workbook_name
        else:
            current_workbook_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        checkbox_states = self.workbook_tabs[current_workbook_name].get('selected_columns', {})

        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            table_name = self.columnselection_comboBox.itemText(index)
            if table_widget:
                layout = table_widget.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item is None:
                        continue
                    widget = item.widget()
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
                layout = table_widget.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item is None:
                        continue
                    widget = item.widget()
                    if isinstance(widget, QCheckBox) and widget.isChecked():

                        field_name = widget.property('field_name')
                        # Ensure table_name is associated with the checkbox
                        widget_table_name = widget.property('table_name')
                        print(field_name, widget_table_name)
                        if widget_table_name is None:
                            widget.setProperty('table_name', table_name)
                            widget_table_name = table_name
                        selected_columns[(widget_table_name, field_name)] = True
        # Store selected_columns in the current workbook
        current_workbook_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        self.workbook_tabs[current_workbook_name]['selected_columns'] = selected_columns
        return selected_columns

    def select_checkboxes(self, values):
        # Values should be tuple format ('table_name', 'field_name')
        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            if table_widget:
                layout = table_widget.layout()
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item is None:
                        continue
                    widget = item.widget()
                    if isinstance(widget, QCheckBox):
                        table_name = widget.property('table_name')
                        field_name = widget.property('field_name')

                        if (table_name, field_name) in values:
                            widget.setChecked(True)
        self.update_table_view()

    def update_table_view(self, deleted=False, workbook_name=None):
        # Get the current workbook
        if workbook_name is None:
            current_workbook_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        else:
            current_workbook_name = workbook_name
        tableView = self.workbook_tabs[current_workbook_name]['tableView']
        # self.load_checkbox_states()
        if deleted:
            self.workbook_tabs[current_workbook_name]['selected_columns'] = self.workbook_tabs[current_workbook_name].get('ordered_columns', {})
            ordered_columns = self.workbook_tabs[current_workbook_name].get('ordered_columns', {})

        else:
            # # update selected columns
            self.get_selected_values()

            # Get the selected columns for the current workbook
            selected_columns = self.workbook_tabs[current_workbook_name].get('selected_columns', {})
            ordered_columns = self.workbook_tabs[current_workbook_name].get('ordered_columns', {})

            if Counter(selected_columns) != Counter(ordered_columns):
                ordered_columns = selected_columns
                self.workbook_tabs[current_workbook_name]['ordered_columns'] = ordered_columns


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

            if SQLUtils.aliquot_join not in join:
                join += SQLUtils.aliquot_join + '\n'
            if SQLUtils.spot_join not in join:
                join += SQLUtils.spot_join + '\n'
            if SQLUtils.upb_data_join not in join:
                join += SQLUtils.upb_data_join + '\n'

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

        #todo add distinct checkbox, always use first column, default to false
        if len(self.checked_sample_names) > 2:
            query_str = f"SELECT {'DISTINCT' if self.workbook_tabs[current_workbook_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} LIMIT 250"
            if len(filtered_where_clause) > 0:
                query_str = f"SELECT {'DISTINCT' if self.workbook_tabs[current_workbook_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} AND UPbAnalysisID IN {ids} LIMIT 250"
        else:
            query_str = f"SELECT {'DISTINCT' if self.workbook_tabs[current_workbook_name]['distinct'] is True else '' } {columns_str} FROM Samples {join} WHERE FALSE"
        print (query_str)
        model = QSqlQueryModel()
        model.setQuery(query_str)
        self.workbook_tabs[current_workbook_name]['model'] = model

        for col, (table, field) in enumerate(ordered_columns):
            header = f"{table}.{field}"
            model.setHeaderData(col, QtCore.Qt.Orientation.Horizontal, header, QtCore.Qt.ItemDataRole.DisplayRole)

        tableView.setModel(model)

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

        for sheet_name, info in self.workbook_tabs.items():
            self.update_table_view(workbook_name=sheet_name)
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
        self.delete_all_workbook_tabs()
        match self.exportformat_comboBox.currentText():
            case 'detritalPy':
                Samples_columns= {('Samples', 'SampleName'): True,
                                   ('Units', 'UnitName'): True,
                                   ('Samples', 'Latitude'): True,
                                   ('Samples', 'Longitude'): True,
                                   ('Sources', 'ShortCitation'): True}
                self.add_workbook_tab('Samples', True, Samples_columns, Samples_columns)

                ZrUPb_columns = {('Samples', 'SampleName'): True,
                          ('Spots', 'SpotName'): True,
                          ('UPb Data', 'Uppm'): True,
                          ('UPb Data', 'U/Th'): True,
                          ('UPb Data', 'BestAge'): True,
                          ('UPb Data', 'Error'): True,
                          ('UPb Data', 'Conc'): True}

                self.add_workbook_tab('ZrUPb', False, ZrUPb_columns, ZrUPb_columns)
                return
            case 'IsoplotR':
                pass
            case 'DZStats':
                pass
            case 'Database':
                pass
            case 'Custom':
                self.create_first_workbook_tab()
                return

    def update_step_2_list(self):
        if self.selectionscope_comboBox.currentText() == 'Samples':
            self.samplesincluded_comboBox.setModel(self.samples_model)
            self.samples_model.dataChanged.connect(lambda: self.update_sample_list(self.samples_model))
        elif self.selectionscope_comboBox.currentText() == 'Aliquots':
            self.samplesincluded_comboBox.setModel(self.aliquots_model)
            self.aliquots_model.dataChanged.connect(lambda: self.update_sample_list(self.aliquots_model))
        elif self.selectionscope_comboBox.currentText() == 'Spots':
            self.samplesincluded_comboBox.setModel(self.spots_model)
            self.spots_model.dataChanged.connect(lambda: self.update_sample_list(self.spots_model))

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

        self.update_table_view()

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

        self.update_table_view()

    def open_column_order_dialog(self):
        # Get current selected columns
        current_workbook_name = self.workbooktabs.tabText(self.workbooktabs.currentIndex())
        ordered_columns = self.workbook_tabs[current_workbook_name].get('ordered_columns', [])

        if not ordered_columns:
            QMessageBox.warning(self, "No Columns Selected", "Please select columns before editing their order.")
            return

        # Open the dialog
        dialog = ColumnOrderDialog(ordered_columns, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get adjusted columns
            adjusted_columns = dialog.get_adjusted_columns()
            # Update the selected columns
            self.workbook_tabs[current_workbook_name]['ordered_columns'] = adjusted_columns
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