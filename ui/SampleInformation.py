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

import Functions.SQLUtils as SQLUtils

from Functions.Widget_classes import (
    set_table, SQLiteTableModel, CheckableSqlTableModel, TreeModel, CheckableTreeCombobox, save_expanded_state,
    delete_data, find_tree_model, CheckableComboBox, get_headers, add_tree_popup, populate_combo_box,
    populate_many_combo_checks, ReadableProxyModel, get_view_from_table, close_loading_dialog, show_loading_dialog,
    get_id_from_name
)
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import SettingsManager
from ui.EditView import EditView

settings = SettingsManager().settings
from ui.GPSFields import GPSFields
from ui.AgeFields import AgeFields
from ui.ColumnFields import ColumnFields
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
        self.columns = ColumnFields(sample_id_list)
        self.verticalLayout_samples.insertWidget(9, self.columns)
        self.gps = GPSFields('Samples', sample_id_list)
        self.top_horizontalLayout: QtW.QHBoxLayout
        self.top_horizontalLayout.addWidget(self.gps)
        self.age = AgeFields('Samples', sample_id_list)
        self.top_horizontalLayout.addWidget(self.age)

        # Sample names table
        self.sample_names_model = CheckableSqlTableModel()  # The one used to populate the dropdown checkbox of samples to edit, shows only name and description
        self.sample_names_proxy = ReadableProxyModel()
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
        self.focus_timer.setSingleShot(True)
        self.discard_timer = QtC.QTimer(self)
        self.discard_timer.setSingleShot(True)
        self.commit_timer = QtC.QTimer(self)
        self.commit_timer.setSingleShot(True)
        self._isApplicationFocused = True
        QtW.QApplication.instance().installEventFilter(self)

        # Sample information models
        self.samples_table = None
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
        self.sample_name_comboBox.setModel(self.sample_names_proxy)
        self.sample_name_comboBox.enable_context_menu(True)
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)

        self.installEventFilter(self)
        end_init_time = time.time()
        logger_setup.get_logger().info(f"Sample information dialog initialized in {end_init_time - start_init_time} seconds")
        self.showMaximized()

        close_loading_dialog('Loading', f'Opening Sample Information window...')

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
        previous_checked_sample_list = self.checked_sample_list
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
        if self.checked_sample_list == previous_checked_sample_list:
            logger_setup.get_logger().info("Sample list has not changed, skipping update")
            return
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
        self.sample_names_proxy = ReadableProxyModel()
        self.sample_names_proxy.setSourceModel(self.sample_names_model)
        logger_setup.get_logger().info(f"Updated sample list: {self.checked_sample_names}")
        end_update_sample_list_time = time.time()
        logger_setup.get_logger().info(f"Updated sample list: {self.checked_sample_names} in {end_update_sample_list_time - start_update_sample_list_time} seconds")
        self.update_fields()

    def update_fields(self):
        show_loading_dialog('Updating','Updating fields...')
        logger_setup.get_logger().info("Updating fields")
        self.disconnect_text_signals()
        if set(self.gps.item_ids) != set(self.checked_sample_list):
            self.gps.update_list(self.checked_sample_list)
        if set(self.age.sample_ids) != set(self.checked_sample_list):
            self.age.update_list(self.checked_sample_list)
        if set(self.columns.checked_sample_list) != set(self.checked_sample_list):
            self.columns.update_list(self.checked_sample_list)
        self.populate_fields()
        self.connect_signals()
        logger_setup.get_logger().info("Fields updated")
        close_loading_dialog('Updating', 'Updating fields...')

    def populate_dropdowns(self):
        start_populate_dropdown_time = time.time()
        logger_setup.get_logger().info("Populating dropdowns")
        show_loading_dialog('Loading', 'Populating dropdowns...')
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
        end_populate_dropdown_time = time.time()
        close_loading_dialog('Loading', 'Populating dropdowns...')
        logger_setup.get_logger().info(f"Populated dropdowns in {end_populate_dropdown_time - start_populate_dropdown_time} seconds")
        logger_setup.get_logger().info("Dropdowns populated")

    def connect_signals(self):
        logger_setup.get_logger().info("Connecting signals")
        # Connect signals and slots
        self.upb_analysis_pushButton.clicked.connect(self.edit_upb_popup)
        self.commit_pushButton.clicked.connect(self.commit_clicked)
        self.cancel_pushButton.clicked.connect(self.discard_clicked)
        self.sample_name_comboBox.closing.connect(self.update_sample_list)
        # this should not be needed as the combobox handles the custom context menus now
        # self.sample_name_comboBox.view().customContextMenuRequested.connect(self.show_context_menu)
        self.sample_name_comboBox.edit_triggered.connect(self.edit_popup)
        self.sample_name_comboBox.delete_triggered.connect(self.delete_item)
        self.sample_igsn_lineEdit.editingFinished.connect(lambda: self.update_field('SampleIGSN', f'{self.sample_igsn_lineEdit.text()}'))
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
            sample_query = f'SELECT * FROM Samples WHERE SampleID IS NULL'
        self.samples_table = QtS.QSqlQueryModel()
        self.samples_table.setQuery(sample_query)
        while self.samples_table.canFetchMore():
            self.samples_table.fetchMore()
        if self.samples_table.rowCount() == 0:
            logger_setup.get_logger().info("No samples to populate")
            self.clear_fields()
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
                if text is None or text == '':
                    self.sample_name_lineEdit.setText('')
                else:
                    self.sample_name_lineEdit.setText(f"{text}")
            elif 'IGSN' in header:
                if text is None or text == '':
                    self.sample_igsn_lineEdit.setText('')
                else:
                    self.sample_igsn_lineEdit.setText(f"{text}")
            elif 'SampleDescription' in header:
                if text is None or text == '':
                    self.sample_description_textEdit.setText('')
                else:
                    self.sample_description_textEdit.setText(f"{text}")

        # Sample tags
        populate_many_combo_checks('Samples_SampleContexts',self.sample_context_comboBox, self.checked_sample_list)
        populate_many_combo_checks('Samples_SamplingMethods', self.sampling_method_comboBox, self.checked_sample_list)
        populate_many_combo_checks('Samples_Units', self.unit_comboBox, self.checked_sample_list)
        populate_many_combo_checks('Samples_RockTypes', self.rock_type_comboBox, self.checked_sample_list)
        populate_many_combo_checks('Samples_Regions', self.region_comboBox, self.checked_sample_list)
        populate_many_combo_checks('Samples_Settings', self.setting_comboBox, self.checked_sample_list)
        populate_many_combo_checks('Samples_AgeSignatures', self.age_signature_comboBox, self.checked_sample_list)

        end_populate_fields_time = time.time()
        logger_setup.get_logger().info(f"Populated fields in {end_populate_fields_time - start_populate_fields_time} seconds")
        logger_setup.get_logger().info("Fields populated")

    def clear_fields(self):
        logger_setup.get_logger().info("Clearing fields")
        self.sample_name_lineEdit.setText('')
        self.sample_igsn_lineEdit.setText('')
        self.sample_description_textEdit.setText('')

        # Sample tags
        if self.sample_context_comboBox.model().rowCount() > 0:
            populate_many_combo_checks('Samples_SampleContexts', self.sample_context_comboBox, self.checked_sample_list)
        if self.sampling_method_comboBox.model().rowCount() > 0:
            populate_many_combo_checks('Samples_SamplingMethods', self.sampling_method_comboBox, self.checked_sample_list)
        if self.unit_comboBox.model().rowCount() > 0:
            populate_many_combo_checks('Samples_Units', self.unit_comboBox, self.checked_sample_list)
        if self.rock_type_comboBox.model().rowCount() > 0:
            populate_many_combo_checks('Samples_RockTypes', self.rock_type_comboBox, self.checked_sample_list)
        if self.region_comboBox.model().rowCount() > 0:
            populate_many_combo_checks('Samples_Regions', self.region_comboBox, self.checked_sample_list)
        if self.setting_comboBox.model().rowCount() > 0:
            populate_many_combo_checks('Samples_Settings', self.setting_comboBox, self.checked_sample_list)
        if self.age_signature_comboBox.model().rowCount() > 0:
            populate_many_combo_checks('Samples_AgeSignatures', self.age_signature_comboBox, self.checked_sample_list)

    def populate_sample_dictionary(self):
        logger_setup.get_logger().info("Populating sample dictionary")
        start_populate_samples_time = time.time()
        headers = get_headers('Samples')
        if len(self.checked_sample_list) > 1:
            self.samples_table = SQLiteTableModel(
                f'SELECT * FROM Samples WHERE SampleID in {tuple(self.checked_sample_list)}')
        elif len(self.checked_sample_list) == 1:
            self.samples_table = SQLiteTableModel(
                f'SELECT * FROM Samples WHERE SampleID = {self.checked_sample_list[0]}')
        else:
            self.samples_table = SQLiteTableModel(f'SELECT * FROM Samples WHERE SampleID IS NULL')
        if self.samples_table.last_error:
            logger_setup.get_logger().critical(f"Error populating samples table")
        if self.samples_table.rowCount() == 0:
            logger_setup.get_logger().info("No samples to populate")
            return
        logger_setup.get_logger().info(f"Populated sample dictionary in {time.time() - start_populate_samples_time} seconds")

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
        item_id = get_id_from_name(table, text)
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
        if len(self.checked_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected")
            return False
        model, indexes = find_tree_model(combo.model(), None)
        if model:
            table = model.table
            id_header = get_headers(table)[0]
        else:
            logger_setup.get_logger().critical(f"Could not find model for combo box {combo.objectName()}")
            return False
        start_update_sample_tags = time.time()
        logger_setup.get_logger().info(f"Updating {table} for {len(self.checked_sample_list)} samples")
        create_savepoint('before_update')
        update = model.update_many_table(f'Samples_{table}', self.checked_sample_list)
        if update == 'False':
            logger_setup.get_logger().critical(f"Failed to update {table} for selected Samples")
            rollback_savepoint('before_update')
            return False
        elif update == 'No':
            logger_setup.get_logger().info(f"No changes to {table} for selected Samples")
            rollback_savepoint('before_update')
            return True
        self.updated = True
        populate_many_combo_checks(f'Samples_{table}', combo, self.checked_sample_list)
        end_update_sample_tags_time = time.time()
        logger_setup.get_logger().info(f"Updated {table} for {len(self.checked_sample_list)} samples in {end_update_sample_tags_time - start_update_sample_tags} seconds")
        release_savepoint('before_update')
        return True

    def add_popup(self, combo: QtW.QComboBox, action: QtG.QAction | None = None):
        combo.blockSignals(True)
        logger_setup.get_logger().info(f"Add popup called")
        model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error adding new item")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                combo.blockSignals(False)
                return
        else:
            table = combo.model().tableName()
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.view())
            dlg_args = add_tree_popup(combo.view(), action)
            show_loading_dialog('Loading', f'Opening add window for {table}...')
            if dlg_args:
                dlg = AddTreeTags(self, table, **dlg_args)
            else:
                dlg = AddTreeTags(self, table)
        elif table in ['References', '"References"']:
            table = 'References'
            show_loading_dialog('Loading', f'Opening add window for {table}...')
            dlg = NewReference(self)
        else:
            show_loading_dialog('Loading', f'Opening add window for {table}...')
            dlg = AddTags(self, table)
        if not dlg:
            combo.blockSignals(False)
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        dlg.exec()
        if dlg.updated:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            populate_many_combo_checks(f'Samples_{table}', combo, self.checked_sample_list)
            combo.blockSignals(False)
        else:
            combo.blockSignals(False)
            return

    def edit_popup(self):
        logger_setup.get_logger().info(f'Edit popup called')
        combo: QtW.QComboBox = self.sender()
        model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error editing table")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                return
        elif isinstance(model, QtC.QSortFilterProxyModel):
            model = model.sourceModel()
            table = model.tableName()
        else:
            table = combo.model().tableName()
        combo.blockSignals(True)
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        elif table != get_view_from_table(table):
            dlg = EditView(self, table)
        else:
            dlg = EditTable(self, table)
        if dlg is None:
            combo.blockSignals(False)
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            populate_many_combo_checks(f'Samples_{table}', combo, self.checked_sample_list)
        combo.blockSignals(False)

    def edit_upb_popup(self):
        logger_setup.get_logger().info("Edit U-Pb popup called")
        show_loading_dialog("Loading", "Showing U-Pb analysis edit dialog")
        self.sender().blockSignals(True)
        dlg = EditUPbTags(self, self.checked_sample_list)
        dlg.exec()
        if dlg.updated:
            self.updated = True
        self.sender().blockSignals(False)

    def delete_item(self):
        logger_setup.get_logger().info(f"Delete item called")
        combo = self.sender()
        selected_ids = []
        model = combo.model()
        table = None
        while not table:
            try: table = model.tableName()
            except AttributeError:
                model = model.sourceModel()
        if isinstance(combo, CheckableComboBox):
            selected_ids = model.checked_ids
        elif isinstance(combo, CheckableTreeCombobox):
            model, indexes = find_tree_model(model, None)
            if model:
                selected_ids = model.checked_ids
        if selected_ids:
            if delete_data(table, selected_ids):
                self.updated = True
                if table == 'Samples':
                    for deleted_id in selected_ids:
                        self.selected_sample_list.remove(deleted_id)
                # Update all
                self.checked_sample_list = []
                self.sample_names_model = CheckableSqlTableModel()
                self.sample_names_model = set_table(self.sample_names_model, 'Samples')
                if len(self.selected_sample_list) > 1:
                    self.sample_names_model.setFilter(f"SampleID in {tuple(self.selected_sample_list)}")
                else:
                    self.sample_names_model.setFilter(f"SampleID = {self.selected_sample_list[0]}")
                self.sample_names_model.select()
                self.sample_names_proxy = QtC.QSortFilterProxyModel()
                self.sample_names_proxy.setSourceModel(self.sample_names_model)
                self.sample_name_comboBox.setModel(self.sample_names_proxy)
                self.check_all_samples()
                self.sample_name_comboBox.enable_context_menu(True)
                self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)
                self.populate_dropdowns()
        else:
            return

    def check_focus(self):
        if self.sample_description_textEdit.hasFocus():
            self.sample_description_textEdit.editingFinished.emit()

    def discard_clicked(self):
        logger_setup.get_logger().info("Discard clicked")
        self.cancel_pushButton.blockSignals(True)
        self.discard_timer.timeout.connect(self.discard_question)
        self.discard_timer.start(200)

    def commit_clicked(self):
        logger_setup.get_logger().info("Commit clicked")
        self.commit_pushButton.blockSignals(True)
        if not self.commit_pushed:
            self.commit_pushed = True
            self.commit_question()

    def discard_question(self):
        logger_setup.get_logger().info("Discard question called")
        if self.updated or self.gps.updated or self.age.updated or self.columns.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to discard all changes?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            logger_setup.get_logger().info("Showing discard question")
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                logger_setup.get_logger().info("Discarding changes")
                self.updated = False
                self.gps.updated = False
                self.age.updated = False
                self.columns.updated = False
                rollback_savepoint('before_edit_samples')
                self.reject()
                self.close_by_dialog = True
                self.close()
                self.close_by_dialog = False
            else:
                self.cancel_pushButton.blockSignals(False)
                pass
        else:
            self.updated = False
            self.gps.updated = False
            self.age.updated = False
            self.columns.updated = False
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def commit_question(self):
        self.age.check_focus()
        self.gps.check_focus()
        self.columns.check_focus()
        self.check_focus()
        if self.updated or self.gps.updated or self.age.updated or self.columns.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to commit all changes to the database?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                self.updated = True
                self.commit()
            else:
                self.commit_pushed = False
                self.commit_pushButton.blockSignals(False)
                pass
        else:
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False

    def commit(self):
        release_savepoint('before_edit_samples')
        # Edit occurred in the dialog
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.updated or self.gps.updated or self.age.updated or self.columns.updated:
                self.discard_question()
                event.ignore()
            else:
                # self.saveWindowState()
                logger_setup.get_logger().info("Closing SampleInformation dialog")
                event.accept()
        else:
            logger_setup.get_logger().info("Closing SampleInformation dialog")
            event.accept()
