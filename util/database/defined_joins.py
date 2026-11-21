# Join lines
# SampleAge-Age joins
sample_age_join = 'LEFT JOIN Ages ON SampleAges.OldestAgeID = Ages.AgeID OR SampleAges.YoungestAgeID = Ages.AgeID'
sample_age_left_joins = '''LEFT JOIN ErrorFormats AS DirectAgeErrorFormats ON SampleAges.DirectAgeErrorFormatID = DirectAgeErrorFormats.ErrorFormatID
                        LEFT JOIN AgeUnits AS SampleAgeUnits ON SampleAges.DirectAgeUnitID = SampleAgeUnits.AgeUnitID'''
sampleage_age_constraint_join = '''LEFT JOIN SampleAges_AgeConstraints ON SampleAges.SampleAgeID = SampleAges_AgeConstraints.SampleAgeID
                        LEFT JOIN AgeConstraints AS SampleAgeConstraints ON SampleAges_AgeConstraints.AgeConstraintID = SampleAgeConstraints.AgeConstraintID'''
sampleage_age_interpretation_join = '''LEFT JOIN SampleAges_AgeInterpretations ON SampleAges.SampleAgeID = SampleAges_AgeInterpretations.SampleAgeID
                        LEFT JOIN AgeInterpretations AS SampleAgeInterpretations ON SampleAges_AgeInterpretations.AgeInterpretationID = SampleAgeInterpretations.AgeInterpretationID'''
sampleage_age_reference_join = '''LEFT JOIN SampleAges_References ON SampleAges.SampleAgeID = SampleAges_References.SampleAgeID
                        LEFT JOIN "References" AS SampleAgeReferences ON SampleAges_References.ReferenceID = SampleAgeReferences.ReferenceID'''

# GPSLocation joins
gps_sample_join = '''LEFT JOIN GPSLocations AS SampleGPS ON Samples.SampleGPSLocationID = SampleGPS.GPSLocationID'''
gps_sample_left_joins = '''LEFT JOIN DirectionUnits AS SampleLatDirections ON SampleGPS.GPSLatDirectionID = SampleLatDirections.DirectionUnitID
                        LEFT JOIN DirectionUnits AS SampleLonDirections ON SampleGPS.GPSLonDirectionID = SampleLonDirections.DirectionUnitID
                        LEFT JOIN DistanceUnits AS SampleElevationUnits ON SampleGPS.GPSElevUnitID = SampleElevationUnits.DistanceUnitID
                        LEFT JOIN GPSFormats AS SampleGPSFormats ON SampleGPS.GPSFormatID = SampleGPSFormats.GPSFormatID'''
gps_column_join = '''LEFT JOIN GPSLocations AS ColumnGPS ON Columns.ColumnBaseGPSID = ColumnGPS.GPSLocationID'''
gps_column_left_joins = '''LEFT JOIN DirectionUnits AS ColumnLatDirections ON ColumnGPS.GPSLatDirectionID = ColumnLatDirections.DirectionUnitID
                        LEFT JOIN DirectionUnits AS ColumnLonDirections ON ColumnGPS.GPSLonDirectionID = ColumnLonDirections.DirectionUnitID
                        LEFT JOIN DistanceUnits AS ColumnElevationUnits ON ColumnGPS.GPSElevUnitID = ColumnElevationUnits.DistanceUnitID
                        LEFT JOIN GPSFormats AS ColumnGPSFormats ON ColumnGPS.GPSFormatID = ColumnGPSFormats.GPSFormatID'''

# ColumnJoins
column_units_join = 'LEFT JOIN DistanceUnits AS ColumnUnits ON Columns.ColumnTotalHeightDepthUnitID = ColumnUnits.DistanceUnitID'

# SampleJoins
age_signature_join = '''LEFT JOIN Samples_AgeSignatures ON Samples.SampleID = Samples_AgeSignatures.SampleID
                                    LEFT JOIN AgeSignatures ON Samples_AgeSignatures.AgeSignatureID = AgeSignatures.AgeSignatureID'''
