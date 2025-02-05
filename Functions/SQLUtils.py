from Functions.Settings_manager import settings
from PyQt6.QtSql import QSqlQueryModel

# ID columns
qsample_id = 'Samples.SampleID'
qaliquot_id = 'Aliquots.AliquotID'
qspot_id = 'Spots.SpotID'
qupb_id = 'UPbAnalyses.UPbAnalysisID'


# Sample view columns
qsample_name = 'Samples.SampleName'
qigsn = 'Samples.SampleIGSN'
qgps = 'GPSLocations.GPSLocationConverted'
qgps_display = 'GPSLocations.GPSLocationDisplay'
qsample_elev = 'GPSLocations.CalculatedGPSElev || "±" || GPSLocations.CalculatedGPSElevError'
qsqmple_elev_display = 'GPSLocations.GPSElev || "±" || GPSLocations.GPSElevError'
qsample_elev_unit = 'SampleElevationUnits.DistanceUnitAbbreviation'
qsample_age = 'SampleAges.SampleAgeDisplay'
qage_range = 'COALESCE(CalculatedOldestDirectAge, " ") || "-" || COALESCE(CalculatedYoungestDirectAge, " ")'
qage_range_display = 'COALESCE(OldestDirectAge, " ") || "-" || COALESCE(YoungestDirectAge, " ") || "(" || COALESCE(DirectAgeUnitAbbreviation, " ") || ")(" || COALESCE(DirectAgeErrorFormatAbbreviation, " ") || ")"'
qsample_age_constraint = 'GROUP_CONCAT(DISTINCT AgeConstraintName)'
qsample_age_interpretation = 'GROUP_CONCAT(DISTINCT AgeInterpretationName)'
qsample_age_references = 'GROUP_CONCAT(DISTINCT AgeReferences.ReferenceDisplay)'
qsample_description = 'Samples.SampleDescription'
qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName)'
qregions = 'GROUP_CONCAT(DISTINCT RegionName)'
qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName)'
qsample_context = 'GROUP_CONCAT(DISTINCT SampleContextName)'
qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName)'
qsettings = 'GROUP_CONCAT(DISTINCT SettingName)'
qunits = 'GROUP_CONCAT(DISTINCT UnitName)'
qsample_created = 'Samples.SampleCreated'
qsample_modified = 'Samples.SampleModified'

# Samples, include null values
qsample_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(Samples.SampleID,"Null"))'
qsample_name_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleName,"Null"))'
qigsn_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleIGSN,"Null"))'
qsample_gps_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleGPSLocationID,"Null"))'
qsample_column_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleColumnID,"Null"))'
qheight_depth_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepth,"Null"))'
qheight_depth_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthError,"Null"))'
qheight_depth_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(HeightDepthUnitID,"Null"))'
qheight_depth_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnHeightDepthUnits.DistanceUnitAbbreviation,"Null"))'
qsample_description_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleDescription,"Null"))'
qsample_reference_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ReferenceDisplay,"Null"))'
qsample_gps_converted_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLocationConverted,"Null"))'
qsample_lat_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLatDeg, "Null"))'
qsample_lat_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLatMin, "Null"))'
qsample_lat_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLatSec, "Null"))'
qsample_lat_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLatDirectionID, "Null"))'
qsample_lat_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleLatDirections.DirectionUnitAbbreviation, "Null"))'
qsample_lon_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLonDeg, "Null"))'
qsample_lon_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLonMin, "Null"))'
qsample_lon_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLonSec, "Null"))'
qsample_lon_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSLonDirectionID, "Null"))'
qsample_lon_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleLonDirections.DirectionUnitAbbreviation, "Null"))'
qsample_utm_zone_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSUTMZone, "Null"))'
qsample_utm_northing_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSUTMN, "Null"))'
qsample_utm_easting_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSUTME, "Null"))'
qsample_gps_format_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSFormatID, "Null"))'
qsample_gps_format_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSFormats.GPSFormatAbbreviation, "Null"))'
qsample_gps_elev_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSElev, "Null"))'
qsample_gps_elev_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSElevError, "Null"))'
qsample_gps_elev_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(GPSLocations.GPSElevUnitID, "Null"))'
qsample_gps_elev_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleElevationUnits.DistanceUnitAbbreviation, "Null"))'
qsample_default_age_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(DefaultSampleAgeID,"Null"))'
qsample_direct_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAge,"Null"))'
qsample_direct_age_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeError,"Null"))'
qsample_direct_age_error_format_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeErrorFormatID,"Null"))'
qsample_direct_age_error_format_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(DirectAgeErrorFormats.ErrorFormatAbbreviation,"Null"))'
qsample_oldest_direct_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.OldestDirectAge,"Null"))'
qsample_youngest_direct_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.YoungestDirectAge,"Null"))'
qsample_direct_age_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.DirectAgeUnitID,"Null"))'
qsample_direct_age_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeUnits.AgeUnitAbbreviation,"Null"))'
qsample_oldest_age_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.OldestAgeID,"Null"))'
qsample_oldest_rel_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(OldAge.AgeName,"Null"))'
qsample_youngest_age_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.YoungestAgeID,"Null"))'
qsample_youngest_rel_age_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(YoungAge.AgeName,"Null"))'
qsample_age_description_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges.SampleAgeDescription,"Null"))'
qsample_age_constraint_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges_AgeConstraints.AgeConstraintID,"Null"))'
qsample_age_constraint_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeConstraints.AgeConstraintName,"Null"))'
qsample_age_interpretation_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleAges_AgeInterpretations.AgeInterpretationID,"Null"))'
qsample_age_interpretation_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeInterpretations.AgeInterpretationName,"Null"))'
qsample_age_reference_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeReferences.ReferenceID,"Null"))'
qsample_age_reference_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AgeReferences.ReferenceDisplay,"Null"))'
qsample_context_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SampleContextName,"Null"))'
qsampling_methods_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SamplingMethodName,"Null"))'
qrock_types_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(RockTypeName,"Null"))'
qregions_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(RegionName,"Null"))'
qsettings_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SettingName,"Null"))'
qunits_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(UnitName,"Null"))'

