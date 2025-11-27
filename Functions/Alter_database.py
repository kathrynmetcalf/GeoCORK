import time

from PyQt6 import QtCore as QtC
from PyQt6 import QtSql as QtS
from PyQt6.QtWidgets import QProgressDialog, QApplication

import Functions.Create_database as Create_db
import logger_setup
from Functions.Database_manager import turn_on_foreign_keys, turn_off_foreign_keys
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings
from Functions.LoadingDialog_manager import LoadingDialogManager
loading_manager = LoadingDialogManager.get_instance()
from Functions.Widget_classes import set_table, get_columns
# the below imports are required for GPS conversions, pycharm detects no usage do not remove
# below comments are for pycharm to ignore issues
# noinspection PyUnresolvedReferences
import pyproj
# noinspection PyUnresolvedReferences
import Functions.GPS_conversions as GPS


def settings_reset(database: QtS.QSqlDatabase = None) -> bool:
    """
    Created generated columns based on current user settings.
    :param database: QSqlDatabase instance to use, if None the default database is used
    :return: True for success, False for failure
    """
    tables_affected = [['UPbAnalyses', Create_db.CREATE_UPBANALYSES_TABLE],
                       ['SampleAges', Create_db.CREATE_SAMPLE_AGE_TABLE],
                       ['GPSLocations', Create_db.CREATE_GPS_LOCATIONS_TABLE],
                       ['Samples', Create_db.CREATE_SAMPLES_TABLE],
                       ['Columns', Create_db.CREATE_COLUMNS_TABLE],
                       ['References', Create_db.CREATE_REFERENCES_TABLE]]
    if drop_virtual_columns(tables_affected, database=database):
        if populate_generated_columns(database):
            return True
        else:
            return False
    else:
        return False

