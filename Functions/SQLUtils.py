from ui.Settings import return_abbreviations

# Query columns with text dependent on settings
abbreviations = return_abbreviations()
selected_age_unit = abbreviations['age_unit']
selected_elev_unit = abbreviations['elevation_unit']
selected_heightdepth_unit = abbreviations['heightdepth_unit']
selected_spotsize_unit = abbreviations['spotsize_unit']

# ID columns
qsample_id = 'Samples.SampleID'
qaliquot_id = 'Aliquots.AliquotID'
qspot_id = 'Spots.SpotID'

# Sample view columns
qsample_name = 'Samples.SampleName'
qigsn = 'Samples.SampleIGSN AS "IGSN"'
qgps = f'''SampleGPS.GPSLocationConverted AS "GPS Coordinates"'''
qsample_elev = f'SampleGPS.CalculatedGPSElev || "±" || SampleGPS.CalculatedGPSElevError AS "Elevation ({selected_elev_unit})"'
qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) AS "Measured Column Name"'
qcolumn_data = f'HeightDepth || "±" || HeightDepthError AS "Column Data ({selected_heightdepth_unit})"'
qcolumn_gps = f'''ColumnGPS.GPSLocationConverted AS "Column base GPS"'''
qsample_age = f'SampleAges.SampleAgeDisplay AS "Age ({selected_age_unit})"'
qage_range = f'COALESCE(CalculatedOldestDirectAge, " ") || "-" || COALESCE(CalculatedYoungestDirectAge, " ") AS "Age Range ({selected_age_unit})"'
qsample_age_constraint = 'GROUP_CONCAT(DISTINCT AgeConstraintName) AS "Age Constraints"'
qsample_age_interpretation = 'GROUP_CONCAT(DISTINCT AgeInterpretationName) AS "Age Interpretations"'
qsample_age_references = 'GROUP_CONCAT(DISTINCT AgeReferences.ReferenceDisplay) AS "Age References"'
qsample_description = 'Samples.SampleDescription AS "Description"'
qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) AS "Age Signatures"'
qregions = 'GROUP_CONCAT(DISTINCT RegionName) AS "Regions"'
qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) AS "Rock Types"'
qsample_context = 'GROUP_CONCAT(DISTINCT SampleContextName) AS "Sample Contexts"'
qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) AS "Sampling Method"'
qsettings = 'GROUP_CONCAT(DISTINCT SettingName) AS "Settings"'
qunits = 'GROUP_CONCAT(DISTINCT UnitName) AS "Units"'
qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName) AS "Aliquots"'
qaliquot_contexts = 'GROUP_CONCAT(DISTINCT AliquotContextName) AS "Aliquot Contexts"'
qspots = 'GROUP_CONCAT(DISTINCT SpotName) AS "Spots"'
qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) AS "Spot Compositions"'
qspot_contexts = 'GROUP_CONCAT(DISTINCT SpotContextName) AS "Spot Contexts"'
qreferences = 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay) AS "UPb References"'
qlab_facilities = 'GROUP_CONCAT(DISTINCT LabFacilityName) AS "Lab Facilities"'
qinstruments = 'GROUP_CONCAT(DISTINCT InstrumentName) AS "Instruments"'
qupb_analysis_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) AS "UPb Analysis Methods"'
qupb_ratio_error_types = 'GROUP_CONCAT(DISTINCT RatioErrorTypes.ErrorTypeAbbreviation) AS "UPb Ratio Error Types"'
qupb_age_error_types = 'GROUP_CONCAT(DISTINCT AgeErrorTypes.ErrorTypeAbbreviation) AS "UPb Age Error Types"'
qupb_age_units = 'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation) AS "UPb Age Units"'
qupb_age_interpretations = 'GROUP_CONCAT(DISTINCT UPbAgeInterpretations.AgeInterpretationName) AS "UPb Age Interpretations"'
qconcordance_types = 'GROUP_CONCAT(DISTINCT ConcordanceTypes.ConcordanceTypeAbbreviation) AS "Concordance Types"'
qspot_sizes = f'GROUP_CONCAT(DISTINCT SpotSize) AS "Spot Sizes ({selected_spotsize_unit})"'
qupb_rejection_reasons = 'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName) AS "UPb Rejection Reasons"'

