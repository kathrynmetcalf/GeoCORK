from ui.Settings import return_abbreviations

# Query columns with text dependent on settings
abbreviations = return_abbreviations()
selected_age_unit = abbreviations['age_unit']
selected_elev_unit = abbreviations['elevation_unit']
selected_heightdepth_unit = abbreviations['heightdepth_unit']
selected_spotsize_unit = abbreviations['spotsize_unit']
selected_gps_format = abbreviations['gps_format']
selected_age_error_format = abbreviations['age_error_format']
selected_ratio_error_format = abbreviations['ratio_error_format']

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
qcolumn_gps = f'''ColumnGPS.GPSLocationConverted AS "Column Base GPS"'''
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
qupb_ratio_error_formats = 'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation) AS "UPb Ratio Error Formats"'
qupb_age_error_formats = 'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation) AS "UPb Age Error Formats"'
qupb_age_units = 'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation) AS "UPb Age Units"'
qupb_age_interpretations = 'GROUP_CONCAT(DISTINCT UPbAgeInterpretations.AgeInterpretationName) AS "UPb Age Interpretations"'
qconcordance_formats = 'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation) AS "Concordance Formats"'
qspot_sizes = f'GROUP_CONCAT(DISTINCT SpotSize) AS "Spot Sizes ({selected_spotsize_unit})"'
qupb_rejection_reasons = 'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName) AS "UPb Rejection Reasons"'
qsample_created = 'Samples.SampleCreated'
qsample_modified = 'Samples.SampleModified'

# Samples, include null values
qsample_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleID,"Null")) AS "Sample IDs"'
qsample_name_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleName,"Null")) AS "Sample Names"'
qigsn_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleIGSN,"Null")) AS "Sample IGSNs"'
qsample_gps_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPSLocationID,"Null")) AS "GPS Location IDs"'
qsample_column_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleColumnID,"Null")) AS "Column IDs"'
qcolumn_name_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(Columns.ColumnName,"Null")) AS "Column Names"'
qcolumn_gps_converted_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLocationConverted,"Null")) AS "Column GPS"'
qheight_depth_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepth,"Null")) AS "HeightDepths"'
qheight_depth_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthError,"Null")) AS "HeightDepth Errors"'
qheight_depth_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthUnitID,"Null")) AS "HeightDepth Units"'
qheight_depth_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnHeightDepthUnits.DistanceUnitName,"Null")) AS "HeightDepth Units"'
qsample_description_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleDescription,"Null")) AS "Descriptions"'
qsample_reference_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ReferenceDisplay,"Null")) AS "References"'
qsample_gps_converted_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLocationConverted,"Null")) AS "Sample GPS"'
qsample_lat_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatDeg, "Null")) AS "Latitude Degrees"'
qsample_lat_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatMin, "Null")) AS "Latitude Minutes"'
qsample_lat_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatSec, "Null")) AS "Latitude Seconds"'
qsample_lat_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLatDirectionID, "Null")) AS "Latitude Direction IDs"'
qsample_lat_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleLatDirections.DirectionUnitName, "Null")) AS "Latitude Directions"'
qsample_lon_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonDeg, "Null")) AS "Longitude Degrees"'
qsample_lon_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonMin, "Null")) AS "Longitude Minutes"'
qsample_lon_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonSec, "Null")) AS "Longitude Seconds"'
qsample_lon_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSLonDirectionID, "Null")) AS "Longitude Direction IDs"'
qsample_lon_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleLonDirections.DirectionUnitName, "Null")) AS "Longitude Directions"'
qsample_utm_zone_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTMZone, "Null")) AS "UTM Zones"'
qsample_utm_northing_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTMN, "Null")) AS "UTM Northings"'
qsample_utm_easting_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSUTME, "Null")) AS "UTM Eastings"'
qsample_gps_format_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSFormatID, "Null")) AS "GPS Format IDs"'
qsample_gps_format_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPSFormats.GPSFormatAbbreviation, "Null")) AS "GPS Formats"'
qsample_gps_elev_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElev, "Null")) AS "Elevations"'
qsample_gps_elev_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElevError, "Null")) AS "Elevation Errors"'
qsample_gps_elev_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPS.GPSElevUnitID, "Null")) AS "Elevation Unit IDs"'
qsample_gps_elev_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleElevationUnits.DistanceUnitAbbreviation, "Null")) AS "Elevation Units"'
qsample_default_age_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(DefaultSampleAgeID,"Null")) AS "Default Age IDs"'
qsample_direct_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAge,"Null")) AS "Direct Ages"'
qsample_direct_age_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeError,"Null")) AS "Direct Age Errors"'
qsample_direct_age_error_format_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeErrorFormatID,"Null")) AS "Direct Age Error Format IDs"'
qsample_direct_age_error_format_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(DirectAgeErrorFormats.ErrorFormatAbbreviation,"Null")) AS "Direct Age Error Formats"'
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