#Columns, skip null values
qcolumn_names = 'GROUP_CONCAT(DISTINCT ColumnName)'
qcolumn_data = f'HeightDepth || "±" || HeightDepthError'
qcolumn_gps = f'''ColumnGPS.GPSLocationConverted'''
qcolumn_calc_total_height_depth = f'Columns.CalculatedColumnTotalHeightDepth'
qcolumn_total_height_depth = f'Columns.ColumnTotalHeightDepth'
qcolumn_total_height_depth_unit = f'ColumnUnits.DistanceUnitAbbreviation'
qcolumn_gps_display = 'ColumnGPS.GPSLocationDisplay'
qcolumn_description = 'ColumnDescription'
qcolumn_created = 'ColumnCreated'
qcolumn_modified = 'ColumnModified'

# Columns, include null values
qcolumn_id = 'Columns.ColumnID'
qcolumn_name = 'Columns.ColumnName'
qcolumn_total_height_depth_ifnull = f'GROUP_CONCAT( DISTINCT ifnull(Columns.CalculatedColumnTotalHeightDepth)"'
qcolumn_gps_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.BaseGPSLocationID,"Null"))'
qcolumn_names_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(Columns.ColumnName,"Null"))'
qcolumn_gps_converted_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLocationConverted,"Null"))'
qcolumn_lat_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatDeg, "Null"))'
qcolumn_lat_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatMin, "Null"))'
qcolumn_lat_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatSec, "Null"))'
qcolumn_lat_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLatDirectionID, "Null"))'
qcolumn_lat_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnLatDirections.DirectionUnitAbbreviation, "Null"))'
qcolumn_lon_deg_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonDeg, "Null"))'
qcolumn_lon_min_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonMin, "Null"))'
qcolumn_lon_sec_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonSec, "Null"))'
qcolumn_lon_dir_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSLonDirectionID, "Null"))"'
qcolumn_lon_dir_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnLonDirections.DirectionUnitAbbreviation, "Null"))"'
qcolumn_utm_zone_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSUTMZone, "Null"))'
qcolumn_utm_northing_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSUTMN, "Null"))"'
qcolumn_utm_easting_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSUTME, "Null"))"'
qcolumn_gps_format_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSFormatID, "Null"))"'
qcolumn_gps_format_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPSFormats.GPSFormatAbbreviation, "Null"))"'
qcolumn_gps_elev_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSElev, "Null"))"'
qcolumn_gps_elev_error_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSElevError, "Null"))"'
qcolumn_gps_elev_unit_id_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnGPS.GPSElevUnitID, "Null"))"'
qcolumn_gps_elev_unit_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnElevationUnits.DistanceUnitAbbreviation, "Null"))"'
qcolumn_description_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(ColumnDescription,"Null"))"'


