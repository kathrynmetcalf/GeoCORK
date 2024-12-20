import PyQt6
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
from PyQt6.QtSql import QSqlDatabase

import Functions.Create_database as Create_db
from Functions.Table_classes import set_table, get_columns
from Functions.DatabaseManager import create_savepoint, release_savepoint, rollback_savepoint
# from pyproj import Proj, transform

# todo: test new settings_reset function
def settings_reset(window: QtW.QMainWindow | QtW.QDialog):
    tables_affected = [['SampleAges', Create_db.CREATE_SAMPLE_AGE_TABLE], ['UPbAnalyses', Create_db.CREATE_UPBANALYSES_TABLE],
                       ['GPSLocations', Create_db.CREATE_GPS_LOCATIONS_TABLE], ['Samples', Create_db.CREATE_SAMPLES_TABLE],
                       ['Columns', Create_db.CREATE_COLUMNS_TABLE]]
    drop_virtual_columns(tables_affected, window)
    populate_generated_columns(window)

def drop_virtual_columns(tables_affected: list, window: QtW.QMainWindow | QtW.QDialog):
    create_savepoint('before_drop', window)
    for table_info in tables_affected:
        table = table_info[0]
        create_sql = table_info[1]
        table_model = QtS.QSqlTableModel()
        set_table(table_model, table)
        query, virtual, stored, columns = get_columns(table)
        if virtual:
            column_str = ', '.join(columns)
            query.exec('PRAGMA foreign_keys=OFF')
            if not query.exec(f'ALTER TABLE {table} RENAME TO {table}_old'):
                if 'already' in query.lastError().text():
                    if not query.exec(f'DROP TABLE {table}_old'):
                        print(f'Error dropping leftover old {table} table: {query.lastError().text()}')
                        rollback_savepoint('before_drop', window)
                        return
                else:
                    print(f'Error renaming {table} table: {query.lastError().text()}')
                    rollback_savepoint('before_drop', window)
                    return
            # Select only the stored columns, not the virtual ones
            if not query.exec(create_sql):
                print(f'Error creating new {table} table: {query.lastError().text()}')
                rollback_savepoint('before_drop', window)
                return
            if not query.exec(f'INSERT INTO {table} SELECT {column_str} FROM {table}_old'):
                print(f'Error copying data from {table} table: {query.lastError().text()}')
                rollback_savepoint('before_drop', window)
                return
            if not query.exec(f'DROP TABLE {table}_old'):
                print(f'Error dropping old {table} table: {query.lastError().text()}')
                rollback_savepoint('before_drop', window)
                return
            new_query, new_virtual, new_stored, new_columns = get_columns(table)
            if new_columns != columns:
                print(f'Error copying new table {table} columns')
                rollback_savepoint('before_drop', window)
                return
            query.exec('PRAGMA foreign_keys=ON')

