import time

from PyQt6 import QtCore as QtC
from PyQt6 import QtSql as QtS

import Functions.Create_database as Create_db
import logger_setup
from Functions.Database_manager import turn_on_foreign_keys, turn_off_foreign_keys
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import settings
from Functions.Widget_classes import set_table, get_columns
# the below imports are required for GPS conversions, pycharm detects no usage do not remove
# below comments are for pycharm to ignore issues
# noinspection PyUnresolvedReferences
import pyproj
# noinspection PyUnresolvedReferences
import Functions.GPS_conversions as GPS


def settings_reset():
    """

    :return: True for success, False for failure
    :rtype: bool
    """
    tables_affected = [['SampleAges', Create_db.CREATE_SAMPLE_AGE_TABLE],
                       ['UPbAnalyses', Create_db.CREATE_UPBANALYSES_TABLE],
                       ['GPSLocations', Create_db.CREATE_GPS_LOCATIONS_TABLE],
                       ['Samples', Create_db.CREATE_SAMPLES_TABLE],
                       ['Columns', Create_db.CREATE_COLUMNS_TABLE], ['References', Create_db.CREATE_REFERENCES_TABLE]]
    if drop_virtual_columns(tables_affected):
        if populate_generated_columns():
            return True
        else:
            return False
    else:
        return False


def drop_virtual_columns(tables_affected: list[list[str]], edit_table: str = None) -> bool:
    """
     Function to drop virtual columns from tables and regenerate them. Function creates new table with no virtual columns,
    copies data from old table, deletes old table, and renames the new table to the old table.
    :param list[list[str]] tables_affected: List of tables affected where index 0 is table_name and index 1 is SQL create string
    :param edit_table:
    :return: True for success, False for failure
    :rtype: bool
    """
    start_time = time.time()
    if not turn_off_foreign_keys():
        return False
    create_savepoint('before_drop')
    for table_info in tables_affected:
        table = table_info[0]
        if edit_table is not None and table != edit_table:
            continue
        create_sql = table_info[1]
        query, virtual, stored, columns = get_columns(table)
        if query.lastError().text() != '':
            logger_setup.get_logger().critical(f'Error getting {table} columns')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_drop')
            return False
        if virtual:

            # Create a new table with the same original columns as the old one
            logger_setup.get_logger().info(f'Creating table: {table}_new')
            if table == 'References':
                column_creation = create_sql.split(f'CREATE TABLE IF NOT EXISTS "{table}"')[1]
            else:
                column_creation = create_sql.split(f'CREATE TABLE IF NOT EXISTS {table}')[1]
            create_sql = f'CREATE TABLE IF NOT EXISTS {table}_new{column_creation}'
            if not query.exec(create_sql):
                logger_setup.get_logger().critical(f'Error creating {table}_new table')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                rollback_savepoint('before_drop')
                return False
            logger_setup.get_logger().info(f'Successfully created table: {table}_new')

            # Select only the stored columns, not the virtual ones
            column_str = ', '.join(columns)
            insert_new_table = f'INSERT INTO {table}_new SELECT {column_str} FROM "{table}"'
            logger_setup.get_logger().info(f'Inserting into old table: {table}_old')
            if not query.exec(insert_new_table):
                logger_setup.get_logger().critical(f'Error inserting {table}_new table')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                rollback_savepoint('before_drop')
                return False
            logger_setup.get_logger().info(f'Successfully inserted into new table: {table}_new')

            # Drop the original table
            drop_original_table = f'DROP TABLE "{table}"'
            logger_setup.get_logger().info(f'Dropping original table: {table}')
            if not query.exec(drop_original_table):
                logger_setup.get_logger().critical(f'Error dropping original {table} table')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                rollback_savepoint('before_drop')
                return False
            logger_setup.get_logger().info(f'Successfully dropped original table: {table}')

            # Rename the new table to the original table name
            alter_table_qry = f'ALTER TABLE {table}_new RENAME TO "{table}"'
            logger_setup.get_logger().info(f'Altering table rename: {table}_new to {table}')
            if not query.exec(f'ALTER TABLE {table}_new RENAME TO "{table}"'):
                logger_setup.get_logger().critical(f'Error renaming {table} table')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                rollback_savepoint('before_drop')
                return False
            logger_setup.get_logger().info(f'Successfully altered table rename: {table}_new to {table}')

            # Get the columns of the new table to compare to the original table
            new_query, new_virtual, new_stored, new_columns = get_columns(table)
            if new_columns != columns:
                logger_setup.get_logger().critical(f'Error copying new table {table} columns')
                logger_setup.get_logger().debug(f'Original columns: {columns}')
                logger_setup.get_logger().debug(f'New columns: {new_columns}')
                rollback_savepoint('before_drop')
                return False

    release_savepoint('before_drop')
    end_time = time.time()
    logger_setup.get_logger().info(f'Dropped virtual columns: {end_time-start_time} seconds')
    if not turn_on_foreign_keys():
        return False
    return True


