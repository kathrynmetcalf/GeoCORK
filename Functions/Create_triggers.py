import sqlite3

'''Commands to create the database triggers'''
'''SQL strings to create each trigger'''

'''Triggers for inserting empty required fields'''
INSERT_EMPTY_NAME_TRIGGERS = '''
CREATE TRIGGER validate_sample_name_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.SampleName IS NULL THEN
            RAISE (ABORT,'Name cannot be empty')
        END;
END;
CREATE TRIGGER validate_aliquot_name_before_insert BEFORE INSERT ON Aliquots
CREATE TRIGGER validate_spot_name_before_insert BEFORE INSERT ON Spots
CREATE TRIGGER validate_sample_context_name_before_insert BEFORE INSERT ON SampleContext
CREATE TRIGGER validate_aliquot_context_name_before_insert BEFORE INSERT ON AliquotContext
CREATE TRIGGER validate_spot_context_name_before_insert BEFORE INSERT ON SamplesContext
CREATE TRIGGER validate_spot_composition_name_before_insert BEFORE INSERT ON SamplesCompositions
CREATE TRIGGER validate_short_citation BEFORE INSERT ON Sources
CREATE TRIGGER validate_region_name_before_insert BEFORE INSERT ON Regions
CREATE TRIGGER validate_setting_name_before_insert BEFORE INSERT ON Settings
CREATE TRIGGER validate_column_name_before_insert BEFORE INSERT ON Columns
CREATE TRIGGER validate_sampling_method_name_before_insert BEFORE INSERT ON SamplingMethods
CREATE TRIGGER validate_rock_type_name_before_insert BEFORE INSERT ON RockTypes
CREATE TRIGGER validate_unit_name_before_insert BEFORE INSERT ON Units
CREATE TRIGGER validate_age_name_before_insert BEFORE INSERT ON Ages
CREATE TRIGGER validate_age_signature_name_before_insert BEFORE INSERT ON AgeSignatures
CREATE TRIGGER validate_lab_facility_name_before_insert BEFORE INSERT ON LabFacilities
CREATE TRIGGER validate_upb_analysis_method_name_before_insert BEFORE INSERT ON UPbAnalysisMethods
CREATE TRIGGER validate_instrument_name_before_insert BEFORE INSERT ON Instruments
CREATE TRIGGER validate_filter_group_name_before_insert BEFORE INSERT ON FilterGroups
CREATE TRIGGER validate_age_max_before_insert BEFORE INSERT ON Ages
CREATE TRIGGER validate_age_min_before_insert BEFORE INSERT ON Ages
'''

'''Triggers for updating empty required fields'''
UPDATE_EMPTY_NAME_TRIGGERS = '''
CREATE TRIGGER validate_sample_name_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.SampleName IS NULL THEN
            RAISE (ABORT,'Name cannot be empty')
        END;
END;
'''

'''Triggers for missing pairs and units, only triggers if there is corresponding data'''
'''e.g. there is latitude but not longitude or an elevation value but no unit'''
MISSING_PAIRS_TRIGGERS = '''
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
END;
CREATE TRIGGER validate_lonlat_deg_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN LonDeg IS NOT NULL AND LatDeg IS NULL THEN
            RAISE (ABORT,'Longitude degrees is missing corresponding latitude degrees')
        END;
END;
CREATE TRIGGER validate_utm_zone_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN UTMN IS NOT NULL AND UTMZone IS NULL THEN
            RAISE (ABORT,'UTM coordinates with missing zone')
        END;
END;
CREATE TRIGGER validate_utm_ne_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN UTMN IS NOT NULL AND UTME IS NULL THEN
            RAISE (ABORT,'UTM northing missing corresponding easting')
        END;
END;
CREATE TRIGGER validate_utm_en_before_update BEFORE UPDATE ON Samples
BEGIN
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

        c.execute(INSERT_EMPTY_NAME_TRIGGERS)
        c.execute(UPDATE_EMPTY_NAME_TRIGGERS)
        c.execute(MISSING_PAIRS_TRIGGERS)

if __name__ == '__main__':
    db_file = '../TestSchema.db'
    create_triggers(db_file)