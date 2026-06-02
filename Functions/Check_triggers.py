from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC

import logger_setup


def update_modified_timestamp(table: str, record_ids: list):
    """
    Update the ModifiedTimestamp field for the given records.
    :param str table: table to be updated
    :param list record_ids: list of record ids to be updated
    :return:
    """
    if not record_ids or not table:
        logger_setup.get_logger().error('No record ids or table given for updating modified timestamp')
        return
    # Get the header for the first column, the ID column
    from Functions.Widget_classes import get_headers
    headers = get_headers(table)
    modified_header = None
    for header in headers:
        if 'Modified' in header:
            modified_header = header
            break
    if not modified_header:
        return f'Unable to find modified header for {table}'
    record_id_header = headers[0]
    query = QtS.QSqlQuery()
    logger_setup.get_logger().info('Updating modified timestamp')
    if len(record_ids) > 1:
        where_sql = f'{record_id_header} IN {tuple(record_ids)}'
    elif len(record_ids) == 1:
        where_sql = f'{record_id_header} = {record_ids[0]}'
    if not query.exec(f'UPDATE {table} SET {modified_header} = CURRENT_TIMESTAMP WHERE {where_sql}'):
        logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        return f'Error updating modified timestamp for {table}'
    return ''

def validate_insert(table: str, columns: list, values: list, gps_format_id: int | None):
    """
    Check that the values being inserted into the database are valid
    The corresponding columns and values should be in the same index in their respective lists
    Tables that need to be validated are in SQLUtils.trigger_tables
    :param str table: table to be inserted into
    :param list columns: list of names of columns to be inserted into
    :param list values: list of values to be inserted into the columns
    :param int gps_format_id: the id of the GPS format to be used for the GPS location, if applicable
    :return:
    """
    if len(columns) != len(values):
        return "Number of columns to set does not match number of values given", None
    pairs = []
    for index in range(len(columns)):
        pairs.append([columns[index], values[index]])

    if table == 'Columns':
        error, header = check_insert_pairs(pairs, 'ColumnTotalHeightDepth', 'ColumnTotalHeightDepthUnitID')
        if error:
            if error != 'ColumnTotalHeightDepthUnitID missing ColumnTotalHeightDepth':
                return "Column total height/depth value missing units", 'ColumnTotalHeightDepthUnitID'
    if table == 'GPSLocations':
        error, header = check_gps_format_insert(pairs, gps_format_id)
        if error:
            return error, header
    if table == 'SampleAges':
        error, header = check_insert_pairs(pairs, 'DirectAgeError', 'DirectAgeErrorFormatID')
        if error:
            if error != 'DirectAgeErrorFormatID missing DirectAgeError':
                return "Direct age error given without error format", 'DirectAgeErrorFormatID'
        error, header = check_insert_pairs(pairs, 'DirectAgeError', 'DirectAge')
        if error:
            if error != 'DirectAge missing DirectAgeError':
                return "Direct age error given without direct age", 'DirectAge'
        # age unit errors
        unit_error, header = check_insert_pairs(pairs, 'DirectAge', 'DirectAgeUnitID')
        if unit_error == 'DirectAgeUnitID missing DirectAge':
            unit_error = None
        oldest_unit_error, header = check_insert_pairs(pairs, 'OldestDirectAge', 'DirectAgeUnitID')
        if oldest_unit_error == 'DirectAgeUnitID missing OldestDirectAge':
            oldest_unit_error = None
        youngest_unit_error, header = check_insert_pairs(pairs, 'YoungestDirectAge', 'DirectAgeUnitID')
        if youngest_unit_error == 'DirectAgeUnitID missing YoungestDirectAge':
            youngest_unit_error = None
        direct_ages_error, header = check_insert_age_range(pairs, 'OldestDirectAge', 'YoungestDirectAge')
        if direct_ages_error:
            return direct_ages_error, header
        if unit_error or oldest_unit_error or youngest_unit_error:
            return "Direct age missing units", 'DirectAgeUnitID'
        relative_error, header = check_insert_age_range(pairs, 'OldestAgeID', 'YoungestAgeID')
        if relative_error:
            return relative_error, header
    if table == 'Samples':
        error, header = check_insert_pairs(pairs, 'HeightDepth', 'HeightDepthUnitID')
        if error:
            if error != 'HeightDepthUnitID missing HeightDepth':
                return "Height/depth value missing units", 'HeightDepthUnitID'
        error, header = check_insert_pairs(pairs, 'HeightDepthError', 'HeightDepth')
        if error:
            if error != 'HeightDepth missing HeightDepthError':
                return "Height/depth error given without value", 'HeightDepth'
        error, header = check_insert_pairs(pairs, 'HeightDepth', 'SampleColumnID')
        if error:
            if error != 'SampleColumnID missing HeightDepth':
                return "Height/depth value missing column", 'SampleColumnID'
    if table == 'UPbAnalyses':
        ratio_error_list = []
        age_error_list = []
        for column in columns:
            if column.endswith('AgeError'):
                age_error_list.append(f'"{column}"')
            elif column.endswith('Error'):
                ratio_error_list.append(f'"{column}"')
        ratio_list = [column.replace('Error', '') for column in ratio_error_list]
        age_list = [column.replace('Error', '') for column in age_error_list]
        for index in range(len(ratio_error_list)):
            error, header = check_insert_pairs(pairs, ratio_error_list[index], ratio_list[index])
            if error:
                if error != f'{ratio_list[index]} missing {ratio_error_list[index]}':
                    return f'{ratio_error_list[index]} missing {ratio_list[index]}', ratio_error_list[index]
            error, header = check_insert_pairs(pairs, ratio_error_list[index], 'RatioErrorFormatID')
            if error:
                if error != 'RatioErrorFormatID missing RatioError':
                    return "Ratio error given without error format", 'RatioErrorFormatID'
        for index in range(len(age_error_list)):
            error, header = check_insert_pairs(pairs, age_error_list[index], age_list[index])
            if error:
                if error != f'{age_list[index]} missing {age_error_list[index]}':
                    return f'{age_error_list[index]} missing {age_list[index]}', age_error_list[index]
            error, header = check_insert_pairs(pairs, age_error_list[index], 'AgeErrorFormatID')
            if error:
                if error != 'AgeErrorFormatID missing AgeError':
                    return "Age error given without error format", 'AgeErrorFormatID'
        error, header = check_insert_concordance(pairs, values[columns.index('ConcordanceFormatID')] if 'ConcordanceFormatID' in columns else None)
        if error:
            if error != 'ConcordanceFormatID missing Concordance':
                return "Concordance/discordance given without type", 'ConcordanceFormatID'
        error, header = check_insert_pairs(pairs, 'SpotSize', 'SpotSizeUnitID')
        if error:
            if error != 'SpotSizeUnitID missing SpotSize':
                return "Spot size given without units", 'SpotSizeUnitID'
    return None, None

