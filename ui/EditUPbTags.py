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
    show_column, set_comboBox_text, find_upb_from_samples, populate_combo_box, add_tree_popup, CheckableTreeCombobox, find_tree_model
)
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import settings
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
        self.parent_window = parent_window
        self.savepoint_manager = SavepointManager.get_instance()
        self.setWindowTitle("Edit U-Pb Information")
        self.setModal(True)
        # self.loadWindowState()

        sources_ui_file = "ui/EditUPbTags.ui"
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

        label_text = self.label.text()
        label_text = label_text.replace("#", str(len(self.upb_analysis_ids)))
        self.label.setText(label_text)

        # self.reference_model = CheckableSqlQueryModel()
        # self.analysis_method_model = QtS.QSqlTableModel()
        # self.analysis_method_tree = CheckableTreeModel()
        # self.lab_facility_model = CheckableSqlTableModel()
        # self.instrument_model = CheckableSqlTableModel()
        # self.ratio_error_format_model = CheckableSqlTableModel()
        # self.age_error_format_model = CheckableSqlTableModel()
        # self.concordance_format_model = CheckableSqlTableModel()
        # self.spot_size_unit_model = CheckableSqlTableModel()

        self.msg = QtW.QMessageBox(self)
        create_savepoint('before_upb_edit')
        self.close_by_dialog = False

        # Fill in information based on selected samples
        self.populate_dropdowns()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.populate_fields()
        # self.increment_progress_dialog(self.init_progress_dialog)
        self.connect_signals()

        self.updated = False

    def populate_dropdowns(self):
        # self.reference_model.setQuery(f'SELECT * FROM ReferenceView')
        # if self.reference_model.lastError().text():
        #     logger_setup.get_logger().critical(
        #         f"Error setting reference model query: {self.reference_model.lastError().text()}")
        # self.analysis_method_model = set_table(self.analysis_method_model, 'UPbAnalysisMethods')
        # self.analysis_method_tree.setSourceModel(self.analysis_method_model)
        # self.lab_facility_model = set_table(self.lab_facility_model, 'LabFacilities')
        # self.instrument_model = set_table(self.instrument_model, 'Instruments')
        # self.ratio_error_format_model = set_table(self.ratio_error_format_model, 'ErrorFormats')
        # self.age_error_format_model = set_table(self.age_error_format_model, 'ErrorFormats')
        # self.concordance_format_model = set_table(self.concordance_format_model, 'ConcordanceFormats')
        # self.spot_size_unit_model = set_table(self.spot_size_unit_model, 'DistanceUnits')

        self.reference_comboBox.model_modifiable = True
        self.reference_comboBox.enable_context_menu(True)
        populate_combo_box(self.reference_comboBox, **{'table': 'ReferenceView'})
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
        populate_combo_box(self.concordance_format_comboBox, **{'table': 'ConcordanceFormats', 'column': 'ConcordanceFormatAbbreviation'})
        populate_combo_box(self.spot_size_unit_comboBox, **{'table': 'DistanceUnits', 'column': 'DistanceUnitAbbreviation'})
        

    def connect_signals(self):
        logger_setup.get_logger().info("Connecting signals")
        # Connect signals and slots
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)

        self.reference_comboBox.closing.connect(lambda: self.update_subfield_id(self.reference_model, 'ReferenceID'))
        self.reference_comboBox.add_triggered.connect(self.add_popup)
        self.reference_comboBox.edit_triggered.connect(self.edit_popup)
        self.analysis_method_comboBox.closing.connect(lambda: self.update_sub_tags(self.analysis_method_tree))
        self.analysis_method_comboBox.add_triggered.connect(self.add_popup)
        self.analysis_method_comboBox.edit_triggered.connect(self.edit_popup)
        self.lab_facility_comboBox.closing.connect(
            lambda: self.update_subfield_id(self.lab_facility_model, 'LabFacilityID'))
        self.lab_facility_comboBox.add_triggered.connect(self.add_popup)
        self.lab_facility_comboBox.edit_triggered.connect(self.edit_popup)
        self.instrument_comboBox.closing.connect(lambda: self.update_subfield_id(self.instrument_model, 'InstrumentID'))
        self.instrument_comboBox.add_triggered.connect(self.add_popup)
        self.instrument_comboBox.edit_triggered.connect(self.edit_popup)
        self.ratio_error_format_comboBox.closing.connect(lambda: self.update_subfield_id(self.ratio_error_format_model, 'RatioErrorFormatID'))
        self.age_error_format_comboBox.closing.connect(lambda: self.update_subfield_id(self.age_error_format_model, 'AgeErrorFormatID'))
        self.concordance_format_comboBox.closing.connect(lambda: self.update_subfield_id(self.concordance_format_model, 'ConcordanceFormatID'))
        self.spot_size_unit_comboBox.closing.connect(lambda: self.update_subfield_id(self.spot_size_unit_model, 'SpotSizeUnitID'))
        self.spot_size_lineEdit.editingFinished.connect(lambda: self.update_subfield('SpotSize', self.spot_size_label.text()))
        
        logger_setup.get_logger().info("Signals connected")

    def populate_fields(self):
        logger_setup.get_logger().info("Populating fields")
        start_populate_fields_time = time.time()
        

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
        
    def populate_upb_checks(self, combo: QtW.QComboBox):
        start_populate_upb_checks_time = time.time()
        all_items = []
        some_items = []
        text = ""
        if isinstance(combo, CheckableTreeCombobox):
            model = find_tree_model(combo.model())
            table = model.table
            col = 0  # Name column is always placed in the first column
            tag_id_header = model.source_model.record().fieldName(0)
            id_col = 1  # ID column is always placed in the second column
        else:
            model = combo.model()
            table = model.tableName()
            try:
                view = model.tableView()
                col = get_view_name_column(view)
            except AttributeError:
                col = get_name_column(model.tableName())
            tag_id_header = model.record().fieldName(0)
            id_col = 0  # ID column is always in the first column
        logger_setup.get_logger().info(f"Populating UPb checks for {table}")
        # Already checked if no analyses are selected
        if isinstance(combo, CheckableTreeCombobox):
            model.blockSignals(True)
            # recursively check data
            def check_data(model: CheckableTreeModel, index: QtC.QModelIndex):
                for row in range(model.rowCount(index)):
                    model_index = model.index(row, col, index)
                    id_index = model.index(row, id_col, index)
                    tag_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
                    upb_analysis_table = SQLiteTableModel(
                        f"SELECT * FROM UPbAnalyses WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)} AND {tag_id_header} = {tag_id}")
                    if upb_analysis_table.rowCount() == len(self.upb_analysis_ids):
                        # All samples have this tag
                        model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                        all_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                    elif upb_analysis_table.rowCount() > 0:
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
                tag_id = model.index(row, 0).data()
                upb_analysis_table = SQLiteTableModel(f"SELECT * FROM UPbAnalyses WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)} AND {tag_id_header} = {tag_id}")
                index = model.index(row, col)
                if upb_analysis_table.rowCount() == len(self.upb_analysis_ids):
                    # All analyses have this tag
                    model.setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if model.lastError().text():
                        logger_setup.get_logger().critical(f"Error setting checked for {model.tableName()}: {model.lastError().text()}")
                    all_items.append(model.data(index, QtC.Qt.ItemDataRole.DisplayRole))
                elif upb_analysis_table.rowCount() > 0:
                    # Some samples have this tag
                    model.setData(index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if model.lastError().text():
                        logger_setup.get_logger().critical(f"Error setting partial checked for {model.tableName()}: {model.lastError().text()}")
                    some_items.append(model.data(index, QtC.Qt.ItemDataRole.DisplayRole))
                else:
                    # No samples have this tag
                    model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
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
        if text == "":
            text = combo.placeholderText()
        combo.setCurrentText(text)
        end_populate_upb_checks_time = time.time()
        logger_setup.get_logger().info(f"Populated UPb checks for {model.tableName()} in {end_populate_upb_checks_time - start_populate_upb_checks_time} seconds")

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
                column = get_name_column(model.tableName())
            for row in range(model.rowCount()):
                name_index = model.index(row, column)
                id_index = model.index(row, 0)
                if model.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                    checked_item_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
                    break
            logger_setup.get_logger().info(f"Updating {field} to {checked_item_id} for {len(self.upb_analysis_ids)} UPb Analyses")
            create_savepoint('before_upb_update')
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
            release_savepoint('before_upb_update')
        else:
            logger_setup.get_logger().info("No UPbAnalyses for selected samples")
            
    def update_subfield(self, field: str, text: str):
        logger_setup.get_logger().info(f"Update field called with {field} and {text}")
        start_update_field_time = time.time()
        if text != "-":
            if len(self.upb_analysis_ids) > 0:
                logger_setup.get_logger().info(f"Updating {field} to {text} for {len(self.selected_sample_list)} samples and {len(self.upb_analysis_ids)} UPb Analyses")
                query = QtS.QSqlQuery()
                create_savepoint('before_upb_update')
                for upb_analysis_id in self.upb_analysis_ids:
                    if not query.exec(f"SELECT {field} FROM UPbAnalyses WHERE UPbAnalysisID = {upb_analysis_id}"):
                        logger_setup.get_logger().critical(f"Failed to select {field} for UPbAnalysisID {upb_analysis_id}: {query.lastError().text()}")
                        return
                    query.next()
                    if query.value(0) != text:
                        logger_setup.get_logger().info(f"Updating {field} to {text} for UPbAnalysisID {upb_analysis_id}")
                        if text is None or text == '':
                            text = 'Null'
                        if not query.exec(f"UPDATE UPbAnalyses SET {field} = {text} WHERE UPbAnalysisID = {upb_analysis_id}"):
                            logger_setup.get_logger().critical(f"Failed to update {field} to {text} for UPbAnalysisID {upb_analysis_id}: {query.lastError().text()}")
                            rollback_savepoint('before_upb_update')
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
            
    def update_sub_tags(self, model: CheckableTreeModel):
        logger_setup.get_logger().info(f"update_tags called with {model.table}")
        table = model.table
        combo = self.sender()
        if not combo.treeView.model_edited:
            logger_setup.get_logger().info(f"No changes to {table}")
            return
        start_update_sub_tags_time = time.time()
        field = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If there are still partial checks, then nothing should be updated
        checked_ids, partially_checked_ids = model.traverse_checkable_tree(QtC.QModelIndex())
        if len(self.selected_sample_list) == 0:
            logger_setup.get_logger().info("No samples selected")
            return
        elif len(checked_ids) > 1:
            logger_setup.get_logger().critical(f"More than one checked value for {field}")
            return
        elif len(checked_ids) == 1:
            # Should only be one checked value
            logger_setup.get_logger().info(f"Updating {field} to {checked_ids[0]} for {len(self.upb_analysis_ids)} UPb Analyses")
            create_savepoint('before_upb_update')
            query = QtS.QSqlQuery()
            if len(self.upb_analysis_ids) > 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = {checked_ids[0]} WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)}")
            if len(self.upb_analysis_ids) == 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = {checked_ids[0]} WHERE UPbAnalysisID = {self.upb_analysis_ids[0]}")
            if not query.exec():
                logger_setup.get_logger().critical(f"Failed to update {field} to {checked_ids[0]} for UPbAnalysisID {self.upb_analysis_ids}: {query.lastError().text()}")
                rollback_savepoint('before_upb_update')
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(f"Updated {field} to {checked_ids[0]} for UPbAnalysisID {self.upb_analysis_ids} in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            logger_setup.get_logger().info(f"Updated {field} to {checked_ids[0]} for UPbAnalysisID {self.upb_analysis_ids}")
            release_savepoint('before_upb_update')
        elif len(checked_ids) == 0 and len(partially_checked_ids) == 0:
            logger_setup.get_logger().info(f"Updating all {table} to unchecked")
            create_savepoint('before_upb_update')
            query = QtS.QSqlQuery()
            if len(self.upb_analysis_ids) > 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = Null WHERE UPbAnalysisID in {tuple(self.upb_analysis_ids)}")
            if len(self.upb_analysis_ids) == 1:
                query.prepare(
                    f"UPDATE UPbAnalyses SET {field} = Null WHERE UPbAnalysisID = {self.upb_analysis_ids[0]}")
            if not query.exec():
                logger_setup.get_logger().critical(f"Failed to update {field} to Null for UPbAnalysisID {self.upb_analysis_ids}: {query.lastError().text()}")
                rollback_savepoint('before_upb_update')
                return
            update_modified_timestamp('UPbAnalyses', self.upb_analysis_ids)
            self.updated = True
            end_update_sub_tags_time = time.time()
            logger_setup.get_logger().info(
                f"Updated {field} to Null for UPbAnalysisID {self.upb_analysis_ids} in {end_update_sub_tags_time - start_update_sub_tags_time} seconds")
            logger_setup.get_logger().info(f"Updated {field} to Null for UPbAnalysisID {self.upb_analysis_ids}")
            release_savepoint('before_upb_update')

    def update_fields(self):
        try:
            self.spot_size_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        # Fill in information based on selected samples
        self.populate_dropdowns()
        self.populate_fields()
        self.spot_size_lineEdit.editingFinished.connect(lambda: self.update_subfield('SpotSize', self.spot_size_label.text()))

    def add_popup(self, action: QtG.QAction | None = None):
        combo = self.sender()
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        if table in SQLUtils.user_viewable_trees:
            view = combo.view()
            dlg = AddTreeTags(table, action.text(), view)
        elif table == '"References"' or table == 'References':
            dlg = NewReference()
        else:
            dlg = AddTags(table)
        if dlg is None:
            return
        dlg.exec()
        self.update_fields()

    def edit_popup(self, action: QtG.QAction | None = None):
        combo = self.sender()
        if isinstance(combo.model(), TreeModel):
            table = combo.model().table
        else:
            table = combo.model().tableName()
        if table in SQLUtils.user_viewable_trees:
            dlg = EditTree(table)
        else:
            dlg = EditTable(table)
        if dlg is None:
            return
        dlg.exec()
        self.update_fields()

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
        # Edit occurred in the dialog, so update the database
        update_database()
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
