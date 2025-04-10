import re
import sqlite3
import time
import typing
from collections import namedtuple
from datetime import datetime, timezone

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from numpy import integer
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QMetaType, QAbstractTableModel, Qt, QModelIndex
from PyQt6.QtGui import QTextOption, QAction
from PyQt6.QtSql import QSqlTableModel, QSqlQueryModel, QSqlQuery, QSqlDatabase
from PyQt6.QtWidgets import QGroupBox, QStyledItemDelegate, QProgressDialog

import Functions.Text_manipulations as TxM
import logger_setup
from Functions import SQLUtils
from Functions.Check_triggers import update_modified_timestamp, validate_update
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import settings


# ---------------------------
#    Delegate Classes
# ---------------------------

# class DecimalDelegate(QtW.QStyledItemDelegate):
#     """
#     Custom delegate to display numerical values with a fixed number of decimal places based upon user
#     settings.
#     """
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.decimal_places = settings.value('decimals_to_show', type=int)
#
#     def displayText(self, value, locale):
#         if isinstance(value, float):
#             return f'{value:.{self.decimal_places}f}'
#         return super().displayText(value, locale)

class FontDelegate(QtW.QStyledItemDelegate):
    """
    Custom delegate to display text with a custom font.
    """
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        font = index.data(QtC.Qt.ItemDataRole.FontRole)
        if font:
            option.font = font

class WordWrapDelegate(QtW.QStyledItemDelegate):
    """
    Custom delegate to enable word wrap in QTableView.
    """

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.textElideMode = Qt.TextElideMode.ElideNone  # Do not cut text
        option.wrapMode = QTextOption.WrapMode.WordWrap  # Allow word wrap

# ---------------------------
#    Table Classes
# ---------------------------

# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'reference_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")

