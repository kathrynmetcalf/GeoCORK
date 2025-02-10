import sys
import time

# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS

from PyQt6.uic import loadUi

import logger_setup

import Functions.Database_views as DB_views
import Functions.SQLUtils as SQLUtils

from Functions.Widget_classes import (
    CheckableSqlTableModel, SampleAgeTableModel, set_table, FontDelegate, SQLiteTableModel, CheckableSqlQueryModel,
    CheckableSqlTableModel, name_column, get_view_name_column, TreeModel, CheckableTreeCombobox, CheckableTreeModel,
    CheckableTreeView, save_expanded_state, show_column, set_comboBox_text, find_upb_from_samples, delete_samples
)
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
from ui.GPSFields import GPSFields
from ui.AgeFields import AgeFields
# from ui.EditTable import EditTable
# from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.New_reference import NewReference
# from ui.AddTreeTags import AddTreeTags


class SampleInformation(QtW.QDialog):
    def __init__(self, parent_window, sample_id_list: list | None):
        super().__init__(parent=parent_window)
        logger_setup.get_logger().info("Starting the sample information dialog")
        start_init_time = time.time()
        self.parent_window = parent_window
        self.savepoint_manager = SavepointManager.get_instance()
        # self.loadWindowState()

        sources_ui_file = "ui/SampleInformation.ui"
        loadUi(sources_ui_file, self)
        self.selected_sample_label: QtW.QLabel
        self.selected_sample_label.setWordWrap(True)
        self.gps = GPSFields('Samples', sample_id_list)
        self.selected_gps_column_verticalLayout: QtW.QVBoxLayout
        self.selected_gps_column_verticalLayout.insertWidget(2, self.gps)
        self.age = AgeFields('Samples', sample_id_list)
        self.name_igsn_age_verticalLayout = QtW.QVBoxLayout()
        self.gridLayout_2.addWidget(self.age, 2, 0, 2, 4)

        # Sample names table
        self.sample_names_model = CheckableSqlTableModel()  # The one used to populate the dropdown checkbox of samples to edit, shows only name and description
        self.sample_names_model = set_table(self.sample_names_model, 'Samples')
        if sample_id_list is None or len(sample_id_list) == 0:
            self.selected_sample_list = []
        else:
            self.selected_sample_list = sample_id_list
            if len(self.selected_sample_list) > 1:
                self.sample_names_model.setFilter(f"SampleID in {tuple(self.selected_sample_list)}")
            else:
                self.sample_names_model.setFilter(f"SampleID = {self.selected_sample_list[0]}")
        self.checked_sample_list = []
        self.checked_sample_names = ""
        self.default_age_ids = []
        self.upb_analysis_ids = None

        self.updated = False
        # self.init_progress_dialog = QtW.QProgressDialog(
        #     f"Loading information for {len(sample_id_list)} samples...", "Cancel", 0, 6, self
        # )
        # self.load_progress_dialog = QtW.QProgressDialog()
        # self.update_progress_dialog = QtW.QProgressDialog()

        # Sample information models
        self.samples_table = None
        self.distance_unit_model = QtS.QSqlTableModel()
        self.elevation_unit_model = QtS.QSqlTableModel()
        self.column_model = QtS.QSqlTableModel()
        self.column_unit_model = QtS.QSqlTableModel()
        self.sample_context_model = QtS.QSqlTableModel()
        self.sample_context_tree = CheckableTreeModel()
        self.sampling_method_model = QtS.QSqlTableModel()
        self.sampling_method_tree = CheckableTreeModel()
        self.unit_model = QtS.QSqlTableModel()
        self.unit_tree = CheckableTreeModel()
        self.rock_type_model = QtS.QSqlTableModel()
        self.rock_type_tree = CheckableTreeModel()
        self.region_model = QtS.QSqlTableModel()
        self.region_tree = CheckableTreeModel()
        self.setting_model = QtS.QSqlTableModel()
        self.setting_tree = CheckableTreeModel()
        self.age_signature_model = QtS.QSqlTableModel()
        self.age_signature_tree = CheckableTreeModel()
        self.analysis_method_model = QtS.QSqlTableModel()
        self.analysis_method_tree = CheckableTreeModel()
        self.instrument_model = CheckableSqlTableModel()
        self.lab_facility_model = CheckableSqlTableModel()
        self.rejection_reason_model = QtS.QSqlTableModel()
        self.reference_model = CheckableSqlQueryModel()
        self.upb_analysis_method_model = QtS.QSqlTableModel()
        self.concordance_type_model = QtS.QSqlTableModel()

        self.gps_location_ids = ""

        self.msg = QtW.QMessageBox(self)
        create_savepoint('before_edit')
        self.close_by_dialog = False
        # self.increment_progress_dialog(self.init_progress_dialog)

        # Fill in information based on selected samples
        self.populate_dropdowns()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.check_all_samples()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.sample_name_comboBox.setModel(self.sample_names_model)
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)

        self.installEventFilter(self)
        end_init_time = time.time()
        logger_setup.get_logger().info(f"Sample information dialog initialized in {end_init_time - start_init_time} seconds")

    def check_all_samples(self):
        logger_setup.get_logger().info("Checking all samples")
        if len(self.selected_sample_list) > 0:
            for row in range(self.sample_names_model.rowCount()):
                index = self.sample_names_model.index(row, 1, QtC.QModelIndex())
                self.sample_names_model.setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            self.update_sample_list()
        else:
            self.uncheck_all_samples()

    def uncheck_all_samples(self):
        logger_setup.get_logger().info("Unchecking all samples")
        for row in range(self.sample_names_model.rowCount()):
            index = self.sample_names_model.index(row, 1, QtC.QModelIndex())
            self.sample_names_model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        self.update_sample_list()

    def update_sample_list(self):
        logger_setup.get_logger().info("Updating the sample list")
        start_update_sample_list_time = time.time()
        self.checked_sample_list = []
        checked_sample_names = []
        self.checked_sample_names = ""
        for row in range(self.sample_names_model.rowCount()):
            name_index = self.sample_names_model.index(row, 1, QtC.QModelIndex())
            if self.sample_names_model.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                name = self.sample_names_model.data(name_index, QtC.Qt.ItemDataRole.DisplayRole)
                checked_sample_names.append(name)
                # add the sample id to the list
                id_index = self.sample_names_model.index(row, 0, QtC.QModelIndex())
                self.checked_sample_list.append(self.sample_names_model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole))
        if len(checked_sample_names) > 1:
            self.checked_sample_names = ", ".join(checked_sample_names)
        elif len(checked_sample_names) == 1:
            self.checked_sample_names = checked_sample_names[0]
        self.selected_sample_label.setText(f"Selected Samples: {self.checked_sample_names}")
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)
        logger_setup.get_logger().info(f"Updated sample list: {self.checked_sample_names}")
        self.upb_analysis_ids = find_upb_from_samples(self.checked_sample_list)
        end_update_sample_list_time = time.time()
        logger_setup.get_logger().info(f"Updated sample list: {self.checked_sample_names} in {end_update_sample_list_time - start_update_sample_list_time} seconds")
        if self.checked_sample_list == 0:
            QtW.QMessageBox.warning(self, "No Samples Selected", "There are no samples to show information for")
            return

        self.disconnect_text_signals()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.populate_fields()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.connect_signals()
        # self.increment_progress_dialog(self.init_progress_dialog)

    def increment_progress_dialog(self, progress_dialog: QtW.QProgressDialog):
        step = progress_dialog.value()
        progress_dialog.setValue(step + 1)
        # Let the event loop process the dialog's updates
        QtW.QApplication.processEvents()
        # If the user clicked "Cancel", we can break out
        if progress_dialog.wasCanceled():
            rollback_savepoint('before_edit')
            self.close_by_dialog = True
            self.close()

    def populate_dropdowns(self):
        start_populate_dropdown_time = time.time()
        logger_setup.get_logger().info("Populating dropdowns")
        self.column_model = set_table(self.column_model, 'Columns')
        self.column_unit_model = set_table(self.column_unit_model, 'DistanceUnits')
        self.sample_context_model = set_table(self.sample_context_model, 'SampleContexts')
        self.sample_context_tree.setSourceModel(self.sample_context_model)
        self.sampling_method_model = set_table(self.sampling_method_model, 'SamplingMethods')
        self.sampling_method_tree.setSourceModel(self.sampling_method_model)
        self.unit_model = set_table(self.unit_model, 'Units')
        self.unit_tree.setSourceModel(self.unit_model)
        self.rock_type_model = set_table(self.rock_type_model, 'RockTypes')
        self.rock_type_tree.setSourceModel(self.rock_type_model)
        self.region_model = set_table(self.region_model, 'Regions')
        self.region_tree.setSourceModel(self.region_model)
        self.setting_model = set_table(self.setting_model, 'Settings')
        self.setting_tree.setSourceModel(self.setting_model)
        self.age_signature_model = set_table(self.age_signature_model, 'AgeSignatures')
        self.age_signature_tree.setSourceModel(self.age_signature_model)
        self.reference_model.setQuery(f'SELECT * FROM ReferenceView')
        if self.reference_model.lastError().text():
            logger_setup.get_logger().critical(f"Error setting reference model query: {self.reference_model.lastError().text()}")
        self.analysis_method_model = set_table(self.analysis_method_model, 'UPbAnalysisMethods')
        self.analysis_method_tree.setSourceModel(self.analysis_method_model)
        self.lab_facility_model = set_table(self.lab_facility_model, 'LabFacilities')
        self.instrument_model = set_table(self.instrument_model, 'Instruments')

        self.column_name_comboBox.model_modifiable = True
        self.column_name_comboBox.setModel(self.column_model)
        show_column(self.column_name_comboBox, 'ColumnName')
        self.height_depth_unit_comboBox.setModel(self.column_unit_model)
        show_column(self.height_depth_unit_comboBox, 'DistanceUnitAbbreviation')
        self.sample_context_comboBox.setModel(self.sample_context_tree)
        self.sampling_method_comboBox.setModel(self.sampling_method_tree)
        self.unit_comboBox.setModel(self.unit_tree)
        self.rock_type_comboBox.setModel(self.rock_type_tree)
        self.region_comboBox.setModel(self.region_tree)
        self.setting_comboBox.setModel(self.setting_tree)
        self.age_signature_comboBox.setModel(self.age_signature_tree)
        self.reference_comboBox.model_modifiable = True
        self.reference_comboBox.setModel(self.reference_model)
        show_column(self.reference_comboBox, 'ReferenceDisplay')
        self.analysis_method_comboBox.model_modifiable = True
        self.analysis_method_comboBox.setModel(self.analysis_method_tree)
        self.lab_facility_comboBox.model_modifiable = True
        self.lab_facility_comboBox.setModel(self.lab_facility_model)
        self.instrument_comboBox.model_modifiable = True
        self.instrument_comboBox.setModel(self.instrument_model)

        self.sample_name_comboBox: CheckableTreeCombobox
        self.sample_name_comboBox.view().setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.sample_name_comboBox.view().customContextMenuRequested.connect(self.show_context_menu)
        end_populate_dropdown_time = time.time()
        logger_setup.get_logger().info(f"Populated dropdowns in {end_populate_dropdown_time - start_populate_dropdown_time} seconds")
        logger_setup.get_logger().info("Dropdowns populated")

    def connect_signals(self):
        logger_setup.get_logger().info("Connecting signals")
        # Connect signals and slots
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.sample_name_comboBox.closing.connect(self.update_sample_list)
        self.sample_igsn_lineEdit.editingFinished.connect(lambda: self.update_field('SampleIGSN', f'"{self.sample_igsn_lineEdit.text()}"'))
        self.column_name_comboBox.currentTextChanged.connect(lambda: self.update_id('SampleColumnID', 'ColumnName', self.column_name_comboBox.currentText(), 'Columns'))
        # self.column_name_comboBox.add_triggered.connect(self.add_popup)
        # self.column_name_comboBox.edit_triggered.connect(self.edit_popup)
        self.height_depth_lineEdit.editingFinished.connect(
            lambda: self.update_field('HeightDepth', self.height_depth_lineEdit.text()))
        self.height_depth_error_lineEdit.editingFinished.connect(
            lambda: self.update_field('HeightDepthError', self.height_depth_error_lineEdit.text()))
        self.height_depth_unit_comboBox.currentTextChanged.connect(lambda: self.update_id('HeightDepthUnitID', 'DistanceUnitAbbreviation', self.height_depth_unit_comboBox.currentText(), 'DistanceUnits'))
        self.sample_context_comboBox.closing.connect(lambda: self.update_sample_tags(self.sample_context_tree, 'SampleContexts'))
        self.sampling_method_comboBox.closing.connect(lambda: self.update_sample_tags(self.sampling_method_tree, 'SamplingMethods'))
        self.unit_comboBox.closing.connect(lambda: self.update_sample_tags(self.unit_tree, 'Units'))
        self.rock_type_comboBox.closing.connect(lambda: self.update_sample_tags(self.rock_type_tree, 'RockTypes'))
        self.region_comboBox.closing.connect(lambda: self.update_sample_tags(self.region_tree, 'Regions'))
        self.setting_comboBox.closing.connect(lambda: self.update_sample_tags(self.setting_tree, 'Settings'))
        self.age_signature_comboBox.closing.connect(lambda: self.update_sample_tags(self.age_signature_tree, 'AgeSignatures'))
        self.reference_comboBox.closing.connect(lambda: self.update_subfield_id(self.reference_model, 'ReferenceID'))
        self.reference_comboBox.add_triggered.connect(self.add_popup)
        # self.reference_comboBox.edit_triggered.connect(self.edit_popup)
        # self.analysis_method_comboBox.closing.connect(lambda: self.update_subfield_id(self.analysis_method_model, 'UPbAnalysisMethodID'))
        self.lab_facility_comboBox.closing.connect(lambda: self.update_subfield_id(self.lab_facility_model, 'LabFacilityID'))
        self.lab_facility_comboBox.add_triggered.connect(self.add_popup)
        # self.lab_facility_comboBox.edit_triggered.connect(self.edit_popup)
        self.instrument_comboBox.closing.connect(lambda: self.update_subfield_id(self.instrument_model, 'InstrumentID'))
        self.instrument_comboBox.add_triggered.connect(self.add_popup)
        # self.instrument_comboBox.edit_triggered.connect(self.edit_popup)
        self.sample_description_lineEdit.editingFinished.connect(lambda: self.update_field('SampleDescription', f'"{self.sample_description_lineEdit.text()}"'))
        logger_setup.get_logger().info("Signals connected")

    def disconnect_text_signals(self):
        logger_setup.get_logger().info("Disconnecting text signals")
        try:
            self.column_name_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.height_depth_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.height_depth_error_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.height_depth_unit_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.sample_description_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        logger_setup.get_logger().info("Text signals disconnected")

    def populate_fields(self):
        logger_setup.get_logger().info("Populating fields")
        start_populate_fields_time = time.time()
        sample_ifnull_query = DB_views.SampleIfNullQuery()
        if len(self.checked_sample_list) > 1:
            self.samples_table = SQLiteTableModel(f'{sample_ifnull_query} WHERE Samples.SampleID in {tuple(self.checked_sample_list)}')
        elif len(self.checked_sample_list) == 1:
            self.samples_table = SQLiteTableModel(f'{sample_ifnull_query} WHERE Samples.SampleID = {self.checked_sample_list[0]}')
        else:
            self.samples_table = SQLiteTableModel(f'{sample_ifnull_query}')
        if self.samples_table.rowCount() == 0:
            if len(self.checked_sample_names) > 5:
                logger_setup.get_logger().critical(f'Unable to retrieve sample information for {len(self.checked_sample_names)} samples: {", ".join(self.checked_sample_names[0:5])}...')
            else:
                logger_setup.get_logger().critical(f'Unable to retrieve sample information for {", ".join(self.checked_sample_names)}')
            return
        text_values = []
        headers = []
        for col in range(self.samples_table.columnCount()):
            # If there is only one value concatenated in the column, add it to the list, otherwise add '-'
            text = self.samples_table._data[0][col]
            header = self.samples_table._headers[col]
            header = header.split('ifnull(')[1].split(',"Null')[0]
            headers.append(header)
            if ',' in text:
                if 'Description' in header:
                    text_values.append(text)
                else:
                    text_values.append('-')
            elif text == 'Null':
                text_values.append('')
            else:
                text_values.append(text)
        if len(text_values) > 0:
            for header in headers:
                if 'SampleName' in header:
                    self.sample_name_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'IGSN' in header:
                    self.sample_igsn_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'ColumnName' in header:
                    set_comboBox_text(self.column_name_comboBox, text_values[headers.index(header)])
                elif 'HeightDepthError' in header:
                    self.height_depth_error_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'HeightDepth' in header:
                    self.height_depth_lineEdit.setText(f"{text_values[headers.index(header)]}")
                elif 'HeightDepthUnit' in header:
                    set_comboBox_text(self.height_depth_unit_comboBox, text_values[headers.index(header)])
                elif 'SampleDescription' in header:
                    self.sample_description_lineEdit.setText(f"{text_values[headers.index(header)]}")

            # Sample tags
            text = self.populate_checks('Samples_SampleContexts', self.sample_context_model, self.sample_context_tree)
            self.sample_context_comboBox.setCurrentText(text)
            text = self.populate_checks('Samples_SamplingMethods', self.sampling_method_model, self.sampling_method_tree)
            self.sampling_method_comboBox.setCurrentText(text)
            text = self.populate_checks('Samples_Units', self.unit_model, self.unit_tree)
            self.unit_comboBox.setCurrentText(text)
            text = self.populate_checks('Samples_RockTypes', self.rock_type_model, self.rock_type_tree)
            self.rock_type_comboBox.setCurrentText(text)
            text = self.populate_checks('Samples_Regions', self.region_model, self.region_tree)
            self.region_comboBox.setCurrentText(text)
            text = self.populate_checks('Samples_Settings', self.setting_model, self.setting_tree)
            self.setting_comboBox.setCurrentText(text)
            text = self.populate_checks('Samples_AgeSignatures', self.age_signature_model, self.age_signature_tree)
            self.age_signature_comboBox.setCurrentText(text)
            text = self.populate_upb_checks(self.reference_model)
            self.reference_comboBox.set_single_click(True)
            self.reference_comboBox.setCurrentText(text)
            text = self.populate_upb_checks(self.analysis_method_model)
            self.analysis_method_comboBox.set_single_click(True)
            self.analysis_method_comboBox.setCurrentText(text)
            text = self.populate_upb_checks(self.lab_facility_model)
            self.lab_facility_comboBox.set_single_click(True)
            self.lab_facility_comboBox.setCurrentText(text)
            text = self.populate_upb_checks(self.instrument_model)
            self.instrument_comboBox.set_single_click(True)
            self.instrument_comboBox.setCurrentText(text)

            self.gps.update_list(self.checked_sample_list)
            self.age.update_list(self.checked_sample_list)
        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(f"Populated fields in {end_populate_fields_time - start_populate_fields_time} seconds")
        logger_setup.get_logger().info("Fields populated")

    def populate_checks(self, many_to_many_table: str, table_model: QtS.QSqlTableModel, tree: CheckableTreeModel = None):
        logger_setup.get_logger().info(f"Populating checks for {many_to_many_table}")
        start_populate_checks_time = time.time()
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        tag_id_header = table_model.record().fieldName(0)
        items = []
        text = ""
        if len(self.checked_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected, so unchecking everything")
            for row in range(table_model.rowCount()):
                if tree is not None:
                    model = tree
                    col = name_column(table_model.tableName())
                    model_index = tree.mapFromSource(table_model.index(row, col))
                else:
                    model = table_model
                    col = name_column(table_model.tableName())
                    model_index = table_model.index(row, col)
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                if model.lastError().text():
                    logger_setup.get_logger().critical(f"Error setting unchecked for {model.tableName()}: {model.lastError().text()}")
            logger_setup.get_logger().info("Unchecked everything")
            return text
        for row in range(table_model.rowCount()):
            tag_id = table_model.index(row, 0).data()
            if len(self.checked_sample_list) > 1:
                many_to_many_model.setFilter(f"SampleID in {tuple(self.checked_sample_list)} AND {tag_id_header} = {tag_id}")
            else:
                many_to_many_model.setFilter(f"SampleID = {self.checked_sample_list[0]} AND {tag_id_header} = {tag_id}")
            if tree is not None:
                model = tree
                col = name_column(table_model.tableName())
                model_index = tree.mapFromSource(table_model.index(row, col))
                error_text = model.source_model.lastError().text()
            else:
                model = table_model
                col = name_column(table_model.tableName())
                model_index = table_model.index(row, col)
                error_text = model.lastError().text()
            if many_to_many_model.rowCount() == len(self.selected_sample_list):
                # All samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                if error_text:
                    logger_setup.get_logger().critical(f"Error setting checked for {model.tableName()}: {error_text}")
                items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
            elif many_to_many_model.rowCount() > 0:
                # Some samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                if error_text:
                    logger_setup.get_logger().critical(f"Error setting partial checked for {model.tableName()}: {error_text}")
                items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                # No samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                if error_text:
                    logger_setup.get_logger().critical(f"Error setting unchecked for {model.tableName()}: {error_text}")
        text = ", ".join(items)
        end_populate_checks_time = time.time()
        logger_setup.get_logger().info(f"Populated checks for {many_to_many_table} in {end_populate_checks_time - start_populate_checks_time} seconds")
        logger_setup.get_logger().info(f"Populated checks for {many_to_many_table}")
        return text

    def populate_upb_checks(self, table_model):
        logger_setup.get_logger().info(f"Populating UPb checks for {table_model.tableName()}")
        start_populate_upb_checks_time = time.time()
        items = []
        text = ""
        table = table_model.tableName()
        try:
            view = table_model.tableView()
            col = get_view_name_column(view)
        except AttributeError:
            col = name_column(table)
        tag_id_header = table_model.record().fieldName(0)
        if len(self.checked_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected, so unchecking everything")
            for row in range(table_model.rowCount()):
                index = table_model.index(row, col)
                table_model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                if table_model.lastError().text():
                    logger_setup.get_logger().critical(f"Error setting unchecked for {table_model.tableName()}: {table_model.lastError().text()}")
            logger_setup.get_logger().info("Unchecked everything")
            return text
        if len(self.upb_analysis_ids) > 0:
            for row in range(table_model.rowCount()):
                tag_id = table_model.index(row, 0).data()
                upb_analysis_table = SQLiteTableModel(f"SELECT * FROM UPbAnalyses WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)} AND {tag_id_header} = {tag_id}")
                index = table_model.index(row, col)
                if upb_analysis_table.rowCount() == len(self.upb_analysis_ids):
                    # All analyses have this tag
                    table_model.setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if table_model.lastError().text():
                        logger_setup.get_logger().critical(f"Error setting checked for {table_model.tableName()}: {table_model.lastError().text()}")
                    items.append(table_model.data(index, QtC.Qt.ItemDataRole.DisplayRole))
                elif upb_analysis_table.rowCount() > 0:
                    # Some samples have this tag
                    table_model.setData(index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if table_model.lastError().text():
                        logger_setup.get_logger().critical(f"Error setting partial checked for {table_model.tableName()}: {table_model.lastError().text()}")
                    items.append(table_model.data(index, QtC.Qt.ItemDataRole.DisplayRole))
                else:
                    # No samples have this tag
                    table_model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if table_model.lastError().text():
                        logger_setup.get_logger().critical(f"Error setting unchecked for {table_model.tableName()}: {table_model.lastError().text()}")
            if items:
                text = ", ".join(map(str, items))
        end_populate_upb_checks_time = time.time()
        logger_setup.get_logger().info(f"Populated UPb checks for {table_model.tableName()} in {end_populate_upb_checks_time - start_populate_upb_checks_time} seconds")
        logger_setup.get_logger().info(f"Populated UPb checks for {table_model.tableName()}")
        return text

    def show_context_menu(self, pos: QtC.QPoint):
        logger_setup.get_logger().info("Showing context menu")
        menu = QtW.QMenu()
        selected_indexes = self.sample_name_comboBox.view().selectedIndexes()
        select_action = menu.addAction("Select all")
        unselect_action = menu.addAction("Unselect all")
        delete_action = menu.addAction("Delete selected")
        action = menu.exec(self.sample_name_comboBox.view().mapToGlobal(pos))
        if action == select_action:
            self.check_all_samples()
        elif action == unselect_action:
            self.uncheck_all_samples()
        elif action == delete_action:
            if self.delete_question():
                delete_samples(selected_indexes)

    def update_field(self, field: str, text: str):
        logger_setup.get_logger().info(f"Update field called with {field} and {text}")
        start_update_field_time = time.time()
        if text != "-":
            if len(self.checked_sample_list) > 0:
                logger_setup.get_logger().info(f"Updating {field} to {text} for {len(self.checked_sample_list)} samples")
                query = QtS.QSqlQuery()
                create_savepoint('before_update')
                for sample_id in self.checked_sample_list:
                    if not query.exec(f"SELECT {field} FROM Samples WHERE SampleID = {sample_id}"):
                        logger_setup.get_logger().critical(f"Failed to select {field} for SampleID {sample_id}: {query.lastError().text()}")
                        return
                    query.next()
                    if query.value(0) != text:
                        logger_setup.get_logger().info(f"Updating {field} to {text} for SampleID {sample_id}")
                        if text is None or text == '':
                            text = 'Null'
                        if not query.exec(f"UPDATE Samples SET {field} = {text} WHERE SampleID = {sample_id}"):
                            logger_setup.get_logger().critical(f"Failed to update {field} to {text} for SampleID {sample_id}: {query.lastError().text()}")
                            rollback_savepoint('before_update')
                            return
                        update_modified_timestamp('Samples', [sample_id])
                self.updated = True
                end_update_field_time = time.time()
                logger_setup.get_logger().info(
                    f"Updated field in {end_update_field_time - start_update_field_time} seconds")
                logger_setup.get_logger().info(f"Updated {field} to {text} for {len(self.checked_sample_list)} samples")
                release_savepoint('before_update')
            else:
                logger_setup.get_logger().info("No samples selected")


    def update_id(self, id_field: str, name_field:str, text: str, table: str):
        logger_setup.get_logger().info(f'update_id called with {id_field}, {name_field}, {text}, {table}')
        start_update_id_time = time.time()
        table_model = QtS.QSqlTableModel()
        table_model.setTable(table)
        table_model.select()
        # table_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        table_model.setFilter(f"{name_field} is '{text}'")
        item_id = table_model.data(table_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if len(self.checked_sample_list) > 0:
            logger_setup.get_logger().info(f"Updating {id_field} to {item_id} for {len(self.checked_sample_list)} samples")
            query = QtS.QSqlQuery()
            create_savepoint('before_update')
            for sample_id in self.checked_sample_list:
                if not query.exec(f"SELECT {id_field} FROM Samples WHERE SampleID = {sample_id}"):
                    logger_setup.get_logger().critical(f"Failed to select {id_field} for SampleID {sample_id}: {query.lastError().text()}")
                    return
                query.next()
                if query.value(0) != item_id:
                    if not query.exec(f"UPDATE Samples SET {id_field} = {item_id} WHERE SampleID = {sample_id}"):
                        logger_setup.get_logger().critical(f"Failed to update {id_field} to {item_id} for SampleID {sample_id}: {query.lastError().text()}")
                        rollback_savepoint('before_update')
                        return
            update_modified_timestamp('Samples', self.checked_sample_list)
            self.updated = True
            end_update_id_time = time.time()
            logger_setup.get_logger().info(f"Updated {id_field} to {item_id} for {len(self.checked_sample_list)} samples in {end_update_id_time - start_update_id_time} seconds")
            logger_setup.get_logger().info(f"Updated {id_field} to {item_id} for {len(self.checked_sample_list)} samples")
            release_savepoint('before_update')
        else:
            logger_setup.get_logger().info("No samples selected")


    def update_subfield_id(self, model: CheckableSqlTableModel | CheckableSqlQueryModel, field: str):
        logger_setup.get_logger().info(f"update_subfield_id called with {model.tableName()} and {field}")
        start_update_subfield_id_time = time.time()
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If nothing is fully checked, then nothing should be updated
        checked_item_id = None  # Should only be one
        if len(self.upb_analysis_ids) > 0:
            try:
                view = model.tableView()
                column = get_view_name_column(view)
            except AttributeError:
                column = name_column(model.tableName())
            for row in range(model.rowCount()):
                name_index = model.index(row, column)
                id_index = model.index(row, 0)
                if model.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                    checked_item_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
                    break
            logger_setup.get_logger().info(f"Updating {field} to {checked_item_id} for {len(self.upb_analysis_ids)} UPb Analyses")
            create_savepoint('before_update')
            query_start_time = time.time()
            query = QtS.QSqlQuery()
            query.setForwardOnly(True)
            if checked_item_id is None:
                checked_item_id = 'Null'
            if len(self.upb_analysis_ids) > 1:
                self.upb_analysis_ids.sort()
                if not query.exec(f"UPDATE UPbAnalyses SET {field} = {checked_item_id} WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)}"):
                    logger_setup.get_logger().critical(f"Failed to update {field} to {checked_item_id} for {len(self.upb_analysis_ids)} UPb Analyses: {query.lastError().text()}")
                update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            else:
                if not query.exec(f"UPDATE UPbAnalyses SET {field} = {checked_item_id} WHERE UPbAnalysisID = {self.upb_analysis_ids[0]}"):
                    logger_setup.get_logger().critical(f"Failed to update {field} to {checked_item_id} for UPbAnalysisID {self.upb_analysis_ids[0]}: {query.lastError().text()}")
                update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids[0])
            query_end_time = time.time()
            logger_setup.get_logger().info(f"Query time: {query_end_time - query_start_time}")
            self.updated = True
            end_update_subfield_id = time.time()
            logger_setup.get_logger().info(f"Updated {field} to {checked_item_id} for {len(self.upb_analysis_ids)} UPb Analyses in {end_update_subfield_id - start_update_subfield_id_time} seconds")
            logger_setup.get_logger().info(f"Updated {field} to {checked_item_id} for {len(self.upb_analysis_ids)} UPb Analyses")
            release_savepoint('before_update')
        else:
            logger_setup.get_logger().info("No UPbAnalyses for selected samples")

    def update_sample_tags(self, model: CheckableTreeModel, table: str):
        logger_setup.get_logger().info(f"update_tags called with {model.table} and {table}")
        start_update_sample_tags = time.time()
        many_to_many_model = QtS.QSqlTableModel()
        set_table(many_to_many_model, f"Samples_{table}")

        if len(self.checked_sample_list) > 0:
            checked_ids , partially_checked_ids, checked_indices, partially_checked_indices = model.traverse_checkable_tree(QtC.QModelIndex())
            logger_setup.get_logger().info(f"Updating {table} for {len(self.checked_sample_list)} samples")
            create_savepoint('before_update')
            for sample_id in self.checked_sample_list:
                update = model.update_db(checked_ids, partially_checked_ids, sample_id)
                if update is False:
                    logger_setup.get_logger().critical(f"Failed to update {table} for SampleID {sample_id}")
                    rollback_savepoint('before_update')
                    return
            self.updated = True
            end_update_sample_tags_time = time.time()
            logger_setup.get_logger().info(f"Updated {table} for {len(self.checked_sample_list)} samples in {end_update_sample_tags_time - start_update_sample_tags} seconds")
            logger_setup.get_logger().info(f"Updated {table} for {len(self.checked_sample_list)} samples")
            release_savepoint('before_update')
        else:
            logger_setup.get_logger().info("No samples selected")

    def update_sub_tags(self, model: CheckableTreeModel, table: str):
        logger_setup.get_logger().info(f"update_tags called with {model.source_model.tableName()} and {table}")
        start_update_sub_tags_time = time.time()
        field = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If there are still partial checks, then nothing should be updated
        checked_ids, partially_checked_ids = model.traverse_checkable_tree(QtC.QModelIndex())
        if len(partially_checked_ids) > 0:
            logger_setup.get_logger().info(f"No changes made to {table}")
        elif len(checked_ids) > 1:
            logger_setup.get_logger().critical(f"More than one checked value for {field}")
        elif len(checked_ids) == 1:
            # Should only be one checked value
            logger_setup.get_logger().info(f"Updating {field} to {checked_ids[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
            create_savepoint('before_update')
            query = QtS.QSqlQuery()
            if len(self.upb_analysis_ids) > 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = {checked_ids[0]} WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)}")
            if len(self.upb_analysis_ids) == 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = {checked_ids[0]} WHERE UPbAnalysisID = {self.upb_analysis_ids[0]}")
            if not query.exec():
                logger_setup.get_logger().critical(f"Failed to update {field} to {checked_ids[0]} for UPbAnalysisID {self.upb_analysis_ids}: {query.lastError().text()}")
                rollback_savepoint('before_update')
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(f"Updated {field} to {checked_ids[0]} for UPbAnalysisID {self.upb_analysis_ids} in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            logger_setup.get_logger().info(f"Updated {field} to {checked_ids[0]} for UPbAnalysisID {self.upb_analysis_ids}")
            release_savepoint('before_update')
        elif len(checked_ids) == 0 and len(partially_checked_ids) == 0:
            logger_setup.get_logger().info(f"Updating all {table} to unchecked")
            create_savepoint('before_update')
            query = QtS.QSqlQuery()
            if len(self.upb_analysis_ids) > 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = Null WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)}")
            if len(self.upb_analysis_ids) == 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = Null WHERE UPbAnalysisID = {self.upb_analysis_ids[0]}")
            if not query.exec():
                logger_setup.get_logger().critical(f"Failed to update {field} to Null for UPbAnalysisID {self.upb_analysis_ids}: {query.lastError().text()}")
                rollback_savepoint('before_update')
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(
                f"Updated {field} to Null for UPbAnalysisID {self.upb_analysis_ids} in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            logger_setup.get_logger().info(f"Updated {field} to Null for UPbAnalysisID {self.upb_analysis_ids}")
            release_savepoint('before_update')

    def add_popup(self, action: QtG.QAction | None = None):
        combo = self.sender()
        table = combo.model().tableName()
        if table in SQLUtils.user_viewable_trees:
            model = combo.model()
            # view = combo.view()
            # save_expanded_state(table, model, view)
            # dlg = AddTreeTags(table, action, view)
        elif table == '"References"' or table == 'References':
            dlg = NewReference()
        else:
            dlg = AddTags(table)
        if dlg is None:
            return
        dlg.exec()

        # Update the model
        if isinstance(combo.model(), QtS.QSqlTableModel):
            combo.model().select()
        # elif isinstance(model, CheckableTreeModel):
        #     model.source_model.select()
        #     model.setSourceModel(model.source_model)

    def delete_question(self):
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to delete these items and all associated data?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def discard_question(self):
        if self.updated or self.gps.updated or self.age.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to discard all changes?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                logger_setup.get_logger().info("Discarding changes")
                rollback_savepoint('before_edit')
                self.reject()
                self.close_by_dialog = True
                self.close()
                self.close_by_dialog = False
            else:
                pass
        else:
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def commit_question(self):
        if self.updated or self.gps.updated or self.age.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to commit all changes to the database?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                self.commit()
            else:
                pass
        else:
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def commit(self):
        release_savepoint('before_edit')
        # Edit occurred in the dialog, so update the database
        update_database()
        # save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView, self.settings)
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.updated or self.gps.updated or self.age.updated:
                self.discard_question()
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
