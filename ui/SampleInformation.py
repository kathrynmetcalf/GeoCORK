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
    def __init__(self, parent_window, sample_model: QtS.QSqlQueryModel | None, selected_sample_list: list | None):
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

        if sample_model is None:
            self.sample_model = QtS.QSqlQueryModel()
            query = TbC.SampleTableModel().setupQuery()
            self.sample_model.setQuery(QtS.QSqlQuery(query, self.db))
            for col in range(self.sample_model.columnCount()):
                header = TxM.add_spaces_camel(
                    self.sample_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                self.sample_model.setHeaderData(col, QtC.Qt.Orientation.Horizontal, header, QtC.Qt.ItemDataRole.DisplayRole)
        else:
            self.sample_model = self.parent_window.sample_model
        if selected_sample_list is None:
            self.selected_sample_list = []
        else:
            self.selected_sample_list = selected_sample_list
        self.sample_table_model = QtS.QSqlQueryModel()

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
        # self.populate_fields()

        # todo: Add functionality to populate fields and update the displayed list based on selected samples
        # self.sample_name_comboBox.selectionChanged.connect(self.update_sample_list)

    def populate_dropdowns(self):
        self.sample_table_model.setQuery(f"SELECT SampleName, Description from SAMPLES")
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

        self.sample_name_comboBox.setView(QtW.QTableView())
        self.sample_name_comboBox.setModel(self.sample_table_model)
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

        # todo: Populate checkboxes based on selected sample
        #  if multiple samples are selected, populate with checks for common values and partial checks for differing values

        if len(self.selected_sample_list) > 1:
            for sample_id in self.selected_sample_list:
                pass
        else:
            selected_sample_id = self.selected_sample_list[0]

            query = QtS.QSqlQuery()
            query.prepare(f"SELECT * FROM SAMPLES WHERE SampleID = {selected_sample_id}")
            query.exec()
            while query.next():
                self.best_age_lineEdit.setText(query.value(2))
                self.best_age_error_lineEdit.setText(query.value(3))
                self.best_age_error_type_comboBox.setCurrentText(query.value(4))
                self.oldest_age_lineEdit.setText(query.value(5))
                self.youngest_age_lineEdit.setText(query.value(6))
                oldest_age_id = query.value(7)
                youngest_age_id = query.value(8)
                self.height_depth_lineEdit.setText(query.value(9))
                self.height_depth_error_lineEdit.setText(query.value(10))
                self.height_depth_unit_comboBox.setCurrentText(query.value(11))
                self.lat_deg_lineEdit.setText(query.value(12))
                self.lat_min_lineEdit.setText(query.value(13))
                self.lat_sec_lineEdit.setText(query.value(14))
                # self.lat_comboBox.setCurrentText()
                self.lon_deg_lineEdit.setText(query.value(15))
                self.lon_min_lineEdit.setText(query.value(16))
                self.lon_sec_lineEdit.setText(query.value(17))
                # self.lon_comboBox.setCurrentText()
                self.utm_zone_lineEdit.setText(query.value(18))
                self.utm_n_lineEdit.setText(query.value(19))
                self.utm_e_lineEdit.setText(query.value(20))
                self.elevation_lineEdit.setText(query.value(21))
                self.elevation_error_lineEdit.setText(query.value(22))
                self.elevation_unit_comboBox.setCurrentText(query.value(23))
                table_model = QtS.QSqlTableModel()
                table_model.setTable('Ages')
                table_model.select()
                index = table_model.index(0, 0, QtC.QModelIndex())
                table_model.setFilter(f"SELECT AgeName FROM Ages WHERE AgeID = {oldest_age_id}")
                self.oldest_age_comboBox.setCurrentText(table_model.data(index))
                table_model.setFilter(f"SELECT AgeName FROM Ages WHERE AgeID = {youngest_age_id}")
                self.youngest_age_comboBox.setCurrentText(table_model.data(index))