column_join = 'LEFT JOIN Columns ON Samples.SampleColumnID = Columns.ColumnID'
column_unit_join = '''LEFT JOIN DistanceUnits AS ColumnHeightDepthUnits ON Samples.HeightDepthUnitID = ColumnHeightDepthUnits.DistanceUnitID'''
region_join = '''LEFT JOIN Samples_Regions ON Samples.SampleID = Samples_Regions.SampleID
                                LEFT JOIN Regions ON Samples_Regions.RegionID = Regions.RegionID'''
rock_type_join = '''LEFT JOIN Samples_RockTypes ON Samples.SampleID = Samples_RockTypes.SampleID
                                LEFT JOIN RockTypes ON Samples_RockTypes.RockTypeID = RockTypes.RockTypeID'''
sample_context_join = '''LEFT JOIN Samples_SampleContexts ON Samples.SampleID = Samples_SampleContexts.SampleID
                                LEFT JOIN SampleContexts ON Samples_SampleContexts.SampleContextID = SampleContexts.SampleContextID'''
sample_sampleage_join = '''LEFT JOIN Samples_SampleAges ON Samples.DefaultSampleAgeID = Samples_SampleAges.SampleAgeID
                                    LEFT JOIN SampleAges ON Samples_SampleAges.SampleAgeID = SampleAges.SampleAgeID'''
default_sample_age_join = '''LEFT JOIN SampleAges AS DefaultSampleAges ON Samples.DefaultSampleAgeID = DefaultSampleAges.SampleAgeID'''
sampling_method_join = '''LEFT JOIN Samples_SamplingMethods ON Samples.SampleID = Samples_SamplingMethods.SampleID
                                LEFT JOIN SamplingMethods ON Samples_SamplingMethods.SamplingMethodID = SamplingMethods.SamplingMethodID'''
setting_join = '''LEFT JOIN Samples_Settings ON Samples.SampleID = Samples_Settings.SampleID
                                LEFT JOIN Settings ON Samples_Settings.SettingID = Settings.SettingID'''
unit_join = '''LEFT JOIN Samples_Units ON Samples.SampleID = Samples_Units.SampleID
                                LEFT JOIN Units ON Samples_Units.UnitID = Units.UnitID'''
sample_aliquot_join = 'LEFT JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID'

