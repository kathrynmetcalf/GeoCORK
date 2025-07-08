import re
import sqlite3
import time
import typing
from collections import namedtuple
from datetime import datetime, timezone
from multiprocessing.process import parent_process

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from numpy import integer
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import QMetaType, QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PyQt6.QtGui import QTextOption, QAction, QFont, QBrush, QColor
from PyQt6.QtSql import QSqlTableModel, QSqlQueryModel, QSqlQuery, QSqlDatabase
from PyQt6.QtWidgets import QGroupBox, QStyledItemDelegate, QProgressDialog, QToolTip, QCompleter

import Functions.Text_manipulations as TxM
import logger_setup
from Functions import SQLUtils
from Functions.Check_triggers import update_modified_timestamp, validate_update
from Functions.LoadingDialog_manager import LoadingDialogManager
from Functions.Database_views import ViewQuery
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings


# ---------------------------
#    Delegate Classes
# ---------------------------

class FontDelegate(QtW.QStyledItemDelegate):
    """
    Custom delegate to display text with a custom font.
    """
    def initStyleOption(self, option, index):
        """Initializes the options of the delegate"""
        super().initStyleOption(option, index)
        font = index.data(QtC.Qt.ItemDataRole.FontRole)
        if font:
            option.font = font

class WordWrapDelegate(QtW.QStyledItemDelegate):
    """
    Custom delegate to enable word wrap in QTableView.
    """
    def initStyleOption(self, option, index):
        """Initializes the options of the delegate"""
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
    with abnormally long query execution time. Only committed data is displayed, uncommitted changes are not visible to
    this connection, so the model must be updated manually while savepoints or other transactions are active.
    """
    def __init__(self, query: str = '', database=None, view_query: ViewQuery = None):
        from Functions.Settings_manager import SettingsManager
        settings = SettingsManager().settings
        db_settings = SettingsManager().db_settings

        super().__init__()
        self._data = []
        self._headers = []
        self.edited_indexes = []
        self.last_error = None
        self.query_text = query
        self.database = database if database is not None else settings.value('db_file', type=str)
        self.view_query = view_query
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = ''
        self.order_col: str = ''

        self.table = None
        self.table_name_col = None

        self.load_data(self.query_text, self.database)

    def setQuery(self, new_query: str, view_query: ViewQuery = None):
        """
        Updates the model with a new query.
        :param new_query: New query string to apply.
        :param view_query: ViewQuery object to apply, if any. Contains additional query information if necessary
        """
        set_time = time.time()
        self.view_query = view_query
        self.load_data(new_query, self.database)
        logger_setup.get_logger().info(f'Set new query in {time.time() - set_time} seconds')

    def update_database(self, new_database: str, view_query: ViewQuery = None):
        """
        Updates the model with a new database.
        :param new_database: New database filename string to apply.
        """
        self.load_data(self.query_text, new_database)

    def load_data(self, query: str, database: str):
        """
        Loads data from the given query and database.
        :param query: Query to load.
        :param database: Database to load from.
        """
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
                logger_setup.get_logger().info('Populating model with query')
                logger_setup.get_logger().debug(f'SQL query: {query}')
                start_time = time.time()
                if self.view_query:
                    # If a ViewQuery is provided, see if there are any temporary tables to create
                    where_ids = self.view_query.where_ids
                    create_temp_id = self.view_query.create_temp_id
                    create_temp_paged = self.view_query.create_temp_paged
                    if create_temp_id and where_ids:
                        cursor.execute(create_temp_id)
                        id_header = create_temp_id.split('TempIDs (')[1].split(' ')[0].strip()
                        cursor.execute(f'INSERT INTO TempIds ({id_header}) VALUES {", ".join(f"({item_id})" for item_id in where_ids)}')
                    if create_temp_paged:
                        cursor.execute(create_temp_paged)
                elif 'TempIds' in query or 'TempPaged' in query:
                    # If the query contains temporary tables, without a ViewQuery, we do not have enough information.
                    logger_setup.get_logger().critical(f'Error loading data from query')
                    logger_setup.get_logger().debug(f'Query includes temporary tables, but no ViewQuery provided.')
                    logger_setup.get_logger().debug(f'SQL query: {query}')
                cursor.execute(query)
                self._data = cursor.fetchall()
                self._headers = [desc[0] for desc in cursor.description]
                logger_setup.get_logger().debug(f"Model populated in {time.time() - start_time} seconds")
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f"Error opening database and executing query")
            logger_setup.get_logger().debug(f"Error: {e}")
            logger_setup.get_logger().debug(f"SQL query: {query}")
            self.last_error = e

        # Get the table name from the query
        if 'table_info' in query:
            self.set_table('table_info')
        elif 'WITH ' in query:
            # The query is too complex to determine the table name directly
            self.set_table(None)
        else:
            self.set_table(query.split('FROM ')[1].split(' ')[0].strip())
        self.endResetModel()

    def set_table(self, new_table: str | None):
        """
        Updates the model with a new table.
        :param new_table: New table name to apply.
        """
        self.table = new_table
        if self.table:
            self.table_name_col = get_name_column(get_view_from_table(self.table))
        else:
            self.table_name_col = None

    def rowCount(self, parent=None):
        """
        Returns the row count of the model.
        :param parent:
        :return:
        """
        return len(self._data)

    def columnCount(self, parent=None):
        """
        Returns the row count of the model.
        :param parent:
        :return:
        """
        return len(self._headers)

    def tableName(self):
        """
        Return the table name for the model.
        :return: table name the query is selecting from or the view is pulling from as string, None if not exists
        """
        return self.table

    class MockRecord:
        """
        Class to mimic QSqlRecord for the SQLiteTableModel.
        Stores a row of data from the SQLite database table and provides methods to access the data.
        """

        def __init__(self, row):
            self.row = row

        def value(self, index):
            """
            Mimics QSqlRecord.value()
            :param index: index of the value to get
            :return: value at the given index in the row
            """
            return self.row[index]

        def setValue(self, index: int, value) -> bool:
            """
            Mimics QSqlRecord.setValue()
            :param index: index of the value to set
            :param value: new value to set
            :return: True if the value was set, False if the index is out of range
            """
            if 0 <= index < len(self.row):
                # Convert tuple to list to allow item assignment, then convert back to tuple
                row = list(self.row)
                row[index] = value
                self.row = tuple(row)
                return True
            return False

        def count(self):
            """Mimics QSqlRecord.count()"""
            return len(self.row)

    def record(self, row: int):
        """
        Returns a MockRecord containing the same attributes as a QSqlRecord. Used so SQLiteTableModels can be used
         interchangeably with QSqlTableModel.
        :param row:
        :return:
        """

        if 0 <= row < len(self._data):
            return self.MockRecord(self._data[row])
        else:
            return None  # or raise IndexError

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Return the data for the given index and role.
        :param index: table index
        :param role: expecting DisplayRole
        :return: data stored in the model at the given index or None if the index is invalid or role is not DisplayRole
        """
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
        """
        Return column headers.
        :param section: column index
        :param orientation: orientation of the header (horizontal or vertical)
        :param role: expecting DisplayRole
        """
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]  # Ensure headers are stored properly
        return super().headerData(section, orientation, role)

    def setHeaderData(self, section, orientation, value, role=Qt.ItemDataRole.EditRole):
        """
        Allow renaming of column headers.
        :param section: column index
        :param orientation: orientation of the header (horizontal or vertical)
        :param value: new header value
        """
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.EditRole:
            self._headers[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return super().setHeaderData(section, orientation, value, role)

    def setData(self, index, value, role = ...) -> bool | None:
        """
        Set the data to value for the given index and role. SQLiteTableModel cannot see uncommitted changes, so model
        must be manually updated as changes occur before commiting.
        :param index: table index
        :param value: new data
        :param role: expecting EditRole to edit data
        :return: True or False or None
        """
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
        new_data = self._data.copy()  # Create a copy of the data to avoid modifying while iterating
        for row in self._data:
            # The first column is assumed to be the primary key
            if row[0] in ids_to_remove:
                new_data.remove(row)
        self._data = new_data
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


class DisplayRoundedModel(QtS.QSqlTableModel):
    """
    Custom QSqlTableModel to display the data of a SQLite database table with rounded values.
    This model was created to display the data in a more user-friendly way, such as rounding.
    """
    def __init__(self, db=QSqlDatabase()):
        super().__init__(db=db)

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        """
        Return the data for the given index and role.
        :param index: table index
        :param role: expecting DisplayRole
        :return: False if index is invalid, otherwise return the user-readable data stored in the model at the given index
        """
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
        """
        Return the raw data for the given index and role.
        :param index: table index
        :param role: any
        :return: same as super().data(index, role)
        """
        return super().data(index, role)

class DisplayRoundedQueryModel(QSqlQueryModel):
    """
    Custom QSqlQueryModel to display the data of a SQLite database table with rounded values.
    This model was created to display the data in a more user-friendly way, such as rounding.
    """
    def __init__(self, db=QSqlDatabase()):
        super().__init__()
        self.table = ''
        self.table_name_col = ''
        self.db = db
        self.query = ''
        self.rounded = True

    def setQuery(self, query: str):
        """
        Set the query for the model. Also sets the table name, view name, name column in the table, and name column in
        the view based on the query.
        :param query: SQLite query as text string
        :return:
        """
        super().setQuery(query, self.db)
        if self.lastError().text():
            logger_setup.get_logger().critical(f"Error displaying table")
            logger_setup.get_logger().debug(f"Failed to set query: {self.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query}")
        else:
            self.query = query
            if 'table_info' in query:
                self.set_table('table_info')
            elif 'WITH ' in query:
                # The query is too complex to determine the table name directly
                self.set_table(None)
            else:
                self.set_table(query.split('FROM ')[1].split(' ')[0].strip())

    def set_table(self, new_table: str | None):
        """
        Updates the model with a new table.
        :param new_table: New table name to apply.
        """
        self.table = new_table
        if self.table:
            if 'JOIN' in self.query or 'ReferenceDisplay' in self.query:
                # Most likely a view query
                self.table_name_col = get_name_column(get_view_from_table(self.table))
            else:
                self.table_name_col = get_name_column(self.table)
        else:
            self.table_name_col = None

    def tableName(self) -> str:
        """
        Return the table name for the model.
        :return: string with table name or ''
        """
        return self.table

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = QtC.Qt.ItemDataRole.DisplayRole):
        """
        Return the data for the given index and role.
        :param index: table index
        :param role: expects DisplayRole
        :return: value if valid index given, False if not
        """
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

class EditableSqlQueryModel(DisplayRoundedQueryModel):
    """Custom DisplayRoundedQueryModel (subclass of QSqlQueryModel) with editable name column and description column.
    Updates the database likee QSqlTablModel does."""
    def __init__(self):
        super().__init__()
        self.query = ''

    def flags(self, index):
        """Sets only the name column and description column as editable"""
        flags = super().flags(index)
        col = get_name_column(self.table)
        if index.column() == col or 'Description' in self.headerData(index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole):
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable
        return flags

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
        id = self.data(self.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if not id:
            logger_setup.get_logger().warning(f'No ID found for row {row} in {self.table}')
            return False
        if not delete_data(self.table, [id]):
            return False
        logger_setup.get_logger().info(f'Successfully deleted {id} from {self.table}')
        return True

class ReadableProxyModel(QtC.QSortFilterProxyModel):
    """
    Displays readable headers for any table. Uses get_readable_header to convert header text.
    Setting original_headers to True returns unmodified headers.
    Sorting takes into account mixed text and numeric data in strings so that A14 is considered less than A104.
    If doi column is present, returns more readable text and creates a tool tip for each entry.
    """
    def __init__(self, view=False):
        super().__init__()
        self.original_headers = False
        self.doi_column_exists = False
        self.doi_column = None
        self.doi_regex = re.compile(r"^(10\.\d{4,9}\/[-._;()\/:A-Z0-9]+)$", re.IGNORECASE)

    def setSourceModel(self, sourceModel):
        super().setSourceModel(sourceModel)
        self.doi_column_exists = False
        self.doi_column = None
        self._check_doi_column()

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: QtC.Qt.ItemDataRole = ...):
        if self.original_headers:
            super().headerData(section, orientation, role)
        if role == QtC.Qt.ItemDataRole.DisplayRole and orientation == QtC.Qt.Orientation.Horizontal:
            header = super().headerData(section, orientation, role)
            if '_' in header:
                return header
            readable_header = get_readable_header(header)
            return readable_header
        super().headerData(section, orientation, role)

    def _check_doi_column(self):
        """Checks if a doi column exists in the table and sets the boolean to True."""
        model = self.sourceModel()
        if not model:
            return

        # For QSqlTableModel or QAbstractItemModel
        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            if str(header).strip().lower() == "doi":
                self.doi_column = col
                self.doi_column_exists = True
                break

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Method to modify data in the table. Currently modifies a doi column's display roles to show invalid/valid dois
        and adds colors, tooltips, and hyperlinking. Currently implemented roles are ForegroundRole, FontRole,
        and ToolTipRole.
        :param index: QModelIndex of the record
        :param role: ItemDataRole to pass in
        :return: The modified data and role for the record
        """
        if not index.isValid():
            return super().data(index, role)

        if role not in (Qt.ItemDataRole.ForegroundRole, Qt.ItemDataRole.FontRole, Qt.ItemDataRole.ToolTipRole):
            return super().data(index, role)

        # Handle tooltip for DOI column
        if self.doi_column_exists and index.column() == self.doi_column:
            source_index = self.mapToSource(index)
            text = self.sourceModel().data(source_index, Qt.ItemDataRole.DisplayRole)
            if isinstance(text, str):
                if text.startswith('doi:'):
                    text = text.replace('doi:', '')
                if re.match(self.doi_regex, text):
                    if role == Qt.ItemDataRole.ForegroundRole:
                        return QBrush(QColor("blue"))
                    elif role == Qt.ItemDataRole.FontRole:
                        font = QFont()
                        font.setUnderline(True)
                        return font
                    elif role == Qt.ItemDataRole.ToolTipRole:
                        return "Valid DOI format, double click to open in browser"
                else:
                    if role == Qt.ItemDataRole.ForegroundRole:
                        return QBrush(QColor("red"))
                    elif role == Qt.ItemDataRole.FontRole:
                        font = QFont()
                        font.setStrikeOut(True)
                        return font
                    elif role == Qt.ItemDataRole.ToolTipRole:
                        return "Invalid DOI format, consider using '10.XXXX/XXXXXX'"

        # Default return for all other roles
        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
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
        elif isinstance(left_data, (int, float)) and isinstance(right_data, (int, float)):
            return left_data < right_data
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
    """
    Custom DisplayRoundedModel (subclass of QSqlTableModel) with check boxes enabled for each row.
    Name column has a tool tip with the description if available
    Supports partial checks through code, but any user input only toggles checked or unchecked.
    Stores lists of checked_ids and partially_checked_ids.
    """
    def __init__(self):
        super().__init__()
        self.primary_key_column = 0
        self.checked_ids = []
        self.partially_checked_ids = []

    def flags(self, index):
        """Set check boxes on the name column only"""
        flags = super().flags(index)
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = get_name_column(get_view_from_table(self.tableName()))
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
        col = get_name_column(get_view_from_table(self.tableName()))
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

    def check_ids_from_list(self, id_list: list, state: QtC.Qt.CheckState = QtC.Qt.CheckState.Checked):
        """
        Check or partially check rows based on a given list of primary key values.
        :param id_list: list of primary key values to mark as checked or partially checked
        :param state: Qt.CheckState.Checked or Qt.CheckState.PartiallyChecked
        """
        for row in range(self.rowCount()):
            record_id = self.index(row, self.primary_key_column).data(QtC.Qt.ItemDataRole.DisplayRole)
            index = self.index(row, get_name_column(get_view_from_table(self.tableName())))
            if record_id in id_list:
                self.setData(index, state, QtC.Qt.ItemDataRole.CheckStateRole)
        self.checked_ids = id_list

    def return_checked_ids(self):
        """Returns a list of checked_ids and a list of partially_checked_ids"""
        return self.checked_ids, self.partially_checked_ids

    def clear_checks(self):
        """
        Clears all checked and partially checked states from the model
        and refreshes the corresponding data in the view.
        """
        name_col = get_name_column(get_view_from_table(self.tableName()))

        for row in range(self.rowCount()):
            index = self.index(row, name_col)
            self.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        if self.checked_ids or self.partially_checked_ids:
            logger_setup.get_logger().critical(f'Error resetting {self.tableName()} checks')
            logger_setup.get_logger().debug(
                f'After clear_checks, {self.tableName()} checkable model still has checked_ids ({self.checked_ids}) and partially_checked_ids ({self.partially_checked_ids})')

    def update_other_table(self, other_table: str, other_ids: list):
        """
        Collect the checked IDs and partially checked IDs from this table and update that field in another table.
        It calls the update_other_table_with_checks function to perform the update operation. This is useful for one-to-many
        relationships, such as updating the ColumnID in the Samples table with the checked ID in the Columns table.
        The relationship must be one-to-one or one-to-many, so there should be only one checked ID. If there are partially
        checked IDs, no item has been selected to associate with all IDs in the other table, so do not update. If the
        relationship is many-to-many, use update_many_table instead.
        :param other_table: name of the other table to update with the checked IDs from this table (e.g. Samples)
        :param other_ids: list of IDs in the other table that correspond to the checked items in this tree model
        (e.g. list of SampleIDs)
        :return: True if the update was successful, False otherwise
        """
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return False
        if self.partially_checked_ids:
            # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
            logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
            return True
        if len(self.checked_ids) > 1:
            # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
            logger_setup.get_logger().error(
                f'Multiple checked IDs given for {self.tableName()}. Select only one ID to update {other_table}.')
            logger_setup.get_logger().debug(
                f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
            return False
        if update_other_table_with_checks(self.tableName(), self.checked_ids, self.partially_checked_ids, other_table, other_ids):
            return True
        else:
            return False

    def update_many_table(self, many_table: str, item_ids: list):
        """
        Updates many-to-many relationship with another table. This method is useful when editing joined views, like
        editing the Units associated with Samples.
        :param many_table: name of the many-to-many table to update (e.g. Samples_Units)
        :param item_ids: list of foreign IDs to update in the many-to-many table (e.g. SampleIDs)
        """
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return False
        if update_many_table_with_checks(self.tableName(), self.checked_ids, self.partially_checked_ids, many_table, item_ids):
            return True
        else:
            return False


class CheckableSqlQueryModel(DisplayRoundedQueryModel):
    """
    Custom DisplayRoundedQueryModel (subclass of QSqlQueryModel) with check boxes enabled for each row.
    Name column has a tool tip with the description if available
    Supports partial checks through code, but any user input only toggles checked or unchecked.
    Stores lists of checked_ids and partially_checked_ids.
    """
    def __init__(self):
        super().__init__()
        self.checked_ids = []
        self.partially_checked_ids = []
        self.primary_key_column = 0

    def flags(self, index):
        """Set check boxes on the name column only"""
        flags = super().flags(index)
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col:
            flags |= QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = get_name_column(get_view_from_table(self.tableName()))
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
        col = get_name_column(get_view_from_table(self.tableName()))

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

    def check_ids_from_list(self, id_list: list, state: QtC.Qt.CheckState = QtC.Qt.CheckState.Checked):
        """
        Check or partially check rows based on a given list of primary key values.
        :param id_list: list of primary key values to mark as checked or partially checked
        :param state: Qt.CheckState.Checked or Qt.CheckState.PartiallyChecked
        """
        for row in range(self.rowCount()):
            record_id = self.index(row, self.primary_key_column).data(QtC.Qt.ItemDataRole.DisplayRole)
            index = self.index(row, get_name_column(get_view_from_table(self.tableName())))
            if record_id in id_list:
                self.setData(index, state, QtC.Qt.ItemDataRole.CheckStateRole)
        self.checked_ids = id_list

    def return_checked_ids(self):
        """Returns a list of checked_ids and a list of partially_checked_ids"""
        return self.checked_ids, self.partially_checked_ids

    def clear_checks(self):
        """
        Clears all checked and partially checked states from the model
        and refreshes the corresponding data in the view.
        """
        name_col = get_name_column(get_view_from_table(self.tableName()))

        for row in range(self.rowCount()):
            index = self.index(row, name_col)
            self.setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        if self.checked_ids or self.partially_checked_ids:
            logger_setup.get_logger().critical(f'Error resetting {self.tableName()} checks')
            logger_setup.get_logger().debug(
                f'After clear_checks, {self.tableName()} checkable model still has checked_ids ({self.checked_ids}) and partially_checked_ids ({self.partially_checked_ids})')

    def update_other_table(self, other_table: str, other_ids: list):
        """
        Collect the checked IDs and partially checked IDs from this table and update that field in another table.
        It calls the update_other_table_with_checks function to perform the update operation. This is useful for one-to-many
        relationships, such as updating the ColumnID in the Samples table with the checked ID in the Columns table.
        The relationship must be one-to-one or one-to-many, so there should be only one checked ID. If there are partially
        checked IDs, no item has been selected to associate with all IDs in the other table, so do not update. If the
        relationship is many-to-many, use update_many_table instead.
        :param other_table: name of the other table to update with the checked IDs from this table (e.g. Samples)
        :param other_ids: list of IDs in the other table that correspond to the checked items in this tree model
        (e.g. list of SampleIDs)
        :return: True if the update was successful, False otherwise
        """
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return False
        if self.partially_checked_ids:
            # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
            logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
            return True
        if len(self.checked_ids) > 1:
            # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
            logger_setup.get_logger().error(
                f'Multiple checked IDs given for {self.tableName()}. Select only one ID to update {other_table}.')
            logger_setup.get_logger().debug(
                f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
            return False
        if update_other_table_with_checks(self.table, self.checked_ids, self.partially_checked_ids, other_table, other_ids):
            return True
        else:
            return False

    def update_many_table(self, many_table: str, item_ids: list):
        """
        Updates many-to-many relationship with another table. This method is useful when editing joined views, like
        editing the Units associated with Samples.
        :param many_table: name of the many-to-many table to update (e.g. Samples_Units)
        :param item_ids: list of foreign IDs to update in the many-to-many table (e.g. SampleIDs)
        """
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return False
        if update_many_table_with_checks(self.table, self.checked_ids, self.partially_checked_ids, many_table, item_ids):
            return True
        else:
            return False

class SampleAgeTableModel(CheckableSqlQueryModel):
    """
    Custom CheckableSqlQueryModel (subclasses DisplayRoundedQueryModel and QSqlQueryModel).
    Intended to track default ages as bolded rows in the model.
    """
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
        """Age is the default age for a sample and should be marked as bold"""
        row = index.row()
        if row not in self.bolded_rows:
            self.bolded_rows.append(row)
            self.dataChanged.emit(index, index, [QtC.Qt.ItemDataRole.FontRole])

    def make_not_bold(self, index):
        """Age is not a default age for any sample and should be marked as bold"""
        row = index.row()
        if row in self.bolded_rows:
            self.bolded_rows.remove(row)
            self.dataChanged.emit(index, index, [QtC.Qt.ItemDataRole.FontRole])


# ---------------------------
#    Table Methods
# ---------------------------


def get_database_tables() -> list:
    """
    Returns a list of all tables in the database.
    :return: List of table names
    """
    query = QtS.QSqlQuery()
    if not query.exec('SELECT name FROM sqlite_master WHERE type="table"'):
        logger_setup.get_logger().critical("Failed to get database tables")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        return []
    tables = []
    while query.next():
        if query.value(0) not in tables:
            tables.append(query.value(0))
    return tables


def set_table(model: QtS.QSqlTableModel, table: str) -> QtS.QSqlTableModel | bool:
    """
    Convenience method to set the table for a QSqlTableModel and select the data. Notifies if any errors occur.
    :param model: QSqlTableModel to populate
    :param table: Name of the SQL database table to populate the model
    :return: populated model if successful, False if not
    """
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

def get_headers(table: str) -> list:
    """
    Return all headers for the given table
    :param table: Name of the SQL database table
    :return: list of headers if successful, empty list if not
    """
    query = QtS.QSqlQuery()
    if 'View' in table:
        show_columns = settings.value(SQLUtils.view_setting_dict[table])
        return show_columns
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
    """
    Return table columns by type for virtual, stored, and regular columns. Considers everything after the modified
    column to be a virtual column and any column before modified with a header containing 'Display' or 'Calculated'
    to be a stored column.
    :param table: Name of the SQL database table
    :return query: Query used to collect columns
    :return virtual: list of virtual column names
    :return stored: list of stored column names
    :return columns: list of regular column names
    """
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
    """
    Returns the column number for the name column in the table.
    :param table: Name of the SQL database table or view
    :return: Returns the column number starting from 0
    """
    table = table.replace('"', '').strip()
    if (table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees or
            table in ['AliquotView', 'AliquotEditView', 'SpotView', 'SpotEditView']):
        return 3
    elif 'Format' in table or 'Unit' in table:
        # return the column for the abbreviation
        return 2
    elif table == 'References' or table == '"References"':
        return 9
    elif table == 'SampleAges':
        return 16
    elif (table in SQLUtils.user_viewable_tables or
          table in ['SampleView', 'SampleEditView', 'Spots', 'GPSLocations', 'FilterGroups', 'ReferenceView',
                    'ColumnView', 'ColumnEditView']):
        return 1
    elif table == 'UPbAnalyses':
        # Use UPbAnalysisID
        return 0
    elif table == 'UPbView' or table == 'UPbEditView':
        # Use spot name
        return 4
    else:
        return None

def description_column(table: str) -> int | None:
    """
    Returns the index of the column header containing 'Description'.
    :param table: Name of the SQL database table or view
    :return: Returns the column number starting from 0
    """
    headers = get_headers(get_view_from_table(table))
    for header in headers:
        if 'Description' in header:
            return headers.index(header)
    return None

def get_table_from_view(view: str):
    """
    Given a view, returns the table that view is derived from.
    :param view: Name of SQL database view
    :return: Name of SQL database table
    """
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

def get_view_from_table(table: str):
    """
    Given a table name, returns the non-editable view associated with that table.
    :param table: Name of SQL database table
    :return: Name of SQL database view
    """
    if table == 'Samples':
        return 'SampleView'
    elif table == 'Aliquots':
        return 'AliquotView'
    elif table == 'Spots':
        return 'SpotView'
    elif table == 'UPbAnalyses':
        return 'UPbView'
    elif table == 'Columns':
        return 'ColumnView'
    elif table == 'References' or table == '"References"':
        return 'ReferenceView'
    else:
        return table

def get_edit_view_from_table(table: str):
    """
    Given a table name, returns the editable view associated with that table.
    :param table: Name of SQL database table
    :return: Name of SQL database view
    """
    if table == 'Samples':
        return 'SampleView'
    elif table == 'Aliquots':
        return 'AliquotEditView'
    elif table == 'Spots':
        return 'SpotEditView'
    elif table == 'UPbAnalyses':
        return 'UPbEditView'
    elif table == 'Columns':
        return 'ColumnEditView'
    elif table == 'References':
        return 'ReferenceEditView'
    else:
        return table


def columns_as_list_current(query: str, cols: list) -> list | None:
    """
    Returns lists of items in given columns. This method reflects uncommitted changes.
    :param cols: List of column indexes as integers or SQL table column headers
    :param query: SQL query of data for table
    :return: lists of items in each row for given columns
    """
    model = QtS.QSqlQueryModel()
    model.setQuery(query)
    if model.lastError().text():
        logger_setup.get_logger().critical(f"Failed to get columns from query: {query}")
        logger_setup.get_logger().debug(f"Error: {model.lastError().text()}")
        return [None for column in cols]
    columns = []
    for col in cols:
        if isinstance(col, int):
            column = col
        elif isinstance(col, str):
            headers = [model.headerData(i, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole) for i in range(model.columnCount())]
            column = headers.index(col)
        else:
            logger_setup.get_logger().critical(f"Failed to get list in table")
            logger_setup.get_logger().debug(f"Invalid column: {col}")
            logger_setup.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        if column < 0 or column >= model.columnCount():
            logger_setup.get_logger().critical(f"Failed to get list in table")
            logger_setup.get_logger().debug(f"Column index {column} out of range for model with {model.columnCount()} columns")
            logger_setup.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        columns.append(column)
    column_lists = []
    for column in columns:
        # Collect unique values from the column
        column_list = list(set(model.index(row, column).data(QtC.Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())))
        column_lists.append(column_list)
    return column_lists

def columns_as_list(query: str, cols: list, view_query: ViewQuery=None) -> list | None:
    """
    Returns lists of items in given columns. This method reflects only committed changes.
    :param cols: List of column indexes as integers or SQL table column headers
    :param query: SQL query of data for table
    :param view_query: ViewQuery object to use for the query, if applicable
    :return: lists of items in each row for given columns
    """
    model = SQLiteTableModel(query, view_query=view_query)
    if model.last_error:
        return None
    columns = []
    for col in cols:
        if isinstance(col, int):
            column = col
        elif isinstance(col, str):
            headers = [model.headerData(i, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole) for i in
                       range(model.columnCount())]
            column = headers.index(col)
        else:
            logger_setup.get_logger().critical(f"Failed to get list in table")
            logger_setup.get_logger().debug(f"Invalid column: {col}")
            logger_setup.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        if column < 0 or column >= model.columnCount():
            logger_setup.get_logger().critical(f"Failed to get list in table")
            logger_setup.get_logger().debug(
                f"Column index {column} out of range for model with {model.columnCount()} columns")
            logger_setup.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        columns.append(column)
    column_lists = []
    for column in columns:
        # Collect unique values from the column
        column_list = list(set(model.index(row, column).data(QtC.Qt.ItemDataRole.DisplayRole) for row in
                       range(model.rowCount())))
        column_lists.append(column_list)
    return column_lists

def get_name_from_id(table: str, item_id: int):
    """
    Returns the name for a given ID record in a table. Queries the database and returns the associated value with the name column.
     Gathers the id column from the table headers and assumes the id column is the first column.
    :param table: Name of the table to query (e.g. RockTypes)
    :param item_id: ID to retrieve the name from (e.g. RockTypeID)
    :return: Name (e.g. RockTypeName)
    """
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    if table == '"References"':
        table = 'References'
    if table != 'UPbAnalyses':
        sql_query = f'SELECT {headers[get_name_column(table)]} FROM "{table}" WHERE {headers[0]}={item_id}'
    else:
        # For UPbAnalyses, we need to use the SpotName column
        sql_query = f'''SELECT SpotName FROM UPbAnalyses
                        JOIN Spots ON UPbAnalyses.SpotID=Spots.SpotID
                        WHERE UPbAnalysisID={item_id}'''
    # logger_setup.get_logger().debug(f'SQL command: {sql_query}')
    if not query.exec(sql_query):
        logger_setup.get_logger().critical(f"Failed to get name for {item_id} in {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return None
    query.next()
    return query.value(0)

def get_id_from_name(table: str, name: str) -> int:
    """
    Returns the primary id for a given name record in a table. Queries the database and returns the first column which
    should always be the id column. Gathers the name column from the table headers.
    :param table: Name of the table to query (e.g. RockTypes)
    :param name: Name to retrieve the ID from (e.g. Sandstone, Granite, etc.)
    :return: ID (e.g. RockTypeID)
    """
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    if table in ['"References"', 'References']:
        # Need to use the ViewQuery to access the generated display column
        show_cols = settings.value('reference_view_columns')
        name_column = get_name_column(get_view_from_table(table))
        name_header = show_cols[name_column]
        query_args = {'show_columns': show_cols, 'where': f'WHERE {show_cols[name_column]}=:name COLLATE NOCASE',
                      'group_col': f'{show_cols[0]}', 'order_col': f'{name_header}'}
        view_query = ViewQuery('References', False, **query_args)
        sql_query = view_query.table_query
    elif table == 'UPbAnalyses':
        # For UPbAnalyses, we need to use the SpotName column
        sql_query = f'''SELECT UPbAnalysisID FROM UPbAnalyses
                        JOIN Spots ON UPbAnalyses.SpotID=Spots.SpotID
                        WHERE SpotName=:name COLLATE NOCASE'''
    else:
        sql_query = f'SELECT {headers[0]} FROM "{table}" WHERE {headers[get_name_column(table)]}=:name COLLATE NOCASE'
    logger_setup.get_logger().debug(f'SQL command: {sql_query}')
    if not query.prepare(sql_query):
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
    query.bindValue(":name", str(name))
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
    Get the total number of records in a table. Optional where clause can be included.
    :param table: name of the table to query
    :param where: optional where clause to append to the count query
    :return: integer of the total number of records
    """
    query = QSqlQuery()
    sql_query = f'SELECT COUNT() FROM "{table}" {where}'
    table = get_view_from_table(table)
    if 'View' in table:
        table = get_table_from_view(table)
        if table in ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses']:
                sql_query = f'SELECT COUNT() FROM (Select * FROM Samples {SQLUtils.get_join_from_table('', [table])}) {where}'


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


