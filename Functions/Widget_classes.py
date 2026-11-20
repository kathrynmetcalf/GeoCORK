import time
from collections import namedtuple
from difflib import SequenceMatcher

from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtSql import QSqlQuery, QSqlDatabase

import util.Text_manipulations as TxM
import logger_setup
from Functions import SQLUtils
from Functions.Check_triggers import update_modified_timestamp
from util.loading_dialog_manager import show_loading_dialog, close_loading_dialog
from Functions.Database_views import ViewQuery
from util.database.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
from util.database.database_helper import get_join_from_table


settings = SettingsManager().settings


# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'reference_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")


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
    from util.widgets.models.LazyCheckableSqlTableModel import LazyCheckableSqlTableModel
    if not isinstance(model, LazyCheckableSqlTableModel):
        while model.canFetchMore():
            model.fetchMore()
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
    table = table.replace('"', '').strip()
    if not query.exec(f'PRAGMA table_xinfo("{table}")'):
        logger_setup.get_logger().critical(f"Failed to get headers for {table}")
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return []
    headers = []
    while query.next():
        headers.append(query.value(1))
    return headers

def get_columns(table: str, database: QSqlDatabase=None):
    """
    Return table columns by type for virtual, stored, and regular columns. Considers everything after the modified
    column to be a virtual column and any column before modified with a header containing 'Display' or 'Calculated'
    to be a stored column.
    :param table: Name of the SQL database table
    :param database: QSqlDatabase connection to use. If None, uses the default connection.
    :return query: Query used to collect columns
    :return virtual: list of virtual column names
    :return stored: list of stored column names
    :return columns: list of regular column names
    """
    if not database:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
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
    if not table:
        return None
    table = table.replace('"', '').strip()
    if (table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees or
            table in ['Ages', 'AliquotView', 'AliquotEditView', 'GrainView', 'GrainEditView']):
        return 3
    elif 'Format' in table or 'Unit' in table:
        # return the column for the abbreviation
        return 2
    elif table == 'References' or table == '"References"':
        return 9
    elif (table in SQLUtils.user_viewable_tables or
          table in ['SampleView', 'SampleEditView', 'Spots', 'GPSLocations', 'FilterGroups', 'ReferenceView',
                    'ReferenceEditView', 'ColumnView', 'ColumnEditView', 'Grains', 'UPbAnalyses', 'GeoChemicalAnalyses',
                    'GeoChemicalAnalytes']):
        return 1
    elif table in ['SpotView', 'SpotEditView']:
        return 4
    elif table in ['UPbView', 'UPbEditView', 'GeoChemView', 'GeoChemEditView']:
        return 5
    elif table == 'SampleAges':
        return 16
    else:
        return None

def get_description_column(table: str) -> int | None:
    """
    Returns the index of the column header containing 'Description'.
    :param table: Name of the SQL database table or view
    :return: Returns the column number starting from 0
    """
    if 'View' in table:
        headers = get_headers(table)
    else:
        headers = get_headers(get_view_from_table(table))
    for header in headers:
        if 'Description' in header:
            return headers.index(header)
    return None

def get_abbreviation_column(table: str) -> int | None:
    """
    Returns the index of the column header containing 'Abbreviation'.
    :param table: Name of the SQL database table or view
    :return: Returns the column number starting from 0
    """
    if 'View' in table:
        headers = get_headers(table)
    else:
        headers = get_headers(get_view_from_table(table))
    for header in headers:
        if 'Abbreviation' in header:
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
    elif 'Grain' in view:
        return 'Grains'
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
    elif table == 'Grains':
        return 'GrainView'
    elif table == 'Spots':
        return 'SpotView'
    elif table == 'UPbAnalyses':
        return 'UPbView'
    elif table == 'GeoChemicalAnalyses':
        return 'GeoChemView'
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
        return 'SampleEditView'
    elif table == 'Aliquots':
        return 'AliquotEditView'
    elif table == 'Grains':
        return 'GrainEditView'
    elif table == 'Spots':
        return 'SpotEditView'
    elif table == 'UPbAnalyses':
        return 'UPbEditView'
    elif table == 'GeoChemicalAnalyses':
        return 'GeoChemEditView'
    elif table == 'Columns':
        return 'ColumnEditView'
    elif table == 'References' or table == '"References"':
        return 'ReferenceView'
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
        logger_setup.get_logger().critical(f"Failed to get columns from query")
        logger_setup.get_logger().debug(f"Query: {query}")
        logger_setup.get_logger().debug(f"Error: {model.lastError().text()}")
        return [None for column in cols]
    while model.canFetchMore():
        model.fetchMore()
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
        if column_list == ['']:
            column_list = []
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
    from util.widgets.models.SQLiteTableModel import SQLiteTableModel
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
    if not table:
        logger_setup.get_logger().info("No table provided")
        return None
    if not item_id:
        logger_setup.get_logger().info(f"No ID provided for {table}")
        return None
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    if table == '"References"':
        table = 'References'
    sql_query = f'SELECT {headers[get_name_column(table)]} FROM "{table}" WHERE {headers[0]}={item_id}'
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
    logger_setup.get_logger().info(f'Getting ID for {name} in {table}')
    if table in ['"References"', 'References']:
        # Need to use the ViewQuery to access the generated display column
        name_column = get_name_column(get_view_from_table(table))
        show_cols = settings.value('reference_view_columns')
        query_args = {'show_columns': [show_cols[0]], 'where': f'WHERE {show_cols[name_column]}=:name COLLATE NOCASE',
                      'group_col': f'{show_cols[0]}', 'order_col': f'{show_cols[name_column]}'}
        view_query = ViewQuery('References', False, **query_args)
        sql_query = view_query.table_query
    else:
        sql_query = f'SELECT {headers[0]} FROM "{table}" WHERE {headers[get_name_column(table)]}=:name COLLATE NOCASE'
    # logger_setup.get_logger().debug(f'SQL command: {sql_query}')
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

def get_id_from_abbreviation(table: str, abbreviation: str) -> int:
    """
    Returns the primary id for a given abbreviation record in a table. Queries the database and returns the first column which
    should always be the id column. Gathers the abbreviation column from the table headers.
    :param table: Name of the table to query (e.g. ErrorFormats)
    :param abbreviation: Abbreviation to retrieve the ID from (e.g. 1s%, 2sabs, etc.)
    :return: ID (e.g. RockTypeID)
    """
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    logger_setup.get_logger().info(f'Getting ID for {abbreviation} in {table}')
    sql_query = f'SELECT {headers[0]} FROM "{table}" WHERE {headers[get_abbreviation_column(table)]}=:name COLLATE NOCASE'
    # logger_setup.get_logger().debug(f'SQL command: {sql_query}')
    if not query.prepare(sql_query):
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
    query.bindValue(":name", str(abbreviation))
    if not query.exec():
        logger_setup.get_logger().critical(f"Failed to get ID for {abbreviation} in {table}")
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
    if table == '"References"':
        table = 'References'
    # Check if the where begins with SELECT or WHERE
    if where and (where.strip().upper().startswith('SELECT') or where.strip().upper().startswith('WITH')):
        from_str = f'FROM ({where})'
    else:
        from_str = f'FROM "{table}" {where}'
    sql_query = f'SELECT COUNT() {from_str}'
    table = get_view_from_table(table)
    if 'View' in table:
        table = get_table_from_view(table)
        if table in ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses']:
                sql_query = f'SELECT COUNT() FROM (Select * FROM Samples {get_join_from_table('', [table])}) {where}'


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


def get_record_row(table: str, record_id: int, ids_to_show: list = None) -> int:
    """
    Gets the row of the record in SQL query results for a given record_id.
    :param table: name of the table to query
    :param record_id: id of the record to find (e.g. RockTypeID=4)
    :param ids_to_show: optional list of IDs to filter the results by so can accurately find the row in a filtered table
    :return: row number/index of the record
    """
    if table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees or table == 'Ages':
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
    base_id_column = get_headers(get_view_from_table(table))[0]
    name_header = get_headers(get_view_from_table(table))[get_name_column(get_view_from_table(table))]
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

