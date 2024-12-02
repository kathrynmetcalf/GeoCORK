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
import ui.New_source
from Functions.Table_classes import CheckableSqlTableModel, SampleAgeTableModel
from ui.EditSampleTable import EditSampleTable
from ui.EditTable import EditTable
from ui.EditTree import EditTree
from ui.Filters import QueryBuilder
from Functions.Tree_classes import TreeModel, CheckableTreeCombobox, CheckableTreeModel, CheckableTreeView


class SampleInformation(QtW.QDialog):
    def __init__(self, parent_window, sample_id_list: list | None):
        print("SampleInformation init")
        super().__init__(parent=parent_window)
        print("SampleInformation super")
        self.parent_window = parent_window
        self.db = self.parent_window.db
        self.settings = QSettings("CSUF", "SampleInformation")
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

        # Sample information models
        self.samples_table = QtS.QSqlQueryModel()
        # todo: display the abbreviation instead of the id for unit and type fields
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
        self.age_source_model = CheckableSqlTableModel()
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
        self.source_model = CheckableSqlTableModel()
        self.upb_analysis_method_model = QtS.QSqlTableModel()
        self.concordance_type_model = QtS.QSqlTableModel()

        self.gps_location_ids = ""

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

        self.installEventFilter(self)

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
        self.gps_format_model = self.set_table(self.gps_format_model, 'GPSFormats')
        self.gps_location_model = self.set_table(self.gps_location_model, 'GPSLocations')
        self.lat_direction_model = self.set_table(self.lat_direction_model, 'DirectionUnits')
        self.lon_direction_model = self.set_table(self.lon_direction_model, 'DirectionUnits')
        self.elevation_unit_model = self.set_table(self.elevation_unit_model, 'DistanceUnits')
        self.column_model = self.set_table(self.column_model, 'Columns')
        self.column_unit_model = self.set_table(self.column_unit_model, 'DistanceUnits')
        self.sample_age_model = self.set_table(self.sample_age_model, 'SampleAges')
        self.age_model = self.set_table(self.age_model, 'Ages')
        self.direct_age_unit_model = self.set_table(self.direct_age_unit_model, 'AgeUnits')
        self.direct_age_error_model = self.set_table(self.direct_age_error_model, 'ErrorTypes')
        self.oldest_age_tree.setSourceModel(self.age_model)
        self.youngest_age_tree.setSourceModel(self.age_model)
        self.age_constraint_model = self.set_table(self.age_constraint_model, 'AgeConstraints')
        self.age_constraint_tree.setSourceModel(self.age_constraint_model)
        self.age_interpretation_model = self.set_table(self.age_interpretation_model, 'AgeInterpretations')
        self.age_interpretation_tree.setSourceModel(self.age_interpretation_model)
        self.age_source_model = self.set_table(self.source_model, 'Sources')
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
        self.analysis_method_model = self.set_table(self.analysis_method_model, 'UPbAnalysisMethods')
        self.analysis_method_tree.setSourceModel(self.analysis_method_model)
        self.lab_facility_model = self.set_table(self.lab_facility_model, 'LabFacilities')
        self.instrument_model = self.set_table(self.instrument_model, 'Instruments')


        self.gps_format_comboBox.setModel(self.gps_format_model)
        self.lat_comboBox.setModel(self.lat_direction_model)
        self.lon_comboBox.setModel(self.lon_direction_model)
        self.elevation_unit_comboBox.setModel(self.elevation_unit_model)
        self.column_name_comboBox.setModel(self.column_model)
        self.height_depth_unit_comboBox.setModel(self.column_unit_model)
        self.view_age_comboBox.setModel(self.sample_age_model)
        self.direct_unit_comboBox.setModel(self.direct_age_unit_model)
        self.direct_age_unit_comboBox.setModel(self.direct_age_unit_model)
        self.direct_age_error_type_comboBox.setModel(self.direct_age_error_model)
        self.oldest_rel_comboBox.setModel(self.oldest_age_tree)
        self.youngest_rel_comboBox.setModel(self.youngest_age_tree)
        self.age_constraint_comboBox.setModel(self.age_constraint_tree)
        self.age_interpretation_comboBox.setModel(self.age_interpretation_tree)
        self.age_source_comboBox.setModel(self.age_source_model)
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
        self.commit_pushButton.clicked.connect(self.commit_question)
        self.cancel_pushButton.clicked.connect(self.discard_question)
        self.sample_names_model.dataChanged.connect(self.update_sample_list)
        self.gps_format_comboBox.currentTextChanged.connect(self.display_gps)
        filter = focus_event_filter()
        self.location_groupBox.installEventFilter(filter)
        # self.lat_deg_lineEdit.editingFinished.connect(lambda: self.update_field('LatDeg', self.lat_deg_lineEdit.text()))
        # self.lat_min_lineEdit.editingFinished.connect(lambda: self.update_field('LatMin', self.lat_min_lineEdit.text()))
        # self.lat_sec_lineEdit.editingFinished.connect(lambda: self.update_field('LatSec', self.lat_sec_lineEdit.text()))
        # self.lat_combobox.currentTextChanged.connect(lambda: self.update_id('DirectionUnitID', 'DirectionUnitAbbreviation', self.lat_combobox.currentText(), 'DirectionUnits'))
        # self.lon_deg_lineEdit.editingFinished.connect(lambda: self.update_field('LonDeg', self.lon_deg_lineEdit.text()))
        # self.lon_min_lineEdit.editingFinished.connect(lambda: self.update_field('LonMin', self.lon_min_lineEdit.text()))
        # self.lon_sec_lineEdit.editingFinished.connect(lambda: self.update_field('LonSec', self.lon_sec_lineEdit.text()))
        # self.lon_combobox.currentTextChanged.connect(lambda: self.update_id('DirectionUnitID', 'DirectionUnitAbbreviation', self.lon_combobox.currentText(), 'DirectionUnits'))
        # self.utm_zone_lineEdit.editingFinished.connect(lambda: self.update_field('UTMZone', self.utm_zone_lineEdit.text()))
        # self.utm_n_lineEdit.editingFinished.connect(lambda: self.update_field('UTMN', self.utm_n_lineEdit.text()))
        # self.utm_e_lineEdit.editingFinished.connect(lambda: self.update_field('UTME', self.utm_e_lineEdit.text()))
        # self.elevation_lineEdit.editingFinished.connect(lambda: self.update_field('GPSElev', self.elevation_lineEdit.text()))
        # self.elevation_error_lineEdit.editingFinished.connect(lambda: self.update_field('GPSElevError', self.elevation_error_lineEdit.text()))
        # self.elevation_unit_comboBox.currentTextChanged.connect(lambda text: self.update_id('DistanceUnitID', 'DistanceUnitAbbreviation', self.elevation_unit_comboBox.currentText(), 'DistanceUnits'))
        self.column_name_comboBox.currentTextChanged.connect(lambda: self.update_id('ColumnID', 'ColumnName', self.column_name_comboBox.currentText(), 'Columns'))
        self.height_depth_lineEdit.editingFinished.connect(
            lambda: self.update_field('HeightDepth', self.height_depth_lineEdit.text()))
        self.height_depth_error_lineEdit.editingFinished.connect(
            lambda: self.update_field('HeightDepthError', self.height_depth_error_lineEdit.text()))
        self.height_depth_unit_comboBox.currentTextChanged.connect(lambda: self.update_id('HeightDepthUnitID', 'DistanceUnitAbbreviation', self.height_depth_unit_comboBox.currentText(), 'DistanceUnits'))
        # self.view_age_comboBox.currentTextChanged.connect(self.display_age)
        self.default_age_checkBox.clicked.connect(lambda: self.update_id('SampleAgeID', 'DirectAge', self.view_age_comboBox.currentText(), 'SampleAges'))
        self.oldest_dir_lineEdit.editingFinished.connect(lambda: self.update_field('OldestAge', self.oldest_dir_lineEdit.text()))
        self.youngest_dir_lineEdit.editingFinished.connect(lambda: self.update_field('YoungestAge', self.youngest_dir_lineEdit.text()))
        self.direct_unit_comboBox.currentTextChanged.connect(lambda: self.update_id('AgeUnitID', 'AgeUnitAbbreviation', self.direct_unit_comboBox.currentText(), 'AgeUnits'))
        self.direct_age_lineEdit.editingFinished.connect(lambda: self.update_field('DirectAge', self.direct_age_lineEdit.text()))
        self.direct_age_error_lineEdit.editingFinished.connect(lambda: self.update_field('DirectAgeError', self.direct_age_error_lineEdit.text()))
        self.direct_age_unit_comboBox.currentTextChanged.connect(lambda: self.update_id('AgeUnitID', 'AgeUnitAbbreviation', self.direct_age_unit_comboBox.currentText(), 'AgeUnits'))
        self.oldest_rel_comboBox.currentTextChanged.connect(
            lambda: self.update_id('OldestAgeID', 'AgeName', self.oldest_rel_comboBox.currentText(), 'Ages'))
        self.youngest_rel_comboBox.currentTextChanged.connect(
            lambda: self.update_id('YoungestAgeID', 'AgeName', self.youngest_rel_comboBox.currentText(), 'Ages'))
        self.direct_age_error_type_comboBox.currentTextChanged.connect(lambda: self.update_id('ErrorTypeID', 'ErrorTypeAbbreviation', self.direct_age_error_type_comboBox.currentText(), 'ErrorTypes'))
        self.sample_description_lineEdit.editingFinished.connect(lambda: self.update_field('SampleDescription', self.sample_description_lineEdit.text()))

        self.age_constraint_comboBox.closing.connect(lambda: self.update_tags(self.age_constraint_tree, 'AgeConstraints'))
        self.age_interpretation_comboBox.closing.connect(lambda: self.update_tags(self.age_interpretation_tree, 'AgeInterpretations'))
        self.age_source_comboBox.closing.connect(lambda: self.update_subfield_id(self.age_source_model, 'SourceID'))
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
            self.samples_table.setQuery(f'{sample_distinct_query}')
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
            self.direct_age_lineEdit.setText(f"{text_values[24]}")
            self.direct_age_error_lineEdit.setText(f"{text_values[25]}")
            self.set_comboBox_text(self.direct_age_error_type_comboBox, text_values[26])
            self.oldest_dir_lineEdit.setText(f"{text_values[27]}")
            self.youngest_dir_lineEdit.setText(f"{text_values[28]}")
            self.set_comboBox_text(self.direct_age_unit_comboBox, text_values[29])
            self.set_comboBox_text(self.oldest_rel_comboBox, text_values[30])
            self.set_comboBox_text(self.youngest_rel_comboBox, text_values[31])
            self.age_description_lineEdit.setText(text_values[32])
            self.set_comboBox_text(self.age_constraint_comboBox, text_values[33])
            self.set_comboBox_text(self.age_interpretation_comboBox, text_values[34])
            self.set_comboBox_text(self.age_source_comboBox, text_values[35])

            self.display_gps()

            # Age tags
            self.display_age(default_age_ids)
            text = self.populate_checks('SampleAges_AgeConstraints', self.age_constraint_model, self.age_constraint_tree)
            self.age_constraint_comboBox.setCurrentText(text)
            text = self.populate_checks('SampleAges_AgeInterpretations', self.age_interpretation_model, self.age_interpretation_tree)
            self.age_interpretation_comboBox.setCurrentText(text)
            text = self.populate_checks('SampleAges_Sources', self.age_source_model)
            self.age_source_comboBox.setCurrentText(text)

            # Sample tags
            text = self.populate_checks('Samples_SampleAges', self.sample_age_model)
            self.view_age_comboBox.setCurrentText(text)
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
            text = self.populate_upb_checks(self.source_model)
            self.source_comboBox.set_single_click(True)
            self.source_comboBox.setCurrentText(text)
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

    def display_age(self, default_age_ids: str):
        model = self.view_age_comboBox.model()
        # split on commas and convert everything to integers
        default_age_ids = list(map(int, default_age_ids.split(',')))
        for row in range(model.rowCount()):
            if model.index(row, 0).data() in default_age_ids:
                # Make the text at that row bold
                model.make_bold(model.index(row, 0))
            else:
                model.make_not_bold(model.index(row, 0))

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
                many_to_many_model.setFilter(f"SampleID in {tuple(self.selected_sample_list)} AND {tag_id_header} = {tag_id}")
            else:
                many_to_many_model.setFilter(f"SampleID = {self.selected_sample_list[0]} AND {tag_id_header} = {tag_id}")
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
        if table_model.tableName() == "Sources":
            # Display the ShortCitation
            col = 6
        elif "Type" or "Unit" in table_model.tableName():
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
                    else:
                        errtxt = query.lastError().text()
                        self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def update_id(self, id_field: str, name_field:str, text: str, table: str):
        table_model = QtS.QSqlTableModel()
        table_model.setTable(table)
        table_model.select()
        # table_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        table_model.setFilter(f"{name_field} is '{text}'")
        item_id = table_model.data(table_model.index(0, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if len(self.checked_sample_list) > 0:
            self.createSavepoint('before_update')
            for sample_id in self.checked_sample_list:
                query = QtS.QSqlQuery()
                query.prepare(f"UPDATE Samples SET {id_field} = {item_id} WHERE SampleID = {sample_id}")
                if query.exec():
                    self.releaseSavepoint('before_update')
                else:
                    errtxt = query.lastError().text()
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

    def update_gps(self):
        if (self.lat_deg_lineEdit.text() != "-" or self.lat_deg_lineEdit.text() != "") and (self.lon_deg_lineEdit.text() != "-" or self.lon_deg_lineEdit.text() != ""):
            lat_deg = self.lat_deg_lineEdit.text()
            lon_deg = self.lon_deg_lineEdit.text()
            if (self.lat_min_lineEdit.text() != "-" or self.lat_min_lineEdit.text() != "") or (self.lon_min_lineEdit.text() != "-" or self.lon_min_lineEdit.text() != ""):
                lat_min = self.lat_min_lineEdit.text()
                lon_min = self.lon_min_lineEdit.text()
                if (self.lat_sec_lineEdit.text() != "-" or self.lat_sec_lineEdit.text() != "") or (self.lon_sec_lineEdit.text() != "-" or self.lon_sec_lineEdit.text() != ""):
                    lat_sec = self.lat_sec_lineEdit.text()
                    lon_sec = self.lon_sec_lineEdit.text()
                    gps_format = 'DMS'
                else:
                    lat_sec = None
                    lon_sec = None
                    gps_format = 'DM'
            else:
                lat_min = None
                lon_min = None
                lat_sec = None
                lon_sec = None
                gps_format = 'D'
            if self.lat_comboBox.currentText() == '' and self.lon_comboBox.currentText() == '':
                gps_format += ' +/-'
                lat_dir = None
                lon_dir = None
            elif self.lat_comboBox.currentText() != '' and self.lon_comboBox.currentText() != '':
                gps_format += ' NSEW'
                lat_dir = self.lat_comboBox.currentText()
                lon_dir = self.lon_comboBox.currentText()
            else:
                self.msg.warning(self, 'Warning', 'Both or neither latitude and longitude directions must be given', QtW.QMessageBox.StandardButton.Ok)
                return
            utm_zone = None
            utm_n = None
            utm_e = None
        elif ((self.lat_deg_lineEdit.text() != "-" or self.lat_deg_lineEdit.text() != "") and (self.lon_deg_lineEdit.text() == "-" or self.lon_deg_lineEdit.text() == "")) or ((self.lat_deg_lineEdit.text() == "-" or self.lat_deg_lineEdit.text() == "") and (self.lon_deg_lineEdit.text() != "-" or self.lon_deg_lineEdit.text() != "")):
            # Only one of lat or lon given
            self.msg.warning(self, 'Warning', 'Both latitude and longitude must be given', QtW.QMessageBox.StandardButton.Ok)
            return
        elif (self.utm_zone_lineEdit.text() != "-" or self.utm_zone_lineEdit.text() != "") and (self.utm_n_lineEdit.text() != "-" or self.utm_n_lineEdit.text() != "") and (self.utm_e_lineEdit.text() != "-" or self.utm_e_lineEdit.text() != ""):
            utm_zone = self.utm_zone_lineEdit.text()
            utm_n = self.utm_n_lineEdit.text()
            utm_e = self.utm_e_lineEdit.text()
            gps_format = 'UTM'
            lat_deg = None
            lat_min = None
            lat_sec = None
            lat_dir = None
            lon_deg = None
            lon_min = None
            lon_sec = None
            lon_dir = None


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
        print(f"update_tags called with {model} and {table}")
        many_to_many_model = QtS.QSqlTableModel()
        many_to_many_model.setTable(f"Samples_{table}")
        many_to_many_model.select()

        if len(self.checked_sample_list) > 0:
            checked_ids , partially_checked_ids = model.traverse_checkable_tree(QtC.QModelIndex())
            self.createSavepoint('before_update')
            for sample_id in self.checked_sample_list:
                update = model.update_db(checked_ids, partially_checked_ids, sample_id)
                if update is False:
                    self.rollback('before_update')
                    errtxt = update
                    self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)
                    return
            self.releaseSavepoint('before_update')

    def update_sub_tags(self, model: TrC.CheckableTreeModel, table: str):
        field = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        aliquot_ids, spot_ids, upb_data_ids = TbC.find_sub_items(self.checked_sample_list, self.db)
        # UPbAnalayses have only one value for each field, so only one value should be checked
        # If nothing is fully checked, then nothing should be updated
        checked_ids, partially_checked_ids = model.traverse_checkable_tree(QtC.QModelIndex())
        if len(checked_ids) == 1:
            # Should only be one checked value
            self.createSavepoint('before_update')
            query = QtS.QSqlQuery()
            if len(upb_data_ids) > 1:
                query.prepare(
                    f"UPDATE UPbData SET {field} = {checked_ids[0]} WHERE UPbAnalysisID in {tuple(upb_data_ids)}")
            if len(upb_data_ids) == 1:
                query.prepare(
                    f"UPDATE UPbData SET {field} = {checked_ids[0]} WHERE UPbAnalysisID = {upb_data_ids[0]}")
            if query.exec():
                print(f"Updated {field} to {checked_ids[0]} for UPbAnalysisID {upb_data_ids}")
                self.releaseSavepoint('before_update')
            else:
                self.rollback('before_update')
                errtxt = query.lastError().text()
                self.msg.critical(self, 'Error', errtxt, QtW.QMessageBox.StandardButton.Ok)

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

class focus_event_filter(QtC.QObject):
    def eventFilter(self, object, event):
        if event.type() == QtC.QEvent.Type.FocusOut:
            if object == self.location_groupBox:
                self.update_gps()
        return super().eventFilter(object, event)