def validate_update(table: str, columns: list, values: list, where: str):
    """
    Check that the values being updated in the database are valid.
    The corresponding columns and values should be in the same index in their respective lists.
    Tables that need to be validated are in SQLUtils.trigger_tables.
    :param table: the table to be updated
    :param columns: the columns to be updated
    :param values: the string values to be entered into the database. Null values should be 'NULL'
    :param where: the text that would come after WHERE in a sql statement
    :return:
    """
    if len(columns) != len(values):
        return "Number of columns to set does not match number of values given", None
    pairs = []
    for index in range(len(columns)):
        if isinstance(values[index], QtC.QVariant) and values[index].isNull():
            pairs.append(([columns[index], 'NULL']))
        elif values[index] in ['', None]:
            pairs.append(([columns[index], '']))
        else:
            pairs.append([columns[index], values[index]])
    table_model = QtS.QSqlQueryModel()
    table_model.setQuery(f'SELECT * FROM {table} WHERE {where}')
    if table_model.lastError().text():
        error = f'Error validating updated values for {table}'
        logger_setup.get_logger().debug(error)
        logger_setup.get_logger().debug(f'Error getting current values for {table}')
        logger_setup.get_logger().debug(f'Error: {table_model.lastError().text()}')
        logger_setup.get_logger().debug(f'Query: SELECT * FROM {table} WHERE {where}')
        return error, None
    all_records = []
    for col in range(1, table_model.columnCount()):
        column_name = table_model.record().fieldName(col)
        new_value = ''
        for index in range(len(columns)):
            if columns[index] == column_name:
                new_value = values[index]
                if new_value in ['NULL', 'Null'] or (isinstance(new_value, QtC.QVariant) and new_value.isNull()):
                    new_value = 'NULL'
                elif new_value in ['', None]:
                    new_value = ''
                break
        old_values = []
        for row in range(table_model.rowCount()):
            old_value = table_model.data(table_model.index(row, col, QtC.QModelIndex()))
            if old_value in ['', None, 'NULL', 'Null'] or (isinstance(old_value, QtC.QVariant) and old_value.isNull()):
                old_value = 'NULL'
            old_values.append(old_value)
        all_records.append([column_name, new_value, old_values])
    if table == 'Columns':
        error, header = check_update_units(all_records, 'ColumnTotalHeightDepth', 'ColumnTotalHeightDepthUnitID')
        if error:
            return f'Column total height/depth {error}', 'ColumnTotalHeightDepthUnitID'
    if table == 'GPSLocations':
        error, header = check_gps_format_update(all_records, values[columns.index('GPSFormatID')])
        if error:
            return error, header
    if table == 'SampleAges':
        error, header = check_update_units(all_records, 'DirectAgeError', 'DirectAgeErrorFormatID')
        if error:
            if error != 'DirectAgeErrorFormatID missing DirectAgeError':
                return "Direct age error given without error type", 'DirectAgeErrorFormatID'
        error, header = check_update_pairs(all_records, 'DirectAgeError', 'DirectAge')
        if error:
            if error != 'DirectAge missing DirectAgeError':
                return "Direct age error given without direct age"
        unit_error, header = check_update_pairs(all_records, 'DirectAge', 'DirectAgeUnitID')
        if unit_error == 'DirectAgeUnitID missing DirectAge':
            unit_error = None
        oldest_unit_error, header = check_update_pairs(all_records, 'OldestDirectAge', 'DirectAgeUnitID')
        if oldest_unit_error == 'DirectAgeUnitID missing OldestDirectAge':
            oldest_unit_error = None
        youngest_unit_error, header = check_update_pairs(all_records, 'YoungestDirectAge', 'DirectAgeUnitID')
        if youngest_unit_error == 'DirectAgeUnitID missing YoungestDirectAge':
            youngest_unit_error = None
        direct_ages_error, header = check_update_age_range(all_records, 'OldestDirectAge', 'YoungestDirectAge', 'DirectAge')
        if direct_ages_error:
            return direct_ages_error, header
        if unit_error or oldest_unit_error or youngest_unit_error:
            return "Direct age missing units", 'DirectAgeUnitID'
        relative_error, header = check_update_age_range(all_records, 'OldestAgeID', 'YoungestAgeID', 'DirectAge')
        if relative_error:
            return relative_error, header
    if table == 'Samples':
        error, header = check_update_pairs(all_records, 'HeightDepth', 'HeightDepthUnitID')
        if error:
            if error != 'HeightDepthUnitID missing HeightDepth':
                return "Height/depth value missing units", header
        error, header = check_update_pairs(all_records, 'HeightDepthError', 'HeightDepth')
        if error:
            if error != 'HeightDepth missing HeightDepthError':
                return "Height/depth error given without value", header
        error, header = check_update_pairs(all_records, 'HeightDepth', 'SampleColumnID')
        if error:
            if error != 'SampleColumnID missing HeightDepth':
                return "Height/depth value missing column", header
    if table == 'UPbAnalyses':
        ratio_error_list = []
        age_error_list = []
        for column in all_records:
            if column[0].endswith('AgeError'):
                age_error_list.append(column[0])
            elif column[0].endswith('Error'):
                ratio_error_list.append(column[0])
        ratio_list = [column.replace('Error', '') for column in ratio_error_list]
        age_list = [column.replace('Error', '') for column in age_error_list]
        for index in range(len(ratio_error_list)):
            error, header = check_update_pairs(all_records, ratio_error_list[index], ratio_list[index])
            if error:
                if error != f'{ratio_list[index].replace(f'"', '')} missing {ratio_error_list[index].replace(f'"', '')}':
                    return f'{ratio_error_list[index].replace(f'"', '')} missing {ratio_list[index].replace(f'"', '')}', header
            error, header = check_update_pairs(all_records, ratio_error_list[index], 'RatioErrorFormatID')
            if error:
                if error != 'RatioErrorFormatID missing RatioError':
                    return "Ratio error given without error format", header
        for index in range(len(age_error_list)):
            error, header = check_update_pairs(all_records, age_error_list[index], age_list[index])
            if error:
                if error != f'{age_list[index].replace(f'"', '')} missing {age_error_list[index].replace(f'"', '')}':
                    return f'{age_error_list[index].replace(f'"', '')} missing {age_list[index].replace(f'"', '')}', header
            error, header = check_update_pairs(all_records, age_list[index], 'AgeUnitID')
            if error:
                if error != f'AgeUnitID missing {age_list[index].replace(f'"', '')}':
                    return f'{age_list[index].replace(f'"', '')} missing units', header
            error, header = check_update_pairs(all_records, age_error_list[index], 'AgeErrorFormatID')
            if error:
                if error != 'AgeErrorFormatID missing AgeError':
                    return "Age error given without error format", header
        error, header = check_update_concordance(all_records)
        if error:
            return error, header
        error, header = check_update_pairs(all_records, 'SpotSize', 'SpotSizeUnitID')
        if error:
            if error != 'SpotSizeUnitID missing SpotSize':
                return "Spot size given without units", header
    return None, None

