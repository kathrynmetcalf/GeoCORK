from util.database.defined_joins import *

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

# Dictionary for limited table abbreviations
limited_table_abbreviations = {
    'Samples': 'lsa',
    'Aliquots': 'lsa',
    'Spots': 'lspag',
    'UPbAnalyses': 'lspag',
    'Grains': 'lspag',
    'Columns': 'lsa',
    'ColumnHeightDepthUnits': 'lsa',
    'SampleLatDirections': 'lsa',
    'SampleLonDirections': 'lsa',
    'SampleElevationUnits': 'lsa',
    'SampleGPSFormats': 'lsa',
    'AgeSignatures': 'lsas',
    'Regions': 'lsre',
    'RockTypes': 'lsrt',
    'SampleAges': 'lssa',
    'DirectAgeErrorFormats': 'lssa',
    'SampleAgeUnits': 'lssa',
    'OldAge': 'lssa',
    'YoungAge': 'lssa',
    'SampleAgeConstraints': 'lsaac',
    'SampleAgeInterpretations': 'lsaai',
    'SampleAgeReferences': 'lsar',
    'SampleContexts': 'lssc',
    'SampleGPS': 'lsa',
    'SamplingMethods': 'lssm',
    'Settings': 'lss',
    'Units': 'lsu',
    'LimitedSamplesGPsInfo': 'lsgps',
    'AliquotContexts': 'laac',
    'GrainContexts': 'lggc',
    'SpotContexts': 'lspsc',
    'UPbAnalysisContexts': 'luac',
    'UPbRejectionReasons': 'lurr',
    'SpotCompositions': 'lspag',
    'GrainCompositions': 'lspag',
    'UPbLabFacilities': 'lspag',
    'UPbInstruments': 'lspag',
    'UPbAnalysisMethods': 'lspag',
    'UPbRatioErrorFormats': 'lspag',
    'UPbAgeErrorFormats': 'lspag',
    'UPbConcordanceFormats': 'lspag',
    'UPbAgeUnits': 'lspag',
    'UPbAgeInterpretations': 'lspag',
    'UPbReferences': 'lspag',
    'UPbSpotSizeUnits': 'lspag',
    'GeoChemicalAnalyses': 'lspag',
    'GeoChemicalAnalysisValues': 'lspag',
    'GeoChemicalAnalytes': 'lspag',
    'GeoChemicalMethods': 'lspag',
    'GeoChemAnalyteUnits': 'lspag',
    'GeoChemAnalyteErrorFormats': 'lspag',
    'GeoChemLabFacilities': 'lspag',
    'GeoChemInstruments': 'lspag',
    'GeoChemReferences': 'lspag',
    'GeoChemSpotSizeUnits': 'lspag',
    'GeoChemicalAnalysisContexts': 'lgcac',
    'GeoChemRejectionReasons': 'lgcrr'
}



# Dictionary of column leaders that could be included in select statements for LimitedSamplesAliquots and LimitedSpotsAnalysesGrains
limited_column_leaders = {
    'LimitedSamplesAliquots': [],
    'LimitedSpotsAnalysesGrains': []
}
for table, abbreviation in limited_table_abbreviations.items():
    limited_column_leaders['LimitedSamplesAliquots'].append(f'{table}.') if abbreviation == 'lsa' else None
    limited_column_leaders['LimitedSpotsAnalysesGrains'].append(f'{table}.') if abbreviation == 'lspag' else None

# Many-to-many columns for each table key, key-value pairs for column in the view and table to edit that information, populate multiple selection dropdowns
many_editable = {
    'Samples': {'SampleAgeSignatureName': 'AgeSignatures', 'SampleAgeSignatureDescription': 'AgeSignatures',
                'RegionName': 'Regions', 'RegionDescription': 'Regions',
                'RockTypeName': 'RockTypes', 'RockTypeDescription': 'RockTypes',
                'SampleContextName': 'SampleContexts', 'SampleContextDescription': 'SampleContexts',
                'SamplingMethodName': 'SamplingMethods', 'SamplingMethodDescription': 'SamplingMethods',
                'SettingName': 'Settings', 'SettingDescription': 'Settings',
                'UnitName': 'Units', 'UnitDescription': 'Units'},
    'Aliquots': {'AliquotContextName': 'AliquotContexts', 'AliquotContextDescription': 'AliquotContexts'},
    'Grains': {'GrainContextName': 'GrainContexts', 'GrainContextDescription': 'GrainContexts'},
    'Spots': {'SpotContextName': 'SpotContexts', 'SpotContextDescription': 'SpotContexts'},
    'UPbAnalyses': {'RejectionReasonName': 'RejectionReasons', 'RejectionReasonDescription': 'RejectionReasons',
                    'UPbAnalysisContextName': 'UPbAnalysisContexts', 'UPbAnalysisContextDescription': 'UPbAnalysisContexts'},
    'GeoChemicalAnalyses': {'RejectionReasonName': 'RejectionReasons', 'RejectionReasonDescription': 'RejectionReasons',
                    'GeoChemAnalysisContextName': 'GeoChemicalAnalysisContexts',
                            'GeoChemAnalysisContextDescription': 'GeoChemicalAnalysisContexts'},
    'References': {'ReferenceDisplay': 'ReferenceDisplay'}
}
# One-to-many columns for each table key, key-value pairs for column in the view and table to edit that information, populate single selection dropdowns
one_editable = {
    'Samples': {'SampleGPSLocationDisplay': 'GPSLocations', 'SampleAgeCalculated': 'SampleAges',
                'ColumnName': 'Columns',
                'ColumnHeightDepthUnitAbbreviation': 'DistanceUnits', 'AliquotName': 'Aliquots'},
    'Columns': {'ColumnTotalHeightDepthUnitAbbreviation': 'DistanceUnits', 'ColumnBaseGPSDisplay': 'GPSLocations'},
    'Aliquots': {'SampleName': 'Samples', 'SpotName': 'Spots'},
    'Grains': {'SpotName': 'Spots', 'GrainCompositionName': 'GrainCompositions'},
    'Spots': {'GrainName': 'Grains', 'AliquotName': 'Aliquots', 'SpotCompositionName': 'SpotCompositions'},
    'UPbAnalyses': {'SpotName': 'Spots', 'GrainName': 'Grains', 'AliquotName': 'Aliquots', 'SampleName': 'Samples',
                    'UPbReference': 'References',
                    'UPbLabFacilityName': 'LabFacilities', 'UPbInstrumentName': 'Instruments',
                    'UPbAnalysisMethodName': 'UPbAnalysisMethods',
                    'UPbRatioErrorFormatAbbreviation': 'ErrorFormats', 'UPbAgeUnitAbbreviation': 'AgeUnits',
                    'UPbAgeErrorFormatAbbreviation': 'ErrorFormats', 'UPbConcordanceFormatAbbreviation': 'ConcordanceFormats',
                    'UPbSpotSizeUnitAbbreviation': 'DistanceUnits'},
    'GeoChemicalAnalyses': {'SpotName': 'Spots', 'GrainName': 'Grains', 'AliquotName': 'Aliquots', 'SampleName': 'Samples',
                    'GeoChemReference': 'References', 'UPbLabFacilityName': 'LabFacilities', 'UPbInstrumentName': 'Instruments',
                    'GeoChemicalMethodName': 'GeoChemicalMethods', 'GeoChemAnalyteUnitAbbreviation': 'AnalyticalUnits',
                    'GeoChemAnalyteErrorFormatAbbreviation': 'ErrorFormats'},
    'References': {}
}

non_editable = {
    'Samples': ['SpotCount', 'Accepted/TotalUPbAnalyses', 'Accepted/TotalGeoChemicalAnalyses', 'RejectionReasonName',
                'SampleCreated', 'SampleModified'],
    'Columns': ['ColumnCreated', 'ColumnModified'],
    'Aliquots': ['Accepted/TotalUPbAnalyses', 'Accepted/TotalGeoChemicalAnalyses', 'AliquotCreated', 'AliquotModified'],
    'Grains': ['Accepted/TotalUPbAnalyses', 'Accepted/TotalGeoChemicalAnalyses', 'GrainCreated', 'GrainModified'],
    'Spots': ['Accepted/TotalUPbAnalyses', 'Accepted/TotalGeoChemicalAnalyses', 'SpotCreated', 'SpotModified'],
    'UPbAnalyses': ['UPbAnalysisCreated', 'UPbAnalysisModified'],
    'GeoChemicalAnalyses': ['GeoChemAnalysisCreated', 'GeoChemAnalysisModified'],
    'References': ['ReferenceDisplay', 'ReferenceCreated', 'ReferenceModified']
}
"""Non-editable columns for each table key, key-value pairs for column in the view and table the to edit that 
information, populate single selection dropdowns"""

not_null = {
    'Samples': ['SampleName'],
    'Columns': ['ColumnName'],
    'Aliquots': ['AliquotName', 'SampleName'],
    'Spots': ['SpotName', 'AliquotName', 'SampleName'],
    'Grains':['GrainName'],
    'UPbAnalyses': ['UPbAnalysisName', 'SpotName', 'AliquotName', 'SampleName']
}
"Tables that are the basis for view and their columns that cannot be null"

user_viewable_tables = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'AliquotContexts', 'Analytes',
                        'Columns', 'GrainContexts', 'GrainCompositions', 'GeoChemicalAnalysisContexts',
                        'GeoChemicalMethods', 'Instruments', 'LabFacilities', 'References', 'Regions', 'RejectionReasons',
                        'RockTypes', 'SampleContexts', 'Samples', 'SamplingMethods', 'Settings', 'SpotCompositions',
                        'SpotContexts', 'UPbAnalysisMethods', 'UPbAnalysisContexts', 'Units']
"""List of all user-viewable tables and trees used throughout GeoCORK."""

user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'AliquotContexts', 'Aliquots',
                       'GeoChemicalAnalysisContexts', 'GeoChemicalAnalyteClasses', 'GeoChemicalMethods', 'GrainContexts',
                       'Regions', 'RockTypes', 'SampleContexts', 'SamplingMethods', 'Settings', 'SpotCompositions',
                       'SpotContexts', 'UPbAnalysisMethods', 'UPbAnalysisContexts', 'Units']
"""List of all user-viewable trees used throughout GeoCORK. If a table is included in this list it is assumed to be in the correct format"""

export_database_tables_viewable = sorted(user_viewable_tables + ['UPbAnalyses', 'Aliquots', 'Spots'])
"""List of all tables to be viewed in the ExporterWidget for exporting a database. Extra tables are included for sanity checking."""

conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Grains', 'Spots', 'UPbAnalyses', 'GeoChemicalAnalyses']
conditionally_editable_trees = ['Aliquots']

trigger_tables = ['Columns', 'ColumnEditView', 'GPSLocations', 'SampleAges', 'Samples', 'SampleEditView', 'Spots',
                  'SpotEditView', 'UPbAnalyses', 'UPbView', 'UPbEditView', 'Grains', 'GrainEditView',
                  'GeoChemicalAnalyses', 'GeoChemEditView', 'GeoChemValueEditView']