# Samples, include null values
qigsn_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleIGSN,"Null")) AS "Sample IGSNs"'
qgps_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPSLocationID,"Null")) AS "GPS Location IDs"'
qcolumn_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleColumnID,"Null")) AS "Column IDs"'
qcolumn_name_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(Columns.ColumnName,"Null")) AS "Column Names"'
qcolumn_gps_converted_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLocationConverted,"Null")) AS "Column GPS"'
qheight_depth_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepth,"Null")) AS "HeightDepths"'
qheight_depth_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthError,"Null")) AS "HeightDepth Errors"'
qheight_depth_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthUnitID,"Null")) AS "HeightDepth Units"'
qheight_depth_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnHeightDepthUnits.DistanceUnitName,"Null")) AS "HeightDepth Units"'
qsample_description_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleDescription,"Null")) AS "Descriptions"'
qsample_reference_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ReferenceDisplay,"Null")) AS "References"'
qsample_gps_converted_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLocationConverted,"Null")) AS "Sample GPS"'
qlat_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatDeg, "Null")) AS "Latitude Degrees"'
qlat_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatMin, "Null")) AS "Latitude Minutes"'
qlat_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatSec, "Null")) AS "Latitude Seconds"'
qlat_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatDirectionID, "Null")) AS "Latitude Direction IDs"'
qlat_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleLatDirections.DirectionUnitName, "Null")) AS "Latitude Directions"'
qlon_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonDeg, "Null")) AS "Longitude Degrees"'
qlon_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonMin, "Null")) AS "Longitude Minutes"'
qlon_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonSec, "Null")) AS "Longitude Seconds"'
qlon_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonDirectionID, "Null")) AS "Longitude Direction IDs"'
qlon_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleLonDirections.DirectionUnitName, "Null")) AS "Longitude Directions"'
qutm_zone_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTMZone, "Null")) AS "UTM Zones"'
qutm_northing_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTMN, "Null")) AS "UTM Northings"'
qutm_easting_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTME, "Null")) AS "UTM Eastings"'
qgps_format_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSFormatID, "Null")) AS "GPS Format IDs"'
qgps_format_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPSFormats.GPSFormatAbbreviation, "Null")) AS "GPS Formats"'
qgps_elev_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElev, "Null")) AS "Elevations"'
qgps_elev_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElevError, "Null")) AS "Elevation Errors"'
qgps_elev_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElevUnitID, "Null")) AS "Elevation Unit IDs"'
qgps_elev_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleElevationUnits.DistanceUnitAbbreviation, "Null")) AS "Elevation Units"'
qsample_default_age_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(DefaultSampleAgeID,"Null")) AS "Default Age IDs"'
qsample_direct_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAge,"Null")) AS "Direct Ages"'
qsample_direct_age_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeError,"Null")) AS "Direct Age Errors"'
qsample_direct_age_error_type_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeErrorTypeID,"Null")) AS "Direct Age Error Type IDs"'
qsample_direct_age_error_type_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(DirectAgeErrorTypes.ErrorTypeAbbreviation,"Null")) AS "Direct Age Error Types"'
qsample_oldest_direct_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.OldestDirectAge,"Null")) AS "Oldest Direct Ages"'
qsample_youngest_direct_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.YoungestDirectAge,"Null")) AS "Youngest Direct Ages"'
qsample_direct_age_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeUnitID,"Null")) AS "Direct Age Unit IDs"'
qsample_direct_age_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeUnits.AgeUnitAbbreviation,"Null")) AS "Direct Age Units"'
qsample_oldest_age_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.OldestAgeID,"Null")) AS "Oldest Age IDs"'
qsample_oldest_rel_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(OldAge.AgeName,"Null")) AS "Oldest Relative Ages"'
qsample_youngest_age_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.YoungestAgeID,"Null")) AS "Youngest Age IDs"'
qsample_youngest_rel_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(YoungAge.AgeName,"Null")) AS "Youngest Relative Ages"'
qsample_age_description_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.SampleAgeDescription,"Null")) AS "Age Descriptions"'
qsample_age_constraint_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges_AgeConstraints.AgeConstraintID,"Null")) AS "Age Constraint IDs"'
qsample_age_constraint_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeConstraints.AgeConstraintName,"Null")) AS "Age Constraints"'
qsample_age_interpretation_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges_AgeInterpretations.AgeInterpretationID,"Null")) AS "Age Interpretation IDs"'
qsample_age_interpretation_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeInterpretations.AgeInterpretationName,"Null")) AS "Age Interpretations"'
qsample_age_reference_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeReferences.ReferenceID,"Null")) AS "Age Reference IDs"'
qsample_age_reference_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeReferences.ReferenceDisplay,"Null")) AS "Age References"'
qaliquots_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AliquotName,"Null")) AS "Aliquots"'
qspots_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SpotName,"Null")) AS "Spots"'
qreferences_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(UPbReferences.ReferenceDisplay,"Null")) AS "References"'
qsample_context_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleContextName,"Null")) AS "Sample Contexts"'
qsampling_methods_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SamplingMethodName,"Null")) AS "Sampling Method"'
qrock_types_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(RockTypeName,"Null")) AS "Rock Types"'
qregions_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(RegionName,"Null")) AS "Regions"'
qsettings_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SettingName,"Null")) AS "Settings"'
qunits_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(UnitName,"Null")) AS "Units"'
qupb_methods_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(UPbAnalysisMethodName,"Null")) AS "UPb Analysis Methods"'
qlabs_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(LabFacilityName,"Null")) AS "Lab Facilities"'
qspot_context_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SpotContextName,"Null")) AS "Spot Contexts"'
qspot_compositions_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SpotCompositionName,"Null")) AS "Spot Compositions"'
qaliquot_context_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AliquotContextName,"Null")) AS "Aliquot Contexts"'

