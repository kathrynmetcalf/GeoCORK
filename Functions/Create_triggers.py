import sqlite3

'''Commands to create the database triggers'''
'''SQL strings to create each trigger'''

'''Triggers for missing pairs and units, only triggers if there is corresponding data'''
'''e.g. there is latitude but not longitude or an elevation value but no unit'''
INSERT_MISSING_PAIRS_TRIGGERS = '''
CREATE TRIGGER validate_hd_units_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
END;
CREATE TRIGGER validate_elev_units_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN Elev IS NOT NULL AND ElevUnit IS NULL THEN
            RAISE (ABORT,'Elevation value with missing units')
        END;
END;
CREATE TRIGGER validate_spot_units_before_insert BEFORE INSERT ON UPbData
BEGIN
    SELECT CASE
        WHEN SpotSize IS NOT NULL AND SpotSizeUnit IS NULL THEN
            RAISE (ABORT,'Spot size value with missing units')
        END;
END;
CREATE TRIGGER validate_latlon_deg_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN LatDeg IS NOT NULL AND LonDeg IS NULL THEN
            RAISE (ABORT,'Latitude degrees is missing corresponding longitude degrees')
        END;
    SELECT CASE
        WHEN LonDeg IS NOT NULL AND LatDeg IS NULL THEN
            RAISE (ABORT,'Longitude degrees is missing corresponding latitude degrees')
        END;
END;
CREATE TRIGGER validate_utm_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN UTMN IS NOT NULL AND UTMZone IS NULL THEN
            RAISE (ABORT,'UTM coordinates with missing zone')
        END;
    SELECT CASE
        WHEN UTMN IS NOT NULL AND UTME IS NULL THEN
            RAISE (ABORT,'UTM northing missing corresponding easting')
        END;
    SELECT CASE
        WHEN UTME IS NOT NULL AND UTMN IS NULL THEN
            RAISE (ABORT,'UTM easting missing corresponding northing')
        END;
END;
'''

UPDATE_MISSING_PAIRS_TRIGGERS = '''
CREATE TRIGGER validate_hd_units_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
END;
CREATE TRIGGER validate_elev_units_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN Elev IS NOT NULL AND ElevUnit IS NULL THEN
            RAISE (ABORT,'Elevation value with missing units')
        END;
END;
CREATE TRIGGER validate_spot_units_before_update BEFORE UPDATE ON UPbData
BEGIN
    SELECT CASE
        WHEN SpotSize IS NOT NULL AND SpotSizeUnit IS NULL THEN
            RAISE (ABORT,'Spot size value with missing units')
        END;
END;
CREATE TRIGGER validate_latlon_deg_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN LatDeg IS NOT NULL AND LonDeg IS NULL THEN
            RAISE (ABORT,'Latitude degrees is missing corresponding longitude degrees')
        END;
    SELECT CASE
        WHEN LonDeg IS NOT NULL AND LatDeg IS NULL THEN
            RAISE (ABORT,'Longitude degrees is missing corresponding latitude degrees')
        END;
END;
CREATE TRIGGER validate_utm_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN UTMN IS NOT NULL AND UTMZone IS NULL THEN
            RAISE (ABORT,'UTM coordinates with missing zone')
        END;
    SELECT CASE
        WHEN UTMN IS NOT NULL AND UTME IS NULL THEN
            RAISE (ABORT,'UTM northing missing corresponding easting')
        END;
    SELECT CASE
        WHEN UTME IS NOT NULL AND UTMN IS NULL THEN
            RAISE (ABORT,'UTM easting missing corresponding northing')
        END;
END;
'''

def create_triggers(db_file):
    """
    Connect to the database and execute the sql strings defined above to create the database indexes
    :param db_file: Database file with full path
    """
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()

        c.execute(INSERT_MISSING_PAIRS_TRIGGERS)
        c.execute(UPDATE_MISSING_PAIRS_TRIGGERS)

if __name__ == '__main__':
    db_file = '../TestSchema.db'
    create_triggers(db_file)