tree_tables_schema = {
    'AgeConstraints.[AgeConstraintName]': {
        'id_column': 'AgeConstraintID',
        'name_column': 'AgeConstraintName',
        'parent_column': 'ParentAgeConstraintID',
        'cte_name': 'RecursiveAgeConstraints',
        'bridge_table': 'SampleAges_AgeConstraints',
        'bridge_from_column': 'SampleAgeID',
        'bridge_to_column': 'AgeConstraintID',
    },
    'AgeInterpretations.[AgeInterpretationName]': {
        'id_column': 'AgeInterpretationID',
        'name_column': 'AgeInterpretationName',
        'parent_column': 'ParentAgeInterpretationID',
        'cte_name': 'RecursiveAgeInterpretations',
        'bridge_table': 'SampleAges_AgeInterpretations',
        'bridge_from_column': 'SampleAgeID',
        'bridge_to_column': 'AgeInterpretationID',
    },
    'AgeSignatures.[AgeSignatureName]': {
        'id_column': 'AgeSignatureID',
        'name_column': 'AgeSignatureName',
        'parent_column': 'ParentAgeSignatureID',
        'cte_name': 'RecursiveAgeSignatures',
        'bridge_table': 'Samples_AgeSignatures',
        'bridge_from_column': 'SampleID',
        'bridge_to_column': 'AgeSignatureID',
    },
    'Ages.[AgeName]': {
        'id_column': 'AgeID',
        'name_column': 'AgeName',
        'parent_column': 'ParentAgeID',
        'cte_name': 'RecursiveAges',
        'bridge_table': 'SampleAges',
        'bridge_from_column': ['OldestAgeID', 'YoungestAgeID'],
        'bridge_to_column': 'AgeID',
    },
    'AliquotContexts.[AliquotContextName]': {
        'id_column': 'AliquotContextID',
        'name_column': 'AliquotContextName',
        'parent_column': 'ParentAliquotContextID',
        'cte_name': 'RecursiveAliquotContexts',
        'bridge_table': 'Aliquots_AliquotContexts',
        'bridge_from_column': 'AliquotID',
        'bridge_to_column': 'AliquotContextID',
    },
    'GrainContexts.[GrainContextName]': {
        'id_column': 'GrainContextID',
        'name_column': 'GrainContextName',
        'parent_column': 'ParentGrainContextID',
        'cte_name': 'RecursiveGrainContexts',
        'bridge_table': 'Grains_GrainContexts',
        'bridge_from_column': 'GrainID',
        'bridge_to_column': 'GrainContextID',
    },
    'Regions.[RegionName]': {
        'id_column': 'RegionID',
        'name_column': 'RegionName',
        'parent_column': 'ParentRegionID',
        'cte_name': 'RecursiveRegions',
        'bridge_table': 'Samples_Regions',
        'bridge_from_column': 'SampleID',
        'bridge_to_column': 'RegionID',
    },
    'RockTypes.[RockTypeName]': {
        'id_column': 'RockTypeID',
        'name_column': 'RockTypeName',
        'parent_column': 'ParentRockTypeID',
        'cte_name': 'RecursiveRockTypes',
        'bridge_table': 'Samples_RockTypes',
        'bridge_from_column': 'SampleID',
        'bridge_to_column': 'RockTypeID',
    },
    'SampleContexts.[SampleContextName]': {
        'id_column': 'SampleContextID',
        'name_column': 'SampleContextName',
        'parent_column': 'ParentSampleContextID',
        'cte_name': 'RecursiveSampleContexts',
        'bridge_table': 'Samples_SampleContexts',
        'bridge_from_column': 'SampleID',
        'bridge_to_column': 'SampleContextID',
    },
    'SamplingMethods.[SamplingMethodName]': {
        'id_column': 'SamplingMethodID',
        'name_column': 'SamplingMethodName',
        'parent_column': 'ParentSamplingMethodID',
        'cte_name': 'RecursiveSamplingMethods',
        'bridge_table': 'Samples_SamplingMethods',
        'bridge_from_column': 'SampleID',
        'bridge_to_column': 'SamplingMethodID',
    },
    'Settings.[SettingName]': {
        'id_column': 'SettingID',
        'name_column': 'SettingName',
        'parent_column': 'ParentSettingID',
        'cte_name': 'RecursiveSettings',
        'bridge_table': 'Samples_Settings',
        'bridge_from_column': 'SampleID',
        'bridge_to_column': 'SettingID',
    },
    'SpotContexts.[SpotContextName]': {
        'id_column': 'SpotContextID',
        'name_column': 'SpotContextName',
        'parent_column': 'ParentSpotContextID',
        'cte_name': 'RecursiveSpotContexts',
        'bridge_table': 'Spots_SpotContexts',
        'bridge_from_column': 'SpotID',
        'bridge_to_column': 'SpotContextID',
    },
    'UPbAnalysisMethods.[UPbAnalysisMethodName]': {
        'id_column': 'UPbAnalysisMethodID',
        'name_column': 'UPbAnalysisMethodName',
        'parent_column': 'ParentUPbAnalysisMethodID',
        'cte_name': 'RecursiveUPbAnalysisMethods',
        'bridge_table': 'UPbAnalyses',
        'bridge_from_column': 'UPbAnalysisID',
        'bridge_to_column': 'UPbAnalysisMethodID',
    },
    'UPbAnalysisContexts.[UPbAnalysisContextName]': {
        'id_column': 'UPbAnalysisContextID',
        'name_column': 'UPbAnalysisContextName',
        'parent_column': 'ParentUPbAnalysisContextID',
        'cte_name': 'RecursiveUPbAnalysisContexts',
        'bridge_table': 'UPbAnalyses_UPbAnalysisContexts',
        'bridge_from_column': 'UPbAnalysisID',
        'bridge_to_column': 'UPbAnalysisContextID',
    },
    'Units.[UnitName]': {
        'id_column': 'UnitID',
        'name_column': 'UnitName',
        'parent_column': 'ParentUnitID',
        'cte_name': 'RecursiveUnits',
        'bridge_table': 'Samples_Units',
        'bridge_from_column': 'SampleID',
        'bridge_to_column': 'UnitID',
    }
}

static_foreign_key_tables = [
    'AgeUnitConversions',
    'AgeUnits',
    'Ages',
    'ConcordanceFormatConversions',
    'ConcordanceFormats',
    'DirectionUnits',
    'DistanceUnits',
    'DistanceUnitConversions',
    'ErrorFormatConversions',
    'ErrorFormats',
    'GPSFormatConversions',
    'GPSFormats',
    'AnalyticalUnits',
    'AnalyticalUnitConversions',
    'GeoChemicalAnalytes'
]
"""Used in MergeDatabase.py as tables to skip if found for foreign key references.
Since these tables should be static across any database and is modified/created exclusively by code"""

static_tables = ['About',
                 'Ages',
                 'AgeUnitConversions',
                 'AgeUnits',
                 'ConcordanceFormatConversions',
                 'ConcordanceFormats',
                 'DirectionUnits',
                 'DistanceUnitConversions',
                 'DistanceUnits',
                 'ErrorFormatConversions',
                 'ErrorFormats',
                 'GPSFormatConversions',
                 'GPSFormats',
                 'AnalyticalUnits',
                 'AnalyticalUnitConversions',
                 'GeoChemicalAnalytes']
"""Used in export_helper.py as tables to skip if found exporting.
Since these tables should be static across any database and is modified/created exclusively by code"""

foreign_key_tables = [
    'SampleAges_AgeConstraints',
    'SampleAges_AgeInterpretations',
    'SampleAges_References',
    'Aliquots',
    'Grains_GrainContexts',
    'Grains',
    'Spots',
    'Samples_AgeSignatures',
    'Samples_Regions',
    'Samples_RockTypes',
    'Samples_SampleAges',
    'Samples_SampleContexts',
    'Samples_SamplingMethods',
    'Samples_Settings',
    'Samples_Units',
    'Aliquots_AliquotContexts',
    'Spots_SpotContexts',
    'UPbAnalyses_RejectionReasons',
    'UPbAnalyses_UPbAnalysisContexts',
    'SampleAges',
    'UPbAnalyses',
    'Samples',
    'Columns',
    'GeoChemicalAnalyses'
]
"""List of all tables that have foreign key references to other tables in the database."""

database_ordered_tables = ['AgeUnits',
                           'AnalyticalUnits',
                           'ConcordanceFormats',
                           'DirectionUnits',
                           'DistanceUnits',
                           'ErrorFormats',
                           'GPSFormats',
                           'AgeUnitConversions',
                           'AnalyticalUnitConversions',
                           'ConcordanceFormatConversions',
                           'DistanceUnitConversions',
                           'ErrorFormatConversions',
                           'GPSFormatConversions',
                           'Ages',
                           'Instruments',
                           'LabFacilities',
                           'RejectionReasons',
                           'References',
                           'UPbAnalysisContexts',
                           'UPbAnalysisMethods',
                           'GeoChemicalMethods',
                           'SpotCompositions',
                           'SpotContexts',
                           'GrainCompositions',
                           'GrainContexts',
                           'AliquotContexts',
                           'AgeConstraints',
                           'AgeInterpretations',
                           'AgeSignatures',
                           'Regions',
                           'RockTypes',
                           'SampleContexts',
                           'SamplingMethods',
                           'Settings',
                           'Units',
                           'GPSLocations',
                           'Columns',
                           'SampleAges',
                           'Samples',
                           'Aliquots',
                           'Grains',
                           'Spots',
                           'UPbAnalyses',
                           'GeoChemicalAnalyses',
                           'SampleAges_References',
                           'SampleAges_AgeConstraints',
                           'SampleAges_AgeInterpretations',
                           'Samples_AgeSignatures',
                           'Samples_Regions',
                           'Samples_RockTypes',
                           'Samples_SampleAges',
                           'Samples_SampleContexts',
                           'Samples_SamplingMethods',
                           'Samples_Settings',
                           'Samples_Units',
                           'Aliquots_AliquotContexts',
                           'Grains_GrainContexts',
                           'Spots_SpotContexts',
                           'UPbAnalyses_RejectionReasons',
                           'UPbAnalyses_UPbAnalysisContexts',
                           'FilterGroups'
                           ]
"""Used in MergeDatabase.py as the order of tables to merge first to last. Since the database is relational it must 
be merged so the related data is merged last so updated primary keys can be properly generated"""




# todo: make element ratios (not isotopic ratios) calculated columns rather than user-fillable
geochemical_analyte_classes = [
    ('element', 'element analyte'),
    ('REE', 'Rare earth element'), # parent is element
    ('compound', 'compound of multiple elements'),
    ('oxide', 'oxide analyte'), # parent is compound
    ('isotope', 'element with specific combined number of protons and neutrons'),
    ('isotopic ratio', 'ratio of elements with specific combined numbers of protons and neutrons'),
    ('activity', 'analyte reported as activity'),
    ('delta value', 'analyte reported as delta value'),
    ('epsilon value', 'analyte reported as epsilon value'),
    ('other', 'other analyte')
]
'''Classes of analytes use in the dictionary below. Used to group analytes.'''

