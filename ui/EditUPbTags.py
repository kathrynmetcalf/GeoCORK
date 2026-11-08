import os
import sys
import time

# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import QSortFilterProxyModel

from PyQt6.uic import loadUi

import logger_setup

import Functions.SQLUtils as SQLUtils

from Functions.Widget_classes import (
    SQLiteTableModel, CheckableSqlQueryModel,
    CheckableSqlTableModel, get_name_column, CheckableTreeModel, TreeModel, populate_many_combo_checks,
    find_current_sub_items, populate_combo_box, add_tree_popup, CheckableTreeCombobox,
    CheckableComboBox, find_tree_model, populate_model_checks, populate_tree_model_checks, save_expanded_state,
    restore_expanded_state, get_name_from_id, get_id_from_name, get_view_from_table, TreeSortFilterProxyModel,
    CheckableTreeView, LazyCheckableTreeModel, show_loading_dialog, close_loading_dialog
)
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import SettingsManager
from ui.EditView import EditView

settings = SettingsManager().settings
from Functions.Database_views import ViewQuery
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
        self.sample_id_list = sample_id_list if sample_id_list is not None else []
        aliquot_ids, grain_ids, spot_ids, upb_analysis_ids = find_current_sub_items(self.sample_id_list, 'Samples')
        self.upb_analysis_ids = upb_analysis_ids
        if len(self.upb_analysis_ids) == 0 or len(self.sample_id_list) == 0:
            logger_setup.get_logger().error("No UPb Analyses for selected samples")
            self.close()
        self.selected_sample_label: QtW.QLabel
        self.selected_sample_label.setWordWrap(True)
        self.sample_name_list = [get_name_from_id('Samples', sample_id) for sample_id in self.sample_id_list]
        self.selected_sample_label.setText(f"Selected Samples: {', '.join(self.sample_name_list)}")

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

        close_loading_dialog("Loading", "Showing U-Pb analysis edit dialog")
        logger_setup.get_logger().info("U-Pb analysis edit dialog initialized in {} seconds".format(time.time() - start_init_time))

    def populate_dropdowns(self):
        self.reference_comboBox.model_modifiable = True
        self.reference_comboBox.enable_context_menu(True)
        reference_columns = settings.value('reference_view_columns')
        query_args = {'show_columns': reference_columns}
        view_query = ViewQuery('References', False, **query_args)
        table_query = view_query.table_query
        populate_combo_box(self.reference_comboBox, **{'table': 'References', 'query': table_query, 'column': 'ReferenceDisplay'})
        self.analysis_method_comboBox.model_modifiable = True
        self.analysis_method_comboBox.enable_context_menu(True)
        populate_combo_box(self.analysis_method_comboBox, **{'table': 'UPbAnalysisMethods'})
        self.lab_facility_comboBox.model_modifiable = True
        self.lab_facility_comboBox.enable_context_menu(True)
        populate_combo_box(self.lab_facility_comboBox, **{'table': 'LabFacilities'})
        self.instrument_comboBox.model_modifiable = True
        self.instrument_comboBox.enable_context_menu(True)
        populate_combo_box(self.instrument_comboBox, **{'table': 'Instruments'})
        self.analysis_context_comboBox.model_modifiable = True
        self.analysis_context_comboBox.enable_context_menu(True)
        populate_combo_box(self.analysis_context_comboBox, **{'table': 'UPbAnalysisContexts'})
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
        self.analysis_context_comboBox.closing.connect(lambda: self.update_many_id('UPbAnalysisContextID'))
        self.analysis_context_comboBox.add_triggered.connect(self.add_popup)
        self.analysis_context_comboBox.edit_triggered.connect(self.edit_popup)
        self.ratio_error_format_comboBox.closing.connect(lambda: self.update_subfield_id('RatioErrorFormatID'))
        self.age_error_format_comboBox.closing.connect(lambda: self.update_subfield_id('AgeErrorFormatID'))
        self.age_unit_comboBox.closing.connect(lambda: self.update_subfield_id('AgeUnitID'))
        self.concordance_format_comboBox.closing.connect(lambda: self.update_subfield_id('ConcordanceFormatID'))
        self.spot_size_unit_comboBox.closing.connect(lambda: self.update_subfield_id('SpotSizeUnitID'))
        self.spot_size_lineEdit.editingFinished.connect(lambda: self.update_subfield('SpotSize', self.spot_size_lineEdit.text()))
        
        logger_setup.get_logger().info("Signals connected")

    def populate_fields(self):
        logger_setup.get_logger().info("Populating fields")
        show_loading_dialog("Loading", "Populating fields")
        start_populate_fields_time = time.time()

        populate_model_checks(self.reference_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'ReferenceID')
        self.reference_comboBox.set_single_click(True)
        populate_model_checks(self.analysis_method_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'UPbAnalysisMethodID')
        self.analysis_method_comboBox.set_single_click(True)
        populate_model_checks(self.lab_facility_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'LabFacilityID')
        self.lab_facility_comboBox.set_single_click(True)
        populate_model_checks(self.instrument_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'InstrumentID')
        self.instrument_comboBox.set_single_click(True)
        populate_model_checks(self.ratio_error_format_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'RatioErrorFormatID')
        self.ratio_error_format_comboBox.set_single_click(True)
        populate_model_checks(self.age_error_format_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'AgeErrorFormatID')
        self.age_error_format_comboBox.set_single_click(True)
        populate_model_checks(self.age_unit_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'AgeUnitID')
        self.age_unit_comboBox.set_single_click(True)
        populate_model_checks(self.concordance_format_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'ConcordanceFormatID')
        self.concordance_format_comboBox.set_single_click(True)
        populate_model_checks(self.spot_size_unit_comboBox.model(), self.upb_analysis_ids, 'UPbAnalyses', 'SpotSizeUnitID')
        self.spot_size_unit_comboBox.set_single_click(True)
        populate_many_combo_checks('UPbAnalyses_UPbAnalysisContexts', self.analysis_context_comboBox, self.upb_analysis_ids)
        self.analysis_context_comboBox.set_single_click(False)

        close_loading_dialog("Loading", "Populating fields")

    def update_subfield_id(self, field: str):
        combo = self.sender()
        if isinstance(combo, CheckableTreeCombobox):
            model, indexes = find_tree_model(combo.model(), None)
            table = model.table
            column = get_name_column(table)
        else:
            model = combo.model()
            if isinstance(model, QSortFilterProxyModel):
                model = model.sourceModel()
            table = model.tableName()
            column = get_name_column(table)
        logger_setup.get_logger().info(f"update_subfield_id called with {table}")
        show_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
        start_update_sub_tags_time = time.time()
        # UPbAnalyses have only one value for each field, so only one value should be checked
        # If there are still partial checks, then nothing should be updated
        checked_ids = model.checked_ids
        partially_checked_ids = model.partially_checked_ids
        if len(self.upb_analysis_ids) > 1:
            query_where_string = f"IN {tuple(self.upb_analysis_ids)}"
        elif len(self.upb_analysis_ids) == 1:
            query_where_string = f"= {self.upb_analysis_ids[0]}"
        else:
            query_where_string = ""
        if len(self.sample_id_list) == 0 or len(self.upb_analysis_ids) == 0:
            logger_setup.get_logger().info("No analyses selected to update")
            close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
            return
        elif len(checked_ids) > 1:
            logger_setup.get_logger().critical(f"More than one checked value for {field.split('ID')[0]}")
            close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
            return
        elif len(checked_ids) == 1:
            # Should only be one checked value
            logger_setup.get_logger().info(
                f"Updating {field} to {list(checked_ids)[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
            create_savepoint('before_upb_update')
            query = QtS.QSqlQuery()
            query.prepare(
                f"UPDATE UPbAnalyses SET {field} = {list(checked_ids)[0]} WHERE UPbAnalysisID {query_where_string}")
            if not query.exec():
                logger_setup.get_logger().critical(
                    f"Failed to update {field} to {list(checked_ids)[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                rollback_savepoint('before_upb_update')
                close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(
                f"Updated {field} to {list(checked_ids)[0]} for {len(self.upb_analysis_ids)} UPb Analyses in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            logger_setup.get_logger().info(
                f"Updated {field} to {list(checked_ids)[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
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
                close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(
                f"Updated {field} to Null for UPbAnalysisID {self.upb_analysis_ids} in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            # logger_setup.get_logger().info(f"Updated {field} to Null for {len(self.upb_analysis_ids)} UPb Analyses")
            release_savepoint('before_upb_update')
        close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
            
    def update_subfield(self, field: str, text: str):
        logger_setup.get_logger().info(f"Update field called with {field} and {text}")
        show_loading_dialog("Updating", f"Updating {field}...")
        start_update_field_time = time.time()
        if text != "-":
            if len(self.upb_analysis_ids) > 0:
                logger_setup.get_logger().info(f"Updating {field} to {text} for {len(self.sample_name_list)} samples and {len(self.upb_analysis_ids)} UPb Analyses")
                query = QtS.QSqlQuery()
                create_savepoint('before_upb_update')
                for upb_analysis_id in self.upb_analysis_ids:
                    if not query.exec(f"SELECT {field} FROM UPbAnalyses WHERE UPbAnalysisID = {upb_analysis_id}"):
                        logger_setup.get_logger().critical(f"Failed to select {field} for {len(self.upb_analysis_ids)} UPb Analyses")
                        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                        close_loading_dialog("Updating", f"Updating {field}...")
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
                            close_loading_dialog("Updating", f"Updating {field}...")
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
        close_loading_dialog("Updating", f"Updating {field}...")

    def update_many_id(self, field: str):
        combo = self.sender()
        if isinstance(combo, CheckableTreeCombobox):
            model, indexes = find_tree_model(combo.model(), None)
            table = model.table
            column = get_name_column(table)
        else:
            model = combo.model()
            if isinstance(model, QSortFilterProxyModel):
                model = model.sourceModel()
            table = model.tableName()
            column = get_name_column(table)
        logger_setup.get_logger().info(f"update_many_id called with {table}")
        show_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
        start_update_sub_tags_time = time.time()
        many_table = 'UPbAnalyses_UPbAnalysisContexts'
        update = model.update_many_table(many_table, self.upb_analysis_ids)
        if update == 'False':
            logger_setup.get_logger().critical(f"Failed to update {field.split('ID')[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
            close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
            return
        elif update == 'No':
            logger_setup.get_logger().info("No changes")
            close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")
            return
        else:
            logger_setup.get_logger().info(f"Updated {field} for {len(self.upb_analysis_ids)} UPb Analyses")
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(
                f"Updated {field} for {len(self.upb_analysis_ids)} UPb Analyses in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
        close_loading_dialog("Updating", f"Updating {field.split('ID')[0]}...")

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
        try:
            model = combo.source_model()
        except AttributeError:
            model = combo.model()
        if isinstance(combo.view(), QtW.QTreeView):
            if not isinstance(model, TreeModel):
                model, indexes = find_tree_model(model, None)
            if model:
                table = model.table
            else:
                logger_setup.get_logger().critical(f"Error adding item")
                logger_setup.get_logger().debug(f"Error: No tree model found")
                return
        elif isinstance(model, QtC.QSortFilterProxyModel):
            model = model.sourceModel()
            table = model.tableName()
        else:
            table = model.tableName()
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
            return
        logger_setup.get_logger().info(f"Showing {table} add dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Update this combo box
            if get_view_from_table(table) != table:
                # This should use a more complex query for a view
                show_columns = SQLUtils.view_setting_dict[get_view_from_table(table)]
                query_args = {'show_columns': show_columns}
                view_query = ViewQuery(table, False, **query_args)
                table_query = view_query.table_query
                name_header = show_columns[get_name_column(get_view_from_table(table))]
                populate_combo_box(combo, **{'table': table, 'query': table_query,'column': name_header})
            else:
                populate_combo_box(combo, **{'table': table})

    def edit_popup(self, action: QtG.QAction | None = None):
        combo = self.sender()
        try:
            model = combo.source_model()
        except AttributeError:
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
            table = model.tableName()
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(self, table)
        elif table != get_view_from_table(table):
            dlg = EditView(self, table)
        else:
            dlg = EditTable(self, table)
        if dlg is None:
            return
        logger_setup.get_logger().info(f"Showing {table} edit dialog")
        if dlg.exec() == QtW.QDialog.DialogCode.Accepted:
            self.updated = True
            # Update this combo box
            populate_combo_box(combo, **{'table': table})

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
                self.updated = False
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
        # save_expanded_state(self.table, self.edit_treeView, self.settings)
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