# Aliquot view columns
qaliquot_count = 'COUNT(DISTINCT Aliquots.AliquotID)'
qaliquot = 'AliquotName'
qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName)'
qaliquot_parent_id = 'ParentAliquotID'
qaliquot_parent_row = 'AliquotParentRow'
qaliquot_sample = 'Samples.SampleName'
qaliquot_contexts = 'GROUP_CONCAT(DISTINCT AliquotContextName)'
qaliquot_spots = 'GROUP_CONCAT(DISTINCT SpotName)'
qaliquot_spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName)'
qaliquot_spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName)'
qaliquot_references = 'GROUP_CONCAT(DISTINCT ReferenceDisplay)'
qaliquot_upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)'
qaliquot_labs = 'GROUP_CONCAT(DISTINCT LabFacilityName)'
qaliquot_created = 'AliquotCreated'
qaliquot_modified = 'AliquotModified'

# Aliquot, include null values
qaliquots_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AliquotName,"Null"))'
qaliquot_context_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(AliquotContextName,"Null"))'


# Spot view columns
qspot_count = 'COUNT(DISTINCT Spots.SpotID)'
qspot = 'SpotName'
qspots = 'GROUP_CONCAT(DISTINCT SpotName)'
qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName)'
qspot_contexts = 'GROUP_CONCAT(DISTINCT SpotContextName)'
qspot_created = 'SpotCreated'
qspot_modified = 'SpotModified'

# Spots, include null values
qspots_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SpotName,"Null"))'
qspot_contexts_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SpotContextName,"Null"))'
qspot_compositions_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(SpotCompositionName,"Null"))'

