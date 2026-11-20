import sqlite3
import time
import typing

import numpy as np
import pandas as pd
import qtawesome
from PyQt6 import QtCore, QtGui, QtSql
from PyQt6.QtCore import QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QFont, QBrush, QColor
from PyQt6.QtSql import QSqlQuery, QSqlDatabase
from PyQt6.QtWidgets import QApplication, QProgressDialog

import logger_setup
from Functions.Database_views import ViewQuery
from Functions.Settings_manager import SettingsManager
from Functions.Widget_classes import get_name_column, get_view_from_table, get_headers, update_other_table_with_checks, \
    get_total_records, get_name_from_id, update_many_table_with_checks, strip_strings
from util.display_formatting import display_value_with_error, display_gps, display_age, return_rounded
from util.loading_dialog_manager import close_loading_dialog, show_loading_dialog, LoadingDialogManager
from util.widgets.models.query_models import CheckableSqlQueryModel

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

    def setData(self, index, value, role=...) -> bool | None:
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
        logger_setup.get_logger().info(
            f"Removing rows for IDs {', '.join(str(remove_id) for remove_id in ids_to_remove)} from {self.table}")
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self._data) - 1)
        ids_to_remove.sort(reverse=False)
        new_data = self._data.copy()  # Create a copy of the data to avoid modifying while iterating
        for row in self._data:
            # The first column is assumed to be the primary key
            if row[0] in ids_to_remove:
                new_data.remove(row)
        self._data = new_data
        self.endRemoveRows()
        logger_setup.get_logger().info(
            f"Removed rows for IDs {', '.join(str(remove_id) for remove_id in ids_to_remove)} from {self.table}")
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
                    logger_setup.get_logger().info(
                        f'This ID does not exist in the query any more. May be removed from this model in a later step.')
                row_data = [query.value(column) for column in range(self.columnCount())]
                self._data[row] = row_data
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))
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