def populate_generated_columns(window: QtW.QMainWindow | QtW.QDialog):
    create_savepoint('before_populate', window)
    # Default units and types
    age_unit_id = 2
    elevation_unit_id = 2
    gps_format_id = 1
    heightdepth_unit_id = 2
    spotsize_unit_id = 5
    age_error_type_id = 1
    ratio_error_type_id = 3

    # Eventually, these will be user-selected

    # Affected list format: [table, unit/type ID header, column1, column2, ...]
    # Save age errors to handle both age unit and age error type
    age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge'],
                         ['UPbAnalyses', 'AgeUnitID', '207Pb/206PbAge', '206Pb/238UAge', '207Pb/235UAge', '208Pb/232ThAge']]
    elevation_unit_affected = [['GPSLocations', 'GPSElevUnitID', 'GPSElev', 'GPSElevError']]
    gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLocationDisplay']]
    heightdepth_unit_affected = [['Samples', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError'], ['Columns', 'ColumnTotalHeightDepthUnitID', 'ColumnTotalHeightDepth']]
    spotsize_unit_affected = [['UPbAnalyses', 'SpotSizeUnitID', 'SpotSize']]
    upb_analyses_model = QtS.QSqlTableModel()
    set_table(upb_analyses_model, 'UPbAnalyses')
    affected_upb_ratio = ['UPbAnalyses', 'RatioErrorTypeID']
    affected_upb_age = ['UPbAnalyses', ['AgeErrorTypeID','AgeUnitID']]
    for col in range(upb_analyses_model.columnCount()):
        if upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole).endswith(
                'AgeError'):
            affected_upb_age.append(
                upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
        elif upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                             QtC.Qt.ItemDataRole.DisplayRole).endswith('Error'):
            affected_upb_ratio.append(
                upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
    age_error_type_affected = [['SampleAges', ['DirectAgeErrorTypeID','DirectAgeUnitID'], 'DirectAgeError'], affected_upb_age]
    ratio_error_type_affected = [affected_upb_ratio]

    convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id], window)
    convert_columns(elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [elevation_unit_id], window)
    convert_columns(gps_unit_affected, ['GPSFormatConversions'], ['GPSFormat'], [gps_format_id], window)
    convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [heightdepth_unit_id], window)
    convert_columns(spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [spotsize_unit_id], window)
    convert_columns(age_error_type_affected, ['ErrorTypeConversions', 'AgeUnitConversions'], ['ErrorType','AgeUnit'], [age_error_type_id, age_unit_id], window)
    convert_columns(ratio_error_type_affected, ['ErrorTypeConversions'], ['ErrorType'], [ratio_error_type_id], window)
    release_savepoint('before_populate', window)

def convert_columns(affected: list, conversion_table: list, id_header_base: list, selected_id: list, window: QtW.QMainWindow | QtW.QDialog):
    if id_header_base[0] in ['AgeUnit', 'DistanceUnit', 'ErrorType', 'GPSFormat']:
        for table_list in affected:
            table = table_list.pop(0)
            if len(conversion_table) > 1:
                table_id_headers = table_list.pop(0)
                table_id_header = table_id_headers[0]
            else:
                table_id_header = table_list.pop(0)
            affected_column_names = table_list

            conversions = retrieve_conversions(conversion_table[0], id_header_base[0], selected_id[0], window)
            if len(conversion_table) > 1:
                age_conversions = retrieve_conversions(conversion_table[1], id_header_base[1], selected_id[1], window)
                generate_age_error_columns(affected_column_names, table, table_id_headers, selected_id, conversions, age_conversions, window)
            elif id_header_base[0] == 'GPSFormat':
                generate_gps_column(affected_column_names, table, table_id_header, selected_id[0], conversions, window)
            else:
                generate_columns(affected_column_names, table, table_id_header, selected_id[0], conversions, window)

def retrieve_conversions(conversion_table: str, id_header_base: str, selected_id: int, window: QtW.QMainWindow | QtW.QDialog):
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
        if 'From' in unit_conversion_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                                      QtC.Qt.ItemDataRole.DisplayRole):
            from_id_col = col
    if calculation_col is type(str) or from_id_col is type(str):
        # Error handling
        print('Calculation and from columns not found')
        rollback_savepoint('before_populate', window)
        return
    conversions = []
    for row in range(unit_conversion_model.rowCount()):
        conversion = unit_conversion_model.record(row).value(calculation_col)
        from_id = unit_conversion_model.record(row).value(from_id_col)
        conversions.append((from_id, conversion))
    return conversions

def generate_columns(affected_column_names: list[str], table: str, table_id_header: str, selected_id: int, conversions: list, window: QtW.QMainWindow | QtW.QDialog):
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
            sql_alter += f' WHEN {table_id_header}={conversion[0]} THEN ({calculation})'
        sql_alter += ' END) VIRTUAL'
        # print(sql_alter)
        if not query.exec(sql_alter):
            print(f'Error adding the calculated column Calculated{column}: {query.lastError().text()}')
            rollback_savepoint('before_populate', window)
            return