def get_record_index(table: str, record_id: int, ids_to_show: list = None) -> int:
    """
    Gets the index of the record for a given record_id.
    :param table: name of the table to query
    :param record_id: id of the record to find (e.g. RockTypeID=4)
    :param ids_to_show: optional list of IDs to filter the results by so can acurately find the row in a filtered table
    :return: row number/index of the record
    """
    if table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees:
        # If the table is a tree, we cannot use this method to find the index, so return -1
        logger_setup.get_logger().error(f'Cannot get record index for tree {table}')
        logger_setup.get_logger().debug(
            f'Table {table} is a tree view which does not use sorting or paging, so cannot get record index')
        logger_setup.get_logger().debug(f'Inspect code to remove sorting and paging for trees')
        return -1
    if not ids_to_show:
        ids_to_show = []
    if record_id not in ids_to_show and len(ids_to_show) > 0:
        record_name = get_name_from_id(table, record_id)
        logger_setup.get_logger().error(f'Record {record_name} not available in this view')
        logger_setup.get_logger().debug(f'Record ID {record_id} in the list of IDs to show: {ids_to_show}')
        return -1
    query = QSqlQuery()
    base_id_column = get_headers(table)[0]
    name_header = get_headers(table)[get_name_column(table)]
    if len(ids_to_show) > 1:
        where = f'WHERE {base_id_column} IN ({", ".join(map(str, ids_to_show))})'
    elif len(ids_to_show) == 1:
        where = f'WHERE {base_id_column} = {ids_to_show[0]}'
    else:
        where = ''
    # Construct the SQL query
    sql_query = f"""
            SELECT row_number 
            FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY {name_header}) AS row_number, {base_id_column}, {name_header} 
                FROM "{table}" {where}
            ) 
            WHERE {base_id_column} = :record_id
        """

    # Prepare and bind parameters
    query.prepare(sql_query)
    query.bindValue(":record_id", int(record_id))

    logger_setup.get_logger().info(f'Getting the record index for record ID: {record_id}')
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

def scroll_to_record(record_id: int, view: QtW.QTableView | QtW.QTreeView):
    """
    Scroll to a specific record in the view.
    :param record_id: id of record
    :param view: view to scroll
    """
    if isinstance(view, QtW.QTableView):
        model = view.model()
        for row in range(model.rowCount()):
            if model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == record_id:
                logger_setup.get_logger().info(f'Scrolling to record ID: {record_id}')
                view.selectionModel().select(model.index(row, 0), QtC.QItemSelectionModel.SelectionFlag.Select |
                                             QtC.QItemSelectionModel.SelectionFlag.Rows)
                # todo: figure out scrolling to the selected row
                # view.scrollTo(model.index(row, 0), QtW.QAbstractItemView.ScrollHint.PositionAtTop)
                # print(view.verticalScrollBar().maximum())
                # view.verticalScrollBar().setValue(row)
                # print(view.verticalScrollBar().value())
                # view.updateGeometry()
                # view.viewport().update()
                # view.setCurrentIndex(model.index(row, 0))
                break

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
    lat_dir = ''
    lon_dir = ''
    if '"' in string or '\'\'' in string:
        # DMS format, (lat_deg°lat_min'lat_sec" lat_dir, lon_deg°lon_min'lon_sec" lon_dir) or (lat_deg°lat_min'lat_sec", lon_deg°lon_min'lon_sec")
        if '"' in string:
            second_delimiter = '"'
        elif '\'\'' in string:
            second_delimiter = '\'\''
        lat_string = string.split(', ')[0]
        lon_string = string.split(', ')[1]
        lat_sec = lat_string.split('°')[1].split(second_delimiter)[0].split('\'')[1]
        lon_sec = lon_string.split('°')[1].split(second_delimiter)[0].split('\'')[1]
        rounded_lat_sec = return_rounded(lat_sec)
        rounded_lon_sec = return_rounded(lon_sec)
        string = string.replace(f'{lat_sec}{second_delimiter}', f'{rounded_lat_sec}{second_delimiter}')
        string = string.replace(f'{lon_sec}{second_delimiter}', f'{rounded_lon_sec}{second_delimiter}')
        if not lat_dir and not lon_dir:
            try:
                lat_dir = lat_string.split(f'{second_delimiter} ')[1]
                lon_dir = lon_string.split(f'{second_delimiter} ')[1]
            except IndexError:
                pass
    if "'" in string:
        # DM format, (lat_deg°lat_min' lat_dir, lon_deg°lon_min' lon_dir) or (lat_deg°lat_min', lon_deg°lon_min')
        lat_string = string.split(', ')[0]
        lon_string = string.split(', ')[1]
        lat_min = lat_string.split('°')[1].split('\'')[0]
        lon_min = lon_string.split('°')[1].split('\'')[0]
        rounded_lat_min = return_rounded(lat_min)
        rounded_lon_min = return_rounded(lon_min)
        string = string.replace(f'{lat_min}\'', f'{rounded_lat_min}\'')
        string = string.replace(f'{lon_min}\'', f'{rounded_lon_min}\'')
        if not lat_dir and not lon_dir:
            try:
                lat_dir = lat_string.split('\' ')[1]
                lon_dir = lon_string.split('\' ')[1]
            except IndexError:
                pass
    if '°' in string:
        # D format, (lat_deg° lat_dir, lon_deg° lon_dir)
        lat_deg = string.split('°')[0]
        lon_deg = string.split(', ')[1].split('°')[0]
        rounded_lat_deg = return_rounded(lat_deg)
        rounded_lon_deg = return_rounded(lon_deg)
        string = string.replace(f'{lat_deg}°', f'{rounded_lat_deg}°')
        string = string.replace(f'{lon_deg}°', f'{rounded_lon_deg}°')
        if not lat_dir and not lon_dir:
            try:
                lat_dir = string.split('° ')[1].split(', ')[0]
                lon_dir = string.split('° ')[2]
            except IndexError:
                lat_dir = ''
                lon_dir = ''
        try:
            lat_dir_id = int(lat_dir)
            query = QtS.QSqlQuery()
            if query.exec(f'SELECT DirectionUnitAbbreviation FROM DirectionUnits WHERE DirectionUnitID={lat_dir_id}'):
                query.next()
                lat_dir_abbreviation = query.value(0)
                lat_string = string.split(', ')[0][:-1] + lat_dir_abbreviation
                string = string.replace(string.split(', ')[0], lat_string)
            lon_dir_id = int(lon_dir)
            if query.exec(f'SELECT DirectionUnitAbbreviation FROM DirectionUnits WHERE DirectionUnitID={lon_dir_id}'):
                query.next()
                lon_dir_abbreviation = query.value(0)
                lon_string = string.split(', ')[1][:-1] + lon_dir_abbreviation
                string = string.replace(string.split(', ')[1], lon_string)
        except:
            # If there is no direction or it is not an ID, there is nothing to do
            pass
    elif ',' in string:
        # UTM format, (UTMZone, UTMEasting, UTMNorthing)
        utm_easting = string.split(',')[1]
        utm_e_m = utm_easting.split('m')[0]
        utm_northing = string.split(',')[2]
        utm_n_m = utm_northing.split('m')[0]
        rounded_northing = return_rounded(utm_n_m)
        rounded_easting = return_rounded(utm_e_m)
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
            try:
                float(value) # value is float, not text
                if value.split('.')[1] != '0':
                    rounded_value = f'{float(value):.{decimal_places}f}'
                else: # value is an integer
                    rounded_value = int(float(value))
            except ValueError:
                rounded_value = value
        else:
            try:
                int(value)  # value is integer, not text
                rounded_value = int(value)
            except ValueError:
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
    :param value: String, float, or integer to convert to the best number format
    :return: Value as a number or the original string if it was not a number
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
    elif isinstance(value, int):
        return value
    else:
        logger_setup.get_logger().info(f"Invalid value type: {type(value)}. Expected str, float, or int.")
        return value


def delete_query(table: str, ids: list):
    if not ids:
        logger_setup.get_logger().error(f"No IDs given for deletion in {table}")
        return False
    create_savepoint('before_delete')
    delete_names = []
    for item_id in ids:
        name = get_name_from_id(table, item_id)
        if name:
            delete_names.append(name)
        else:
            logger_setup.get_logger().warning(f"Could not find name for ID {item_id} in {table}")
    logger_setup.get_logger().info(f"Deleting {table}: {delete_names}")
    query = QtS.QSqlQuery()
    id_header = get_headers(table)[0]  # Get the first header which is the ID column
    if len(ids) > 0:
        query.prepare(f'DELETE FROM "{table}" WHERE {id_header} in {tuple(ids)}')
    if len(ids) == 1:
        query.prepare(f'DELETE FROM "{table}" WHERE {id_header}={ids[0]}')
    if not query.exec():
        logger_setup.get_logger().error(f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        rollback_savepoint('before_delete')
        return False
    logger_setup.get_logger().info(f"Deleted {len(ids)} records from {table}")
    release_savepoint('before_delete')
    return True

def delete_data(table: str, data_ids: list):
    """
    Given a table, delete given IDS. If table is Samples, Aliquots, or Spots, delete given ids and all sub items
    :param table: Table the IDs belong to
    :param data_ids: List of table IDs
    :return: True or False
    """
    if len(data_ids) == 0:
        logger_setup.get_logger().error(f"No IDs given for deletion in {table}")
        return False
    if not delete_question(table, data_ids):
        logger_setup.get_logger().info(f"Deletion cancelled for {table} with IDs: {', '.join(map(str, data_ids))}")
        return False
    show_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
    # Delete the selected samples from a table and all children, aliquots, spots, and UPb data dependent on them
    sample_ids = []
    aliquot_ids = []
    aliquot_child_ids = []
    spot_ids = []
    upb_analysis_ids = []
    table_child_ids = []
    childless_samples = []
    childless_aliquots = []
    childless_spots = []
    if table == 'Samples':
        aliquot_ids, spot_ids, upb_analysis_ids = find_current_sub_items(data_ids, table)
        aliquot_child_ids = []
        for parent_id in aliquot_ids:
            aliquot_child_ids = find_child_ids('Aliquots', parent_id, aliquot_child_ids)
        sample_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(sample_ids)} samples, {len(aliquot_ids)} aliquots, {len(aliquot_child_ids)} sub-aliquots, {len(spot_ids)} spots, and {len(upb_analysis_ids)} UPb analyses")
    elif table == 'Aliquots':
        spot_ids, upb_analysis_ids = find_current_sub_items(data_ids, table)
        aliquot_ids = data_ids
        aliquot_child_ids = []
        for parent_id in aliquot_ids:
            aliquot_child_ids = find_child_ids('Aliquots', parent_id, aliquot_child_ids)
        logger_setup.get_logger().info(f"Deleting {len(aliquot_ids)} aliquots, {len(aliquot_child_ids)} sub-aliquots, {len(spot_ids)} spots, and {len(upb_analysis_ids)} UPb analyses")
        parent_samples = find_current_parent_items(aliquot_ids, table)
        if parent_samples:
            # Determine if all aliquots of these samples are being deleted
            for sample_id in parent_samples:
                sub_aliquot_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id], 'Samples')
                if not any(aliquot_id not in aliquot_ids for aliquot_id in sub_aliquot_ids):
                    # If all aliquots of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)
    elif table == 'Spots':
        upb_analysis_ids = find_current_sub_items(data_ids, table)
        spot_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(spot_ids)} spots and {len(upb_analysis_ids)} UPb analyses")
        parent_samples, parent_aliquots = find_current_parent_items(data_ids, table)
        if parent_aliquots:
            # Determine if all spots of these aliquots are being deleted
            for aliquot_id in parent_aliquots:
                sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([aliquot_id], 'Aliquots')
                if not any(spot_id not in spot_ids for spot_id in sub_spot_ids):
                    # If all spots of the aliquot are being deleted, add the aliquot to the list
                    if aliquot_id not in childless_aliquots:
                        childless_aliquots.append(aliquot_id)
        if childless_aliquots:
            # Determine if all spots of these samples are being deleted
            for sample_id in parent_samples:
                sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id], 'Samples')
                if not any(spot_id not in spot_ids for spot_id in sub_spot_ids):
                    # If all spots of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)
    elif table == 'UPbAnalyses':
        upb_analysis_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(upb_analysis_ids)} UPb analyses")
        parent_samples, parent_aliquots, parent_spots = find_current_parent_items(data_ids, table)
        if parent_spots:
            # Determine if all UPb analyses of these spots are being deleted
            for spot_id in parent_spots:
                sub_upb_analysis_ids = find_current_sub_items([spot_id], 'Spots')
                if not any(upb_analysis_id not in upb_analysis_ids for upb_analysis_id in sub_upb_analysis_ids):
                    # If all UPb analyses of the spot are being deleted, add the spot to the list
                    if spot_id not in childless_spots:
                        childless_spots.append(spot_id)
        if childless_spots:
            # Determine if all UPb analyses of these aliquots are being deleted
            for aliquot_id in parent_aliquots:
                sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([aliquot_id], 'Aliquots')
                if not any(upb_analysis_id not in upb_analysis_ids for upb_analysis_id in sub_upb_analysis_ids):
                    # If all UPb analyses of the aliquot are being deleted, add the aliquot to the list
                    if aliquot_id not in childless_aliquots:
                        childless_aliquots.append(aliquot_id)
        if childless_aliquots:
            # Determine if all UPb analyses of these samples are being deleted
            for sample_id in parent_samples:
                sub_aliquot_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id], 'Samples')
                if not any(upb_analysis_id not in upb_analysis_ids for upb_analysis_id in sub_upb_analysis_ids):
                    # If all UPb analyses of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)
    elif table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees:
        # For user viewable trees, we need to check for child IDs
        table_child_ids = []
        for parent_id in data_ids:
            # Find all child IDs of the given parent_id
            table_child_ids = find_child_ids(table, parent_id, table_child_ids)
    if childless_samples or childless_aliquots or childless_spots:
        # If there are childless samples, aliquots, or spots, warn the user these will be deleted as well and ask if they want to proceed
        msg_box = QtW.QMessageBox()
        msg_box.setIcon(QtW.QMessageBox.Icon.Question)
        msg_box.setWindowTitle('Delete Empty Items')
        msg_text = f'Deleting these {len(data_ids)} {table} will also delete the following empty items:'
        if childless_samples:
            sample_names = [get_name_from_id('Samples', sample_id) for sample_id in childless_samples]
            msg_text += f'\n{len(childless_samples)} Samples: {", ".join(sample_names)}'
        if childless_aliquots:
            aliquot_names = [get_name_from_id('Aliquots', aliquot_id) for aliquot_id in childless_aliquots]
            msg_text += f'\n{len(childless_aliquots)} Aliquots: {", ".join(aliquot_names)}'
        if childless_spots:
            spot_names = [get_name_from_id('Spots', spot_id) for spot_id in childless_spots]
            msg_text += f'\n{len(childless_spots)} Spots: {", ".join(spot_names)}'
        msg_text += '\n\nDo you want to continue?'
        msg_box.setText(msg_text)
        msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response == QtW.QMessageBox.StandardButton.Yes:
            # If the user wants to delete the empty items, add them to the deletion lists
            if childless_samples:
                sample_ids.extend(childless_samples)
            if childless_aliquots:
                aliquot_ids.extend(childless_aliquots)
            if childless_spots:
                spot_ids.extend(childless_spots)
        else:
            # If the user does not want to delete the empty items, cancel the deletion
            close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
            logger_setup.get_logger().info(f"Deletion cancelled for {table} with IDs: {', '.join(map(str, data_ids))}")
            return False

    from Functions.Database_manager import turn_on_foreign_keys
    # Double-check that foreign keys are enabled
    if not turn_on_foreign_keys():
        close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
        return False
    if table in ('Samples', 'Aliquots', 'Spots', 'UPbAnalyses'):
        if upb_analysis_ids:
            if not delete_query('UPbAnalyses', upb_analysis_ids):
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(upb_analysis_ids)} UPb analyses')
        if spot_ids:
            if not delete_query('Spots', spot_ids):
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(spot_ids)} spots')
        if aliquot_ids:
            aliquot_ids.extend(aliquot_child_ids)  # Include child aliquots in the deletion
            if not delete_query('Aliquots', aliquot_ids):
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(aliquot_ids)} Aliquots')
        if sample_ids:
            if not delete_query('Samples', sample_ids):
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(sample_ids)} Samples')
    else:
        if table_child_ids:
            delete_ids = data_ids + table_child_ids
        else:
            delete_ids = data_ids
        if delete_ids:
            if not delete_query(table, delete_ids):
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(delete_ids)} {table} records')

    close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
    return True

