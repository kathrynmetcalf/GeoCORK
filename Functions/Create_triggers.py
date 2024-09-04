import sqlite3

'''Commands to create the database triggers'''
'''SQL strings to create each trigger'''

'''Triggers for missing pairs and units, only triggers if there is corresponding data'''
'''e.g. there is latitude but not longitude or an elevation value but no unit'''
INSERT_HD_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_hd_units_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
END;'''
INSERT_ELEV_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_elev_units_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.Elev IS NOT NULL AND NEW.ElevUnit IS NULL THEN
            RAISE (ABORT,'Elevation value with missing units')
        END;
END;'''
INSERT_SPOT_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_spot_units_before_insert BEFORE INSERT ON UPbData
BEGIN
    SELECT CASE
        WHEN NEW.SpotSize IS NOT NULL AND NEW.SpotSizeUnit IS NULL THEN
            RAISE (ABORT,'Spot size value with missing units')
        END;
END;
'''
INSERT_LATLON_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_latlon_deg_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.LonDeg IS NULL THEN
            RAISE (ABORT,'Latitude degrees is missing corresponding longitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LonDeg IS NOT NULL AND NEW.LatDeg IS NULL THEN
            RAISE (ABORT,'Longitude degrees is missing corresponding latitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
        END;
END;
'''
INSERT_UTM_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_utm_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTMZone IS NULL THEN
            RAISE (ABORT,'UTM coordinates with missing zone')
        END;
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTME IS NULL THEN
            RAISE (ABORT,'UTM northing missing corresponding easting')
        END;
    SELECT CASE
        WHEN NEW.UTME IS NOT NULL AND NEW.UTMN IS NULL THEN
            RAISE (ABORT,'UTM easting missing corresponding northing')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
        END;
END;
'''

UPDATE_HD_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_hd_units_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
END;
'''
UPDATE_ELEV_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_elev_units_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.Elev IS NOT NULL AND NEW.ElevUnit IS NULL THEN
            RAISE (ABORT,'Elevation value with missing units')
        END;
END;
'''
UPDATE_SPOT_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_spot_units_before_update BEFORE UPDATE ON UPbData
BEGIN
    SELECT CASE
        WHEN NEW.SpotSize IS NOT NULL AND NEW.SpotSizeUnit IS NULL THEN
            RAISE (ABORT,'Spot size value with missing units')
        END;
END;
'''
UPDATE_LATLON_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_latlon_deg_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.LonDeg IS NULL THEN
            RAISE (ABORT,'Latitude degrees is missing corresponding longitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LonDeg IS NOT NULL AND NEW.LatDeg IS NULL THEN
            RAISE (ABORT,'Longitude degrees is missing corresponding latitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
        END;
END;
'''
UPDATE_UTM_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS validate_utm_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTMZone IS NULL THEN
            RAISE (ABORT,'UTM coordinates with missing zone')
        END;
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTME IS NULL THEN
            RAISE (ABORT,'UTM northing missing corresponding easting')
        END;
    SELECT CASE
        WHEN NEW.UTME IS NOT NULL AND NEW.UTMN IS NULL THEN
            RAISE (ABORT,'UTM easting missing corresponding northing')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
        END;
END;
'''

# Triggers to update the modified timestamp when a value is updated
AGESIGNATURES_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_agesignatures AFTER UPDATE ON AgeSignatures
BEGIN
    UPDATE AgeSignatures SET AgeSignatureModified = CURRENT_TIMESTAMP WHERE AgeSignatureID = NEW.AgeSignatureID OR ParentAgeSignatureID = NEW.ParentAgeSignatureID OR AgeSignatureName = NEW.AgeSignatureName OR AgeSignatureDescription = NEW.AgeSignatureDescription;
END;
'''
AGES_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_ages AFTER UPDATE ON Ages
BEGIN
    UPDATE Ages SET AgeModified = CURRENT_TIMESTAMP WHERE AgeID = NEW.AgeID OR ParentAgeID = NEW.ParentAgeID OR AgeName = NEW.AgeName OR MaxMa = NEW.MaxMa OR MinMa = NEW.MinMa;
END;
'''
UNITS_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_units AFTER UPDATE ON Units
BEGIN
    UPDATE Units SET UnitModified = CURRENT_TIMESTAMP WHERE UnitID = NEW.UnitID OR ParentUnitID = NEW.ParentUnitID OR UnitName = NEW.UnitName OR UnitDescription = NEW.UnitDescription;
END;
'''

def create_triggers(c):
    """
    Take database cursor and execute the sql strings defined above to create the database triggers
    :param c: Cursor of database connection
    """
    c.execute(INSERT_HD_TRIGGER)
    c.execute(INSERT_ELEV_TRIGGER)
    c.execute(INSERT_SPOT_TRIGGER)
    c.execute(INSERT_LATLON_TRIGGER)
    c.execute(INSERT_UTM_TRIGGER)
    c.execute(UPDATE_HD_TRIGGER)
    c.execute(UPDATE_ELEV_TRIGGER)
    c.execute(UPDATE_SPOT_TRIGGER)
    c.execute(UPDATE_LATLON_TRIGGER)
    c.execute(UPDATE_UTM_TRIGGER)
    c.execute(UNITS_TRIGGER)

if __name__ == '__main__':
    db_file = '../TestSchema.db'
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        create_triggers(db_file)