import PyQt6
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from Functions.Settings_manager import settings

import pyproj
import Functions.Create_database as Create_db
from Functions.Table_classes import set_table, get_columns
from Functions.Savepoint_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint
import Functions.GPS_conversions as GPS # gps conversions

def settings_reset():
    tables_affected = [['SampleAges', Create_db.CREATE_SAMPLE_AGE_TABLE], ['UPbAnalyses', Create_db.CREATE_UPBANALYSES_TABLE],
                       ['GPSLocations', Create_db.CREATE_GPS_LOCATIONS_TABLE], ['Samples', Create_db.CREATE_SAMPLES_TABLE],
                       ['Columns', Create_db.CREATE_COLUMNS_TABLE], ['References', Create_db.CREATE_REFERENCES_TABLE]]
    query = QtS.QSqlQuery()
    query.exec('COMMIT')
    query.exec('VACUUM')
    if drop_virtual_columns(tables_affected):
        populate_generated_columns()

def drop_virtual_columns(tables_affected: list, edit_table: str = None):
    create_savepoint('before_drop')
    for table_info in tables_affected:
        table = table_info[0]
        if edit_table is not None and table != edit_table:
            continue
        create_sql = table_info[1]
        query, virtual, stored, columns = get_columns(table)
        if query.lastError().text() != '':
            print(f'Error getting {table} columns: {query.lastError().text()}')
            rollback_savepoint('before_drop')
            return False
        if virtual:
            column_str = ', '.join(columns)
            if not query.exec('PRAGMA foreign_keys=OFF'):
                print(f'Error turning off foreign keys: {query.lastError().text()}')
                rollback_savepoint('before_drop')
                return False
            if not query.exec(f'ALTER TABLE "{table}" RENAME TO {table}_old'):
                if 'already' in query.lastError().text():
                    if not query.exec(f'DROP TABLE {table}_old'):
                        print(f'Error dropping leftover old {table} table: {query.lastError().text()}')
                        rollback_savepoint('before_drop')
                        return False
                    if not query.exec(f'ALTER TABLE "{table}" RENAME TO {table}_old'):
                        print(f'Error renaming {table} table: {query.lastError().text()}')
                        rollback_savepoint('before_drop')
                        return False
                else:
                    print(f'Error renaming {table} table: {query.lastError().text()}')
                    rollback_savepoint('before_drop')
                    return False
            # Select only the stored columns, not the virtual ones
            if not query.exec(create_sql):
                print(f'Error creating new {table} table: {query.lastError().text()}')
                rollback_savepoint('before_drop')
                return False
            if not query.exec(f'INSERT INTO "{table}" SELECT {column_str} FROM {table}_old'):
                print(f'Error copying data from {table} table: {query.lastError().text()}')
                rollback_savepoint('before_drop')
                return False
            if not query.exec(f'DROP TABLE {table}_old'):
                print(f'Error dropping old {table} table: {query.lastError().text()}')
                rollback_savepoint('before_drop')
                return False
            new_query, new_virtual, new_stored, new_columns = get_columns(table)
            if new_columns != columns:
                print(f'Error copying new table {table} columns')
                rollback_savepoint('before_drop')
                return False
            if not query.exec('PRAGMA foreign_keys=ON'):
                print(f'Error turning on foreign keys: {query.lastError().text()}')
                rollback_savepoint('before_drop')
                return False
    release_savepoint('before_drop')
    return True