def drop_virtual_columns(tables_affected: list[list[str]], edit_table: str = None, database: QtS.QSqlDatabase = None) -> bool:
    """
     Function to drop virtual columns from tables and regenerate them. Function creates new table with no virtual columns,
    copies data from old table, deletes old table, and renames the new table to the old table.
    :param list[list[str]] tables_affected: List of tables affected where index 0 is table_name and index 1 is SQL create string.
    :param edit_table: Specific table to edit, if None all tables in tables_affected are edited.
    :param QtS.QSqlDatabase database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    :rtype: bool
    """
    start_time = time.time()
    if not turn_off_foreign_keys():
        return False
    drop_count = len(tables_affected)+1
    drop_progress = QProgressDialog("Resetting calculations...", "Cancel", 0, drop_count, loading_manager.dialog)
    drop_progress.setMinimumDuration(0)
    table_idx = 0
    create_savepoint('before_drop')

    for table_info in tables_affected:
        logger_setup.get_logger().info(f"Progress: {table_idx}/{drop_count}")
        table = table_info[0]
        drop_progress.setValue(table_idx + 1)
        # Let the event loop process the dialog's updates
        QApplication.processEvents()
        # If the user clicked "Cancel", we can break out
        if drop_progress.wasCanceled():
            return False
        if edit_table is not None and table != edit_table:
            continue
        create_sql = table_info[1]
        query, virtual, stored, columns = get_columns(table, database)
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
            logger_setup.get_logger().info(f'Inserting into new table: {table}_new')
            if not query.exec(insert_new_table):
                logger_setup.get_logger().critical(f'Error inserting {table}_new table')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                rollback_savepoint('before_drop')
                return False
            logger_setup.get_logger().info(f'Successfully inserted into new table: {table}_new')

            if not database.commit():
                if 'no transaction is active' not in database.lastError().text():
                    logger_setup.get_logger().critical(f"Error committing database")
                    logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
                    return False
            if not database.close():
                if 'no transaction is active' not in database.lastError().text():
                    logger_setup.get_logger().critical(f"Error closing database")
                    logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
                    return False
            if not database.open():
                logger_setup.get_logger().critical(f"Error opening database")
                logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
                return False

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

        table_idx += 1

    drop_progress.setValue(table_idx + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if drop_progress.wasCanceled():
        return False

    release_savepoint('before_drop')
    end_time = time.time()
    logger_setup.get_logger().info(f'Dropped virtual columns: {end_time-start_time} seconds')
    if not turn_on_foreign_keys():
        return False
    return True


def populate_generated_columns(database: QtS.QSqlDatabase = None) -> bool:
    """
    Function to populate generated columns for all tables with virtual columns based on current user settings.
    Uses the default connection established with the database file in GeoCORKMain.py if no database is provided.
    :return: True for success, False for failure
    :rtype: bool
    """
    start_time = time.time()
    create_savepoint('before_populate')
    logger_setup.get_logger().info('Populating generated columns...')
    populate_count = 0
    populate_progress = QProgressDialog('Recalculating from settings...', 'Cancel', 0, 11, loading_manager.dialog)
    populate_progress.setMinimumDuration(0)

    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False

    # Retrieve the settings
    age_unit_id = settings.value('age_unit_id')  # default to Ma
    elevation_unit_id = settings.value('elevation_unit_id')  # default to m
    gps_format_id = settings.value('gps_format_id')  # default to DD +/-
    heightdepth_unit_id = settings.value('heightdepth_unit_id')  # default to m
    spotsize_unit_id = settings.value('spotsize_unit_id')  # default to um
    age_error_format_id = settings.value('age_error_format_id')  # default to 1 sigma abs
    ratio_error_format_id = settings.value('ratio_error_format_id')  # default to 1 sigma %
    concordance_format_id = settings.value('concordance_format_id')  # default conc ratio

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
    concordance_format_affected = [['UPbAnalyses', 'ConcordanceFormatID', 'Concordance_206Pb/238Uv207Pb/206Pb',
                                    'Concordance_206Pb/238Uv207Pb/235U']]
    if database is None:
        upb_analyses_model = QtS.QSqlTableModel()
    else:
        upb_analyses_model = QtS.QSqlTableModel(db=database)
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

    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'],
                           [age_unit_id], database=database):
        rollback_savepoint('before_populate')
        return False

    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                           [elevation_unit_id], database=database):
        rollback_savepoint('before_populate')
        return False

    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(gps_unit_affected, ['GPSFormatConversions'], ['GPSFormat'],
                           [gps_format_id], database=database):
        rollback_savepoint('before_populate')
        return False

    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                           [heightdepth_unit_id], database=database):
        rollback_savepoint('before_populate')
        return False

    populate_count += 1
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                           [spotsize_unit_id], database=database):
        rollback_savepoint('before_populate')
        return False

    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(concordance_format_affected, ['ConcordanceFormatConversions'], ['ConcordanceFormat'],
                           [concordance_format_id], database=database):
        rollback_savepoint('before_populate')
        return False
    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(age_error_format_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                           ['ErrorFormat', 'AgeUnit'], [age_error_format_id, age_unit_id], database=database):
        rollback_savepoint('before_populate')
        return False
    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(ratio_error_format_affected, ['ErrorFormatConversions'], ['ErrorFormat'],
                           [ratio_error_format_id], database=database):
        rollback_savepoint('before_populate')
        return False
    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not generate_reference_column('References', settings.value('reference_format'), database=database):
        rollback_savepoint('before_populate')
        return False
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_count += 1
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not generate_age_display_column('SampleAges', database=database):
        rollback_savepoint('before_populate')
        return False
    populate_count += 1
    logger_setup.get_logger().info(f'Populate progress: {populate_count}/11')
    populate_progress.setValue(populate_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if populate_progress.wasCanceled():
        rollback_savepoint('before_populate')
        return False
    if not generate_best_age_fill_columns(database=database):
        rollback_savepoint('before_populate')
        return False
    populate_count += 1
    release_savepoint('before_populate')
    end_time = time.time()
    logger_setup.get_logger().info(f'Populated virtual columns: {end_time-start_time} seconds')
    return True


def convert_columns(affected: list[list[str]], conversion_table: list[str], id_header_base: list,
                    selected_id: list, database: QtS.QSqlDatabase = None) -> bool:
    """
    Helper function to generate virtual columns used in the database based on parameters.
    :param list[list[str]] affected: Affected tables/column list. Index 0 is table_name, indexes n+1 are columns affected and need to be converted.
    :param list[str] conversion_table: List of conversion helper tables used for affected list.
    :param id_header_base: The first part of the column ID header for conversion.
    :param selected_id: The format ID used to define what format to convert everything to.
    :param QtS.QSqlDatabase database: QSqlDatabase instance to use, if None the default database is used.
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
                conversions = retrieve_conversions(conversion_table[0], id_header_base[0], selected_id[0], database=database)
            except NotImplementedError:
                return False
            if len(conversion_table) > 1:
                try:
                    age_conversions = retrieve_conversions(conversion_table[1], id_header_base[1], selected_id[1], database=database)
                except NotImplementedError:
                    return False
                if not generate_age_error_columns(affected_column_names, table, table_id_headers, selected_id,
                                                  conversions, age_conversions, database=database):
                    return False
            elif id_header_base[0] == 'GPSFormat':
                if not generate_gps_column(affected_column_names, table, table_id_header, selected_id[0], conversions, database=database):
                    return False
            else:
                if not generate_columns(affected_column_names, table, table_id_header, selected_id[0], conversions, database=database):
                    return False
    return True


def retrieve_conversions(conversion_table: str, id_header_base: str, selected_id: int, database: QtS.QSqlDatabase = None) -> list[tuple[any, any]]:
    """
    Function to retrieve the conversion logic from the database for a given format ID.
    :param str conversion_table: Table in the database which stores conversion information.
    :param str id_header_base: The first part of the column ID header for conversion.
    :param int selected_id: The format ID used to define what format to convert everything to.
    :param QtS.QSqlDatabase database: QSqlDatabase instance to use, if None the default database is used.
    :raises NotImplementedError: Raised if no calculation column and from columns not found.
    :return: List of from_ids and conversion logic.
    """
    if database is None:
        unit_conversion_model = QtS.QSqlTableModel()
    else:
        unit_conversion_model = QtS.QSqlTableModel(db=database)
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
                     conversions: list, database: QtS.QSqlDatabase = None) -> bool:
    """
    Generate virtual columns in the database based on the affected column names and conversions.
    :param affected_column_names: List of column names to be affected by the conversion.
    :param table: Name of the table where the columns will be added.
    :param table_id_header: The header of the ID column in the table used to identify rows for conversion.
    :param selected_id: The ID of the selected format to convert to.
    :param conversions: List of tuples containing the from_id and conversion logic.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    """
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
    for column in affected_column_names:
        inverse_column = None
        if '/' in column:
            calc_column_name = f'"Calculated{column}"'
            column = f'"{column}"'
            if 'Error' in column:
                inverse_column = column.replace('"', '')
                inverse_column = f'"{inverse_column.split("/")[1].split("Error")[0]}/{inverse_column.split("/")[0]}Error"'
        else:
            calc_column_name = f'Calculated{column}'
        sql_alter = f'ALTER TABLE {table} ADD COLUMN {calc_column_name} REAL AS (CASE'
        sql_alter += f' WHEN {table_id_header}={selected_id} AND {column} IS NOT NULL THEN {column}'
        for conversion in conversions:
            calculation = conversion[1].replace('x', column)
            if 'y' in calculation:
                ratio_column = f'{calc_column_name.replace('Error', '')}'
                calculation = calculation.replace('y', ratio_column)
            if column in calculation:
                calculation = f'({calculation})'
            else:
                calculation = f'"{calculation}"'
            sql_alter += f' WHEN {table_id_header}={conversion[0]} AND {column} IS NOT NULL THEN {calculation}'
        if inverse_column:
            # If the inverse error is an absolute error, we need to calculate it
            inverse_error_ratio = f'{inverse_column}/"Calculated{inverse_column.replace("Error", "").replace('"', '')}"'
            inverse_error = f'(({inverse_error_ratio})*{calc_column_name.replace("Error", "")})'
            if selected_id in (3,4):
                # The ratio error is a percent, so the inverse error is the same percentage
                sql_alter += f' WHEN {table_id_header}={selected_id} AND {column} IS NULL THEN {inverse_column}'
            else:
                # The inverse error is an absolute error, so we need to calculate it
                sql_alter += f' WHEN {table_id_header}={selected_id} AND {column} IS NULL THEN {inverse_error}'
            for conversion in conversions:
                if conversion[0] in (3,4):
                    # The ratio error is a percent, so the inverse error is the same percentage
                    inverse_replace = inverse_column
                else:
                    # The inverse error is an absolute error, so we need to calculate it
                    inverse_replace = inverse_error
                calculation = conversion[1].replace('x', inverse_replace)
                if 'y' in calculation:
                    ratio_column = f'{calc_column_name.replace('Error', '')}'
                    calculation = calculation.replace('y', ratio_column)
                if inverse_replace in calculation:
                    calculation = f'({calculation})'
                else:
                    calculation = f'"{calculation}"'
                sql_alter += f' WHEN {table_id_header}={conversion[0]} AND {column} IS NULL THEN {calculation}'
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


def generate_age_display_column(table: str, database: QtS.QSqlDatabase = None) -> bool:
    """
    Generate a calculated column in the given table that displays the age in a user-friendly format.
    :param table: Name of the table where the calculated age column will be added.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    :rtype: bool
    """
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
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
                               err_conversions: list, age_conversions: list, database: QtS.QSqlDatabase = None) -> bool:
    """
    Generate virtual columns in the database for age errors based on the affected column names and conversions.
    :param affected_column_names: List of column names to be affected by the conversion.
    :param table: Name of the table where the columns will be added.
    :param table_id_headers: List of headers for the ID columns in the table used to identify rows for conversion.
    :param selected_id: List of IDs for the selected formats to convert to.
    :param err_conversions: List of tuples containing the error type ID and conversion logic.
    :param age_conversions: List of tuples containing the age unit ID and conversion logic.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    :rtype: bool
    """
    table_error_id_header = table_id_headers[0]
    table_age_id_header = table_id_headers[1]
    selected_error_type_id = selected_id[0]
    selected_age_unit_id = selected_id[1]
    err_conversions.append((selected_error_type_id, 'x'))
    age_conversions.append((selected_age_unit_id, 'x'))
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
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

def generate_best_age_fill_columns(database: QtS.QSqlDatabase = None) -> bool:
    """
    Generate virtual columns in the UPbAnalyses table to fill missing BestAge values based on user settings.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    """
    young_column_setting = settings.value('young_fill_best_age')
    old_column_setting = settings.value('old_fill_best_age')
    best_age_cutoff = settings.value('best_age_cutoff')
    # for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge', 'CalculatedBestAgeError'):
    for column in ('BestAge', 'BestAgeError'):
        logger_setup.get_logger().info(f'Constructing query for {column}')
        young_column = young_column_setting.replace('"', '')
        old_column = old_column_setting.replace('"', '')
        young_age = young_column
        if 'Error' in column:
            young_column = f'{young_column.replace('"', '')}Error'
            old_column = f'{old_column.replace('"', '')}Error'
            young_age = f'{young_column.replace("Error", "")}'
        # if 'Calculated' in column:
        #     young_column = f'Calculated{young_column.replace('"', '')}'
        #     old_column = f'Calculated{old_column.replace('"', '')}'
        #     young_age = f'Calculated{young_column.replace("Error", "")}'
        sql_alter = f'''ALTER TABLE UPbAnalyses ADD COLUMN "{column}Filled" REAL AS 
                        (CASE WHEN "{column}" IS NULL THEN
                            (CASE 
                                WHEN "{young_column}" IS NULL AND "{old_column}" IS NULL THEN NULL
                                WHEN "{young_column}" IS NULL THEN "{old_column}"
                                WHEN "{old_column}" IS NULL THEN "{young_column}"
                                WHEN "{young_age}" < "{best_age_cutoff}" THEN "{young_column}"
                                ELSE "{old_column}"
                            END)
                            ELSE "{column}"
                        END) VIRTUAL'''
        if database is None:
            query = QtS.QSqlQuery()
        else:
            query = QtS.QSqlQuery(db=database)
        if not query.exec(sql_alter):
            logger_setup.get_logger().critical(f'Failed to fill missing values for {column}')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_populate')
            return False
        logger_setup.get_logger().info(f'Successfully updated {column}')
    age_unit_id = settings.value('age_unit_id')  # default to Ma
    age_error_format_id = settings.value('age_error_format_id')  # default to 1 sigma abs
    age_unit_affected = [['UPbAnalyses', 'AgeUnitID', 'BestAgeFilled']]
    age_error_format_affected = [['UPbAnalyses', ['AgeErrorFormatID', 'AgeUnitID'], 'BestAgeErrorFilled']]
    if not convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'],
                           [age_unit_id], database=database):
        rollback_savepoint('before_populate')
        return False
    if not convert_columns(age_error_format_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                           ['ErrorFormat', 'AgeUnit'], [age_error_format_id, age_unit_id], database=database):
        rollback_savepoint('before_populate')
        return False
    return True

def generate_gps_column(affected_column_names: list[str], table: str, table_id_header: str, selected_id: int,
                        conversions: list, database: QtS.QSqlDatabase = None) -> bool:
    """
    Generate a GPS column in the database based on the affected column names and conversions.
    :param affected_column_names: List of column names to be affected by the conversion.
    :param table: Name of the table where the GPS column will be added.
    :param table_id_header: The header of the ID column in the table used to identify rows for conversion.
    :param selected_id: The ID of the selected GPS format to convert to.
    :param conversions: List of tuples containing the GPS format ID and conversion logic.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    :rtype: bool
    """
    logger_setup.get_logger().info(f'Generating GPS column for {affected_column_names}')
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
    column = 'GPSLocationConverted'
    variables = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec',
                 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'deg_symbol', 'min_symbol', 'sec_symbol']
    modules = ['GPS', 'pyproj']
    global_vars = {name: globals()[name] for name in modules}

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
    if not query.exec(f'SELECT * FROM GPSLocations'):
        logger_setup.get_logger().critical(f'Error selecting from {table}')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        rollback_savepoint('before_populate')
        return False
    while query.next():
        gps_id = query.record().value('GPSLocationID')
        gps_format_id = query.record().value('GPSFormatID')
        GPSLatDeg = query.record().value('GPSLatDeg')
        GPSLatMin = query.record().value('GPSLatMin')
        GPSLatSec = query.record().value('GPSLatSec')
        GPSLatDirectionID = query.record().value('GPSLatDirectionID')
        GPSLonDeg = query.record().value('GPSLonDeg')
        GPSLonMin = query.record().value('GPSLonMin')
        GPSLonSec = query.record().value('GPSLonSec')
        GPSLonDirectionID = query.record().value('GPSLonDirectionID')
        GPSUTMZone = query.record().value('GPSUTMZone')
        GPSUTMN = query.record().value('GPSUTMN')
        GPSUTME = query.record().value('GPSUTME')
        deg_symbol = u'\N{DEGREE SIGN}'
        min_symbol = "'"
        sec_symbol = '"'
        # deg_symbol = '\u00b0'
        # deg_symbol = '°'
        local_vars = {name: locals()[name] for name in variables}
        if database is None:
            update_query = QtS.QSqlQuery()
        else:
            update_query = QtS.QSqlQuery(db=database)

        for conversion in conversions:
            if conversion[0] == gps_format_id:
                gps_code = conversion[1]
                if '°' in gps_code:
                    gps_code = gps_code.replace('°', '{deg_symbol}')
                exec(gps_code, global_vars, local_vars)
                gps_display = local_vars.get('converted')
                update_query.prepare(f'UPDATE {table} SET {column}=:gps_display WHERE "GPSLocationID"={gps_id}')
                update_query.bindValue(':gps_display', gps_display)
                # logger_setup.get_logger().info(f'Updating the calculated {column}')
                if not update_query.exec():
                    logger_setup.get_logger().critical(f'Error adding the calculated column {column}')
                    logger_setup.get_logger().debug(f'Error: {update_query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {update_query.lastQuery()}')
                    logger_setup.get_logger().debug(f'Bound values: {update_query.boundValues()}')
                    rollback_savepoint('before_populate')
                    return False
                gps_elements = gps_display.split(', ')
                for sql_gps_alter in sql_gps_alters:
                    gps_column = sql_gps_alter.split('COLUMN ')[1].split(" VIRTUAL")[0]
                    update_query.prepare(f'UPDATE {table} SET {gps_column}=:value WHERE "GPSLocationID"={gps_id}')
                    update_query.bindValue(':value', gps_elements[sql_gps_alters.index(sql_gps_alter)])
                    if not update_query.exec():
                        logger_setup.get_logger().critical(
                            f'Error adding the calculated column {gps_column}')
                        logger_setup.get_logger().debug(f'Error: {update_query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {update_query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {update_query.boundValues()}')
                        rollback_savepoint('before_populate')
                        return False
                    # logger_setup.get_logger().info(f'Successfully updated {gps_column}')
                # logger_setup.get_logger().info(f'Successfully updated {column}')
                break
    logger_setup.get_logger().info(f'Successfully generated GPS Columns')
    return True


def generate_reference_column(table: str, constructor: str, database: QtS.QSqlDatabase = None) -> bool:
    """
    Generate a calculated column in the given table that displays the reference in a user-friendly format.
    :param table: Name of the table where the calculated reference column will be added.
    :param constructor: SQL expression to construct the reference display.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    :rtype: bool
    """
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
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


def update_generated_columns(table: str, database: QtS.QSqlDatabase = None) -> bool:
    """
    Updates all generated columns for a given table.
    :param str table: Name of the table to update generated columns for.
    :param QtS.QSqlDatabase database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    """
    if table == 'GPSLocations':
        # Drop the virtual columns
        tables_affected = [[['GPSLocations', Create_db.CREATE_GPS_LOCATIONS_TABLE]]]
        drop_virtual_columns(tables_affected, table, database=database)
        create_savepoint('before_populate')
        # Retrieve the settings
        elevation_unit_id = settings.value('elevation_unit_id')
        gps_format_id = settings.value('gps_format_id')
        # Convert the columns and catch any errors
        elevation_unit_affected = [['GPSLocations', 'GPSElevUnitID', 'GPSElev', 'GPSElevError']]
        gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLocationDisplay']]
        if not convert_columns(elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [elevation_unit_id], database=database):
            return False
        if not convert_columns(gps_unit_affected, ['GPSFormatConversions'], ['GPSFormat'],
                               [gps_format_id], database=database):
            return False
        release_savepoint('before_populate')
    elif table == 'SampleAges':
        # Drop the virtual columns
        tables_affected = [['SampleAges', Create_db.CREATE_SAMPLE_AGE_TABLE]]
        drop_virtual_columns(tables_affected, table, database=database)
        create_savepoint('before_populate')
        # Retrieve the settings
        age_unit_id = settings.value('age_unit_id')
        age_error_type_id = settings.value('age_error_type_id')
        # Convert the columns and catch any errors
        age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge']]
        age_error_type_affected = [['SampleAges', ['DirectAgeErrorFormatID', 'DirectAgeUnitID'], 'DirectAgeError']]
        if not convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id],
                               database=database):
            return False

        if not convert_columns(age_error_type_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                               ['ErrorFormat', 'AgeUnit'],[age_error_type_id, age_unit_id], database=database):
            return False
        release_savepoint('before_populate')
    elif table == 'UPbAnalyses':
        # Drop the virtual columns
        tables_affected = [['UPbAnalyses', Create_db.CREATE_UPBANALYSES_TABLE]]
        drop_virtual_columns(tables_affected, table, database=database)
        create_savepoint('before_populate')
        # Retrieve the settings
        age_unit_id = settings.value('age_unit_id')
        spotsize_unit_id = settings.value('spotsize_unit_id')
        ratio_error_format_id = settings.value('ratio_error_type_id')
        age_error_format_id = settings.value('age_error_type_id')
        concordance_format_id = settings.value('concordance_format_id')

        # Collect the tables and columns to be converted
        age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge'],
                             ['UPbAnalyses', 'AgeUnitID', '207Pb/206PbAge', '206Pb/238UAge', '207Pb/235UAge',
                              '208Pb/232ThAge', 'BestAge']]
        spotsize_unit_affected = [['UPbAnalyses', 'SpotSizeUnitID', 'SpotSize']]
        concordance_format_affected = [['UPbAnalyses', 'ConcordanceFormatID', 'Concordance_206Pb/238Uv207Pb/206Pb',
                                        'Concordance_206Pb/238Uv207Pb/235U']]
        if database is None:
            upb_analyses_model = QtS.QSqlTableModel()
        else:
            upb_analyses_model = QtS.QSqlTableModel(db=database)
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
        if not convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'],
                               [age_unit_id], database=database):
            return False

        if not convert_columns(spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [spotsize_unit_id], database=database):
            return False

        if not convert_columns(concordance_format_affected, ['ConcordanceFormatConversions'], ['ConcordanceFormat'],
                               [concordance_format_id], database=database):
            return False

        if not convert_columns(age_error_format_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                               ['ErrorFormat', 'AgeUnit'], [age_error_format_id, age_unit_id],
                               database=database):
            return False

        if not convert_columns(ratio_error_format_affected, ['ErrorFormatConversions'], ['ErrorFormat'],
                               [ratio_error_format_id], database=database):
            return False

        release_savepoint('before_populate')
    elif table == 'References':
        # Drop the virtual columns
        tables_affected = [['References', Create_db.CREATE_REFERENCES_TABLE]]
        drop_virtual_columns(tables_affected, table, database=database)
        create_savepoint('before_populate')
        # Convert the columns and catch any errors
        if not generate_reference_column(table, 'ReferenceID', database=database):
            return False
        release_savepoint('before_populate')
    elif table == 'Samples':
        # Drop the virtual columns
        tables_affected = [['Samples', Create_db.CREATE_SAMPLES_TABLE]]
        drop_virtual_columns(tables_affected, table, database=database)
        create_savepoint('before_populate')
        # Retrieve the settings
        heightdepth_unit_id = settings.value('heightdepth_unit_id')
        # Convert the columns and catch any errors
        heightdepth_unit_affected = [['Samples', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError']]
        if not convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [heightdepth_unit_id], database=database):
            return False
        release_savepoint('before_populate')
    elif table == 'Columns':
        # Drop the virtual columns
        tables_affected = [['Columns', Create_db.CREATE_COLUMNS_TABLE]]
        drop_virtual_columns(tables_affected, table, database=database)
        create_savepoint('before_populate')
        # Retrieve the settings
        heightdepth_unit_id = settings.value('heightdepth_unit_id')
        column_total_heightdepth_unit_id = settings.value('column_total_heightdepth_unit_id')
        # Convert the columns and catch any errors
        heightdepth_unit_affected = [['Columns', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError']]
        column_total_heightdepth_unit_affected = [['Columns', 'ColumnTotalHeightDepthUnitID', 'ColumnTotalHeightDepth']]
        if not convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [heightdepth_unit_id], database=database):
            return False

        if not convert_columns(column_total_heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                               [column_total_heightdepth_unit_id], database=database):
            return False
        release_savepoint('before_populate')
    else:
        return False
    return True


def convert_gps_location(gps_id: int, database: QtS.QSqlDatabase = None) -> bool:
    """
    Convert a GPS location to its display format based on the GPSFormatConversions table.
    :param gps_id: The GPSLocationID to convert
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    """
    if database is None:
        gps_model = QtS.QSqlTableModel()
    else:
        gps_model = QtS.QSqlTableModel(db=database)
    set_table(gps_model, 'GPSLocations')
    gps_model.setFilter(f'GPSLocationID={gps_id}')
    if gps_model.lastError().text() != '':
        logger_setup.get_logger().critical(f'Error getting GPSLocations')
        logger_setup.get_logger().debug(f'Error: {gps_model.lastError().text()}')
        logger_setup.get_logger().debug(f'Filter: {gps_model.filter()}')
        return False
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
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
        conversions = retrieve_conversions('GPSFormatConversions', 'GPSFormat', gps_format_id, database=database)
    except NotImplementedError:
        return False
    create_savepoint('before_populate_gps')
    for conversion in conversions:
        if conversion[0] == gps_format_id:
            gps_code = conversion[1]
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

def return_sample_age_display(sample_age_id: int, database: QtS.QSqlDatabase = None) -> str:
    """
    During a transaction, this function will return the display string for a sample age.
    :param sample_age_id: The sample age ID to convert.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: age_display: The string representation of the sample age.
    """
    selected_age_unit_id = settings.value('age_unit_id')
    selected_error_type_id = settings.value('age_error_format_id')
    if database is None:
        sample_age_model = QtS.QSqlTableModel()
    else:
        sample_age_model = QtS.QSqlTableModel(db=database)
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
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
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
        age_conversions = retrieve_conversions('AgeUnitConversions', 'AgeUnit', selected_age_unit_id, database=database)
        error_conversions = retrieve_conversions('ErrorFormatConversions', 'ErrorFormat', selected_error_type_id, database=database)
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

def convert_sample_age(sample_age_id: int, database: QtS.QSqlDatabase = None) -> bool:
    """
    Convert a sample age to its display format based on the AgeUnitConversions and ErrorFormatConversions tables.
    :param sample_age_id: The SampleAgeID to convert.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    """
    selected_error_type_id = settings.value('age_error_format_id')
    if database is None:
        sample_age_model = QtS.QSqlTableModel()
    else:
        sample_age_model = QtS.QSqlTableModel(db=database)
    set_table(sample_age_model, 'SampleAges')
    sample_age_model.setFilter(f'SampleAgeID={sample_age_id}')
    if sample_age_model.lastError().text() != '':
        logger_setup.get_logger().critical(f'Error getting SampleAges')
        logger_setup.get_logger().debug(f'Error: {sample_age_model.lastError().text()}')
        logger_setup.get_logger().debug(f'Filter: {sample_age_model.filter()}')
        return False
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(db=database)
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
        age_conversions = retrieve_conversions('AgeUnitConversions', 'AgeUnit', DirectAgeUnitID, database=database)
        error_conversions = retrieve_conversions('ErrorFormatConversions', 'ErrorFormat', DirectAgeErrorFormatID, database=database)
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