class SQLiteTableModel(QAbstractTableModel):
    """
    Custom QAbstractTableModel to display a query from a SQLite database. If database is not given, the database file
    stored in settings will be used. This model was created due to the limitations of QSqlTableModel and QSqlQueryModel
    with abnormally long query execution time.
    """
    def __init__(self, query: str = '', database=None):
        from Functions.Settings_manager import settings

        super().__init__()
        self._data = []
        self._headers = []
        self.edited_indexes = []
        self.last_error = None
        self.query_text = query
        self.database = database if database is not None else settings._instance.value('db_file', type=str)

        self.load_data(self.query_text, self.database)

    def setQuery(self, new_query: str):
        """Updates the model with a new query."""
        self.load_data(new_query, self.database)

    def update_database(self, new_database: str):
        """Updates the model with a new database."""
        self.load_data(self.query_text, new_database)

    def load_data(self, query: str, database: str):
        """Loads data from the given query and database."""
        if query == '':
            return
        self.beginResetModel()
        self._data.clear()
        self._headers.clear()
        self.last_error = None
        self.query_text = query
        self.database = database
        uri = f'file:{database}?mode=ro&immutable=1'

        try:
            conn = sqlite3.connect(uri, uri=True)
            with conn:
                cursor = conn.cursor()
                cursor.execute(query)
                self._data = cursor.fetchall()
                self._headers = [desc[0] for desc in cursor.description]
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f"Error opening database and executing query")
            logger_setup.get_logger().debug(f"Error: {e}")
            logger_setup.get_logger().debug(f"SQL query: {query}")
            self.last_error = e
        if 'table_info' in query:
            table = 'table_info'
        else:
            table = query.split('FROM ')[1].split(' ')[0]
        if 'View' in table:
            self.view = table
            if 'Sample' in table:
                self.table = 'Samples'
            elif 'Aliquot' in table:
                self.table = 'Aliquots'
            elif 'Spot' in table:
                self.table = 'Spots'
            elif 'UPb' in table:
                self.table = 'UPbAnalyses'
            elif 'Column' in table:
                self.table = 'Columns'
            elif 'Reference' in table:
                self.table = 'References'
            self.table_name_col = get_name_column(self.table)
            self.view_name_col = get_view_name_column(self.view)
        else:
            self.table = table
            self.table_name_col = get_name_column(self.table)
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def tableName(self):
        return self.table

    def tableView(self):
        return self.view

    def record(self, row: int):
        class MockRecord:
            def __init__(self, row):
                self.row = row

            def value(self, index):
                return self.row[index]

            def count(self):
                return len(self.row)

        if 0 <= row < len(self._data):
            return MockRecord(self._data[row])
        else:
            return None  # or raise IndexError

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None  # Return None instead of False to avoid type errors

        if role == Qt.ItemDataRole.DisplayRole:
            # Fetch value directly from `_data`
            value = self._data[index.row()][index.column()]
            header = self._headers[index.column()]  # Get column header

            # Apply formatting based on header names
            if isinstance(value, str):
                if 'Age' in header:
                    for age_string in [f'({settings.value("age_unit_abbreviation")})', 'AgeCalculated', 'AgeDisplay']:
                        if age_string in header:
                            return display_age(value)
                elif 'GPS' in header:
                    return display_gps(value)
                elif 'Elevation' in header or 'Height' in header or 'Depth' in header:
                    return display_value_with_error(value)
            elif isinstance(value, (int, float)):  # Format numerical values
                return return_rounded(value)
            return value  # Return raw value if no formatting is applied

        return None  # Return None for roles that are not DisplayRole

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Return column headers."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]  # Ensure headers are stored properly
        return super().headerData(section, orientation, role)

    def setHeaderData(self, section, orientation, value, role=Qt.ItemDataRole.EditRole):
        """Allow renaming of column headers."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.EditRole:
            self._headers[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return super().setHeaderData(section, orientation, value, role)

    def setData(self, index, value, role = ...):
        if role == Qt.ItemDataRole.EditRole:
            if self._data[index.row()][index.column()] == value:
                # No change
                return True
            data_list = list(self._data)
            rows = []
            for row in range(len(data_list)):
                row_list = list(data_list[row])
                if row == index.row():
                    row_list[index.column()] = value
                rows.append(row_list)

            data_list = []
            for row in rows:
                data_list.append(tuple(row))
            self._data = tuple(data_list)
            self.edited_indexes.append(index)
            return self._data[index.row()][index.column()] == value

    def removeRows(self, ids_to_remove: list) -> bool:
        """
        Removes rows from the table based on provided primary key ids for the table.
        :param ids_to_remove: list of ids to remove from the table
        :return: True for success, False otherwise
        """
        self.beginRemoveRows(QtC.QModelIndex(), 0, len(self._data) - 1)
        ids_to_remove.sort(reverse=False)
        for id in ids_to_remove:
            for row in self._data:
                if id in row:
                    self._data.remove(row)
                    break
        self.endRemoveRows()
        return True

    def insertRow(self, row_data: list) -> bool:
        """
        Inserts rows into the table. Rows provided should be in the same format as the table.
        :param row_data: list of row data that will be inserted into the table
        :return: True for success, False otherwise
        """
        self.beginInsertRows(QtC.QModelIndex(), len(self._data), len(self._data))
        self._data.append(row_data)
        self.endInsertRows()
        logger_setup.get_logger().info(f'Updated {self.table}')
        return True

    def column_as_list(self, col):
        """
        returns a list of items in a column
        :param col: string or integer representing column
        :return: list of items in each row for a given column
        """
        if isinstance(col, str):
            column = self._headers.index(col)
        elif isinstance(col, int):
            column = col
        else:
            return
        return [row[column] for row in self._data]


class QSqlTableModelModifiedTrigger(QtS.QSqlTableModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole:
            return super().setData(index, value, role)

        row = index.row()

        # Call the base method to update the actual cell
        if not super().setData(index, value, role):
            return False

        update_modified_timestamp(self.tableName(), self.index(row, 1))

        return True

class DisplayRoundedModel(QtS.QSqlTableModel):
    """

    """
    def __init__(self, db=QSqlDatabase()):
        super().__init__(db=db)

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            # check the header of the selected index
            header = self.headerData(index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = super().data(index, role)
            if isinstance(value, str):
                if 'Age' in header:
                    for age_string in [f'({settings.value("age_unit_abbreviation")})', 'AgeCalculated', 'AgeDisplay']:
                        if age_string in header:
                            return display_age(value)
                elif 'GPS' in header and 'Format' not in header:
                    return display_gps(value)
                elif 'Elevation' in header or 'Height' in header or 'Depth' in header and 'Unit' not in header:
                    return display_value_with_error(value)
            # if the value is a number but not an integer
            elif value is not None and isinstance(value, (int, float)):
                return return_rounded(value)
            else:
                return value
        return super().data(index, role)

    def unrounded_data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        return super().data(index, role)

class DisplayRoundedQueryModel(QSqlQueryModel):
    def __init__(self, db=QSqlDatabase()):
        super().__init__()
        self.view = ''
        self.view_name_col = ''
        self.table = ''
        self.table_name_col = ''
        self.db = db
        self.rounded = True

    def setQuery(self, query):
        super().setQuery(query, self.db)
        if self.lastError().text():
            logger_setup.get_logger().critical(f"Error displaying table")
            logger_setup.get_logger().debug(f"Failed to set query: {self.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query}")
        else:
            table = query.split('FROM ')[1].split(' ')[0]
            if 'View' in table:
                self.view = table
                if 'Sample' in table:
                    self.table = 'Samples'
                elif 'Aliquot' in table:
                    self.table = 'Aliquots'
                elif 'Spot' in table:
                    self.table = 'Spots'
                elif 'Column' in table:
                    self.table = 'Columns'
                elif 'Reference' in table:
                    self.table = 'References'
                self.table_name_col = get_name_column(self.table)
                self.view_name_col = get_view_name_column(self.view)
            else:
                self.table = table
                self.table_name_col = get_name_column(self.table)

    def tableName(self):
        return self.table

    def tableView(self):
        return self.view

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = QtC.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            # check the header of the selected index
            header = self.headerData(index.column(), QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            value = super().data(index, role)
            if isinstance(value, str):
                if 'Age' in header:
                    for age_string in [f'({settings.value("age_unit_abbreviation")})', 'AgeCalculated', 'AgeDisplay']:
                        if age_string in header:
                            return display_age(value)
                elif 'GPS' in header:
                    return display_gps(value)
                elif 'Elevation' in header or 'Height' in header or 'Depth' in header:
                    return display_value_with_error(value)
            # if the value is a number but not an integer, and rounded is True
            elif value is not None and isinstance(value, (int, float)) and self.rounded:
                return return_rounded(value)
            else:
                return value
        return super().data(index, role)

    def unrounded_data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = QtC.Qt.ItemDataRole.DisplayRole):
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
        logger_setup.get_logger().info(f"Setting {field_type} to {value}")
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
        error, header = validate_update(self.tableName(), columns, values, where)
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
            if 'Sample' in tableName:
                self.table = 'Samples'
            elif 'Aliquot' in tableName:
                self.table = 'Aliquots'
            elif 'Spot' in tableName:
                self.table = 'Spots'
            elif 'UPbAnalysis' in tableName:
                self.table = 'UPbAnalyses'
            elif 'Column' in tableName:
                self.table = 'Columns'
            elif 'Reference' in tableName:
                self.table = 'References'
            super().setTable(self.table)
        else:
            logger_setup.get_logger().error(f'Table {tableName} is not a view')

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
                if not query.exec(f'SELECT GPSLocationID FROM GPSLocations WHERE GPSLocationDisplay="{value}"'):
                    logger_setup.get_logger().critical(f'Failed to get GPSLocationID for {value}')
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    return False
                query.next()
                set_value = query.value(0)
                # set_value = foreign_table.record(0).value('GPSLocationID')
            else:
                set_header = header
                set_value = value
            columns.append(set_header)
            values.append(set_value)

        error, header = validate_update(self.table, columns, values, f'{id_header}={id}')
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
            logger_setup.get_logger().critical(f'Failed to update {self.table} with {column_str}={value_str}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
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
        error = update_modified_timestamp(self.table, [record_id])
        if error is not None:
            logger_setup.get_logger().error(error)
            return False

    def deleteRowFromTable(self, row):
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        query = QtS.QSqlQuery()
        if not query.exec(f'DELETE FROM {self.table} WHERE {id_header}={id}'):
            logger_setup.get_logger().critical(f'Failed to delete {id} from {self.table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return False
        return True

class EditableSqlQueryModel(DisplayRoundedQueryModel):
    def __init__(self):
        super().__init__()
        self.query = ''

    def flags(self, index):
        flags = super().flags(index)
        col = get_name_column(self.table)
        if index.column() == col or 'Description' in self.headerData(index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole):
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable
        return flags

    def setQuery(self, query):
        super().setQuery(query)
        self.query = query

    def setData(self, index: QtC.QModelIndex, value, role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:
            edited_id = self.data(self.index(index.row(), 0), QtC.Qt.ItemDataRole.DisplayRole)
            id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            edited_header = self.headerData(index.column(), QtC.Qt.Orientation.Horizontal)
            query = QtS.QSqlQuery()
            if not query.exec(f'SELECT {edited_header} FROM {self.table} WHERE {id_header}={edited_id}'):
                logger_setup.get_logger().critical(f'Failed to get {edited_header} from {self.table}')
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                return False
            if query.next():
                if query.value(0) == value:
                    logger_setup.get_logger().info(f'{edited_header} is already set to {value}')
                    return True
            query.prepare(f'UPDATE {self.table} SET {edited_header}=:value WHERE {id_header}=:id')
            query.bindValue(':value', value)
            query.bindValue(':id', edited_id)
            if not query.exec():
                logger_setup.get_logger().critical(f'Failed to update {edited_header} in {self.table}')
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
                return False
            logger_setup.get_logger().info(f'Successfully updated {edited_header} in {self.table}')
            update_modified_timestamp(self.tableName(), [edited_id])
            self.setQuery(self.query)
            self.dataChanged.emit(index, index)
            return True
        return super().setData(index, value, role)

    def deleteRowFromTable(self, row):
        id_header = self.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        query = QtS.QSqlQuery()
        if not query.exec(f'DELETE FROM {self.table} WHERE {id_header}={id}'):
            logger_setup.get_logger().critical(f'Failed to delete {id} from {self.table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return False
        logger_setup.get_logger().info(f'Successfully deleted {id} from {self.table}')
        return True

class ReadableProxyModel(QtC.QSortFilterProxyModel):
    def __init__(self, view=False):
        self.view = view
        super().__init__()
        self.original_headers = False

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: QtC.Qt.ItemDataRole = ...):
        if self.original_headers:
            super().headerData(section, orientation, role)
        if role == QtC.Qt.ItemDataRole.DisplayRole and orientation == QtC.Qt.Orientation.Horizontal:
            header = super().headerData(section, orientation, role)
            if '_' in header:
                return header
            if not self.view:
                readable_header = get_readable_header(header)
                return readable_header
            else:
                readable_header = TxM.add_spaces_camel(header)
                return readable_header
        super().headerData(section, orientation, role)

    def setData(self, index: QtC.QModelIndex, value, role: int) -> bool:
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            source_index = self.mapToSource(index)
            return self.sourceModel().setData(source_index, value, role)
        return super().setData(index, value, role)

    def determine_numeric(self, value):
        if isinstance(value, str):
            if value == '':
                return value
            elif '.' in value:
                try:
                    float(value)  # value is float, not text
                    if float(value) - int(float(value)) != 0:
                        return float(value)
                    else:  # value is an integer
                        return int(float(value))
                except ValueError:
                    return value
            try:
                int(value)  # value is integer, not text
                return int(value)
            except ValueError:
                return value
        elif isinstance(value, float):
            if value - int(value) != 0:
                return value
            else:
                return int(value)
        else:
            return value

    def separate_parts(self, text):
        parts = re.split(r'(\d+)', text)
        if parts:
            # return all sets of numbers and strings
            return [int(part) if part.isdigit() else part for part in parts]
        else:
            return None

    def compare_parts(self, left_parts, right_parts):
        for left_part, right_part in zip(left_parts, right_parts):
            if left_part != right_part:
                return left_part < right_part
        # If all compared parts are equal, return the shorter one
        return len(left_parts) < len(right_parts)

    def lessThan(self, left, right):
        left_data = self.determine_numeric(left.data(QtC.Qt.ItemDataRole.DisplayRole))
        right_data = self.determine_numeric(right.data(QtC.Qt.ItemDataRole.DisplayRole))
        if isinstance(left_data, str) and isinstance(right_data, str):
            left_parts = self.separate_parts(left_data)
            right_parts = self.separate_parts(right_data)
            return self.compare_parts(left_parts, right_parts)
        else:
            return super().lessThan(left, right)

class SampleAgeProxyModel(QtC.QSortFilterProxyModel):
    """
    Proxy model to display updated SampleAgeDisplay while generated columns cannot update during a transaction.
    """
    def __init__(self):
        super().__init__()

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            name_col = get_name_column('SampleAges')
            if index.column() == name_col:
                from Functions.Alter_database import return_sample_age_display
                id = self.sourceModel().index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                if id is not None:
                    # get the updated sample age display calculated from the database
                    age_display = return_sample_age_display(id)
                    if age_display is not None:
                        # return the user-readable age display
                        return display_age(age_display)

class CheckableSqlTableModel(DisplayRoundedModel):
    def __init__(self):
        super().__init__()
        self.primary_key_column = 0
        self.checked_ids = []
        self.partially_checked_ids = []

    def flags(self, index):
        flags = super().flags(index)
        col = get_name_column(self.tableName())
        if index.column() == col:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = get_name_column(self.tableName())
        if index.column() == col and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.checked_ids:
                return QtC.Qt.CheckState.Checked
            elif self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                return QtC.Qt.CheckState.PartiallyChecked
            else:
                return QtC.Qt.CheckState.Unchecked
        elif index.column() == col and role == QtC.Qt.ItemDataRole.ToolTipRole:
            description_col = None
            for header_col in range(self.columnCount()):
                header = self.headerData(header_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if 'Description' in header:
                    description_col = header_col
                    break
            if description_col is not None:
                return super().data(self.index(index.row(), description_col), QtC.Qt.ItemDataRole.DisplayRole)
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value, role: QtC.Qt.ItemDataRole = ...) -> bool:
        col = get_name_column(self.tableName())
        if index.column() == col and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if value == QtC.Qt.CheckState.Checked:
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) not in self.checked_ids:
                    self.checked_ids.append(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
            elif value == QtC.Qt.CheckState.PartiallyChecked:
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) not in self.partially_checked_ids:
                    self.partially_checked_ids.append(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
            else:
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.checked_ids:

                    self.checked_ids.remove(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                    self.partially_checked_ids.remove(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def return_checked_ids(self):
        return self.checked_ids, self.partially_checked_ids

    def clear_checks(self):
        self.checked_ids = []
        self.partially_checked_ids = []

    def update_other_table(self, other_table: str, other_ids: list):
        # Updates another table with the checked IDs. These are one-to-many relationships like SpotComposition, where we
        # want to update the SpotCompositionID in the Spots table with the checked IDs in the SpotComposition table. This
        # method is useful when editing joined views, like editing the SpotComposition in the SampleEditView.
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return False
        if update_other_table_with_checks(self.tableName(), self.checked_ids, self.partially_checked_ids, other_table, other_ids):
            return True
        else:
            return False

    def update_many_table(self, many_table: str, item_ids: list):
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return False
        if update_many_table_with_checks(self.tableName(), self.checked_ids, self.partially_checked_ids, many_table, item_ids):
            return True
        else:
            return False


class CheckableSqlQueryModel(DisplayRoundedQueryModel):
    def __init__(self):
        super().__init__()
        self.checked_ids = []
        self.partially_checked_ids = []

    def flags(self, index):
        flags = super().flags(index)
        col = get_name_column(self.table)
        if index.column() == col:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        try:
            view = self.tableView()
            if view == '':
                col = get_name_column(self.table)
            else:
                col = get_view_name_column(view)
        except AttributeError:
            col = get_name_column(self.tableName())
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.checked_ids:
                return QtC.Qt.CheckState.Checked
            elif self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                return QtC.Qt.CheckState.PartiallyChecked
            else:
                return QtC.Qt.CheckState.Unchecked
        elif index.column() == col and role == QtC.Qt.ItemDataRole.ToolTipRole:
            description_col = None
            for header_col in range(self.columnCount()):
                header = self.headerData(header_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if 'Description' in header:
                    description_col = header_col
                    break
            if description_col is not None:
                return super().data(self.index(index.row(), description_col), QtC.Qt.ItemDataRole.DisplayRole)
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value, role: QtC.Qt.ItemDataRole = ...) -> bool:
        try:
            view = self.tableView()
            if view == '':
                col = get_name_column(self.tableName())
            else:
                col = get_view_name_column(view)
        except AttributeError:
            col = get_name_column(self.tableName())

        if index.column() == col and role == QtC.Qt.ItemDataRole.CheckStateRole:
            if value == QtC.Qt.CheckState.Checked:
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) not in self.checked_ids:
                    self.checked_ids.append(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
            elif value == QtC.Qt.CheckState.PartiallyChecked:
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) not in self.partially_checked_ids:
                    self.partially_checked_ids.append(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
            else:
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.checked_ids:
                    self.checked_ids.remove(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
                if self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                    self.partially_checked_ids.remove(self.index(index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole))
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def return_checked_ids(self):
        return self.checked_ids, self.partially_checked_ids

    def clear_checks(self):
        self.checked_ids = []
        self.partially_checked_ids = []

    def update_other_table(self, other_table: str, other_ids: list):
        # Updates another table with the checked IDs. These are one-to-many relationships like SpotComposition, where we
        # want to update the SpotCompositionID in the Spots table with the checked IDs in the SpotComposition table. This
        # method is useful when editing joined views, like editing the SpotComposition in the SampleEditView.
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return False
        if update_other_table_with_checks(self.table, self.checked_ids, self.partially_checked_ids, other_table, other_ids):
            return True
        else:
            return False

    def update_many_table(self, many_table: str, item_ids: list):
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return False
        if update_many_table_with_checks(self.table, self.checked_ids, self.partially_checked_ids, many_table, item_ids):
            return True
        else:
            return False

class SampleAgeTableModel(CheckableSqlQueryModel):
    def __init__(self):
        super().__init__()
        self.bolded_rows = []
        self.default_query = 'SELECT * FROM SampleAges'

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


# ---------------------------
#    Table Methods
# ---------------------------


def set_table(model: QtS.QSqlTableModel, table: str):
    # logger_setup.get_logger().info(f"Setting table to {table}")
    model.setTable(table)
    if model.lastError().text():
        logger_setup.get_logger().critical(f"Failed to set table to {table})")
        logger_setup.get_logger().debug(f"setTable error: {model.lastError().text()}")
        return False
    model.select()
    if model.lastError().text():
        logger_setup.get_logger().critical(f"Failed to set table to {table})")
        logger_setup.get_logger().debug(f"select error: {model.lastError().text()}")
        return False
    return model

def get_headers(table: str):
    query = QtS.QSqlQuery()
    if table == '"References"':
        table = 'References'
    if not query.exec(f'PRAGMA table_xinfo("{table}")'):
        logger_setup.get_logger().critical(f"Failed to get headers for {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return []
    headers = []
    while query.next():
        headers.append(query.value(1))
    return headers

def get_columns(table: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'PRAGMA table_xinfo("{table}")'):
        logger_setup.get_logger().critical(f"Failed to get columns for {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
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

def get_name_column(table: str) -> int | None:
    table = table.replace('"', '')
    if table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees:
        return 3
    elif 'Format' in table or 'Unit' in table:
        # return the column for the abbreviation
        return 2
    elif table == 'References' or table == '"References"':
        return 9
    elif table == 'SampleAges':
        return 16
    elif table in SQLUtils.user_viewable_tables or table in ['Spots', 'GPSLocations', 'FilterGroups']:
        return 1
    elif table == 'SampleView':
        return 2
    elif table == 'AliquotView':
        return 5
    elif table == 'SpotView':
        return 5
    elif table == 'UPbView':
        return 5
    else:
        return None

def description_column(table: str) -> int | None:
    headers = get_headers(table)
    for header in headers:
        if 'Description' in header:
            return headers.index(header)
    return None

def get_table_from_view(view: str):
    if 'Sample' in view:
        return 'Samples'
    elif 'Aliquot' in view:
        return 'Aliquots'
    elif 'Spot' in view:
        return 'Spots'
    elif 'UPb' in view:
        return 'UPbAnalyses'
    elif 'Column' in view:
        return 'Columns'
    elif 'Reference' in view:
        return 'References'
    else:
        return view

def get_view_name_column(view: str) -> int | None:
    table = get_table_from_view(view)
    table_name_col = get_name_column(table)
    if table_name_col is not None:
        # View columns may be reorganized, so we need to get the header from the table then find it in the view columns
        name_header = get_headers(table)[table_name_col]
        view_column_settings = SQLUtils.view_setting_dict[view]
        view_columns = settings.value(view_column_settings)
        if name_header in view_columns:
            view_name_col = view_columns.index(name_header)
            return view_name_col

def get_name_from_id(table: str, item_id: int):
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    if not query.exec(f'SELECT {headers[get_name_column(table)]} FROM {table} WHERE {headers[0]}={item_id}'):
        logger_setup.get_logger().critical(f"Failed to get name for {item_id} in {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return None
    query.next()
    return query.value(0)

def get_id_from_name(table: str, name: str):
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    if not query.prepare(f'SELECT {headers[0]} FROM {table} WHERE {headers[get_name_column(table)]}=:name COLLATE NOCASE'):
        logger_setup.get_logger().critical(f"Could not find ID for {name} in {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
    query.bindValue(":name", name)
    if not query.exec():
        logger_setup.get_logger().critical(f"Failed to get ID for {name} in {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
        return None
    query.next()
    return query.value(0)

def get_total_records(table: str, where:str='') -> int:
    """
    Get the total number of records in the table
    """
    start_time = time.time()
    id_header = get_headers(table)[0]
    query = QSqlQuery()

    if 'View' in table:
        table = get_table_from_view(table)

    # Construct the query based on the table
    sql_query = f'SELECT COUNT({id_header}) FROM "{table}" {where}'

    # Execute the query
    logger_setup.get_logger().info(f'Fetching total records for {table}')
    if not query.exec(sql_query):
        # Handle query execution error
        logger_setup.get_logger().critical(f'Error fetching total records')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return 0

    # Fetch the count
    if query.next():
        return query.value(0)
    return 0

def get_record_index(table: str, record_id: int):
    """
    Get the index of a specific record ID
    """
    query = QSqlQuery()
    if 'View' in table:
        table = get_table_from_view(table)

    # Construct the SQL query
    base_id_column = get_headers(table)[0]
    sql_query = f"""
            SELECT row_number 
            FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY {base_id_column}) AS row_number, {base_id_column} FROM {table}
            ) 
            WHERE {base_id_column} = :record_id
        """

    # Prepare and bind parameters
    query.prepare(sql_query)
    query.bindValue(":record_id", record_id)

    logger_setup.get_logger().info('Getting the record index for record ID: {record_id}')
    # Execute the query
    if not query.exec():
        # Handle query execution error
        logger_setup.get_logger().critical(f'Error fetching the record')
        logger_setup.get_logger().debug(f'Error fetching records index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
        return -1

    # Fetch the result
    if query.next():
        return query.value(0) - 1  # Convert to zero-based index

    return -1

def get_column_types(table: str):
    query = QtS.QSqlQuery()
    column_types = []
    if not query.exec(f'PRAGMA table_info("{table}")'):
        logger_setup.get_logger().critical(f"Failed to get columns for {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return column_types
    while query.next():
        column_types.append(query.value(2))
    return column_types

def foreign_key_columns(table: str):
    query = QtS.QSqlQuery()
    foreign_keys = {}
    if not query.exec(f'PRAGMA foreign_key_list("{table}")'):
        logger_setup.get_logger().critical(f"Failed to get foreign keys for {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return foreign_keys
    while query.next():
        foreign_table = query.value(2)
        table_display_column = get_name_column(foreign_table)
        foreign_query = QtS.QSqlQuery()
        if not foreign_query.exec(f'PRAGMA table_info("{foreign_table}")'):
            logger_setup.get_logger().error(f"Failed to get columns for {foreign_table}")
            logger_setup.get_logger().debug(f"Error: {foreign_query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return foreign_keys
        table_display_header = None
        while foreign_query.next():
            if foreign_query.value(0) == table_display_column:
                table_display_header = foreign_query.value(1)
                break
        if not table_display_header:
            logger_setup.get_logger().error(f"Failed to get display column for {foreign_table}")
            return {}
        foreign_keys[query.value(3)] = {'table': query.value(2), 'id_column': query.value(4), 'display_column': table_display_header}
    return foreign_keys

def get_foreign_id_table(table: str, header: str, value):
    if 'ID' not in header:
        logger_setup.get_logger().error(f"Header {header} does not contain ID")
        return value
    foreign_keys = foreign_key_columns(table)
    if header in foreign_keys.keys():
        foreign_table = foreign_keys[header]['table']
        id_column = foreign_keys[header]['id_column']
        display_column = foreign_keys[header]['display_column']
        query = QtS.QSqlQuery()
        if not query.exec(f'SELECT {id_column} FROM {foreign_table} WHERE {display_column}="{value}"'):
            logger_setup.get_logger().critical(f"Failed to get ID for {value} in {foreign_table}")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            return value
        query.next()
        return query.value(0), foreign_table

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
        lat_string = string.split(', ')[0]
        lon_string = string.split(', ')[1]
        lat_sec = lat_string.split('°')[1].split('\'')[1].split('"')[0]
        lon_sec = lon_string.split('°')[1].split('\'')[1].split('"')[0]
        rounded_lat_sec = return_rounded(lat_sec)
        rounded_lon_sec = return_rounded(lon_sec)
        string = string.replace(lat_sec, f'{rounded_lat_sec}')
        string = string.replace(lon_sec, f'{rounded_lon_sec}')
    if "'" in string:
        # DM format, (lat_deg°lat_min' lat_dir, lon_deg°lon_min' lon_dir) or (lat_deg°lat_min', lon_deg°lon_min')
        lat_string = string.split(', ')[0]
        lon_string = string.split(', ')[1]
        lat_min = lat_string.split('°')[1].split('\'')[0]
        lon_min = lon_string.split('°')[1].split('\'')[0]
        rounded_lat_min = return_rounded(lat_min)
        rounded_lon_min = return_rounded(lon_min)
        string = string.replace(lat_min, f'{rounded_lat_min}')
        string = string.replace(lon_min, f'{rounded_lon_min}')
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
        string = string.replace(utm_n_m, f'{rounded_northing}')
        string = string.replace(utm_e_m, f'{rounded_easting}')
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
        if value == '':
            return value
        elif '.' in value:
            if float(value): # value is float, not text
                if value.split('.')[1] != '0':
                    rounded_value = f'{float(value):.{decimal_places}f}'
                else: # value is an integer
                    rounded_value = int(float(value))
            else:
                rounded_value = value
        elif int(value):  # value is integer, not text
            rounded_value = int(value)
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

def return_number(value: str | float | int):
    """
    Convert a string to a number, if possible. If not, return it as is.
    :param value: string, float, or integer to convert to the best number format
    :return: value as a number or the original string if it was not a number
    """
    if isinstance(value, str):
        if value == '':
            return value
        try:
            return_value = int(value)
        except ValueError:
            try:
                return_value = float(value)
            except ValueError:
                return_value = value
        return return_value
    elif isinstance(value, float):
        try:
            return_value = int(value)
        except ValueError:
            return_value = value
        return return_value
    if isinstance(value, int):
        return value


def delete_query(table, ids, id_name):
    query = QtS.QSqlQuery()
    if len(ids) > 0:
        query.prepare(f'DELETE FROM {table} WHERE {id_name} in {tuple(ids)}')
    if len(ids) == 1:
        query.prepare(f'DELETE FROM {table} WHERE {id_name}={ids[0]}')
    if not query.exec():
        logger_setup.get_logger().error(f"Failed to delete {id_name} from {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastError().text()}")
        return False
    return True

def delete_data(data_ids: list, table: str):
    """
    Given Samples, Aliquots, or Spots, delete given ids and all sub items
    :param data_ids: List of sample, aliquot, or spot IDs
    :param table: Table the IDs belong to
    :return: True or False
    """
    # Delete the selected samples and all aliquots, spots, and UPb data associated with them
    if table == 'Samples':
        aliquot_ids, spot_ids, upb_analysis_ids = find_sub_items(data_ids, table)
        sample_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(sample_ids)} samples, {len(aliquot_ids)} aliquots, {len(spot_ids)} spots, and {len(upb_analysis_ids)} UPb analyses")
    elif table == 'Aliquots':
        spot_ids, upb_analysis_ids = find_sub_items(data_ids, table)
        aliquot_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(aliquot_ids)} aliquots, {len(spot_ids)} spots, and {len(upb_analysis_ids)} UPb analyses")
    elif table == 'Spots':
        upb_analysis_ids = find_sub_items(data_ids, table)
        spot_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(spot_ids)} spots and {len(upb_analysis_ids)} UPb analyses")
    else:
        logger_setup.get_logger().critical(f"Failed to delete {table}")
        logger_setup.get_logger().debug(f"Error: This method is only for Samples, Aliquots, and Spots")
        return False

    create_savepoint('before_delete')

    from Functions.Database_manager import turn_on_foreign_keys
    # Double-check that foreign keys are enabled
    if not turn_on_foreign_keys():
        return False
    if not delete_query('UPbAnalyses', upb_analysis_ids, 'UPbAnalysisID'):
        rollback_savepoint('before_delete')
        return False
    logger_setup.get_logger().info(f'Deleted {len(upb_analysis_ids)} UPb analyses')
    if not delete_query('Spots', spot_ids, 'SpotID'):
        rollback_savepoint('before_delete')
        return False
    logger_setup.get_logger().info(f'Deleted {len(spot_ids)} spots')
    if table in ['Samples', 'Aliquots']:
        if not delete_query('Aliquots', aliquot_ids, 'AliquotID'):
            rollback_savepoint('before_delete')
            return False
        logger_setup.get_logger().info(f'Deleted {len(aliquot_ids)} Aliquots')
    if table == 'Samples':
        if not delete_query('Samples', sample_ids, 'SampleID'):
            rollback_savepoint('before_delete')
            return False
        logger_setup.get_logger().info(f'Deleted {len(sample_ids)} Samples')

    release_savepoint('before_delete')
    return True

def find_upb_from_samples(sample_ids):
    # Find UPb analyses for a list of samples
    logger_setup.get_logger().info(f"Finding UPb Analyses for {len(sample_ids)} samples")
    upb_analysis_ids = []
    if len(sample_ids) > 1:
        upb_analysis_table = SQLiteTableModel(f'SELECT UPbAnalysisID FROM UPbView WHERE SampleID in {tuple(sample_ids)}')
    elif len(sample_ids) == 1:
        upb_analysis_table = SQLiteTableModel(f'SELECT UPbAnalysisID FROM UPbView WHERE SampleID={sample_ids[0]}')
    else:
        # No samples selected
        return
    if not upb_analysis_table.last_error:
        for row in range(upb_analysis_table.rowCount()):
            upb_data_id = upb_analysis_table.data(upb_analysis_table.index(row, 0))
            upb_analysis_ids.append(upb_data_id)
        return upb_analysis_ids
    else:
        # There was an error creating the table
        return

def find_sub_items(data_ids: list, table: str):
    # Find all the sub items of a list of samples, aliquots, or spots
    logger_setup.get_logger().info(f"Finding sub items for {len(data_ids)} {table}")
    aliquot_ids = []
    spot_ids = []
    upb_analysis_ids = []
    if table == 'Samples':
        for sample_id in data_ids:
            aliquot_table = SQLiteTableModel(f'SELECT AliquotID FROM Aliquots WHERE SampleID={sample_id}')
            for a_row in range(aliquot_table.rowCount()):
                aliquot_id = aliquot_table.data(aliquot_table.index(a_row, 0))
                aliquot_ids.append(aliquot_id)
                spot_table = SQLiteTableModel(f'SELECT SpotID FROM Spots WHERE AliquotID={aliquot_id}')
                for s_row in range(spot_table.rowCount()):
                    spot_id = spot_table.data(spot_table.index(s_row, 0))
                    spot_ids.append(spot_id)
                    UPb_analysis_table = SQLiteTableModel(f'SELECT UPbAnalysisID FROM UPbAnalyses WHERE SpotID={spot_id}')
                    for row in range(UPb_analysis_table.rowCount()):
                        upb_data_id = UPb_analysis_table.data(UPb_analysis_table.index(row, 0))
                        upb_analysis_ids.append(upb_data_id)
        return aliquot_ids, spot_ids, upb_analysis_ids
    elif table == 'Aliquots':
        for aliquot_id in data_ids:
            spot_table = SQLiteTableModel(f'SELECT SpotID FROM Spots WHERE AliquotID={aliquot_id}')
            for s_row in range(spot_table.rowCount()):
                spot_id = spot_table.data(spot_table.index(s_row, 0))
                spot_ids.append(spot_id)
                UPb_analysis_table = SQLiteTableModel(f'SELECT UPbAnalysisID FROM UPbAnalyses WHERE SpotID={spot_id}')
                for row in range(UPb_analysis_table.rowCount()):
                    upb_data_id = UPb_analysis_table.data(UPb_analysis_table.index(row, 0))
                    upb_analysis_ids.append(upb_data_id)
        return spot_ids, upb_analysis_ids
    elif table == 'Spots':
        for spot_id in data_ids:
            UPb_analysis_table = SQLiteTableModel(f'SELECT UPbAnalysisID FROM UPbAnalyses WHERE SpotID={spot_id}')
            for row in range(UPb_analysis_table.rowCount()):
                upb_data_id = UPb_analysis_table.data(UPb_analysis_table.index(row, 0))
                upb_analysis_ids.append(upb_data_id)
        return upb_analysis_ids



# ---------------------------
#    Tree Classes
# ---------------------------

'''
Editable tree model example:
https://doc.qt.io/qt-6/qtwidgets-itemviews-editabletreemodel-example.html

qsqltablemodel source code:
https://github.com/openwebos/qt/blob/master/src/sql/models/qsqltablemodel.cpp

qsortfilterproxymodel source code:
https://github.com/openwebos/qt/blob/92fde5feca3d792dfd775348ca59127204ab4ac0/src/gui/itemviews/qsortfilterproxymodel.cpp#L143
'''


class TreeItem:
    def __init__(self, itemData: QtS.QSqlRecord, parentItem):
        """
        Create a tree item with given data and parent item
        Parameters
        ----------
        itemData: SQL record from QSqlTableModel
        parentItem: parent tree item
        """
        self.itemData = itemData
        self.parentItem = parentItem
        self.childItems = []

    def __del__(self):
        """
        Deletes all children of deleted item
        """
        logger_setup.get_logger().info(f'Deleting tree items')
        for child_tree_item in self.childItems:
            del child_tree_item
        del self.childItems

    def appendChild(self, child_item):
        """
        Add each child item
        Parameters
        ----------
        child_item
        """
        # add each child item
        self.childItems.append(child_item)

    def removeChild(self, row: int):
        """
        Remove a child item at a position
        Parameters
        ----------
        row: number of child in list of its parent's children
        """
        # remove a child item at a position
        if row < 0 or row >= len(self.childItems):
            return False
        else:
            self.childItems.remove(row)
            return True

    def clear(self):
        """
        Recursively remove all children
        """
        # remove all children
        for child_tree_item in self.childItems:
            child_tree_item.clear()
        self.childItems.clear()

    def child(self, row: int):
        """
        Return the # row child of the item, or none if the row is invalid or there are no children
        Parameters
        ----------
        row
        Returns
        -------
        None or child item
        """
        # child in given row
        if row < 0 or row >= len(self.childItems):
            return None
        else:
            return self.childItems[row]

    def childCount(self):
        # number of children
        return len(self.childItems)

    def row(self):
        # row of item in its parent's list of children
        if self.parentItem:
            # return self.parent_item.childItems.indexOf(TreeItem(self))
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        # number of columns in input data
        if self.itemData:
            return self.itemData.count()
        else:
            return 0

    def data(self, column: int):
        # get data at given column
        if self.itemData is None:
            return QtC.QVariant()
        if column < 0 or column >= self.itemData.count():
            return QtC.QVariant()
        else:
            value = self.itemData.value(column)
            return value

    def setData(self, column: int, value: typing.Any):
        if column < 0 or column >= self.itemData.count():
            return False
        else:
            field = self.itemData.field(column)
            self.itemData.setValue(field.name(), value)
            return True

    def setRecord(self, record: QtS.QSqlRecord):
        self.itemData = record

    def parent(self):
        # parent for given item
        if self.itemData is None:
            return None
        else:
            return self.parentItem


class TreeModel(QtC.QAbstractProxyModel):
    dataEdited = QtC.pyqtSignal()
    save_state = QtC.pyqtSignal()

    def __init__(self, source_model=None, parent=None, db=QSqlDatabase()):
        # database table
        super().__init__(parent)

        self.source_model = source_model
        self.base_filter = ""
        self.base_filter_sql = ""
        self.base_query = ""
        self.base_query_sql = ""
        self.table = ""
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.root_item = TreeItem(QtS.QSqlRecord(), None)
        self.parent_item = TreeItem(QtS.QSqlRecord(), None)
        self.child_item = TreeItem(QtS.QSqlRecord(), None)
        self.lastError = QtS.QSqlError()
        self.db = db

        if self.source_model:
            # If a table model was set
            self.setSourceModel(self.source_model)

    def sourceModel(self):
        return self.source_model

    def setSourceModel(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel):
        logger_setup.get_logger().info(f'Setting source model for tree model...')
        try:
            if source_model.tableName() != '':
                self.table = source_model.tableName()
            else:
                return
        except AttributeError:
            logger_setup.get_logger().critical(f'Error displaying the selected table')
            if isinstance(source_model, QSqlQueryModel):
                logger_setup.get_logger().debug(f'Cannot retrieve table name from QSqlQueryModel')
        if isinstance(source_model, QSqlTableModel):
            self.base_filter = f"{source_model.filter()}".split("ORDER")[0]
            if len(self.base_filter) > 0:
                self.base_filter_sql = f"{self.base_filter} AND "
                self.base_query = f"SELECT * FROM {self.table} WHERE {self.base_filter}"
            else:
                self.base_filter_sql = self.base_filter
                self.base_query = f"SELECT * FROM {self.table}"
        elif isinstance(source_model, QSqlQueryModel):
            query_object = source_model.query()
            self.base_query = f"{query_object.lastQuery()}".split("ORDER")[0]
        elif isinstance(source_model, SQLiteTableModel):
            self.base_query = source_model.query_text.split("ORDER")[0]
        if len(self.base_query) > 0:
            if ' WHERE ' in self.base_query:
                self.base_query_sql = f"{self.base_query} AND "
            else:
                self.base_query_sql = f"{self.base_query} WHERE "
        if 'FROM AliquotView' in self.base_query:
            self.source_model = SQLiteTableModel(query=self.base_query)
        else:
            self.source_model = DisplayRoundedQueryModel(db=self.db)
            self.source_model.setQuery(f'{self.base_query}')
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.header_variables()
        if self.root_item.childCount() > 0:
            self.root_item.clear()
        # self.root_item = TreeItem(QtS.QSqlRecord(), None)
        self.parent_item = TreeItem(QtS.QSqlRecord(), None)
        self.child_item = TreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()

    def setup_model_data(self):
        # Add all nodes to the tree model
        # start with root item, look for children
        logger_setup.get_logger().info(f'Building the {self.table} tree from the model...')
        start_build_time = time.time()
        root_id = 0
        child_ids = self.find_children(root_id)
        # add each child to model with parent (root)
        self.add_to_tree(child_ids, self.root_item)
        # look for children of those
        # add each child to the model with parent
        # etc. until there are no more children
        self.source_model.setQuery(f"{self.base_query}")
        logger_setup.get_logger().info(f'Finished building the {self.table} tree with {self.source_model.rowCount()} items in {time.time() - start_build_time:.2f} seconds')

    def find_children(self, parent_id: int):
        # Find children of a given ID using the source_model's filtered data
        self.source_model.setQuery(f"{self.base_query_sql}  "
                                   f"{self.parent_id_header} is {parent_id if parent_id != 0 else 'NULL'}")
        child_ids = []
        for row in range(self.source_model.rowCount()):
            child_ids.append(self.source_model.record(row).value(0))

        return child_ids

    def add_to_tree(self, child_ids: list, parent: TreeItem):
        if not child_ids:
            return
        # logger_setup.get_logger().info(f'Adding {len(child_ids)} children to the tree...')
        # logger_setup.get_logger().debug(f'Child IDs: {child_ids}')
        for child_id in child_ids:
            self.source_model.setQuery(f"{self.base_query_sql} {self.id_header} is {child_id}")
            if self.source_model.rowCount() > 0:
                record = self.source_model.record(0)
                item = TreeItem(record, parent)
                logger_setup.get_logger().info(f'Added {record.value(3)}')
                parent.appendChild(item)
                # logger_setup.get_logger().debug(f'Added {child_id} to the tree')
                new_child_ids = self.find_children(child_id)
                self.add_to_tree(new_child_ids, item)

    def add_top_item(self, data):
        TreeItem(data, 0)

    def column_headers(self):
        for col in range(self.source_model.columnCount()):
            self.sourceHeaders.append(
                self.source_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            if col == 0:
                # Label the first column with the item name
                self.proxyHeaders.append(
                    self.source_model.headerData(3, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 1:
                # Label the second column with the item ID
                self.proxyHeaders.append(
                    self.source_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 2:
                # Label the third column with the parent ID
                self.proxyHeaders.append(
                    self.source_model.headerData(1, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif col == 3:
                # Label the fourth column with the parent row
                self.proxyHeaders.append(
                    self.source_model.headerData(2, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            else:
                self.proxyHeaders.append(
                    self.source_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))

    def header_variables(self):
        self.id_header = self.sourceHeaders[0]
        self.parent_id_header = self.sourceHeaders[1]
        self.parent_row_header = self.sourceHeaders[2]
        self.item_name_header = self.sourceHeaders[3]
        self.item_description_header = self.sourceHeaders[4]

    def getItem(self, index: QtC.QModelIndex) -> TreeItem:  # returns tree item
        if not index.isValid():
            return self.root_item
        else:
            item = index.internalPointer()
            if not item:
                logger_setup.get_logger().error(f"Error finding item for tree index")
                logger_setup.get_logger().debug(f"No item for index {index.row()},{index.column()},{index.parent()}")
            return item

    def index(self, row: int, column: int, parent: QModelIndex) -> QtC.QModelIndex:
        # Given row, column, and parent, create an index for a child item at row and column
        # First check if parent is valid and parent item exists
        # Then get the child at the specified row and create an index for it
        # index for views and delegates
        if not isinstance(parent, QtC.QModelIndex):
            pass
        if not self.hasIndex(row, column, parent):
            return QtC.QModelIndex()
        if parent.isValid():
            parentItem = self.getItem(parent)
        else:
            parentItem = self.root_item
        if not parentItem:
            return QtC.QModelIndex()
        if row < 0 or row > self.rowCount(parent):
            return QtC.QModelIndex()
        if column < 0 or column > self.columnCount(parent):
            return QtC.QModelIndex()
        item = parentItem.child(row)
        if item:
            return self.createIndex(row, column, item)
        else:
            return QtC.QModelIndex()

    def parent(self, index: QtC.QModelIndex):
        # Given index, find parent and create index for parent item
        if not index.isValid():
            return QtC.QModelIndex()
        item = self.getItem(index)
        parentItem = item.parent()
        if parentItem == self.root_item or not parentItem:
            return QtC.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent: QtC.QModelIndex = QtC.QModelIndex) -> int:
        if not parent.isValid():
            parentItem = self.root_item
        else:
            parentItem = self.getItem(parent)
        return parentItem.childCount()

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        return self.source_model.columnCount()

    def hasChildren(self, parent: QtC.QModelIndex = ...):
        if not parent.isValid():
            return True
        parentItem = self.getItem(parent)
        if parentItem.childCount() > 0:
            return True
        return False

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            item = self.root_item
        else:
            item = self.getItem(index)
        if role == QtC.Qt.ItemDataRole.DisplayRole or role == QtC.Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                # Show name in first column
                return item.data(3)
            elif index.column() == 1:
                # Show item ID in second column
                return item.data(0)
            elif index.column() == 2:
                # Show parent ID in third column
                return item.data(1)
            elif index.column() == 3:
                # Show parent row in fourth column
                return item.data(2)
            else:
                return item.data(index.column())
        elif index.column() == 0 and role == QtC.Qt.ItemDataRole.ToolTipRole:
            if self.table == 'Ages':
                # For the Ages table, the tooltip is the age range
                oldest_age = self.data(index.siblingAtColumn(4), QtC.Qt.ItemDataRole.DisplayRole)
                youngest_age = self.data(index.siblingAtColumn(5), QtC.Qt.ItemDataRole.DisplayRole)
                return f'{oldest_age}-{youngest_age} Ma'
            description_col = None
            for header_col in range(self.columnCount()):
                header = self.headerData(header_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if 'Description' in header:
                    description_col = header_col
                    break
            if description_col is not None:
                return super().data(self.index(index.row(), description_col, index.parent()), QtC.Qt.ItemDataRole.DisplayRole)
        return None

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: QtC.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:
            sourceIndex = self.mapToSource(index)
            if sourceIndex.isValid():
                logger_setup.get_logger().info(
                    f'Setting data in {self.table} tree at {sourceIndex.row()},{sourceIndex.column()}')
                treeItem = self.getItem(index)
                if index.column() == 0:
                    # Show name in first column
                    dataCol = 3
                elif index.column() == 1:
                    # Show item ID in second column
                    dataCol = 0
                elif index.column() == 2:
                    # Show parent ID in third column
                    dataCol = 1
                elif index.column() == 3:
                    # Show parent row in third column
                    dataCol = 2
                else:
                    dataCol = index.column()
                # Get the updated modified timestamp
                modified_col = self.source_model.columnCount() - 1
                source_modified_index = self.source_model.index(sourceIndex.row(), modified_col, QtC.QModelIndex())
                proxy_modified_index = self.mapFromSource(source_modified_index)
                if proxy_modified_index.isValid() and source_modified_index.isValid():
                    # If the changed data index and the modified timestamp index are valid for both models, change the data
                    name_header = self.source_model.headerData(sourceIndex.column(), QtC.Qt.Orientation.Horizontal)
                    table_id = self.source_model.data(sourceIndex.siblingAtColumn(0), QtC.Qt.ItemDataRole.DisplayRole)
                    query = QtS.QSqlQuery()
                    query.prepare(f"UPDATE {self.table} SET {name_header}=:value WHERE {self.id_header}={table_id}")
                    query.bindValue(":value", value)
                    if not query.exec():
                        logger_setup.get_logger().critical(f'Error editing data in {self.table}')
                        logger_setup.get_logger().debug(
                            f'Error setting data in {self.table} tree at {sourceIndex.row()},{sourceIndex.column()}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                        return False
                    modified = self.source_model.data(source_modified_index, QtC.Qt.ItemDataRole.DisplayRole)
                    treeItem.setData(dataCol, value)
                    self.dataChanged.emit(index, index)
                    update_modified_timestamp(self.table, [table_id])
                    treeItem.setData(modified_col, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
                    self.dataChanged.emit(index, index)
                    logger_setup.get_logger().info(
                        f'Successfully set data in {self.table} tree at {sourceIndex.row()},{sourceIndex.column()} to {value}')
                    return True
                else:
                    logger_setup.get_logger().critical(f"Error editing data in {self.table}")
                    logger_setup.get_logger().debug(
                        f'Invalid indices for setting data in {self.table} tree at {sourceIndex.row()},{sourceIndex.column()}')
                    return False
        return False

    def moveItem(self, item_id: int, row: int, p_id: str):
        """
        Move an item to a new parent and parent row
        @param item_id: unique ID of the item to move
        @param row: new parent row number for the item
        @param p_id: new parent ID for the item, represented by a string to use in the setFilter method, either 'IS NULL' or 'is parentID'
        @return: True if the item was successfully moved, None if there was an error
        """
        # Try making change to database, then reset the tree model
        if p_id == 'IS NULL':
            parentID = 'NULL'
        else:
            parentID = int(p_id[2:])
        self.source_model.setQuery(
            f"{self.base_query_sql}  {self.id_header} is {item_id} AND {self.parent_id_header} {p_id} AND {self.parent_row_header} is {row}")
        if self.source_model.rowCount() > 0:
            # If the item is already in the correct place, do nothing
            return None
        self.source_model.setQuery(
            f"{self.base_query_sql}  {self.id_header} is {item_id}")  # Only one record for each item ID
        oldParentID = self.source_model.record(0).value(1)  # Get the current parent ID
        if isinstance(oldParentID, int):
            opID = f'= {oldParentID}'
        else:
            opID = 'IS NULL'
            oldParentID = 'NULL'
        oldParentRow = self.source_model.record(0).value(2)  # Get the current parent row
        # Look for children of the new parent at and below the point of insertion, order them by parent row from largest to smallest
        filtered_model = QtS.QSqlQueryModel()
        filtered_model.setQuery(
            f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {p_id} AND {self.parent_row_header} >= {row} ORDER BY {self.parent_row_header} DESC")
        child_count = filtered_model.rowCount()
        if child_count > 0:
            # If the parent already has children and the new one is replacing an existing row, update their parent rows
            for child in range(child_count):  # Starting with the last child
                # increase the parent row by 1 for each child after the target row
                childID = filtered_model.record(child).value(0)
                currentParentRow = filtered_model.record(child).value(2)
                newParentRow = currentParentRow + 1
                self.source_model.setQuery(self.base_query)  # Reset the filter
                if not self.update_parent_info(childID, parentID, newParentRow):
                    return None
                if currentParentRow == row:
                    # Now update the moved item into the new space
                    self.source_model.setQuery(self.base_query)  # Reset the filter
                    if not self.update_parent_info(item_id, parentID, row):
                        return None
        else:  # no children to update
            self.source_model.setQuery(self.base_query)  # Reset the filter
            if not self.update_parent_info(item_id, parentID, row):
                return None
        # Look for remaining children of the old parent whose parent rows need to be updated, order them by parent row from smallest to largest
        self.source_model.setQuery(
            f"{self.base_query_sql}  {self.parent_id_header} {opID} AND {self.parent_row_header} > {oldParentRow} ORDER BY {self.parent_row_header} ASC")
        child_count = self.source_model.rowCount()
        if child_count > 0:
            current_rows = []
            child_ids = []
            for child in range(
                    child_count):  # Starting with the first child to update, save important values before the model filter is reset
                # decrease the parent row by 1 for each child after the old parent row
                current_rows.append(self.source_model.record(child).value(2))
                child_ids.append(self.source_model.record(child).value(0))
            for child in range(child_count):
                newParentRow = current_rows[child] - 1
                self.source_model.setQuery(self.base_query)  # Reset the filter
                if not self.update_parent_info(child_ids[child], oldParentID, newParentRow):
                    return None
        self.source_model.setQuery(self.base_query)  # Reset the filter
        return True

    def update_parent_info(self, item_id: int, parent_id, parent_row: int):
        # Update the parent ID and parent row for a given item ID
        query = QtS.QSqlQuery()
        query.prepare(
            f'UPDATE {self.table} SET {self.parent_id_header} = :parent_id, {self.parent_row_header} = :parent_row WHERE {self.id_header} = :item_id')
        if parent_id == 'NULL':
            query.bindValue(':parent_id', QtC.QVariant())
        else:
            query.bindValue(':parent_id', parent_id)
        query.bindValue(':parent_row', parent_row)
        query.bindValue(':item_id', item_id)
        if not query.exec():
            logger_setup.get_logger().error(
                f'Error updating parent for {item_id} in table {self.table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
            return None
        else:
            update_modified_timestamp(self.table, [item_id])
            logger_setup.get_logger().info(f'Successfully updated parent for {item_id} in table {self.table}')
            return True

    def insertItem(self, item_name: str, item_description: str, parent_id=None, parent_row=None):
        # Add a new item to the database, first as a top-level item, then move it to the correct parent and row
        query = QtS.QSqlQuery()
        p_id = 'IS NULL'
        self.source_model.setQuery(f"{self.base_query_sql} {self.sourceHeaders[1]} {p_id}")
        child_count = self.source_model.rowCount()
        query.prepare(
            f'INSERT INTO {self.table}({self.parent_row_header}, {self.item_name_header}, {self.item_description_header}) VALUES(:parent_row, :item_name, :item_description)')
        query.bindValue(':parent_row', child_count)
        query.bindValue(':item_name', item_name)
        query.bindValue(':item_description', None if item_description=='' else item_description)
        create_savepoint('before_insert')
        self.save_state.emit()
        if not query.exec():
            logger_setup.get_logger().critical(f'Error inserting new item {item_name}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
            rollback_savepoint('before_insert')
            return None
        else:
            logger_setup.get_logger().info(f'Successfully inserted new item {item_name}')
            if parent_id:
                p_id = f'= {parent_id}'
            else:
                p_id = 'IS NULL'
            if parent_row is None:
                # If no parent row is given, the item is added to the end of the list
                self.source_model.setQuery(f"{self.base_query_sql} {self.parent_id_header} {p_id}")
                child_count = self.source_model.rowCount()
                parent_row = child_count
            self.source_model.setQuery(f"{self.base_query_sql} {self.item_name_header} is '{item_name}'")
            item_id = self.source_model.record(0).value(0)
            if not self.moveItem(item_id, parent_row, p_id):
                rollback_savepoint('before_insert')
                return None
            release_savepoint('before_insert')
            self.dataEdited.emit()
            return True

    def removeItem(self, item_id: int, parent_row: int, parent_id=None):
        # Remove an item and all children from the database
        del_ids = [item_id]

        def find_child_ids(parentID: int, del_ids: list):
            # Find all children of a given parent ID
            filtered_model = QtS.QSqlQueryModel()
            filtered_model.setQuery(f"SELECT * FROM {self.table} WHERE {self.parent_id_header} = {parentID}")
            for row in range(filtered_model.rowCount()):
                record = filtered_model.record(row)
                del_ids.append(record.value(0))
                find_child_ids(record.value(0), del_ids)
            return del_ids

        del_ids = find_child_ids(item_id, del_ids)
        del_join = ', '.join([str(i) for i in del_ids])
        del_string = f'({del_join})'
        if len(del_ids) == 1:
            sql_where_str = f'={del_ids[0]}'
        elif len(del_ids) > 1:
            sql_where_str = f'IN {del_string}'
        elif len(del_ids) == 0:
            logger_setup.get_logger().info(f'Item was already deleted')
            logger_setup.get_logger().debug(f'Item ID: {item_id}')
            return True
        logger_setup.get_logger().info(
            f'Deleting item {item_id} and {len(del_ids) - 1} dependents from {self.table}...')
        self.source_model.setQuery(self.base_query)  # Reset the filter
        query = QtS.QSqlQuery()
        query.prepare(f'DELETE FROM {self.table} WHERE {self.id_header} {sql_where_str}')
        create_savepoint('before_delete')
        self.save_state.emit()
        if not query.exec():  # if item and children not deleted, rollback
            logger_setup.get_logger().critical(f'Error deleting items from {self.table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_delete')
            return False
        logger_setup.get_logger().info(f'Successfully deleted items from {self.table}')
        if parent_id:
            pID = f'= {parent_id}'
        else:
            pID = 'IS NULL'
            parent_id = 'NULL'
        filtered_model = QtS.QSqlQueryModel()
        filtered_model.setQuery(
            f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {pID} AND {self.parent_row_header} >= {parent_row} ORDER BY {self.parent_row_header} ASC")
        childCount = filtered_model.rowCount()
        if childCount > 0:
            # If the parent already has children at rows beyond the deleted one, update their parent rows to close the gap
            for child in range(childCount):  # Starting with the next child after the deleted one
                # decrease the parent row by 1 for each child after the deleted one
                childID = filtered_model.record(child).value(0)
                currentParentRow = filtered_model.record(child).value(2)
                newParentRow = currentParentRow - 1
                self.source_model.setQuery(self.base_query)  # Reset the filter
                if not self.update_parent_info(childID, parent_id, newParentRow):
                    logger_setup.get_logger().critical(f'Error updating parent row for child')
                    logger_setup.get_logger().debug(f'Child ID: {childID}')
                    rollback_savepoint('before_delete')
                    return False
        release_savepoint('before_delete')
        logger_setup.get_logger().info(
            f'Successfully deleted item {item_id} and {len(del_ids) - 1} dependents from {self.table}...')
        self.dataEdited.emit()
        return True

    def mapToSource(self, proxy_index: QtC.QModelIndex) -> QtC.QModelIndex:
        if not proxy_index.isValid() or not self.source_model:
            return QtC.QModelIndex()
        if not isinstance(self.source_model, QtS.QSqlQueryModel | SQLiteTableModel):
            logger_setup.get_logger().critical(f'Data type error')
            logger_setup.get_logger().debug(f'Source model is not a QSqlQueryModel')
            return QtC.QModelIndex()
        proxy_col = proxy_index.column()
        item = self.getItem(proxy_index)
        item_id = item.data(0)
        source_row = None
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            if record.value(0) == item_id:
                source_row = row
                break
        if source_row is None:
            return QtC.QModelIndex()
        if proxy_col == 0:  # first column is item name which maps to fourth column in source model
            source_col = 3
        elif proxy_col == 1:  # second column is item ID which maps to first column in source model
            source_col = 0
        elif proxy_col == 2:  # third column is parent ID which maps to second column in source model
            source_col = 1
        elif proxy_col == 3:  # fourth column is parent row which maps to third column in source model
            source_col = 2
        else:
            source_col = proxy_col
        return self.source_model.index(source_row, source_col, QtC.QModelIndex())

    def mapFromSource(self, source_index: QtC.QModelIndex) -> QtC.QModelIndex:
        if not source_index.isValid():
            return QtC.QModelIndex()
        source_row = source_index.row()
        source_col = source_index.column()
        if source_col == 0:  # first column is item ID which maps to second column in proxy model
            proxy_col = 1
        elif source_col == 1:  # second column is parent ID which maps to third column in proxy model
            proxy_col = 2
        elif source_col == 2:  # third column is parent row which maps to fourth column in proxy model
            proxy_col = 3
        elif source_col == 3:  # fourth column is item name which maps to first column in proxy model
            proxy_col = 0
        else:
            proxy_col = source_col  # same column as table model
        record = self.source_model.record(source_row)
        item_id = record.value(0)
        item = self.find_id_in_tree(item_id)
        proxy_row = item.row()  # row number of item in its parent's child list
        parent_item = item.parent()
        if parent_item == self.root_item:
            parent_index = QtC.QModelIndex()
        else:
            parent_index = self.createIndex(parent_item.row(), proxy_col, parent_item)
        return self.index(proxy_row, proxy_col, parent_index)

    def find_id_in_tree(self, item_id: int) -> TreeItem:  # returns tree item with itemID
        def search(item_index: QtC.QModelIndex):
            item = self.getItem(item_index)
            if not item_index.isValid():
                if item != self.root_item:
                    return None
            if item.data(0) == item_id:
                return item
            for row in range(item.childCount()):
                child_index = self.index(row, 0, item_index)
                result = search(child_index)
                if result:
                    return result
            return None

        return search(QtC.QModelIndex())

    def find_id_source_row(self, itemID: int):
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            if record.value(0) == itemID:
                return row
        return

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        if not index.isValid():
            # the root can be a drop destination
            return QtC.Qt.ItemFlag.ItemIsDropEnabled
        modified_col = self.source_model.columnCount() - 1
        created_col = self.source_model.columnCount() - 2
        if index.column() == modified_col or index.column() == created_col:
            # If the column is the created timestamp or modified timestamp, it is not editable. IDs should not be visible at all
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsDragEnabled | QtC.Qt.ItemFlag.ItemIsDropEnabled
        else:
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsDragEnabled | QtC.Qt.ItemFlag.ItemIsDropEnabled

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes):
        mimeData = QtC.QMimeData()
        encodedData = QtC.QByteArray()
        stream = QtC.QDataStream(encodedData, QtC.QIODevice.OpenModeFlag.WriteOnly)
        for index in indexes:
            if index.isValid() and index.column() == 0:
                item = self.getItem(index)
                stream.writeInt32(item.data(0))  # item ID
        mimeData.setData('application/x-qabstractitemmodeldatalist', encodedData)
        return mimeData

    def canDropMimeData(self, data, action, row, column, parent):
        if action == QtC.Qt.DropAction.IgnoreAction:
            return False
        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            logger_setup.get_logger().critical(f'Error dropping item')
            logger_setup.get_logger().debug(f'Drop data format not recognized')
            return False
        return True

    def dropMimeData(self, data: QtC.QMimeData, action: QtC.Qt.DropAction, row: int, column: int,
                     parent: QtC.QModelIndex):
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
        encodedData = data.data('application/x-qabstractitemmodeldatalist')
        stream = QtC.QDataStream(encodedData, QtC.QIODevice.OpenModeFlag.ReadOnly)
        itemIDs = []
        rows = []
        parentID = self.getItem(parent).data(0)
        if isinstance(parentID, int):
            pID = f'= {parentID}'
        else:  # If the parent ID is not an integer
            pID = 'IS NULL'
        create_savepoint('drop_mime_data')
        self.save_state.emit()
        while not stream.atEnd():
            itemIDs.append(stream.readInt32())
            if row == -1:
                # If the row is -1, the item is being moved to the end of the list
                self.source_model.setQuery(f"{self.base_query_sql} {self.sourceHeaders[1]} {pID}")
                childCount = self.source_model.rowCount()
                row = childCount
            rows.append(row)
            row += 1
        if not itemIDs:
            logger_setup.get_logger().debug(f'No items to move')
            rollback_savepoint('drop_mime_data')
            return False
        for move in range(len(itemIDs)):
            self.source_model.setQuery(
                f"{self.base_query_sql}  {self.id_header} is {itemIDs[move]}")  # Only one record for each item ID
            oldParentID = self.source_model.record(0).value(1)  # Get the current parent ID
            if self.table == 'Aliquots' and parentID == oldParentID:
                logger_setup.get_logger().info(f"Cannot reorder top-level aliquots")
                rollback_savepoint('drop_mime_data')
                return False
            if not self.moveItem(itemIDs[move], rows[move], pID):
                logger_setup.get_logger().critical(f'Error moving item')
                logger_setup.get_logger().debug(f'Item: {itemIDs[move]}, rows: {rows[move]}, parent_ID: {pID}')
                rollback_savepoint('drop_mime_data')
                return False
        # All moves were successful
        self.source_model.setQuery(self.base_query)  # Reset the filter
        release_savepoint('drop_mime_data')
        # Emit signal so that the view can rebuild the tree model
        self.dataEdited.emit()
        return True

    def supportedDropActions(self):
        return QtC.Qt.DropAction.CopyAction | QtC.Qt.DropAction.MoveAction

    def supportedDragActions(self):
        return QtC.Qt.DropAction.CopyAction | QtC.Qt.DropAction.MoveAction

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...):
        if role != QtC.Qt.ItemDataRole.DisplayRole:
            return QtC.QVariant()
        if orientation == QtC.Qt.Orientation.Horizontal:
            return self.proxyHeaders[section]
        return QtC.QVariant()

    def top_node(self, item_ids: list) -> tuple:
        def walk_tree(parent_id, item_ids: list):
            if isinstance(parent_id, int):
                pID = f'= {parent_id}'
            else:
                pID = 'IS NULL'
            filtered_model = QtS.QSqlQueryModel()
            filtered_model.setQuery(
                f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {pID} ORDER BY {self.parent_row_header} ASC")
            childCount = filtered_model.rowCount()
            for child in range(childCount):
                child_id = filtered_model.record(child).value(0)
                parent_row = child
                if child_id in item_ids:
                    return parent_id, parent_row
                else:
                    walk_tree(child_id, item_ids)

        parent_id = 'Null'
        (top_parent_id, top_parent_row) = walk_tree(parent_id, item_ids)
        return top_parent_id, top_parent_row


class CheckableTreeItem(TreeItem):
    def __init__(self, record: QtS.QSqlRecord, parent: TreeItem = None):
        super().__init__(record, parent)
        self.checkState = QtC.Qt.CheckState.Unchecked

    def setCheckState(self, state: QtC.Qt.CheckState):
        self.checkState = state

    def getCheckState(self):
        return self.checkState


class CheckableTreeModel(TreeModel):
    def __init__(self, source_model=QSqlTableModel(), parent=None):
        # database table
        super().__init__(source_model, parent)
        self.root_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.parent_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.child_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.item_ids = None
        self.many_to_many = None
        if self.source_model:
            # If a table model with a valid table was passed, set the source model and create the tree
            self.setSourceModel(self.source_model)

    def setSourceModel(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel):
        logger_setup.get_logger().info(f'Setting source model for tree model...')
        try:
            if source_model.tableName() != '':
                self.table = source_model.tableName()
            else:
                return
        except AttributeError:
            logger_setup.get_logger().critical(f'Error displaying the selected table')
            if isinstance(source_model, QSqlQueryModel):
                logger_setup.get_logger().debug(f'Cannot retrieve table name from QSqlQueryModel')
        if isinstance(source_model, QSqlTableModel):
            self.base_filter = f"{source_model.filter()}"
            if len(self.base_filter) > 0:
                self.base_filter_sql = f"{self.base_filter} AND "
                self.base_query = f"SELECT * FROM {self.table} WHERE {self.base_filter}"
            else:
                self.base_filter_sql = self.base_filter
                self.base_query = f"SELECT * FROM {self.table}"
        elif isinstance(source_model, QSqlQueryModel):
            query_object = source_model.query()
            self.base_query = f"{query_object.lastQuery()}"
        elif isinstance(source_model, SQLiteTableModel):
            self.base_query = source_model.query_text
        if len(self.base_query) > 0:
            if ' WHERE ' in self.base_query:
                self.base_query_sql = f"{self.base_query} AND "
            else:
                self.base_query_sql = f"{self.base_query} WHERE "
        self.source_model = DisplayRoundedQueryModel()
        self.source_model.setQuery(f'{self.base_query}')
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.header_variables()
        if self.root_item.childCount() > 0:
            logger_setup.get_logger().info(f'Clearing previous values from the tree model...')
            self.beginResetModel()
            self.root_item.clear()
            self.endResetModel()
        self.root_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.parent_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.child_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()
        self.source_model.setQuery(self.base_query)

    def add_to_tree(self, child_ids: list, parent: CheckableTreeItem):
        for child_id in child_ids:
            self.source_model.setQuery(f"{self.base_query_sql} {self.id_header} is {child_id}")
            if self.source_model.rowCount() > 0:
                record = self.source_model.record(0)

                item = CheckableTreeItem(record, parent)
                parent.appendChild(item)
                new_child_ids = self.find_children(child_id)
                self.add_to_tree(new_child_ids, item)

    def set_item(self, item_ids: list, man_to_many: str):
        self.item_ids = item_ids
        self.many_to_many = man_to_many  # Many-to-many table name
        first_table = self.many_to_many.split('_')[0]
        first_table_id_header = get_headers(first_table)[0]
        item_ids = []
        query = QtS.QSqlQuery()
        if len(self.item_ids) >= 1:
            query.prepare(f"SELECT * FROM {self.many_to_many} WHERE {first_table_id_header} in {tuple(self.item_ids)}")
        if len(self.item_ids) == 1:
            query.prepare(f"SELECT * FROM {self.many_to_many} WHERE {first_table_id_header} = {self.item_ids[0]}")
        if query.exec():
            while query.next():
                item_ids.append(query.value(1))
            for item_id in item_ids:
                item = self.find_id_in_tree(item_id)
                if item:
                    item.setCheckState(QtC.Qt.CheckState.Checked)
            logger_setup.get_logger().info(f'Successfully set {first_table} {self.item_ids} for table {self.many_to_many}')
        else:
            logger_setup.get_logger().critical(
                f'Error checking data for table {self.many_to_many}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            item = self.root_item
        else:
            item = self.getItem(index)
        if index.column() == 0 and role == QtC.Qt.ItemDataRole.CheckStateRole:
            return item.getCheckState()

        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: QtC.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid():
            return False
        if index.column() == 0 and role == QtC.Qt.ItemDataRole.CheckStateRole:
            tree_item = self.getItem(index)
            if tree_item.getCheckState() != value:
                tree_item.setCheckState(value)
                # print(f"Setting check state for {tree_item.data(0)} to {value}")
                self.dataChanged.emit(index, index, [role])
                return True
        return super().setData(index, value, role)

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        # name_col = name_column(self.table)
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        if index.column() == 0:
            # If the column is the name item, it is checkable
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable | QtC.Qt.ItemFlag.ItemIsDragEnabled | QtC.Qt.ItemFlag.ItemIsDropEnabled
        return super().flags(index)

    def clear_checks(self, parent: QtC.QModelIndex):
        for row in range(self.rowCount(parent)):
            name_index = self.index(row, 0, parent)
            self.setData(name_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            self.clear_checks(name_index)

    def check_checkable_tree(self, parent: QtC.QModelIndex, checked_items: list, partially_checked_items: list):
        for row in range(self.rowCount(parent)):
            name_index = self.index(row, 0, parent)
            id_index = self.index(row, 1, parent)
            if self.data(id_index, QtC.Qt.ItemDataRole.DisplayRole) in checked_items:
                self.setData(name_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            elif self.data(id_index, QtC.Qt.ItemDataRole.DisplayRole) in partially_checked_items:
                self.setData(name_index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
            else:
                self.setData(name_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            self.check_checkable_tree(name_index, checked_items, partially_checked_items)

    def traverse_checkable_tree(self, parent: QtC.QModelIndex):
        checked_items = []
        partially_checked_items = []
        checked_indices = []
        partially_checked_indices = []
        for row in range(self.rowCount(parent)):
            name_index = self.index(row, 0, parent)
            id_index = self.index(row, 1, parent)
            if self.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                checked_items.append(self.data(id_index, QtC.Qt.ItemDataRole.DisplayRole))
                checked_indices.append(name_index)
            elif self.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.PartiallyChecked:
                partially_checked_items.append(self.data(id_index, QtC.Qt.ItemDataRole.DisplayRole))
                partially_checked_indices.append(name_index)
            child_checked_item, child_partially_checked_items, child_checked_indices, child_partially_checked_indices = self.traverse_checkable_tree(name_index)
            checked_items.extend(child_checked_item)
            partially_checked_items.extend(child_partially_checked_items)
            checked_indices.extend(child_checked_indices)
            partially_checked_indices.extend(child_partially_checked_indices)
        return checked_items, partially_checked_items, checked_indices, partially_checked_indices

    def update_other_table(self, other_table: str, other_ids: list):
        # Updates another table with the checked IDs. These are one-to-many relationships like SpotComposition, where we
        # want to update the SpotCompositionID in the Spots table with the checked IDs in the SpotComposition table. This
        # method is useful when editing joined views, like editing the SpotComposition in the SampleEditView.
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return False
        checked_items, partially_checked_items, checked_indices, partially_checked_indices = self.traverse_checkable_tree(
            QtC.QModelIndex())
        checked_ids = []
        partially_checked_ids = []
        for index in checked_indices:
            checked_ids.append(self.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole))
        for index in partially_checked_indices:
            partially_checked_ids.append(self.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole))
        if update_other_table_with_checks(self.table, checked_ids, partially_checked_ids, other_table, other_ids):
            return True
        else:
            return False

    def update_many_table(self, many_table: str, item_ids: list | None):
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs provided for updating many-to-many table {self.many_to_many}')
            return False
        checked_items, partially_checked_items, checked_indices, partially_checked_indices = self.traverse_checkable_tree(QtC.QModelIndex())
        if update_many_table_with_checks(self.table, checked_items, partially_checked_items, many_table, item_ids):
            return True
        else:
            return False

class TreeListProxyModel(QtC.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.column = 0

    def filterAcceptsColumn(self, source_column, source_parent):
        return source_column == self.column

    def data(self, index: QtC.QModelIndex, role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return QtC.QVariant()
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            source_index = self.mapToSource(index)
            return self.sourceModel().data(source_index, role)
        return super().data(index, role)

class TreeSortFilterProxyModel(QtC.QSortFilterProxyModel):
    def __init__(self, parent=None, view=None):
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(True)  # Enables recursive filtering for tree structures
        self.view = view  # The view containing the model (e.g., QTreeView)

    def filterAcceptsRow(self, source_row, source_parent):
        # Override this method to implement custom filtering logic
        model = self.sourceModel()

        # Iterate through visible columns of the given row to check for a match
        column_count = model.columnCount(source_parent)
        for column in range(column_count):
            # Check if the column is visible
            if self.view is not None and self.view.isColumnHidden(column):
                continue  # Skip hidden columns

            index = model.index(source_row, column, source_parent)
            # If the filter pattern is empty, accept all rows
            if self.filterRegularExpression().pattern() == '':
                return True
            # If the current column's data matches the filter, accept this row
            if index.data() is not None and self.filterRegularExpression().match(str(index.data())).hasMatch():
                return True
        # If no column matches, reject this row
        return False



# ---------------------------
#    Tree Methods
# ---------------------------

def get_selected_tree_ids(selected_model: QtC.QAbstractItemModel | QtC.QAbstractProxyModel, indexes: list):
    item_ids = []
    parent_ids = []
    parent_rows = []
    for index in indexes:
        if index.column() == 0:
            item_id = selected_model.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole)
            parent_id = selected_model.data(index.siblingAtColumn(2), QtC.Qt.ItemDataRole.DisplayRole)
            parent_row = selected_model.data(index.siblingAtColumn(3), QtC.Qt.ItemDataRole.DisplayRole)
            item_ids.append(item_id)
            parent_ids.append(parent_id)
            parent_rows.append(parent_row)
    return item_ids, parent_ids, parent_rows

def find_tree_model(model, indexes: list | None):
    # Dig down through any proxy models to find the tree model and retrieve the model and mapped indexes
    if isinstance(model, CheckableTreeModel | TreeModel):
        tree_model = model
        tree_indexes = indexes
        return tree_model, tree_indexes
    else:
        try:
            source_model = model.sourceModel()
            source_indexes = [model.mapToSource(index) for index in indexes]
            tree_model, tree_indexes = find_tree_model(source_model, source_indexes)
            return tree_model, tree_indexes
        except AttributeError:
            try:
                source_model = model.source_model
                source_indexes = [model.mapToSource(index) for index in indexes]
                tree_model, tree_indexes = find_tree_model(source_model, source_indexes)
            except AttributeError:
                return None, None


# ---------------------------
#    Widget Classes
# ---------------------------

class FocusGroupBox(QGroupBox):
    focusLost = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super(FocusGroupBox, self).__init__(parent)
        self.setFocusPolicy(QtC.Qt.FocusPolicy.NoFocus)
        self.focus_lost_timer = QtC.QTimer(self)
        self.focus_lost_timer.setSingleShot(True)
        self.focus_lost_timer.timeout.connect(self.check_focus_state)
        self.initial_values = []
        self.edited = False
        self.installEventFilter(self)
        self.reset_edited()

    def reset_edited(self):
        self.edited = False
        self.connect_child_signals()

    def connect_child_signals(self):
        self.initial_values = []
        for child in self.findChildren(QtW.QWidget):
            if isinstance(child, QtW.QLineEdit):
                if isinstance(child.parent(), QtW.QComboBox):
                    continue
                try:
                    child.editingFinished.disconnect()
                except TypeError:
                    pass
                self.initial_values.append([child, child.text()])
                child.editingFinished.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, CheckableComboBox | CheckableTreeCombobox):
                try:
                    child.currentTextChanged.disconnect()
                except TypeError:
                    pass
                self.initial_values.append([child, child.currentText()])
                child.currentTextChanged.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, QtW.QComboBox):
                try:
                    child.activated.disconnect()
                except TypeError:
                    pass
                self.initial_values.append([child, child.currentIndex()])
                child.activated.connect(lambda ch=child: self.set_edited(ch))
            elif isinstance(child, QtW.QCheckBox):
                try:
                    child.stateChanged.disconnect()
                except TypeError:
                    pass
                self.initial_values.append([child, child.isChecked()])
                child.stateChanged.connect(lambda ch=child: self.set_edited(ch))
            child.installEventFilter(self)

    def disconnect_child_signals(self):
        for child in self.findChildren(QtW.QWidget):
            if isinstance(child, QtW.QLineEdit):
                try:
                    child.editingFinished.disconnect()
                except TypeError:
                    pass
            elif isinstance(child, CheckableComboBox | CheckableTreeCombobox):
                try:
                    child.currentTextChanged.disconnect()
                except TypeError:
                    pass
            elif isinstance(child, QtW.QComboBox):
                try:
                    child.activated.disconnect()
                except TypeError:
                    pass
            elif isinstance(child, QtW.QCheckBox):
                try:
                    child.stateChanged.disconnect()
                except TypeError:
                    pass
            child.removeEventFilter(self)

    def set_edited(self, child: QtW.QWidget):
        if not isinstance(child, QtW.QWidget):
            child = self.sender()
        if isinstance(child, QtW.QLineEdit) and isinstance(child.parent(), QtW.QComboBox):
            # The line edit of the combo box completer has been triggered, but wait until the index changes
            return
        initial_value = None
        for pair in self.initial_values:
            if pair[0] == child:
                initial_value = pair[1]
                break
        if initial_value is None:
            return
        if isinstance(child, QtW.QLineEdit):
            if child.text() != initial_value:
                logger_setup.get_logger().info(f'{child.objectName()} was edited')
                self.edited = True
        elif isinstance(child, QtW.QComboBox):
            if child.currentIndex() != initial_value:
                self.edited = True
        elif isinstance(child, QtW.QCheckBox):
            if child.isChecked() != initial_value:
                self.edited = True

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.FocusOut:
            self.focus_lost_timer.start(100)
        return super().eventFilter(obj, event)

    def check_focus_state(self, child=None):
        has_focus = self.any_child_has_focus()
        if not has_focus:
            logger_setup.get_logger().info(f'{self.objectName()} has lost focus')
            if self.edited:
                logger_setup.get_logger().info(f'{self.objectName()} was edited and needs to be updated')
                self.focusLost.emit()

    def any_child_has_focus(self):
        for child in self.findChildren(QtW.QWidget):
            if child.hasFocus():
                return True
        return False

class CustomDragTabBar(QtW.QTabBar):
    def __init__(self, permanent_tabs: list, parent=None):
        super().__init__(parent)
        self.permanent_tabs = permanent_tabs

    def add_vertical_line(self):
        # self.setStyleSheet("""
        #     QTabBar::tab {padding: 10px;}
        #     QTabBar::tab:nth-child(3) {{border-right: 5px solid red;}}
        #     """)
        self.setStyleSheet("""
            QTabBar::tab {padding: 10px;}
            """)

    def update_permanent_tabs(self, names: list):
        self.permanent_tabs = names

    def mouseReleaseEvent(self, event):
        # Move the permanent tabs to the left side of the tab bar
        super().mouseReleaseEvent(event)
        if self.permanent_tabs:
            self.correct_tab_order()

    def correct_tab_order(self):
        for index in range(self.count()):
            if self.tabText(index) in self.permanent_tabs:
                for i in range(len(self.permanent_tabs)):
                    if self.tabText(index) == self.permanent_tabs[i]:
                        if index != i:
                            # Permanent tab is not in the correct position
                            self.moveTab(index, i)
                        else:  # Permanent tab is in the correct position
                            break