# Aliquot view columns
qsample_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(Samples.SampleID,"Null")) AS "Sample IDs"'

# Join lines
# SampleAge-Age joins
sample_age_join = 'LEFT JOIN Ages ON SampleAges.OldestAgeID=Ages.AgeID OR SampleAges.YoungestAgeID=Ages.AgeID'
sample_age_left_joins = '''LEFT JOIN ErrorTypes AS DirectAgeErrorTypes ON DirectAgeErrorTypes.ErrorTypeID=SampleAges.DirectAgeErrorTypeID
                        LEFT JOIN AgeUnits ON AgeUnits.AgeUnitID=SampleAges.DirectAgeUnitID
                        LEFT JOIN Ages AS OldAge ON SampleAges.OldestAgeID=OldAge.AgeID
                        LEFT JOIN Ages AS YoungAge ON SampleAges.YoungestAgeID=YoungAge.AgeID
                        LEFT JOIN SampleAges_AgeConstraints ON SampleAges.SampleAgeID=SampleAges_AgeConstraints.SampleAgeID
                        LEFT JOIN AgeConstraints ON AgeConstraints.AgeConstraintID=SampleAges_AgeConstraints.AgeConstraintID
                        LEFT JOIN SampleAges_AgeInterpretations ON SampleAges.SampleAgeID=SampleAges_AgeInterpretations.SampleAgeID
                        LEFT JOIN AgeInterpretations ON AgeInterpretations.AgeInterpretationID=SampleAges_AgeInterpretations.AgeInterpretationID
                        LEFT JOIN SampleAges_References ON SampleAges.SampleAgeID=SampleAges_References.SampleAgeID
                        LEFT JOIN "References" AS AgeReferences ON AgeReferences.ReferenceID=SampleAges_References.ReferenceID'''

# GPSLocation joins
gps_sample_join = '''LEFT JOIN GPSLocations AS SampleGPS ON Samples.SampleGPSLocationID=SampleGPS.GPSLocationID'''
gps_sample_left_joins = '''LEFT JOIN DirectionUnits AS SampleLatDirections ON SampleLatDirections.DirectionUnitID=SampleGPS.GPSLatDirectionID
                        LEFT JOIN DirectionUnits AS SampleLonDirections ON SampleLonDirections.DirectionUnitID=SampleGPS.GPSLonDirectionID
                        LEFT JOIN DistanceUnits AS SampleElevationUnits ON SampleElevationUnits.DistanceUnitID=SampleGPS.GPSElevUnitID
                        LEFT JOIN GPSFormats AS SampleGPSFormats ON SampleGPSFormats.GPSFormatID=SampleGPS.GPSFormatID'''