def generate_age_error_columns(affected_column_names: list[str], table: str, table_id_headers: list, selected_id: list, err_conversions: list, age_conversions: list, window: QtW.QMainWindow | QtW.QDialog):
    table_error_id_header = table_id_headers[0]
    table_age_id_header = table_id_headers[1]
    selected_error_type_id = selected_id[0]
    selected_age_unit_id = selected_id[1]
    query = QtS.QSqlQuery()
    for err_column in affected_column_names:
        if '/' in err_column:
            calc_column_name = f'"Calculated{err_column}"'
            err_column = f'"{err_column}"'
        else:
            calc_column_name = f'Calculated{err_column}'
        sql_alter = f'ALTER TABLE {table} ADD COLUMN {calc_column_name} REAL AS (CASE'
        sql_alter += f' WHEN {table_age_id_header}={selected_age_unit_id} AND {table_error_id_header}={selected_error_type_id} THEN {err_column}'
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
        # print(sql_alter)
        if not query.exec(sql_alter):
            print(f'Error adding the calculated column Calculated{err_column}: {query.lastError().text()}')
            rollback_savepoint('before_populate', window)
            return

def generate_gps_column(affected_column_names: list[str], table: str, table_id_header: str, selected_id: int, conversions: list, window: QtW.QMainWindow | QtW.QDialog):
    query = QtS.QSqlQuery()
    column = 'GPSLocationDisplay'
    gps_model = QtS.QSqlTableModel()
    set_table(gps_model, table)
    for row in range(gps_model.rowCount()):
        gps_id = gps_model.record(row).value(table_id_header)
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

        for conversion in conversions:
            if conversion[0] == gps_id:
                gps_code = conversion[1]
                gps_display = eval(gps_code)
                if not query.exec(f'UPDATE {table} SET {column}="{gps_display}" WHERE {table_id_header}={gps_id}'):
                    print(f'Error updating GPSLocationDisplay: {query.lastError().text()}')
                    rollback_savepoint('before_populate', window)
                    return


# def convert_gps_columns(selected_gps_format_id: int, selected_direction_unit_id: int):
#     query = QtS.QSqlQuery()
#     sql_alter = f'ALTER TABLE GPSLocations ADD COLUMN CalculatedGPSCoordinates REAL AS (CASE'
#     if selected_gps_format_id == 0:
#         # Selected DD
#         sql_alter += f'''
#             WHEN GPSFormatID={selected_gps_format_id} THEN'''
#         if selected_direction_unit_id == 0:
#             # Selected +/-
#             sql_alter += f'''
#                 CASE
#                     WHEN (GPSLatDirectionID IS NULL AND GPSLonDirectionID IS NULL) OR (GPSLatDirectionID=0 AND GPSLonDirectionID=2) THEN GPSLatDeg  || "," || GPSLonDeg
#                     WHEN GPSLatDirectionID=1 AND GPSLonDirectionID=3 THEN GPSLatDeg, -GPSLonDeg
#                     WHEN GPSLatDirectionID=2 AND GPSLonDirectionID=0 THEN -GPSLatDeg, GPSLonDeg
#                     WHEN GPSLatDirectionID=3 AND GPSLonDirectionID=1 THEN -GPSLatDeg, -GPSLonDeg
#                 END'''
#         elif selected_direction_unit_id == 1:
#             # Selected NSEW
#             sql_alter += f'''
#                 CASE
#                     WHEN GPSLatDirectionID=0 AND GPSLonDirectionID=2 THEN GPSLatDeg || " N," ||  GPSLonDeg || " E"
#                     WHEN GPSLatDirectionID=1 AND GPSLonDirectionID=2 THEN GPSLatDeg || " S," ||  GPSLonDeg || " E"
#                     WHEN GPSLatDirectionID=0 AND GPSLonDirectionID=3 THEN GPSLatDeg || " N," ||  GPSLonDeg || " W"
#                     WHEN GPSLatDirectionID=1 AND GPSLonDirectionID=3 THEN GPSLatDeg || " S," ||  GPSLonDeg || " W"
#                     WHEN GPSLatDirectionID IS NULL AND GPSLonDirectionID IS NULL THEN
#                         CASE
#                             WHEN GPSLatDeg > 0 AND GPSLonDeg > 0 THEN GPSLatDeg || " N," ||  GPSLonDeg || " E"
#                             WHEN GPSLatDeg < 0 AND GPSLonDeg > 0 THEN GPSLatDeg || " S," ||  GPSLonDeg || " E"
#                             WHEN GPSLatDeg > 0 AND GPSLonDeg < 0 THEN GPSLatDeg || " N," ||  GPSLonDeg || " W"
#                             WHEN GPSLatDeg < 0 AND GPSLonDeg < 0 THEN GPSLatDeg || " S," ||  GPSLonDeg || " W"
#                         END
#                 END'''
#
#
#