class CheckableSQLiteTableModel(SQLiteTableModel):
    """
    Custom SQLiteTableModel with check boxes enabled for each row.
    Name column has a tool tip with the description if available
    Supports partial checks through code, but any user input only toggles checked or unchecked.
    Stores lists of checked_ids and partially_checked_ids.
    """
    checksChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.checked_ids = set()
        self.partially_checked_ids = set()
        self.primary_key_column = 0
        self.single_click = False
        self.not_null = False

    def flags(self, index):
        """Set check boxes on the name column only"""
        flags = super().flags(index)
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col:
            flags |= QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = get_name_column(get_view_from_table(self.tableName()))
        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.checked_ids:
                return QtCore.Qt.CheckState.Checked
            elif self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                return QtCore.Qt.CheckState.PartiallyChecked
            else:
                return QtCore.Qt.CheckState.Unchecked
        elif index.column() == col and role == QtCore.Qt.ItemDataRole.ToolTipRole:
            description_col = None
            for header_col in range(self.columnCount()):
                header = self.headerData(header_col, QtCore.Qt.Orientation.Horizontal,
                                         QtCore.Qt.ItemDataRole.DisplayRole)
                if 'Description' in header:
                    description_col = header_col
                    break
            if description_col is not None:
                return super().data(self.index(index.row(), description_col), QtCore.Qt.ItemDataRole.DisplayRole)
        return super().data(index, role)

    def setData(self, index: QtCore.QModelIndex, value, role: QtCore.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid():
            return super().setData(index, value, role)
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            item_id = self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if not item_id:
                logger_setup.get_logger().debug(f'No ID found for row {index.row()} in {self.tableName()}')
                return False
            if value == QtCore.Qt.CheckState.Checked:
                if item_id not in self.checked_ids:
                    self.checked_ids.add(item_id)
            elif value == QtCore.Qt.CheckState.PartiallyChecked:
                if item_id not in self.partially_checked_ids:
                    self.partially_checked_ids.add(item_id)
            else:
                if item_id in self.checked_ids:
                    self.checked_ids.remove(item_id)
                if item_id in self.partially_checked_ids:
                    self.partially_checked_ids.remove(item_id)
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def clear_checks(self):
        """
        Clears the check state of all items in the model.
        This method clears the checked_id and partially_checked_ids sets.
        """
        if self.checked_ids or self.partially_checked_ids:
            self.update_model_checks(set(), set())

    def check_all(self):
        """
        Adds all IDs in the source model to the set of checked_ids and clear the set of
        partially_checked_ids.
        """
        all_ids = set()
        for row in range(self.rowCount()):
            item_id = self.index(row, 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if item_id:
                all_ids.add(item_id)
        self.update_model_checks(all_ids, set())

    def update_model_checks(self, checked_items: set[int], partially_checked_items: set[int]):
        """
        Checks the checkable items in the model based on the provided sets of checked and partially checked IDs.
        This method updates the checked_id and partially_checked_ids sets.
        :param checked_items: set of item IDs that should be checked
        :param partially_checked_items: set of item IDs that should be partially checked
        :return:
        """
        if self.checked_ids != checked_items or self.partially_checked_ids != partially_checked_items:
            self.checked_ids = checked_items
            self.partially_checked_ids = partially_checked_items
            logger_setup.get_logger().info(f'{self.table} checks updated')
            self.checksChanged.emit()

    def return_checked_ids(self):
        """Returns a list of checked_ids and a list of partially_checked_ids"""
        return list(self.checked_ids), list(self.partially_checked_ids)

    def selected_items_string(self):
        """
        Returns a list of strings representing the items selected by the user.
        Includes both checked and partially checked items.
        """
        selected_names = set()
        for checked_id in self.checked_ids:
            name = get_name_from_id(self.tableName(), checked_id)
            if name is not None:
                selected_names.add(name)
        for partially_checked_id in self.partially_checked_ids:
            name = get_name_from_id(self.tableName(), partially_checked_id)
            if name is not None:
                selected_names.add(name)
        # Sort the names alphabetically (case-insensitive) and return as a semicolon separated string
        return '; '.join(sorted(selected_names, key=lambda s: s.lower()))

    def update_other_table(self, other_table: str, other_ids: list) -> str:
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
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return 'False'
        if self.partially_checked_ids:
            # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
            logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
            return 'No'
        if len(self.checked_ids) > 1:
            # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
            logger_setup.get_logger().error(
                f'Multiple checked IDs given for {self.tableName()}. Select only one ID to update {other_table}.')
            logger_setup.get_logger().debug(
                f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
            return 'False'
        return update_other_table_with_checks(self.table, list(self.checked_ids), list(self.partially_checked_ids),
                                              other_table, other_ids)

    def update_many_table(self, many_table: str, item_ids: list) -> str:
        """
        Updates many-to-many relationship with another table. This method is useful when editing joined views, like
        editing the Units associated with Samples.
        :param many_table: name of the many-to-many table to update (e.g. Samples_Units)
        :param item_ids: list of foreign IDs to update in the many-to-many table (e.g. SampleIDs)
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return 'False'
        return update_many_table_with_checks(self.table, list(self.checked_ids), list(self.partially_checked_ids),
                                             many_table, item_ids)


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

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        if index.row in self.bolded_rows and role == QtCore.Qt.ItemDataRole.FontRole:
            font = QtGui.QFont()
            font.setBold(True)
            return font
        if index.column() == 1 and role == QtCore.Qt.ItemDataRole.DisplayRole:
            string = super().data(index, role)
            return display_age(string)
        return super().data(index, role)

    def make_bold(self, index):
        """Age is the default age for a sample and should be marked as bold"""
        row = index.row()
        if row not in self.bolded_rows:
            self.bolded_rows.append(row)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.FontRole])

    def make_not_bold(self, index):
        """Age is not a default age for any sample and should be marked as bold"""
        row = index.row()
        if row in self.bolded_rows:
            self.bolded_rows.remove(row)
            self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.FontRole])


class DisplayRoundedTableModel(QtSql.QSqlTableModel):
    """
    Custom QSqlTableModel to display the data of a SQLite database table with rounded values.
    This model was created to display the data in a more user-friendly way, such as rounding.
    """

    def __init__(self, db=QSqlDatabase()):
        super().__init__(db=db)

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        """
        Return the data for the given index and role.
        :param index: table index
        :param role: expecting DisplayRole
        :return: False if index is invalid, otherwise return the user-readable data stored in the model at the given index
        """
        if not index.isValid():
            return False
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            # check the header of the selected index
            header = self.headerData(index.column(), QtCore.Qt.Orientation.Horizontal,
                                     QtCore.Qt.ItemDataRole.DisplayRole)
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
        if (self.tableName().endswith('Formats') or self.tableName().endswith(
                'Units')) and role == QtCore.Qt.ItemDataRole.ToolTipRole:
            format_name = self.index(index.row(), 1).data(QtCore.Qt.ItemDataRole.DisplayRole)
            return format_name

        return super().data(index, role)

    def unrounded_data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        """
        Return the raw data for the given index and role.
        :param index: table index
        :param role: any
        :return: same as super().data(index, role)
        """
        return super().data(index, role)


class CheckableSqlTableModel(DisplayRoundedTableModel):
    """
    Custom DisplayRoundedTableModel (subclass of QSqlTableModel) with check boxes enabled for each row.
    Name column has a tool tip with the description if available
    Supports partial checks through code, but any user input only toggles checked or unchecked.
    Stores lists of checked_ids and partially_checked_ids.
    Setting single_click to True will upon click uncheck all items except the one clicked, forcing the user to select
    only one item at a time.
    Setting not_null to True will prevent the user from unchecking all items, ensuring that at least one item is always
    selected.
    """
    checksChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.primary_key_column = 0
        self.checked_ids = set()
        self.partially_checked_ids = set()
        self.single_click = False
        self.not_null = False

    def flags(self, index):
        """Set check boxes on the name column only"""
        index_flags = super().flags(index)
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col:
            index_flags |= QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        return index_flags

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        if not index.isValid():
            return False
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.checked_ids:
                return QtCore.Qt.CheckState.Checked
            elif self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                return QtCore.Qt.CheckState.PartiallyChecked
            else:
                return QtCore.Qt.CheckState.Unchecked
        elif index.column() == col and role == QtCore.Qt.ItemDataRole.ToolTipRole:
            description_col = None
            for header_col in range(self.columnCount()):
                header = self.headerData(header_col, QtCore.Qt.Orientation.Horizontal,
                                         QtCore.Qt.ItemDataRole.DisplayRole)
                if 'Description' in header:
                    description_col = header_col
                    break
            if description_col is not None:
                return super().data(self.index(index.row(), description_col), QtCore.Qt.ItemDataRole.DisplayRole)
        return super().data(index, role)

    def setData(self, index: QtCore.QModelIndex, value, role: QtCore.Qt.ItemDataRole = ...) -> bool:
        if not index.isValid():
            return super().setData(index, value, role)
        col = get_name_column(get_view_from_table(self.tableName()))
        if index.column() == col and role == QtCore.Qt.ItemDataRole.CheckStateRole:
            item_id = self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if not item_id:
                logger_setup.get_logger().debug(f'No ID found for row {index.row()} in {self.tableName()}')
                return False
            if value == QtCore.Qt.CheckState.Checked:
                if item_id not in self.checked_ids:
                    self.checked_ids.add(item_id)
                if item_id in self.partially_checked_ids:
                    self.partially_checked_ids.remove(item_id)
            elif value == QtCore.Qt.CheckState.PartiallyChecked:
                if item_id not in self.partially_checked_ids:
                    self.partially_checked_ids.add(item_id)
                if item_id in self.checked_ids:
                    self.checked_ids.remove(item_id)
            else:
                if self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.checked_ids:
                    self.checked_ids.remove(self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole))
                if self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole) in self.partially_checked_ids:
                    self.partially_checked_ids.remove(
                        self.index(index.row(), 0).data(QtCore.Qt.ItemDataRole.DisplayRole))
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def clear_checks(self):
        """
        Clears the check state of all items in the model.
        This method clears the checked_id and partially_checked_ids sets.
        """
        if self.checked_ids or self.partially_checked_ids:
            self.update_model_checks(set(), set())

    def check_all(self):
        """
        Adds all IDs in the source model to the set of checked_ids and clear the set of
        partially_checked_ids.
        """
        all_ids = set()
        for row in range(self.rowCount()):
            item_id = self.index(row, 0).data(QtCore.Qt.ItemDataRole.DisplayRole)
            if item_id:
                all_ids.add(item_id)
        self.update_model_checks(all_ids, set())

    def update_model_checks(self, checked_items: set[int], partially_checked_items: set[int]):
        """
        Checks the checkable items in the model based on the provided sets of checked and partially checked IDs.
        This method updates the checked_id and partially_checked_ids sets.
        :param checked_items: set of item IDs that should be checked
        :param partially_checked_items: set of item IDs that should be partially checked
        :return:
        """
        if self.checked_ids != checked_items or self.partially_checked_ids != partially_checked_items:
            self.checked_ids = checked_items
            self.partially_checked_ids = partially_checked_items
            self.checksChanged.emit()

    def return_checked_ids(self):
        """Returns a list of checked_ids and a list of partially_checked_ids"""
        return list(self.checked_ids), list(self.partially_checked_ids)

    def selected_items_string(self):
        """
        Returns a list of strings representing the items selected by the user.
        Includes both checked and partially checked items.
        """
        selected_names = set()
        for checked_id in self.checked_ids:
            name = get_name_from_id(self.tableName(), checked_id)
            if name is not None:
                selected_names.add(name)
        for partially_checked_id in self.partially_checked_ids:
            name = get_name_from_id(self.tableName(), partially_checked_id)
            if name is not None:
                selected_names.add(name)
        # Sort the names alphabetically (case-insensitive) and return as a semicolon separated string
        return '; '.join(sorted(selected_names, key=lambda s: s.lower()))

    def update_other_table(self, other_table: str, other_ids: list) -> str:
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
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not other_ids:
            logger_setup.get_logger().error(f'No item IDs given for {other_table}')
            return 'False'
        if self.partially_checked_ids:
            # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
            logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
            return 'No'
        if len(self.checked_ids) > 1:
            # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
            logger_setup.get_logger().error(
                f'Multiple checked IDs given for {self.tableName()}. Select only one ID to update {other_table}.')
            logger_setup.get_logger().debug(
                f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
            return 'False'
        return update_other_table_with_checks(self.tableName(), list(self.checked_ids),
                                              list(self.partially_checked_ids), other_table, other_ids)

    def update_many_table(self, many_table: str, item_ids: list) -> str:
        """
        Updates many-to-many relationship with another table. This method is useful when editing joined views, like
        editing the Units associated with Samples.
        :param many_table: name of the many-to-many table to update (e.g. Samples_Units)
        :param item_ids: list of foreign IDs to update in the many-to-many table (e.g. SampleIDs)
        :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
        """
        if not item_ids:
            logger_setup.get_logger().error(f'No item IDs given for {many_table}')
            return 'False'
        return update_many_table_with_checks(self.tableName(), list(self.checked_ids), list(self.partially_checked_ids),
                                             many_table, item_ids)


class LazyCheckableSqlTableModel(CheckableSqlTableModel):
    """
    Custom CheckableSqlTableModel that only loads items when they are first visible.
    Uses the canFetchMore and fetchMore methods to load items in batches when needed, which improves performance for large tables.
    """

    def __init__(self):
        super().__init__()
        self.batch_size = 1000  # Number of rows to load in each batch
        self.loaded_row_count = 0  # Number of rows currently loaded
        self.total_rows = 0  # Number of rows that can be loaded

    def setTable(self, tableName: typing.Optional[str]):
        super().setTable(tableName)
        self.total_rows = get_total_records(self.tableName())

    def rowCount(self, parent=None):
        # Return the number of loaded rows
        return self.loaded_row_count

    def canFetchMore(self, parent=None):
        # Check if there are more rows to load
        return self.loaded_row_count < self.total_rows

    def fetchMore(self, parent=None):
        # Load the next batch of rows
        remaining_rows = self.total_rows - self.loaded_row_count
        rows_to_load = min(self.batch_size, remaining_rows)

        if rows_to_load > 0:
            # Fetch the next batch of rows from the database
            self.beginInsertRows(QtCore.QModelIndex(), self.loaded_row_count, self.loaded_row_count + rows_to_load - 1)
            self.loaded_row_count += rows_to_load
            self.endInsertRows()
            logger_setup.get_logger().debug(
                f'Loaded {rows_to_load} more rows for {self.tableName()}, total loaded: {self.loaded_row_count}/{self.total_rows}')

    def data(self, index: QtCore.QModelIndex = ..., role: QtCore.Qt.ItemDataRole = ...):
        # Override data method to ensure that only loaded rows are accessed
        if index.row() >= self.loaded_row_count:
            return None  # Return None for rows that are not yet loaded
        return super().data(index, role)


class ImportSheetTableModel(QAbstractTableModel):
    """
    Class to load an openpyxl worksheet into a pandas DataFrame and display it in a QTableView.
    Adds a DataFrame for row status (accepted, rejected, disabled).
    :param sheet:
    :param check_style:
    :param parent:
    """
    userDataChanged = QtCore.pyqtSignal(QModelIndex, QModelIndex, list)

    def __init__(self, sheet, check_style=False, parent=None):
        super().__init__(parent=parent)
        # drop empty rows and columns from the dataframe
        self.sheet = sheet
        non_empty_rows = []
        sheet_rows = []
        for row in sheet.iter_rows(values_only=True):
            sheet_rows.append(row)
        self._dataframe = pd.DataFrame(sheet_rows)
        # strip strings for all items in the dataframe
        self._dataframe = self._dataframe.map(strip_strings)
        # Replace any cells with only whitespace or "" with nan
        self._dataframe.replace(to_replace=r'^\s*$', value=np.nan, regex=True, inplace=True)
        # Replace any cells with only "NULL" (case insensitive) with nan
        self._dataframe.replace(to_replace='NULL', value=np.nan, regex=True, inplace=True)
        # Fill None with nan
        self._dataframe.fillna(value=np.nan, inplace=True)
        # Fill all nan with 'NULL'
        self._dataframe.replace(to_replace=np.nan, value='NULL', regex=True, inplace=True)
        self.header_background_brushes = {}
        self.cell_background_brushes = {}
        # Rename headers as integer of their column index
        column_headers = list(self._dataframe.columns)
        for column_header in column_headers:
            column_index = column_headers.index(column_header)
            if column_header != column_index:
                self._dataframe.columns.values[column_index] = column_index
        # Create another dataframe to store row status, accepted, rejected, disabled. Default accepted.
        # Also store the text color and strikethrough font. Default np.nan
        self._status_dataframe = pd.DataFrame({'_row_status': ['accepted'] * len(self._dataframe),
                                               '_color': [np.nan] * len(self._dataframe),
                                               '_strikethrough': [np.nan] * len(self._dataframe)})
        self.rejected_icon = qtawesome.icon('fa5s.minus-circle', color='red', scale_factor=1.0)
        self.accepted_icon = qtawesome.icon('fa5s.check', color='green', scale_factor=1.0)

        # todo these need to be switched over to color settings
        self.gray_brush = QBrush(QColor("#A0A0A0"))
        self.red_brush = QBrush(QColor("red"))
        self.transparent_brush = QBrush(QtCore.Qt.GlobalColor.transparent)

        if check_style:
            self.style_model()

        self.reset_row_headers()
        self._data_array = self._dataframe.to_numpy()
        self._status_array = self._status_dataframe.to_numpy()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent == QtCore.QModelIndex():
            return len(self._dataframe)
        return 0

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if parent == QtCore.QModelIndex():
            return len(self._dataframe.columns)
        return 0

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
            value = str(self._data_array[index.row(), index.column()])
            return 'NULL' if value == 'nan' else str(value)
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Return the cell background color if set
            return self.cell_background_brushes.get(index, self.transparent_brush)
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            # Return gray text if the row is disabled
            status = self._status_array[index.row(), 0]
            if status == 'disabled':
                # logger_setup.get_logger().debug(f'Setting gray text for disabled row {index.row()}')
                return self.gray_brush  # Gray text
            elif isinstance(self._status_array[index.row(), 1], QBrush):
                return self._status_array[index.row(), 1]
        elif role == QtCore.Qt.ItemDataRole.FontRole:
            if isinstance(self._status_array[index.row(), 2], QFont):
                return self._status_array[index.row(), 2]

        # return super().data(index, role)
        return None

    def setData(self, index: QtCore.QModelIndex, value,
                role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return super().setData(index, value, role)
        if role in [QtCore.Qt.ItemDataRole.EditRole, QtCore.Qt.ItemDataRole.DisplayRole]:
            if self._dataframe.iat[index.row(), index.column()] != value:
                self._dataframe.iat[index.row(), index.column()] = value
                self.dataChanged.emit(index, index, [role])
                if role == QtCore.Qt.ItemDataRole.EditRole:
                    self.userDataChanged.emit(index, index, [role])
                self._data_array[index.row(), index.column()] = value
            return True
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Update the cell background color
            self.cell_background_brushes[index] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return None

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation,
                   role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return str(self._dataframe.index[section])
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                # Return the column header background color if set
                return self.header_background_brushes.get(section, self.transparent_brush)
        if role == QtCore.Qt.ItemDataRole.DecorationRole and orientation == QtCore.Qt.Orientation.Vertical:
            status = self._status_array[section, 0]
            if status == 'accepted':
                return self.accepted_icon
            elif status == 'rejected':
                return self.rejected_icon
            elif status == 'disabled':
                return None  # No icon for disabled
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return "Double click to define/map column data"
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return 'Double Click to accept/reject analysis data\nright click for more options'

        return super().headerData(section, orientation, role)

    def setHeaderData(self, section, orientation, value,
                      role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.EditRole):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.EditRole:
            if value != self._dataframe.columns[section]:
                self._dataframe.rename({self._dataframe.columns[section]: value}, axis=1, inplace=True)
                self.headerDataChanged.emit(orientation, section, section)
            return True
        elif orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.BackgroundRole:
            # Update the column header background color
            if section not in self.header_background_brushes or self.header_background_brushes[section] != value:
                self.header_background_brushes[section] = value
                self.headerDataChanged.emit(orientation, section, section)
            return True
        elif orientation == QtCore.Qt.Orientation.Vertical:
            if role == QtCore.Qt.ItemDataRole.DecorationRole:
                # Update the row status based on the value
                if value in ['accepted', 'rejected', 'disabled'] and self._status_array[section, 0] != value:
                    self._status_dataframe.iat[section, 0] = value
                    self.headerDataChanged.emit(orientation, section, section)
                    # Also update the foreground color of all cells in the row
                    for column in range(self.columnCount()):
                        index = self.index(section, column)
                        self.dataChanged.emit(index, index, [QtCore.Qt.ItemDataRole.ForegroundRole])
                    self._status_array = self._status_dataframe.to_numpy()
                    return True
        return super().setHeaderData(section, orientation, value, role)

    def removeSelectedRows(self, rows: list) -> bool:
        """
        Removes rows from the table based on provided row indices.
        :param rows: list of row indices to remove from the table
        :return: True for success, False otherwise
        """
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self._dataframe) - 1)
        rows.sort(reverse=True)
        for row in rows:
            if row == self.rowCount() - 1:
                # dropping the last row
                self._dataframe.drop(self._dataframe.tail(1).index, axis=0, inplace=True)
                self._status_dataframe.drop(self._status_dataframe.tail(1).index, axis=0, inplace=True)
            else:
                self._dataframe.drop(self._dataframe.index[row], axis=0, inplace=True)
                self._status_dataframe.drop(self._status_dataframe.index[row], axis=0, inplace=True)
        self._dataframe.reset_index(drop=True, inplace=True)
        self._status_dataframe.reset_index(drop=True, inplace=True)
        self._data_array = self._dataframe.to_numpy()
        self._status_array = self._status_dataframe.to_numpy()
        self.endRemoveRows()
        return True

    def removeRow(self, row: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Removes a row from the table based on provided row index.
        :param row: row index to remove from the table
        :param parent:
        :return: True for success, False otherwise
        """
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        if row == self.rowCount() - 1:
            # dropping the last row
            self._dataframe.drop(self._dataframe.tail(1).index, axis=0, inplace=True)
            self._status_dataframe.drop(self._status_dataframe.tail(1).index, axis=0, inplace=True)
        else:
            self._dataframe.drop(self._dataframe.index[row], axis=0, inplace=True)
            self._status_dataframe.drop(self._status_dataframe.index[row], axis=0, inplace=True)
        self._dataframe.reset_index(drop=True, inplace=True)
        self._dataframe.index = np.arange(1, len(self._dataframe) + 1)
        self._status_dataframe.reset_index(drop=True, inplace=True)
        self._status_dataframe.index = np.arange(1, len(self._status_dataframe) + 1)
        self._data_array = self._dataframe.to_numpy()
        self._status_array = self._status_dataframe.to_numpy()
        self.endRemoveRows()
        return True

    def removeSelectedColumns(self, columns: list) -> bool:
        """
        Removes columns from the table based on provided column indices.
        :param columns: list of column indices to remove from the table
        :return: True for success, False otherwise
        """
        self.beginResetModel()
        columns.sort(reverse=True)
        for col in columns:
            self._dataframe.drop(self._dataframe.columns[col], axis=1, inplace=True)
        self._data_array = self._dataframe.to_numpy()
        self.endResetModel()
        return True

    def removeColumn(self, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Removes a column from the table based on the provided column index.
        :param column: column index to remove from the table
        :param parent:
        :return: True for success, False otherwise
        """
        self.beginRemoveColumns(QtCore.QModelIndex(), column, column)
        self._dataframe.drop(self._dataframe.columns[column], axis=1, inplace=True)
        self._data_array = self._dataframe.to_numpy()
        self.endRemoveColumns()
        return True

    def insertColumns(self, column: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Inserts columns into the table at the given position.
         New columns will be named "{column+count}", and any headers to the left that are the same as their index will be
         renamed to match their new index.
        :param column:
        :param count:
        :param parent:
        :return:
        """
        self.beginInsertColumns(parent, column, column + count - 1)
        for i in range(count):
            new_col_name = f'{column + 1}'
            self._dataframe.insert(column, new_col_name, 'NULL')
        self.endInsertColumns()

        # Rename any integer headers to the right to match their new index
        for col in range(column, len(self._dataframe.columns)):
            try:
                header = int(self._dataframe.columns[col])
                if header != col:
                    self._dataframe.columns.values[col] = col
            except ValueError:
                # This header is not an integer, so skip it
                continue
        self._data_array = self._dataframe.to_numpy()
        return True

    def insertColumn(self, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Inserts a column into the table at the given position.
        :param column:
        :param parent:
        :return:
        """
        self.beginInsertColumns(QtCore.QModelIndex(), column, column)
        new_column = ['NULL'] * len(self._dataframe.index)
        new_df = pd.DataFrame(new_column, index=self._dataframe.index)
        upper_df = self._dataframe.iloc[:, :column]
        lower_df = self._dataframe.iloc[:, column:]
        self._dataframe = pd.concat([upper_df, new_df, lower_df], axis=1)
        # self._dataframe.fillna('NULL', inplace=True)
        self.endInsertColumns()
        # Rename any integer headers to the right to match their new index
        for col in range(column, len(self._dataframe.columns)):
            try:
                header = int(self._dataframe.columns[col])
                if header != col:
                    self._dataframe.columns.values[col] = col
            except ValueError:
                # This header is not an integer, so skip it
                continue
        self._data_array = self._dataframe.to_numpy()
        return True

    def reset_row_headers(self):
        """
        Resets the row headers to be sequential integers starting from 1.
        """
        self.beginResetModel()
        self._dataframe.index = [str(i + 1) for i in self._dataframe.index]
        self._status_dataframe.index = [str(i + 1) for i in self._status_dataframe.index]
        self.endResetModel()

    def rows_for_status(self, status: str):
        """
        Returns the row index (not header) for all rows with the given status.
        :param status: 'accepted', 'rejected', or 'disabled'
        :return:
        """
        if status in ['accepted', 'rejected', 'disabled']:
            df = self._status_dataframe.copy()
            df.reset_index(drop=True, inplace=True)
            return df.index[df['_row_status'] == status].tolist()
        else:
            return []

    def return_row_status(self, row) -> str:
        """
        Returns the row status of the index's row.
        """
        return str(self._status_array[row, 0])

    def update_row_status(self, row, status: str):
        """
        Updates the row status and icon of the index's row.
        """
        if status in ['accepted', 'rejected', 'disabled']:
            self._status_dataframe.iat[row, 0] = status
            self._status_array[row, 0] = status

    def style_model(self):
        """
        Styles the model by getting the font and color for each cell in the sheet based on its content.
        """
        if self.sheet.max_row != self.rowCount():
            logger_setup.get_logger().error(
                'Rows have been removed and can no longer be mapped to the original import file.\n\nSave the current mapping, reload the import file, and select the checkbox before removing rows.')
            return False
        if self.rowCount() != self._status_dataframe.shape[0]:
            logger_setup.get_logger().critical(
                'Data are unsynced.\n\nSave the current mapping and reload the import file.')
            return False

        logger_setup.get_logger().info('Identifying rejected rows by style')
        show_loading_dialog('Loading', 'Identifying rejected rows...')

        style_progress_dialog = QProgressDialog(
            "Identifying rejected rows...", "Cancel", 0, self.sheet.max_row + 1,
            LoadingDialogManager.get_instance().dialog
        )

        for row in range(1, self.sheet.max_row + 1):
            style_progress_dialog.setValue(row)
            QApplication.processEvents()
            if style_progress_dialog.wasCanceled():
                close_loading_dialog('Loading', 'Identifying rejected rows...')
                return False
            for col in range(1, self.sheet.max_column):
                if col > self.columnCount():
                    continue
                if self._status_array[row - 1, 0] == 'rejected':
                    continue
                cell = self.sheet.cell(row=row, column=col)
                if cell.font:
                    font = cell.font
                    if font.color and hasattr(font.color, "rgb") and isinstance(font.color.rgb, str):
                        hex_col = "#" + font.color.rgb[-6:]
                        # if the color is red or close to red set the row to rejected automatically
                        if hex_col.lower() in ["#EB1800", "#FF00000"]:  # Red
                            self._status_dataframe.iat[row - 1, 0] = 'rejected'
                            self._status_dataframe.iat[row - 1, 1] = self.red_brush
                            break
                    # if the row is struck through auto set rejected
                    if font.strike:
                        self._status_dataframe.iat[row - 1, 0] = 'rejected'
                        font = QFont()
                        font.setStrikeOut(True)
                        self._status_dataframe.iat[row - 1, 2] = font
                        break
        style_progress_dialog.setValue(row + 1)
        QApplication.processEvents()
        if style_progress_dialog.wasCanceled():
            close_loading_dialog('Loading', 'Identifying rejected rows...')
            return False

        logger_setup.get_logger().info('Identified rejected rows by style')
        close_loading_dialog('Loading', 'Identifying rejected rows...')
        self._status_array = self._status_dataframe.to_numpy()
        return True

    def unstyle_model(self):
        # Default font color
        for row in range(self.rowCount()):
            self._status_dataframe.iat[row + 1, 0] = 'rejected'
            self._status_dataframe.iat[row + 1, 1] = np.nan
            self._status_dataframe.iat[row + 1, 2] = np.nan
        self._status_array = self._status_dataframe.to_numpy()

    def clear_all_background_colors(self):
        """
        Sets all backgrounds to default which is usually transparent
        """
        self.cell_background_brushes = {}