# UPb view columns
qupb_count = 'SUM(CASE WHEN Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID)'  # accepted/total
qupb_references = 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay)'
qupb_lab_facilities = 'GROUP_CONCAT(DISTINCT LabFacilityName)'
qupb_instruments = 'GROUP_CONCAT(DISTINCT InstrumentName)'
qupb_analysis_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName)'
qupb_204cps = 'UPbAnalyses."Pb204cps"'
qupb_206cps = 'UPbAnalyses."Pb206cps"'
qupb_207cps = 'UPbAnalyses."Pb207cps"'
qupb_208cps = 'UPbAnalyses."Pb208cps"'
qupb_pbcps = 'UPbAnalyses."Pb*cps"'
qupb_232cps = 'UPbAnalyses."Th232cps"'
qupb_235cps = 'UPbAnalyses."U235cps"'
qupb_238cps = 'UPbAnalyses."U238cps"'
qupb_uppm = 'UPbAnalyses."Uppm"'
qupb_thppm = 'UPbAnalyses."Thppm"'
qupb_uth = 'UPbAnalyses."U/Th"'
qupb_thu = 'UPbAnalyses."Th/U"'
qupb_calc_uth = 'UPbAnalyses."CalculatedU/Th"'
qupb_calc_thu = 'UPbAnalyses."CalculatedTh/U"'
qupb_206207 = 'UPbAnalyses."206Pb/207Pb"'
qupb_206207_error = 'UPbAnalyses."206Pb/207PbError"'
qupb_calc_206207 = 'UPbAnalyses."Calculated206Pb/207Pb"'
qupb_calc_206207_error = 'UPbAnalyses."Calculated206Pb/207PbError"'
qupb_207206 = 'UPbAnalyses."207Pb/206Pb"'
qupb_207206_error = 'UPbAnalyses."207Pb/206PbError"'
qupb_calc_207206 = 'UPbAnalyses."Calculated207Pb/206Pb"'
qupb_calc_207206_error = 'UPbAnalyses."Calculated207Pb/206PbError"'
qupb_207235 = 'UPbAnalyses."207Pb/235U"'
qupb_207235_error = 'UPbAnalyses."207Pb/235UError"'
qupb_calc_207235 = 'UPbAnalyses."Calculated207Pb/225U"'
qupb_calc_207235_error = 'UPbAnalyses."Calculated207Pb/235UError"'
qupb_235207 = 'UPbAnalyses."235U/207Pb"'
qupb_235207_error = 'UPbAnalyses."235U/207PbError"'
qupb_calc_235207 = 'UPbAnalyses."Calculated235U/207Pb"'
qupb_calc_235207_error = 'UPbAnalyses."Calculated235U/207PbError"'
qupb_206238 = 'UPbAnalyses."206Pb/238U"'
qupb_206238_error = 'UPbAnalyses."206Pb/238UError"'
qupb_calc_206238 = 'UPbAnalyses."Calculated206Pb/238U"'
qupb_calc_206238_error = 'UPbAnalyses."Calculated206Pb/238UError"'
qupb_238206 = 'UPbAnalyses."238U/206Pb"'
qupb_238206_error = 'UPbAnalyses."238U/206PbError"'
qupb_calc_238206 = 'UPbAnalyses."Calculated238U/206Pb"'
qupb_calc_238206_error = 'UPbAnalyses."Calculated238U/206PbError"'
qupb_208232 = 'UPbAnalyses."208Pb/232Th"'
qupb_208232_error = 'UPbAnalyses."208Pb/232ThError"'
qupb_calc_208232 = 'UPbAnalyses."Calculated208Pb/232Th"'
qupb_calc_208232_error = 'UPbAnalyses."Calculated208Pb/232ThError"'
qupb_232208 = 'UPbAnalyses."232Th/208Pb"'
qupb_232208_error = 'UPbAnalyses."232Th/208PbError"'
qupb_calc_232208 = 'UPbAnalyses."Calculated232Th/208Pb"'
qupb_calc_232208_error = 'UPbAnalyses."Calculated232Th/208PbError"'
qupb_238232 = 'UPbAnalyses."238U/232Th"'
qupb_238232_error = 'UPbAnalyses."238U/232ThError"'
qupb_calc_238232 = 'UPbAnalyses."Calculated238U/232Th"'
qupb_calc_238232_error = 'UPbAnalyses."Calculated238U/232ThError"'
qupb_232238 = 'UPbAnalyses."232Th/238U"'
qupb_232238_error = 'UPbAnalyses."232Th/238UError"'
qupb_calc_232238 = 'UPbAnalyses."Calculated232Th/238U"'
qupb_calc_232238_error = 'UPbAnalyses."Calculated232Th/238UError"'
qupb204238 = 'UPbAnalyses."204Pb/238U"'
qupb204238_error = 'UPbAnalyses."204Pb/238UError"'
qupb_calc_204238 = 'UPbAnalyses."Calculated204Pb/238U"'
qupb_calc_204238_error = 'UPbAnalyses."Calculated204Pb/238UError"'
qupb_2382204 = 'UPbAnalyses."238U/204Pb"'
qupb_2382204_error = 'UPbAnalyses."238U/204PbError"'
qupb_calc_238204 = 'UPbAnalyses."Calculated238U/204Pb"'
qupb_calc_238204_error = 'UPbAnalyses."Calculated238U/204PbError"'
qupb_206204 = 'UPbAnalyses."206Pb/204Pb"'
qupb_206204_error = 'UPbAnalyses."206Pb/204PbError"'
qupb_calc_206204 = 'UPbAnalyses."Calculated206Pb/204Pb"'
qupb_calc_206204_error = 'UPbAnalyses."Calculated206Pb/204PbError"'
qupb_204206 = 'UPbAnalyses."204Pb/206Pb"'
qupb_204206_error = 'UPbAnalyses."204Pb/206PbError"'
qupb_calc_204206 = 'UPbAnalyses."Calculated204Pb/206Pb"'
qupb_calc_204206_error = 'UPbAnalyses."Calculated204Pb/206PbError"'
qupb_207204 = 'UPbAnalyses."207Pb/204Pb"'
qupb_207204_error = 'UPbAnalyses."207Pb/204PbError"'
qupb_calc_207204 = 'UPbAnalyses."Calculated207Pb/204Pb"'
qupb_calc_207204_error = 'UPbAnalyses."Calculated207Pb/204PbError"'
qupb_204207 = 'UPbAnalyses."204Pb/207Pb"'
qupb_204207_error = 'UPbAnalyses."204Pb/207PbError"'
qupb_calc_204207 = 'UPbAnalyses."Calculated204Pb/207Pb"'
qupb_calc_204207_error = 'UPbAnalyses."Calculated204Pb/207PbError"'
upb_208204 = 'UPbAnalyses."208Pb/204Pb"'
qupb_208204_error = 'UPbAnalyses."208Pb/204PbError"'
qupb_calc_208204 = 'UPbAnalyses."Calculated208Pb/204Pb"'
qupb_calc_208204_error = 'UPbAnalyses."Calculated208Pb/204PbError"'
upb_204208 = 'UPbAnalyses."204Pb/208Pb"'
upb_204208_error = 'UPbAnalyses."204Pb/208PbError"'
qupb_calc_204208 = 'UPbAnalyses."Calculated204Pb/208Pb"'
qupb_calc_204208_error = 'UPbAnalyses."Calculated204Pb/208PbError"'
qupb_ratio_error_formats = 'GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation)'
qupb_error_corr = 'UPbAnalyses.ErrorCorr'
qupb_207206_age = 'UPbAnalyses."207Pb/206PbAge"'
qupb_207206_age_error = 'UPbAnalyses."207Pb/206PbAgeError"'
qupb_calc_207206_age = 'UPbAnalyses."Calculated207Pb/206PbAge"'
qupb_calc_207206_age_error = 'UPbAnalyses."Calculated207Pb/206PbAgeError'
qupb_207235_age = 'UPbAnalyses."207Pb/235UAge"'
qupb_207235_age_error = 'UPbAnalyses."207Pb/235UAgeError"'
qupb_calc_207235_age = 'UPbAnalyses."Calculated207Pb/235UAge"'
qupb_calc_207235_age_error = 'UPbAnalyses."Calculated207Pb/235UAgeError"'
qupb_206238_age = 'UPbAnalyses."206Pb/238UAge"'
qupb_206238_age_error = 'UPbAnalyses."206Pb/238UAgeError"'
qupb_calc_206238_age = 'UPbAnalyses."Calculated206Pb/238UAge"'
qupb_calc_206238_age_error = 'UPbAnalyses."Calculated206Pb/238UAgeError"'
qupb_208232_age = 'UPbAnalyses."208Pb/232ThAge"'
qupb_208232_age_error = 'UPbAnalyses."208Pb/232ThAgeError"'
qupb_calc_208232_age = 'UPbAnalyses."Calculated208Pb/232ThAge"'
qupb_calc_208232_age_error = 'UPbAnalyses."Calculated208Pb/232ThAgeError"'
qupb_best_age = 'UPbAnalyses.BestAge'
qupb_best_age_error = 'UPbAnalyses.BestAgeError'
qupb_calc_best_age = 'UPbAnalyses."CalculatedBestAge"'
qupb_calc_best_age_error = 'UPbAnalyses."CalculatedBestAgeError"'
qupb_age_error_formats = 'GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation)'
qupb_age_units = 'GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation)'
qupb_age_interpretations = 'GROUP_CONCAT(DISTINCT UPbAgeInterpretations.AgeInterpretationName)'
qupb_concordance = 'UPbAnalyses.Concordance'
qupb_calc_concordance = 'UPbAnalyses."CalculatedConcordance"'
qconcordance_formats = 'GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation)'
qspot_size = 'UPbAnalyses.SpotSize'
qspot_sizes = f'GROUP_CONCAT(DISTINCT CalculatedSpotSize)'
qspot_size_unit = 'GROUP_CONCAT(DISTINCT SpotSizeUnit.DistanceUnitAbbreviation)'
qupb_rejected = 'CASE WHEN UPbAnalyses.Rejected = 1 THEN "Rejected" ELSE "Accepted" END'
qupb_rejection_reasons = 'GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName)'
qupb_created = 'UPbAnalysisCreated'
qupb_modified = 'UPbAnalysisModified'

