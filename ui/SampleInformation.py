import os
import sys
from pathlib import Path
import sqlite3
import re
from random import sample
import time

# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6.QtCore import Qt, QEventLoop, QStandardPaths, QPoint, QSettings, QSize
from PyQt6.QtWidgets import QFileDialog, QWidget, QPushButton

from PyQt6.uic import loadUi
import Functions.Create_database as Create_db
import Functions.Table_classes as TbC
import Functions.Tree_classes as TrC
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import ui.import_wizard
import ui.New_source
from Functions.Table_classes import CheckableSqlTableModel
from ui.EditSampleTable import EditSampleTable
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.Filters import QueryBuilder
from Functions.Tree_classes import TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView


class SampleInformation(QtW.QDialog):
    def __init__(self, parent_window, sample_id_list: list | None):
        super().__init__()
        # Define any variables here
        self.parent_window = parent_window
        self.db = self.parent_window.db
        self.settings = QSettings("CSUF", "SampleInformation")
        # self.loadWindowState()

        self.lat_deg_lineEdit: QtW.QLineEdit
        self.lat_min_lineEdit: QtW.QLineEdit
        self.lat_sec_lineEdit: QtW.QLineEdit
        self.lat_combobox: QtW.QComboBox
        self.lon_deg_lineEdit: QtW.QLineEdit
        self.lon_min_lineEdit: QtW.QLineEdit
        self.lon_sec_lineEdit: QtW.QLineEdit
        self.lon_combobox: QtW.QComboBox

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        sources_ui_file = os.path.join(base_path, "SampleInformation.ui")
        loadUi(sources_ui_file, self)

        # Sample names table
        self.sample_names_model = TbC.CheckableSqlTableModel()  # The one used to populate the dropdown checkbox of samples to edit, shows only name and description
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

        # Sample information models
        self.samples_table = QtS.QSqlQueryModel()
        self.age_tree_view = QtW.QTreeView()
        self.age_model = QtS.QSqlTableModel()
        self.oldest_age_tree = TreeModel()
        self.youngest_age_tree = TreeModel()
        self.column_model = QtS.QSqlTableModel()
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
        self.source_model = CheckableSqlTableModel()
        self.analysis_method_model = QtS.QSqlTableModel()
        self.analysis_method_tree = CheckableTreeModel()
        self.lab_facility_model = CheckableSqlTableModel()
        self.instrument_model = CheckableSqlTableModel()

        self.msg = QtW.QMessageBox(self)
        self.createSavepoint('before_edit')
        self.close_by_dialog = False

        # Fill in information based on selected samples
        self.populate_dropdowns()
        self.populate_fields()
        self.check_all_samples()
        self.sample_name_comboBox.setModel(self.sample_names_model)
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)

        # Connect signals and slots
        self.connect_signals()
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)

    def createSavepoint(self, savepoint_name: str):
        query = QtS.QSqlQuery(self.db)
        if query.exec(f'SAVEPOINT {savepoint_name}') is False:
            errtxt = Er.savepoint_fail("Samples")
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def releaseSavepoint(self, savepoint_name: str):
        query = QtS.QSqlQuery(self.db)
        if query.exec(f'RELEASE SAVEPOINT {savepoint_name}') is False:
            errtxt = Er.savepoint_release_fail("Samples")
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

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
        self.checked_sample_names = ", ".join(checked_sample_names)
        self.selected_sample_label.setText(f"Selected Samples: {self.checked_sample_names}")
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)
        self.populate_fields()

    def populate_dropdowns(self):
        self.age_model = self.set_table(self.age_model, 'Ages')
        self.oldest_age_tree.setSourceModel(self.age_model)
        self.youngest_age_tree.setSourceModel(self.age_model)
        self.column_model = self.set_table(self.column_model, 'Columns')
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
        self.source_model = self.set_table(self.source_model, 'Sources')
        self.analysis_method_model = self.set_table(self.analysis_method_model, 'AnalysisMethods')
        self.analysis_method_tree.setSourceModel(self.analysis_method_model)
        self.lab_facility_model = self.set_table(self.lab_facility_model, 'LabFacilities')
        self.instrument_model = self.set_table(self.instrument_model, 'Instruments')


        self.oldest_rel_comboBox.setModel(self.oldest_age_tree)
        self.youngest_rel_comboBox.setModel(self.youngest_age_tree)
        self.sample_context_comboBox.setModel(self.sample_context_tree)
        self.sampling_method_comboBox.setModel(self.sampling_method_tree)
        self.unit_comboBox.setModel(self.unit_tree)
        self.rock_type_comboBox.setModel(self.rock_type_tree)
        self.region_comboBox.setModel(self.region_tree)
        self.setting_comboBox.setModel(self.setting_tree)
        self.age_signature_comboBox.setModel(self.age_signature_tree)
        self.source_comboBox.setModel(self.source_model)
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
        self.sample_names_model.dataChanged.connect(self.update_sample_list)
        self.lat_deg_lineEdit.textChanged.connect(lambda text: self.update_field('LatDeg', text))
        self.lat_min_lineEdit.textChanged.connect(lambda text: self.update_field('LatMin', text))
        self.lat_sec_lineEdit.textChanged.connect(lambda text: self.update_field('LatSec', text))
        # self.lat_combobox.currentTextChanged.connect(lambda text: self.update_id('LatDirID', text, 'LocationUnits'))
        self.lon_deg_lineEdit.textChanged.connect(lambda text: self.update_field('LonDeg', text))
        self.lon_min_lineEdit.textChanged.connect(lambda text: self.update_field('LonMin', text))
        self.lon_sec_lineEdit.textChanged.connect(lambda text: self.update_field('LonSec', text))
        # self.lon_combobox.currentTextChanged.connect(lambda text: self.update_id('LonDirID', text, 'LocationUnits'))
        self.utm_zone_lineEdit.textChanged.connect(lambda text: self.update_field('UTMZone', text))
        self.utm_n_lineEdit.textChanged.connect(lambda text: self.update_field('UTMN', text))
        self.utm_e_lineEdit.textChanged.connect(lambda text: self.update_field('UTME', text))
        self.elevation_lineEdit.textChanged.connect(lambda text: self.update_field('Elevation', text))
        self.elevation_error_lineEdit.textChanged.connect(lambda text: self.update_field('ElevationError', text))
        # self.elevation_unit_comboBox.currentTextChanged.connect(lambda text: self.update_id('ElevationUnitID', text, 'DistanceUnits'))
        self.oldest_rel_comboBox.currentTextChanged.connect(lambda text: self.update_id('OldestAgeID', text, 'Ages'))
        self.youngest_rel_comboBox.currentTextChanged.connect(lambda text: self.update_id('YoungestAgeID', text, 'Ages'))
        self.oldest_dir_lineEdit.textChanged.connect(lambda text: self.update_field('OldestAge', text))
        self.youngest_dir_lineEdit.textChanged.connect(lambda text: self.update_field('YoungestAge', text))
        self.best_age_lineEdit.textChanged.connect(lambda text: self.update_field('AverageAge', text))
        self.best_age_error_lineEdit.textChanged.connect(lambda text: self.update_field('AverageAgeError', text))
        # self.best_age_error_type_comboBox.currentTextChanged.connect(lambda text: self.update_id('ErrorSigma', text, 'ErrorTypes'))
        # self.column_name_comboBox.currentTextChanged.connect(lambda text: self.update_id('ColumnID', text, 'Columns'))
        self.height_depth_lineEdit.textChanged.connect(lambda text: self.update_field('HeightDepth', text))
        self.height_depth_error_lineEdit.textChanged.connect(lambda text: self.update_field('HeightDepthError', text))
        # self.height_depth_unit_comboBox.currentTextChanged.connect(lambda text: self.update_id('HeightDepthUnitID', text, 'DistanceUnits'))
        self.sample_description_lineEdit.textChanged.connect(lambda text: self.update_field('SampleDescription', text))

        self.sample_context_comboBox.closing.connect(lambda: self.update_tags(self.sample_context_tree, 'SampleContexts'))
        self.sampling_method_comboBox.closing.connect(lambda: self.update_tags(self.sampling_method_tree, 'SamplingMethods'))
        self.unit_comboBox.closing.connect(lambda: self.update_tags(self.unit_tree, 'Units'))
        self.rock_type_comboBox.closing.connect(lambda: self.update_tags(self.rock_type_tree, 'RockTypes'))
        self.region_comboBox.closing.connect(lambda: self.update_tags(self.region_tree, 'Regions'))
        self.setting_comboBox.closing.connect(lambda: self.update_tags(self.setting_tree, 'Settings'))
        self.age_signature_comboBox.closing.connect(lambda: self.update_tags(self.age_signature_tree, 'AgeSignatures'))
        # self.source_comboBox.closing.connect(lambda: self.update_subfield_id(self.source_model, 'SourceID'))
        # self.analysis_method_comboBox.closing.connect(lambda: self.update_subfield_id(self.analysis_method_model, 'UPbAnalysisMethodID'))
        # self.lab_facility_comboBox.closing.connect(lambda: self.update_subfield_id(self.lab_facility_model, 'LabFacilityID'))
        # self.instrument_comboBox.closing.connect(lambda: self.update_subfield_id(self.instrument_model, 'InstrumentID'))

    def populate_fields(self):
        sample_distinct_query = TbC.SampleDistinctQuery()
        if len(self.checked_sample_list) > 1:
            self.samples_table.setQuery(f'{sample_distinct_query} WHERE SampleID in {tuple(self.selected_sample_list)}')
        elif len(self.checked_sample_list) == 1:
            self.samples_table.setQuery(f'{sample_distinct_query} WHERE SampleID = {self.selected_sample_list[0]}')
        else:
            return
        text_values = []
        for col in range(self.samples_table.columnCount()):
            # If there is only one value concatenated in the column, add it to the list, otherwise add '-'
            text = self.samples_table.index(0, col).data()
            if ',' in text:
                text_values.append('-')
            elif text == 'Null':
                text_values.append('')
            else:
                text_values.append(text)
        self.best_age_lineEdit.setText(f"{text_values[0]}")
        self.best_age_error_lineEdit.setText(f"{text_values[1]}")
        self.best_age_error_type_comboBox.setCurrentText(text_values[2])
        self.oldest_dir_lineEdit.setText(f"{text_values[3]}")
        self.youngest_dir_lineEdit.setText(f"{text_values[4]}")
        oldest_age_id = text_values[5]
        youngest_age_id = text_values[6]
        self.height_depth_lineEdit.setText(f"{text_values[7]}")
        self.height_depth_error_lineEdit.setText(f"{text_values[8]}")
        self.height_depth_unit_comboBox.setCurrentText(text_values[9])
        self.lat_deg_lineEdit.setText(f"{text_values[10]}")
        self.lat_min_lineEdit.setText(f"{text_values[11]}")
        self.lat_sec_lineEdit.setText(f"{text_values[12]}")
        # self.lat_comboBox.setCurrentText()
        self.lon_deg_lineEdit.setText(f"{text_values[13]}")
        self.lon_min_lineEdit.setText(f"{text_values[14]}")
        self.lon_sec_lineEdit.setText(f"{text_values[15]}")
        # self.lon_comboBox.setCurrentText()
        self.utm_zone_lineEdit.setText(text_values[16])
        self.utm_n_lineEdit.setText(f"{text_values[17]}")
        self.utm_e_lineEdit.setText(f"{text_values[18]}")
        self.elevation_lineEdit.setText(f"{text_values[19]}")
        self.elevation_error_lineEdit.setText(f"{text_values[20]}")
        self.elevation_unit_comboBox.setCurrentText(text_values[21])
        self.sample_description_lineEdit.setText(text_values[22])

        table_model = QtS.QSqlTableModel()
        table_model.setTable('Ages')
        table_model.select()
        index = table_model.index(0, 3, QtC.QModelIndex())
        if oldest_age_id == '-':
            self.oldest_rel_comboBox.setCurrentText(f'{oldest_age_id}')
        else:
            table_model.setFilter(f"AgeID = {oldest_age_id}")
            text = table_model.data(index)
            self.oldest_rel_comboBox.set_text(text)
        if youngest_age_id == '-':
            self.youngest_rel_comboBox.setCurrentText(f'{youngest_age_id}')
        else:
            table_model.setFilter(f"AgeID = {youngest_age_id}")
            text = table_model.data(index)
            self.youngest_rel_comboBox.set_text(text)

        # Sample tags
        text = self.populate_checks(self.sample_context_model, self.sample_context_tree, 'Samples_SampleContexts')
        self.sample_context_comboBox.setCurrentText(text)
        text = self.populate_checks(self.sampling_method_model, self.sampling_method_tree, 'Samples_SamplingMethods')
        self.sampling_method_comboBox.setCurrentText(text)
        text = self.populate_checks(self.unit_model, self.unit_tree, 'Samples_Units')
        self.unit_comboBox.setCurrentText(text)
        text = self.populate_checks(self.rock_type_model, self.rock_type_tree, 'Samples_RockTypes')
        self.rock_type_comboBox.setCurrentText(text)
        text = self.populate_checks(self.region_model, self.region_tree, 'Samples_Regions')
        self.region_comboBox.setCurrentText(text)
        text = self.populate_checks(self.setting_model, self.setting_tree, 'Samples_Settings')
        self.setting_comboBox.setCurrentText(text)
        text = self.populate_checks(self.age_signature_model, self.age_signature_tree, 'Samples_AgeSignatures')
        self.age_signature_comboBox.setCurrentText(text)
        text = self.populate_sub_checks(self.source_model)
        self.source_comboBox.set_single_click(True)
        self.source_comboBox.setCurrentText(text)
        text = self.populate_sub_checks(self.analysis_method_model)
        self.analysis_method_comboBox.set_single_click(True)
        self.analysis_method_comboBox.setCurrentText(text)
        text = self.populate_sub_checks(self.lab_facility_model)
        self.lab_facility_comboBox.set_single_click(True)
        self.lab_facility_comboBox.setCurrentText(text)
        text = self.populate_sub_checks(self.instrument_model)
        self.instrument_comboBox.set_single_click(True)
        self.instrument_comboBox.setCurrentText(text)

    def populate_checks(self, table_model: QtS.QSqlTableModel, tree: CheckableTreeModel, many_to_many_table: str):
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        tag_id_header = table_model.record().fieldName(0)
        items = []
        text = ""
        if len(self.checked_sample_list) == 0:
            # No samples selected, so uncheck everything
            for row in range(table_model.rowCount()):
                tree_index = tree.mapFromSource(table_model.index(row, 3))
                tree.setData(tree_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            return text
        for row in range(table_model.rowCount()):
            tag_id = table_model.index(row, 0).data()
            if len(self.checked_sample_list) > 1:
                many_to_many_model.setFilter(f"SampleID in {tuple(self.selected_sample_list)} AND {tag_id_header} = {tag_id}")
            else:
                many_to_many_model.setFilter(f"SampleID = {self.selected_sample_list[0]} AND {tag_id_header} = {tag_id}")
            tree_index = tree.mapFromSource(table_model.index(row, 3))
            if many_to_many_model.rowCount() == len(self.selected_sample_list):
                # All samples have this tag
                tree.setData(tree_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                items.append(tree.data(tree_index, QtC.Qt.ItemDataRole.DisplayRole))
            elif many_to_many_model.rowCount() > 0:
                # Some samples have this tag
                tree.setData(tree_index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                items.append(tree.data(tree_index, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                # No samples have this tag
                tree.setData(tree_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        text = ", ".join(items)
        return text

    def populate_sub_checks(self, table_model):
        if table_model.tableName() == "Sources":
            col = 6
        else:
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
        aliquot_ids, spot_ids, upb_data_ids = TbC.find_sub_items(self.checked_sample_list, self.db)
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

    def show_context_menu(self, pos: QPoint):
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
                TbC.delete_samples(selected_indexes, self.db)

    def update_field(self, field: str, text: str):
        if text != "-":
            self.createSavepoint('before_update')
            if len(self.checked_sample_list) > 0:
                for sample_id in self.checked_sample_list:
                    query = QtS.QSqlQuery()
                    query.prepare(f"UPDATE Samples SET {field} = {text} WHERE SampleID = {sample_id}")
                    if query.exec():
                        self.releaseSavepoint('before_update')
                        print(f"Updated {field} to {text} for SampleID {sample_id}")
                    else:
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def update_id(self, field: str, text: str, table: str):
        table_model = QtS.QSqlTableModel()
        table_model.setTable(table)
        table_model.select()
        table_model.setFilter(f"{table_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)} = {text}")
        item_id = table_model.data(table_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if len(self.checked_sample_list) > 0:
            self.createSavepoint('before_update')
            for sample_id in self.checked_sample_list:
                query = QtS.QSqlQuery()
                query.prepare(f"UPDATE Samples SET {field} = {item_id} WHERE SampleID = {sample_id}")
                if query.exec():
                    self.releaseSavepoint('before_update')
                else:
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def update_subfield_id(self, model: CheckableSqlTableModel, field: str):
        aliquot_ids, spot_ids, upb_data_ids = TbC.find_sub_items(self.checked_sample_list, self.db)
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If nothing is fully checked, then nothing should be updated
        checked_item_id = None  # Should only be one
        if len(upb_data_ids) > 0:
            if model.tableName() == "Sources":
                column = 6
            else:
                column = 1
            for row in range(model.rowCount()):
                name_index = model.index(row, column)
                id_index = model.index(row, 0)
                if model.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                    checked_item_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
            # todo: optimize update for thousands of analysis IDs
            # todo: figure out what other transaction is going on before beginning one for the updates
            self.createSavepoint('before_update')
            query_start_time = time.time()
            if model.database().transaction():
                query = QtS.QSqlQuery()
                query.setForwardOnly(True)
                if len(upb_data_ids) > 1:
                    print(len(upb_data_ids))
                    upb_data_ids.sort()
                    query.exec(f"UPDATE UPbData SET {field} = {checked_item_id} WHERE UPbAnalysisID in {tuple(upb_data_ids)[0:10]}")
                else:
                    query.exec(f"UPDATE UPbData SET {field} = {checked_item_id} WHERE UPbAnalysisID = {upb_data_ids[0]}")
                if model.database().commit():
                    print(f"Updated {field} to {checked_item_id} for UPbAnalysisID {upb_data_ids[0:10]}")
                    self.releaseSavepoint('before_update')
                else:
                    print(f"Failed to update {field} to {checked_item_id} for UPbAnalysisID {upb_data_ids[0:10]}")
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
            query_end_time = time.time()
            print(f"Query time: {query_end_time - query_start_time}")

    def update_tags(self, model: TrC.CheckableTreeModel, table: str):
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(f"Samples_{table}")
        many_to_many_model.select()

        if len(self.checked_sample_list) > 0:
            checked_items , partially_checked_items = model.traverse_checkable_tree(QtC.QModelIndex())
            for sample_id in self.checked_sample_list:
                model.update_db(checked_items, partially_checked_items, sample_id)

    def update_sub_tags(self, model: TrC.CheckableTreeModel, table: str):
        field = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        aliquot_ids, spot_ids, upb_data_ids = TbC.find_sub_items(self.checked_sample_list, self.db)
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If nothing is fully checked, then nothing should be updated
        checked_items, partially_checked_items = model.traverse_checkable_tree(QtC.QModelIndex())
        checked_item_id = None  # Should only be one
        if len(checked_items) > 0:
            self.createSavepoint('before_update')
            query = QtS.QSqlQuery()
            if len(upb_data_ids) > 1:
                query.prepare(
                    f"UPDATE UPbData SET {field} = {checked_item_id} WHERE UPbAnalysisID in {tuple(upb_data_ids)}")
            if len(upb_data_ids) == 1:
                query.prepare(
                    f"UPDATE UPbData SET {field} = {checked_item_id} WHERE UPbAnalysisID = {upb_data_ids[0]}")
            if query.exec():
                print(f"Updated {field} to {checked_item_id} for UPbAnalysisID {upb_data_ids}")
                self.releaseSavepoint('before_update')
            else:
                self.rollback('before_update')
                errtxt = query.lastError().text()
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

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
            self.rollback('before_edit')
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
        query = QtS.QSqlQuery(self.db)
        if query.exec(f'ROLLBACK TO SAVEPOINT {savepoint_name}') is False:
            errtxt = Er.rollback_fail("Samples")
            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
        else:
            self.reject()
        self.close_by_dialog = True
        self.close()
        self.close_by_dialog = False

    def commit(self):
        self.releaseSavepoint('before_edit')
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