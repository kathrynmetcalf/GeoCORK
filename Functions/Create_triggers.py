import sqlite3

from PyQt6 import QtSql as QtS


def create_triggers(db: QtS.QSqlDatabase):
    """
    Take database cursor and execute the sql strings defined above to create the database triggers
    :param db: QSqlDatabase object
    """

    '''Methods for creating the database triggers'''
    '''SQL strings to create each trigger'''

    def modified_list_statement(table: str):
        query = QtS.QSqlQuery(db)
        query.exec(f'PRAGMA table_info({table})')
        columns = []
        while query.next(): columns.append(query.value(1))
        modified_list = []
        for column in columns:
            if 'Created' or 'Modified' not in column:
                modified_list.append(f'"{column}"')
        modified_statement = ' OR '.join([f'{column} = NEW.{column}' for column in modified_list])
        return modified_statement

    def check_error_columns():
        query = QtS.QSqlQuery(db)
        query.exec('PRAGMA table_info(UPbAnalyses)')
        columns = []
        while query.next(): columns.append(query.value(1))
        ratio_error_list = []
        age_error_list = []
        for column in columns:
            if column.endswith('AgeError'):
                age_error_list.append(f'"{column}"')
            elif column.endswith('Error'):
                ratio_error_list.append(f'"{column}"')
        ratio_list = [column.replace('Error', '') for column in ratio_error_list]
        age_list = [column.replace('Error', '') for column in age_error_list]
        ratio_error_statement = ' OR '.join(ratio_error_list)
        new_ratio_error_statement = ' OR '.join([f'NEW.{column}' for column in ratio_error_list])
        missing_ratio_list = [f'({column_error} IS NOT NULL AND {column} IS NULL)' for column_error, column in
                              zip(ratio_error_list, ratio_list)]
        missing_ratio_statement = ' OR '.join(missing_ratio_list)
        age_error_statement = ' OR '.join(age_error_list)
        new_age_error_statement = ' OR '.join([f'NEW.{column}' for column in age_error_list])
        missing_age_list = [f'({column_error} IS NOT NULL AND {column} IS NULL)' for column_error, column in
                            zip(age_error_list, age_list)]
        missing_age_statement = ' OR '.join(missing_age_list)
        return ratio_error_statement, new_ratio_error_statement, age_error_statement, new_age_error_statement, missing_ratio_statement, missing_age_statement

    ratio_error_statement, new_ratio_error_statement, age_error_statement, new_age_error_statement, missing_ratio_statement, missing_age_statement = check_error_columns()

    '''Triggers for missing pairs and units, only triggers if there is corresponding data'''
    '''e.g. there is latitude but not longitude or an elevation value but no unit'''
    CREATE_COLUMN_UNITS_INSERT_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_column_units_before_insert BEFORE INSERT ON Columns
    BEGIN
        SELECT CASE
            WHEN NEW."ColumnTotalHeightDepth" IS NOT NULL AND NEW."ColumnTotalHeightDepthUnitID" IS NULL THEN
                RAISE (ABORT,'Column total height/depth value with missing units')
            END;
    END;'''
    CREATE_COLUMN_UNITS_UPDATE_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_column_units_before_update BEFORE UPDATE ON Columns
    BEGIN
        SELECT CASE
            WHEN NEW."ColumnTotalHeightDepth" IS NOT NULL AND NEW."ColumnTotalHeightDepthUnitID" IS NULL THEN
                RAISE (ABORT,'Column total height/depth value with missing units')
            END;
        SELECT CASE
            WHEN "ColumnTotalHeightDepth" IS NOT NULL AND NEW."ColumnTotalHeightDepthUnitID" IS NULL THEN
                RAISE (ABORT,'Column total height/depth value with missing units')
                END;
        SELECT CASE
            WHEN NEW."ColumnTotalHeightDepth" IS NOT NULL AND "ColumnTotalHeightDepthUnitID" IS NULL THEN
                RAISE (ABORT,'Column total height/depth value with missing units')
            END;
    END;
    '''
    CREATE_GPS_INSERT_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_gps_before_insert BEFORE INSERT ON GPSLocations
    BEGIN
        SELECT CASE
            WHEN (NEW."GPSLatDeg" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) OR 
            (NEW."GPSLonDeg" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) THEN
                RAISE (ABORT, 'Missing corresponding degrees latitude or longitude')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatMin" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) OR
            (NEW."GPSLonMin" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) THEN
                RAISE(ABORT, 'No degrees given for minutes')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatSec" IS NOT NULL AND NEW."GPSLatMin" IS NULL) OR
            (NEW."GPSLonSec" IS NOT NULL AND NEW."GPSLonMin" IS NULL) THEN
                RAISE(ABORT, 'No minutes given for seconds')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatDirectionID" IS NOT NULL AND NEW."GPSLonDirectionID" IS NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND NEW."GPSLatDirectionID" IS NULL) THEN
                RAISE(ABORT, 'Missing corresponding direction for latitude or longitude')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatDirectionID" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) THEN
                RAISE(ABORT, 'Missing corresponding degrees for direction')
            END;
        SELECT CASE 
            WHEN (NEW."GPSLatDirectionID" IS 1 AND NEW."GPSLatDeg" < 0) OR
            (NEW."GPSLonDirectionID" IS 3 AND NEW."GPSLonDeg" < 0) THEN
                RAISE(ABORT, 'Negative value with S or W direction')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatDirectionID" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) THEN
                RAISE(ABORT, 'Lat Lon direction given for UTM coordinates. Coordinates should be entered in the format originally provided.')
            END;
        SELECT CASE
            WHEN NEW."GPSLatDeg" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL THEN
                RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format originally provided.')
            END;
        SELECT CASE 
            WHEN NEW."GPSUTMZone" IS NOT NULL AND (NEW."GPSLatDeg" OR NEW."GPSLonDeg") IS NOT NULL THEN
                RAISE (ABORT, 'UTM zone given for Lat Lon coordinates. Coordinates should be entered in the format originally provided.')
            END;
        SELECT CASE
            WHEN NEW."GPSUTMN" IS NOT NULL AND NEW."GPSUTMZone" IS NULL THEN
                RAISE (ABORT,'UTM coordinates with missing zone')
            END;
        SELECT CASE
            WHEN NEW."GPSUTMN" IS NOT NULL AND NEW."GPSUTME" IS NULL THEN
                RAISE (ABORT,'UTM northing missing corresponding easting')
            END;
        SELECT CASE
            WHEN NEW."GPSUTME" IS NOT NULL AND NEW."GPSUTMN" IS NULL THEN
                RAISE (ABORT,'UTM easting missing corresponding northing')
            END;
        SELECT CASE
            WHEN NEW."GPSElev" IS NOT NULL AND NEW."GPSElevUnitID" IS NULL THEN
                RAISE (ABORT,'Elevation value with missing units')
            END;
        SELECT CASE
            WHEN NEW."GPSElevError" IS NOT NULL AND NEW."GPSElev" IS NULL THEN
                RAISE (ABORT,'Elevation error value with missing elevation')
            END;
    END;
    '''
    CREATE_GPS_UPDATE_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_gps_before_update BEFORE UPDATE ON GPSLocations
    BEGIN
        SELECT CASE
            WHEN (NEW."GPSLatDeg" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) OR (NEW."GPSLonDeg" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) OR 
            ("GPSLatDeg" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) OR (NEW."GPSLonDeg" IS NOT NULL AND "GPSLatDeg" IS NULL) OR 
            (NEW."GPSLatDeg" IS NOT NULL AND "GPSLonDeg" IS NULL) OR ("GPSLonDeg" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) THEN
                RAISE (ABORT,'Missing corresponding degrees latitude or longitude')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatMin" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) OR (NEW."GPSLonMin" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) OR
            ("GPSLatMin" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) OR ("GPSLonMin" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) OR
            (NEW."GPSLatMin" IS NOT NULL AND "GPSLatDeg" IS NULL) OR (NEW."GPSLonMin" IS NOT NULL AND "GPSLonDeg" IS NULL) THEN
                RAISE(ABORT, 'No degrees given for minutes')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatSec" IS NOT NULL AND NEW."GPSLatMin" IS NULL) OR (NEW."GPSLonSec" IS NOT NULL AND NEW."GPSLonMin" IS NULL) OR
            ("GPSLatSec" IS NOT NULL AND NEW."GPSLatMin" IS NULL) OR ("GPSLonSec" IS NOT NULL AND NEW."GPSLonMin" IS NULL) OR
            (NEW."GPSLatSec" IS NOT NULL AND "GPSLatMin" IS NULL) OR (NEW."GPSLonSec" IS NOT NULL AND "GPSLonMin" IS NULL) THEN
                RAISE(ABORT, 'No minutes given for seconds')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatDirectionID" IS NOT NULL AND NEW."GPSLonDirectionID" IS NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND NEW."GPSLatDirectionID" IS NULL) OR
            ("GPSLatDirectionID" IS NOT NULL AND NEW."GPSLonDirectionID" IS NULL) OR
            ("GPSLonDirectionID" IS NOT NULL AND NEW."GPSLatDirectionID" IS NULL) OR
            (NEW."GPSLatDirectionID" IS NOT NULL AND "GPSLonDirectionID" IS NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND "GPSLatDirectionID" IS NULL) THEN
                RAISE(ABORT, 'Missing corresponding direction for latitude or longitude')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatDirectionID" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) OR
            ("GPSLatDirectionID" IS NOT NULL AND NEW."GPSLatDeg" IS NULL) OR
            ("GPSLonDirectionID" IS NOT NULL AND NEW."GPSLonDeg" IS NULL) OR
            (NEW."GPSLatDirectionID" IS NOT NULL AND "GPSLatDeg" IS NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND "GPSLonDeg" IS NULL) THEN
                RAISE(ABORT, 'Missing corresponding degrees for direction')
            END;
        SELECT CASE 
            WHEN (NEW."GPSLatDirectionID" IS 1 AND NEW."GPSLatDeg" < 0) OR
            (NEW."GPSLonDirectionID" IS 3 AND NEW."GPSLonDeg" < 0) OR 
            ("GPSLatDirectionID" IS 1 AND NEW."GPSLatDeg" < 0) OR
            ("GPSLonDirectionID" IS 3 AND NEW."GPSLonDeg" < 0) OR 
            (NEW."GPSLatDirectionID" IS 1 AND "GPSLatDeg" < 0) OR
            (NEW."GPSLonDirectionID" IS 3 AND "GPSLonDeg" < 0) THEN
                RAISE(ABORT, 'Negative value with S or W direction')
            END;
        SELECT CASE 
            WHEN (NEW."GPSLatDirectionID" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) OR
            ("GPSLatDirectionID" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) OR
            ("GPSLonDirectionID" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) OR
            (NEW."GPSLatDirectionID" IS NOT NULL AND "GPSUTMN" IS NOT NULL) OR
            (NEW."GPSLonDirectionID" IS NOT NULL AND "GPSUTMN" IS NOT NULL) THEN
                RAISE(ABORT, 'Lat Lon direction given for UTM coordinates. Coordinates should be entered in the format originally provided.')
            END;
        SELECT CASE 
            WHEN NEW."GPSUTMZone" IS NOT NULL AND (NEW."GPSLatDeg" OR NEW."GPSLonDeg") IS NOT NULL OR 
            ("GPSUTMZone" IS NOT NULL AND (NEW."GPSLatDeg" OR NEW."GPSLonDeg") IS NOT NULL) OR 
            (NEW."GPSUTMZone" IS NOT NULL AND ("GPSLatDeg" OR "GPSLonDeg") IS NOT NULL) THEN
                RAISE (ABORT, 'UTM zone given for Lat Lon coordinates. Coordinates should be entered in the format originally provided.')
            END;
        SELECT CASE
            WHEN (NEW."GPSUTMN" IS NOT NULL AND NEW."GPSUTMZone" IS NULL) OR 
            (NEW."GPSUTMN" IS NOT NULL AND "GPSUTMZone" IS NULL) OR 
            ("GPSUTMN" IS NOT NULL AND NEW."GPSUTMZone" IS NULL) THEN
                RAISE (ABORT,'UTM coordinates with missing zone')
            END;
        SELECT CASE
            WHEN (NEW."GPSUTMN" IS NOT NULL AND NEW."GPSUTME" IS NULL) OR 
            (NEW."GPSUTMN" IS NOT NULL AND "GPSUTME" IS NULL) OR
            ("GPSUTMN" IS NOT NULL AND NEW."GPSUTME" IS NULL) THEN
                RAISE (ABORT,'UTM northing missing corresponding easting')
            END;
        SELECT CASE
            WHEN (NEW."GPSUTME" IS NOT NULL AND NEW."GPSUTMN" IS NULL) OR
            (NEW."GPSUTME" IS NOT NULL AND "GPSUTMN" IS NULL) OR
            ("GPSUTME" IS NOT NULL AND NEW."GPSUTMN" IS NULL) THEN
                RAISE (ABORT,'UTM easting missing corresponding northing')
            END;
        SELECT CASE
            WHEN (NEW."GPSLatDeg" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) OR 
            (NEW."GPSLatDeg" IS NOT NULL AND "GPSUTMN" IS NOT NULL) OR
            ("GPSLatDeg" IS NOT NULL AND NEW."GPSUTMN" IS NOT NULL) THEN
                RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
            END;
    END;
    '''
    CREATE_SAMPLEAGES_INSERT_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_age_units_before_insert BEFORE INSERT ON SampleAges
    BEGIN
        SELECT CASE
            WHEN NEW."DirectAgeError" IS NOT NULL AND NEW."DirectAgeErrorTypeID" IS NULL THEN
                RAISE (ABORT,'Direct age error value with missing units')
            END;
        SELECT CASE
            WHEN NEW."DirectAgeError" IS NOT NULL AND NEW."DirectAge" IS NULL THEN
                RAISE (ABORT,'Direct age error value with missing age')
            END;
        SELECT CASE
            WHEN (NEW."DirectAge" IS NOT NULL OR NEW."OldestDirectAge" IS NOT NULL OR NEW."YoungestDirectAge" IS NOT NULL) AND NEW."DirectAgeUnitID" IS NULL THEN
                RAISE (ABORT,'Direct age value with missing units')
            END;
    END;
    '''
    CREATE_SAMPLEAGES_UPDATE_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_age_units_before_update BEFORE UPDATE ON SampleAges
    BEGIN
        SELECT CASE
            WHEN (NEW."DirectAgeError" IS NOT NULL AND NEW."DirectAgeErrorTypeID" IS NULL) OR ("DirectAgeError" IS NOT NULL AND NEW."DirectAgeErrorTypeID" IS NULL) THEN
                RAISE (ABORT,'Direct age error value with missing units')
            END;
        SELECT CASE
            WHEN (NEW."DirectAgeError" IS NOT NULL AND NEW."DirectAge" IS NULL) OR ("DirectAgeError" IS NOT NULL AND NEW."DirectAge" IS NULL) THEN
                RAISE (ABORT,'Direct age error value with missing age')
            END;
        SELECT CASE
            WHEN ((NEW."DirectAge" IS NOT NULL OR NEW."OldestDirectAge" IS NOT NULL OR NEW."YoungestDirectAge" IS NOT NULL) AND NEW."DirectAgeUnitID" IS NULL) OR 
            (("DirectAge" IS NOT NULL OR "OldestDirectAge" IS NOT NULL OR "YoungestDirectAge" IS NOT NULL) AND NEW."DirectAgeUnitID" IS NULL) OR 
            ((NEW."DirectAge" IS NOT NULL OR NEW."OldestDirectAge" IS NOT NULL OR NEW."YoungestDirectAge" IS NOT NULL) AND "DirectAgeUnitID" IS NULL) THEN
                RAISE (ABORT,'Direct age value with missing units')
            END;
    END;
    '''
    CREATE_SAMPLES_INSERT_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_sample_info_before_insert BEFORE INSERT ON Samples
    BEGIN
        SELECT CASE
            WHEN NEW."HeightDepth" IS NOT NULL AND NEW."HeightDepthUnitID" IS NULL THEN
                RAISE (ABORT,'Height/depth value with missing units')
            END;
        SELECT CASE
            WHEN NEW."HeightDepthError" IS NOT NULL AND NEW."HeightDepth" IS NULL THEN
                RAISE (ABORT,'Height/depth error value with missing height/depth value')
            END;
        SELECT CASE
            WHEN NEW."HeightDepth" IS NOT NULL AND NEW."SampleColumnID" IS NULL THEN
                RAISE (ABORT,'Height/depth value with missing column')
            END;
    END;
    '''
    CREATE_SAMPLES_UPDATE_TRIGGERS = '''
    CREATE TRIGGER IF NOT EXISTS validate_sample_info_before_update BEFORE UPDATE ON Samples
    BEGIN
        SELECT CASE
            WHEN (NEW."HeightDepth" IS NOT NULL AND NEW."HeightDepthUnitID" IS NULL) OR 
            ("HeightDepth" IS NOT NULL AND NEW."HeightDepthUnitID" IS NULL) OR 
            (NEW."HeightDepth" IS NOT NULL AND "HeightDepthUnitID" IS NULL) THEN
                RAISE (ABORT,'Height/depth value with missing units')
            END;
        SELECT CASE
            WHEN (NEW."HeightDepthError" IS NOT NULL AND NEW."HeightDepth" IS NULL) OR
            ("HeightDepthError" IS NOT NULL AND NEW."HeightDepth" IS NULL) OR
            (NEW."HeightDepthError" IS NOT NULL AND "HeightDepth" IS NULL) THEN
                RAISE (ABORT,'Height/depth error value with missing height/depth value')
            END;
        SELECT CASE
            WHEN (NEW."HeightDepth" IS NOT NULL AND NEW."SampleColumnID" IS NULL) OR 
            ("HeightDepth" IS NOT NULL AND NEW."SampleColumnID" IS NULL) OR 
            (NEW."HeightDepth" IS NOT NULL AND "SampleColumnID" IS NULL) THEN
                RAISE (ABORT,'Height/depth value with missing column')
            END;
    END;
    '''
    CREATE_UPBANALYSES_INSERT_TRIGGERS = f'''
    CREATE TRIGGER IF NOT EXISTS validate_upbanalyses_before_insert BEFORE INSERT ON UPbAnalyses
    BEGIN
        SELECT CASE
            WHEN ({new_ratio_error_statement}) IS NOT NULL AND NEW."RatioErrorTypeID" IS NULL THEN
                RAISE (ABORT,'Ratio error values with missing type')
            END;
        SELECT CASE
            WHEN ({missing_ratio_statement}) THEN
                RAISE (ABORT,'Ratio error values with missing corresponding ratio')
            END;
        SELECT CASE
            WHEN ({new_age_error_statement}) IS NOT NULL AND NEW."AgeErrorTypeID" IS NULL THEN
                RAISE (ABORT,'Age error values with missing type')
            END;
        SELECT CASE
            WHEN ({missing_age_statement}) THEN
                RAISE (ABORT,'Age error values with missing corresponding age')
            END;
        SELECT CASE
            WHEN NEW."Concordance" IS NOT NULL AND NEW."ConcordanceTypeID" IS NULL THEN
                RAISE (ABORT,'Concordance value with missing type')
            END;
        SELECT CASE
            WHEN NEW."SpotSize" IS NOT NULL AND NEW."SpotSizeUnitID" IS NULL THEN
                RAISE (ABORT,'Spot size value with missing units')
            END;
    END;
    '''
    CREATE_UPBANALYSES_UPDATE_TRIGGERS = f'''
    CREATE TRIGGER IF NOT EXISTS validate_upbanalyses_before_update BEFORE UPDATE ON UPbAnalyses
    BEGIN
        SELECT CASE
            WHEN (({new_ratio_error_statement}) IS NOT NULL AND NEW."RatioErrorTypeID" IS NULL) OR 
            (({ratio_error_statement}) IS NOT NULL AND NEW."RatioErrorTypeID" IS NULL) OR 
            (({new_ratio_error_statement}) IS NOT NULL AND "RatioErrorTypeID" IS NULL) THEN
                RAISE (ABORT,'Ratio error values with missing type')
            END;
        SELECT CASE
            WHEN {missing_ratio_statement} THEN
                RAISE (ABORT,'Ratio error values with missing corresponding ratio')
            END;
        SELECT CASE
            WHEN (({new_age_error_statement}) IS NOT NULL AND NEW."AgeErrorTypeID" IS NULL) OR 
            (({age_error_statement}) IS NOT NULL AND NEW."AgeErrorTypeID" IS NULL) OR
            (({new_age_error_statement}) IS NOT NULL AND "AgeErrorTypeID" IS NULL) THEN
                RAISE (ABORT,'Age error values with missing type')
            END;
        SELECT CASE
            WHEN {missing_age_statement} THEN
                RAISE (ABORT,'Age error values with missing corresponding age')
            END;
        SELECT CASE
            WHEN (NEW."Concordance" IS NOT NULL AND NEW."ConcordanceTypeID" IS NULL) OR 
            ("Concordance" IS NOT NULL AND NEW."ConcordanceTypeID" IS NULL) OR
            (NEW."Concordance" IS NOT NULL AND "ConcordanceTypeID" IS NULL) THEN
                RAISE (ABORT,'"Concordance" value with missing type')
            END;
        SELECT CASE
            WHEN (NEW."SpotSize" IS NOT NULL AND NEW."SpotSizeUnitID" IS NULL) OR 
            ("SpotSize" IS NOT NULL AND NEW."SpotSizeUnitID" IS NULL) OR
            (NEW."SpotSize" IS NOT NULL AND "SpotSizeUnitID" IS NULL) THEN
                RAISE (ABORT,'Spot size value with missing units')
            END;
    END;
    '''

    # Triggers to update the modified timestamp when a value is updated
    ABOUT_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_about AFTER UPDATE ON About
    BEGIN
        UPDATE "About" SET "AboutModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('About')};
    END;'''
    AGECONSTRAINTS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_ageconstraints AFTER UPDATE ON AgeConstraints
    BEGIN
        UPDATE "AgeConstraints" SET "AgeConstraintModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('AgeConstraints')};
    END;'''
    AGE_CONVERSIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_age_conversions AFTER UPDATE ON AgeUnitConversions
    BEGIN
        UPDATE "AgeUnitConversions" SET "AgeUnitConversionModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('AgeUnitConversions')};
    END;'''
    AGEINTERPRETATIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_ageinterpretations AFTER UPDATE ON AgeInterpretations
    BEGIN
        UPDATE "AgeInterpretations" SET "AgeInterpretationModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('AgeInterpretations')};
    END;'''
    AGESIGNATURES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_agesignatures AFTER UPDATE ON AgeSignatures
    BEGIN
        UPDATE "AgeSignatures" SET "AgeSignatureModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('AgeSignatures')};
    END;'''
    AGEUNITS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_ageunits AFTER UPDATE ON AgeUnits
    BEGIN
        UPDATE "AgeUnits" SET "AgeUnitModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('AgeUnits')};
    END;'''
    AGES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_ages AFTER UPDATE ON Ages
    BEGIN
        UPDATE "Ages" SET "AgeModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Ages')};
    END;'''
    ALIQUOTCONTEXT_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_aliquotcontexts AFTER UPDATE ON AliquotContexts
    BEGIN
        UPDATE "AliquotContexts" SET "AliquotContextModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('AliquotContexts')};
    END;'''
    ALIQUOTS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_aliquots AFTER UPDATE ON Aliquots
    BEGIN
        UPDATE "Aliquots" SET "AliquotModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Aliquots')};
    END;'''
    ALIQUOTS_ALIQUOTCONTEXT_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_aliquots_aliquotcontexts AFTER UPDATE ON Aliquots_AliquotContexts
    BEGIN
        UPDATE "Aliquots_AliquotContexts" SET "Aliquots_AliquotContextModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Aliquots_AliquotContexts')};
    END;'''
    COLUMNS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_columns AFTER UPDATE ON Columns
    BEGIN
        UPDATE "Columns" SET "ColumnModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Columns')};
    END;'''
    CONCORDANCETYPES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_concordancetypes AFTER UPDATE ON ConcordanceTypes
    BEGIN
        UPDATE "ConcordanceTypes" SET "ConcordanceTypeModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('ConcordanceTypes')};
    END;'''
    CONCORDANCE_CONVERSIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_concordance_conversions AFTER UPDATE ON ConcordanceTypeConversions
    BEGIN 
        UPDATE "ConcordanceTypeConversions" SET "ConcordanceConversionModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('ConcordanceTypeConversions')};
    END;'''
    DIRECTIONUNITS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_directionunits AFTER UPDATE ON DirectionUnits
    BEGIN
        UPDATE "DirectionUnits" SET "DirectionUnitModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('DirectionUnits')};
    END;'''
    DISTANCEUNITS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_distanceunits AFTER UPDATE ON DistanceUnits
    BEGIN
        UPDATE "DistanceUnits" SET "DistanceUnitModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('DistanceUnits')};
    END;'''
    DISTANCE_CONVERSIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_distance_conversions AFTER UPDATE ON DistanceUnitConversions
    BEGIN
        UPDATE "DistanceUnitConversions" SET "DistanceConversionModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('DistanceUnitConversions')};
    END;'''
    ERRORTYPES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_errortypes AFTER UPDATE ON ErrorTypes
    BEGIN
        UPDATE "ErrorTypes" SET "ErrorTypeModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('ErrorTypes')};
    END;'''
    ERROR_CONVERSIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_error_conversions AFTER UPDATE ON ErrorTypeConversions
    BEGIN
        UPDATE "ErrorTypeConversions" SET "ErrorConversionModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('ErrorTypeConversions')};
    END;'''
    GPS_CONVERSIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_gps_conversions AFTER UPDATE ON GPSLocationConversions
    BEGIN
        UPDATE "GPSLocationConversions" SET "GPSConversionModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('GPSLocationConversions')};
    END;'''
    GPS_FORMATS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_gps_formats AFTER UPDATE ON GPSFormats
    BEGIN
        UPDATE "GPSFormats" SET "GPSFormatModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('GPSFormats')};
    END;'''
    GPS_LOCATIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_gpslocations AFTER UPDATE ON GPSLocations
    BEGIN
        UPDATE "GPSLocations" SET "GPSLocationModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('GPSLocations')};
    END;'''
    FILTERGROUPS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_filtergroups AFTER UPDATE ON FilterGroups
    BEGIN
        UPDATE "FilterGroups" SET "FilterGroupModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('FilterGroups')};
    END;'''
    INSTRUMENTS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_instruments AFTER UPDATE ON Instruments
    BEGIN
        UPDATE "Instruments" SET "InstrumentModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Instruments')};
    END;'''
    LABFACILITIES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_labfacilities AFTER UPDATE ON LabFacilities
    BEGIN
        UPDATE "LabFacilities" SET "LabFacilityModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('LabFacilities')};
    END;'''
    REGIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_regions AFTER UPDATE ON Regions
    BEGIN
        UPDATE "Regions" SET "RegionModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Regions')};
    END;'''
    REJECTIONREASONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_rejectionreasons AFTER UPDATE ON RejectionReasons
    BEGIN
        UPDATE "RejectionReasons" SET "RejectionReasonModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('RejectionReasons')};
    END;'''
    ROCKTYPES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_rocktypes AFTER UPDATE ON RockTypes
    BEGIN
        UPDATE "RockTypes" SET "RockTypeModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('RockTypes')};
    END;'''
    SAMPLEAGES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_sampleages AFTER UPDATE ON SampleAges
    BEGIN
        UPDATE "SampleAges" SET "SampleAgeModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('SampleAges')};
    END;'''
    SAMPLECONTEXT_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samplecontexts AFTER UPDATE ON SampleContexts
    BEGIN
        UPDATE "SampleContexts" SET "SampleContextModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('SampleContexts')};
    END;'''
    SAMPLEAGES_AGECONSTRAINTS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_sampleages_ageconstraints AFTER UPDATE ON SampleAges_AgeConstraints
    BEGIN
        UPDATE "SampleAges_AgeConstraints" SET "SampleAges_AgeConstraintsModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('SampleAges_AgeConstraints')};
    END;'''
    SAMPLEAGES_AGEINTERPRETATIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_sampleages_ageinterpretations AFTER UPDATE ON SampleAges_AgeInterpretations
    BEGIN
        UPDATE "SampleAges_AgeInterpretations" SET {modified_list_statement('SampleAges_AgeInterpretations')};
    END;'''
    SAMPLEAGES_SOURCES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_sampleages_sources AFTER UPDATE ON SampleAges_Sources
    BEGIN
        UPDATE "SampleAges_Sources" SET "SampleAges_SourcesModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('SampleAges_Sources')};
    END;'''
    SAMPLES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples AFTER UPDATE ON Samples
    BEGIN
        UPDATE "Samples" SET "SampleModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples')};
    END;'''
    SAMPLES_AGESIGNATURES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples_agesignatures AFTER UPDATE ON Samples_AgeSignatures
    BEGIN
        UPDATE "Samples_AgeSignatures" SET "Samples_AgeSignaturesModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples_AgeSignatures')};
    END;'''
    SAMPLES_REGIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples_regions AFTER UPDATE ON Samples_Regions
    BEGIN
        UPDATE "Samples_Regions" SET "Samples_RegionsModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples_Regions')};
    END;'''
    SAMPLES_ROCKTYPES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples_rocktypes AFTER UPDATE ON Samples_RockTypes
    BEGIN
        UPDATE "Samples_RockTypes" SET "Samples_RockTypesModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples_RockTypes')};
    END;'''
    SAMPLES_SAMPLECONTEXT_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples_samplecontexts AFTER UPDATE ON Samples_SampleContexts
    BEGIN
        UPDATE "Samples_SampleContexts" SET "Samples_SampleContextModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples_SampleContexts')};
    END;'''
    SAMPLES_SAMPLINGMETHODS_MODIFIED_RIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples_samplingmethods AFTER UPDATE ON Samples_SamplingMethods
    BEGIN
        UPDATE "Samples_SamplingMethods" SET "Samples_SamplingMethodsModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples_SamplingMethods')};
    END;'''
    SAMPLES_SETTINGS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples_settings AFTER UPDATE ON Samples_Settings
    BEGIN
        UPDATE "Samples_Settings" SET "Samples_SettingsModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples_Settings')};
    END;'''
    SAMPLES_UNITS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samples_units AFTER UPDATE ON Samples_Units
    BEGIN
        UPDATE "Samples_Units" SET "Samples_UnitsModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Samples_Units')};
    END;'''
    SAMPLINGMETHODS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_samplingmethods AFTER UPDATE ON SamplingMethods
    BEGIN
        UPDATE "SamplingMethods" SET "SamplingMethodModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('SamplingMethods')};
    END;'''
    SETTINGS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_settings AFTER UPDATE ON Settings
    BEGIN
        UPDATE "Settings" SET "SettingModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Settings')};
    END;'''
    SOURCES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_sources AFTER UPDATE ON Sources
    BEGIN
        UPDATE "Sources" SET "SourceModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Sources')};
    END;'''
    SPOTCOMPOSITIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_spotcompositions AFTER UPDATE ON SpotCompositions
    BEGIN
        UPDATE "SpotCompositions" SET "SpotCompositionModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('SpotCompositions')};
    END;'''
    SPOTCONTEXT_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_spotcontexts AFTER UPDATE ON SpotContexts
    BEGIN
        UPDATE "SpotContexts" SET "SpotContextModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('SpotContexts')};
    END;'''
    SPOTS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_spots AFTER UPDATE ON Spots
    BEGIN
        UPDATE "Spots" SET "SpotModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Spots')};
    END;'''
    SPOTS_SPOTCOMPOSITIONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_spots_spotcompositions AFTER UPDATE ON Spots_SpotCompositions
    BEGIN
        UPDATE "Spots_SpotCompositions" SET "Spots_SpotCompositionsModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Spots_SpotCompositions')};
    END;'''
    SPOTS_SPOTCONTEXTS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_spots_spotcontexts AFTER UPDATE ON Spots_SpotContexts
    BEGIN
        UPDATE "Spots_SpotContexts" SET "Spots_SpotContextModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Spots_SpotContexts')};
    END;'''
    UNITS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_units AFTER UPDATE ON Units
    BEGIN
        UPDATE "Units" SET "UnitModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('Units')};
    END;'''
    UPBANALYSISMETHODS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_upbanalysismethods AFTER UPDATE ON UPbAnalysisMethods
    BEGIN
        UPDATE "UPbAnalysisMethods" SET "UPbAnalysisMethodModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('UPbAnalysisMethods')};
    END;'''
    UPBANALYSES_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_upbdata AFTER UPDATE ON UPbAnalyses
    BEGIN
        UPDATE "UPbAnalyses" SET "UPbAnalysisModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('UPbAnalyses')};
    END;'''
    UPBANALYSES_REJECTIONREASONS_MODIFIED_TRIGGER = f'''
    CREATE TRIGGER IF NOT EXISTS update_modified_upbanalyses_rejectionreasons AFTER UPDATE ON UPbAnalyses_RejectionReasons
    BEGIN
        UPDATE "UPbAnalyses_RejectionReasons" SET "UPbAnalyses_RejectionReasonsModified" = CURRENT_TIMESTAMP WHERE {modified_list_statement('UPbAnalyses_RejectionReasons')};
    END;'''

    query = QtS.QSqlQuery()

    query.exec(CREATE_COLUMN_UNITS_INSERT_TRIGGERS)
    query.exec(CREATE_COLUMN_UNITS_UPDATE_TRIGGERS)
    query.exec(CREATE_GPS_INSERT_TRIGGERS)
    query.exec(CREATE_GPS_UPDATE_TRIGGERS)
    query.exec(CREATE_SAMPLEAGES_INSERT_TRIGGERS)
    query.exec(CREATE_SAMPLEAGES_UPDATE_TRIGGERS)
    query.exec(CREATE_SAMPLES_INSERT_TRIGGERS)
    query.exec(CREATE_SAMPLES_UPDATE_TRIGGERS)
    query.exec(CREATE_UPBANALYSES_INSERT_TRIGGERS)
    query.exec(CREATE_UPBANALYSES_UPDATE_TRIGGERS)

    query.exec(ABOUT_MODIFIED_TRIGGER)
    query.exec(AGECONSTRAINTS_MODIFIED_TRIGGER)
    query.exec(AGE_CONVERSIONS_MODIFIED_TRIGGER)
    query.exec(AGEINTERPRETATIONS_MODIFIED_TRIGGER)
    query.exec(AGESIGNATURES_MODIFIED_TRIGGER)
    query.exec(AGEUNITS_MODIFIED_TRIGGER)
    query.exec(AGES_MODIFIED_TRIGGER)
    query.exec(ALIQUOTCONTEXT_MODIFIED_TRIGGER)
    query.exec(ALIQUOTS_MODIFIED_TRIGGER)
    query.exec(ALIQUOTS_ALIQUOTCONTEXT_MODIFIED_TRIGGER)
    query.exec(COLUMNS_MODIFIED_TRIGGER)
    query.exec(CONCORDANCETYPES_MODIFIED_TRIGGER)
    query.exec(CONCORDANCE_CONVERSIONS_MODIFIED_TRIGGER)
    query.exec(DIRECTIONUNITS_MODIFIED_TRIGGER)
    query.exec(DISTANCEUNITS_MODIFIED_TRIGGER)
    query.exec(DISTANCE_CONVERSIONS_MODIFIED_TRIGGER)
    query.exec(ERRORTYPES_MODIFIED_TRIGGER)
    query.exec(ERROR_CONVERSIONS_MODIFIED_TRIGGER)
    query.exec(GPS_CONVERSIONS_MODIFIED_TRIGGER)
    query.exec(GPS_FORMATS_MODIFIED_TRIGGER)
    query.exec(GPS_LOCATIONS_MODIFIED_TRIGGER)
    query.exec(FILTERGROUPS_MODIFIED_TRIGGER)
    query.exec(INSTRUMENTS_MODIFIED_TRIGGER)
    query.exec(LABFACILITIES_MODIFIED_TRIGGER)
    query.exec(REGIONS_MODIFIED_TRIGGER)
    query.exec(REJECTIONREASONS_MODIFIED_TRIGGER)
    query.exec(ROCKTYPES_MODIFIED_TRIGGER)
    query.exec(SAMPLEAGES_MODIFIED_TRIGGER)
    query.exec(SAMPLECONTEXT_MODIFIED_TRIGGER)
    query.exec(SAMPLEAGES_AGECONSTRAINTS_MODIFIED_TRIGGER)
    query.exec(SAMPLEAGES_AGEINTERPRETATIONS_MODIFIED_TRIGGER)
    query.exec(SAMPLEAGES_SOURCES_MODIFIED_TRIGGER)
    query.exec(SAMPLES_MODIFIED_TRIGGER)
    query.exec(SAMPLES_AGESIGNATURES_MODIFIED_TRIGGER)
    query.exec(SAMPLES_REGIONS_MODIFIED_TRIGGER)
    query.exec(SAMPLES_ROCKTYPES_MODIFIED_TRIGGER)
    query.exec(SAMPLES_SAMPLECONTEXT_MODIFIED_TRIGGER)
    query.exec(SAMPLES_SAMPLINGMETHODS_MODIFIED_RIGGER)
    query.exec(SAMPLES_SETTINGS_MODIFIED_TRIGGER)
    query.exec(SAMPLES_UNITS_MODIFIED_TRIGGER)
    query.exec(SAMPLINGMETHODS_MODIFIED_TRIGGER)
    query.exec(SETTINGS_MODIFIED_TRIGGER)
    query.exec(SOURCES_MODIFIED_TRIGGER)
    query.exec(SPOTCOMPOSITIONS_MODIFIED_TRIGGER)
    query.exec(SPOTCONTEXT_MODIFIED_TRIGGER)
    query.exec(SPOTS_MODIFIED_TRIGGER)
    query.exec(SPOTS_SPOTCOMPOSITIONS_MODIFIED_TRIGGER)
    query.exec(SPOTS_SPOTCONTEXTS_MODIFIED_TRIGGER)
    query.exec(UNITS_MODIFIED_TRIGGER)
    query.exec(UPBANALYSISMETHODS_MODIFIED_TRIGGER)
    query.exec(UPBANALYSES_MODIFIED_TRIGGER)
    query.exec(UPBANALYSES_REJECTIONREASONS_MODIFIED_TRIGGER)