geochemical_analytes = [
    # Elements
    ('Silver', 'Ag', 'silver', 'element'),
    ('Aluminum', 'Al', 'aluminum', 'element'),
    ('Argon', 'Ar', 'argon', 'element'),
    ('Arsenic', 'As', 'arsenic', 'element'),
    ('Gold', 'Au', 'gold', 'element'),
    ('Boron', 'B', 'boron', 'element'),
    ('Barium', 'Ba', 'barium', 'element'),
    ('Beryllium', 'Be', 'beryllium', 'element'),
    ('Bismuth', 'Bi', 'bismuth', 'element'),
    ('Bromium', 'Br', 'bromium', 'element'),
    ('Carbon', 'C', 'carbon', 'element'),
    ('Inorganic carbon', 'C(inorg)', 'inorganic carbon', 'element'),
    ('Non-carbonate carbon', 'C(non-carb)', 'non-carbonate carbon', 'element'),
    ('Organic carbon', 'C(org)', 'organic carbon', 'element'),
    ('Total carbon', 'C(tot)', 'total carbon', 'element'),
    ('Calcium', 'Ca', 'calcium', 'element'),
    ('Cadmium', 'Cd', 'cadmium', 'element'),
    ('Cerium', 'Ce', 'cerium', 'REE'),
    ('Chlorine', 'Cl', 'chlorine', 'element'),
    ('Cobalt', 'Co', 'cobalt', 'element'),
    ('Chromium', 'Cr', 'chromium', 'element'),
    ('Cesium', 'Cs', 'cesium', 'element'),
    ('Copper', 'Cu', 'copper', 'element'),
    ('Dissolved inorganic carbon', 'DIC', 'dissolved inorganic carbon', 'element'),
    ('Dysprosium', 'Dy', 'dysprosium', 'REE'),
    ('Erbium', 'Er', 'erbium', 'REE'),
    ('Europium', 'Eu', 'europium', 'REE'),
    ('Fluorine', 'F', 'fluorine', 'element'),
    ('Iron', 'Fe', 'iron', 'element'),
    ('Francium', 'Fr', 'francium', 'element'),
    ('Gallium', 'Ga', 'gallium', 'element'),
    ('Gadolinium', 'Gd', 'gadolinium', 'REE'),
    ('Germanium', 'Ge', 'germanium', 'element'),
    ('Hydrogen', 'H', 'hydrogen', 'element'),
    ('Total hydrogen', 'H(TOT)', 'total hydrogen', 'element'),
    ('Helium', 'He', 'helium', 'element'),
    ('Hafnium', 'Hf', 'hafnium', 'element'),
    ('Mercury', 'Hg', 'mercury', 'element'),
    ('Holmium', 'Ho', 'holmium', 'REE'),
    ('Iodine', 'I', 'iodine', 'element'),
    ('Indium', 'In', 'indium', 'element'),
    ('Iridium', 'Ir', 'iridium', 'element'),
    ('Potassium', 'K', 'potassium', 'element'),
    ('Krypton', 'Kr', 'krypton', 'element'),
    ('Lanthanum', 'La', 'lanthanum', 'REE'),
    ('Lithium', 'Li', 'lithium', 'element'),
    ('Lutetium', 'Lu', 'lutetium', 'REE'),
    ('Magnesium', 'Mg', 'magnesium', 'element'),
    ('Manganese', 'Mn', 'manganese', 'element'),
    ('Molybdenum', 'Mo', 'molybdenum', 'element'),
    ('Nitrogen', 'N', 'nitrogen', 'element'),
    ('Organic nitrogen', 'N(ORG)', 'organic nitrogen', 'element'),
    ('Total nitrogen', 'N(TOT)', 'total nitrogen', 'element'),
    ('Native copper', 'NCU', 'native copper', 'element'),
    ('Sodium', 'Na', 'sodium', 'element'),
    ('Niobium', 'Nb', 'niobium', 'element'),
    ('Neodymium', 'Nd', 'neodymium', 'REE'),
    ('Neon', 'Ne', 'neon', 'element'),
    ('Nickel', 'Ni', 'nickel', 'element'),
    ('Oxygen', 'O', 'oxygen', 'element'),
    ('Osmium', 'Os', 'osmium', 'element'),
    ('Common osmium at initial age', 'Os(I)', 'common osmium at initial age', 'element'),
    ('Phosphorus', 'P', 'phosphorus', 'element'),
    ('Phosphorous, organic', 'P(ORG)', 'phosphorous, organic', 'element'),
    ('Protactinium', 'Pa', 'protactinium', 'element'),
    ('Lead', 'Pb', 'lead', 'element'),
    ('Palladium', 'Pd', 'palladium', 'element'),
    ('Praseodymium', 'Pr', 'praseodymium', 'REE'),
    ('Platinum', 'Pt', 'platinum', 'element'),
    ('Radium', 'Ra', 'radium', 'element'),
    ('Rubidium', 'Rb', 'rubidium', 'element'),
    ('Rhenium', 'Re', 'rhenium', 'element'),
    ('Rhodium', 'Rh', 'rhodium', 'element'),
    ('Ruthenium', 'Ru', 'ruthenium', 'element'),
    ('Sulfur', 'S', 'sulfur', 'element'),
    ('Total sulfur', 'S(TOT)', 'total sulfur', 'element'),
    ('Sulfur present in pyrite form', 'S_PY', 'sulfur present in pyrite form', 'element'),
    ('Antimony', 'Sb', 'antimony', 'element'),
    ('Scandium', 'Sc', 'scandium', 'element'),
    ('Selenium', 'Se', 'selenium', 'element'),
    ('Silica', 'Si', 'silica', 'element'),
    ('Samarium', 'Sm', 'samarium', 'REE'),
    ('Tin', 'Sn', 'tin', 'element'),
    ('Strontium', 'Sr', 'strontium', 'element'),
    ('Total inorganic carbon', 'TIC', 'total inorganic carbon', 'element'),
    ('Total organic carbon', 'TOC', 'total organic carbon', 'element'),
    ('Tantalum', 'Ta', 'tantalum', 'element'),
    ('Terbium', 'Tb', 'terbium', 'REE'),
    ('Tellurium', 'Te', 'tellurium', 'element'),
    ('Thorium', 'Th', 'thorium', 'element'),
    ('Titanium', 'Ti', 'titanium', 'element'),
    ('Thallium', 'Tl', 'thallium', 'element'),
    ('Thulium', 'Tm', 'thulium', 'REE'),
    ('Uranium', 'U', 'uranium', 'element'),
    ('Vanadium', 'V', 'vanadium', 'element'),
    ('Tungsten', 'W', 'tungsten', 'element'),
    ('Xenon', 'Xe', 'xenon', 'element'),
    ('Yttrium', 'Y', 'yttrium', 'element'),
    ('Ytterbium', 'Yb', 'ytterbium', 'REE'),
    ('Zinc', 'Zn', 'zinc', 'element'),
    ('Zirconium', 'Zr', 'zirconium', 'element'),
    # Oxides
    ('Dialuminum dioxide', 'Al2O2', 'Dialuminum dioxide', 'oxide'),
    ('Aluminium oxide', 'Al2O3', 'aluminium oxide', 'oxide'),
    ('Barium oxide', 'BaO', 'barium oxide', 'oxide'),
    ('Carbon dioxide', 'CO2', 'carbon dioxide', 'oxide'),
    ('Calcium oxide', 'CaO', 'calcium oxide', 'oxide'),
    ('Cerium oxide', 'Ce2O3', 'cerium oxide', 'oxide'),
    ('Cerium dioxide', 'CeO2', 'cerium dioxide', 'oxide'),
    ('Cobalt oxide', 'CoO', 'cobalt oxide', 'oxide'),
    ('Chromium oxide', 'Cr2O3', 'chromium oxide', 'oxide'),
    ('Cu2O', 'Cu2O', 'copper(i) oxide (cuprous oxide)', 'oxide'),
    ('Copper oxide', 'CuO', 'copper oxide', 'oxide'),
    ('Dysprosium oxide', 'Dy2O3', 'dysprosium oxide', 'oxide'),
    ('Erbium oxide', 'Er2O3', 'erbium oxide', 'oxide'),
    ('Europium oxide', 'Eu2O3', 'europium oxide', 'oxide'),
    ('Fe2O3', 'Fe2O3', 'ferric iron oxide (tri-valent iron)', 'oxide'),
    ('Fe2O3T', 'Fe2O3T', 'total iron oxide content reported as ferric (tri-valent) iron', 'oxide'),
    ('Fe3O4', 'Fe3O4', 'ferrosoferric oxide (Iron (II,III) oxide)', 'oxide'),
    ('FeO', 'FeO', 'ferrous iron oxide (di-valent)', 'oxide'),
    ('FeOT', 'FeOT', 'total iron oxide content reported as ferrous (di-valent) iron', 'oxide'),
    ('Gadolinium oxide', 'Gd2O3', 'gadolinium oxide', 'oxide'),
    ('Water', 'H2O', 'water', 'oxide'),
    ('Hafnium dioxide', 'HfO', 'hafnium dioxide', 'oxide'),
    ('Hafnium oxide', 'HfO2', 'hafnium oxide', 'oxide'),
    ('Holmium oxide', 'Ho2O3', 'holmium oxide', 'oxide'),
    ('Potassium oxide', 'K2O', 'potassium oxide', 'oxide'),
    ('Lanthanum oxide', 'La2O3', 'lanthanum oxide', 'oxide'),
    ('Lutetium oxide', 'Lu2O3', 'lutetium oxide', 'oxide'),
    ('Magnesium oxide', 'MgO', 'magnesium oxide', 'oxide'),
    ('Manganese tetroxide', 'Mn3O4', 'manganese tetroxide', 'oxide'),
    ('Manganese oxide', 'MnO', 'manganese oxide', 'oxide'),
    ('Nitrogen dioxide', 'NO2', 'nitrogen dioxide', 'oxide'),
    ('Nitrate', 'NO3', 'nitrate', 'oxide'),
    ('Sodium oxide', 'Na2O', 'sodium oxide', 'oxide'),
    ('Niobium oxide', 'Nb2O3', 'niobium oxide', 'oxide'),
    ('Niobium pentoxide', 'Nb2O5', 'niobium pentoxide', 'oxide'),
    ('Neodymium oxide', 'Nd2O3', 'neodymium oxide', 'oxide'),
    ('Nickel oxide', 'NiO', 'nickel oxide', 'oxide'),
    ('Hydroxide', 'OH', 'hydroxide', 'oxide'),
    ('Phosphorus trioxide', 'P2O3', 'phosphorus trioxide', 'oxide'),
    ('Phosphorus oxide', 'P2O5', 'phosphorus oxide', 'oxide'),
    ('Phosphate', 'PO4', 'phosphate', 'oxide'),
    ('Lead oxide', 'PbO', 'lead oxide', 'oxide'),
    ('Praseodymium oxide', 'Pr2O3', 'praseodymium oxide', 'oxide'),
    ('Pr6O11', 'Pr6O11', 'praseodymium (III, IV) oxide', 'oxide'),
    ('SiO2, high pressure', 'SIOH', 'SiO2, high pressure', 'oxide'),
    ('Sulfur dioxide', 'SO2', 'sulfur dioxide', 'oxide'),
    ('Sulfur trioxide', 'SO3', 'sulfur trioxide', 'oxide'),
    ('Sulfate', 'SO4', 'sulfate', 'oxide'),
    ('Scandium oxide', 'Sc2O3', 'scandium oxide', 'oxide'),
    ('Silica oxide', 'SiO2', 'silica oxide', 'oxide'),
    ('Samarium oxide', 'Sm2O3', 'samarium oxide', 'oxide'),
    ('Strontium oxide', 'SrO', 'strontium oxide', 'oxide'),
    ('Tantalum oxide', 'Ta2O5', 'tantalum oxide', 'oxide'),
    ('Terbium oxide', 'Tb2O3', 'terbium oxide', 'oxide'),
    ('Thorium monoxide', 'ThO', 'thorium monoxide', 'oxide'),
    ('Thorium dioxide', 'ThO2', 'thorium dioxide', 'oxide'),
    ('Ti2O3', 'Ti2O3', 'titanium(III) oxide', 'oxide'),
    ('TiO', 'TiO', 'titanium(II) oxide', 'oxide'),
    ('Titanium oxide', 'TiO2', 'titanium oxide', 'oxide'),
    ('Thulium oxide', 'Tm2O3', 'thulium oxide', 'oxide'),
    ('Uranium oxide', 'UO2', 'uranium oxide', 'oxide'),
    ('Vanadium sesquioxide', 'V2O3', 'vanadium sesquioxide', 'oxide'),
    ('Vanadium pentoxide', 'V2O5', 'vanadium pentoxide', 'oxide'),
    ('Tungsten trioxide', 'WO3', 'tungsten trioxide', 'oxide'),
    ('Y2O3', 'Y2O3', 'yttrium(III) oxide', 'oxide'),
    ('Yttrium oxide', 'YO2', 'yttrium oxide', 'oxide'),
    ('Ytterbium oxide', 'Yb2O3', 'ytterbium oxide', 'oxide'),
    ('Zinc oxide', 'ZnO', 'zinc oxide', 'oxide'),
    ('Zirconium pentoxide', 'Zr2O3', 'zirconium pentoxide', 'oxide'),
    ('Zirconium oxide', 'ZrO2', 'zirconium oxide', 'oxide'),

    # Isotope system: Al
    ('Aluminum isotope Al-26', 'Al26', 'aluminum isotope Al-26', 'isotope'),
    ('Al27/Mg24', 'Al27/Mg24', 'ratio of aluminum isotope Al-27 to magnesium isotope Mg-24', 'isotopic ratio'),

    # Isotope system: Ar
    ('Argon isotope Ar-36', 'Ar36', 'argon isotope Ar-36', 'isotope'),
    ('Argon isotope Ar-37', 'Ar37', 'argon isotope Ar-37', 'isotope'),
    ('Argon isotope Ar-38', 'Ar38', 'argon isotope Ar-38', 'isotope'),
    ('Argon isotope Ar-39', 'Ar39', 'argon isotope Ar-39', 'isotope'),
    ('Argon isotope Ar-40', 'Ar40', 'argon isotope Ar-40', 'isotope'),
    ('Atmospheric argon isotope ar40', 'Ar40/ATM', 'atmospheric argon isotope ar40', 'isotope'),
    ('Radiogenic ar40', 'Ar40*', 'radiogenic ar40', 'isotope'),
    ('Ar36/Ar38', 'Ar36/Ar38', 'ratio of argon isotopes Ar-36 to Ar-38', 'isotopic ratio'),
    ('Ar36/Ar39', 'Ar36/Ar39', 'ratio of argon isotopes Ar-36 to Ar-39', 'isotopic ratio'),
    ('Ar36/Ar40', 'Ar36/Ar40', 'ratio of argon isotopes Ar-36 to Ar-40', 'isotopic ratio'),
    ('Ar36/Xe132', 'Ar36/Xe132', 'ratio of argon isotope Ar-36 to xenon isotope Xe-132', 'isotopic ratio'),
    ('Ar37/Ar40', 'Ar37/Ar40', 'ratio of Ar-37 to Ar-40', 'isotopic ratio'),
    ('Ar38/Ar36', 'Ar38/Ar36', 'ratio of argon isotopes Ar-38 to Ar-36', 'isotopic ratio'),
    ('Ar38/Ar40', 'Ar38/Ar40', 'ratio of argon isotopes Ar-38 to Ar-40', 'isotopic ratio'),
    ('Ar39/Ar40', 'Ar39/Ar40', 'ratio of argon isotopes Ar-39 to Ar-40', 'isotopic ratio'),
    ('Ar40/Ar36', 'Ar40/Ar36', 'ratio of argon isotopes Ar-40 to Ar-36', 'isotopic ratio'),
    ('Ar40/Ar36_Initial', 'Ar40/Ar36_Initial', 'initial ratio of argon isotopes Ar-40 to Ar-37', 'isotopic ratio'),
    ('Ar40/Ar39', 'Ar40/Ar39', 'ratio of argon isotopes Ar-40 to Ar-39', 'isotopic ratio'),
    ('Ar40/He4', 'Ar40/He4', 'ratio of argon isotopes Ar-40 to helium isotope He-4', 'isotopic ratio'),
    ('Ar40*/Ar39_K', 'Ar40*/Ar39_K', 'ratio of argon isotopes, radiogenic Ar-40 to Ar-39 produced from K', 'isotopic ratio'),

    # Isotope system: B
    ('B11/B10', 'B11/B10', 'ratio of boron isotopes B-11 to B-10', 'isotopic ratio'),
    ('Delta_B11', 'Delta_B11', 'calculated as (B11/B10_sample / B11/B10_ NIST SRM951 -1)*1000', 'delta value'),

    # Isotope system: Be
    ('Beryllium isotope Be-10', 'Be10', 'beryllium isotope Be-10', 'isotope'),
    ('Beryllium isotope Be-9', 'Be9', 'beryllium isotope Be-9', 'isotope'),
    ('Be10/Be9', 'Be10/Be9', 'ratio of beryllium isotopes Be-10 to Be-9', 'isotopic ratio'),
    ('Be10/Be9(T)', 'Be10/Be9(T)', 'ratio of isotopes Be-10 to Be-9, time corrected', 'isotopic ratio'),

    # Isotope system: C
    ('Carbon isotope C-14', 'C14', 'carbon isotope C-14', 'isotope'),
    ('Delta_C13', 'Delta_C13', 'calculated as (C13/C12_sample / C13/C12_PDB -1)*1000', 'delta value'),

    # Isotope system: Ca
    ('Calcium isotope Ca-41', 'Ca41', 'calcium isotope Ca-41', 'isotope'),
    ('Delta_Ca44', 'Delta_Ca44', 'calculated as (Ca44/Ca40_sample / Ca44/Ca40_std -1)*1000', 'delta value'),

    # Isotope system: Cd
    ('E_Cd', 'E_Cd', 'calculated as (Cd114/Cd110_sample/ Cd114/Cd110_std - 1)*1000', 'epsilon value'),

    # Isotope system: Ce
    ('Ce136/Ce142', 'Ce136/Ce142', 'ratio of cerium isotopes Ce-136 to Ce-142', 'isotopic ratio'),
    ('Ce138/Ce142', 'Ce138/Ce142', 'ratio of cerium isotopes Ce-138 to Ce-142', 'isotopic ratio'),
    ('Ce140/Nd146', 'Ce140/Nd146', 'ratio of cerium to neodymium isotopes Ce-140 to Nd-146', 'isotopic ratio'),
    ('E_Ce', 'E_Ce', 'calculated as (Ce138/Ce142_sample/ Ce138/Ce142_std - 1)*1000', 'epsilon value'),

    # Isotope system: Cl
    ('Radiogenic Cl isotope Cl-36', 'Cl36', 'radiogenic Cl isotope Cl-36', 'isotope'),
    ('Radiogenic Cl isotope Cl-38', 'Cl38', 'radiogenic Cl isotope Cl-38', 'isotope'),
    ('Delta_Cl37', 'Delta_Cl37', 'calculated as (Cl37/Cl35_sample / Cl37/Cl35_SMOC -1)*1000', 'delta value'),

    # Isotope system: Co
    ('Cobalt isotope Co-56', 'Co56', 'cobalt isotope Co-56', 'isotope'),

    # Isotope system: Cs
    ('Cesium isotope Cs-137 reported as activity', 'Cs137_Activity', 'cesium isotope Cs-137 reported as activity', 'activity'),

    # Isotope system: Cu
    ('DELTA_Cu65', 'DELTA_Cu65', 'calculated as (Cu65/Cu63_sample / Cu65/Cu63_NIST-976 - 1)*1000', 'delta value'),

    # Isotope system: Fe
    ('DELTA_Fe56', 'DELTA_Fe56', 'calculated as (Fe56/Fe54_ sample / Fe56/Fe54_IRMM-014 -1)*1000', 'delta value'),
    ('DELTA_Fe57', 'DELTA_Fe57', 'calculated as (Fe57/Fe54_sample / Fe57/Fe54_IRMM-014 -1)*1000', 'delta value'),

    # Isotope system: Gd
    ('Gd155/Sm152', 'Gd155/Sm152', 'ratio of gadolinium isotope Gd155 to samarium isotope Sm152', 'isotopic ratio'),

    # Isotope system: H
    ('DELTA_D', 'DELTA_D', 'calculated as (H2/H1_sample / H2/H1_std -1)*1000', 'delta value'),
    ('DELTA_H2', 'DELTA_H2', 'calculated as (H2/H1_sample / H2/H1_std -1)*1000', 'delta value'),

    # Isotope system: He
    ('Helium isotope He3', 'He3', 'helium isotope He3', 'isotope'),
    ('Helium isotope He4', 'He4', 'helium isotope He4', 'isotope'),
    ('Helium isotope He4 measured by neutron coincidence counting', 'He4(NCC)', 'helium isotope He4 measured by neutron coincidence counting', 'isotope'),
    ('He3/He4', 'He3/He4', 'ratio of helium isotopes He3 to He4', 'isotopic ratio'),
    ('He3/He4(R/Ra)', 'He3/He4(R/Ra)', 'ratio of helium isotopes He3 to He4 expressed relative to the helium isotope ratio of the atmosphere', 'isotopic ratio'),
    ('He4/Ar40', 'He4/Ar40', 'ratio of helium isotope He4 to argon isotope Ar40', 'isotopic ratio'),
    ('He4/He3', 'He4/He3', 'ratio of helium isotopes He4 to He3', 'isotopic ratio'),
    ('He4/Ne20', 'He4/Ne20', 'ratio of helium isotope He4 to neon isotope Ne20', 'isotopic ratio'),
    ('He4/Ne21', 'He4/Ne21', 'ratio of helium isotope He4 to neon isotope Ne21', 'isotopic ratio'),

    # Isotope system: Hf
    ('Hf174/Hf177', 'Hf174/Hf177', 'ratio of hafnium isotopes Hf174 to Hf177', 'isotopic ratio'),
    ('Hf176/Hf177', 'Hf176/Hf177', 'ratio of hafnium isotopes Hf176 to Hf177', 'isotopic ratio'),
    ('Hf176/Hf177(I)', 'Hf176/Hf177(I)', 'ratio of hafnium isotopes Hf176 to Hf177 at initial time', 'isotopic ratio'),
    ('Hf176/Hf177(T)', 'Hf176/Hf177(T)', 'ratio of hafnium isotopes Hf176 to Hf177, time corrected', 'isotopic ratio'),
    ('Hf177/Hf178', 'Hf177/Hf178', 'ratio of hafnium isotopes Hf177 to Hf178', 'isotopic ratio'),
    ('Hf178/Hf177', 'Hf178/Hf177', 'ratio of hafnium isotopes Hf178 to Hf177', 'isotopic ratio'),
    ('Hf179/Hf177', 'Hf179/Hf177', 'ratio of hafnium isotopes Hf179 to Hf177', 'isotopic ratio'),
    ('Hf180/Hf177', 'Hf180/Hf177', 'ratio of hafnium isotopes Hf180 to Hf177', 'isotopic ratio'),
    ('Hf180/W184', 'Hf180/W184', 'ratio of hafnium isotope Hf180 to wolfram isotope W184', 'isotopic ratio'),
    ('E_Hf', 'E_Hf', 'calculated as (176Hf/177Hf_sample/ 176Hf/177Hf_std - 1)*1000', 'epsilon value'),
    ('E_Hf(T)', 'E_Hf(T)', 'calculated as (176Hf/177Hf_sample/ 176Hf/177Hf_std - 1)*1000, time corrected', 'epsilon value'),

    # Isotope system: Kr
    ('Krypton isotope Kr78', 'Kr78', 'krypton isotope Kr78', 'isotope'),
    ('Krypton isotope Kr80', 'Kr80', 'krypton isotope Kr80', 'isotope'),
    ('Krypton isotope Kr81', 'Kr81', 'krypton isotope Kr81', 'isotope'),
    ('Krypton isotope Kr82', 'Kr82', 'krypton isotope Kr82', 'isotope'),
    ('Krypton isotope Kr83', 'Kr83', 'krypton isotope Kr83', 'isotope'),
    ('Krypton isotope kr84', 'Kr84', 'krypton isotope kr84', 'isotope'),
    ('Krypton isotope Kr86', 'Kr86', 'krypton isotope Kr86', 'isotope'),
    ('Krypton isotope Kr90', 'Kr90', 'krypton isotope Kr90', 'isotope'),
    ('Kr78/Kr83', 'Kr78/Kr83', 'ratio of krypton isotopes Kr78 to Kr83', 'isotopic ratio'),
    ('Kr78/Kr84', 'Kr78/Kr84', 'ratio of krypton isotopes Kr78 to Kr84', 'isotopic ratio'),
    ('Kr78/Kr86', 'Kr78/Kr86', 'ratio of krypton isotopes Kr78 to Kr86', 'isotopic ratio'),
    ('Kr80/Kr83', 'Kr80/Kr83', 'ratio of krypton isotopes Kr80 to Kr83', 'isotopic ratio'),
    ('Kr80/Kr84', 'Kr80/Kr84', 'ratio of krypton isotopes Kr80 to Kr84', 'isotopic ratio'),
    ('Kr80/Kr86', 'Kr80/Kr86', 'ratio of krypton isotopes Kr80 to Kr86', 'isotopic ratio'),
    ('Kr81/Kr86', 'Kr81/Kr86', 'ratio of krypton isotopes Kr81 to Kr86', 'isotopic ratio'),
    ('Kr82/Kr83', 'Kr82/Kr83', 'ratio of krypton isotopes Kr82 to Kr83', 'isotopic ratio'),
    ('Kr82/Kr84', 'Kr82/Kr84', 'ratio of krypton isotopes Kr82 to Kr84', 'isotopic ratio'),
    ('Kr82/Kr86', 'Kr82/Kr86', 'ratio of krypton isotopes Kr82 to Kr86', 'isotopic ratio'),
    ('Kr83/Kr84', 'Kr83/Kr84', 'ratio of krypton isotopes Kr83 to Kr84', 'isotopic ratio'),
    ('Kr83/Kr86', 'Kr83/Kr86', 'ratio of krypton isotopes Kr83 to Kr86', 'isotopic ratio'),
    ('Kr84/Kr83', 'Kr84/Kr83', 'ratio of krypton isotopes Kr84 to Kr83', 'isotopic ratio'),
    ('Kr84/Kr86', 'Kr84/Kr86', 'ratio of krypton isotopes Kr84 to Kr86', 'isotopic ratio'),
    ('Kr84/Xe132', 'Kr84/Xe132', 'ratio of krypton isotopes Kr84 to xenon isotopes Xe132', 'isotopic ratio'),
    ('Kr86/Kr84', 'Kr86/Kr84', 'ratio of krypton isotopes Kr86 to Kr84', 'isotopic ratio'),

    # Isotope system: Li
    ('Li7/Li6', 'Li7/Li6', 'ratio of lithium isotopes Li7 to Li6', 'isotopic ratio'),
    ('DELTA_Li6', 'DELTA_Li6', 'calculated as (Li6/Li7_sample / Li6/Li7_std -1)*1000', 'delta value'),
    ('DELTA_Li7', 'DELTA_Li7', 'calculated as (Li7/Li6_sample / Li7/Li6_std -1)*1000', 'delta value'),

    # Isotope system: Lu
    ('Lu176/Hf177', 'Lu176/Hf177', 'ratio of lutetium isotope Lu176 to hafnium isotope Hf177', 'isotopic ratio'),
    ('Lu176/Hf177(T)', 'Lu176/Hf177(T)', 'ratio of lutetium isotope Lu176 to hafnium isotope Hf177, time corrected', 'isotopic ratio'),
    ('Lu176/Lu177', 'Lu176/Lu177', 'ratio of lutetium isotopes Lu176 to Lu177', 'isotopic ratio'),

    # Isotope system: Mg
    ('DELTA_Mg25', 'DELTA_Mg25', 'calculated as (Mg25/Mg24_sample / Mg25/Mg24_std - 1)*1000', 'delta value'),
    ('DELTA_Mg26', 'DELTA_Mg26', 'calculated as (Mg26/Mg24_sample / Mg26/Mg24_std - 1)*1000', 'delta value'),
    ('E_Mg25', 'E_Mg25', 'calculated as (Mg25/Mg24_sample/ Mg25/Mg24_std - 1)*1000', 'epsilon value'),
    ('E_Mg26', 'E_Mg26', 'calculated as (Mg26/Mg24_sample/ Mg26/Mg24_std - 1)*1000', 'epsilon value'),

    # Isotope system: Mn
    ('Manganese isotope Mn54', 'Mn54', 'manganese isotope Mn54', 'isotope'),

    # Isotope system: Mo
    ('DELTA_Mo98', 'DELTA_Mo98', 'calculated as (Mo98/Mo95_sample / Mo98/Mo95_std - 1)*1000', 'delta value'),

    # Isotope system: N
    ('N2/Ar36', 'N2/Ar36', 'ratio of nitrogen isotope N2 to argon isotope Ar36', 'isotopic ratio'),
    ('N2/He3', 'N2/He3', 'ratio of nitrogen isotope N2 to helium isotope He3', 'isotopic ratio'),
    ('DELTA_N15', 'DELTA_N15', 'calculated as (N15/N14_sample / N15/N14_std - 1)*1000', 'delta value'),

    # Isotope system: Na
    ('Sodium isotope Na22', 'Na22', 'sodium isotope Na22', 'isotope'),

    # Isotope system: Nd
    ('Neodymium isotope Nd144', 'Nd144', 'neodymium isotope Nd144', 'isotope'),
    ('Nd142/Nd144', 'Nd142/Nd144', 'ratio of neodymium isotopes Nd142 to Nd144', 'isotopic ratio'),
    ('Nd143/Nd144', 'Nd143/Nd144', 'ratio of neodymium isotopes Nd143 to Nd144', 'isotopic ratio'),
    ('Nd143/Nd144(I)', 'Nd143/Nd144(I)', 'ratio of neodymium isotopes Nd143 to Nd144 at initial age', 'isotopic ratio'),
    ('Nd143/Nd144(T)', 'Nd143/Nd144(T)', 'ratio of neodymium isotopes Nd143 to Nd144, time corrected', 'isotopic ratio'),
    ('Nd144/Nd146', 'Nd144/Nd146', 'ratio of neodymium isotopes Nd144 to Nd146', 'isotopic ratio'),
    ('Nd145/Nd144', 'Nd145/Nd144', 'ratio of neodymium isotopes Nd145 to Nd144', 'isotopic ratio'),
    ('Nd146/Nd142', 'Nd146/Nd142', 'ratio of neodymium isotopes Nd146 to Nd142', 'isotopic ratio'),
    ('Nd146/Nd144', 'Nd146/Nd144', 'ratio of neodymium isotopes Nd146 to Nd144', 'isotopic ratio'),
    ('Nd146/Nd145', 'Nd146/Nd145', 'ratio of neodymium isotopes Nd146 to Nd145', 'isotopic ratio'),
    ('Nd146/Sm152', 'Nd146/Sm152', 'ratio of neodymium isotope Nd146 to samarium isotope Sm152', 'isotopic ratio'),
    ('Nd148/Nd144', 'Nd148/Nd144', 'ratio of neodymium isotopes Nd148 to Nd144', 'isotopic ratio'),
    ('Nd148O/Nd144O', 'Nd148O/Nd144O', 'ratio of neodymium Nd148 oxide to neodymium Nd144 oxide', 'isotopic ratio'),
    ('Nd150/Nd144', 'Nd150/Nd144', 'ratio of neodymium isotopes Nd150 to Nd144', 'isotopic ratio'),
    ('E_Nd', 'E_Nd', 'calculated as (Nd143/Nd144_sample/ Nd143/Nd144_std - 1)*1000', 'epsilon value'),
    ('E_Nd(T)', 'E_Nd(T)', 'calculated as (Nd143/Nd144_sample/ Nd143/Nd144_std - 1)*1000, time corrected', 'epsilon value'),

    # Isotope system: Ne
    ('Neon isotope ne20', 'Ne20', 'neon isotope ne20', 'isotope'),
    ('Neon isotope Ne21', 'Ne21', 'neon isotope Ne21', 'isotope'),
    ('Neon isotope Ne22', 'Ne22', 'neon isotope Ne22', 'isotope'),
    ('Neon isotope Ne23', 'Ne23', 'neon isotope Ne23', 'isotope'),
    ('Ne20/Ne21', 'Ne20/Ne21', 'ratio of neon isotope Ne20 to Ne21', 'isotopic ratio'),
    ('Ne20/Ne22', 'Ne20/Ne22', 'ratio of neon isotope Ne20 to Ne22', 'isotopic ratio'),
    ('Ne21/He4', 'Ne21/He4', 'ratio of neon isotope Ne21 to helium isotope He4', 'isotopic ratio'),
    ('Ne21/Ne20', 'Ne21/Ne20', 'ratio of neon isotope Ne21 to Ne20', 'isotopic ratio'),
    ('Ne21/Ne22', 'Ne21/Ne22', 'ratio of neon isotope Ne21 to Ne22', 'isotopic ratio'),
    ('Ne22/Ne20', 'Ne22/Ne20', 'ratio of neon isotope Ne22 to Ne20', 'isotopic ratio'),
    ('Ne22/Ne21', 'Ne22/Ne21', 'ratio of neon isotope Ne22 to Ne21', 'isotopic ratio'),

    # Isotope system: Ni
    ('DELTA_Ni60', 'DELTA_Ni60', 'calculated as (Ni60/Ni58_sample / Ni60/Ni58_std - 1)*1000', 'delta value'),

    # Isotope system: O
    ('O17/O16', 'O17/O16', 'ratio of oxygen isotopes O17 to O16', 'isotopic ratio'),
    ('O18/O16', 'O18/O16', 'ratio of oxygen isotopes O18 to O16', 'isotopic ratio'),
    ('Cap_Delta_O17', 'Cap_Delta_O17', 'deviation from the Earth-Moon line of O17/O16 and O18/O16 ratios as the vertical displacement of any point from it, calculated as Cap_Delta_O17=1000*ln(1+(delta_O17/1000))-0.52*1000*ln(1+(delta_O18/1000))', 'delta value'),
    ('DELTA_O17', 'DELTA_O17', 'calculated as (O17/O16_sample / O17/O16_std - 1)*1000', 'delta value'),
    ('DELTA_O18', 'DELTA_O18', 'calculated as (O18/O16_sample / O18/O16_std - 1)*1000', 'delta value'),

    # Isotope system: Os
    ('Osmium isotope Os188', 'Os188', 'osmium isotope Os188', 'isotope'),
    ('Os184/Os188', 'Os184/Os188', 'ratio of osmium isotopes Os184 to Os188', 'isotopic ratio'),
    ('Os186/Os188', 'Os186/Os188', 'ratio of osmium isotopes Os186 to Os188', 'isotopic ratio'),
    ('Os187/Os186', 'Os187/Os186', 'ratio of osmium isotopes Os187 to Os186', 'isotopic ratio'),
    ('Os187/Os188', 'Os187/Os188', 'ratio of osmium isotopes Os187 to Os188', 'isotopic ratio'),
    ('Os187/Os188(I)', 'Os187/Os188(I)', 'ratio of osmium isotopes Os187 to Os188 at initial age', 'isotopic ratio'),
    ('Os187/Os188(T)', 'Os187/Os188(T)', 'ratio of osmium isotopes Os187 to Os188, time corrected', 'isotopic ratio'),
    ('Os188/Os192', 'Os188/Os192', 'ratio of osmium isotopes Os188 to Os192', 'isotopic ratio'),
    ('Os189/Os188', 'Os189/Os188', 'ratio of osmium isotopes Os189 to Os188', 'isotopic ratio'),
    ('Os190/Os188', 'Os190/Os188', 'ratio of osmium isotopes Os190 to Os188', 'isotopic ratio'),
    ('Os192/Os188', 'Os192/Os188', 'ratio of osmium isotopes Os192 to Os188', 'isotopic ratio'),

    # Isotope system: Pa
    ('Protactinium isotope Pa231', 'Pa231', 'protactinium isotope Pa231', 'isotope'),
    ('Excess protactinium Pa231', 'Pa231_XS', 'excess protactinium Pa231', 'isotope'),
    ('Pa231/Th230', 'Pa231/Th230', 'ratio of protactinium isotope Pa231 to thorium isotope Th230', 'isotopic ratio'),
    ('Protactinium isotope Pa231, reported as activity', 'Pa231_ACTIVITY', 'protactinium isotope Pa231, reported as activity', 'activity'),
    ('Pa231/U235_ACTIVITY', 'Pa231/U235_ACTIVITY', 'ratio of protactinium isotope Pa231 to uranium isotope U235, reported as activity', 'activity'),

    # Isotope system: Pb
    ('Lead isotope Pb204', 'Pb204', 'lead isotope Pb204', 'isotope'),
    ('Lead isotope 206', 'Pb206', 'lead isotope 206', 'isotope'),
    ('Lead isotope Pb207', 'Pb207', 'lead isotope Pb207', 'isotope'),
    ('Lead isotope Pb208', 'Pb208', 'lead isotope Pb208', 'isotope'),
    ('Lead isotope Pb210', 'Pb210', 'lead isotope Pb210', 'isotope'),
    ('Excess lead Pb210', 'Pb210_XS', 'excess lead Pb210', 'isotope'),
    ('Pb204_Pb206', 'Pb204/Pb206', 'ratio of lead isotopes Pb204 to Pb206', 'isotopic ratio'),
    ('Pb204_Pb208', 'Pb204/Pb208', 'ratio of lead isotopes Pb204 to Pb208', 'isotopic ratio'),
    ('Pb206_Pb204', 'Pb206/Pb204', 'ratio of lead isotopes Pb206 to Pb204', 'isotopic ratio'),
    ('Pb206/Pb204(I)', 'Pb206/Pb204(I)', 'ratio of lead isotopes Pb206 to Pb204 at initial age', 'isotopic ratio'),
    ('Pb206/Pb204(T)', 'Pb206/Pb204(T)', 'ratio of lead isotopes Pb206 to Pb204, time corrected', 'isotopic ratio'),
    ('Pb206/Pb207', 'Pb206/Pb207', 'ratio of lead isotopes Pb206 to Pb207', 'isotopic ratio'),
    ('Pb206/Pb208', 'Pb206/Pb208', 'ratio of lead isotopes Pb206 to Pb208', 'isotopic ratio'),
    ('Pb206/U235', 'Pb206/U235', 'ratio of lead isotope Pb206 to uranium isotope U235', 'isotopic ratio'),
    ('Pb206/U238', 'Pb206/U238', 'ratio of lead isotope Pb206 to uranium isotope U238', 'isotopic ratio'),
    ('Pb206/U238(T)', 'Pb206/U238(T)', 'ratio of lead isotope Pb206 to uranium isotope U238, time corrected', 'isotopic ratio'),
    ('Pb207/Pb204', 'Pb207/Pb204', 'ratio of lead isotopes Pb207 to Pb204', 'isotopic ratio'),
    ('Pb207/Pb204(I)', 'Pb207/Pb204(I)', 'ratio of lead isotopes Pb207 to Pb204 at initial age', 'isotopic ratio'),
    ('Pb207/Pb204(T)', 'Pb207/Pb204(T)', 'ratio of lead isotopes Pb207 to Pb204, time corrected', 'isotopic ratio'),
    ('Pb207/Pb206', 'Pb207/Pb206', 'ratio of lead isotopes Pb207 to Pb206', 'isotopic ratio'),
    ('Pb207/Pb206(I)', 'Pb207/Pb206(I)', 'ratio of lead isotopes Pb207 to Pb206 at initial age', 'isotopic ratio'),
    ('Pb207/Pb208', 'Pb207/Pb208', 'ratio of lead isotopes Pb207 to Pb208', 'isotopic ratio'),
    ('Pb207/U235', 'Pb207/U235', 'ratio of lead isotope Pb207 to uranium isotope U235', 'isotopic ratio'),
    ('Pb207/U235(T)', 'Pb207/U235(T)', 'ratio of lead isotope Pb207 to uranium isotope U235, time corrected', 'isotopic ratio'),
    ('Pb208/Pb204', 'Pb208/Pb204', 'ratio of lead isotopes Pb208 to Pb204', 'isotopic ratio'),
    ('Pb208/Pb204(I)', 'Pb208/Pb204(I)', 'ratio of lead isotopes Pb208 to Pb204 at initial age', 'isotopic ratio'),
    ('Pb208/Pb204(T)', 'Pb208/Pb204(T)', 'ratio of lead isotopes Pb208 to Pb204, time corrected', 'isotopic ratio'),
    ('Pb208/Pb206', 'Pb208/Pb206', 'ratio of lead isotopes Pb208 to Pb206', 'isotopic ratio'),
    ('Pb208/Pb206(I)', 'Pb208/Pb206(I)', 'ratio of lead isotopes Pb208 to Pb206 at initial age', 'isotopic ratio'),
    ('Pb208/Th232', 'Pb208/Th232', 'ratio of lead isotope Pb208 to thorium isotope Th232', 'isotopic ratio'),
    ('Pb208/Th232(T)', 'Pb208/Th232(T)', 'ratio of lead isotope Pb208 to thorium isotope Th232, time corrected', 'isotopic ratio'),
    ('Pb210/Ra226', 'Pb210/Ra226', 'ratio of lead isotope Pb210 to radium isotope Ra226', 'isotopic ratio'),
    ('Pb210/U238', 'Pb210/U238', 'ratio of lead isotope Pb210 to uranium isotope U238', 'isotopic ratio'),
    ('Lead isotope Pb210, reported as activity', 'Pb210_ACTIVITY', 'lead isotope Pb210, reported as activity', 'activity'),
    ('Pb210/Ra226_ACTIVITY', 'Pb210/Ra226_ACTIVITY', 'ratio of lead isotope Pb210 to radium isotope Ra226, reported as activity', 'activity'),

    # Isotope system: Po
    ('Polonium isotope Po210', 'Po210', 'polonium isotope Po210', 'isotope'),
    ('Po210/Pb210', 'Po210/Pb210', 'ratio of polonium isotope Po210 to lead isotope Pb210', 'isotopic ratio'),
    ('Polonium isotope Po210, reported as activity', 'Po210_ACTIVITY', 'polonium isotope Po210, reported as activity', 'activity'),

    # Isotope system: Pt
    ('Pt190/Os188', 'Pt190/Os188', 'ratio of platinum isotope Pt190 to osmium isotope Os188', 'isotopic ratio'),

    # Isotope system: Ra
    ('Radium isotope Ra226', 'Ra226', 'radium isotope Ra226', 'isotope'),
    ('Ra226/Th230', 'Ra226/Th230', 'ratio of radium isotope Ra226 to thorium isotope Th230', 'isotopic ratio'),
    ('Radium isotope Ra226, reported as activity', 'Ra226_ACTIVITY', 'radium isotope Ra226, reported as activity', 'activity'),
    ('Ra226/Th230/ACTIVITY', 'Ra226/Th230/ACTIVITY', 'ratio of radium isotope Ra226 to thorium isotope Th230, reported as activity', 'activity'),

    # Isotope system: Rb
    ('Rubidium isotope Rb87', 'Rb87', 'rubidium isotope Rb87', 'isotope'),
    ('Rb87/Rb86', 'Rb87/Rb86', 'ratio of rubidium isotopes Rb87 to Rb86', 'isotopic ratio'),
    ('Rb87/Sr86', 'Rb87/Sr86', 'ratio of rubidium isotope Rb87 to strontium isotope Sr86', 'isotopic ratio'),

    # Isotope system: Re
    ('Re187/Os186', 'Re187/Os186', 'ratio of rhenium isotope Re187 to osmium isotope Os186', 'isotopic ratio'),
    ('Re187/Os188', 'Re187/Os188', 'ratio of rhenium isotope Re187 to osmium isotope Os188', 'isotopic ratio'),
    ('Re187/Os189', 'Re187/Os189', 'ratio of rhenium isotope Re187 to osmium isotope Os189', 'isotopic ratio'),

    # Isotope system: S
    ('Cap_Delta_S33', 'Cap_Delta_S33', 'deviation of Delta_S33 from the terrestrial fractionation array, calculated as Cap_Delta_S33=Delta_S33-(Delta_S34/1000+1)^0.515-1)*1000', 'delta value'),
    ('Cap_Delta_S36', 'Cap_Delta_S36', 'deviation of Delta_S36 from the terrestrial fractionation array, calculated as Cap_Delta_S36=Delta_S36-((Delta_S34/1000+1)^1.9-1)*1000', 'delta value'),
    ('DELTA_S33', 'DELTA_S33', 'calculated as (S33/S32_sample / S33/S32_std - 1)*1000', 'delta value'),
    ('DELTA_S34', 'DELTA_S34', 'calculated as (S34/S32_sample / S34/S32_std - 1)*1000', 'delta value'),
    ('DELTA_S34SO4', 'DELTA_S34SO4', 'sulfur isotope of the sulfate; calculated as (S33/S32_sample / S33/S32_std - 1)*1000', 'delta value'),
    ('DELTA_S36', 'DELTA_S36', 'calculated as (S36/S32_sample / S36/S32_std - 1)*1000', 'delta value'),

    # Isotope system: Sc
    ('Scandium isotope Sc46', 'Sc46', 'scandium isotope Sc46', 'isotope'),

    # Isotope system: Si
    ('DELTA_Si29', 'DELTA_Si29', 'calculated as (Si29/Si28_sample / Si29/Si28_std - 1)*1000', 'delta value'),
    ('DELTA_Si30', 'DELTA_Si30', 'calculated as (Si30/Si28_sample / Si30/Si28_std - 1)*1000', 'delta value'),

    # Isotope system: Sm
    ('Samarium isotope Sm147', 'Sm147', 'samarium isotope Sm147', 'isotope'),
    ('Sm144/Sm152', 'Sm144/Sm152', 'ratio of samarium isotopes Sm144 to Sm152', 'isotopic ratio'),
    ('Sm147/Nd143', 'Sm147/Nd143', 'ratio of samarium isotope Sm147 to neodymium isotope Nd143', 'isotopic ratio'),
    ('Sm147/Nd144', 'Sm147/Nd144', 'ratio of samarium isotope Sm147 to neodymium isotope Nd144', 'isotopic ratio'),
    ('Sm147/Nd146', 'Sm147/Nd146', 'ratio of samarium to neodymium isotopes Sm147 to Nd146', 'isotopic ratio'),
    ('Sm148/Sm152', 'Sm148/Sm152', 'ratio of samarium isotopes Sm148 to Sm152', 'isotopic ratio'),
    ('Sm149/Sm152', 'Sm149/Sm152', 'ratio of samarium isotopes Sm149 to Sm152', 'isotopic ratio'),
    ('Sm150/Sm152', 'Sm150/Sm152', 'ratio of samarium isotopes Sm150 to Sm152', 'isotopic ratio'),
    ('Sm154/Sm152', 'Sm154/Sm152', 'ratio of samarium isotopes Sm154 to Sm152', 'isotopic ratio'),

    # Isotope system: Sr
    ('Strontium isotope 86', 'Sr86', 'strontium isotope 86', 'isotope'),
    ('Sr84/Sr86', 'Sr84/Sr86', 'ratio of strontium isotopes Sr84 to Sr86', 'isotopic ratio'),
    ('Sr84/Sr88', 'Sr84/Sr88', 'ratio of strontium isotopes Sr84 to Sr88', 'isotopic ratio'),
    ('Sr86/Sr88', 'Sr86/Sr88', 'ratio of strontium isotopes Sr86 to Sr88', 'isotopic ratio'),
    ('Sr87/Sr86', 'Sr87/Sr86', 'ratio of strontium isotopes Sr87 to Sr86', 'isotopic ratio'),
    ('Sr87/Sr86(I)', 'Sr87/Sr86(I)', 'ratio of strontium isotopes Sr87 to Sr86 at initial age', 'isotopic ratio'),
    ('Sr87/Sr86(T)', 'Sr87/Sr86(T)', 'ratio of strontium isotopes Sr87 to Sr86, time corrected', 'isotopic ratio'),
    ('Sr87/Sr88', 'Sr87/Sr88', 'ratio of strontium isotopes Sr87 to Sr88', 'isotopic ratio'),
    ('Sr88/Sr86', 'Sr88/Sr86', 'ratio of strontium isotopes Sr88 to Sr86', 'isotopic ratio'),
    ('E_Sr', 'E_Sr', 'calculated as (Sr87/Sr86_sample/ Sr87/Sr86_std - 1)*1000', 'epsilon value'),
    ('E_Sr(T)', 'E_Sr(T)', 'calculated as (Sr87/Sr86_sample/ Sr87/Sr86_std - 1)*1000, time corrected', 'epsilon value'),

    # Isotope system: Th
    ('Thorium isotope Th230', 'Th230', 'thorium isotope Th230', 'isotope'),
    ('Excess thorium 230', 'Th230_XS', 'excess thorium 230', 'isotope'),
    ('Thorium isotope Th232', 'Th232', 'thorium isotope Th232', 'isotope'),
    ('Thorium 234', 'Th234', 'thorium 234', 'isotope'),
    ('Thorium 234 excess', 'Th234_XS', 'thorium 234 excess', 'isotope'),
    ('Th228/Th232', 'Th228/Th232', 'ratio of thorium isotopes Th228 to Th232', 'isotopic ratio'),
    ('Th230/Th232', 'Th230/Th232', 'ratio of thorium isotopes Th230 to Th232', 'isotopic ratio'),
    ('Th230/U238', 'Th230/U238', 'ratio of thorium isotope Th230 to uranium isotope U238', 'isotopic ratio'),
    ('Th232_Pb204', 'Th232_Pb204', 'ratio of thorium isotope Th232 to lead isotope Pb204', 'isotopic ratio'),
    ('Th232_Pb208', 'Th232_Pb208', 'ratio of thorium isotope Th232 to lead isotope Pb208', 'isotopic ratio'),
    ('Th232_Th230', 'Th232_Th230', 'ratio of isotopes Th232 to Th230', 'isotopic ratio'),
    ('Th232/U238', 'Th232/U238', 'ratio of thorium isotope Th232 to uranium isotope U238', 'isotopic ratio'),
    ('Th227 reported as activity', 'Th227_ACTIVITY', 'Th227 reported as activity', 'activity'),
    ('Thorium isotope Th230, reported as activity', 'Th230_ACTIVITY', 'thorium isotope Th230, reported as activity', 'activity'),
    ('Th230/Th232_ACTIVITY', 'Th230/Th232_ACTIVITY', 'ratio of thorium isotopes Th230 to Th232, reported as activity', 'activity'),
    ('Th230_U238_ACTIVITY', 'Th230_U238_ACTIVITY', 'ratio of thorium isotope Th230 to uranium isotope U238, reported as activity', 'activity'),
    ('Thorium isotope Th232, reported as activity', 'Th232_ACTIVITY', 'thorium isotope Th232, reported as activity', 'activity'),
    ('Th232/Th230_ACTIVITY', 'Th232/Th230_ACTIVITY', 'ratio of isotopes Th232 to Th230 measured as activity', 'activity'),
    ('Th238/Th232_ACTIVITY', 'Th238/Th232_ACTIVITY', 'ratio of thorium isotopes Th238 to Th232, reported as activity', 'activity'),

    # Isotope system: Ti
    ('DELTA_Ti49', 'DELTA_Ti49', 'calculated as (Ti49/Ti47_sample / Ti49/Ti47_std - 1)*1000', 'delta value'),

    # Isotope system: Tl
    ('Tl203/Tl205', 'Tl203/Tl205', 'ratio of thallium isotopes Tl203 to Tl205', 'isotopic ratio'),
    ('Tl205/Tl203', 'Tl205/Tl203', 'ratio of thallium isotopes Tl205 to Tl203', 'isotopic ratio'),
    ('E_Tl', 'E_Tl', 'calculated as (Tl205/Tl203_sample/ Tl205/Tl203_std - 1)*1000', 'epsilon value'),

    # Isotope system: U
    ('Uranium isotope U234', 'U234', 'uranium isotope U234', 'isotope'),
    ('Uranium isotope U238', 'U238', 'uranium isotope U238', 'isotope'),
    ('U/Zr91', 'U/Zr91', 'ratio of uranium to zirconium isotope Zr91', 'isotopic ratio'),
    ('U/Zr92', 'U/Zr92', 'ratio of uranium to zirconium isotope Zr92', 'isotopic ratio'),
    ('U234/U238', 'U234/U238', 'ratio of uranium isotopes U234 to U238', 'isotopic ratio'),
    ('U235/Pb204', 'U235/Pb204', 'ratio of uranium isotope U235 to lead isotope Pb204', 'isotopic ratio'),
    ('U235/Pb207', 'U235/Pb207', 'ratio of uranium isotope U235 to lead isotope Pb207', 'isotopic ratio'),
    ('U235/U234', 'U235/U234', 'ratio of uranium isotopes U235 to U234', 'isotopic ratio'),
    ('U236/Pb204', 'U236/Pb204', 'ratio of uranium isotope U236 to lead isotope Pb204', 'isotopic ratio'),
    ('U236/U238', 'U236/U238', 'ratio of uranium isotopes U236 to U238', 'isotopic ratio'),
    ('U238/Pb204', 'U238/Pb204', 'ratio of uranium isotope U238 to lead isotope Pb204', 'isotopic ratio'),
    ('U238/Pb206', 'U238/Pb206', 'ratio of uranium isotope U238 to lead isotope Pb206', 'isotopic ratio'),
    ('U238/Pb208', 'U238/Pb208', 'ratio of uranium isotope U238 to lead isotope Pb208', 'isotopic ratio'),
    ('U238/Th230', 'U238/Th230', 'ratio of uranium isotope U238 to thorium isotope Th230', 'isotopic ratio'),
    ('U238/Th232', 'U238/Th232', 'ratio of uranium isotope U238 to thorium isotope Th232', 'isotopic ratio'),
    ('U230/Th232_ACTIVITY', 'U230/Th232_ACTIVITY', 'ratio of uranium isotope U230 to thorium isotope Th232, reported as activity', 'activity'),
    ('Uranium isotope U234, reported as activity', 'U234_ACTIVITY', 'uranium isotope U234, reported as activity', 'activity'),
    ('U234/U238_ACTIVITY', 'U234/U238_ACTIVITY', 'ratio of uranium isotopes U234 to U238, measured as activity', 'activity'),
    ('U234/U238_ACTIVITY(T)', 'U234/U238_ACTIVITY(T)', 'ratio of uranium isotopes U234 to U238, measured as activity at time t', 'activity'),
    ('Uranium isotope U238, reported as activity', 'U238_ACTIVITY', 'uranium isotope U238, reported as activity', 'activity'),
    ('U238/Th230_ACTIVITY', 'U238/Th230_ACTIVITY', 'ratio of uranium isotope U238 to thorium isotope Th230, reported as activity', 'activity'),
    ('U238/Th232_ACTIVITY', 'U238/Th232_ACTIVITY', 'ratio of uranium isotope U238 to thorium isotope Th232, reported as activity', 'activity'),
    ('DELTA_U234', 'DELTA_U234', 'calculated as (U234/U238_sample / U234/U238_secular_equilibrium - 1)*1000', 'delta value'),
    ('DELTA_U238', 'DELTA_U238', 'calculated as (U238/U235_sample / U238/U235_secular_equilibrium - 1)*1000', 'delta value'),

    # Isotope system: V
    ('Vanadium isotope V48', 'V48', 'vanadium isotope V48', 'isotope'),
    ('DELTA_V51', 'DELTA_V51', 'calculated as (V51/V50_sample / V51/V50_std - 1)*1000', 'delta value'),

    # Isotope system: W
    ('W182/W184', 'W182/W184', 'ratio of tungsten isotopes W182 to W184', 'isotopic ratio'),
    ('E_W182', 'E_W182', 'calculated as (W182/W184_sample/ W182/W184_std - 1)*1000', 'epsilon value'),
    ('E_W183', 'E_W183', 'calculated as (W183/W184_sample/ W183/W184_std - 1)*1000', 'epsilon value'),

    # Isotope system: Xe
    ('Xenon isotope Xe124', 'Xe124', 'xenon isotope Xe124', 'isotope'),
    ('Xenon isotope Xe126', 'Xe126', 'xenon isotope Xe126', 'isotope'),
    ('Xenon isotope Xe128', 'Xe128', 'xenon isotope Xe128', 'isotope'),
    ('Xenon isotope Xe129', 'Xe129', 'xenon isotope Xe129', 'isotope'),
    ('Xenon isotope Xe130', 'Xe130', 'xenon isotope Xe130', 'isotope'),
    ('Xenon isotope Xe131', 'Xe131', 'xenon isotope Xe131', 'isotope'),
    ('Xenon isotope Xe132', 'Xe132', 'xenon isotope Xe132', 'isotope'),
    ('Xenon isotope Xe134', 'Xe134', 'xenon isotope Xe134', 'isotope'),
    ('Xenon isotope Xe136', 'Xe136', 'xenon isotope Xe136', 'isotope'),
    ('Xe124/Xe126', 'Xe124/Xe126', 'ratio of xenon isotopes Xe124 to Xe126', 'isotopic ratio'),
    ('Xe124/Xe130', 'Xe124/Xe130', 'ratio of xenon isotopes Xe124 to Xe130', 'isotopic ratio'),
    ('Xe124/Xe132', 'Xe124/Xe132', 'ratio of xenon isotopes Xe124 to Xe132', 'isotopic ratio'),
    ('Xe126/Xe130', 'Xe126/Xe130', 'ratio of xenon isotopes Xe126 to Xe130', 'isotopic ratio'),
    ('Xe126/Xe132', 'Xe126/Xe132', 'ratio of xenon isotopes Xe126 to Xe132', 'isotopic ratio'),
    ('Xe128/Xe130', 'Xe128/Xe130', 'ratio of xenon isotopes Xe128 to Xe130', 'isotopic ratio'),
    ('Xe128/Xe132', 'Xe128/Xe132', 'ratio of xenon isotopes Xe128 to Xe132', 'isotopic ratio'),
    ('Xe129/Xe130', 'Xe129/Xe130', 'ratio of xenon isotopes Xe129 to Xe130', 'isotopic ratio'),
    ('Xe129/Xe132', 'Xe129/Xe132', 'ratio of xenon isotopes Xe129 to Xe132', 'isotopic ratio'),
    ('Xe129/Xe136', 'Xe129/Xe136', 'ratio of xenon isotopes Xe129 to Xe136', 'isotopic ratio'),
    ('Xe130/Xe132', 'Xe130/Xe132', 'ratio of xenon isotopes Xe130 to Xe132', 'isotopic ratio'),
    ('Xe131/Xe126', 'Xe131/Xe126', 'ratio of xenon isotopes Xe131 to Xe126', 'isotopic ratio'),
    ('Xe131/Xe130', 'Xe131/Xe130', 'ratio of xenon isotopes Xe131 to Xe130', 'isotopic ratio'),
    ('Xe131/Xe132', 'Xe131/Xe132', 'ratio of xenon isotopes Xe131 to Xe132', 'isotopic ratio'),
    ('Xe132/Xe130', 'Xe132/Xe130', 'ratio of xenon isotopes Xe132 to Xe130', 'isotopic ratio'),
    ('Xe134/Xe130', 'Xe134/Xe130', 'ratio of xenon isotopes Xe134 to Xe130', 'isotopic ratio'),
    ('Xe134/Xe132', 'Xe134/Xe132', 'ratio of xenon isotopes Xe134 to Xe132', 'isotopic ratio'),
    ('Xe134/Xe136', 'Xe134/Xe136', 'ratio of xenon isotopes Xe134 to Xe136', 'isotopic ratio'),
    ('Xe136/He4', 'Xe136/He4', 'ratio of xenon isotope Xe136 to helium isotope he4', 'isotopic ratio'),
    ('Xe136/Xe130', 'Xe136/Xe130', 'ratio of xenon isotopes Xe136 to Xe130', 'isotopic ratio'),
    ('Xe136/Xe132', 'Xe136/Xe132', 'ratio of xenon isotopes Xe136 to Xe132', 'isotopic ratio'),

    # Isotope system: Yb
    ('Yb176/Hf177', 'Yb176/Hf177', 'ratio of ytterbium isotope Yb176 to hafnium isotope Hf177', 'isotopic ratio'),

    # Isotope system: Zn
    ('DELTA_Zn66', 'DELTA_Zn66', 'calculated as (Zn66/Zn64_sample / Zn66/Zn64_std - 1)*1000', 'delta value'),
    ('DELTA_Zn68', 'DELTA_Zn68', 'calculated as (Zn68/Zn64_sample / Zn68/Zn64_std - 1)*1000', 'delta value'),

    # Compounds and other
    ('Acetate', 'Acetate', 'acetate', 'compound'),
    ('Barite', 'BaSO4', 'barite', 'compound'),
    ('Methane', 'CH4', 'methane', 'compound'),
    ('Calcium carbonate', 'CaCO3', 'calcium carbonate', 'compound'),
    ('Calcium sulfate', 'CaSO4', 'calcium sulfate', 'compound'),
    ('Fe-Fe', 'Fe-Fe', 'iron ferrite (FeFe2O4)', 'compound'),
    ('Siderite', 'FeCO3', 'siderite', 'compound'),
    ('FeS', 'FeS', 'ferrous sulfide (di-valent)', 'compound'),
    ('Iron sulfide', 'FeS2', 'iron sulfide', 'compound'),
    ('Hydrogen (diatomic)', 'H2', 'hydrogen', 'compound'),
    ('H2OM', 'H2OM', 'crystal water (H2O-)', 'compound'),
    ('H2OP', 'H2OP', 'crystal water (H2O+)', 'compound'),
    ('Hydrogen sulfide', 'H2S', 'hydrogen sulfide', 'compound'),
    ('Total hydrogen sulfide', 'H2S(TOT)', 'total hydrogen sulfide', 'compound'),
    ('Silicic acid', 'H4SiO4', 'silicic acid', 'compound'),
    ('Bicarbonate', 'HCO3', 'bicarbonate', 'compound'),
    ('Manganese carbonate', 'MnCO3', 'manganese carbonate', 'compound'),
    ('Nitrogen (diatomic)', 'N2', 'nitrogen', 'compound'),
    ('Nitrogen measured in nanomols', 'N2[nmol]', 'nitrogen measured in nanomols', 'compound'),
    ('Ammonia', 'NH3', 'ammonia', 'compound'),
    ('Ammonium', 'NH4', 'ammonium', 'compound'),
    ('Oxygen (diatomic)', 'O2', 'dioxygen', 'compound'),
    ('Sulfur present as sulfide', 'S_(SLFI)', 'sulfur present as sulfide', 'compound'),
    ('Ti-magnetite', 'TI-MT', 'ti-magnetite', 'compound'),
    ('Titanoniobate', 'TI-NB', 'titanoniobate', 'compound'),
    ('Alkalinity', 'Alk', 'alkalinity', 'other'),
    ('Bromide', 'Br-', 'bromide', 'other'),
    ('Chrg_Bal', 'Chrg_Bal', 'electrical charge balance, calculated as the sum of cations vs. anions', 'other'),
    ('Fallout radionuclide measurement', 'FRM', 'fallout radionuclide measurement', 'other'),
    ('Fe3/FeT', 'Fe3/FeT', 'ratio of feric iron to total iron', 'other'),
    ('Gamma osmium', 'G_Os', 'gamma osmium', 'other'),
    ('Gamma osmium, time corrected', 'G_Os(T)', 'gamma osmium, time corrected', 'other'),
    ('Loss on ignition', 'LOI', 'loss on ignition', 'other'),
    ('Percent nitrogen in the a defect site of diamonds', 'N(A)', 'percent nitrogen in the a defect site of diamonds', 'other'),
    ('Percent nitrogen in the b defect site of diamonds', 'N(B)', 'percent nitrogen in the b defect site of diamonds', 'other'),
    ('Pressure', 'PRESS', 'pressure', 'other'),
    ('Salinity', 'SAL', 'salinity', 'other'),
    ('Amorphous silica', 'Si(AMORPH)', 'amorphous silica', 'other'),
    ('Talc', 'TALC', 'talc', 'other'),
    ('Temperature', 'TEMP', 'temperature', 'other'),
    ('Total weight percent of analyzed parameters', 'TOTAL', 'total weight percent of analyzed parameters', 'other'),
    ('PH', 'pH', 'pH', 'other'),
    ('The correlation coefficient used to calculate the best-fit line', 'r2', 'the correlation coefficient used to calculate the best-fit line', 'other'),
]
"""Static list of valid geochemical analytes. Used to populate GeoChemicalAnalytes table."""

