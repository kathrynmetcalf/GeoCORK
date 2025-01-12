import sys
from pathlib import Path
import sqlite3
from random import sample

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from collections import namedtuple

from PyQt6.QtCore import QMetaType

from Functions.Settings_manager import settings
from Functions import SQLUtils
from Functions import Database_views as DB_views
from Functions import Check_triggers
import Functions.Alter_database as Alter_db

# from PyQt6.QtSql import rollback
from PyQt6.sip import delete
from openpyxl.styles.builtins import total, calculation

# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'reference_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")


def set_table(model: QtS.QSqlTableModel, table: str):
    model.setTable(table)
    model.select()
    return model

class DecimalDelegate(QtW.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.decimal_places = settings.value('decimals_to_show')

    def display_text(self, value):
        if isinstance(value, float):

            return f'{value:.{self.decimal_places}f}'

class VerifiableSqlTableModel(QtS.QSqlTableModel):
    row_submitted = QtC.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.edited_indexes = []
        self.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)

    def setData(self, index, value, role = ...):
        field_type = self.record().field(index.column()).typeID()
        print(f"Field type: {field_type}, Value: {value}")
        if role == QtC.Qt.ItemDataRole.EditRole:
            if value == '' and field_type in (QMetaType.Type.Double.value, QMetaType.Type.Float.value, QMetaType.Type.Float16.value, QMetaType.Type.Int.value):
                # Set the value to NULL
                return super().setData(index, None, role)
        return super().setData(index, value, role)

    def submit(self):
        if not self.isDirty():
            return True
        if self.tableName() in SQLUtils.trigger_tables:
            # get the edited row
            current_row = self.edited_indexes[0].row()
            columns = []
            values = []
            id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            id = self.data(self.index(current_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
            for column in range(1, self.columnCount()):
                columns.append(self.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                values.append(self.data(self.index(current_row, column), QtC.Qt.ItemDataRole.DisplayRole))
            where = f'{id_header}={id}'
            error = Check_triggers.validate_update(self.tableName(), columns, values, where)
            if error is not None:
                print(error)
                return False
        if super().submit():
            self.row_submitted.emit(current_row)
            return True
        return False

    def on_row_submitted(self, row):
        record_id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        error = Check_triggers.update_modified_timestamp(self.tableName(), [record_id])
        if error is not None:
            print(error)
            return False

class VerifiableRelationalTableModel(QtS.QSqlRelationalTableModel):
    row_submitted = QtC.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.edited_indexes = []
        self.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)

    def setData(self, index, value, role = ...):
        field_type = self.record().field(index.column()).typeID()
        print(f"Field type: {field_type}, Value: {value}")
        if role == QtC.Qt.ItemDataRole.EditRole:
            if value == '' and field_type in (QMetaType.Type.Double.value, QMetaType.Type.Float.value, QMetaType.Type.Float16.value, QMetaType.Type.Int.value):
                # Set the value to NULL
                return super().setData(index, None, role)
        return super().setData(index, value, role)

    def submit(self):
        if not self.isDirty():
            return True
        if self.tableName() in SQLUtils.trigger_tables:
            # get the edited row
            if len(self.edited_indexes) == 0:
                # no rows edited
                return True
            current_row = self.edited_indexes[0].row()
            columns = []
            values = []
            id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            id = self.data(self.index(current_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
            for column in range(1, self.columnCount()):
                columns.append(self.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
                values.append(self.data(self.index(current_row, column), QtC.Qt.ItemDataRole.DisplayRole))
            where = f'{id_header}={id}'
            error = Check_triggers.validate_update(self.tableName(), columns, values, where)
            if error is not None:
                print(error)
                return False
        if super().submit():
            self.row_submitted.emit(self.edited_indexes[0].row())
            # Alter_db.populate_generated_columns()
            return True
        return False

    def on_row_submitted(self, row):
        record_id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        error = Check_triggers.update_modified_timestamp(self.tableName(), [record_id])
        if error is not None:
            print(error)
            return False

class DisplayRoundedModel(QtS.QSqlTableModel):
    def __init__(self):
        super().__init__()

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            # check the header of the selected index
            header = self.headerData(index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = super().data(index, role)
            if f'({settings.value('age_unit_abbreviation')})' in header:
                # print(f'Displaying {value}')
                return display_age(value)
            elif 'GPS' in header:
                # print(f'Displaying {value}')
                return display_gps(value)
            elif 'Elevation' in header or 'Height' in header or 'Depth' in header:
                # print(f'Displaying {value}')
                return display_value_with_error(value)
            # if the value is a number but not an integer
            elif value is not None and isinstance(value, (int, float)):
                return return_rounded(value)
        return super().data(index, role)

class ColumnTableModel(QtS.QSqlQueryModel):
    def __init__(self):
        super().__init__()
        self.default_query = DB_views.ColumnViewQuery()
        self.setQuery(self.default_query)

def SampleIfNullQuery():
    sample_ifnull_query = f'''
    SELECT 
        {SQLUtils.qsample_id},
        {SQLUtils.qigsn_ifnull},
        {SQLUtils.qsample_gps_id_ifnull},
        {SQLUtils.qcolumn_name_ifnull},
        {SQLUtils.qheight_depth_ifnull},
        {SQLUtils.qheight_depth_error_ifnull},
        {SQLUtils.qheight_depth_unit_ifnull},
        {SQLUtils.qsample_description_ifnull},
        {SQLUtils.qsample_lat_deg_ifnull},
        {SQLUtils.qsample_lat_min_ifnull},
        {SQLUtils.qsample_lat_sec_ifnull},
        {SQLUtils.qsample_lat_dir_ifnull},
        {SQLUtils.qsample_lon_deg_ifnull},
        {SQLUtils.qsample_lon_min_ifnull},
        {SQLUtils.qsample_lon_sec_ifnull},
        {SQLUtils.qsample_lon_dir_ifnull},
        {SQLUtils.qsample_utm_zone_ifnull},
        {SQLUtils.qsample_utm_northing_ifnull},
        {SQLUtils.qsample_utm_easting_ifnull},
        {SQLUtils.qsample_gps_format_ifnull},
        {SQLUtils.qsample_gps_elev_ifnull},
        {SQLUtils.qsample_gps_elev_error_ifnull},
        {SQLUtils.qsample_gps_elev_unit_ifnull},
        {SQLUtils.qsample_default_age_id_ifnull},
        {SQLUtils.qsample_direct_age_ifnull},
        {SQLUtils.qsample_direct_age_error_ifnull},
        {SQLUtils.qsample_direct_age_error_format_ifnull},
        {SQLUtils.qsample_oldest_direct_age_ifnull},
        {SQLUtils.qsample_youngest_direct_age_ifnull},
        {SQLUtils.qsample_direct_age_unit_ifnull},
        {SQLUtils.qsample_oldest_rel_age_ifnull},
        {SQLUtils.qsample_youngest_rel_age_ifnull},
        {SQLUtils.qsample_age_description_ifnull},
        {SQLUtils.qsample_age_constraint_ifnull},
        {SQLUtils.qsample_age_interpretation_ifnull},
        {SQLUtils.qsample_age_reference_ifnull}
        
    FROM Samples
    {SQLUtils.age_signature_join}
    {SQLUtils.column_join}
    {SQLUtils.column_unit_join}
    {SQLUtils.region_join}
    {SQLUtils.rock_type_join}
    {SQLUtils.sample_context_join}
    {SQLUtils.sample_sampleage_join}
    {SQLUtils.sampling_method_join}
    {SQLUtils.setting_join}
    {SQLUtils.unit_join}
    {SQLUtils.sample_age_join}
    {SQLUtils.sample_age_left_joins}
    {SQLUtils.gps_sample_join}
    {SQLUtils.gps_sample_left_joins}
    {SQLUtils.gps_column_join}
    {SQLUtils.gps_column_left_joins}
    {SQLUtils.aliquot_join}
    {SQLUtils.aliquot_context_join}
    {SQLUtils.spot_join}
    {SQLUtils.spot_composition_join}
    {SQLUtils.spot_context_join}
    {SQLUtils.upb_analysis_join}
    {SQLUtils.upb_reference_join}
    {SQLUtils.upb_labs_join}
    {SQLUtils.upb_instruments_join}
    {SQLUtils.upb_method_join}
    {SQLUtils.upb_ratio_error_format_join}
    {SQLUtils.upb_age_error_format_join}
    {SQLUtils.upb_age_unit_join}
    {SQLUtils.upb_concordance_format_join}
    {SQLUtils.upb_spot_size_unit_join}
    {SQLUtils.upb_rejection_reason_join}
    '''
    # print(sample_ifnull_query)
    return sample_ifnull_query

def ColumnIfNullQuery():
    column_ifnull_query = f'''
    SELECT 
        {SQLUtils.qcolumn_id},
        {SQLUtils.qcolumn_gps_id_ifnull},
        {SQLUtils.qcolumn_gps_converted_ifnull},
        {SQLUtils.qcolumn_lat_deg_ifnull},
        {SQLUtils.qcolumn_lat_min_ifnull},
        {SQLUtils.qcolumn_lat_sec_ifnull},
        {SQLUtils.qcolumn_lat_dir_ifnull},
        {SQLUtils.qcolumn_lon_deg_ifnull},
        {SQLUtils.qcolumn_lon_min_ifnull},
        {SQLUtils.qcolumn_lon_sec_ifnull},
        {SQLUtils.qcolumn_lon_dir_ifnull},
        {SQLUtils.qcolumn_utm_zone_ifnull},
        {SQLUtils.qcolumn_utm_northing_ifnull},
        {SQLUtils.qcolumn_utm_easting_ifnull},
        {SQLUtils.qcolumn_gps_format_id_ifnull},
        {SQLUtils.qcolumn_gps_format_ifnull},
        {SQLUtils.qcolumn_gps_elev_ifnull},
        {SQLUtils.qcolumn_gps_elev_error_ifnull},
        {SQLUtils.qcolumn_gps_elev_unit_ifnull}
    FROM Columns
    {SQLUtils.gps_column_join}
    {SQLUtils.gps_column_left_joins}
    '''
    return column_ifnull_query

class AliquotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self):
        # Select lines
        aliquots = 'AliquotName as "Aliquots"'
        aliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Contexts"'
        spots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ReferenceDisplay) as "References"'
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
                    {SQLUtils.reference_join}
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
        references = 'GROUP_CONCAT(DISTINCT ReferenceDisplay) as "References"'
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
                    {SQLUtils.upb_reference_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_labs_join}
                    GROUP BY SpotName
                    ORDER BY Spots.SpotID
                    '''

        return spot_query

def GPSIfNullQuery():
    gps_ifnull_query = f'''
    SELECT 
    GROUP_CONCAT(DISTINCT ifnull(GPSLatDeg, "Null")) as "Latitude Degrees",
    GROUP_CONCAT(DISTINCT ifnull(GPSLatMin, "Null")) as "Latitude Minutes",
    GROUP_CONCAT(DISTINCT ifnull(GPSLatSec, "Null")) as "Latitude Seconds",
    GROUP_CONCAT(DISTINCT ifnull(GPSLatDirectionID, "Null")) as "Latitude Direction",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonDeg, "Null")) as "Longitude Degrees",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonMin, "Null")) as "Longitude Minutes",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonSec, "Null")) as "Longitude Seconds",
    GROUP_CONCAT(DISTINCT ifnull(GPSLonDirectionID, "Null")) as "Longitude Direction",
    GROUP_CONCAT(DISTINCT ifnull(GPSUTMZone, "Null")) as "UTM Zone",
    GROUP_CONCAT(DISTINCT ifnull(GPSUTMN, "Null")) as "UTM Northing",
    GROUP_CONCAT(DISTINCT ifnull(GPSUTME, "Null")) as "UTM Easting",
    GROUP_CONCAT(DISTINCT ifnull(GPSFormatID, "Null")) as "GPS Format",
    GROUP_CONCAT(DISTINCT ifnull(GPSElev, "Null")) as "Elevation",
    GROUP_CONCAT(DISTINCT ifnull(GPSElevError, "Null")) as "Elevation Error",
    GROUP_CONCAT(DISTINCT ifnull(GPSElevUnitID, "Null")) as "Elevation Unit"
    FROM GPSLocations
    '''
    return gps_ifnull_query

def SampleAgeIfNullQuery():
    sample_age_ifnull_query = f'''
    SELECT 
    GROUP_CONCAT(DISTINCT ifnull(DirectAge, "Null")) as "Direct Ages",
    GROUP_CONCAT(DISTINCT ifnull(DirectAgeError, "Null")) as "Direct Age Errors",
    GROUP_CONCAT(DISTINCT ifnull(DirectAgeErrorFormatID, "Null")) as "Direct Age Error Formats",
    GROUP_CONCAT(DISTINCT ifnull(OldestDirectAge, "Null")) as "Oldest Direct Ages",
    GROUP_CONCAT(DISTINCT ifnull(YoungestDirectAge, "Null")) as "Youngest Direct Ages",
    GROUP_CONCAT(DISTINCT ifnull(DirectAgeUnitID, "Null")) as "Direct Age Units",
    GROUP_CONCAT(DISTINCT ifnull(OldestAgeID, "Null")) as "Oldest Age IDs",
    GROUP_CONCAT(DISTINCT ifnull(YoungestAgeID, "Null")) as "Youngest Age IDs",
    GROUP_CONCAT(DISTINCT ifnull(SampleAgeDescription, "Null")) as "Sample Age Descriptions"
    FROM SampleAges
    '''
    return sample_age_ifnull_query

def get_columns(table: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'PRAGMA table_xinfo("{table}")'):
        print(f"Failed to get columns for {table}")
        return query, [], [], []
    virtual = []
    stored = []
    columns = []
    modified_column = False
    while query.next():
        if not modified_column:
            if 'Modified' in query.value(1):
                modified_column = True
                columns.append(f'"{query.value(1)}"')
            elif 'Calculated' in query.value(1) or 'Display' in query.value(1):
                stored.append(f'"{query.value(1)}"')
            else:
                columns.append(f'"{query.value(1)}"')
        else:
            virtual.append(f'"{query.value(1)}"')
    return query, virtual, stored, columns

def name_column(table: str):
    if table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees:
        return 3
    elif 'Format' in table or 'Unit' in table:
        # return the column for the abbreviation
        return 2
    elif table == '"References"':
        return 6
    elif table == 'GPSLocations':
        return 1
    elif table in SQLUtils.user_viewable_tables or table == 'Spots' or table == 'SampleAges':
        return 1
    else:
        return None

def column_type(table: str, column: str):
    query = QtS.QSqlQuery()
    column_type = None
    if not query.exec(f'PRAGMA table_info("{table}")'):
        print(f"Failed to get columns for {table}")
        return column_type
    while query.next():
        if query.value(1) == column:
            column_type = query.value(2)
            break
    return column_type

def foreign_key_columns(table: str):
    query = QtS.QSqlQuery()
    foreign_keys = {}
    if not query.exec(f'PRAGMA foreign_key_list("{table}")'):
        print(f"Failed to get foreign keys for {table}")
        return foreign_keys
    while query.next():
        foreign_table = query.value(2)
        table_display_column = name_column(foreign_table)
        foreign_query = QtS.QSqlQuery()
        if not foreign_query.exec(f'PRAGMA table_info("{foreign_table}")'):
            print(f"Failed to get columns for {foreign_table}")
            return foreign_keys
        while foreign_query.next():
            if foreign_query.value(0) == table_display_column:
                table_display_header = foreign_query.value(1)
                break
        try: table_display_header
        except NameError:
            table_display_header = None
            print(f"Failed to get display column for {foreign_table}")
            return {}
        foreign_keys[query.value(3)] = {'table': query.value(2), 'id_column': query.value(4), 'display_column': table_display_header}
    return foreign_keys

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
        col = name_column(self.tableName())
        if index.column() == col:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = name_column(self.tableName())
        if index.column() == col and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if index.row() in self.checked_data.keys():
                return QtC.Qt.CheckState.Checked
            elif index.row() in self.partially_checked_data.keys():
                return QtC.Qt.CheckState.PartiallyChecked
            else:
                return QtC.Qt.CheckState.Unchecked
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value, role: QtC.Qt.ItemDataRole = ...) -> bool:
        col = name_column(self.tableName())
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
        if self.model().tableName() == '"References"':
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

class SampleAgeTableModel(QtS.QSqlQueryModel):
    def __init__(self):
        super().__init__()
        self.bolded_rows = []
        self.default_query = '''SELECT SampleAgeID, SampleAgeDisplay, DirectAge, DirectAgeError, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, DirectAgeUnitID, 
                        OldestAgeID, YoungestAgeID, SampleAgeDescription, SampleAgeCreated, SampleAgeModified FROM SampleAges'''
        self.setQuery(self.default_query)

    def tableName(self):
        return 'SampleAges'

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if index.row in self.bolded_rows and role == QtC.Qt.ItemDataRole.FontRole:
            font = QtG.QFont()
            font.setBold(True)
            return font
        if index.column() == 1 and role == QtC.Qt.ItemDataRole.DisplayRole:
            string = super().data(index, role)
            return display_age(string)
        return super().data(index, role)

    def make_bold(self, index):
        row = index.row()
        if row not in self.bolded_rows:
            self.bolded_rows.append(row)
            self.dataChanged.emit(index, index, [QtC.Qt.ItemDataRole.FontRole])

    def make_not_bold(self, index):
        row = index.row()
        if row in self.bolded_rows:
            self.bolded_rows.remove(row)
            self.dataChanged.emit(index, index, [QtC.Qt.ItemDataRole.FontRole])

def display_age(string: str):
    # split string on commas
    if ',' not in string:
        return ''
    else:
        age_elements = string.split(', ')
        # element 0 is the direct age with error, element 1 is the direct age range, and element 2 is the relative age range
        # for 0, retrieve the number in parentheses, the direct age unit ID which is the same for 0 and 1
        age_ids = age_elements[2].split('-')
        age_model = QtS.QSqlTableModel()
        age_model = set_table(age_model, 'Ages')
        if age_ids[0] != '':
            old_age_id = int(age_ids[0])
            age_model.setFilter(f'AgeID={old_age_id}')
            old_age_name = age_model.record(0).value('AgeName')
        else:
            old_age_name = ''
        if age_ids[1] != '':
            young_age_id = int(age_ids[1])
            age_model.setFilter(f'AgeID={young_age_id}')
            young_age_name = age_model.record(0).value('AgeName')
        else:
            young_age_name = ''
        if ' (' in age_elements[0]:
            # age unit is in the display, so replace ids with abbreviations
            age_unit_id = int(age_elements[0].split(' (')[1].split(')')[0])
            age_unit_model = QtS.QSqlTableModel()
            age_unit_model = set_table(age_unit_model, 'AgeUnits')
            if age_unit_id is not None:
                age_unit_model.setFilter(f'AgeUnitID={age_unit_id}')
                age_unit_abbreviation = age_unit_model.record(0).value('AgeUnitAbbreviation')
            else:
                age_unit_abbreviation = ''
            # in age_elements[0] and age_elements[1], replace the direct age unit ID with the unit abbreviation
            age_elements[0] = age_elements[0].replace(f'({age_unit_id})', f'({age_unit_abbreviation})')
            age_elements[1] = age_elements[1].replace(f'({age_unit_id})', f'({age_unit_abbreviation})')
        # age_elements[0] is in the format 'DirectAge±DirectAgeError (DirectAgeUnitID)' or 'DirectAge±DirectAgeError'
        # age_elements[1] is in the format 'OldestDirectAge-YoungestDirectAge (DirectAgeUnitID)' or 'OldestDirectAge-YoungestDirectAge'
        # replace the float values with the rounded values unless the value is an integer
        age = age_elements[0].split('±')[0]
        rounded_age = return_rounded(age)
        age_error = age_elements[0].split('±')[1].split(' ')[0]
        rounded_error = return_rounded(age_error)
        old_age = age_elements[1].split('-')[0]
        rounded_old_age = return_rounded(old_age)
        young_age = age_elements[1].split('-')[1]
        rounded_young_age = return_rounded(young_age)
        age_elements[0] = age_elements[0].replace(f'{age}±{age_error}', f'{rounded_age}±{rounded_error}')
        age_elements[1] = age_elements[1].replace(f'{old_age}-{young_age}', f'{rounded_old_age}-{rounded_young_age}')
        age_elements[2] = f'{old_age_name}-{young_age_name}'
        return ', '.join(age_elements)

def display_gps(string: str):
    if '"' in string:
        # DMS format, (lat_deg°lat_min'lat_sec" lat_dir, lon_deg°lon_min'lon_sec" lon_dir) or (lat_deg°lat_min'lat_sec", lon_deg°lon_min'lon_sec")
        lat_sec = string.split('°')[1].split('\'')[1].split('"')[0]
        lon_sec = string.split('°')[1].split('\'')[1].split('"')[1]
        rounded_lat_sec = return_rounded(lat_sec)
        rounded_lon_sec = return_rounded(lon_sec)
        string = string.replace(lat_sec, rounded_lat_sec)
        string = string.replace(lon_sec, rounded_lon_sec)
    if "'" in string:
        # DM format, (lat_deg°lat_min' lat_dir, lon_deg°lon_min' lon_dir) or (lat_deg°lat_min', lon_deg°lon_min')
        lat_min = string.split('°')[1].split('\'')[0]
        lon_min = string.split('°')[1].split('\'')[1]
        rounded_lat_min = return_rounded(lat_min)
        rounded_lon_min = return_rounded(lon_min)
        string = string.replace(lat_min, rounded_lat_min)
        string = string.replace(lon_min, rounded_lon_min)
    if '°' in string:
        # D format, (lat_deg° lat_dir, lon_deg° lon_dir)
        lat_deg = string.split('°')[0]
        lon_deg = string.split(', ')[1].split('°')[0]
        rounded_lat_deg = return_rounded(lat_deg)
        rounded_lon_deg = return_rounded(lon_deg)
        string = string.replace(lat_deg, f'{rounded_lat_deg}')
        string = string.replace(lon_deg, f'{rounded_lon_deg}')
    elif ',' in string:
        # UTM format, (UTMZone, UTMEasting, UTMNorthing)
        utm_easting = string.split(',')[1]
        utm_northing = string.split(',')[2]
        rounded_northing = return_rounded(utm_northing)
        rounded_easting = return_rounded(utm_easting)
        string = string.replace(utm_northing, rounded_northing)
        string = string.replace(utm_easting, rounded_easting)
    else:
        # No GPS given, return ''
        string = ''
    return string

def display_value_with_error(string: str):
    if '±' in string:
        # value with error, value±error (unit) or value±error
        value = string.split('±')[0]
        rounded_value = return_rounded(value)
        error = string.split('±')[1].split(' ')[0]
        rounded_error = return_rounded(error)
        string = string.replace(f'{value}±{error}', f'{rounded_value}±{rounded_error}')
    return string

def return_rounded(value: str | float | int):
    decimal_places = settings.value('decimals_to_show')
    if isinstance(value, str):
        if '.' in value:
            if float(value): # value is numbers, not text
                if value.split('.')[1] != '0':
                    rounded_value = f'{float(value):.{decimal_places}f}'
                else: # value is an integer
                    rounded_value = int(float(value))
            else:
                rounded_value = value
        else:
            rounded_value = value
    elif isinstance(value, float):
        rounded_value = f'{value:.{decimal_places}f}'
    else:
        rounded_value = value
    return rounded_value

class FontDelegate(QtW.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        font = index.data(QtC.Qt.ItemDataRole.FontRole)
        if font:
            option.font = font

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

def delete_samples(sample_ids: list):
    # Delete the selected samples and all aliquots, spots, and UPb data associated with them
    aliquot_ids, spot_ids, upb_data_ids = find_sub_items(sample_ids, 'UPbData')

    # Get a list of tables in the database
    query = QtS.QSqlQuery()
    db = QtS.QSqlDatabase.database('qt_sql_default_connection')
    tables = db.tables()

    save_query = QtS.QSqlQuery()
    if save_query.exec('SAVEPOINT before_delete') is False:
        errtxt = save_query.lastError().text()
        return errtxt

    def release_savepoint():
        save_query = QtS.QSqlQuery()
        if save_query.exec('RELEASE SAVEPOINT before_delete') is False:
            errtxt = save_query.lastError().text()
            return errtxt

    def rollback_savepoint():
        save_query = QtS.QSqlQuery()
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

def find_sub_items(sample_ids):
    # Find all the sub items of a list of samples
    query = QtS.QSqlQuery()
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

