import sqlite3
import time

from PyQt6 import QtSql
from PyQt6.QtWidgets import QProgressDialog, QApplication

import logger_setup
from Functions.LoadingDialog_manager import LoadingDialogManager

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

CREATE_ALIQUOTS_SAMPLES_COMPOSITE_INDEX = '''CREATE INDEX IF NOT EXISTS idx_Aliquots_AliquotID_SampleID ON Aliquots(SampleID, AliquotID, AliquotName)'''

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

CREATE_GRAINS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Grains_GrainID ON Grains(GrainID)'''

CREATE_GRAIN_CONTEXTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_GrainContexts_GrainContextID ON GrainContexts(GrainContextID)'''

CREATE_GRAIN_COMPOSITIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_GrainCompositions_GrainCompositionID ON GrainCompositions(GrainCompositionID)'''

CREATE_GRAINS_CONTEXTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Grains_GrainContexts_GrainID ON Grains_GrainContexts(GrainID, GrainContextID)'''

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

CREATE_SPOT_COMPOSITIONS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SpotCompositions_SpotCompositionID ON SpotCompositions(SpotCompositionID)'''

CREATE_SPOT_CONTEXT_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_SpotContexts_SpotContextID ON SpotContexts(SpotContextID)'''

CREATE_SPOTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_Spots_SpotID ON Spots(SpotID)'''

CREATE_SPOTS_ALIQUOTS_INDEX = '''CREATE INDEX IF NOT EXISTS idx_Spots_AliquotID ON Spots(AliquotID)'''

CREATE_SPOTS_ALIQUOTS_COMPOSITE_INDEX = '''CREATE INDEX IF NOT EXISTS idx_Spots_SpotID_AliquotID ON Spots(AliquotID, SpotID)'''

CREATE_SPOTS_GRAINS_INDEX = '''CREATE INDEX IF NOT EXISTS idx_Spots_GrainsID ON Spots(GrainID)'''

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

CREATE_UPBANALYSIS_CONTEXT_INDEX = '''CREATE INDEX IF NOT EXISTS idx_UPbAnalysisContexts_UPbAnalysisContextID ON UPbAnalysisContexts(UPbAnalysisContextID)'''

CREATE_UPBANALYSES_UPBANALYSISCONTEXTS_INDEX = '''
                    CREATE INDEX IF NOT EXISTS idx_UPbAnalyses_UPbAnalysisContexts_UPbAnalysisContextID ON UPbAnalyses_UpbAnalysisContexts(UPbAnalysisContextID)'''


def create_indexes(database=None) -> bool:
    """
    Connect to the database and execute the sql strings defined above to create the database tables.
    Only creates tables that do not already exist - does not overwrite existing tables.
    If the Ages table is empty, it will fill it from the Geologic timescale xml file.
    Populates the units, formats, and conversion tables.
    Uses the default database connection if no database is provided.
    :param database: QSqlDatabase instance to create tables in, if None uses the default connection
    :return: True on success, False on failure
    :rtype: bool
    """
    loading_manager = LoadingDialogManager.get_instance()
    start_time = time.time()

    if not drop_all_indexes(database):
        return False

    logger_setup.get_logger().info('Creating database indexes')
    if database is None:
        query = QtSql.QSqlQuery()
    else:
        query = QtSql.QSqlQuery(database)

    total_indexes = 68
    index_count = 0
    index_progress = QProgressDialog('Indexing database...', 'Cancel', 0, total_indexes, loading_manager.dialog)
    index_progress.setMinimumDuration(0)

    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create unit and format tables
    if not query.exec(CREATE_AGE_UNITS_INDEX):
        # If the index already exists, ignore the error
        if 'already exists' in query.lastError().text():
            logger_setup.get_logger().debug('AgeUnits index already exists')
        else:
            logger_setup.get_logger().critical(f'Error creating AgeUnits index')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            loading_manager.close_loading_dialog('Loading', 'Indexing database...')
            return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    if not query.exec(CREATE_CONCORDANCE_FORMATS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ConcordanceFormats index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_DIRECTION_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating DirectionUnits index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_DISTANCE_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating DistanceUnits index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_ERROR_FORMATS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ErrorFormats index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_GPS_FORMATS_INDEX):
        logger_setup.get_logger().critical(f'Error creating GPSFormats index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create conversion table
    if not query.exec(CREATE_AGE_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeConversions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_CONCORDANCE_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ConcordanceConversions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_DISTANCE_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating DistanceConvesions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_ERROR_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating ErrorConversions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_GPS_CONVERSIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating GPSConversions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create analysis tag tables
    if not query.exec(CREATE_INSTRUMENTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Instruments index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_LAB_FACILITIES_INDEX):
        logger_setup.get_logger().critical(f'Error creating LabFacilities index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_REJECTION_REASONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating RejectionReasons index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_REFERENCES_INDEX):
        logger_setup.get_logger().critical(f'Error creating References index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSIS_METHOD_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSIS_CONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSES_UPBANALYSISCONTEXTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    # Create spot tag tables
    if not query.exec(CREATE_SPOT_COMPOSITIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating SpotCompositions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SPOT_CONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating SpotContexts index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # if not query.exec(CREATE_SPOTS_SPOTCONTEXTS_INDEX):
    #     logger_setup.get_logger().critical(f'Error creating SpotContexts index')
    #     logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
    #     logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
    #     loading_manager.close_loading_dialog('Loading', 'Indexing database...')
    #     return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create aliquot tag tables
    if not query.exec(CREATE_ALIQUOT_CONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating AliquotContexts index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create sample tag tables
    if not query.exec(CREATE_AGE_CONSTRAINTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeConstraints index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_AGE_INTERPRETATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeInterpretations index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_AGE_SIGNATURES_INDEX):
        logger_setup.get_logger().critical(f'Error creating AgeSignatures index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_AGES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Ages index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_COLUMNS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Columns index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_GPS_LOCATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating GPSLocations index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_REGIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Regions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_ROCK_TYPES_INDEX):
        logger_setup.get_logger().critical(f'Error creating RockTypes index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLE_AGE_INDEX):
        logger_setup.get_logger().critical(f'Error creating SampleAges index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLE_CONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating SampleContexts index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLEAGES_AGECONSTRAINTS_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating SampleAges_AgeConstraints index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLEAGES_AGEINTERPRETATIONS_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating SampleAges_AgeInterpretations index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLEAGES_REFERENCES_INDEX):
        logger_setup.get_logger().critical(f'Error creating SampleAges_References index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLING_METHODS_INDEX):
        logger_setup.get_logger().critical(f'Error creating SamplingMethods index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SETTINGS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Settings index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Units index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create sample item and analysis indexes
    if not query.exec(CREATE_SAMPLES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_ALIQUOTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Aliquots index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    if not query.exec(CREATE_ALIQUOTS_SAMPLES_COMPOSITE_INDEX):
        logger_setup.get_logger().critical(f'Error creating Aliquots index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SPOTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Spots index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    if not query.exec(CREATE_UPBANALYSES_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create many-to-many sample indexes
    if not query.exec(CREATE_SAMPLES_AGESIGNATURES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_AgeSignatures index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_REGIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_Regions index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_ROCKTYPES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_RockTypes index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_SAMPLEAGES_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_SampleAges index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_SAMPLECONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_SampleContext index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_SAMPLINGMETHODS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_SamplingMethods index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_SETTINGS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_Settings index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_UNITS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_Units index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create many-to-many aliquot tables
    if not query.exec(CREATE_ALIQUOTS_ALIQUOTCONTEXT_INDEX):
        logger_setup.get_logger().critical(f'Error creating Aliquots_AliquotContexts index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create many-to-many spot tables
    # if not query.exec(CREATE_SPOTS_SPOTCONTEXTS_INDEX):
    #     logger_setup.get_logger().critical(f'Error creating Spots_SpotsContexts index')
    #     logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
    #     logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
    #     loading_manager.close_loading_dialog('Loading', 'Indexing database...')
    #     return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create many-to-many analysis tables
    if not query.exec(CREATE_UPBANALYSES_REJECTIONREASONS_INDEX):
        logger_setup.get_logger().critical(
            f'Error creating UPbAnalyses_RejectionReasons index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_FILTER_GROUPS_INDEX):
        logger_setup.get_logger().critical(f'Error creating FilterGroups index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # Create foreign key indexes
    if not query.exec(CREATE_COLUMNS_GPSLOCATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Columns_GPSLocations index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SAMPLES_GPSLOCATIONS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Samples_GPSLocations index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_ALIQUOTS_SAMPLES_INDEX):
        if 'already exists' in query.lastError().text():
            logger_setup.get_logger().debug('Aliquots_Samples index already exists')
        else:
            logger_setup.get_logger().critical(f'Error creating Aliquots_Samples index')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            loading_manager.close_loading_dialog('Loading', 'Indexing database...')
            return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_SPOTS_ALIQUOTS_INDEX):
        if 'already exists' in query.lastError().text():
            logger_setup.get_logger().debug('Spots_Aliquots index already exists')
        else:
            logger_setup.get_logger().critical(f'Error creating Spots_Aliquots index')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            loading_manager.close_loading_dialog('Loading', 'Indexing database...')
            return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    if not query.exec(CREATE_SPOTS_ALIQUOTS_COMPOSITE_INDEX):
        logger_setup.get_logger().critical(f'Error creating Spots index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    if not query.exec(CREATE_SPOTS_GRAINS_INDEX):
        logger_setup.get_logger().critical(f'Error creating Spots index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # if not query.exec(CREATE_SPOTS_GRAINS_COMPOSITE_INDEX):
    #     logger_setup.get_logger().critical(f'Error creating Spots index')
    #     logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
    #     logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
    #     loading_manager.close_loading_dialog('Loading', 'Indexing database...')
    #     return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSES_SPOTS_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_Spots index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False

    # if not query.exec(CREATE_UPBANALYSES_SPOTS_COMPOSITE_INDEX):
    #     logger_setup.get_logger().critical(f'Error creating UPbAnalyses_Spots index')
    #     logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
    #     logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
    #     loading_manager.close_loading_dialog('Loading', 'Indexing database...')
    #     return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSES_REFERENCE_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_Spots index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSES_LABFACILITY_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_LabFacilities index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSES_INSTRUMENT_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalsyses_Instruments index')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False

    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')
    index_progress.setValue(index_count + 1)
    # Let the event loop process the dialog's updates
    QApplication.processEvents()
    # If the user clicked "Cancel", we can break out
    if index_progress.wasCanceled():
        return False


    if not query.exec(CREATE_UPBANALYSES_UPBANALYSISMETHODS_INDEX):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_UPbAnalysisMethodsindex')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        loading_manager.close_loading_dialog('Loading', 'Indexing database...')
        return False
    index_count += 1
    logger_setup.get_logger().info(f'Indexing progress: {index_count}/{total_indexes}')

    end_time = time.time()
    logger_setup.get_logger().info(f'Database indexes created in {end_time - start_time} seconds')
    loading_manager.close_loading_dialog('Loading', 'Indexing database...')
    return True


def drop_all_indexes(database=None) -> bool:
    """
        Connect to the database and execute the sql strings defined above to create the database tables.
        Only creates tables that do not already exist - does not overwrite existing tables.
        If the Ages table is empty, it will fill it from the Geologic timescale xml file.
        Populates the units, formats, and conversion tables.
        Uses the default database connection if no database is provided.
        :param database: QSqlDatabase instance to drop indexes in, if None uses the default connection
        :return: True on success, False on failure
        :rtype: bool
        """
    start_time = time.time()
    logger_setup.get_logger().info('Dropping all database indexes')
    if database is None:
        database = QtSql.QSqlDatabase.database()

    # Fetch all index names from sqlite_master
    select_indexes = "SELECT name FROM sqlite_master WHERE type='index'"
    try:
        conn = sqlite3.connect(database.databaseName())
        with conn:
            cursor = conn.cursor()
            cursor.execute(select_indexes)
            index_names = cursor.fetchall()
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical(f"Error resetting indexes")
        logger_setup.get_logger().debug(f'Error retrieving indexes: {e}')
        logger_setup.get_logger().debug(f'SQL query: {select_indexes}')
        return False

    # Drop each index
    for idx_name in index_names:
        if 'sqlite_autoindex' in idx_name[0]:
            continue
        drop_statement = f"DROP INDEX IF EXISTS {idx_name[0]}"

        try:
            conn = sqlite3.connect(database.databaseName())
            with conn:
                cursor = conn.cursor()
                cursor.execute(drop_statement)
            conn.commit()
            conn.close()
            logger_setup.get_logger().info(f'Dropped index {idx_name[0]}')
        except sqlite3.Error as e:
            logger_setup.get_logger().critical(f"Error resetting indexes")
            logger_setup.get_logger().debug(f'Error dropping index {idx_name[0]}: {e}')
            logger_setup.get_logger().debug(f'SQL query: {drop_statement}')
            return False
        # if not query.exec(drop_statement):
        #     logger_setup.get_logger().critical(f"Error dropping index '{idx_name}'")
        #     logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
        #     logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
        #     return False
        # else:
        #     logger_setup.get_logger().debug(f"Successfully dropped index '{idx_name}'")

    end_time = time.time()
    logger_setup.get_logger().info(f'Database indexes dropped in {end_time - start_time} seconds')
    return True