#Columns, skip null values
qcolumn_calc_total_height_depth = f'Columns.CalculatedColumnTotalHeightDepth AS "Total Height/Depth ({selected_heightdepth_unit})"'
qcolumn_total_height_depth = f'Columns.ColumnTotalHeightDepth AS "Total Height/Depth"'
qcolumn_total_height_depth_unit = f'ColumnUnits.DistanceUnitAbbreviation AS "Height/Depth Unit"'
qcolumn_gps_display = 'ColumnGPS.GPSLocationDisplay AS "Column Base GPS"'
qcolumn_description = 'ColumnDescription'
qcolumn_created = 'ColumnCreated'
qcolumn_modified = 'ColumnModified'

# Columns, include null values
qcolumn_id = 'Columns.ColumnID'
# already defined above
qcolumn_name = 'Columns.ColumnName'
qcolumn_total_height_depth_ifnull = f'GROUP_CONCAT( DISTINCT ifnull(Columns.CalculatedColumnTotalHeightDepth) AS "Total Height/Depth ({selected_heightdepth_unit})"'
qcolumn_gps_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.BaseGPSLocationID,"Null")) AS "Base GPS Location IDs"'
# already defined above
# qcolumn_gps_converted_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLocationConverted,"Null")) AS "Column GPS"'
qcolumn_lat_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatDeg, "Null")) AS "Latitude Degrees"'
qcolumn_lat_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatMin, "Null")) AS "Latitude Minutes"'
qcolumn_lat_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatSec, "Null")) AS "Latitude Seconds"'
qcolumn_lat_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatDirectionID, "Null")) AS "Latitude Direction IDs"'
qcolumn_lat_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnLatDirections.DirectionUnitName, "Null")) AS "Latitude Directions"'
qcolumn_lon_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonDeg, "Null")) AS "Longitude Degrees"'
qcolumn_lon_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonMin, "Null")) AS "Longitude Minutes"'
qcolumn_lon_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonSec, "Null")) AS "Longitude Seconds"'
qcolumn_lon_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonDirectionID, "Null")) AS "Longitude Direction IDs"'
qcolumn_lon_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnLonDirections.DirectionUnitName, "Null")) AS "Longitude Directions"'
qcolumn_utm_zone_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSUTMZone, "Null")) AS "UTM Zones"'
qcolumn_utm_northing_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSUTMN, "Null")) AS "UTM Northings"'
qcolumn_utm_easting_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSUTME, "Null")) AS "UTM Eastings"'
qcolumn_gps_format_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSFormatID, "Null")) AS "GPS Format IDs"'
qcolumn_gps_format_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPSFormats.GPSFormatAbbreviation, "Null")) AS "GPS Formats"'
qcolumn_gps_elev_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSElev, "Null")) AS "Elevations"'
qcolumn_gps_elev_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSElevError, "Null")) AS "Elevation Errors"'
qcolumn_gps_elev_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSElevUnitID, "Null")) AS "Elevation Unit IDs"'
qcolumn_gps_elev_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnElevationUnits.DistanceUnitAbbreviation, "Null")) AS "Elevation Units"'
qcolumn_description_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnDescription,"Null")) AS "Description"'


# Aliquot view columns
qsample_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(Samples.SampleID,"Null")) AS "Sample IDs"'