def populate_generated_columns():
    create_savepoint('before_populate')
    # Retrieve the settings
    age_unit_id = settings.value('age_unit_id') #default to Ma
    elevation_unit_id = settings.value('elevation_unit_id') # default to m
    gps_format_id = settings.value('gps_format_id') # default to DD +/-
    heightdepth_unit_id = settings.value('heightdepth_unit_id') # default to m
    spotsize_unit_id = settings.value('spotsize_unit_id') # default to um
    age_error_format_id = settings.value('age_error_format_id') # default to 1 sigma abs
    ratio_error_format_id = settings.value('ratio_error_format_id') # default to 1 sigma abs
    concordance_format_id = settings.value('concordance_format_id') # default conc ratio
    reference_format = settings.value('reference_format')

    # Affected list format: [[table1, [unit/type ID headers], column1, column2, ...], [table2, [unit/type ID headers], column1, column2, ...], ...]
    # Save age errors to handle both age unit and age error type
    age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge'],
                         ['UPbAnalyses', 'AgeUnitID', '207Pb/206PbAge', '206Pb/238UAge', '207Pb/235UAge', '208Pb/232ThAge', 'BestAge']]
    elevation_unit_affected = [['GPSLocations', 'GPSElevUnitID', 'GPSElev', 'GPSElevError']]
    gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLocationDisplay']]
    heightdepth_unit_affected = [['Samples', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError'], ['Columns', 'ColumnTotalHeightDepthUnitID', 'ColumnTotalHeightDepth']]
    spotsize_unit_affected = [['UPbAnalyses', 'SpotSizeUnitID', 'SpotSize']]
    concordance_format_affected = [['UPbAnalyses', 'ConcordanceFormatID', 'Concordance']]
    upb_analyses_model = QtS.QSqlTableModel()
    set_table(upb_analyses_model, 'UPbAnalyses')
    affected_upb_ratio = ['UPbAnalyses', 'RatioErrorFormatID']
    affected_upb_age = ['UPbAnalyses', ['AgeErrorFormatID','AgeUnitID']]
    for col in range(upb_analyses_model.columnCount()):
        if upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole).endswith(
                'AgeError'):
            affected_upb_age.append(
                upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
        elif upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                             QtC.Qt.ItemDataRole.DisplayRole).endswith('Error'):
            affected_upb_ratio.append(
                upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
    age_error_format_affected = [['SampleAges', ['DirectAgeErrorFormatID','DirectAgeUnitID'], 'DirectAgeError'], affected_upb_age]
    ratio_error_format_affected = [affected_upb_ratio]

    # Convert the columns and catch any errors
    output = convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id])
    if output == "error":
        return
    output = convert_columns(elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [elevation_unit_id])
    if output == "error":
        return
    output = convert_columns(gps_unit_affected, ['GPSFormatConversions'], ['GPSFormat'], [gps_format_id])
    if output == "error":
        return
    output = convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [heightdepth_unit_id])
    if output == "error":
        return
    output = convert_columns(spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [spotsize_unit_id])
    if output == "error":
        return
    output = convert_columns(concordance_format_affected, ['ConcordanceFormatConversions'], ['ConcordanceFormat'], [concordance_format_id])
    if output == "error":
        return
    output = convert_columns(age_error_format_affected, ['ErrorFormatConversions', 'AgeUnitConversions'], ['ErrorFormat','AgeUnit'], [age_error_format_id, age_unit_id])
    if output == "error":
        return
    output = convert_columns(ratio_error_format_affected, ['ErrorFormatConversions'], ['ErrorFormat'], [ratio_error_format_id])
    if output == "error":
        return
    output = generate_reference_column('References', 'ReferenceID', reference_format)
    if output == "error":
        return
    output = generate_age_display_column('SampleAges', 'SampleAgeID')
    if output == "error":
        return
    release_savepoint('before_populate')

def convert_columns(affected: list, conversion_table: list, id_header_base: list, selected_id: list):
    if id_header_base[0] in ['AgeUnit', 'DistanceUnit', 'ErrorFormat', 'GPSFormat', 'ConcordanceFormat']:
        for table_list in affected:
            table = table_list.pop(0)
            if len(conversion_table) > 1:
                table_id_headers = table_list.pop(0)
                table_id_header = table_id_headers[0]
            else:
                table_id_header = table_list.pop(0)
            affected_column_names = table_list

            conversions = retrieve_conversions(conversion_table[0], id_header_base[0], selected_id[0])
            if conversions == "error":
                return "error"
            if len(conversion_table) > 1:
                age_conversions = retrieve_conversions(conversion_table[1], id_header_base[1], selected_id[1])
                if age_conversions == "error":
                    return "error"
                output = generate_age_error_columns(affected_column_names, table, table_id_headers, selected_id, conversions, age_conversions)
                if output == "error":
                    return "error"
            elif id_header_base[0] == 'GPSFormat':
                output = generate_gps_column(affected_column_names, table, table_id_header, selected_id[0], conversions)
                if output == "error":
                    return "error"
            else:
                output = generate_columns(affected_column_names, table, table_id_header, selected_id[0], conversions)
                if output == "error":
                    return "error"