calculated_analytes = [
    ('Sample age', 'Age', 'sample age'),
    ('B/Ca', 'B/Ca', 'ratio of boron to calcium'),
    ('Ba/Ca', 'Ba/Ca', 'ratio of barium to calcium'),
    ('C-14_Age', 'C14_Age', 'C-14_Age'),
    ('C/N', 'C/N', 'ratio of organic carbon to total nitrogen'),
    ('Ca/K', 'Ca/K', 'ratio of calcium to potassium'),
    ('Calibrated C-14_Age', 'C14_Age_Calibrated', 'calibrated C-14_Age'),
    ('Cd/Ca', 'Cd/Ca', 'ratio of cadmium to calcium'),
    ('Mg/Ca', 'Mg/Ca', 'ratio of magnesium to calcium'),
    ('Min[EM]', 'Min[EM]', 'End member (replace Min with mineral abbreviation)'),
    ('Mn_Ca', 'Mn_Ca', 'ratio of manganese to calcium'),
    ('Nd/Ca', 'Nd/Ca', 'ratio of neodymium to calcium'),
    ('Sr/Ca', 'Sr/Ca', 'ratio of Sr to Ca')
]
"""Geochemical analytes removed from EarthChem list. Element ratios to be created as calculated values instead later"""


as_table_dict = {
    'DirectAgeErrorFormats': 'ErrorFormats',
    'OldAge': 'Ages',
    'YoungAge': 'Ages',
    'SampleAgeUnits': 'AgeUnits',
    'SampleAgeConstraints': 'AgeConstraints',
    'SampleAgeInterpretations': 'AgeInterpretations',
    'SampleAgeReferences': 'References',
    'SampleGPS': 'GPSLocations',
    'SampleLatDirections': 'DirectionUnits',
    'SampleLonDirections': 'DirectionUnits',
    'SampleElevationUnits': 'DistanceUnits',
    'SampleGPSFormats': 'GPSFormats',
    'ColumnGPS': 'GPSLocations',
    'ColumnLatDirections': 'DirectionUnits',
    'ColumnLonDirections': 'DirectionUnits',
    'ColumnElevationUnits': 'DistanceUnits',
    'ColumnGPSFormats': 'GPSFormats',
    'ColumnUnits': 'DistanceUnits',
    'ColumnHeightDepthUnits': 'DistanceUnits',
    'UPbLabFacilities': 'LabFacilities',
    'UPbInstruments': 'Instruments',
    'UPbReferences': 'References',
    'UPbRatioErrorFormats': 'ErrorFormats',
    'UPbAgeErrorFormats': 'ErrorFormats',
    'UPbAgeUnits': 'AgeUnits',
    'UPbAgeInterpretations': 'AgeInterpretations',
    'UPbConcordanceFormats': 'ConcordanceFormats',
    'UPbSpotSizeUnits': 'DistanceUnits',
    'UPbRejectionReasons': 'RejectionReasons',
    'UPbAnalysisContexts': 'UPbAnalysisContexts',
    'DefaultSampleAges': 'SampleAges',
    'GeoChemReferences': 'References',
    'GeoChemLabFacilities': 'LabFacilities',
    'GeoChemInstruments': 'Instruments',
    'GeoChemAnalyteErrorFormats': 'ErrorFormats',
    'GeoChemAnalyteUnits': 'AnalyticalUnits',
    'GeoChemSpotSizeUnits': 'DistanceUnits',
    'GeoChemRejectionReasons': 'RejectionReasons',
    'GeoChemicalAnalysisContexts': 'GeoChemicalAnalysisContexts'
}
"""Static list of foreign key references found in tables and their associated table.
Issues with database properly keeping track of this through pragma queries have led to this
to ensure values are not missed"""