def check_update_units(all_records: list, value_col: str, unit_id_col: str):
    """
    Check that the value and unit id are both being set, both not set, or the value is not being set without a unit id
    :param list all_records: list of lists [column_name, new_value, old_values] for each column in the table
    :param str value_col: the name of the column that holds the value
    :param str unit_id_col: the name of the column that holds the unit id
    :return:
    """
    new_value = ''
    new_unit_id = ''
    old_unit_ids = []
    for record in all_records:
        if record[0] == value_col:
            new_value = record[1]
            old_values = record[2]
        if record[0] == unit_id_col:
            new_unit_id = record[1]
            old_unit_ids = record[2]

    if new_value != '' and new_unit_id != '':
        # Both the value and unit id are changing
        if new_value != 'NULL' and new_unit_id == 'NULL':
            return f"missing unit", unit_id_col
    elif new_value != '':
        # Only the value is being set, so compare with the old unit id
        if new_value != 'NULL' and 'NULL' in old_unit_ids:
            return f"missing unit", unit_id_col
    # A unit id missing a value is not problematic
    return None, None

def check_insert_pairs(pairs: list, column1: str, column2: str):
    """
    Checks a pair of columns that should have data in both columns or both be NULL.
    :param list pairs: list of values to validate
    :param str column1: column value 1 to check
    :param str column2: column value 2 to check
    """
    new_column1 = None
    new_column2 = None
    for pair in pairs:
        if '"' in column1 and '"' not in pair[0]:
            pair[0] = f'"{pair[0]}"'
            pair[1] = f'"{pair[1]}"'
        if pair[0] == column1:
            new_column1 = pair[1]
        if pair[0] == column2:
            new_column2 = pair[1]
        if new_column1 is not None and new_column2 is not None:
            break
    if new_column1 != 'NULL' and new_column2 == 'NULL':
        return f'{column1} missing {column2}', column2
    if new_column1 == 'NULL' and new_column2 != 'NULL':
        return f'{column2} missing {column1}', column1
    return None, None

def check_update_pairs(all_records: list, column1, column2):
    column1 = column1.replace(f'"', '')
    column2 = column2.replace(f'"', '')
    new_column1 = None
    new_column2 = None
    old_column1s = []
    old_column2s = []
    for record in all_records:
        if record[0] == column1:
            new_column1 = str(record[1])
            old_column1s = record[2]
        if record[0] == column2:
            new_column2 = str(record[1])
            old_column2s = record[2]
        if new_column1 is not None and new_column2 is not None:
            break
    if new_column1 != '' and new_column2 != '':
        # Both the columns are changing
        if new_column1 != 'NULL' and new_column2 == 'NULL':
            return f'{column1} missing {column2}', column2
        if new_column1 == 'NULL' and new_column2 != 'NULL':
            return f'{column2} missing {column1}', column1
    elif new_column1 != '':
        # Only column1 is being set, so compare with the old column2
        if new_column1 != 'NULL' and 'NULL' in old_column2s:
            return f'{column1} missing {column2}', column2
        if new_column1 == 'NULL' and 'NULL' not in old_column2s:
            return f'{column2} missing {column1}', column1
    elif new_column2 != '':
        # Only column2 is being set, so compare with the old column1
        if new_column2 != 'NULL' and 'NULL' in old_column1s:
            return f'{column2} missing {column1}', column1
        if new_column2 == 'NULL' and 'NULL' not in old_column1s:
            return f'{column1} missing {column2}', column2
    return None, None

def check_insert_age_range(pairs: list, old_column: str, young_column: str):
    from Functions.Widget_classes import SQLiteTableModel, get_headers
    if not pairs or not old_column or not young_column:
        return 'Incomplete data given for age range'
    age_model = None
    if 'ID' in old_column and 'ID' in young_column:
        age_model = SQLiteTableModel('SELECT * FROM Ages')
        if age_model.last_error:
            return f'Unable to access Ages table', None
    for pair in pairs:
        if pair[0] == old_column:
            new_old = pair[1]
        if pair[0] == young_column:
            new_young = pair[1]
    if age_model:
        if new_old != 'NULL' and new_young != 'NULL':
            age_model.setQuery(f'SELECT * FROM Ages WHERE {get_headers('Ages')[0]} = {new_old}')
            while age_model.canFetchMore():
                age_model.fetchMore()
            if age_model.rowCount() == 0:
                return f'{old_column} does not exist', old_column
            oldest_old = age_model.index(0, 4).data(QtC.Qt.ItemDataRole.DisplayRole)
            youngest_old = age_model.index(0, 5).data(QtC.Qt.ItemDataRole.DisplayRole)
            age_model.setQuery(f'SELECT * FROM Ages WHERE {get_headers('Ages')[0]} = {new_young}')
            while age_model.canFetchMore():
                age_model.fetchMore()
            if age_model.rowCount() == 0:
                return f'{young_column} does not exist', young_column
            oldest_young = age_model.index(0, 4).data(QtC.Qt.ItemDataRole.DisplayRole)
            youngest_young = age_model.index(0, 5).data(QtC.Qt.ItemDataRole.DisplayRole)
            if oldest_old < oldest_young and youngest_old < youngest_young:
                return f'Oldest relative age is younger than youngest relative age', old_column
    else:
        if new_old != 'NULL' and new_young != 'NULL':
            if new_old < new_young:
                return f'Oldest direct age is younger than youngest direct age', old_column
    return None, None

