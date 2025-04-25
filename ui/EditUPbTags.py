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
    set_table, FontDelegate, SQLiteTableModel, CheckableSqlQueryModel,
    CheckableSqlTableModel, get_name_column, get_view_name_column, CheckableTreeModel, TreeModel,
    show_column, set_comboBox_text, find_upb_from_samples, populate_combo_box, add_tree_popup, CheckableTreeCombobox,
    CheckableComboBox, find_tree_model, populate_model_checks, populate_tree_model_checks, save_expanded_state,
    restore_expanded_state
)
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import settings
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Database_manager import update_database
from ui.New_reference import NewReference
from ui.AddTags import AddTags
from ui.AddTreeTags import AddTreeTags
from ui.EditTable import EditTable
from ui.EditTree import EditTree

class EditUPbTags(QtW.QDialog):
    def __init__(self, parent_window, sample_id_list: list | None):
        super().__init__(parent=parent_window)
        logger_setup.get_logger().info("Starting the sample information dialog")
        start_init_time = time.time()
        self.loading_manager = LoadingDialogManager.get_instance()
        self.parent_window = parent_window
        self.savepoint_manager = SavepointManager.get_instance()
        self.setWindowTitle("Edit U-Pb Information")
        self.setModal(True)
        # self.loadWindowState()
        self.updated = False
        self.close_by_dialog = False

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "EditUPbTags.ui")
        loadUi(sources_ui_file, self)

        # Sample names table
        self.selected_sample_label: QtW.QLabel
        self.selected_sample_label.setWordWrap(True)
        if sample_id_list is None or len(sample_id_list) == 0:
            self.selected_sample_list = []
        else:
            self.selected_sample_list = sample_id_list
            if len(self.selected_sample_list) > 1:
                self.sample_names_model = SQLiteTableModel(
                    f'SELECT SampleName FROM Samples WHERE SampleID in {tuple(self.selected_sample_list)}')
            else:
                self.sample_names_model = SQLiteTableModel(
                    f'SELECT SampleName FROM Samples WHERE SampleID = {self.selected_sample_list[0]}')
            self.sample_name_list = []
            for row in range(self.sample_names_model.rowCount()):
                index = self.sample_names_model.index(row, 0, QtC.QModelIndex())
                self.sample_name_list.append(self.sample_names_model.data(index, QtC.Qt.ItemDataRole.DisplayRole))
            if len(self.sample_name_list) > 1:
                self.text_sample_names = ", ".join(self.sample_name_list)
            elif len(self.sample_name_list) == 1:
                self.text_sample_names = self.sample_name_list[0]
            self.selected_sample_label.setText(f"Selected Samples: {self.text_sample_names}")
            self.upb_analysis_ids = find_upb_from_samples(self.selected_sample_list)
        if len(self.upb_analysis_ids) == 0:
            logger_setup.get_logger().error("No UPb Analyses for selected samples")
            self.close()

        label_text = self.label.text()
        label_text = label_text.replace("#", str(len(self.upb_analysis_ids)))
        self.label.setText(label_text)

        self.msg = QtW.QMessageBox(self)
        create_savepoint('before_upb_edit')

        # Fill in information based on selected samples
        self.populate_dropdowns()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.populate_fields()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.connect_signals()

        self.loading_manager.close_loading_dialog("Loading", "Showing U-Pb analysis edit dialog")

    def populate_dropdowns(self):
        self.reference_comboBox.model_modifiable = True
        self.reference_comboBox.enable_context_menu(True)
        populate_combo_box(self.reference_comboBox, **{'table': 'ReferenceView', 'column': 'ReferenceDisplay'})
        self.analysis_method_comboBox.model_modifiable = True
        self.analysis_method_comboBox.enable_context_menu(True)
        populate_combo_box(self.analysis_method_comboBox, **{'table': 'UPbAnalysisMethods'})
        self.lab_facility_comboBox.model_modifiable = True
        self.lab_facility_comboBox.enable_context_menu(True)
        populate_combo_box(self.lab_facility_comboBox, **{'table': 'LabFacilities'})
        self.instrument_comboBox.model_modifiable = True
        self.instrument_comboBox.enable_context_menu(True)
        populate_combo_box(self.instrument_comboBox, **{'table': 'Instruments'})
        populate_combo_box(self.ratio_error_format_comboBox, **{'table': 'ErrorFormats', 'column': 'ErrorFormatAbbreviation'})
        populate_combo_box(self.age_error_format_comboBox, **{'table': 'ErrorFormats', 'column': 'ErrorFormatAbbreviation'})
        populate_combo_box(self.age_unit_comboBox, **{'table': 'AgeUnits', 'column': 'AgeUnitAbbreviation'})
        populate_combo_box(self.concordance_format_comboBox, **{'table': 'ConcordanceFormats', 'column': 'ConcordanceFormatAbbreviation'})
        populate_combo_box(self.spot_size_unit_comboBox, **{'table': 'DistanceUnits', 'column': 'DistanceUnitAbbreviation'})

    def connect_signals(self):
        logger_setup.get_logger().info("Connecting signals")
        # Connect signals and slots
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)

        self.reference_comboBox.closing.connect(lambda: self.update_subfield_id('ReferenceID'))
        self.reference_comboBox.add_triggered.connect(self.add_popup)
        self.reference_comboBox.edit_triggered.connect(self.edit_popup)
        self.analysis_method_comboBox.closing.connect(lambda: self.update_subfield_id('UPbAnalysisMethodID'))
        self.analysis_method_comboBox.add_triggered.connect(self.add_popup)
        self.analysis_method_comboBox.edit_triggered.connect(self.edit_popup)
        self.lab_facility_comboBox.closing.connect(
            lambda: self.update_subfield_id('LabFacilityID'))
        self.lab_facility_comboBox.add_triggered.connect(self.add_popup)
        self.lab_facility_comboBox.edit_triggered.connect(self.edit_popup)
        self.instrument_comboBox.closing.connect(lambda: self.update_subfield_id('InstrumentID'))
        self.instrument_comboBox.add_triggered.connect(self.add_popup)
        self.instrument_comboBox.edit_triggered.connect(self.edit_popup)
        self.ratio_error_format_comboBox.closing.connect(lambda: self.update_subfield_id('RatioErrorFormatID'))
        self.age_error_format_comboBox.closing.connect(lambda: self.update_subfield_id('AgeErrorFormatID'))
        self.age_unit_comboBox.closing.connect(lambda: self.update_subfield_id('AgeUnitID'))
        self.concordance_format_comboBox.closing.connect(lambda: self.update_subfield_id('ConcordanceFormatID'))
        self.spot_size_unit_comboBox.closing.connect(lambda: self.update_subfield_id('SpotSizeUnitID'))
        self.spot_size_lineEdit.editingFinished.connect(lambda: self.update_subfield('SpotSize', self.spot_size_lineEdit.text()))
        
        logger_setup.get_logger().info("Signals connected")

    def populate_fields(self):
        logger_setup.get_logger().info("Populating fields")
        self.loading_manager.show_loading_dialog("Loading", "Populating fields")
        start_populate_fields_time = time.time()

        self.populate_upb_checks(self.reference_comboBox)
        self.reference_comboBox.set_single_click(True)
        self.populate_upb_checks(self.analysis_method_comboBox)
        self.analysis_method_comboBox.set_single_click(True)
        self.populate_upb_checks(self.lab_facility_comboBox)
        self.lab_facility_comboBox.set_single_click(True)
        self.populate_upb_checks(self.instrument_comboBox)
        self.instrument_comboBox.set_single_click(True)
        self.populate_upb_checks(self.ratio_error_format_comboBox)
        self.ratio_error_format_comboBox.set_single_click(True)
        self.populate_upb_checks(self.age_error_format_comboBox)
        self.age_error_format_comboBox.set_single_click(True)
        self.populate_upb_checks(self.age_unit_comboBox)
        self.age_unit_comboBox.set_single_click(True)
        self.populate_upb_checks(self.concordance_format_comboBox)
        self.concordance_format_comboBox.set_single_click(True)
        self.populate_upb_checks(self.spot_size_unit_comboBox)
        self.spot_size_unit_comboBox.set_single_click(True)

        self.loading_manager.close_loading_dialog("Loading", "Populating fields")

    def populate_upb_checks(self, combo: QtW.QComboBox):
        start_populate_upb_checks_time = time.time()
        text = ""
        if isinstance(combo.model(), CheckableSqlTableModel | CheckableSqlQueryModel):
            model = combo.model()
            combo.objectName()
            try:
                table = model.view
                name_column = get_view_name_column(table)
            except AttributeError:
                table = model.tableName()
                name_column = get_name_column(table)
            if 'ratio_error' in combo.objectName():
                table_id_header = 'RatioErrorFormatID'
            elif 'age_error' in combo.objectName():
                table_id_header = 'AgeErrorFormatID'
            elif 'spot_size' in combo.objectName():
                table_id_header = 'SpotSizeUnitID'
            else:
                table_id_header = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if not populate_model_checks(model, self.upb_analysis_ids, 'UPbAnalyses', table_id_header):
                return
            checked_ids = model.checked_ids
            partially_checked_ids = model.partially_checked_ids
        elif isinstance(combo.model(), CheckableTreeModel):
            tree_model, indexes = find_tree_model(combo.model(), None)
            table = tree_model.table
            model = tree_model.sourceModel()
            try:
                name_column = get_view_name_column(model.view)
            except AttributeError:
                name_column = get_name_column(table)
            if not populate_tree_model_checks(tree_model, self.upb_analysis_ids, 'UPbAnalyses'):
                return
            checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = tree_model.traverse_checkable_tree(QtC.QModelIndex())
        if partially_checked_ids:
            text = "-"
        elif checked_ids:
            checked_names = []
            for row in range(model.rowCount()):
                if model.data(model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole) in checked_ids:
                    checked_names.append(model.data(model.index(row, name_column), QtC.Qt.ItemDataRole.DisplayRole))
            text = ", ".join(checked_names)
        else:
            text = combo.placeholderText()
        combo.setCurrentText(text)
        end_populate_upb_checks_time = time.time()
        logger_setup.get_logger().info(f"Populated UPb checks for {table} in {end_populate_upb_checks_time - start_populate_upb_checks_time} seconds")

    def update_subfield_id(self, field: str):
        combo = self.sender()
        if isinstance(combo, CheckableTreeCombobox):
            model, indexes = find_tree_model(combo.model(), None)
            table = model.table
            column = get_name_column(table)
        else:
            model = combo.model()
            table = model.tableName()
            try:
                view = model.tableView()
                column = get_view_name_column(view)
            except AttributeError:
                column = get_name_column(table)
        logger_setup.get_logger().info(f"update_subfield_id called with {table}")
        self.loading_manager.show_loading_dialog("Updating", f"Updating {field}")
        start_update_sub_tags_time = time.time()
        # UPbAnalyses have only one value for each field, so only one value should be checked
        # If there are still partial checks, then nothing should be updated
        if isinstance(model, CheckableTreeModel):
            checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = model.traverse_checkable_tree(
                QtC.QModelIndex())
        else:
            checked_ids = model.checked_ids
            partially_checked_ids = model.partially_checked_ids
        if len(self.upb_analysis_ids) > 1:
            query_where_string = f"IN {tuple(self.upb_analysis_ids)}"
        elif len(self.upb_analysis_ids) == 1:
            query_where_string = f"= {self.upb_analysis_ids[0]}"
        if len(self.selected_sample_list) == 0 or len(self.upb_analysis_ids) == 0:
            logger_setup.get_logger().info("No analyses selected to update")
            self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")
            return
        elif len(checked_ids) > 1:
            logger_setup.get_logger().critical(f"More than one checked value for {field}")
            self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")
            return
        elif len(checked_ids) == 1:
            # Should only be one checked value
            logger_setup.get_logger().info(
                f"Updating {field} to {checked_ids[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
            create_savepoint('before_upb_update')
            query = QtS.QSqlQuery()
            query.prepare(
                f"UPDATE UPbAnalyses SET {field} = {checked_ids[0]} WHERE UPbAnalysisID {query_where_string}")
            if not query.exec():
                logger_setup.get_logger().critical(
                    f"Failed to update {field} to {checked_ids[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                rollback_savepoint('before_upb_update')
                self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(
                f"Updated {field} to {checked_ids[0]} for {len(self.upb_analysis_ids)} UPb Analyses in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            logger_setup.get_logger().info(
                f"Updated {field} to {checked_ids[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
            release_savepoint('before_upb_update')
        elif len(checked_ids) == 0 and len(partially_checked_ids) == 0:
            logger_setup.get_logger().info(f"Updating all {table} to unchecked")
            create_savepoint('before_upb_update')
            query = QtS.QSqlQuery()
            query.prepare(
                f"UPDATE UPbAnalyses SET {field} = Null WHERE UPbAnalysisID {query_where_string}")
            if not query.exec():
                logger_setup.get_logger().critical(
                    f"Failed to update {field} to Null for {len(self.upb_analysis_ids)} UPb Analyses")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                rollback_savepoint('before_upb_update')
                self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(
                f"Updated {field} to Null for UPbAnalysisID {self.upb_analysis_ids} in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            # logger_setup.get_logger().info(f"Updated {field} to Null for {len(self.upb_analysis_ids)} UPb Analyses")
            release_savepoint('before_upb_update')
        self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")
            
    def update_subfield(self, field: str, text: str):
        logger_setup.get_logger().info(f"Update field called with {field} and {text}")
        self.loading_manager.show_loading_dialog("Updating", f"Updating {field}")
        start_update_field_time = time.time()
        if text != "-":
            if len(self.upb_analysis_ids) > 0:
                logger_setup.get_logger().info(f"Updating {field} to {text} for {len(self.selected_sample_list)} samples and {len(self.upb_analysis_ids)} UPb Analyses")
                query = QtS.QSqlQuery()
                create_savepoint('before_upb_update')
                for upb_analysis_id in self.upb_analysis_ids:
                    if not query.exec(f"SELECT {field} FROM UPbAnalyses WHERE UPbAnalysisID = {upb_analysis_id}"):
                        logger_setup.get_logger().critical(f"Failed to select {field} for {len(self.upb_analysis_ids)} UPb Analyses")
                        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                        self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")
                        return
                    query.next()
                    if query.value(0) != text:
                        logger_setup.get_logger().info(f"Updating {field} to {text} for UPbAnalysisID {upb_analysis_id}")
                        if text is None or text == '':
                            text = 'Null'
                        if not query.exec(f"UPDATE UPbAnalyses SET {field} = {text} WHERE UPbAnalysisID = {upb_analysis_id}"):
                            logger_setup.get_logger().critical(f"Failed to update {field} to {text} for {len(self.upb_analysis_ids)} UPb Analyses")
                            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                            rollback_savepoint('before_upb_update')
                            self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")
                            return
                        update_modified_timestamp('UPbAnalyses', [upb_analysis_id])
                self.updated = True
                end_update_field_time = time.time()
                logger_setup.get_logger().info(
                    f"Updated field in {end_update_field_time - start_update_field_time} seconds")
                logger_setup.get_logger().info(f"Updated {field} to {text} for {len(self.upb_analysis_ids)} UPb analyses")
                release_savepoint('before_upb_update')
            else:
                logger_setup.get_logger().info("No samples selected")
        self.loading_manager.close_loading_dialog("Updating", f"Updating {field}")

    def update_fields(self):
        try:
            self.spot_size_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        # Fill in information based on selected samples
        self.populate_dropdowns()
        self.populate_fields()
        self.spot_size_lineEdit.editingFinished.connect(lambda: self.update_subfield('SpotSize', self.spot_size_lineEdit.text()))

    def add_popup(self, action: QtG.QAction | None = None):
        combo = self.sender()
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        dlg = None
        if table in SQLUtils.user_viewable_trees:
            save_expanded_state(table, combo.model(), combo.view())
            dlg_args = add_tree_popup(combo.view(), combo.model(), action)
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
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})
            if isinstance(combo, CheckableTreeCombobox):
                restore_expanded_state(table, combo.model(), combo.view())

    def edit_popup(self, action: QtG.QAction | None = None):
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
        if self.updated:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setText('Are you sure you want to discard all changes?')
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                logger_setup.get_logger().info("Discarding changes")
                rollback_savepoint('before_upb_edit')
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
        if self.updated:
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
        release_savepoint('before_upb_edit')
        # save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView, self.settings)
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            if self.updated:
                self.discard_question()
                event.ignore()
            else:
                logger_setup.get_logger().info("Closing EditUPbTags dialog")
                event.accept()
        else:
            logger_setup.get_logger().info("Closing EditUPbTags dialog")
            event.accept()
