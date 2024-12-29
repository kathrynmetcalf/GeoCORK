import sys
from pathlib import Path
import sqlite3
import re
import decimal
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
from pandas.plotting import table

import Functions.Create_database as Create_db
import Functions.Table_classes as TbC
import Functions.Tree_classes as TrC
import Functions.Text_manipulations as TxM
import Functions.Errors as Er
import ui.import_wizard
import ui.New_reference
from Functions.Alter_database import release_savepoint
from Functions.Table_classes import CheckableSqlTableModel, SampleAgeTableModel, set_table, FontDelegate
from ui.EditSampleTable import EditSampleTable
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.Filters import QueryBuilder
from Functions.Tree_classes import TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView
from Functions.Database_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
from Functions.Check_triggers import validate_insert, validate_update, update_modified_timestamp
from Functions.Settings_manager import settings

# todo: Figure out why it is slowing down after checking and unchecking a bunch of stuff

class SampleInformation(QtW.QDialog):
    def __init__(self, parent_window, sample_id_list: list | None):
        super().__init__(parent=parent_window)
        self.parent_window = parent_window
        self.savepoint_manager = SavepointManager.get_instance()
        # self.loadWindowState()

        self.lat_deg_lineEdit: QtW.QLineEdit
        # widget.setProperty
        self.lat_min_lineEdit: QtW.QLineEdit
        self.lat_sec_lineEdit: QtW.QLineEdit
        self.lat_combobox: QtW.QComboBox
        self.lon_deg_lineEdit: QtW.QLineEdit
        self.lon_min_lineEdit: QtW.QLineEdit
        self.lon_sec_lineEdit: QtW.QLineEdit
        self.lon_combobox: QtW.QComboBox

        sources_ui_file = "ui/SampleInformation.ui"
        loadUi(sources_ui_file, self)

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
        self.gps_format_model = QtS.QSqlTableModel()
        self.gps_location_model = QtS.QSqlTableModel()
        self.direction_unit_model = QtS.QSqlTableModel()
        self.lat_direction_model = QtS.QSqlTableModel()
        self.lon_direction_model = QtS.QSqlTableModel()
        self.distance_unit_model = QtS.QSqlTableModel()
        self.elevation_unit_model = QtS.QSqlTableModel()
        self.column_model = QtS.QSqlTableModel()
        self.column_unit_model = QtS.QSqlTableModel()
        self.sample_age_model = SampleAgeTableModel()
        self.age_tree_view = QtW.QTreeView()
        self.age_model = QtS.QSqlTableModel()
        self.oldest_age_tree = TreeModel()
        self.youngest_age_tree = TreeModel()
        self.direct_age_unit_model = QtS.QSqlTableModel()
        self.error_type_model = QtS.QSqlTableModel()
        self.direct_age_error_model = QtS.QSqlTableModel()
        self.age_constraint_model = QtS.QSqlTableModel()
        self.age_constraint_tree = CheckableTreeModel()
        self.age_interpretation_model = QtS.QSqlTableModel()
        self.age_interpretation_tree = CheckableTreeModel()
        self.age_reference_model = CheckableSqlTableModel()
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
        self.populate_age_dropdown()
        self.populate_fields()
        self.connect_signals()

    def populate_dropdowns(self):
        self.gps_format_model = self.set_table(self.gps_format_model, 'GPSFormats')
        self.gps_location_model = self.set_table(self.gps_location_model, 'GPSLocations')
        self.lat_direction_model = self.set_table(self.lat_direction_model, 'DirectionUnits')
        self.lat_direction_model.setFilter('DirectionUnitAbbreviation = "N" OR DirectionUnitAbbreviation = "S"')
        self.lon_direction_model = self.set_table(self.lon_direction_model, 'DirectionUnits')
        self.lon_direction_model.setFilter('DirectionUnitAbbreviation = "E" OR DirectionUnitAbbreviation = "W"')
        self.elevation_unit_model = self.set_table(self.elevation_unit_model, 'DistanceUnits')
        self.column_model = self.set_table(self.column_model, 'Columns')
        self.column_unit_model = self.set_table(self.column_unit_model, 'DistanceUnits')
        self.age_model = self.set_table(self.age_model, 'Ages')
        self.direct_age_unit_model = self.set_table(self.direct_age_unit_model, 'AgeUnits')
        self.direct_age_error_model = self.set_table(self.direct_age_error_model, 'ErrorFormats')
        self.oldest_age_tree.setSourceModel(self.age_model)
        self.youngest_age_tree.setSourceModel(self.age_model)
        self.age_constraint_model = self.set_table(self.age_constraint_model, 'AgeConstraints')
        self.age_constraint_tree.setSourceModel(self.age_constraint_model)
        self.age_interpretation_model = self.set_table(self.age_interpretation_model, 'AgeInterpretations')
        self.age_interpretation_tree.setSourceModel(self.age_interpretation_model)
        self.age_reference_model = self.set_table(self.reference_model, '"References"')
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


        self.gps_format_comboBox.setModel(self.gps_format_model)
        self.show_column(self.gps_format_comboBox, 'GPSFormatAbbreviation')
        self.lat_comboBox.setModel(self.lat_direction_model)
        self.show_column(self.lat_comboBox, 'DirectionUnitAbbreviation')
        self.lon_comboBox.setModel(self.lon_direction_model)
        self.show_column(self.lon_comboBox, 'DirectionUnitAbbreviation')
        self.elevation_unit_comboBox.setModel(self.elevation_unit_model)
        self.show_column(self.elevation_unit_comboBox, 'DistanceUnitAbbreviation')
        self.column_name_comboBox.setModel(self.column_model)
        self.show_column(self.column_name_comboBox, 'ColumnName')
        self.height_depth_unit_comboBox.setModel(self.column_unit_model)
        self.show_column(self.height_depth_unit_comboBox, 'DistanceUnitAbbreviation')
        self.edit_age_comboBox.setModel(self.sample_age_model)
        self.show_column(self.edit_age_comboBox, 'SampleAgeDisplay')
        self.direct_unit_comboBox.setModel(self.direct_age_unit_model)
        self.show_column(self.direct_unit_comboBox, 'AgeUnitAbbreviation')
        self.direct_age_unit_comboBox.setModel(self.direct_age_unit_model)
        self.show_column(self.direct_age_unit_comboBox, 'AgeUnitAbbreviation')
        self.direct_age_error_type_comboBox.setModel(self.direct_age_error_model)
        self.show_column(self.direct_age_error_type_comboBox, 'ErrorFormatAbbreviation')
        self.oldest_rel_comboBox.setModel(self.oldest_age_tree)
        self.youngest_rel_comboBox.setModel(self.youngest_age_tree)
        self.age_constraint_comboBox.setModel(self.age_constraint_tree)
        self.age_interpretation_comboBox.setModel(self.age_interpretation_tree)
        self.age_reference_comboBox.setModel(self.age_reference_model)
        self.sample_context_comboBox.setModel(self.sample_context_tree)
        self.sampling_method_comboBox.setModel(self.sampling_method_tree)
        self.unit_comboBox.setModel(self.unit_tree)
        self.rock_type_comboBox.setModel(self.rock_type_tree)
        self.region_comboBox.setModel(self.region_tree)
        self.setting_comboBox.setModel(self.setting_tree)
        self.age_signature_comboBox.setModel(self.age_signature_tree)
        self.reference_comboBox.setModel(self.reference_model)
        self.analysis_method_comboBox.setModel(self.analysis_method_tree)
        self.lab_facility_comboBox.setModel(self.lab_facility_model)
        self.instrument_comboBox.setModel(self.instrument_model)

        self.sample_name_comboBox: CheckableTreeCombobox
        self.sample_name_comboBox.view().setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
        self.sample_name_comboBox.view().customContextMenuRequested.connect(self.show_context_menu)

        # self.location_groupBox.install_children_event_filter()
        self.latlon_groupBox.install_children_event_filter()
        self.utm_groupBox.install_children_event_filter()
        self.elev_groupBox.install_children_event_filter()
        # self.age_groupBox.install_children_event_filter()
        self.direct_age_groupBox.install_children_event_filter()
        self.relative_age_groupBox.install_children_event_filter()
        self.age_information_groupBox.install_children_event_filter()


    def populate_age_dropdown(self):
        self.edit_age_comboBox.setItemDelegate(FontDelegate(self.edit_age_comboBox))
        samples_sampleage_model = QtS.QSqlTableModel()
        set_table(samples_sampleage_model, 'Samples_SampleAges')
        if len(self.checked_sample_list) > 1:
            samples_sampleage_model.setFilter(f'SampleID in {tuple(self.checked_sample_list)}')
        elif len(self.checked_sample_list) == 1:
            samples_sampleage_model.setFilter(f'SampleID = {self.checked_sample_list[0]}')
        else:
            samples_sampleage_model.setFilter('')
        sample_ages = []
        for row in range(samples_sampleage_model.rowCount()):
            sample_ages.append(samples_sampleage_model.index(row, 1).data())
        if len(sample_ages) > 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID in {tuple(sample_ages)}')
        elif len(sample_ages) == 1:
            self.sample_age_model.setQuery(f'{self.sample_age_model.default_query} WHERE SampleAgeID = {sample_ages[0]}')
        for row in range(self.sample_age_model.rowCount()):
            if self.sample_age_model.index(row, 0).data() in self.default_age_ids:
                # Make the text at that row bold
                self.sample_age_model.make_bold(self.sample_age_model.index(row, 0))
            else:
                self.sample_age_model.make_not_bold(self.sample_age_model.index(row, 0))

    def set_table(self, model: QtS.QSqlTableModel, table: str):
        model.setTable(table)
        model.select()
        return model

    def show_column(self, comboBox: QtW.QComboBox, column: str):
        model = comboBox.model()
        for col in range(model.columnCount()):
            header = model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if header == column:
                comboBox.setModelColumn(col)

    def connect_signals(self):
        # Connect signals and slots
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.sample_names_model.dataChanged.connect(self.update_sample_list)
        self.sample_igsn_lineEdit.editingFinished.connect(lambda: self.update_field('SampleIGSN', f'"{self.sample_igsn_lineEdit.text()}"'))
        self.gps_format_comboBox.currentTextChanged.connect(self.display_gps)
        self.latlon_groupBox.connect_child_signals()
        self.latlon_groupBox.focusLost.connect(self.update_gps)
        self.utm_groupBox.connect_child_signals()
        self.utm_groupBox.focusLost.connect(self.update_gps)
        self.elev_groupBox.connect_child_signals()
        self.elev_groupBox.focusLost.connect(self.update_gps)
        # self.location_groupBox.focusLost.connect(self.update_gps)
        self.column_name_comboBox.currentTextChanged.connect(lambda: self.update_id('ColumnID', 'ColumnName', self.column_name_comboBox.currentText(), 'Columns'))
        self.height_depth_lineEdit.editingFinished.connect(
            lambda: self.update_field('HeightDepth', self.height_depth_lineEdit.text()))
        self.height_depth_error_lineEdit.editingFinished.connect(
            lambda: self.update_field('HeightDepthError', self.height_depth_error_lineEdit.text()))
        self.height_depth_unit_comboBox.currentTextChanged.connect(lambda: self.update_id('HeightDepthUnitID', 'DistanceUnitAbbreviation', self.height_depth_unit_comboBox.currentText(), 'DistanceUnits'))
        self.edit_age_comboBox.currentTextChanged.connect(self.display_age)
        self.default_age_checkBox.clicked.connect(self.update_age)
        self.direct_age_groupBox.connect_child_signals()
        self.direct_age_groupBox.focusLost.connect(self.update_age)
        self.relative_age_groupBox.connect_child_signals()
        self.relative_age_groupBox.focusLost.connect(self.update_age)
        self.age_information_groupBox.connect_child_signals()
        self.age_information_groupBox.focusLost.connect(self.update_age)
        self.sample_context_comboBox.closing.connect(lambda: self.update_sample_tags(self.sample_context_tree, 'SampleContexts'))
        self.sampling_method_comboBox.closing.connect(lambda: self.update_sample_tags(self.sampling_method_tree, 'SamplingMethods'))
        self.unit_comboBox.closing.connect(lambda: self.update_sample_tags(self.unit_tree, 'Units'))
        self.rock_type_comboBox.closing.connect(lambda: self.update_sample_tags(self.rock_type_tree, 'RockTypes'))
        self.region_comboBox.closing.connect(lambda: self.update_sample_tags(self.region_tree, 'Regions'))
        self.setting_comboBox.closing.connect(lambda: self.update_sample_tags(self.setting_tree, 'Settings'))
        self.age_signature_comboBox.closing.connect(lambda: self.update_sample_tags(self.age_signature_tree, 'AgeSignatures'))
        # self.reference_comboBox.closing.connect(lambda: self.update_subfield_id(self.reference_model, 'ReferenceID'))
        # self.analysis_method_comboBox.closing.connect(lambda: self.update_subfield_id(self.analysis_method_model, 'UPbAnalysisMethodID'))
        # self.lab_facility_comboBox.closing.connect(lambda: self.update_subfield_id(self.lab_facility_model, 'LabFacilityID'))
        # self.instrument_comboBox.closing.connect(lambda: self.update_subfield_id(self.instrument_model, 'InstrumentID'))
        self.sample_description_lineEdit.editingFinished.connect(lambda: self.update_field('SampleDescription', f'"{self.sample_description_lineEdit.text()}"'))

    def disconnect_text_signals(self):
        self.latlon_groupBox.disconnect_child_signals()
        self.utm_groupBox.disconnect_child_signals()
        self.elev_groupBox.disconnect_child_signals()
        self.direct_age_groupBox.disconnect_child_signals()
        self.relative_age_groupBox.disconnect_child_signals()
        self.age_information_groupBox.disconnect_child_signals()
        try:
            self.gps_format_comboBox.currentTextChanged.disconnect(self.display_gps)
        except TypeError:
            pass
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
            self.edit_age_comboBox.currentTextChanged.disconnect(self.display_age)
        except TypeError:
            pass
        try:
            self.default_age_checkBox.clicked.disconnect()
        except TypeError:
            pass
        try:
            self.oldest_direct_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.youngest_direct_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.direct_unit_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_error_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_unit_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.oldest_rel_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.youngest_rel_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.direct_age_error_type_comboBox.currentTextChanged.disconnect()
        except TypeError:
            pass
        try:
            self.sample_description_lineEdit.editingFinished.disconnect()
        except TypeError:
            pass

    def populate_fields(self):
        sample_ifnull_query = TbC.SampleIfNullQuery()
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
            if ',' in text:
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
            self.gps_location_ids = text_values[2]
            self.set_comboBox_text(self.column_name_comboBox, text_values[3])
            self.height_depth_lineEdit.setText(f"{text_values[4]}")
            self.height_depth_error_lineEdit.setText(f"{text_values[5]}")
            self.set_comboBox_text(self.height_depth_unit_comboBox, text_values[6])
            self.sample_description_lineEdit.setText(text_values[7])
            self.lat_deg_lineEdit.setText(f"{text_values[8]}")
            self.lat_min_lineEdit.setText(f"{text_values[9]}")
            self.lat_sec_lineEdit.setText(f"{text_values[10]}")
            self.set_comboBox_text(self.lat_comboBox, text_values[11])
            self.lon_deg_lineEdit.setText(f"{text_values[12]}")
            self.lon_min_lineEdit.setText(f"{text_values[13]}")
            self.lon_sec_lineEdit.setText(f"{text_values[14]}")
            self.set_comboBox_text(self.lon_comboBox, text_values[15])
            self.utm_zone_lineEdit.setText(f"{text_values[16]}")
            self.utm_n_lineEdit.setText(f"{text_values[17]}")
            self.utm_e_lineEdit.setText(f"{text_values[18]}")
            self.set_comboBox_text(self.gps_format_comboBox, text_values[19])
            self.elevation_lineEdit.setText(f"{text_values[20]}")
            self.elevation_error_lineEdit.setText(f"{text_values[21]}")
            self.set_comboBox_text(self.elevation_unit_comboBox, text_values[22])
            default_age_ids = text_values[23]
            self.default_age_ids = []
            if default_age_ids != '':
                if ',' in default_age_ids:
                    self.default_age_ids = [int(x) for x in default_age_ids.split(',')]
                else:
                    self.default_age_ids = [int(default_age_ids)]
                for row in range(self.sample_age_model.rowCount()):
                    if self.sample_age_model.index(row, 0).data() == self.default_age_ids[0]:
                        self.edit_age_comboBox.setCurrentIndex(row)
                        break
            self.default_age_checkBox.setChecked(self.default_age_ids != '')
            self.direct_age_lineEdit.setText(f"{text_values[24]}")
            self.direct_age_error_lineEdit.setText(f"{text_values[25]}")
            self.set_comboBox_text(self.direct_age_error_type_comboBox, text_values[26])
            self.oldest_direct_lineEdit.setText(f"{text_values[27]}")
            self.youngest_direct_lineEdit.setText(f"{text_values[28]}")
            self.set_comboBox_text(self.direct_age_unit_comboBox, text_values[29])
            self.set_comboBox_text(self.oldest_rel_comboBox, text_values[30])
            self.set_comboBox_text(self.youngest_rel_comboBox, text_values[31])
            self.age_description_lineEdit.setText(text_values[32])
            self.set_comboBox_text(self.age_constraint_comboBox, text_values[33])
            self.set_comboBox_text(self.age_interpretation_comboBox, text_values[34])
            self.set_comboBox_text(self.age_reference_comboBox, text_values[35])

            self.display_gps()

            # Age tags
            text = self.populate_checks('SampleAges_AgeConstraints', self.age_constraint_model, self.age_constraint_tree)
            self.age_constraint_comboBox.setCurrentText(text)
            text = self.populate_checks('SampleAges_AgeInterpretations', self.age_interpretation_model, self.age_interpretation_tree)
            self.age_interpretation_comboBox.setCurrentText(text)
            text = self.populate_checks('SampleAges_References', self.age_reference_model)
            self.age_reference_comboBox.setCurrentText(text)

            # Sample tags
            text = self.populate_checks('Samples_SampleAges', self.sample_age_model)
            self.edit_age_comboBox.setCurrentText(text)
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

    def set_comboBox_text(self, comboBox: QtW.QComboBox, text: str):
        if text == '' or text == '-':
            comboBox.setCurrentIndex(-1)
        else:
            comboBox.setCurrentText(text)

    def display_gps(self):
        current_gps_format = self.gps_format_comboBox.currentText()
        if current_gps_format == '':
            # Show all gps fields
            self.utm_groupBox.show()
            self.latlon_groupBox.show()
            self.lat_min_lineEdit.show()
            self.lon_min_lineEdit.show()
            self.lat_min_label.show()
            self.lon_min_label.show()
            self.lat_sec_lineEdit.show()
            self.lon_sec_lineEdit.show()
            self.lat_sec_label.show()
            self.lon_sec_label.show()
            self.lat_comboBox.show()
            self.lon_comboBox.show()
        elif current_gps_format == 'UTM':
            self.utm_groupBox.show()
            self.latlon_groupBox.hide()
        else:
            self.utm_groupBox.hide()
            self.latlon_groupBox.show()
            self.lat_deg_lineEdit.show()
            self.lon_deg_lineEdit.show()
            self.lat_deg_label.show()
            self.lon_deg_label.show()
            if 'M' in current_gps_format:
                self.lat_min_lineEdit.show()
                self.lon_min_lineEdit.show()
                self.lat_min_label.show()
                self.lon_min_label.show()
                if 'S' in current_gps_format:
                    self.lat_sec_lineEdit.show()
                    self.lon_sec_lineEdit.show()
                    self.lat_sec_label.show()
                    self.lon_sec_label.show()
                else:
                    self.lat_sec_lineEdit.hide()
                    self.lon_sec_lineEdit.hide()
                    self.lat_sec_label.hide()
                    self.lon_sec_label.hide()
            else:
                self.lat_min_lineEdit.hide()
                self.lon_min_lineEdit.hide()
                self.lat_min_label.hide()
                self.lon_min_label.hide()
                self.lat_sec_lineEdit.hide()
                self.lon_sec_lineEdit.hide()
                self.lat_sec_label.hide()
                self.lon_sec_label.hide()
            if '+/-' in current_gps_format:
                self.lat_comboBox.hide()
                self.lon_comboBox.hide()
            elif 'NSEW' in current_gps_format:
                self.lat_comboBox.show()
                self.lon_comboBox.show()

    def display_age(self):
        sample_age_row = self.edit_age_comboBox.currentIndex()
        sample_age_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if sample_age_id in self.default_age_ids:
            self.default_age_checkBox.setChecked(True)
        else:
            self.default_age_checkBox.setChecked(False)
        self.direct_age_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 2), QtC.Qt.ItemDataRole.DisplayRole)}")
        self.direct_age_error_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 3), QtC.Qt.ItemDataRole.DisplayRole)}")
        age_error_type_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 4), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.direct_age_error_model.rowCount()):
            if self.direct_age_error_model.index(row, 0).data() == age_error_type_id:
                age_error_abbreviation = self.direct_age_error_model.index(row, 2).data()
                self.set_comboBox_text(self.direct_age_error_type_comboBox, age_error_abbreviation)
                break
        self.oldest_direct_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 5), QtC.Qt.ItemDataRole.DisplayRole)}")
        self.youngest_direct_lineEdit.setText(f"{self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 6), QtC.Qt.ItemDataRole.DisplayRole)}")
        direct_age_unit_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 7), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.direct_age_unit_model.rowCount()):
            if self.direct_age_unit_model.index(row, 0).data() == direct_age_unit_id:
                direct_age_unit_abbreviation = self.direct_age_unit_model.index(row, 2).data()
                self.set_comboBox_text(self.direct_age_unit_comboBox, direct_age_unit_abbreviation)
                break
        oldest_age_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 8), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.age_model.rowCount()):
            if self.age_model.index(row, 0).data() == oldest_age_id:
                oldest_age = self.age_model.index(row, 3).data()
                self.set_comboBox_text(self.oldest_rel_comboBox, oldest_age)
                break
        youngest_age_id = self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 9), QtC.Qt.ItemDataRole.DisplayRole)
        for row in range(self.age_model.rowCount()):
            if self.age_model.index(row, 0).data() == youngest_age_id:
                youngest_age = self.age_model.index(row, 3).data()
                self.set_comboBox_text(self.youngest_rel_comboBox, youngest_age)
                break
        self.age_description_lineEdit.setText(self.sample_age_model.data(self.sample_age_model.index(sample_age_row, 10), QtC.Qt.ItemDataRole.DisplayRole))
        sampleage_ageconstraint_model = QtS.QSqlTableModel()
        self.set_table(sampleage_ageconstraint_model, 'SampleAges_AgeConstraints')
        text = self.populate_checks('SampleAges_AgeConstraints', sampleage_ageconstraint_model)
        self.set_comboBox_text(self.age_constraint_comboBox, text)
        sampleage_ageinterpretation_model = QtS.QSqlTableModel()
        self.set_table(sampleage_ageinterpretation_model, 'SampleAges_AgeInterpretations')
        text = self.populate_checks('SampleAges_AgeInterpretations', sampleage_ageinterpretation_model)
        self.set_comboBox_text(self.age_interpretation_comboBox, text)
        sampleage_reference_model = QtS.QSqlTableModel()
        self.set_table(sampleage_reference_model, 'SampleAges_References')
        text = self.populate_checks('SampleAges_References', sampleage_reference_model)
        self.set_comboBox_text(self.age_reference_comboBox, text)


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
                TbC.delete_samples(selected_indexes)

    def update_field(self, field: str, text: str):
        print(f"Update_field called with {field} and {text}")
        if text != "-":
            if len(self.checked_sample_list) > 0:
                if text is None or text == '':
                    text = 'Null'
                query = QtS.QSqlQuery()
                create_savepoint('before_update')
                for sample_id in self.checked_sample_list:
                    if not query.exec(f"UPDATE Samples SET {field} = {text} WHERE SampleID = {sample_id}"):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                update_modified_timestamp('Samples', self.checked_sample_list)
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
                if not query.exec(f"UPDATE Samples SET {id_field} = {item_id} WHERE SampleID = {sample_id}"):
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    rollback_savepoint('before_update')
                    return
            update_modified_timestamp('Samples', self.checked_sample_list)
            release_savepoint('before_update')

    def update_gps(self):
        print('Update_gps called')
        if len(self.checked_sample_list) > 0:
            create_savepoint('before_update')
            gps_format_abbreviation = self.gps_format_comboBox.currentText()
            self.gps_format_model.setFilter(f"GPSFormatAbbreviation = '{gps_format_abbreviation}'")
            gps_format_id = self.gps_format_model.data(self.gps_format_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            self.gps_format_model.setFilter('')  # Clear the filter
            if 'D' in gps_format_abbreviation:
                lat_deg = self.lat_deg_lineEdit.text()
                lon_deg = self.lon_deg_lineEdit.text()
                if 'M' in gps_format_abbreviation:
                    lat_min = self.lat_min_lineEdit.text()
                    lon_min = self.lon_min_lineEdit.text()
                    if 'S' in gps_format_abbreviation:
                        lat_sec = self.lat_sec_lineEdit.text()
                        lon_sec = self.lon_sec_lineEdit.text()
                    else:
                        lat_sec = 'Null'
                        lon_sec = 'Null'
                else:
                    lat_min = 'Null'
                    lon_min = 'Null'
                    lat_sec = 'Null'
                    lon_sec = 'Null'
                if '+/-' in gps_format_abbreviation:
                    lat_dir = 'Null'
                    lon_dir = 'Null'
                elif ' NSEW' in gps_format_abbreviation:
                    lat_dir = self.lat_comboBox.currentText()
                    lon_dir = self.lon_comboBox.currentText()
                    self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lat_dir}'")
                    lat_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
                    self.direction_unit_model.setFilter(f"DirectionUnitAbbreviation = '{lon_dir}'")
                    lon_dir = self.direction_unit_model.data(self.direction_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
                utm_zone = 'Null'
                utm_n = 'Null'
                utm_e = 'Null'
            elif gps_format_abbreviation == 'UTM':
                lat_deg = 'Null'
                lat_min = 'Null'
                lat_sec = 'Null'
                lat_dir = 'Null'
                lon_deg = 'Null'
                lon_min = 'Null'
                lon_sec = 'Null'
                lon_dir = 'Null'
                utm_zone = self.utm_zone_lineEdit.text()
                utm_n = self.utm_n_lineEdit.text()
                utm_e = self.utm_e_lineEdit.text()
            elevation = self.elevation_lineEdit.text()
            elevation_error = self.elevation_error_lineEdit.text()
            elevation_unit = self.elevation_unit_comboBox.currentText()
            if not elevation:
                elevation = 'Null'
            if not elevation_error:
                elevation_error = 'Null'
            if not elevation_unit:
                elevation_unit = 'Null'
            else:
                self.elevation_unit_model.setFilter(f"DistanceUnitAbbreviation = '{elevation_unit}'")
                elevation_unit = self.elevation_unit_model.data(self.elevation_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)

            if len(self.checked_sample_list) > 1:
                self.sample_names_model.setFilter(f"SampleID in {tuple(self.checked_sample_list)}")
            elif len(self.checked_sample_list) == 1:
                self.sample_names_model.setFilter(f"SampleID = {self.checked_sample_list[0]}")
            gps_ids = []
            for row in range(self.sample_names_model.rowCount()):
                if self.sample_names_model.index(row, 3).data() != 'Null':
                    gps_ids.append(self.sample_names_model.index(row, 3).data())
            query = QtS.QSqlQuery()
            gps_columns = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin',
                           'GPSLonSec', 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'GPSElev',
                           'GPSElevError', 'GPSElevUnitID']
            qgps_columns = ', '.join(gps_columns)
            gps_values = [lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir, utm_zone, utm_n,
                          utm_e, elevation, elevation_error, elevation_unit]
            qgps_values = ', '.join(gps_values)
            gps_to_delete = []
            gps_to_update = []
            if len(gps_ids) > 0:
                for gps in gps_ids:
                    self.sample_names_model.setFilter(f"SampleGPSLocationID = {gps}")
                    self.column_model.setFilter(f"ColumnBaseGPSLocationID = {gps}")
                    samples_with_gps = []
                    for row in range(self.sample_names_model.rowCount()):
                        if self.sample_names_model.index(row, 0).data() not in self.checked_sample_list:
                            samples_with_gps.append(self.sample_names_model.index(row, 0).data())
                    if len(samples_with_gps) == 0 and self.column_model.rowCount() == 0:
                        # There are no other samples or columns with this GPS location
                        if len(gps_to_update) == 0:
                            # Choose the first GPS location to update and delete the rest that will be unused
                            gps_to_update.append(gps)
                        else:
                            gps_to_delete.append(gps)
                if len(gps_to_update) == 0:
                    # All gps are associated with other samples or columns, so create a new one
                    error = validate_insert('GPSLocations', gps_columns, gps_values, gps_format_id)
                    if error:
                        errtxt = error
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                    if not query.exec(f'''INSERT INTO GPSLocations ({qgps_columns}) = (qgps_values)'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                    gps_id = query.lastInsertId()
                else:
                    error = validate_update('GPSLocations', gps_columns, gps_values, gps_format_id)
                    if error:
                        errtxt = error
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                    if not query.exec(f'''UPDATE GPSLocations SET ({qgps_columns}) = ({qgps_values}) WHERE GPSLocationID = {gps_to_update[0]}'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                    update_modified_timestamp('GPSLocations', gps_to_update)
                    gps_id = gps_to_update[0]
                    if len(gps_to_delete) > 0:
                        if not query.exec(f'DELETE FROM GPSLocations WHERE GPSLocationID in {tuple(gps_to_delete)}'):
                            errtxt = query.lastError().text()
                            self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                            rollback_savepoint('before_update')
                        return
            for sample_id in self.checked_sample_list:
                if not query.exec(f'''UPDATE Samples SET SampleGPSLocationID = {gps_id} WHERE SampleID = {sample_id}'''):
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    rollback_savepoint('before_update')
                    return
                update_modified_timestamp('Samples', sample_id)
            release_savepoint('before_update')

    def update_age(self):
        print('Update_age called')
        if len(self.checked_sample_list) > 0:
            default_age = self.default_age_checkBox.isChecked()
            direct_age = self.direct_age_lineEdit.text()
            if not direct_age or direct_age == '':
                direct_age = 'Null'
            direct_age_error = self.direct_age_error_lineEdit.text()
            if not direct_age_error or direct_age_error == '':
                direct_age_error = 'Null'
            direct_age_unit = self.direct_age_unit_comboBox.currentText()
            direct_age_error_type = self.direct_age_error_type_comboBox.currentText()
            oldest_direct = self.oldest_direct_lineEdit.text()
            if not oldest_direct or oldest_direct == '':
                oldest_direct = 'Null'
            youngest_direct = self.youngest_direct_lineEdit.text()
            if not youngest_direct or youngest_direct == '':
                youngest_direct = 'Null'
            oldest_rel = self.oldest_rel_comboBox.currentText()
            youngest_rel = self.youngest_rel_comboBox.currentText()
            age_description = self.age_description_lineEdit.text()
            if not age_description or age_description == '':
                age_description = 'Null'
            age_constraint = self.age_constraint_comboBox.currentText()
            age_interpretation = self.age_interpretation_comboBox.currentText()
            age_reference = self.age_reference_comboBox.currentText()

            row = self.edit_age_comboBox.currentIndex()
            sample_age_id = self.sample_age_model.data(self.sample_age_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
            old_sample_age_id = sample_age_id
            if direct_age_unit == '':
                direct_age_unit_id = 'Null'
            else:
                self.direct_age_unit_model.setFilter(f"AgeUnitAbbreviation = '{direct_age_unit}'")
                direct_age_unit_id = self.direct_age_unit_model.data(self.direct_age_unit_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if direct_age_error_type == '':
                direct_age_error_type_id = 'Null'
            else:
                self.direct_age_error_model.setFilter(f"ErrorFormatAbbreviation = '{direct_age_error_type}'")
                direct_age_error_type_id = self.direct_age_error_model.data(self.direct_age_error_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if oldest_rel == '':
                oldest_rel_id = 'Null'
            else:
                self.age_model.setFilter(f"AgeName = '{oldest_rel}'")
                oldest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if youngest_rel == '':
                youngest_rel_id = 'Null'
            else:
                self.age_model.setFilter(f"AgeName = '{youngest_rel}'")
                youngest_rel_id = self.age_model.data(self.age_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if age_constraint == '':
                age_constraint_id = 'Null'
            else:
                self.age_constraint_model.setFilter(f"AgeConstraintName = '{age_constraint}'")
                age_constraint_id = self.age_constraint_model.data(self.age_constraint_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if age_interpretation == '':
                age_interpretation_id = 'Null'
            else:
                self.age_interpretation_model.setFilter(f"AgeInterpretationName = '{age_interpretation}'")
                age_interpretation_id = self.age_interpretation_model.data(self.age_interpretation_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
            if age_reference == '':
                age_reference_id = 'Null'
            else:
                self.reference_model.setFilter(f"ShortCitation = '{age_reference}'")
                age_reference_id = self.reference_model.data(self.reference_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)

            create_savepoint('before_update')
            update_age = True
            samples_sampleages_model = QtS.QSqlTableModel()
            set_table(samples_sampleages_model, 'Samples_SampleAges')
            samples_sampleages_model.setFilter(f"SampleAgeID = {sample_age_id}")
            if samples_sampleages_model.rowCount() > 0:
                for row in range(samples_sampleages_model.rowCount()):
                    if samples_sampleages_model.index(row, 0).data() not in self.checked_sample_list:
                        update_age = False
            query = QtS.QSqlQuery()
            if update_age:
                if not query.exec(f'''UPDATE SampleAges SET (DirectAge, DirectAgeError, DirectAgeUnitID, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, OldestAgeID, YoungestAgeID, SampleAgeDescription) = 
                    ({direct_age}, {direct_age_error}, {direct_age_unit_id}, {direct_age_error_type_id}, {oldest_direct}, {youngest_direct}, {oldest_rel_id}, {youngest_rel_id}, "{age_description}") 
                    WHERE SampleAgeID = {sample_age_id}'''):
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    rollback_savepoint('before_update')
                    return
                update_modified_timestamp('SampleAges', sample_age_id)
            else:
                if not query.exec(f'''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeUnitID, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, OldestAgeID, YoungestAgeID, SampleAgeDescription) VALUES 
                    ({direct_age}, {direct_age_error}, {direct_age_unit_id}, {direct_age_error_type_id}, {oldest_direct}, {youngest_direct}, {oldest_rel_id}, {youngest_rel_id}, "{age_description}")'''):
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    rollback_savepoint('before_update')
                    return
                sample_age_id = query.lastInsertId()
            if age_constraint_id != 'Null':
                sampleages_ageconstraints_model = QtS.QSqlTableModel()
                set_table(sampleages_ageconstraints_model, 'SampleAges_AgeConstraints')
                sampleages_ageconstraints_model.setFilter(f"SampleAgeID = {sample_age_id} AND AgeConstraintID = {age_constraint_id}")
                if sampleages_ageconstraints_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO SampleAges_AgeConstraints (SampleAgeID, AgeConstraintID) VALUES ({sample_age_id}, {age_constraint_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                    return
            if age_interpretation_id != 'Null':
                sampleages_ageinterpretations_model = QtS.QSqlTableModel()
                set_table(sampleages_ageinterpretations_model, 'SampleAges_AgeInterpretations')
                sampleages_ageinterpretations_model.setFilter(f"SampleAgeID = {sample_age_id} AND AgeInterpretationID = {age_interpretation_id}")
                if sampleages_ageinterpretations_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO SampleAges_AgeInterpretations (SampleAgeID, AgeInterpretationID) VALUES ({sample_age_id}, {age_interpretation_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                    return
            if age_reference_id != 'Null':
                sampleages_references_model = QtS.QSqlTableModel()
                set_table(sampleages_references_model, 'SampleAges_References')
                sampleages_references_model.setFilter(f"SampleAgeID = {sample_age_id} AND ReferenceID = {age_reference_id}")
                if sampleages_references_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO SampleAges_References (SampleAgeID, ReferenceID) VALUES ({sample_age_id}, {age_reference_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                    return
            for sample_id in self.checked_sample_list:
                samples_sampleages_model = QtS.QSqlTableModel()
                set_table(samples_sampleages_model, 'Samples_SampleAges')
                samples_sampleages_model.setFilter(f"SampleID = {sample_id} AND SampleAgeID = {sample_age_id}")
                if samples_sampleages_model.rowCount() == 0:
                    if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES ({sample_id}, {sample_age_id})'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                if default_age:
                    if not query.exec(f'''UPDATE Samples SET DefaultSampleAgeID = {sample_age_id} WHERE SampleID = {sample_id}'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
                    update_modified_timestamp('Samples', [sample_id])
                    print(f"Updated DefaultSampleAgeID to {sample_age_id} for SampleID {sample_id}")
                if old_sample_age_id != sample_age_id:
                    if not query.exec(f'''DELETE FROM Samples_SampleAges WHERE SampleID = {sample_id} AND SampleAgeID = {old_sample_age_id}'''):
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                        rollback_savepoint('before_update')
                        return
            self.default_age_ids = []
            self.sample_names_model.select()
            for row in range(self.sample_names_model.rowCount()):
                if self.sample_names_model.index(row, 0).data() in self.checked_sample_list:
                    default_age_id = self.sample_names_model.index(row, 8).data()
                    if default_age_id not in self.default_age_ids:
                        self.default_age_ids.append(default_age_id)
            release_savepoint('before_update')
            self.populate_age_dropdown()

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

    def eventFilter(self, object, event):
        if event.type() == QtC.QEvent.Type.MouseButtonRelease:
            focus_widget = self.focusWidget()
            if focus_widget is not None:
                if object != focus_widget:
                    focus_widget.clearFocus()
                    return True
        return super().eventFilter(object, event)


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