def check_update_age_range(all_records: list, old_column: str, young_column: str, direct_column: str):
    from Functions.Widget_classes import SQLiteTableModel, get_headers
    if not all_records or not old_column or not young_column:
        return 'Incomplete data given for age range'
    age_model = None
    if 'ID' in old_column and 'ID' in young_column:
        age_model = SQLiteTableModel('SELECT * FROM Ages')
        if age_model.last_error:
            return f'Unable to access Ages table', None
    for record in all_records:
        if record[0] == old_column:
            new_old = record[1]
            old_olds = record[2]
        if record[0] == young_column:
            new_young = record[1]
            old_youngs = record[2]
        if record[0] == direct_column:
            new_direct = record[1]
            old_directs = record[2]
    if age_model:
        if new_old != 'NULL':
            age_model.setQuery(f'SELECT * FROM Ages WHERE {get_headers('Ages')[0]} = {new_old}')
            while age_model.canFetchMore():
                age_model.fetchMore()
            if age_model.rowCount() == 0:
                return f'{old_column} does not exist', old_column
            new_oldest_old = float(age_model.index(0, 4).data(QtC.Qt.ItemDataRole.DisplayRole))
            new_youngest_old = float(age_model.index(0, 5).data(QtC.Qt.ItemDataRole.DisplayRole))
        if new_young != 'NULL':
            age_model.setQuery(f'SELECT * FROM Ages WHERE {get_headers('Ages')[0]} = {new_young}')
            while age_model.canFetchMore():
                age_model.fetchMore()
            if age_model.rowCount() == 0:
                return f'{young_column} does not exist', young_column
            new_oldest_young = float(age_model.index(0, 4).data(QtC.Qt.ItemDataRole.DisplayRole))
            new_youngest_young = float(age_model.index(0, 5).data(QtC.Qt.ItemDataRole.DisplayRole))
        if new_old != 'NULL' and new_young != 'NULL':
            if new_oldest_old < new_oldest_young and new_youngest_old < new_youngest_young:
                return f'Oldest relative age is younger than youngest relative age', old_column
        elif new_old != 'NULL':
            for old_young in old_youngs:
                if old_young != 'NULL':
                    age_model.setQuery(f'SELECT * FROM Ages WHERE {get_headers('Ages')[0]} = {old_young}')
                    while age_model.canFetchMore():
                        age_model.fetchMore()
                    if age_model.rowCount() == 0:
                        return f'{young_column} does not exist', young_column
                    oldest_young = age_model.index(0, 4).data(QtC.Qt.ItemDataRole.DisplayRole)
                    youngest_young = age_model.index(0, 5).data(QtC.Qt.ItemDataRole.DisplayRole)
                    if new_oldest_old < oldest_young and new_youngest_old < youngest_young:
                        return f'Oldest relative age is younger than youngest relative age', old_column
        elif new_young != 'NULL':
            for old_old in old_olds:
                if old_old != 'NULL':
                    age_model.setQuery(f'SELECT * FROM Ages WHERE {get_headers('Ages')[0]} = {old_old}')
                    while age_model.canFetchMore():
                        age_model.fetchMore()
                    if age_model.rowCount() == 0:
                        return f'{old_column} does not exist', old_column
                    oldest_old = age_model.index(0, 4).data(QtC.Qt.ItemDataRole.DisplayRole)
                    youngest_old = age_model.index(0, 5).data(QtC.Qt.ItemDataRole.DisplayRole)
                    if oldest_old < new_oldest_young and youngest_old < new_youngest_young:
                        return f'Oldest relative age is younger than youngest relative age', old_column
        if new_old != 'NULL' and new_direct != 'NULL':
            if new_direct > new_oldest_old:
                return f'Direct age not in relative age range', direct_column
        if new_young != 'NULL' and new_direct != 'NULL':
            if new_direct < new_youngest_young:
                return f'Direct age not in relative age range', direct_column
    else:
        if new_old != 'NULL' and new_young != 'NULL':
            if new_old < new_young:
                return f'Oldest direct age is younger than youngest direct age', old_column
        elif new_old != 'NULL':
            for old_young in old_youngs:
                if old_young != 'NULL':
                    if new_old < old_young:
                        return f'Oldest direct age is younger than youngest direct age', old_column
        elif new_young != 'NULL':
            for old_old in old_olds:
                if old_old != 'NULL':
                    if old_old < new_young:
                        return f'Oldest direct age is younger than youngest direct age', old_column
        if new_old != 'NULL' and new_direct != 'NULL':
            if new_direct > new_old:
                return f'Direct age not in direct age range', old_column
        if new_young != 'NULL' and new_direct != 'NULL':
            if new_direct < new_young:
                return f'Direct age not in direct age range', old_column
    return None, None