def delete_question(table, delete_ids):
    show_loading_dialog('Preparing', 'Gathering information...')
    msg_box = QtW.QMessageBox()
    msg_box.setIcon(QtW.QMessageBox.Icon.Question)
    if table == 'Samples':
        sample_names = [get_name_from_id(table, sample_id) for sample_id in delete_ids]
        # Samples have a special case where they are related to Aliquots, Spots, and UPbAnalyses
        aliquot_ids, spot_ids, upb_analysis_ids = find_current_sub_items(delete_ids, table)
        msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?' \
                    f'\nSamples: {", ".join(sample_names)}' \
                    f'\nAssociated with {len(aliquot_ids)} aliquots, {len(spot_ids)} spots, and {len(upb_analysis_ids)} U-Pb analyses'
    elif table == 'Aliquots':
        aliquot_names = [get_name_from_id(table, aliquot_id) for aliquot_id in delete_ids]
        # Look for children of Aliquots
        child_aliquot_ids = []
        for aliquot_id in delete_ids:
            # Find all child aliquots of the given aliquot_id
            child_aliquot_ids = (aliquot_id, child_aliquot_ids)

        # Aliquots have a special case where they are related to Spots and UPbAnalyses
        spot_ids, upb_analysis_ids = find_current_sub_items(delete_ids, table)
        msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?' \
                    f'\nAliquots: {", ".join(aliquot_names)}' \
                    f'\nAssociated with {len(child_aliquot_ids)} child aliquots, {len(spot_ids)} spots, and {len(upb_analysis_ids)} U-Pb analyses'
    elif table == 'Spots':
        spot_names = [get_name_from_id(table, spot_id) for spot_id in delete_ids]
        # Spots have a special case where they are related to UPbAnalyses
        upb_analysis_ids = find_current_sub_items(delete_ids, table)
        msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?' \
                    f'\nSpots: {", ".join(spot_names)}' \
                    f'\nAssociated with {len(upb_analysis_ids)} U-Pb analyses'
    else:
        if table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees:
            # For user viewable trees, we need to check for child IDs
            child_ids = []
            for parent_id in delete_ids:
                # Find all child IDs of the given parent_id
                child_ids = find_child_ids(table, parent_id, child_ids)
            all_delete_ids = set(delete_ids + child_ids)
            tree_item_names = [get_name_from_id(table, item_id) for item_id in all_delete_ids]
            msg_text = f'Are you sure you want to delete these {len(all_delete_ids)} {table}?' \
                        f'\n{table}: {", ".join(tree_item_names)}'
        else:
            item_names = [get_name_from_id(table, item_id) for item_id in delete_ids]
            all_delete_ids = set(delete_ids)
            msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?' \
                        f'\n{table}: {", ".join(item_names)}'
        associations = find_foreign_associations(table, list(all_delete_ids))
        if len(associations) == 0:
            association_text = ''
        elif len(associations) < 4:
            # List the associations with their names for up to three table associations
            association_text = '\nAssociated with: '
            for associated_table, ids in associations.items():
                if not ids:
                    logger_setup.get_logger().info(f'Unable to find IDs for {associated_table} associations')
                    return False
                elif len(ids) == 0:
                    continue
                # append the association text with the number of IDs and the names of the IDs
                elif len(ids) < 11:
                    association_text += f'\n{len(ids)} {associated_table} ({", ".join(get_name_from_id(associated_table, id) for id in ids)})'
                else:
                    if associated_table == 'UPbAnalyses':
                        # We can use spot names, but just list the number of analyses
                        association_text += f'\n{len(ids)} {associated_table}'
                    else:
                        association_text += f'\n{len(ids)} {associated_table} ({", ".join(get_name_from_id(associated_table, id) for id in ids[:10])}...)'
        else:
            association_text = f'\nAssociated with '
            for associated_table, ids in associations.items():
                # append the association text with the number of IDs and the names of the IDs
                association_text += f'{len(ids)} {associated_table}, '
        msg_text += association_text
    msg_box.setText(msg_text)
    msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.No)
    close_loading_dialog('Preparing', 'Gathering information...')
    response = msg_box.exec()
    if response == QtW.QMessageBox.StandardButton.Yes:
        return True
    else:
        return False


def find_child_ids(table, parent_id, child_ids=None):
    """
    Find all child IDs of a given parent ID in a table. This is used to find all child aliquots of a given aliquot ID.
    :param table: Database table to search for child IDs
    :param parent_id: ID of the parent record to find children for
    :param child_ids: List of child IDs so far, used for recursion
    :return:
    """
    # Find all child aliquots of the given aliquot_id
    if not child_ids:
        child_ids = []
    query = QtS.QSqlQuery()
    table_headers = get_headers(table)
    id_header = table_headers[0]  # Get the first column header which is the ID column
    parent_id_header = table_headers[1]  # Get the second column header which is the Parent ID column
    query.prepare(f'SELECT {id_header} FROM {table} WHERE {parent_id_header}=:parent_id')
    query.bindValue(':parent_id', parent_id)
    if not query.exec():
        logger_setup.get_logger().critical(f"Error finding child aliquots to delete")
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        return
    while query.next():
        if query.value(0) not in child_ids:
            child_ids.append(query.value(0))
            find_child_ids(table, query.value(0), child_ids)
    return child_ids


def find_foreign_associations(table, item_ids):
    """
    One-to-many and many-to-many associations for a given table and item IDs, such as UPbAnalyses and LabFacilities or
    Samples_Units.
    :param table: table of foreign key in another table or second table in many-to-many relationship
    :param item_ids: list of item IDs to check for associations
    :return: dictionary of associations with table names as keys and lists of item IDs as values
    """
    # Find all many-to-many tables where table is the second table in the relationship
    if not item_ids:
        logger_setup.get_logger().warning(f"No item IDs provided for finding foreign associations in {table}")
        return {}
    logger_setup.get_logger().info(f"Finding foreign associations for {len(item_ids)} {table}")
    id_header = get_headers(table)[0]
    associations = {}
    db_tables = get_database_tables()
    if len(item_ids) > 1:
        where = f'WHERE {id_header} IN {tuple(item_ids)}'
    elif len(item_ids) == 1:
        where = f'WHERE {id_header} = {item_ids[0]}'
    for db_table in db_tables:
        if 'Conversions' in db_table or ('Units' in db_table and db_table not in ['Samples_Units', 'Units']):
            # Skip Conversions table as it is not a foreign key association
            continue
        elif '_' in db_table and db_table.split('_')[1] == table:
            # This is a many-to-many table where table is the second table in the relationship
            first_table = db_table.split('_')[0]
            first_table_id_header = get_headers(first_table)[0]  # Get the first column header which is the ID column
            if first_table not in associations:
                associations[first_table] = []
            foreign_table_model = SQLiteTableModel(f'SELECT {first_table_id_header} FROM "{db_table}" {where}')
            if not foreign_table_model.last_error:
                for row in range(foreign_table_model.rowCount()):
                    foreign_id = foreign_table_model.data(foreign_table_model.index(row, 0))
                    if foreign_id not in associations[first_table]:
                        associations[first_table].append(foreign_id)
        else:
            if table in ['Units']:
                # These are tables without one-to-one or one-to-many relationships, so skip them
                continue
            # Check if the table is a foreign key in db_table. Not capable of handling non-editable table ID headers
            # (e.g. DistanceUnitID), but handles anything that can be edited by the user
            for header in get_headers(db_table):
                if id_header in header and get_headers(db_table)[0] not in header:
                    # This is a one-to-many relationship where table is the foreign key in db_table
                    if db_table not in associations:
                        associations[db_table] = []
                    if id_header != header:
                        where_one = where.replace(f'{id_header}', f'"{header}"')
                    else:
                        where_one = where
                    foreign_table_model = SQLiteTableModel(f'SELECT {get_headers(db_table)[0]} FROM "{db_table}" {where_one}')
                    if not foreign_table_model.last_error:
                        for row in range(foreign_table_model.rowCount()):
                            foreign_id = foreign_table_model.data(foreign_table_model.index(row, 0))
                            if foreign_id not in associations[db_table]:
                                associations[db_table].append(foreign_id)
                    break
    return associations


def find_upb_from_samples(sample_ids):
    # Find UPb analyses for a list of samples
    logger_setup.get_logger().info(f"Finding UPb Analyses for {len(sample_ids)} samples")
    upb_analysis_ids = []
    if len(sample_ids) > 1:
        where = f'WHERE SampleID in {tuple(sample_ids)}'
    elif len(sample_ids) == 1:
        where = f'WHERE SampleID = {sample_ids[0]}'
    else:
        # No samples selected
        return
    query_args = {'where': where, 'show_columns': ['UPbAnalysisID']}
    view_query = ViewQuery('UPbAnalyses', False, **query_args)
    table_query = view_query.table_query
    show_loading_dialog('Loading', 'Gathering related data for UPb Analyses...')
    upb_analysis_table = SQLiteTableModel(table_query, view_query=view_query)
    close_loading_dialog('Loading', 'Gathering related data for UPb Analyses...')
    if not upb_analysis_table.last_error:
        for row in range(upb_analysis_table.rowCount()):
            upb_data_id = upb_analysis_table.data(upb_analysis_table.index(row, 0))
            upb_analysis_ids.append(upb_data_id)
        return upb_analysis_ids
    else:
        # There was an error creating the table
        return

