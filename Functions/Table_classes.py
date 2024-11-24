import sys
from pathlib import Path
import sqlite3
from random import sample

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from collections import namedtuple

from Functions import SQLUtils

# from PyQt6.QtSql import rollback
from PyQt6.sip import delete
from openpyxl.styles.builtins import total, calculation

# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'source_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")


def set_table(model: QtS.QSqlTableModel, table: str):
    model.setTable(table)
    model.select()
    return model



class SampleTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, ids_to_show=None, rows_per_page=None, offset=None):
        sample_query = f'''
                    SELECT
                        {SQLUtils.qsample_id},
                        {SQLUtils.qsample_name},
                        {SQLUtils.qelev},
                        {SQLUtils.qage},
                        {SQLUtils.qage_range},
                        {SQLUtils.qgeo_age},
                        {SQLUtils.qcolumn_name},
                        {SQLUtils.qcolumn_data},
                        {SQLUtils.qaliquots},
                        {SQLUtils.qspots},
                        {SQLUtils.qsources},
                        {SQLUtils.qage_signature},
                        {SQLUtils.qsample_context},
                        {SQLUtils.qrock_types},
                        {SQLUtils.qregions},
                        {SQLUtils.qsampling_methods},
                        {SQLUtils.qsettings},
                        {SQLUtils.qunits},
                        {SQLUtils.qupb_methods},
                        {SQLUtils.qlabs},
                        {SQLUtils.qspot_context},
                        {SQLUtils.qspot_compositions},
                        {SQLUtils.qaliquot_context}
                    FROM Samples
                    {SQLUtils.age_signature_join}
                    {SQLUtils.column_join}
                    {SQLUtils.region_join}
                    {SQLUtils.rock_type_join}
                    {SQLUtils.sample_context_join}
                    {SQLUtils.sample_sampleage_join}
                    {SQLUtils.sampling_method_join}
                    {SQLUtils.setting_join}
                    {SQLUtils.unit_join}
                    {SQLUtils.sample_age_join}
                    {SQLUtils.sample_age_error_type_join}
                    {SQLUtils.sample_age_unit_join}
                    {SQLUtils.sample_old_age_join}
                    {SQLUtils.sample_young_age_join}
                    {SQLUtils.sampleage_ageconstraint_join}
                    {SQLUtils.sampleage_ageinterpretation_join}
                    {SQLUtils.gps_sample_join}
                    {SQLUtils.gps_column_join}
                    {SQLUtils.aliquot_join}
                    {SQLUtils.aliquot_context_join}
                    {SQLUtils.spot_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.spot_context_join}
                    {SQLUtils.upb_analysis_join}
                    {SQLUtils.upb_source_join}
                    {SQLUtils.upb_labs_join}
                    {SQLUtils.upb_instruments_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_ratio_error_type_join}
                    {SQLUtils.upb_age_error_type_join}
                    {SQLUtils.upb_age_unit_join}
                    {SQLUtils.upb_concordance_type_join}
                    {SQLUtils.upb_spot_size_unit_join}
                    {SQLUtils.upb_rejection_reason_join}
                    {f"WHERE Samples.SampleID IN {ids_to_show}" if ids_to_show is not None else ""}
                    GROUP BY Samples.SampleName
					ORDER BY Samples.SampleID
					{f"LIMIT {rows_per_page}" if rows_per_page is not None else ""}
					{f"OFFSET {offset}" if offset is not None else ""}
                    '''

        simple_sample_query = f'''
                    SELECT
                        {SQLUtils.qsample_id},
                        {SQLUtils.qsample_name},
                        {SQLUtils.qelev}
                    FROM Samples
                    {SQLUtils.gps_sample_join}
                    '''

        print(simple_sample_query)
        return sample_query

