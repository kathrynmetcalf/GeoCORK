import sqlite3
from dataclasses import field

from PyQt6 import uic, QtSql, QtCore
from PyQt6.QtCore import QSettings, QSize
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel
from PyQt6.QtWidgets import QWidget, QApplication, QGridLayout, QLabel, QCheckBox, QStackedWidget, QSpacerItem, \
    QSizePolicy, QTableView

import Filters
import SQLUtils
from Table_classes import CheckableSqlTableModel, CheckableComboBox
from QComboBoxLabel import QComboBoxLabel
from Tree_classes import CheckableTreeCombobox
from collections import Counter

class ExportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.checked_filter_list = []

        self.checked_sample_list = []
        self.checked_aliquot_list = []
        self.checked_spot_list = []

        self.checked_sample_names = '()'
        self.checked_aliquot_names = '()'
        self.checked_spot_names = '()'

        self.selected_columns = []
        self.ordered_columns = []

        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.db_file = widget.db_file

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)
        self.settings = QSettings("CSUF", "GeoChron")

        ok = self.db.open()

        # self.loadWindowState()

        self.samplesincluded_comboBox: CheckableComboBox()

        uic.loadUi('ui/ExporterUI.ui', self)

        # list of all user-viewable tables in the database
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

        #todo fix for updating the filter list when the filter model is updated
        self.filter_model.dataChanged.connect(lambda: self.update_filter_list(self.filter_model))

        self.update_step_2_list()
        # self.update_column_attributes()
        self.populate_stack()
        self.export_format()

        self.editorder_pushbutton.clicked.connect(self.open_column_order_dialog)
        self.viewpreview_pushbutton.clicked.connect(self.update_table_view)
        # self.export_pushbutton.clicked.connect(self.export_format())

        self.exportformat_comboBox.currentIndexChanged.connect(self.export_format)
        self.selectionscope_comboBox.currentIndexChanged.connect(self.update_step_2_list)
        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)

        self.show()

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
                checkbox.checkStateChanged.connect(self.update_table_view)

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


    #todo for predefined formats (detritalPy, etc ) populate the fields with the correct fields
    def save_checkbox_states(self):
        # Save the state of checkboxes for the current table
        current_widget = self.columnattributes_stack.currentWidget()
        if current_widget:
            layout = current_widget.layout()
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QCheckBox):
                    # field_name = widget.property("field_name")
                    # Save checkbox state as a custom property or external storage
                    widget.setProperty("saved_state", widget.isChecked())

    def load_checkbox_states(self):
        # Load the state of checkboxes for the current table
        current_widget = self.columnattributes_stack.currentWidget()
        if current_widget:
            layout = current_widget.layout()
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QCheckBox):
                    # Retrieve and set the saved state if it exists
                    saved_state = widget.property("saved_state")
                    if saved_state is not None:
                        widget.setChecked(saved_state)


    def get_selected_values(self):
        selected_columns = []
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
                        if widget_table_name is None:
                            widget.setProperty('table_name', table_name)
                            widget_table_name = table_name
                        selected_columns.append((widget_table_name, field_name))
        self.selected_columns = tuple(selected_columns)
        return tuple(selected_columns)

    def select_checkboxes(self, values):
        #values should be tuple format ('table_name', 'field_name')
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
                            print(field_name)
                            widget.setChecked(True)
        self.update_table_view()

    def update_table_view(self):
        # Get the selected columns
        model = QSqlQueryModel()
        self.get_selected_values()

        if Counter(self.selected_columns) != Counter(self.ordered_columns):
            self.ordered_columns = self.get_selected_values()

        if not self.ordered_columns:
            # No columns selected, clear the table view
            self.tableView.setModel(None)
            return

        tables = []
        columns_str = ''
        for table, field in self.ordered_columns:
            tables.append(table)
            # Build the SQL query
            columns_str += f'[{field}], '

        columns_str = columns_str[0:-2]
        join = SQLUtils.get_join_from_table(tables)

        filtered_where_clause = ''
        ids = []
        for filter_id, filter_json in self.checked_filter_list:
            # print(filter_id, filter_json)
            if len(self.checked_filter_list) > 0:
                filtered_where_clause=Filters.process_json_to_sql(filter_json[1:-1], scope='UPbData')
                filtered_where_clause= filtered_where_clause[0:-1]

            sql_query = ''

            if SQLUtils.aliquot_join not in join:
                join += SQLUtils.aliquot_join + '\n'
            if SQLUtils.spot_join not in join:
                join += SQLUtils.spot_join + '\n'
            if SQLUtils.upb_data_join not in join:
                join += SQLUtils.upb_data_join + '\n'
            sql_query = f"SELECT DISTINCT UPbAnalysisID FROM ({filtered_where_clause});"

            conn = sqlite3.connect(self.db_file)
            with conn:
                for id in conn.execute(sql_query).fetchall():
                    ids.append(id[0])

        if len(self.checked_filter_list) == 1:
            ids = f"({', '.join(map(str, ids))})"
        else:
            # Count the occurrences of each ID
            id_counts = Counter(ids)
            # Extract IDs that appear more than once
            ids_more_than_once = [id for id, count in id_counts.items() if count > 1]

            ids = f"({', '.join(map(str, ids_more_than_once))})"

        #todo maybe change to pagination

        if len(self.checked_sample_names) > 2:
            query_str = f"SELECT {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} LIMIT 250"
            if len(filtered_where_clause) > 0:
                query_str = f"SELECT {columns_str} FROM Samples {join} WHERE Samples.SampleID IN {self.checked_sample_names} AND UPbAnalysisID IN {ids} LIMIT 250"
        else:
            query_str = f"SELECT {columns_str} FROM Samples {join} WHERE FALSE"
        print('final table query string')
        print(query_str)
        model.setQuery(query_str)

        for col in range(model.columnCount()):
            header = model.headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
            model.setHeaderData(col, QtCore.Qt.Orientation.Horizontal, header, QtCore.Qt.ItemDataRole.DisplayRole)

        self.tableView.setModel(model)

    def export_data(self):
        query = self.tableView.model().query()


    def export_format(self):
        match(self.exportformat_comboBox.currentText()):
            case 'detritalPy':
                values = [('Samples', 'SampleName'),
                          ('Spots', 'SpotName'),
                          ('UPb Data', 'Uppm'),
                          ('UPb Data', 'U/Th'),
                          ('UPb Data', 'BestAge'),
                          ('UPb Data', 'Error'),
                          ('UPb Data', 'Conc')
                          ]
                self.select_checkboxes(values)
                return
            case 'IsoplotR':
                pass
            case 'DZStats':
                pass
            case 'Database':
                pass
            case 'Custom':
                pass
        self.tableView.setModel(None)


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
                    # todo update placeholder text to include samplename instead of "1" for now

                    # add the sample id to the list
                    id_index = model.index(row, 0, QtCore.QModelIndex())
                    self.checked_sample_list.append(model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))

            self.checked_sample_names = f"({', '.join(map(str, self.checked_sample_list))})"

        elif self.selectionscope_comboBox.currentText() == 'Aliquots':
            self.checked_aliquot_list = []
            for row in range(model.rowCount()):
                name_index = model.index(row, 1, QtCore.QModelIndex())
                if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                    # todo update placeholder text to include samplename instead of "1" for now

                    # add the sample id to the list
                    id_index = model.index(row, 0, QtCore.QModelIndex())
                    self.checked_aliquot_list.append(model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))

            self.checked_aliquot_names = f"({', '.join(map(str, self.checked_aliquot_list))})"

        elif self.selectionscope_comboBox.currentText() == 'Spots':
            self.checked_spot_list = []
            for row in range(model.rowCount()):
                name_index = model.index(row, 1, QtCore.QModelIndex())
                if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                    # todo update placeholder text to include samplename instead of "1" for now

                    # add the sample id to the list
                    id_index = model.index(row, 0, QtCore.QModelIndex())
                    self.checked_spot_list.append(model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))

            self.checked_spot_names = f"({', '.join(map(str, self.checked_spot_list))})"

        self.update_table_view()

    def update_filter_list(self, model):
        self.checked_filter_list = []
        for row in range(model.rowCount()):
            name_index = model.index(row, 1, QtCore.QModelIndex())
            if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                #todo update placeholder text to include filtername instead of "1" for now

                # name = model.data(name_index, QtCore.Qt.ItemDataRole.DisplayRole)
                # self.checked_sample_list.append(name)
                # add the sample id to the list
                id_index = model.index(row, 0, QtCore.QModelIndex())
                filter_json = model.index(row, 2, QtCore.QModelIndex())
                self.checked_filter_list.append((model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole),
                                                 model.data(filter_json, QtCore.Qt.ItemDataRole.DisplayRole)))

        self.update_table_view()


    def open_column_order_dialog(self):
        # Get current selected columns

        if not self.ordered_columns:
            QMessageBox.warning(self, "No Columns Selected", "Please select columns before editing their order.")
            return

        # Open the dialog
        dialog = ColumnOrderDialog(self.ordered_columns, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get adjusted columns
            ordered_columns = dialog.get_adjusted_columns()
            # Update the selected columns
            self.ordered_columns = ordered_columns
            # print(ordered_columns)
            # Update the table view with the new column order
            self.update_table_view()




from PyQt6.QtWidgets import QDialog, QListWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox


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