class PartiallyCloseableTabWidget(QtW.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_tabs = []
        self.tabBar = CustomDragTabBar(self.permanent_tabs)
        self.setTabBar(self.tabBar)
        self.setTabsClosable(True)
        self.setMovable(True)

    def set_permanent_tabs(self, names: list):
        self.permanent_tabs = names
        self.tabBar.update_permanent_tabs(self.permanent_tabs)
        self.update_close_buttons()

    def update_close_buttons(self):
        for index in range(self.count()):
            if self.tabText(index) in self.permanent_tabs:
                self.tabBar.setTabButton(index, QtW.QTabBar.ButtonPosition.LeftSide, None)
                self.tabBar.setTabButton(index, QtW.QTabBar.ButtonPosition.RightSide, None)
        # self.setTabsClosable(True)
        # self.setMovable(True)

    def addTab(self, widget, name):
        for index in range(self.count()):
            # Check all tabs to see if the name already exists, set focus to that tab if it does
            if self.tabText(index) == name:
                self.setCurrentIndex(index)
                return
        super().addTab(widget, name)
        # if self.count() >= 3:
        #     self.tabBar.add_vertical_line()
        self.update_close_buttons()
        self.setCurrentIndex(self.count() - 1)

    def insertTab(self, index, widget, name):
        for i in range(self.count()):
            if self.tabText(i) == name:
                self.setCurrentIndex(i)
                return
        super().insertTab(index, widget, name)
        self.update_close_buttons()
        self.setCurrentIndex(index)

    def removeTab(self, index):
        super().removeTab(index)
        self.update_close_buttons()
        if self.tabText(index) in self.permanent_tabs and self.tabText(index-1) in self.permanent_tabs:
            self.setCurrentIndex(index-1)
        elif self.tabText(index) in self.permanent_tabs:
            self.setCurrentIndex(index-1)
        elif self.tabText(index-1) in self.permanent_tabs:
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(index)
        # if self.count() >= 3:
            # self.tabBar.add_vertical_line()

class CompleterInputDialog(QtW.QDialog):
    def __init__(self, parent: QtW.QWidget, title: str, label: str, completer_list: list[str], editable: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayout(QtW.QVBoxLayout())
        self.layout().addWidget(QtW.QLabel(label))
        self.combo_box = QtW.QComboBox()
        self.combo_box.setEditable(editable)
        self.line_edit = self.combo_box.lineEdit()
        self.combo_box.addItems(completer_list)
        self.completer = QtW.QCompleter(completer_list)
        self.completer.setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.line_edit.setCompleter(self.completer)
        self.layout().addWidget(self.combo_box)
        self.button_box = QtW.QDialogButtonBox(QtW.QDialogButtonBox.StandardButton.Ok | QtW.QDialogButtonBox.StandardButton.Cancel)
        self.layout().addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_input(self):
        return self.line_edit.text()

class ReorderListView(QtW.QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDefaultDropAction(QtC.Qt.DropAction.MoveAction)
        self.setDragDropMode(QtW.QListView.DragDropMode.DragDrop)
        self.setDragEnabled(True)

    def startDrag(self, action):
        index = self.currentIndex()
        # The permanent header will always be at the top, so this works even with multiple selection.
        if index.isValid():
            # Do not move the permanent header
            if index.data().replace(' ','') == self.model().sourceModel().permanent_header:
                return 
            super().startDrag(action)

    def dropEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            if index.row() == 0 and self.model().sourceModel().permanent_header != '':
                # Trying to drop before the permanent header
                event.ignore()
            elif self.dropIndicatorPosition() == self.dropIndicatorPosition().OnItem:
                # Not valid or trying to drop on an item
                event.ignore()
            else:
                # Dropping between items
                super().dropEvent(event)


class ColumnListProxyModel(QtC.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def data(self, index: QtC.QModelIndex, role: int = ...):
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            header = super().data(index, role)
            readable_header = get_readable_header(header)
            return readable_header
        return super().data(index, role)

class ColumnItemModel(QtG.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_header = ''

    def set_permanent_header(self, header: str):
        # Set the header that should always be checked, the name or display column
        self.permanent_header = header

    def data(self, index, role: int = ...):
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtC.Qt.ItemDataRole.DisplayRole) == self.permanent_header:
                return QtC.Qt.CheckState.Checked
            else:
                return super().data(index, role)
        return super().data(index, role)

    def setData(self, index, value, role: int = ...):
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtC.Qt.ItemDataRole.DisplayRole) == self.permanent_header and value == QtC.Qt.CheckState.Unchecked:
                return False
        return super().setData(index, value, role)

class CheckableSampleTableView(QtW.QTableView):
    def __init__(self):
        super().__init__()
        self.resizeColumnsToContents()
        self.clicked.connect(self.toggle_check_state)


    def toggle_check_state(self, index: QtC.QModelIndex):
        if self.model():
            self.model().dataChanged.connect(self.update)
            if index.isValid() and QtC.Qt.ItemFlag.ItemIsUserCheckable in self.model().flags(index):
                current_state = self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)
                new_state = QtC.Qt.CheckState.Unchecked if current_state == QtC.Qt.CheckState.Checked else QtC.Qt.CheckState.Checked
                self.model().setData(index, new_state, QtC.Qt.ItemDataRole.CheckStateRole)

class CheckableComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    edit_triggered = QtC.pyqtSignal(QtW.QComboBox)
    add_triggered = QtC.pyqtSignal(QtW.QComboBox)
    delete_triggered = QtC.pyqtSignal(QtW.QComboBox)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.completer().setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.completer().setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.lineEdit().setPlaceholderText("Search")
        self.lineEdit().setCompleter(self.completer())
        self.model_modifiable = False
        self.single_click = False
        self.not_null = False
        self.proxy_model = None
        # self.tableView = QtW.QTableView()
        # self.setView(self.tableView)
        self.setSizeAdjustPolicy(QtW.QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.context_menu = False
        self.name_col = None
        self.table = ''
        self.popup_shown = False

        self.view().viewport().installEventFilter(self)

    def model(self):
        if self.proxy_model:
            return self.proxy_model.sourceModel()
        else:
            return super().model()

    def setModel(self, model: CheckableSqlTableModel | CheckableSqlQueryModel | SampleAgeTableModel):
        super().setModel(model)
        combo_model = model
        if isinstance(model, QtC.QSortFilterProxyModel):
            self.proxy_model = model
            model = model.sourceModel()
        column = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        if isinstance(column, int):
            self.table = None
            self.name_col = None
            return
        # If it is not a table model, it is a view, get the name of the table
        if not isinstance(model, QtS.QSqlTableModel) and 'SampleAge' not in column and 'Reference' not in column:
            if 'Sample' in column:
                self.table = 'Samples'
            elif 'Aliquot' in column:
                self.table = 'Aliquots'
            elif 'Spot' in column:
                self.table = 'Spots'
            elif 'UPbAnalysis' in column:
                self.table = 'UPbAnalyses'
            elif 'Column' in column:
                self.table = 'Columns'
            elif 'Reference' in column:
                self.table = '"References"'
            view = model.tableView()
            self.name_col = get_view_name_column(view)
        # If it is just a table or SampleAge query, use the table name
        else:
            self.table = model.tableName()
            self.name_col = get_name_column(model.tableName())
        if self.name_col:
            show_column(self, combo_model.headerData(self.name_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))

    def enable_context_menu(self, show_context_menu: bool):
        self.context_menu = show_context_menu
        if self.context_menu and self.model_modifiable:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            # self.customContextMenuRequested.connect(self.contextMenuEvent)
        else:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.NoContextMenu)

    def contextMenuEvent(self, event):
        menu = TreeContextMenu()
        if self.table == '"References"':
            table = 'References'
        else:
            table = self.table
        if self.model().rowCount() !=0:
            edit_action = menu.addAction(f"Edit {TxM.add_spaces_camel(table)}")
            add_action = menu.addAction(f"Add {TxM.add_spaces_camel(table)}")
            clear_all_action = menu.addAction("Clear All Checks")
            delete_action = menu.addAction(f"Delete {TxM.add_spaces_camel(table)}")
        else:
            edit_action = None
            add_action = menu.addAction(f"Add {TxM.add_spaces_camel(table)}")
            clear_all_action = None
            delete_action = None
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == edit_action:
            self.edit_triggered.emit(self)
        elif action == add_action:
            self.add_triggered.emit(self)
        elif action == clear_all_action:
            self.clear_all_checks()
        elif action == delete_action:
            self.delete_triggered.emit(self)

    def set_single_click(self, single_click: bool):
        self.single_click = single_click

    def set_closed_on_line_edit_click(self, closedOnLineEditClick: bool):
        self.closedOnLineEditClick = closedOnLineEditClick

    def set_line_edit_text(self, text):
        self.lineEdit().setText(text)

    def clear_all_checks(self):
        for row in range(self.model().rowCount()):
            index = self.model().index(row, self.name_col)
            # if row == self.view().currentIndex().row():
            #     self.model().setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
            # else:
            self.model().setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            # logger_setup.get_logger().info(
            #     f"Changed {self.model().data(index, QtC.Qt.ItemDataRole.DisplayRole)} state to {self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)}"
            # )
        logger_setup.get_logger().info(f'Cleared all checks in {self.table} combo box')

    def showPopup(self):
        super().showPopup()
        if self.model().rowCount() == 0:
            return
        # self.view().resizeColumnToContents(self.name_col)
        if self.width() > self.view().sizeHintForColumn(self.name_col):
            self.view().setFixedWidth(self.width())
        else:
            self.view().setFixedWidth(self.view().sizeHintForColumn(self.name_col))
        self.view().setFixedHeight(self.view().sizeHint().height())
        self.popup_shown = True

    def hidePopup(self):
        if self.popup_shown:
            super().hidePopup()
            self.closing.emit()
            self.popup_shown = False

    def eventFilter(self, obj, event):
        if obj == self.lineEdit():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                if self.closedOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return super().eventFilter(obj, event)

        if obj == self.view().viewport():
            if self.proxy_model:
                proxy_index = self.view().currentIndex()
                source_index = self.proxy_model.mapToSource(proxy_index)
            else:
                source_index = self.view().currentIndex()
            if event.type() == QtC.QEvent.Type.MouseButtonRelease and event.button() == QtC.Qt.MouseButton.LeftButton:
                if self.single_click and self.model().checked_ids:
                    # Was the only selected item unchecked? If so, set the current index to -1 before clearing all checks
                    if isinstance(self.model(), CheckableTreeModel):
                        clicked_id = self.model().index(source_index.row(), 1, source_index.parent()).data(
                            QtC.Qt.ItemDataRole.DisplayRole)
                    else:
                        clicked_id = self.model().index(source_index.row(), 0).data(QtC.Qt.ItemDataRole.DisplayRole)
                    if clicked_id in self.model().checked_ids:
                        if self.not_null:
                            logger_setup.get_logger().error(f'{self.model().headerData(self.name_col, 
                               Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)} cannot be blank')
                            return True
                        self.view().setCurrentIndex(QtC.QModelIndex())
                    self.clear_all_checks()
                    self.model().setData(source_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                    self.set_line_edit_text(source_index.data(QtC.Qt.ItemDataRole.DisplayRole))
                    self.hidePopup()
                    return True
                else:
                    # Get model index from view index
                    index = self.model().index(source_index.row(), self.name_col)
                    if self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                        self.model().setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    elif self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Unchecked:
                        self.model().setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                    checked_ids = self.model().checked_ids
                    checked_names = []
                    for id in checked_ids:
                        checked_names.append(get_name_from_id(self.table, id))
                    text = ', '.join(checked_names)
                    self.set_line_edit_text(text)
                    self.showPopup()
                    return True
            elif event.type() == QtC.QEvent.Type.MouseButtonRelease and event.button() == QtC.Qt.MouseButton.RightButton:
                if self.context_menu:
                    self.contextMenuEvent(event)
                    return True
            return super().eventFilter(obj, event)

        return super().eventFilter(obj, event)

class SearchableSQLComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    delete_triggered = QtC.pyqtSignal(QtW.QComboBox)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_menu = False
        self.name_col = None
        self.userTyped = False
        self.previous_index = self.currentIndex()
        self.proxy_model = QtC.QSortFilterProxyModel()

    def setModel(self, model: QtS.QSqlTableModel | QtS.QSqlQueryModel | SQLiteTableModel):
        self.proxy_model.setSourceModel(model)
        super().setModel(self.proxy_model)
        self.name_col = None
        try:
            if model.view != '':
                name_col = get_view_name_column(model.view)
        except AttributeError:
            pass
        if not self.name_col:
            self.name_col = get_name_column(model.tableName())
        self.setModelColumn(self.name_col)

    def search_items(self, text):
        self.userTyped = True
        self.proxy_model.setFilterFixedString(text)
        self.showPopup()
        if self.proxy_model.rowCount() > 0:
            self.setCurrentIndex(0)
        else:
            self.setCurrentIndex(0)

    def enable_context_menu(self, show_context_menu: bool):
        self.context_menu = show_context_menu
        if self.context_menu:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            # self.customContextMenuRequested.connect(self.contextMenuEvent)
        else:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.NoContextMenu)

    def contextMenuEvent(self, event):
        menu = QtW.QMenu(self)
        if self.model().rowCount() !=0:
            delete_action = menu.addAction(f"Delete item")
        else:
            delete_action = None
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.delete_triggered.emit(self)

    def hidePopup(self):
        super().hidePopup()
        self.closing.emit()
        # self.update_line_edit()

class SearchableComboBox(QtW.QComboBox):
    selection_changed = QtC.pyqtSignal(QtW.QComboBox)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.list_view = QtW.QListView()
        self.setView(self.list_view)
        self.previous_index = -1
        # self.all_items = []
        self.completer().setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.completer().setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.lineEdit().setCompleter(self.completer())
        self.lineEdit().editingFinished.connect(self.validate_input)

    def addItem(self, text: str):
        super().addItem(text)
        # Set the default text to blank
        self.lineEdit().setText(None)

    def addItems(self, texts):
        super().addItems(texts)
        # Set the default text to blank
        self.lineEdit().setText(None)

    def validate_input(self):
        text = self.lineEdit().text()
        if self.findText(text) == -1 or text == 'None':
            self.lineEdit().setText(None)
            self.setCurrentIndex(-1)
        elif text not in [self.itemText(i) for i in range(self.count())]:
            # The text does not match anything in the combo box
            # Reset the text to blank
            self.lineEdit().setText(None)
            self.setCurrentIndex(-1)

class TemporaryComboBox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)

    def hidePopup(self):
        super().hidePopup()
        self.closing.emit()