def retrieve_conversions(conversion_table: str, id_header_base: str, selected_id: int):
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
        print('Calculation and from columns not found')
        rollback_savepoint('before_populate')
        return "error"
    conversions = []
    for row in range(unit_conversion_model.rowCount()):
        conversion = unit_conversion_model.record(row).value(calculation_col)
        from_id = unit_conversion_model.record(row).value(from_id_col)
        conversions.append((from_id, conversion))
    return conversions

def generate_columns(affected_column_names: list[str], table: str, table_id_header: str, selected_id: int, conversions: list):
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
            rollback_savepoint('before_populate')
            return "error"

def generate_age_display_column(table: str, table_id_header: str):
    query = QtS.QSqlQuery()
    column = 'SampleAgeDisplay'
    sql_alter = f'ALTER TABLE "{table}" ADD COLUMN {column} TEXT AS (ifnull(CalculatedDirectAge, "") || "±" || ifnull(CalculatedDirectAgeError, "") || ", " || ifnull(CalculatedOldestDirectAge, "") || "-" || ifnull(CalculatedYoungestDirectAge, "") || ", " || ifnull(OldestAgeID, "") || "-" || ifnull(YoungestAgeID, ""))'
    if not query.exec(sql_alter):
        print(f'Error updating SampleAgeDisplay: {query.lastError().text()}')
        rollback_savepoint('before_populate')
        return "error"

def generate_age_error_columns(affected_column_names: list[str], table: str, table_id_headers: list, selected_id: list, err_conversions: list, age_conversions: list):
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
        # print(sql_alter)
        if not query.exec(sql_alter):
            print(f'Error adding the calculated column Calculated{err_column}: {query.lastError().text()}')
            rollback_savepoint('before_populate')
            return "error"

