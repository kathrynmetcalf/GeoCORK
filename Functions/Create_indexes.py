import sqlite3
import time

from PyQt6 import QtSql

import logger_setup

'''Commands to create the database indexes'''
'''SQL strings to create each index'''

'''Indexes to improve search performance'''
SEARCH_INDEXES = '''

'''

CREATE_AGE_CONSTRAINTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_AgeConstraints_AgeConstraintID ON AgeConstraints(AgeConstraintID)'''

CREATE_AGE_INTERPRETATIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_AgeInterpretations_AgeInterpretationID ON AgeInterpretations(AgeInterpretationID)'''

CREATE_AGE_SIGNATURES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_AgeSignatures_AgeSignatureID ON AgeSignatures(AgeSignatureID)'''

CREATE_AGE_UNITS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_AgeUnits_AgeUnitID ON AgeUnits(AgeUnitID)'''

CREATE_AGE_CONVERSIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_AgeUnitConversions_AgeUnitConversionID ON AgeUnitConversions(AgeUnitConversionID)'''

CREATE_AGES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Ages_AgeID ON Ages(AgeID)'''

CREATE_ALIQUOT_CONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_AliquotContexts_AliquotContextID ON AliquotContexts(AliquotContextID)'''

CREATE_ALIQUOTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Aliquots_AliquotID ON Aliquots(AliquotID)'''

CREATE_ALIQUOTS_ALIQUOTCONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Aliquots_Aliquots_AliquotContextID ON Aliquots_AliquotContexts(Aliquots_AliquotContextID)'''

CREATE_COLUMNS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Columns_ColumnID ON Columns(ColumnID)'''

CREATE_CONCORDANCE_FORMATS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_ConcordanceFormats_ConcordanceFormatID ON ConcordanceFormats(ConcordanceFormatID)'''

CREATE_CONCORDANCE_CONVERSIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_ConcordanceFormatConversions_FromConcordanceFormatID ON ConcordanceFormatConversions(FromConcordanceFormatID)'''

CREATE_DIRECTION_UNITS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_DirectionUnits_DirectionUnitID ON DirectionUnits(DirectionUnitID)'''

CREATE_DISTANCE_UNITS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_DistanceUnits_DistanceUnitID ON DistanceUnits(DistanceUnitID)'''

CREATE_DISTANCE_CONVERSIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_DistanceUnitConversions_FromDistanceUnitID ON DistanceUnitConversions(FromDistanceUnitID)'''

CREATE_ERROR_FORMATS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_ErrorFormats_ErrorFormatID ON ErrorFormats(ErrorFormatID)'''

CREATE_ERROR_CONVERSIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_ErrorFormatConversions_FromErrorFormatID ON ErrorFormatConversions(FromErrorFormatID)'''

CREATE_GPS_CONVERSIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_GPSFormatConversions_FromGPSFormatID ON GPSFormatConversions(FromGPSFormatID)'''

CREATE_GPS_FORMATS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_GPSFormats_GPSFormatID ON GPSFormats(GPSFormatID)'''

CREATE_GPS_LOCATIONS_INDEX = '''
                        CREATE INDEX IF NOT EXISTS idx_GPSLocations_GPSLocationID ON GPSLocations(GPSLocationID)'''

CREATE_FILTER_GROUPS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_FilterGroups_FilterGroupID ON FilterGroups(FilterGroupID)'''

CREATE_INSTRUMENTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Instruments_InstrumentID ON Instruments(InstrumentID)'''

CREATE_LAB_FACILITIES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_LabFacilities_LabFacilityID ON LabFacilities(LabFacilityID)'''

CREATE_REFERENCES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_References_ReferenceID ON "References"(ReferenceID)'''

CREATE_REGIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Regions_RegionID ON Regions(RegionID)'''

CREATE_REJECTION_REASONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_RejectionReasons_RejectionReasonID ON RejectionReasons(RejectionReasonID)'''

CREATE_ROCK_TYPES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_RockTypes_RockTypeID ON RockTypes(RockTypeID)'''

