import sys
import time

# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS

from PyQt6.uic import loadUi
from pandas.plotting import table

import Functions.Create_database as Create_db
import Functions.Table_classes as TbC
import Functions.Tree_classes as TrC
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import Functions.Database_views as DB_views
import ui.import_wizard
import ui.New_reference
from Functions.Alter_database import release_savepoint
from Functions.Table_classes import CheckableSqlTableModel, SampleAgeTableModel, set_table, FontDelegate
from ui.EditSampleTable import EditSampleTable
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.Filters import QueryBuilder
from Functions.Tree_classes import TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import settings
from ui.GPSFields import GPSFields
from ui.AgeFields import AgeFields


# todo: Figure out why it is slowing down after checking and unchecking a bunch of stuff

class SampleInformation(QtW.QDialog):
    def __init__(self, parent_window, sample_id_list: list | None):
        super().__init__(parent=parent_window)
        self.parent_window = parent_window
        self.savepoint_manager = SavepointManager.get_instance()
        # self.loadWindowState()

        sources_ui_file = "ui/SampleInformation.ui"
        loadUi(sources_ui_file, self)
        self.gps = GPSFields('Samples', sample_id_list)
        self.selected_gps_column_verticalLayout: QtW.QVBoxLayout
        self.selected_gps_column_verticalLayout.insertWidget(2, self.gps)
        self.age = AgeFields('Samples', sample_id_list)
        self.name_igsn_age_verticalLayout = QtW.QVBoxLayout()
        self.gridLayout_2.addWidget(self.age, 2, 0, 2, 4)

        # Sample names table
        self.sample_names_model = CheckableSqlTableModel()  # The one used to populate the dropdown checkbox of samples to edit, shows only name and description
        self.sample_names_model = self.set_table(self.sample_names_model, 'Samples')
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

        # Sample information models
        self.samples_table = QtS.QSqlQueryModel()
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
        self.reference_model = CheckableSqlTableModel()
        self.upb_analysis_method_model = QtS.QSqlTableModel()
        self.concordance_type_model = QtS.QSqlTableModel()

        self.gps_location_ids = ""

        self.msg = QtW.QMessageBox(self)
        create_savepoint('before_edit')
        self.close_by_dialog = False

        # Fill in information based on selected samples
        self.populate_dropdowns()
        self.check_all_samples()
        self.sample_name_comboBox.setModel(self.sample_names_model)
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)

        self.installEventFilter(self)

    def check_all_samples(self):
        if len(self.selected_sample_list) > 0:
            for row in range(self.sample_names_model.rowCount()):
                index = self.sample_names_model.index(row, 1, QtC.QModelIndex())
                self.sample_names_model.setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            self.update_sample_list()
        else:
            self.uncheck_all_samples()

    def uncheck_all_samples(self):
        for row in range(self.sample_names_model.rowCount()):
            index = self.sample_names_model.index(row, 1, QtC.QModelIndex())
            self.sample_names_model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        self.update_sample_list()

    def update_sample_list(self):
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
        self.disconnect_text_signals()
        # self.populate_age_dropdown()
        self.populate_fields()
        self.connect_signals()

    def populate_dropdowns(self):
        self.column_model = self.set_table(self.column_model, 'Columns')
        self.column_unit_model = self.set_table(self.column_unit_model, 'DistanceUnits')
        self.sample_context_model = self.set_table(self.sample_context_model, 'SampleContexts')
        self.sample_context_tree.setSourceModel(self.sample_context_model)
        self.sampling_method_model = self.set_table(self.sampling_method_model, 'SamplingMethods')
        self.sampling_method_tree.setSourceModel(self.sampling_method_model)
        self.unit_model = self.set_table(self.unit_model, 'Units')
        self.unit_tree.setSourceModel(self.unit_model)
        self.rock_type_model = self.set_table(self.rock_type_model, 'RockTypes')
        self.rock_type_tree.setSourceModel(self.rock_type_model)
        self.region_model = self.set_table(self.region_model, 'Regions')
        self.region_tree.setSourceModel(self.region_model)
        self.setting_model = self.set_table(self.setting_model, 'Settings')
        self.setting_tree.setSourceModel(self.setting_model)
        self.age_signature_model = self.set_table(self.age_signature_model, 'AgeSignatures')
        self.age_signature_tree.setSourceModel(self.age_signature_model)
        self.reference_model = self.set_table(self.reference_model, '"References"')
        self.analysis_method_model = self.set_table(self.analysis_method_model, 'UPbAnalysisMethods')
        self.analysis_method_tree.setSourceModel(self.analysis_method_model)
        self.lab_facility_model = self.set_table(self.lab_facility_model, 'LabFacilities')
        self.instrument_model = self.set_table(self.instrument_model, 'Instruments')


        self.column_name_comboBox.setModel(self.column_model)
        TbC.show_column(self.column_name_comboBox, 'ColumnName')
        self.height_depth_unit_comboBox.setModel(self.column_unit_model)
        TbC.show_column(self.height_depth_unit_comboBox, 'DistanceUnitAbbreviation')
        self.sample_context_comboBox.setModel(self.sample_context_tree)
        self.sampling_method_comboBox.setModel(self.sampling_method_tree)
        self.unit_comboBox.setModel(self.unit_tree)
        self.rock_type_comboBox.setModel(self.rock_type_tree)
        self.region_comboBox.setModel(self.region_tree)
        self.setting_comboBox.setModel(self.setting_tree)
        self.age_signature_comboBox.setModel(self.age_signature_tree)
        self.reference_comboBox.setModel(self.reference_model)
        TbC.show_column(self.reference_comboBox, 'ReferenceDisplay')
        self.analysis_method_comboBox.setModel(self.analysis_method_tree)
        self.lab_facility_comboBox.setModel(self.lab_facility_model)
        self.instrument_comboBox.setModel(self.instrument_model)

        self.sample_name_comboBox: CheckableTreeCombobox
        self.sample_name_comboBox.view().setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.sample_name_comboBox.view().customContextMenuRequested.connect(self.show_context_menu)

    def set_table(self, model: QtS.QSqlTableModel, table: str):
        model.setTable(table)
        model.select()
        return model

    def connect_signals(self):
        # Connect signals and slots
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.sample_names_model.dataChanged.connect(self.update_sample_list)
        self.sample_igsn_lineEdit.editingFinished.connect(lambda: self.update_field('SampleIGSN', f'"{self.sample_igsn_lineEdit.text()}"'))
        # self.location_groupBox.focusLost.connect(self.update_gps)
        self.column_name_comboBox.currentTextChanged.connect(lambda: self.update_id('ColumnID', 'ColumnName', self.column_name_comboBox.currentText(), 'Columns'))
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
        self.sample_description_lineEdit.editingFinished.connect(lambda: self.update_field('SampleDescription', f'"{self.sample_description_lineEdit.text()}"'))

    def disconnect_text_signals(self):
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

    def populate_fields(self):
        sample_ifnull_query = DB_views.SampleIfNullQuery()
        sample_query_table = QtS.QSqlTableModel()
        self.set_table(sample_query_table, 'Samples')
        if len(self.checked_sample_list) > 1:
            self.samples_table.setQuery(f'{sample_ifnull_query} WHERE Samples.SampleID in {tuple(self.checked_sample_list)}')
        elif len(self.checked_sample_list) == 1:
            self.samples_table.setQuery(f'{sample_ifnull_query} WHERE Samples.SampleID = {self.checked_sample_list[0]}')
        else:
            self.samples_table.setQuery(f'{sample_ifnull_query}')
        if self.samples_table.lastError().text() != '':
            self.msg.critical(self, 'Error', self.samples_table.lastError().text(), QtW.QMessageBox.StandardButton.Ok)
            return
        text_values = []
        for col in range(self.samples_table.columnCount()):
            # If there is only one value concatenated in the column, add it to the list, otherwise add '-'
            text = self.samples_table.index(0, col).data()
            if type(text) == str and ',' in text:
                if len(text_values) == 23:
                    text_values.append(text)
                else:
                    text_values.append('-')
            elif text == 'Null':
                text_values.append('')
            else:
                text_values.append(text)
        if len(text_values) > 0:
            self.sample_igsn_lineEdit.setText(f"{text_values[1]}")
            TbC.set_comboBox_text(self.column_name_comboBox, text_values[3])
            self.height_depth_lineEdit.setText(f"{text_values[4]}")
            self.height_depth_error_lineEdit.setText(f"{text_values[5]}")
            TbC.set_comboBox_text(self.height_depth_unit_comboBox, text_values[6])
            self.sample_description_lineEdit.setText(text_values[7])

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

    def populate_checks(self, many_to_many_table: str, table_model: QtS.QSqlTableModel, tree: CheckableTreeModel = None):
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        tag_id_header = table_model.record().fieldName(0)
        items = []
        text = ""
        if len(self.checked_sample_list) == 0:
            # No samples selected, so uncheck everything
            for row in range(table_model.rowCount()):
                if tree is not None:
                    model = tree
                    col = TbC.name_column(table_model.tableName())
                    model_index = tree.mapFromSource(table_model.index(row, col))
                else:
                    model = table_model
                    col = TbC.name_column(table_model.tableName())
                    model_index = table_model.index(row, col)
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            return text
        for row in range(table_model.rowCount()):
            tag_id = table_model.index(row, 0).data()
            if len(self.checked_sample_list) > 1:
                many_to_many_model.setFilter(f"SampleID in {tuple(self.checked_sample_list)} AND {tag_id_header} = {tag_id}")
            else:
                many_to_many_model.setFilter(f"SampleID = {self.checked_sample_list[0]} AND {tag_id_header} = {tag_id}")
            if tree is not None:
                model = tree
                col = TbC.name_column(table_model.tableName())
                model_index = tree.mapFromSource(table_model.index(row, col))
            else:
                model = table_model
                col = TbC.name_column(table_model.tableName())
                model_index = table_model.index(row, col)
            if many_to_many_model.rowCount() == len(self.selected_sample_list):
                # All samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
            elif many_to_many_model.rowCount() > 0:
                # Some samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                # No samples have this tag
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        text = ", ".join(items)
        return text

    def populate_upb_checks(self, table_model):
        if table_model.tableName() == '"References"':
            # Display the ShortCitation
            col = 6
        elif "Format" or "Unit" in table_model.tableName():
            # Display the abbreviation
            col = 2
        else:
            # Display the Name
            col = 1
        upb_data_table = QtS.QSqlTableModel()
        upb_data_table.setTable('UPbData')
        upb_data_table.select()
        tag_id_header = table_model.record().fieldName(0)
        items = []
        text = ""
        if len(self.checked_sample_list) == 0:
            # No samples selected, so uncheck everything
            for row in range(table_model.rowCount()):
                index = table_model.index(row, col)
                table_model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            return text
        aliquot_ids, spot_ids, upb_data_ids = TbC.find_sub_items(self.checked_sample_list)
        if len(upb_data_ids) > 0:
            for row in range(table_model.rowCount()):
                tag_id = table_model.index(row, 0).data()
                upb_data_table.setFilter(f"UPbAnalysisID in {tuple(upb_data_ids)} AND {tag_id_header} = {tag_id}")
                index = table_model.index(row, col)
                if upb_data_table.rowCount() == len(upb_data_ids):
                    # All analyses have this tag
                    table_model.setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                    items.append(table_model.data(index, QtC.Qt.ItemDataRole.DisplayRole))
                elif upb_data_table.rowCount() > 0:
                    # Some samples have this tag
                    table_model.setData(index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    items.append(table_model.data(index, QtC.Qt.ItemDataRole.DisplayRole))
                else:
                    # No samples have this tag
                    table_model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            text = ", ".join(map(str, items))
            return text
        return text

    def show_context_menu(self, pos: QtC.QPoint):
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
                TbC.delete_samples(selected_indexes)

    def update_field(self, field: str, text: str):
        print(f"Update_field called with {field} and {text}")
        if text != "-":
            if len(self.checked_sample_list) > 0:
                query = QtS.QSqlQuery()
                create_savepoint('before_update')
                for sample_id in self.checked_sample_list:
                    if not query.exec(f"SELECT {field} FROM Samples WHERE SampleID = {sample_id}"):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        return
                    query.next()
                    if query.value(0) != text:
                        if text is None or text == '':
                            text = 'Null'
                        if not query.exec(f"UPDATE Samples SET {field} = {text} WHERE SampleID = {sample_id}"):
                            errtxt = query.lastError().text()
                            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                            rollback_savepoint('before_update')
                            return
                        update_modified_timestamp('Samples', [sample_id])
                release_savepoint('before_update')

    def update_id(self, id_field: str, name_field:str, text: str, table: str):
        print(f'Update_id called with {id_field}, {name_field}, {text}, {table}')
        table_model = QtS.QSqlTableModel()
        table_model.setTable(table)
        table_model.select()
        # table_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        table_model.setFilter(f"{name_field} is '{text}'")
        item_id = table_model.data(table_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if len(self.checked_sample_list) > 0:
            query = QtS.QSqlQuery()
            create_savepoint('before_update')
            for sample_id in self.checked_sample_list:
                if not query.exec(f"SELECT {id_field} FROM Samples WHERE SampleID = {sample_id}"):
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    return
                query.next()
                if query.value(0) != item_id:
                    if not query.exec(f"UPDATE Samples SET {id_field} = {item_id} WHERE SampleID = {sample_id}"):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
            update_modified_timestamp('Samples', self.checked_sample_list)
            release_savepoint('before_update')

    def update_subfield_id(self, model: CheckableSqlTableModel, field: str):
        print(f"update_subfield_id called with {model.tableName()} and {field}")
        aliquot_ids, spot_ids, upb_data_ids = TbC.find_sub_items(self.checked_sample_list)
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If nothing is fully checked, then nothing should be updated
        checked_item_id = None  # Should only be one
        if len(upb_data_ids) > 0:
            column = TbC.name_column(model.tableName())
            for row in range(model.rowCount()):
                name_index = model.index(row, column)
                id_index = model.index(row, 0)
                if model.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                    checked_item_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
            # todo: optimize update for thousands of analysis IDs
            # todo: figure out what other transaction is going on before beginning one for the updates
            create_savepoint('before_update')
            query_start_time = time.time()
            if model.database().transaction():
                query = QtS.QSqlQuery()
                query.setForwardOnly(True)
                if len(upb_data_ids) > 1:
                    print(len(upb_data_ids))
                    upb_data_ids.sort()
                    if not query.exec(f"UPDATE UPbData SET {field} = {checked_item_id} WHERE UPbAnalysisID in {tuple(upb_data_ids)[0:10]}"):
                        print(f"Failed to update {field} to {checked_item_id} for UPbAnalysisID {upb_data_ids[0:10]}")
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    update_modified_timestamp('UPbData', upb_data_ids[0:10])
                else:
                    if not query.exec(f"UPDATE UPbData SET {field} = {checked_item_id} WHERE UPbAnalysisID = {upb_data_ids[0]}"):
                        print(f"Failed to update {field} to {checked_item_id} for UPbAnalysisID {upb_data_ids[0]}")
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    update_modified_timestamp('UPbData', upb_data_ids[0])
                if model.database().commit():
                    print(f"Updated {field} to {checked_item_id} for UPbAnalysisID {upb_data_ids[0:10]}")
                    release_savepoint('before_update')
                else:
                    print(f"Failed to update {field} to {checked_item_id} for UPbAnalysisID {upb_data_ids[0:10]}")
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            query_end_time = time.time()
            print(f"Query time: {query_end_time - query_start_time}")
            release_savepoint('before_update')

    def update_sample_tags(self, model: TrC.CheckableTreeModel, table: str):
        print(f"update_tags called with {model.source_model.tableName()} and {table}")
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(f"Samples_{table}")
        many_to_many_model.select()

        if len(self.checked_sample_list) > 0:
            checked_ids , partially_checked_ids = model.traverse_checkable_tree(QtC.QModelIndex())
            create_savepoint('before_update')
            for sample_id in self.checked_sample_list:
                update = model.update_db(checked_ids, partially_checked_ids, sample_id)
                if update is False:
                    rollback_savepoint('before_update')
                    errtxt = update
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    return
            release_savepoint('before_update')

    def update_sub_tags(self, model: TrC.CheckableTreeModel, table: str):
        print(f"update_tags called with {model.source_model.tableName()} and {table}")
        field = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        aliquot_ids, spot_ids, upb_data_ids = TbC.find_sub_items(self.checked_sample_list)
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If nothing is fully checked, then nothing should be updated
        checked_ids, partially_checked_ids = model.traverse_checkable_tree(QtC.QModelIndex())
        if len(checked_ids) == 1:
            # Should only be one checked value
            create_savepoint('before_update')
            query = QtS.QSqlQuery()
            if len(upb_data_ids) > 1:
                query.prepare(
                    f"UPDATE UPbData SET {field} = {checked_ids[0]} WHERE UPbAnalysisID in {tuple(upb_data_ids)}")
            if len(upb_data_ids) == 1:
                query.prepare(
                    f"UPDATE UPbData SET {field} = {checked_ids[0]} WHERE UPbAnalysisID = {upb_data_ids[0]}")
            if not query.exec():
                rollback_savepoint('before_update')
                errtxt = query.lastError().text()
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                return
            update_modified_timestamp('UPbData', upb_data_ids)
            print(f"Updated {field} to {checked_ids[0]} for UPbAnalysisID {upb_data_ids}")
            release_savepoint('before_update')

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
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setText('Are you sure you want to discard all changes?')
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            rollback_savepoint('before_edit')
            self.reject()
            self.close_by_dialog = True
            self.close()
            self.close_by_dialog = False
        else:
            pass

    def commit_question(self):
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

    def rollback(self, savepoint_name: str):
        query = QtS.QSqlQuery()
        if not query.exec(f'ROLLBACK TO SAVEPOINT {savepoint_name}'):
            errtxt = query.lastError().text()
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        else:
            self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        release_savepoint('before_edit')
        # TrC.save_expanded_state(self.table, self.tree_proxy_model, self.edit_treeView, self.settings)
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def closeEvent(self, event: QtG.QCloseEvent):
        if not self.close_by_dialog:
            self.discard_question()
            event.ignore()
        else:
            event.accept()