# UPb, include null values
qupb_references_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(UPbReferences.ReferenceDisplay,"Null")) AS "References"'
qupb_methods_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(UPbAnalysisMethodName,"Null")) AS "UPb Analysis Methods"'
qupb_labs_ifnull = 'GROUP_CONCAT(DISTINCT ifnull(LabFacilityName,"Null")) AS "Lab Facilities"'


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
gps_sample_join = '''LEFT JOIN GPSLocations AS GPSLocations ON Samples.SampleGPSLocationID=GPSLocations.GPSLocationID'''
gps_sample_left_joins = '''LEFT JOIN DirectionUnits AS SampleLatDirections ON SampleLatDirections.DirectionUnitID=GPSLocations.GPSLatDirectionID
                        LEFT JOIN DirectionUnits AS SampleLonDirections ON SampleLonDirections.DirectionUnitID=GPSLocations.GPSLonDirectionID
                        LEFT JOIN DistanceUnits AS SampleElevationUnits ON SampleElevationUnits.DistanceUnitID=GPSLocations.GPSElevUnitID
                        LEFT JOIN GPSFormats AS GPSFormats ON GPSFormats.GPSFormatID=GPSLocations.GPSFormatID'''
gps_column_join = '''LEFT JOIN GPSLocations AS ColumnGPS ON Columns.ColumnBaseGPSID=ColumnGPS.GPSLocationID'''
gps_column_left_joins = '''LEFT JOIN DirectionUnits AS ColumnLatDirections ON ColumnLatDirections.DirectionUnitID=ColumnGPS.GPSLatDirectionID
                        LEFT JOIN DirectionUnits AS ColumnLonDirections ON ColumnLonDirections.DirectionUnitID=ColumnGPS.GPSLonDirectionID
                        LEFT JOIN DistanceUnits AS ColumnElevationUnits ON ColumnElevationUnits.DistanceUnitID=ColumnGPS.GPSElevUnitID
                        LEFT JOIN GPSFormats AS ColumnGPSFormats ON ColumnGPSFormats.GPSFormatID=ColumnGPS.GPSFormatID'''

# ColumnJoins
column_units_join = 'LEFT JOIN DistanceUnits as ColumnUnits ON ColumnUnits.DistanceUnitID=Columns.ColumnTotalHeightDepthUnitID'

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
sample_aliquot_join = 'LEFT JOIN Aliquots ON Aliquots.SampleID=Samples.SampleID'