CREATE_SAMPLE_AGE_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SampleAges_SampleAgeID ON SampleAges(SampleAgeID)'''

CREATE_SAMPLE_CONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SampleContexts_SampleContextID ON SampleContexts(SampleContextID, SpotContextName)'''

CREATE_SAMPLEAGES_AGECONSTRAINTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SampleAges_AgeConstraints_SampleAgeID ON SampleAges_AgeConstraints(SampleAgeID, AgeConstraintID)'''

CREATE_SAMPLEAGES_AGEINTERPRETATIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SampleAges_AgeInterpretations_SampleAgeID ON SampleAges_AgeInterpretations(SampleAgeID, AgeInterpretationID)'''

CREATE_SAMPLEAGES_REFERENCES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SampleAges_References_SampleAgeID ON SampleAges_References(SampleAgeID, ReferenceID)'''

CREATE_SAMPLES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_SampleID ON Samples(SampleID, SampleName, SampleIGSN)'''

CREATE_SAMPLES_AGESIGNATURES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_AgeSignatures_SampleID ON Samples_AgeSignatures(SampleID, AgeSignatureID)'''

CREATE_SAMPLES_REGIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_Regions_SampleID ON Samples_Regions(SampleID, RegionID)'''

CREATE_SAMPLES_ROCKTYPES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_RockTypes_SampleID ON Samples_RockTypes(SampleID, RockTypeID)'''

CREATE_SAMPLES_SAMPLEAGES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_SampleAges_SampleID ON Samples_SampleAges(SampleID, SampleAgeID)'''

CREATE_SAMPLES_SAMPLECONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_SampleContexts_SampleID ON Samples_SampleContexts(SampleID, SampleContextID)'''

CREATE_SAMPLES_SAMPLINGMETHODS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_SamplingMethods_SampleID ON Samples_SamplingMethods(SampleID, SamplingMethodID)'''

CREATE_SAMPLES_SETTINGS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_Settings_SampleID ON Samples_Settings(SampleID, SettingID)'''

CREATE_SAMPLES_UNITS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_Units_SampleID ON Samples_Units(SampleID, UnitID)'''

CREATE_SAMPLING_METHODS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SamplingMethods_SamplingMethodID ON SamplingMethods(SamplingMethodID)'''

CREATE_SETTINGS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Settings_SettingID ON Settings(SettingID)'''

CREATE_SPOT_COMPOSITION_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SpotCompositions_SpotCompositionID ON SpotCompositions(SpotCompositionID)'''

CREATE_SPOT_CONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SpotContexts_SpotContextID ON SpotContexts(SpotContextID)'''

CREATE_SPOTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Spots_SpotID ON Spots(SpotID)'''

CREATE_SPOTS_SPOTCONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Spots_SpotContexts_SpotID ON Spots_SpotContexts(SpotID)'''

CREATE_UNITS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Units_UnitID ON Units(UnitID)'''

CREATE_UPBANALYSES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_UPbAnalysisID ON UPbAnalyses(UPbAnalysisID)'''

CREATE_UPBANALYSES_REJECTIONREASONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_UPbAnalysisID_UPbAnalyses_RejectionReasons_RejectionReasonID ON UPbAnalyses_RejectionReasons(UPbAnalysisID, RejectionReasonID)'''

CREATE_UPBANALYSIS_METHOD_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_UPbAnalysisMethods_UPbAnalysisMethodID ON UPbAnalysisMethods(UPbAnalysisMethodID)'''