def populate_generated_columns() -> bool:
    """
    Function to populate generated columns for all tables with virtual columns based on current user settings.
    :return: True for success, False for failure
    :rtype: bool
    """
    start_time = time.time()
    create_savepoint('before_populate')
    # Retrieve the settings
    age_unit_id = settings._instance.value('age_unit_id')  # default to Ma
    elevation_unit_id = settings._instance.value('elevation_unit_id')  # default to m
    gps_format_id = settings._instance.value('gps_format_id')  # default to DD +/-
    heightdepth_unit_id = settings._instance.value('heightdepth_unit_id')  # default to m
    spotsize_unit_id = settings._instance.value('spotsize_unit_id')  # default to um
    age_error_format_id = settings._instance.value('age_error_format_id')  # default to 1 sigma abs
    ratio_error_format_id = settings._instance.value('ratio_error_format_id')  # default to 1 sigma abs
    concordance_format_id = settings._instance.value('concordance_format_id')  # default conc ratio
    reference_format = settings._instance.value('reference_format')

    # Affected list format: [[table1, [unit/type ID headers], column1, column2, ...], [table2, [unit/type ID headers], column1, column2, ...], ...]
    # Save age errors to handle both age unit and age error type
    age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge'],
                         ['UPbAnalyses', 'AgeUnitID', '207Pb/206PbAge', '206Pb/238UAge', '207Pb/235UAge',
                          '208Pb/232ThAge', 'BestAge']]
    elevation_unit_affected = [['GPSLocations', 'GPSElevUnitID', 'GPSElev', 'GPSElevError']]
    gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLocationDisplay']]
    heightdepth_unit_affected = [['Samples', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError'],
                                 ['Columns', 'ColumnTotalHeightDepthUnitID', 'ColumnTotalHeightDepth']]
    spotsize_unit_affected = [['UPbAnalyses', 'SpotSizeUnitID', 'SpotSize']]
    concordance_format_affected = [['UPbAnalyses', 'ConcordanceFormatID', 'Concordance']]
    upb_analyses_model = QtS.QSqlTableModel()
    set_table(upb_analyses_model, 'UPbAnalyses')
    affected_upb_ratio = ['UPbAnalyses', 'RatioErrorFormatID']
    affected_upb_age = ['UPbAnalyses', ['AgeErrorFormatID', 'AgeUnitID']]
    for col in range(upb_analyses_model.columnCount()):
        if upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole).endswith(
                'AgeError'):
            affected_upb_age.append(
                upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
        elif upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                           QtC.Qt.ItemDataRole.DisplayRole).endswith('Error'):
            affected_upb_ratio.append(
                upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
    age_error_format_affected = [['SampleAges', ['DirectAgeErrorFormatID', 'DirectAgeUnitID'], 'DirectAgeError'],
                                 affected_upb_age]
    ratio_error_format_affected = [affected_upb_ratio]

    # Convert the columns and catch any errors
    if not convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id]):
        rollback_savepoint('before_populate')
        return False

    if not convert_columns(elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                           [elevation_unit_id]):
        rollback_savepoint('before_populate')
        return False

    if not convert_columns(gps_unit_affected, ['GPSFormatConversions'], ['GPSFormat'], [gps_format_id]):
        rollback_savepoint('before_populate')
        return False

    if not convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                           [heightdepth_unit_id]):
        rollback_savepoint('before_populate')
        return False

    if not convert_columns(spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [spotsize_unit_id]):
        rollback_savepoint('before_populate')
        return False

    if not convert_columns(concordance_format_affected, ['ConcordanceFormatConversions'], ['ConcordanceFormat'],
                           [concordance_format_id]):
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(age_error_format_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                           ['ErrorFormat', 'AgeUnit'], [age_error_format_id, age_unit_id]):
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(ratio_error_format_affected, ['ErrorFormatConversions'], ['ErrorFormat'],
                           [ratio_error_format_id]):
        rollback_savepoint('before_populate')
        return False
    if not generate_reference_column('References', 'ReferenceID', reference_format):
        rollback_savepoint('before_populate')
        return False
    if not generate_age_display_column('SampleAges', 'SampleAgeID'):
        rollback_savepoint('before_populate')
        return False
    if not generate_best_age_fill_columns():
        rollback_savepoint('before_populate')
        return False
    release_savepoint('before_populate')
    end_time = time.time()
    logger_setup.get_logger().info(f'Populated virtual columns: {end_time-start_time} seconds')
    return True


def convert_columns(affected: list[list[str]], conversion_table: list[str], id_header_base: list,
                    selected_id: list) -> bool:
    """
    Helper function to generate virtual columns used in the database based on parameters
    :param list[list[str]] affected: Affected tables/column list. Index 0 is table_name, indexes n+1 are columns affected and need to be converted.
    :param list[str] conversion_table: List of conversion helper tables used for affected list
    :param id_header_base: The first part of the column ID header for conversion
    :param selected_id: The format ID used to define what format to convert everything to
    :return: True for success, False for failure
    :rtype: bool
    """
    if id_header_base[0] in ['AgeUnit', 'DistanceUnit', 'ErrorFormat', 'GPSFormat', 'ConcordanceFormat']:
        for table_list in affected:
            table = table_list.pop(0)
            if len(conversion_table) > 1:
                table_id_headers = table_list.pop(0)
                table_id_header = table_id_headers[0]
            else:
                table_id_header = table_list.pop(0)
            affected_column_names = table_list

            try:
                conversions = retrieve_conversions(conversion_table[0], id_header_base[0], selected_id[0])
            except NotImplementedError:
                return False
            if len(conversion_table) > 1:
                try:
                    age_conversions = retrieve_conversions(conversion_table[1], id_header_base[1], selected_id[1])
                except NotImplementedError:
                    return False
                if not generate_age_error_columns(affected_column_names, table, table_id_headers, selected_id,
                                                  conversions, age_conversions):
                    return False
            elif id_header_base[0] == 'GPSFormat':
                if not generate_gps_column(affected_column_names, table, table_id_header, selected_id[0], conversions):
                    return False
            else:
                if not generate_columns(affected_column_names, table, table_id_header, selected_id[0], conversions):
                    return False
    return True