def generate_gps_column(affected_column_names: list[str], table: str, table_id_header: str, selected_id: int, conversions: list):
    query = QtS.QSqlQuery()
    column = 'GPSLocationConverted'
    variables = ['GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec',
                 'GPSLonDirectionID', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME', 'deg_symbol']
    modules = ['GPS', 'pyproj']
    global_vars = {name: globals()[name] for name in modules}
    gps_model = QtS.QSqlTableModel()
    set_table(gps_model, table)
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
        local_vars = {name: locals()[name] for name in variables}

        for conversion in conversions:
            if conversion[0] == gps_format_id:
                gps_code = conversion[1]
                exec(gps_code, global_vars, local_vars)
                gps_display = local_vars.get('converted')
                if not query.exec(f'UPDATE {table} SET {column}="{gps_display}" WHERE "GPSLocationID"={gps_id}'):
                    print(f'Error updating GPSLocationDisplay: {query.lastError().text()}')
                    rollback_savepoint('before_populate')
                    return "error"
                break

def generate_reference_column(table: str, table_id_header: str, constructor: str):
    query = QtS.QSqlQuery()
    column = 'ReferenceDisplay'

    sql_alter = f'ALTER TABLE "{table}" ADD COLUMN {column} TEXT AS {constructor} VIRTUAL'
    if not query.exec(sql_alter):
        print(f'Error updating ReferenceDisplay: {query.lastError().text()}')
        rollback_savepoint('before_populate')
        return "error"

def update_generated_columns(table: str):
    if table == 'GPSLocations':
        # Drop the virtual columns
        tables_affected = [[['GPSLocations', Create_db.CREATE_GPS_LOCATIONS_TABLE]]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        elevation_unit_id = settings.value('elevation_unit_id')
        gps_format_id = settings.value('gps_format_id')
        # Convert the columns and catch any errors
        elevation_unit_affected = [['GPSLocations', 'GPSElevUnitID', 'GPSElev', 'GPSElevError']]
        gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLocationDisplay']]
        output = convert_columns(elevation_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                                 [elevation_unit_id])
        if output == "error":
            return
        output = convert_columns(gps_unit_affected, ['GPSFormatConversions'], ['GPSFormat'], [gps_format_id])
        if output == "error":
            return
        release_savepoint('before_populate')
        return True
    elif table == 'SampleAges':
        # Drop the virtual columns
        tables_affected = [['SampleAges', Create_db.CREATE_SAMPLE_AGE_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        age_unit_id = settings.value('age_unit_id')
        age_error_type_id = settings.value('age_error_type_id')
        # Convert the columns and catch any errors
        age_unit_affected = [['SampleAges', 'DirectAgeUnitID', 'DirectAge', 'OldestDirectAge', 'YoungestDirectAge']]
        age_error_type_affected = [['SampleAges', ['DirectAgeErrorFormatID','DirectAgeUnitID'], 'DirectAgeError']]
        output = convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id])
        if output == "error":
            return
        output = convert_columns(age_error_type_affected, ['ErrorFormatConversions', 'AgeUnitConversions'], ['ErrorFormat','AgeUnit'],
                                 [age_error_type_id, age_unit_id])
        if output == "error":
            return
        release_savepoint('before_populate')
        return True
    elif table == 'UPbAnalyses':
        # Drop the virtual columns
        tables_affected = [['UPbAnalyses', Create_db.CREATE_UPBANALYSES_TABLE]]
        drop_virtual_columns(tables_affected, table)
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
        output = convert_columns(age_unit_affected, ['AgeUnitConversions'], ['AgeUnit'], [age_unit_id])
        if output == "error":
            return
        output = convert_columns(spotsize_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'],
                                 [spotsize_unit_id])
        if output == "error":
            return
        output = convert_columns(concordance_format_affected, ['ConcordanceFormatConversions'], ['ConcordanceFormat'],
                                 [concordance_format_id])
        if output == "error":
            return
        output = convert_columns(age_error_format_affected, ['ErrorFormatConversions', 'AgeUnitConversions'],
                                 ['ErrorFormat', 'AgeUnit'], [age_error_format_id, age_unit_id])
        if output == "error":
            return
        output = convert_columns(ratio_error_format_affected, ['ErrorFormatConversions'], ['ErrorFormat'],
                                 [ratio_error_format_id])
        if output == "error":
            return
        release_savepoint('before_populate')
        return True
    elif table == 'References':
        # Drop the virtual columns
        tables_affected = [['References', Create_db.CREATE_REFERENCES_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        reference_format = settings.value('reference_format')
        # Convert the columns and catch any errors
        output = generate_reference_column(table, 'ReferenceID', reference_format)
        if output == "error":
            return
        release_savepoint('before_populate')
        return True
    elif table == 'Samples':
        # Drop the virtual columns
        tables_affected = [['Samples', Create_db.CREATE_SAMPLES_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        heightdepth_unit_id = settings.value('heightdepth_unit_id')
        # Convert the columns and catch any errors
        heightdepth_unit_affected = [['Samples', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError']]
        output = convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [heightdepth_unit_id])
        if output == "error":
            return
        release_savepoint('before_populate')
        return True
    elif table == 'Columns':
        # Drop the virtual columns
        tables_affected = [['Columns', Create_db.CREATE_COLUMNS_TABLE]]
        drop_virtual_columns(tables_affected, table)
        create_savepoint('before_populate')
        # Retrieve the settings
        heightdepth_unit_id = settings.value('heightdepth_unit_id')
        column_total_heightdepth_unit_id = settings.value('column_total_heightdepth_unit_id')
        # Convert the columns and catch any errors
        heightdepth_unit_affected = [['Columns', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError']]
        column_total_heightdepth_unit_affected = [['Columns', 'ColumnTotalHeightDepthUnitID', 'ColumnTotalHeightDepth']]
        output = convert_columns(heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [heightdepth_unit_id])
        if output == "error":
            return
        output = convert_columns(column_total_heightdepth_unit_affected, ['DistanceUnitConversions'], ['DistanceUnit'], [column_total_heightdepth_unit_id])
        if output == "error":
            return
        release_savepoint('before_populate')
        return True
    else:
        return