# AliquotJoins
aliquot_sample_join = 'LEFT JOIN Samples ON Samples.SampleID=Aliquots.SampleID'
aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts ON Aliquots.AliquotID=Aliquots_AliquotContexts.AliquotID
                                LEFT JOIN AliquotContexts ON AliquotContexts.AliquotContextID=Aliquots_AliquotContexts.AliquotContextID'''

# Aliquot-spot Join
aliquot_spot_join = 'LEFT JOIN Spots ON Spots.AliquotID=Aliquots.AliquotID'

# SpotJoins
spot_aliquot_join = 'LEFT JOIN Aliquots ON Aliquots.AliquotID=Spots.AliquotID'
spot_composition_join = '''LEFT JOIN SpotCompositions ON SpotCompositions.SpotCompositionID=Spots.SpotCompositionID'''
spot_context_join = '''LEFT JOIN Spots_SpotContexts ON Spots.SpotID=Spots_SpotContexts.SpotID
                                LEFT JOIN SpotContexts ON SpotContexts.SpotContextID=Spots_SpotContexts.SpotContextID'''
spot_upb_analysis_join = 'LEFT JOIN UPbAnalyses ON UPbAnalyses.SpotID=Spots.SpotID'

# UPbJoins
upb_spot_join = 'LEFT JOIN Spots ON Spots.SpotID=UPbAnalyses.SpotID'
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
                       qspots, qspot_compositions, qspot_contexts, qupb_references, qupb_lab_facilities, qupb_instruments,
                       qupb_analysis_methods, qupb_ratio_error_formats, qupb_age_error_formats, qupb_age_units,
                       qupb_age_interpretations, qconcordance_formats, qspot_sizes, qupb_rejection_reasons]

# Many-to-many tables related to table at the beginning of each list, populate multiple selection dropdowns
many_editable = [['Samples', 'AgeSignatures', 'Regions', 'RockTypes', 'SampleContexts', 'SamplingMethods', 'Settings', 'Units'],
             ['Aliquots', 'AliquotContexts'], ['Spots', 'SpotCompositions', 'SpotContexts'], ['UPbAnalyses', 'RejectionReasons']]
# One-to-many columns related to table at the beginning of each list, populate single selection dropdowns
one_editable = [['Samples', 'SampleAges', 'Columns', 'DistanceUnits'],
            ['Columns', 'DistanceUnits'], ['Aliquots', 'Samples'], ['Spots', 'Aliquots', 'SpotCompositions'],
            ['UPbAnalyses', 'Spots', 'References', 'LabFacilities', 'Instruments', 'UPbAnalysisMethods', 'ErrorFormats', 'AgeUnits', 'AgeInterpretations', 'ConcordanceFormats', 'DistanceUnits']]



user_viewable_tables = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts',
                        'Columns', 'Instruments', 'LabFacilities', 'References', 'Regions', 'RejectionReasons',
                        'RockTypes', 'SampleContexts', 'Samples', 'SamplingMethods', 'Settings', 'SpotCompositions',
                        'SpotContexts', 'UPbAnalysisMethods', 'Units']

user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts',
                       'Regions', 'RockTypes', 'SampleContexts', 'SamplingMethods', 'Settings', 'SpotCompositions',
                       'SpotContexts', 'UPbAnalysisMethods', 'Units']
conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Spots', 'UPbAnalyses']
conditionally_editable_trees = ['Aliquots']

trigger_tables = ['Columns', 'GPSLocations', 'SampleAges', 'Samples', 'SampleView', 'ColumnEditView', 'UPbAnalyses', 'UPbAnalysesView', 'UPbAnalysesEditView']

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
    'References': [
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
        "CalculatedConcordance",
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
        "CalculatedBestAge",
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

view_attributes_dict = {
    'SampleView': [
        f"{qsample_id}", f"{qigsn}", f"{qsample_name}", f"{qsample_description}", f"{qgps}", f"{qsample_elev}", f"{qsample_age}",
        f"{qsample_age_constraint}", f"{qsample_age_interpretation}", f"{qsample_age_references}", f"{qcolumn_name}", f"{qcolumn_data}",
        f"{qage_signature}", f"{qregions}", f"{qrock_types}", f"{qsample_context}", f"{qsampling_methods}", f"{qsettings}",
        f"{qunits}", f"{qaliquots}", f"{qaliquot_contexts}", f"{qspot_count}", f"{qspot_compositions}", f"{qspot_contexts}",
        f"{qupb_count}", f"{qupb_lab_facilities}", f"{qupb_analysis_methods}", f"{qupb_ratio_error_formats}", f"{qupb_age_units}",
        f"{qupb_age_error_formats}", f"{qconcordance_formats}", f"{qspot_sizes}", f"{qupb_rejection_reasons}", f"{qupb_references}",
        f"{qsample_created}", f"{qsample_modified}"
        ],
    'ColumnView': [
        f"{qcolumn_id}", f"{qcolumn_name}", f"{qcolumn_calc_total_height_depth}", f"{qcolumn_gps}",
        f"{qcolumn_description}", f"{qcolumn_created}", f"{qcolumn_modified}"
    ],
    'ColumnEditView': [
        f"{qcolumn_id}", f"{qcolumn_name}", f"{qcolumn_total_height_depth}", f"{qcolumn_total_height_depth_unit}",
        f"{qcolumn_gps_display}", f"{qcolumn_description}", f"{qcolumn_created}", f"{qcolumn_modified}"
    ],
    'AliquotView': [
        f"{qaliquot_id}", f"{qaliquot_parent_id}", f"{qaliquot_parent_row}", f"{qaliquot}", f"{qaliquot_sample}",
        f"{qaliquot_contexts}", f"{qspot_count}", f"{qspot_compositions}", f"{qspot_contexts}", f"{qupb_count}",
        f"{qupb_lab_facilities}", f"{qupb_analysis_methods}", f"{qupb_ratio_error_formats}", f"{qupb_age_units}",
        f"{qupb_age_error_formats}", f"{qconcordance_formats}", f"{qspot_sizes}", f"{qupb_rejection_reasons}",
        f"{qupb_references}", f"{qaliquot_created}", f"{qaliquot_modified}"
    ],
    'SpotView': [
        f"{qspot_id}", f"{qspots}", f"{qsample_name}", f"{qaliquot}", f"{qspot_compositions}", f"{qspot_contexts}",
        f"{qupb_count}", f"{qupb_lab_facilities}", f"{qupb_analysis_methods}", f"{qupb_ratio_error_formats}",
        f"{qupb_age_units}", f"{qupb_age_error_formats}", f"{qconcordance_formats}", f"{qspot_sizes}", f"{qupb_rejection_reasons}",
        f"{qupb_references}", f"{qspot_created}", f"{qspot_modified}"
    ],
    'UPbAnalysisView': [
        f"{qupb_id}", f"{qspot}", f"{qaliquot}", f"{qsample_name}", f"{qupb_references}", f"{qupb_lab_facilities}",
        f"{qupb_instruments}", f"{qupb_analysis_methods}", 'UPbAnalyses."Pb204cps"', 'UPbAnalyses."Pb206cps"',
        'UPbAnalyses."Pb207cps"', 'UPbAnalyses."Pb208cps"', 'UPbAnalyses."Pb*cps"', 'UPbAnalyses."Th232cps"',
        'UPbAnalyses."U235cps"', 'UPbAnalyses."U238cps"', 'UPbAnalyses."Uppm"', 'UPbAnalyses."Thppm"',
        'UPbAnalyses."CalculatedU/Th"', 'UPbAnalyses."CalculatedTh/U"',
        'UPbAnalyses."Calculated206Pb/207Pb"', 'UPbAnalyses."Calculated206Pb/207PbError"',
        'UPbAnalyses."Calculated207Pb/206Pb"', 'UPbAnalyses."Calculated207Pb/206PbError"',
        'UPbAnalyses."Calculated207Pb/235U"', 'UPbAnalyses."Calculated207Pb/235UError"',
        'UPbAnalyses."Calculated235U/207Pb"', 'UPbAnalyses."Calculated235U/207PbError"',
        'UPbAnalyses."Calculated206Pb/238U"', 'UPbAnalyses."Calculated206Pb/238UError"',
        'UPbAnalyses."Calculated238U/206Pb"', 'UPbAnalyses."Calculated238U/206PbError"',
        'UPbAnalyses."Calculated208Pb/232Th"', 'UPbAnalyses."Calculated208Pb/232ThError"',
        'UPbAnalyses."Calculated232Th/208Pb"', 'UPbAnalyses."Calculated232Th/208PbError"',
        'UPbAnalyses."Calculated238U/232Th"', 'UPbAnalyses."Calculated238U/232ThError"',
        'UPbAnalyses."Calculated232Th/238U"', 'UPbAnalyses."Calculated232Th/238UError"',
        'UPbAnalyses."Calculated204Pb/238U"', 'UPbAnalyses."Calculated204Pb/238UError"',
        'UPbAnalyses."Calculated238U/204Pb"', 'UPbAnalyses."Calculated238U/204PbError"',
        'UPbAnalyses."Calculated206Pb/204Pb"', 'UPbAnalyses."Calculated206Pb/204PbError"',
        'UPbAnalyses."Calculated204Pb/206Pb"', 'UPbAnalyses."Calculated204Pb/206PbError"',
        'UPbAnalyses."Calculated207Pb/204Pb"', 'UPbAnalyses."Calculated207Pb/204PbError"',
        'UPbAnalyses."Calculated204Pb/207Pb"', 'UPbAnalyses."Calculated204Pb/207PbError"',
        'UPbAnalyses."Calculated208Pb/204Pb"', 'UPbAnalyses."Calculated208Pb/204PbError"',
        'UPbAnalyses."Calculated204Pb/208Pb"', 'UPbAnalyses."Calculated204Pb/208PbError"', 'UPbAnalyses."ErrorCorr/Rho"',
        'UPbAnalyses."Calculated207Pb/206PbAge"', 'UPbAnalyses."Calculated207Pb/206PbAgeError"',
        'UPbAnalyses."Calculated206Pb/238UAge"', 'UPbAnalyses."Calculated206Pb/238UAgeError"',
        'UPbAnalyses."Calculated207Pb/235UAge"', 'UPbAnalyses."Calculated207Pb/235UAgeError"',
        'UPbAnalyses."Calculated208Pb/232ThAge"', 'UPbAnalyses."Calculated208Pb/232ThAgeError"',
        'UPbAnalyses."CalculatedBestAge"', 'UPbAnalyses."CalculatedBestAgeError"', 'UPbAnalyses."CalculatedSpotSize"',
        'UPbAnalyses."CalculatedConcordance"', f"{qupb_rejection_reasons}", f"{qupb_created}", f"{qupb_modified}"
    ]
}


upb_possible_database_input_fields = [
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
    'RatioErrorFormatID',
    '207Pb/206PbAge', '207Pb/206PbAgeError',
    '207Pb/235UAge', '207Pb/235UAgeError',
    '206Pb/238UAge', '206Pb/238UAgeError',
    '208Pb/232ThAge', '208Pb/232ThAgeError',
    'BestAge', 'BestAgeError',

    'AgeErrorFormatID',
    'AgeUnitID',
    'Concordance', 'ConcordanceFormatID',
    'SpotSize', 'SpotSizeUnitID',
    'Rejected',

    'ReferenceID',
    'LabFacilityID',
    'InstrumentID',
    'UPbAnalysisMethodID'
]

upb_possible_user_input_fields = {
    'Base Info': [
        'Sample Name',
        'Aliquot Name',
        'Spot Name',
        'Reference Display',
        'Lab Facility Name',
        'Instrument Name',
        'UPb Analysis Method Name',
        'Rejection Reason',
        'Spot Size'
    ],
    'Ratios': [
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

        'ErrorCorr/Rho'

    ],
    'Age Ratios': [
        '207Pb/206PbAge', '207Pb/206PbAgeError',
        '207Pb/235UAge', '207Pb/235UAgeError',
        '206Pb/238UAge', '206Pb/238UAgeError',
        '208Pb/232ThAge', '208Pb/232ThAgeError',
        'BestAge', 'BestAgeError',
        'Concordance'
    ],
    'Isotope Counts': [
        'Pb204cps', 'Pb206cps', 'Pb207cps', 'Pb208cps', 'Pb*cps', 'Th232cps', 'U235cps', 'U238cps',
        'Uppm', 'Thppm'
    ]
}


def get_join_from_table(tables: list[str]) -> str:
    join = ""

    for table in tables:
        match table:
            case 'AgeConstraints':
                continue
                if default_sample_age_join not in join:
                    join += default_sample_age_join + '\n'
                if age_constraint_join not in join:
                    join += age_constraint_join + '\n'
            case 'AgeInterpretations':
                continue
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
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
            case 'AliquotContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_context_join not in join:
                    join += aliquot_context_join + '\n'
            case 'Columns':
                if column_join not in join:
                    join += column_join + '\n'
            case 'LabFacilities':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_labs_join not in join:
                    join += upb_labs_join + '\n'
            case 'Instruments':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_instruments_join not in join:
                    join += upb_instruments_join + '\n'
            case 'References':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'Regions':
                if region_join not in join:
                    join += region_join + '\n'
            case 'RejectionReasons':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
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
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
            case 'SpotCompositions':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_composition_join not in join:
                    join += spot_composition_join + '\n'
            case 'SpotContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_context_join not in join:
                    join += spot_context_join + '\n'
            case 'UPbAnalyses':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
            case 'UPbAnalysisMethods':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_method_join not in join:
                    join += upb_method_join + '\n'
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'
            case 'Samples':
                pass
    return join