class CheckableTreeView(QtW.QTreeView):
    close = QtC.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.expandAll()
        self.hideColumn(1)  # don't show ID column
        self.hideColumn(2)  # don't show parent ID column
        self.hideColumn(3)  # don't show parent row column
        self.setSortingEnabled(False)
        self.setHeaderHidden(False)

        self.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        self.model_edited = False
        # self.clicked.connect(self.toggle_check_state)

    def setModel(self, model: TreeModel):
        super().setModel(model)
        self.connect_edited_signal()

    def resizeColumnsToContents(self):
        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)

    def connect_edited_signal(self):
        self.model().dataChanged.connect(lambda: self.toggle_edited(True))

    def disconnect_edited_signal(self):
        try:
            self.model().dataChanged.disconnect(lambda: self.toggle_edited(True))
        except TypeError:
            pass

    def toggle_edited(self, edited: bool):
        self.model_edited = edited
        # print(f'{self.model().table} edited {edited}')

    def toggle_check_state(self, index: QtC.QModelIndex):
        if self.model():
            if index.isValid() and QtC.Qt.ItemFlag.ItemIsUserCheckable in self.model().flags(index):
                current_state = self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)
                new_state = QtC.Qt.CheckState.Unchecked if current_state == QtC.Qt.CheckState.Checked else QtC.Qt.CheckState.Checked
                self.model().setData(index, new_state, QtC.Qt.ItemDataRole.CheckStateRole)

    def expand_all_checked(self):
        tree_model, indexes = find_tree_model(self.model(), None)
        checked_items, partially_checked_items, checked_indices, partially_checked_indices = tree_model.traverse_checkable_tree(QtC.QModelIndex())

        def expand_parents(item_index: QtC.QModelIndex):
            parent = item_index.parent()
            while parent.isValid():
                self.expand(parent)
                parent = parent.parent()

        for index in checked_indices:
            expand_parents(index)
        for index in partially_checked_indices:
            expand_parents(index)