def check_gps_format_insert(pairs: list, format_id: int):
    if not pairs or not format_id:
        return 'Incomplete data given for GPS location'
    gps_format_model = QtS.QSqlTableModel()
    gps_format_model.setTable('GPSFormats')
    gps_format_model.select()
    while gps_format_model.canFetchMore():
        gps_format_model.fetchMore()
    from Functions.Widget_classes import get_name_from_id
    gps_format_abbreviation = get_name_from_id('GPSFormats', format_id)
    for pair in pairs:
        if pair[0] == 'GPSLatDeg':
            new_latdeg = f'{pair[1]}'
            if not try_float(new_latdeg) and new_latdeg != 'NULL' and new_latdeg != '':
                return 'Latitude degrees must be a number', 'GPSLatDeg'
        elif pair[0] == 'GPSLatMin':
            new_latmin = f'{pair[1]}'
            if not try_float(new_latmin) and new_latmin != 'NULL' and new_latmin != '':
                return 'Latitude minutes must be a number', 'GPSLatMin'
        elif pair[0] == 'GPSLatSec':
            new_latsec = f'{pair[1]}'
            if not try_float(new_latsec) and new_latsec != 'NULL' and new_latsec != '':
                return 'Latitude seconds must be a number', 'GPSLatSec'
        elif pair[0] == 'GPSLatDirectionID':
            new_latdir = f'{pair[1]}'
        elif pair[0] == 'GPSLonDeg':
            new_londeg = f'{pair[1]}'
            if not try_float(new_londeg) and new_londeg != 'NULL' and new_londeg != '':
                return 'Longitude degrees must be a number', 'GPSLonDeg'
        elif pair[0] == 'GPSLonMin':
            new_lonmin = f'{pair[1]}'
            if not try_float(new_lonmin) and new_lonmin != 'NULL' and new_lonmin != '':
                return 'Longitude minutes must be a number', 'GPSLonMin'
        elif pair[0] == 'GPSLonSec':
            new_lonsec = f'{pair[1]}'
            if not try_float(new_lonsec) and new_lonsec != 'NULL' and new_lonsec != '':
                return 'Longitude seconds must be a number', 'GPSLonSec'
        elif pair[0] == 'GPSLonDirectionID':
            new_londir = f'{pair[1]}'
        elif pair[0] == 'GPSUTMZone':
            new_utmzone = f'{pair[1]}'
            if new_utmzone != 'NULL' and new_utmzone != '':
                zone_int_str = ''
                # Go through each character and add it to the zone_int_str if it is a digit, stop when we reach a non-digit character after we have started adding digits
                for char in new_utmzone:
                    if char.isdigit():
                        zone_int_str += char
                    elif len(zone_int_str) > 0:
                        break
                if not try_float(zone_int_str) or zone_int_str == '':
                    return 'UTM zone must include a number', 'GPSUTMZone'
        elif pair[0] == 'GPSUTMN':
            new_utmn = f'{pair[1]}'
            if not try_float(new_utmn) and new_utmn != 'NULL' and new_utmn != '':
                return 'UTM northing must be a number', 'GPSUTMN'
        elif pair[0] == 'GPSUTME':
            new_utme = f'{pair[1]}'
            if not try_float(new_utme) and new_utme != 'NULL' and new_utme != '':
                return 'UTM easting must be a number', 'GPSUTME'
        elif pair[0] == 'GPSElev':
            new_elev = f'{pair[1]}'
            if not try_float(new_elev) and new_elev != 'NULL' and new_elev != '':
                return 'Elevation must be a number', 'GPSElev'
        elif pair[0] == 'GPSElevError':
            new_elev_error = f'{pair[1]}'
            if not try_float(new_elev_error) and new_elev_error != 'NULL' and new_elev_error != '':
                return 'Elevation error must be a number', 'GPSElevError'
        elif pair[0] == 'GPSElevUnitID':
            new_elev_unit = f'{pair[1]}'

    if 'D' in gps_format_abbreviation:
        # DD, DDM, or DMS
        if new_utmn != 'NULL' or new_utme != 'NULL' or new_utmzone != 'NULL':
            return 'UTM coordinates given for degrees format. Coordinates should be entered in the format originally provided.', 'GPSUTMZone'
        if new_latdeg != 'NULL' and new_londeg == 'NULL':
            return 'Missing degrees lon in degree format', 'GPSLonDeg'
        if new_latdeg == 'NULL' and new_londeg != 'NULL':
            return 'Missing degrees lat in degree format', 'GPSLatDeg'
        if new_latdeg != 'NULL' and (float(new_latdeg) < -90 or float(new_latdeg) > 90):
            return 'Latitude must be between -90 and 90', 'GPSLatDeg'
        if new_londeg != 'NULL' and (float(new_londeg) < -180 or float(new_londeg) > 180):
            return 'Longitude must be between -180 and 180', 'GPSLonDeg'
        if 'DD ' in gps_format_abbreviation:
            # DD
            if new_latmin != 'NULL' or new_latsec != 'NULL':
                return 'Minutes and/or seconds given in DD format', 'GPSLatMin'
            if new_lonmin != 'NULL' or new_lonsec != 'NULL':
                return 'Minutes and/or seconds given in DD format', 'GPSLonMin'
        elif 'DM' in gps_format_abbreviation:
            # DDM or DMS
            if new_latmin != 'NULL' and new_lonmin == 'NULL':
                return 'Missing minutes lon in degree format', 'GPSLonMin'
            if new_latmin == 'NULL' and new_lonmin != 'NULL':
                return 'Missing minutes lat in degree format', 'GPSLatMin'
            if new_latdeg == 'NULL' and new_latmin != 'NULL':
                return 'Minutes given without degrees in degree format', 'GPSLatDeg'
            if new_londeg == 'NULL' and new_lonmin != 'NULL':
                return 'Minutes given without degrees in degree format', 'GPSLonDeg'
            if new_latmin != 'NULL' and (float(new_latmin) < 0 or float(new_latmin) >= 60):
                return 'Minutes must be between 0 and 59', 'GPSLatMin'
            if new_lonmin != 'NULL' and (float(new_lonmin) < 0 or float(new_lonmin) >= 60):
                return 'Minutes must be between 0 and 59', 'GPSLonMin'
            if 'DDM ' in gps_format_abbreviation:
                if new_latsec != 'NULL':
                    return 'Seconds given in DDM format', 'GPSLatSec'
                if new_lonsec != 'NULL':
                    return 'Seconds given in DDM format', 'GPSLonSec'
            elif 'DMS' in gps_format_abbreviation:
                if new_latsec != 'NULL' and new_lonsec == 'NULL':
                    return 'Missing seconds lon in DMS format', 'GPSLonSec'
                if new_latsec == 'NULL' and new_lonsec != 'NULL':
                    return 'Missing seconds lat in DMS format', 'GPSLatSec'
                if new_latmin == 'NULL' and new_latsec != 'NULL':
                    return 'Seconds given without minutes in DMS format', 'GPSLatMin'
                if new_lonmin == 'NULL' and new_lonsec != 'NULL':
                    return 'Seconds given without minutes in DMS format', 'GPSLonMin'
                if new_latsec != 'NULL' and (float(new_latsec) < 0 or float(new_latsec) >= 60):
                    return 'Seconds must be between 0 and 59', 'GPSLatSec'
                if new_lonsec != 'NULL' and (float(new_lonsec) < 0 or float(new_lonsec) >= 60):
                    return 'Seconds must be between 0 and 59', 'GPSLonSec'
        if '+/-' in gps_format_abbreviation:
            if new_latdir != 'NULL':
                return 'Use signs instead of directions in +/- format', 'GPSLatDirectionID'
            if new_londir != 'NULL':
                return 'Use signs instead of directions in +/- format', 'GPSLonDirectionID'
        elif 'NSEW' in gps_format_abbreviation:
            if new_latdir == 'NULL' and new_londir != 'NULL':
                return 'Only one direction given in NSEW format', 'GPSLatDirectionID'
            if new_latdir != 'NULL' and new_londir == 'NULL':
                return 'Only one direction given in NSEW format', 'GPSLonDirectionID'
            if new_latdir == 'NULL' and new_latdeg != 'NULL':
                return 'Missing direction in NSEW format', 'GPSLatDirectionID'
            if new_londir == 'NULL' and new_londeg != 'NULL':
                return 'Missing direction in NSEW format', 'GPSLonDirectionID'
            if '-' in new_latdeg:
                return 'Use only positive coordinates in NSEW format', 'GPSLatDeg'
            if '-' in new_londeg:
                return 'Use only positive coordinates in NSEW format', 'GPSLonDeg'
            if new_latdir in ('3','4'):
                return 'Latitude direction must be N or S', 'GPSLatDirectionID'
            if new_londir in ('1','2'):
                return 'Longitude direction must be E or W', 'GPSLonDirectionID'
    if 'UTM' in gps_format_abbreviation:
        if new_latdeg != 'NULL' or new_latmin != 'NULL' or new_latsec != 'NULL' or new_latdir != 'NULL':
            return 'Degree coordinates given for UTM format. Coordinates should be entered in the format originally provided.', 'GPSLatDeg'
        if new_londeg != 'NULL' or new_lonmin != 'NULL' or new_lonsec != 'NULL' or new_londir != 'NULL':
            return 'Degree coordinates given for UTM format. Coordinates should be entered in the format originally provided.', 'GPSLonDeg'
        if new_utmn != 'NULL' and new_utme == 'NULL':
            return 'Missing easting in UTM format', 'GPSUTME'
        if new_utme != 'NULL' and new_utmn == 'NULL':
            return 'Missing northing in UTM format', 'GPSUTMN'
        if (new_utmn != 'NULL' and new_utmzone == 'NULL') or (new_utme != 'NULL' and new_utmzone == 'NULL'):
            return 'Missing UTM zone in UTM format', 'GPSUTMZone'
        if new_utmzone != 'NULL' and new_utme == 'NULL':
            return 'Missing easting in UTM format', 'GPSUTME'
        if new_utmzone != 'NULL' and (new_utme == 'NULL' or new_utmn == 'NULL'):
            return 'UTM zone given without coordinates in UTM format', 'GPSUTMZone'
    if new_elev != 'NULL' and new_elev_unit == 'NULL':
        return 'Elevation missing units', 'GPSElevUnitID'
    if new_elev_error != 'NULL' and new_elev == 'NULL':
        return 'Elevation error given without elevation', 'GPSElev'
    return None, None