table_attributes_dict = {
    'AgeConstraints': [
        "AgeConstraintName", "AgeConstraintDescription",
        "AgeConstraintCreated", "AgeConstraintModified"],
    'AgeInterpretations': [
        "AgeInterpretationName", "AgeInterpretationDescription",
        "AgeInterpretationCreated", "AgeInterpretationModified"],
    'Ages': [
        "AgeName", "OldestAge", "YoungestAge",
        "AgeCreated", "AgeModified"
    ],
    'AgeSignatures': [
        "AgeSignatureName", "AgeSignatureDescription",
        "AgeSignatureCreated", "AgeSignatureModified"
    ],
    'AliquotContexts': [
        "AliquotContextName", "AliquotContextDescription",
        "AliquotContextCreated", "AliquotContextModified"
    ],
    'Aliquots': [
        "AliquotName", "AliquotDescription", "AliquotCreated", "AliquotModified"
    ],
    'Columns': [
        "ColumnName", "ColumnDescription",
        "CalculatedColumnTotalHeightDepth",
        "ColumnCreated", "ColumnModified"
    ],
    'GPSLocations': [
        "GPSLocationConverted", "GPSLocationDisplay",
        "CalculatedZone", "CalculatedEasting", "CalculatedNorthing",
        "CalculatedLat", "CalculatedLon",
        "CalculatedGPSElev", "CalculatedGPSElevError"
    ],
    'GrainCompositions': [
        "GrainCompositionName", "GrainCompositionDescription",
        "GrainCompositionCreated", "GrainCompositionModified"
    ],
    'GrainContexts': [
        "GrainContextName", "GrainContextDescription",
        "GrainContextCreated", "GrainContextModified"
    ],
    'Grains': [
        "GrainName", "GrainDescription", "GrainCreated", "GrainModified"
    ],
    'Instruments': [
        "InstrumentName", "InstrumentDescription",
        "InstrumentCreated", "InstrumentModified"
    ],
    'LabFacilities': [
        "LabFacilityName", "LabFacilityDescription",
        "LabFacilityCreated", "LabFacilityModified"
    ],
    'References': [
        "Authors", "Year", "Title", "Source", "DOI", "ReferenceDescription",
        "ReferenceCreated", "ReferenceModified", "ReferenceDisplay"
    ],
    'Regions': [
        "RegionName", "RegionDescription",
        "RegionCreated", "RegionModified"
    ],
    'RejectionReasons': [
        "RejectionReasonName", "RejectionReasonDescription",
        "RejectionReasonCreated", "RejectionReasonModified"
    ],
    'RockTypes': [
        "RockTypeName", "RockTypeDescription",
        "RockTypeCreated", "RockTypeModified"
    ],
    'SampleAges': [
        "CalculatedDirectAge", "CalculatedDirectAgeError", "CalculatedOldestDirectAge", "CalculatedYoungestDirectAge",
        "SampleAgeDescription", 'OldestAge', 'YoungestAge', "SampleAgeCreated", "SampleAgeModified"
    ],
    'SampleContexts': [
        "SampleContextName", "SampleContextDescription",
        "SampleContextCreated", "SampleContextModified"
    ],
    'Samples': [
        "SampleName", "SampleIGSN", "CalculatedHeightDepth", "CalculatedHeightDepthError", "SampleDescription",
        "SampleCreated", "SampleModified"
    ],
    'SamplingMethods': [
        "SamplingMethodName", "SamplingMethodDescription",
        "SamplingMethodCreated", "SamplingMethodModified"
    ],
    'Settings': [
        "SettingName", "SettingDescription",
        "SettingCreated", "SettingModified"
    ],
    'Spots': [
        "SpotName", "SpotDescription", "SpotCreated", "SpotModified"
    ],
    'SpotCompositions': [
        "SpotCompositionName", "SpotCompositionDescription",
        "SpotCompositionCreated", "SpotCompositionModified"
    ],
    'SpotContexts': [
        "SpotContextName", "SpotContextDescription",
        "SpotContextCreated", "SpotContextModified"
    ],
    'UPbAnalyses': [
        "UPbAnalysisName",
        "Pb204cps",
        "Pb206cps",
        "Pb207cps",
        "Pb208cps",
        "Pb*cps",
        "Th232cps",
        "U235cps",
        "U238cps",
        "Uppm",
        "Thppm",
        "CalculatedU/Th",
        "CalculatedTh/U",

        "Calculated204Pb/206Pb",
        "Calculated204Pb/206PbError",
        "Calculated204Pb/207Pb",
        "Calculated204Pb/207PbError",
        "Calculated204Pb/208Pb",
        "Calculated204Pb/208PbError",
        "Calculated204Pb/238U",
        "Calculated204Pb/238UError",
        "Calculated206Pb/204Pb",
        "Calculated206Pb/204PbError",
        "Calculated206Pb/207Pb",
        "Calculated206Pb/207PbError",
        "Calculated206Pb/238U",
        "Calculated206Pb/238UError",
        "Calculated207Pb/204Pb",
        "Calculated207Pb/204PbError",
        "Calculated207Pb/206Pb",
        "Calculated207Pb/206PbError",
        "Calculated207Pb/235U",
        "Calculated207Pb/235UError",
        "Calculated208Pb/204Pb",
        "Calculated208Pb/204PbError",
        "Calculated208Pb/232Th",
        "Calculated208Pb/232ThError",
        "Calculated232Th/208Pb",
        "Calculated232Th/208PbError",
        "Calculated232Th/238U",
        "Calculated232Th/238UError",
        "Calculated235U/207Pb",
        "Calculated235U/207PbError",
        "Calculated238U/204Pb",
        "Calculated238U/204PbError",
        "Calculated238U/206Pb",
        "Calculated238U/206PbError",
        "Calculated238U/232Th",
        "Calculated238U/232ThError",

        "Calculated206Pb/238UAge",
        "Calculated206Pb/238UAgeError",
        "Calculated207Pb/206PbAge",
        "Calculated207Pb/206PbAgeError",
        "Calculated207Pb/235UAge",
        "Calculated207Pb/235UAgeError",
        "Calculated208Pb/232ThAge",
        "Calculated208Pb/232ThAgeError",
        "CalculatedBestAge",
        "CalculatedBestAgeError",
        "CalculatedBestAgeFilled",
        "CalculatedBestAgeErrorFilled",

        "ErrorCorr/Rho_68v76",
        "ErrorCorr/Rho_68v75",

        "CalculatedConcordance_206Pb/238Uv207Pb/206Pb",
        "CalculatedConcordance_206Pb/238Uv207Pb/235U",
        "MinimumSegmentedDiscordance",
        "Rejected",
        "CalculatedUPbSpotSize",

        "UPbAnalysisCreated",
        "UPbAnalysisModified"
    ],
    'UPbAnalysisContexts': [
        "UPbAnalysisContextName", "UPbAnalysisContextDescription",
        "UPbAnalysisContextCreated", "UPbAnalysisContextModified"
    ],
    'UPbAnalysisMethods': [
        "UPbAnalysisMethodName", "UPbAnalysisMethodDescription",
        "UPbAnalysisMethodCreated", "UPbAnalysisMethodModified"
    ],
    'Units': [
        "UnitName", "UnitDescription",
        "UnitCreated", "UnitModified"
    ]
}
"""List of all columns visible to the user.
Used in ExporterWidget.py as valid columns able to be exported
Used in Filters.py as valid columns to be filtered"""

