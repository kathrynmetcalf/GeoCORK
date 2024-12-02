selected_age_unit = 'Ma'
selected_elev_unit = 'm'
selected_heightdepth_unit = 'm'
spot_size_unit = 'um'
ratio_error_type = '1σ %'
age_error_type = '1σ abs'

# ID columns
qsample_id = 'Samples.SampleID'
qaliquot_id = 'Aliquots.AliquotID'
qspot_id = 'Spots.SpotID'

# View columns
qsample_name = 'SampleName AS "Sample Name"'
qage = f'CalculatedDirectAge || "±" || COALESCE(CalculatedDirectAgeError, " ") AS "Age {selected_age_unit}"'
qage_range = f'COALESCE(CalculatedOldestDirectAge, " ") || "-" || COALESCE(CalculatedYoungestDirectAge, " ") AS "Age Range {selected_age_unit}"'
qgeo_age = 'COALESCE(OldAge.AgeName, " ") || "-" || COALESCE(YoungAge.AgeName, " ") AS "Geologic Age"'
qage_signature_distinct = 'GROUP_CONCAT(DISTINCT AgeSignatureName) AS "Age Signatures"'
qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) AS "Measured Column Name"'
qcolumn_data = f'HeightDepth || "±" || HeightDepthError AS "Column Data ({selected_heightdepth_unit})"'
qcolumn_gps = f'''ColumnGPS.CalculatedBaseGPS AS "GPS Coordinates"'''
qgps = f'''SampleGPS.CalculatedGPSCoordinates AS "GPS Coordinates"'''
qelev = f'SampleGPS.CalculatedGPSElev || "±" || SampleGPS.CalculatedGPSElevError AS "Elevation ({selected_elev_unit})"'
qaliquots_distinct = 'GROUP_CONCAT(DISTINCT AliquotName) AS "Aliquots"'
qspots_distinct = 'GROUP_CONCAT(DISTINCT SpotName) AS "Spots"'
qsources_distinct = 'GROUP_CONCAT(DISTINCT ShortCitation) AS "Sources"'
qsample_context_distinct = 'GROUP_CONCAT(DISTINCT SampleContextName) AS "Sample Contexts"'
qsampling_methods_distinct = 'GROUP_CONCAT(DISTINCT SamplingMethodName) AS "Sampling Method"'
qrock_types_distinct = 'GROUP_CONCAT(DISTINCT RockTypeName) AS "Rock Types"'
qregions_distinct = 'GROUP_CONCAT(DISTINCT RegionName) AS "Regions"'
qsettings_distinct = 'GROUP_CONCAT(DISTINCT SettingName) AS "Settings"'
qunits_distinct = 'GROUP_CONCAT(DISTINCT UnitName) AS "Units"'
qupb_methods_distinct = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) AS "UPb Analysis Methods"'
qlabs_distinct = 'GROUP_CONCAT(DISTINCT LabFacilityName) AS "Lab Facilities"'
qspot_context_distinct = 'GROUP_CONCAT(DISTINCT SpotContextName) AS "Spot Contexts"'
qspot_compositions_distinct = 'GROUP_CONCAT(DISTINCT SpotCompositionName) AS "Spot Compositions"'
qaliquot_context_distinct = 'GROUP_CONCAT(DISTINCT AliquotContextName) AS "Aliquot Contexts"'