# AliquotJoins
aliquot_sample_join = 'INNER JOIN Samples ON Aliquots.SampleID = Samples.SampleID'
aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts ON Aliquots.AliquotID = Aliquots_AliquotContexts.AliquotID
                                LEFT JOIN AliquotContexts ON Aliquots_AliquotContexts.AliquotContextID = AliquotContexts.AliquotContextID'''

# Aliquot-spot Join
aliquot_spot_join = 'INNER JOIN Spots ON Aliquots.AliquotID = Spots.AliquotID'

# GrainJoins
grain_context_join = '''LEFT JOIN Grains_GrainContexts ON Grains.GrainID = Grains_GrainContexts.GrainID
                                LEFT JOIN GrainContexts ON Grains_GrainContexts.GrainContextID = GrainContexts.GrainContextID'''
grain_composition_join = '''LEFT JOIN GrainCompositions ON Grains.GrainCompositionID = GrainCompositions.GrainCompositionID'''
grain_spot_join = 'LEFT JOIN Spots ON Grains.GrainID = Spots.GrainID'

# SpotJoins
spot_aliquot_join = 'INNER JOIN Aliquots ON Spots.AliquotID = Aliquots.AliquotID'
spot_composition_join = '''LEFT JOIN SpotCompositions ON Spots.SpotCompositionID = SpotCompositions.SpotCompositionID'''
spot_context_join = '''LEFT JOIN Spots_SpotContexts ON Spots.SpotID = Spots_SpotContexts.SpotID
                                LEFT JOIN SpotContexts ON Spots_SpotContexts.SpotContextID = SpotContexts.SpotContextID'''
spot_grain_join = 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID'
spot_upb_analysis_join = 'INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID'
spot_geochem_analysis_join = 'INNER JOIN GeoChemicalAnalyses ON Spots.SpotID = GeoChemicalAnalyses.SpotID'

# UPbJoins
upb_spot_join = 'INNER JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID'
upb_reference_join = 'LEFT JOIN "References" AS UPbReferences ON UPbAnalyses.ReferenceID = UPbReferences.ReferenceID'
upb_labs_join = 'LEFT JOIN LabFacilities AS UPbLabFacilities ON UPbAnalyses.LabFacilityID = UPbLabFacilities.LabFacilityID'
upb_instruments_join = 'LEFT JOIN Instruments AS UPbInstruments ON UPbAnalyses.InstrumentID = UPbInstruments.InstrumentID'
upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalyses.UPbAnalysisMethodID = UPbAnalysisMethods.UPbAnalysisMethodID'
upb_ratio_error_format_join = 'LEFT JOIN ErrorFormats AS UPbRatioErrorFormats ON UPbAnalyses.RatioErrorFormatID = UPbRatioErrorFormats.ErrorFormatID'
upb_age_error_format_join = 'LEFT JOIN ErrorFormats AS UPbAgeErrorFormats ON UPbAnalyses.AgeErrorFormatID = UPbAgeErrorFormats.ErrorFormatID'
upb_age_unit_join = 'LEFT JOIN AgeUnits AS UPbAgeUnits ON UPbAnalyses.AgeUnitID = UPbAgeUnits.AgeUnitID'
upb_age_interpretation_join = 'LEFT JOIN AgeInterpretations AS UPbAgeInterpretations ON UPbAnalyses.AgeInterpretationID = UPbAgeInterpretations.AgeInterpretationID'
upb_concordance_format_join = 'LEFT JOIN ConcordanceFormats AS UPbConcordanceFormats ON UPbAnalyses.ConcordanceFormatID = UPbConcordanceFormats.ConcordanceFormatID'
upb_spot_size_unit_join = 'LEFT JOIN DistanceUnits AS UPbSpotSizeUnits ON UPbAnalyses.SpotSizeUnitID = UPbSpotSizeUnits.DistanceUnitID'
upb_rejection_reason_join = '''LEFT JOIN UPbAnalyses_RejectionReasons ON UPbAnalyses.UPbAnalysisID = UPbAnalyses_RejectionReasons.UPbAnalysisID
                                    LEFT JOIN RejectionReasons AS UPbRejectionReasons ON UPbAnalyses_RejectionReasons.RejectionReasonID = UPbRejectionReasons.RejectionReasonID'''
upb_context_join = '''LEFT JOIN UPbAnalyses_UPbAnalysisContexts ON UPbAnalyses.UPbAnalysisID = UPbAnalyses_UPbAnalysisContexts.UPbAnalysisID
                                LEFT JOIN UPbAnalysisContexts ON UPbAnalyses_UPbAnalysisContexts.UPbAnalysisContextID = UPbAnalysisContexts.UPbAnalysisContextID'''
upb_distinct_join_sample = '''LEFT JOIN DistinctUPbAnalyses ON Samples.SampleID = DistinctUPbAnalyses.SampleID'''
upb_distinct_join_aliquot = '''LEFT JOIN DistinctUPbAnalyses ON Aliquots.AliquotID = DistinctUPbAnalyses.AliquotID'''
upb_distinct_join_grain = '''LEFT JOIN DistinctUPbAnalyses ON Grains.GrainID = DistinctUPbAnalyses.GrainID'''
upb_distinct_join_spot = '''LEFT JOIN DistinctUPbAnalyses ON Spots.SpotID = DistinctUPbAnalyses.SpotID'''


# GeoChemicalAnalyses joins
geochem_spot_join = 'INNER JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID'
geochem_reference_join = 'LEFT JOIN "References" AS GeoChemReferences ON GeoChemicalAnalyses.ReferenceID = GeoChemReferences.ReferenceID'
geochem_labs_join = 'LEFT JOIN LabFacilities AS GeoChemLabFacilities ON GeoChemicalAnalyses.LabFacilityID = GeoChemLabFacilities.LabFacilityID'
geochem_instruments_join = 'LEFT JOIN Instruments AS GeoChemInstruments ON GeoChemicalAnalyses.InstrumentID = GeoChemInstruments.InstrumentID'
geochem_method_join = 'LEFT JOIN GeoChemicalMethods ON GeoChemicalAnalyses.GeoChemicalMethodID = GeoChemicalMethods.GeoChemicalMethodID'
geochem_analyte_value_join = 'LEFT JOIN GeoChemicalAnalysisValues ON GeoChemicalAnalyses.GeoChemAnalysisID = GeoChemicalAnalysisValues.GeoChemAnalysisID'
geochem_analyte_join = 'LEFT JOIN GeoChemicalAnalytes ON GeoChemicalAnalysisValues.GeoChemAnalyteID = GeoChemicalAnalytes.GeoChemAnalyteID'
geochem_analyte_unit_join = 'LEFT JOIN AnalyticalUnits AS GeoChemAnalyteUnits ON GeoChemicalAnalysisValues.GeoChemAnalyteUnitID = GeoChemAnalyteUnits.AnalyticalUnitID'
geochem_analyte_error_format_join = 'LEFT JOIN ErrorFormats AS GeoChemAnalyteErrorFormats ON GeoChemicalAnalysisValues.GeoChemAnalyteErrorFormatID = GeoChemAnalyteErrorFormats.ErrorFormatID'
geochem_spot_size_unit_join = 'LEFT JOIN DistanceUnits AS GeoChemSpotSizeUnits ON GeoChemicalAnalyses.SpotSizeUnitID = GeoChemSpotSizeUnits.DistanceUnitID'
geochem_rejection_reasons_join = '''LEFT JOIN GeoChemicalAnalyses_RejectionReasons ON GeoChemicalAnalyses.GeoChemAnalysisID = GeoChemicalAnalyses_RejectionReasons.GeoChemAnalysisID
                            LEFT JOIN RejectionReasons AS GeoChemRejectionReasons ON GeoChemicalAnalyses_RejectionReasons.RejectionReasonID = GeoChemRejectionReasons.RejectionReasonID'''
geochem_contexts_join = '''LEFT JOIN GeoChemicalAnalyses_GeoChemicalAnalysisContexts ON GeoChemicalAnalyses.GeoChemAnalysisID = GeoChemicalAnalyses_GeoChemicalAnalysisContexts.GeoChemAnalysisID
                            LEFT JOIN GeoChemicalAnalysisContexts ON GeoChemicalAnalyses_GeoChemicalAnalysisContexts.GeoChemAnalysisContextID = GeoChemicalAnalysisContexts.GeoChemAnalysisContextID'''
geochem_distinct_join_sample = '''LEFT JOIN DistinctGeoChemicalAnalyses ON Samples.SampleID = DistinctGeoChemicalAnalyses.SampleID'''
geochem_distinct_join_aliquot = '''LEFT JOIN DistinctGeoChemicalAnalyses ON Aliquots.AliquotID = DistinctGeoChemicalAnalyses.AliquotID'''
geochem_distinct_join_grain = '''LEFT JOIN DistinctGeoChemicalAnalyses ON Grains.GrainID = DistinctGeoChemicalAnalyses.GrainID'''
geochem_distinct_join_spot = '''LEFT JOIN DistinctGeoChemicalAnalyses ON Spots.SpotID = DistinctGeoChemicalAnalyses.SpotID'''

# Limited hierarchy joins
limited_sample_aliquot_hierarchy_join = f'''
                        INNER JOIN LimitedSpotsAnalysesGrains lspag ON lsa.AliquotID = lspag.AliquotID
                        '''
limited_spot_analysis_grain_hierarchy_join = f'''
                        INNER JOIN LimitedSamplesAliquots lsa ON lspag.AliquotID = lsa.AliquotID
                        '''
# GeoChem-specific limited hierarchy: ties LimitedSpotsGeoChemAnalyses back to the LimitedSamplesAliquots tier
limited_spot_geochem_grain_hierarchy_join = f'''
                        INNER JOIN LimitedSamplesAliquots lsa ON lspgcg.AliquotID = lsa.AliquotID
                        '''
limited_sample_hierarchy_joins = [column_join, column_unit_join]
# Limited tags
# Limit the many-to-many relationships
upb_distinct_join_limited_sample = '''LEFT JOIN DistinctUPbAnalyses ON lsa.SampleID = DistinctUPbAnalyses.SampleID'''
upb_distinct_join_limited_aliquot = '''LEFT JOIN DistinctUPbAnalyses ON lsa.AliquotID = DistinctUPbAnalyses.AliquotID'''
upb_distinct_join_limited_grain = '''LEFT JOIN DistinctUPbAnalyses ON lspag.GrainID = DistinctUPbAnalyses.GrainID'''
upb_distinct_join_limited_spot = '''LEFT JOIN DistinctUPbAnalyses ON lspag.SpotID = DistinctUPbAnalyses.SpotID'''
gc_distinct_join_limited_sample = '''LEFT JOIN DistinctGeoChemicalAnalyses ON lsa.SampleID = DistinctGeoChemicalAnalyses.SampleID'''
gc_distinct_join_limited_aliquot = '''LEFT JOIN DistinctGeoChemicalAnalyses ON lsa.AliquotID = DistinctGeoChemicalAnalyses.AliquotID'''
gc_distinct_join_limited_grain = '''LEFT JOIN DistinctGeoChemicalAnalyses ON lspag.GrainID = DistinctGeoChemicalAnalyses.GrainID'''
gc_distinct_join_limited_spot = '''LEFT JOIN DistinctGeoChemicalAnalyses ON lspag.SpotID = DistinctGeoChemicalAnalyses.SpotID'''
limited_sample_tags = [
        f'''LimitedSamples_AgeSignatures AS (
            SELECT 
            s_ags.SampleID, 
            REPLACE(GROUP_CONCAT(DISTINCT ags.AgeSignatureName), ",", "; ") AS AgeSignatureName
            FROM AgeSignatures ags
            INNER JOIN Samples_AgeSignatures s_ags ON ags.AgeSignatureID = s_ags.AgeSignatureID
            INNER JOIN LimitedSamplesAliquots lsa ON s_ags.SampleID = lsa.SampleID
            GROUP BY s_ags.SampleID
        )''',
        f'''LimitedSamples_Regions AS (
            SELECT s_re.SampleID, 
            REPLACE(GROUP_CONCAT(DISTINCT re.RegionName), ",", "; ") AS RegionName
            FROM Regions re
            INNER JOIN Samples_Regions s_re ON re.RegionID = s_re.RegionID
            INNER JOIN LimitedSamplesAliquots lsa ON s_re.SampleID = lsa.SampleID
            GROUP BY s_re.SampleID
        )''',
        f'''LimitedSamples_RockTypes AS (
            SELECT 
            s_rt.SampleID, 
            REPLACE(GROUP_CONCAT(DISTINCT rt.RockTypeName), ",", "; ") AS RockTypeName
            FROM RockTypes rt
            INNER JOIN Samples_RockTypes s_rt ON rt.RockTypeID = s_rt.RockTypeID
            INNER JOIN LimitedSamplesAliquots lsa ON s_rt.SampleID = lsa.SampleID
            GROUP BY s_rt.SampleID
        )''',
        f'''LimitedSamples_SampleAges AS (
            SELECT 
            s_sa.SampleID, 
            s_sa.SampleAgeID, 
            sa.SampleAgeConverted, 
            sa.SampleAgeDisplay, 
            DirectAgeErrorFormats.ErrorFormatName, 
            SampleAgeUnits.AgeUnitName
            FROM SampleAges sa
            INNER JOIN Samples_SampleAges s_sa ON sa.SampleAgeID = s_sa.SampleAgeID
            INNER JOIN LimitedSamplesAliquots lsa ON s_sa.SampleID = lsa.SampleID
            {sample_age_left_joins.replace('SampleAges.', 'sa.')}
            GROUP BY s_sa.SampleID
        )''',
        f'''LimitedSampleAges_AgeConstraints AS (
            SELECT 
            lssa.SampleID,
            sa_ac.SampleAgeID, 
            REPLACE(GROUP_CONCAT(DISTINCT ac.AgeConstraintName), ",", "; ") AS AgeConstraintName
            FROM AgeConstraints ac
            INNER JOIN SampleAges_AgeConstraints sa_ac ON ac.AgeConstraintID = sa_ac.AgeConstraintID
            INNER JOIN LimitedSamples_SampleAges lssa ON sa_ac.SampleAgeID = lssa.SampleAgeID
            GROUP BY lssa.SampleID
        )''',
        f'''LimitedSampleAges_AgeInterpretations AS (
            SELECT  
            lssa.SampleID,
            sa_ai.SampleAgeID, 
            REPLACE(GROUP_CONCAT(DISTINCT ai.AgeInterpretationName), ",", "; ") AS AgeInterpretationName
            FROM AgeInterpretations ai
            INNER JOIN SampleAges_AgeInterpretations sa_ai ON ai.AgeInterpretationID = sa_ai.AgeInterpretationID
            INNER JOIN LimitedSamples_SampleAges lssa ON sa_ai.SampleAgeID = lssa.SampleAgeID
            GROUP BY lssa.SampleID
        )''',
        f'''LimitedSampleAges_References AS (
            SELECT  
            lssa.SampleID,
            sa_r.SampleAgeID, 
            REPLACE(GROUP_CONCAT(DISTINCT r.ReferenceDisplay), ",", "; ") AS ReferenceDisplay
            FROM "References" r
            INNER JOIN SampleAges_References sa_r ON r.ReferenceID = sa_r.ReferenceID
            INNER JOIN LimitedSamples_SampleAges lssa ON sa_r.SampleAgeID = lssa.SampleAgeID
            GROUP BY lssa.SampleID
        )''',
        f'''LimitedSamples_SampleContexts AS (
            SELECT 
            s_sc.SampleID, 
            REPLACE(GROUP_CONCAT(DISTINCT sc.SampleContextName), ",", "; ") AS SampleContextName
            FROM SampleContexts sc
            INNER JOIN Samples_SampleContexts s_sc ON sc.SampleContextID = s_sc.SampleContextID
            INNER JOIN LimitedSamplesAliquots lsa ON s_sc.SampleID = lsa.SampleID
            GROUP BY lsa.SampleID
        )''',
        f'''LimitedSamples_SamplingMethods AS (
            SELECT 
            s_sm.SampleID, 
            REPLACE(GROUP_CONCAT(DISTINCT sm.SamplingMethodName), ",", "; ") AS SamplingMethodName
            FROM SamplingMethods sm
            INNER JOIN Samples_SamplingMethods s_sm ON sm.SamplingMethodID = s_sm.SamplingMethodID
            INNER JOIN LimitedSamplesAliquots lsa ON s_sm.SampleID = lsa.SampleID
            GROUP BY lsa.SampleID
        )''',
        f'''LimitedSamples_Settings AS (
            SELECT 
            s_se.SampleID, 
            REPLACE(GROUP_CONCAT(DISTINCT se.SettingName), ",", "; ") AS SettingName
            FROM Settings se
            INNER JOIN Samples_Settings s_se ON se.SettingID = s_se.SettingID
            INNER JOIN LimitedSamplesAliquots lsa ON s_se.SampleID = lsa.SampleID
            GROUP BY lsa.SampleID
        )''',
        f'''LimitedSamples_Units AS (
            SELECT 
            s_u.SampleID, 
            REPLACE(GROUP_CONCAT(DISTINCT u.UnitName), ",", "; ") AS UnitName
            FROM Units u
            INNER JOIN Samples_Units s_u ON u.UnitID = s_u.UnitID
            INNER JOIN LimitedSamplesAliquots lsa ON s_u.SampleID = lsa.SampleID
            GROUP BY lsa.SampleID
        )'''
        ]
limited_aliquot_tags = [
        f'''LimitedAliquots_AliquotContexts AS (
            SELECT a_ac.AliquotID, ac.AliquotContextName
            FROM AliquotContexts ac
            INNER JOIN Aliquots_AliquotContexts a_ac ON ac.AliquotContextID = a_ac.AliquotContextID
            INNER JOIN LimitedSamplesAliquots lsa ON a_ac.AliquotID = lsa.AliquotID
        )''']
limited_spot_tags = [
        f'''LimitedSpots_SpotContexts AS (
            SELECT s_sc.SpotID, sc.SpotContextName
            FROM SpotContexts sc
            INNER JOIN Spots_SpotContexts s_sc ON sc.SpotContextID = s_sc.SpotContextID
            INNER JOIN LimitedSpotsAnalysesGrains lspag ON s_sc.SpotID = lspag.SpotID
        )''',
        f'''LimitedGrains_GrainContexts AS (
            SELECT g_gc.GrainID, gc.GrainContextName
            FROM GrainContexts gc
            INNER JOIN Grains_GrainContexts g_gc ON gc.GrainContextID = g_gc.GrainContextID
            INNER JOIN LimitedSpotsAnalysesGrains lspag ON g_gc.GrainID = lspag.GrainID
        )''']
limited_upb_tags = [
        f'''LimitedUPbAnalyses_UPbAnalysisContexts AS (
            SELECT ua_uac.UPbAnalysisID, ac.UPbAnalysisContextName
            FROM UPbAnalysisContexts ac
            INNER JOIN UPbAnalyses_UPbAnalysisContexts ua_uac ON ac.UPbAnalysisContextID = ua_uac.UPbAnalysisContextID
            INNER JOIN LimitedSpotsAnalysesGrains lspag ON ua_uac.UPbAnalysisID = lspag.UPbAnalysisID
        )''',
        f'''LimitedUPbAnalyses_RejectionReasons AS (
            SELECT ua_rr.UPbAnalysisID, rr.RejectionReasonName
            FROM RejectionReasons rr
            INNER JOIN UPbAnalyses_RejectionReasons ua_rr ON rr.RejectionReasonID = ua_rr.RejectionReasonID
            INNER JOIN LimitedSpotsAnalysesGrains lspag ON ua_rr.UPbAnalysisID = lspag.UPbAnalysisID
        )''']

limited_grain_tags = [
        f'''LimitedGrains_GrainContexts AS (
            SELECT g_gc.GrainID, gc.GrainContextName
            FROM GrainContexts gc
            INNER JOIN Grains_GrainContexts g_gc ON gc.GrainContextID = g_gc.GrainContextID
            INNER JOIN LimitedSpotsAnalysesGrains lspag ON g_gc.GrainID = lspag.GrainID
        )''']

limited_geochem_tags = [
        f'''LimitedGeoChemicalAnalyses_GeoChemicalAnalysisContexts AS (
            SELECT gca_gcac.GeoChemAnalysisID, gcac.GeoChemAnalysisContextName
            FROM GeoChemicalAnalysisContexts gcac
            INNER JOIN GeoChemicalAnalyses_GeoChemicalAnalysisContexts gca_gcac ON gcac.GeoChemAnalysisContextID = gca_gcac.GeoChemAnalysisContextID
            INNER JOIN LimitedSpotsAnalysesGrains lspag ON gca_gcac.GeoChemAnalysisID = lspag.GeoChemAnalysisID
        )''',
        f'''LimitedGeoChemicalAnalyses_RejectionReasons AS (
            SELECT gca_rr.GeoChemAnalysisID, rr.RejectionReasonName
            FROM RejectionReasons rr
            INNER JOIN GeoChemicalAnalyses_RejectionReasons gca_rr ON rr.RejectionReasonID = gca_rr.RejectionReasonID
            INNER JOIN LimitedSpotsAnalysesGrains lspag ON gca_rr.GeoChemAnalysisID = lspag.GeoChemAnalysisID
        )''']

# Limited tag joins
limited_sample_tags_join = [
    'LEFT JOIN LimitedSamples_AgeSignatures lsas ON lsa.SampleID = lsas.SampleID',
    'LEFT JOIN LimitedSamples_Regions lsre ON lsa.SampleID = lsre.SampleID',
    'LEFT JOIN LimitedSamples_RockTypes lsrt ON lsa.SampleID = lsrt.SampleID',
    'LEFT JOIN LimitedSamples_SampleAges lssa ON lsa.DefaultSampleAgeID = lssa.SampleAgeID',
    'LEFT JOIN LimitedSampleAges_AgeConstraints lsaac ON lsa.DefaultSampleAgeID = lsaac.SampleAgeID',
    'LEFT JOIN LimitedSampleAges_AgeInterpretations lsaai ON lsa.DefaultSampleAgeID = lsaai.SampleAgeID',
    'LEFT JOIN LimitedSampleAges_References lsar ON lsa.DefaultSampleAgeID = lsar.SampleAgeID',
    'LEFT JOIN LimitedSamples_SampleContexts lssc ON lsa.SampleID = lssc.SampleID',
    'LEFT JOIN LimitedSamples_SamplingMethods lssm ON lsa.SampleID = lssm.SampleID',
    'LEFT JOIN LimitedSamples_Settings lss ON lsa.SampleID = lss.SampleID',
    'LEFT JOIN LimitedSamples_Units lsu ON lsa.SampleID = lsu.SampleID',
    ]

limited_aliquot_tags_join = [f'LEFT JOIN LimitedAliquots_AliquotContexts laac ON lsa.AliquotID = laac.AliquotID']

limited_spot_tags_join = [
    'LEFT JOIN LimitedSpots_SpotContexts lspsc ON lspag.SpotID = lspsc.SpotID',
    'LEFT JOIN LimitedGrains_GrainContexts lggc ON lspag.GrainID = lggc.GrainID'
    ]

limited_upb_tags_join = [
    'LEFT JOIN LimitedUPbAnalyses_UPbAnalysisContexts luac ON lspag.UPbAnalysisID = luac.UPbAnalysisID',
    'LEFT JOIN LimitedUPbAnalyses_RejectionReasons lurr ON lspag.UPbAnalysisID = lurr.UPbAnalysisID'
    ]

limited_grain_tags_join = [
    'LEFT JOIN LimitedGrains_GrainContexts lggc ON lspag.GrainID = lggc.GrainID'
]

limited_geochem_tags_join = [
    'LEFT JOIN LimitedGeoChemicalAnalyses_GeoChemicalAnalysisContexts lgcac ON lspag.GeoChemAnalysisID = lgcac.GeoChemAnalysisID',
    'LEFT JOIN LimitedGeoChemicalAnalyses_RejectionReasons lgcrr ON lspag.GeoChemAnalysisID = lgcrr.GeoChemAnalysisID'
    ]

limited_lsa_lspag_joins = {
    'LimitedSamplesAliquots': [column_join,
                    column_unit_join,
                    gps_sample_join,
                    gps_sample_left_joins,
                    gps_column_join,
                    gps_column_left_joins
                ],
    'LimitedSpotsAnalysesGrains': [grain_composition_join,
                    spot_composition_join,
                    upb_reference_join,
                    upb_labs_join,
                    upb_instruments_join,
                    upb_method_join,
                    upb_ratio_error_format_join,
                    upb_age_error_format_join,
                    upb_age_unit_join,
                    upb_concordance_format_join,
                    upb_age_interpretation_join,
                    upb_spot_size_unit_join,
                    geochem_reference_join,
                    geochem_labs_join,
                    geochem_instruments_join,
                    geochem_method_join,
                    geochem_analyte_value_join,
                    geochem_analyte_join,
                    geochem_analyte_unit_join,
                    geochem_analyte_error_format_join,
                    geochem_rejection_reasons_join,
                    geochem_contexts_join],
    'LimitedSpotsUPbAnalysesGrains': [grain_composition_join,
                    spot_composition_join,
                    upb_reference_join,
                    upb_labs_join,
                    upb_instruments_join,
                    upb_method_join,
                    upb_ratio_error_format_join,
                    upb_age_error_format_join,
                    upb_age_unit_join,
                    upb_concordance_format_join,
                    upb_age_interpretation_join,
                    upb_spot_size_unit_join],
    'LimitedSpotsGeoChemicalAnalysesGrains': [grain_composition_join,
                    spot_composition_join,
                    geochem_reference_join,
                    geochem_labs_join,
                    geochem_instruments_join,
                    geochem_method_join,
                    geochem_analyte_value_join,
                    geochem_analyte_join,
                    geochem_analyte_unit_join,
                    geochem_analyte_error_format_join,
                    geochem_rejection_reasons_join,
                    geochem_contexts_join]
}