table_attributes_description_dict = {
    'AgeConstraints': {'attributes': [
        "AgeConstraintName", "AgeConstraintDescription",
        "AgeConstraintCreated", "AgeConstraintModified"], 'description': 'How the ages are constrained: e.g. biostratigraphy, weighted mean'},
    'AgeInterpretations': {'attributes': [
        "AgeInterpretationName", "AgeInterpretationDescription",
        "AgeInterpretationCreated", "AgeInterpretationModified"], 'description': 'How the ages are interpreted: e.g. deposition, metamorphism'},
    'AgeSignatures': {'attributes': [
        "AgeSignatureName", "AgeSignatureDescription",
        "AgeSignatureCreated", "AgeSignatureModified"], 'description': 'Descriptors for age fingerprints or populations of ages'},
    'AliquotContexts': {'attributes': [
        "AliquotContextName", "AliquotContextDescription",
        "AliquotContextCreated", "AliquotContextModified"], 'description': 'Open-ended tag for additional context'},
    'Aliquots': {'attributes': [
        "AliquotName", "AliquotDescription", "AliquotCreated", "AliquotModified"], 'description': 'Subsets of samples - can be nested subsets, links to samples and spots'},
    'Columns': {'attributes': [
        "ColumnName", "ColumnDescription",
        "CalculatedColumnTotalHeightDepth",
        "ColumnCreated", "ColumnModified"], 'description': 'Cores, wells, stratigraphic columns, etc.'},
    'GPSLocations': {'attributes': [
        "GPSLocationConverted", "GPSLocationDisplay",
        "CalculatedZone", "CalculatedEasting", "CalculatedNorthing",
        "CalculatedLat", "CalculatedLon",
        "CalculatedGPSElev", "CalculatedGPSElevError"], 'description': 'GPS coordinates and elevations'},
    'GrainCompositions': {'attributes': [
        "GrainCompositionName", "GrainCompositionDescription",
        "GrainCompositionCreated", "GrainCompositionModified"], 'description': 'Minerals or descriptive compositions of grains'},
    'GrainContexts': {'attributes': [
        "GrainContextName", "GrainContextDescription",
        "GrainContextCreated", "GrainContextModified"], 'description': 'Open-ended tag for additional context'},
    'Grains': {'attributes': [
        "GrainName", "GrainDescription", "GrainCreated", "GrainModified"], 'description': 'Grains, optionally associated with spots'},
    'Instruments': {'attributes': [
        "InstrumentName", "InstrumentDescription",
        "InstrumentCreated", "InstrumentModified"], 'description': 'Instruments used for analyses'},
    'LabFacilities': {'attributes': [
        "LabFacilityName", "LabFacilityDescription",
        "LabFacilityCreated", "LabFacilityModified"], 'description': 'Lab facilities where analyses were conducted'},
    'References': {'attributes': [
        "Authors", "Year", "Title", "Source", "DOI", "ReferenceDescription",
        "ReferenceCreated", "ReferenceModified", "ReferenceDisplay"], 'description': 'References for analyses'},
    'Regions': {'attributes': [
        "RegionName", "RegionDescription",
        "RegionCreated", "RegionModified"], 'description': 'Regions of sample sites'},
    'RejectionReasons': {'attributes': [
        "RejectionReasonName", "RejectionReasonDescription",
        "RejectionReasonCreated", "RejectionReasonModified"], 'description': 'Reasons for analysis rejection'},
    'RockTypes': {'attributes': [
        "RockTypeName", "RockTypeDescription",
        "RockTypeCreated", "RockTypeModified"], 'description': 'Rock types of samples'},
    'SampleAges': {'attributes': [
        "CalculatedDirectAge", "CalculatedDirectAgeError", "CalculatedOldestDirectAge", "CalculatedYoungestDirectAge",
        "SampleAgeDescription", "SampleAgeCreated", "SampleAgeModified"], 'description': 'Ages of the samples'},
    'SampleContexts': {'attributes': [
        "SampleContextName", "SampleContextDescription",
        "SampleContextCreated", "SampleContextModified"], 'description': 'Open-ended tag for additional context'},
    'Samples': {'attributes': [
        "SampleName", "SampleIGSN", "CalculatedHeightDepth", "CalculatedHeightDepthError", "SampleDescription",
        "SampleCreated", "SampleModified"], 'description': 'Samples each collected from a single location, linked to aliquots and analyses'},
    'SamplingMethods': {'attributes': [
        "SamplingMethodName", "SamplingMethodDescription",
        "SamplingMethodCreated", "SamplingMethodModified"], 'description': 'Methods of sampling: e.g. grab, core'},
    'Settings': {'attributes': [
        "SettingName", "SettingDescription",
        "SettingCreated", "SettingModified"], 'description': 'Sample settings: e.g. basin, batholith, tectonic environment'},
    'Spots': {'attributes': [
        "SpotName", "SpotDescription", "SpotCreated", "SpotModified"], 'description': 'Locations of analysis: e.g. laser spot, dissolved grain'},
    'SpotCompositions': {'attributes': [
        "SpotCompositionName", "SpotCompositionDescription",
        "SpotCompositionCreated", "SpotCompositionModified"], 'description': 'Compositions of analyzed material - may be different from overall rock or grain'},
    'SpotContexts': {'attributes': [
        "SpotContextName", "SpotContextDescription",
        "SpotContextCreated", "SpotContextModified"], 'description': 'Open-ended tag for additional context: e.g. rim, core'},
    'UPbAnalyses': {'attributes': [
        "UPbAnalysisName",
        "Pb204cps",
        "Pb206cps",
        "Pb207cps",
        "Pb208cps",
        "Pb*cps",
        "Th232cps",
        "U235cps",
        "U238cps",
        "Uppm",
        "Thppm",
        "CalculatedU/Th",
        "CalculatedTh/U",

        "Calculated204Pb/206Pb",
        "Calculated204Pb/206PbError",
        "Calculated204Pb/207Pb",
        "Calculated204Pb/207PbError",
        "Calculated204Pb/208Pb",
        "Calculated204Pb/208PbError",
        "Calculated204Pb/238U",
        "Calculated204Pb/238UError",
        "Calculated206Pb/204Pb",
        "Calculated206Pb/204PbError",
        "Calculated206Pb/207Pb",
        "Calculated206Pb/207PbError",
        "Calculated206Pb/238U",
        "Calculated206Pb/238UError",
        "Calculated207Pb/204Pb",
        "Calculated207Pb/204PbError",
        "Calculated207Pb/206Pb",
        "Calculated207Pb/206PbError",
        "Calculated207Pb/235U",
        "Calculated207Pb/235UError",
        "Calculated208Pb/204Pb",
        "Calculated208Pb/204PbError",
        "Calculated208Pb/232Th",
        "Calculated208Pb/232ThError",
        "Calculated232Th/208Pb",
        "Calculated232Th/208PbError",
        "Calculated232Th/238U",
        "Calculated232Th/238UError",
        "Calculated235U/207Pb",
        "Calculated235U/207PbError",
        "Calculated238U/204Pb",
        "Calculated238U/204PbError",
        "Calculated238U/206Pb",
        "Calculated238U/206PbError",
        "Calculated238U/232Th",
        "Calculated238U/232ThError",

        "Calculated206Pb/238UAge",
        "Calculated206Pb/238UAgeError",
        "Calculated207Pb/206PbAge",
        "Calculated207Pb/206PbAgeError",
        "Calculated207Pb/235UAge",
        "Calculated207Pb/235UAgeError",
        "Calculated208Pb/232ThAge",
        "Calculated208Pb/232ThAgeError",
        "CalculatedBestAge",
        "CalculatedBestAgeError",
        "CalculatedBestAgeFilled",
        "CalculatedBestAgeErrorFilled",

        "ErrorCorr/Rho_68v76",
        "ErrorCorr/Rho_68v75",

        "CalculatedConcordance_206Pb/238Uv207Pb/206Pb",
        "CalculatedConcordance_206Pb/238Uv207Pb/235U",
        "MinimumSegmentedDiscordance",
        "Rejected",
        "CalculatedSpotSize",

        "UPbAnalysisCreated",
        "UPbAnalysisModified"],
        'description': 'U-Pb analyses, linked to spots'},
    'UPbAnalysisContexts': {'attributes': [
        "UPbAnalysisContextName", "UPbAnalysisContextDescription",
        "UPbAnalysisContextCreated", "UPbAnalysisContextModified"], 'description': 'Open-ended tag for additional context'},
    'UPbAnalysisMethods': {'attributes': [
        "UPbAnalysisMethodName", "UPbAnalysisMethodDescription",
        "UPbAnalysisMethodCreated", "UPbAnalysisMethodModified"], 'description': 'Analytical methods for U-Pb analyses'},
    'Units': {'attributes': [
        "UnitName", "UnitDescription",
        "UnitCreated", "UnitModified"], 'description': 'Geologic units for samples'},
}
"""List of all columns visible to the user with descriptions.
Used in ExporterWidget.py as valid columns able to be exported
Used in Filters.py as valid columns to be filtered"""