def retrieve_conversions(conversion_table: str, id_header_base: str, selected_id: int) -> list[tuple[any, any]]:
    """
    :param str conversion_table: Table in the database which stores conversion information
    :param str id_header_base: The first part of the column ID header for conversion
    :param int selected_id: The format ID used to define what format to convert everything to
    :raises NotImplementedError: Raised if no calculation column and from columns not found.
    :return: List of from_ids and conversion logic.
    """
    unit_conversion_model = QtS.QSqlTableModel()
    set_table(unit_conversion_model, conversion_table)
    unit_conversion_model.setFilter(f'To{id_header_base}ID={selected_id}')
    # Get the column index for the header {id_header_base}Calculation
    calculation_col = 'None'
    from_id_col = 'None'
    for col in range(unit_conversion_model.columnCount()):
        if 'Calculation' in unit_conversion_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                                             QtC.Qt.ItemDataRole.DisplayRole):
            calculation_col = col
        elif 'From' in unit_conversion_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                                        QtC.Qt.ItemDataRole.DisplayRole):
            from_id_col = col
        if calculation_col != 'None' and from_id_col != 'None':
            break
    if calculation_col is type(str) or from_id_col is type(str):
        # Error handling
        logger_setup.get_logger().critical(f'Error retrieving conversions')
        logger_setup.get_logger().debug(f'Calculation: {calculation_col} and from columns:{from_id_col} not found')
        raise NotImplementedError('Calculation not implemented.')
    conversions = []
    for row in range(unit_conversion_model.rowCount()):
        conversion = unit_conversion_model.record(row).value(calculation_col)
        from_id = unit_conversion_model.record(row).value(from_id_col)
        conversions.append((from_id, conversion))
    return conversions


def generate_columns(affected_column_names: list[str], table: str, table_id_header: str, selected_id: int,
                     conversions: list) -> bool:
    """

    :param affected_column_names:
    :param table:
    :param table_id_header:
    :param selected_id:
    :param conversions:
    :return: True for success, False for failure
    """
    query = QtS.QSqlQuery()
    for column in affected_column_names:
        if '/' in column:
            calc_column_name = f'"Calculated{column}"'
            column = f'"{column}"'
        else:
            calc_column_name = f'Calculated{column}'
        sql_alter = f'ALTER TABLE {table} ADD COLUMN {calc_column_name} REAL AS (CASE'
        sql_alter += f' WHEN {table_id_header}={selected_id} THEN {column}'
        for conversion in conversions:
            calculation = conversion[1].replace('x', column)
            if 'y' in calculation:
                ratio_column = column.replace('Error', '')
                calculation = calculation.replace('y', ratio_column)
            if column in calculation:
                calculation = f'({calculation})'
            else:
                calculation = f'"{calculation}"'
            sql_alter += f' WHEN {table_id_header}={conversion[0]} THEN {calculation}'
        sql_alter += ' END) VIRTUAL'

        logger_setup.get_logger().info(f'Adding the calculated column {column}')
        if not query.exec(sql_alter):
            logger_setup.get_logger().critical(f'Error adding the calculated column {column}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_populate')
            return False
        logger_setup.get_logger().info(f'Successfully updated {column}')
    return True