def find_sub_items(data_ids: list, table: str) -> tuple:
    """
    Find all sub items of a list of samples, aliquots, or spots. This is intended to find sub items for Samples, Aliquots,
    and Spots, and return the IDs of the sub items. For commited data only.
    :param data_ids: List of data IDs to find sub items for
    :param table: Table to search for sub items, can be 'Samples', 'Aliquots', or 'Spots'
    :return: tuple of lists of sub item IDs
    """
    # Find all the sub items of a list of samples, aliquots, or spots
    logger_setup.get_logger().info(f"Finding sub items for {len(data_ids)} {table}")
    if not data_ids:
        logger_setup.get_logger().warning(f"No data IDs provided for finding sub items in {table}")
        return None, None, None
    show_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    aliquot_ids = []
    spot_ids = []
    upb_analysis_ids = []
    if table == 'Samples':
        sql_query = f"""SELECT Aliquots.AliquotID, Spots.SpotID, UPbAnalyses.UPbAnalysisID FROM Aliquots
                        {SQLUtils.aliquot_spot_join}
                        {SQLUtils.spot_upb_analysis_join}
                        WHERE SampleID {where}"""
        aliquot_ids, spot_ids, upb_analysis_ids = columns_as_list(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return aliquot_ids, spot_ids, upb_analysis_ids
    elif table == 'Aliquots':
        sql_query = f"""SELECT Spots.SpotID, UPbAnalyses.UPbAnalysisID FROM Spots
                        {SQLUtils.spot_upb_analysis_join}
                        WHERE AliquotID {where}"""
        spot_ids, upb_analysis_ids = columns_as_list(sql_query, [0, 1])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return spot_ids, upb_analysis_ids
    elif table == 'Spots':
        sql_query = f"""SELECT UPbAnalyses.UPbAnalysisID FROM UPbAnalyses
                        WHERE SpotID {where}"""
        upb_analysis_ids = columns_as_list(sql_query, [0])[0]
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return upb_analysis_ids
    else:
        logger_setup.get_logger().critical(f"Table {table} in not supported for finding sub items")
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return None, None, None


def find_parent_items(data_ids: list, table: str) -> tuple:
    """
    Find parent items for a list of data IDs in a given table. This is intended to find parent items for Aliquots, Spots,
    and UPbAnalyses. For commited data only.
    :param data_ids: List of data IDs to find parent items for
    :param table: Table to search for parent items
    :return: Tuple of lists of parent sample IDs, aliquot IDs, and spot IDs
    """
    logger_setup.get_logger().info(f"Finding parent items for {len(data_ids)} {table}")
    if not data_ids:
        logger_setup.get_logger().warning(f"No data IDs provided for finding parent items in {table}")
        return None, None, None
    show_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    sample_ids = []
    aliquot_ids = []
    spot_ids = []
    if table == 'UPbAnalyses':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, UPbAnalyses.SpotID FROM UPbAnalyses 
                        {SQLUtils.upb_spot_join}
                        {SQLUtils.spot_aliquot_join}
                        WHERE UPbAnalysisID {where}"""
        sample_ids, aliquot_ids, spot_ids = columns_as_list(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids, spot_ids
    elif table == 'Spots':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID FROM Spots
                        {SQLUtils.spot_aliquot_join}
                         WHERE SpotID {where}"""
        sample_ids, aliquot_ids = columns_as_list(sql_query, [0, 1])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids
    elif table == 'Aliquots':
        sql_query = f"""SELECT SampleID FROM Aliquots
                        WHERE AliquotID {where}"""
        sample_ids = columns_as_list(sql_query, [0])[0]
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids
    else:
        logger_setup.get_logger().critical(f"Table {table} in not supported for finding parent items")
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return None, None, None


def find_current_sub_items(data_ids: list, table: str):
    """
    Find all sub items of a list of samples, aliquots, or spots. This is intended to find sub items for Samples, Aliquots,
    and Spots, and return the IDs of the sub items. For uncommited data only with a significant efficiency cost.
    :param data_ids: List of data IDs to find sub items for
    :param table: Table to search for sub items, can be 'Samples', 'Aliquots', or 'Spots'
    :return: Tuple of lists of sub item IDs
    """
    # Find all the sub items of a list of samples, aliquots, or spots
    logger_setup.get_logger().info(f"Finding sub items for {len(data_ids)} {table}")
    if not data_ids:
        logger_setup.get_logger().warning(f"No data IDs provided for finding sub items in {table}")
        return None, None, None
    show_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    aliquot_ids = []
    spot_ids = []
    upb_analysis_ids = []
    if table == 'Samples':
        sql_query = f"""SELECT Aliquots.AliquotID, Spots.SpotID, UPbAnalyses.UPbAnalysisID FROM Aliquots
                        {SQLUtils.aliquot_spot_join}
                        {SQLUtils.spot_upb_analysis_join}
                        WHERE SampleID {where}"""
        aliquot_ids, spot_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return aliquot_ids, spot_ids, upb_analysis_ids
    elif table == 'Aliquots':
        sql_query = f"""SELECT Spots.SpotID, UPbAnalyses.UPbAnalysisID FROM Spots
                        {SQLUtils.spot_upb_analysis_join}
                        WHERE AliquotID {where}"""
        spot_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return spot_ids, upb_analysis_ids
    elif table == 'Spots':
        sql_query = f"""SELECT UPbAnalyses.UPbAnalysisID FROM UPbAnalyses
                        WHERE SpotID {where}"""
        upb_analysis_ids = columns_as_list_current(sql_query, [0])[0]
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return upb_analysis_ids
    else:
        logger_setup.get_logger().critical(f"Table {table} in not supported for finding sub items")
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return None, None, None


def find_current_parent_items(data_ids: list, table: str):
    """
    Find parent items for a list of data IDs in a given table. This is intended to find parent items for Aliquots, Spots,
    and UPbAnalyses. For uncommited data only with a significant efficiency cost.
    :param data_ids: List of data IDs to find parent items for
    :param table: Table to search for parent items
    :return: Tuple of lists of parent sample IDs, aliquot IDs, and spot IDs
    """
    logger_setup.get_logger().info(f"Finding parent items for {len(data_ids)} {table}")
    if not data_ids:
        logger_setup.get_logger().warning(f"No data IDs provided for finding parent items in {table}")
        return None, None, None
    show_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    sample_ids = []
    aliquot_ids = []
    spot_ids = []
    if table == 'UPbAnalyses':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, UPbAnalyses.SpotID FROM UPbAnalyses 
                        {SQLUtils.upb_spot_join}
                        {SQLUtils.spot_aliquot_join}
                        WHERE UPbAnalysisID {where}"""
        sample_ids, aliquot_ids, spot_ids = columns_as_list_current(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids, spot_ids
    elif table == 'Spots':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID FROM Spots
                        {SQLUtils.spot_aliquot_join}
                         WHERE SpotID {where}"""
        sample_ids, aliquot_ids = columns_as_list_current(sql_query, [0, 1])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids
    elif table == 'Aliquots':
        sql_query = f"""SELECT SampleID FROM Aliquots
                        WHERE AliquotID {where}"""
        sample_ids = columns_as_list_current(sql_query, [0])[0]
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids
    else:
        logger_setup.get_logger().critical(f"Table {table} in not supported for finding parent items")
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return None, None, None



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
    def __init__(self, itemData: QtS.QSqlRecord | SQLiteTableModel.MockRecord, parent_item):
        """
        Create a tree item with given data and parent item
        Parameters
        ----------
        itemData: SQL record from a QSql model or a mock record from SQLiteTableModel
        parent_item: parent tree item
        """
        self.itemData = itemData
        self.parent_item = parent_item
        self.childItems = []

    def __del__(self):
        """
        Deletes all children of deleted item
        """
        # logger_setup.get_logger().info(f'Deleting tree items')
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
        if self.parent_item:
            # return self.parent_item.childItems.indexOf(TreeItem(self))
            return self.parent_item.childItems.index(self)
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
        elif isinstance(self.itemData, QtS.QSqlRecord):
            field = self.itemData.field(column)
            self.itemData.setValue(field.name(), value)
            return True
        elif isinstance(self.itemData, SQLiteTableModel.MockRecord):
            # The itemData is a mock record
            self.itemData.setValue(column, value)

    def setRecord(self, record: QtS.QSqlRecord):
        self.itemData = record

    def parent(self):
        # parent for given item
        if self.itemData is None:
            return None
        else:
            return self.parent_item


class TreeModel(QtC.QAbstractProxyModel):
    """
    A tree model that can be used to display hierarchical data in a tree view. A proxy model is used to allow for
    easier translation to and from the source model, which can be a QSqlTableModel, QSqlQueryModel, or SQLiteTableModel.
    Because the order of children is preserved in the database, sorting should not be used on the tree model.
    Assumes that the first four data columns are ordered as follows:
    0: ID
    1: Parent ID
    2: Parent Row
    3: Name
    """
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
        self.parent_to_children = {}
        self.item_data = {}
        self.lastError = QtS.QSqlError()
        self.db = db

        if self.source_model:
            # Check if a table model was set
            if isinstance(self.source_model, QSqlTableModel):
                if self.source_model.tableName() == '':
                    return
            elif isinstance(self.source_model, QSqlQueryModel):
                query_object = source_model.query()
                if query_object.lastQuery() == '':
                    return
            elif isinstance(self.source_model,SQLiteTableModel):
                if source_model.query_text == '':
                    return
            self.setSourceModel(self.source_model)

    def sourceModel(self):
        """
        Returns the source model of the tree model.
        :return: data model
        """
        return self.source_model

    def setSourceModel(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel):
        """
        Set the source model for the tree model. This method initializes the tree model with the given source model,
        retrieves the table name, and sets up the base query and filter for the model. It also clears any previous tree
        model data and sets up the root item, parent item, and child item as TreeItems for the tree structure.
        If the base query is an Aliquot view or from Ages, it will set the source model to a SQLiteTableModel to speed
        up building the tree. Otherwise, it will set the source model to a DisplayRoundedQueryModel.
        :param source_model: Populated QSqlTableModel, QSqlQueryModel, or SQLiteTableModel
        :return: Nothing if there is an error
        """
        logger_setup.get_logger().info(f'Setting source model for tree model...')
        try:
            if source_model.tableName() != '':
                self.table = source_model.tableName()
            else:
                logger_setup.get_logger().critical('Error setting up tree model')
                logger_setup.get_logger().debug('No table name set')
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
            view_query = source_model.view_query
        if len(self.base_query) > 0:
            if ' WHERE ' in self.base_query:
                self.base_query_sql = f"{self.base_query} AND "
            else:
                self.base_query_sql = f"{self.base_query} WHERE "
        if (('FROM LimitedAliquots' in self.base_query or 'FROM Ages' in self.base_query) or
                isinstance(source_model, SQLiteTableModel)):
            if isinstance(source_model, SQLiteTableModel) and source_model.query_text == self.base_query:
                # If the source model is already a SQLiteTableModel with the same query, use it
                self.source_model = source_model
            else:
                try:
                    self.source_model = SQLiteTableModel(query=self.base_query, view_query=view_query)
                except NameError:
                    self.source_model = SQLiteTableModel(query=self.base_query)
                if self.source_model.last_error:
                    logger_setup.get_logger().critical(f'Error displaying the selected table')
                    return
        else:
            self.source_model = DisplayRoundedQueryModel(db=self.db)
            self.source_model.setQuery(f'{self.base_query}')
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.header_variables()
        if self.root_item.childCount() > 0:
            logger_setup.get_logger().info('Clearing previous tree model...')
            self.root_item.clear()
        # self.root_item = TreeItem(QtS.QSqlRecord(), None)
        self.parent_item = TreeItem(QtS.QSqlRecord(), None)
        self.child_item = TreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()

    def setup_model_data(self):
        """
        Set up the model data for the tree model. This will build the tree from the source model.
        """
        self.parent_to_children = {}
        self.item_data = {}
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            item_id = record.value(0)  # Assuming the first column is the ID
            parent_id = record.value(1)  # Assuming the second column is the Parent ID
            if not parent_id:
                parent_id = None

            self.item_data[item_id] = record
            if parent_id not in self.parent_to_children:
                self.parent_to_children[parent_id] = []

            self.parent_to_children[parent_id].append(item_id)

        for parent_id, child_ids in self.parent_to_children.items():
            child_ids.sort(key=lambda x: self.item_data[x].value(2))  # Sort by parent row

        # Add all nodes to the tree model
        # start with root item, look for children
        logger_setup.get_logger().info(f'Building the {self.table} tree from the model...')
        show_loading_dialog('Loading', f'Building the {self.table} tree with {self.source_model.rowCount()} items...')
        start_build_time = time.time()
        # add each child to model with parent (root)
        self.add_to_tree(self.root_item)
        # look for children of those
        # add each child to the model with parent
        # etc. until there are no more children
        close_loading_dialog('Loading', f'Building the {self.table} tree with {self.source_model.rowCount()} items...')
        logger_setup.get_logger().info(f'Finished building the {self.table} tree with {self.source_model.rowCount()} items in {time.time() - start_build_time:.2f} seconds')

    def add_to_tree(self, parent: TreeItem):
        """
        Add child items with unique child IDs to the tree model under the specified parent item. This method iterates
        through the list of child IDs, finds the corresponding records in the source model, and creates
        TreeItem instances for each child. It appends these items to the parent item in the tree structure. If a child
        ID has children, it recursively calls itself to add those children as well.
        :param parent: TreeItem parent to add children to
        :return: None if there are no child IDs
        """
        if parent == self.root_item:
            parent_id = None
        else:
            parent_id = parent.itemData.value(0)
        child_ids = self.parent_to_children.get(parent_id, [])
        if not child_ids:
            return
        # logger_setup.get_logger().info(f'Adding {len(child_ids)} children to the tree...')
        # logger_setup.get_logger().debug(f'Child IDs: {child_ids}')

        for child_id in child_ids:
            add_time = time.time()
            record = self.item_data[child_id]
            item = TreeItem(record, parent)
            parent.appendChild(item)
            # logger_setup.get_logger().debug(f'Added {child_id} to the tree')
            # logger_setup.get_logger().info(f'Added {record.value(3)} in {time.time() - add_time} seconds')
            self.add_to_tree(item)

    def column_headers(self):
        """
        Set up the column headers for the tree model based on the source model.
        """
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
        """
        Set up variables for commonly-used headers in the tree model based on the source model headers.
        :return: None if there are no source headers
        """
        if len(self.sourceHeaders) == 0:
            return
        self.id_header = self.sourceHeaders[0]
        self.parent_id_header = self.sourceHeaders[1]
        self.parent_row_header = self.sourceHeaders[2]
        self.item_name_header = self.sourceHeaders[3]
        self.item_description_header = self.sourceHeaders[4]

    def tableName(self) -> str:
        """
        Returns the name of the table this model is based on.
        :return: Name of model table
        """
        return self.table

    def getItem(self, index: QtC.QModelIndex) -> TreeItem:  # returns tree item
        """
        Returns the tree item for a given index.
        :param index: QModelIndex in the model
        :return: TreeItem for the given index, or root item if index is invalid
        """
        if not index.isValid():
            return self.root_item
        else:
            # index = self.index(index.row(), index.column(), index.parent())
            item = index.internalPointer()
            if not item:
                logger_setup.get_logger().error(f"Error finding item for tree index")
                logger_setup.get_logger().debug(f"No item for index {index.row()},{index.column()},{index.parent()}")
            return item

    def index(self, row: int, column: int, parent: QModelIndex=QModelIndex()) -> QtC.QModelIndex:
        """
        Create an index for a child item at the given row and column under the specified parent.
        :param row: row number of the child item
        :param column: column number of the child item
        :param parent: parent QModelIndex for the child item
        :return: QModelIndex for the child item, or an invalid QModelIndex if the parent is not valid or the row/column
        is out of bounds
        """
        # Given row, column, and parent, create an index for a child item at row and column
        # First check if parent is valid and parent item exists
        # Then get the child at the specified row and create an index for it
        # index for views and delegates
        if not isinstance(parent, QtC.QModelIndex):
            pass
        if not self.hasIndex(row, column, parent):
            return QtC.QModelIndex()
        if parent.isValid():
            parent_item = self.getItem(parent)
        else:
            parent_item = self.root_item
        if not parent_item:
            return QtC.QModelIndex()
        if row < 0 or row > self.rowCount(parent):
            return QtC.QModelIndex()
        if column < 0 or column > self.columnCount(parent):
            return QtC.QModelIndex()
        item = parent_item.child(row)
        if item:
            return self.createIndex(row, column, item)
        else:
            return QtC.QModelIndex()

    def parent(self, index: QtC.QModelIndex):
        """
        Returns the parent index of the given index.
        :param index: QModelIndex for which to find the parent
        :return: parent QModelIndex, or an invalid QModelIndex if the index is invalid or has no parent
        """
        # Given index, find parent and create index for parent item
        if not index.isValid():
            return QtC.QModelIndex()
        item = self.getItem(index)
        parent_item = item.parent()
        if parent_item == self.root_item or not parent_item:
            return QtC.QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QtC.QModelIndex = QtC.QModelIndex) -> int:
        """
        Returns the number of rows (children) for the given parent index.
        :param parent: parent QModelIndex for which to count children
        :return: Number of child items under the parent index, or 0 if the parent is invalid
        """
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = self.getItem(parent)
        return parent_item.childCount()

    def columnCount(self, parent: QtC.QModelIndex = ...) -> int:
        """
        Returns the number of columns in the model. Regardless of the parent index, the number of columns is always
        the same as the number of columns in the source model.
        :param parent: Any parent QModelIndex (not used in this implementation)
        :return: Number of columns in the source model
        """
        return self.source_model.columnCount()

    def hasChildren(self, parent: QtC.QModelIndex = ...) -> bool:
        """
        Check if the given parent index has children.
        :param parent: parent QModelIndex to check for children
        :return: True if the parent has children or is the root, False otherwise
        """
        if not parent.isValid():
            return True
        parent_item = self.getItem(parent)
        if parent_item.childCount() > 0:
            return True
        return False

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        """
        Returns the data for the given index and role. The expand/collapse icon is only available on the first column,
        and the first column cannot be hidden without hiding the expand/collapse icon, so the columns are shuffled to
        return the order as follows:
        0: Name
        1: Item ID
        2: Parent ID
        3: Parent Row
        If available, the data in the description column will be shown as a tooltip for the first column. For Ages table,
        the tooltip will show the geologic timescale age range in millions of years (Ma).
        :param index: QModelIndex for which to retrieve data
        :param role: Expected role for the data, such as DisplayRole, EditRole, or ToolTipRole
        :return: Data for the given index and role
        """
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
                tool_tip = item.data(description_col)
                return tool_tip
        # super().data(index, role)  # Slows down the model considerably
        return None

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: QtC.Qt.ItemDataRole = ...) -> bool:
        """
        Set the data for the given index and role. This will update the source model and the tree item data. If the
        source model is not a SQLiteTableModel, it is connected to current database values and will also update the
        database with the new data.
        SQLiteTableModel data are based on uncommitted changes, so any changes to the database would not be reflected
        in the tree model until the changes are committed. Here, we manually update the data for display in the tree
        model.
        :param index: QModelIndex for which to set data
        :param value: value to set for the given index
        :param role: role for the data, such as EditRole
        :return: True if the data was successfully set, False if the index is invalid, or the default return value if the
        role is not EditRole.
        """
        if not index.isValid():
            return False
        if role == QtC.Qt.ItemDataRole.EditRole:
            logger_setup.get_logger().info(
                f'Setting data in {self.table} tree at {index.row()},{index.column()}')
            start_set_time = time.time()
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
            if not isinstance(self.source_model, SQLiteTableModel):
                # The model is connected to the database
                # Get the updated modified timestamp
                sourceIndex = self.mapToSource(index)
                if sourceIndex.isValid():
                    logger_setup.get_logger().info(
                        f'Setting data in {self.table} tree at {sourceIndex.row()},{sourceIndex.column()}')
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
                        # modified = self.source_model.data(source_modified_index, QtC.Qt.ItemDataRole.DisplayRole)
                        update_modified_timestamp(self.table, [table_id])
                        treeItem.setData(modified_col, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
            treeItem.setData(dataCol, value)
            self.dataChanged.emit(index, index)
            logger_setup.get_logger().info(
                f'Successfully set data in {self.table} tree at {index.row()},{index.column()} to {value} in {time.time() - start_set_time:.2f} seconds')
            return True
        return super().setData(index, value, role)

    def moveItem(self, item_id: int, row: int, p_id: str) -> bool:
        """
        Move an item to a new parent and parent row. Updates the changes in the source model and the database.
        :param item_id: unique ID of the item to move
        :param row: new parent row number for the item
        :param p_id: new parent ID for the item, either 'IS NULL' or 'is parentID'
        :return: True if the item was successfully moved, False if there was an error
        """
        # Try making change to database, then reset the tree model
        if p_id == 'IS NULL':
            parentID = 'NULL'
        else:
            parentID = int(p_id[2:])
        self.source_model.setQuery(
            f"{self.base_query_sql} {self.id_header} is {item_id} AND {self.parent_id_header} {p_id} AND {self.parent_row_header} is {row}")
        if self.source_model.rowCount() > 0:
            # If the item is already in the correct place, do nothing
            return True
        # self.save_state.emit()
        self.source_model.setQuery(
            f"{self.base_query_sql} {self.id_header} is {item_id}")  # Only one record for each item ID
        oldParentID = self.source_model.record(0).value(1)  # Get the current parent ID
        if isinstance(oldParentID, int):
            op_id = f'= {oldParentID}'
        else:
            op_id = 'IS NULL'
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
                    return False
                if currentParentRow == row:
                    # Now update the moved item into the new space
                    self.source_model.setQuery(self.base_query)  # Reset the filter
                    if not self.update_parent_info(item_id, parentID, row):
                        return False
        else:  # no children to update
            self.source_model.setQuery(self.base_query)  # Reset the filter
            if not self.update_parent_info(item_id, parentID, row):
                return False
        # Look for remaining children of the old parent whose parent rows need to be updated, order them by parent row from smallest to largest
        self.source_model.setQuery(
            f"{self.base_query_sql}  {self.parent_id_header} {op_id} AND {self.parent_row_header} > {oldParentRow} ORDER BY {self.parent_row_header} ASC")
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
                    return False
        self.source_model.setQuery(self.base_query)  # Reset the filter
        return True

    def update_parent_info(self, item_id: int, parent_id, parent_row: int):
        """
        Update the parent ID and parent row for a given item ID in the database.
        :param item_id: unique ID of the item to update
        :param parent_id: unique ID of the new parent, or None if the item has no parent
        :param parent_row: row number of the new parent in the parent's list of children
        :return: True if the update was successful, False if there was an error
        """
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
            return False
        else:
            update_modified_timestamp(self.table, [item_id])
            logger_setup.get_logger().info(f'Successfully updated parent for {item_id} in table {self.table}')
            return True

    def insertItem(self, item_name: str, item_description: str, parent_id=None, parent_row=None) -> bool:
        """
        Insert a new item into the database and the tree model. The item is first added as a top-level item, then moved
        to the correct parent and row. If no parent ID is given, the item is added to the root item. If no parent row is
        given, the item is added to the end of the child list.
        :param item_name: new item name to add to the tree model
        :param item_description: new item description to add to the tree model
        :param parent_id: unique ID of the parent item, or None if the item has no parent
        :param parent_row: row number of the parent item. If None, the item is added to the end of the list.
        :return: True if the item was successfully inserted, False if there was an error adding or moving item
        """
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
        # self.save_state.emit()
        if not query.exec():
            logger_setup.get_logger().critical(f'Error inserting new item {item_name}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            logger_setup.get_logger().debug(f"Bound values: {query.boundValues()}")
            rollback_savepoint('before_insert')
            return False
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
                return False
            release_savepoint('before_insert')
            self.dataEdited.emit()
            return True

    def removeItem(self, item_id: int, parent_row: int, parent_id=None):
        """
        Remove an item and all its children from the database and the tree model. The item is first deleted from the
        database, then the tree model is updated to reflect the changes. If the item has children, their parent rows are
        updated to close the gap left by the deleted item.
        :param item_id: unique ID of the item to remove
        :param parent_row: row number of the parent item in the parent's list of children
        :param parent_id: unique ID of the parent item, or None if the item has no parent
        :return: True if the item was successfully removed or already removed, False if there was an error deleting the
        item or updating the tree model.
        """
        # Remove an item and all children from the database
        del_ids = [item_id]
        if len(del_ids) == 0:
            logger_setup.get_logger().info(f'Item was already deleted')
            logger_setup.get_logger().debug(f'Item ID: {item_id}')
            return True
        # self.save_state.emit()
        if not delete_data(self.table, del_ids):
            return False
        logger_setup.get_logger().info(f'Successfully deleted items from {self.table}')
        if parent_id:
            p_id = f'= {parent_id}'
        else:
            p_id = 'IS NULL'
            parent_id = 'NULL'
        filtered_model = QtS.QSqlQueryModel()
        filtered_model.setQuery(
            f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {p_id} AND {self.parent_row_header} >= {parent_row} ORDER BY {self.parent_row_header} ASC")
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
        """
        Maps a proxy index (TreeModel index) to the source model index (QSqlQueryModel or SQLiteTableModel index).
        The expand/collapse icon is only available on the first column, and the first column cannot be hidden without
        hiding the expand/collapse icon, so the columns are shuffled as follows:
        TreeModel (proxy model) columns:
        0: Name,
        1: Item ID,
        2: Parent ID,
        3: Parent Row;
        Source Model (QSqlQueryModel or SQLiteTableModel) columns:
        0: Item ID,
        1: Parent ID,
        2: Parent Row,
        3: Item Name;
        :param proxy_index: index of tree model (proxy model) to map to source model
        :return: the source model index corresponding to the given proxy index, or an invalid QModelIndex if the proxy
        index is not valid
        """
        if not proxy_index.isValid() or not self.source_model:
            return QtC.QModelIndex()
        if not isinstance(self.source_model, QtS.QSqlQueryModel | SQLiteTableModel):
            logger_setup.get_logger().critical(f'Data type error')
            logger_setup.get_logger().debug(f'Source model is not a QSqlQueryModel or SQLiteTableModel')
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
        """
        Maps a source index (QSqlQueryModel or SQLiteTableModel index) to the proxy model index (TreeModel index).
        The expand/collapse icon is only available on the first column, and the first column cannot be hidden without
        hiding the expand/collapse icon, so the columns are shuffled as follows:
        Source Model (QSqlQueryModel or SQLiteTableModel) columns:
        0: Item ID,
        1: Parent ID,
        2: Parent Row,
        3: Item Name;
        TreeModel (proxy model) columns:
        0: Name,
        1: Item ID,
        2: Parent ID,
        3: Parent Row;
        :param source_index: the source model index to map to the proxy model
        :return: index of the proxy model (TreeModel) corresponding to the given source index, or an invalid QModelIndex
        if the source index is not valid
        """
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

    def find_id_in_tree(self, item_id: int) -> TreeItem:
        """
        Find an item in the tree model by its unique ID. This method recursively searches through the tree items to find
        the item with the given ID.
        :param item_id: unique ID of the item to find
        :return: tree item with the given ID, or None if the item is not found
        """
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

    def find_id_source_row(self, item_id: int):
        """
        Find the row number in the source model for a given item ID. This is used to map the item ID to its row in the
        source model, which is necessary for operations like moving or deleting items.
        :param item_id: unique ID of the item to find in the source model
        :return: row number in the source model where the item with the given ID is located, or None if the item is not
        found
        """
        for row in range(self.source_model.rowCount()):
            record = self.source_model.record(row)
            if record.value(0) == item_id:
                return row
        return

    def flags(self, index: QtC.QModelIndex) -> QtC.Qt.ItemFlag:
        """
        Returns the item flags for the given index. This determines whether the item is editable, selectable, draggable,
        and droppable. All items are selectable, draggable, and droppable, and all but the created and modified
        timestamp columns are editable. ID columns should not be visible at all.
        :param index: index for which to get the item flags
        :return: item flags for the given index
        """
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
        """
        Returns the MIME types supported by this model for drag and drop operations.
        :return: List of MIME types supported by this model
        """
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes: list[QtC.QModelIndex]) -> QtC.QMimeData:
        """
        Creates a QMimeData object containing the data for the given indexes. This is used for drag and drop operations.
        Only the first column (item ID) is included in the MIME data, as it is the unique identifier for the item.
        :param indexes: list of QModelIndex objects to create MIME data for
        :return: MIME data object containing the item IDs for the given indexes
        """
        mimeData = QtC.QMimeData()
        encodedData = QtC.QByteArray()
        stream = QtC.QDataStream(encodedData, QtC.QIODevice.OpenModeFlag.WriteOnly)
        for index in indexes:
            if index.isValid() and index.column() == 0:
                item = self.getItem(index)
                stream.writeInt32(item.data(0))  # item ID
        mimeData.setData('application/x-qabstractitemmodeldatalist', encodedData)
        return mimeData

    def canDropMimeData(self, data: QtC.QMimeData, action: QtC.Qt.DropAction, row, column, parent) -> bool:
        """
        Checks if the model can accept the dropped MIME data. This is used to determine if the drop operation is valid.
        :param data: MIME data to check for drop validity
        :param action: Drop action performed (e.g., MoveAction)
        :param row: row where the item is dropped, not used in this implementation
        :param column: column where the item is dropped, not used in this implementation
        :param parent: parent index where the item is dropped, not used in this implementation
        :return: False if the action is IgnoreAction or if the data format is not recognized, True otherwise
        """
        if action == QtC.Qt.DropAction.IgnoreAction:
            return False
        if not data.hasFormat('application/x-qabstractitemmodeldatalist'):
            logger_setup.get_logger().critical(f'Error dropping item')
            logger_setup.get_logger().debug(f'Drop data format not recognized')
            return False
        return True

    def dropMimeData(self, data: QtC.QMimeData, action: QtC.Qt.DropAction, row: int, column: int,
                     parent: QtC.QModelIndex):
        """
        Handles the drop of MIME data into the model. This method processes the dropped data, updates the source model,
        and moves the items to the new parent and row. If the drop is successful, it emits the dataEdited signal to
        notify the view to rebuild the tree model.
        :param data: MIME data dropped into the model
        :param action: Drop actio performed (e.g., MoveAction)
        :param row: row where the item is dropped
        :param column: column where the item is dropped, not used in this implementation
        :param parent: parent index where the item is dropped
        :return:
        """
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
        encodedData = data.data('application/x-qabstractitemmodeldatalist')
        stream = QtC.QDataStream(encodedData, QtC.QIODevice.OpenModeFlag.ReadOnly)
        item_ids = []
        rows = []
        parentID = self.getItem(parent).data(0)
        if isinstance(parentID, int):
            p_id = f'= {parentID}'
        else:  # If the parent ID is not an integer
            p_id = 'IS NULL'
        create_savepoint('drop_mime_data')
        # self.save_state.emit()
        while not stream.atEnd():
            item_ids.append(stream.readInt32())
            if row == -1:
                # If the row is -1, the item is being moved to the end of the list
                self.source_model.setQuery(f"{self.base_query_sql} {self.sourceHeaders[1]} {p_id}")
                childCount = self.source_model.rowCount()
                row = childCount
            rows.append(row)
            row += 1
        if not item_ids:
            logger_setup.get_logger().debug(f'No items to move')
            rollback_savepoint('drop_mime_data')
            return False
        for move in range(len(item_ids)):
            self.source_model.setQuery(
                f"{self.base_query_sql} {self.id_header} is {item_ids[move]}")  # Only one record for each item ID
            oldParentID = self.source_model.record(0).value(1)  # Get the current parent ID
            if self.table == 'Aliquots' and parentID == oldParentID:
                logger_setup.get_logger().info(f"Cannot reorder top-level aliquots")
                rollback_savepoint('drop_mime_data')
                return False
            if not self.moveItem(item_ids[move], rows[move], p_id):
                logger_setup.get_logger().critical(f'Error moving item')
                logger_setup.get_logger().debug(f'Item: {item_ids[move]}, rows: {rows[move]}, parent_ID: {p_id}')
                rollback_savepoint('drop_mime_data')
                return False
        # All moves were successful
        self.source_model.setQuery(self.base_query)  # Reset the filter
        release_savepoint('drop_mime_data')
        # Emit signal so that the view can rebuild the tree model
        self.dataEdited.emit()
        return True

    def supportedDropActions(self):
        """
        Returns the drop actions supported by this model. This is used to determine what actions are allowed when
        dropping items into the model.
        :return: Drop actions supported by this model, which are CopyAction and MoveAction
        """
        return QtC.Qt.DropAction.CopyAction | QtC.Qt.DropAction.MoveAction

    def supportedDragActions(self):
        """
        Returns the drag actions supported by this model. This is used to determine what actions are allowed when
        dragging items from the model. There is no corresponding QtC.Qt.DragAction, so we return the drop actions.
        :return: Drag actions supported by this model, which are CopyAction and MoveAction
        """
        return QtC.Qt.DropAction.CopyAction | QtC.Qt.DropAction.MoveAction

    def headerData(self, section: int, orientation: QtC.Qt.Orientation, role: int = ...):
        """
        Returns the header data for the given section and orientation. This is used to display the column headers in the
        view. The headers are defined in the source model, and this method retrieves the appropriate header based on the
        section and orientation. If the role is not DisplayRole, it returns an empty QVariant.
        :param section: column index for which to get the header data
        :param orientation: header orientation (horizontal or vertical)
        :param role: role for the header data, such as DisplayRole
        :return: header data for the given section and orientation, or an empty QVariant if the role is not DisplayRole
        """
        if role != QtC.Qt.ItemDataRole.DisplayRole:
            return QtC.QVariant()
        if orientation == QtC.Qt.Orientation.Horizontal:
            return self.proxyHeaders[section]
        return QtC.QVariant()

    def top_node(self, item_ids: list) -> tuple:
        """
        Find the top parent ID and row for a list of item IDs. This method traverses the tree model to find the topmost
        parent that contains any of the given item IDs. It returns the top parent ID and the row number of that parent in
        the tree model.
        :param item_ids: list of unique item IDs
        :return: tuple containing the top parent ID and the row number of the top child in that parent
        """
        def walk_tree(parent_id, item_ids: list):
            if isinstance(parent_id, int):
                p_id = f'= {parent_id}'
            else:
                p_id = 'IS NULL'
            filtered_model = QtS.QSqlQueryModel()
            filtered_model.setQuery(
                f"SELECT * FROM {self.table} WHERE {self.parent_id_header} {p_id} ORDER BY {self.parent_row_header} ASC")
            childCount = filtered_model.rowCount()
            for child in range(childCount):
                child_id = filtered_model.record(child).value(0)
                parent_row = child
                if child_id in item_ids:
                    return parent_id, parent_row
                else:
                    walk_tree(child_id, item_ids)

        parent_id = 'Null'
        if len(item_ids) == 0:
            logger_setup.get_logger().debug(f'No item IDs provided, returning None')
            return None, None
        if '' in item_ids:
            logger_setup.get_logger().debug(f'Empty item ID found, referencing root. Returning None')
            return None, None
        (top_parent_id, top_parent_row) = walk_tree(parent_id, item_ids)
        return top_parent_id, top_parent_row


class CheckableTreeItem(TreeItem):
    """
    A tree item that can be checked or unchecked. This is used in the CheckableTreeModel to allow users to select
    multiple items in the tree. It inherits from TreeItem and adds a check state property to indicate whether the item
    is checked or not.
    """
    def __init__(self, record: QtS.QSqlRecord, parent: TreeItem = None):
        super().__init__(record, parent)
        self.checkState = QtC.Qt.CheckState.Unchecked

    def setCheckState(self, state: QtC.Qt.CheckState):
        """
        Set the check state of the item. This is used to mark the item as checked or unchecked in the tree view.
        :param state: CheckState to set for the item, such as Checked, Unchecked, or PartiallyChecked
        """
        self.checkState = state

    def getCheckState(self):
        """
        Get the check state of the item. This is used to retrieve the current check state of the item in the tree view.
        :return: CheckState of the item, such as Checked, Unchecked, or PartiallyChecked
        """
        return self.checkState


class CheckableTreeModel(TreeModel):
    """
    A tree model that supports checkable items. This model extends the TreeModel to allow items to be checked or
    unchecked in the tree view. It uses CheckableTreeItem to represent each item in the tree, which includes a check
    state property to indicate whether the item is checked or not. This model is used to display hierarchical data in a
    tree structure, where each item can be expanded or collapsed, and items can be selected by checking them.
    """
    def __init__(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel=QSqlTableModel(), parent=None):
        # database table
        super().__init__(source_model, parent)
        self.root_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.parent_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.child_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.item_ids = None
        self.many_to_many = None
        if self.source_model:
            # Check if a table model was set
            if isinstance(self.source_model, QSqlTableModel):
                if self.source_model.tableName() == '':
                    return
            elif isinstance(self.source_model, QSqlQueryModel):
                query_object = source_model.query()
                if query_object.lastQuery() == '':
                    return
            elif isinstance(self.source_model, SQLiteTableModel):
                if source_model.query_text == '':
                    return
            self.setSourceModel(self.source_model)

    def setSourceModel(self, source_model: QSqlTableModel | QSqlQueryModel | SQLiteTableModel):
        """
        Set the source model for the tree model. This method initializes the tree model with the given source model,
        retrieves the table name, and sets up the base query and filter for the model. It also clears any previous tree
        model data and sets up the root item, parent item, and child item as CheckableTreeItems for the tree structure.
        If the base query is an Aliquot view or from Ages, it will set the source model to a SQLiteTableModel to speed
        up building the tree. Otherwise, it will set the source model to a DisplayRoundedQueryModel.
        :param source_model: Populated QSqlTableModel, QSqlQueryModel, or SQLiteTableModel
        :return: Nothing if there is an error
        :param source_model:
        :return:
        """
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
            view_query = source_model.view_query
        if len(self.base_query) > 0:
            if ' WHERE ' in self.base_query:
                self.base_query_sql = f"{self.base_query} AND "
            else:
                self.base_query_sql = f"{self.base_query} WHERE "
        if (('FROM LimitedAliquots' in self.base_query or 'FROM Ages' in self.base_query) or
                isinstance(source_model, SQLiteTableModel)):
            if isinstance(source_model, SQLiteTableModel) and source_model.query_text == self.base_query:
                # If the source model is already a SQLiteTableModel with the same query, do not reset it
                self.source_model = source_model
            else:
                try:
                    self.source_model = SQLiteTableModel(query=self.base_query, view_query=view_query)
                except NameError:
                    self.source_model = SQLiteTableModel(query=self.base_query)
                if self.source_model.last_error:
                    logger_setup.get_logger().critical(f'Error displaying the selected table')
                    return
        else:
            self.source_model = DisplayRoundedQueryModel(db=self.db)
            self.source_model.setQuery(f'{self.base_query}')
        self.sourceHeaders = []
        self.proxyHeaders = []
        self.column_headers()
        self.header_variables()
        if self.root_item.childCount() > 0:
            logger_setup.get_logger().info('Clearing previous tree model...')
            self.root_item.clear()
        self.root_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.parent_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.child_item = CheckableTreeItem(QtS.QSqlRecord(), None)
        self.setup_model_data()

    def add_to_tree(self, parent: CheckableTreeItem):
        """
        Add child items with unique child IDs to the tree model under the specified parent item. This method iterates
        through the list of child IDs, finds the corresponding records in the source model, and creates
        CheckableTreeItem instances for each child. It appends these items to the parent item in the tree structure.
        If a child ID has children, it recursively calls itself to add those children as well.
        :param parent: CheckableTreeItem parent to add children to
        :return: None if there are no child IDs
        """
        if parent == self.root_item:
            for parent_id in (None, '', 'NULL'):
                child_ids = self.parent_to_children.get(parent_id, [])
                if child_ids:
                    break
        else:
            parent_id = parent.itemData.value(0)
            child_ids = self.parent_to_children.get(parent_id, [])
        if not child_ids:
            return
        # logger_setup.get_logger().info(f'Adding {len(child_ids)} children to the tree...')
        # logger_setup.get_logger().debug(f'Child IDs: {child_ids}')

        for child_id in child_ids:
            add_time = time.time()
            record = self.item_data[child_id]
            item = CheckableTreeItem(record, parent)
            parent.appendChild(item)
            # logger_setup.get_logger().debug(f'Added {child_id} to the tree')
            # logger_setup.get_logger().info(f'Added {record.value(3)} in {time.time() - add_time} seconds')
            self.add_to_tree(item)

    def data(self, index: QtC.QModelIndex = ..., role: QtC.Qt.ItemDataRole = ...):
        """
        Returns the data for the given index and role. This method is used to retrieve the data for each item in the tree
        model, including the check state for checkable items.
        :param index: QModelIndex for which to get the data
        :param role: role for the data, such as DisplayRole or CheckStateRole
        :return: CheckState of the item if the index is valid and the role is CheckStateRole, otherwise calls the base class
        """
        if not index.isValid():
            item = self.root_item
        else:
            item = self.getItem(index)
        if index.column() == 0 and role == QtC.Qt.ItemDataRole.CheckStateRole:
            return item.getCheckState()

        return super().data(index, role)

    def setData(self, index: QtC.QModelIndex, value: typing.Any, role: QtC.Qt.ItemDataRole = ...) -> bool:
        """
        Sets the data for the given index and role. This method is used to update the check state of checkable items in
        the tree model. If the index is valid and the column is the first column (the checkable item), it updates the
        check state of the item and emits the dataChanged signal to notify the view of the change. If the index is not
        valid or the column is not the first column, it calls the base class implementation to handle other data roles.
        :param index: QModelIndex for which to set the data
        :param value: value to set for the item, such as CheckState
        :param role: role for the data, such as DisplayRole or CheckStateRole
        :return: True if the data was successfully set, False otherwise
        """
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
        """
        Returns the item flags for the given index. This determines whether the item is checkable, editable, selectable,
        draggable, and droppable. Only the first column (the checkable item) is checkable. For other columns, it calls
        the base class implementation to get the default flags.
        :param index: QModelIndex for which to get the item flags
        :return: Item flags for the given index, which include ItemIsEnabled, ItemIsSelectable, ItemIsEditable,
        ItemIsUserCheckable, ItemIsDragEnabled, and ItemIsDropEnabled for the first column, or the default flags for other
        columns.
        """
        # name_col = name_column(self.table)
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        if index.column() == 0:
            # If the column is the name item, it is checkable
            return QtC.Qt.ItemFlag.ItemIsEnabled | QtC.Qt.ItemFlag.ItemIsSelectable | QtC.Qt.ItemFlag.ItemIsEditable | QtC.Qt.ItemFlag.ItemIsUserCheckable | QtC.Qt.ItemFlag.ItemIsDragEnabled | QtC.Qt.ItemFlag.ItemIsDropEnabled
        return super().flags(index)

    def clear_checks(self, parent: QtC.QModelIndex):
        """
        Clears the check state of all items in the tree model under the specified parent index. This method iterates
        through all rows under the parent index and sets the check state of each item to Unchecked. It also clears any
        checks recursively for child items.
        :param parent: QModelIndex of the parent item whose children should be unchecked, usually first called with
        QModelIndex() for the root item
        """
        for row in range(self.rowCount(parent)):
            name_index = self.index(row, 0, parent)
            self.setData(name_index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
            self.clear_checks(name_index)

    def check_checkable_tree(self, parent: QtC.QModelIndex, checked_items: list[int], partially_checked_items: list[int]):
        """
        Checks the checkable items in the tree model based on the provided lists of checked and partially checked IDs.
        This method iterates through all rows under the specified parent index and sets the check state of each item
        according to whether its ID is in the checked_items or partially_checked_items lists. It also recursively checks
        child items under the parent index.
        :param parent: QModelIndex of the parent item whose children should be unchecked, usually first called with
        QModelIndex() for the root item
        :param checked_items: list of item IDs that should be checked
        :param partially_checked_items: list of item IDs that should be partially checked
        :return:
        """
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
        """
        Traverses the checkable tree model and collects the IDs of checked and partially checked items. This method
        iterates through all rows under the specified parent index and checks the check state of each item. It collects
        the IDs of checked items and partially checked items, as well as their corresponding indices in the tree model.
        It also recursively traverses child items under the parent index to gather their checked and partially checked
        IDs and indices.
        :param parent: QModelIndex of the parent item whose children should be checked, usually first called with
        QModelIndex() for the root item
        :return: tuple containing lists of checked IDs, partially checked IDs, checked indices, and partially checked indices.
        """
        checked_ids = []
        partially_checked_ids = []
        checked_indices = []
        partially_checked_indices = []
        for row in range(self.rowCount(parent)):
            name_index = self.index(row, 0, parent)
            id_index = self.index(row, 1, parent)
            if self.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                checked_ids.append(self.data(id_index, QtC.Qt.ItemDataRole.DisplayRole))
                checked_indices.append(name_index)
            elif self.data(name_index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.PartiallyChecked:
                partially_checked_ids.append(self.data(id_index, QtC.Qt.ItemDataRole.DisplayRole))
                partially_checked_indices.append(name_index)
            child_checked_item, child_partially_checked_ids, child_checked_indices, child_partially_checked_indices = self.traverse_checkable_tree(name_index)
            checked_ids.extend(child_checked_item)
            partially_checked_ids.extend(child_partially_checked_ids)
            checked_indices.extend(child_checked_indices)
            partially_checked_indices.extend(child_partially_checked_indices)
        return checked_ids, partially_checked_ids, checked_indices, partially_checked_indices

    def update_other_table(self, other_table: str, other_ids: list[int]):
        """
        Collect the checked IDs and partially checked IDs from this table and update that field in another table.
        It calls the update_other_table_with_checks function to perform the update operation. This is useful for one-to-many
        relationships. The relationship must be one-to-one or one-to-many, so there should be only one checked ID. If
        there are partially checked IDs, no item has been selected to associate with all IDs in the other table, so do
        not update. If the relationship is many-to-many, use update_many_table instead.
        :param other_table: name of the other table to update with the checked IDs from this table (e.g. Samples)
        :param other_ids: list of IDs in the other table that correspond to the checked items in this tree model
        (e.g. list of SampleIDs)
        :return: True if the update was successful, False otherwise
        """
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return False
        checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = self.traverse_checkable_tree(
            QtC.QModelIndex())
        if partially_checked_ids:
            # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
            logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
            return True
        if len(checked_ids) > 1:
            # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
            logger_setup.get_logger().error(
                f'Multiple checked IDs given for {self.tableName()}. Select only one ID to update {other_table}.')
            logger_setup.get_logger().debug(
                f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
            return False
        if update_other_table_with_checks(self.table, checked_ids, partially_checked_ids, other_table, other_ids):
            return True
        else:
            return False

    def update_many_table(self, many_table: str, item_ids: list | None):
        """
        Updates many-to-many relationship with another table. This method is useful when editing joined views, like
        editing the Units associated with Samples.
        :param many_table: name of the many-to-many table to update (e.g. Samples_Units)
        :param item_ids: list of foreign IDs to update in the many-to-many table (e.g. SampleIDs)
        :return: True if the update was successful, False otherwise
        """
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs provided for updating many-to-many table {self.many_to_many}')
            return False
        checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = self.traverse_checkable_tree(QtC.QModelIndex())
        if update_many_table_with_checks(self.table, checked_ids, partially_checked_ids, many_table, item_ids):
            return True
        else:
            return False

class TreeSortFilterProxyModel(ReadableProxyModel):
    """
    A proxy model that filters and sorts items in a tree structure. This model extends QSortFilterProxyModel to
    provide custom filtering logic for tree items. It allows filtering based on a regular expression and supports
    recursive filtering for tree structures. The model can be used with a QTreeView to display hierarchical data
    while applying the specified filter criteria.
    """
    def __init__(self, parent=None, view: QtW.QTreeView =None):
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(True)  # Enables recursive filtering for tree structures
        self.view = view  # The view containing the model (e.g., QTreeView)
        self.filter_column = 0  # Default column to filter on
        self.filter_ids = []  # List of IDs to filter by

    def data(self, index: QtC.QModelIndex, role: QtC.Qt.ItemDataRole = ...):
        if role == Qt.ItemDataRole.ToolTipRole:
            # If the role is for tooltips, return the data from the source model
            tree_model, source_indexes = find_tree_model(self, [index])
            if tree_model and source_indexes:
                return tree_model.data(source_indexes[0], role)
        else:
            # For other roles, use the default implementation
            return super().data(index, role)

    def mapToSource(self, proxy_index):
        # Maps the proxy index to the source model index
        if not proxy_index.isValid():
            return QtC.QModelIndex()
        source_index = super().mapToSource(proxy_index)
        if source_index.isValid():
            pointed_index = self.sourceModel().index(source_index.row(), source_index.column(), source_index.parent())
            pointer = pointed_index.internalPointer()
            return pointed_index

    def filterAcceptsRow(self, source_row: int, source_parent: QtC.QModelIndex = QtC.QModelIndex()) -> bool:
        """
        Determines whether a row in the source model should be accepted or rejected based on the filter criteria.
        This method checks if the row matches the filter pattern and if the row's ID is in the list of filter IDs.
        :param source_row: row number in the source model to check for acceptance
        :param source_parent: parent index in the source model, used for hierarchical filtering
        :return: True if the row matches the filter criteria, False otherwise
        """
        # Override this method to implement custom filtering logic
        model = self.sourceModel()
        # If there is a list of filter IDs, check if the current row's ID matches any of them
        if self.filter_column and self.filter_ids:
            item_id = model.data(model.index(source_row, self.filter_column, source_parent),
                                 QtC.Qt.ItemDataRole.DisplayRole)
            if item_id not in self.filter_ids:
                return False
        # If no filter IDs are set or the current row's ID matches, proceed with the default filtering logic
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
            # logger_setup.get_logger().debug(f'Checking if {index.data()} matches filter {self.filterRegularExpression().pattern()}')
            # If the current column's data matches the filter, accept this row
            if index.data() is not None and self.filterRegularExpression().match(str(index.data())).hasMatch():
                # logger_setup.get_logger().debug(f'We have a match')
                return True
        # If no column matches, reject this row
        return False


# ---------------------------
#    Tree Methods
# ---------------------------

def get_selected_tree_ids(indexes: list[QtC.QModelIndex]):
    """
    Return the item IDs, parent IDs, and parent rows for the selected items in a tree model. This method iterates through
    the provided indexes, which are expected to be from a tree model, and retrieves the item ID, parent ID, and parent row
    for each selected item. It returns three lists: item IDs, parent IDs, and parent rows.
    :param indexes: List of QModelIndex objects representing the selected items in the tree model
    :return: Tuple containing three lists: item_ids, parent_ids, and parent_rows
    """
    item_ids = []
    parent_ids = []
    parent_rows = []
    for index in indexes:
        item_id = index.siblingAtColumn(1).data(QtC.Qt.ItemDataRole.DisplayRole)
        parent_id = index.siblingAtColumn(2).data(QtC.Qt.ItemDataRole.DisplayRole)
        parent_row = index.siblingAtColumn(3).data(QtC.Qt.ItemDataRole.DisplayRole)
        if item_id not in item_ids:
            item_ids.append(item_id)
        if parent_id not in parent_ids:
            parent_ids.append(parent_id)
        if parent_row not in parent_rows:
            parent_rows.append(parent_row)
    return item_ids, parent_ids, parent_rows

def find_tree_model(model, indexes: list[QtC.QModelIndex] | None):
    """
    Find the tree model and mapped indexes from a given model and indexes. This is useful when there may be layers of
    proxy models between the view and the actual tree model. The function checks if the provided model
    is an instance of CheckableTreeModel or TreeModel. If it is, it returns the model and the indexes as they are.
    If the model is a proxy model, it attempts to retrieve the source model and map the indexes to the source model.
    Indexes may be none if there are no indexes to map, in which case it returns the model and an empty list.
    :param model: tree model or proxy model from which to find the tree model
    :param indexes: list of QModelIndex objects to map to the source model
    :return: tuple containing the tree model and the mapped indexes, or None if no tree model is found
    """
    # Dig down through any proxy models to find the tree model and retrieve the model and mapped indexes
    if isinstance(model, CheckableTreeModel | TreeModel):
        tree_model = model
        tree_indexes = indexes
        return tree_model, tree_indexes
    else:
        try:
            source_model = model.sourceModel()
            source_indexes = []
            if indexes:
                for index in indexes:
                    # Map the index to the index in the source model
                    source_index = model.mapToSource(index)
                    # Use the index method of the source model to populate the internal pointer if applicable
                    pointed_index = source_model.index(source_index.row(), source_index.column(), source_index.parent())
                    if not pointed_index.isValid():
                        pointed_index = QtC.QModelIndex()
                    source_indexes.append(pointed_index)
            else:
                source_indexes = indexes
            tree_model, tree_indexes = find_tree_model(source_model, source_indexes)
            return tree_model, tree_indexes
        except AttributeError:
            try:
                source_model = model.source_model
                if indexes:
                    source_indexes = [model.mapToSource(index) for index in indexes]
                else:
                    source_indexes = indexes
                tree_model, tree_indexes = find_tree_model(source_model, source_indexes)
            except AttributeError:
                return None, None


# ---------------------------
#    Widget Classes
# ---------------------------

class EditingTextEdit(QtW.QTextEdit):
    """
    A QTextEdit subclass that emits a signal when editing is finished. This is useful for detecting when the user has
    finished editing the text in the QTextEdit, such as when they click outside of it or press Enter. The signal is
    not emitted when the application loses focus, to avoid incomplete edits being processed.
    """
    editingFinished = QtC.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._isApplicationFocused = True
        QtW.QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtC.QEvent.Type.ApplicationDeactivate:
            self._isApplicationFocused = False
        elif event.type() == QtC.QEvent.Type.ApplicationActivate:
            self._isApplicationFocused = True
        return super().eventFilter(obj, event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self._isApplicationFocused:
            # Only emit if the application is focused, not if the whole application has lost focus
            self.editingFinished.emit()

class FocusGroupBox(QGroupBox):
    """
    A QGroupBox subclass that emits a signal when it loses focus. This is useful for detecting when the user has
    clicked outside the group box or switched focus to another widget. Some data require validation to ensure that
    values have units set, etc. Only once editing within the group box is finished should validation and errors be
    processed. This class also tracks whether any child widgets have been edited to prevent unnecessary updates when
    the group box loses focus without any changes.
    """
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
        """
        Reset the edited state of the group box and reconnect child signals. This is useful when the changes have been
        processed and the group box is ready for new edits.
        :return:
        """
        self.edited = False
        self.connect_child_signals()

    def connect_child_signals(self):
        """
        Connect signals for child widgets to track changes. This method iterates through all child widgets of the group
        box and connects their edit signals to the set_edited method. It also stores the initial values of the child widgets
        to compare against later. This allows the group box to detect if any child widget has been edited, and thus
        whether the group box itself has been edited. The initial values are stored in a list of pairs, where each pair
        contains the child widget and its initial value. The signals are disconnected first to avoid duplicate connections.
        This is useful for ensuring that the group box can accurately track changes made to its child widgets.
        Currently supports QLineEdit, QComboBox, CheckableComboBox, CheckableTreeCombobox, and QCheckBox.
        :return:
        """
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
        """
        Disconnect signals for child widgets to prevent memory leaks and unwanted behavior. This method iterates through
        all child widgets of the group box and disconnects their signals that were connected in connect_child_signals.
        It also removes the event filter from each child widget.
        :return:
        """
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
                try:
                    child.add_triggered.disconnect()
                except TypeError:
                    pass
                try:
                    child.edit_triggered.disconnect()
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
        """
        Set the edited state of the group box based on the child's current value compared to its initial value. This method
        checks if the current value of the child widget differs from its initial value stored in self.initial_values. If
        the values differ, it sets the edited state of the group box to True and logs the change. This is useful for
        tracking changes made to the child widgets and determining if the group box needs to be updated. The method also
        handles different types of child widgets, including QLineEdit, CheckableComboBox, CheckableTreeCombobox,
        :param child:
        :return:
        """
        if not isinstance(child, QtW.QWidget):
            if isinstance(child, str) and isinstance(self.sender(), CheckableComboBox):
                child = self.sender().lineEdit()
            else:
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
        elif isinstance(child, CheckableComboBox | CheckableTreeCombobox):
            if child.currentText() != initial_value:
                self.edited = True
        elif isinstance(child, QtW.QComboBox):
            if child.currentIndex() != initial_value:
                self.edited = True
        elif isinstance(child, QtW.QCheckBox):
            if child.isChecked() != initial_value:
                self.edited = True

    def eventFilter(self, obj, event):
        """
        Event filter to set a delay when focus is lost to allow other widgets to process their focus and edit events.
        :param obj:
        :param event:
        :return:
        """
        if event.type() == QtC.QEvent.Type.FocusOut:
            self.focus_lost_timer.start(100)
        return super().eventFilter(obj, event)

    def check_focus_state(self, child: QtW.QWidget=None):
        """
        Check if the group box or any of its children has focus. If not, emit the focusLost signal. This method is called
        when the focus lost timer times out, indicating that the group box has lost focus. It checks if any child widget
        has focus. If no child has focus, it emits the focusLost signal to notify that the group box has lost focus.
        If a specific child is provided, it checks that child's focus state instead.
        :param child: widget within the group box to check the focus state of, if None checks all children
        :return:
        """
        if child is not None:
            # If a specific child is provided, check its focus state
            has_focus = child.hasFocus()
        has_focus = self.any_child_has_focus()
        if not has_focus:
            logger_setup.get_logger().info(f'{self.objectName()} has lost focus')
            if self.edited:
                logger_setup.get_logger().info(f'{self.objectName()} was edited and needs to be updated')
                self.focusLost.emit()

    def any_child_has_focus(self):
        """
        Check if any child widget of the group box has focus. This method iterates through all child widgets of the group
        box and checks if any of them has focus. If at least one child has focus, it returns True; otherwise, it returns
        False. This is useful for determining if the group box itself has focus or if any of its child widgets are being
        edited. It helps to avoid unnecessary signals when working within a group box.
        :return: True if any child has focus, False otherwise
        """
        for child in self.findChildren(QtW.QWidget):
            if child.hasFocus():
                return True
        return False

class CustomDragTabBar(QtW.QTabBar):
    """
    A custom QTabBar that allows for drag-and-drop reordering of tabs and maintains a list of permanent tabs.
    This class extends QTabBar to provide functionality for dragging tabs, reordering them, and ensuring that certain
    tabs remain in a fixed position (permanent tabs). It also provides methods to update the list of permanent tabs
    and to correct the order of tabs after a drag-and-drop operation. The mouseReleaseEvent is overridden to ensure
    that the permanent tabs are always in the correct order after a drag-and-drop operation.
    """
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

    def update_permanent_tabs(self, names: list[str]):
        """
        Update the list of permanent tabs. This method is used to set or update the names of the tabs that should
        remain in a fixed position (permanent tabs) in the tab bar. It can be called to change the permanent tabs
        dynamically, for example, when the user changes the configuration of the application or when new tabs are added.
        :param names: list of names of the tabs that should be permanent, which will not be closable or movable
        :return:
        """
        self.permanent_tabs = names

    def mouseReleaseEvent(self, event):
        """
        Handle the mouse release event to ensure that permanent tabs are always in the correct order after a drag-and-drop operation.
        :param event:
        :return:
        """
        # Move the permanent tabs to the left side of the tab bar
        super().mouseReleaseEvent(event)
        if self.permanent_tabs:
            self.correct_tab_order()

    def correct_tab_order(self):
        """
        Correct the order of permanent tabs in the tab bar. This method checks the current order of tabs in the tab bar
        and ensures that the permanent tabs are in the correct positions. If a permanent tab is not in the correct position,
        it moves it to the correct position. This is useful after a drag-and-drop operation to ensure that the permanent
        tabs remain in their designated positions.
        :return:
        """
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
    """
    Custom QTabWidget that allows for some permanent tabs that cannot be closed or moved, but allows other tabs to be
    created, moved, and closed.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_tabs = []
        self.tabBar = CustomDragTabBar(self.permanent_tabs)
        self.setTabBar(self.tabBar)
        self.setTabsClosable(True)
        self.setMovable(True)

    def set_permanent_tabs(self, names: list[str]):
        """
        Set the list of permanent tabs that should not be closable or movable. This method updates the list of permanent
        tabs in the tab widget. Permanent tabs are those that should always remain in the tab bar and cannot be closed
        or moved by the user.
        :param names: list of names of the tabs that should be permanent, which will not be closable or movable
        :return:
        """
        self.permanent_tabs = names
        self.tabBar.update_permanent_tabs(self.permanent_tabs)
        self.update_close_buttons()

    def update_close_buttons(self):
        """
        Update the close buttons for the tabs in the tab widget. This method iterates through all tabs and sets the
        close buttons for each tab based on whether the tab is a permanent tab or not. Permanent tabs will not have
        close buttons, while other tabs will have close buttons that allow them to be closed by the user.
        :return:
        """
        for index in range(self.count()):
            if self.tabText(index) in self.permanent_tabs:
                self.tabBar.setTabButton(index, QtW.QTabBar.ButtonPosition.LeftSide, None)
                self.tabBar.setTabButton(index, QtW.QTabBar.ButtonPosition.RightSide, None)
        # self.setTabsClosable(True)
        # self.setMovable(True)

    def addTab(self, widget: QtW.QWidget, name: str):
        """
        Add a new tab to the tab widget with the specified widget and name. If a tab with the same name already exists,
        it will set focus to that tab instead of creating a new one. This prevents duplicate tabs with the same name.
        :param widget: QWidget to be added as a tab
        :param name: Name of the tab to be added
        :return:
        """
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

    def insertTab(self, index: int, widget: QtW.QWidget, name: str):
        """
        Insert a new tab at the specified index with the given widget and name. If a tab with the same name already
        exists, it will set focus to that tab instead of creating a new one. This prevents duplicate tabs with the same name.
        :param index: Position at which to insert the new tab
        :param widget: QWidget to be added as a tab
        :param name: Name of the tab to be added
        :return:
        """
        for i in range(self.count()):
            if self.tabText(i) == name:
                self.setCurrentIndex(i)
                return
        super().insertTab(index, widget, name)
        self.update_close_buttons()
        self.setCurrentIndex(index)

    def removeTab(self, index: int):
        """
        Remove the tab at the specified index. If the tab being removed is a permanent tab, it will not be removed.
        :param index: Position at which to remove the tab
        :return:
        """
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
    """
    A dialog that allows the user to input text with a completer. This dialog contains a combo box with a completer
    that provides suggestions based on a list of strings. The user can type in the combo box, and the completer will
    suggest completions based on the input.
    """
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
    """
    A QListView subclass that allows for reordering items via drag-and-drop. This class extends QListView to provide
    functionality for dragging and dropping items to reorder them within the list. It sets the default drop action to
    MoveAction and enables drag-and-drop mode. The startDrag method is overridden to prevent dragging the permanent header,
    which is always at the top of the list. The dropEvent method is overridden to handle dropping items between other items
    while preventing drops before the permanent header or on an item.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDefaultDropAction(QtC.Qt.DropAction.MoveAction)
        self.setDragDropMode(QtW.QListView.DragDropMode.DragDrop)
        self.setDragEnabled(True)

    def startDrag(self, action: QtC.Qt.DropAction):
        """
        Start the drag operation for the selected item. This method is called when the user starts dragging an item
        from the list view. It checks if the current index is valid and if the item is not the permanent header.
        :param action: DropAction to be used for the drag operation because there is no DragAction
        :return:
        """
        index = self.currentIndex()
        # The permanent header will always be at the top, so this works even with multiple selection.
        if index.isValid():
            # Do not move the permanent header
            if index.data().replace(' ','') == self.model().sourceModel().permanent_header:
                return 
            super().startDrag(action)

    def dropEvent(self, event):
        """
        Handle the drop event for the list view. This method is called when the user drops an item onto the list view.
        It checks if the drop is valid, ensuring that the item is not being dropped before the permanent header or on an item.
        :param event:
        :return:
        """
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
    """
    A proxy model that filters and sorts columns in a list. This model extends QSortFilterProxyModel to display headers
    in the list as user-readable strings instead of raw database column names.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def data(self, index: QtC.QModelIndex, role: int = ...):
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            header = super().data(index, role)
            readable_header = get_readable_header(header)
            return readable_header
        return super().data(index, role)

class ColumnItemModel(QtG.QStandardItemModel):
    """
    A model that represents a list of columns with checkable items. This model extends QStandardItemModel to provide
    functionality for displaying a list of columns with checkboxes. It allows users to select which columns should be
    displayed in a view. The model can be used with a QTreeView or QListView to show the columns as checkable items.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.permanent_header = ''

    def set_permanent_header(self, header: str):
        """
        Set the permanent header that should always be checked. This header will not be allowed to be unchecked by the user.
        :param header: name of the header that should always be checked
        :return:
        """
        # Set the header that should always be checked, the name or display column
        self.permanent_header = header

    def data(self, index, role: int = ...):
        """
        Return the data for the given index and role. This method overrides the default data method to provide
        custom behavior for the check state role. If the role is CheckStateRole, it checks if the item is the permanent
        header and returns Checked if it is, otherwise it calls the superclass method to get the default behavior.
        :param index:
        :param role:
        :return:
        """
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtC.Qt.ItemDataRole.DisplayRole) == self.permanent_header:
                return QtC.Qt.CheckState.Checked
            else:
                return super().data(index, role)
        return super().data(index, role)

    def setData(self, index, value, role: int = ...):
        """
        Set the data for the given index and role. This method overrides the default setData method to provide
        custom behavior for the check state role. If the role is CheckStateRole and the item is the permanent header,
        it prevents the user from unchecking it by returning False. Otherwise, it calls the superclass method to set the data.
        :param index:
        :param value:
        :param role:
        :return:
        """
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtC.Qt.ItemDataRole.DisplayRole) == self.permanent_header and value == QtC.Qt.CheckState.Unchecked:
                return False
        return super().setData(index, value, role)

class CheckableComboBox(QtW.QComboBox):
    """
    A QComboBox subclass that allows for checkable items in the dropdown list. This class extends QComboBox to provide
    functionality for displaying a list of items with checkboxes. It allows users to select multiple items from the
    dropdown list by checking the checkboxes next to each item. Closing the dropdown will emit a signal similar to editing
    finished that can be connected to a slot for further processing. A proxy model filter allows the user can search for
    items by typing in the line edit. The view supports a context menu for editing, adding, and deleting items.
    Setting single_click to True will upon click uncheck all items except the one clicked, forcing the user to select
    only one item at a time.
    Setting not_null to True will prevent the user from unchecking all items, ensuring that at least one item is always selected.
    """
    closing = QtC.pyqtSignal()
    edit_triggered = QtC.pyqtSignal(QtW.QComboBox)
    add_triggered = QtC.pyqtSignal(QtW.QComboBox)
    delete_triggered = QtC.pyqtSignal(QtW.QComboBox)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setPlaceholderText("Search")
        self.lineEdit().setReadOnly(False)
        self.model_modifiable = False
        self.single_click = False
        self.not_null = False
        self.typing = False
        self.proxy_model = None
        # self.tableView = QtW.QTableView()
        # self.setView(self.tableView)
        self.setSizeAdjustPolicy(QtW.QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.context_menu = False
        self.name_col = None
        self.table = ''
        self.popup_shown = False

        self.view().setFocusProxy(self.lineEdit())
        self.view().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.lineEdit().textEdited.connect(self.update_filter)
        self.lineEdit().textChanged.connect(self.le_text_changed)
        self.view().viewport().installEventFilter(self)
        self.lineEdit().installEventFilter(self)

    def le_text_changed(self):
        """
        Handle text changes in the line edit. This method is called whenever the text in the line edit is changed while
        not typing to make sure that it reflects the current state of the tree view.
        :return:
        """
        # print(f'{self.objectName()} line edit text changed: {self.lineEdit().text()}')
        if not self.typing:
            self.update_line_edit()

    def start_typing(self):
        """
        Start typing in the line edit, which will grab the keyboard focus and allow the user to type in the search box.
        :return:
        """
        self.typing = True
        self.lineEdit().grabKeyboard()

    def stop_typing(self):
        """
        Stop typing in the line edit, which will release the keyboard focus and clear the search filter.
        :return:
        """
        self.typing = False
        self.lineEdit().releaseKeyboard()
        self.proxy_model.setFilterRegularExpression('')

    def update_line_edit(self):
        """
        Update the line edit text with the names of the checked items. This method retrieves the IDs of the checked items
        from the model and converts them to names using the get_name_from_id function. The names are then joined into a
        colon-separated string and set as the text of the line edit. This is useful for displaying the selected items
        in the line edit of the combo box.
        :return:
        """
        checked_ids = []
        checked_names = []
        try:
            checked_ids = self.model().checked_ids
        except AttributeError:
            # If the model does not have a list of checked ids, get checked state of each row
            if self.model().columnCount() > 1:
                for row in range(self.model().rowCount()):
                    index = self.model().index(row, 0)
                    if self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                        checked_id = self.model().data(index, QtC.Qt.ItemDataRole.UserRole)
                        if checked_id is not None and checked_id not in checked_ids:
                            checked_ids.append(checked_id)
            else:
                # If the model has only one column, assume it is a list of names
                for row in range(self.model().rowCount()):
                    index = self.model().index(row, 0)
                    if self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole) == QtC.Qt.CheckState.Checked:
                        checked_name = self.model().data(index, QtC.Qt.ItemDataRole.DisplayRole)
                        if checked_name is not None and checked_name not in checked_names:
                            checked_names.append(checked_name)
        for id in checked_ids:
            checked_names.append(get_name_from_id(self.table, id))
        text = '; '.join(checked_names)
        self.set_line_edit_text(text)

    def set_line_edit_text(self, text: str):
        """
        Set the text of the line edit to the given text. This method is used to check if the user is typing in the line edit
        and only update the text if they are not currently typing.
        :param text: string to set as the text of the line edit
        :return:
        """
        if not self.typing:
            self.lineEdit().setText(text)

    def setCurrentText(self, text: str):
        """
        Set the current text of the combo box to the given text. The text is only set if the user is not currently typing.
        :param text: String to set as the current text of the combo box
        :return:
        """
        if not self.typing:
            super().setCurrentText(text)

    def setCurrentIndex(self, index: int):
        """
        Set the current index of the combo box to the given index. The index is only set if the user is not currently typing.
        :param index: row index to set as the current index of the combo box
        :return:
        """
        if not self.typing:
            super().setCurrentIndex(index)

    def model(self):
        """
        Get the model of the combo box. If a proxy model is set, it returns the source model of the proxy model.
        :return: checkable model
        """
        if self.proxy_model:
            return self.proxy_model.sourceModel()
        else:
            return super().model()

    def setModel(self, model: CheckableSqlTableModel | CheckableSqlQueryModel | SampleAgeTableModel | QtC.QSortFilterProxyModel):
        """
        Set the model for the combo box. If a proxy model is provided, it sets the source model of the proxy model.
        :param model: checkable model or proxy model
        :return:
        """
        start_set_model_time = time.time()
        if isinstance(model, QtC.QSortFilterProxyModel):
            self.proxy_model = model
            model = model.sourceModel()
        else:
            self.proxy_model = QtC.QSortFilterProxyModel()
            self.proxy_model.setSourceModel(model)
        self.proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.table = model.tableName()
        super().setModel(self.proxy_model)

        column = model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
        if isinstance(column, int):
            self.table = None
            self.name_col = None
            return
        self.name_col = get_name_column(get_view_from_table(self.table))
        if self.name_col:
            self.proxy_model.setFilterKeyColumn(self.name_col)
            show_column(self, self.name_col)
        self.view().setMinimumWidth(self.view().sizeHint().width())
        logger_setup.get_logger().debug(f'Set model for {self.table} combo box in {time.time() - start_set_model_time:.2f} seconds')

    def update_filter(self, text: str):
        """
        Update the filter of the proxy model based on the text entered in the line edit. This method is called whenever
        the text in the line edit is edited by typing. It sets the filter regular expression of the proxy model
        to match (case-insensitive) the text entered by the user.
        :param text: string to filter the items in the combo box
        :return:
        """
        self.start_typing()
        # logger_setup.get_logger().debug(f'Setting filter to: {text}')
        search_expression = QtC.QRegularExpression(text,
                                                   options=QtC.QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setFilterRegularExpression(search_expression)
        self.lineEdit().setText(text)
        self.showPopup()

    def enable_context_menu(self, show_context_menu: bool):
        """
        Enable or disable the context menu for the combo box. If show_context_menu is True and the model is modifiable,
        it sets the context menu policy to CustomContextMenu and connects the customContextMenuRequested signal to
        the contextMenuEvent method. If show_context_menu is False or the model is not modifiable, it disables the context menu.
        :param show_context_menu:
        :return:
        """
        self.context_menu = show_context_menu
        if self.context_menu and self.model_modifiable:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            # self.customContextMenuRequested.connect(self.contextMenuEvent)
        else:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.NoContextMenu)

    def contextMenuEvent(self, event):
        """
        Handle the context menu event for the combo box. This method is called when the user right-clicks on the combo box.
        It creates a context menu with options to edit, add, clear all checks, select all, and delete items based on the
        current table of the combo box. Actions are processed based on the user's selection in the context menu and
        emit signals for editing, adding, and deleting items to be handled by the parent widget.
        :param event:
        :return:
        """
        menu = TreeContextMenu()
        if self.table == '"References"':
            table = 'References'
        else:
            table = self.table
        if self.table in ('Samples', 'Aliquots', 'Spots', 'UPbAnalyses') and self.model().rowCount() !=0:
            edit_action = menu.addAction(f"Edit {TxM.add_spaces_camel(table)}")
            add_action = None
            clear_all_action = menu.addAction("Clear All Checks")
            select_all_action = menu.addAction("Check All")
            delete_action = menu.addAction(f"Delete {TxM.add_spaces_camel(table)}")
        elif self.table in ('Samples', 'Aliquots', 'Spots', 'UPbAnalyses'):
            edit_action = None
            add_action = None
            clear_all_action = None
            select_all_action = None
            delete_action = None
        elif self.model().rowCount() !=0:
            edit_action = menu.addAction(f"Edit {TxM.add_spaces_camel(table)}")
            add_action = menu.addAction(f"Add {TxM.add_spaces_camel(table)}")
            clear_all_action = menu.addAction("Clear All Checks")
            select_all_action = menu.addAction("Check All")
            delete_action = menu.addAction(f"Delete checked {TxM.add_spaces_camel(table)}")
        else:
            edit_action = None
            add_action = menu.addAction(f"Add {TxM.add_spaces_camel(table)}")
            clear_all_action = None
            select_all_action = None
            delete_action = None
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == edit_action:
            self.edit_triggered.emit(self)
        elif action == add_action:
            self.add_triggered.emit(self)
        elif action == clear_all_action:
            self.clear_all_checks()
        elif action == select_all_action:
            self.select_all()
        elif action == delete_action:
            self.delete_triggered.emit(self)

    def set_single_click(self, single_click: bool):
        """
        Set whether the combo box should allow single-click selection of items. If single_click is True, clicking on an
        item will uncheck all other items and select only the clicked item. If single_click is False, clicking on an
        item will toggle its check state without affecting other items.
        :param single_click: True or False
        :return:
        """
        self.single_click = single_click

    def clear_all_checks(self):
        """
        Clear all checks in the combo box. This method iterates through all rows in the model and sets the check state
        of each item to Unchecked. It also clears the text in the line edit to indicate that no items are selected.
        :return:
        """
        for row in range(self.model().rowCount()):
            index = self.model().index(row, self.name_col)
            self.model().setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
        self.lineEdit().setText("")
        logger_setup.get_logger().info(f'Cleared all checks in {self.table} combo box')

    def select_all(self):
        """
        Set all items in the combo box to Checked. This method iterates through all rows in the model and sets
        the check state of each item to Checked. It also updates the line edit text to show the names of all checked items.
        :return:
        """
        for row in range(self.model().rowCount()):
            index = self.model().index(row, self.name_col)
            self.model().setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
        checked_ids = self.model().checked_ids
        checked_names = []
        for id in checked_ids:
            checked_names.append(get_name_from_id(self.table, id))
        text = '; '.join(checked_names)
        self.set_line_edit_text(text)
        logger_setup.get_logger().info(f'Selected all items in {self.table} combo box')

    def showPopup(self):
        """
        Show the popup for the combo box. This method is called to display the dropdown list of items in the combo box.
        The popup is shown only if there are items in the model. It sets the width of the view to fit the width of the
        combo box or the size hint for the name column, whichever is larger. It also sets the height of the view to
        fit the size hint of the view. The popup_shown flag is set to True to indicate that the popup is currently shown.
        :return:
        """
        if self.proxy_model.rowCount() == 0:
            return
        if self.width() > self.view().sizeHintForColumn(self.name_col):
            self.view().setFixedWidth(self.width())
            # self.view().setColumnWidth(self.name_col, self.width())
        else:
            self.view().setFixedWidth(self.view().sizeHintForColumn(self.name_col))
        self.view().setFixedHeight(self.view().sizeHint().height())
        super().showPopup()
        self.popup_shown = True
        logger_setup.get_logger().debug(f'Popup shown in {self.table} combo box')

    def hidePopup(self):
        """
        Hide the popup for the combo box. This method is called to hide the dropdown view in the combo box only if it
        is shown. It checks if the user has clicked outside the view or if the single_click mode is enabled to keep the
        popup open when selecting multiple items is allowed. If the popup is shown, it hides the popup and emits the
        closing signal.
        :return:
        """
        if self.popup_shown:
            if not self.single_click:
                # Check if the cursor is still over the view, if so, do not hide the popup
                if self.view().rect().contains(self.view().mapFromGlobal(QtG.QCursor.pos())):
                    return
            super().hidePopup()
            self.closing.emit()
            self.popup_shown = False
            self.stop_typing()

    def eventFilter(self, obj, event):
        """
        Filter events for the combo box and its view. This method is used to handle mouse button press events on the
        combo box and its view. It checks if the event is a mouse button press on the line edit or the view's viewport.
        If the event is a right-click on the line edit, it shows the context menu if it is enabled. If the event is a
        left-click on the view's viewport, it checks if single_click mode is enabled. If it is, it clears all checks
        and sets the current index to the clicked item, updating the line edit text accordingly. If the event is a right-click
        on the view's viewport, it shows the context menu if it is enabled. Other events are passed to the superclass.
        :param obj:
        :param event:
        :return:
        """
        if obj == self.lineEdit():
            if event.type() == QtC.QEvent.Type.MouseButtonPress and event.button() == QtC.Qt.MouseButton.RightButton:
                if self.context_menu:
                    self.stop_typing()
                    self.contextMenuEvent(event)
                    return True
            return super().eventFilter(obj, event)

        if obj == self.view().viewport():
            if self.proxy_model:
                proxy_index = self.view().currentIndex()
                source_index = self.proxy_model.mapToSource(proxy_index)
            else:
                source_index = self.view().currentIndex()
            if event.type() == QtC.QEvent.Type.MouseButtonPress and event.button() == QtC.Qt.MouseButton.LeftButton:
                if self.single_click:
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
                        self.stop_typing()
                        self.view().setCurrentIndex(QtC.QModelIndex())
                        source_index = QtC.QModelIndex()
                    self.clear_all_checks()
                    self.model().setData(source_index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                    self.stop_typing()
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
                    self.stop_typing()
                    self.update_line_edit()
                    self.showPopup()
                    return True
            elif event.type() == QtC.QEvent.Type.MouseButtonPress and event.button() == QtC.Qt.MouseButton.RightButton:
                if self.context_menu:
                    self.stop_typing()
                    self.contextMenuEvent(event)
                    return True
            return super().eventFilter(obj, event)

        return super().eventFilter(obj, event)

class SearchableComboBox(QtW.QComboBox):
    """
    A QComboBox subclass that allows for searching items in the dropdown list. This class extends QComboBox to provide
    functionality for searching items in the dropdown list by typing in the line edit. It uses a completer to filter
    the items containing the text entered by the user. The selection_changed signal is emitted whenever the
    selection in the combo box changes, allowing for custom handling of selection changes.
    """
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
        """
        Add a single item to the combo box. This method overrides the default addItem method to set the default text
        to blank after adding the item. This ensures that the combo box does not display 'None' as a default value.
        :param text: text to be added as an item to the combo box
        :return:
        """
        super().addItem(text)
        # Set the default text to blank
        self.lineEdit().setText(None)

    def addItems(self, texts: list[str]):
        """
        Add multiple items to the combo box. This method overrides the default addItems method to set the default text
        to blank after adding the items. This ensures that the combo box does not display 'None' as a default value.
        :param texts: list of text strings to be added as items to the combo box
        :return:
        """
        super().addItems(texts)
        # Set the default text to blank
        self.lineEdit().setText(None)

    def validate_input(self):
        """
        Validate the input in the line edit. This method checks if the text entered in the line edit matches any of
        the items in the combo box. If the text does not match any item, it sets the text to None and resets the current
        index to -1. If the text matches an item, it sets the current index to that item. This ensures that the combo box
        does not display 'None' as a default value and only shows valid selections.
        :return:
        """
        text = self.lineEdit().text()
        if self.findText(text) == -1 or text == 'None':
            self.lineEdit().setText(None)
            self.setCurrentIndex(-1)
        elif text not in [self.itemText(i) for i in range(self.count())]:
            # The text does not match anything in the combo box
            # Reset the text to blank
            self.lineEdit().setText(None)
            self.setCurrentIndex(-1)

class CheckableTreeView(QtW.QTreeView):
    """
    A QTreeView subclass that allows for checkable items in a tree structure. This class extends QTreeView to allows users
    to select multiple items. The model can be set to a CheckableTreeModel, which provides the data for the tree.
    """

    def __init__(self):
        super().__init__()
        self.expandAll()
        self.hideColumn(1)  # don't show ID column
        self.hideColumn(2)  # don't show parent ID column
        self.hideColumn(3)  # don't show parent row column
        self.setSortingEnabled(False)
        self.setHeaderHidden(False)

        self.header().setSectionResizeMode(QtW.QHeaderView.ResizeMode.ResizeToContents)
        # self.clicked.connect(self.toggle_check_state)

    def setModel(self, model: CheckableTreeModel | QSortFilterProxyModel):
        """
        Set the model for the tree view. This method overrides the default setModel method to ensure that the model
        is a CheckableTreeModel or a proxy model wrapping a CheckableTreeModel.
        :param model: CheckableTreeModel to be set as the model for the tree view
        :return:
        """
        if isinstance(model, QSortFilterProxyModel):
            if not isinstance(model.sourceModel(), CheckableTreeModel):
                raise TypeError("Model must be a CheckableTreeModel or a QSortFilterProxyModel wrapping a CheckableTreeModel")
        super().setModel(model)

    def resizeColumnsToContents(self):
        """
        Resize all columns in the tree view to fit their contents. This method iterates through all columns in the model
        and resizes each column to fit the contents of the items in that column. This is useful for ensuring that all
        columns are displayed correctly and that the text in each column is fully visible.
        :return:
        """
        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)

    def toggle_check_state(self, index: QtC.QModelIndex):
        """
        Toggle the check state of the item at the given index. This method checks if the model is set and if the index
        is valid and user-checkable. If so, it toggles the check state of the item between Checked and Unchecked.
        :param index: QModelIndex to be checked or unchecked
        :return:
        """
        if self.model():
            if index.isValid() and QtC.Qt.ItemFlag.ItemIsUserCheckable in self.model().flags(index):
                current_state = self.model().data(index, QtC.Qt.ItemDataRole.CheckStateRole)
                new_state = QtC.Qt.CheckState.Unchecked if current_state == QtC.Qt.CheckState.Checked else QtC.Qt.CheckState.Checked
                self.model().setData(index, new_state, QtC.Qt.ItemDataRole.CheckStateRole)

    def expand_all_checked(self):
        """
        Expand all parents of checked items in the tree view. This method traverses the tree model and expands all
        parent items of checked and partially checked items. It ensures that all parents of checked items are visible
        in the tree view, making it easier for users to see the hierarchy of checked items.
        :return:
        """
        tree_model, indexes = find_tree_model(self.model(), [])
        if not tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = tree_model.traverse_checkable_tree(QtC.QModelIndex())
        if isinstance(self.model(), QSortFilterProxyModel):
            checked_indices = [self.model().mapFromSource(index) for index in checked_indices]
            partially_checked_indices = [self.model().mapFromSource(index) for index in partially_checked_indices]

        def expand_parents(item_index: QtC.QModelIndex):
            """
            Expand parent index of the given item index in the tree view. Recursively expands each parent.
            :param item_index: QModelIndex of the item whose parent should be expanded
            :return:
            """
            parent = item_index.parent()
            while parent.isValid():
                self.expand(parent)
                parent = parent.parent()

        for index in checked_indices:
            expand_parents(index)
        for index in partially_checked_indices:
            expand_parents(index)

class TreeCombobox(QtW.QComboBox):
    """
    Custom QComboBox subclass that displays a tree structure in the dropdown list. This class extends QComboBox to provide
    functionality for displaying a tree view of items in the dropdown list. It allows users to search for items by typing
    in the line edit, and it uses a TreeSortFilterProxyModel to filter the items based on the text entered. The tree view
    supports context menus for editing, adding, and expanding/collapsing items. The combo box can be used to select items
    from a tree structure, making it suitable for hierarchical data representation.
    """
    closing = QtC.pyqtSignal()
    edit_triggered = QtC.pyqtSignal(QtW.QComboBox)
    add_triggered = QtC.pyqtSignal(QtW.QComboBox, QAction)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proxy_model = None
        self.tree_model = None
        self.setEditable(True)
        self.lineEdit().setPlaceholderText("Search")
        self.lineEdit().setReadOnly(False)
        self.treeView = QtW.QTreeView()
        self.treeView.setRootIsDecorated(True)
        self.closedOnLineEditClick = False
        self.checkable = False
        self.expand_collapse = False
        self.popup_shown = False
        self.typing = False
        self.context_menu = False
        self.setView(self.treeView)
        self.treeView.viewport().installEventFilter(self)
        self.treeView.setWindowFlags(QtC.Qt.WindowType.Popup)
        self.treeView.setFocusProxy(self.lineEdit())
        self.treeView.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.lineEdit().installEventFilter(self)
        self.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.lineEdit().textEdited.connect(self.update_filter)
        self.setCompleter(None)

    def start_typing(self):
        """
        Start typing in the line edit, which will grab the keyboard focus and allow the user to type in the search box.
        :return:
        """
        if not self.typing:
            save_expanded_state(self.tree_model.tableName(), self.treeView)
            self.typing = True
            self.lineEdit().grabKeyboard()

    def stop_typing(self):
        """
        Stop typing in the line edit, which will release the keyboard focus and clear the search filter.
        :return:
        """
        if self.typing:
            self.typing = False
            self.lineEdit().releaseKeyboard()
            self.proxy_model.setFilterRegularExpression('')
            restore_expanded_state(self.tree_model.tableName(), self.treeView)

    def set_text(self, text: str):
        """
        Set the text of the line edit to the given text. This method is used to update the line edit text when the user
        selects an item from the tree view or when the text is set programmatically. It checks if the combo box is not
        currently typing before setting the text to avoid conflicts with user input. If the model is checkable, the
        subclass CheckableTreeModel will handle the check state of items, and this method will set the text
        :param text: text to set as the text of the line edit
        :return:
        """
        if not self.checkable and not self.typing:
            self.lineEdit().setText(text)

    def setModel(self, model: CheckableTreeModel | QSortFilterProxyModel):
        """
        Set the model for the tree view in the combo box. This method overrides the default setModel method to set
        a TreeSortFilterProxyModel as the source model for the tree view. The proxy model allows for filtering of items
        based on the text entered in the line edit. It also sets the filter case sensitivity to case-insensitive and
        enables recursive filtering. The first column is shown, and all other columns are hidden by default.
        :param model:
        :return:
        """
        start_set_model_time = time.time()
        self.tree_model, indexes = find_tree_model(model, None)
        if not self.tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        self.proxy_model = TreeSortFilterProxyModel(self, self.treeView)
        self.proxy_model.setSourceModel(model)
        self.proxy_model.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        super().setModel(self.proxy_model)
        show_column(self, 0)
        self.treeView.resizeColumnToContents(0)
        self.treeView.setMinimumWidth(self.treeView.sizeHint().width())
        self.treeView.setSortingEnabled(False)
        logger_setup.get_logger().debug(f'Set model for tree combobox in {time.time() - start_set_model_time:.2f} seconds')

    def update_filter(self, text: str):
        """
        Update the filter of the proxy model based on the text entered in the line edit. This method is called whenever
        the text in the line edit is edited by typing. It sets the filter regular expression of the proxy model
        to match (case-insensitive) the text entered by the user. If the text is not empty, it expands all items in
        the tree view to show all matching items. This allows users to search for items in the tree structure by typing.
        :param text: text to filter the items in the tree view
        :return:
        """
        self.start_typing()
        # logger_setup.get_logger().debug(f'Setting filter to: {text}')
        search_expression = QtC.QRegularExpression(text, options=QtC.QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setFilterRegularExpression(search_expression)
        if text != "":
            self.treeView.expandAll()
        self.showPopup()

    def enable_context_menu(self, show_context_menu: bool):
        """
        Enable or disable the context menu for the tree view in the combo box. If show_context_menu is True, it sets
        the context menu policy to CustomContextMenu and connects the customContextMenuRequested signal to the
        show_context_menu method. If show_context_menu is False, it sets the context menu policy to NoContextMenu.
        :param show_context_menu: True or False to enable or disable the context menu
        :return:
        """
        self.context_menu = show_context_menu
        if self.context_menu:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)
        else:
            self.setContextMenuPolicy(QtC.Qt.ContextMenuPolicy.NoContextMenu)

    def show_context_menu(self, pos):
        """
        Show the context menu for the tree view in the combo box. This method is called when the user right-clicks
        on the tree view. It creates a TreeContextMenu and sets the view to the tree view. The context menu includes
        options for editing, adding, expanding/collapsing items, and other actions based on the current table of the model.
        If the model is an Aliquots table, it sets the view to the tree view with specific options. The action selected
        in the context menu is processed, and signals are emitted for editing or adding items. The popup is shown after
        the context menu is executed to ensure that the user can continue interacting with the combo box.
        :param pos:
        :return:
        """
        menu = TreeContextMenu()
        tree_model, indexes = find_tree_model(self.model(), None)
        if not tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        if tree_model.tableName() == 'Aliquots':
            menu.set_view(self.treeView, False, False)
        else:
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
            self.showPopup()

    def set_line_edit_text(self, text: str):
        """
        Set the text of the line edit to the given text. This method is only called when the user is not currently typing.
        :param text: text to set as the text of the line edit
        :return:
        """
        if not self.typing:
            self.lineEdit().setText(text)

    def setCurrentText(self, text: str):
        """
        Set the current text of the combo box to the given text. The text is only set if the user is not currently typing.
        :param text: text to set as the current text of the combo box
        :return:
        """
        if not self.typing:
            super().setCurrentText(text)

    def setCurrentIndex(self, index: int):
        """
        Set the current index of the combo box to the given index. The index is only set if the user is not currently typing.
        :param index: row index to set as the current index of the combo box
        :return:
        """
        if not self.typing:
            super().setCurrentIndex(index)

    def setEditText(self, text: str):
        """
        Set the text of the line edit to the given text. This method is used to update the line edit text when the user
        selects an item from the tree view or when the text is set programmatically. It checks if the combo box is not
        currently typing before setting the text to avoid conflicts with user input.
        :param text: String to set as the current text of the combo box
        :return:
        """
        if not self.typing:
            self.lineEdit().setText(text)

    def showPopup(self):
        """
        Show the popup for the combo box. This method is called to display the dropdown list of items in the combo box.
        If the model is a tree model and the user is not typing, it restores the expanded state of the tree view before
        showing the popup. It resizes the columns to fit the contents and sets the width and height of the tree view to
        fit the size hint for the name column. The popup_shown flag is set to True to indicate that the popup is
        currently shown. If the tree model has no items, it does not show the popup.
        :return:
        """
        tree_model, indexes = find_tree_model(self.model(), None)
        if not tree_model:
            return
        if tree_model.rowCount(QtC.QModelIndex()) == 0:
            return
        if not self.typing:
            restore_expanded_state(tree_model.table, self.treeView)
        super().showPopup()
        self.treeView.resizeColumnToContents(0)
        # print(self.treeView.sizeHintForColumn(0))
        if self.treeView.width() < self.treeView.sizeHintForColumn(0):
            self.treeView.setFixedWidth(self.treeView.sizeHintForColumn(0))
        if self.treeView.height() < self.treeView.sizeHint().height():
            self.treeView.setFixedHeight(self.treeView.sizeHint().height())
        # logger_setup.get_logger().debug(f'Popup showed: {self.treeView.isVisible()}')
        self.popup_shown = True

    def hidePopup(self):
        """
        Hide the popup for the combo box. This method is called to hide the dropdown view in the combo box only if it
        is shown. It checks if the user has clicked outside the view or if the expand/collapse action was triggered to
        keep the popup open when expanding/collapsing or selecting multiple items is allowed. When hiding, it saves the
        expanded state of the tree view if the model is a tree model and the user is not typing. This ensures that the
        expansions to show filtered items do not overwrite the user's expanded state. The typing state is stopped and the
        closing signal is emitted to notify that the popup is being closed.
        :return:
        """
        if self.popup_shown:
            if self.treeView.rect().contains(self.treeView.mapFromGlobal(QtG.QCursor.pos())):
                # Check if the cursor is still on the view
                if self.expand_collapse:
                    # The click was an expand/collapse action and should not close the popup
                    return
            super().hidePopup()
            model, indexes = find_tree_model(self.model(), None)
            if model and not self.typing:
                save_expanded_state(model.table, self.treeView)
            self.popup_shown = False
            self.stop_typing()
            self.closing.emit()

    def focusOutEvent(self, event):
        """
        Handle the focus out event for the combo box. This method is called when the combo box loses focus. If the event
        is a focus out event, it hides the popup to ensure that the dropdown list is not visible when the combo box
        loses focus.
        :param event:
        :return:
        """
        if event == QtC.QEvent.Type.FocusOut:
            self.hidePopup()
        super().focusOutEvent(event)

    def eventFilter(self, obj, event):
        """
        Filter events for the combo box and its view. This method is used to handle mouse button press events on the
        combo box and its view. It checks if the event is a mouse button press on the line edit or the view's viewport.
        If the event is a right-click on the line edit, it shows the context menu if it is enabled. If the event is a
        left-click on the view's viewport, it checks if the expand/collapse action was triggered. If it was, it expands
        or collapses the item at the clicked position without selecting it. If the event is a right-click on the view's
        viewport, it shows the context menu if it is enabled. Other events are passed to the superclass.
        :param obj:
        :param event:
        :return:
        """
        if obj == self.treeView.viewport():
            if event.type() == QtC.QEvent.Type.MouseButtonPress:
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
                    self.stop_typing()
                    self.set_text(index.data(QtC.Qt.ItemDataRole.DisplayRole))
                    self.expand_collapse = False
                    self.hidePopup()
                    return True
                else:
                    self.stop_typing()
                    if self.treeView.isExpanded(index):
                        self.treeView.collapse(index)
                    else:
                        self.treeView.expand(index)
                    # save_expanded_state(model.table, self.treeView)
                    self.expand_collapse = True
                    self.showPopup()
                    return True
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

class CheckableTreeCombobox(TreeCombobox):
    """
    Custom QComboBox subclass that displays a checkable tree structure in the dropdown list. This class extends TreeCombobox
    to provide functionality checkable tree models. It allows users to select multiple items from the
    dropdown list by checking the checkboxes next to each item. Closing the dropdown will emit a signal similar to editing
    finished that can be connected to a slot for further processing. A proxy model filter allows the user can search for
    items by typing in the line edit. The view supports a context menu for editing, adding, and deleting items.
    Setting single_click to True will upon click uncheck all items except the one clicked, forcing the user to select
    only one item at a time.
    """
    closing = QtC.pyqtSignal()
    edit_triggered = QtC.pyqtSignal(QtW.QComboBox)
    add_triggered = QtC.pyqtSignal(QtW.QComboBox, QAction)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.checkable = True
        self.single_click = False
        self.closedOnLineEditClick = False
        self.clicked = False
        self.edited = False
        self.treeView = CheckableTreeView()
        # show the empty root item in the combo box
        self.treeView.setRootIsDecorated(True)
        self.treeView.setWindowFlags(QtC.Qt.WindowType.Popup)
        self.treeView.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.treeView.viewport().installEventFilter(self)
        self.treeView.setFocusProxy(self.lineEdit())
        self.setView(self.treeView)
        self.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.lineEdit().textChanged.connect(self.le_text_changed)
        self.context_menu = False

    def le_text_changed(self):
        """
        Handle text changes in the line edit. This method is called whenever the text in the line edit is changed while
        not typing to make sure that it reflects the current state of the tree view.
        :return:
        """
        # print(f'{self.objectName()} line edit text changed: {self.lineEdit().text()}')
        if not self.typing:
            self.update_line_edit()

    def setModel(self, model: CheckableTreeModel):
        """
        Set the model for the checkable tree combo box. This method overrides the TreeCombobox setModel method to ensure
        connect the dataChanged signal of the model to the update_line_edit method to update the line edit text whenever
        the data in the model changes. It also expands all checked items in the tree view to show the hierarchy of checked
        items.
        :param model: CheckableTreeModel to be set as the model for the checkable tree combo box
        :return:
        """
        super().setModel(model)
        if self.model():
            self.model().dataChanged.connect(self.update_line_edit)
        self.treeView.expand_all_checked()

    def set_single_click(self, single_click):
        """
        Set whether the checkable tree combo box should allow single-click selection. If single_click is True, clicking
        on an item will uncheck all other items and select only the clicked item. If single_click is False, multiple items
        can be selected.
        :param single_click:
        :return:
        """
        self.single_click = single_click

    def update_line_edit(self):
        """
        Update the line edit text based on the checked items in the tree view. This method is called whenever the data
        in the model changes or when the user interacts with the tree view. It retrieves the checked items from the tree
        model and updates the line edit text accordingly. If there are partially checked items, the line edit is set to a
        dash ('-'). If there are fully checked items, the line edit is set to a semicolon-separated list of their names.
        If no items are checked, the line edit is set to the placeholder text. This ensures that the line edit always
        reflects the current state of the tree view and provides a clear indication of the selected items.
        :return:
        """
        current_line_edit_text = self.lineEdit().text()
        # If the line edit contains a comma, it is likely a list of items
        current_names = current_line_edit_text.split('; ')
        tree_model, indexes = find_tree_model(self.model(), None)
        if not tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = tree_model.traverse_checkable_tree(
            QtC.QModelIndex())
        if partially_checked_indices:
            # At least one item is partially checked, so the line edit should be a dash
            self.lineEdit().setText('-')
        elif checked_indices:
            # At least some items are fully checked and should be included in the list
            new_names = []
            for index in checked_indices:
                new_name = index.data(QtC.Qt.ItemDataRole.DisplayRole)
                if new_name not in new_names and new_name != '':
                    new_names.append(new_name)
            if current_line_edit_text == '' or current_line_edit_text == '-':
                self.lineEdit().setText('; '.join(new_names))
            else:
                if new_names != current_names:
                    self.lineEdit().setText('; '.join(new_names))
        else:
            # No items are checked, so the line edit should be set to the placeholder text
            self.lineEdit().setText(self.placeholderText())
        # logger_setup.get_logger().debug(f'Line edit text updated to {self.lineEdit().text()}')
        self.programatic_text_change = False

    def clear_all_checks(self):
        """
        Clear all checks in the checkable tree combo box. This method traverses the tree model and unchecks all items
        in the tree view.
        :return:
        """
        # traverse the tree and uncheck all items
        def traverse_tree(parent: QtC.QModelIndex):
            for row in range(self.model().rowCount(parent)):
                index = self.model().index(row, 0, parent)
                self.model().setData(index, QtC.Qt.CheckState.Unchecked, QtC.Qt.ItemDataRole.CheckStateRole)
                traverse_tree(index)

        traverse_tree(QtC.QModelIndex())

    def check_all(self):
        """
        Check all items in the checkable tree combo box. This method traverses the tree model and checks all items
        in the tree view.
        :return:
        """
        # traverse the tree and check all items
        def traverse_tree(parent: QtC.QModelIndex):
            for row in range(self.model().rowCount(parent)):
                index = self.model().index(row, 0, parent)
                self.model().setData(index, QtC.Qt.CheckState.Checked, QtC.Qt.ItemDataRole.CheckStateRole)
                traverse_tree(index)

        traverse_tree(QtC.QModelIndex())

    def show_context_menu(self, pos):
        """
        Show the context menu for the checkable tree combo box. This method is called when the user right-clicks on
        the checkable tree view or the line edit. It creates a TreeContextMenu and passes the tree view. The context menu
        includes options for editing, adding, expanding/collapsing items, and other actions based on the current table of
        the model. The action selected in the context menu is processed, and signals are emitted for editing or adding
        items. The popup is shown after the context menu is executed to ensure that the user can continue interacting
        with the combo box.
        :param pos:
        :return:
        """
        menu = TreeContextMenu()
        tree_model, indexes = find_tree_model(self.model(), None)
        if not tree_model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
            return
        if tree_model.tableName() == 'Aliquots':
            menu.set_view(self.treeView, False, False)
        else:
            menu.set_view(self.treeView, False)
        action = menu.exec(self.mapToGlobal(pos))
        if action:
            if action.text() == 'Edit':
                logger_setup.get_logger().info(f'Edit triggered for checkable tree combo box')
                self.edit_triggered.emit(self)
            elif 'Add' in action.text() or 'Insert' in action.text():
                logger_setup.get_logger().info(f'Add triggered for checkable tree combo box')
                self.add_triggered.emit(self, action)
            elif 'Expand' in action.text() or 'Collapse' in action.text():
                expand_collapse(self.treeView, action)
            elif 'Check all' in action.text():
                self.check_all()
            elif 'Clear all checks' in action.text():
                self.clear_all_checks()

    def showPopup(self):
        """
        Show the popup for the checkable tree combo box. This method is called to display the dropdown list of items in
        the checkable tree combo box. If the model is a tree model and the user is not typing, it expands the parents of
        checked items to show the hierarchy of checked items.
        :return:
        """
        super().showPopup()
        if not self.clicked:
            # If the user has not clicked on an item yet, expand all checked items. After the first click, the
            # user's expanded state is saved and restored when the popup is shown again.
            self.treeView.expand_all_checked()

    def hidePopup(self):
        """
        Hide the popup for the checkable tree combo box. This method is called to hide the dropdown view in the combo box
        only if it is shown. It checks if the user has clicked outside the view or if the expand/collapse action was
        triggered to keep the popup open when expanding/collapsing or selecting multiple items is allowed. When hiding, it
        saves the expanded state of the tree view if the model is a tree model and the user is not typing. This ensures that
        the expansions to show filtered items do not overwrite the user's expanded state. The typing state is stopped and the
        closing signal is emitted to notify that the popup is being closed. If the popup is already hidden, it does nothing.
        :return:
        """
        if self.popup_shown:
            # Check if the cursor is still over the view or the combo box and the combo box has focus, if so, do not hide the popup
            if (self.treeView.rect().contains(self.treeView.mapFromGlobal(QtG.QCursor.pos()))
                or self.rect().contains(self.mapFromGlobal(QtG.QCursor.pos()))) and self.hasFocus():
                if not self.single_click:
                    return
                if self.expand_collapse:
                    # The click was an expand/collapse action and should not close the popup
                    return
            super().hidePopup()
            model, indexes = find_tree_model(self.model(), None)
            if model and not self.typing and self.clicked:
                # Only save the expanded state if the user clicked on an item, the model is a tree model, and the user is not typing
                save_expanded_state(model.table, self.treeView)
            self.popup_shown = False
            self.clicked = False
            self.stop_typing()
            self.closing.emit()
            self.update_line_edit()

    def eventFilter(self, obj, event):
        """
        Filter events for the viewport of the checkable tree combo box. This method is used to handle mouse button press
        events on the viewport of the tree view. If the event is a left-click on the viewport, it checks if the
        expand/collapse button was clicked. If it was, it expands or collapses the item at the clicked position. If not,
        it toggles the check state of the item at the clicked position. If the event is a right-click on the viewport,
        it shows the context menu if it is enabled. Other events are passed to the superclass.
        :param obj:
        :param event:
        :return:
        """
        if obj == self.treeView.viewport():
            if event.type() == QtC.QEvent.Type.MouseButtonPress and event.button() == QtC.Qt.MouseButton.LeftButton:
                index = self.treeView.indexAt(event.pos())
                if not index.isValid():
                    super().eventFilter(obj, event)
                self.clicked = True
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
                    # This returns true when the expand/collapse icon is NOT clicked
                    if self.single_click:
                        # Was the only selected item unchecked? If so, set the current index to the root before clearing all checks
                        tree_model, indexes = find_tree_model(self.model(), None)
                        if not tree_model:
                            logger_setup.get_logger().info(f'No checkable tree model found in {self.objectName()}')
                            return True
                        checked_ids, partially_checked_ids, checked_indices, partially_checked_indices = (
                            tree_model.traverse_checkable_tree(QtC.QModelIndex()))
                        if self.treeView.currentIndex() in checked_indices:
                            self.treeView.setCurrentIndex(QtC.QModelIndex())
                        self.clear_all_checks()
                        self.treeView.toggle_check_state(self.treeView.currentIndex())
                        self.stop_typing()
                        self.set_line_edit_text(self.treeView.currentIndex().data(QtC.Qt.ItemDataRole.DisplayRole))
                        self.expand_collapse = True
                        self.hidePopup()
                    else:
                        self.treeView.toggle_check_state(self.treeView.currentIndex())
                        self.stop_typing()
                        self.update_line_edit()
                        self.expand_collapse = False
                        self.showPopup()
                    return True
                else:
                    if not isinstance(self.model(), TreeModel):
                        tree_model, indexes = find_tree_model(self.model(), None)
                    else:
                        tree_model = self.model()
                    self.stop_typing()
                    if self.treeView.isExpanded(index):
                        self.treeView.collapse(index)
                    else:
                        self.treeView.expand(index)
                    if tree_model:
                        save_expanded_state(tree_model.table, self.treeView)
                    self.expand_collapse = True
                    self.showPopup()
                    return True
            elif event.type() == QtC.QEvent.Type.MouseButtonPress and event.button() == QtC.Qt.MouseButton.RightButton:
                self.stop_typing()
                self.show_context_menu(event.pos())
                return True
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)

class TreeContextMenu(QtW.QMenu):
    """
    Custom context menu for tree views. This class extends QMenu to provide a context menu for tree views with options
    for editing, adding, expanding/collapsing items, and viewing data. It dynamically adds actions based on the selected
    items in the tree view. The context menu can handle both single and multiple selections, and it provides options
    for inserting items above or below the selected item, adding child items, and adding parent items. It also includes
    options for expanding and collapsing items, as well as viewing data related to the selected items. A tree view is
    passed with bool values to enable or disable specific actions such as delete, add, and edit. The context menu
    can be used with both checkable and non-checkable tree views, and it provides a flexible way to interact with tree
    structures in the application.
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self.tree_view = None
        self.model = None
        self.indexes = None

    def set_view(self, tree_view: QtW.QTreeView, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        """
        Set the view for the context menu. This method initializes the context menu with actions based on the selected
        items in the tree view. It retrieves the model and indexes of the selected items, and then adds actions for
        editing, adding, deleting, expanding, and collapsing items. It also adds actions for viewing data if the model
        is an Aliquots table. The actions are added based on whether the delete, add, and edit actions are active or not.
        Actions are also different depending on if single or multiple items are selected.
        :param tree_view: QTreeView that contains selected items for which the context menu is created
        :param delete_active: Adds delete action if True, otherwise does not add it
        :param add_active: Adds add actions if True, otherwise does not add it
        :param edit_active: Adds edit actions if True, otherwise does not add it
        :return:
        """
        self.tree_view = tree_view
        self.model, self.indexes = find_tree_model(self.tree_view.model(), self.tree_view.selectedIndexes())
        if not self.model:
            logger_setup.get_logger().info(f'No checkable tree model found in {self.tree_view.objectName()}')
            return
        item_ids, parent_ids, parent_rows = get_selected_tree_ids(self.indexes)
        if len(item_ids) == 1:  # only one item selected
            self.add_single_tree_actions(delete_active, add_active, edit_active)
        else:
            self.add_multi_tree_actions(delete_active, add_active, edit_active)
        self.add_expand_collapse_actions()
        if 'Aliquot' in self.model.table:
            self.add_view_data_actions()

    def add_single_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        """
        Add actions for a single selected item in the tree view. This method adds actions for editing, adding, and deleting
        a single item in the tree view. Several hierarchical add actions are available for a single item.
        :param delete_active: Adds delete action if True, otherwise does not add it
        :param add_active: Adds add actions if True, otherwise does not add it
        :param edit_active: Adds edit action if True, otherwise does not add it
        :return:
        """
        if edit_active:
            self.addAction('Edit')
        if add_active:
            add_menu = self.addMenu('Add')
            add_menu.addAction('Insert above')
            add_menu.addAction('Insert below')
            add_menu.addAction('Add child')
            add_menu.addAction('Add parent')
            add_menu.addAction('Add to end')
        if delete_active:
            self.addAction('Delete selected')

    def add_multi_tree_actions(self, delete_active: bool = True, add_active: bool = True, edit_active: bool = True):
        """
        Add actions for multiple selected items in the tree view. This method adds actions for editing, adding, and deleting
        multiple items in the tree view. No hierarchical add actions are available for multiple items.
        :param delete_active:
        :param add_active:
        :param edit_active:
        :return:
        """
        if edit_active:
            self.addAction('Edit')
        if delete_active:
            self.addAction('Delete selected')
        if add_active:
            self.addAction('Add')

    def add_expand_collapse_actions(self):
        """
        Add actions for expanding and collapsing items in the tree view. This method adds actions for expanding and collapsing
        children, all children, and all items in the tree view. These actions allow users to quickly expand or collapse
        the tree structure to view or hide the details of the items. The actions are grouped into Expand and Collapse menus.
        :return:
        """
        expand_menu = self.addMenu('Expand')
        expand_menu.addAction('Expand children')
        expand_menu.addAction('Expand all children')
        expand_menu.addAction('Expand all')
        collapse_menu = self.addMenu('Collapse')
        collapse_menu.addAction('Collapse children')
        collapse_menu.addAction('Collapse all children')
        collapse_menu.addAction('Collapse all')

    def add_checkable_actions(self):
        """
        Add actions for checkable tree views. This method adds actions to check all items or clear all checks in the
        checkable tree view.
        :return:
        """
        if isinstance(self.tree_view, CheckableTreeView):
            self.addAction('Clear all checks')
            self.addAction('Check all')

    def add_view_data_actions(self):
        """
        Add actions for viewing data related to the selected items in the tree view. This method adds actions to view
        spots and U-Pb analyses for the selected aliquots in separate tabs.
        :return:
        """
        view_data_menu = self.addMenu('View Data')
        view_data_menu.addAction('View Spots')
        view_data_menu.addAction('View U-Pb Analyses')


class FrozenTableView(QtW.QTableView):
    """
    Custom QTableView subclass that allows freezing the first column of the table. This class extends QTableView to
    provide functionality for freezing the first column of the table, allowing it to remain visible while scrolling
    horizontally. The frozen column is displayed in a separate QTableView that is stacked over the main table view.
    The frozen table view is updated whenever the model is set or when the section sizes change. It also synchronizes
    the vertical scroll bar with the main table view to ensure that both views scroll together. The frozen column
    is updated whenever the section sizes change, and the geometry of the frozen table view is adjusted to match the
    main table view's geometry.
    """
    # todo: Troubleshoot the frozen column resizing issue when the table is resized
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
        """
        Set the model for the frozen table view and the main table view. This method overrides the QTableView setModel
        method to ensure that both the main table view and the frozen table view are set to the same model. It also
        hides all columns except the first one in the frozen table view. The frozen table view is updated to match the
        geometry of the main table view, and the section widths are set to match the main table view's column widths.
        :param model:
        :return:
        """
        super().setModel(model)
        self.frozen_table_view.setModel(model)
        self.frozen_table_view.setSelectionModel(self.selectionModel())
        for col in range(model.columnCount()):
            if col != 1:
                self.frozen_table_view.hideColumn(col)

        self.update_frozen_table_geometry()

    def update_section_height(self, logicalIndex):
        """
        Update the height of the frozen table view's row based on the logical index. This method is called whenever
        the height of a section in the main table view changes. It sets the row height of the frozen table view to
        match the row height of the main table view for the specified logical index. This ensures that the frozen column
        remains aligned with the main table view's rows even when the row heights change.
        :param logicalIndex:
        :return:
        """
        self.frozen_table_view.setRowHeight(logicalIndex, self.rowHeight(logicalIndex))

    def update_section_width(self, logicalIndex):
        """
        Update the width of the frozen table view's column based on the logical index. This method is called whenever
        the width of a section in the main table view changes. It sets the column width of the frozen table view to
        match the column width of the main table view for the specified logical index. This ensures that the frozen column
        remains aligned with the main table view's columns even when the column widths change.
        :param logicalIndex:
        :return:
        """
        self.frozen_table_view.setColumnWidth(logicalIndex, self.columnWidth(logicalIndex))
        self.update_frozen_table_geometry()

    def resizeEvent(self, event):
        """
        Handle the resize event for the frozen table view. This method is called whenever the main table view is resized.
        It updates the geometry of the frozen table view to match the new size of the main table view. The frozen table
        view's geometry is adjusted to ensure that it occupies the same space as the first column of the main table view.
        :param event:
        :return:
        """
        super().resizeEvent(event)
        self.update_frozen_table_geometry()

    def moveCursor(self, cursorAction, modifiers):
        """
        Move the cursor in the frozen table view based on the cursor action and modifiers. This method overrides the
        QTableView moveCursor method to handle the case where the cursor is moved left and the current column is greater
        than 1. If the cursor is moved left and the current column is greater than 1, it checks if the visual rectangle
        of the current index is outside the width of the frozen column. If it is, it adjusts the horizontal scroll bar
        value to ensure that the frozen column remains visible. This allows the user to navigate through the table while
        keeping the frozen column in view. The method returns the current index after moving the cursor.
        :param cursorAction:
        :param modifiers:
        :return: current index after moving the cursor
        """
        current = super().moveCursor(cursorAction, modifiers)
        if (cursorAction == QtW.QAbstractItemView.CursorAction.MoveLeft and current.column() > 1 and
                self.visualRect(current).topLeft().x() < self.frozen_table_view.columnWidth(1)):
            new_value = (self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() -
                         self.frozen_table_view.columnWidth(1))
            self.horizontalScrollBar().setValue(new_value)
        return current

    def scrollTo(self, index, hint = ...):
        """
        Scroll to the specified index in the frozen table view. This method overrides the QTableView scrollTo method
        to handle the case where the index is in a column greater than 1. If the index's column is greater than 1, it
        calls the superclass scrollTo method to scroll to the specified index. This ensures that the frozen column remains
        visible while scrolling through the table. The hint parameter is passed to the superclass method to specify
        how the scrolling should be performed (e.g., whether to scroll to the top, center, etc.). If the index is in
        the first two columns, it does not scroll to the index, as the frozen column is always visible.
        :param index:
        :param hint:
        :return:
        """
        if index.column() > 1:
            super().scrollTo(index, hint)

    def update_frozen_table_geometry(self):
        """
        Update the geometry of the frozen table view to match the main table view's geometry. This method is called
        whenever the model is set or when the section sizes change. It adjusts the geometry of the frozen table view
        to ensure that it occupies the same space as the first column of the main table view. The frozen table view's
        geometry is set based on the vertical header width, frame width, column width of the first column, and the
        viewport height of the main table view. This ensures that the frozen column remains aligned with the main table
        view's rows and columns, even when the table is resized or the section sizes change. The geometry is set to
        ensure that the frozen column is positioned correctly relative to the main table view's viewport and headers.
        :return:
        """

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

# ---------------------------
#    Widget Methods
# ---------------------------

def set_comboBox_text(comboBox: QtW.QComboBox, text: str):
    """
    Set the text of a combo box. This method updates the current index of the combo box based on the provided text.
    :param comboBox: combo box to set the text for
    :param text: text string to set in the combo box
    :return:
    """
    if text == '' or text == '-':
        comboBox.setCurrentIndex(-1)
    else:
        comboBox.setCurrentText(text)

def show_column(comboBox: QtW.QComboBox, column: str | int):
    """
    Set the model column for a combo box. This method sets the model column of the combo box to the specified column.
    If the column is a string, it searches for the column index by matching the header data. If the column is an integer,
    it sets the model column directly. It also sorts the model if it is a proxy model and not a tree. All other columns
    will not be shown in the view. This allows the combo box to display only the specified column while hiding others.
    :param comboBox: combo box to set the model column for
    :param column: column name or index to set as the model column
    :return:
    """
    try:
        if comboBox.proxy_model:
            model = comboBox.proxy_model
        else:
            model = comboBox.model()
    except AttributeError:
        model = comboBox.model()
    if model:
        if isinstance(column, str):
            # If the column is a string, find the index of the column by its header data
            if isinstance(model, ReadableProxyModel):
                # If the model is a ReadableProxyModel, get the readable header to compare
                column = get_readable_header(column)
            for col in range(model.columnCount()):
                header = model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if header == column:
                    column = col
                    break
        comboBox.setModelColumn(column)
        if not isinstance(comboBox.view(), QtW.QListView):
            for model_column in range(model.columnCount()):
                if model_column != column:
                    try:
                        comboBox.view().hideColumn(model_column)
                    except AttributeError:
                        # If the view does not have a hideColumn method, no need
                        pass
        tree_model, indexes = find_tree_model(model, None)
        if isinstance(model, QtC.QSortFilterProxyModel) and not tree_model:
            model.sort(column, QtC.Qt.SortOrder.AscendingOrder)

def add_tree_popup(tree_view: QtW.QTreeView, action: QtG.QAction | None = None):
    """
    Determine the arguments to pass to a dialog for adding or inserting items in a tree view based on the selected
    indexes and the action.
    :param tree_view: QtW.QTreeView to add or insert items in
    :param action: QtG.QAction that specifies the action to perform (e.g., insert above, insert below, add child, etc.)
    :return: library dialog arguments to pass to the dialog for adding or inserting items in the tree view
    """
    dlg_args = None
    indexes = tree_view.selectedIndexes()
    model = tree_view.model()
    tree_model, tree_indexes = find_tree_model(model, indexes)
    if not tree_model:
        logger_setup.get_logger().info(f'No tree model found in {tree_view.objectName()}')
        return dlg_args
    item_ids, parent_ids, parent_rows = get_selected_tree_ids(tree_indexes)
    if action:
        if action.text() == 'Insert above':
            row = parent_rows[0]
            parent_id = parent_ids[0]
            dlg_args = {'parent_ids' : parent_id, 'parent_row': row}
        elif action.text() == 'Insert below':
            row = parent_rows[0] + 1
            parent_id = parent_ids[0]
            dlg_args = {'parent_ids' : parent_id, 'parent_row': row}
        elif action.text() == 'Add child':
            parent_id = item_ids[0]
            dlg_args = {'parent_ids' : parent_id}
        elif action.text() == 'Add parent':
            dlg_args = {'add_item': 'parent', 'item_ids': item_ids, 'old_parent_ids': parent_ids, 'old_parent_rows': parent_rows}
        elif action.text() == 'Add to end' or action.text() == 'Add':
            dlg_args = {'add_item': 'child'}
    return dlg_args

def save_expanded_state(table: str, tree_view: QtW.QTreeView):
    """
    Save the expanded state of the tree view to the settings
    :param table: Name of table with parent-child relationships
    :param tree_view: The view displaying the model
    :return:
    """
    show_loading_dialog('Saving expanded state', 'Saving the expanded state of the tree view...')
    start_save_expanded_time = time.time()
    expanded_ids = set()
    model = tree_view.model()
    def save_state(index):
        if index.isValid() and tree_view.isExpanded(index):
            item_id = model.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole)
            expanded_ids.add(item_id)
        row_count = model.rowCount(index)
        for i in range(row_count):
            save_state(model.index(i, 0, index))

    root_index = QtC.QModelIndex()
    root_row_count = model.rowCount(root_index)
    for i in range(root_row_count):
        save_state(model.index(i, 0, root_index))
    SettingsManager().db_settings.setValue(f'expanded_ids_{table}', expanded_ids)
    logger_setup.get_logger().debug(f'Expanded state saved for {table} table in {time.time() - start_save_expanded_time} seconds')
    close_loading_dialog('Saving expanded state', 'Saving the expanded state of the tree view...')

def restore_expanded_state(table: str, tree_view: QtW.QTreeView):
    """
    Restore the expanded state of the tree view from the set of expanded ids stored in settings
    :param table: Name of table with parent-child relationships
    :param tree_view: The view to display the model
    :return:
    """
    # logger_setup.get_logger().info(f'Restoring expanded state for {table} table')
    show_loading_dialog('Restoring expanded state', 'Restoring the expanded state of the tree view...')
    start_expand_tree_time = time.time()
    expanded_ids = SettingsManager().db_settings.value(f'expanded_ids_{table}', set())
    model = tree_view.model()

    def restore_state(index):
        if index.isValid():
            item_id = model.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole)
            is_expanded = item_id in expanded_ids
            tree_view.setExpanded(index, is_expanded)
        row_count = model.rowCount(index)
        for row in range(row_count):
            restore_state(model.index(row, 0, index))

    restore_state(QtC.QModelIndex())
    logger_setup.get_logger().info(f'Expanded state restored in {time.time() - start_expand_tree_time} seconds')
    close_loading_dialog('Restoring expanded state', 'Restoring the expanded state of the tree view...')

def expand_all_children(tree_view: QtW.QTreeView, parent_index: QtC.QModelIndex):
    """
    Expand all children of the given parent index in the tree view. This method recursively expands all child items
    of the specified parent index in the tree view. It ensures that all child items are expanded, allowing the user
    to view the entire hierarchy of items under the specified parent. If the parent index is invalid, it defaults to
    the root index. If the parent index does not have column 0, it is adjusted to ensure that the correct column is used
    for expanding children. The method iterates through all rows of the model under the parent index and recursively
    calls itself for each child index. After expanding all children, it also expands the parent index itself if it is not
    already expanded. This is useful for ensuring that the parent item's children are visible in the tree view after
    expanding them.
    :param tree_view: the tree view to expand children in
    :param parent_index: the parent index whose children should be expanded
    :return:
    """
    show_loading_dialog('Expanding children', 'Expanding all children in the tree view...')
    # make sure the parent_index has column 0
    if not parent_index.isValid():
        parent_index = QtC.QModelIndex()  # parent is root
    if parent_index.column() != 0:
        parent_index = parent_index.siblingAtColumn(0)

    model = tree_view.model()
    for row in range(model.rowCount(parent_index)):
        child_index = model.index(row, 0, parent_index)
        expand_all_children(tree_view, child_index)
    if not tree_view.isExpanded(parent_index):
        tree_view.expand(parent_index)
    close_loading_dialog('Expanding children', 'Expanding all children in the tree view...')

def collapse_all_children(tree_view: QtW.QTreeView, parent_index: QtC.QModelIndex):
    """
    Collapse all children of the given parent index in the tree view. This method recursively collapses all child items
    of the specified parent index in the tree view. It ensures that all child items are collapsed, hiding their details
    from the view. If the parent index is invalid, it defaults to the root index. If the parent index does not have
    column 0, it is adjusted to ensure that the correct column is used for collapsing children. The method iterates
    through all rows of the model under the parent index and recursively calls itself for each child index. After collapsing
    all children, it also collapses the parent index itself if it is currently expanded. This is useful for ensuring
    that the parent item's children are hidden in the tree view after collapsing them.
    :param tree_view: the tree view to collapse children in
    :param parent_index: the parent index whose children should be collapsed
    :return:
    """
    show_loading_dialog('Collapsing children', 'Collapsing all children in the tree view...')
    # make sure the parent_index has column 0
    if not parent_index.isValid():
        parent_index = QtC.QModelIndex()  # parent is root
    if parent_index.column() != 0:
        parent_index = parent_index.siblingAtColumn(0)

    model = tree_view.model()
    for row in range(model.rowCount(parent_index)):
        child_index = model.index(row, 0, parent_index)
        collapse_all_children(tree_view, child_index)
    if tree_view.isExpanded(parent_index):
        tree_view.collapse(parent_index)
    close_loading_dialog('Collapsing children', 'Collapsing all children in the tree view...')

def expand_collapse(tree_view: QtW.QTreeView, action: QtG.QAction):
    """
    Handles TreContextMenu actions for expanding and collapsing items in a tree view. This method checks the text of the
    action and performs the corresponding operation on the selected indexes in the tree view. It can expand or collapse
    children, expand or collapse all children, expand or collapse all items, and save the expanded state of the tree
    view after performing the action.
    :param tree_view: QTreeView to perform the action on
    :param action: QAction selected from a TreeContextMenu
    :return:
    """
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
    model = tree_view.model()
    if isinstance(model, QtC.QSortFilterProxyModel):
        # If the model is a proxy model, we need to get the source model
        model = model.sourceModel()
    try:
        table = model.table
    except AttributeError:
        logger_setup.get_logger().error('Error saving expanded state')
        return
    save_expanded_state(table, tree_view)

def populate_combo_box(comboBox: QtW.QComboBox, **kwargs):
    """
    Populate a combo box with data from a database table or query. This method sets the model for the combo box based
    on the provided keyword arguments. It can handle both SQL queries and table names, and it supports displaying
    hierarchical data in a tree structure if the table is part of a user viewable tree. The method also allows specifying
    a specific column to display in the combo box. If a query is provided, it uses a DisplayRoundedQueryModel; otherwise,
    it uses a DisplayRoundedModel or a SQLiteTableModel based on the table name. If the table is part of a user viewable
    tree, it sets the model to a CheckableTreeModel or TreeModel. If the combo box is a CheckableComboBox, it uses
    CheckableSqlTableModel or CheckableSqlQueryModel to populate the combo box. The method also ensures that the
    specified column is displayed in the combo box, and it defaults to showing the name column if no specific column
    is provided.
    :param comboBox: QComboBox or subclass combo box to populate with data
    :param kwargs: keyword arguments to specify the table: str, query: str, and/or column: str
    :return:
    """
    table: str = None
    query: str = None
    column: str = None
    start_populate_combo_time = time.time()
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
        if table:
            model.set_table(table)
        if not table:
            table = model.tableName()
        if table == 'SampleAges':
            model.rounded = False
            proxy_model = SampleAgeProxyModel()
            proxy_model.setSourceModel(model)
            model = proxy_model
    elif table == 'Ages':
        model = SQLiteTableModel('SELECT * FROM Ages')
        if model.last_error:
            logger_setup.get_logger().error(f'Error setting up Ages table model')
            return
    elif table != get_view_from_table(table):
        # Need to use a special view query
        query_args = {'show_columns': settings.value(SQLUtils.view_setting_dict[get_view_from_table(table)])}
        view_query = ViewQuery(table, edit_view=False, **query_args)
        table_query = view_query.table_query
        model = DisplayRoundedQueryModel()
        show_loading_dialog('Loading', f'Loading related data for {table}...')
        model.setQuery(table_query)
        model.set_table(table)
        close_loading_dialog('Loading', f'Loading related data for {table}...')
    else:
        model = DisplayRoundedModel()
        set_table(model, table)
    if table in SQLUtils.user_viewable_trees:
        if isinstance(comboBox, CheckableTreeCombobox):
            tree_model = CheckableTreeModel()
        else:
            tree_model = TreeModel()
        tree_model.setSourceModel(model)
        comboBox.setModel(tree_model)
        if column:
            show_column(comboBox, column)
        else:
            show_column(comboBox, tree_model.headerData(0, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
    else:
        checkable_model = None
        if isinstance(comboBox, CheckableComboBox) and not query and (table == get_view_from_table(table)):
            # If the combo box is a CheckableComboBox and the table is not a view, use CheckableSqlTableModel
            checkable_model = CheckableSqlTableModel()
            set_table(checkable_model, table)
            comboBox.setModel(checkable_model)
        elif isinstance(comboBox, CheckableComboBox) and not query:
            # If the combo box is a CheckableComboBox and the table is a view, use CheckableSqlQueryModel
            checkable_model = CheckableSqlQueryModel()
            checkable_model.setQuery(table_query)
            comboBox.setModel(checkable_model)
        elif isinstance(comboBox, CheckableComboBox) and query:
            checkable_model = CheckableSqlQueryModel()
            checkable_model.setQuery(query)
            comboBox.setModel(checkable_model)
        else:
            try:
                comboBox.setModel(model)
            except Exception as e:
                logger_setup.get_logger().error(f'Error setting model for combo box {comboBox.objectName()}')
                logger_setup.get_logger().debug(f'Error: {e}')
                return
        if checkable_model and not checkable_model.tableName():
            if table:
                set_table(checkable_model, table)
            elif model.tableName():
                set_table(checkable_model, model.tableName())
        if column:
            show_column(comboBox, column)
        else:
            if isinstance(model, SampleAgeProxyModel):
                name_col = get_name_column('SampleAges')
            else:
                name_col = get_name_column(get_view_from_table(model.tableName()))
            show_column(comboBox, model.headerData(name_col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
    logger_setup.get_logger().debug(f'Populated combo box {comboBox.objectName()} in {time.time() - start_populate_combo_time} seconds')

def populate_model_checks(model: CheckableSqlTableModel | CheckableSqlQueryModel, item_ids: list, item_table: str=None, table_id_header: str=None):
    """
    Populate the checkable model with checks based on the item IDs and the item table, e.g. given a checkable Columns
    model and a list of Sample IDs, mark what columns are associated with those samples. This method iterates through
    the rows of the model and checks how many of the given item IDs have a specific tag in the item table. It updates
    the check state of the model's data based on the number of item IDs that have the tag. If all items have the tag,
    the check state is set to Checked; if some items have the tag, it is set to PartiallyChecked; and if no items
    have the tag, it is set to Unchecked.
    :param model: checkable model to populate with checks, data from a database table (e.g. Columns)
    :param item_ids: list of item IDs from a separate table (e.g. Sample IDs)
    :param item_table: table the list of item IDs is from. If the relationship is one-to-one or one-to-many, this may be
    a main table (e.g. Samples). If the relationship is many-to-many, this may be a junction table (e.g. SampleAges_References).
    :param table_id_header: name of the column in item_table that contains the IDs to check in the model. This may be
    different from the model table ID column (e.g. SampleColumnID column in the Samples table)
    :return: True if the model was populated successfully, False otherwise
    """
    start_populate_model_checks_time = time.time()
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
    col = get_name_column(get_view_from_table(model.tableName()))
    # Check that the table_id_header is in the item_table headers
    if table_id_header not in get_headers(item_table):
        # If not, check if it is a header of a view
        item_view = get_view_from_table(item_table)
        item_edit_view = get_edit_view_from_table(item_table)
        if table_id_header in get_headers(item_view):
            item_table = item_view
        elif table_id_header in get_headers(item_edit_view):
            item_table = item_edit_view
    for row in range(model.rowCount()):
        table_id = model.index(row, 0).data()
        if 'View' in item_table:
            # If the item_table is a view, we need to use the view query
            show_columns = settings.value(SQLUtils.view_setting_dict[item_table])
            where = f"WHERE {item_id_header} {query_where_str} AND {table_id_header} = {table_id}"
            edit_view = True if 'Edit' in item_table else False
            query_args = {'show_columns': show_columns, 'where': where}
            view_query = ViewQuery(item_table, edit_view, **query_args)
            model_query = view_query.table_query
            show_loading_dialog('Loading', f'Loading related data for {item_table}...')
        elif item_table == 'References':
            model_query = f'SELECT {table_id_header}, {item_id_header} FROM "References" WHERE {item_id_header} {query_where_str} AND {table_id_header} = {table_id}'
        else:
            model_query = f"SELECT {table_id_header}, {item_id_header} FROM {item_table} WHERE {item_id_header} {query_where_str} AND {table_id_header} = {table_id}"
        query_model.setQuery(model_query)
        close_loading_dialog('Loading', f'Loading related data for {item_table}...')
        if query_model.lastError().isValid():
            logger_setup.get_logger().critical(f'Error getting checks for {model.tableName()}')
            logger_setup.get_logger().debug(f'Error: {query_model.lastError().text()}')
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
    logger_setup.get_logger().debug(f'Populated model checks for {model.tableName()} in {time.time() - start_populate_model_checks_time} seconds')
    return True

def populate_tree_model_checks(tree_model: CheckableTreeModel, item_ids: list, item_table: str=None, table_id_header: str=None):
    """
    Populate the tree model with checks based on the item IDs and the item table, e.g. given a checkable Units model and
    a list of Sample IDs, mark what units are associated with those samples. This method recursively iterates through
    the rows of the tree model and checks how many of the given item IDs have a specific tag in the item table. If all
    items have the tag, the check state is set to Checked; if some items have the tag, it is set to PartiallyChecked;
    and if no items have the tag, it is set to Unchecked.
    :param tree_model: checkable tree model to populate with checks, data from a database table (e.g. Units)
    :param item_ids: list of item IDs from a separate table (e.g. Sample IDs)
    :param item_table: table the list of item IDs is from. If the relationship is one-to-one or one-to-many, this may be
    a main table (e.g. Samples). If the relationship is many-to-many, this may be a junction table (e.g. SamplesUnits).
    :param table_id_header: name of the column in item_table that contains the IDs to check in the model. This may be
    different from the model table ID column in a one-to-one or one-to-many relationship.
    :return: True if the model was populated successfully, False otherwise
    """
    start_populate_tree_model_checks_time = time.time()
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
        query_str = f"SELECT {table_id_header}, {item_id_header} FROM {item_table} WHERE {item_id_header} {query_where_str} AND {table_id_header} = {table_id}"
        query_model.setQuery(query_str)
        if query_model.lastError().isValid():
            logger_setup.get_logger().critical(f'Error getting checks for {table}')
            logger_setup.get_logger().debug(f'Error: {query_model.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query_str}')
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
    logger_setup.get_logger().debug(f'Populated tree model checks for {table} in {time.time() - start_populate_tree_model_checks_time} seconds')
    return True

def populate_many_combo_checks(many_to_many_table: str, combo: QtW.QComboBox, first_table_ids: list):
    """
    Populate a combo box with checks based on a many-to-many relationship table and a list of IDs from the first table.
    This method checks how many of the given IDs have a specific tag in the many-to-many relationship table. It updates
    the check state of the combo box's model based on the number of IDs that have the tag. If all items have the tag,
    the check state is set to Checked; if some items have the tag, it is set to PartiallyChecked; and if no items
    have the tag, it is set to Unchecked. The method also handles both CheckableTreeCombobox and regular QComboBox
    instances, adjusting the model and column indices accordingly.
    :param many_to_many_table: Many-to-many relationship table name (e.g. SampleAges_References)
    :param combo: combo box to populate with checks, can be a CheckableTreeCombobox or a regular QComboBox. Data must be
    from the second table in the many-to-many relationship (e.g. References)
    :param first_table_ids: list of IDs from the first table (e.g. Sample IDs)
    :return:
    """
    start_populate_many_checks_time = time.time()
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
        if not model:
            logger_setup.get_logger().info(f"Could not find tree model for {combo.objectName()}")
            return
        col = 0  # Name column is always placed in the first column
        tag_id_header = model.source_model.record().fieldName(0)
        id_col = 1  # ID column is always placed in the second column
    else:
        model = combo.model()
        try:
            col = get_name_column(get_view_from_table(model.tableName()))
            tag_id_header = model.record().fieldName(0)
        except AttributeError:
            logger_setup.get_logger().info(f'No table name found for {combo.objectName()}')
            return
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
        combo.treeView.expand_all_checked()
    if not text:
        text = combo.placeholderText()
    combo.setCurrentText(text)
    end_populate_checks_time = time.time()
    logger_setup.get_logger().info(
        f"Populated checks for {many_to_many_table} in {end_populate_checks_time - start_populate_checks_time} seconds")
    logger_setup.get_logger().info(f"Populated checks for {many_to_many_table} in {time.time() - start_populate_many_checks_time} seconds")

def get_readable_header(header: str):
    """
    For a given header/col name it will convert to a user readable header format by removing spaces, abbreviations, and
    adding units from the settings where appropriate. This method MUST work for all viewable columns and tables.
    :param header: header to convert
    :return: converted header
    """
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
    elif 'GPSElev' in header:
        header += f' ({settings.value("elevation_unit_abbreviation")})'
    elif 'TotalHeightDepthCalculated' in header:
        header = f'Calculated Total Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
    elif 'TotalHeightDepth' in header:
        header = f'Total Height/Depth'
    elif 'HeightDepthCalculated' in header or 'CalculatedHeightDepth' in header:
        header = f'Calculated Height/Depth ({settings.value('heightdepth_unit_abbreviation')})'
    elif 'HeightDepth' in header:
        header = header.replace('HeightDepth', 'Height/Depth')
    elif 'AgeError' in header and 'Calculated' in header:
        header += f' ({settings.value("age_error_format_abbreviation")})'
    elif 'CalculatedSpotSize' in header:
        header = f'Calculated Spot Size ({settings.value('spotsize_unit_abbreviation')})'
    elif 'CalculatedConcordance' in header:
        header = f'Calculated Concordance ({settings.value('concordance_format_abbreviation')})'
    elif ('Age' in header and 'Calculated' in header
          and not any(s in header for s in ['Name', 'Description', 'Reference', 'Unit', 'Format', 'Created', 'Modified'])):
        header += f' ({settings.value("age_unit_abbreviation")})'
    elif 'Error' in header and 'Calculated' in header:
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
    if ' Pb/' in header:
        header = header.replace(' Pb/', 'Pb/')
    if ' U/' in header:
        header = header.replace(' U/', 'U/')
    if ' Pb ' in header:
        header = header.replace(' Pb ', 'Pb ')
    if ' U ' in header:
        header = header.replace(' U ', 'U ')
    return header

loading_manager = LoadingDialogManager.get_instance()

def show_loading_dialog(title, message):
    """
    Show a loading dialog while the action is taking place. This method uses a timer to delay the display of the loading
    dialog to avoid showing it unnecessarily if the action completes quickly. The loading dialog is managed by the
    LoadingDialogManager, which ensures that it is closed properly after the action is completed. The title and message
    of the loading dialog can be customized.
    :param title: Title of the loading dialog
    :param message: Message to display in the loading dialog
    :return:
    """
    # Wait one second before showing the loading dialog in case it is not needed
    # timer = QtC.QTimer()
    # timer.timeout.connect(lambda: loading_manager.show_loading_dialog(title, message))
    # timer.start(100)
    loading_manager.show_loading_dialog(title, message)

def close_loading_dialog(title, message):
    """
    Close the loading dialog with the given title and message. This ensures that the loading dialog is closed properly.
    :param title: Title of the loading dialog to close
    :param message: Message displayed in the loading dialog to close
    :return:
    """
    loading_manager.close_loading_dialog(title, message)


# ---------------------------
#    Database Methods
# ---------------------------

def update_other_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, update_table: str, update_ids: list):
    """
    Take the checked ids from a table and update that field in another table. The relationship must be one-to-one or
    one-to-many, so there should be only one checked ID. If there are partially checked IDs, no item has been selected
    to associate with all IDs in the other table, so do not update. If the relationship is many-to-many, use
    update_many_table_with_checks.
    :param table: table with checked data (e.g. Columns)
    :param checked_ids: ids of checked items in the table, must be a single ID for one-to-one or one-to-many relationships
    :param partially_checked_ids: ids of partially checked items in the table (e.g. Column IDs)
    :param update_table: table to update (e.g. Samples)
    :param update_ids: ids to update in the update table (e.g. list of sample IDs to link to the checked column ID)
    :return: True if successful, False if not or not needed
    """
    if not update_ids:
        logger_setup.get_logger().error(f'No item IDs given for {update_table}')
        return False
    if partially_checked_ids:
        # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
        logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
        return True
    if len(checked_ids) > 1:
        # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
        logger_setup.get_logger().error(f'Multiple checked IDs given for {table}. Select only one ID to update {update_table}.')
        logger_setup.get_logger().debug(f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
        return False
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
        if current_id != '':
            if int(current_id) not in current_ids:
                current_ids.append(int(current_id))
    if current_ids == checked_ids:
        logger_setup.get_logger().info(f'Checks are up to date')
        return False
    create_savepoint('update_other_table')
    if not query.exec(f'UPDATE {update_table} SET {id_header} = {checked_ids[0]} WHERE {other_id_header} {query_where_str}'):
        logger_setup.get_logger().critical(f'Failed to add item to {update_table}')
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        rollback_savepoint('update_other_table')
        return False
    logger_setup.get_logger().info(f'Added {id_header} {checked_ids[0]} to {update_table}')
    release_savepoint('update_other_table')
    return True

def update_many_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, many_table: str, first_table_ids: list) -> bool:
    """
    Take the checked ids from a table and update that field in the second column of a many-to-many table with another table.
    The relationship must be many-to-many, so partially checked IDs are permitted.
    :param table: table with checked data (e.g. Regions)
    :param checked_ids: ids of checked items in the table (e.g. list of region IDs)
    :param partially_checked_ids: ids of partially checked items in the table (e.g. list of region IDs that are partially checked)
    :param many_table: many-to-many table to update (e.g. Samples_Regions)
    :param first_table_ids: ids to update in the first table (e.g. list of sample IDs to link to the checked region IDs)
    :return: True if successful or not needed, False if not
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
        f'SELECT {first_table_id_header}, {second_table_id_header} FROM {many_table} WHERE {first_table_id_header} {query_where_str}')
    current_pairs = []
    for row in range(query_model.rowCount()):
        first_id = query_model.data(query_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        second_id = query_model.data(query_model.index(row, 1), QtC.Qt.ItemDataRole.DisplayRole)
        pair = (first_id, second_id)
        if pair not in current_pairs:
            current_pairs.append(pair)
    model_query = f'SELECT {second_table_id_header} FROM "{second_table}"'
    query_model.setQuery(model_query)
    if query_model.lastError().isValid():
        logger_setup.get_logger().critical(f'Error getting {table} checks for {first_table}')
        logger_setup.get_logger().debug(f'Error: {query_model.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {model_query}')
        return False
    create_savepoint('update_many_table')
    to_remove = []
    to_add = []
    for row in range(query_model.rowCount()):
        second_id = query_model.data(query_model.index(row, 0), QtC.Qt.ItemDataRole.DisplayRole)
        if second_id in partially_checked_ids:
            pass
        else:
            for first_id in first_table_ids:
                pair = (first_id, second_id)
                if second_id in checked_ids and pair not in current_pairs and second_id not in to_add:
                    to_add.append(second_id)
                elif second_id not in checked_ids and pair in current_pairs and second_id not in to_remove:
                    to_remove.append(second_id)
    if to_add == [] and to_remove == []:
        logger_setup.get_logger().info(f'No changes to {many_table}')
        release_savepoint('update_many_table')
        return True
    if to_remove:
        for id in to_remove:
            query.prepare(
                f"DELETE FROM {many_table} WHERE {first_table_id_header} {query_where_str} AND {second_table_id_header} = {id}")
            if not query.exec():
                logger_setup.get_logger().critical(f"Error unchecking {second_table} from {first_table}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('update_many_table')
                return False
        logger_setup.get_logger().info(f"Removed {to_remove} associated with item IDs {first_table_ids} from {many_table}")
    if to_add:
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

eventTypeNames = {event_type: event_type.name for event_type in QtC.QEvent.Type}