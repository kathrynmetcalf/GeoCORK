import PyQt6
from PyQt6 import QtSql as QtS
import Functions.Create_database as Create_db
from Functions.Database_manager import SavepointManager, create_savepoint, release_savepoint, rollback_savepoint

def check_database_schema(database: QtS.QSqlDatabase, blank_schema_file: str):
    # create a temporary database with Create_database, then compare its schema with the loaded file
    # if the schemas are different, create a new database with the correct schema and copy the data over
    # if the schemas are the same, return the loaded database
    db_schema = get_database_schema(database)
    blank_db_connection_name = 'blank_db'
    blank_db = QtS.QSqlDatabase.addDatabase('QSQLITE', blank_db_connection_name)
    blank_db.setDatabaseName(blank_schema_file)
    if not blank_db.open():
        print(f'Failed to open blank database: {blank_db.lastError().text()}')
        return None

    blank_schema = get_database_schema(blank_db)
    if db_schema == blank_schema:
        blank_db.close()
        return database
    elif blank_schema is None:
        print('Failed to get blank schema')
        blank_db.close()
        QtS.QSqlDatabase.removeDatabase(blank_db_connection_name)
        return None
    elif db_schema == {}:
        # This is a new empty database, so return it as is
        blank_db.close()
        QtS.QSqlDatabase.removeDatabase(blank_db_connection_name)
        return database
    else:
        differences = compare_schemas(db_schema, blank_schema)
        # all ages were in Ma, all elevations were in m, and all gps were in DD +/-
        if differences['only_in_input_schema'] == [] and differences['only_in_current_schema'] == []:
            # the only differences are in the data, not the schema
            return database
        age_unit_id = 2  # Ma
        elev_unit_id = 2  # m
        gps_format_id = 1  # DD +/-
        ratio_error_format_id = 1  # 1-sigma absolute
        age_error_format_id = 1  # 1-sigma absolute
        concordance_format_id = 2  # Con%
        spot_size_unit_id = 5 # µm
        tables_to_convert = []
        create_savepoint('before_convert_schema')
        query = QtS.QSqlQuery()
        if not query.exec('DROP VIEW IF EXISTS SampleView'):
            print(f'Failed to drop SampleView: {query.lastError().text()}')
            rollback_savepoint('before_convert_schema')
            return
        for key in differences['only_in_input_schema']:
            # if it is a trigger or view, we need to drop it
            if db_schema[key]['type'] == 'trigger':
                if not query.exec(f'DROP TRIGGER IF EXISTS {key}'):
                    print(f'Failed to drop trigger {key}: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
            elif db_schema[key]['type'] == 'view':
                query = QtS.QSqlQuery()
                if not query.exec(f'DROP VIEW IF EXISTS {key}'):
                    print(f'Failed to drop view {key}: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
            # if it is a table, we need to check if it has any data and copy it over
            elif db_schema[key]['type'] == 'table':
                table_model = QtS.QSqlTableModel()
                table_model.setTable(key)
                table_model.select()
                if table_model.rowCount == 0 or key == 'GeochemData':
                    # if the table is empty, we can just drop it
                    if not drop_table(key):
                        rollback_savepoint('before_convert_schema')
                        return
                else:
                    # if the table has data, we need to copy it over
                    tables_to_convert.append(key)
        for key in differences['only_in_current_schema']:
            # if it is a table, we need to create it. If it is a view, it will be created later
            if blank_schema[key]['type'] == 'table' and 'view' not in key:
                query = QtS.QSqlQuery()
                if not query.exec(blank_schema[key]['sql']):
                    print(f'Failed to create table {key}: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
        # populate the unit and format tables
        Create_db.populate_tables()
        for key in differences['different']:
            query = QtS.QSqlQuery()
            table_model = QtS.QSqlTableModel()
            table_model.setTable(key)
            table_model.select()
            if table_model.rowCount == 0:
                # if the table is empty, we can just drop it and replace it with the new one
                if not drop_table(key):
                    rollback_savepoint('before_convert_schema')
                    return
                if not query.exec(blank_schema[key]['sql']):
                    print(f'Failed to create table {key}: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
            elif "View" not in key:
                query.exec('PRAGMA foreign_keys=OFF')
                # if it is a table, we need to copy the data over
                if not query.exec(f'ALTER TABLE "{key}" RENAME TO {key}_old'):
                    print(f'Failed to rename table {key}: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
                if not query.exec(blank_schema[key]['sql']):
                    print(f'Failed to create table {key}: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
                # copy the data over
                if key == 'Columns':
                    if not query.exec(f'''INSERT INTO "{key}" (ColumnID, ColumnName, ColumnDescription, ColumnCreated, ColumnModified) 
                                            SELECT ColumnID, ColumnName, ColumnDescription, ColumnCreated, ColumnModified
                                            FROM {key}_old'''):
                        print(f'Failed to copy data to {key}: {query.lastError().text()}')
                        rollback_savepoint('before_convert_schema')
                        return
                    if not drop_table(f'{key}_old'):
                        rollback_savepoint('before_convert_schema')
                        return
                elif key == 'Ages':
                    if not query.exec(f'''INSERT INTO "{key}" (AgeID, ParentAgeID, AgeParentRow, AgeName, OldestAge, YoungestAge, 
                                            AgeCreated, AgeModified) SELECT AgeID, ParentAgeID, AgeParentRow, AgeName, 
                                            MaxMa, MinMa, AgeCreated, AgeModified FROM {key}_old'''):
                        print(f'Failed to copy data to {key}: {query.lastError().text()}')
                        rollback_savepoint('before_convert_schema')
                        return
                    if not drop_table(f'{key}_old'):
                        rollback_savepoint('before_convert_schema')
                        return
                elif key == 'Samples':
                    # print(f'{table_model.rowCount()} samples to convert')
                    # move age and gps data to the new tables
                    for row in range(table_model.rowCount()):
                        sample_id = table_model.record(row).value('SampleID')
                        sample_created = table_model.record(row).value('SampleCreated')
                        sample_modified = table_model.record(row).value('SampleModified')
                        if not query.exec(f'SELECT ColumnID from Samples_Columns WHERE SampleID = {sample_id}'):
                            print(f'Failed to get column ID: {query.lastError().text()}')
                            rollback_savepoint('before_convert_schema')
                            return
                        if query.next():
                            column_id = query.value(0)
                        else:
                            column_id = 'NULL'
                        query.prepare(f'''INSERT INTO SampleAges (DirectAge, DirectAgeUnitID, OldestDirectAge, 
                                            YoungestDirectAge, OldestAgeID, YoungestAgeID, SampleAgeCreated, SampleAgeModified)
                                            VALUES (:DirectAge, :DirectAgeUnitID, :OldestDirectAge, 
                                            :YoungestDirectAge, :OldestAgeID, :YoungestAgeID, :SampleAgeCreated, :SampleAgeModified)''')
                        query.bindValue(':DirectAge', table_model.record(row).value('AverageAge'))
                        query.bindValue(':DirectAgeUnitID', age_unit_id)
                        query.bindValue(':OldestDirectAge', table_model.record(row).value('OldestAge'))
                        query.bindValue(':YoungestDirectAge', table_model.record(row).value('YoungestAge'))
                        query.bindValue(':OldestAgeID', table_model.record(row).value('OldestAgeID'))
                        query.bindValue(':YoungestAgeID', table_model.record(row).value('YoungestAgeID'))
                        query.bindValue(':SampleAgeCreated', sample_created)
                        query.bindValue(':SampleAgeModified', sample_modified)
                        if not query.exec():
                            print(f'Failed to insert data into SampleAges: {query.lastError().text()}')
                            rollback_savepoint('before_convert_schema')
                            return
                        sample_age_id = query.lastInsertId()
                        query.prepare(f'''INSERT INTO GPSLocations (GPSFormatID, GPSLatDeg, GPSLatMin, GPSLatSec,  
                                            GPSLonDeg, GPSLonMin, GPSLonSec, GPSElev, GPSElevUnitID, 
                                            GPSLocationCreated, GPSLocationModified)
                                            VALUES (:GPSFormatID, :GPSLatDeg, :GPSLatMin, :GPSLatSec, 
                                            :GPSLonDeg, :GPSLonMin, :GPSLonSec, :GPSElev, :GPSElevUnitID,
                                            :GPSLocationCreated, :GPSLocationModified)''')
                        query.bindValue(':GPSFormatID', gps_format_id)
                        query.bindValue(':GPSLatDeg', table_model.record(row).value('LatDeg'))
                        query.bindValue(':GPSLatMin', table_model.record(row).value('LatMin'))
                        query.bindValue(':GPSLatSec', table_model.record(row).value('LatSec'))
                        query.bindValue(':GPSLonDeg', table_model.record(row).value('LonDeg'))
                        query.bindValue(':GPSLonMin', table_model.record(row).value('LonMin'))
                        query.bindValue(':GPSLonSec', table_model.record(row).value('LonSec'))
                        query.bindValue(':GPSElev', table_model.record(row).value('Elevation'))
                        query.bindValue(':GPSElevUnitID', elev_unit_id)
                        query.bindValue(':GPSLocationCreated', sample_created)
                        query.bindValue(':GPSLocationModified', sample_modified)
                        if not query.exec():
                            print(f'Failed to insert data into GPSLocations: {query.lastError().text()}')
                            rollback_savepoint('before_convert_schema')
                            return
                        gps_id = query.lastInsertId()
                        query.prepare(f'''INSERT INTO Samples (SampleID, SampleName, SampleGPSLocationID, 
                                            SampleColumnID, HeightDepth, HeightDepthError, HeightDepthUnitID, DefaultSampleAgeID, 
                                            SampleDescription, SampleCreated, SampleModified)
                                            VALUES (:SampleID, :SampleName, :SampleGPSLocationID, :SampleColumnID , 
                                            :HeightDepth, :HeightDepthError, :HeightDepthUnitID, :DefaultSampleAgeID, 
                                            :SampleDescription, :SampleCreated, :SampleModified)''')
                        query.bindValue(':SampleID', sample_id)
                        query.bindValue(':SampleName', table_model.record(row).value('SampleName'))
                        query.bindValue(':SampleGPSLocationID', gps_id)
                        query.bindValue(':SampleColumnID', column_id)
                        query.bindValue(':HeightDepth', table_model.record(row).value('HeightDepth'))
                        query.bindValue(':HeightDepthError', table_model.record(row).value('HeightDepthError'))
                        query.bindValue(':HeightDepthUnitID', elev_unit_id)
                        query.bindValue(':DefaultSampleAgeID', sample_age_id)
                        query.bindValue(':SampleDescription', table_model.record(row).value('SampleDescription'))
                        query.bindValue(':SampleCreated', sample_created)
                        query.bindValue(':SampleModified', sample_modified)
                        # if not query.exec(f'''INSERT INTO Samples (SampleID, SampleName, SampleAgeID, SampleGPSLocationID,
                        #                                             SampleColumnID, HeightDepth, HeightDepthError, HeightDepthUnitID, DefaultSampleAgeID,
                        #                                             SampleDescription, SampleCreated, SampleModified)
                        #                                             VALUES ({sample_id}, "{table_model.record(row).value('SampleName')}", {sample_age_id}, {gps_id},
                        #                                             {column_id} , {table_model.record(row).value('HeightDepth')}, {table_model.record(row).value('HeightDepthError')},
                        #                                             {elev_unit_id}, {sample_age_id}, "{table_model.record(row).value('SampleDescription')}",
                        #                                             "{sample_created}", "{sample_modified}")'''):
                        if not query.exec():
                            print(f'Failed to insert data into Samples: {query.lastError().text()}')
                            rollback_savepoint('before_convert_schema')
                            return
                        if not query.exec(f'''INSERT INTO Samples_SampleAges (SampleID, SampleAgeID, 
                                            Samples_SampleAgesCreated, Samples_SampleAgesModified) 
                                            VALUES ({sample_id}, {sample_age_id}, "{sample_created}", "{sample_modified}")'''):
                            print(f'Failed to insert data into Samples_SampleAges: {query.lastError().text()}')
                            rollback_savepoint('before_convert_schema')
                            return
                    if not drop_table('Samples_Columns'):
                        rollback_savepoint('before_convert_schema')
                        return
                    if not drop_table(f'{key}_old'):
                        rollback_savepoint('before_convert_schema')
                        return
                elif key == 'Aliquots':
                    if not query.exec(f'INSERT INTO {key} (AliquotID, AliquotName, SampleID, AliquotCreated, AliquotModified) SELECT AliquotID, AliquotName, SampleID, AliquotCreated, AliquotModified FROM {key}_old'):
                        print(f'Failed to copy data to {key}: {query.lastError().text()}')
                        rollback_savepoint('before_convert_schema')
                        return
                    if not drop_table(f'{key}_old'):
                        rollback_savepoint('before_convert_schema')
                        return
                elif key == 'Spots':
                    if not query.exec(f'INSERT INTO {key} (SpotID, SpotName, AliquotID, SpotCompositionID, SpotCreated, SpotModified) SELECT SpotID, SpotName, AliquotID, SpotCompositionID, SpotCreated, SpotModified FROM {key}_old'):
                        print(f'Failed to copy data to {key}: {query.lastError().text()}')
                        rollback_savepoint('before_convert_schema')
                        return
                    if not drop_table(f'{key}_old'):
                        rollback_savepoint('before_convert_schema')
                        return
                elif key == 'UPbAnalysisMethods':
                    if not query.exec(f'''INSERT INTO {key} (UPbAnalysisMethodID, UPbAnalysisMethodName, UPbAnalysisMethodDescription, 
                                            UPbAnalysisMethodCreated, UPbAnalysisMethodModified) SELECT UPbAnalysisMethodID, 
                                            UPbAnalysisMethodName, UPbAnalysisMethodDescription, UPbAnalysisMethodCreated, 
                                            UPbAnalysisMethodModified FROM {key}_old'''):
                        print(f'Failed to copy data to UPbAnalysisMethods: {query.lastError().text()}')
                        rollback_savepoint('before_convert_schema')
                        return
                    if not drop_table(f'{key}_old'):
                        rollback_savepoint('before_convert_schema')
                        return
                elif '_' in key:
                    columns = []
                    for column in range(table_model.columnCount()):
                        columns.append(table_model.record(0).fieldName(column))
                    columns = ', '.join(columns)
                    for row in range(table_model.rowCount()):
                        item_table = key.split('_')[0]
                        item_id = table_model.record(row).value(f'{item_table[:-1]}ID')
                        other_table = key.split('_')[1]
                        other_id = table_model.record(row).value(f'{other_table[:-1]}ID')
                        created = table_model.record(row).value(f'{key}Created')
                        modified = table_model.record(row).value(f'{key}Modified')
                        if not query.exec(f'''INSERT INTO {key} ({item_table[:-1]}ID, {other_table[:-1]}ID, {key}Created, {key}Modified) 
                                            VALUES ({item_id}, {other_id}, "{created}", "{modified}")'''):
                            if "UNIQUE constraint failed" not in query.lastError().text():
                                print(f'Failed to copy data to {key}: {query.lastError().text()}')
                                rollback_savepoint('before_convert_schema')
                                return
                    if not drop_table(f'{key}_old'):
                        rollback_savepoint('before_convert_schema')
                        return
                query.exec('PRAGMA foreign_keys=ON')
        for key in tables_to_convert:
            query = QtS.QSqlQuery()
            table_model = QtS.QSqlTableModel()
            table_model.setTable(key)
            table_model.select()
            if key == 'Sources':
                if not query.exec(f'''INSERT INTO "References" (ReferenceID, Authors, Year, Title, Source, DOI, 
                                    ReferenceCreated, ReferenceModified) SELECT SourceID, Authors, Year, Title, Source, 
                                    doi, SourceCreated, SourceModified FROM {key}'''):
                    print(f'Failed to copy data to References: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
                if not drop_table(key):
                    rollback_savepoint('before_convert_schema')
                    return
            elif key == 'AnalysisMethods':
                if not query.exec(f'''INSERT INTO UPbAnalysisMethods (UPbAnalysisMethodID, ParentUPbAnalysisMethodID, 
                                        UPbAnalysisMethodParentRow, UPbAnalysisMethodName, UPbAnalysisMethodDescription, 
                                        UPbAnalysisMethodCreated, UPbAnalysisMethodModified) SELECT AnalysisMethodID,
                                        ParentAnalysisMethodID, AnalysisMethodParentRow, AnalysisMethodName,
                                        AnalysisMethodDescription, AnalysisMethodCreated, AnalysisMethodModified FROM {key}'''):
                    print(f'Failed to copy data to UPbAnalysisMethods: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
                if not drop_table(key):
                    rollback_savepoint('before_convert_schema')
                    return
            elif key == 'UPbData':

                if not query.exec(f'''INSERT INTO UPbAnalyses (UPbAnalysisID, SpotID, ReferenceID, LabFacilityID, InstrumentID, 
                                        UPbAnalysisMethodID, Uppm, "206Pb/204Pb", "U/Th", "206Pb/207Pb", "206Pb/207PbError",
                                        "207Pb/235U", "207Pb/235UError", "206Pb/238U", "206Pb/238UError", RatioErrorFormatID, 
                                        "ErrorCorr/Rho", "207Pb/206PbAge", "207Pb/206PbAgeError", "207Pb/235UAge", "207Pb/235UAgeError",
                                        "206Pb/238UAge", "206Pb/238UAgeError", "BestAge", "BestAgeError", AgeErrorFormatID,
                                        AgeUnitID, Concordance, ConcordanceFormatID, SpotSize, SpotSizeUnitID, Rejected, 
                                        UPbAnalysisCreated, UPbAnalysisModified) SELECT UPbAnalysisID, SpotID, SourceID, LabFacilityID,
                                        InstrumentID, UPbAnalysisMethodID, Uppm, "206Pb/204Pb", "U/Th", "206Pb/207Pb", "206Pb/207PbError",
                                        "207Pb/235U", "207Pb/235UError", "206Pb/238U", "206Pb/238UError", {ratio_error_format_id},
                                        "ErrorCorr/Rho", "206Pb/207PbAge", "206Pb/207PbAgeError", "207Pb/235UAge", "207Pb/235UAgeError",
                                        "206Pb/238UAge", "206Pb/238UAgeError", "BestAge", "Error", {age_error_format_id},
                                        {age_unit_id}, Conc, {concordance_format_id}, SpotSize, {spot_size_unit_id}, Accepted,
                                        UPbAnalysisCreated, UPbAnalysisModified FROM {key}'''):
                    print(f'Failed to copy data to UPbAnalyses: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
                for row in range(table_model.rowCount()):
                    if table_model.record(row).value('Accepted') == 1:
                        if not query.exec(f'UPDATE UPbAnalyses SET Rejected = 0 WHERE UPbAnalysisID = {table_model.record(row).value("UPbAnalysisID")}'):
                            print(f'Failed to update UPbAnalyses: {query.lastError().text()}')
                            rollback_savepoint('before_convert_schema')
                            return
                    elif table_model.record(row).value('Accepted') == 0:
                        if not query.exec(f'UPDATE UPbAnalyses SET Rejected = 1 WHERE UPbAnalysisID = {table_model.record(row).value("UPbAnalysisID")}'):
                            print(f'Failed to update UPbAnalyses: {query.lastError().text()}')
                            rollback_savepoint('before_convert_schema')
                            return
                table_model.clear()
                if not drop_table(key):
                    rollback_savepoint('before_convert_schema')
                    return
            elif key.endswith('Context'):
                columns = []
                for column in range(table_model.columnCount()):
                    columns.append(table_model.record(0).fieldName(column))
                columns = ', '.join(columns)
                if not query.exec(f'INSERT INTO "{key}s" SELECT {columns} FROM {key}'):
                    print(f'Failed to copy data to {key}: {query.lastError().text()}')
                    rollback_savepoint('before_convert_schema')
                    return
                if not drop_table(key):
                    rollback_savepoint('before_convert_schema')
                    return
        if not query.exec('PRAGMA schema_version'):
            print(f'Failed to get schema version: {query.lastError().text()}')
            rollback_savepoint('before_convert_schema')
            return
        print('Database schema updated')
        release_savepoint('before_convert_schema')
        return database

def get_database_schema(db: QtS.QSqlDatabase):
    db_query = QtS.QSqlQuery(db)
    db_query.prepare('SELECT * FROM sqlite_master')
    if not db_query.exec():
        print(f'Failed to get database schema: {db_query.lastError().text()}')
        return None
    schema = {}

    while db_query.next():
        type = db_query.value(0)
        name = db_query.value(1)
        tbl_name = db_query.value(2)
        sql = db_query.value(4)
        schema[name] = {'type': type, 'tbl_name': tbl_name, 'sql': sql}
    return schema

def compare_schemas(input_schema, current_schema):
    differences = {
        'only_in_input_schema': [],
        'only_in_current_schema': [],
        'different': []
    }
    for key in input_schema:
        if key not in current_schema:
            differences['only_in_input_schema'].append(key)
        elif input_schema[key] != current_schema[key]:
            differences['different'].append(key)
    for key in current_schema:
        if key not in input_schema:
            differences['only_in_current_schema'].append(key)
    return differences

def drop_table(table_name: str):
    query = QtS.QSqlQuery()
    db = QtS.QSqlDatabase.database()
    if db.transaction():
        db.commit()
    if not query.exec(f'DROP TABLE IF EXISTS {table_name}'):
        print(f'Failed to drop table {table_name}: {query.lastError().text()}')
        return False
    return True