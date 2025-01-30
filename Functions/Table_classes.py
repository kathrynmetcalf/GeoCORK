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
import Functions.Text_manipulations as TxM
from Functions import Check_triggers

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

class FontDelegate(QtW.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        font = index.data(QtC.Qt.ItemDataRole.FontRole)
        if font:
            option.font = font

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
            if isinstance(value, str):
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
            else:
                return value
        return super().data(index, role)

    def unrounded_data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        return super().data(index, role)

class DisplayRoundedQueryModel(QtS.QSqlQueryModel):
    def __init__(self):
        super().__init__()

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            # check the header of the selected index
            header = self.headerData(index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = super().data(index, role)
            if isinstance(value, str):
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
            else:
                return value
        return super().data(index, role)

    def unrounded_data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        return super().data(index, role)

class VerifiableSqlTableModel(DisplayRoundedModel):
    row_submitted = QtC.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.edited_indexes = []
        self.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnRowChange)
        self.submitError = ''
        self.headerToFix = ''

    def setData(self, index, value, role = ...):
        field_type = self.record().field(index.column()).typeID()
        print(f"Field type: {field_type}, Value: {value}")
        if role == QtC.Qt.ItemDataRole.EditRole:
            if value == '' and field_type in (QMetaType.Type.Double.value, QMetaType.Type.Float.value, QMetaType.Type.Float16.value, QMetaType.Type.Int.value, QMetaType.Type.UInt.value):
                # Set the value to NULL
                value = None
            elif '.' not in str(value):
                # Make sure integers don't have decimals added on
                try:
                    value = int(value)
                except ValueError:
                    pass
            self.edited_indexes.append(index)
            # return super().setData(index, value, role)
        return super().setData(index, value, role)

    def submit(self):
        if not self.edited_indexes:
            # no changes to submit
            return True
        # get the edited row
        current_row = self.edited_indexes[0].row()
        if self.tableName() in SQLUtils.trigger_tables:
            if not self.verify_row(current_row):
                return False
        if super().submit():
            self.row_submitted.emit(current_row)
            self.edited_indexes = []
            self.submitError = ''
            self.headerToFix = ''
            return True
        else:
            return False

    # def on_row_submitted(self, row):
    #     record_id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
    #     error, header = Check_triggers.update_modified_timestamp(self.tableName(), [record_id])
    #     if error is not None:
    #         print(error)
    #         return False

    def verify_row(self, current_row):
        columns = []
        values = []
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(current_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        foreign_table = QtS.QSqlTableModel()
        for column in range(1, self.columnCount()):
            header = self.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = self.data(self.index(current_row, column), QtC.Qt.ItemDataRole.DisplayRole)
            if 'ID' in header and type(value) is not int:
                # get the ID from the display value
                set_value = self.get_foreign_id(self.tableName(), header, value)
            else:
                set_value = value
            columns.append(header)
            values.append(set_value)
        where = f'{id_header}={id}'
        error, header = Check_triggers.validate_update(self.tableName(), columns, values, where)
        if error is not None:
            self.submitError = error
            self.headerToFix = header
            return False
        return True

class VerifiableSqlViewModel(VerifiableSqlTableModel):
    row_submitted = QtC.pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.table = ''
        self.setEditStrategy(QtS.QSqlTableModel.EditStrategy.OnManualSubmit)

    def setTable(self, tableName):
        if 'View' in tableName:
            if 'Column' in tableName:
                self.table = 'Columns'
            elif 'Sample' in tableName:
                self.table = 'Samples'
            super().setTable(tableName)
        else:
            print('Table name is not a view')

    def submit(self):
        if not self.isDirty():
            return True
        # get the edited row
        current_row = self.edited_indexes[0].row()
        columns = []
        values = []
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(current_row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        foreign_table = QtS.QSqlTableModel()
        # Need to map the joined columns to the actual table columns
        for column in range(1, self.columnCount()):
            header = self.headerData(column, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = self.unrounded_data(self.index(current_row, column), QtC.Qt.ItemDataRole.DisplayRole)
            # if header == 'Total Height/Depth':
            #     set_header = 'ColumnTotalHeightDepth'
            #     set_value = value
            if 'Unit' in header:
                set_header = 'ColumnTotalHeightDepthUnitID'
                set_table(foreign_table, 'DistanceUnits')
                foreign_table.setFilter(f'DistanceUnitAbbreviation="{value}"')
                set_value = foreign_table.record(0).value('DistanceUnitID')
            elif 'GPS' in header:
                set_header = 'ColumnBaseGPSID'
                query = QtS.QSqlQuery()
                query.exec(f'SELECT GPSLocationID FROM GPSLocations WHERE GPSLocationDisplay="{value}"')
                query.next()
                set_value = query.value(0)
                # set_value = foreign_table.record(0).value('GPSLocationID')
            else:
                set_header = header
                set_value = value
            columns.append(set_header)
            values.append(set_value)

        error, header = Check_triggers.validate_update(self.table, columns, values, f'{id_header}={id}')
        if error is not None:
            self.submitError = error
            self.headerToFix = header
            return False
        column_str = ", ".join(columns)
        # create a string of question marks separated by commas for the values
        value_str = ", ".join('?' * len(values))
        query = QtS.QSqlQuery()
        query.prepare(f'UPDATE {self.table} SET ({column_str}) = ({value_str}) WHERE {id_header}={id}')
        for i, value in enumerate(values):
            query.bindValue(i, value)
        if not query.exec():
            print(f'Failed to update {self.table} with {column_str}={value_str}')
            return False
        self.row_submitted.emit(current_row)
        if not self.on_row_submitted(current_row):
            return False
        self.edited_indexes = []
        self.submitError = ''
        self.headerToFix = ''
        return True

    def on_row_submitted(self, row):
        record_id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        error = Check_triggers.update_modified_timestamp(self.table, [record_id])
        if error is not None:
            print(error)
            return False

    def deleteRowFromTable(self, row):
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        query = QtS.QSqlQuery()
        if not query.exec(f'DELETE FROM {self.table} WHERE {id_header}={id}'):
            print(f'Failed to delete {id} from {self.table}')
            return False
        return True

class ReadableProxyModel(QtC.QSortFilterProxyModel):
    def __init__(self):
        super().__init__()

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: QtC.Qt.ItemDataRole = ...):
        if role == QtC.Qt.ItemDataRole.DisplayRole and orientation == QtC.Qt.Orientation.Horizontal:
            header = super().headerData(section, orientation, role)
            if 'ID' in header:
                if 'Elev' in header:
                    header.replace('ID', f'({settings.value('elevation_unit_abbreviation')})')
                elif 'AgeUnit' in header:
                    header.replace('ID', f'({settings.value('age_unit_abbreviation')})')
                elif 'RatioErrorFormat' in header:
                    header.replace('ID', f'({settings.value('ratio_error_format_abbreviation')})')
                elif 'AgeErrorFormat' in header:
                    header.replace('ID', f'({settings.value('age_error_format_abbreviation')})')
                elif 'Height' in header:
                    header.replace('ID', f'({settings.value('heightdepth_unit_abbreviation')})')
                elif 'GPSFormat' in header:
                    header.replace('ID', f'({settings.value('gps_format_abbreviation')})')
                elif 'SpotSize' in header:
                    header.replace('ID', f'({settings.value('spotsize_unit_abbreviation')})')
                elif 'ConcordanceFormat' in header:
                    header.replace('ID', f'({settings.value('concordance_format_abbreviation')})')
            if 'GPSLocationConverted' in header:
                header = 'GPS Location'
            elif 'GPSElev || ' in header:
                header = f'Elevation ({settings.value('elevation_unit_abbreviation')})'
            elif 'TotalHeightDepth' in header:
                header = f'Total Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
            elif 'HeightDepth' in header:
                header = f'Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
            elif 'AgeDisplay' in header:
                header = f'Age ({settings.value('age_unit_abbreviation')})'
            elif 'AgeReferences' in header:
                header = 'Age References'
            elif 'SUM' in header:
                header = 'Accepted/TotalUPbAnalayses'
            elif 'COUNT' in header and 'SpotID' in header:
                header = 'Number of Spots'
            elif 'SpotSize' in header:
                header = f'Spot Size ({settings.value('spotsize_unit_abbreviation')})'
            elif 'DISTINCT' in header:
                # Form is 'GROUP_CONCAT(DISTINCT table.column)' or 'GROUP_CONCAT(DISTINCT column)', get column
                if '.' in header:
                    header = header.split('(')[1].split(')')[0].split('.')[-1]
                else:
                    header = header.split('(')[1].split(')')[0].split(' ')[-1]
            if 'Name' in header and (header != 'SampleName' and header != 'AliquotName' and header != 'SpotName'):
                header = header.replace('Name', '')
                if header.endswith('y'):
                    header = header[:-1] + 'ies'
                elif header.endswith('is'):
                    header = header[:-2] + 'es'
                else:
                    header += 's'
            if 'Abbreviation' in header:
                header = header.replace('Abbreviation', '')
            if 'Display' in header:
                header = header.replace('Display', '')
            if 'Calculated' in header:
                header = header.replace('Calculated', '')
            if 'ppm' in header:
                header = header.replace('ppm', '(ppm)')
            if 'cps' in header:
                header = header.replace('cps', '(cps)')
            header = TxM.add_spaces_camel(header)
            return header
        super().headerData(section, orientation, role)

def get_headers(table: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'PRAGMA table_xinfo("{table}")'):
        print(f"Failed to get headers for {table}")
        return []
    headers = []
    while query.next():
        headers.append(query.value(1))
    return headers

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
        return 9
    elif table == 'GPSLocations':
        return 1
    elif table in SQLUtils.user_viewable_tables or table == 'Spots' or table == 'SampleAges':
        return 1
    else:
        return None

def get_name_from_id(table: str, id: int):
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    if not query.exec(f'SELECT {headers[name_column(table)]} FROM {table} WHERE {headers[0]}={id}'):
        print(f"Failed to get name for {id} in {table}")
        return None
    query.next()
    return query.value(0)

def get_id_from_name(table: str, name: str):
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    if not query.exec(f'SELECT {headers[0]} FROM {table} WHERE {headers[name_column(table)]}="{name}"'):
        print(f"Failed to get ID for {name} in {table}")
        return None
    query.next()
    return query.value(0)

def get_column_types(table: str):
    query = QtS.QSqlQuery()
    column_types = []
    if not query.exec(f'PRAGMA table_info("{table}")'):
        print(f"Failed to get columns for {table}")
        return column_types
    while query.next():
        column_types.append(query.value(2))
    return column_types

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


def get_foreign_id_table(table: str, header: str, value):
    if 'ID' not in header:
        print(f"Header {header} does not contain ID")
        return value
    foreign_keys = foreign_key_columns(table)
    if header in foreign_keys.keys():
        foreign_table = foreign_keys[header]['table']
        id_column = foreign_keys[header]['id_column']
        display_column = foreign_keys[header]['display_column']
        query = QtS.QSqlQuery()
        if not query.exec(f'SELECT {id_column} FROM {foreign_table} WHERE {display_column}="{value}"'):
            print(f"Failed to get ID for {value} in {foreign_table}")
            return value
        query.next()
        return query.value(0), foreign_table

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

class CheckableSqlTableModel(DisplayRoundedModel):
    def __init__(self):
        super().__init__()
        self.primary_key_column = 0
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

class CheckableSqlQueryModel(DisplayRoundedQueryModel):
    def __init__(self):
        super().__init__()
        self.checked_data = {}
        self.partially_checked_data = {}

    def setQuery(self, query):
        super().setQuery(query)
        self.table = query.split('FROM ')[1].split(' ')[0]

    def tableName(self):
        return self.table

    def flags(self, index):
        flags = super().flags(index)
        col = name_column(self.table)
        if index.column() == col:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = name_column(self.table)
        if index.column() == col and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if index.row() in self.checked_data.keys():
                return QtC.Qt.CheckState.Checked
            elif index.row() in self.partially_checked_data.keys():
                return QtC.Qt.CheckState.PartiallyChecked
            else:
                return QtC.Qt.CheckState.Unchecked
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value, role: QtC.Qt.ItemDataRole = ...) -> bool:
        col = name_column(self.table)
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

class CheckableComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    edit_triggered = QtC.pyqtSignal(QtW.QComboBox)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.closedOnLineEditClick = True
        self.single_click = False
        self.tableView = CheckableSampleTableView()
        self.setView(self.tableView)
        self.setSizeAdjustPolicy(QtW.QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.context_menu = False

        self.tableView.viewport().installEventFilter(self)

    def setModel(self, model: CheckableSqlTableModel | CheckableSqlQueryModel | SampleAgeTableModel):
        super().setModel(model)

    def enable_context_menu(self, show_context_menu: bool):
        self.context_menu = show_context_menu
        if self.context_menu:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
        else:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.NoContextMenu)

    def set_single_click(self, single_click: bool):
        self.single_click = single_click

    def set_closed_on_line_edit_click(self, closedOnLineEditClick: bool):
        self.closedOnLineEditClick = closedOnLineEditClick

    def set_line_edit_text(self, text):
        self.lineEdit().setText(text)

    def show_context_menu(self, pos):
        menu = QtW.QMenu()
        edit_action = menu.addAction(f"Edit {TxM.add_spaces_camel(self.model().tableName())}")
        clear_all_action = menu.addAction("Clear All Checks")
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.edit_triggered.emit(self)
        elif action == clear_all_action:
            self.clear_all_checks()

    def clear_all_checks(self):
        col = name_column(self.model.tableName())
        for row in range(self.model.rowCount()):
            index = self.model.index(row, col)
            if row == self.tableView.currentIndex().row():
                self.model.setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            else:
                self.model.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            print(f"Changed state to {self.model.data(index, QtC.Qt.ItemDataRole.CheckStateRole)}")


    def showPopup(self):
        self.tableView.resizeColumnsToContents()
        columns = self.model().columnCount()
        width_hint = 0
        show_cols_indices = []
        if self.model().tableName() == '"References"':
            show_cols = ["ReferenceDisplay", "ReferenceDescription"]
        elif 'Units' in self.model().tableName() or 'Formats' in self.model().tableName():
            show_cols = ["Abbreviation"]
        else:
            show_cols = ["Name", "Description"]
        for col in range(0, columns):
            # hide all but name and description
            col_name = self.model().headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if any(s in col_name for s in show_cols):
                self.tableView.showColumn(col)
                show_cols_indices.append(col)
                # Add up the size hints for all the visible columns
                width_hint += self.tableView.columnWidth(col)
            else:
                self.tableView.hideColumn(col)
        self.tableView.setSortingEnabled(False)
        width_c1 = self.tableView.sizeHintForColumn(show_cols_indices[0])
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
            # print(f"Object: viewport, Event type: {event.type()}")
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                if self.single_click:
                    print(f"Clicked text: {self.tableView.currentIndex().data()}")
                    print("Single click mode enabled")
                    self.clear_all_checks()
                    self.set_line_edit_text(self.tableView.currentIndex().data())
                    self.hidePopup()
                    return True
                else:
                    self.tableView.toggle_check_state(self.tableView.currentIndex())
                    self.showPopup()
                    return True
            return super().eventFilter(obj, event)

        return super().eventFilter(obj, event)

class SearchableSQLComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.proxy_model = QtC.QSortFilterProxyModel()
        self.lineEdit().textChanged.connect(self.search_items)

    def setModel(self, model: QtS.QSqlTableModel | VerifiableSqlViewModel):
        self.proxy_model.setSourceModel(model)
        super().setModel(self.proxy_model)
        self.setModelColumn(name_column(model.tableName()))

    def search_items(self, text):
        self.proxy_model.setFilterFixedString(text)
        self.showPopup()
        if self.proxy_model.rowCount() > 0:
            self.setCurrentIndex(0)
        else:
            self.setCurrentIndex(-1)

class SearchableComboBox(QtW.QComboBox):
    selection_changed = QtC.pyqtSignal(QtW.QComboBox)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.list_view = QtW.QListView()
        self.setView(self.list_view)
        self.previous_index = -1
        # self.all_items = []
        self.completer().setFilterMode(QtC.Qt.MatchFlag.MatchStartsWith)
        self.completer().setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.lineEdit().setCompleter(self.completer())

        self.lineEdit().editingFinished.connect(self.validate_input)

    def addItem(self, text):
        super().addItem(text)
        # self.all_items.append(text)
        # Set the default text to blank
        self.lineEdit().setText(None)

    def addItems(self, texts):
        super().addItems(texts)
        # self.all_items.extend(texts)
        self.lineEdit().setText(None)

    def validate_input(self):
        if self.findText(self.lineEdit().text()) == -1 or self.lineEdit().text() == 'None':
            self.lineEdit().setText(None)
            self.setCurrentIndex(-1)

class TemporaryComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)

    def hidePopup(self):
        super().hidePopup()
        self.closing.emit()

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
        utm_e_m = utm_easting.split('m')[0]
        utm_northing = string.split(',')[2]
        utm_n_m = utm_northing.split('m')[0]
        rounded_northing = ' ' + return_rounded(utm_n_m)
        rounded_easting = ' ' + return_rounded(utm_e_m)
        string = string.replace(utm_n_m, rounded_northing)
        string = string.replace(utm_e_m, rounded_easting)
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
        if value - int(value) != 0:
            rounded_value = f'{value:.{decimal_places}f}'
        else:
            rounded_value = int(value)
    else:
        rounded_value = value
    return rounded_value

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

def set_comboBox_text(comboBox: QtW.QComboBox, text: str):
    if text == '' or text == '-':
        comboBox.setCurrentIndex(-1)
    else:
        comboBox.setCurrentText(text)

def show_column(comboBox: QtW.QComboBox, column: str):
    model = comboBox.model()
    for col in range(model.columnCount()):
        header = model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        if header == column:
            comboBox.setModelColumn(col)