def generate_age_display_column(table: str, table_id_header: str) -> bool:
    """

    :param table:
    :param table_id_header:
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QtS.QSqlQuery()
    column = 'SampleAgeDisplay'
    sql_alter = f'ALTER TABLE "{table}" ADD COLUMN {column} TEXT AS (ifnull(CalculatedDirectAge, "") || "±" || ifnull(CalculatedDirectAgeError, "") || ", " || ifnull(CalculatedOldestDirectAge, "") || "-" || ifnull(CalculatedYoungestDirectAge, "") || ", " || ifnull(OldestAgeID, "") || "-" || ifnull(YoungestAgeID, ""))'
    logger_setup.get_logger().info(f'Adding the calculated column {column}')
    if not query.exec(sql_alter):
        logger_setup.get_logger().critical(f'Error adding the calculated column {column}')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully updated {column}')
    return True


def generate_age_error_columns(affected_column_names: list[str], table: str, table_id_headers: list, selected_id: list,
                               err_conversions: list, age_conversions: list) -> bool:
    """

    :param affected_column_names:
    :param table:
    :param table_id_headers:
    :param selected_id:
    :param err_conversions:
    :param age_conversions:
    :return: True for success, False for failure
    :rtype: bool
    """
    table_error_id_header = table_id_headers[0]
    table_age_id_header = table_id_headers[1]
    selected_error_type_id = selected_id[0]
    selected_age_unit_id = selected_id[1]
    err_conversions.append((selected_error_type_id, 'x'))
    age_conversions.append((selected_age_unit_id, 'x'))
    query = QtS.QSqlQuery()
    for err_column in affected_column_names:
        if '/' in err_column:
            calc_column_name = f'"Calculated{err_column}"'
            err_column = f'"{err_column}"'
        else:
            calc_column_name = f'Calculated{err_column}'
        sql_alter = f'ALTER TABLE {table} ADD COLUMN {calc_column_name} REAL AS (CASE'
        # sql_alter += f' WHEN {table_age_id_header}={selected_age_unit_id} AND {table_error_id_header}={selected_error_type_id} THEN {err_column}'
        for err_conversion in err_conversions:
            err_calculation = err_conversion[1].replace('x', err_column)
            age_column = err_column.replace('Error', '')
            if 'y' in err_calculation:
                err_calculation = err_calculation.replace('y', age_column)
            if selected_error_type_id == 2 or selected_error_type_id == 3:
                # Converting to a percent error, so don't need to convert the age
                sql_alter += f' WHEN {table_error_id_header}={err_conversion[0]} THEN ({err_calculation})'
            else:
                # Converting to an absolute error, so need to convert the age
                for age_conversion in age_conversions:
                    calculation = age_conversion[1].replace('x', f'({err_calculation})')
                    sql_alter += f' WHEN {table_age_id_header}={age_conversion[0]} AND {table_error_id_header}={err_conversion[0]} THEN ({calculation})'
        sql_alter += ' END) VIRTUAL'
        logger_setup.get_logger().info(f'Updating the calculated {err_column}')
        if not query.exec(sql_alter):
            logger_setup.get_logger().critical(f'Error adding the calculated column {err_column}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_populate')
            return False
        logger_setup.get_logger().info(f'Successfully updated {err_column}')
    return True

def generate_best_age_fill_columns():
    young_column_setting = settings.value('young_fill_best_age')
    old_column_setting = settings.value('old_fill_best_age')
    best_age_cutoff = settings.value('best_age_cutoff')
    for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge', 'CalculatedBestAgeError'):
        logger_setup.get_logger().info(f'Constructing query for {column}')
        young_column = young_column_setting.replace('"', '')
        old_column = old_column_setting.replace('"', '')
        if 'Error' in column:
            young_column = f'{young_column.replace('"', '')}Error'
            old_column = f'{old_column.replace('"', '')}Error'
        if 'Calculated' in column:
            young_column = f'Calculated{young_column.replace('"', '')}'
            old_column = f'Calculated{old_column.replace('"', '')}'
        sql_alter = f'''ALTER TABLE UPbAnalyses ADD COLUMN "{column}Filled" REAL AS 
                        (CASE WHEN "{column}" IS NULL THEN
                            (CASE 
                                WHEN "{young_column}" IS NULL AND "{old_column}" IS NULL THEN NULL
                                WHEN "{young_column}" IS NULL THEN "{old_column}"
                                WHEN "{old_column}" IS NULL THEN "{young_column}"
                                WHEN "{young_column}" < "{best_age_cutoff}" THEN "{young_column}"
                                ELSE "{old_column}"
                            END)
                            ELSE "{column}"
                        END) VIRTUAL'''
        query = QtS.QSqlQuery()
        if not query.exec(sql_alter):
            logger_setup.get_logger().critical(f'Failed to fill missing values for {column}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_populate')
            return False
        logger_setup.get_logger().info(f'Successfully updated {column}')
    return True

def generate_gps_column(affected_column_names: list[str], table: str, table_id_header: str, selected_id: int,
                        conversions: list) -> bool:
    """

    :param affected_column_names:
    :param table:
    :param table_id_header:
    :param selected_id:
    :param conversions:
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QtS.QSqlQuery()
    column = 'GPSLocationConverted'
    variables = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec',
                 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'deg_symbol', 'min_symbol', 'sec_symbol']
    modules = ['GPS', 'pyproj']
    global_vars = {name: globals()[name] for name in modules}
    gps_model = QtS.QSqlTableModel()
    set_table(gps_model, table)

    if selected_id == 7:  # UTM selected
        sql_zone_alter = f'ALTER TABLE {table} ADD COLUMN CalculatedZone VIRTUAL'
        sql_e_alter = f'ALTER TABLE {table} ADD COLUMN CalculatedEasting VIRTUAL'
        sql_n_alter = f'ALTER TABLE {table} ADD COLUMN CalculatedNorthing VIRTUAL'
        sql_gps_alters = [sql_zone_alter, sql_e_alter, sql_n_alter]
    else:  # lat, lon of some form selected
        sql_lat_alter = f'ALTER TABLE {table} ADD COLUMN CalculatedLat VIRTUAL'
        sql_lon_alter = f'ALTER TABLE {table} ADD COLUMN CalculatedLon VIRTUAL'
        sql_gps_alters = [sql_lat_alter, sql_lon_alter]
    for sql_gps_alter in sql_gps_alters:
        logger_setup.get_logger().info(
            f'Adding the calculated column {sql_gps_alter.split("COLUMN ")[1].split(" VIRTUAL")[0]}')
        if not query.exec(sql_gps_alter):
            logger_setup.get_logger().critical(
                f'Error adding the calculated column {sql_gps_alter.split("COLUMN ")[1]}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_populate')
            return False
    for row in range(gps_model.rowCount()):
        gps_id = gps_model.record(row).value('GPSLocationID')
        gps_format_id = gps_model.record(row).value('GPSFormatID')
        GPSLatDeg = gps_model.record(row).value('GPSLatDeg')
        GPSLatMin = gps_model.record(row).value('GPSLatMin')
        GPSLatSec = gps_model.record(row).value('GPSLatSec')
        GPSLatDirectionID = gps_model.record(row).value('GPSLatDirectionID')
        GPSLonDeg = gps_model.record(row).value('GPSLonDeg')
        GPSLonMin = gps_model.record(row).value('GPSLonMin')
        GPSLonSec = gps_model.record(row).value('GPSLonSec')
        GPSLonDirectionID = gps_model.record(row).value('GPSLonDirectionID')
        GPSUTMZone = gps_model.record(row).value('GPSUTMZone')
        GPSUTMN = gps_model.record(row).value('GPSUTMN')
        GPSUTME = gps_model.record(row).value('GPSUTME')
        deg_symbol = u'\N{DEGREE SIGN}'
        min_symbol = "'"
        sec_symbol = '"'
        # deg_symbol = '\u00b0'
        # deg_symbol = '°'
        local_vars = {name: locals()[name] for name in variables}

        for conversion in conversions:
            if conversion[0] == gps_format_id:
                gps_code = conversion[1]
                if '°' in gps_code:
                    gps_code = gps_code.replace('°', '{deg_symbol}')
                exec(gps_code, global_vars, local_vars)
                gps_display = local_vars.get('converted')
                query.prepare(f'UPDATE {table} SET {column}=:gps_display WHERE "GPSLocationID"={gps_id}')
                query.bindValue(':gps_display', gps_display)
                logger_setup.get_logger().info(f'Updating the calculated {column}')
                if not query.exec():
                    logger_setup.get_logger().critical(f'Error adding the calculated column {column}')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                    rollback_savepoint('before_populate')
                    return False
                gps_elements = gps_display.split(', ')
                for sql_gps_alter in sql_gps_alters:
                    gps_column = sql_gps_alter.split('COLUMN ')[1].split(" VIRTUAL")[0]
                    query.prepare(f'UPDATE {table} SET {gps_column}=:value WHERE "GPSLocationID"={gps_id}')
                    query.bindValue(':value', gps_elements[sql_gps_alters.index(sql_gps_alter)])
                    if not query.exec():
                        logger_setup.get_logger().critical(
                            f'Error adding the calculated column {gps_column}')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                        rollback_savepoint('before_populate')
                        return False
                    logger_setup.get_logger().info(f'Successfully updated {gps_column}')
                logger_setup.get_logger().info(f'Successfully updated {column}')
                break
    return True


