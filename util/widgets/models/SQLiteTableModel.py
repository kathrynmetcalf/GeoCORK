import sqlite3
import time

from PyQt6 import QtCore
from PyQt6.QtCore import QAbstractTableModel
from PyQt6.QtSql import QSqlQuery

import logger_setup
from Functions.Database_views import ViewQuery
from Functions.Settings_manager import SettingsManager
from Functions.Widget_classes import display_value_with_error, display_gps, get_name_column, get_view_from_table, \
    display_age, return_rounded, get_headers

settings = SettingsManager().settings

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
        self.view_query = view_query

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
                cursor.execute(query)
                self._data = cursor.fetchall()
                self._headers = [desc[0] for desc in cursor.description]
                logger_setup.get_logger().debug(f"Model populated in {time.time() - start_time} seconds")
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f"Error executing query")
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

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """
        Return the data for the given index and role.
        :param index: table index
        :param role: expecting DisplayRole
        :return: data stored in the model at the given index or None if the index is invalid or role is not DisplayRole
        """
        if not index.isValid():
            return None  # Return None instead of False to avoid type errors

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
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

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """
        Return column headers.
        :param section: column index
        :param orientation: orientation of the header (horizontal or vertical)
        :param role: expecting DisplayRole
        """
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._headers[section]  # Ensure headers are stored properly
        return super().headerData(section, orientation, role)

    def setHeaderData(self, section, orientation, value, role=QtCore.Qt.ItemDataRole.EditRole):
        """
        Allow renaming of column headers.
        :param section: column index
        :param orientation: orientation of the header (horizontal or vertical)
        :param value: new header value
        """
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.EditRole:
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
        if not index.isValid():
            return super().setData(index, value, role)
        if role == QtCore.Qt.ItemDataRole.EditRole:
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
            self._data = list(data_list)
            self.edited_indexes.append(index)
            if self._data[index.row()][index.column()] == value:
                self.dataChanged.emit(index, index)
            return self._data[index.row()][index.column()] == value
        return super().setData(index, value, role)

    def removeRows(self, ids_to_remove: list) -> bool:
        """
        Removes rows from the table based on provided primary key ids for the table.
        :param ids_to_remove: list of ids to remove from the table
        :return: True for success, False otherwise
        """
        logger_setup.get_logger().info(f"Removing rows for IDs {', '.join(str(remove_id) for remove_id in ids_to_remove)} from {self.table}")
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self._data) - 1)
        ids_to_remove.sort(reverse=False)
        new_data = self._data.copy()  # Create a copy of the data to avoid modifying while iterating
        for row in self._data:
            # The first column is assumed to be the primary key
            if row[0] in ids_to_remove:
                new_data.remove(row)
        self._data = new_data
        self.endRemoveRows()
        logger_setup.get_logger().info(f"Removed rows for IDs {', '.join(str(remove_id) for remove_id in ids_to_remove)} from {self.table}")
        return True

    def insertRow(self, row_data: list) -> bool:
        """
        Inserts rows into the table. Rows provided should be in the same format as the table.
        :param row_data: list of row data that will be inserted into the table
        :return: True for success, False otherwise
        """
        self.beginInsertRows(QtCore.QModelIndex(), len(self._data), len(self._data))
        self._data.append(row_data)
        self.endInsertRows()
        logger_setup.get_logger().info(f'Updated {self.table}')
        return True

    def canFetchMore(self, parent=None):
        """
        SQLiteTableModel already selects all data at once, so no more data to fetch.
        :return:
        """
        return False

    def update_id_rows_from_db(self, update_ids: list) -> bool:
        """
        Replace row data for certain IDs from the database using a QSqlQuery and the query and/or view query
        """
        query = QSqlQuery()
        if self.view_query:
            show_columns = self.view_query.show_columns
            group_col = self.view_query.group_col
            order_col = self.view_query.order_col
            limit = self.view_query.limit
        for row in range(len(self._data)):
            if self._data[row][0] in update_ids:
                where = f'WHERE {get_headers(self.table)[0]} = {self._data[row][0]}'
                if self.view_query:
                    view_query = ViewQuery(self.table, True, **{'show_columns': show_columns, 'where': where,
                                                                'group_col': group_col, 'order_col': order_col,
                                                                'limit': limit})
                    query_text = view_query.table_query
                else:
                    query_text = f'{self.query_text.split(' WHERE ')[0]} {where}'
                if not query.exec(query_text):
                    logger_setup.get_logger().critical(f'Error updating {self.table} display')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    return False
                if not query.next():
                    logger_setup.get_logger().info(f'This ID does not exist in the query any more. May be removed from this model in a later step.')
                row_data = [query.value(column) for column in range(self.columnCount())]
                self._data[row] = row_data
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() -1 , self.columnCount() - 1))
        return True

    def insert_id_rows_from_db(self, add_ids: list) -> bool:
        """
        Inserts rows into the table based on list of IDs in the table. Rows provided should be in the same format as the table.
        """
        query = QSqlQuery()
        if self.view_query:
            show_columns = self.view_query.show_columns
            group_col = self.view_query.group_col
            order_col = self.view_query.order_col
            limit = self.view_query.limit
        for add_id in add_ids:
            where = f'WHERE {get_headers(self.table)[0]} = {add_id}'
            if self.view_query:
                view_query = ViewQuery(self.table, True, **{'show_columns': show_columns, 'where': where,
                                                            'group_col': group_col, 'order_col': order_col,
                                                            'limit': limit})
                query_text = view_query.table_query
            else:
                query_text = f'{self.query_text.split(' WHERE ')[0]} {where}'
            if not query.exec(query_text):
                logger_setup.get_logger().critical(f'Error updating {self.table} display')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False
            if not query.next():
                logger_setup.get_logger().info(
                    f'This ID does not exist in the query any more. May be removed from this model in a later step.')
            row_data = [query.value(column) for column in range(self.columnCount())]
            if not self.insertRow(row_data):
                return False
        return True