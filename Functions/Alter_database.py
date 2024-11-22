import PyQt6
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from Functions.Table_classes import set_table
from pyproj import Proj, transform

# Affected list format: [table, column1, column2, ...]
age_unit_affected = [['SampleAges','DirectAge','DirectAgeError','OldestDirectAge','YoungestDirectAge'],['UPbAnalyses', '207Pb/206PbAge', '207Pb/206PbAgeError', '206Pb/238UAge', '206Pb/238UAgeError', '207Pb/235UAge', '207Pb/235UAgeError', '208Pb/232ThAge', '208Pb/232ThAgeError']]
elevation_unit_affected = [['GPSLocations', 'Elev', 'ElevError']]
gps_unit_affected = [['GPSLocations', 'GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec', 'GPSUTMZone', 'GPSUTMN', 'GPSUTME']]
heightdepth_unit_affected = [['Samples', 'HeightDepth', 'HeightDepthError'],['Columns', 'ColumnTotalHeightDepth']]
spotsize_unit_affected = [['UPbAnalyses', 'SpotSize']]
upb_analyses_model = QtS.QSqlTableModel()
set_table(upb_analyses_model, 'UPbAnalyses')
affected_upb = ['UPbAnalyses']
for col in range(upb_analyses_model.columnCount()):
    if upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole).endswith('Error'):
        affected_upb.append(upb_analyses_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole))
age_error_type_affected = [['SampleAges', 'DirectAgeError'], affected_upb]

def convert_columns(affected: list, conversion_table: str, id_header_base: str, selected_id: int):
    if id_header_base in ['AgeUnit', 'DistanceUnit', 'ErrorType']:
        for table_list in affected:
            table = table_list.pop(0)
            affected_column_names = table_list
            table_model = QtS.QSqlTableModel()
            set_table(table_model, table)
            # Get column names for SampleAges table and check if calculated ones exist
            calculated_column_names = ['Calculated' + name for name in affected_column_names]
            for col in range(table_model.columnCount()):
                if table_model.headerData(col, QtC.Qt.Orientation.Horizontal,
                                          QtC.Qt.ItemDataRole.DisplayRole) in calculated_column_names:
                    # If calculated columns exist, drop
                    f'''ALTER TABLE {table} DROP COLUMN {table_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole)}'''
        unit_conversion_model = QtS.QSqlTableModel()
        set_table(unit_conversion_model, conversion_table)
        unit_conversion_model.setFilter(f'To{id_header_base}ID={selected_id}')
        conversions = []
        for row in range(unit_conversion_model.rowCount()):
            conversion = unit_conversion_model.record(row).value(f'{id_header_base}Calculation')
            from_id = unit_conversion_model.record(row).value(f'From{id_header_base}ID')
            conversions.append((from_id, conversion))
        generate_columns(affected_column_names, table, f'{id_header_base}ID', selected_id, conversions)
    elif id_header_base in ['DirectionUnit'] or id_header_base in ['GPSFormat']:
        gps_location_model = QtS.QSqlTableModel()
        set_table(gps_location_model, 'GPSLocations')
        for col in range(gps_location_model.columnCount()):
            if gps_location_model.headerData(col, QtC.Qt.Orientation.Horizontal, QtC.Qt.ItemDataRole.DisplayRole) == 'CalculatedCoordinates':
                # If calculated columns exist, drop
                f'''ALTER TABLE GPSLocations DROP COLUMN CalculatedCoordinates'''
        gps_format_model = QtS.QSqlTableModel()
        set_table(gps_format_model, 'GPSFormats')
        gps_conversion_model = QtS.QSqlTableModel()
        set_table(gps_conversion_model, 'GPSConversions')
        direction_conversion_model = QtS.QSqlTableModel()
        set_table(direction_conversion_model, 'DirectionConversions')
        selected_gps_format_id = 3
        selected_direction_unit_id = 1
        gps_format_abbreviation = gps_format_model.setFilter(f'GPSFormatID={selected_gps_format_id}').record(0).value('GPSFormatAbbreviation')




        pass

