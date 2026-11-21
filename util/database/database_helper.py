import time

from PyQt6 import QtSql, QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QSortFilterProxyModel
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QApplication, QMessageBox

from Functions import SQLUtils
from Functions.Database_views import ViewQuery
from util import logger
from util.database.Savepoint_manager import rollback_savepoint, release_savepoint, create_savepoint
from util.database.defined_joins import *
from util.display_formatting import get_readable_header
from util.loading_dialog_manager import close_loading_dialog, show_loading_dialog, LoadingDialogManager
from util.settings_manager import SettingsManager

settings = SettingsManager().settings


def get_database_tables() -> list:
    """
    Returns a list of all tables in the database.
    :return: List of table names
    """
    query = QtSql.QSqlQuery()
    if not query.exec('SELECT name FROM sqlite_master WHERE type="table"'):
        logger.get_logger().critical("Failed to get database tables")
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        return []
    tables = []
    while query.next():
        if query.value(0) not in tables:
            tables.append(query.value(0))
    return tables


def set_table(model: QtSql.QSqlTableModel, table: str) -> QtSql.QSqlTableModel | bool:
    """
    Convenience method to set the table for a QSqlTableModel and select the data. Notifies if any errors occur.
    :param model: QSqlTableModel to populate
    :param table: Name of the SQL database table to populate the model
    :return: populated model if successful, False if not
    """
    # logger_setup.get_logger().info(f"Setting table to {table}")
    model.setTable(table)
    if model.lastError().text():
        logger.get_logger().critical(f"Failed to set table to {table})")
        logger.get_logger().debug(f"setTable error: {model.lastError().text()}")
        return False
    model.select()
    if model.lastError().text():
        logger.get_logger().critical(f"Failed to set table to {table})")
        logger.get_logger().debug(f"select error: {model.lastError().text()}")
        return False
    from util.widgets.models.table_models import LazyCheckableSqlTableModel
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
    query = QtSql.QSqlQuery()
    if 'View' in table:
        show_columns = settings.value(SQLUtils.view_setting_dict[table])
        return show_columns
    table = table.replace('"', '').strip()
    if not query.exec(f'PRAGMA table_xinfo("{table}")'):
        logger.get_logger().critical(f"Failed to get headers for {table}")
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return []
    headers = []
    while query.next():
        headers.append(query.value(1))
    return headers


def get_columns(table: str, database: QSqlDatabase = None):
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
        query = QtSql.QSqlQuery()
    else:
        query = QtSql.QSqlQuery(database)
    if not query.exec(f'PRAGMA table_xinfo("{table}")'):
        logger.get_logger().critical(f"Failed to get columns for {table}")
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
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
    model = QtSql.QSqlQueryModel()
    model.setQuery(query)
    if model.lastError().text():
        logger.get_logger().critical(f"Failed to get columns from query")
        logger.get_logger().debug(f"Query: {query}")
        logger.get_logger().debug(f"Error: {model.lastError().text()}")
        return [None for column in cols]
    while model.canFetchMore():
        model.fetchMore()
    columns = []
    for col in cols:
        if isinstance(col, int):
            column = col
        elif isinstance(col, str):
            headers = [model.headerData(i, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole) for i
                       in range(model.columnCount())]
            column = headers.index(col)
        else:
            logger.get_logger().critical(f"Failed to get list in table")
            logger.get_logger().debug(f"Invalid column: {col}")
            logger.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        if column < 0 or column >= model.columnCount():
            logger.get_logger().critical(f"Failed to get list in table")
            logger.get_logger().debug(
                f"Column index {column} out of range for model with {model.columnCount()} columns")
            logger.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        columns.append(column)
    column_lists = []
    for column in columns:
        # Collect unique values from the column
        column_list = list(
            set(model.index(row, column).data(QtCore.Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())))
        if column_list == ['']:
            column_list = []
        column_lists.append(column_list)
    return column_lists