def scroll_to_record(record_id: int, view: QtW.QTableView):
    """
    Scroll to a specific record in the view.
    :param record_id: id of record
    :param view: view to scroll
    """
    model = view.model()
    if model is None or isinstance(view, QtW.QTreeView):
        return
    view_index = QtC.QModelIndex()
    for row in range(model.rowCount()):
        if model.index(row, 0).data(QtC.Qt.ItemDataRole.DisplayRole) == record_id:
            logger_setup.get_logger().info(f'Scrolling to record ID: {record_id}')
            view_index = model.index(row, 0)
            break
    if not view_index.isValid():
        logger_setup.get_logger().critical(f'Error scrolling to record')
        logger_setup.get_logger().debug(f'Invalid index for ID {record_id} in scroll_to_record')
        return
    max_view_index = model.index(view_index.row(), model.columnCount()-1)

    # view.verticalScrollBar().setValue(view_index.row())

    def update_view():
        view.setCurrentIndex(view_index)
        view.scrollTo(view_index, QtW.QAbstractItemView.ScrollHint.PositionAtCenter)
        selection_model = view.selectionModel()
        if selection_model is None:
            view.selectRow(view_index.row())
            view.setCurrentIndex(view_index)
        else:
            selection_model.clearSelection()
            selection_flags = (
                        QtC.QItemSelectionModel.SelectionFlag.Select | QtC.QItemSelectionModel.SelectionFlag.Rows)
            selection = QtC.QItemSelection(view_index, max_view_index)
            selection_model.select(selection, selection_flags)
            # selection_model.setCurrentIndex(view_index, QtC.QItemSelectionModel.SelectionFlag.Current)
        # view.updateGeometry()
        view.viewport().update()
        from util.widgets.views.frozen_views import FrozenTableView
        if isinstance(view, FrozenTableView):
            view.frozen_table_view.viewport().update()
        view.setFocus()
        QtW.QApplication.processEvents()

    QtC.QTimer.singleShot(0, update_view)

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


def strip_strings(x):
    """
    Remove excess white space from strings. Returns the data unchanged if not a string.
    :param x: Value from a DataFrame.
    :return: Stripped value if string, unchanged if another data type.
    """
    if isinstance(x, str):
        return x.strip()
    return x




def merge_intervals(intervals):
    intervals = sorted(intervals)
    merged = []
    for a, b in intervals:
        if not merged or a > merged[-1][1]:
            merged.append([a, b])
        else:
            merged[-1][1] = max(merged[-1][1], b)
    return [(a, b) for a, b in merged]

def intersect_intervals(a, b):
    output = []
    i = j = 0
    while i < len(a) and j < len(b):
        a0, a1 = a[i]
        b0, b1 = b[j]
        lo, hi = max(a0, b0), min(a1, b1)
        if hi > lo:
            output.append((lo, hi))
        if a1 < b1:
            i += 1
        else:
            j += 1
    return output

def common_strings(strings: list[str] | None) -> str:
    """
    Find text common to ALL strings. Replace unique chunks with the placeholder [-]
    """
    # Minimum length of common string to match, reduce noise
    minimum_length = 2
    placeholder = "[-]"
    strings = [s for s in strings if s is not None]
    if not strings:
        return "-"

    # Begin with the first string and build matches from there
    base = strings[0]
    common_regions = [(0, len(base))]

    for s in strings[1:]:
        sequence_matches = SequenceMatcher(None, base, s)
        matches = [(m.a, m.a + m.size) for m in sequence_matches.get_matching_blocks() if m.size >= minimum_length]
        matches = merge_intervals(matches)
        common_regions = intersect_intervals(common_regions, matches)
        if not common_regions:
            break

    # Build string using common regions
    parts = []
    last = 0
    for a, b in common_regions:
        if a > last:
            parts.append(placeholder)
        parts.append(base[a:b])
        last = b
    if last < len(base):
        parts.append(placeholder)
    elif len(parts) == 1 and parts[0] in strings:
        # One string is the exact same as the base, so do not include the last character
        parts[0] = parts[0][0:-1]
        parts.append(placeholder)
    output = []
    for part in parts:
        if output and output[-1] == placeholder and part == placeholder:
            # Don't have two placeholders in a row
            continue
        output.append(part)

    return "".join(output)

