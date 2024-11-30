import PyQt6
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6.QtSql import QSqlDatabase

from Functions.Table_classes import set_table, get_columns
# from pyproj import Proj, transform

def drop_virtual_columns(db, tables_affected: list):
    create_savepoint(db)
    for table_info in tables_affected:
        table = table_info[0]
        create_sql = table_info[1]
        table_model = QtS.QSqlTableModel()
        set_table(table_model, table)
        query, virtual, stored, columns = get_columns(db, table)
        if virtual:
            column_str = ', '.join(columns)
            query.exec('PRAGMA foreign_keys=OFF')
            if not query.exec(f'ALTER TABLE {table} RENAME TO {table}_old'):
                if 'already' in query.lastError().text():
                    if not query.exec(f'DROP TABLE {table}_old'):
                        print(f'Error dropping leftover old {table} table: {query.lastError().text()}')
                        rollback_savepoint(db)
                        return
                else:
                    print(f'Error renaming {table} table: {query.lastError().text()}')
                    rollback_savepoint(db)
                    return
            # Select only the stored columns, not the virtual ones
            if not query.exec(create_sql):
                print(f'Error creating new {table} table: {query.lastError().text()}')
                rollback_savepoint(db)
                return
            if not query.exec(f'INSERT INTO {table} SELECT {column_str} FROM {table}_old'):
                print(f'Error copying data from {table} table: {query.lastError().text()}')
                rollback_savepoint(db)
                return
            if not query.exec(f'DROP TABLE {table}_old'):
                print(f'Error dropping old {table} table: {query.lastError().text()}')
                rollback_savepoint(db)
                return
            new_query, new_virtual, new_stored, new_columns = get_columns(db, table)
            if new_columns != columns:
                print(f'Error copying new table {table} columns')
                rollback_savepoint(db)
                return
            query.exec('PRAGMA foreign_keys=ON')

def populate_generated_columns(db):
    create_savepoint(db)
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
    gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec', 'GPSUTMZone',
         'GPSUTMN', 'GPSUTME']]
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

    convert_columns(db, age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id])
    convert_columns(db, elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [elevation_unit_id])
    # convert_gps_columns(gps_unit_affected, gps_format_id)
    convert_columns(db, heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [heightdepth_unit_id])
    convert_columns(db, spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [spotsize_unit_id])
    convert_columns(db, age_error_type_affected, ['ErrorTypeConversions', 'AgeUnitConversions'], ['ErrorType','AgeUnit'], [age_error_type_id, age_unit_id])
    convert_columns(db, ratio_error_type_affected, ['ErrorTypeConversions'], ['ErrorType'], [ratio_error_type_id])
    release_savepoint(db)

def convert_columns(db: QSqlDatabase, affected: list, conversion_table: list, id_header_base: list, selected_id: list):
    if id_header_base[0] in ['AgeUnit', 'DistanceUnit', 'ErrorType']:
        for table_list in affected:
            table = table_list.pop(0)
            if len(conversion_table) > 1:
                table_id_headers = table_list.pop(0)
                table_id_header = table_id_headers[0]
            else:
                table_id_header = table_list.pop(0)
            affected_column_names = table_list

            conversions = retrieve_conversions(db, conversion_table[0], id_header_base[0], selected_id[0])
            if len(conversion_table) > 1:
                age_conversions = retrieve_conversions(db, conversion_table[1], id_header_base[1], selected_id[1])
                generate_age_error_columns(db, affected_column_names, table, table_id_headers, selected_id, conversions, age_conversions)
            else:
                generate_columns(db, affected_column_names, table, table_id_header, selected_id[0], conversions)

def retrieve_conversions(db, conversion_table: str, id_header_base: str, selected_id: int):
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
        rollback_savepoint(db)
        return
    conversions = []
    for row in range(unit_conversion_model.rowCount()):
        conversion = unit_conversion_model.record(row).value(calculation_col)
        from_id = unit_conversion_model.record(row).value(from_id_col)
        conversions.append((from_id, conversion))
    return conversions

def generate_columns(db: QSqlDatabase, affected_column_names: list[str], table: str, table_id_header: str, selected_id: int, conversions: list):
    query = QtS.QSqlQuery(db)
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
            rollback_savepoint(db)
            return

def generate_age_error_columns(db: QSqlDatabase, affected_column_names: list[str], table: str, table_id_headers: list, selected_id: list, err_conversions: list, age_conversions: list):
    table_error_id_header = table_id_headers[0]
    table_age_id_header = table_id_headers[1]
    selected_error_type_id = selected_id[0]
    selected_age_unit_id = selected_id[1]
    query = QtS.QSqlQuery(db)
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
            rollback_savepoint(db)
            return




# if id_header_base in ['DirectionUnit'] or id_header_base in ['GPSFormat']:
#     gps_location_model = QtS.QSqlTableModel()
#     set_table(gps_location_model, 'GPSLocations')
#     for col in range(gps_location_model.columnCount()):
#         if gps_location_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole) == 'CalculatedGPSCoordinates':
#             # If calculated columns exist, drop
#             f'''ALTER TABLE GPSLocations DROP COLUMN CalculatedGPSCoordinates'''
#     gps_format_model = QtS.QSqlTableModel()
#     set_table(gps_format_model, 'GPSFormats')
#     gps_conversion_model = QtS.QSqlTableModel()
#     set_table(gps_conversion_model, 'GPSConversions')
#     direction_conversion_model = QtS.QSqlTableModel()
#     set_table(direction_conversion_model, 'DirectionConversions')
#     selected_gps_format_id = 3
#     selected_direction_unit_id = 1
#     gps_format_abbreviation = gps_format_model.setFilter(f'GPSFormatID={selected_gps_format_id}').record(0).value('GPSFormatAbbreviation')
#
#
#
#
#     pass
#
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

def create_savepoint(db):
    save_query = QtS.QSqlQuery(db)
    if save_query.exec('SAVEPOINT before_alter') is False:
        errtxt = save_query.lastError().text()
        return errtxt

def release_savepoint(db):
    save_query = QtS.QSqlQuery(db)
    if save_query.exec('RELEASE SAVEPOINT before_alter') is False:
        errtxt = save_query.lastError().text()
        return errtxt

def rollback_savepoint(db):
    save_query = QtS.QSqlQuery(db)
    if save_query.exec('ROLLBACK TO before_alter') is False:
        errtxt = save_query.lastError().text()
        return errtxt