class TreeCombobox(QtW.QComboBox):
    closing = QtC.pyqtSignal()
    edit_triggered = QtC.pyqtSignal(QtW.QComboBox)
    add_triggered = QtC.pyqtSignal(QtW.QComboBox, QAction)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.completer().setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.completer().setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.lineEdit().setPlaceholderText("Search")
        self.lineEdit().setCompleter(self.completer())
        self.lineEdit().setReadOnly(False)
        self.treeView = QtW.QTreeView()
        self.treeView.setRootIsDecorated(True)
        self.checkable = False
        self.popup_shown = False
        self.context_menu = False
        self.setView(self.treeView)
        self.treeView.viewport().installEventFilter(self)
        self.treeView.setWindowFlags(QtC.Qt.WindowType.Popup)

    def set_text(self, text):
        if not self.checkable:
            self.lineEdit().setText(text)

    def setModel(self, model):
        super().setModel(model)
        # Hide all but the first column
        for column in range(1, model.columnCount()):
            self.treeView.hideColumn(column)
        self.treeView.resizeColumnToContents(1)
        self.treeView.setMinimumWidth(self.treeView.sizeHint().width())

    def enable_context_menu(self, show_context_menu: bool):
        self.context_menu = show_context_menu
        if self.context_menu:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
        else:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.NoContextMenu)

    def show_context_menu(self, pos):
        menu = TreeContextMenu()
        menu.set_view(self.treeView, False)
        action = menu.exec(self.mapToGlobal(pos))
        if action:
            if action.text() == 'Edit':
                self.edit_triggered.emit(self)
                logger_setup.get_logger().info(f'Edit triggered for combo box')
            elif 'Add' in action.text() or 'Insert' in action.text():
                self.add_triggered.emit(self, action)
                logger_setup.get_logger().info(f'Add triggered for combo box')
            elif 'Expand' in action.text() or 'Collapse' in action.text():
                expand_collapse(self.treeView, action)

    def showPopup(self):
        tree_model, indexes = find_tree_model(self.model(), None)
        if tree_model:
            restore_expanded_state(tree_model.table, tree_model, self.treeView)
        else:
            return
        if tree_model.rowCount(QtC.QModelIndex()) == 0:
            return
        self.treeView.resizeColumnToContents(0)
        self.treeView.setFixedWidth(self.treeView.sizeHintForColumn(0))
        self.treeView.setFixedHeight(self.treeView.sizeHint().height())
        # font_metrics = QtG.QFontMetrics(self.treeView.font())
        # max_text_width = 0
        # def get_max_text_width(model, parent, max_text_width):
        #     for row in range(model.rowCount(parent)):
        #         index = model.index(row, 0, parent)
        #         text = index.data(QtC.Qt.ItemDataRole.DisplayRole)
        #         width = font_metrics.horizontalAdvance(text)
        #         if width > max_text_width:
        #             max_text_width = width
        #         get_max_text_width(model, index, max_text_width)
        # get_max_text_width(self.model(), QtC.QModelIndex(), max_text_width)
        # total_width = max_text_width + self.treeView.verticalScrollBar().sizeHint().width()
        # self.treeView.setFixedWidth(total_width)
        super().showPopup()
        self.popup_shown = True

    def hidePopup(self):
        if self.popup_shown:
            super().hidePopup()
            model, indexes = find_tree_model(self.model(), None)
            if model:
                save_expanded_state(model.table, self.model(), self.treeView)
            self.popup_shown = False
            self.closing.emit()

    def eventFilter(self, obj, event):
        if obj == self.treeView.viewport():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                # If the user clicks on the expand/collapse button, do not select the item, only expand/collapse

                index = self.treeView.indexAt(event.pos())
                model, indexes = find_tree_model(self.model(), None)
                if not index.isValid():
                    super().eventFilter(obj, event)
                # Define the rectangle for the item and the expand/collapse button
                item_rect = self.treeView.visualRect(index)
                option = QtW.QStyleOptionViewItem()
                option.initFrom(self.treeView)
                option.rect = item_rect
                option.state = QtW.QStyle.StateFlag.State_Enabled
                if self.treeView.model().hasChildren(index):
                    option.state |= QtW.QStyle.StateFlag.State_Children
                if self.treeView.isExpanded(index):
                    option.state |= QtW.QStyle.StateFlag.State_Open

                expand_button_rect = self.treeView.style().subElementRect(
                    QtW.QStyle.SubElement.SE_TreeViewDisclosureItem,
                    option, self.treeView)
                if expand_button_rect.contains(event.pos()):
                    self.set_text(index.data(QtC.Qt.ItemDataRole.DisplayRole))
                    self.hidePopup()
                    return True
                else:
                    if self.treeView.isExpanded(index):
                        self.treeView.collapse(index)
                    else:
                        self.treeView.expand(index)
                    save_expanded_state(model.table, model, self.treeView)
                    self.showPopup()
                    return True
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