def generate_reference_column(table: str, table_id_header: str, constructor: str) -> bool:
    """

    :param table:
    :param table_id_header:
    :param constructor:
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QtS.QSqlQuery()
    column = 'ReferenceDisplay'

    sql_alter = f'ALTER TABLE "{table}" ADD COLUMN {column} TEXT AS ({constructor}) VIRTUAL'
    logger_setup.get_logger().info(f'Adding the calculated column {column}')
    if not query.exec(sql_alter):
        logger_setup.get_logger().critical(f'Error adding the calculated column {column}')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        rollback_savepoint('before_populate')
        return False
    logger_setup.get_logger().info(f'Successfully updated {column}')
    return True


def update_generated_columns(table: str) -> bool:
    """
    Updates all of the generated columns for a given table.
    :param str table:
    :return: True for success, False for failure
    """
    if table == 'GPSLocations':
        # Drop the virtual columns
        tables_affected = [[['GPSLocations', Create_db.CREATE_GPS_LOCATIONS_TABLE]]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        elevation_unit_id = settings._instance.value('elevation_unit_id')
        gps_format_id = settings._instance.value('gps_format_id')
        # Convert the columns and catch any errors
        elevation_unit_affected = [['GPSLocations', 'GPSElevUnitID', 'GPSElev', 'GPSElevError']]
        gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLocationDisplay']]
        if not convert_columns(elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [elevation_unit_id]):
            return False
        if not convert_columns(gps_unit_affected, ['GPSFormatConversions'], ['GPSFormat'], [gps_format_id]):
            return False
        release_savepoint('before_populate')
    elif table == 'SampleAges':
        # Drop the virtual columns
        tables_affected = [['SampleAges', Create_db.CREATE_SAMPLE_AGE_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        age_unit_id = settings._instance.value('age_unit_id')
        age_error_type_id = settings._instance.value('age_error_type_id')
        # Convert the columns and catch any errors
        age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge']]
        age_error_type_affected = [['SampleAges', ['DirectAgeErrorFormatID', 'DirectAgeUnitID'], 'DirectAgeError']]
        if not convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id]):
            return False

        if not convert_columns(age_error_type_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                               ['ErrorFormat', 'AgeUnit'],
                               [age_error_type_id, age_unit_id]):
            return False
        release_savepoint('before_populate')
    elif table == 'UPbAnalyses':
        # Drop the virtual columns
        tables_affected = [['UPbAnalyses', Create_db.CREATE_UPBANALYSES_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        age_unit_id = settings._instance.value('age_unit_id')
        spotsize_unit_id = settings._instance.value('spotsize_unit_id')
        ratio_error_format_id = settings._instance.value('ratio_error_type_id')
        age_error_format_id = settings._instance.value('age_error_type_id')
        concordance_format_id = settings._instance.value('concordance_format_id')

        # Collect the tables and columns to be converted
        age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge'],
                             ['UPbAnalyses', 'AgeUnitID', '207Pb/206PbAge', '206Pb/238UAge', '207Pb/235UAge',
                              '208Pb/232ThAge', 'BestAge']]
        spotsize_unit_affected = [['UPbAnalyses', 'SpotSizeUnitID', 'SpotSize']]
        concordance_format_affected = [['UPbAnalyses', 'ConcordanceFormatID', 'Concordance']]
        upb_analyses_model = QtS.QSqlTableModel()
        set_table(upb_analyses_model, 'UPbAnalyses')
        affected_upb_ratio = ['UPbAnalyses', 'RatioErrorFormatID']
        affected_upb_age = ['UPbAnalyses', ['AgeErrorFormatID', 'AgeUnitID']]
        for col in range(upb_analyses_model.columnCount()):
            if upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                             QtC.Qt.ItemDataRole.DisplayRole).endswith(
                'AgeError'):
                affected_upb_age.append(
                    upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
            elif upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                               QtC.Qt.ItemDataRole.DisplayRole).endswith('Error'):
                affected_upb_ratio.append(
                    upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
        age_error_format_affected = [['SampleAges', ['DirectAgeErrorFormatID', 'DirectAgeUnitID'], 'DirectAgeError'],
                                     affected_upb_age]
        ratio_error_format_affected = [affected_upb_ratio]

        # Convert the columns and catch any errors
        if not convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id]):
            return False

        if not convert_columns(spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [spotsize_unit_id]):
            return False

        if not convert_columns(concordance_format_affected, ['ConcordanceFormatConversions'], ['ConcordanceFormat'],
                               [concordance_format_id]):
            return False

        if not convert_columns(age_error_format_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                               ['ErrorFormat', 'AgeUnit'], [age_error_format_id, age_unit_id]):
            return False

        if not convert_columns(ratio_error_format_affected, ['ErrorFormatConversions'], ['ErrorFormat'],
                               [ratio_error_format_id]):
            return False

        release_savepoint('before_populate')
    elif table == 'References':
        # Drop the virtual columns
        tables_affected = [['References', Create_db.CREATE_REFERENCES_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        reference_format = settings._instance.value('reference_format')
        # Convert the columns and catch any errors
        if not generate_reference_column(table, 'ReferenceID', reference_format):
            return False
        release_savepoint('before_populate')
    elif table == 'Samples':
        # Drop the virtual columns
        tables_affected = [['Samples', Create_db.CREATE_SAMPLES_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        heightdepth_unit_id = settings._instance.value('heightdepth_unit_id')
        # Convert the columns and catch any errors
        heightdepth_unit_affected = [['Samples', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError']]
        if not convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [heightdepth_unit_id]):
            return False
        release_savepoint('before_populate')
    elif table == 'Columns':
        # Drop the virtual columns
        tables_affected = [['Columns', Create_db.CREATE_COLUMNS_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        heightdepth_unit_id = settings._instance.value('heightdepth_unit_id')
        column_total_heightdepth_unit_id = settings._instance.value('column_total_heightdepth_unit_id')
        # Convert the columns and catch any errors
        heightdepth_unit_affected = [['Columns', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError']]
        column_total_heightdepth_unit_affected = [['Columns', 'ColumnTotalHeightDepthUnitID', 'ColumnTotalHeightDepth']]
        if not convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [heightdepth_unit_id]):
            return False

        if not convert_columns(column_total_heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [column_total_heightdepth_unit_id]):
            return False
        release_savepoint('before_populate')
    else:
        return False
    return True


def convert_gps_location(gps_id: int) -> bool:
    """

    :param gps_id:
    :return: True for success, False for failure
    """
    gps_model = QtS.QSqlTableModel()
    set_table(gps_model, 'GPSLocations')
    gps_model.setFilter(f'GPSLocationID={gps_id}')
    if gps_model.lastError().text() != '':
        logger_setup.get_logger().critical(f'Error getting GPSLocations')
        logger_setup.get_logger().debug(f'Error: {gps_model.lastError().text()}')
        logger_setup.get_logger().debug(f'Filter: {gps_model.filter()}')
        return False
    query = QtS.QSqlQuery()
    column = 'GPSLocationConverted'
    variables = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec',
                 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'deg_symbol']
    modules = ['GPS', 'pyproj']
    global_vars = {name: globals()[name] for name in modules}
    gps_format_id = gps_model.record(0).value('GPSFormatID')
    GPSLatDeg = gps_model.record(0).value('GPSLatDeg')
    GPSLatMin = gps_model.record(0).value('GPSLatMin')
    GPSLatSec = gps_model.record(0).value('GPSLatSec')
    GPSLatDirectionID = gps_model.record(0).value('GPSLatDirectionID')
    GPSLonDeg = gps_model.record(0).value('GPSLonDeg')
    GPSLonMin = gps_model.record(0).value('GPSLonMin')
    GPSLonSec = gps_model.record(0).value('GPSLonSec')
    GPSLonDirectionID = gps_model.record(0).value('GPSLonDirectionID')
    GPSUTMZone = gps_model.record(0).value('GPSUTMZone')
    GPSUTMN = gps_model.record(0).value('GPSUTMN')
    GPSUTME = gps_model.record(0).value('GPSUTME')
    deg_symbol = u'\N{DEGREE SIGN}'
    min_symbol = "'"
    sec_symbol = '"'
    local_vars = {name: locals()[name] for name in variables}
    try:
        conversions = retrieve_conversions('GPSFormatConversions', 'GPSFormat', gps_format_id)
    except NotImplementedError:
        return False
    create_savepoint('before_populate_gps')
    for conversion in conversions:
        if conversion[0] == gps_format_id:
            gps_code = conversion[1]
            # gps_code = gps_code.replace("'", "\\'")
            # quote_indexes = []
            # # for each character in gps_code, if it is a quote, add its index to the list
            # for index in range(len(gps_code)):
            #     if gps_code[index] == '"':
            #         quote_indexes.append(index)
            # escaped = gps_code[quote_indexes[1]:quote_indexes[-1]].replace('"', '\\"')
            # gps_code = gps_code[:quote_indexes[1]] + escaped + gps_code[quote_indexes[-1]:]
            exec(gps_code, global_vars, locals())
            gps_display = locals().get('converted')
            logger_setup.get_logger().info(f'Updating the calculated {column}')
            query.prepare(f'UPDATE GPSLocations SET {column}=:display WHERE "GPSLocationID"={gps_id}')
            query.bindValue(':display', gps_display)
            if not query.exec():
                logger_setup.get_logger().critical(f'Error adding the calculated column {column}')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                rollback_savepoint('before_populate_gps')
                return False
            logger_setup.get_logger().info(f'Successfully updated GPS display')
            break
    release_savepoint('before_populate_gps')
    return True

def return_sample_age_display(sample_age_id: int) -> str:
    """
    During a transaction, this function will return the display string for a sample age.
    :param sample_age_id: The sample age ID to convert
    :return: age_display: The string representation of the sample age
    """
    selected_age_unit_id = settings.value('age_unit_id')
    selected_error_type_id = settings.value('age_error_format_id')
    sample_age_model = QtS.QSqlTableModel()
    set_table(sample_age_model, 'SampleAges')
    sample_age_model.setFilter(f'SampleAgeID={sample_age_id}')
    if sample_age_model.lastError().text() != '':
        logger_setup.get_logger().critical(f'Error getting SampleAges')
        logger_setup.get_logger().debug(f'Error: {sample_age_model.lastError().text()}')
        logger_setup.get_logger().debug(f'Filter: {sample_age_model.filter()}')
        return ''
    if sample_age_model.rowCount() == 0:
        logger_setup.get_logger().debug(f'No SampleAges with ID {sample_age_id} found. It may have been deleted.')
        return ''
    query = QtS.QSqlQuery()
    column = 'SampleAgeDisplay'
    variables = ['DirectAge', 'DirectAgeError', 'DirectAgeUnitID', 'DirectAgeErrorFormatID', 'OldestDirectAge',
                 'YoungestDirectAge']
    modules = ['GPS', 'pyproj']
    global_vars = {name: globals()[name] for name in modules}
    DirectAge = sample_age_model.record(0).value('DirectAge')
    DirectAgeError = sample_age_model.record(0).value('DirectAgeError')
    DirectAgeUnitID = sample_age_model.record(0).value('DirectAgeUnitID')
    DirectAgeErrorFormatID = sample_age_model.record(0).value('DirectAgeErrorFormatID')
    OldestDirectAge = sample_age_model.record(0).value('OldestDirectAge')
    YoungestDirectAge = sample_age_model.record(0).value('YoungestDirectAge')
    OldestAgeID = sample_age_model.record(0).value('OldestAgeID')
    YoungestAgeID = sample_age_model.record(0).value('YoungestAgeID')
    local_vars = {name: locals()[name] for name in variables}
    try:
        age_conversions = retrieve_conversions('AgeUnitConversions', 'AgeUnit', selected_age_unit_id)
        error_conversions = retrieve_conversions('ErrorFormatConversions', 'ErrorFormat', selected_error_type_id)
    except NotImplementedError:
        return ''
    calc_age_columns = ['DirectAge', 'DirectAgeError', 'OldestDirectAge', 'YoungestDirectAge', 'SampleAgeDisplay']
    age_values = [DirectAge, DirectAgeError, OldestDirectAge, YoungestDirectAge]
    age_calculation = 'x*1'
    for conversion in age_conversions:
        if conversion[0] == DirectAgeUnitID:
            age_calculation = conversion[1]
            break
    error_calculation = 'x*1'
    for conversion in error_conversions:
        if conversion[0] == DirectAgeErrorFormatID:
            error_calculation = conversion[1]
            # x is the original error and y is the original direct age
            if 'y' in error_calculation:
                error_calculation = error_calculation.replace('y', 'DirectAge')
            if selected_error_type_id != 2 or selected_error_type_id != 3:
                # Converting to an absolute error, so need to convert the age
                error_calculation = age_calculation.replace('x', f'({error_calculation})')
            break
    error_calculation = error_calculation.replace('x', 'DirectAgeError')
    calc_age_values = []
    calculated = None
    for column in calc_age_columns:
        if 'Error' in column:
            if age_values[calc_age_columns.index(column)] != '':
                calculated_error = eval(error_calculation)
                calc_age_values.append(calculated_error)
            else:
                calc_age_values.append('')
        elif 'DirectAge' in column:
            if age_values[calc_age_columns.index(column)] != '':
                calculation = age_calculation.replace('x', f'{column}')
                calculated_age = eval(calculation)
                calc_age_values.append(calculated_age)
            else:
                calc_age_values.append('')
        else:
            pass
    age_display = f'{calc_age_values[0]}±{calc_age_values[1]}, {calc_age_values[2]}-{calc_age_values[3]}, {OldestAgeID}-{YoungestAgeID}'
    return age_display

def convert_sample_age(sample_age_id: int) -> bool:
    """

    :param sample_age_id:
    :return: True for success, False for failure
    """
    selected_error_type_id = settings._instance.value('age_error_format_id')
    sample_age_model = QtS.QSqlTableModel()
    set_table(sample_age_model, 'SampleAges')
    sample_age_model.setFilter(f'SampleAgeID={sample_age_id}')
    if sample_age_model.lastError().text() != '':
        logger_setup.get_logger().critical(f'Error getting SampleAges')
        logger_setup.get_logger().debug(f'Error: {sample_age_model.lastError().text()}')
        logger_setup.get_logger().debug(f'Filter: {sample_age_model.filter()}')
        return False
    query = QtS.QSqlQuery()
    column = 'SampleAgeDisplay'
    variables = ['DirectAge', 'DirectAgeError', 'DirectAgeUnitID', 'DirectAgeErrorFormatID', 'OldestDirectAge',
                 'YoungestDirectAge']
    modules = ['GPS', 'pyproj']
    global_vars = {name: globals()[name] for name in modules}
    DirectAge = sample_age_model.record(0).value('DirectAge')
    DirectAgeError = sample_age_model.record(0).value('DirectAgeError')
    DirectAgeUnitID = sample_age_model.record(0).value('DirectAgeUnitID')
    DirectAgeErrorFormatID = sample_age_model.record(0).value('DirectAgeErrorFormatID')
    OldestDirectAge = sample_age_model.record(0).value('OldestDirectAge')
    YoungestDirectAge = sample_age_model.record(0).value('YoungestDirectAge')
    OldestAgeID = sample_age_model.record(0).value('OldestAgeID')
    YoungestAgeID = sample_age_model.record(0).value('YoungestAgeID')
    local_vars = {name: locals()[name] for name in variables}
    try:
        age_conversions = retrieve_conversions('AgeUnitConversions', 'AgeUnit', DirectAgeUnitID)
        error_conversions = retrieve_conversions('ErrorFormatConversions', 'ErrorFormat', DirectAgeErrorFormatID)
    except NotImplementedError:
        return False
    create_savepoint('before_populate_age')
    calc_age_columns = ['DirectAge', 'DirectAgeError', 'OldestDirectAge', 'YoungestDirectAge', 'SampleAgeDisplay']
    age_calculation = 'x*1'
    for conversion in age_conversions:
        if conversion[0] == DirectAgeUnitID:
            age_calculation = conversion[1]
            break
    error_calculation = 'x*1'
    for conversion in error_conversions:
        if conversion[0] == DirectAgeErrorFormatID:
            # x is the original error and y is the original direct age
            if 'y' in error_calculation:
                error_calculation = error_calculation.replace('y', 'DirectAge')
            if selected_error_type_id != 2 or selected_error_type_id != 3:
                # Converting to an absolute error, so need to convert the age
                error_calculation = age_calculation.replace('x', f'({error_calculation})')
            break
    error_calculation = error_calculation.replace('x', 'DirectAgeError')
    calc_age_values = []
    calculated = None
    for column in calc_age_columns:
        if 'Error' in column:
            calculated_error = eval(error_calculation)
            calc_age_values.append(calculated_error)
        elif 'DirectAge' in column:
            calculation = age_calculation.replace('x', f'{column}')
            calculated_age = eval(calculation)
            calc_age_values.append(calculated_age)
        else:
            pass
    age_display = f'{calc_age_values[0]}±{calc_age_values[1]}, {calc_age_values[2]}-{calc_age_values[3]}, {OldestAgeID}-{YoungestAgeID}'
    calc_age_values.append(age_display)
    sql_placeholders = ", ".join('?' * len(calc_age_values))
    if not query.prepare(f'UPDATE SampleAges SET ({', '.join(calc_age_columns)}) = ({sql_placeholders}) WHERE "SampleAgeID"={sample_age_id}'):
        logger_setup.get_logger().error(
            f'Error updating the age display. Displays will update on returning to main page')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        rollback_savepoint('before_populate_age')
        return False
    for i, value in enumerate(calc_age_values):
        query.bindValue(i, value)
    if not query.exec():
        logger_setup.get_logger().error(
            f'Error updating the age display. Displays will update on returning to main page')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
        rollback_savepoint('before_populate_age')
        return False
    logger_setup.get_logger().info(f'Successfully updated SampleAge display')
    release_savepoint('before_populate_age')
    return True