gps_column_join = '''LEFT JOIN GPSLocations AS ColumnGPS ON Columns.ColumnBaseGPSID=ColumnGPS.GPSLocationID'''
gps_columns_left_joins = '''LEFT JOIN DirectionUnits AS ColumnLatDirections ON ColumnLatDirections.DirectionUnitID=ColumnGPS.GPSLatDirectionID
                        LEFT JOIN DirectionUnits AS ColumnLonDirections ON ColumnLonDirections.DirectionUnitID=ColumnGPS.GPSLonDirectionID
                        LEFT JOIN DistanceUnits AS ColumnElevationUnits ON ColumnElevationUnits.DistanceUnitID=ColumnGPS.GPSElevUnitID
                        LEFT JOIN GPSFormats AS ColumnGPSFormats ON ColumnGPSFormats.GPSFormatID=ColumnGPS.GPSFormatID'''

# SampleJoins
age_signature_join = '''LEFT JOIN Samples_AgeSignatures ON Samples.SampleID=Samples_AgeSignatures.SampleID
                                    LEFT JOIN AgeSignatures ON AgeSignatures.AgeSignatureID=Samples_AgeSignatures.AgeSignatureID'''
column_join = 'LEFT JOIN Columns ON Samples.SampleColumnID=Columns.ColumnID'
column_unit_join = '''LEFT JOIN DistanceUnits AS ColumnHeightDepthUnits ON ColumnHeightDepthUnits.DistanceUnitID=Samples.HeightDepthUnitID'''
region_join = '''LEFT JOIN Samples_Regions ON Samples.SampleID=Samples_Regions.SampleID
                                LEFT JOIN Regions ON Regions.RegionID=Samples_Regions.RegionID'''
rock_type_join = '''LEFT JOIN Samples_RockTypes ON Samples.SampleID=Samples_RockTypes.SampleID
                                LEFT JOIN RockTypes ON RockTypes.RockTypeID=Samples_RockTypes.RockTypeID'''
sample_context_join = '''LEFT JOIN Samples_SampleContexts ON Samples.SampleID=Samples_SampleContexts.SampleID
                                LEFT JOIN SampleContexts ON SampleContexts.SampleContextID=Samples_SampleContexts.SampleContextID'''
sample_sampleage_join = '''LEFT JOIN Samples_SampleAges ON Samples.DefaultSampleAgeID=Samples_SampleAges.SampleAgeID
                                    LEFT JOIN SampleAges ON SampleAges.SampleAgeID=Samples_SampleAges.SampleAgeID'''
default_sample_age_join = '''LEFT JOIN SampleAges as DefaultSampleAges ON SampleAges.SampleAgeID=Samples.DefaultSampleAgeID'''
sampling_method_join = '''LEFT JOIN Samples_SamplingMethods ON Samples.SampleID=Samples_SamplingMethods.SampleID
                                LEFT JOIN SamplingMethods ON SamplingMethods.SamplingMethodID=Samples_SamplingMethods.SamplingMethodID'''
setting_join = '''LEFT JOIN Samples_Settings ON Samples.SampleID=Samples_Settings.SampleID
                                LEFT JOIN Settings ON Settings.SettingID=Samples_Settings.SettingID'''
unit_join = '''LEFT JOIN Samples_Units ON Samples.SampleID=Samples_Units.SampleID
                                LEFT JOIN Units ON Units.UnitID=Samples_Units.UnitID'''
aliquot_join = 'LEFT JOIN Aliquots ON Aliquots.SampleID=Samples.SampleID'