def SampleDistinctQuery():
    sample_distinct_query = f'''
    SELECT 
    GROUP_CONCAT(DISTINCT ifnull(DirectAge,"Null")) as "Direct Ages",
    GROUP_CONCAT(DISTINCT ifnull(DirectAgeError,"Null")) as "Direct Age Errors",
    GROUP_CONCAT(DISTINCT ifnull(DirectAgeErrorTypeID,"Null")) as "Error Sigmas",
    GROUP_CONCAT(DISTINCT ifnull(OldestDirectAge,"Null")) as "Oldest Ages",
    GROUP_CONCAT(DISTINCT ifnull(YoungestDirectAge,"Null")) as "Youngest Ages",
    GROUP_CONCAT(DISTINCT ifnull(OldestAgeID,"Null")) as "Oldest Age IDs",
    GROUP_CONCAT(DISTINCT ifnull(YoungestAgeID,"Null")) as "Youngest Age IDs",
    GROUP_CONCAT(DISTINCT ifnull(HeightDepth,"Null")) as "HeightDepths",
    GROUP_CONCAT(DISTINCT ifnull(HeightDepthError,"Null")) as "HeightDepth Errors",
    GROUP_CONCAT(DISTINCT ifnull(HeightDepthUnitID,"Null")) as "HeightDepth Units",
    GROUP_CONCAT(DISTINCT ifnull(GPSLatDeg,"Null")) as "Latitude Degrees",
    GROUP_CONCAT(DISTINCT ifnull(GPSLatMin,"Null")) as "Latitude Minutes",
    GROUP_CONCAT(DISTINCT ifnull(GPSLatSec,"Null")) as "Latitude Seconds",
    GROUP_CONCAT(DISTINCT ifnull(GPSLatDirectionID,"Null")) as "Latitude Directions",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonDeg,"Null")) as "Longitude Degrees",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonMin,"Null")) as "Longitude Minutes",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonSec,"Null")) as "Longitude Seconds",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonDirectionID,"Null")) as "Longitude Directions",
    GROUP_CONCAT(DISTINCT ifnull(GPSUTMZone,"Null")) as "UTM Zones",
    GROUP_CONCAT(DISTINCT ifnull(GPSUTMN,"Null")) as "UTM Northings",
    GROUP_CONCAT(DISTINCT ifnull(GPSUTME,"Null")) as "UTM Eastings",
    GROUP_CONCAT(DISTINCT ifnull(Elev,"Null")) as "Elevations",
    GROUP_CONCAT(DISTINCT ifnull(ElevError,"Null")) as "Elevation Errors",
    GROUP_CONCAT(DISTINCT ifnull(ElevUnitID,"Null")) as "Elevation Units",
    GROUP_CONCAT(DISTINCT ifnull(SampleDescription,"Null")) as "Descriptions"
    FROM Samples
    '''
    return sample_distinct_query

class AliquotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self):
        # Select lines
        aliquots = 'AliquotName as "Aliquots"'
        aliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Contexts"'
        spots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

        aliquot_query = f'''
                    SELECT
                        Aliquots.AliquotID,
                        {aliquots},
                        {aliquot_context},
                        {spots},
                        {spot_context},
                        {spot_compositions},
                        {references},
                        {upb_methods},
                        {labs}
                    FROM Aliquots
                    {SQLUtils.aliquot_context_join}
                    {SQLUtils.spot_join}
                    {SQLUtils.spot_context_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.upb_data_join}
                    {SQLUtils.source_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.labs_join}
                    GROUP BY AliquotName
                    ORDER BY Aliquots.AliquotID
                    '''
        return aliquot_query


class SpotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, ids_to_show):
        # Select lines
        spots = 'SpotName as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

        spot_query = f'''
                    SELECT
                        Spots.SpotID,
                        {spots},
                        {spot_context},
                        {spot_compositions},
                        {references},
                        {upb_methods},
                        {labs}
                    FROM Spots
                    {SQLUtils.spot_context_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.upb_analysis_join}
                    {SQLUtils.upb_source_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_labs_join}
                    GROUP BY SpotName
                    ORDER BY Spots.SpotID
                    '''

        return spot_query

class ComboList(QtW.QComboBox):
    def __init__(self, parent, model):
        super().__init__(parent)
        self.setModel(model)
        self.currentTextChanged.connect(self.combo_value)

    def combo_value(self):
        print(self.currentText())

class CheckableSampleTableView(QtW.QTableView):
    def __init__(self):
        super().__init__()
        # for col in range(0, 26):
        #     # hide all but name and description
        #     if col != 1 and col != 23:
        #         self.hideColumn(col)
        self.resizeColumnsToContents()
        self.clicked.connect(self.toggle_check_state)


    def toggle_check_state(self, index: QtC.QModelIndex):
        if self.model():
            self.model().dataChanged.connect(self.update)
            if index.isValid() and QtC.Qt.ItemFlag.ItemIsUserCheckable in self.model().flags(index):
                current_state = self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)
                new_state = QtC.Qt.CheckState.Unchecked if current_state == QtC.Qt.CheckState.Checked else QtC.Qt.CheckState.Checked
                self.model().setData(index, new_state, QtC.Qt.ItemDataRole.CheckStateRole)