def columns_as_list(query: str, cols: list, view_query: ViewQuery = None) -> list | None:
    """
    Returns lists of items in given columns. This method reflects only committed changes.
    :param cols: List of column indexes as integers or SQL table column headers
    :param query: SQL query of data for table
    :param view_query: ViewQuery object to use for the query, if applicable
    :return: lists of items in each row for given columns
    """
    from util.widgets.models.table_models import SQLiteTableModel
    model = SQLiteTableModel(query, view_query=view_query)
    if model.last_error:
        return None
    columns = []
    for col in cols:
        if isinstance(col, int):
            column = col
        elif isinstance(col, str):
            headers = [model.headerData(i, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole) for i
                       in
                       range(model.columnCount())]
            column = headers.index(col)
        else:
            logger.get_logger().critical(f"Failed to get list in table")
            logger.get_logger().debug(f"Invalid column: {col}")
            logger.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        if column < 0 or column >= model.columnCount():
            logger.get_logger().critical(f"Failed to get list in table")
            logger.get_logger().debug(
                f"Column index {column} out of range for model with {model.columnCount()} columns")
            logger.get_logger().debug(f"SQL query: {query}")
            return [None for column in cols]
        columns.append(column)
    column_lists = []
    for column in columns:
        # Collect unique values from the column
        column_list = list(set(model.index(row, column).data(QtCore.Qt.ItemDataRole.DisplayRole) for row in
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
        logger.get_logger().info("No table provided")
        return None
    if not item_id:
        logger.get_logger().info(f"No ID provided for {table}")
        return None
    query = QtSql.QSqlQuery()
    headers = get_headers(table)
    if table == '"References"':
        table = 'References'
    sql_query = f'SELECT {headers[get_name_column(table)]} FROM "{table}" WHERE {headers[0]}={item_id}'
    # logger_setup.get_logger().debug(f'SQL command: {sql_query}')
    if not query.exec(sql_query):
        logger.get_logger().critical(f"Failed to get name for {item_id} in {table}")
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
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
    query = QtSql.QSqlQuery()
    headers = get_headers(table)
    logger.get_logger().info(f'Getting ID for {name} in {table}')
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
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
    query.bindValue(":name", str(name))
    if not query.exec():
        logger.get_logger().critical(f"Failed to get ID for {name} in {table}")
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
        logger.get_logger().debug(f"Bound values: {query.boundValues()}")
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
    query = QtSql.QSqlQuery()
    headers = get_headers(table)
    logger.get_logger().info(f'Getting ID for {abbreviation} in {table}')
    sql_query = f'SELECT {headers[0]} FROM "{table}" WHERE {headers[get_abbreviation_column(table)]}=:name COLLATE NOCASE'
    # logger_setup.get_logger().debug(f'SQL command: {sql_query}')
    if not query.prepare(sql_query):
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
    query.bindValue(":name", str(abbreviation))
    if not query.exec():
        logger.get_logger().critical(f"Failed to get ID for {abbreviation} in {table}")
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
        logger.get_logger().debug(f"Bound values: {query.boundValues()}")
        return None
    query.next()
    return query.value(0)


def get_total_records(table: str, where: str = '') -> int:
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
    logger.get_logger().info(f'Fetching total records for {table}')
    if not query.exec(sql_query):
        # Handle query execution error
        logger.get_logger().critical(f'Error fetching total records')
        logger.get_logger().debug(f'Error: {query.lastError().text()}')
        logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
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
        logger.get_logger().error(f'Cannot get record index for tree {table}')
        logger.get_logger().debug(
            f'Table {table} is a tree view which does not use sorting or paging, so cannot get record index')
        logger.get_logger().debug(f'Inspect code to remove sorting and paging for trees')
        return -1
    if not ids_to_show:
        ids_to_show = []
    if record_id not in ids_to_show and len(ids_to_show) > 0:
        record_name = get_name_from_id(table, record_id)
        logger.get_logger().error(f'Record {record_name} not available in this view')
        logger.get_logger().debug(f'Record ID {record_id} in the list of IDs to show: {ids_to_show}')
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

    logger.get_logger().info(f'Getting the record index for record ID: {record_id}')
    # Execute the query
    if not query.exec():
        # Handle query execution error
        logger.get_logger().critical(f'Error fetching the record')
        logger.get_logger().debug(f'Error fetching records index: {query.lastError().text()}')
        logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
        logger.get_logger().debug(f'Bound values: {query.boundValues()}')
        return -1

    # Fetch the result
    if query.next():
        return query.value(0) - 1  # Convert to zero-based index

    return -1


def get_join_from_table(join: str, tables: list[str]) -> str:
    """
    Function to take a current SQL join string and append other join strings based upon a list of tables.

    :param str join: Current join statement to add to
    :param list[str] tables: List of tables to append to the join statement
    :return: Final join with added tables
    :rtype: str
    """
    for table in tables:
        match table:
            case 'AgeConstraints':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_constraint_join not in join:
                    join += sampleage_age_constraint_join + '\n'
            case 'AgeInterpretations':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_interpretation_join not in join:
                    join += sampleage_age_interpretation_join + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Ages':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
            case 'OldAge':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
                if sample_age_left_joins not in join:
                    join += sample_age_left_joins + '\n'
            case 'YoungAge':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
                if sample_age_left_joins not in join:
                    join += sample_age_left_joins + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Aliquots':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
            case 'AliquotContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_context_join not in join:
                    join += aliquot_context_join + '\n'
            case 'Columns':
                if column_join not in join:
                    join += column_join + '\n'
            case 'DefaultSampleAges':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += default_sample_age_join + '\n'
            case 'LabFacilities':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_labs_join not in join:
                    join += upb_labs_join + '\n'
            case 'Grains':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
            case 'GrainCompositions':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
                if grain_composition_join not in join:
                    join += grain_composition_join + '\n'
            case 'GrainContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
                if grain_context_join not in join:
                    join += grain_context_join + '\n'
            case 'GPSLocations':
                if gps_sample_join not in join:
                    join += gps_sample_join + '\n'
                if gps_sample_left_joins not in join:
                    join += gps_sample_left_joins + '\n'
            case 'Instruments':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_instruments_join not in join:
                    join += upb_instruments_join + '\n'
            case 'References' | '"References"':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'ReferenceView':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
            case 'Regions':
                if region_join not in join:
                    join += region_join + '\n'
            case 'UPbRejectionReasons':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_rejection_reason_join not in join:
                    join += upb_rejection_reason_join + '\n'
            case 'GeoChemRejectionReasons':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_rejection_reasons_join not in join:
                    join += geochem_rejection_reasons_join + '\n'
            case 'RockTypes':
                if rock_type_join not in join:
                    join += rock_type_join + '\n'
            case 'SampleAges':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += default_sample_age_join + '\n'
            case 'SampleAgeConstraints':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_constraint_join not in join:
                    join += sampleage_age_constraint_join + '\n'
            case 'SampleAgeInterpretations':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_interpretation_join not in join:
                    join += sampleage_age_interpretation_join + '\n'
            case 'SampleAgeReferences':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_reference_join not in join:
                    join += sampleage_age_reference_join + '\n'
            case 'SampleContexts':
                if sample_context_join not in join:
                    join += sample_context_join + '\n'
            case 'SamplingMethods':
                if sampling_method_join not in join:
                    join += sampling_method_join + '\n'
            case 'Settings':
                if setting_join not in join:
                    join += setting_join + '\n'
            case 'Spots':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
            case 'SpotCompositions':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_composition_join not in join:
                    join += spot_composition_join + '\n'
            case 'SpotContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_context_join not in join:
                    join += spot_context_join + '\n'
            case 'UPbAgeInterpretations':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_age_interpretation_join not in join:
                    join += upb_age_interpretation_join + '\n'
            case 'UPbAnalyses':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
            case 'UPbAnalysisContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_context_join not in join:
                    join += upb_context_join + '\n'
            case 'UPbAnalysisMethods':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_method_join not in join:
                    join += upb_method_join + '\n'
            case 'UPbReferences':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'GeoChemicalAnalyses':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
            case 'GeoChemicalAnalysisContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_contexts_join not in join:
                    join += geochem_contexts_join + '\n'
            case 'GeoChemicalMethods':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_method_join not in join:
                    join += geochem_method_join + '\n'
            case 'GeoChemReferences':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_reference_join not in join:
                    join += geochem_reference_join + '\n'
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'
            case 'Samples':
                pass
    return join


def get_column_types(table: str):
    query = QtSql.QSqlQuery()
    column_types = []
    if not query.exec(f'PRAGMA table_info("{table}")'):
        logger.get_logger().critical(f"Failed to get columns for {table}")
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return column_types
    while query.next():
        column_types.append(query.value(2))
    return column_types


def delete_query(table: str, ids: list):
    moved_ids = []  # Keep track of IDs that were moved during deletion
    if not ids:
        logger.get_logger().error(f"No IDs given for deletion in {table}")
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
            logger.get_logger().warning(f"Could not find name for ID {item_id} in {table}")
            logger.get_logger().debug(f"ID {item_id} not found in {table}")
            rollback_savepoint('before_delete')
            return False, moved_ids
    logger.get_logger().info(f"Deleting {table}: {delete_names}")
    query = QtSql.QSqlQuery()
    headers = get_headers(table)
    id_header = headers[0]  # Get the first header which is the ID column
    for delete_id in ids:
        parent_id = None
        parent_row = None
        if table in SQLUtils.user_viewable_trees:
            query.exec(f'SELECT {headers[1]}, {headers[2]} FROM "{table}" WHERE {id_header}={delete_id}')
            if not query.next():
                logger.get_logger().critical(
                    f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
                logger.get_logger().debug(
                    f"ID {delete_id} not found in {table}. Unable to retrieve parent information for tree structure.")
                rollback_savepoint('before_delete')
                return False, moved_ids
            parent_id = query.value(0)
            parent_row = query.value(1)
        query.prepare(f'DELETE FROM "{table}" WHERE {id_header}={delete_id}')
        if not query.exec():
            logger.get_logger().critical(
                f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
            logger.get_logger().debug(f"Error: {query.lastError().text()}")
            logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_delete')
            return False, moved_ids
        logger.get_logger().info(f"Successfully deleted ID {delete_id} from {table}")
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
                logger.get_logger().critical(
                    f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
                logger.get_logger().debug(f"Error finding affected records during delete")
                logger.get_logger().debug(f"Error: {query.lastError().text()}")
                logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint(f"before_delete")
                return False, moved_ids
            while query.next():
                affected_ids.append(query.value(0))
            for affected_id in affected_ids:
                update_query = f'UPDATE "{table}" SET {headers[2]} = {headers[2]} - 1 WHERE {id_header} = {affected_id}'
                if not query.exec(update_query):
                    logger.get_logger().critical(
                        f"Failed to delete {', '.join(get_name_from_id(table, item_id) for item_id in ids)} from {table}")
                    logger.get_logger().debug(f"Error updating affected record during delete")
                    logger.get_logger().debug(f"Error: {query.lastError().text()}")
                    logger.get_logger().debug(f"SQL query: {update_query}")
                    rollback_savepoint(f"before_delete")
                    return False, moved_ids
                if affected_id not in ids and affected_id not in moved_ids:
                    moved_ids.append(affected_id)
            if moved_ids:
                from Functions.Check_triggers import update_modified_timestamp
                update_modified_timestamp(table, moved_ids)
    logger.get_logger().info(f"Deleted {len(ids)} records from {table}")
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
        logger.get_logger().error(f"No IDs given for deletion in {table}")
        return False
    if not delete_question(table, data_ids):
        logger.get_logger().info(f"Deletion cancelled for {table} with IDs: {', '.join(map(str, data_ids))}")
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
        delete_aliquot_ids, delete_grain_ids, delete_spot_ids, delete_upb_analysis_ids = find_current_sub_items(
            data_ids, table)
        aliquot_child_ids = []
        for parent_id in delete_aliquot_ids:
            aliquot_child_ids = find_child_ids('Aliquots', parent_id, aliquot_child_ids)
        delete_sample_ids = data_ids
        logger.get_logger().info(
            f"Deleting {len(delete_sample_ids)} samples, {len(delete_aliquot_ids)} aliquots, {len(aliquot_child_ids)} sub-aliquots, {len(delete_grain_ids)} grains, {len(delete_spot_ids)} spots, and {len(delete_upb_analysis_ids)} UPb analyses")
        delete_aliquot_ids.extend(aliquot_child_ids)
    elif table == 'Aliquots':
        delete_grain_ids, delete_spot_ids, delete_upb_analysis_ids = find_current_sub_items(data_ids, table)
        delete_aliquot_ids = data_ids
        aliquot_child_ids = []
        for parent_id in delete_aliquot_ids:
            aliquot_child_ids = find_child_ids('Aliquots', parent_id, aliquot_child_ids)
        logger.get_logger().info(
            f"Deleting {len(delete_aliquot_ids)} aliquots, {len(aliquot_child_ids)} sub-aliquots, {len(delete_grain_ids)} grains, {len(delete_spot_ids)} spots, and {len(delete_upb_analysis_ids)} UPb analyses")
        delete_aliquot_ids.extend(aliquot_child_ids)
        parent_samples = find_current_parent_items(delete_aliquot_ids, table)
        if parent_samples:
            # Determine if all aliquots of these samples are being deleted
            for sample_id in parent_samples:
                sub_aliquot_ids, sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id],
                                                                                                            'Samples')
                if not any(aliquot_id not in delete_aliquot_ids for aliquot_id in sub_aliquot_ids):
                    # If all aliquots of the sample are being deleted, add the sample to the list
                    if sample_id not in childless_samples:
                        childless_samples.append(sample_id)
    elif table == 'Grains':
        delete_spot_ids, delete_upb_analysis_ids = find_current_sub_items(data_ids, table)
        delete_grain_ids = data_ids
        logger.get_logger().info(
            f"Deleting {len(delete_grain_ids)} grains, {len(delete_spot_ids)} spots, and {len(delete_upb_analysis_ids)} UPb analyses")
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
        logger.get_logger().info(
            f"Deleting {len(delete_spot_ids)} spots and {len(delete_upb_analysis_ids)} UPb analyses")
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
        logger.get_logger().info(f"Deleting {len(delete_upb_analysis_ids)} UPb analyses")
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
                sub_parent_sample_ids, sub_parent_aliquot_ids, sub_parent_spot_ids = find_current_parent_items(
                    [grain_id], 'Grains')
                if not any(spot_id not in childless_spots for spot_id in sub_parent_spot_ids):
                    # If all Spots of the grain are being deleted, add the grain to the list
                    if grain_id not in spotless_grains:
                        spotless_grains.append(grain_id)
        if childless_aliquots:
            # Determine if all UPb analyses of these samples are being deleted
            for sample_id in parent_samples:
                sub_aliquot_ids, sub_grain_ids, sub_spot_ids, sub_upb_analysis_ids = find_current_sub_items([sample_id],
                                                                                                            'Samples')
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
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
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
            msg_box.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Cancel)
            response = msg_box.exec()
            if response == QtWidgets.QMessageBox.StandardButton.Yes:
                # If the user wants to delete the empty items, add them to the deletion lists
                delete_all = True
            elif response == QtWidgets.QMessageBox.StandardButton.No:
                delete_all = False
            else:
                # cancel the deletion
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                logger.get_logger().info(
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

    # Double-check that foreign keys are enabled
    if not turn_on_foreign_keys():
        close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
        return False
    if table in ('Samples', 'Aliquots', 'Spots', 'UPbAnalyses'):
        if delete_upb_analysis_ids:
            if not delete_query('UPbAnalyses', delete_upb_analysis_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger.get_logger().info(f'Deleted {len(delete_upb_analysis_ids)} UPb analyses')
        if delete_grain_ids:
            if not delete_query('Grains', delete_grain_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger.get_logger().info(f'Deleted {len(delete_grain_ids)} Grains')
        if delete_spot_ids:
            if not delete_query('Spots', delete_spot_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger.get_logger().info(f'Deleted {len(delete_spot_ids)} spots')
        if delete_aliquot_ids:
            parent_samples = find_current_parent_items(delete_aliquot_ids, 'Aliquots')
            query = f'SELECT * FROM Aliquots WHERE SampleID in ({parent_samples})'
            aliquot_model = QtSql.QSqlQueryModel()
            aliquot_model.setQuery(query)
            from util.widgets.models.tree_models import TreeModel
            aliquot_tree = TreeModel(aliquot_model)
            if not aliquot_tree.removeItems(delete_aliquot_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger.get_logger().info(f'Deleted {len(delete_aliquot_ids)} Aliquots')
        if delete_sample_ids:
            if not delete_query('Samples', delete_sample_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger.get_logger().info(f'Deleted {len(delete_sample_ids)} Samples')
    else:
        if table_child_ids:
            delete_ids = data_ids + table_child_ids
        else:
            delete_ids = data_ids
        if delete_ids:
            if not delete_query(table, delete_ids)[0]:
                close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
                return False
            logger.get_logger().info(f'Deleted {len(delete_ids)} {table} records')

    close_loading_dialog('Deleting', f'Deleting {len(data_ids)} {table}...')
    return True


def delete_question(table, delete_ids):
    show_loading_dialog('Preparing', 'Gathering information...')
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
    detail_text = ''
    if table == 'Samples':
        sample_names = [get_name_from_id(table, sample_id) for sample_id in delete_ids]
        if None in sample_names:
            logger.get_logger().info(f'Samples were already deleted or do not exist')
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
            upb_analysis_names = [get_name_from_id('UPbAnalyses', upb_analysis_id) for upb_analysis_id in
                                  upb_analysis_ids]
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
            upb_analysis_names = [get_name_from_id('UPbAnalyses', upb_analysis_id) for upb_analysis_id in
                                  upb_analysis_ids]
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
    msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
    close_loading_dialog('Preparing', 'Gathering information...')
    response = msg_box.exec()
    if response == QtWidgets.QMessageBox.StandardButton.Yes:
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
    query = QtSql.QSqlQuery()
    table_headers = get_headers(table)
    id_header = table_headers[0]  # Get the first column header which is the ID column
    parent_id_header = table_headers[1]  # Get the second column header which is the Parent ID column
    query.prepare(f'SELECT {id_header} FROM {table} WHERE {parent_id_header}=:parent_id')
    query.bindValue(':parent_id', parent_id)
    if not query.exec():
        logger.get_logger().critical(f"Error finding child aliquots to delete")
        logger.get_logger().debug(f'Error: {query.lastError().text()}')
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
        logger.get_logger().warning(f"No item IDs provided for finding foreign associations in {table}")
        return {}
    logger.get_logger().info(f"Finding foreign associations for {len(item_ids)} {table}")
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
            from util.widgets.models.table_models import SQLiteTableModel
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
                    foreign_table_model = SQLiteTableModel(
                        f'SELECT {get_headers(db_table)[0]} FROM "{db_table}" {where_one}')
                    if not foreign_table_model.last_error:
                        for row in range(foreign_table_model.rowCount()):
                            foreign_id = foreign_table_model.data(foreign_table_model.index(row, 0))
                            if foreign_id and foreign_id not in associations[db_table]:
                                associations[db_table].append(foreign_id)
                    break
    return associations


def find_upb_from_samples(sample_ids):
    # Find UPb analyses for a list of samples
    logger.get_logger().info(f"Finding UPb Analyses for {len(sample_ids)} samples")
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
    from util.widgets.models.table_models import SQLiteTableModel
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
    logger.get_logger().info(f"Finding sub items for {len(data_ids)} {table}")
    if not data_ids:
        logger.get_logger().warning(f"No data IDs provided for finding sub items in {table}")
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
                        {aliquot_spot_join}
                        {spot_upb_analysis_join}
                        WHERE SampleID {where}"""
        aliquot_ids, spot_ids, upb_analysis_ids = columns_as_list(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return aliquot_ids, spot_ids, upb_analysis_ids
    elif table == 'Aliquots':
        sql_query = f"""SELECT Spots.SpotID, UPbAnalyses.UPbAnalysisID FROM Spots
                        {spot_upb_analysis_join}
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
        logger.get_logger().critical(f"Table {table} in not supported for finding sub items")
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
    logger.get_logger().info(f"Finding parent items for {len(data_ids)} {table}")
    if not data_ids:
        logger.get_logger().warning(f"No data IDs provided for finding parent items in {table}")
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
                        {upb_spot_join}
                        {spot_aliquot_join}
                        WHERE UPbAnalysisID {where}"""
        sample_ids, aliquot_ids, spot_ids = columns_as_list(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids, spot_ids
    elif table == 'Spots':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, Spots.GrainID FROM Spots
                        {spot_aliquot_join}
                         WHERE SpotID {where}"""
        sample_ids, aliquot_ids, grain_ids = columns_as_list(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids
    elif table == 'Grains':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID FROM Spots
                                {spot_aliquot_join}
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
        logger.get_logger().critical(f"Table {table} in not supported for finding parent items")
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
    logger.get_logger().info(f"Finding sub items for {len(data_ids)} {table}")
    aliquot_ids = []
    grain_ids = []
    spot_ids = []
    upb_analysis_ids = []
    if not data_ids:
        logger.get_logger().warning(f"No data IDs provided for finding sub items in {table}")
        if table == 'Spots':
            return grain_ids, upb_analysis_ids
        elif table == 'Grains':
            return spot_ids, upb_analysis_ids
        elif table == 'Aliquots':
            return grain_ids, spot_ids, upb_analysis_ids
        elif table == 'Samples':
            return aliquot_ids, grain_ids, spot_ids, upb_analysis_ids
        else:
            logger.get_logger().critical(f"Table {table} in not supported for finding sub items")
            return None, None, None, None
    show_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    if table == 'Samples':
        sql_query = f"""SELECT Aliquots.AliquotID, Spots.SpotID, Grains.GrainID, UPbAnalyses.UPbAnalysisID FROM Aliquots
                        {aliquot_spot_join}
                        {spot_upb_analysis_join}
                        {spot_grain_join}
                        WHERE Aliquots.SampleID {where}"""
        aliquot_ids, spot_ids, grain_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1, 2, 3])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return aliquot_ids, grain_ids, spot_ids, upb_analysis_ids
    elif table == 'Aliquots':
        sql_query = f"""SELECT Spots.SpotID, Grains.GrainID, UPbAnalyses.UPbAnalysisID FROM Spots
                        {spot_upb_analysis_join}
                        {spot_grain_join}
                        WHERE Spots.AliquotID {where}"""
        spot_ids, grain_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return grain_ids, spot_ids, upb_analysis_ids
    elif table == 'Spots':
        sql_query = f"""SELECT Grains.GrainID, UPbAnalyses.UPbAnalysisID FROM UPbAnalyses
                        {upb_spot_join}
                        {spot_grain_join}
                        WHERE UPbAnalyses.SpotID {where}"""
        grain_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return grain_ids, upb_analysis_ids
    elif table == 'Grains':
        sql_query = f"""SELECT Spots.SpotID, UPbAnalyses.UPbAnalysisID FROM UPbAnalyses
                        {upb_spot_join}
                        WHERE Spots.GrainID {where}"""
        spot_ids, upb_analysis_ids = columns_as_list_current(sql_query, [0, 1])
        close_loading_dialog('Finding Sub Items', f'Finding sub items for {len(data_ids)} {table}...')
        return spot_ids, upb_analysis_ids
    else:
        logger.get_logger().critical(f"Table {table} in not supported for finding sub items")
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
    logger.get_logger().info(f"Finding parent items for {len(data_ids)} {table}")
    if not data_ids:
        logger.get_logger().warning(f"No data IDs provided for finding parent items in {table}")
        return None, None, None, None
    show_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
    if len(data_ids) > 1:
        where = f'IN {tuple(data_ids)}'
    else:
        where = f'= {data_ids[0]}'
    if table == 'UPbAnalyses':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, Spots.GrainID, UPbAnalyses.SpotID FROM UPbAnalyses 
                        {upb_spot_join}
                        {spot_grain_join}
                        {spot_aliquot_join}
                        WHERE UPbAnalysisID {where}"""
        sample_ids, aliquot_ids, grain_ids, spot_ids = columns_as_list_current(sql_query, [0, 1, 2, 3])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids, grain_ids, spot_ids
    elif table == 'Grains':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID, Spots.SpotID FROM Spots
                        {spot_aliquot_join}
                        WHERE Spots.GrainID {where}"""
        sample_ids, aliquot_ids, spot_ids = columns_as_list_current(sql_query, [0, 1, 2])
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return sample_ids, aliquot_ids, spot_ids
    elif table == 'Spots':
        sql_query = f"""SELECT Aliquots.SampleID, Spots.AliquotID FROM Spots
                        {spot_aliquot_join}
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
        logger.get_logger().critical(f"Table {table} in not supported for finding parent items")
        close_loading_dialog('Finding Parent Items', f'Finding parent items for {len(data_ids)} {table}...')
        return None, None, None


def update_other_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, update_table: str,
                                   update_ids: list) -> str:
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
        logger.get_logger().error(f'No item IDs given for {update_table}')
        return 'False'
    if partially_checked_ids:
        # Any selection for a one-to-many relationship should be complete, so there should be no partially checked IDs
        logger.get_logger().info(f'Partially checked IDs for one-to-many relationship, no changes to update')
        return 'No'
    if len(checked_ids) > 1:
        # If there are multiple checked IDs, this is a many-to-many relationship, so we should not use this function
        logger.get_logger().error(
            f'Multiple checked IDs given for {table}. Select only one ID to update {update_table}.')
        logger.get_logger().debug(
            f'This should be a one-to-many relationship, so set the checkable combo box to single click.')
        return 'False'
    id_header = get_headers(table)[0]
    other_id_header = get_headers(update_table)[0]
    current_ids = []
    query = QtSql.QSqlQuery()
    if len(update_ids) > 1:
        query_where_str = f'in {tuple(update_ids)}'
    else:
        query_where_str = f'= {update_ids[0]}'
    # Check that the id_header is in the update_table headers
    id_header = get_edit_column(id_header, update_table)
    if not id_header:
        logger.get_logger().critical(f'Error saving checks for {table}')
        logger.get_logger().debug(f'Could not find {table} ID header in {update_table}')
        return 'False'
    query.prepare(f"SELECT {id_header} FROM {update_table} WHERE {other_id_header} {query_where_str}")
    if not query.exec():
        logger.get_logger().critical(
            f'Failed to get items from {update_table}')
        logger.get_logger().debug(f"Error: {query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
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
        logger.get_logger().info(f'Checks are up to date')
        return 'No'
    create_savepoint('update_other_table')
    if len(list(checked_ids)) == 0:
        if not query.exec(f'UPDATE {update_table} SET {id_header} = NULL WHERE {other_id_header} {query_where_str}'):
            logger.get_logger().critical(f'Failed to remove item from {update_table}')
            logger.get_logger().debug(f"Error: {query.lastError().text()}")
            logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('update_other_table')
            return 'False'
        logger.get_logger().info(f'Cleared {id_header} in {update_table}')
    else:
        if not query.exec(
                f'UPDATE {update_table} SET {id_header} = {list(checked_ids)[0]} WHERE {other_id_header} {query_where_str}'):
            logger.get_logger().critical(f'Failed to add item to {update_table}')
            logger.get_logger().debug(f"Error: {query.lastError().text()}")
            logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('update_other_table')
            return 'False'
        logger.get_logger().info(f'Added {id_header} {list(checked_ids)[0]} to {update_table}')
    from Functions.Check_triggers import update_modified_timestamp
    update_modified_timestamp(update_table, update_ids)
    release_savepoint('update_other_table')
    return 'True'


def update_many_table_with_checks(table: str, checked_ids: list, partially_checked_ids: list, many_table: str,
                                  first_table_ids: list) -> str:
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
    query_model = QtSql.QSqlQueryModel()
    query = QtSql.QSqlQuery()
    if len(first_table_ids) > 1:
        query_where_str = f'in {tuple(first_table_ids)}'
    elif len(first_table_ids) == 1:
        query_where_str = f'= {first_table_ids[0]}'
    else:
        logger.get_logger().error(f'No item IDs given for {first_table}')
        return 'False'
    query_model.setQuery(
        f'SELECT {first_table_id_header}, {second_table_id_header} FROM {many_table} WHERE {first_table_id_header} {query_where_str}')
    while query_model.canFetchMore():
        query_model.fetchMore()
    current_pairs = []
    for row in range(query_model.rowCount()):
        first_id = query_model.data(query_model.index(row, 0), QtCore.Qt.ItemDataRole.DisplayRole)
        second_id = query_model.data(query_model.index(row, 1), QtCore.Qt.ItemDataRole.DisplayRole)
        pair = (first_id, second_id)
        if pair not in current_pairs:
            current_pairs.append(pair)
    model_query = f'SELECT {second_table_id_header} FROM "{second_table}"'
    query_model.setQuery(model_query)
    if query_model.lastError().isValid():
        logger.get_logger().critical(f'Error getting {table} checks for {first_table}')
        logger.get_logger().debug(f'Error: {query_model.lastError().text()}')
        logger.get_logger().debug(f'SQL query: {model_query}')
        return 'False'
    while query_model.canFetchMore():
        query_model.fetchMore()
    create_savepoint('update_many_table')
    to_remove = []
    to_add = []
    for row in range(query_model.rowCount()):
        second_id = query_model.data(query_model.index(row, 0), QtCore.Qt.ItemDataRole.DisplayRole)
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
        logger.get_logger().info(f'No changes to {many_table}')
        release_savepoint('update_many_table')
        return 'No'
    if to_remove:
        for id in to_remove:
            query.prepare(
                f"DELETE FROM {many_table} WHERE {first_table_id_header} {query_where_str} AND {second_table_id_header} = {id}")
            if not query.exec():
                logger.get_logger().critical(f"Error unchecking {second_table} from {first_table}")
                logger.get_logger().debug(f"Error: {query.lastError().text()}")
                logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
                rollback_savepoint('update_many_table')
                return 'False'
        logger.get_logger().info(
            f"Removed {to_remove} associated with item IDs {first_table_ids} from {many_table}")
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
                        logger.get_logger().critical(
                            f"Error adding {second_table} to {first_table}")
                        logger.get_logger().debug(f"Error: {query.lastError().text()}")
                        logger.get_logger().debug(f"SQL query: {query.lastQuery()}")
                        logger.get_logger().debug(f"Bound values: {query.boundValues()}")
                        rollback_savepoint('update_many_table')
                        return 'False'
        logger.get_logger().info(f"Added {to_add} associated with item IDs {first_table_ids} to {many_table}")
    logger.get_logger().info(
        f"Successfully updated {many_table} for {first_table_id_header} {first_table_ids}")
    release_savepoint('update_many_table')
    return 'True'


def get_edit_column(table_id_header, item_table):
    if table_id_header in get_headers(item_table):
        return table_id_header
    else:
        # If not, check if it is part of a header name
        for header in get_headers(item_table):
            if table_id_header in header:
                return header
    logger.get_logger().debug(f'Could not find edit column for {item_table} with header {table_id_header}')
    return None


def bulk_update_parent_row(table, parent_id, spaces_to_move: int, new_row: int | None = None,
                           old_row: int | None = None) -> tuple[bool, list[int]]:
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
        logger.get_logger().critical(f'Error shifting {table} data')
        logger.get_logger().debug(f'Missing parent row constraints')
        return False, []
    if new_row == old_row:
        logger.get_logger().info(f'{table} data already in the correct position at row {old_row}')
        return True, []
    logger.get_logger().info(
        f'Bulk updating {table} data for children of {parent_id} from old row {old_row} to new row {new_row}')
    query1 = QtSql.QSqlQuery()
    query2 = QtSql.QSqlQuery()
    select_query = QtSql.QSqlQuery()
    if parent_id in ['NULL', '', None]:
        parent_id = 'NULL'
        parent_id_sql = 'IS NULL'
    else:
        parent_id_sql = f'= {parent_id}'
    move_size_query = QtSql.QSqlQuery()
    move_size_query.prepare(f'''SELECT MAX({parent_row_header}) AS maximum
                FROM {table} WHERE {parent_id_header} IS :parent_id''')
    move_size_query.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())
    if not move_size_query.exec():
        logger.get_logger().critical(f'Error shifting {table} data')
        logger.get_logger().debug(f"Error: {move_size_query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {move_size_query.lastQuery()}")
        logger.get_logger().debug(f"Bound values: {move_size_query.boundValues()}")
        return False, []
    max_child_row = 0
    if move_size_query.next():
        if move_size_query.value(0):
            max_child_row = move_size_query.value(0)
    if new_row is not None and old_row is None:
        logger.get_logger().info(f'Making space to insert new child at {new_row}')
        k = max_child_row - new_row + spaces_to_move
        query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k} + {spaces_to_move}
        WHERE {parent_id_header} IS :parent_id AND {parent_row_header} >= {new_row};
        ''')
        query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

        query2.prepare(f'''
        UPDATE {table} SET {parent_row_header} = {parent_row_header} - {k}
        WHERE {parent_id_header} IS :parent_id AND {parent_row_header} > {new_row}
        ''')
        query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

        select_query.prepare(
            f'SELECT {id_header} FROM {table} WHERE {parent_id_header} {parent_id_sql} AND {parent_row_header} >= {new_row}')
    elif old_row is not None and new_row is None:
        logger.get_logger().info(f'Closing space from removed child at {old_row}')
        if old_row > max_child_row:
            logger.get_logger().info(f'Space already closed')
        k = max_child_row - old_row
        query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k}
        WHERE {parent_id_header} IS :parent_id AND {parent_row_header} > {old_row};
        ''')
        query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

        query2.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} - ({k} + {spaces_to_move})
        WHERE {parent_id_header} IS :parent_id 
        AND {parent_row_header} > {old_row}
        ''')
        query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

        select_query.prepare(
            f'SELECT {id_header} FROM {table} WHERE {parent_id_header} {parent_id_sql} AND {parent_row_header} > {old_row}')
    elif new_row is not None and old_row is not None:
        if new_row < old_row:
            logger.get_logger().info(f'Moving child up from {old_row} to {new_row}')
            k = max_child_row - new_row + 1
            query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k}
            WHERE {parent_id_header} IS :parent_id 
                AND {parent_row_header} >= {new_row} 
                AND {parent_row_header} <= {old_row};
            ''')
            query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

            query2.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} - {k} + {spaces_to_move}
            WHERE {parent_id_header} IS :parent_id
                AND {parent_row_header} > {max_child_row}
                AND {parent_row_header} < {old_row} + {k};
            ''')
            query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

            select_query.prepare(f'''SELECT {id_header} FROM {table} 
            WHERE {parent_id_header} {parent_id_sql} 
            AND {parent_row_header} >= {new_row} 
            AND {parent_row_header} <= {old_row}''')
        elif new_row > old_row:
            logger.get_logger().info(f'Moving child down from {old_row} to {new_row}')
            k = max_child_row - old_row + 1
            # Move all rows that will be changing to the end
            query1.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} + {k}
            WHERE {parent_id_header} IS :parent_id 
                AND {parent_row_header} >= {old_row}
                AND {parent_row_header} <= {new_row};
            ''')
            query1.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

            # Leave the first row past the end and move the others up to the old row and down, leaving a space at new row
            query2.prepare(f'''UPDATE {table} SET {parent_row_header} = {parent_row_header} - ({k} + {spaces_to_move})
            WHERE {parent_id_header} IS :parent_id
                AND {parent_row_header} > {max_child_row} + {spaces_to_move};
            ''')
            query2.bindValue(':parent_id', parent_id if parent_id != 'NULL' else QtCore.QVariant())

            select_query.prepare(f'''SELECT {id_header} FROM {table} 
            WHERE {parent_id_header} {parent_id_sql} 
                AND {parent_row_header} > {old_row} 
                AND {parent_row_header} <= {new_row}''')
    if not select_query.exec():
        logger.get_logger().critical(f'Error shifting {table} data')
        logger.get_logger().debug(f"Error: {select_query.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {select_query.lastQuery()}")
        logger.get_logger().debug(f"Bound values: {select_query.boundValues()}")
        return False, []
    while select_query.next():
        updated_ids.append(select_query.value(0))
    if not updated_ids:
        logger.get_logger().info(f'No items to shift for {table}')
        return True, []
    # Move items well out of the way to avoid unique ParentID, ParentRow errors
    if not query1.exec():
        logger.get_logger().critical(f'Error shifting {table} data')
        logger.get_logger().debug(f"Error: {query1.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query1.lastQuery()}")
        logger.get_logger().debug(f"Bound values: {query1.boundValues()}")
        return False, []
    # Move items to the new position
    if not query2.exec():
        logger.get_logger().critical(f'Error shifting {table} data')
        logger.get_logger().debug(f"Error: {query2.lastError().text()}")
        logger.get_logger().debug(f"SQL query: {query2.lastQuery()}")
        logger.get_logger().debug(f"Bound values: {query2.boundValues()}")
        return False, []
    from Functions.Check_triggers import update_modified_timestamp
    update_modified_timestamp(table, updated_ids)
    return True, updated_ids


def get_selected_tree_ids(indexes: list[QtCore.QModelIndex]):
    """
    Return the item IDs, parent IDs, and parent rows for the selected items in a tree model. This method iterates through
    the provided indexes, which are expected to be from a tree model, and retrieves the item ID, parent ID, and parent row
    for each selected item. It returns three lists: item IDs, parent IDs, and parent rows.
    :param indexes: List of QModelIndex objects representing the selected items in the tree model
    :return: Tuple containing three lists: item_ids, parent_ids, and parent_rows
    """
    item_parent_dictionary = {}
    for index in indexes:
        item_id = index.siblingAtColumn(1).data(QtCore.Qt.ItemDataRole.DisplayRole)
        parent_id = index.siblingAtColumn(2).data(QtCore.Qt.ItemDataRole.DisplayRole)
        parent_row = index.siblingAtColumn(3).data(QtCore.Qt.ItemDataRole.DisplayRole)
        if item_id not in item_parent_dictionary.keys():
            item_parent_dictionary[item_id] = [parent_id, parent_row]
    return item_parent_dictionary


def find_tree_model(model, indexes: list[QtCore.QModelIndex] | None):
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
    from util.widgets.models.tree_models import TreeModel, CheckableTreeModel
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
                        pointed_index = QtCore.QModelIndex()
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


def map_from_tree_model(input_model, tree_indexes: list[QtCore.QModelIndex]):
    model_chain = []
    model = input_model
    from util.widgets.models.tree_models import TreeModel
    while not isinstance(model, TreeModel):
        model_chain.insert(0, model)
        model = model.sourceModel() if hasattr(model, 'sourceModel') else getattr(model, 'source_model', None)

    model_indexes = tree_indexes
    for model in model_chain:
        parent_indexes = [model.mapFromSource(model_index) for model_index in model_indexes]
        model_indexes = parent_indexes
    return model_indexes


def set_comboBox_text(comboBox: QtWidgets.QComboBox, text: str):
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
        logger.get_logger().debug(f'ComboBox {comboBox.objectName()} text "{text}" not found in items.')


def show_column(comboBox: QtWidgets.QComboBox, column: str | int):
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
            from util.widgets.models.proxy_models import ReadableProxyModel
            if isinstance(model, ReadableProxyModel):
                # If the model is a ReadableProxyModel, get the readable header to compare
                column = get_readable_header(column)
            for col in range(model.columnCount()):
                header = model.headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole)
                if header == column:
                    column_int = col
                    break
        else:
            column_int = column
        comboBox.setCompleter(None)
        comboBox.setModelColumn(column_int)
        if not isinstance(comboBox.view(), QtWidgets.QListView):
            for model_column in range(model.columnCount()):
                if model_column != column_int:
                    try:
                        comboBox.view().hideColumn(model_column)
                    except AttributeError:
                        # If the view does not have a hideColumn method, no need
                        pass
            from util.widgets.models.proxy_models import TreeSortFilterProxyModel
            if isinstance(comboBox.view().model(), TreeSortFilterProxyModel):
                comboBox.view().model().update_visible_columns()
        if isinstance(comboBox.view().model(), QtCore.QSortFilterProxyModel) and not tree_model:
            comboBox.view().model().sort(column_int, QtCore.Qt.SortOrder.AscendingOrder)
        close_loading_dialog('Loading', f'Loading {count} items...')


def add_tree_popup(tree_view: QtWidgets.QTreeView, action: QtGui.QAction | None = None):
    """
    Determine the arguments to pass to a dialog for adding or inserting items in a tree view based on the selected
    indexes and the action.
    :param tree_view: QtWidgets.QTreeView to add or insert items in
    :param action: QtGui.QAction that specifies the action to perform (e.g., insert above, insert below, add child, etc.)
    :return: library dialog arguments to pass to the dialog for adding or inserting items in the tree view
    """
    dlg_args = None
    indexes = tree_view.selectedIndexes()
    model = tree_view.model()
    tree_model, tree_indexes = find_tree_model(model, indexes)
    if not tree_model:
        logger.get_logger().info(f'No tree model found in {tree_view.objectName()}')
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
            dlg_args = {'parent_id': parent_id, 'parent_row': row}
        elif action_text == 'Insert below':
            row = item_parent_dictionary[first_item_id][1] + 1
            parent_id = item_parent_dictionary[first_item_id][0]
            dlg_args = {'parent_id': parent_id, 'parent_row': row}
        elif action_text == 'Add child':
            parent_id = first_item_id
            dlg_args = {'parent_id': parent_id}
        elif action_text == 'Add parent':
            parent_ids = [item_parent_dictionary[item_id][0] for item_id in item_ids]
            parent_rows = [item_parent_dictionary[item_id][1] for item_id in item_ids]
            dlg_args = {'add_item': 'parent', 'item_ids': item_ids, 'old_parent_ids': parent_ids,
                        'old_parent_rows': parent_rows}
        elif action_text == 'Add to end' or action_text == 'Add':
            dlg_args = {'add_item': 'child'}
    return dlg_args


def turn_on_foreign_keys(database: QSqlDatabase = QSqlDatabase()) -> bool:
    """
    Turn on foreign keys for a given database connection, if no database is provided the default database will be used.
    :param QSqlDatabase database: QSqlDatabase instance to enable foreign keys
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QSqlQuery(database)
    logger.get_logger().debug(f'Turning on foreign keys for database: {database.connectionName()}')
    if not query.exec('PRAGMA foreign_keys=ON'):
        logger.get_logger().critical(f'Could not turn on foreign keys')
        logger.get_logger().debug(f'Error: {query.lastError().text()}')
        logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec('PRAGMA foreign_keys'):
        logger.get_logger().critical(f'Could not check foreign keys')
        logger.get_logger().debug(f'Error: {query.lastError().text()}')
        logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if query.next():
        if query.value(0) == 1:
            logger.get_logger().info('Foreign keys are on')
            return True
        else:
            logger.get_logger().critical('Failed to re-enable foreign keys')
            logger.get_logger().info(f'Foreign keys status: {query.value(0)}')
            return False

    return False


def turn_off_foreign_keys(database: QSqlDatabase = QSqlDatabase()) -> bool:
    """
    Turn off foreign keys for a given database connection, if no database is provided the default database will be used.
    :param QSqlDatabase database: QSqlDatabase instance to enable foreign keys
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QSqlQuery(database)
    logger.get_logger().debug(f'Turning off foreign keys for database: {database.connectionName()}')
    if not query.exec('PRAGMA foreign_keys=OFF'):
        logger.get_logger().critical(f'Could not turn off foreign keys')
        logger.get_logger().debug(f'Error: {query.lastError().text()}')
        logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec('PRAGMA foreign_keys'):
        logger.get_logger().critical(f'Could not check foreign keys')
        logger.get_logger().debug(f'Error: {query.lastError().text()}')
        logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if query.next():
        if query.value(0) == 0:
            logger.get_logger().info('Foreign keys are off')
            return True
        else:
            logger.get_logger().critical('Failed to disable foreign keys')
            return False

    return False


def update_database(database=None) -> bool:
    """
    Run this on startup and when settings are changed.
    The database has generated columns that set display values based on units and formats in settings. These need to be
    updated if the settings are changed. This function will drop and recreate the generated columns.
    Uses the default connection established with the database file in GeoCORKMain.py if no database is provided.
    :param database: QSqlDatabase instance to use, if None the default database is used
    :return: True for success, False for failure
    :rtype: bool
    """
    start_time = time.time()
    loading_manager = LoadingDialogManager.get_instance()
    loading_manager.show_loading_dialog('Loading', 'Updating database... \n(GeoCORK may be slower for large databases)')
    logger.get_logger().info("Updating database")
    # Check if the database exists and all tables are present
    if database is None:
        db = QSqlDatabase.database()
    else:
        db = database
    if not db.commit():
        if 'no transaction is active' not in db.lastError().text():
            logger.get_logger().critical(f"Error committing database")
            logger.get_logger().debug(f'Error: {db.lastError().text()}')
            loading_manager.close_loading_dialog('Loading',
                                                 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
    if not db.close():
        if 'no transaction is active' not in db.lastError().text():
            logger.get_logger().critical(f"Error closing database")
            logger.get_logger().debug(f'Error: {db.lastError().text()}')
            loading_manager.close_loading_dialog('Loading',
                                                 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
    if not db.open():
        logger.get_logger().critical(f"Error opening database")
        logger.get_logger().debug(f'Error: {db.lastError().text()}')
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    if not turn_on_foreign_keys():
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    if database is None:
        database = QSqlDatabase.database()
    query = QSqlQuery(db=database)

    '''Backup database before any changes.
    Restore the backup before returning if the update fails'''

    from Functions import Create_indexes
    from util.database.create import Create_database as Create_db
    from util.database import alter_database as Alter_db

    # Update database schema
    if not query.exec('SELECT Version FROM About WHERE AboutID = 1'):
        db_version = None
    else:
        if not query.next():
            logger.get_logger().critical('Error retrieving database version')
            logger.get_logger().debug(f'Error: {query.lastError().text()}')
            logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
            loading_manager.close_loading_dialog('Loading',
                                                 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
        else:
            db_version = query.value(0)
            logger.get_logger().info(f'Database version: {db_version}')
    # if db_version != settings.value('geocork_version'):
    if not turn_off_foreign_keys():
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    schema_success = Create_db.update_schema(db_version, database=db)
    if schema_success == 'False':
        logger.get_logger().debug(f"Error updating schema from {db_version} to {settings.value('geocork_version')}")
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setText(
            f"Error updating schema from {db_version} to {settings.value('geocork_version')}\nWould you like to try to open the database anyway? \n \n This will likely cause issues with your data and is not recommended.")
        dialog.setWindowTitle("Error updating database")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        ret = dialog.exec()
        if ret != QMessageBox.StandardButton.Yes:
            loading_manager.close_loading_dialog('Loading',
                                                 'Updating database... \n(GeoCORK may be slower for large databases)')
            return False
        logger.get_logger().info('Trying to open the database anyway')
    elif schema_success == 'Cancel':
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    elif schema_success != 'True':
        # A backup file was returned to restore
        backup_file = schema_success
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setText(
            f"Error updating schema from v.{db_version} to v.{settings.value('geocork_version')}\nWould you like to restore from the backup file?")
        dialog.setWindowTitle("Error updating database")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        ret = dialog.exec()
        if ret != QMessageBox.StandardButton.Yes:
            loading_manager.close_loading_dialog('Loading',
                                                 'Updating database... \n(GeoCORK may be slower for large databases)')
            for widget in QApplication.allWidgets():
                if widget.objectName() == 'LandingPage':
                    widget.restore_backup(database.databaseName(), backup_file)
                    return False

    if not turn_on_foreign_keys():
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    if not Create_db.create_tables(database):
        logger.get_logger().critical(f"Error creating database tables")
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    if not Create_indexes.create_indexes(db):
        logger.get_logger().critical(f"Error creating database indexes")
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    # Make sure the view column settings do not have any leftover old column names
    from ui.settings import SettingsCore
    if not SettingsCore.update_column_settings():
        logger.get_logger().critical(f"Error updating database settings")
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False

    # Drop and regenerate the generated columns
    if not Alter_db.settings_reset(database):
        logger.get_logger().critical(f"Error resetting settings")
        loading_manager.close_loading_dialog('Loading',
                                             'Updating database... \n(GeoCORK may be slower for large databases)')
        return False
    end_time = time.time()
    loading_manager.close_loading_dialog('Loading',
                                         'Updating database... \n(GeoCORK may be slower for large databases)')
    logger.get_logger().info(f"Database updated in {end_time - start_time} seconds")
    database.commit()

    '''Delete backup made at the beginning of the update if it exists'''

    return True