def check_gps_format_update(all_records: list, new_format_id: int):
    gps_format_model = QtS.QSqlTableModel()
    gps_format_model.setTable('GPSFormats')
    gps_format_model.select()
    while gps_format_model.canFetchMore():
        gps_format_model.fetchMore()
    from Functions.Widget_classes import get_name_from_id
    gps_format_abbreviation = get_name_from_id('GPSFormats', new_format_id)
    for record in all_records:
        if record[0] == 'GPSLatDeg':
            new_latdeg = str(record[1])
            old_latdegs = str(record[2])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Latitude degrees must be a number', 'GPSLatDeg'
        elif record[0] == 'GPSLatMin':
            new_latmin = str(record[1])
            old_latmins = str(record[2])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Latitude minutes must be a number', 'GPSLatMin'
        elif record[0] == 'GPSLatSec':
            new_latsec = str(record[1])
            old_latsecs = str(record[2])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Latitude seconds must be a number', 'GPSLatSec'
        elif record[0] == 'GPSLatDirectionID':
            new_latdir = str(record[1])
            old_latdirs = str(record[2])
        elif record[0] == 'GPSLonDeg':
            new_londeg = str(record[1])
            old_londegs = str(record[2])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Longitude degrees must be a number', 'GPSLonDeg'
        elif record[0] == 'GPSLonMin':
            new_lonmin = str(record[1])
            old_lonmins = str(record[2])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Longitude minutes must be a number', 'GPSLonMin'
        elif record[0] == 'GPSLonSec':
            new_lonsec = str(record[1])
            old_lonsecs = str(record[2])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Longitude seconds must be a number', 'GPSLonSec'
        elif record[0] == 'GPSLonDirectionID':
            new_londir = str(record[1])
            old_londirs = str(record[2])
        elif record[0] == 'GPSUTMZone':
            new_utmzone = str(record[1])
            old_utmzones = str(record[1])
        elif record[0] == 'GPSUTMN':
            new_utmn = str(record[1])
            old_utmns = str(record[1])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'UTM northing must be a number', 'GPSUTMN'
        elif record[0] == 'GPSUTME':
            new_utme = str(record[1])
            old_utmes = str(record[1])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'UTM easting must be a number', 'GPSUTME'
        elif record[0] == 'GPSElev':
            new_elev = str(record[1])
            old_elevs = str(record[1])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Elevation must be a number', 'GPSElev'
        elif record[0] == 'GPSElevError':
            new_elev_error = str(record[1])
            old_elev_errors = str(record[1])
            if not try_float(record[1]) and record[1] != 'NULL' and record[1] != '':
                return 'Elevation error must be a number', 'GPSElevError'
        elif record[0] == 'GPSElevUnitID':
            new_elev_unit = str(record[1])
            old_elev_units = str(record[1])

    if 'D' in gps_format_abbreviation:
        # DD, DDM, or DMS
        if (new_utmn != 'NULL' or (new_utmn == '' and 'NULL' not in old_utmns)) or (new_utme != 'NULL' or (new_utme == '' and 'NULL' not in old_utmes) or (new_utmzone != 'NULL' or (new_utmzone == '' and 'NULL' not in old_utmzones))):
            return 'UTM coordinates given for degrees format. Coordinates should be entered in the format originally provided.', 'GPSUTMZone'
        if (new_latdeg != 'NULL' and new_londeg == 'NULL'):
            return 'Missing degrees lon in degree format', 'GPSLonDeg'
        if (new_latdeg == 'NULL' and new_londeg != 'NULL'):
            return 'Missing degrees lat in degree format', 'GPSLatDeg'
        if (new_latdeg == '' and 'NULL' not in old_latdegs):
            return 'Missing degrees lat in degree format', 'GPSLatDeg'
        if (new_londeg == '' and 'NULL' not in old_londegs):
            return 'Missing degrees lon in degree format', 'GPSLonDeg'
        if 'DD ' in gps_format_abbreviation:
            # DD
            if new_latmin != 'NULL' or new_latsec != 'NULL' or (new_latmin == '' and 'NULL' not in old_latmins) or (new_latsec == '' and 'NULL' not in old_latsecs):
                return 'Minutes and/or seconds given in DD format', 'GPSLatMin'
            if new_lonmin != 'NULL' or new_lonsec != 'NULL' or (new_lonmin == '' and 'NULL' not in old_lonmins) or (new_lonsec == '' and 'NULL' not in old_lonsecs):
                return 'Minutes and/or seconds given in DD format', 'GPSLonMin'
        elif 'DM' in gps_format_abbreviation:
            # DDM or DMS
            if (new_latmin != 'NULL' and new_lonmin == 'NULL') or (new_lonmin == '' and 'NULL' not in old_lonmins):
                return 'Missing minutes lon in degree format', 'GPSLonMin'
            if (new_latmin == 'NULL' and new_lonmin != 'NULL') or (new_latmin == '' and 'NULL' not in old_latmins):
                return 'Missing minutes lat in degrees format', 'GPSLatMin'
            if (new_latdeg == 'NULL' and new_latmin != 'NULL') or (new_latdeg == '' and 'NULL' not in old_latdegs):
                return 'Minutes given without degrees in degree format', 'GPSLatDeg'
            if (new_londeg == 'NULL' and new_lonmin != 'NULL') or (new_londeg == '' and 'NULL' not in old_londegs):
                return 'Minutes given without degrees in degree format', 'GPSLonDeg'
            try:
                if new_latdeg != '' and new_latdeg != 'NULL':
                    int(new_latdeg)
            except ValueError:
                return f'Decimal degrees given in {gps_format_abbreviation} format', 'GPSLatDeg'
            try:
                if new_londeg != '' and new_londeg != 'NULL':
                    int(new_londeg)
            except ValueError:
                return f'Decimal degrees given in {gps_format_abbreviation} format', 'GPSLonDeg'
            if 'DDM ' in gps_format_abbreviation:
                if new_latsec != 'NULL' or (new_latsec == '' and 'NULL' not in old_latsecs):
                    return 'Seconds given in DDM format', 'GPSLatSec'
                if new_lonsec != 'NULL' or (new_lonsec == '' and 'NULL' not in old_lonsecs):
                    return 'Seconds given in DDM format', 'GPSLonSec'
            elif 'DMS' in gps_format_abbreviation:
                if (new_latsec == '' and 'NULL' not in old_latsecs) or (new_latsec == 'NULL' and new_lonsec != 'NULL'):
                    return 'Missing seconds lat in DMS format', 'GPSLatSec'
                if (new_latsec != 'NULL' and new_lonsec == 'NULL') or (new_lonsec == '' and 'NULL' not in old_lonsecs):
                    return 'Missing seconds lon in DMS format', 'GPSLonSec'
                if (new_latmin == 'NULL' and new_latsec != 'NULL') or (new_latmin == '' and 'NULL' not in old_latmins):
                    return 'Seconds given without minutes in DMS format', 'GPSLatMin'
                if (new_lonmin == 'NULL' and new_lonsec != 'NULL') or (new_lonmin == '' and 'NULL' not in old_lonmins):
                    return 'Seconds given without minutes in DMS format', 'GPSLonMin'
                try:
                    if new_latmin != '' and new_latmin != 'NULL':
                        int(new_latmin)
                except ValueError:
                    return 'Decimal minutes given in DMS format', 'GPSLatMin'
                try:
                    if new_lonmin != '' and new_lonmin != 'NULL':
                        int(new_lonmin)
                except ValueError:
                    return 'Decimal minutes given in DMS format', 'GPSLonMin'
        if '+/-' in gps_format_abbreviation:
            if new_latdir != 'NULL' or (new_latdir == '' and 'NULL' not in old_latdirs):
                return 'Use signs instead of directions in +/- format', 'GPSLatDirectionID'
            if new_londir != 'NULL' or (new_londir == '' and 'NULL' not in old_londirs):
                return 'Use signs instead of directions in +/- format', 'GPSLonDirectionID'
        elif 'NSEW' in gps_format_abbreviation:
            if new_latdir == 'NULL' and new_londir != 'NULL':
                return 'Only one direction given in NSEW format', 'GPSLatDirectionID'
            if new_latdir != 'NULL' and new_londir == 'NULL':
                return 'Only one direction given in NSEW format', 'GPSLonDirectionID'
            if (new_latdir == '' and 'NULL' not in old_latdirs) and (new_londir != '' and 'NULL' in old_londirs):
                return 'Only one direction given in NSEW format', 'GPSLatDirectionID'
            if (new_londir == '' and 'NULL' not in old_londirs) and (new_latdir != '' and 'NULL' in old_latdirs):
                return 'Only one direction given in NSEW format', 'GPSLonDirectionID'
            if ((new_latdir == 'NULL' and new_latdeg != 'NULL') or
                    (new_latdir == 'NULL' and new_latdeg =='' and 'NULL' not in old_latdegs) or
                    (new_latdir == '' and 'NULL' in old_latdirs and new_latdeg != 'NULL')):
                return 'Missing direction in NSEW format', 'GPSLatDirectionID'
            if ((new_londir == 'NULL' and new_londeg != 'NULL') or
                    (new_londir == 'NULL' and new_londeg == '' and 'NULL' not in old_londegs) or
                    (new_londir == '' and 'NULL' in old_londirs and new_londeg != 'NULL')):
                return 'Missing direction in NSEW format', 'GPSLonDirectionID'
            if ((new_latdir != 'NULL' and new_latdeg == 'NULL') or
                    (new_latdir != 'NULL' and new_latdeg == '' and 'NULL' in old_latdegs) or
                    (new_latdir == '' and 'NULL' not in old_latdirs and new_latdeg == 'NULL')):
                return 'Direction given without coordinates in NSEW format', 'GPSLatDirectionID'
            if ((new_londir != 'NULL' and new_londeg == 'NULL') or
                    (new_londir != 'NULL' and new_londeg == '' and 'NULL' in old_londegs) or
                    (new_londir == '' and 'NULL' not in old_londirs and new_londeg == 'NULL')):
                return 'Direction given without coordinates in NSEW format', 'GPSLonDirectionID'
            if '-' in new_latdeg or (new_latdeg == '' and '-' in old_latdegs):
                return 'Use only positive coordinates in NSEW format', 'GPSLatDeg'
            if '-' in new_londeg or (new_londeg == '' and '-' in old_londegs):
                return 'Use only positive coordinates in NSEW format', 'GPSLonDeg'
            if new_latdir in ('3','4'):
                return 'Latitude direction must be N or S', 'GPSLatDirectionID'
            if new_londir in ('1','2'):
                return 'Longitude direction must be E or W', 'GPSLonDirectionID'
    if 'UTM' in gps_format_abbreviation:
        if ((new_latdeg != 'NULL' or (new_latdeg == '' and 'NULL' not in old_latdegs)) or
                (new_latmin != 'NULL' or (new_latmin == '' and 'NULL' not in old_latmins)) or
                (new_latsec != 'NULL' or (new_latsec == '' and 'NULL' not in old_latsecs)) or
                (new_latdir != 'NULL' or (new_latdir == '' and 'NULL' not in old_latdirs))):
            return 'Degrees coordinates given for UTM format. Coordinates should be entered in the format originally provided.', 'GPSLatDeg'
        if ((new_londeg == '' and 'NULL' not in old_londegs) or
                (new_lonmin != 'NULL' or (new_lonmin == '' and 'NULL' not in old_lonmins)) or
                (new_lonsec != 'NULL' or (new_lonsec == '' and 'NULL' not in old_lonsecs)) or
                (new_londir != 'NULL' or (new_londir == '' and 'NULL' not in old_londirs))):
            return 'Degrees coordinates given for UTM format. Coordinates should be entered in the format originally provided.', 'GPSLonDeg'
        if ((new_utmn != 'NULL' and new_utme == 'NULL') or
                (new_utmn != 'NULL' and new_utme == '' and 'NULL' in old_utmes) or
                (new_utmn == '' and 'NULL' not in old_utmns and new_utme == 'NULL')):
            return 'Missing easting in UTM format', 'GPSUTME'
        if ((new_utme != 'NULL' and new_utmn == 'NULL') or
                (new_utme != 'NULL' and new_utmn == '' and 'NULL' in old_utmns) or
                (new_utme == '' and 'NULL' not in old_utmes and new_utmn == 'NULL')):
            return 'Missing northing in UTM format', 'GPSUTMN'
        if ((new_utmn != 'NULL' and new_utmzone == 'NULL') or
                (new_utme != 'NULL' and new_utmzone == '' and 'NULL' in old_utmzones) or
                (new_utme == '' and 'NULL' not in old_utmes and new_utmzone == 'NULL')):
            return 'Missing UTM zone in UTM format', 'GPSUTMZone'
        if ((new_utmzone != 'NULL' and new_utme == 'NULL') or
                (new_utmzone != 'NULL' and new_utme == '' and 'NULL' in old_utmes) or
                (new_utmzone == '' and 'NULL' not in old_utmzones and new_utme == 'NULL')):
            return 'UTM zone given without coordinates in UTM format', 'GPSUTMZone'
    if (new_elev != 'NULL' and new_elev_unit == 'NULL') or (new_elev != 'NULL' and new_elev_unit == '' and 'NULL' in old_elev_units) or (new_elev == '' and 'NULL' not in old_elevs and new_elev_unit == 'NULL'):
        return 'Elevation missing units', 'GPSElevUnitID'
    if (new_elev == 'NULL' and new_elev_error != 'NULL') or (new_elev == 'NULL' and new_elev_error == '' and 'NULL' not in old_elev_errors) or (new_elev == '' and 'NULL' in old_elevs and new_elev_error != 'NULL'):
        return 'Elevation error missing elevation', 'GPSElev'
    return None, None

