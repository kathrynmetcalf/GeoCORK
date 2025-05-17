import os
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
    CheckableSqlTableModel, get_name_column, get_view_name_column, TreeModel, CheckableTreeCombobox, CheckableTreeModel,
    CheckableTreeView, save_expanded_state, show_column, set_comboBox_text, find_upb_from_samples, delete_data,
    find_tree_model, CheckableComboBox, get_selected_tree_ids, get_headers, add_tree_popup, restore_expanded_state,
    DisplayRoundedQueryModel, populate_combo_box, populate_many_combo_checks
)
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import settings
from Functions.Database_manager import update_database
from Functions.LoadingDialog_manager import LoadingDialogManager
from ui.GPSFields import GPSFields
from ui.AgeFields import AgeFields
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.AddTags import AddTags
from ui.AddTreeTags import AddTreeTags
from ui.New_reference import NewReference
from ui.EditUPbTags import EditUPbTags


class SampleInformation(QtW.QDialog):
    def __init__(self, parent_window, sample_id_list: list | None):
        super().__init__(parent=parent_window)
        logger_setup.get_logger().info("Starting the sample information dialog")
        self.loading_manager = LoadingDialogManager.get_instance()
        start_init_time = time.time()
        self.parent_window = parent_window
        self.savepoint_manager = SavepointManager.get_instance()
        self.setWindowTitle("Edit Sample Information")
        self.setModal(True)

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "SampleInformation.ui")
        loadUi(sources_ui_file, self)

        self.selected_sample_label: QtW.QLabel
        self.selected_sample_label.setWordWrap(True)
        self.gps = GPSFields('Samples', sample_id_list)
        self.top_horizontalLayout: QtW.QHBoxLayout
        self.top_horizontalLayout.addWidget(self.gps)
        self.age = AgeFields('Samples', sample_id_list)
        self.top_horizontalLayout.addWidget(self.age, 1)

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

        self.upb_analysis_pushButton.setAutoDefault(False)
        self.commit_pushButton.setAutoDefault(False)
        self.cancel_pushButton.setAutoDefault(False)
        self.updated = False
        self.commit_pushed = False
        self.focus_timer = QtC.QTimer(self)
        self._isApplicationFocused = True
        QtW.QApplication.instance().installEventFilter(self)

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
        self.sample_description_textEdit: QtW.QTextEdit
        self.sample_description_textEdit.setLineWrapMode(QtW.QTextEdit.LineWrapMode.WidgetWidth)

        self.gps_location_ids = ""

        self.msg = QtW.QMessageBox(self)
        create_savepoint('before_edit_samples')
        self.close_by_dialog = False

        # Fill in information based on selected samples
        self.sample_dictionary = {}
        self.populate_dropdowns()
        self.check_all_samples()
        self.sample_name_comboBox.setModel(self.sample_names_model)
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)

        self.installEventFilter(self)
        end_init_time = time.time()
        logger_setup.get_logger().info(f"Sample information dialog initialized in {end_init_time - start_init_time} seconds")
        self.showMaximized()

        self.loading_manager.close_loading_dialog('Loading', f'Opening Sample Information window...')

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
            self.sample_name_lineEdit.setEnabled(False)
            self.sample_igsn_lineEdit.setEnabled(False)
        elif len(checked_sample_names) == 1:
            self.checked_sample_names = checked_sample_names[0]
            self.sample_name_lineEdit.setEnabled(True)
            self.sample_igsn_lineEdit.setEnabled(True)
        self.selected_sample_label.setText(f"Selected Samples: {self.checked_sample_names}")
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)
        logger_setup.get_logger().info(f"Updated sample list: {self.checked_sample_names}")
        end_update_sample_list_time = time.time()
        logger_setup.get_logger().info(f"Updated sample list: {self.checked_sample_names} in {end_update_sample_list_time - start_update_sample_list_time} seconds")
        self.update_fields()

    def update_fields(self):
        self.loading_manager.show_loading_dialog('Updating','Updating fields...')
        logger_setup.get_logger().info("Updating fields")
        self.disconnect_text_signals()
        self.populate_fields()
        self.connect_signals()
        logger_setup.get_logger().info("Fields updated")
        self.loading_manager.close_loading_dialog('Updating', 'Updating fields...')

    def populate_dropdowns(self):
        start_populate_dropdown_time = time.time()
        logger_setup.get_logger().info("Populating dropdowns")

        populate_combo_box(self.column_name_comboBox, **{'table': 'Columns', 'column': 'ColumnName'})
        self.column_name_comboBox.model_modifiable = True
        self.column_name_comboBox.enable_context_menu(True)
        self.column_name_comboBox.set_single_click(True)
        self.column_name_comboBox.setPlaceholderText("Name of column, core, etc.")
        populate_combo_box(self.height_depth_unit_comboBox, **{'table': 'DistanceUnits', 'column': 'DistanceUnitAbbreviation'})
        self.sample_context_comboBox.model_modifiable = True
        self.sample_context_comboBox.enable_context_menu(True)
        populate_combo_box(self.sample_context_comboBox, **{'table': 'SampleContexts'})
        self.sampling_method_comboBox.model_modifiable = True
        self.sampling_method_comboBox.enable_context_menu(True)
        populate_combo_box(self.sampling_method_comboBox, **{'table': 'SamplingMethods'})
        self.unit_comboBox.model_modifiable = True
        self.unit_comboBox.enable_context_menu(True)
        populate_combo_box(self.unit_comboBox, **{'table': 'Units'})
        self.rock_type_comboBox.model_modifiable = True
        self.rock_type_comboBox.enable_context_menu(True)
        populate_combo_box(self.rock_type_comboBox, **{'table': 'RockTypes'})
        self.region_comboBox.model_modifiable = True
        self.region_comboBox.enable_context_menu(True)
        populate_combo_box(self.region_comboBox, **{'table': 'Regions'})
        self.setting_comboBox.model_modifiable = True
        self.setting_comboBox.enable_context_menu(True)
        populate_combo_box(self.setting_comboBox, **{'table': 'Settings'})
        self.age_signature_comboBox.model_modifiable = True
        self.age_signature_comboBox.enable_context_menu(True)
        populate_combo_box(self.age_signature_comboBox, **{'table': 'AgeSignatures'})

        self.sample_name_comboBox: CheckableComboBox
        self.sample_name_comboBox.view().setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.column_name_comboBox.view().setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        end_populate_dropdown_time = time.time()
        logger_setup.get_logger().info(f"Populated dropdowns in {end_populate_dropdown_time - start_populate_dropdown_time} seconds")
        logger_setup.get_logger().info("Dropdowns populated")

    def connect_signals(self):
        logger_setup.get_logger().info("Connecting signals")
        # Connect signals and slots
        self.upb_analysis_pushButton.clicked.connect(self.edit_upb_popup)
        self.commit_pushButton.clicked.connect(self.commit_clicked)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.sample_name_comboBox.closing.connect(self.update_sample_list)
        self.sample_name_comboBox.view().customContextMenuRequested.connect(self.show_context_menu)
        self.sample_igsn_lineEdit.editingFinished.connect(lambda: self.update_field('SampleIGSN', f'{self.sample_igsn_lineEdit.text()}'))
        self.column_groupBox.focusLost.connect(self.focus_lost_delay)
        self.sample_context_comboBox.closing.connect(lambda: self.update_sample_tags(self.sample_context_comboBox))
        self.sample_context_comboBox.add_triggered.connect(self.add_popup)
        self.sample_context_comboBox.edit_triggered.connect(self.edit_popup)
        self.sampling_method_comboBox.closing.connect(lambda: self.update_sample_tags(self.sampling_method_comboBox))
        self.sampling_method_comboBox.add_triggered.connect(self.add_popup)
        self.sampling_method_comboBox.edit_triggered.connect(self.edit_popup)
        self.unit_comboBox.closing.connect(lambda: self.update_sample_tags(self.unit_comboBox))
        self.unit_comboBox.add_triggered.connect(self.add_popup)
        self.unit_comboBox.edit_triggered.connect(self.edit_popup)
        self.rock_type_comboBox.closing.connect(lambda: self.update_sample_tags(self.rock_type_comboBox))
        self.rock_type_comboBox.add_triggered.connect(self.add_popup)
        self.rock_type_comboBox.edit_triggered.connect(self.edit_popup)
        self.region_comboBox.closing.connect(lambda: self.update_sample_tags(self.region_comboBox))
        self.region_comboBox.add_triggered.connect(self.add_popup)
        self.region_comboBox.edit_triggered.connect(self.edit_popup)
        self.setting_comboBox.closing.connect(lambda: self.update_sample_tags(self.setting_comboBox))
        self.setting_comboBox.add_triggered.connect(self.add_popup)
        self.setting_comboBox.edit_triggered.connect(self.edit_popup)
        self.age_signature_comboBox.closing.connect(lambda: self.update_sample_tags(self.age_signature_comboBox))
        self.age_signature_comboBox.add_triggered.connect(self.add_popup)
        self.age_signature_comboBox.edit_triggered.connect(self.edit_popup)
        self.sample_description_textEdit.editingFinished.connect(lambda: self.update_field('SampleDescription', f'{self.sample_description_textEdit.toPlainText()}'))
        logger_setup.get_logger().info("Signals connected")

    def disconnect_text_signals(self):
        logger_setup.get_logger().info("Disconnecting text signals")
        try:
            self.column_name_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.column_groupBox.focusLost.disconnect()
        except TypeError:
            pass
        try:
            self.sample_description_textEdit.editingFinished.disconnect()
        except TypeError:
            pass
        logger_setup.get_logger().info("Text signals disconnected")

    def populate_fields(self):
        logger_setup.get_logger().info("Populating fields")
        start_populate_fields_time = time.time()
        headers = get_headers('Samples')
        if len(self.checked_sample_list) > 1:
            sample_query = f'SELECT * FROM Samples WHERE SampleID in {tuple(self.checked_sample_list)}'
        elif len(self.checked_sample_list) == 1:
            sample_query = f'SELECT * FROM Samples WHERE SampleID = {self.checked_sample_list[0]}'
        else:
            sample_query = f'SELECT * FROM Samples'
        self.samples_table = QtS.QSqlQueryModel()
        self.samples_table.setQuery(sample_query)
        if self.samples_table.rowCount() == 0:
            logger_setup.get_logger().info("No samples to populate")
            return
        for header in headers:
            values = [self.samples_table.record(row).value(header) for row in range(self.samples_table.rowCount())]
            if len(set(values)) == 1 and not values[0]:
                # If all values are the same and empty, add an empty string
                text = ""
            elif len(set(values)) == 1 and values[0]:
                # If all values are the same and not empty, add the value
                text = values[0]
            else:
                # If values are different, add '-'
                text = "-"
            if 'SampleName' in header:
                if not text:
                    self.sample_name_lineEdit.setText(self.sample_name_lineEdit.placeholderText())
                else:
                    self.sample_name_lineEdit.setText(f"{text}")
            elif 'IGSN' in header:
                if not text:
                    self.sample_igsn_lineEdit.setText(self.sample_igsn_lineEdit.placeholderText())
                else:
                    self.sample_igsn_lineEdit.setText(f"{text}")
            elif 'ColumnID' in header:
                if not text:
                    set_comboBox_text(self.column_name_comboBox, self.column_name_comboBox.placeholderText())
                elif text == "-":
                    set_comboBox_text(self.column_name_comboBox, text)
                else:
                    column_id = text
                    query = QtS.QSqlQuery()
                    if not query.exec(f"SELECT ColumnName FROM Columns WHERE ColumnID = {column_id}"):
                        logger_setup.get_logger().critical(f"Error finding column name")
                        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                        return
                    query.next()
                    text = query.value(0)
                    set_comboBox_text(self.column_name_comboBox, text)
            elif 'HeightDepthError' in header and 'Calculated' not in header:
                if not text:
                    self.height_depth_error_lineEdit.setText(self.height_depth_error_lineEdit.placeholderText())
                else:
                    self.height_depth_error_lineEdit.setText(f"{text}")
            elif 'HeightDepth' in header:
                if not text:
                    self.height_depth_lineEdit.setText(self.height_depth_lineEdit.placeholderText())
                else:
                    self.height_depth_lineEdit.setText(f"{text}")
            elif 'HeightDepthUnit' in header:
                if not text:
                    set_comboBox_text(self.height_depth_unit_comboBox, settings.value('heightdepth_unit_abbreviation'))
                elif text == "-":
                    set_comboBox_text(self.height_depth_unit_comboBox, text)
                else:
                    unit_id = text
                    query = QtS.QSqlQuery()
                    if not query.exec(f"SELECT DistanceUnitAbbreviation FROM DistanceUnits WHERE DistanceUnitID = {unit_id}"):
                        logger_setup.get_logger().critical(f"Error finding height depth unit")
                        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                        return
                    query.next()
                    text = query.value(0)
                    set_comboBox_text(self.height_depth_unit_comboBox, text)
            elif 'HeightDepth' in header and 'Calculated' not in header:
                if not text:
                    self.height_depth_lineEdit.setText(self.height_depth_lineEdit.placeholderText())
                else:
                    self.height_depth_lineEdit.setText(f"{text}")
            elif 'SampleDescription' in header:
                if not text:
                    self.sample_description_textEdit.setText(self.sample_description_textEdit.placeholderText())
                else:
                    self.sample_description_textEdit.setText(f"{text}")
        # if len(self.sample_dictionary) == 0:
        #     self.populate_sample_dictionary()

        # Sample tags
        self.populate_checks('Samples_SampleContexts',self.sample_context_comboBox)
        self.populate_checks('Samples_SamplingMethods', self.sampling_method_comboBox)
        self.populate_checks('Samples_Units', self.unit_comboBox)
        self.populate_checks('Samples_RockTypes', self.rock_type_comboBox)
        self.populate_checks('Samples_Regions', self.region_comboBox)
        self.populate_checks('Samples_Settings', self.setting_comboBox)
        self.populate_checks('Samples_AgeSignatures', self.age_signature_comboBox)

        if set(self.gps.item_ids) != set(self.checked_sample_list):
            self.gps.update_list(self.checked_sample_list)
        if set(self.age.sample_ids) != set(self.checked_sample_list):
            self.age.update_list(self.checked_sample_list)
        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(f"Populated fields in {end_populate_fields_time - start_populate_fields_time} seconds")
        logger_setup.get_logger().info("Fields populated")

    def populate_sample_dictionary(self):
        logger_setup.get_logger().info("Populating fields")
        start_populate_fields_time = time.time()
        headers = get_headers('Samples')
        if len(self.checked_sample_list) > 1:
            self.samples_table = SQLiteTableModel(
                f'SELECT * FROM Samples WHERE SampleID in {tuple(self.checked_sample_list)}')
        elif len(self.checked_sample_list) == 1:
            self.samples_table = SQLiteTableModel(
                f'SELECT * FROM Samples WHERE SampleID = {self.checked_sample_list[0]}')
        else:
            self.samples_table = SQLiteTableModel(f'SELECT * FROM Samples')
        if self.samples_table.rowCount() == 0:
            logger_setup.get_logger().info("No samples to populate")
            return

    def populate_checks(self, many_to_many_table: str, combo: QtW.QComboBox):
        logger_setup.get_logger().info(f"Populating checks for {many_to_many_table}")
        start_populate_checks_time = time.time()
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        all_items = []
        some_items = []
        text = ""
        if isinstance(combo, CheckableTreeCombobox):
            model, indexes = find_tree_model(combo.model(), None)
            col = 0  # Name column is always placed in the first column
            tag_id_header = model.source_model.record().fieldName(0)
            id_col = 1  # ID column is always placed in the second column
        else:
            model = combo.model()
            col = get_name_column(model.tableName())
            tag_id_header = model.record().fieldName(0)
            id_col = 0  # ID column is always in the first column
        if len(self.checked_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected, so unchecking everything")
            if isinstance(combo, CheckableTreeCombobox):
                model.blockSignals(True)
                # recursively uncheck everything
                def uncheck_all(model: CheckableTreeModel, index: QtC.QModelIndex):
                    for row in range(model.rowCount(index)):
                        model_index = model.index(row, col, index)
                        model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                        uncheck_all(model, model_index)
                uncheck_all(model, QtC.QModelIndex())
                model.blockSignals(False)
            else:
                for row in range(model.rowCount()):
                    model_index = model.index(row, col)
                    model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if model.lastError().text():
                        logger_setup.get_logger().critical(f"Error setting unchecked for {model.tableName()}: {model.lastError().text()}")
            logger_setup.get_logger().info("Unchecked everything")
            combo.setCurrentText(text)
        else:
            logger_setup.get_logger().info(f"Checking {many_to_many_table}")
            if isinstance(combo, CheckableTreeCombobox):
                model.blockSignals(True)
                # recursively check data
                def check_data(model: CheckableTreeModel, index: QtC.QModelIndex):
                    for row in range(model.rowCount(index)):
                        model_index = model.index(row, col, index)
                        id_index = model.index(row, id_col, index)
                        tag_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
                        if len(self.checked_sample_list) > 1:
                            many_to_many_model.setFilter(
                                f"SampleID in {tuple(self.checked_sample_list)} AND {tag_id_header} = {tag_id}")
                        else:
                            many_to_many_model.setFilter(
                                f"SampleID = {self.checked_sample_list[0]} AND {tag_id_header} = {tag_id}")
                        if many_to_many_model.rowCount() == len(self.checked_sample_list):
                            # All samples have this tag
                            model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                            all_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                        elif many_to_many_model.rowCount() > 0:
                            # Some samples have this tag
                            model.setData(model_index, QtC.Qt.CheckState.PartiallyChecked,
                                          QtC.Qt.ItemDataRole.CheckStateRole)
                            some_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                        else:
                            # No samples have this tag
                            model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                        check_data(model, model_index)
                check_data(model, QtC.QModelIndex())
            else:
                for row in range(model.rowCount()):
                    tag_id = model.index(row, id_col).data()
                    if len(self.checked_sample_list) > 1:
                        many_to_many_model.setFilter(f"SampleID in {tuple(self.checked_sample_list)} AND {tag_id_header} = {tag_id}")
                    else:
                        many_to_many_model.setFilter(f"SampleID = {self.checked_sample_list[0]} AND {tag_id_header} = {tag_id}")
                    model_index = model.index(row, col)
                    if many_to_many_model.rowCount() == len(self.checked_sample_list):
                        # All samples have this tag
                        model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                        if model.lastError().text():
                            logger_setup.get_logger().critical(f"Error setting checked for {model.tableName()}: {model.lastError().text()}")
                        all_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                    elif many_to_many_model.rowCount() > 0:
                        # Some samples have this tag
                        model.setData(model_index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                        if model.lastError().text():
                            logger_setup.get_logger().critical(f"Error setting partial checked for {model.tableName()}: {model.lastError().text()}")
                        some_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                    else:
                        # No samples have this tag
                        model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                        if model.lastError().text():
                            logger_setup.get_logger().critical(f"Error setting unchecked for {model.tableName()}: {model.lastError().text()}")
        if not all_items and not some_items:
            # No samples have these tags
            text = ""
        elif not some_items:
            # All samples have the same tags
            text = ', '.join(all_items)
        else:
            # Samples have different tags
            text = "-"
        if isinstance(combo, CheckableTreeCombobox):
            model.blockSignals(False)
            combo.treeView.connect_edited_signal()
        if not text:
            text = combo.placeholderText()
        combo.setCurrentText(text)
        end_populate_checks_time = time.time()
        logger_setup.get_logger().info(f"Populated checks for {many_to_many_table} in {end_populate_checks_time - start_populate_checks_time} seconds")
        logger_setup.get_logger().info(f"Populated checks for {many_to_many_table}")
        return text

    def show_context_menu(self, pos: QtC.QPoint):
        combo = self.sender()
        logger_setup.get_logger().info("Showing context menu")
        menu = QtW.QMenu()
        selected_indexes = combo.view().selectedIndexes()
        if isinstance(combo, CheckableComboBox) and not combo.single_click:
            select_action = menu.addAction("Select all")
            unselect_action = menu.addAction("Unselect all")
            delete_action = menu.addAction("Delete selected")
            add_action = None
            edit_action = None
        else:
            add_action = menu.addAction("Add")
            edit_action = menu.addAction("Edit")
            select_action = None
            unselect_action = None
            delete_action = None
        action = menu.exec(combo.view().mapToGlobal(pos))
        if action == select_action:
            self.check_all_samples()
        elif action == unselect_action:
            self.uncheck_all_samples()
        elif action == delete_action:
            if self.delete_question():
                delete_data(selected_indexes, 'Samples')
                action = None
        elif action == add_action:
            self.add_popup(combo, action)
            action = None
        elif action == edit_action:
            self.edit_popup()
            action = None

    def update_field(self, field: str, text: str):
        logger_setup.get_logger().info(f"Update field called with {field} and {text}")
        if 'before_edit_samples' not in self.savepoint_manager.savepoint_list:
            # The edits were already saved and the save point released
            return
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
                        query.prepare(f"UPDATE Samples SET {field} = :text WHERE SampleID = :sample_id")
                        query.bindValue(":text", text)
                        query.bindValue(":sample_id", sample_id)
                        if not query.exec():
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

    def update_sample_tags(self, combo: CheckableTreeCombobox):
        logger_setup.get_logger().info(f"update_sample_tags called with {combo.objectName()}")
        if not isinstance(combo, CheckableTreeCombobox):
            logger_setup.get_logger().critical(f"Combo box is not CheckableTreeComboBox")
            return False
        model, indexes = find_tree_model(combo.model(), None)
        if model:
            table = model.table
            id_header = get_headers(table)[0]
        else:
            logger_setup.get_logger().critical(f"Could not find model for combo box {combo.objectName()}")
            return False
        if not combo.treeView.model_edited:
            logger_setup.get_logger().info(f"No changes to {table}")
            return True
        start_update_sample_tags = time.time()
        many_to_many_model = QtS.QSqlTableModel()
        set_table(many_to_many_model, f"Samples_{table}")

        if len(self.checked_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected")
            return
        else:
            checked_ids , partially_checked_ids, checked_indices, partially_checked_indices = model.traverse_checkable_tree(QtC.QModelIndex())
            logger_setup.get_logger().info(f"Updating {table} for {len(self.checked_sample_list)} samples")
            create_savepoint('before_update')
            update = model.update_many_table(f'Samples_{table}', self.checked_sample_list)
            if update is False:
                logger_setup.get_logger().critical(f"Failed to update {table} for selected Samples")
                rollback_savepoint('before_update')
                return
            self.updated = True
            combo.treeView.toggle_edited(False)
            populate_many_combo_checks(f'Samples_{table}', combo, self.checked_sample_list)
            end_update_sample_tags_time = time.time()
            logger_setup.get_logger().info(f"Updated {table} for {len(self.checked_sample_list)} samples in {end_update_sample_tags_time - start_update_sample_tags} seconds")
            # logger_setup.get_logger().info(f"Updated {table} for {len(self.checked_sample_list)} samples")
            release_savepoint('before_update')

    def update_column_info(self):
        logger_setup.get_logger().info("Update column height called")
        if not self.column_groupBox.edited:
            logger_setup.get_logger().info(f"No changes to column height")
            return
        if len(self.checked_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected")
            return
        start_update_column_height_time = time.time()
        create_savepoint('before_update')
        query = QtS.QSqlQuery()
        if not query.exec(f"SELECT ColumnID FROM Columns WHERE ColumnName = '{self.column_name_comboBox.currentText()}'"):
            logger_setup.get_logger().critical(f"Failed to select ColumnID for {self.column_name_comboBox.currentText()}")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_update')
            return
        query.next()
        column_id = query.value(0)
        if not query.exec(f"SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = '{self.height_depth_unit_comboBox.currentText()}'"):
            logger_setup.get_logger().critical(f"Failed to select DistanceUnitID for {self.height_depth_unit_comboBox.currentText()}")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_update')
            return
        query.next()
        unit_id = query.value(0)
        for sample_id in self.checked_sample_list:
            query.prepare(f'''UPDATE Samples SET SampleColumnID = :columnID, HeightDepth = :height, 
                            HeightDepthError = :error, HeightDepthUnitID = :unitID WHERE SampleID = :sample_id''')
            query.bindValue(":columnID", column_id)
            query.bindValue(":height", self.height_depth_lineEdit.text())
            query.bindValue(":error", self.height_depth_error_lineEdit.text())
            query.bindValue(":unitID", unit_id)
            query.bindValue(":sample_id", sample_id)
            if not query.exec():
                logger_setup.get_logger().critical(f"Failed to update column information")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('before_update')
                return
        update_modified_timestamp('Samples', self.checked_sample_list)
        self.updated = True
        end_update_column_height_time = time.time()
        logger_setup.get_logger().info(f"Updated column height in {end_update_column_height_time - start_update_column_height_time} seconds")
        release_savepoint('before_update')

    def add_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.model(), combo.view())
            dlg_args = add_tree_popup(combo.view(), action)
            self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {table}...')
            if dlg_args:
                dlg = AddTreeTags(self, table, **dlg_args)
            else:
                dlg = AddTreeTags(self, table)
        else:
            self.loading_manager.show_loading_dialog('Loading', f'Opening add window for {table}...')
            dlg = AddTags(self, table)
        if not dlg:
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        dlg.exec()
        if dlg.updated:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            if isinstance(combo, CheckableTreeCombobox):
                restore_expanded_state(table, combo.model(), combo.view())
            self.populate_checks(f'Samples_{table}', combo)
        else:
            return

    def edit_popup(self):
        combo = self.sender()
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        else:
            dlg = EditTable(self, table)
        if dlg is None:
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            if isinstance(combo, CheckableTreeCombobox):
                restore_expanded_state(table, combo.model(), combo.view())
            self.populate_checks(f'Samples_{table}', combo)

    def edit_upb_popup(self):
        logger_setup.get_logger().info("Edit U-Pb popup called")
        self.loading_manager.show_loading_dialog("Loading", "Showing U-Pb analysis edit dialog")
        dlg = EditUPbTags(self, self.checked_sample_list)
        dlg.exec()
        if dlg.updated:
            self.updated = True

    def check_focus(self):
        if self.column_groupBox.any_child_has_focus() and self.column_groupBox.edited:
            self.column_groupBox.focusLost.emit()
        if self.sample_description_textEdit.hasFocus():
            self.sample_description_textEdit.editingFinished.emit()

    def focus_lost_delay(self):
        if self._isApplicationFocused:
            self.lost_group_box = self.sender()
            self.focus_timer.setSingleShot(True)
            if self.lost_group_box == self.column_groupBox:
                self.focus_timer.timeout.connect(self.update_column_info)
                self.focus_timer.start(100)

    def commit_clicked(self):
        logger_setup.get_logger().info("Commit clicked")
        self.commit_pushed = True
        self.commit_question()

    def delete_question(self):
        msg_box = QtW.QMessageBox(self)
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to delete these samples and all associated data?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

    def discard_question(self):
        logger_setup.get_logger().info("Discard question called")
        if self.updated or self.gps.updated or self.age.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to discard all changes?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            logger_setup.get_logger().info("Showing discard question")
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                logger_setup.get_logger().info("Discarding changes")
                rollback_savepoint('before_edit_samples')
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
        self.age.check_focus()
        self.gps.check_focus()
        self.check_focus()
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
                self.commit_pushed = False
                pass
        else:
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def commit(self):
        release_savepoint('before_edit_samples')
        # Edit occurred in the dialog
        self.updated = True
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
                # self.saveWindowState()
                logger_setup.get_logger().info("Closing SampleInformation dialog")
                event.accept()
        else:
            logger_setup.get_logger().info("Closing SampleInformation dialog")
            event.accept()