# def convert_gps(GPSColumns: list, selected_gps_id: int, selected_dir_id: int, conversions: list):
#     GPSLatDeg = GPSColumns[0]
#     GPSLatMin = GPSColumns[1]
#     GPSLatSec = GPSColumns[2]
#     GPSLatDirectionID = GPSColumns[3]
#     GPSLonDeg = GPSColumns[4]
#     GPSLonMin = GPSColumns[5]
#     GPSLonSec = GPSColumns[6]
#     GPSLonDirectionID = GPSColumns[7]
#     GPSUTMZone = GPSColumns[8]
#     GPSUTMN = GPSColumns[9]
#     GPSUTME = GPSColumns[10]
#
#     # Convert direction to positive and negative
#     direction_unit_table = QtS.QSqlTableModel()
#     set_table(direction_unit_table, 'DirectionUnits')
#     S_id = direction_unit_table.setFilter('DirectionUnitAbbreviation="S"').record(0).value('DirectionUnitID')
#     S_conversion = direction_unit_table.setFilter('DirectionUnitAbbreviation="S"').record(0).value('DirectionUnitConversion')
#     W_id = direction_unit_table.setFilter('DirectionUnitAbbreviation="W"').record(0).value('DirectionUnitID')
#     W_conversion = direction_unit_table.setFilter('DirectionUnitAbbreviation="W"').record(0).value('DirectionUnitConversion')
#     gps_format_table = QtS.QSqlTableModel()
#     set_table(gps_format_table, 'GPSFormats')
#     DD_id = gps_format_table.setFilter('GPSFormatAbbreviation="DD"').record(0).value('GPSFormatID')
#     DDM_id = gps_format_table.setFilter('GPSFormatAbbreviation="DDM"').record(0).value('GPSFormatID')
#     DMS_id = gps_format_table.setFilter('GPSFormatAbbreviation="DMS"').record(0).value('GPSFormatID')
#     UTM_id = gps_format_table.setFilter('GPSFormatAbbreviation="UTM"').record(0).value('GPSFormatID')
#     gps_conversion_table = QtS.QSqlTableModel()
#     set_table(gps_conversion_table, 'GPSConversions')
#
#     if GPSLatDirectionID == S_id:
#         GPSLatDeg = S_conversion.replace('x', f'{GPSLatDeg}')
#         GPSLatMin = S_conversion.replace('x', f'{GPSLatMin}')
#         GPSLatSec = S_conversion.replace('x', f'{GPSLatSec}')
#     if GPSLonDirectionID == W_id:
#         GPSLonDeg = W_conversion.replace('x', f'{GPSLonDeg}')
#         GPSLonMin = W_conversion.replace('x', f'{GPSLonMin}')
#         GPSLonSec = W_conversion.replace('x', f'{GPSLonSec}')
#     for conversion in conversions:
#         from_id = conversion[0]
#
#
#
#