# Sample information columns
qsample_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(Samples.SampleID,"Null")) AS "Sample IDs"'
qigsn_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleIGSN,"Null")) AS "Sample IGSNs"'
qgps_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPSLocationID,"Null")) AS "GPS Location IDs"'
qcolumn_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleColumnID,"Null")) AS "Column IDs"'
qcolumn_name_distinct = 'GROUP_CONCAT(DISTINCT ifnull(Columns.ColumnName,"Null")) AS "Column Names"'
qheight_depth_distinct = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepth,"Null")) AS "HeightDepths"'
qheight_depth_error_distinct = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthError,"Null")) AS "HeightDepth Errors"'
qheight_depth_unit_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthUnitID,"Null")) AS "HeightDepth Units"'
qheight_depth_unit_distinct = 'GROUP_CONCAT(DISTINCT ifnull(ColumnHeightDepthUnits.DistanceUnitName,"Null")) AS "HeightDepth Units"'
qsample_description_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleDescription,"Null")) AS "Descriptions"'
qlat_deg_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatDeg, "Null")) AS "Latitude Degrees"'
qlat_min_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatMin, "Null")) AS "Latitude Minutes"'
qlat_sec_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatSec, "Null")) AS "Latitude Seconds"'
qlat_dir_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatDirectionID, "Null")) AS "Latitude Direction IDs"'
qlat_dir_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleLatDirections.DirectionUnitName, "Null")) AS "Latitude Directions"'
qlon_deg_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonDeg, "Null")) AS "Longitude Degrees"'
qlon_min_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonMin, "Null")) AS "Longitude Minutes"'
qlon_sec_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonSec, "Null")) AS "Longitude Seconds"'
qlon_dir_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonDirectionID, "Null")) AS "Longitude Direction IDs"'
qlon_dir_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleLonDirections.DirectionUnitName, "Null")) AS "Longitude Directions"'
qutm_zone_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTMZone, "Null")) AS "UTM Zones"'
qutm_northing_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTMN, "Null")) AS "UTM Northings"'
qutm_easting_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTME, "Null")) AS "UTM Eastings"'
qgps_format_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSFormatID, "Null")) AS "GPS Format IDs"'
qgps_format_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPSFormats.GPSFormatAbbreviation, "Null")) AS "GPS Formats"'
qgps_elev_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElev, "Null")) AS "Elevations"'
qgps_elev_error_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElevError, "Null")) AS "Elevation Errors"'
qgps_elev_unit_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElevUnitID, "Null")) AS "Elevation Unit IDs"'
qgps_elev_unit_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleElevationUnits.DistanceUnitAbbreviation, "Null")) AS "Elevation Units"'
qsample_default_age_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(DefaultSampleAgeID,"Null")) AS "Default Age IDs"'
qsample_direct_age_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAge,"Null")) AS "Direct Ages"'
qsample_direct_age_error_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeError,"Null")) AS "Direct Age Errors"'
qsample_direct_age_error_type_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeErrorTypeID,"Null")) AS "Direct Age Error Type IDs"'
qsample_direct_age_error_type_distinct = 'GROUP_CONCAT(DISTINCT ifnull(DirectAgeErrorTypes.ErrorTypeAbbreviation,"Null")) AS "Direct Age Error Types"'
qsample_oldest_direct_age_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.OldestDirectAge,"Null")) AS "Oldest Direct Ages"'
qsample_youngest_direct_age_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.YoungestDirectAge,"Null")) AS "Youngest Direct Ages"'
qsample_direct_age_unit_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeUnitID,"Null")) AS "Direct Age Unit IDs"'
qsample_direct_age_unit_distinct = 'GROUP_CONCAT(DISTINCT ifnull(AgeUnits.AgeUnitAbbreviation,"Null")) AS "Direct Age Units"'
qsample_oldest_age_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.OldestAgeID,"Null")) AS "Oldest Age IDs"'
qsample_oldest_rel_age_distinct = 'GROUP_CONCAT(DISTINCT ifnull(OldAge.AgeName,"Null")) AS "Oldest Relative Ages"'
qsample_youngest_age_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.YoungestAgeID,"Null")) AS "Youngest Age IDs"'
qsample_youngest_rel_age_distinct = 'GROUP_CONCAT(DISTINCT ifnull(YoungAge.AgeName,"Null")) AS "Youngest Relative Ages"'
qsample_age_description_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.SampleAgeDescription,"Null")) AS "Age Descriptions"'
qsample_age_constraint_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges_AgeConstraints.AgeConstraintID,"Null")) AS "Age Constraint IDs"'
qsample_age_constraint_distinct = 'GROUP_CONCAT(DISTINCT ifnull(AgeConstraints.AgeConstraintName,"Null")) AS "Age Constraints"'
qsample_age_interpretation_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges_AgeInterpretations.AgeInterpretationID,"Null")) AS "Age Interpretation IDs"'
qsample_age_interpretation_distinct = 'GROUP_CONCAT(DISTINCT ifnull(AgeInterpretations.AgeInterpretationName,"Null")) AS "Age Interpretations"'
qsample_age_source_id_distinct = 'GROUP_CONCAT(DISTINCT ifnull(AgeSources.SourceID,"Null")) AS "Age Source IDs"'
qsample_age_source_distinct = 'GROUP_CONCAT(DISTINCT ifnull(AgeSources.ShortCitation,"Null")) AS "Age Sources"'

# Join lines
# SampleAge-Age joins
sample_age_join = 'LEFT JOIN Ages ON SampleAges.OldestAgeID=Ages.AgeID OR SampleAges.YoungestAgeID=Ages.AgeID'
sample_age_error_type_join = 'LEFT JOIN ErrorTypes AS DirectAgeErrorTypes ON DirectAgeErrorTypes.ErrorTypeID=SampleAges.DirectAgeErrorTypeID'
sample_age_unit_join = 'LEFT JOIN AgeUnits ON AgeUnits.AgeUnitID=SampleAges.DirectAgeUnitID'
sample_old_age_join = 'LEFT JOIN Ages AS OldAge ON SampleAges.OldestAgeID=OldAge.AgeID'
sample_young_age_join = 'LEFT JOIN Ages AS YoungAge ON SampleAges.YoungestAgeID=YoungAge.AgeID'
sampleage_ageconstraint_join = '''LEFT JOIN SampleAges_AgeConstraints ON SampleAges.SampleAgeID=SampleAges_AgeConstraints.SampleAgeID
                                LEFT JOIN AgeConstraints ON AgeConstraints.AgeConstraintID=SampleAges_AgeConstraints.AgeConstraintID'''