def check_insert_concordance(pairs: list, concordance_format_id: int):
    if not pairs or not concordance_format_id:
        return 'Incomplete data given for concordance'
    concordance_format_model = QtS.QSqlTableModel()
    concordance_format_model.setTable('ConcordanceFormats')
    concordance_format_model.select()
    while concordance_format_model.canFetchMore():
        concordance_format_model.fetchMore()
    new_68v76_concordance = 'NULL'
    new_68v75_concordance = 'NULL'
    for pair in pairs:
        if pair[0] == 'Concordance_206Pb/238Uv207Pb/206Pb':
            new_68v76_concordance = pair[1]
        elif pair[0] == 'Concordance_207Pb/238Uv207Pb/235U':
            new_68v75_concordance = pair[1]
    if (new_68v76_concordance != 'NULL' or new_68v75_concordance != 'NULL') and not concordance_format_id:
        return 'Concordance format ID missing', 'ConcordanceFormatID'
    # if 'MinSegDisc' in format_name:
    #     if new_68v76_concordance != 'NULL' or new_68v75_concordance != 'NULL':
    #         return '206Pb/238Uv207Pb/206Pb and 207Pb/238Uv207Pb/235U concordance values should be NULL in MinSegDisc format', 'Concordance_206Pb/238Uv207Pb/206Pb'
    return None, None

