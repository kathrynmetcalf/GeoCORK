import sqlite3

'''Commands to create the database indexes'''
'''SQL strings to create each index'''

'''All the fields the user sees which must be unique to avoid confusion. 
Attempts to insert a duplicate name will raise an error'''
UNIQUE_NAME_INDEXES = '''
CREATE UNIQUE INDEX idx_sample_name ON Samples (SampleName)
CREATE UNIQUE INDEX idx_aliquot_name ON Aliquots (AliquotName)
CREATE UNIQUE INDEX idx_spot_name ON Spots (SpotName)
CREATE UNIQUE INDEX idx_sample_context_name ON SampleContext (SampleContextName)
CREATE UNIQUE INDEX idx_aliquot_context_name ON AliquotContext (AliquotContextName)
CREATE UNIQUE INDEX idx_spot_context_name ON SamplesContext (SpotContextName)
CREATE UNIQUE INDEX idx_spot_composition_name ON SamplesCompositions (SpotCompositionName)
CREATE UNIQUE INDEX idx_short_citation ON Sources (ShortCitation)
CREATE UNIQUE INDEX idx_region_name ON Regions (RegionName)
CREATE UNIQUE INDEX idx_setting_name ON Settings (SettingName)
CREATE UNIQUE INDEX idx_column_name ON Columns (ColumnName)
CREATE UNIQUE INDEX idx_sampling_method_name ON SamplingMethods (SamplingMethodName)
CREATE UNIQUE INDEX idx_rock_type_name ON RockTypes (RockTypeName)
CREATE UNIQUE INDEX idx_unit_name ON Units (UnitName)
CREATE UNIQUE INDEX idx_age_name ON Ages (AgeName)
CREATE UNIQUE INDEX idx_age_signature_name ON AgeSignatures (AgeSignatureName)
CREATE UNIQUE INDEX idx_lab_facility_name ON LabFacilities (LabFacilityName)
CREATE UNIQUE INDEX idx_upb_analysis_method_name ON UPbAnalysisMethods (UPbAnalysisName)
CREATE UNIQUE INDEX idx_instrument_name ON Instruments (InstrumentName)
CREATE UNIQUE INDEX idx_filter_group_name ON FilterGroups (FilterGroupName)
'''

def create_indexes(db_file):
    """
    Connect to the database and execute the sql strings defined above to create the database indexes
    :param db_file: Database file with full path
    """
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()

        c.execute(UNIQUE_NAME_INDEXES)

if __name__ == '__main__':
    db_file = '../TestSchema.db'
    create_indexes(db_file)