class CheckableTreeCombobox(TreeCombobox):
    closing = QtC.pyqtSignal()
    edit_triggered = QtC.pyqtSignal(QtW.QComboBox)
    add_triggered = QtC.pyqtSignal(QtW.QComboBox, QAction)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.completer().setCompletionMode(QtW.QCompleter.CompletionMode.PopupCompletion)
        self.completer().setFilterMode(QtC.Qt.MatchFlag.MatchContains)
        self.lineEdit().setPlaceholderText("Search")
        self.lineEdit().setCompleter(self.completer())
        self.checkable = True
        self.single_click = False
        self.closedOnLineEditClick = False
        self.edited = False
        self.treeView = CheckableTreeView()
        # show the empty root item in the combo box
        self.treeView.setRootIsDecorated(True)
        self.setView(self.treeView)
        self.context_menu = False

        self.lineEdit().installEventFilter(self)
        self.treeView.viewport().installEventFilter(self)

    def setModel(self, model: CheckableTreeModel):
        super().setModel(model)
        if self.model():
            self.model().dataChanged.connect(self.update_line_edit)
        show_column(self, model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
        self.treeView.resizeColumnsToContents()
        self.treeView.expand_all_checked()

    def set_single_click(self, single_click):
        self.single_click = single_click

    def set_line_edit_text(self, text):
        self.lineEdit().setText(text)

    def update_line_edit(self):
        current_line_edit_text = self.lineEdit().text()
        tree_model, indexes = find_tree_model(self.model(), None)
        checked_items, partially_checked_items, checked_indices, partially_checked_indices = tree_model.traverse_checkable_tree(
            QtC.QModelIndex())
        if partially_checked_indices:
            # At least one item is partially checked, so the line edit should be a dash
            self.lineEdit().setText('-')
        elif checked_indices:
            # At least some items are fully checked and should be included in the list
            new_line_edit_text = str(self.model().data(self.treeView.currentIndex(), QtC.Qt.ItemDataRole.DisplayRole))
            if current_line_edit_text == '' or current_line_edit_text == '-':
                self.lineEdit().setText(new_line_edit_text)
            else:
                if new_line_edit_text not in current_line_edit_text:
                    text = ', '.join([current_line_edit_text, new_line_edit_text])
                    self.lineEdit().setText(text)
        else:
            # No items are checked, so the line edit should be blank
            self.lineEdit().setText('')

    def clear_all_checks(self):
        # traverse the tree and uncheck all items
        def traverse_tree(parent: QtC.QModelIndex):
            for row in range(self.model().rowCount(parent)):
                index = self.model().index(row, 0, parent)
                self.model().setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                traverse_tree(index)

        traverse_tree(QtC.QModelIndex())

    def showPopup(self):
        super().showPopup()
        self.popup_shown = True

    def hidePopup(self):
        if self.popup_shown:
            super().hidePopup()
            self.popup_shown = False

    def show_context_menu(self, pos):
        menu = TreeContextMenu()
        menu.set_view(self.treeView, False)
        action = menu.exec(self.mapToGlobal(pos))
        if action:
            if action.text() == 'Edit':
                self.edit_triggered.emit(self)
                logger_setup.get_logger().info(f'Edit triggered for checkable tree combo box')
            elif 'Add' in action.text() or 'Insert' in action.text():
                self.add_triggered.emit(self, action)
                logger_setup.get_logger().info(f'Add triggered for checkable tree combo box')
            elif 'Expand' in action.text() or 'Collapse' in action.text():
                expand_collapse(self.treeView, action)

    def eventFilter(self, obj, event):
        if obj == self.lineEdit():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease:
                if self.closedOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return super().eventFilter(obj, event)

        if obj == self.treeView.viewport():
            if event.type() == QtC.QEvent.Type.MouseButtonRelease and event.button() == QtC.Qt.MouseButton.LeftButton:
                index = self.treeView.indexAt(event.pos())
                if not index.isValid():
                    super().eventFilter(obj, event)
                # Define the rectangle for the item and the expand/collapse button
                item_rect = self.treeView.visualRect(index)
                option = QtW.QStyleOptionViewItem()
                option.initFrom(self.treeView)
                option.rect = item_rect
                option.state = QtW.QStyle.StateFlag.State_Enabled
                if self.treeView.model().hasChildren(index):
                    option.state |= QtW.QStyle.StateFlag.State_Children
                if self.treeView.isExpanded(index):
                    option.state |= QtW.QStyle.StateFlag.State_Open

                expand_button_rect = self.treeView.style().subElementRect(QtW.QStyle.SubElement.SE_TreeViewDisclosureItem,
                                                                 option, self.treeView)
                if expand_button_rect.contains(event.pos()):
                    if self.single_click:
                        # Was the only selected item unchecked? If so, set the current index to the root before clearing all checks
                        checked_items, partially_checked_items, checked_indices, partially_checked_indices = self.model().traverse_checkable_tree(
                            QtC.QModelIndex())
                        if self.treeView.currentIndex() in checked_indices:
                            self.treeView.setCurrentIndex(QtC.QModelIndex())
                        self.clear_all_checks()
                        self.treeView.toggle_check_state(self.treeView.currentIndex())
                        self.set_line_edit_text(self.treeView.currentIndex().data(QtC.Qt.ItemDataRole.DisplayRole))
                        self.hidePopup()
                    else:
                        self.treeView.toggle_check_state(self.treeView.currentIndex())
                        self.update_line_edit()
                        self.showPopup()
                    return True
                else:
                    if self.treeView.isExpanded(index):
                        self.treeView.collapse(index)
                    else:
                        self.treeView.expand(index)
                    save_expanded_state(self.model().table, self.model(), self.treeView)
                    self.showPopup()
                    return True
            elif event.type() == QtC.QEvent.Type.MouseButtonRelease and event.button() == QtC.Qt.MouseButton.RightButton:
                self.show_context_menu(event.pos())
                return True
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

class TreeContextMenu(QtW.QMenu):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.tree_view = None
        self.model = None
        self.indexes = None

    def set_view(self, tree_view: QtW.QTreeView, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        self.tree_view = tree_view
        self.model, self.indexes = find_tree_model(self.tree_view.model(), self.tree_view.selectedIndexes())
        item_ids, parent_ids, parent_rows = get_selected_tree_ids(self.model, self.indexes)
        if len(item_ids) == 1:  # only one item selected
            self.add_single_tree_actions(delete_active, add_active, edit_active)
        else:
            self.add_multi_tree_actions(delete_active, add_active, edit_active)
        self.add_expand_collapse_actions()
        if 'Aliquot' in self.model.table:
            self.add_view_data_actions()

    def add_single_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        if edit_active:
            edit_action = self.addAction('Edit')
        if add_active:
            add_menu = self.addMenu('Add')
            insert_above_action = add_menu.addAction('Insert above')
            insert_below_action = add_menu.addAction('Insert below')
            add_child_action = add_menu.addAction('Add child')
            add_parent_action = add_menu.addAction('Add parent')
            add_end_action = add_menu.addAction('Add to end')
        if delete_active:
            delete_action = self.addAction('Delete')

    def add_multi_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        if edit_active:
            edit_action = self.addAction('Edit')
        if delete_active:
            delete_action = self.addAction('Delete')
        if add_active:
            add_action = self.addAction('Add')

    def add_expand_collapse_actions(self):
        expand_menu = self.addMenu('Expand')
        expand_children_action = expand_menu.addAction('Expand children')
        expand_all_children_action = expand_menu.addAction('Expand all children')
        expand_all_action = expand_menu.addAction('Expand all')
        collapse_menu = self.addMenu('Collapse')
        collapse_children_action = collapse_menu.addAction('Collapse children')
        collapse_all_children_action = collapse_menu.addAction('Collapse all children')
        collapse_all_action = collapse_menu.addAction('Collapse all')

    def add_checkable_actions(self):
        if isinstance(self.tree_view, CheckableTreeView):
            clear_action = self.addAction('Clear checks')

    def add_view_data_actions(self):
        view_data_menu = self.addMenu('View Data')
        view_spot_action = view_data_menu.addAction('View Spots')
        view_upb_analyses_action = view_data_menu.addAction('View U-Pb Analyses')


class FrozenTableView(QtW.QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frozen_table_view = QtW.QTableView()
        # self.frozen_table_view.setFocusPolicy(QtC.Qt.FocusPolicy.NoFocus)
        self.frozen_table_view.verticalHeader().hide()
        self.frozen_table_view.horizontalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeMode.Fixed)

        layout = QtW.QVBoxLayout(self)
        layout.addWidget(self.frozen_table_view)

        self.viewport().stackUnder(self.frozen_table_view)

        self.frozen_table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozen_table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.frozen_table_view.show()
        self.update_frozen_table_geometry()

        self.verticalHeader().sectionResized.connect(self.update_section_height)
        self.horizontalHeader().sectionResized.connect(self.update_section_width)
        self.verticalScrollBar().valueChanged.connect(self.frozen_table_view.verticalScrollBar().setValue)
        self.frozen_table_view.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)

        # self.frozen_table_view.installEventFilter(self)

    def setModel(self, model):
        super().setModel(model)
        self.frozen_table_view.setModel(model)
        self.frozen_table_view.setSelectionModel(self.selectionModel())
        for col in range(model.columnCount()):
            if col != 1:
                self.frozen_table_view.hideColumn(col)

        self.update_frozen_table_geometry

    def update_section_height(self, logicalIndex, oldSize, newSize):
        self.frozen_table_view.setRowHeight(logicalIndex, self.rowHeight(logicalIndex))

    def update_section_width(self, logicalIndex, oldSize, newSize):
        self.frozen_table_view.setColumnWidth(logicalIndex, self.columnWidth(logicalIndex))
        self.update_frozen_table_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_frozen_table_geometry()

    def moveCursor(self, cursorAction, modifiers):
        current = super().moveCursor(cursorAction, modifiers)
        if cursorAction == QtW.QAbstractItemView.CursorAction.MoveLeft and current.column() > 1 and self.visualRect(current).topLeft().x() < self.frozen_table_view.columnWidth(1):
            new_value = self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() - self.frozen_table_view.columnWidth(1)
            self.horizontalScrollBar().setValue(new_value)
        return current

    def scrollTo(self, index, hint = ...):
        if index.column() > 1:
            super().scrollTo(index, hint)

    def update_frozen_table_geometry(self):

        self.frozen_table_view.setGeometry(self.verticalHeader().width() + self.frameWidth() - 1,
                                           self.frameWidth() - 1, self.columnWidth(1) + 1,
                                           self.viewport().height() + self.horizontalHeader().height() + 1)
        self.frozen_table_view.setColumnWidth(1, self.columnWidth(1) + 1)
        logger_setup.get_logger().debug(f'Frozen column geometry: (x: {self.frozen_table_view.x()}, y: {self.frozen_table_view.y()}, width: {self.frozen_table_view.width()}, height: {self.frozen_table_view.height()})')
        logger_setup.get_logger().debug(f'Table geometry: (x: {self.x()}, y: {self.y()}, width: {self.width()}, height: {self.height()})')
        logger_setup.get_logger().debug(f'Viewport geometry: (x: {self.viewport().x()}, y: {self.viewport().y()}, width: {self.viewport().width()}, height: {self.viewport().height()})')

    # def eventFilter(self, object, event):
    #     if object == self.frozen_table_view.viewport():
    #         object = self.viewport()
    #     super().eventFilter(object, event)

class MaxWidthDelegate(QStyledItemDelegate):
    def __init__(self, max_width, parent=None):
        super().__init__(parent)
        self.max_width = max_width

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QtC.QSize(min(size.width(), self.max_width), size.height())

# ---------------------------
#    Widget Methods
# ---------------------------

def set_comboBox_text(comboBox: QtW.QComboBox, text: str):
    if text == '' or text == '-':
        comboBox.setCurrentIndex(-1)
    else:
        comboBox.setCurrentText(text)

def show_column(comboBox: QtW.QComboBox, column: str):
    try:
        if comboBox.proxy_model:
            model = comboBox.proxy_model
        else:
            model = comboBox.model()
    except AttributeError:
        model = comboBox.model()
    if model:
        for col in range(model.columnCount()):
            header = model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
            if header == column:
                comboBox.setModelColumn(col)
                if isinstance(model, QtC.QSortFilterProxyModel):
                    model.sort(col, QtC.Qt.SortOrder.AscendingOrder)
                return

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

def add_tree_popup(tree_view: QtW.QTreeView, tree_model: TreeModel, action: QtG.QAction | None = None):
    dlg_args = None
    indexes = tree_view.selectedIndexes()
    model = tree_view.model()
    tree_model, tree_indexes = find_tree_model(model, indexes)
    item_ids, parent_ids, parent_rows = get_selected_tree_ids(tree_model, tree_indexes)
    if action:
        if action.text() == 'Insert above':
            row = parent_rows[0]
            parent_id = parent_ids[0]
            dlg_args = {'parent_id' : parent_id, 'parent_row': row}
        elif action.text() == 'Insert below':
            row = parent_rows[0] + 1
            parent_id = parent_ids[0]
            dlg_args = {'parent_id' : parent_id, 'parent_row': row}
        elif action.text() == 'Add child':
            parent_id = item_ids[0]
            dlg_args = {'parent_id' : parent_id}
        elif action.text() == 'Add parent':
            dlg_args = {'add_item': 'parent', 'update_ids': item_ids, 'new_child_ids': parent_ids, 'new_parent_rows': parent_rows}
        elif action.text() == 'Add to end':
            dlg_args = None
    return dlg_args

def save_expanded_state(table: str, model, treeView: QtW.QTreeView):
    '''
    Save the expanded state of the tree view to the settings
    @param table: Name of table with parent-child relationships
    @param model: The model to save the state from, some kind of QSqlQueryModel or QSortFilterProxyModel
    @param treeView: The view displaying the model
    @return:
    '''

    expanded_ids = set()

    def save_state(index):
        if index.isValid() and treeView.isExpanded(index):
            item_id = model.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole)
            expanded_ids.add(item_id)
        for i in range(model.rowCount(index)):
            save_state(model.index(i, 0, index))

    root_index = QtC.QModelIndex()
    for i in range(model.rowCount(root_index)):
        save_state(model.index(i, 0, root_index))
    settings.setValue(f'expanded_ids_{table}', expanded_ids)

