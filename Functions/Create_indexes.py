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
                    CREATE INDEX IF NOT EXISTS idx_AgeUnitConversions_AgeUnitConversionID ON AgeUnitConversions(FromAgeUnitID)'''

CREATE_AGES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Ages_AgeID ON Ages(AgeID)'''

CREATE_ALIQUOT_CONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_AliquotContexts_AliquotContextID ON AliquotContexts(AliquotContextID)'''

CREATE_ALIQUOTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Aliquots_AliquotID ON Aliquots(AliquotID)'''

CREATE_ALIQUOTS_ALIQUOTCONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Aliquots_Aliquots_AliquotContextID ON Aliquots_AliquotContexts(AliquotID, AliquotContextID)'''

CREATE_ALIQUOTS_SAMPLES_INDEX = '''CREATE INDEX IF NOT EXISTS idx_Aliquots_SampleID ON Aliquots(SampleID)'''

CREATE_COLUMNS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Columns_ColumnID ON Columns(ColumnID)'''

CREATE_COLUMNS_GPSLOCATIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Columns_GPSLocations_ColumnID ON Columns(ColumnID, ColumnBaseGPSID)'''

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
                    CREATE INDEX IF NOT EXISTS idx_SampleContexts_SampleContextID ON SampleContexts(SampleContextID, SampleContextName)'''

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

CREATE_SAMPLES_GPSLOCATIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Samples_GPSLocations_GPSLocationID ON Samples(SampleID, SampleGPSLocationID)'''

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

CREATE_SPOTS_ALIQUOT_INDEX = '''CREATE INDEX IF NOT EXISTS idx_Spots_AliquotID ON Spots(AliquotID)'''

CREATE_UNITS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Units_UnitID ON Units(UnitID)'''

CREATE_UPBANALYSES_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_UPbAnalysisID ON UPbAnalyses(UPbAnalysisID)'''

CREATE_UPBANALYSES_REJECTIONREASONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_UPbAnalysisID_UPbAnalyses_RejectionReasons_RejectionReasonID ON UPbAnalyses_RejectionReasons(UPbAnalysisID, RejectionReasonID)'''

CREATE_UPBANALYSES_SPOTS_INDEX = '''CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_SpotID ON UPbAnalyses(SpotID)'''

CREATE_UPBANALYSES_REFERENCE_INDEX = '''CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_ReferenceID ON UPbAnalyses(ReferenceID);'''

CREATE_UPBANALYSES_LABFACILITY_INDEX = '''CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_LabFacilityID ON UPbAnalyses(LabFacilityID);'''

CREATE_UPBANALYSES_INSTRUMENT_INDEX = '''CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_InstrumentID ON UPbAnalyses(InstrumentID);'''

CREATE_UPBANALYSES_UPBANALYSISMETHODS_INDEX = '''CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_UPbAnalysisMethodID ON UPbAnalyses(UPbAnalysisMethodID);'''