def convert_gps_columns(selected_gps_format_id: int, selected_direction_unit_id: int):
    query = QtS.QSqlQuery()
    sql_alter = f'ALTER TABLE GPSLocations ADD COLUMN CalculatedCoordinates REAL AS (CASE'
    if selected_gps_format_id == 0:
        # Selected DD
        sql_alter += f'''
            WHEN GPSFormatID={selected_gps_format_id} THEN'''
        if selected_direction_unit_id == 0:
            # Selected +/-
            sql_alter += f'''
                CASE
                    WHEN (GPSLatDirectionID IS NULL AND GPSLonDirectionID IS NULL) OR (GPSLatDirectionID=0 AND GPSLonDirectionID=2) THEN GPSLatDeg  || "," || GPSLonDeg
                    WHEN GPSLatDirectionID=1 AND GPSLonDirectionID=3 THEN GPSLatDeg, -GPSLonDeg
                    WHEN GPSLatDirectionID=2 AND GPSLonDirectionID=0 THEN -GPSLatDeg, GPSLonDeg
                    WHEN GPSLatDirectionID=3 AND GPSLonDirectionID=1 THEN -GPSLatDeg, -GPSLonDeg
                END'''
        elif selected_direction_unit_id == 1:
            # Selected NSEW
            sql_alter += f'''
                CASE
                    WHEN GPSLatDirectionID=0 AND GPSLonDirectionID=2 THEN GPSLatDeg || " N," ||  GPSLonDeg || " E"
                    WHEN GPSLatDirectionID=1 AND GPSLonDirectionID=2 THEN GPSLatDeg || " S," ||  GPSLonDeg || " E"
                    WHEN GPSLatDirectionID=0 AND GPSLonDirectionID=3 THEN GPSLatDeg || " N," ||  GPSLonDeg || " W"
                    WHEN GPSLatDirectionID=1 AND GPSLonDirectionID=3 THEN GPSLatDeg || " S," ||  GPSLonDeg || " W"
                    WHEN GPSLatDirectionID IS NULL AND GPSLonDirectionID IS NULL THEN
                        CASE
                            WHEN GPSLatDeg > 0 AND GPSLonDeg > 0 THEN GPSLatDeg || " N," ||  GPSLonDeg || " E"
                            WHEN GPSLatDeg < 0 AND GPSLonDeg > 0 THEN GPSLatDeg || " S," ||  GPSLonDeg || " E"
                            WHEN GPSLatDeg > 0 AND GPSLonDeg < 0 THEN GPSLatDeg || " N," ||  GPSLonDeg || " W"
                            WHEN GPSLatDeg < 0 AND GPSLonDeg < 0 THEN GPSLatDeg || " S," ||  GPSLonDeg || " W"
                        END
                END'''




def convert_gps(GPSColumns: list, selected_gps_id: int, selected_dir_id: int, conversions: list):
    GPSLatDeg = GPSColumns[0]
    GPSLatMin = GPSColumns[1]
    GPSLatSec = GPSColumns[2]
    GPSLatDirectionID = GPSColumns[3]
    GPSLonDeg = GPSColumns[4]
    GPSLonMin = GPSColumns[5]
    GPSLonSec = GPSColumns[6]
    GPSLonDirectionID = GPSColumns[7]
    GPSUTMZone = GPSColumns[8]
    GPSUTMN = GPSColumns[9]
    GPSUTME = GPSColumns[10]

    # Convert direction to positive and negative
    direction_unit_table = QtS.QSqlTableModel()
    set_table(direction_unit_table, 'DirectionUnits')
    S_id = direction_unit_table.setFilter('DirectionUnitAbbreviation="S"').record(0).value('DirectionUnitID')
    S_conversion = direction_unit_table.setFilter('DirectionUnitAbbreviation="S"').record(0).value('DirectionUnitConversion')
    W_id = direction_unit_table.setFilter('DirectionUnitAbbreviation="W"').record(0).value('DirectionUnitID')
    W_conversion = direction_unit_table.setFilter('DirectionUnitAbbreviation="W"').record(0).value('DirectionUnitConversion')
    gps_format_table = QtS.QSqlTableModel()
    set_table(gps_format_table, 'GPSFormats')
    DD_id = gps_format_table.setFilter('GPSFormatAbbreviation="DD"').record(0).value('GPSFormatID')
    DDM_id = gps_format_table.setFilter('GPSFormatAbbreviation="DDM"').record(0).value('GPSFormatID')
    DMS_id = gps_format_table.setFilter('GPSFormatAbbreviation="DMS"').record(0).value('GPSFormatID')
    UTM_id = gps_format_table.setFilter('GPSFormatAbbreviation="UTM"').record(0).value('GPSFormatID')
    gps_conversion_table = QtS.QSqlTableModel()
    set_table(gps_conversion_table, 'GPSConversions')

    if GPSLatDirectionID == S_id:
        GPSLatDeg = S_conversion.replace('x', f'{GPSLatDeg}')
        GPSLatMin = S_conversion.replace('x', f'{GPSLatMin}')
        GPSLatSec = S_conversion.replace('x', f'{GPSLatSec}')
    if GPSLonDirectionID == W_id:
        GPSLonDeg = W_conversion.replace('x', f'{GPSLonDeg}')
        GPSLonMin = W_conversion.replace('x', f'{GPSLonMin}')
        GPSLonSec = W_conversion.replace('x', f'{GPSLonSec}')
    for conversion in conversions:
        from_id = conversion[0]





def generate_columns(affected_column_names: list[str], table: str, id_header: str, selected_id: int, conversions: list):
    query = QtS.QSqlQuery()
    replace_x_tables = ['SampleAges', 'UPbAnalyses', ]
    for column in affected_column_names:
        sql_alter = f'ALTER TABLE {table} ADD COLUMN Calculated{column} REAL AS (CASE'
        sql_alter += f' WHEN {id_header}={selected_id} THEN {column}'
        for conversion in conversions:
            if table == 'SampleAges':
                calculation = conversion[1].replace('x', f'DirectAge')
            calculation = conversion[1].replace('x', column)
            sql_alter += f' WHEN {id_header}={conversion[0]} THEN ({calculation})'
        sql_alter += ' END)'
        if not query.exec(sql_alter):
            # Error handling
            print(query.lastError().text())