def delete_query(table: str, ids: list):
    moved_ids = []  # Keep track of IDs that were moved during deletion
    if not ids:
        logger_setup.get_logger().error(f"No IDs given for deletion in {table}")
        return False, moved_ids
    create_savepoint('before_delete')
    delete_names = []
    for item_id in ids:
        if not item_id:
            continue
        name = get_name_from_id(table, item_id)
        if name:
            delete_names.append(name)
        else:
            logger_setup.get_logger().warning(f"Could not find name for ID {item_id} in {table}")
            logger_setup.get_logger().debug(f"ID {item_id} not found in {table}")
            rollback_savepoint('before_delete')
            return False, moved_ids
    logger_setup.get_logger().info(f"Deleting {table}: {delete_names}")
    query = QtS.QSqlQuery()
    headers = get_headers(table)
    id_header = headers[0]  # Get the first header which is the ID column
    for delete_id in ids:
        parent_id = None
        parent_row = None
        if table in SQLUtils.user_viewable_trees:
            query.exec(f'SELECT {headers[1]}, {headers[2]} FROM "{table}" WHERE {id_header}={delete_id}')
            if not query.next():
                logger_setup.get_logger().critical(f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
                logger_setup.get_logger().debug(f"ID {delete_id} not found in {table}. Unable to retrieve parent information for tree structure.")
                rollback_savepoint('before_delete')
                return False, moved_ids
            parent_id = query.value(0)
            parent_row = query.value(1)
        query.prepare(f'DELETE FROM "{table}" WHERE {id_header}={delete_id}')
        if not query.exec():
            logger_setup.get_logger().critical(f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_delete')
            return False, moved_ids
        logger_setup.get_logger().info(f"Successfully deleted ID {delete_id} from {table}")
        if table in SQLUtils.user_viewable_trees and parent_row:
            if parent_id in ids:
                # If the parent is also being deleted, we don't need to update the remaining children
                continue
            affected_ids = []
            if not parent_id:
                where_sql = f'{headers[1]} IS NULL AND {headers[2]} > {parent_row}'
            else:
                where_sql = f'{headers[1]} = {parent_id} AND {headers[2]} > {parent_row}'
            query.prepare(f'SELECT {id_header} FROM "{table}" WHERE {where_sql}')
            if not query.exec():
                logger_setup.get_logger().critical(f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
                logger_setup.get_logger().debug(f"Error finding affected records during delete")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint(f"before_delete")
                return False, moved_ids
            while query.next():
                affected_ids.append(query.value(0))
            for affected_id in affected_ids:
                update_query = f'UPDATE "{table}" SET {headers[2]} = {headers[2]} - 1 WHERE {id_header} = {affected_id}'
                if not query.exec(update_query):
                    logger_setup.get_logger().critical(f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
                    logger_setup.get_logger().debug(f"Error updating affected record during delete")
                    logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger_setup.get_logger().debug(f"SQL query: {update_query}")
                    rollback_savepoint(f"before_delete")
                    return False, moved_ids
                if affected_id not in ids and affected_id not in moved_ids:
                    moved_ids.append(affected_id)
            if moved_ids:
                update_modified_timestamp(table, moved_ids)
    logger_setup.get_logger().info(f"Deleted {len(ids)} records from {table}")
    release_savepoint('before_delete')
    return True, moved_ids

def delete_data(table: str, data_ids: list, enable_message=True):
    """
    Given a table, delete given IDS. If table is Samples, Aliquots, Grains, or Spots, delete given ids and all sub items
    :param table: Table the IDs belong to
    :param data_ids: List of table IDs
    :param enable_message: Enable message to also ask about deleting items that have no child items remaining
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
    delete_sample_ids = []
    delete_aliquot_ids = []
    aliquot_child_ids = []
    delete_spot_ids = []
    delete_grain_ids = []
    delete_upb_analysis_ids = []
    table_child_ids = []
    childless_samples = []
    childless_aliquots = []
    childless_spots = []
    spotless_grains = []
    if table == 'Samples':
        delete_aliquot_ids, delete_grain_ids, delete_spot_ids, delete_upb_analysis_ids = find_current_sub_items(data_ids, table)
        aliquot_child_ids = []
        for parent_id in delete_aliquot_ids:
            aliquot_child_ids = find_child_ids('Aliquots', parent_id, aliquot_child_ids)
        delete_sample_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(delete_sample_ids)} samples, {len(delete_aliquot_ids)} aliquots, {len(aliquot_child_ids)} sub-aliquots, {len(delete_grain_ids)} grains, {len(delete_spot_ids)} spots, and {len(delete_upb_analysis_ids)} UPb analyses")
        delete_aliquot_ids.extend(aliquot_child_ids)
    elif table == 'Aliquots':
        delete_grain_ids, delete_spot_ids, delete_upb_analysis_ids = find_current_sub_items(data_ids, table)
        delete_aliquot_ids = data_ids
        aliquot_child_ids = []
        for parent_id in delete_aliquot_ids:
            aliquot_child_ids = find_child_ids('Aliquots', parent_id, aliquot_child_ids)
        logger_setup.get_logger().info(f"Deleting {len(delete_aliquot_ids)} aliquots, {len(aliquot_child_ids)} sub-aliquots, {len(delete_grain_ids)} grains, {len(delete_spot_ids)} spots, and {len(delete_upb_analysis_ids)} UPb analyses")
        delete_aliquot_ids.extend(aliquot_child_ids)
        parent_samples = find_current_parent_items(delete_aliquot_ids, table)
        if parent_samples:
            # Determine if all aliquots of these samples are being deleted
            for sample_id in parent_samples:
                sub_aliquot_ids, sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id], 'Samples')
                if not any(aliquot_id not in delete_aliquot_ids for aliquot_id in sub_aliquot_ids):
                    # If all aliquots of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)
    elif table == 'Grains':
        delete_spot_ids, delete_upb_analysis_ids = find_current_sub_items(data_ids, table)
        delete_grain_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(delete_grain_ids)} grains, {len(delete_spot_ids)} spots, and {len(delete_upb_analysis_ids)} UPb analyses")
        parent_samples, parent_aliquots, parent_spots = find_current_parent_items(data_ids, table)
        if parent_aliquots:
            # Determine if all spots of these aliquots are being deleted
            for aliquot_id in parent_aliquots:
                sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([aliquot_id], 'Aliquots')
                if not any(spot_id not in delete_spot_ids for spot_id in sub_spot_ids):
                    # If all spots of the aliquot are being deleted, add the aliquot to the list
                    if aliquot_id not in childless_aliquots:
                        childless_aliquots.append(aliquot_id)
        if childless_aliquots:
            # Determine if all spots of these samples are being deleted
            for sample_id in parent_samples:
                sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id], 'Samples')
                if not any(spot_id not in delete_spot_ids for spot_id in sub_spot_ids):
                    # If all spots of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)

    elif table == 'Spots':
        grain_ids, delete_upb_analysis_ids = find_current_sub_items(data_ids, table)
        delete_spot_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(delete_spot_ids)} spots and {len(delete_upb_analysis_ids)} UPb analyses")
        parent_samples, parent_aliquots = find_current_parent_items(data_ids, table)
        if parent_aliquots:
            # Determine if all spots of these aliquots are being deleted
            for aliquot_id in parent_aliquots:
                sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([aliquot_id], 'Aliquots')
                if not any(spot_id not in delete_spot_ids for spot_id in sub_spot_ids):
                    # If all spots of the aliquot are being deleted, add the aliquot to the list
                    if aliquot_id not in childless_aliquots:
                        childless_aliquots.append(aliquot_id)
        if childless_aliquots:
            # Determine if all spots of these samples are being deleted
            for sample_id in parent_samples:
                sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id], 'Samples')
                if not any(spot_id not in delete_spot_ids for spot_id in sub_spot_ids):
                    # If all spots of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)
        # Determine if all UPb analyses of these grains are being deleted
        for grain_id in grain_ids:
            sub_parent_sample_ids, sub_parent_aliquot_ids, sub_parent_spot_ids = find_current_parent_items(
                [grain_id], 'Grains')
            if not any(spot_id not in delete_spot_ids for spot_id in sub_parent_spot_ids):
                # If all Spots of the grain are being deleted, add the grain to the list
                if grain_id not in spotless_grains:
                    spotless_grains.append(grain_id)

    elif table == 'UPbAnalyses':
        delete_upb_analysis_ids = data_ids
        logger_setup.get_logger().info(f"Deleting {len(delete_upb_analysis_ids)} UPb analyses")
        parent_samples, parent_aliquots, parent_grains, parent_spots = find_current_parent_items(data_ids, table)
        if parent_spots:
            # Determine if all UPb analyses of these spots are being deleted
            for spot_id in parent_spots:
                sub_grain_ids, sub_upb_analysis_ids = find_current_sub_items([spot_id], 'Spots')
                if not any(upb_analysis_id not in delete_upb_analysis_ids for upb_analysis_id in sub_upb_analysis_ids):
                    # If all UPb analyses of the spot are being deleted, add the spot to the list
                    if spot_id not in childless_spots:
                        childless_spots.append(spot_id)
        if childless_spots:
            # Determine if all UPb analyses of these aliquots are being deleted
            for aliquot_id in parent_aliquots:
                sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([aliquot_id], 'Aliquots')
                if not any(upb_analysis_id not in delete_upb_analysis_ids for upb_analysis_id in sub_upb_analysis_ids):
                    # If all UPb analyses of the aliquot are being deleted, add the aliquot to the list
                    if aliquot_id not in childless_aliquots:
                        childless_aliquots.append(aliquot_id)
            # Determine if all UPb analyses of these grains are being deleted
            for grain_id in parent_grains:
                sub_parent_sample_ids, sub_parent_aliquot_ids,sub_parent_spot_ids = find_current_parent_items([grain_id], 'Grains')
                if not any(spot_id not in childless_spots for spot_id in sub_parent_spot_ids):
                    # If all Spots of the grain are being deleted, add the grain to the list
                    if grain_id not in spotless_grains:
                        spotless_grains.append(grain_id)
        if childless_aliquots:
            # Determine if all UPb analyses of these samples are being deleted
            for sample_id in parent_samples:
                sub_aliquot_ids, sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id], 'Samples')
                if not any(upb_analysis_id not in delete_upb_analysis_ids for upb_analysis_id in sub_upb_analysis_ids):
                    # If all UPb analyses of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)
    elif table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees or table == 'Ages':
        # For user viewable trees, we need to check for child IDs
        table_child_ids = []
        for parent_id in data_ids:
            # Find all child IDs of the given parent_id
            table_child_ids = find_child_ids(table, parent_id, table_child_ids)
    if childless_samples or childless_aliquots or spotless_grains or childless_spots:
        # If there are childless samples, aliquots, grains, or spots, ask the user if these should be deleted as well
        delete_all = False
        if enable_message:
            msg_box = QtW.QMessageBox()
            msg_box.setIcon(QtW.QMessageBox.Icon.Question)
            msg_box.setWindowTitle('Delete Empty Items')
            msg_text = f'Deleting these {len(data_ids)} {table} leaves empty items. \n\nWould you like to delete these as well?'
            detailed_text = f''
            if childless_samples:
                sample_names = [get_name_from_id('Samples', sample_id) for sample_id in childless_samples]
                detailed_text += f'{len(childless_samples)} Samples: \n{"\n".join(sample_names)}'
            if childless_aliquots:
                aliquot_names = [get_name_from_id('Aliquots', aliquot_id) for aliquot_id in childless_aliquots]
                msg_text += f'\n{len(childless_aliquots)} Aliquots: \n{"\n".join(aliquot_names)}'
            if spotless_grains:
                grain_names = [get_name_from_id('Grains', grain_id) for grain_id in spotless_grains]
                msg_text += f'\n{len(spotless_grains)} Grains: \n{"\n".join(grain_names)}'
            if childless_spots:
                spot_names = [get_name_from_id('Spots', spot_id) for spot_id in childless_spots]
                msg_text += f'\n{len(childless_spots)} Spots: \n{"\n".join(spot_names)}'
            msg_box.setText(msg_text)
            msg_box.setStandardButtons(QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No | QtW.QMessageBox.StandardButton.Cancel)
            msg_box.setDefaultButton(QtW.QMessageBox.StandardButton.Cancel)
            response = msg_box.exec()
            if response == QtW.QMessageBox.StandardButton.Yes:
                # If the user wants to delete the empty items, add them to the deletion lists
                delete_all = True
            elif response == QtW.QMessageBox.StandardButton.No:
                delete_all = False
            else:
                # cancel the deletion
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                logger_setup.get_logger().info(
                    f"Deletion cancelled for {table} with IDs: {', '.join(map(str, data_ids))}")
                return False
        if delete_all:
            if childless_samples:
                delete_sample_ids.extend(childless_samples)
            if childless_aliquots:
                delete_aliquot_ids.extend(childless_aliquots)
            if childless_spots:
                delete_spot_ids.extend(childless_spots)
            if spotless_grains:
                delete_grain_ids.extend(spotless_grains)

    from Functions.Database_manager import turn_on_foreign_keys
    # Double-check that foreign keys are enabled
    if not turn_on_foreign_keys():
        close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
        return False
    if table in ('Samples', 'Aliquots', 'Spots', 'UPbAnalyses'):
        if delete_upb_analysis_ids:
            if not delete_query('UPbAnalyses', delete_upb_analysis_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(delete_upb_analysis_ids)} UPb analyses')
        if delete_grain_ids:
            if not delete_query('Grains', delete_grain_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(delete_grain_ids)} Grains')
        if delete_spot_ids:
            if not delete_query('Spots', delete_spot_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(delete_spot_ids)} spots')
        if delete_aliquot_ids:
            parent_samples = find_current_parent_items(delete_aliquot_ids, 'Aliquots')
            query = f'SELECT * FROM Aliquots WHERE SampleID in ({parent_samples})'
            aliquot_model = QtS.QSqlQueryModel()
            aliquot_model.setQuery(query)
            from util.widgets.models.TreeModel import TreeModel
            aliquot_tree = TreeModel(aliquot_model)
            if not aliquot_tree.removeItems(delete_aliquot_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(delete_aliquot_ids)} Aliquots')
        if delete_sample_ids:
            if not delete_query('Samples', delete_sample_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(delete_sample_ids)} Samples')
    else:
        if table_child_ids:
            delete_ids = data_ids + table_child_ids
        else:
            delete_ids = data_ids
        if delete_ids:
            if not delete_query(table, delete_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger_setup.get_logger().info(f'Deleted {len(delete_ids)} {table} records')

    close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
    return True

def delete_question(table, delete_ids):
    show_loading_dialog('Preparing', 'Gathering information...')
    msg_box = QtW.QMessageBox()
    msg_box.setIcon(QtW.QMessageBox.Icon.Question)
    detail_text = ''
    if table == 'Samples':
        sample_names = [get_name_from_id(table, sample_id) for sample_id in delete_ids]
        if None in sample_names:
            logger_setup.get_logger().info(f'Samples were already deleted or do not exist')
            close_loading_dialog('Preparing', 'Gathering information...')
            return False
        # Samples have a special case where they are related to Aliquots, Spots, and UPbAnalyses
        aliquot_ids, grain_ids, spot_ids, upb_analysis_ids = find_current_sub_items(delete_ids, table)
        msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?\n'
        msg_text += f'\nAssociated with {len(aliquot_ids)} aliquots, {len(grain_ids)} grains, {len(spot_ids)} spots, and {len(upb_analysis_ids)} U-Pb analyses'
        detail_text = f'Samples: {"\n".join(sample_names)}\n'
        if len(aliquot_ids) > 0:
            aliquot_names = [get_name_from_id('Aliquots', aliquot_id) for aliquot_id in aliquot_ids]
            detail_text += f'Aliquots: {"\n".join(aliquot_names)}\n'
        if len(grain_ids) > 0:
            grain_names = [get_name_from_id('Grains', grain_id) for grain_id in grain_ids]
            detail_text += f'Grains: {"\n".join(grain_names)}\n'
        if len(spot_ids) > 0:
            spot_names = [get_name_from_id('Spots', spot_id) for spot_id in spot_ids]
            detail_text += f'Spots: {"\n".join(spot_names)}\n'
        if len(upb_analysis_ids) > 0:
            upb_analysis_names = [get_name_from_id('UPbAnalyses', upb_analysis_id) for upb_analysis_id in upb_analysis_ids]
            detail_text += f'U-Pb Analyses: {"\n".join(upb_analysis_names)}\n'
    elif table == 'Aliquots':
        aliquot_names = [get_name_from_id(table, aliquot_id) for aliquot_id in delete_ids]
        # Look for children of Aliquots
        child_aliquot_ids = []
        for aliquot_id in delete_ids:
            # Find all child aliquots of the given aliquot_id
            child_aliquot_ids = (aliquot_id, child_aliquot_ids)
        # Aliquots have a special case where they are related to Spots and UPbAnalyses
        aliquot_ids = delete_ids.extend(child_aliquot_ids)
        grain_ids, spot_ids, upb_analysis_ids = find_current_sub_items(aliquot_ids, table)
        msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?\n'
        msg_text += f'\nAliquots: {", ".join(aliquot_names)}\n'
        msg_text += f'\nAssociated with {len(child_aliquot_ids)} child aliquots, {len(grain_ids)} grains, {len(spot_ids)} spots, and {len(upb_analysis_ids)} U-Pb analyses'
        detail_text = f'Aliquots: {"\n".join(aliquot_names)}...\n'
        if len(child_aliquot_ids) > 0:
            child_aliquot_names = [get_name_from_id('Aliquots', aliquot_id) for aliquot_id in child_aliquot_ids]
            detail_text += f'Child Aliquots: {"\n".join(child_aliquot_names)}\n'
        if len(grain_ids) > 0:
            grain_names = [get_name_from_id('Grains', grain_id) for grain_id in grain_ids]
            detail_text += f'Grains: {"\n".join(grain_names)}\n'
        if len(spot_ids) > 0:
            spot_names = [get_name_from_id('Spots', spot_id) for spot_id in spot_ids]
            detail_text += f'Spots: {"\n".join(spot_names)}\n'
        if len(upb_analysis_ids) > 0:
            upb_analysis_names = [get_name_from_id('UPbAnalyses', upb_analysis_id) for upb_analysis_id in upb_analysis_ids]
            detail_text += f'U-Pb Analyses: {"\n".join(upb_analysis_names)}\n'
    elif table == 'Spots':
        spot_names = [get_name_from_id(table, spot_id) for spot_id in delete_ids]
        # Spots have a special case where they are related to UPbAnalyses and Grains
        grain_ids, upb_analysis_ids = find_current_sub_items(delete_ids, table)
        msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?\n'
        msg_text += f'\nAssociated with {len(grain_ids)} grains and {len(upb_analysis_ids)} U-Pb analyses'
        detail_text = f'Spots: {"\n".join(spot_names)}\n'
        if len(grain_ids) > 0:
            grain_names = [get_name_from_id('Grains', grain_id) for grain_id in grain_ids]
            detail_text += f'Grains: {"\n".join(grain_names)}\n'
        if len(upb_analysis_ids) > 0:
            upb_analysis_names = [get_name_from_id('UPbAnalyses', upb_analysis_id) for upb_analysis_id in
                                  upb_analysis_ids]
            detail_text += f'U-Pb Analyses: {"\n".join(upb_analysis_names)}\n'
    else:
        if table in SQLUtils.user_viewable_trees or table in SQLUtils.conditionally_editable_trees or table == 'Ages':
            # For user viewable trees, we need to check for child IDs
            child_ids = []
            for parent_id in delete_ids:
                # Find all child IDs of the given parent_id
                child_ids = find_child_ids(table, parent_id, child_ids)
            all_delete_ids = set(delete_ids + child_ids)
            tree_item_names = [f'"{get_name_from_id(table, item_id)}"' for item_id in all_delete_ids]
            msg_text = f'Are you sure you want to delete these {len(all_delete_ids)} {table}?'
            detail_text = f'{table}: {"\n".join(tree_item_names)}'
        else:
            item_names = [f'"{get_name_from_id(table, item_id)}"' for item_id in delete_ids]
            all_delete_ids = set(delete_ids)
            msg_text = f'Are you sure you want to delete these {len(delete_ids)} {table}?'
            detail_text = f'{table}: {"\n".join(item_names)}'
        associations = find_foreign_associations(table, list(all_delete_ids))
        associated_id_count = sum(len(ids) for ids in associations.values())
        if associated_id_count == 0:
            association_text = f'\nAssociated with no other records.'
        else:
            # Find the number of tables with non-empty associations
            detail_text = ''
            non_empty_tables = [associated_table for associated_table, ids in associations.items() if ids]
            if len(non_empty_tables) < 4:
                # List the associations with their names for up to three table associations
                association_text = '\nAssociated with: '
                for associated_table, ids in associations.items():
                    if len(ids) == 0:
                        association_text += f'\nNo {associated_table}'
                        continue
                    # append the association text with the number of IDs and the names of the IDs
                    else:
                        association_text += f'\n{len(ids)} {associated_table}'
                        detail_text += f'{associated_table}: \n{"\n".join(get_name_from_id(associated_table, id) for id in ids)}\n'
            else:
                association_text = f'\nAssociated with '
                for associated_table, ids in associations.items():
                    # append the association text with the number of IDs and the names of the IDs
                    association_text += f'{len(ids)} {associated_table}, '
        msg_text += association_text
    msg_box.setText(msg_text)
    if detail_text != '':
        msg_box.setDetailedText(detail_text)
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
            if first_table and first_table not in associations:
                associations[first_table] = []
            from util.widgets.models.SQLiteTableModel import SQLiteTableModel
            foreign_table_model = SQLiteTableModel(f'SELECT {first_table_id_header} FROM "{db_table}" {where}')
            if not foreign_table_model.last_error:
                for row in range(foreign_table_model.rowCount()):
                    foreign_id = foreign_table_model.data(foreign_table_model.index(row, 0))
                    if foreign_id and foreign_id not in associations[first_table]:
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
                    if db_table and db_table not in associations:
                        associations[db_table] = []
                    if id_header != header:
                        where_one = where.replace(f'{id_header}', f'"{header}"')
                    else:
                        where_one = where
                    foreign_table_model = SQLiteTableModel(f'SELECT {get_headers(db_table)[0]} FROM "{db_table}" {where_one}')
                    if not foreign_table_model.last_error:
                        for row in range(foreign_table_model.rowCount()):
                            foreign_id = foreign_table_model.data(foreign_table_model.index(row, 0))
                            if foreign_id and foreign_id not in associations[db_table]:
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
    from util.widgets.models.SQLiteTableModel import SQLiteTableModel
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
    Find parent items for a list of data IDs in a given table. This is intended to find parent items for Aliquots, Grains,
    Spots, and UPbAnalyses. For commited data only.
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
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, Spots.GrainID FROM Spots
                        {SQLUtils.spot_aliquot_join}
                         WHERE SpotID {where}"""
        sample_ids, aliquot_ids, grain_ids = columns_as_list(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids
    elif table == 'Grains':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID FROM Spots
                                {SQLUtils.spot_aliquot_join}
                                 WHERE GrainID {where}"""
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
    Find all sub items of a list of samples, aliquots, grains, or spots. This is intended to find sub items for Samples, Aliquots,
    and Spots, and return the IDs of the sub items. For uncommited data only with a significant efficiency cost.
    :param data_ids: List of data IDs to find sub items for
    :param table: Table to search for sub items, can be 'Samples', 'Aliquots', 'Grains', or 'Spots'
    :return: Tuple of lists of sub item IDs
    """
    # Find all the sub items of a list of samples, aliquots, or spots
    logger_setup.get_logger().info(f"Finding sub items for {len(data_ids)} {table}")
    aliquot_ids = []
    grain_ids = []
    spot_ids = []
    upb_analysis_ids = []
    if not data_ids:
        logger_setup.get_logger().warning(f"No data IDs provided for finding sub items in {table}")
        if table == 'Spots':
            return grain_ids, upb_analysis_ids
        elif table == 'Grains':
            return spot_ids, upb_analysis_ids
        elif table == 'Aliquots':
            return grain_ids, spot_ids, upb_analysis_ids
        elif table == 'Samples':
            return aliquot_ids, grain_ids, spot_ids, upb_analysis_ids
        else:
            logger_setup.get_logger().critical(f"Table {table} in not supported for finding sub items")
            return None, None, None, None
    show_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    if table == 'Samples':
        sql_query = f"""SELECT Aliquots.AliquotID, Spots.SpotID, Grains.GrainID, UPbAnalyses.UPbAnalysisID FROM Aliquots
                        {SQLUtils.aliquot_spot_join}
                        {SQLUtils.spot_upb_analysis_join}
                        {SQLUtils.spot_grain_join}
                        WHERE Aliquots.SampleID {where}"""
        aliquot_ids, spot_ids, grain_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1, 2, 3])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return aliquot_ids, grain_ids, spot_ids, upb_analysis_ids
    elif table == 'Aliquots':
        sql_query = f"""SELECT Spots.SpotID, Grains.GrainID, UPbAnalyses.UPbAnalysisID FROM Spots
                        {SQLUtils.spot_upb_analysis_join}
                        {SQLUtils.spot_grain_join}
                        WHERE Spots.AliquotID {where}"""
        spot_ids, grain_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return grain_ids, spot_ids, upb_analysis_ids
    elif table == 'Spots':
        sql_query = f"""SELECT Grains.GrainID, UPbAnalyses.UPbAnalysisID FROM UPbAnalyses
                        {SQLUtils.upb_spot_join}
                        {SQLUtils.spot_grain_join}
                        WHERE UPbAnalyses.SpotID {where}"""
        grain_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return grain_ids, upb_analysis_ids
    elif table == 'Grains':
        sql_query = f"""SELECT Spots.SpotID, UPbAnalyses.UPbAnalysisID FROM UPbAnalyses
                        {SQLUtils.upb_spot_join}
                        WHERE Spots.GrainID {where}"""
        spot_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return spot_ids, upb_analysis_ids
    else:
        logger_setup.get_logger().critical(f"Table {table} in not supported for finding sub items")
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return None, None, None, None


def find_current_parent_items(data_ids: list, table: str):
    """
    Find parent items for a list of data IDs in a given table. This is intended to find parent items for Aliquots, Spots,
    Grains, and UPbAnalyses. For uncommited data only with a significant efficiency cost.
    :param data_ids: List of data IDs to find parent items for
    :param table: Table to search for parent items
    :return: Tuple of lists of parent sample IDs, aliquot IDs, and spot IDs
    """
    logger_setup.get_logger().info(f"Finding parent items for {len(data_ids)} {table}")
    if not data_ids:
        logger_setup.get_logger().warning(f"No data IDs provided for finding parent items in {table}")
        return None, None, None, None
    show_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    if table == 'UPbAnalyses':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, Spots.GrainID, UPbAnalyses.SpotID FROM UPbAnalyses 
                        {SQLUtils.upb_spot_join}
                        {SQLUtils.spot_grain_join}
                        {SQLUtils.spot_aliquot_join}
                        WHERE UPbAnalysisID {where}"""
        sample_ids, aliquot_ids, grain_ids, spot_ids = columns_as_list_current(sql_query, [0, 1, 2, 3])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids, grain_ids, spot_ids
    elif table == 'Grains':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, Spots.SpotID FROM Spots
                        {SQLUtils.spot_aliquot_join}
                        WHERE Spots.GrainID {where}"""
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




# ---------------------------
#    Tree Methods
# ---------------------------


def bulk_update_parent_row(table, parent_id, spaces_to_move: int, new_row: int | None = None, old_row: int | None = None) -> tuple[bool, list[int]]:
    """
    Update the parent row for a given range of child rows in the database.
    :param table: table name
    :param parent_id: unique ID of the new parent, or None if the item has no parent
    :param spaces_to_move: number of items in a row to move, remove, or insert
    :param new_row: row to create space at, None if closing space for item moved to another parent or removed
    :param old_row: row to close space at, None if creating space for item moved from another parent or inserted
    :return: True if the update was successful, False if there was an error
    """
    # Update the parent ID and parent row for a row range
    headers = get_headers(table)
    id_header = headers[0]
    parent_id_header = headers[1]
    parent_row_header = headers[2]
    updated_ids = []
    if new_row is None and old_row is None:
        logger_setup.get_logger().critical(f'Error shifting {table} data')
        logger_setup.get_logger().debug(f'Missing parent row constraints')
        return False, []
    if new_row == old_row:
        logger_setup.get_logger().info(f'{table} data already in the correct position at row {old_row}')
        return True, []
    logger_setup.get_logger().info(f'Bulk updating {table} data for children of {parent_id} from old row {old_row} to new row {new_row}')
    query1 = QtS.QSqlQuery()
    query2 = QtS.QSqlQuery()
    select_query = QtS.QSqlQuery()
    if parent_id in ['NULL', '', None]:
        parent_id = 'NULL'
        parent_id_sql = 'IS NULL'
    else:
        parent_id_sql = f'= {parent_id}'
    move_size_query = QtS.QSqlQuery()
    move_size_query.prepare(f'''SELECT MAX({parent_row_header}) AS maximum
                FROM {table} WHERE {parent_id_header} IS :parent_id''')
    move_size_query.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())
    if not move_size_query.exec():
        logger_setup.get_logger().critical(f'Error shifting {table} data')
        logger_setup.get_logger().debug(f"Error: {move_size_query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {move_size_query.lastQuery()}")
        logger_setup.get_logger().debug(f"Bound values: {move_size_query.boundValues()}")
        return False, []
    max_child_row = 0
    if move_size_query.next():
        if move_size_query.value(0):
            max_child_row = move_size_query.value(0)
    if new_row is not None and old_row is None:
        logger_setup.get_logger().info(f'Making space to insert new child at {new_row}')
        k = max_child_row - new_row + spaces_to_move
        query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k} + {spaces_to_move}
        WHERE {parent_id_header} IS :parent_id AND {parent_row_header} >= {new_row};
        ''')
        query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

        query2.prepare(f'''
        UPDATE {table} SET {parent_row_header} = {parent_row_header} - {k}
        WHERE {parent_id_header} IS :parent_id AND {parent_row_header} > {new_row}
        ''')
        query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

        select_query.prepare(f'SELECT {id_header} FROM {table} WHERE {parent_id_header} {parent_id_sql} AND {parent_row_header} >= {new_row}')
    elif old_row is not None and new_row is None:
        logger_setup.get_logger().info(f'Closing space from removed child at {old_row}')
        if old_row > max_child_row:
            logger_setup.get_logger().info(f'Space already closed')
        k = max_child_row - old_row
        query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k}
        WHERE {parent_id_header} IS :parent_id AND {parent_row_header} > {old_row};
        ''')
        query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

        query2.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} - ({k} + {spaces_to_move})
        WHERE {parent_id_header} IS :parent_id 
        AND {parent_row_header} > {old_row}
        ''')
        query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

        select_query.prepare(f'SELECT {id_header} FROM {table} WHERE {parent_id_header} {parent_id_sql} AND {parent_row_header} > {old_row}')
    elif new_row is not None and old_row is not None:
        if new_row < old_row:
            logger_setup.get_logger().info(f'Moving child up from {old_row} to {new_row}')
            k = max_child_row - new_row + 1
            query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k}
            WHERE {parent_id_header} IS :parent_id 
                AND {parent_row_header} >= {new_row} 
                AND {parent_row_header} <= {old_row};
            ''')
            query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

            query2.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} - {k} + {spaces_to_move}
            WHERE {parent_id_header} IS :parent_id
                AND {parent_row_header} > {max_child_row}
                AND {parent_row_header} < {old_row} + {k};
            ''')
            query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

            select_query.prepare(f'''SELECT {id_header} FROM {table} 
            WHERE {parent_id_header} {parent_id_sql} 
            AND {parent_row_header} >= {new_row} 
            AND {parent_row_header} <= {old_row}''')
        elif new_row > old_row:
            logger_setup.get_logger().info(f'Moving child down from {old_row} to {new_row}')
            k = max_child_row - old_row + 1
            # Move all rows that will be changing to the end
            query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k}
            WHERE {parent_id_header} IS :parent_id 
                AND {parent_row_header} >= {old_row}
                AND {parent_row_header} <= {new_row};
            ''')
            query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

            # Leave the first row past the end and move the others up to the old row and down, leaving a space at new row
            query2.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} - ({k} + {spaces_to_move})
            WHERE {parent_id_header} IS :parent_id
                AND {parent_row_header} > {max_child_row} + {spaces_to_move};
            ''')
            query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtC.QVariant())

            select_query.prepare(f'''SELECT {id_header} FROM {table} 
            WHERE {parent_id_header} {parent_id_sql} 
                AND {parent_row_header} > {old_row} 
                AND {parent_row_header} <= {new_row}''')
    if not select_query.exec():
        logger_setup.get_logger().critical(f'Error shifting {table} data')
        logger_setup.get_logger().debug(f"Error: {select_query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {select_query.lastQuery()}")
        logger_setup.get_logger().debug(f"Bound values: {select_query.boundValues()}")
        return False, []
    while select_query.next():
        updated_ids.append(select_query.value(0))
    if not updated_ids:
        logger_setup.get_logger().info(f'No items to shift for {table}')
        return True, []
    # Move items well out of the way to avoid unique ParentID, ParentRow errors
    if not query1.exec():
        logger_setup.get_logger().critical(f'Error shifting {table} data')
        logger_setup.get_logger().debug(f"Error: {query1.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query1.lastQuery()}")
        logger_setup.get_logger().debug(f"Bound values: {query1.boundValues()}")
        return False, []
    # Move items to the new position
    if not query2.exec():
        logger_setup.get_logger().critical(f'Error shifting {table} data')
        logger_setup.get_logger().debug(f"Error: {query2.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query2.lastQuery()}")
        logger_setup.get_logger().debug(f"Bound values: {query2.boundValues()}")
        return False, []
    update_modified_timestamp(table, updated_ids)
    return True, updated_ids

def get_selected_tree_ids(indexes: list[QtC.QModelIndex]):
    """
    Return the item IDs, parent IDs, and parent rows for the selected items in a tree model. This method iterates through
    the provided indexes, which are expected to be from a tree model, and retrieves the item ID, parent ID, and parent row
    for each selected item. It returns three lists: item IDs, parent IDs, and parent rows.
    :param indexes: List of QModelIndex objects representing the selected items in the tree model
    :return: Tuple containing three lists: item_ids, parent_ids, and parent_rows
    """
    item_parent_dictionary = {}
    for index in indexes:
        item_id = index.siblingAtColumn(1).data(QtC.Qt.ItemDataRole.DisplayRole)
        parent_id = index.siblingAtColumn(2).data(QtC.Qt.ItemDataRole.DisplayRole)
        parent_row = index.siblingAtColumn(3).data(QtC.Qt.ItemDataRole.DisplayRole)
        if item_id not in item_parent_dictionary.keys():
            item_parent_dictionary[item_id] = [parent_id, parent_row]
    return item_parent_dictionary

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
    from util.widgets.models.CheckableTreeModel import CheckableTreeModel
    from util.widgets.models.TreeModel import TreeModel
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
                return tree_model, tree_indexes
            except AttributeError:
                return None, None


def map_from_tree_model(input_model, tree_indexes: list[QtC.QModelIndex]):
    model_chain = []
    model = input_model
    from util.widgets.models.TreeModel import TreeModel
    while not isinstance(model, TreeModel):
        model_chain.insert(0, model)
        model = model.sourceModel() if hasattr(model, 'sourceModel') else getattr(model, 'source_model', None)

    model_indexes = tree_indexes
    for model in model_chain:
        parent_indexes = [model.mapFromSource(model_index) for model_index in model_indexes]
        model_indexes = parent_indexes
    return model_indexes

class ColumnListProxyModel(QtC.QSortFilterProxyModel):
    """
    A proxy model that filters and sorts columns in a list. This model extends QSortFilterProxyModel to display headers
    in the list as user-readable strings instead of raw database column names.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)
        self.setSortCaseSensitivity(QtC.Qt.CaseSensitivity.CaseInsensitive)

    def data(self, index: QtC.QModelIndex, role: int = ...):
        if role == QtC.Qt.ItemDataRole.DisplayRole:
            header = super().data(index, role)
            readable_header = get_readable_header(header)
            return readable_header
        return super().data(index, role)


class DisableItemModel(QtG.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.disabled_items = []

    def data(self, index: QtC.QModelIndex, role: int = ...):
        if not index.isValid():
            return None
        if role == QtC.Qt.ItemDataRole.DisplayRole or role == QtC.Qt.ItemDataRole.EditRole:
            item = self.item(index.row(), index.column()).data(QtC.Qt.ItemDataRole.DisplayRole)
            if item:
                return item
        elif role == QtC.Qt.ItemDataRole.ToolTipRole:
            item = self.item(index.row(), index.column()).data(QtC.Qt.ItemDataRole.DisplayRole)
            if not isinstance(item, str):
                item = item.text()
            query = QSqlQuery()
            if query.exec(f'SELECT GeoChemAnalyteName, GeoChemAnalyteDescription FROM GeoChemicalAnalytes WHERE GeoChemAnalyteAbbreviation IS {item}'):
                if query.next():
                    if query.value('GeoChemAnalyteName') or query.value('GeoChemAnalyteDescription'):
                        tool_tip = f'{query.value('GeoChemAnalyteName')}: {query.value('GeoChemAnalyteDescription')}'
                        return tool_tip
        elif role == QtC.Qt.ItemDataRole.ForegroundRole:
            # Return gray text if the row is disabled
            item = self.item(index.row(), index.column()).data(QtC.Qt.ItemDataRole.DisplayRole)
            if item in self.disabled_items:
                # logger_setup.get_logger().debug(f'Setting gray text for disabled item}')
                return QBrush(QColor("#A0A0A0"))  # Gray text
        return super().data(index, role)

    def flags(self, index: QtC.QModelIndex):
        if not index.isValid():
            return None
        item = self.item(index.row(), index.column()).data(QtC.Qt.ItemDataRole.DisplayRole)
        if item in self.disabled_items:
            # Item is not selectable
            return QtC.Qt.ItemFlag.NoItemFlags
        return super().flags(index)

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
        if not index.isValid():
            return super().setData(index, value, role)
        if role == QtC.Qt.ItemDataRole.CheckStateRole:
            if self.data(index, QtC.Qt.ItemDataRole.DisplayRole) == self.permanent_header and value == QtC.Qt.CheckState.Unchecked:
                return False
        return super().setData(index, value, role)

class TableToolTipModel(QtG.QStandardItemModel):
    """
    Subclass of QStandardItemModel to link table items in the model with descriptions to return as tool tips. Can be
    applied to any combo box or list that accepts QStandardItemModel
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def data(self, index, role=QtC.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.ToolTipRole:
            table = self.data(index, Qt.ItemDataRole.DisplayRole)
            if table in SQLUtils.table_attributes_description_dict.keys():
                description = SQLUtils.table_attributes_description_dict[table]['description']
                return description
        return super().data(index, role)












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
    if comboBox.currentText() != text:
        logger_setup.get_logger().debug(f'ComboBox {comboBox.objectName()} text "{text}" not found in items.')

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
        model = comboBox.model()
        if isinstance(model, QSortFilterProxyModel):
            model = model.sourceModel()
    except AttributeError:
        model = comboBox.model()
    if model:
        tree_model, indexes = find_tree_model(model, None)
        if tree_model:
            count = tree_model.sourceModel().rowCount()
        else:
            count = model.rowCount()
        show_loading_dialog('Loading', f'Loading {count} items...')
        if isinstance(column, str):
            # If the column is a string, find the index of the column by its header data
            column_int = None
            from util.widgets.models.ReadableProxyModel import ReadableProxyModel
            if isinstance(model, ReadableProxyModel):
                # If the model is a ReadableProxyModel, get the readable header to compare
                column = get_readable_header(column)
            for col in range(model.columnCount()):
                header = model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)
                if header == column:
                    column_int = col
                    break
        else:
            column_int = column
        comboBox.setCompleter(None)
        comboBox.setModelColumn(column_int)
        if not isinstance(comboBox.view(), QtW.QListView):
            for model_column in range(model.columnCount()):
                if model_column != column_int:
                    try:
                        comboBox.view().hideColumn(model_column)
                    except AttributeError:
                        # If the view does not have a hideColumn method, no need
                        pass
            from util.widgets.models.TreeSortFilterProxyModel import TreeSortFilterProxyModel
            if isinstance(comboBox.view().model(), TreeSortFilterProxyModel):
                comboBox.view().model().update_visible_columns()
        if isinstance(comboBox.view().model(), QtC.QSortFilterProxyModel) and not tree_model:
            comboBox.view().model().sort(column_int, QtC.Qt.SortOrder.AscendingOrder)
        close_loading_dialog('Loading', f'Loading {count} items...')

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
    item_parent_dictionary = get_selected_tree_ids(tree_indexes)
    if action:
        action_text = action.text()
        item_ids = list(item_parent_dictionary.keys())
        first_item_id = item_ids[0] if item_ids else None
        if not first_item_id:
            action_text = 'Add'
        if action_text == 'Insert above':
            row = item_parent_dictionary[first_item_id][1]
            parent_id = item_parent_dictionary[first_item_id][0]
            dlg_args = {'parent_id' : parent_id, 'parent_row': row}
        elif action_text == 'Insert below':
            row = item_parent_dictionary[first_item_id][1] + 1
            parent_id = item_parent_dictionary[first_item_id][0]
            dlg_args = {'parent_id' : parent_id, 'parent_row': row}
        elif action_text == 'Add child':
            parent_id = first_item_id
            dlg_args = {'parent_id' : parent_id}
        elif action_text == 'Add parent':
            parent_ids = [item_parent_dictionary[item_id][0] for item_id in item_ids]
            parent_rows = [item_parent_dictionary[item_id][1] for item_id in item_ids]
            dlg_args = {'add_item': 'parent', 'item_ids': item_ids, 'old_parent_ids': parent_ids, 'old_parent_rows': parent_rows}
        elif action_text == 'Add to end' or action_text == 'Add':
            dlg_args = {'add_item': 'child'}
    return dlg_args

def save_expanded_state(table: str, tree_view: QtW.QTreeView):
    """
    Save the expanded state of the tree view to the settings
    :param table: Name of table with parent-child relationships
    :param tree_view: The view displaying the model
    :return:
    """
    if table not in SQLUtils.user_viewable_tables and table != 'Aliquots' and table != 'Ages':
        return
    show_loading_dialog('Saving expanded state', f'Saving the expanded state of {table}...')
    logger_setup.get_logger().info(f'Saving the expanded state of {table}...')
    start_save_expanded_time = time.time()
    from util.widgets.models.TrackExpandedTreeView import TrackExpandedTreeView
    if isinstance(tree_view, TrackExpandedTreeView):
        expanded_ids = tree_view.expanded_ids
    else:
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

    settings.setValue(f'expanded_ids_{table}', expanded_ids)
    logger_setup.get_logger().debug(f'Expanded state saved for {table} table in {time.time() - start_save_expanded_time} seconds')
    close_loading_dialog('Saving expanded state', f'Saving the expanded state of {table}...')

def restore_expanded_state(table: str, tree_view: QtW.QTreeView):
    """
    Restore the expanded state of the tree view from the set of expanded ids stored in settings
    :param table: Name of table with parent-child relationships
    :param tree_view: The view to display the model
    :return:
    """
    # logger_setup.get_logger().info(f'Restoring expanded state for {table} table')
    show_loading_dialog('Restoring expanded state', f'Restoring the expanded state of {table}...')
    logger_setup.get_logger().info(f'Restoring the expanded state of {table}...')
    start_expand_tree_time = time.time()
    expanded_ids = settings.value(f'expanded_ids_{table}', set())
    from util.widgets.models.TrackExpandedTreeView import TrackExpandedTreeView
    if isinstance(tree_view, TrackExpandedTreeView):
        tree_view.expanded_ids = expanded_ids
        tree_view.expand_from_ids()
    else:
        model = tree_view.model()
        from util.widgets.models.LazyCheckableTreeModel import LazyCheckableTreeModel
        if isinstance(model, LazyCheckableTreeModel):
            model.load_id_list(list(expanded_ids))
        def restore_state(index):
            if index.isValid():
                item_id = model.data(index.siblingAtColumn(1), QtC.Qt.ItemDataRole.DisplayRole)
                if item_id in expanded_ids and not tree_view.isExpanded(index):
                    tree_view.setExpanded(index, True)
                elif item_id not in expanded_ids and tree_view.isExpanded(index):
                    tree_view.setExpanded(index, False)
            row_count = model.rowCount(index)
            for row in range(row_count):
                restore_state(model.index(row, 0, index))
        restore_state(QtC.QModelIndex())

    logger_setup.get_logger().info(f'Expanded state restored in {time.time() - start_expand_tree_time} seconds')
    close_loading_dialog('Restoring expanded state', f'Restoring the expanded state of {table}...')

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
        if not tree_view.selectedIndexes() or len(tree_view.selectedIndexes()) == 0:
            return
        tree_view.expand(tree_view.selectedIndexes()[0])
    elif action.text() == 'Expand all children':
        for index in tree_view.selectedIndexes():
            expand_all_children(tree_view, index)
    elif action.text() == 'Expand all':
        tree_view.expandAll()
    elif action.text() == 'Collapse children':
        if not tree_view.selectedIndexes() or len(tree_view.selectedIndexes()) == 0:
            return
        tree_view.collapse(tree_view.selectedIndexes()[0])
    elif action.text() == 'Collapse all children':
        for index in tree_view.selectedIndexes():
            collapse_all_children(tree_view, index)
    elif action.text() == 'Collapse all':
        tree_view.collapseAll()
    tree_model = find_tree_model(tree_view.model(), [])[0]
    try:
        table = tree_model.tableName()
    except AttributeError:
        logger_setup.get_logger().error('Error saving expanded state')
        return
    save_expanded_state(table, tree_view)

def get_edit_column(table_id_header, item_table):
    if table_id_header in get_headers(item_table):
        return table_id_header
    else:
        # If not, check if it is part of a header name
        for header in get_headers(item_table):
            if table_id_header in header:
                return header
    logger_setup.get_logger().debug(f'Could not find edit column for {item_table} with header {table_id_header}')
    return None

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
    elif 'CalculatedConcordance_206Pb/238Uv207Pb/206Pb' in header:
        header = f'Calculated Concordance 206Pb/238Uv207Pb/206Pb ({settings.value('concordance_format_abbreviation')})'
    elif 'CalculatedConcordance_206Pb/238Uv207Pb/235U' in header:
        header = f'Calculated Concordance 206Pb/238Uv207Pb/235U ({settings.value('concordance_format_abbreviation')})'
    elif ('Age' in header and 'Calculated' in header
          and not any(s in header for s in ['Name', 'Description', 'Reference', 'Unit', 'Format', 'Created', 'Modified'])):
        header += f' ({settings.value("age_unit_abbreviation")})'
    elif 'Error' in header and 'Calculated' in header:
        if 'Corr/Rho' in header:
            header += f' ({settings.value("ratio_error_format_abbreviation")})'
        else:
            header = header.replace('Error', f' Error ({settings.value("ratio_error_format_abbreviation")})')
    if 'Name' in header and header not in ('SampleName', 'Sample Name', 'AliquotName', 'Aliquot Name', 'SpotName', 'Spot Name', 'GrainName', 'Grain Name', 'UPbAnalysisName', 'U-Pb Analysis Name'):
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
    if '8 U' in header:
        header = header.replace('8 U', '8U')
    if '5 U' in header:
        header = header.replace('5 U', '5U')
    if '2 Th' in header:
        header = header.replace('2 Th', '2Th')
    if ' Pb' in header:
        header = header.replace(' Pb', 'Pb')
    if ' U ' in header:
        header = header.replace(' U ', 'U ')
    if '(' in header and ' (' not in header:
        header = header.replace('(', ' (')
    return header







# ---------------------------
#    Database Methods
# ---------------------------

def update_other_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, update_table: str, update_ids: list) -> str:
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
    :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
    """
    if not update_ids:
        logger_setup.get_logger().error(f'No item IDs given for {update_table}')
        return 'False'
    if partially_checked_ids:
        # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
        logger_setup.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
        return 'No'
    if len(checked_ids) > 1:
        # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
        logger_setup.get_logger().error(f'Multiple checked IDs given for {table}. Select only one ID to update {update_table}.')
        logger_setup.get_logger().debug(f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
        return 'False'
    id_header = get_headers(table)[0]
    other_id_header = get_headers(update_table)[0]
    current_ids = []
    query = QtS.QSqlQuery()
    if len(update_ids) > 1:
        query_where_str = f'in {tuple(update_ids)}'
    else:
        query_where_str = f'= {update_ids[0]}'
    # Check that the id_header is in the update_table headers
    id_header = get_edit_column(id_header, update_table)
    if not id_header:
        logger_setup.get_logger().critical(f'Error saving checks for {table}')
        logger_setup.get_logger().debug(f'Could not find {table} ID header in {update_table}')
        return 'False'
    query.prepare(f"SELECT {id_header} FROM {update_table} WHERE {other_id_header} {query_where_str}")
    if not query.exec():
        logger_setup.get_logger().critical(
            f'Failed to get items from {update_table}')
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return 'False'
    while query.next():
        current_id = query.value(0)
        if current_id != '':
            if int(current_id) not in current_ids:
                current_ids.append(int(current_id))
        else:
            if None not in current_ids:
                current_ids.append(None)
    if current_ids == checked_ids or checked_ids == [] and current_ids == [None]:
        logger_setup.get_logger().info(f'Checks are up to date')
        return 'No'
    create_savepoint('update_other_table')
    if len(list(checked_ids)) == 0:
        if not query.exec(f'UPDATE {update_table} SET {id_header} = NULL WHERE {other_id_header} {query_where_str}'):
            logger_setup.get_logger().critical(f'Failed to remove item from {update_table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('update_other_table')
            return 'False'
        logger_setup.get_logger().info(f'Cleared {id_header} in {update_table}')
    else:
        if not query.exec(f'UPDATE {update_table} SET {id_header} = {list(checked_ids)[0]} WHERE {other_id_header} {query_where_str}'):
            logger_setup.get_logger().critical(f'Failed to add item to {update_table}')
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('update_other_table')
            return 'False'
        logger_setup.get_logger().info(f'Added {id_header} {list(checked_ids)[0]} to {update_table}')
    update_modified_timestamp(update_table, update_ids)
    release_savepoint('update_other_table')
    return 'True'

def update_many_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, many_table: str, first_table_ids: list) -> str:
    """
    Take the checked ids from a table and update that field in the second column of a many-to-many table with another table.
    The relationship must be many-to-many, so partially checked IDs are permitted.
    :param table: table with checked data (e.g. Regions)
    :param checked_ids: ids of checked items in the table (e.g. list of region IDs)
    :param partially_checked_ids: ids of partially checked items in the table (e.g. list of region IDs that are partially checked)
    :param many_table: many-to-many table to update (e.g. Samples_Regions)
    :param first_table_ids: ids to update in the first table (e.g. list of sample IDs to link to the checked region IDs)
    :return: 'True' if successful, 'No' if not needed, 'False' needed but failed
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
        return 'False'
    query_model.setQuery(
        f'SELECT {first_table_id_header}, {second_table_id_header} FROM {many_table} WHERE {first_table_id_header} {query_where_str}')
    while query_model.canFetchMore():
        query_model.fetchMore()
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
        return 'False'
    while query_model.canFetchMore():
        query_model.fetchMore()
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
        return 'No'
    if to_remove:
        for id in to_remove:
            query.prepare(
                f"DELETE FROM {many_table} WHERE {first_table_id_header} {query_where_str} AND {second_table_id_header} = {id}")
            if not query.exec():
                logger_setup.get_logger().critical(f"Error unchecking {second_table} from {first_table}")
                logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
                logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('update_many_table')
                return 'False'
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
                        return 'False'
        logger_setup.get_logger().info(f"Added {to_add} associated with item IDs {first_table_ids} to {many_table}")
    logger_setup.get_logger().info(
        f"Successfully updated {many_table} for {first_table_id_header} {first_table_ids}")
    release_savepoint('update_many_table')
    return 'True'

eventTypeNames = {event_type: event_type.name for event_type in QtC.QEvent.Type}


# ---------------------------
#    Python Methods
# ---------------------------

def search_dictionary(dictionary: dict, target_value):
    """
    Search a nested dictionary for a target value.
    :param dictionary:
    :param target_value:
    :return:
    """
    if not isinstance(dictionary, dict):
        return False

    def search_nested_dict(search_dict):
        for key, value in search_dict.items():
            if key == target_value:
                return True
            elif isinstance(value, dict):
                if search_nested_dict(value):
                    return True
            else:
                if value == target_value:
                    return True
        return False

    return search_nested_dict(dictionary)