def restore_expanded_state(table: str, model, treeView: QtW.QTreeView):
    """
    Restore the expanded state of the tree view from the settings
    :param table: Name of table with parent-child relationships
    :param model: The model to restore the state to, some kind of QSqlTableModel or QSortFilterProxyModel
    :param treeView: The view to display the model
    :return:
    """
    logger_setup.get_logger().info(f'Restoring expanded state for {table} table')
    start_expand_tree_time = time.time()
    expanded_ids = settings.value(f'expanded_ids_{table}', set())
    indexes_to_expand = set()
    indexes_to_collapse = set()

    def restore_state(index):
        item_id = model.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole)
        if index == QtC.QModelIndex():
            pass
        elif item_id in expanded_ids:
            indexes_to_expand.add(index)
        else:
            indexes_to_collapse.add(index)
        for row in range(model.rowCount(index)):
            restore_state(model.index(row, 0, index))

    restore_state(QtC.QModelIndex())
    for index in indexes_to_expand:
        treeView.setExpanded(index, True)
    for index in indexes_to_collapse:
        treeView.setExpanded(index, False)
    logger_setup.get_logger().info(f'Expanded state restored in {time.time() - start_expand_tree_time} seconds')

def expand_all_children(tree_view: QtW.QTreeView, parent_index: QtC.QModelIndex):
    model = tree_view.model()
    # make sure the parent_index has column 0
    if not parent_index.isValid():
        parent_index = QtC.QModelIndex()  # parent is root
    if parent_index.column() != 0:
        parent_index = parent_index.siblingAtColumn(0)
    tree_view.expand(parent_index)
    for row in range(model.rowCount(parent_index)):
        child_index = model.index(row, 0, parent_index)
        expand_all_children(tree_view, child_index)

def collapse_all_children(tree_view: QtW.QTreeView, parent_index: QtC.QModelIndex):
    # make sure the parent_index has column 0
    if not parent_index.isValid():
        parent_index = QtC.QModelIndex()  # parent is root
    if parent_index.column() != 0:
        parent_index = parent_index.siblingAtColumn(0)

    model = tree_view.model()
    for row in range(model.rowCount(parent_index)):
        child_index = model.index(row, 0, parent_index)
        collapse_all_children(tree_view, child_index)

def expand_collapse(tree_view: QtW.QTreeView, action: QtG.QAction):
    if action.text() == 'Expand children':
        tree_view.expand(tree_view.selectedIndexes()[0])
    elif action.text() == 'Expand all children':
        for index in tree_view.selectedIndexes():
            expand_all_children(tree_view, index)
    elif action.text() == 'Expand all':
        tree_view.expandAll()
    elif action.text() == 'Collapse children':
        tree_view.collapse(tree_view.selectedIndexes()[0])
    elif action.text() == 'Collapse all children':
        for index in tree_view.selectedIndexes():
            collapse_all_children(tree_view, index)
    elif action.text() == 'Collapse all':
        tree_view.collapseAll()