# AliquotJoins
aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts ON Aliquots.AliquotID=Aliquots_AliquotContexts.AliquotID
                                LEFT JOIN AliquotContexts ON AliquotContexts.AliquotContextID=Aliquots_AliquotContexts.AliquotContextID'''

# Aliquot-spot Join
spot_join = 'LEFT JOIN Spots ON Spots.AliquotID=Aliquots.AliquotID'

# SpotJoins
spot_composition_join = '''LEFT JOIN SpotCompositions ON SpotCompositions.SpotCompositionID=Spots.SpotCompositionID'''
spot_context_join = '''LEFT JOIN Spots_SpotContexts ON Spots.SpotID=Spots_SpotContexts.SpotID
                                LEFT JOIN SpotContexts ON SpotContexts.SpotContextID=Spots_SpotContexts.SpotContextID'''
upb_analysis_join = 'LEFT JOIN UPbAnalyses ON UPbAnalyses.SpotID=Spots.SpotID'

# UPbJoins
upb_reference_join = 'LEFT JOIN "References" AS UPbReferences ON UPbReferences.ReferenceID=UPbAnalyses.ReferenceID'
upb_labs_join = 'LEFT JOIN LabFacilities ON LabFacilities.LabFacilityID=UPbAnalyses.LabFacilityID'
upb_instruments_join = 'LEFT JOIN Instruments ON Instruments.InstrumentID=UPbAnalyses.InstrumentID'
upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalysisMethods.UPbAnalysisMethodID=UPbAnalyses.UPbAnalysisMethodID'
upb_ratio_error_type_join = 'LEFT JOIN ErrorTypes AS RatioErrorTypes ON RatioErrorTypes.ErrorTypeID=UPbAnalyses.RatioErrorTypeID'
upb_age_error_type_join = 'LEFT JOIN ErrorTypes AS AgeErrorTypes ON AgeErrorTypes.ErrorTypeID=UPbAnalyses.AgeErrorTypeID'
upb_age_unit_join = 'LEFT JOIN AgeUnits AS UPbAgeUnits ON UPbAgeUnits.AgeUnitID=UPbAnalyses.AgeUnitID'
upb_age_interpretation_join = 'LEFT JOIN AgeInterpretations AS UPbAgeInterpretations ON AgeInterpretations.AgeInterpretationID=UPbAnalyses.AgeInterpretationID'
upb_concordance_type_join = 'LEFT JOIN ConcordanceTypes ON ConcordanceTypes.ConcordanceTypeID=UPbAnalyses.ConcordanceTypeID'
upb_spot_size_unit_join = 'LEFT JOIN DistanceUnits AS SpotSizeUnits ON SpotSizeUnits.DistanceUnitID=UPbAnalyses.SpotSizeUnitID'
upb_rejection_reason_join = '''LEFT JOIN UPbAnalyses_RejectionReasons ON UPbAnalyses.UPbAnalysisID=UPbAnalyses_RejectionReasons.UPbAnalysisID
                                    LEFT JOIN RejectionReasons AS UPbRejectionReasons ON UPbRejectionReasons.RejectionReasonID=UPbAnalyses_RejectionReasons.RejectionReasonID'''

# Information for settings

sample_view_columns = [qsample_id, qigsn, qsample_name, qgps, qsample_elev, qcolumn_gps, qcolumn_data, qsample_age,
                       qage_range, qsample_age_constraint, qsample_age_interpretation,
                       qsample_age_references, qsample_description, qage_signature, qregions, qrock_types,
                       qsample_context, qsampling_methods, qsettings, qunits, qaliquots, qaliquot_contexts,
                       qspots, qspot_compositions, qspot_contexts, qreferences, qlab_facilities, qinstruments,
                       qupb_analysis_methods, qupb_ratio_error_types, qupb_age_error_types, qupb_age_units,
                       qupb_age_interpretations, qconcordance_types, qspot_sizes, qupb_rejection_reasons]

# Many-to-many tables related to table at the beginning of each list, populate multiple selection dropdowns
many_editable = [['Samples', 'AgeSignatures', 'Regions', 'RockTypes', 'SampleContexts', 'SamplingMethods', 'Settings', 'Units'],
             ['Aliquots', 'AliquotContexts'], ['Spots', 'SpotCompositions', 'SpotContexts'], ['UPbAnalyses', 'RejectionReasons']]
# One-to-many columns related to table at the beginning of each list, populate single selection dropdowns
one_editable = [['Samples', 'SampleAges', 'Columns', 'DistanceUnits'],
            ['Columns', 'DistanceUnits'], ['Aliquots', 'Samples'], ['Spots', 'Aliquots', 'SpotCompositions'],
            ['UPbAnalyses', 'Spots', 'References', 'LabFacilities', 'Instruments', 'UPbAnalysisMethods', 'ErrorTypes', 'AgeUnits', 'AgeInterpretations', 'ConcordanceTypes', 'DistanceUnits']]



user_viewable_tables = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts',
                        'Columns', 'Instruments', 'LabFacilities',
                        'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts', 'Samples',
                        'SamplingMethods', 'Settings', '"References"',
                        'SpotCompositions', 'SpotContexts', 'UPbAnalysisMethods', 'Units']
user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts',
                       'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts',
                       'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContexts', 'UPbAnalysisMethods',
                       'Units']
conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Spots', 'UPbAnalyses']
conditionally_editable_trees = ['Aliquots']

trigger_tables = ['Columns', 'GPSLocations', 'SampleAges', 'Samples', 'UPbAnalyses']

views = ['SampleView', 'AliquotView', 'SpotView', 'UPbView']