# Join lines
# SampleAge-Age joins
sample_age_join = 'LEFT JOIN Ages ON SampleAges.OldestAgeID=Ages.AgeID OR SampleAges.YoungestAgeID=Ages.AgeID'
sample_age_left_joins = '''LEFT JOIN ErrorFormats AS DirectAgeErrorFormats ON DirectAgeErrorFormats.ErrorFormatID=SampleAges.DirectAgeErrorFormatID
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
gps_column_left_joins = '''LEFT JOIN DirectionUnits AS ColumnLatDirections ON ColumnLatDirections.DirectionUnitID=ColumnGPS.GPSLatDirectionID
                        LEFT JOIN DirectionUnits AS ColumnLonDirections ON ColumnLonDirections.DirectionUnitID=ColumnGPS.GPSLonDirectionID
                        LEFT JOIN DistanceUnits AS ColumnElevationUnits ON ColumnElevationUnits.DistanceUnitID=ColumnGPS.GPSElevUnitID
                        LEFT JOIN GPSFormats AS ColumnGPSFormats ON ColumnGPSFormats.GPSFormatID=ColumnGPS.GPSFormatID'''

# ColumnJoins
column_units_join = 'LEFT JOIN DistanceUnits as ColumnUnits ON ColumnUnits.DistanceUnitID=Columns.ColumnTotalHeightDepthUnitID'

# SampleJoins
age_constraint_join = '''LEFT JOIN SampleAges_AgeConstraints ON Samples.SampleID=SampleAges_AgeConstraints.SampleAgeID
                        LEFT JOIN AgeConstraints ON AgeConstraints.AgeConstraintID=SampleAges_AgeConstraints.AgeConstraintID'''
age_interpretation_join = '''LEFT JOIN SampleAges_AgeInterpretations ON Samples.SampleID=SampleAges_AgeInterpretations.SampleAgeID
                            LEFT JOIN AgeInterpretations ON AgeInterpretations.AgeInterpretationID=SampleAges_AgeInterpretations.AgeInterpretationID'''
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
default_sample_age_join = '''LEFT JOIN SampleAges ON SampleAges.SampleAgeID=Samples.DefaultSampleAgeID'''
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
upb_ratio_error_format_join = 'LEFT JOIN ErrorFormats AS RatioErrorFormats ON RatioErrorFormats.ErrorFormatID=UPbAnalyses.RatioErrorFormatID'
upb_age_error_format_join = 'LEFT JOIN ErrorFormats AS AgeErrorFormats ON AgeErrorFormats.ErrorFormatID=UPbAnalyses.AgeErrorFormatID'
upb_age_unit_join = 'LEFT JOIN AgeUnits AS UPbAgeUnits ON UPbAgeUnits.AgeUnitID=UPbAnalyses.AgeUnitID'
upb_age_interpretation_join = 'LEFT JOIN AgeInterpretations AS UPbAgeInterpretations ON AgeInterpretations.AgeInterpretationID=UPbAnalyses.AgeInterpretationID'
upb_concordance_format_join = 'LEFT JOIN ConcordanceFormats ON ConcordanceFormats.ConcordanceFormatID=UPbAnalyses.ConcordanceFormatID'
upb_spot_size_unit_join = 'LEFT JOIN DistanceUnits AS SpotSizeUnits ON SpotSizeUnits.DistanceUnitID=UPbAnalyses.SpotSizeUnitID'
upb_rejection_reason_join = '''LEFT JOIN UPbAnalyses_RejectionReasons ON UPbAnalyses.UPbAnalysisID=UPbAnalyses_RejectionReasons.UPbAnalysisID
                                    LEFT JOIN RejectionReasons AS UPbRejectionReasons ON UPbRejectionReasons.RejectionReasonID=UPbAnalyses_RejectionReasons.RejectionReasonID'''

# Information for settings

sample_view_columns = [qsample_id, qigsn, qsample_name, qgps, qsample_elev, qcolumn_gps, qcolumn_data, qsample_age,
                       qage_range, qsample_age_constraint, qsample_age_interpretation,
                       qsample_age_references, qsample_description, qage_signature, qregions, qrock_types,
                       qsample_context, qsampling_methods, qsettings, qunits, qaliquots, qaliquot_contexts,
                       qspots, qspot_compositions, qspot_contexts, qreferences, qlab_facilities, qinstruments,
                       qupb_analysis_methods, qupb_ratio_error_formats, qupb_age_error_formats, qupb_age_units,
                       qupb_age_interpretations, qconcordance_formats, qspot_sizes, qupb_rejection_reasons]

# Many-to-many tables related to table at the beginning of each list, populate multiple selection dropdowns
many_editable = [
    ['Samples', 'AgeSignatures', 'Regions', 'RockTypes', 'SampleContexts', 'SamplingMethods', 'Settings', 'Units'],
    ['Aliquots', 'AliquotContexts'], ['Spots', 'SpotCompositions', 'SpotContexts'], ['UPbAnalyses', 'RejectionReasons']]
# One-to-many columns related to table at the beginning of each list, populate single selection dropdowns
one_editable = [['Samples', 'SampleAges', 'Columns', 'DistanceUnits'],
            ['Columns', 'DistanceUnits'], ['Aliquots', 'Samples'], ['Spots', 'Aliquots', 'SpotCompositions'],
            ['UPbAnalyses', 'Spots', 'References', 'LabFacilities', 'Instruments', 'UPbAnalysisMethods', 'ErrorFormats', 'AgeUnits', 'AgeInterpretations', 'ConcordanceFormats', 'DistanceUnits']]


user_viewable_alltables = ['AgeConstraints', 'AgeInterpretations', 'Ages', 'AgeSignatures', 'Aliquots', 'AliquotContexts',
                        'Columns', 'Instruments', 'LabFacilities',
                        '"References"', 'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts', 'Samples',
                        'SamplingMethods', 'Settings',
                        'Spots', 'SpotCompositions', 'SpotContexts', 'UPbAnalyses', 'UPbAnalysisMethods', 'Units']
user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts',
                       'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts',
                       'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContexts', 'UPbAnalysisMethods',
                       'Units']
user_viewable_tables = ['Columns', 'LabFacilities', 'Instruments', 'Sources', 'UPbAnalyses', 'Spots',
                        'UPbAnalysisMethods']

conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Spots', 'UPbAnalyses']
conditionally_editable_trees = ['Aliquots']

trigger_tables = ['Columns', 'GPSLocations', 'SampleAges', 'Samples', 'SampleView', 'ColumnEditView', 'UPbAnalyses']

views = ['SampleView', 'AliquotView', 'SpotView', 'UPbView', 'ColumnView', 'ColumnEditView']

age_units = [('Billion years', 'Ga', '1000000000'),
                 ('Million years', 'Ma', '1000000'),
                 ('Thousand years', 'ka', '1000'),
                 ('Years', 'a', '1')]

concordance_formats = [('Concordance ratio', 'Con', 'Ratio agreement between the 206Pb/238U age to the 207Pb/235U age'),
                         ('Concordance percent', 'Con%', 'Percent agreement between the 206Pb/238U age and the 207Pb/235U age'),
                         ('Discordance ratio', 'Dis', 'Ratio disagreement between  the 206Pb/238U age to the 207Pb/206Pb age'),
                         ('Discordance percent', 'Dis%', 'Percent disagreement between the 206Pb/238U age and the 207Pb/206Pb age')]

direction_units = [('North', 'N','positive north'),
                       ('South', 'S','positive south'),
                       ('East', 'E','positive east'),
                       ('West', 'W','positive west')]

distance_units = [('Kilometers', 'km', '1000'),
                 ('Meters', 'm', '1'),
                 ('Centimeters', 'cm', '0.01'),
                 ('Millimeter', 'mm', '0.001'),
                 ('Micrometer', 'µm', '0.000001'),
                 ('Miles', 'mi', '5280'),
                 ('Yards', 'yd', '3'),
                 ('Feet', 'ft', '1'),
                 ('Inches', 'in', f'(1/12)')]

error_formats = [('1 sigma absolute', '1σ abs', '1σ absolute uncertainty'),
                         ('2 sigma absolute', '2σ abs', '2σ absolute uncertainty'),
                         ('1 sigma percent', '1σ %', '1σ percent uncertainty'),
                         ('2 sigma percent', '2σ %', '2σ percent uncertainty')]

gps_formats = [('Decimal degrees positive/negative', 'DD +/-', 'Decimal degrees with positive N and E and negative S and W'),
                   ('Decimal degrees cardinal', 'DD NSEW', 'Decimal degrees with cardinal directions'),
                   ('Degrees minutes positive/negative', 'DDM +/-', 'Degrees and decimal minutes with positive N and E and negative S and W'),
                   ('Degrees minutes cardinal', 'DDM NSEW', 'Degrees and decimal minutes with cardinal directions'),
                   ('Degrees minutes seconds positive/negative', 'DMS +/-', 'Degrees, minutes, and seconds with positive N and E and negative S and W'),
                   ('Degrees minutes seconds cardinal', 'DMS NSEW', 'Degrees, minutes, and seconds with cardinal directions'),
                   ('Universal Transverse Mercator', 'UTM', 'Universal Transverse Mercator with zone, northing, and easting')]


table_attributes_dict = {
    'AgeConstraints': [
        "AgeConstraintName", "AgeConstraintDescription",
        "AgeConstraintCreated", "AgeConstraintModified"],
    'AgeInterpretations': [
        "AgeInterpretationName", "AgeInterpretationDescription",
        "AgeInterpretationCreated", "AgeInterpretationModified"],
    'Ages': [
        "AgeName", "MaxMa", "MinMa",
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
        "AliquotName", "AliquotCreated", "AliquotModified"
    ],
    'Columns': [
        "ColumnName", "ColumnDescription",
        "ColumnCreated", "ColumnModified"
    ],
    'Instruments': [
        "InstrumentName", "InstrumentDescription",
        "InstrumentCreated", "InstrumentModified"
    ],
    'LabFacilities': [
        "LabFacilityName", "LabFacilityDescription",
        "LabFacilityCreated", "LabFacilityModified"
    ],
    '"References"': [
        "Authors", "Year", "Title", "Source", "doi", "ShortCitation", "ReferenceDescription",
        "ReferenceCreated", "ReferenceModified"
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
        "SampleAgeDescription", "SampleAgeCreated", "SampleAgeModified"
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
        "SpotName", "SpotCreated", "SpotModified"
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
        "Calculated206Pb/207Pb",
        "Calculated207Pb/206Pb",
        "Calculated207Pb/235U",
        "Calculated235U/207Pb",
        "Calculated206Pb/238U",
        "Calculated238U/206Pb",
        "Calculated208Pb/232Th",
        "Calculated232Th/208Pb",
        "Calculated238U/232Th",
        "Calculated232Th/238U",
        "Calculated204Pb/238U",
        "Calculated238U/204Pb",
        "Calculated206Pb/204Pb",
        "Calculated204Pb/206Pb",
        "Calculated207Pb/204Pb",
        "Calculated204Pb/207Pb",
        "Calculated208Pb/204Pb",
        "Calculated204Pb/208Pb",
        "Concordance",
        "Rejected",
        "UPbAnalysisCreated",
        "UPbAnalysisModified",
        "Calculated207Pb/206PbAge",
        "Calculated206Pb/238UAge",
        "Calculated207Pb/235UAge",
        "Calculated208Pb/232ThAge",
        "CalculatedSpotSize",
        "Calculated207Pb/206PbAgeError",
        "Calculated207Pb/235UAgeError",
        "Calculated206Pb/238UAgeError",
        "Calculated208Pb/232ThAgeError",
        "BestAge",
        "CalculatedBestAgeError",
        "Calculated206Pb/207PbError",
        "Calculated207Pb/206PbError",
        "Calculated207Pb/235UError",
        "Calculated235U/207PbError",
        "Calculated206Pb/238UError",
        "Calculated238U/206PbError",
        "Calculated208Pb/232ThError",
        "Calculated232Th/208PbError",
        "Calculated238U/232ThError",
        "Calculated232Th/238UError",
        "Calculated204Pb/238UError",
        "Calculated238U/204PbError",
        "Calculated206Pb/204PbError",
        "Calculated204Pb/206PbError",
        "Calculated207Pb/204PbError",
        "Calculated204Pb/207PbError",
        "Calculated208Pb/204PbError",
        "Calculated204Pb/208PbError"
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

upb_possible_input_fields = [
    'SpotID',
    'Pb204cps', 'Pb206cps', 'Pb207cps', 'Pb208cps', 'Pb*cps', 'Th232cps', 'U235cps', 'U238cps',
    'Uppm', 'Thppm',
    'U/Th', 'Th/U',

    '206Pb/204Pb', '206Pb/204PbError',
    '204Pb/206Pb', '204Pb/206PbError',
    '207Pb/204Pb', '207Pb/204PbError',
    '204Pb/207Pb', '204Pb/207PbError',
    '208Pb/204Pb', '208Pb/204PbError',
    '204Pb/208Pb', '204Pb/208PbError',
    '206Pb/207Pb', '206Pb/207PbError',
    '207Pb/206Pb', '207Pb/206PbError',

    '204Pb/238U', '204Pb/238UError',
    '238U/204Pb', '238U/204PbError',
    '206Pb/238U', '206Pb/238UError',
    '238U/206Pb', '238U/206PbError',
    '207Pb/235U', '207Pb/235UError',
    '235U/207Pb', '235U/207PbError',
    '208Pb/232Th', '208Pb/232ThError',
    '232Th/208Pb', '232Th/208PbError',

    '238U/232Th', '238U/232ThError',
    '232Th/238U', '232Th/238UError',

    'ErrorCorr/Rho',
    'RatioErrorTypeID',
    '207Pb/206PbAge', '207Pb/206PbAgeError',
    '207Pb/235UAge', '207Pb/235UAgeError',
    '206Pb/238UAge', '206Pb/238UAgeError',
    '208Pb/232ThAge', '208Pb/232ThAge',
    'BestAge', 'BestAgeError',

    'AgeErrorTypeID',
    'AgeUnitID',
    'Concordance', 'ConcordanceTypeID',
    'SpotSize', 'SpotSizeUnitID',
    'Rejected',

    'ReferenceID',
    'LabFacilityID',
    'InstrumentID',
    'UPbAnalysisMethodID'
]


def get_join_from_table(tables: list[str]) -> str:
    join = ""

    for table in tables:
        match table:
            case 'AgeConstraints':
                if default_sample_age_join not in join:
                    join += default_sample_age_join + '\n'
                if age_constraint_join not in join:
                    join += age_constraint_join + '\n'
            case 'AgeInterpretations':
                if default_sample_age_join not in join:
                    join += default_sample_age_join + '\n'
                if age_interpretation_join not in join:
                    join += age_interpretation_join + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Ages':
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Aliquots':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
            case 'AliquotContexts':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if aliquot_context_join not in join:
                    join += aliquot_context_join + '\n'
            case 'Columns':
                if column_join not in join:
                    join += column_join + '\n'
            case 'LabFacilities':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_analysis_join not in join:
                    join += upb_analysis_join + '\n'
                if upb_labs_join not in join:
                    join += upb_labs_join + '\n'
            case 'Instruments':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_analysis_join not in join:
                    join += upb_analysis_join + '\n'
                if upb_instruments_join not in join:
                    join += upb_instruments_join + '\n'
            case 'References':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_analysis_join not in join:
                    join += upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'Regions':
                if region_join not in join:
                    join += region_join + '\n'
            case 'RejectionReasons':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_analysis_join not in join:
                    join += upb_analysis_join + '\n'
                if upb_rejection_reason_join not in join:
                    join += upb_rejection_reason_join + '\n'
            case 'RockTypes':
                if rock_type_join not in join:
                    join += rock_type_join + '\n'
            case 'SampleAges':
                if default_sample_age_join not in join:
                    join += default_sample_age_join + '\n'
            case 'SampleContexts':
                if sample_context_join not in join:
                    join += sample_context_join + '\n'
            case 'SamplingMethods':
                if sampling_method_join not in join:
                    join += sampling_method_join + '\n'
            case 'Settings':
                if setting_join not in join:
                    join += setting_join + '\n'
            case 'Spots':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
            case 'SpotCompositions':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if spot_composition_join not in join:
                    join += spot_composition_join + '\n'
            case 'SpotContexts':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if spot_context_join not in join:
                    join += spot_context_join + '\n'
            case 'UPbAnalyses':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_analysis_join not in join:
                    join += upb_analysis_join + '\n'
            case 'UPbAnalysisMethods':
                if aliquot_join not in join:
                    join += aliquot_join + '\n'
                if spot_join not in join:
                    join += spot_join + '\n'
                if upb_analysis_join not in join:
                    join += upb_analysis_join + '\n'
                if upb_method_join not in join:
                    join += upb_method_join + '\n'
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'
            case 'Samples':
                pass
    return join