def populate_combo_box(comboBox: QtW.QComboBox, **kwargs):
    table: str = None
    view: str = None
    query: str = None
    column: str = None
    for key, value in kwargs.items():
        if key == 'table':
            table = TxM.remove_spaces(value)  # ensure there are no spaces in the table name
            if table == 'References':
                table = '"References"'
        elif key == 'query':
            query = value
        elif key == 'column':
            column = value
    if query:
        model = DisplayRoundedQueryModel()
        model.setQuery(query)
        table = model.tableName()
        try:
            view = model.tableView()
        except AttributeError:
            pass
        if table == 'SampleAges':
            model.rounded = False
            proxy_model = SampleAgeProxyModel()
            proxy_model.setSourceModel(model)
            model = proxy_model
    elif 'View' in table:
        view = table
        model = DisplayRoundedQueryModel()
        model.setQuery(f"SELECT * FROM {view}")
        table = model.tableName()
    else:
        model = DisplayRoundedModel()
        set_table(model, table)
    if table in SQLUtils.user_viewable_trees:
        if isinstance(comboBox, CheckableTreeCombobox):
            tree_model = CheckableTreeModel()
            tree_model.setSourceModel(model)
            comboBox.setModel(tree_model)
        else:
            tree_model = TreeModel()
            tree_model.setSourceModel(model)
            comboBox.setModel(tree_model)
        if column:
            show_column(comboBox, column)
        else:
            show_column(comboBox, tree_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
    else:
        if isinstance(comboBox, CheckableComboBox) and not view:
            checkable_model = CheckableSqlTableModel()
            set_table(checkable_model, table)
            comboBox.setModel(checkable_model)
        elif isinstance(comboBox, CheckableComboBox) and view:
            checkable_model = CheckableSqlQueryModel()
            checkable_model.setQuery(f"SELECT * FROM {view}")
            comboBox.setModel(checkable_model)
        else:
            comboBox.setModel(model)
        if column:
            show_column(comboBox, column)
        elif view:
            name_col = get_view_name_column(view)
            show_column(comboBox, model.headerData(name_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
        else:
            name_col = get_name_column(table)
            show_column(comboBox, model.headerData(name_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))

def populate_model_checks(model: CheckableSqlTableModel | CheckableSqlQueryModel, item_ids, item_table: str=None, table_id_header: str=None):
    if table_id_header is None:
        table_id_header = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
    item_id_header = get_headers(item_table)[0]
    query_model = QtS.QSqlQueryModel()
    if len(item_ids) > 1:
        query_where_str = f'in {tuple(item_ids)}'
    elif len(item_ids) == 1:
        query_where_str = f'= {item_ids[0]}'
    else:
        logger_setup.get_logger().error(f'No item IDs given for {model.tableName()}')
        return False
    try:
        col = model.view_name_col
        if col == '':
            col = get_name_column(model.tableName())
    except AttributeError:
        col = get_name_column(model.tableName())
    for row in range(model.rowCount()):
        table_id = model.index(row, 0).data()
        if item_table == 'References':
            model_query = f'SELECT {table_id_header}, {item_id_header} FROM "References" WHERE {item_id_header} {query_where_str} AND {table_id_header} = {table_id}'
        else:
            model_query = f"SELECT {table_id_header}, {item_id_header} FROM {item_table} WHERE {item_id_header} {query_where_str} AND {table_id_header} = {table_id}"
        query_model.setQuery(model_query)
        if query_model.lastError().isValid():
            logger_setup.get_logger().critical(f'Error getting checks for {model.tableName()}')
            logger_setup.get_logger().debug(f'Error: {model.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {model_query}')
            return False
        # Go through each line in the model and check how many item_ids have this tag
        if query_model.rowCount() == len(item_ids):
            # All items have this tag
            model.setData(model.index(row, col), QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
        elif query_model.rowCount() > 0:
            # Some items have this tag
            model.setData(model.index(row, col), QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
        else:
            # No items have this tag, go ahead and uncheck it
            model.setData(model.index(row, col), QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
    return True

def populate_tree_model_checks(tree_model: CheckableTreeModel, item_ids, item_table: str=None, table_id_header: str=None):
    id_col = 1  # ID column is always placed in the second column
    if not item_ids[0]:
        tree_model.blockSignals(True)
        tree_model.clear_checks(QtC.QModelIndex())
        tree_model.blockSignals(False)
        return True
    table = tree_model.table
    if table_id_header is None:
        table_id_header = tree_model.headerData(id_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        if ' ' in table_id_header:
            table_id_header = TxM.remove_spaces(table_id_header)
    item_id_header = get_headers(item_table)[0]
    query_model = QtS.QSqlQueryModel()
    if len(item_ids) > 1:
        query_where_str = f'in {tuple(item_ids)}'
    elif len(item_ids) == 1:
        query_where_str = f'= {item_ids[0]}'
    else:
        logger_setup.get_logger().error(f'No item IDs given for {table}')
        return False
    table_model = QtS.QSqlQueryModel()
    table_model.setQuery(f"SELECT * FROM {table}")
    all_items = []
    some_items = []
    for row in range(table_model.rowCount()):
        table_id = table_model.index(row, 0).data()
        query_model = f"SELECT {table_id_header}, {item_id_header} FROM {item_table} WHERE {item_id_header} {query_where_str} AND {table_id_header} = {table_id}"
        query_model.setQuery(query_model)
        if query_model.lastError().isValid():
            logger_setup.get_logger().critical(f'Error getting checks for {table}')
            logger_setup.get_logger().debug(f'Error: {query_model.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query_model}')
            return False
        # Go through each line in the model and check how many item_ids have this tag
        if query_model.rowCount() == len(item_ids):
            # All items have this tag
            all_items.append(table_id)
        elif query_model.rowCount() > 0:
            # Some items have this tag
            some_items.append(table_id)
    tree_model.blockSignals(True)
    tree_model.check_checkable_tree(QtC.QModelIndex(), all_items, some_items)
    tree_model.blockSignals(False)
    return True

def populate_many_combo_checks(many_to_many_table: str, combo: QtW.QComboBox, first_table_ids: list):
    if first_table_ids == []:
        return
    logger_setup.get_logger().info(f"Populating checks for {many_to_many_table}")
    start_populate_checks_time = time.time()
    many_to_many_model = QtS.QSqlTableModel()
    many_to_many_model.setTable(many_to_many_table)
    many_to_many_model.select()
    first_table = many_to_many_table.split('_')[0]
    first_table_id_header = get_headers(first_table)[0]
    all_items = []
    some_items = []
    text = ""

    if isinstance(combo, CheckableTreeCombobox):
        model, indexes = find_tree_model(combo.model(), None)
        col = 0  # Name column is always placed in the first column
        tag_id_header = model.source_model.record().fieldName(0)
        id_col = 1  # ID column is always placed in the second column
    else:
        model = combo.model()
        col = get_name_column(model.tableName())
        tag_id_header = model.record().fieldName(0)
        id_col = 0  # ID column is always in the first column
    if len(first_table_ids) == 0:
        logger_setup.get_logger().info("No items selected, so unchecking everything")
        if isinstance(combo, CheckableTreeCombobox):
            model.blockSignals(True)

            # recursively uncheck everything
            def uncheck_all(model: CheckableTreeModel, index: QtC.QModelIndex):
                for row in range(model.rowCount(index)):
                    model_index = model.index(row, col, index)
                    model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    uncheck_all(model, model_index)

            uncheck_all(model, QtC.QModelIndex())
            model.blockSignals(False)
        else:
            for row in range(model.rowCount()):
                model_index = model.index(row, col)
                model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                if model.lastError().text():
                    logger_setup.get_logger().critical(f"Error setting unchecked for {model.tableName()}")
                    logger_setup.get_logger().debug(f"Error: {model.lastError().text()}")
        logger_setup.get_logger().info("Unchecked everything")
        combo.setCurrentText(text)
    else:
        logger_setup.get_logger().info(f"Checking {many_to_many_table}")
        if isinstance(combo, CheckableTreeCombobox):
            model.blockSignals(True)

            # recursively check data
            def check_data(model: CheckableTreeModel, index: QtC.QModelIndex):
                for row in range(model.rowCount(index)):
                    model_index = model.index(row, col, index)
                    id_index = model.index(row, id_col, index)
                    tag_id = model.data(id_index, QtC.Qt.ItemDataRole.DisplayRole)
                    if len(first_table_ids) > 1:
                        many_to_many_model.setFilter(
                            f"{first_table_id_header} in {tuple(first_table_ids)} AND {tag_id_header} = {tag_id}")
                    else:
                        many_to_many_model.setFilter(
                            f"{first_table_id_header} = {first_table_ids[0]} AND {tag_id_header} = {tag_id}")
                    if many_to_many_model.rowCount() == len(first_table_ids):
                        # All items have this tag
                        model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                        all_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                    elif many_to_many_model.rowCount() > 0:
                        # Some items have this tag
                        model.setData(model_index, QtC.Qt.CheckState.PartiallyChecked,
                                      QtC.Qt.ItemDataRole.CheckStateRole)
                        some_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                    else:
                        # No items have this tag
                        model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    check_data(model, model_index)

            check_data(model, QtC.QModelIndex())
        else:
            for row in range(model.rowCount()):
                tag_id = model.index(row, id_col).data()
                if len(first_table_ids) > 1:
                    many_to_many_model.setFilter(
                        f"{first_table_id_header} in {tuple(first_table_ids)} AND {tag_id_header} = {tag_id}")
                else:
                    many_to_many_model.setFilter(
                        f"{first_table_id_header} = {first_table_ids[0]} AND {tag_id_header} = {tag_id}")
                model_index = model.index(row, col)
                if many_to_many_model.rowCount() == len(first_table_ids):
                    # All items have this tag
                    model.setData(model_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if model.lastError().text():
                        logger_setup.get_logger().critical(
                            f"Error setting checked for {model.tableName()}")
                        logger_setup.get_logger().debug(f"Error: {model.lastError().text()}")
                    all_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                elif many_to_many_model.rowCount() > 0:
                    # Some items have this tag
                    model.setData(model_index, QtC.Qt.CheckState.PartiallyChecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if model.lastError().text():
                        logger_setup.get_logger().critical(
                            f"Error setting partial checked for {model.tableName()}")
                        logger_setup.get_logger().debug(f"Error: {model.lastError().text()}")
                    some_items.append(model.data(model_index, QtC.Qt.ItemDataRole.DisplayRole))
                else:
                    # No items have this tag
                    model.setData(model_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                    if model.lastError().text():
                        logger_setup.get_logger().critical(
                            f"Error setting unchecked for {model.tableName()}")
                        logger_setup.get_logger().debug(f"Error: {model.lastError().text()}")
    if not all_items and not some_items:
        # No items have these tags
        text = ""
    elif not some_items:
        # All items have the same tags
        text = ', '.join(all_items)
    else:
        # items have different tags
        text = "-"
    if isinstance(combo, CheckableTreeCombobox):
        model.blockSignals(False)
        combo.treeView.connect_edited_signal()
    if not text:
        text = combo.placeholderText()
    combo.setCurrentText(text)
    end_populate_checks_time = time.time()
    logger_setup.get_logger().info(
        f"Populated checks for {many_to_many_table} in {end_populate_checks_time - start_populate_checks_time} seconds")
    logger_setup.get_logger().info(f"Populated checks for {many_to_many_table}")

def get_readable_header(header: str):
    header = TxM.remove_spaces(header)
    if 'ID' in header or 'Abbreviation' in header:
        if 'Elev' in header:
            header = 'Elevation Unit'
        elif 'AgeUnit' in header:
            header = 'Age Unit'
        elif 'RatioErrorFormat' in header:
            header = 'Ratio Error Format'
        elif 'AgeErrorFormat' in header:
            header = 'Age Error Format'
        elif 'Height' in header:
            header = 'Height/Depth Unit'
        elif 'GPSFormat' in header:
            header = 'GPS Format'
        elif 'SpotSize' in header:
            header = 'Spot Size Unit'
        elif 'ConcordanceFormat' in header:
            header = 'Concordance Format'
    if 'GPSLocationConverted' in header:
        header = 'Converted GPS Location'
    elif 'GPSLocationDisplay' in header:
        header = 'GPS Location'
    elif 'SampleElevationCalculated' in header:
        header = f'Calculated Sample Elevation ({settings.value('elevation_unit_abbreviation')})'
    elif 'SampleElevation' in header:
        header = f'Sample Elevation'
    elif 'ColumnElevationCalculated' in header:
        header = f'Calculated Column Elevation ({settings.value('elevation_unit_abbreviation')})'
    elif 'ColumnElevation' in header:
        header = f'Column Elevation'
    elif 'TotalHeightDepthCalculated' in header:
        header = f'Calculated Total Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
    elif 'TotalHeightDepth' in header:
        header = f'Total Height/Depth'
    elif 'HeightDepthCalculated' in header:
        header = f'Calculated Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
    elif 'HeightDepth' in header:
        header = f'Height/Depth'
    elif 'AgeCalculated' in header:
        header = f'Calculated Age ({settings.value('age_unit_abbreviation')})'
    elif 'CalculatedSpotSize' in header:
        header = f'Calculated Spot Size ({settings.value('spotsize_unit_abbreviation')})'
    elif 'CalculatedConcordance' in header:
        header = f'Calculated Concordance ({settings.value('concordance_format_abbreviation')})'
    elif 'AgeError' in header:
        header += f' ({settings.value("age_error_format_abbreviation")})'
    elif 'Age' in header and not any(s in header for s in ['Name', 'Reference', 'Unit', 'Format']):
        header += f' ({settings.value("age_unit_abbreviation")})'
    elif 'Error' in header:
        if 'Corr/Rho' in header:
            header += f' ({settings.value("ratio_error_format_abbreviation")})'
        else:
            header = header.replace('Error', f' Error ({settings.value("ratio_error_format_abbreviation")})')
    if 'Name' in header and header not in ('SampleName', 'Sample Name', 'AliquotName', 'Aliquot Name', 'SpotName', 'Spot Name'):
        header = header.replace('Name', '')
        if header.endswith('y'):
            header = header[:-1] + 'ies'
        elif header.endswith('is'):
            header = header[:-2] + 'es'
        else:
            header += 's'
    if 'Display' in header:
        header = header.replace('Display', '')
    if 'Calculated' in header:
        header = header.replace('Calculated', 'Converted ')
    if 'ppm' in header:
        header = header.replace('ppm', '(ppm)')
    if 'cps' in header:
        header = header.replace('cps', '(cps)')
    if '"' in header:
        header = header.replace('"', '')
    header = TxM.add_spaces_camel(header)
    if 'U Pb' in header:
        header = header.replace('U Pb', 'U-Pb')
    return header



def show_loading_dialog(title, message, cancel_callback=None):
    """
    Show a loading dialog while the action is taking places
    :return:
    """
    # Wait one second before showing the loading dialog
    timer = QtC.QTimer()
    timer.start(1000)
    LoadingDialogManager.show_loading_dialog(message, title, cancel_callback)

def close_loading_dialog(title, message):
    """
    Close the loading dialog
    :return:
    """
    LoadingDialogManager.close_loading_dialog(title, message)


# ---------------------------
#    Database Methods
# ---------------------------

def update_other_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, update_table: str, update_ids: list):
    """
    Take the checked ids from a table and update that field in another table. The relationship must be one-to-one or
    one-to-many, so the checked ids should be complete. If the relationship is many-to-many, use update_many_table_with_checks.
    :param table: table with checked data
    :param checked_ids: ids of checked items in the table
    :param partially_checked_ids: ids of partially checked items in the table
    :param update_table: table to update
    :param update_ids: ids to update in the update table
    :return: True if successful or not needed, False if not
    """
    if not update_ids:
        logger_setup.get_logger().error(f'No item IDs given for {update_table}')
        return False
    if partially_checked_ids:
        # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
        logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
        return True
    if not checked_ids:
        logger_setup.get_logger().info(f'No checked items to update.')
        return True
    id_header = get_headers(table)[0]
    other_id_header = get_headers(update_table)[0]
    current_ids = []
    query = QtS.QSqlQuery()
    if len(update_ids) > 1:
        query_where_str = f'in {tuple(update_ids)}'
    else:
        query_where_str = f'= {update_ids[0]}'
    query.prepare(f"SELECT {id_header} FROM {update_table} WHERE {other_id_header} {query_where_str}")
    if not query.exec():
        logger_setup.get_logger().critical(
            f'Failed to get items from {update_table}')
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return False
    while query.next():
        current_id = query.value(0)
        if current_id not in current_ids:
            current_ids.append(current_id)
    if current_ids == checked_ids:
        logger_setup.get_logger().info(f'Checks are up to date')
        return True
    create_savepoint('update_other_table')
    if len(checked_ids) == 1:
        if not query.exec(f'UPDATE {update_table} SET {id_header} = {checked_ids[0]} WHERE {other_id_header} {query_where_str}'):
            logger_setup.get_logger().critical(f'Failed to add item to {update_table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('update_other_table')
            return False
        logger_setup.get_logger().info(f'Added {id_header} {checked_ids[0]} to {update_table}')
        release_savepoint('update_other_table')
        return True
    else:
        logger_setup.get_logger().critical(f'Too many checks for {update_table}')

def update_many_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, many_table: str, first_table_ids: list):
    """
        Take the checked ids from a table and update that field in the second column of a many-to-many table with another table.
        The relationship must be many-to-many, so the checked ids may be partial.
        :param table: table with checked data
        :param checked_ids: ids of checked items in the table
        :param partially_checked_ids: ids of partially checked items in the table
        :param many_table: first table in the manny-to-many table to update
        :param first_table_ids: ids to update in the first table
    """
    first_table = many_table.split('_')[0]
    second_table = many_table.split('_')[1]
    first_table_id_header = get_headers(first_table)[0]
    second_table_id_header = get_headers(table)[0]
    query_model = QtS.QSqlQueryModel()
    query = QtS.QSqlQuery()
    if len(first_table_ids) > 1:
        query_where_str = f'in {tuple(first_table_ids)}'
    elif len(first_table_ids) == 1:
        query_where_str = f'= {first_table_ids[0]}'
    else:
        logger_setup.get_logger().error(f'No item IDs given for {first_table}')
        return False
    query_model.setQuery(
        f'SELECT {second_table_id_header} FROM {many_table} WHERE {first_table_id_header} {query_where_str}')
    current_ids = []
    for row in range(query_model.rowCount()):
        current_id = query_model.data(query_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if current_id not in current_ids:
            current_ids.append(current_id)
    model_query = f"SELECT {second_table_id_header} FROM {second_table}"
    query_model.setQuery(model_query)
    if query_model.lastError().isValid():
        logger_setup.get_logger().critical(
            f'Error getting {table} checks for {first_table}')
        logger_setup.get_logger().debug(f'Error: {query_model.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {model_query}')
        return False
    create_savepoint('update_many_table')
    to_remove = []
    to_add = []
    for row in range(query_model.rowCount()):
        second_table_id = query_model.data(query_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if second_table_id in checked_ids and second_table_id not in current_ids:
            to_add.append(second_table_id)
        elif second_table_id in partially_checked_ids:
            pass
        elif second_table_id not in checked_ids and second_table_id in current_ids:
            to_remove.append(second_table_id)
    for id in to_remove:
        if id in current_ids:
            query.prepare(
                f"DELETE FROM {many_table} WHERE {first_table_id_header} {query_where_str} AND {second_table_id_header} = {id}")
            if not query.exec():
                logger_setup.get_logger().critical(
                    f"Error unchecking {second_table} from {first_table}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('update_many_table')
                return False
    logger_setup.get_logger().info(f"Removed {to_remove} associated with item IDs {first_table_ids} from {many_table}")
    for id in to_add:
        query.prepare(
            f"INSERT INTO {many_table}({first_table_id_header}, {second_table_id_header}) VALUES(?, ?)")
        for item_id in first_table_ids:
            query.addBindValue(item_id)
            query.addBindValue(id)
            if not query.exec():
                # If it is a unique constraint fail, just continue
                if 'UNIQUE constraint failed' in query.lastError().text():
                    pass
                # If it is another type of error, log it and rollback
                else:
                    logger_setup.get_logger().critical(
                        f"Error adding {second_table} to {first_table}")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                    logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
                    rollback_savepoint('update_many_table')
                    return False
    logger_setup.get_logger().info(f"Added {to_add} associated with item IDs {first_table_ids} to {many_table}")
    logger_setup.get_logger().info(
        f"Successfully updated {many_table} for {first_table_id_header} {first_table_ids}")
    release_savepoint('update_many_table')
    return True