# dictionary of Views and their associated settings_value for columns to display throughout GeoCORK

# Dictionary of tables with unit/format IDs and columns that connect with that unit/format
unit_format_affected = {
    'SampleAges': {'DirectAgeUnitID': ['DirectAge', 'OldestDirectAge', 'YoungestDirectAge', 'DirectAgeError'],
                   'DirectAgeErrorFormatID': ['DirectAgeError']},
    'UPbAnalyses': {'AgeUnitID': ['207Pb/206PbAge', '206Pb/238UAge', '207Pb/235UAge', '208Pb/232ThAge', 'BestAge',
                                  '207Pb/206PbAgeError', '206Pb/238UAgeError', '207Pb/235UAgeError', '208Pb/232ThAge',
                                  'BestAgeError'],
                    'AgeErrorFormatID': ['207Pb/206PbAgeError', '206Pb/238UAgeError', '207Pb/235UAgeError', '208Pb/232ThAge',
                                  'BestAgeError'],
                    'SpotSizeUnitID': ['SpotSize'], 'ConcordanceFormatID': ['Concordance_206Pb/238Uv207Pb/206Pb',
                                'Concordance_206Pb/238Uv207Pb/235U'],
                    'RatioErrorFormatID': ['206Pb/204PbError', '204Pb/206PbError', '207Pb/204PbError',
                                           '204Pb/207PbError', '208Pb/204PbError', '204Pb/208PbError',
                                           '206Pb/207PbError', '207Pb/206PbError', '204Pb/238UError', '238U/204PbError',
                                           '206Pb/238UError', '238U/206PbError', '207Pb/235UError', '235U/207PbError',
                                           '208Pb/232ThError', '232Th/208PbError', '238U/232ThError', '232Th/238UError',]},
    'GPSLocations': {'GPSElevUnitID': ['GPSElev', 'GPSElevError'], 'GPSFormatID': ['GPSLocationDisplay']},
    'Samples': {'HeightDepthUnitID': ['HeightDepth', 'HeightDepthError']},
    'Columns': {'ColumnTotalHeightDepthUnitID': ['ColumnTotalHeightDepth']}
}
elevation_unit_affected = [['GPSLocations', 'GPSElevUnitID', 'GPSElev', 'GPSElevError']]
gps_unit_affected = [['GPSLocations', 'GPSFormatID', 'GPSLocationDisplay']]
heightdepth_unit_affected = [['Samples', 'HeightDepthUnitID', 'HeightDepth', 'HeightDepthError'],
                             ['Columns', 'ColumnTotalHeightDepthUnitID', 'ColumnTotalHeightDepth']]
spotsize_unit_affected = [['UPbAnalyses', 'SpotSizeUnitID', 'UPbSpotSize'],
                          ['GeoChemicalAnalyses', 'SpotSizeUnitID', 'GeoChemSpotSize']]
concordance_format_affected = [['UPbAnalyses', 'ConcordanceFormatID', 'Concordance_206Pb/238Uv207Pb/206Pb',
                                'Concordance_206Pb/238Uv207Pb/235U']]