CREATE_UPBANALYSIS_METHOD_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_UPbAnalysisMethods_UPbAnalysisMethodID ON UPbAnalysisMethods(UPbAnalysisMethodID)'''


def create_indexes() -> bool:
    """
    Connect to the database and execute the sql strings defined above to create the database tables
    Only creates tables that do not already exist - does not overwrite existing tables
    If the Ages table is empty, it will fill it from the Geologic timescale xml file
    Populates the units, formats, and conversion tables
    Uses the default database connection
    :return: True on success, False on failure
    :rtype: bool
    """
    start_time = time.time()
    logger_setup.get_logger().info('Creating database indexes')
    query = QtSql.QSqlQuery()

    # Create unit and format tables
    if not query.exec(CREATE_AGE_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeUnits index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_AGE_UNITS_INDEX}')
        return False

    if not query.exec(CREATE_CONCORDANCE_FORMATS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ConcordanceFormats index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_CONCORDANCE_FORMATS_INDEX}')
        return False

    if not query.exec(CREATE_DIRECTION_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating DirectionUnits index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_DIRECTION_UNITS_INDEX}')
        return False

    if not query.exec(CREATE_DISTANCE_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating DistanceUnits index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_DISTANCE_UNITS_INDEX}')
        return False

    if not query.exec(CREATE_ERROR_FORMATS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ErrorFormats index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_ERROR_FORMATS_INDEX}')
        return False

    if not query.exec(CREATE_GPS_FORMATS_INDEX):
        logger_setup.get_logger().critical(f'Error creating GPSFormats index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_GPS_FORMATS_INDEX}')
        return False

    # Create conversion table
    if not query.exec(CREATE_AGE_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeConversions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_AGE_CONVERSIONS_INDEX}')
        return False

    if not query.exec(CREATE_CONCORDANCE_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ConcordanceConversions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_CONCORDANCE_CONVERSIONS_INDEX}')
        return False

    if not query.exec(CREATE_DISTANCE_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating DistanceConvesions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_DISTANCE_CONVERSIONS_INDEX}')
        return False

    if not query.exec(CREATE_ERROR_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ErrorConversions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_ERROR_CONVERSIONS_INDEX}')
        return False

    if not query.exec(CREATE_GPS_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating GPSConversions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_GPS_CONVERSIONS_INDEX}')
        return False

    # Create analysis tag tables
    if not query.exec(CREATE_INSTRUMENTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Instruments index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_INSTRUMENTS_INDEX}')
        return False

    if not query.exec(CREATE_LAB_FACILITIES_INDEX):
        logger_setup.get_logger().critical(f'Error creating LabFacilities index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_LAB_FACILITIES_INDEX}')
        return False

    if not query.exec(CREATE_REJECTION_REASONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating RejectionReasons index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_REJECTION_REASONS_INDEX}')
        return False

    if not query.exec(CREATE_REFERENCES_INDEX):
        logger_setup.get_logger().critical(f'Error creating References index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_REFERENCES_INDEX}')
        return False

    if not query.exec(CREATE_UPBANALYSIS_METHOD_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSIS_METHOD_INDEX}')
        return False

    # Create spot tag tables
    if not query.exec(CREATE_SPOT_COMPOSITION_INDEX):
        logger_setup.get_logger().critical(f'Error creating SpotCompositions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SPOT_COMPOSITION_INDEX}')
        return False

    if not query.exec(CREATE_SPOT_CONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating SpotContexts index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SPOT_CONTEXT_INDEX}')
        return False

    # Create aliquot tag tables
    if not query.exec(CREATE_ALIQUOT_CONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating AliquotContexts index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_ALIQUOT_CONTEXT_INDEX}')
        return False

    # Create sample tag tables
    if not query.exec(CREATE_AGE_CONSTRAINTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeConstraints index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_AGE_CONSTRAINTS_INDEX}')
        return False

    if not query.exec(CREATE_AGE_INTERPRETATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeInterpretations index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_AGE_INTERPRETATIONS_INDEX}')
        return False

    if not query.exec(CREATE_AGE_SIGNATURES_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeSignatures index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_AGE_SIGNATURES_INDEX}')
        return False

    if not query.exec(CREATE_AGES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Ages index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_AGES_INDEX}')
        return False

    if not query.exec(CREATE_COLUMNS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Columns index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_COLUMNS_INDEX}')
        return False

    if not query.exec(CREATE_GPS_LOCATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating GPSLocations index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_GPS_LOCATIONS_INDEX}')
        return False

    if not query.exec(CREATE_REGIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Regions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_REGIONS_INDEX}')
        return False

    if not query.exec(CREATE_ROCK_TYPES_INDEX):
        logger_setup.get_logger().critical(f'Error creating RockTypes index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_ROCK_TYPES_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLE_AGE_INDEX):
        logger_setup.get_logger().critical(f'Error creating SampleAges index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLE_AGE_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLE_CONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating SampleContexts index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLE_CONTEXT_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLEAGES_AGECONSTRAINTS_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating SampleAges_AgeConstraints index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLEAGES_AGECONSTRAINTS_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLEAGES_AGEINTERPRETATIONS_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating SampleAges_AgeInterpretations index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLEAGES_AGEINTERPRETATIONS_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLEAGES_REFERENCES_INDEX):
        logger_setup.get_logger().critical(f'Error creating SampleAges_References index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLEAGES_REFERENCES_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLING_METHODS_INDEX):
        logger_setup.get_logger().critical(f'Error creating SamplingMethods index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLING_METHODS_INDEX}')
        return False

    if not query.exec(CREATE_SETTINGS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Settings index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SETTINGS_INDEX}')
        return False

    if not query.exec(CREATE_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Units index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UNITS_INDEX}')
        return False

    # Create sample item and analysis indexes
    if not query.exec(CREATE_SAMPLES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_INDEX}')
        return False

    if not query.exec(CREATE_ALIQUOTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Aliquots index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_ALIQUOTS_INDEX}')
        return False

    if not query.exec(CREATE_SPOTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Spots index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SPOTS_INDEX}')
        return False

    if not query.exec(CREATE_UPBANALYSES_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSES_INDEX}')
        return False

    # Create many-to-many sample indexes
    if not query.exec(CREATE_SAMPLES_AGESIGNATURES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_AgeSignatures index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_AGESIGNATURES_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_REGIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_Regions index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_REGIONS_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_ROCKTYPES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_RockTypes index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_ROCKTYPES_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_SAMPLEAGES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_SampleAges index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_SAMPLEAGES_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_SAMPLECONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_SampleContext index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_SAMPLECONTEXT_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_SAMPLINGMETHODS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_SamplingMethods index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_SAMPLINGMETHODS_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_SETTINGS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_Settings index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_SETTINGS_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_Units index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_UNITS_INDEX}')
        return False

    # Create many-to-many aliquot tables
    if not query.exec(CREATE_ALIQUOTS_ALIQUOTCONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating Aliquots_AliquotContexts index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_ALIQUOTS_ALIQUOTCONTEXT_INDEX}')
        return False

    # Create many-to-many spot tables
    if not query.exec(CREATE_SPOTS_SPOTCONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating Spots_SpotsContexts index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SPOTS_SPOTCONTEXT_INDEX}')
        return False

    # Create many-to-many analysis tables
    if not query.exec(CREATE_UPBANALYSES_REJECTIONREASONS_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating UPbAnalyses_RejectionReasons index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSES_REJECTIONREASONS_INDEX}')
        return False

    if not query.exec(CREATE_FILTER_GROUPS_INDEX):
        logger_setup.get_logger().critical(f'Error creating FilterGroups index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_FILTER_GROUPS_INDEX}')
        return False

    # Create foreign key indexes
    if not query.exec(CREATE_COLUMNS_GPSLOCATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Columns_GPSLocations index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_COLUMNS_GPSLOCATIONS_INDEX}')
        return False

    if not query.exec(CREATE_SAMPLES_GPSLOCATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_GPSLocations index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SAMPLES_GPSLOCATIONS_INDEX}')
        return False

    if not query.exec(CREATE_ALIQUOTS_SAMPLES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Aliquots_Samples index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_ALIQUOTS_SAMPLES_INDEX}')
        return False

    if not query.exec(CREATE_SPOTS_ALIQUOT_INDEX):
        logger_setup.get_logger().critical(f'Error creating Spots_Aliquots index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_SPOTS_ALIQUOT_INDEX}')
        return False

    if not query.exec(CREATE_UPBANALYSES_SPOTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_Spots index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSES_SPOTS_INDEX}')
        return False

    if not query.exec(CREATE_UPBANALYSES_REFERENCE_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_Spots index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSES_REFERENCE_INDEX}')
        return False

    if not query.exec(CREATE_UPBANALYSES_LABFACILITY_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating UPbAnalyses_LabFacilities index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSES_LABFACILITY_INDEX}')
        return False

    if not query.exec(CREATE_UPBANALYSES_INSTRUMENT_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalsyses_Instruments index: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSES_INSTRUMENT_INDEX}')
        return False

    if not query.exec(CREATE_UPBANALYSES_UPBANALYSISMETHODS_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating UPbAnalyses_UPbAnalysisMethodsindex: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL command: {CREATE_UPBANALYSES_UPBANALYSISMETHODS_INDEX}')
        return False

    end_time = time.time()
    logger_setup.get_logger().info(f'Database indexes created in {end_time - start_time} seconds')
    return True


def drop_all_indexes() -> bool:
    """
        Connect to the database and execute the sql strings defined above to create the database tables
        Only creates tables that do not already exist - does not overwrite existing tables
        If the Ages table is empty, it will fill it from the Geologic timescale xml file
        Populates the units, formats, and conversion tables
        Uses the default database connection
        :return: True on success, False on failure
        :rtype: bool
        """
    start_time = time.time()
    logger_setup.get_logger().info('Dropping all database indexes')
    query = QtSql.QSqlQuery()

    # Fetch all index names from sqlite_master
    if not query.exec("SELECT name FROM sqlite_master WHERE type='index'"):
        logger_setup.get_logger().critical(f"Failed to list indexes: {query.lastError().text()}")
        return False

    index_names = []
    while query.next():
        if 'sqlite' not in query.value(0):
            index_names.append(query.value(0))

    # Drop each index
    for idx_name in index_names:
        drop_statement = f"DROP INDEX IF EXISTS [{idx_name}]"
        if not query.exec(drop_statement):
            logger_setup.get_logger().critical(f"Error dropping index '{idx_name}': {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL command: {drop_statement}")
            return False
        else:
            logger_setup.get_logger().debug(f"Successfully dropped index '{idx_name}'")

    end_time = time.time()
    logger_setup.get_logger().info(f'Database indexes dropped in {end_time - start_time} seconds')
    return True
