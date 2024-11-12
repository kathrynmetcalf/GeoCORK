import sys
from pathlib import Path
import sqlite3

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from collections import namedtuple

# from PyQt6.QtSql import rollback
from PyQt6.sip import delete
from openpyxl.styles.builtins import total

# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'source_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")


class SampleTableModel(QtS.QSqlQueryModel):
    def setupQuery(self):
        # Select lines
        qsample_id = 'S.SampleID'
        qsample_name = 'SampleName AS "Sample Name"'
        qage = 'AverageAge || "±" || COALESCE(AverageAgeError, " ") as "Age (Ma)"'
        qage_range = 'COALESCE(OldestAge, " ") || "-" || COALESCE(YoungestAge, " ") as "Age Range (Ma)"'
        qgeo_age = 'COALESCE(OldA.AgeName, " ") || "-" || COALESCE(YoungA.AgeName, " ") as "Geologic Age"'
        qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures"'
        qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) as "Measured Column Name"'
        qcolumn_data = 'HeightDepth || "±" || COALESCE(HeightDepthError, " " || HeightDepthUnit) as "Column Data"'
        qlat = f'''LatDeg || "°" || LatMin || "'" || LatSec || '"' as "Latitude"'''
        qlon = f'''LonDeg || "°" || LonMin || "'" || LonSec || '"' as "Longitude"'''
        qutm_zone = 'UTMZone As "UTM Zone"'
        qutm_n = 'UTMN As "UTM Northing"'
        qutm_e = 'UTME As "UTM Easting"'
        qelev = 'Elev || "±" || COALESCE(ElevError, " " || ElevUnit) as "Elevation"'
        qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots"'
        qspots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        qreferences = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        qcontext = 'GROUP_CONCAT(DISTINCT SampleContextName) as "Sample Contexts"'
        qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) as "Sampling Methods"'
        qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"'
        qregions = 'GROUP_CONCAT(DISTINCT RegionName) as "Regions"'
        qsettings = 'GROUP_CONCAT(DISTINCT SettingName) as "Settings"'
        qunits = 'GROUP_CONCAT(DISTINCT UnitName) as "Units"'
        qupb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        qlabs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'
        qspot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        qaliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Contexts"'

        # Join lines
        old_age_join = 'LEFT JOIN Ages as OldA ON S.OldestAgeID=OldA.AgeID'
        young_age_join = 'LEFT JOIN Ages as YoungA ON S.YoungestAgeID=YoungA.AgeID'
        age_signature_join = '''LEFT JOIN Samples_AgeSignatures as S_AS ON S.SampleID=S_AS.SampleID
                                LEFT JOIN AgeSignatures as AgS ON Ags.AgeSignatureID=S_AS.AgeSignatureID'''
        column_join = '''LEFT JOIN Samples_Columns as S_C ON S.SampleID=S_C.SampleID
                                LEFT JOIN Columns as C ON C.ColumnID=S_C.ColumnID'''
        rock_type_join = '''LEFT JOIN Samples_RockTypes as S_RT ON S.SampleID=S_RT.SampleID
                            LEFT JOIN RockTypes as RT ON RT.RockTypeID=S_RT.RockTypeID'''
        region_join = '''LEFT JOIN Samples_Regions as S_R ON S.SampleID=S_R.SampleID
                            LEFT JOIN Regions as R ON R.RegionID=S_R.RegionID'''
        setting_join = '''LEFT JOIN Samples_Settings as S_ST ON S.SampleID=S_ST.SampleID
                            LEFT JOIN Settings as ST ON ST.SettingID=S_ST.SettingID'''
        unit_join = '''LEFT JOIN Samples_Units as S_U ON S.SampleID=S_U.SampleID
                            LEFT JOIN Units as U ON U.UnitID=S_U.UnitID'''
        sample_context_join = '''LEFT JOIN Samples_SampleContexts as S_SC ON S.SampleID=S_SC.SampleID
                            LEFT JOIN SampleContexts as SC ON SC.SampleContextID=S_SC.SampleContextID'''
        sampling_method_join = '''LEFT JOIN Samples_SamplingMethods as S_SM ON S.SampleID=S_SM.SampleID
                            LEFT JOIN SamplingMethods as SM ON SM.SamplingMethodID=S_SM.SamplingMethodID'''
        aliquot_join = 'LEFT JOIN Aliquots as AQ ON AQ.SampleID=S.SampleID'
        spot_join = 'LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID'
        upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
        source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'
        upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
        labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'
        spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                            LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
        spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
        aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts as AQ_AQCX ON AQ.AliquotID=AQ_AQCX.AliquotID
                            LEFT JOIN AliquotContexts as AQCX ON AQCX.AliquotContextID=AQ_AQCX.AliquotContextID'''

        sample_query = f'''
                    SELECT
                        {qsample_id},
                        {qsample_name},
                        {qlat},
                        {qlon},
                        {qutm_zone},
                        {qutm_n},
                        {qutm_e},
                        {qelev},
                        {qage},
                        {qage_range},
                        {qgeo_age},
                        {qcolumn_name},
                        {qcolumn_data},
                        {qaliquots},
                        {qspots},
                        {qreferences},
                        {qage_signature},
                        {qcontext},
                        {qrock_types},
                        {qregions},
                        {qsampling_methods},
                        {qsettings},
                        {qunits},
                        {qupb_methods},
                        {qlabs},
                        {qspot_context},
                        {qspot_compositions},
                        {qaliquot_context}
                    FROM Samples as S
                    {column_join}
                    {old_age_join}
                    {young_age_join}
                    {age_signature_join}
                    {rock_type_join}
                    {sample_context_join}
                    {aliquot_join}
                    {spot_join}
                    {upb_data_join}
                    {source_join}
                    {region_join}
                    {sampling_method_join}
                    {setting_join}
                    {unit_join}
                    {upb_method_join}
                    {labs_join}
                    {spot_context_join}
                    {spot_composition_join}
                    {aliquot_context_join}
                    GROUP BY SampleName
					ORDER BY S.SampleID
                    '''

        return sample_query

def SampleDistinctQuery():
    sample_distinct_query = f'''
    SELECT 
    GROUP_CONCAT(DISTINCT ifnull(AverageAge,"Null")) as "Average Ages",
    GROUP_CONCAT(DISTINCT ifnull(AverageAgeError,"Null")) as "Average Age Errors",
    GROUP_CONCAT(DISTINCT ifnull(ErrorSigma,"Null")) as "Error Sigmas",
    GROUP_CONCAT(DISTINCT ifnull(OldestAge,"Null")) as "Oldest Ages",
    GROUP_CONCAT(DISTINCT ifnull(YoungestAge,"Null")) as "Youngest Ages",
    GROUP_CONCAT(DISTINCT ifnull(OldestAgeID,"Null")) as "Oldest Age IDs",
    GROUP_CONCAT(DISTINCT ifnull(YoungestAgeID,"Null")) as "Youngest Age IDs",
    GROUP_CONCAT(DISTINCT ifnull(HeightDepth,"Null")) as "HeightDepths",
    GROUP_CONCAT(DISTINCT ifnull(HeightDepthError,"Null")) as "HeightDepth Errors",
    GROUP_CONCAT(DISTINCT ifnull(HeightDepthUnit,"Null")) as "HeightDepth Units",
    GROUP_CONCAT(DISTINCT ifnull(LatDeg,"Null")) as "Latitude Degrees",
    GROUP_CONCAT(DISTINCT ifnull(LatMin,"Null")) as "Latitude Minutes",
    GROUP_CONCAT(DISTINCT ifnull(LatSec,"Null")) as "Latitude Seconds",
    GROUP_CONCAT(DISTINCT ifnull(LonDeg,"Null")) as "Longitude Degrees",
    GROUP_CONCAT(DISTINCT ifnull(LonMin,"Null")) as "Longitude Minutes",
    GROUP_CONCAT(DISTINCT ifnull(LonSec,"Null")) as "Longitude Seconds",
    GROUP_CONCAT(DISTINCT ifnull(UTMZone,"Null")) as "UTM Zones",
    GROUP_CONCAT(DISTINCT ifnull(UTMN,"Null")) as "UTM Northings",
    GROUP_CONCAT(DISTINCT ifnull(UTME,"Null")) as "UTM Eastings",
    GROUP_CONCAT(DISTINCT ifnull(Elev,"Null")) as "Elevations",
    GROUP_CONCAT(DISTINCT ifnull(ElevError,"Null")) as "Elevation Errors",
    GROUP_CONCAT(DISTINCT ifnull(ElevUnit,"Null")) as "Elevation Units",
    GROUP_CONCAT(DISTINCT ifnull(Description,"Null")) as "Descriptions"
    FROM Samples
    '''
    return sample_distinct_query

class AliquotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, sample_ID):
        # Select lines
        aliquots = 'AliquotName as "Aliquots"'
        aliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Contexts"'
        spots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

        # Join lines
        aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts as AQ_AQCX ON AQ.AliquotID=AQ_AQCX.AliquotID
                            LEFT JOIN AliquotContexts as AQCX ON AQCX.AliquotContextID=AQ_AQCX.AliquotContextID'''
        spot_join = 'LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID'
        spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                            LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
        spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
        upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
        source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'
        upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
        labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'

        aliquot_query = f'''
                    SELECT
                        {aliquots},
                        {aliquot_context},
                        {spots},
                        {spot_context},
                        {spot_compositions},
                        {references},
                        {upb_methods},
                        {labs}
                    FROM Aliquots as AQ
                    {aliquot_context_join}
                    {spot_join}
                    {spot_context_join}
                    {spot_composition_join}
                    {upb_data_join}
                    {source_join}
                    {upb_method_join}
                    {labs_join}
                    WHERE SampleID = {sample_ID}
                    GROUP BY AliquotName
                    '''

        return aliquot_query


class SpotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, parent_id, id_type='sample'):
        # Select lines
        spots = 'SpotName as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

        # Join lines'
        spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                            LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
        spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
        upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
        source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'
        upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
        labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'

        # Where statement
        if id_type == 'sample':
            where = f'WHERE SampleID = {parent_id}'
        elif id_type == 'aliquot':
            where = f'WHERE AliquotID = {parent_id}'
        else:
            return 'Error - must select a parent ID'

        spot_query = f'''
                    SELECT
                        {spots},
                        {spot_context},
                        {spot_compositions},
                        {references},
                        {upb_methods},
                        {labs}
                    FROM Spots as SP
                    {spot_context_join}
                    {spot_composition_join}
                    {upb_data_join}
                    {source_join}
                    {upb_method_join}
                    {labs_join}
                    {where}
                    GROUP BY SpotName
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
        for col in range(0, 26):
            # hide all but name and description
            if col != 1 and col != 23:
                self.hideColumn(col)
        self.resizeColumnsToContents()
        self.clicked.connect(self.toggle_check_state)


    def toggle_check_state(self, index: QtC.QModelIndex):
        if self.model():
            self.model().dataChanged.connect(self.update)
            if index.isValid() and QtC.Qt.ItemFlag.ItemIsUserCheckable in self.model().flags(index):
                current_state = self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)
                new_state = QtC.Qt.CheckState.Unchecked if current_state == QtC.Qt.CheckState.Checked else QtC.Qt.CheckState.Checked
                self.model().setData(index, new_state, QtC.Qt.ItemDataRole.CheckStateRole)

class CheckableSQLTableModel(QtS.QSqlTableModel):
    def __init__(self):
        super().__init__()
        self.checked_data = {}

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if index.column() == 1 and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if index.row() not in self.checked_data.keys():
                return QtC.Qt.CheckState.Unchecked
            else:
                return QtC.Qt.CheckState.Checked
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value, role: QtC.Qt.ItemDataRole = ...) -> bool:
        if index.column() == 1 and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if value == QtC.Qt.CheckState.Checked:
                self.checked_data[index.row()] = value
            else:
                if index.row() in self.checked_data.keys():
                    self.checked_data.pop(index.row())
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

class CheckableSampleComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.closedOnLineEditClick = False
        self.tableView = CheckableSampleTableView()
        self.setView(self.tableView)
        self.setSizeAdjustPolicy(QtW.QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        self.tableView.viewport().installEventFilter(self)

    def set_line_edit_text(self, text):
        self.lineEdit().setText(text)

    def showPopup(self):
        self.tableView.resizeColumnsToContents()
        columns = self.model().columnCount()
        width_hint = 0
        for col in range(0, columns):
            # hide all but name and description
            col_name = self.model().headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if "Name" in col_name or "Description" in col_name:
                self.tableView.showColumn(col)
                # Add up the size hints for all the visible columns
                width_hint += self.tableView.columnWidth(col)
            else:
                self.tableView.hideColumn(col)
        self.tableView.setSortingEnabled(False)
        width_c1 = self.tableView.sizeHintForColumn(1)
        width_tree = self.tableView.sizeHint().width()
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
                self.tableView.toggle_check_state(self.tableView.currentIndex())
                self.showPopup()
                return True
            return super().eventFilter(obj, event)

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
            errtxt = query.lastError().text()
            return errtxt

    def rollback_savepoint():
        save_query = QtS.QSqlQuery(db)
        if save_query.exec('ROLLBACK TO before_delete') is False:
            errtxt = query.lastError().text()
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

# class table_proxy_model(QtC.QSortFilterProxyModel):
#     def __int__(self):
#         super().__init__()
#
#         sourceModel.dataChanged.connect(self.sourceDataChanged)
#
#     def sourceDataChanged(self, ):