def check_update_concordance(pairs: list):
    concordance_format_model = QtS.QSqlTableModel()
    concordance_format_model.setTable('ConcordanceFormats')
    concordance_format_model.select()
    while concordance_format_model.canFetchMore():
        concordance_format_model.fetchMore()
    new_68v76_concordance = ''
    new_68v75_concordance = ''
    old_68v76_concordances = []
    old_68v75_concordances = []
    new_concordance_format_id = ''
    old_concordance_format_ids = []
    for pair in pairs:
        if pair[0] == 'Concordance_206Pb/238Uv207Pb/206Pb':
            new_68v76_concordance = pair[1]
            old_68v76_concordances = pair[2]
        elif pair[0] == 'Concordance_207Pb/238Uv207Pb/235U':
            new_68v75_concordance = pair[1]
            old_68v75_concordances = pair[2]
        if pair[0] == 'ConcordanceFormatID':
            new_concordance_format_id = pair[1]
            old_concordance_format_ids = pair[2]
    if new_68v76_concordance != '' or new_68v75_concordance != '':
        if ((new_68v76_concordance != 'NULL' or (new_68v76_concordance == '' and 'NULL' not in old_68v76_concordances))
                or (new_68v75_concordance != 'NULL' or (new_68v75_concordance == '' and 'NULL' not in old_68v75_concordances))
                and not (new_concordance_format_id or (new_concordance_format_id == '' and 'NULL' not in old_concordance_format_ids))):
            return 'Concordance format ID missing', 'ConcordanceFormatID'
    return None, None

def check_dependencies(table: str, record_id_header: str, record_ids: list, record_names: list):
    """
    Check whether the records provided are being used in other tables
    :param table: the table to be deleted from
    :param record_id_header: the header for the id column
    :param record_ids: the list of record ids to be deleted
    :return: Nothing if successful, error message if not
    """

    def build_dependencies_check(table: str, dependent_table: str, record_id_header: str, record_ids: list, record_names: list):
        """
        Check if the records are being used in the dependent table
        :param table: name of the table to be checked
        :param dependent_table: name of the table that the records are being checked against
        :param record_id_header: name of the column to be checked in the dependent table
        :param record_ids: list of record ids to be checked
        :param record_names: list of names of the records, empty string if not applicable
        :return: text of the dependencies
        """
        query = QtS.QSqlQuery()
        dependencies_text = ''
        record_dependent_ids = []
        for index in range(len(record_ids)):
            if not query.exec(f'SELECT * FROM {dependent_table} WHERE {record_id_header} = {record_ids[index]}'):
                return f'Unable to check if {table} records are being used in {dependent_table}: {query.lastError().text()}'
            dependent_ids = []
            while query.next():
                dependent_ids.append(query.value(0))
            if dependent_ids:
                if record_names[index]:
                    name = record_names[index]
                else:
                    name = record_ids[index]
                dependencies_text += f'{table}: {name} is associated with {len(dependent_ids)} records in {dependent_table}.\n'
            record_dependent_ids.append(dependent_ids)
        return dependencies_text, record_dependent_ids

    def build_child_check(table: str, record_id_header: str, record_ids: list, record_names: list):
        query = QtS.QSqlQuery()
        children_text = ''
        record_child_ids = []
        for index in range(len(record_ids)):
            if not query.exec(f'SELECT * FROM {table} WHERE "Parent{record_id_header}" = {record_ids[index]}'):
                return f'Unable to check if {table} records have children: {query.lastError().text()}'
            child_ids = []
            while query.next():
                child_ids.append(query.value(0))
            if child_ids:
                if record_names[index]:
                    name = record_names[index]
                else:
                    name = record_ids[index]
                children_text += f'{table}: {name} has {len(child_ids)} children.\n'
            record_child_ids.append(child_ids)
        return children_text, record_child_ids

    def build_parent_check(table: str, record_id_header:str, record_ids: list, record_names: list):
        query = QtS.QSqlQuery()
        parents_text = ''
        record_parent_ids = []
        for index in range(len(record_ids)):
            if not query.exec(f'SELECT "Parent{record_id_header}" FROM {table} WHERE {record_id_header} = {record_ids[index]}'):
                return f'Unable to check if {table} records have parents: {query.lastError().text()}'
            parent_ids = []
            while query.next():
                parent_ids.append(query.value(0))
            if parent_ids:
                if record_names[index]:
                    name = record_names[index]
                else:
                    name = record_ids[index]
                parents_text += f'{table}: {name} has {len(parent_ids)} parents.\n'
            record_parent_ids.append(parent_ids)
        return parents_text, record_parent_ids

    if table == 'AgeConstraints' or table == 'AgeInterpretations' or table == 'Sources':
        # Check if the record is being used in SampleAges
        dependencies_text = build_dependencies_check(table, 'SampleAges', record_id_header, record_ids, record_names)
        return dependencies_text
    if table == 'Ages':
        # Check if the record is being used in SampleAges
        dependencies_text, record_dependent_ids = build_dependencies_check(table, 'SampleAges', 'OldestAgeID', record_ids, record_names)
        text, list = build_dependencies_check(table, 'SampleAges', 'YoungestAgeID', record_ids, record_names)
        dependencies_text += text
        for item in list:
            record_dependent_ids.append(item)
        children_text, record_child_ids = build_child_check(table, 'parentAgeID', record_ids, record_names)
        parent_text, record_parent_ids = build_parent_check(table, record_id_header, 'parentAgeID', record_ids, record_names)
        return dependencies_text, record_dependent_ids
    if table == 'AliquotContexts':
        # Check if the record is being used in Aliquots_AliquotContexts
        dependencies_text = build_dependencies_check(table, 'Aliquots_AliquotContexts', 'AliquotContextID', record_ids, record_names)
        return dependencies_text
    if table == 'Aliquots':
        # Check which samples it belongs to
        dependencies_text = build_dependencies_check(table, 'Samples', 'SampleID', record_ids, record_names)

def try_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False