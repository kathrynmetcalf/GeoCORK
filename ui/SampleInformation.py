import sys
from pathlib import Path
import sqlite3
import re
from random import sample

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
import ui.import_wizard
import ui.New_source
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

        sources_ui_file = "ui/SampleInformation.ui"
        loadUi(sources_ui_file, self)



        self.sample_names_model = TbC.CheckableSQLTableModel()  # The one used to populate the dropdown checkbox of samples to edit, shows only name and description
        self.sample_names_model = self.set_table(self.sample_names_model, 'Samples')
        if sample_id_list is None:
            self.selected_sample_list = []
        else:
            self.selected_sample_list = sample_id_list
            if len(self.selected_sample_list) > 1:
                self.sample_names_model.setFilter(f"SampleID in {tuple(self.selected_sample_list)}")
            else:
                self.sample_names_model.setFilter(f"SampleID = {self.selected_sample_list[0]}")
        self.checked_sample_list = []
        self.checked_sample_names = ""

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
        self.reference_model = QtS.QSqlTableModel()
        self.analysis_method_model = QtS.QSqlTableModel()
        self.analysis_method_tree = CheckableTreeModel()
        self.lab_facility_model = QtS.QSqlTableModel()
        self.instrument_model = QtS.QSqlTableModel()

        self.populate_dropdowns()
        self.populate_fields()
        self.check_all_samples()
        self.sample_name_comboBox.setModel(self.sample_names_model)
        self.sample_name_comboBox.set_line_edit_text(self.checked_sample_names)

        # todo: Add functionality to populate fields and update the displayed list based on selected samples
        self.sample_names_model.dataChanged.connect(self.update_sample_list)

    def check_all_samples(self):
        for row in range(self.sample_names_model.rowCount()):
            index = self.sample_names_model.index(row, 1, QtC.QModelIndex())
            self.sample_names_model.setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            print(f"Check state is {self.sample_names_model.data(index, QtC.Qt.ItemDataRole.CheckStateRole)}")
        self.update_sample_list()

    def update_sample_list(self):
        self.checked_sample_list = []
        checked_sample_names = []
        self.checked_sample_names = ""
        for row in range(self.sample_names_model.rowCount()):
            index = self.sample_names_model.index(row, 1, QtC.QModelIndex())
            if self.sample_names_model.data(index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                name = self.sample_names_model.data(index, QtC.Qt.ItemDataRole.DisplayRole)
                checked_sample_names.append(name)
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
        self.reference_model = self.set_table(self.reference_model, 'References')
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


    def set_table(self, model: QtS.QSqlTableModel, table: str):
        model.setTable(table)
        model.select()
        return model

    def populate_fields(self):
        if len(self.selected_sample_list) > 1:
            for sample_id in self.selected_sample_list:
                pass
            # todo use distinct instead in sql query
        else:
            selected_sample_id = self.selected_sample_list[0]

            query = QtS.QSqlQuery()
            query.prepare(f"SELECT * FROM SAMPLES WHERE SampleID = {selected_sample_id}")
            query.exec()
            while query.next():
                self.best_age_lineEdit.setText(f"{query.value(2)}")
                self.best_age_error_lineEdit.setText(f"{query.value(3)}")
                self.best_age_error_type_comboBox.setCurrentText(query.value(4))
                self.oldest_dir_lineEdit.setText(f"{query.value(5)}")
                self.youngest_dir_lineEdit.setText(f"{query.value(6)}")
                oldest_age_id = query.value(7)
                youngest_age_id = query.value(8)
                self.height_depth_lineEdit.setText(f"{query.value(9)}")
                self.height_depth_error_lineEdit.setText(f"{query.value(10)}")
                self.height_depth_unit_comboBox.setCurrentText(query.value(11))
                self.lat_deg_lineEdit.setText(f"{query.value(12)}")
                self.lat_min_lineEdit.setText(f"{query.value(13)}")
                self.lat_sec_lineEdit.setText(f"{query.value(14)}")
                # self.lat_comboBox.setCurrentText()
                self.lon_deg_lineEdit.setText(f"{query.value(15)}")
                self.lon_min_lineEdit.setText(f"{query.value(16)}")
                self.lon_sec_lineEdit.setText(f"{query.value(17)}")
                # self.lon_comboBox.setCurrentText()
                self.utm_zone_lineEdit.setText(query.value(18))
                self.utm_n_lineEdit.setText(f"{query.value(19)}")
                self.utm_e_lineEdit.setText(f"{query.value(20)}")
                self.elevation_lineEdit.setText(f"{query.value(21)}")
                self.elevation_error_lineEdit.setText(f"{query.value(22)}")
                self.elevation_unit_comboBox.setCurrentText(query.value(23))
                table_model = QtS.QSqlTableModel()
                table_model.setTable('Ages')
                table_model.select()
                index = table_model.index(0, 0, QtC.QModelIndex())
                table_model.setFilter(f"SELECT AgeName FROM Ages WHERE AgeID = {oldest_age_id}")
                self.oldest_rel_comboBox.setCurrentText(table_model.data(index))
                table_model.setFilter(f"SELECT AgeName FROM Ages WHERE AgeID = {youngest_age_id}")
                self.youngest_rel_comboBox.setCurrentText(table_model.data(index))

                # Sample tags
                self.populate_checks(self.sample_context_model, self.sample_context_tree, 'Samples_SampleContexts')
                self.populate_checks(self.sampling_method_model, self.sampling_method_tree, 'Samples_SamplingMethods')
                # self.populate_checks(self.unit_model, self.unit_tree, 'Samples_Units')
                # self.populate_checks(self.rock_type_model, self.rock_type_tree, 'Samples_RockTypes')
                # self.populate_checks(self.region_model, self.region_tree, 'Samples_Regions')
                # self.populate_checks(self.setting_model, self.setting_tree, 'Samples_Settings')
                # self.populate_checks(self.age_signature_model, self.age_signature_tree, 'Samples_AgeSignatures')

    def populate_checks(self, table_model: QtS.QSqlTableModel, tree: CheckableTreeModel, many_to_many_table: str):
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(many_to_many_table)
        many_to_many_model.select()
        tag_id_header = table_model.record().fieldName(0)
        if len(self.checked_sample_list) == 0:
            # No samples selected, so uncheck everything
            for row in range(table_model.rowCount()):
                tree.setData(table_model.index(row, 0), QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            return
        for row in range(table_model.rowCount()):
            tag_id = table_model.index(row, 0).data()
            many_to_many_model.setFilter(f"SampleID in {tuple(self.selected_sample_list)} AND {tag_id_header} = {tag_id}")
            if many_to_many_model.rowCount() == len(self.selected_sample_list):
                # All samples have this tag
                tree.setData(table_model.index(row, 0), QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            elif many_to_many_model.rowCount() > 0:
                # Some samples have this tag
                tree.setData(table_model.index(row, 0), QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
            else:
                # No samples have this tag
                tree.setData(table_model.index(row, 0), QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)

widgets = [
{'widget_name': '', 'widget_type': '', 'current_text': '', 'data_col': 0, 'data_type': 'ID, value'},
{'widget_name': 'best_age_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 2, 'data_type': 'value'},
{'widget_name': 'best_age_error_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 3, 'data_type': 'value'},
{'widget_name': 'best_age_error_type_comboBox', 'widget_type': 'comboBox', 'current_text': '', 'data_col': 4, 'data_type': 'ID'},
{'widget_name': 'oldest_dir_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 5, 'data_type': 'value'},
{'widget_name': 'youngest_dir_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 6, 'data_type': 'value'},
{'widget_name': 'oldest_rel_comboBox', 'widget_type': 'comboBox', 'current_text': '', 'data_col': 7, 'data_type': 'ID'},
{'widget_name': 'youngest_rel_comboBox', 'widget_type': 'comboBox', 'current_text': '', 'data_col': 8, 'data_type': 'ID'},
{'widget_name': 'height_depth_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 9, 'data_type': 'value'},
{'widget_name': 'height_depth_error_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 10, 'data_type': 'value'},
{'widget_name': 'height_depth_unit_comboBox', 'widget_type': 'comboBox', 'current_text': '', 'data_col': 11, 'data_type': 'ID'},
{'widget_name': 'lat_deg_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 12, 'data_type': 'value'},
{'widget_name': 'lat_min_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 13, 'data_type': 'value'},
{'widget_name': 'lat_sec_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 14, 'data_type': 'value'},
{'widget_name': 'lon_deg_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 15, 'data_type': 'value'},
{'widget_name': 'lon_min_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 16, 'data_type': 'value'},
{'widget_name': 'lon_sec_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 17, 'data_type': 'value'},
{'widget_name': 'utm_zone_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 18, 'data_type': 'value'},
{'widget_name': 'utm_n_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 19, 'data_type': 'value'},
{'widget_name': 'utm_e_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 20, 'data_type': 'value'},
{'widget_name': 'elevation_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 21, 'data_type': 'value'},
{'widget_name': 'elevation_error_lineEdit', 'widget_type': 'lineEdit', 'current_text': '', 'data_col': 22, 'data_type': 'value'},
{'widget_name': 'elevation_unit_comboBox', 'widget_type': 'comboBox', 'current_text': '', 'data_col': 23, 'data_type': 'ID'},
    ]