class CheckableSqlTableModel(QtS.QSqlTableModel):
    def __init__(self):
        super().__init__()
        self.checked_data = {}
        self.partially_checked_data = {}

    def flags(self, index):
        flags = super().flags(index)
        if self.tableName() == 'Sources':
            col = 6
        else:
            col = 1
        if index.column() == col:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if self.tableName() == 'Sources':
            col = 6
        else:
            col = 1
        if index.column() == col and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if index.row() in self.checked_data.keys():
                return QtC.Qt.CheckState.Checked
            elif index.row() in self.partially_checked_data.keys():
                return QtC.Qt.CheckState.PartiallyChecked
            else:
                return QtC.Qt.CheckState.Unchecked
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value, role: QtC.Qt.ItemDataRole = ...) -> bool:
        if self.tableName() == 'Sources':
            col = 6
        else:
            col = 1
        if index.column() == col and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if value == QtC.Qt.CheckState.Checked:
                self.checked_data[index.row()] = value
            elif value == QtC.Qt.CheckState.PartiallyChecked:
                self.partially_checked_data[index.row()] = value
            else:
                if index.row() in self.checked_data.keys():
                    self.checked_data.pop(index.row())
                if index.row() in self.partially_checked_data.keys():
                    self.partially_checked_data.pop(index.row())
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

class CheckableComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.closedOnLineEditClick = True
        self.single_click = False
        self.tableView = CheckableSampleTableView()
        self.setView(self.tableView)
        self.setSizeAdjustPolicy(QtW.QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.tableView.viewport().installEventFilter(self)

    def set_single_click(self, single_click):
        self.single_click = single_click

    def set_line_edit_text(self, text):
        self.lineEdit().setText(text)

    def clear_all_checks(self):
        if self.model().tableName() == 'Sources':
            col = 6
        else:
            col = 1
        for row in range(self.model().rowCount()):
            index = self.model().index(row, col)
            if row == self.tableView.currentIndex().row():
                self.model().setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            else:
                self.model().setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            print(f"Changed state to {self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)}")


    def showPopup(self):
        self.tableView.resizeColumnsToContents()
        columns = self.model().columnCount()
        width_hint = 0
        for col in range(0, columns):
            # hide all but name and description
            col_name = self.model().headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if "Name" in col_name or "Description" in col_name or "ShortCitation" in col_name:
                self.tableView.showColumn(col)
                # Add up the size hints for all the visible columns
                width_hint += self.tableView.columnWidth(col)
            else:
                self.tableView.hideColumn(col)
        self.tableView.setSortingEnabled(False)
        width_c1 = self.tableView.sizeHintForColumn(1)
        if width_hint < 2 * width_c1:
            size_hint = width_hint
        else:
            size_hint = 2 * width_c1
        self.tableView.setMinimumWidth(size_hint)
        # row height * number of rows plus header height
        total_height = self.tableView.rowHeight(0)*self.tableView.model().rowCount() + self.tableView.horizontalHeader().height()
        if total_height > self.tableView.sizeHint().height():
            self.tableView.setFixedHeight(self.tableView.sizeHint().height())
        else:
            self.tableView.setFixedHeight(total_height)
        super().showPopup()
        # print(f"Height of dropdown: {self.tableView.height()}")

    def hidePopup(self):
        super().hidePopup()
        self.closing.emit()

    def eventFilter(self, obj, event):
        if obj == self.lineEdit():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                if self.closedOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return super().eventFilter(obj, event)

        if obj == self.tableView.viewport():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                if self.single_click:
                    print(f"Clicked text: {self.tableView.currentIndex().data()}")
                    print("Single click mode enabled")
                    self.clear_all_checks()
                    self.set_line_edit_text(self.tableView.currentIndex().data())
                self.tableView.toggle_check_state(self.tableView.currentIndex())
                self.showPopup()
                return True
            return super().eventFilter(obj, event)

def comboBox_display_table(comboBox):
    comboBox.tableView.resizeColumnsToContents()
    columns = comboBox.model().columnCount()
    width_hint = 0
    for col in range(0, columns):
        # hide all but name and description
        col_name = comboBox.model().headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        if "Name" in col_name or "Description" in col_name:
            comboBox.tableView.showColumn(col)
            # Add up the size hints for all the visible columns
            width_hint += comboBox.tableView.columnWidth(col)
        else:
            comboBox.tableView.hideColumn(col)
    comboBox.tableView.setSortingEnabled(False)
    width_c1 = comboBox.tableView.sizeHintForColumn(1)
    width_tree = comboBox.tableView.sizeHint().width()
    if width_hint < 2 * width_c1:
        size_hint = width_hint
    else:
        size_hint = 2 * width_c1
    comboBox.tableView.setMinimumWidth(size_hint)
    # row height * number of rows plus header height
    total_height = comboBox.tableView.rowHeight(
        0) * comboBox.tableView.model().rowCount() + comboBox.tableView.horizontalHeader().height()
    if total_height > comboBox.tableView.sizeHint().height():
        comboBox.tableView.setFixedHeight(comboBox.tableView.sizeHint().height())
    else:
        comboBox.tableView.setFixedHeight(total_height)

def delete_samples(sample_ids: list, db: QtS.QSqlDatabase):
    # Delete the selected samples and all aliquots, spots, and UPb data associated with them
    aliquot_ids, spot_ids, upb_data_ids = find_sub_items(sample_ids, 'UPbData', db)

    # Get a list of tables in the database
    tables = db.tables()
    query = QtS.QSqlQuery(db)

    save_query = QtS.QSqlQuery(db)
    if save_query.exec('SAVEPOINT before_delete') is False:
        errtxt = save_query.lastError().text()
        return errtxt

    def release_savepoint():
        save_query = QtS.QSqlQuery(db)
        if save_query.exec('RELEASE SAVEPOINT before_delete') is False:
            errtxt = save_query.lastError().text()
            return errtxt

    def rollback_savepoint():
        save_query = QtS.QSqlQuery(db)
        if save_query.exec('ROLLBACK TO before_delete') is False:
            errtxt = save_query.lastError().text()
            return errtxt

    def delete_query(table, ids, id_name):
        if len(ids) > 0:
            query.prepare(f'DELETE FROM {table} WHERE {id_name} in {tuple(ids)}')
        if len(ids) == 1:
            query.prepare(f'DELETE FROM {table} WHERE {id_name}={ids[0]}')
        if not query.exec():
            rollback_savepoint()
            return query.lastError().text()

    delete_query('UPbData', upb_data_ids, 'UPbDataID')
    for table in tables:
        if 'Spots_' in table:
            delete_query(f'Spots_{table}', spot_ids, 'SpotID')
        elif 'Aliquots_' in table:
            delete_query(f'Aliquots_{table}', aliquot_ids, 'AliquotID')
        elif 'Samples_' in table:
            delete_query(f'Samples_{table}', sample_ids, 'SampleID')
    delete_query('Spots', spot_ids, 'SpotID')
    delete_query('Aliquots', aliquot_ids, 'AliquotID')
    delete_query('Samples', sample_ids, 'SampleID')

    release_savepoint()

def find_sub_items(sample_ids, db):
    # Find all the sub items of a list of samples
    query = QtS.QSqlQuery(db)
    aliquot_ids = []
    spot_ids = []
    upb_data_ids = []
    sample_table = QtS.QSqlTableModel()
    sample_table.setTable('Samples')
    sample_table.select()
    aliquot_table = QtS.QSqlTableModel()
    aliquot_table.setTable('Aliquots')
    aliquot_table.select()
    spot_table = QtS.QSqlTableModel()
    spot_table.setTable('Spots')
    spot_table.select()
    UPb_data_table = QtS.QSqlTableModel()
    UPb_data_table.setTable('UPbData')
    UPb_data_table.select()

    for sample_id in sample_ids:
        aliquot_table.setFilter(f'SampleID={sample_id}')
        for row in range(aliquot_table.rowCount()):
            aliquot_id = aliquot_table.record(row).value('AliquotID')
            aliquot_ids.append(aliquot_id)
            spot_table.setFilter(f'AliquotID={aliquot_id}')
            for row in range(spot_table.rowCount()):
                spot_id = spot_table.record(row).value('SpotID')
                spot_ids.append(spot_id)
                UPb_data_table.setFilter(f'SpotID={spot_id}')
                for row in range(UPb_data_table.rowCount()):
                    upb_data_id = UPb_data_table.record(row).value('UPbAnalysisID')
                    upb_data_ids.append(upb_data_id)
    return aliquot_ids, spot_ids, upb_data_ids

