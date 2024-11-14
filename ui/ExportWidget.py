from PyQt6 import uic, QtSql, QtCore
from PyQt6.QtCore import QSettings, QSize
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel
from PyQt6.QtWidgets import QWidget, QApplication, QGridLayout, QLabel, QCheckBox, QStackedWidget, QSpacerItem, \
    QSizePolicy, QTableView

import SQLUtils
from Table_classes import CheckableSqlTableModel, CheckableComboBox
from QComboBoxLabel import QComboBoxLabel
from Tree_classes import CheckableTreeCombobox


class ExportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_tables = []
        self.selected_columns = []
        for widget in QApplication.topLevelWidgets():
            if widget.inherits("QMainWindow"):
                self.db_file = widget.db_file

        self.db = QSqlDatabase.addDatabase('QSQLITE', 'Exporter')
        self.db.setDatabaseName(self.db_file)
        self.settings = QSettings("CSUF", "GeoChron")

        ok = self.db.open()
        self.checked_sample_list = []
        # self.loadWindowState()
        self.model = QtSql.QSqlQueryModel()

        self.samplesincluded_comboBox: CheckableComboBox()

        uic.loadUi('ui/ExporterUI.ui', self)

        # list of all user-viewable tables in the database
        self.user_view_tables = ['Ages',
                                 'Age Signatures', 'Aliquots', 'Aliquot Contexts', 'Analysis Methods', 'Columns',
                                 'Lab Facilities',
                                 'Instruments',
                                 'Regions', 'Rock Types', 'Sample Contexts', 'Samples', 'Sampling Methods', 'Settings',
                                 'Sources', 'Spots',
                                 'Spot Compositions', 'Spot Contexts', 'UPb Data', 'Units',
                                 'UPb Analysis Methods']

        self.table_fields = {
            'Age Signatures': [
                "AgeSignatureName", "AgeSignatureDescription", "AgeSignatureCreated", "AgeSignatureModified"
            ],
            'Ages': [
                "AgeName", "MaxMa", "MinMa", "AgeCreated", "AgeModified"
            ],
            'Aliquot Contexts': [
                "AliquotContextName", "AliquotContextDescription", "AliquotContextCreated", "AliquotContextModified"
            ],
            'Aliquots': [
                "AliquotName", "AliquotCreated", "AliquotModified"
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
            'Spot Compositions': [
                "SpotCompositionName", "SpotCompositionDescription", "SpotCompositionCreated", "SpotCompositionModified"
            ],
            'Spot Contexts': [
                "SpotContextName", "SpotContextDescription", "SpotContextCreated", "SpotContextModified"
            ],
            'Spots': [
                "SpotName", "SpotCreated", "SpotModified"
            ],
            'UPb Analysis Methods': [
                "UPbAnalysisMethodName", "UPbAnalysisMethodDescription", "UPbAnalysisMethodCreated",
                "UPbAnalysisMethodModified"
            ],
            'UPb Data': [
                "U/Th", "206Pb/204Pb", "206Pb/207Pb", "206Pb/207Pberror", "207Pb/235U", "207Pb/235Uerror",
                "206Pb/238U", "206Pb/238Uerror", "ErrorCorr", "206Pb/207PbAge", "206Pb/207PbAgeError",
                "207Pb/235UAge", "207Pb/235UAgeError", "206Pb/238UAge", "206Pb/238UAgeError",
                "UPbAnalysisCreated", "UPbAnalysisModified"
            ],
            'Units': [
                "UnitName", "UnitDescription", "UnitCreated", "UnitModified"
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

        self.update_step_2_list()
        # self.update_column_attributes()
        self.populate_stack()

        self.viewpreview_pushbutton.clicked.connect(self.update_table_view)
        self.export_pushbutton.clicked.connect(self.export_data)

        self.selectionscope_comboBox.currentIndexChanged.connect(self.update_step_2_list)
        self.columnselection_comboBox.currentIndexChanged.connect(self.switch_table_layout)
        # self.samples_model.dataChanged.connect(self.update_sample_list)
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
        self.columnattributes_stack.setCurrentIndex(selected_table_index+1)
        print(str(selected_table_index) + ": " + self.columnselection_comboBox.currentText())
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

    def view_preview(self):
        # Dictionary to store checked items by table
        checked_attributes = {}

        # Loop through each table in the stack
        for index in range(self.columnattributes_stack.count()):
            table_widget = self.columnattributes_stack.widget(index)
            table_name = self.columnselection_comboBox.itemText(index)
            layout = table_widget.layout()

            # List to store checked fields for the current table
            checked_fields = []

            # Iterate over each item in the layout and gather checked checkboxes
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QCheckBox) and widget.isChecked():
                    field_name = widget.property('field_name')

                    checked_fields.append(field_name)

            # Only add to dictionary if there are checked fields
            if checked_fields:
                checked_attributes[table_name] = checked_fields

        # Output the dictionary for preview (print here, replace with desired output in UI)
        print(checked_attributes)
        # Alternatively, you can set up a signal or display this dictionary in a UI component as needed

    def get_selected_values(self):
        selected_tables = []
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
                        selected_columns.append(field_name)
                        if widget_table_name not in selected_tables:
                            selected_tables.append(widget_table_name)
        return selected_tables, selected_columns

    def update_table_view(self):
        # Get the selected columns
        self.selected_tables, self.selected_columns = self.get_selected_values()
        print(self.selected_tables)
        print(self.selected_columns)
        if not self.selected_columns:
            # No columns selected, clear the table view
            self.tableView.setModel(None)
            return

        # # Get the selected items (IDs)
        # selected_items = self.checked_sample_list
        # if not selected_items:
        #     # No items selected, clear the table view
        #     self.tableView.setModel(None)
        #     return

        join = SQLUtils.get_join_from_table(self.selected_tables)

        # Get the selection scope
        # selection_scope = self.selectionscope_comboBox.currentText()

        # # Determine the filter field
        # filter_field = self.get_filter_field(table_name, selection_scope)
        # if not filter_field:
        #     # Cannot filter this table based on the selection scope
        #     self.tableView.setModel(None)
        #     return

        # Build the SQL query
        columns_str = ', '.join(self.selected_columns)
        # placeholders = ', '.join(['?'] * len(selected_items))
        query_str = f"SELECT {columns_str} FROM Samples {join} WHERE FALSE"
        print(query_str)

        # for item in selected_items:
        #     query.addBindValue(item)

        # Set the model

        self.model.setQuery(query_str)

        for col in range(self.model.columnCount()):
            header = self.model.headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
            self.model.setHeaderData(col, QtCore.Qt.Orientation.Horizontal, header, QtCore.Qt.ItemDataRole.DisplayRole)

        row_count = self.model.rowCount()
        column_count = self.model.columnCount()
        print(f"Model row count: {row_count}, column count: {column_count}")
        self.tableView.setModel(self.model)


    def export_data(self):
        pass



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

    def set_table(self, model: QtSql.QSqlTableModel, table: str):
        model.setTable(table)
        model.select()
        return model

    def update_sample_list(self, model):
        self.checked_sample_list = []
        for row in range(model.rowCount()):
            name_index = model.index(row, 1, QtCore.QModelIndex())
            if model.data(name_index, QtCore.Qt.ItemDataRole.CheckStateRole) == QtCore.Qt.CheckState.Checked:
                name = model.data(name_index, QtCore.Qt.ItemDataRole.DisplayRole)
                self.checked_sample_list.append(name)
                # add the sample id to the list
                id_index = model.index(row, 0, QtCore.QModelIndex())
                self.checked_sample_list.append(model.data(id_index, QtCore.Qt.ItemDataRole.DisplayRole))
        print(self.checked_sample_list)
        # self.checked_sample_names = ", ".join(checked_sample_names)
        # self.populate_fields()