sampleage_ageinterpretation_join = '''LEFT JOIN SampleAges_AgeInterpretations ON SampleAges.SampleAgeID=SampleAges_AgeInterpretations.SampleAgeID
                                LEFT JOIN AgeInterpretations ON AgeInterpretations.AgeInterpretationID=SampleAges_AgeInterpretations.AgeInterpretationID'''
sampleage_source_join = '''LEFT JOIN SampleAges_Sources ON SampleAges.SampleAgeID=SampleAges_Sources.SampleAgeID
                            LEFT JOIN Sources AS AgeSources ON AgeSources.SourceID=SampleAges_Sources.SourceID'''

# GPSLocation joins
gps_sample_join = '''LEFT JOIN GPSLocations AS SampleGPS ON Samples.SampleGPSLocationID=SampleGPS.GPSLocationID
                        LEFT JOIN DirectionUnits AS SampleLatDirections ON SampleLatDirections.DirectionUnitID=SampleGPS.GPSLatDirectionID
                        LEFT JOIN DirectionUnits AS SampleLonDirections ON SampleLonDirections.DirectionUnitID=SampleGPS.GPSLonDirectionID
                        LEFT JOIN DistanceUnits AS SampleElevationUnits ON SampleElevationUnits.DistanceUnitID=SampleGPS.GPSElevUnitID
                        LEFT JOIN GPSFormats AS SampleGPSFormats ON SampleGPSFormats.GPSFormatID=SampleGPS.GPSFormatID'''
gps_column_join = '''LEFT JOIN GPSLocations AS ColumnGPS ON Columns.ColumnBaseGPSID=ColumnGPS.GPSLocationID
                        LEFT JOIN DirectionUnits AS ColumnLatDirections ON ColumnLatDirections.DirectionUnitID=ColumnGPS.GPSLatDirectionID
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
upb_source_join = 'LEFT JOIN Sources ON Sources.SourceID=UPbAnalyses.SourceID'
upb_labs_join = 'LEFT JOIN LabFacilities ON LabFacilities.LabFacilityID=UPbAnalyses.LabFacilityID'
upb_instruments_join = 'LEFT JOIN Instruments ON Instruments.InstrumentID=UPbAnalyses.InstrumentID'
upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalysisMethods.UPbAnalysisMethodID=UPbAnalyses.UPbAnalysisMethodID'
upb_ratio_error_type_join = 'LEFT JOIN ErrorTypes AS RatioErrorTypes ON RatioErrorTypes.ErrorTypeID=UPbAnalyses.RatioErrorTypeID'
upb_age_error_type_join = 'LEFT JOIN ErrorTypes AS AgeErrorTypes ON AgeErrorTypes.ErrorTypeID=UPbAnalyses.AgeErrorTypeID'
upb_age_unit_join = 'LEFT JOIN AgeUnits AS UPbAgeUnits ON UPbAgeUnits.AgeUnitID=UPbAnalyses.AgeUnitID'
upb_concordance_type_join = 'LEFT JOIN ConcordanceTypes ON ConcordanceTypes.ConcordanceTypeID=UPbAnalyses.ConcordanceTypeID'
upb_spot_size_unit_join = 'LEFT JOIN DistanceUnits AS SpotSizeUnits ON SpotSizeUnits.DistanceUnitID=UPbAnalyses.SpotSizeUnitID'
upb_rejection_reason_join = 'LEFT JOIN RejectionReasons ON UPbAnalyses.RejectionReasonID=RejectionReasons.RejectionReasonID'


user_viewable_tables = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts', 'Columns', 'Instruments', 'LabFacilities',
                        'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts', 'Samples', 'SamplingMethods', 'Settings', 'Sources',
                        'SpotCompositions', 'SpotContexts', 'UPbAnalysisMethods', 'Units']
user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts', 'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts',
                       'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContexts', 'UPbAnalysisMethods', 'Units']
conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Spots', 'UPbAnalyses']
conditionally_editable_trees = ['Aliquots']


'''
SampleLat
SampleLon
SampleUTMZone
SampleUTMN
SampleUTME
SampleElev
ColumnBaseLat
ColumnBaseLon
ColumnBaseUTMZone
ColumnBaseUTMN
ColumnBaseUTME
ColumnTotalHeightDepth

'''