def create_indexes():
    """
    Connect to the database and execute the sql strings defined above to create the database tables
    Only creates tables that do not already exist - does not overwrite existing tables
    If the Ages table is empty, it will fill it from the Geologic timescale xml file
    Populates the units, formats, and conversion tables
    Uses the default database connection
    """
    start_time = time.time()
    logger_setup.get_logger().info('Creating database indexes')
    query = QtSql.QSqlQuery()


    # Create unit and format tables
    query.exec(CREATE_AGE_UNITS_INDEX)
    query.exec(CREATE_CONCORDANCE_FORMATS_INDEX)
    query.exec(CREATE_DIRECTION_UNITS_INDEX)
    query.exec(CREATE_DISTANCE_UNITS_INDEX)
    query.exec(CREATE_ERROR_FORMATS_INDEX)

    # Create conversion tables
    query.exec(CREATE_AGE_CONVERSIONS_INDEX)
    query.exec(CREATE_CONCORDANCE_CONVERSIONS_INDEX)
    query.exec(CREATE_DISTANCE_CONVERSIONS_INDEX)
    query.exec(CREATE_ERROR_CONVERSIONS_INDEX)

    # Create analysis tag tables
    query.exec(CREATE_INSTRUMENTS_INDEX)
    query.exec(CREATE_LAB_FACILITIES_INDEX)
    query.exec(CREATE_REJECTION_REASONS_INDEX)
    query.exec(CREATE_REFERENCES_INDEX)
    query.exec(CREATE_UPBANALYSIS_METHOD_INDEX)

    # Create spot tag tables
    query.exec(CREATE_SPOT_COMPOSITION_INDEX)
    query.exec(CREATE_SPOT_CONTEXT_INDEX)

    # Create aliquot tag tables
    query.exec(CREATE_ALIQUOT_CONTEXT_INDEX)

    # Create sample tag tables
    query.exec(CREATE_AGE_CONSTRAINTS_INDEX)
    query.exec(CREATE_AGE_INTERPRETATIONS_INDEX) # Shared with upb analyses
    query.exec(CREATE_AGE_SIGNATURES_INDEX)
    query.exec(CREATE_AGES_INDEX)
    query.exec(CREATE_COLUMNS_INDEX)
    query.exec(CREATE_GPS_CONVERSIONS_INDEX)
    query.exec(CREATE_GPS_FORMATS_INDEX)
    query.exec(CREATE_GPS_LOCATIONS_INDEX)
    query.exec(CREATE_REGIONS_INDEX)
    query.exec(CREATE_ROCK_TYPES_INDEX)
    query.exec(CREATE_SAMPLE_AGE_INDEX)
    query.exec(CREATE_SAMPLE_CONTEXT_INDEX)
    query.exec(CREATE_SAMPLEAGES_AGECONSTRAINTS_INDEX)
    query.exec(CREATE_SAMPLEAGES_AGEINTERPRETATIONS_INDEX)
    query.exec(CREATE_SAMPLEAGES_REFERENCES_INDEX)
    query.exec(CREATE_SAMPLING_METHODS_INDEX)
    query.exec(CREATE_SETTINGS_INDEX)
    query.exec(CREATE_UNITS_INDEX)

    # Create sample item and analysis tables
    query.exec(CREATE_SAMPLES_INDEX)
    query.exec(CREATE_ALIQUOTS_INDEX)
    query.exec(CREATE_SPOTS_INDEX)
    query.exec(CREATE_UPBANALYSES_INDEX)

    # Create many-to-many sample tables
    query.exec(CREATE_SAMPLES_AGESIGNATURES_INDEX)
    query.exec(CREATE_SAMPLES_REGIONS_INDEX)
    query.exec(CREATE_SAMPLES_ROCKTYPES_INDEX)
    query.exec(CREATE_SAMPLES_SAMPLEAGES_INDEX)
    query.exec(CREATE_SAMPLES_SAMPLECONTEXT_INDEX)
    query.exec(CREATE_SAMPLES_SAMPLINGMETHODS_INDEX)
    query.exec(CREATE_SAMPLES_SETTINGS_INDEX)
    query.exec(CREATE_SAMPLES_UNITS_INDEX)

    # Create many-to-many anliquot tables
    query.exec(CREATE_ALIQUOTS_ALIQUOTCONTEXT_INDEX)

    # Create many-to-many spot tables
    query.exec(CREATE_SPOTS_SPOTCONTEXT_INDEX)

    # Create many-to-many analysis tables
    query.exec(CREATE_UPBANALYSES_REJECTIONREASONS_INDEX)

    query.exec(CREATE_FILTER_GROUPS_INDEX)

    end_time = time.time()
    logger_setup.get_logger().info(f'Database indexes created in {end_time - start_time} seconds')
