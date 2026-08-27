# ID columns
qsample_id = 'Samples.SampleID AS SampleID'
qaliquot_id = 'Aliquots.AliquotID AS AliquotID'
qgrain_id = 'Grains.GrainID AS GrainID'
qspot_id = 'Spots.SpotID AS SpotID'
qupb_id = 'UPbAnalyses.UPbAnalysisID AS UPbAnalysisID'
qcolumn_id = 'Columns.ColumnID AS ColumnID'
qreference_id = '"References".ReferenceID AS ReferenceID'


# Sample view columns
qsample_name = 'Samples.SampleName AS SampleName'
qigsn = 'Samples.SampleIGSN AS SampleIGSN'
qgps = 'SampleGPS.GPSLocationConverted AS GPSSampleLocationCalculated'
qgps_display = 'SampleGPS.GPSLocationDisplay AS SampleGPSLocationDisplay'
qsample_gps_id = 'Samples.SampleGPSLocationID AS SampleGPSLocationID'
qsample_elev = 'NULLIF(COALESCE(SampleGPS.CalculatedGPSElev, "") || "±" || COALESCE(SampleGPS.CalculatedGPSElevError, ""), "±") AS SampleElevationCalculated'
qsample_elev_display = 'NULLIF(COALESCE(SampleGPS.GPSElev, "") || "±" || COALESCE(SampleGPS.GPSElevError, "") || " (" || COALESCE(SampleElevationUnits.DistanceUnitAbbreviation, "") || ")", " ") AS SampleElevation'
qsample_elev_unit = 'SampleElevationUnits.DistanceUnitAbbreviation AS SampleElevationUnitAbbreviation'
qsample_column_data = 'NULLIF(COALESCE(Samples.CalculatedHeightDepth, "") || "±" || COALESCE(Samples.CalculatedHeightDepthError, ""), "±") AS ColumnHeightDepthCalculated'
qsample_column_data_display = 'NULLIF(COALESCE(Samples.HeightDepth, "") || "±" || COALESCE(Samples.HeightDepthError, "") || " (" || COALESCE(ColumnHeightDepthUnits.DistanceUnitAbbreviation, "") || ")", "±") AS ColumnHeightDepth'
qsample_column_height_depth = 'Samples.HeightDepth AS ColumnHeightDepth'
qsample_column_height_depth_error = 'Samples.HeightDepthError AS ColumnHeightDepthError'
qsample_column_data_unit = 'ColumnHeightDepthUnits.DistanceUnitAbbreviation AS ColumnHeightDepthUnitAbbreviation'
qsample_age = 'SampleAges.SampleAgeConverted AS SampleAgeCalculated'
qsample_age_display = 'SampleAges.SampleAgeDisplay AS SampleAgeDisplay'
qsample_age_unit = 'SampleAgeUnits.AgeUnitAbbreviation AS SampleAgeUnitAbbreviation'
qsample_age_error_format = 'DirectAgeErrorFormats.ErrorFormatAbbreviation AS DirectAgeErrorFormatAbbreviation'
qsample_age_constraints = 'SampleAgeConstraints.AgeConstraintName AS SampleAgeConstraintName'
qsample_age_interpretations = 'SampleAgeInterpretations.AgeInterpretationName AS SampleAgeInterpretationName'
qsample_age_references = 'SampleAgeReferences.ReferenceDisplay AS SampleAgeReferenceDisplay'
qsample_description = 'Samples.SampleDescription AS SampleDescription'
qage_signatures = 'AgeSignatures.AgeSignatureName SampleAgeSignatureName'
qregions = 'Regions.RegionName AS RegionName'
qrock_types = 'RockTypes.RockTypeName RockTypeName'
qsample_contexts = 'SampleContexts.SampleContextName AS SampleContextName'
qsampling_methods = 'SamplingMethods.SamplingMethodName AS SamplingMethodName'
qsettings = 'Settings.SettingName AS SettingName'
qunits = 'Units.UnitName AS UnitName'
qsample_created = 'Samples.SampleCreated AS SampleCreated'
qsample_modified = 'Samples.SampleModified AS SampleModified'

#Columns, skip null values
qcolumn_name = 'Columns.ColumnName AS ColumnName'
qcolumn_names = 'REPLACE(GROUP_CONCAT(DISTINCT Columns.ColumnName), ",", "; ") AS ColumnName'
qcolumn_data = f'NULLIF(COALESCE(Columns.CalculatedHeightDepth, "") || "±" || COALESCE(Columns.CalculatedHeightDepthError, ""), "±") AS ColumnHeightDepth'
qcolumn_data_display = f'NULLIF(COALESCE(Columns.HeightDepth, "") || "±" || COALESCE(Columns.HeightDepthError, ""), "±") AS ColumnHeightDepth'
qcolumn_gps = f'ColumnGPS.GPSLocationConverted AS ColumnGPSLocationCalculated'
qcolumn_gps_display = 'ColumnGPS.GPSLocationDisplay AS ColumnGPSLocationDisplay'
qcolumn_gps_id = 'Columns.ColumnBaseGPSID AS ColumnGPSLocationID'
qcolumn_calc_total_height_depth = f'Columns.CalculatedColumnTotalHeightDepth AS ColumnTotalHeightDepthCalculated'
qcolumn_total_height_depth = f'Columns.ColumnTotalHeightDepth AS ColumnTotalHeightDepth'
qcolumn_total_height_depth_unit = f'ColumnUnits.DistanceUnitAbbreviation AS ColumnTotalHeightDepthUnitAbbreviation'
qcolumn_elev = 'NULLIF(COALESCE(ColumnGPS.CalculatedGPSElev, "") || "±" || COALESCE(ColumnGPS.CalculatedGPSElevError, ""), "±") AS ColumnElevationCalculated'
qcolumn_elev_display = 'NULLIF(COALESCE(ColumnGPS.GPSElev, "") || "±" || COALESCE(ColumnGPS.GPSElevError, "") || " (" || COALESCE(ColumnElevationUnits.DistanceUnitAbbreviation, "") || ")", "±") AS ColumnElevation'
qcolumn_elev_unit = 'ColumnElevationUnits.DistanceUnitAbbreviation AS ColumnElevationUnitAbbreviation'
qcolumn_description = 'Columns.ColumnDescription AS ColumnDescription'
qcolumn_created = 'Columns.ColumnCreated AS ColumnCreated'
qcolumn_modified = 'Columns.ColumnModified AS ColumnModified'

# Aliquot view columns
qaliquot_count = 'COUNT(DISTINCT Aliquots.AliquotID) AS AliquotCount'
qaliquot_name = 'Aliquots.AliquotName AS AliquotName'
qaliquots = 'REPLACE(GROUP_CONCAT(DISTINCT Aliquots.AliquotName), ",", "; ") AS AliquotName'
qaliquot_parent_id = 'Aliquots.ParentAliquotID AS ParentAliquotID'
qaliquot_parent_row = 'Aliquots.AliquotParentRow AS AliquotParentRow'
qaliquot_sample = 'Samples.SampleName AS SampleName'
qaliquot_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT AliquotContexts.AliquotContextName), ",", "; ") AS AliquotContextName'
qaliquot_spots = 'REPLACE(GROUP_CONCAT(DISTINCT Spots.SpotName), ",", "; ") AS SpotName'
qaliquot_spot_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT SpotContexts.SpotContexts.SpotContextName), ",", "; ") AS SpotContextName'
qaliquot_spot_compositions = 'REPLACE(GROUP_CONCAT(DISTINCT SpotCompositions.SpotCompositionName), ",", "; ") AS SpotCompositionName'
qaliquot_references = 'REPLACE(GROUP_CONCAT(DISTINCT ReferenceDisplay), ",", "; ") AS UPbReference'
qaliquot_upb_methods = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalysisMethods.UPbAnalysisMethodName), ",", "; ") AS UPbAnalysisMethodName'
qaliquot_upb_labs = 'REPLACE(GROUP_CONCAT(DISTINCT UPbLabFacilities.LabFacilityName), ",", "; ") AS UPbLabFacilityName'
qaliquot_description = 'Aliquots.AliquotDescription AS AliquotDescription'
qaliquot_created = 'Aliquots.AliquotCreated AS AliquotCreated'
qaliquot_modified = 'Aliquots.AliquotModified AS AliquotModified'

# Grain view columns
qgrain_count = 'COUNT(DISTINCT Grains.GrainID) AS GrainCount'
qgrain_name = 'Grains.GrainName AS GrainName'
qgrains = 'REPLACE(GROUP_CONCAT(DISTINCT Grains.GrainName), ",", "; ") AS GrainName'
qgrain_composition = 'GrainCompositions.GrainCompositionName AS GrainCompositionName'
qgrain_compositions = 'REPLACE(GROUP_CONCAT(DISTINCT GrainCompositions.GrainCompositionName), ",", "; ") AS GrainCompositionName'
qgrain_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT GrainContexts.GrainContextName), ",", "; ") AS GrainContextName'
qgrain_description = 'Grains.GrainDescription AS GrainDescription'
qgrain_created = 'Grains.GrainCreated AS GrainCreated'
qgrain_modified = 'Grains.GrainModified AS GrainModified'

# Spot view columns
qspot_count = 'COUNT(DISTINCT Spots.SpotID) AS SpotCount'
qspot_name = 'Spots.SpotName AS SpotName'
qspots = 'REPLACE(GROUP_CONCAT(DISTINCT Spots.SpotName), ",", "; ") AS SpotName'
qspot_composition = 'SpotCompositions.SpotCompositionName AS SpotCompositionName'
qspot_compositions = 'REPLACE(GROUP_CONCAT(DISTINCT SpotCompositions.SpotCompositionName), ",", "; ") AS SpotCompositionName'
qspot_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT SpotContexts.SpotContextName), ",", "; ") AS SpotContextName'
qspot_description = 'Spots.SpotDescription AS SpotDescription'
qspot_created = 'Spots.SpotCreated AS SpotCreated'
qspot_modified = 'Spots.SpotModified AS SpotModified'

# UPb view columns
qupb_analyses = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalyses.UPbAnalysisName), ",", "; ") AS UPbAnalyses'
qupb_analysis_name = 'UPbAnalyses.UPbAnalysisName AS UPbAnalysisName'
qupb_analysis_description = 'UPbAnalyses.UPbAnalysisDescription AS UPbAnalysisDescription'
qupb_count = 'DistinctUPbAnalyses.AcceptedTotalUPbAnalyses AS "Accepted/TotalUPbAnalyses"'
qupb_count_sample_subquery = f'''
DistinctUPbAnalyses AS 
(
    SELECT 
    lsa.SampleID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM LimitedSamplesAliquots lsa
    INNER JOIN Spots ON lsa.AliquotID = Spots.AliquotID
    INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
    GROUP BY lsa.SampleID
)
'''
qupb_count_aliquot_subquery = f'''
DistinctUPbAnalyses AS 
(
    SELECT
    lsa.AliquotID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM LimitedSamplesAliquots lsa
    INNER JOIN Spots ON lsa.AliquotID = Spots.AliquotID
    INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
    GROUP BY lsa.AliquotID
)
'''
qupb_count_grain_subquery = f'''
DistinctUPbAnalyses AS 
(
    SELECT
    lspag.GrainID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM LimitedSpotsAnalysesGrains lspag
    INNER JOIN UPbAnalyses ON lspag.SpotID = UPbAnalyses.SpotID
    GROUP BY lspag.GrainID
)
'''
qupb_count_spot_subquery = f'''
DistinctUPbAnalyses AS 
(
    SELECT
    lspag.SpotID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM LimitedSpotsAnalysesGrains lspag
    INNER JOIN UPbAnalyses ON lspag.SpotID = UPbAnalyses.SpotID
    GROUP BY lspag.SpotID
)
'''
qupb_references = 'REPLACE(GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay), ",", "; ") AS UPbReference'
qupb_reference = 'UPbReferences.ReferenceDisplay AS UPbReference'
qupb_lab_facilities = 'REPLACE(GROUP_CONCAT(DISTINCT UPbLabFacilities.LabFacilityName), ",", "; ") AS UPbLabFacilityName'
qupb_lab_facility = 'UPbLabFacilities.LabFacilityName AS UPbLabFacilityName'
qupb_instruments = 'REPLACE(GROUP_CONCAT(DISTINCT UPbInstruments.InstrumentName), ",", "; ") AS UPbInstrumentName'
qupb_instrument = 'UPbInstruments.InstrumentName AS UPbInstrumentName'
qupb_analysis_methods = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalysisMethods.UPbAnalysisMethodName), ",", "; ") AS UPbAnalysisMethodName'
qupb_analysis_method = 'UPbAnalysisMethods.UPbAnalysisMethodName AS UPbAnalysisMethodName'
qupb_204cps = 'UPbAnalyses."Pb204cps" AS "Pb204cps"'
qupb_206cps = 'UPbAnalyses."Pb206cps" AS "Pb206cps"'
qupb_207cps = 'UPbAnalyses."Pb207cps" AS "Pb207cps"'
qupb_208cps = 'UPbAnalyses."Pb208cps" AS "Pb208cps"'
qupb_pbcps = 'UPbAnalyses."Pb*cps" AS "Pb*cps"'
qupb_232cps = 'UPbAnalyses."Th232cps" AS "Th232cps"'
qupb_235cps = 'UPbAnalyses."U235cps" AS "U235cps"'
qupb_238cps = 'UPbAnalyses."U238cps" AS "U238cps"'
qupb_uppm = 'UPbAnalyses."Uppm" AS "Uppm"'
qupb_thppm = 'UPbAnalyses."Thppm" AS "Thppm"'
qupb_pbppm = 'UPbAnalyses."Pbppm" AS "Pbppm"'
qupb_uth = 'UPbAnalyses."U/Th" AS "U/Th"'
qupb_thu = 'UPbAnalyses."Th/U" AS "Th/U"'
qupb_calc_uth = 'UPbAnalyses."CalculatedU/Th" AS "CalculatedU/Th"'
qupb_calc_thu = 'UPbAnalyses."CalculatedTh/U" AS "CalculatedTh/U"'
qupb_206207 = 'UPbAnalyses."206Pb/207Pb" AS "206Pb/207Pb"'
qupb_206207_error = 'UPbAnalyses."206Pb/207PbError" AS "206Pb/207PbError"'
qupb_calc_206207 = 'UPbAnalyses."Calculated206Pb/207Pb" AS "Calculated206Pb/207Pb"'
qupb_calc_206207_error = 'UPbAnalyses."Calculated206Pb/207PbError" AS "Calculated206Pb/207PbError"'
qupb_207206 = 'UPbAnalyses."207Pb/206Pb" AS "207Pb/206Pb"'
qupb_207206_error = 'UPbAnalyses."207Pb/206PbError" AS "207Pb/206PbError"'
qupb_calc_207206 = 'UPbAnalyses."Calculated207Pb/206Pb" AS "Calculated207Pb/206Pb"'
qupb_calc_207206_error = 'UPbAnalyses."Calculated207Pb/206PbError" AS "Calculated207Pb/206PbError"'
qupb_207235 = 'UPbAnalyses."207Pb/235U" AS "207Pb/235U"'
qupb_207235_error = 'UPbAnalyses."207Pb/235UError" AS "207Pb/235UError"'
qupb_calc_207235 = 'UPbAnalyses."Calculated207Pb/235U" AS "Calculated207Pb/235U"'
qupb_calc_207235_error = 'UPbAnalyses."Calculated207Pb/235UError" AS "Calculated207Pb/235UError"'
qupb_235207 = 'UPbAnalyses."235U/207Pb" AS "235U/207Pb"'
qupb_235207_error = 'UPbAnalyses."235U/207PbError" AS "235U/207PbError"'
qupb_calc_235207 = 'UPbAnalyses."Calculated235U/207Pb" AS "Calculated235U/207Pb"'
qupb_calc_235207_error = 'UPbAnalyses."Calculated235U/207PbError" AS "Calculated235U/207PbError"'
qupb_206238 = 'UPbAnalyses."206Pb/238U" AS "206Pb/238U"'
qupb_206238_error = 'UPbAnalyses."206Pb/238UError" AS "206Pb/238UError"'
qupb_calc_206238 = 'UPbAnalyses."Calculated206Pb/238U" AS "Calculated206Pb/238U"'
qupb_calc_206238_error = 'UPbAnalyses."Calculated206Pb/238UError" AS "Calculated206Pb/238UError"'
qupb_238206 = 'UPbAnalyses."238U/206Pb" AS "238U/206Pb"'
qupb_238206_error = 'UPbAnalyses."238U/206PbError" AS "238U/206PbError"'
qupb_calc_238206 = 'UPbAnalyses."Calculated238U/206Pb" AS "Calculated238U/206Pb"'
qupb_calc_238206_error = 'UPbAnalyses."Calculated238U/206PbError" AS "Calculated238U/206PbError"'
qupb_208232 = 'UPbAnalyses."208Pb/232Th" AS "208Pb/232Th"'
qupb_208232_error = 'UPbAnalyses."208Pb/232ThError" AS "208Pb/232ThError"'
qupb_calc_208232 = 'UPbAnalyses."Calculated208Pb/232Th" AS "Calculated208Pb/232Th"'
qupb_calc_208232_error = 'UPbAnalyses."Calculated208Pb/232ThError" AS "Calculated208Pb/232ThError"'
qupb_232208 = 'UPbAnalyses."232Th/208Pb" AS "232Th/208Pb"'
qupb_232208_error = 'UPbAnalyses."232Th/208PbError" AS "232Th/208PbError"'
qupb_calc_232208 = 'UPbAnalyses."Calculated232Th/208Pb" AS "Calculated232Th/208Pb"'
qupb_calc_232208_error = 'UPbAnalyses."Calculated232Th/208PbError" AS "Calculated232Th/208PbError"'
qupb_238232 = 'UPbAnalyses."238U/232Th" AS "238U/232Th"'
qupb_238232_error = 'UPbAnalyses."238U/232ThError" AS "238U/232ThError"'
qupb_calc_238232 = 'UPbAnalyses."Calculated238U/232Th" AS "Calculated238U/232Th"'
qupb_calc_238232_error = 'UPbAnalyses."Calculated238U/232ThError" AS "Calculated238U/232ThError"'
qupb_232238 = 'UPbAnalyses."232Th/238U" AS "232Th/238U"'
qupb_232238_error = 'UPbAnalyses."232Th/238UError" AS "232Th/238UError"'
qupb_calc_232238 = 'UPbAnalyses."Calculated232Th/238U" AS "Calculated232Th/238U"'
qupb_calc_232238_error = 'UPbAnalyses."Calculated232Th/238UError" AS "Calculated232Th/238UError"'
qupb_204238 = 'UPbAnalyses."204Pb/238U" AS "204Pb/238U"'
qupb_204238_error = 'UPbAnalyses."204Pb/238UError" AS "204Pb/238UError"'
qupb_calc_204238 = 'UPbAnalyses."Calculated204Pb/238U" AS "Calculated204Pb/238U"'
qupb_calc_204238_error = 'UPbAnalyses."Calculated204Pb/238UError" AS "Calculated204Pb/238UError"'
qupb_238204 = 'UPbAnalyses."238U/204Pb" AS "238U/204Pb"'
qupb_238204_error = 'UPbAnalyses."238U/204PbError" AS "238U/204PbError"'
qupb_calc_238204 = 'UPbAnalyses."Calculated238U/204Pb" AS "Calculated238U/204Pb"'
qupb_calc_238204_error = 'UPbAnalyses."Calculated238U/204PbError" AS "Calculated238U/204PbError"'
qupb_206204 = 'UPbAnalyses."206Pb/204Pb" AS "206Pb/204Pb"'
qupb_206204_error = 'UPbAnalyses."206Pb/204PbError" AS "206Pb/204PbError"'
qupb_calc_206204 = 'UPbAnalyses."Calculated206Pb/204Pb" AS "Calculated206Pb/204Pb"'
qupb_calc_206204_error = 'UPbAnalyses."Calculated206Pb/204PbError" AS "Calculated206Pb/204PbError"'
qupb_204206 = 'UPbAnalyses."204Pb/206Pb" AS "204Pb/206Pb"'
qupb_204206_error = 'UPbAnalyses."204Pb/206PbError" AS "204Pb/206PbError"'
qupb_calc_204206 = 'UPbAnalyses."Calculated204Pb/206Pb" AS "Calculated204Pb/206Pb"'
qupb_calc_204206_error = 'UPbAnalyses."Calculated204Pb/206PbError" AS "Calculated204Pb/206Pb"'
qupb_207204 = 'UPbAnalyses."207Pb/204Pb" AS "207Pb/204Pb"'
qupb_207204_error = 'UPbAnalyses."207Pb/204PbError" AS "207Pb/204PbError"'
qupb_calc_207204 = 'UPbAnalyses."Calculated207Pb/204Pb" AS "Calculated207Pb/204Pb"'
qupb_calc_207204_error = 'UPbAnalyses."Calculated207Pb/204PbError" AS "Calculated207Pb/204Pb"'
qupb_204207 = 'UPbAnalyses."204Pb/207Pb" AS "204Pb/207Pb"'
qupb_204207_error = 'UPbAnalyses."204Pb/207PbError" AS "204Pb/207PbError"'
qupb_calc_204207 = 'UPbAnalyses."Calculated204Pb/207Pb" AS "Calculated204Pb/207Pb"'
qupb_calc_204207_error = 'UPbAnalyses."Calculated204Pb/207PbError" AS "Calculated204Pb/207Pb"'
qupb_208204 = 'UPbAnalyses."208Pb/204Pb" AS "208Pb/204Pb"'
qupb_208204_error = 'UPbAnalyses."208Pb/204PbError" AS "208Pb/204PbError"'
qupb_calc_208204 = 'UPbAnalyses."Calculated208Pb/204Pb" AS "Calculated208Pb/204Pb"'
qupb_calc_208204_error = 'UPbAnalyses."Calculated208Pb/204PbError" AS "Calculated208Pb/204Pb"'
qupb_204208 = 'UPbAnalyses."204Pb/208Pb" AS "204Pb/208Pb"'
qupb_204208_error = 'UPbAnalyses."204Pb/208PbError" AS "204Pb/208PbError"'
qupb_calc_204208 = 'UPbAnalyses."Calculated204Pb/208Pb" AS "Calculated204Pb/208Pb"'
qupb_calc_204208_error = 'UPbAnalyses."Calculated204Pb/208PbError" AS "Calculated204Pb/208Pb"'
qupb_ratio_error_formats = 'REPLACE(GROUP_CONCAT(DISTINCT UPbRatioErrorFormats.ErrorFormatAbbreviation), ",", "; ") AS UPbRatioErrorFormatAbbreviation'
qupb_ratio_error_format = 'UPbRatioErrorFormats.ErrorFormatAbbreviation AS UPbRatioErrorFormatAbbreviation'
qupb_207206_age = 'UPbAnalyses."207Pb/206PbAge" AS "207Pb/206PbAge"'
qupb_207206_age_error = 'UPbAnalyses."207Pb/206PbAgeError" AS "207Pb/206PbAgeError"'
qupb_calc_207206_age = 'UPbAnalyses."Calculated207Pb/206PbAge" AS "Calculated207Pb/206PbAge"'
qupb_calc_207206_age_error = 'UPbAnalyses."Calculated207Pb/206PbAgeError" AS "Calculated207Pb/206PbAgeError"'
qupb_207235_age = 'UPbAnalyses."207Pb/235UAge" AS "207Pb/235UAge"'
qupb_207235_age_error = 'UPbAnalyses."207Pb/235UAgeError" AS "207Pb/235UAgeError"'
qupb_calc_207235_age = 'UPbAnalyses."Calculated207Pb/235UAge" AS "Calculated207Pb/235UAge"'
qupb_calc_207235_age_error = 'UPbAnalyses."Calculated207Pb/235UAgeError" AS "Calculated207Pb/235UAgeError"'
qupb_206238_age = 'UPbAnalyses."206Pb/238UAge" AS "206Pb/238UAge"'
qupb_206238_age_error = 'UPbAnalyses."206Pb/238UAgeError" AS "206Pb/238UAgeError"'
qupb_calc_206238_age = 'UPbAnalyses."Calculated206Pb/238UAge" AS "Calculated206Pb/238UAge"'
qupb_calc_206238_age_error = 'UPbAnalyses."Calculated206Pb/238UAgeError" AS "Calculated206Pb/238UAgeError"'
qupb_208232_age = 'UPbAnalyses."208Pb/232ThAge" AS "208Pb/232ThAge"'
qupb_208232_age_error = 'UPbAnalyses."208Pb/232ThAgeError" AS "208Pb/232ThAgeError"'
qupb_calc_208232_age = 'UPbAnalyses."Calculated208Pb/232ThAge" AS "Calculated208Pb/232ThAge"'
qupb_calc_208232_age_error = 'UPbAnalyses."Calculated208Pb/232ThAgeError" AS "Calculated208Pb/232ThAgeError"'
qupb_best_age = 'UPbAnalyses.BestAge AS BestAge'
qupb_best_age_error = 'UPbAnalyses.BestAgeError AS BestAgeError'
qupb_best_age_filled = 'UPbAnalyses.BestAgeFilled AS BestAgeFilled'
qupb_best_age_filled_error = 'UPbAnalyses.BestAgeErrorFilled AS BestAgeErrorFilled'
qupb_calc_best_age = 'UPbAnalyses."CalculatedBestAge" AS "CalculatedBestAge"'
qupb_calc_best_age_error = 'UPbAnalyses."CalculatedBestAgeError" AS "CalculatedBestAgeError"'
qupb_calc_best_age_filled = 'UPbAnalyses.CalculatedBestAgeFilled AS CalculatedBestAgeFilled'
qupb_calc_best_age_filled_error = 'UPbAnalyses.CalculatedBestAgeErrorFilled AS CalculatedBestAgeErrorFilled'
qupb_age_error_formats = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAgeErrorFormats.ErrorFormatAbbreviation), ",", "; ") AS UPbAgeErrorFormatAbbreviation'
qupb_age_error_format = 'UPbAgeErrorFormats.ErrorFormatAbbreviation AS UPbAgeErrorFormatAbbreviation'
qupb_age_units = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation), ",", "; ") AS UPbAgeUnitAbbreviation'
qupb_age_unit = 'UPbAgeUnits.AgeUnitAbbreviation AS UPbAgeUnitAbbreviation'
qupb_age_interpretations = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAgeInterpretations.AgeInterpretationName), ",", "; ") AS UPbAgeInterpretationName'
qupb_age_interpretation = 'UPbAgeInterpretations.AgeInterpretationName AS UPbAgeInterpretationName'
qupb_concordance_68v76 = 'UPbAnalyses."CalculatedConcordance_206Pb/238Uv207Pb/206Pb" AS "Concordance_206Pb/238Uv207Pb/206Pb"'
qupb_error_corr_68v76 = 'UPbAnalyses."ErrorCorr/Rho_68v76" AS "ErrorCorr/Rho_68v76"'
qupb_concordance_68v75 = 'UPbAnalyses."CalculatedConcordance_206Pb/238Uv207Pb/235U" AS "Concordance_206Pb/238Uv207Pb/235U"'
qupb_error_corr_68v75 = 'UPbAnalyses."ErrorCorr/Rho_68v75" AS "ErrorCorr/Rho_68v75"'
qupb_calc_concordance_68v76 = 'UPbAnalyses."CalculatedConcordance_206Pb/238Uv207Pb/206Pb" AS "Concordance_206Pb/238Uv207Pb/206Pb"'
qupb_calc_concordance_68v75 = 'UPbAnalyses."CalculatedConcordance_206Pb/238Uv207Pb/235U" AS "Concordance_206Pb/238Uv207Pb/235U"'
qupb_concordance_formats = 'REPLACE(GROUP_CONCAT(DISTINCT UPbConcordanceFormats.ConcordanceFormatAbbreviation), ",", "; ") AS UPbConcordanceFormatAbbreviation'
qupb_concordance_format = 'UPbConcordanceFormats.ConcordanceFormatAbbreviation AS UPbConcordanceFormatAbbreviation'
qupb_minsegdisc = 'UPbAnalyses.MinimumSegmentedDiscordance AS MinimumSegmentedDiscordance'
qupb_spot_size = 'UPbAnalyses.SpotSize AS UPbSpotSize'
qupb_calc_spot_size = 'UPbAnalyses.CalculatedSpotSize AS CalculatedUPbSpotSize'
qupb_spot_sizes = f'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalyses.CalculatedSpotSize), ",", "; ") AS CalculatedUPbSpotSize'
qupb_spot_size_units = 'REPLACE(GROUP_CONCAT(DISTINCT UPbSpotSizeUnits.DistanceUnitAbbreviation), ",", "; ") AS UPbSpotSizeUnitAbbreviation'
qupb_spot_size_unit = 'UPbSpotSizeUnits.DistanceUnitAbbreviation AS UPbSpotSizeUnitAbbreviation'
rejected_text = "'Rejected'"
accepted_text = "'Accepted'"
qupb_rejected = f'(CASE WHEN UPbAnalyses.Rejected = 1 THEN {rejected_text} ELSE {accepted_text} END) AS Rejected'
qupb_rejection_reasons = 'REPLACE(GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName), ",", "; ") AS UPbRejectionReasonName'
qupb_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalysisContexts.UPbAnalysisContextName), ",", "; ") AS UPbAnalysisContextName'
qupb_created = 'UPbAnalyses.UPbAnalysisCreated AS UPbAnalysisCreated'
qupb_modified = 'UPbAnalyses.UPbAnalysisModified AS UPbAnalysisModified'

# Reference view columns
qreference_display = 'ReferenceDisplay AS ReferenceDisplay'
qauthors = 'Authors AS Authors'
qyear = 'Year AS Year'
qtitle = 'Title AS Title'
qsource = 'Source AS Source'
qdoi = 'DOI AS DOI'
qreference_description = 'ReferenceDescription AS ReferenceDescription'
qreference_created = 'ReferenceCreated AS ReferenceCreated'
qreference_modified = 'ReferenceModified AS ReferenceModified'

# GeoChemicalAnalyses view columns
qgeochem_id = 'GeoChemicalAnalyses.GeoChemAnalysisID AS GeoChemAnalysisID'
qgeochem_analysis_name = 'GeoChemicalAnalyses.GeoChemAnalysisName AS GeoChemAnalysisName'
qgeochem_analyte = 'GeoChemicalAnalytes.GeoChemAnalyteName AS GeoChemAnalyteName'
qgeochem_analyte_abbreviation = 'GeoChemicalAnalytes.GeoChemAnalyteAbbreviation AS GeoChemAnalyteAbbreviation'
qgeochem_analyte_abbreviations = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemicalAnalytes.GeoChemAnalyteAbbreviation), ",", "; ") AS GeoChemAnalyteAbbreviation'
qgeochem_analyte_value = 'GeoChemicalAnalyses.GeoChemAnalyteValue AS GeoChemAnalyteValue'
qgeochem_analyte_error = 'GeoChemicalAnalyses.GeoChemAnalyteError AS GeoChemAnalyteError'
qgeochem_analyte_unit = 'GeoChemAnalyteUnits.AnalyticalUnitAbbreviation AS GeoChemAnalyteUnitAbbreviation'
qgeochem_analyte_units = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemAnalyteUnits.AnalyticalUnitAbbreviation), ",", "; ") AS GeoChemAnalyteUnitAbbreviation'
qgeochem_analyte_error_format = 'GeoChemAnalyteErrorFormats.ErrorFormatAbbreviation AS GeoChemAnalyteErrorFormatAbbreviation'
qgeochem_analyte_error_formats = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemAnalyteErrorFormats.ErrorFormatAbbreviation), ",", "; ") AS GeoChemAnalyteErrorFormatAbbreviation'
qgeochem_lab_facility = 'GeoChemLabFacilities.LabFacilityName AS GeoChemLabFacilityName'
qgeochem_lab_facilities = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemLabFacilities.LabFacilityName), ",", "; ") AS GeoChemLabFacilityName'
qgeochem_instrument = 'GeoChemInstruments.InstrumentName AS GeoChemInstrumentName'
qgeochem_instruments = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemInstruments.InstrumentName), ",", "; ") AS GeoChemInstrumentName'
qgeochem_method = 'GeoChemicalMethods.GeoChemicalMethodName AS GeoChemicalMethodName'
qgeochem_methods = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemicalMethods.GeoChemicalMethodName), ",", "; ") AS GeoChemicalMethodName'
qgeochem_reference = 'GeoChemReferences.ReferenceDisplay AS GeoChemReference'
qgeochem_references = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemReferences.ReferenceDisplay), ",", "; ") AS GeoChemReference'
qgeochem_spot_size = 'GeoChemicalAnalyses.SpotSize AS GeoChemSpotSize'
qgeochem_calc_spot_size = 'GeoChemicalAnalyses.CalculatedSpotSize AS CalculatedGeoChemSpotSize'
qgeochem_spot_sizes = f'REPLACE(GROUP_CONCAT(DISTINCT GeoChemicalAnalyses.CalculatedSpotSize), ",", "; ") AS CalculatedGeoChemSpotSize'
qgeochem_spot_size_units = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemSpotSizeUnits.DistanceUnitAbbreviation), ",", "; ") AS GeoChemSpotSizeUnitAbbreviation'
qgeochem_spot_size_unit = 'GeoChemSpotSizeUnits.DistanceUnitAbbreviation AS GeoChemSpotSizeUnitAbbreviation'
qgeochem_rejected = f'(CASE WHEN GeoChemicalAnalyses.Rejected = 1 THEN {rejected_text} ELSE {accepted_text} END) AS Rejected'
qgeochem_rejection_reasons = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemRejectionReasons.RejectionReasonName), ",", "; ") AS GeoChemRejectionReasonName'
qgeochem_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemicalAnalysisContexts.GeoChemAnalysisContextName), ",", "; ") AS GeoChemAnalysisContextName'
qgeochem_created = 'GeoChemicalAnalyses.GeoChemAnalysisCreated AS GeoChemAnalysisCreated'
qgeochem_modified = 'GeoChemicalAnalyses.GeoChemAnalysisModified AS GeoChemAnalysisModified'
qgeochem_count = 'DistinctGeoChemicalAnalyses.AcceptedTotalGeoChemicalAnalyses AS "Accepted/TotalGeoChemicalAnalyses"'
qgeochem_count_sample_subquery = f'''
DistinctGeoChemicalAnalyses AS 
(
    SELECT 
    lsa.SampleID,
    SUM(CASE WHEN GeoChemicalAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT GeoChemicalAnalyses.GeoChemAnalysisID) AS AcceptedTotalGeoChemicalAnalyses
    FROM LimitedSamplesAliquots lsa
    INNER JOIN Spots ON lsa.AliquotID = Spots.AliquotID
    INNER JOIN GeoChemicalAnalyses ON Spots.SpotID = GeoChemicalAnalyses.SpotID
    GROUP BY lsa.SampleID
)
'''
qgeochem_count_aliquot_subquery = f'''
DistinctGeoChemicalAnalyses AS 
(
    SELECT
    lsa.AliquotID,
    SUM(CASE WHEN GeoChemicalAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT GeoChemicalAnalyses.GeoChemAnalysisID) AS AcceptedTotalGeoChemicalAnalyses
    FROM LimitedSamplesAliquots lsa
    INNER JOIN Spots ON lsa.AliquotID = Spots.AliquotID
    INNER JOIN GeoChemicalAnalyses ON Spots.SpotID = GeoChemicalAnalyses.SpotID
    GROUP BY lsa.AliquotID
)
'''
qgeochem_count_grain_subquery = f'''
DistinctGeoChemicalAnalyses AS 
(
    SELECT
    lspag.GrainID,
    SUM(CASE WHEN GeoChemicalAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT GeoChemicalAnalyses.GeoChemAnalysisID) AS AcceptedTotalGeoChemicalAnalyses
    FROM LimitedSpotsAnalysesGrains lspag
    INNER JOIN GeoChemicalAnalyses ON lspag.SpotID = GeoChemicalAnalyses.SpotID
    GROUP BY lspag.GrainID
)
'''
qgeochem_count_spot_subquery = f'''
DistinctGeoChemicalAnalyses AS 
(
    SELECT
    lspag.SpotID,
    SUM(CASE WHEN GeoChemicalAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT GeoChemicalAnalyses.GeoChemAnalysisID) AS AcceptedTotalGeoChemicalAnalyses
    FROM LimitedSpotsAnalysesGrains lspag
    INNER JOIN GeoChemicalAnalyses ON lspag.SpotID = GeoChemicalAnalyses.SpotID
    GROUP BY lspag.SpotID
)
'''

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
geochem_analyte_join = 'LEFT JOIN GeoChemicalAnalytes ON GeoChemicalAnalyses.GeoChemAnalyteID = GeoChemicalAnalytes.GeoChemAnalyteID'
geochem_analyte_unit_join = 'LEFT JOIN AnalyticalUnits AS GeoChemAnalyteUnits ON GeoChemicalAnalyses.GeoChemAnalyteUnitID = GeoChemAnalyteUnits.AnalyticalUnitID'
geochem_analyte_error_format_join = 'LEFT JOIN ErrorFormats AS GeoChemAnalyteErrorFormats ON GeoChemicalAnalyses.GeoChemAnalyteErrorFormatID = GeoChemAnalyteErrorFormats.ErrorFormatID'
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

shared_leaf_tables = {'Spots', 'Grains', 'LabFacilities', 'Instruments',
                      'SpotCompositions', 'GrainCompositions'}

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
                       'GeoChemicalAnalysisContexts', 'GeoChemicalMethods', 'GrainContexts', 'Regions', 'RockTypes',
                       'SampleContexts', 'SamplingMethods', 'Settings', 'SpotCompositions',
                       'SpotContexts', 'UPbAnalysisMethods', 'UPbAnalysisContexts', 'Units']
"""List of all user-viewable trees used throughout GeoCORK. If a table is included in this list it is assumed to be in the correct format"""

export_database_tables_viewable = sorted(user_viewable_tables + ['UPbAnalyses', 'Aliquots', 'Spots'])
"""List of all tables to be viewed in the ExporterWidget for exporting a database. Extra tables are included for sanity checking."""

conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Grains', 'Spots', 'UPbAnalyses', 'GeoChemicalAnalyses']
conditionally_editable_trees = ['Aliquots']

trigger_tables = ['Columns', 'ColumnEditView', 'GPSLocations', 'SampleAges', 'Samples', 'SampleEditView', 'Spots',
                  'SpotEditView', 'UPbAnalyses', 'UPbView', 'UPbEditView', 'Grains', 'GrainEditView',
                  'GeoChemicalAnalyses', 'GeoChemEditView']

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
"""Used in ExportDatabase.py as tables to skip if found exporting.
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
                           'GeoChemicalMethods'
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

views = ['SampleView', 'SampleEditView', 'AliquotView', 'AliquotEditView', 'SpotView',
         'SpotEditView', 'UPbView', 'UPbEditView', 'ColumnView', 'ColumnEditView', 'ReferenceView', 'GeoChemView', 'GeoChemEditView']
"""List of all views in the database. These views pull information from other tables for a comprehensive view of data
See Database_views.py for further"""

age_units = [('Billion years', 'Ga', '1000000000'),
             ('Million years', 'Ma', '1000000'),
             ('Thousand years', 'ka', '1000'),
             ('Years', 'a', '1')]
"""Static list of valid age units. Used to create AgeUnits table."""

analytical_units = [('Parts per million', 'ppm', 'Concentration in parts per million (mg/kg or μg/g)'),
                      ('Parts per billion', 'ppb', 'Concentration in parts per billion (μg/kg or ng/g)'),
                      ('Parts per trillion', 'ppt', 'Concentration in parts per trillion (ng/kg or pg/g)'),
                      ('Weight percent', 'wt%', 'Concentration as a percentage by weight'),
                      ('Micrograms per gram', 'μg/g', 'Concentration in micrograms per gram (equivalent to ppm)'),
                      ('Nanograms per gram', 'ng/g', 'Concentration in nanograms per gram (equivalent to ppb)'),
                      ('Milligrams per kilogram', 'mg/kg', 'Concentration in milligrams per kilogram (equivalent to ppm)'),
                      ('Moles per gram', 'mol/g', 'Concentration in moles per gram'),
                      ('Atoms per gram', 'atoms/g', 'Concentration in atoms per gram'),
                      ('Counts per second', 'cps', 'Raw signal intensity in counts per second'),
                      ('Isotope ratio', 'ratio', 'Dimensionless ratio of two isotope abundances (e.g., 206Pb/238U, 87Sr/86Sr)'),
                      ('Delta notation', 'δ‰', 'Per mil deviation of an isotope ratio from a reference standard (e.g., δ18O, δ13C)'),
                      ('Epsilon notation', 'ε', 'Parts per 10,000 deviation of an isotope ratio from a reference (e.g., εNd, εHf)'),
                      ('Initial ratio', 'initial', 'Isotope ratio corrected for radiogenic ingrowth back to time of formation'),
                      ('Atomic percent', 'at%', 'Isotope abundance as a percentage of total atoms of that element'),
                      ('Fractional abundance', 'fraction', 'Isotope abundance as a decimal fraction of total atoms of that element')]
"""Static list of valid analytical units. Used to create AnalyticalUnits table."""

geochemical_analytes = [
    ('Al27/Mg24', 'Al27/Mg24', 'ratio of aluminum isotope Al-27 to magnesium isotope Mg-24'),
    ('Acetate', 'Acetate', 'acetate'),
    ('Silver', 'Ag', 'silver'),
    ('Sample age', 'Age', 'sample age'),
    ('Aluminum', 'Al', 'aluminum'),
    ('Aluminum isotope Al-26', 'Al26', 'aluminum isotope Al-26'),
    ('Dialuminum dioxide', 'Al2O2', 'Dialuminum dioxide'),
    ('Aluminium oxide', 'Al2O3', 'aluminium oxide'),
    ('Alkalinity', 'Alk', 'alkalinity'),
    ('Argon', 'Ar', 'argon'),
    ('Argon isotope Ar-36', 'Ar36', 'argon isotope Ar-36'),
    ('Ar36/Ar38', 'Ar36/Ar38', 'ratio of argon isotopes Ar-36 to Ar-38'),
    ('Ar36/Ar39', 'Ar36/Ar39', 'ratio of argon isotopes Ar-36 to Ar-39'),
    ('Ar36/Ar40', 'Ar36/Ar40', 'ratio of argon isotopes Ar-36 to Ar-40'),
    ('Ar36/Xe132', 'Ar36/Xe132', 'ratio of argon isotope Ar-36 to xenon isotope Xe-132'),
    ('Argon isotope Ar-37', 'Ar37', 'argon isotope Ar-37'),
    ('Ar37/Ar40', 'Ar37/Ar40', 'ratio of Ar-37 to Ar-40'),
    ('Argon isotope Ar-38', 'Ar38', 'argon isotope Ar-38'),
    ('Ar38/Ar36', 'Ar38/Ar36', 'ratio of argon isotopes Ar-38 to Ar-36'),
    ('Ar38/Ar40', 'Ar38/Ar40', 'ratio of argon isotopes Ar-38 to Ar-40'),
    ('Argon isotope Ar-39', 'Ar39', 'argon isotope Ar-39'),
    ('Ar39/Ar40', 'Ar39/Ar40', 'ratio of argon isotopes Ar-39 to Ar-40'),
    ('Argon isotope Ar-40', 'Ar40', 'argon isotope Ar-40'),
    ('Ar40/Ar36', 'Ar40/Ar36', 'ratio of argon isotopes Ar-40 to Ar-36'),
    ('Ar40/Ar36_Initial', 'Ar40/Ar36_Initial', 'initial ratio of argon isotopes Ar-40 to Ar-37'),
    ('Ar40/Ar39', 'Ar40/Ar39', 'ratio of argon isotopes Ar-40 to Ar-39'),
    ('Atmospheric argon isotope ar40', 'Ar40/ATM', 'atmospheric argon isotope ar40'),
    ('Ar40/He4', 'Ar40/He4', 'ratio of argon isotopes Ar-40 to helium isotope He-4'),
    ('Radiogenic ar40', 'Ar40*', 'radiogenic ar40'),
    ('Ar40*/Ar39_K', 'Ar40*/Ar39_K', 'ratio of argon isotopes, radiogenic Ar-40 to Ar-39 produced from K'),
    ('Arsenic', 'As', 'arsenic'),
    ('Gold', 'Au', 'gold'),
    ('Boron', 'B', 'boron'),
    ('B/Ca', 'B/Ca', 'ratio of boron to calcium'),
    ('B11/B10', 'B11/B10', 'ratio of boron isotopes B-11 to B-10'),
    ('Barium', 'Ba', 'barium'),
    ('Ba/Ca', 'Ba/Ca', 'ratio of barium to calcium'),
    ('Barium oxide', 'BaO', 'barium oxide'),
    ('Barite', 'BaSO4', 'barite'),
    ('Beryllium', 'Be', 'beryllium'),
    ('Beryllium isotope Be-10', 'Be10', 'beryllium isotope Be-10'),
    ('Be10/Be9', 'Be10/Be9', 'ratio of beryllium isotopes Be-10 to Be-9'),
    ('Be10/Be9(T)', 'Be10/Be9(T)', 'ratio of isotopes Be-10 to Be-9, time corrected'),
    ('Beryllium isotope Be-9', 'Be9', 'beryllium isotope Be-9'),
    ('Bismuth', 'Bi', 'bismuth'),
    ('Bromium', 'Br', 'bromium'),
    ('Bromide', 'Br-', 'bromide'),
    ('Carbon', 'C', 'carbon'),
    ('Inorganic carbon', 'C(inorg)', 'inorganic carbon'),
    ('Organic carbon', 'C(org)', 'organic carbon'),
    ('Total carbon', 'C(tot)', 'total carbon'),
    ('Non-carbonate carbon', 'C(non-carb)', 'non-carbonate carbon'),
    ('C/N', 'C/N', 'ratio of organic carbon to total nitrogen'),
    ('Carbon isotope C-14', 'C14', 'carbon isotope C-14'),
    ('C-14_Age', 'C14_Age', 'C-14_Age'),
    ('Calcium', 'Ca', 'calcium'),
    ('Ca/K', 'Ca/K', 'ratio of calcium to potassium'),
    ('Calcium isotope Ca-41', 'Ca41', 'calcium isotope Ca-41'),
    ('Calcium carbonate', 'CaCO3', 'calcium carbonate'),
    ('Calibrated C-14_Age', 'C14_Age_Calibrated', 'calibrated C-14_Age'),
    ('Calcium oxide', 'CaO', 'calcium oxide'),
    ('Cap_Delta_O17', 'Cap_Delta_O17', 'deviation from the Earth-Moon line of O17/O16 and O18/O16 ratios as the vertical displacement of any point from it, calculated as Cap_Delta_O17=1000*ln(1+(delta_O17/1000))-0.52*1000*ln(1+(delta_O18/1000))'),
    ('Cap_Delta_S33', 'Cap_Delta_S33', 'deviation of Delta_S33 from the terrestrial fractionation array, calculated as Cap_Delta_S33=Delta_S33-(Delta_S34/1000+1)^0.515-1)*1000'),
    ('Cap_Delta_S36', 'Cap_Delta_S36', 'deviation of Delta_S36 from the terrestrial fractionation array, calculated as Cap_Delta_S36=Delta_S36-((Delta_S34/1000+1)^1.9-1)*1000'),
    ('Calcium sulfate', 'CaSO4', 'calcium sulfate'),
    ('Cadmium', 'Cd', 'cadmium'),
    ('Cd/Ca', 'Cd/Ca', 'ratio of cadmium to calcium'),
    ('Cerium', 'Ce', 'cerium'),
    ('Ce136/Ce142', 'Ce136/Ce142', 'ratio of cerium isotopes Ce-136 to Ce-142'),
    ('Ce138/Ce142', 'Ce138/Ce142', 'ratio of cerium isotopes Ce-138 to Ce-142'),
    ('Ce140/Nd146', 'Ce140/Nd146', 'ratio of cerium to neodymium isotopes Ce-140 to Nd-146'),
    ('Cerium oxide', 'Ce2O3', 'cerium oxide'),
    ('Cerium dioxide', 'CeO2', 'cerium dioxide'),
    ('Methane', 'CH4', 'methane'),
    ('Chlorine', 'Cl', 'chlorine'),
    ('Chrg_Bal', 'Chrg_Bal', 'electrical charge balance, calculated as the sum of cations vs. anions'),
    ('Radiogenic Cl isotope Cl-36', 'Cl36', 'radiogenic Cl isotope Cl-36'),
    ('Radiogenic Cl isotope Cl-38', 'Cl38', 'radiogenic Cl isotope Cl-38'),
    ('Cobalt', 'Co', 'cobalt'),
    ('Carbon dioxide', 'CO2', 'carbon dioxide'),
    ('Cobalt isotope Co-56', 'Co56', 'cobalt isotope Co-56'),
    ('Cobalt oxide', 'CoO', 'cobalt oxide'),
    ('Chromium', 'Cr', 'chromium'),
    ('Chromium oxide', 'Cr2O3', 'chromium oxide'),
    ('Cesium', 'Cs', 'cesium'),
    ('Cesium isotope Cs-137 reported as activity', 'Cs137_Activity', 'cesium isotope Cs-137 reported as activity'),
    ('Copper', 'Cu', 'copper'),
    ('Cu2O', 'Cu2O', 'copper(i) oxide (cuprous oxide)'),
    ('Copper oxide', 'CuO', 'copper oxide'),
    ('Delta_B11', 'Delta_B11', 'calculated as (B11/B10_sample / B11/B10_ NIST SRM951 -1)*1000'),
    ('Delta_C13', 'Delta_C13', 'calculated as (C13/C12_sample / C13/C12_PDB -1)*1000'),
    ('Delta_Ca44', 'Delta_Ca44', 'calculated as (Ca44/Ca40_sample / Ca44/Ca40_std -1)*1000'),
    ('Delta_Cl37', 'Delta_Cl37', 'calculated as (Cl37/Cl35_sample / Cl37/Cl35_SMOC -1)*1000'),
    ('DELTA_Cu65', 'DELTA_Cu65', 'calculated as (Cu65/Cu63_sample / Cu65/Cu63_NIST-976 - 1)*1000'),
    ('DELTA_D', 'DELTA_D', 'calculated as (H2/H1_sample / H2/H1_std -1)*1000'),
    ('DELTA_Fe56', 'DELTA_Fe56', 'calculated as (Fe56/Fe54_ sample / Fe56/Fe54_IRMM-014 -1)*1000'),
    ('DELTA_Fe57', 'DELTA_Fe57', 'calculated as (Fe57/Fe54_sample / Fe57/Fe54_IRMM-014 -1)*1000'),
    ('DELTA_H2', 'DELTA_H2', 'calculated as (H2/H1_sample / H2/H1_std -1)*1000'),
    ('DELTA_Li6', 'DELTA_Li6', 'calculated as (Li6/Li7_sample / Li6/Li7_std -1)*1000'),
    ('DELTA_Li7', 'DELTA_Li7', 'calculated as (Li7/Li6_sample / Li7/Li6_std -1)*1000'),
    ('DELTA_Mg25', 'DELTA_Mg25', 'calculated as (Mg25/Mg24_sample / Mg25/Mg24_std - 1)*1000'),
    ('DELTA_Mg26', 'DELTA_Mg26', 'calculated as (Mg26/Mg24_sample / Mg26/Mg24_std - 1)*1000'),
    ('DELTA_Mo98', 'DELTA_Mo98', 'calculated as (Mo98/Mo95_sample / Mo98/Mo95_std - 1)*1000'),
    ('DELTA_N15', 'DELTA_N15', 'calculated as (N15/N14_sample / N15/N14_std - 1)*1000'),
    ('DELTA_Ni60', 'DELTA_Ni60', 'calculated as (Ni60/Ni58_sample / Ni60/Ni58_std - 1)*1000'),
    ('DELTA_O17', 'DELTA_O17', 'calculated as (O17/O16_sample / O17/O16_std - 1)*1000'),
    ('DELTA_O18', 'DELTA_O18', 'calculated as (O18/O16_sample / O18/O16_std - 1)*1000'),
    ('DELTA_S33', 'DELTA_S33', 'calculated as (S33/S32_sample / S33/S32_std - 1)*1000'),
    ('DELTA_S34', 'DELTA_S34', 'calculated as (S34/S32_sample / S34/S32_std - 1)*1000'),
    ('DELTA_S34SO4', 'DELTA_S34SO4', 'sulfur isotope of the sulfate; calculated as (S33/S32_sample / S33/S32_std - 1)*1000'),
    ('DELTA_S36', 'DELTA_S36', 'calculated as (S36/S32_sample / S36/S32_std - 1)*1000'),
    ('DELTA_Si29', 'DELTA_Si29', 'calculated as (Si29/Si28_sample / Si29/Si28_std - 1)*1000'),
    ('DELTA_Si30', 'DELTA_Si30', 'calculated as (Si30/Si28_sample / Si30/Si28_std - 1)*1000'),
    ('DELTA_Ti49', 'DELTA_Ti49', 'calculated as (Ti49/Ti47_sample / Ti49/Ti47_std - 1)*1000'),
    ('DELTA_U234', 'DELTA_U234', 'calculated as (U234/U238_sample / U234/U238_secular_equilibrium - 1)*1000'),
    ('DELTA_U238', 'DELTA_U238', 'calculated as (U238/U235_sample / U238/U235_secular_equilibrium - 1)*1000'),
    ('DELTA_V51', 'DELTA_V51', 'calculated as (V51/V50_sample / V51/V50_std - 1)*1000'),
    ('DELTA_Zn66', 'DELTA_Zn66', 'calculated as (Zn66/Zn64_sample / Zn66/Zn64_std - 1)*1000'),
    ('DELTA_Zn68', 'DELTA_Zn68', 'calculated as (Zn68/Zn64_sample / Zn68/Zn64_std - 1)*1000'),
    ('Dissolved inorganic carbon', 'DIC', 'dissolved inorganic carbon'),
    ('Dysprosium', 'Dy', 'dysprosium'),
    ('Dysprosium oxide', 'Dy2O3', 'dysprosium oxide'),
    ('E_Cd', 'E_Cd', 'calculated as (Cd114/Cd110_sample/ Cd114/Cd110_std - 1)*1000'),
    ('E_Ce', 'E_Ce', 'calculated as (Ce138/Ce142_sample/ Ce138/Ce142_std - 1)*1000'),
    ('E_Hf', 'E_Hf', 'calculated as (176Hf/177Hf_sample/ 176Hf/177Hf_std - 1)*1000'),
    ('E_Hf(T)', 'E_Hf(T)', 'calculated as (176Hf/177Hf_sample/ 176Hf/177Hf_std - 1)*1000, time corrected'),
    ('E_Mg25', 'E_Mg25', 'calculated as (Mg25/Mg24_sample/ Mg25/Mg24_std - 1)*1000'),
    ('E_Mg26', 'E_Mg26', 'calculated as (Mg26/Mg24_sample/ Mg26/Mg24_std - 1)*1000'),
    ('E_Nd', 'E_Nd', 'calculated as (Nd143/Nd144_sample/ Nd143/Nd144_std - 1)*1000'),
    ('E_Nd(T)', 'E_Nd(T)', 'calculated as (Nd143/Nd144_sample/ Nd143/Nd144_std - 1)*1000, time corrected'),
    ('E_Sr', 'E_Sr', 'calculated as (Sr87/Sr86_sample/ Sr87/Sr86_std - 1)*1000'),
    ('E_Sr(T)', 'E_Sr(T)', 'calculated as (Sr87/Sr86_sample/ Sr87/Sr86_std - 1)*1000, time corrected'),
    ('E_Tl', 'E_Tl', 'calculated as (Tl205/Tl203_sample/ Tl205/Tl203_std - 1)*1000'),
    ('E_W182', 'E_W182', 'calculated as (W182/W184_sample/ W182/W184_std - 1)*1000'),
    ('E_W183', 'E_W183', 'calculated as (W183/W184_sample/ W183/W184_std - 1)*1000'),
    ('Erbium', 'Er', 'erbium'),
    ('Erbium oxide', 'Er2O3', 'erbium oxide'),
    ('Europium', 'Eu', 'europium'),
    ('Europium oxide', 'Eu2O3', 'europium oxide'),
    ('Fluorine', 'F', 'fluorine'),
    ('Iron', 'Fe', 'iron'),
    ('Fe2O3', 'Fe2O3', 'ferric iron oxide (tri-valent iron)'),
    ('Fe2O3T', 'Fe2O3T', 'total iron oxide content reported as ferric (tri-valent) iron'),
    ('Fe3O4', 'Fe3O4', 'ferrosoferric oxide (Iron (II,III) oxide)'),
    ('Fe3/FeT', 'Fe3/FeT', 'ratio of feric iron to total iron'),
    ('Siderite', 'FeCO3', 'siderite'),
    ('Fe-Fe', 'Fe-Fe', 'iron ferrite (FeFe2O4)'),
    ('FeO', 'FeO', 'ferrous iron oxide (di-valent)'),
    ('FeOT', 'FeOT', 'total iron oxide content reported as ferrous (di-valent) iron'),
    ('FeS', 'FeS', 'ferrous sulfide (di-valent)'),
    ('Iron sulfide', 'FeS2', 'iron sulfide'),
    ('Francium', 'Fr', 'francium'),
    ('Fallout radionuclide measurement', 'FRM', 'fallout radionuclide measurement'),
    ('Gamma osmium', 'G_Os', 'gamma osmium'),
    ('Gamma osmium, time corrected', 'G_Os(T)', 'gamma osmium, time corrected'),
    ('Gallium', 'Ga', 'gallium'),
    ('Gadolinium', 'Gd', 'gadolinium'),
    ('Gd155/Sm152', 'Gd155/Sm152', 'ratio of gadolinium isotope Gd155 to samarium isotope Sm152'),
    ('Gadolinium oxide', 'Gd2O3', 'gadolinium oxide'),
    ('Germanium', 'Ge', 'germanium'),
    ('Hydrogen', 'H', 'hydrogen'),
    ('Total hydrogen', 'H(TOT)', 'total hydrogen'),
    ('Hydrogen (diatomic)', 'H2', 'hydrogen'),
    ('Water', 'H2O', 'water'),
    ('H2OM', 'H2OM', 'crystal water (H2O-)'),
    ('H2OP', 'H2OP', 'crystal water (H2O+)'),
    ('Hydrogen sulfide', 'H2S', 'hydrogen sulfide'),
    ('Total hydrogen sulfide', 'H2S(TOT)', 'total hydrogen sulfide'),
    ('Silicic acid', 'H4SiO4', 'silicic acid'),
    ('Bicarbonate', 'HCO3', 'bicarbonate'),
    ('Helium', 'He', 'helium'),
    ('Helium isotope He3', 'He3', 'helium isotope He3'),
    ('He3/He4', 'He3/He4', 'ratio of helium isotopes He3 to He4'),
    ('He3/He4(R/Ra)', 'He3/He4(R/Ra)', 'ratio of helium isotopes He3 to He4 expressed relative to the helium isotope ratio of the atmosphere'),
    ('Helium isotope He4', 'He4', 'helium isotope He4'),
    ('Helium isotope He4 measured by neutron coincidence counting', 'He4(NCC)', 'helium isotope He4 measured by neutron coincidence counting'),
    ('He4/Ar40', 'He4/Ar40', 'ratio of helium isotope He4 to argon isotope Ar40'),
    ('He4/He3', 'He4/He3', 'ratio of helium isotopes He4 to He3'),
    ('He4/Ne20', 'He4/Ne20', 'ratio of helium isotope He4 to neon isotope Ne20'),
    ('He4/Ne21', 'He4/Ne21', 'ratio of helium isotope He4 to neon isotope Ne21'),
    ('Hafnium', 'Hf', 'hafnium'),
    ('Hf174/Hf177', 'Hf174/Hf177', 'ratio of hafnium isotopes Hf174 to Hf177'),
    ('Hf176/Hf177', 'Hf176/Hf177', 'ratio of hafnium isotopes Hf176 to Hf177'),
    ('Hf176/Hf177(I)', 'Hf176/Hf177(I)', 'ratio of hafnium isotopes Hf176 to Hf177 at initial time'),
    ('Hf176/Hf177(T)', 'Hf176/Hf177(T)', 'ratio of hafnium isotopes Hf176 to Hf177, time corrected'),
    ('Hf177/Hf178', 'Hf177/Hf178', 'ratio of hafnium isotopes Hf177 to Hf178'),
    ('Hf178/Hf177', 'Hf178/Hf177', 'ratio of hafnium isotopes Hf178 to Hf177'),
    ('Hf179/Hf177', 'Hf179/Hf177', 'ratio of hafnium isotopes Hf179 to Hf177'),
    ('Hf180/Hf177', 'Hf180/Hf177', 'ratio of hafnium isotopes Hf180 to Hf177'),
    ('Hf180/W184', 'Hf180/W184', 'ratio of hafnium isotope Hf180 to wolfram isotope W184'),
    ('Hafnium dioxide', 'HfO', 'hafnium dioxide'),
    ('Hafnium oxide', 'HfO2', 'hafnium oxide'),
    ('Mercury', 'Hg', 'mercury'),
    ('Holmium', 'Ho', 'holmium'),
    ('Holmium oxide', 'Ho2O3', 'holmium oxide'),
    ('Iodine', 'I', 'iodine'),
    ('Indium', 'In', 'indium'),
    ('Iridium', 'Ir', 'iridium'),
    ('Potassium', 'K', 'potassium'),
    ('Potassium oxide', 'K2O', 'potassium oxide'),
    ('Krypton', 'Kr', 'krypton'),
    ('Krypton isotope Kr78', 'Kr78', 'krypton isotope Kr78'),
    ('Kr78/Kr83', 'Kr78/Kr83', 'ratio of krypton isotopes Kr78 to Kr83'),
    ('Kr78/Kr84', 'Kr78/Kr84', 'ratio of krypton isotopes Kr78 to Kr84'),
    ('Kr78/Kr86', 'Kr78/Kr86', 'ratio of krypton isotopes Kr78 to Kr86'),
    ('Krypton isotope Kr80', 'Kr80', 'krypton isotope Kr80'),
    ('Kr80/Kr83', 'Kr80/Kr83', 'ratio of krypton isotopes Kr80 to Kr83'),
    ('Kr80/Kr84', 'Kr80/Kr84', 'ratio of krypton isotopes Kr80 to Kr84'),
    ('Kr80/Kr86', 'Kr80/Kr86', 'ratio of krypton isotopes Kr80 to Kr86'),
    ('Krypton isotope Kr81', 'Kr81', 'krypton isotope Kr81'),
    ('Kr81/Kr86', 'Kr81/Kr86', 'ratio of krypton isotopes Kr81 to Kr86'),
    ('Krypton isotope Kr82', 'Kr82', 'krypton isotope Kr82'),
    ('Kr82/Kr83', 'Kr82/Kr83', 'ratio of krypton isotopes Kr82 to Kr83'),
    ('Kr82/Kr84', 'Kr82/Kr84', 'ratio of krypton isotopes Kr82 to Kr84'),
    ('Kr82/Kr86', 'Kr82/Kr86', 'ratio of krypton isotopes Kr82 to Kr86'),
    ('Krypton isotope Kr83', 'Kr83', 'krypton isotope Kr83'),
    ('Kr83/Kr84', 'Kr83/Kr84', 'ratio of krypton isotopes Kr83 to Kr84'),
    ('Kr83/Kr86', 'Kr83/Kr86', 'ratio of krypton isotopes Kr83 to Kr86'),
    ('Krypton isotope kr84', 'Kr84', 'krypton isotope kr84'),
    ('Kr84/Kr83', 'Kr84/Kr83', 'ratio of krypton isotopes Kr84 to Kr83'),
    ('Kr84/Kr86', 'Kr84/Kr86', 'ratio of krypton isotopes Kr84 to Kr86'),
    ('Kr84/Xe132', 'Kr84/Xe132', 'ratio of krypton isotopes Kr84 to xenon isotopes Xe132'),
    ('Krypton isotope Kr86', 'Kr86', 'krypton isotope Kr86'),
    ('Kr86/Kr84', 'Kr86/Kr84', 'ratio of krypton isotopes Kr86 to Kr84'),
    ('Krypton isotope Kr90', 'Kr90', 'krypton isotope Kr90'),
    ('Lanthanum', 'La', 'lanthanum'),
    ('Lanthanum oxide', 'La2O3', 'lanthanum oxide'),
    ('Lithium', 'Li', 'lithium'),
    ('Li7/Li6', 'Li7/Li6', 'ratio of lithium isotopes Li7 to Li6'),
    ('Loss on ignition', 'LOI', 'loss on ignition'),
    ('Lutetium', 'Lu', 'lutetium'),
    ('Lu176/Hf177', 'Lu176/Hf177', 'ratio of lutetium isotope Lu176 to hafnium isotope Hf177'),
    ('Lu176/Hf177(T)', 'Lu176/Hf177(T)', 'ratio of lutetium isotope Lu176 to hafnium isotope Hf177, time corrected'),
    ('Lu176/Lu177', 'Lu176/Lu177', 'ratio of lutetium isotopes Lu176 to Lu177'),
    ('Lutetium oxide', 'Lu2O3', 'lutetium oxide'),
    ('Magnesium', 'Mg', 'magnesium'),
    ('Mg/Ca', 'Mg/Ca', 'ratio of magnesium to calcium'),
    ('Magnesium oxide', 'MgO', 'magnesium oxide'),
    ('Min[EM]', 'Min[EM]', 'End member (replace Min with mineral abbreviation)'),
    ('Manganese', 'Mn', 'manganese'),
    ('Mn_Ca', 'Mn_Ca', 'ratio of manganese to calcium'),
    ('Manganese tetroxide', 'Mn3O4', 'manganese tetroxide'),
    ('Manganese isotope Mn54', 'Mn54', 'manganese isotope Mn54'),
    ('Manganese carbonate', 'MnCO3', 'manganese carbonate'),
    ('Manganese oxide', 'MnO', 'manganese oxide'),
    ('Nitrogen', 'N', 'nitrogen'),
    ('Percent nitrogen in the a defect site of diamonds', 'N(A)', 'percent nitrogen in the a defect site of diamonds'),
    ('Percent nitrogen in the b defect site of diamonds', 'N(B)', 'percent nitrogen in the b defect site of diamonds'),
    ('Organic nitrogen', 'N(ORG)', 'organic nitrogen'),
    ('Total nitrogen', 'N(TOT)', 'total nitrogen'),
    ('Nitrogen (diatomic)', 'N2', 'nitrogen'),
    ('Nitrogen measured in nanomols', 'N2[nmol]', 'nitrogen measured in nanomols'),
    ('N2/Ar36', 'N2/Ar36', 'ratio of nitrogen isotope N2 to argon isotope Ar36'),
    ('N2/He3', 'N2/He3', 'ratio of nitrogen isotope N2 to helium isotope He3'),
    ('Sodium', 'Na', 'sodium'),
    ('Sodium isotope Na22', 'Na22', 'sodium isotope Na22'),
    ('Sodium oxide', 'Na2O', 'sodium oxide'),
    ('Niobium', 'Nb', 'niobium'),
    ('Niobium oxide', 'Nb2O3', 'niobium oxide'),
    ('Niobium pentoxide', 'Nb2O5', 'niobium pentoxide'),
    ('Native copper', 'NCU', 'native copper'),
    ('Neodymium', 'Nd', 'neodymium'),
    ('Nd/Ca', 'Nd/Ca', 'ratio of neodymium to calcium'),
    ('Nd142/Nd144', 'Nd142/Nd144', 'ratio of neodymium isotopes Nd142 to Nd144'),
    ('Nd143/Nd144', 'Nd143/Nd144', 'ratio of neodymium isotopes Nd143 to Nd144'),
    ('Nd143/Nd144(I)', 'Nd143/Nd144(I)', 'ratio of neodymium isotopes Nd143 to Nd144 at initial age'),
    ('Nd143/Nd144(T)', 'Nd143/Nd144(T)', 'ratio of neodymium isotopes Nd143 to Nd144, time corrected'),
    ('Neodymium isotope Nd144', 'Nd144', 'neodymium isotope Nd144'),
    ('Nd144/Nd146', 'Nd144/Nd146', 'ratio of neodymium isotopes Nd144 to Nd146'),
    ('Nd145/Nd144', 'Nd145/Nd144', 'ratio of neodymium isotopes Nd145 to Nd144'),
    ('Nd146/Nd142', 'Nd146/Nd142', 'ratio of neodymium isotopes Nd146 to Nd142'),
    ('Nd146/Nd144', 'Nd146/Nd144', 'ratio of neodymium isotopes Nd146 to Nd144'),
    ('Nd146/Nd145', 'Nd146/Nd145', 'ratio of neodymium isotopes Nd146 to Nd145'),
    ('Nd146/Sm152', 'Nd146/Sm152', 'ratio of neodymium isotope Nd146 to samarium isotope Sm152'),
    ('Nd148/Nd144', 'Nd148/Nd144', 'ratio of neodymium isotopes Nd148 to Nd144'),
    ('Nd148O/Nd144O', 'Nd148O/Nd144O', 'ratio of neodymium Nd148 oxide to neodymium Nd144 oxide'),
    ('Nd150/Nd144', 'Nd150/Nd144', 'ratio of neodymium isotopes Nd150 to Nd144'),
    ('Neodymium oxide', 'Nd2O3', 'neodymium oxide'),
    ('Neon', 'Ne', 'neon'),
    ('Neon isotope ne20', 'Ne20', 'neon isotope ne20'),
    ('Ne20/Ne21', 'Ne20/Ne21', 'ratio of neon isotope Ne20 to Ne21'),
    ('Ne20/Ne22', 'Ne20/Ne22', 'ratio of neon isotope Ne20 to Ne22'),
    ('Neon isotope Ne21', 'Ne21', 'neon isotope Ne21'),
    ('Ne21/He4', 'Ne21/He4', 'ratio of neon isotope Ne21 to helium isotope He4'),
    ('Ne21/Ne20', 'Ne21/Ne20', 'ratio of neon isotope Ne21 to Ne20'),
    ('Ne21/Ne22', 'Ne21/Ne22', 'ratio of neon isotope Ne21 to Ne22'),
    ('Neon isotope Ne22', 'Ne22', 'neon isotope Ne22'),
    ('Ne22/Ne20', 'Ne22/Ne20', 'ratio of neon isotope Ne22 to Ne20'),
    ('Ne22/Ne21', 'Ne22/Ne21', 'ratio of neon isotope Ne22 to Ne21'),
    ('Neon isotope Ne23', 'Ne23', 'neon isotope Ne23'),
    ('Ammonia', 'NH3', 'ammonia'),
    ('Ammonium', 'NH4', 'ammonium'),
    ('Nickel', 'Ni', 'nickel'),
    ('Nickel oxide', 'NiO', 'nickel oxide'),
    ('Nitrogen dioxide', 'NO2', 'nitrogen dioxide'),
    ('Nitrate', 'NO3', 'nitrate'),
    ('Oxygen', 'O', 'oxygen'),
    ('O17/O16', 'O17/O16', 'ratio of oxygen isotopes O17 to O16'),
    ('O18/O16', 'O18/O16', 'ratio of oxygen isotopes O18 to O16'),
    ('Oxygen (diatomic)', 'O2', 'dioxygen'),
    ('Hydroxide', 'OH', 'hydroxide'),
    ('Osmium', 'Os', 'osmium'),
    ('Common osmium at initial age', 'Os(I)', 'common osmium at initial age'),
    ('Os184/Os188', 'Os184/Os188', 'ratio of osmium isotopes Os184 to Os188'),
    ('Os186/Os188', 'Os186/Os188', 'ratio of osmium isotopes Os186 to Os188'),
    ('Os187/Os186', 'Os187/Os186', 'ratio of osmium isotopes Os187 to Os186'),
    ('Os187/Os188', 'Os187/Os188', 'ratio of osmium isotopes Os187 to Os188'),
    ('Os187/Os188(I)', 'Os187/Os188(I)', 'ratio of osmium isotopes Os187 to Os188 at initial age'),
    ('Os187/Os188(T)', 'Os187/Os188(T)', 'ratio of osmium isotopes Os187 to Os188, time corrected'),
    ('Osmium isotope Os188', 'Os188', 'osmium isotope Os188'),
    ('Os188/Os192', 'Os188/Os192', 'ratio of osmium isotopes Os188 to Os192'),
    ('Os189/Os188', 'Os189/Os188', 'ratio of osmium isotopes Os189 to Os188'),
    ('Os190/Os188', 'Os190/Os188', 'ratio of osmium isotopes Os190 to Os188'),
    ('Os192/Os188', 'Os192/Os188', 'ratio of osmium isotopes Os192 to Os188'),
    ('Phosphorus', 'P', 'phosphorus'),
    ('Phosphorous, organic', 'P(ORG)', 'phosphorous, organic'),
    ('Phosphorus trioxide', 'P2O3', 'phosphorus trioxide'),
    ('Phosphorus oxide', 'P2O5', 'phosphorus oxide'),
    ('Protactinium', 'Pa', 'protactinium'),
    ('Protactinium isotope Pa231', 'Pa231', 'protactinium isotope Pa231'),
    ('Protactinium isotope Pa231, reported as activity', 'Pa231_ACTIVITY', 'protactinium isotope Pa231, reported as activity'),
    ('Pa231/Th230', 'Pa231/Th230', 'ratio of protactinium isotope Pa231 to thorium isotope Th230'),
    ('Pa231/U235_ACTIVITY', 'Pa231/U235_ACTIVITY', 'ratio of protactinium isotope Pa231 to uranium isotope U235, reported as activity'),
    ('Excess protactinium Pa231', 'Pa231_XS', 'excess protactinium Pa231'),
    ('Lead', 'Pb', 'lead'),
    ('Lead isotope Pb204', 'Pb204', 'lead isotope Pb204'),
    ('Pb204_Pb206', 'Pb204_Pb206', 'ratio of lead isotopes Pb204 to Pb206'),
    ('Pb204_Pb208', 'Pb204_Pb208', 'ratio of lead isotopes Pb204 to Pb208'),
    ('Lead isotope 206', 'Pb206', 'lead isotope 206'),
    ('Pb206_Pb204', 'Pb206_Pb204', 'ratio of lead isotopes Pb206 to Pb204'),
    ('Pb206/Pb204(I)', 'Pb206/Pb204(I)', 'ratio of lead isotopes Pb206 to Pb204 at initial age'),
    ('Pb206/Pb204(T)', 'Pb206/Pb204(T)', 'ratio of lead isotopes Pb206 to Pb204, time corrected'),
    ('Pb206/Pb207', 'Pb206/Pb207', 'ratio of lead isotopes Pb206 to Pb207'),
    ('Pb206/Pb208', 'Pb206/Pb208', 'ratio of lead isotopes Pb206 to Pb208'),
    ('Pb206/U235', 'Pb206/U235', 'ratio of lead isotope Pb206 to uranium isotope U235'),
    ('Pb206/U238', 'Pb206/U238', 'ratio of lead isotope Pb206 to uranium isotope U238'),
    ('Pb206/U238(T)', 'Pb206/U238(T)', 'ratio of lead isotope Pb206 to uranium isotope U238, time corrected'),
    ('Lead isotope Pb207', 'Pb207', 'lead isotope Pb207'),
    ('Pb207/Pb204', 'Pb207/Pb204', 'ratio of lead isotopes Pb207 to Pb204'),
    ('Pb207/Pb204(I)', 'Pb207/Pb204(I)', 'ratio of lead isotopes Pb207 to Pb204 at initial age'),
    ('Pb207/Pb204(T)', 'Pb207/Pb204(T)', 'ratio of lead isotopes Pb207 to Pb204, time corrected'),
    ('Pb207/Pb206', 'Pb207/Pb206', 'ratio of lead isotopes Pb207 to Pb206'),
    ('Pb207/Pb206(I)', 'Pb207/Pb206(I)', 'ratio of lead isotopes Pb207 to Pb206 at initial age'),
    ('Pb207/Pb208', 'Pb207/Pb208', 'ratio of lead isotopes Pb207 to Pb208'),
    ('Pb207/U235', 'Pb207/U235', 'ratio of lead isotope Pb207 to uranium isotope U235'),
    ('Pb207/U235(T)', 'Pb207/U235(T)', 'ratio of lead isotope Pb207 to uranium isotope U235, time corrected'),
    ('Lead isotope Pb208', 'Pb208', 'lead isotope Pb208'),
    ('Pb208/Pb204', 'Pb208/Pb204', 'ratio of lead isotopes Pb208 to Pb204'),
    ('Pb208/Pb204(I)', 'Pb208/Pb204(I)', 'ratio of lead isotopes Pb208 to Pb204 at initial age'),
    ('Pb208/Pb204(T)', 'Pb208/Pb204(T)', 'ratio of lead isotopes Pb208 to Pb204, time corrected'),
    ('Pb208/Pb206', 'Pb208/Pb206', 'ratio of lead isotopes Pb208 to Pb206'),
    ('Pb208/Pb206(I)', 'Pb208/Pb206(I)', 'ratio of lead isotopes Pb208 to Pb206 at initial age'),
    ('Pb208/Th232', 'Pb208/Th232', 'ratio of lead isotope Pb208 to thorium isotope Th232'),
    ('Pb208/Th232(T)', 'Pb208/Th232(T)', 'ratio of lead isotope Pb208 to thorium isotope Th232, time corrected'),
    ('Lead isotope Pb210', 'Pb210', 'lead isotope Pb210'),
    ('Lead isotope Pb210, reported as activity', 'Pb210_ACTIVITY', 'lead isotope Pb210, reported as activity'),
    ('Pb210/Ra226', 'Pb210/Ra226', 'ratio of lead isotope Pb210 to radium isotope Ra226'),
    ('Pb210/Ra226_ACTIVITY', 'Pb210/Ra226_ACTIVITY', 'ratio of lead isotope Pb210 to radium isotope Ra226, reported as activity'),
    ('Pb210/U238', 'Pb210/U238', 'ratio of lead isotope Pb210 to uranium isotope U238'),
    ('Excess lead Pb210', 'Pb210_XS', 'excess lead Pb210'),
    ('Lead oxide', 'PbO', 'lead oxide'),
    ('Palladium', 'Pd', 'palladium'),
    ('PH', 'pH', 'pH'),
    ('Polonium isotope Po210', 'Po210', 'polonium isotope Po210'),
    ('Polonium isotope Po210, reported as activity', 'Po210_ACTIVITY', 'polonium isotope Po210, reported as activity'),
    ('Po210/Pb210', 'Po210/Pb210', 'ratio of polonium isotope Po210 to lead isotope Pb210'),
    ('Phosphate', 'PO4', 'phosphate'),
    ('Praseodymium', 'Pr', 'praseodymium'),
    ('Praseodymium oxide', 'Pr2O3', 'praseodymium oxide'),
    ('Pr6O11', 'Pr6O11', 'praseodymium (III, IV) oxide'),
    ('Pressure', 'PRESS', 'pressure'),
    ('Platinum', 'Pt', 'platinum'),
    ('Pt190/Os188', 'Pt190/Os188', 'ratio of platinum isotope Pt190 to osmium isotope Os188'),
    ('The correlation coefficient used to calculate the best-fit line', 'r2', 'the correlation coefficient used to calculate the best-fit line'),
    ('Radium', 'Ra', 'radium'),
    ('Radium isotope Ra226', 'Ra226', 'radium isotope Ra226'),
    ('Radium isotope Ra226, reported as activity', 'Ra226_ACTIVITY', 'radium isotope Ra226, reported as activity'),
    ('Ra226/Th230', 'Ra226/Th230', 'ratio of radium isotope Ra226 to thorium isotope Th230'),
    ('Ra226/Th230/ACTIVITY', 'Ra226/Th230/ACTIVITY', 'ratio of radium isotope Ra226 to thorium isotope Th230, reported as activity'),
    ('Rubidium', 'Rb', 'rubidium'),
    ('Rubidium isotope Rb87', 'Rb87', 'rubidium isotope Rb87'),
    ('Rb87/Rb86', 'Rb87/Rb86', 'ratio of rubidium isotopes Rb87 to Rb86'),
    ('Rb87/Sr86', 'Rb87/Sr86', 'ratio of rubidium isotope Rb87 to strontium isotope Sr86'),
    ('Rhenium', 'Re', 'rhenium'),
    ('Re187/Os186', 'Re187/Os186', 'ratio of rhenium isotope Re187 to osmium isotope Os186'),
    ('Re187/Os188', 'Re187/Os188', 'ratio of rhenium isotope Re187 to osmium isotope Os188'),
    ('Re187/Os189', 'Re187/Os189', 'ratio of rhenium isotope Re187 to osmium isotope Os189'),
    ('Rhodium', 'Rh', 'rhodium'),
    ('Ruthenium', 'Ru', 'ruthenium'),
    ('Sulfur', 'S', 'sulfur'),
    ('Total sulfur', 'S(TOT)', 'total sulfur'),
    ('Sulfur present as sulfide', 'S_(SLFI)', 'sulfur present as sulfide'),
    ('Sulfur present in pyrite form', 'S_PY', 'sulfur present in pyrite form'),
    ('Salinity', 'SAL', 'salinity'),
    ('Antimony', 'Sb', 'antimony'),
    ('Scandium', 'Sc', 'scandium'),
    ('Scandium oxide', 'Sc2O3', 'scandium oxide'),
    ('Scandium isotope Sc46', 'Sc46', 'scandium isotope Sc46'),
    ('Selenium', 'Se', 'selenium'),
    ('Silica', 'Si', 'silica'),
    ('Amorphous silica', 'Si(AMORPH)', 'amorphous silica'),
    ('Silica oxide', 'SiO2', 'silica oxide'),
    ('SiO2, high pressure', 'SIOH', 'SiO2, high pressure'),
    ('Samarium', 'Sm', 'samarium'),
    ('Sm144/Sm152', 'Sm144/Sm152', 'ratio of samarium isotopes Sm144 to Sm152'),
    ('Samarium isotope Sm147', 'Sm147', 'samarium isotope Sm147'),
    ('Sm147/Nd143', 'Sm147/Nd143', 'ratio of samarium isotope Sm147 to neodymium isotope Nd143'),
    ('Sm147/Nd144', 'Sm147/Nd144', 'ratio of samarium isotope Sm147 to neodymium isotope Nd144'),
    ('Sm147/Nd146', 'Sm147/Nd146', 'ratio of samarium to neodymium isotopes Sm147 to Nd146'),
    ('Sm148/Sm152', 'Sm148/Sm152', 'ratio of samarium isotopes Sm148 to Sm152'),
    ('Sm149/Sm152', 'Sm149/Sm152', 'ratio of samarium isotopes Sm149 to Sm152'),
    ('Sm150/Sm152', 'Sm150/Sm152', 'ratio of samarium isotopes Sm150 to Sm152'),
    ('Sm154/Sm152', 'Sm154/Sm152', 'ratio of samarium isotopes Sm154 to Sm152'),
    ('Samarium oxide', 'Sm2O3', 'samarium oxide'),
    ('Tin', 'Sn', 'tin'),
    ('Sulfur dioxide', 'SO2', 'sulfur dioxide'),
    ('Sulfur trioxide', 'SO3', 'sulfur trioxide'),
    ('Sulfate', 'SO4', 'sulfate'),
    ('Strontium', 'Sr', 'strontium'),
    ('Sr/Ca', 'Sr/Ca', 'ratio of Sr to Ca'),
    ('Sr84/Sr86', 'Sr84/Sr86', 'ratio of strontium isotopes Sr84 to Sr86'),
    ('Sr84/Sr88', 'Sr84/Sr88', 'ratio of strontium isotopes Sr84 to Sr88'),
    ('Strontium isotope 86', 'Sr86', 'strontium isotope 86'),
    ('Sr86/Sr88', 'Sr86/Sr88', 'ratio of strontium isotopes Sr86 to Sr88'),
    ('Sr87/Sr86', 'Sr87/Sr86', 'ratio of strontium isotopes Sr87 to Sr86'),
    ('Sr87/Sr86(I)', 'Sr87/Sr86(I)', 'ratio of strontium isotopes Sr87 to Sr86 at initial age'),
    ('Sr87/Sr86(T)', 'Sr87/Sr86(T)', 'ratio of strontium isotopes Sr87 to Sr86, time corrected'),
    ('Sr87/Sr88', 'Sr87/Sr88', 'ratio of strontium isotopes Sr87 to Sr88'),
    ('Sr88/Sr86', 'Sr88/Sr86', 'ratio of strontium isotopes Sr88 to Sr86'),
    ('Strontium oxide', 'SrO', 'strontium oxide'),
    ('Tantalum', 'Ta', 'tantalum'),
    ('Tantalum oxide', 'Ta2O5', 'tantalum oxide'),
    ('Talc', 'TALC', 'talc'),
    ('Terbium', 'Tb', 'terbium'),
    ('Terbium oxide', 'Tb2O3', 'terbium oxide'),
    ('Tellurium', 'Te', 'tellurium'),
    ('Temperature', 'TEMP', 'temperature'),
    ('Thorium', 'Th', 'thorium'),
    ('Th227 reported as activity', 'Th227_ACTIVITY', 'Th227 reported as activity'),
    ('Th228/Th232', 'Th228/Th232', 'ratio of thorium isotopes Th228 to Th232'),
    ('Thorium isotope Th230', 'Th230', 'thorium isotope Th230'),
    ('Thorium isotope Th230, reported as activity', 'Th230_ACTIVITY', 'thorium isotope Th230, reported as activity'),
    ('Th230/Th232', 'Th230/Th232', 'ratio of thorium isotopes Th230 to Th232'),
    ('Th230/Th232_ACTIVITY', 'Th230/Th232_ACTIVITY', 'ratio of thorium isotopes Th230 to Th232, reported as activity'),
    ('Th230/U238', 'Th230/U238', 'ratio of thorium isotope Th230 to uranium isotope U238'),
    ('Th230_U238_ACTIVITY', 'Th230_U238_ACTIVITY', 'ratio of thorium isotope Th230 to uranium isotope U238, reported as activity'),
    ('Excess thorium 230', 'Th230_XS', 'excess thorium 230'),
    ('Thorium 232', 'Th232', 'thorium 232'),
    ('Thorium isotope Th232, reported as activity', 'Th232_ACTIVITY', 'thorium isotope Th232, reported as activity'),
    ('Th232_Pb204', 'Th232_Pb204', 'ratio of thorium isotope Th232 to lead isotope Pb204'),
    ('Th232_Pb208', 'Th232_Pb208', 'ratio of thorium isotope Th232 to lead isotope Pb208'),
    ('Th232_Th230', 'Th232_Th230', 'ratio of isotopes Th232 to Th230'),
    ('Th232/Th230_ACTIVITY', 'Th232/Th230_ACTIVITY', 'ratio of isotopes Th232 to Th230 measured as activity'),
    ('Th232/U238', 'Th232/U238', 'ratio of thorium isotope Th232 to uranium isotope U238'),
    ('Thorium 234', 'Th234', 'thorium 234'),
    ('Thorium 234 excess', 'Th234_XS', 'thorium 234 excess'),
    ('Th238/Th232_ACTIVITY', 'Th238/Th232_ACTIVITY', 'ratio of thorium isotopes Th238 to Th232, reported as activity'),
    ('Thorium monoxide', 'ThO', 'thorium monoxide'),
    ('Thorium dioxide', 'ThO2', 'thorium dioxide'),
    ('Titanium', 'Ti', 'titanium'),
    ('Ti2O3', 'Ti2O3', 'titanium(III) oxide'),
    ('Total inorganic carbon', 'TIC', 'total inorganic carbon'),
    ('Ti-magnetite', 'TI-MT', 'ti-magnetite'),
    ('Titanoniobate', 'TI-NB', 'titanoniobate'),
    ('TiO', 'TiO', 'titanium(II) oxide'),
    ('Titanium oxide', 'TiO2', 'titanium oxide'),
    ('Thallium', 'Tl', 'thallium'),
    ('Tl203/Tl205', 'Tl203/Tl205', 'ratio of thallium isotopes Tl203 to Tl205'),
    ('Tl205/Tl203', 'Tl205/Tl203', 'ratio of thallium isotopes Tl205 to Tl203'),
    ('Thulium', 'Tm', 'thulium'),
    ('Thulium oxide', 'Tm2O3', 'thulium oxide'),
    ('Total organic carbon', 'TOC', 'total organic carbon'),
    ('Total weight percent of analyzed parameters', 'TOTAL', 'total weight percent of analyzed parameters'),
    ('Uranium', 'U', 'uranium'),
    ('U/Zr91', 'U/Zr91', 'ratio of uranium to zirconium isotope Zr91'),
    ('U/Zr92', 'U/Zr92', 'ratio of uranium to zirconium isotope Zr92'),
    ('U230/Th232_ACTIVITY', 'U230/Th232_ACTIVITY', 'ratio of uranium isotope U230 to thorium isotope Th232, reported as activity'),
    ('Uranium isotope U234', 'U234', 'uranium isotope U234'),
    ('Uranium isotope U234, reported as activity', 'U234_ACTIVITY', 'uranium isotope U234, reported as activity'),
    ('U234/U238', 'U234/U238', 'ratio of uranium isotopes U234 to U238'),
    ('U234/U238_ACTIVITY', 'U234/U238_ACTIVITY', 'ratio of uranium isotopes U234 to U238, measured as activity'),
    ('U234/U238_ACTIVITY(T)', 'U234/U238_ACTIVITY(T)', 'ratio of uranium isotopes U234 to U238, measured as activity at time t'),
    ('U235/Pb204', 'U235/Pb204', 'ratio of uranium isotope U235 to lead isotope Pb204'),
    ('U235/Pb207', 'U235/Pb207', 'ratio of uranium isotope U235 to lead isotope Pb207'),
    ('U235/U234', 'U235/U234', 'ratio of isotopes U235 to U234'),
    ('U236/Pb204', 'U236/Pb204', 'ratio of uranium isotope U236 to lead isotope Pb204'),
    ('U236/U238', 'U236/U238', 'ratio of isotopes U236 to U238'),
    ('Uranium isotope U238', 'U238', 'uranium isotope U238'),
    ('Uranium isotope U238, reported as activity', 'U238_ACTIVITY', 'uranium isotope U238, reported as activity'),
    ('U238/Pb204', 'U238/Pb204', 'ratio of uranium isotope U238 to lead isotope Pb204'),
    ('U238/Pb206', 'U238/Pb206', 'ratio of uranium isotope U238 to lead isotope Pb206'),
    ('U238/Pb208', 'U238/Pb208', 'ratio of uranium isotope U238 to lead isotope Pb208'),
    ('U238/Th230', 'U238/Th230', 'ratio of uranium isotope U238 to thorium isotope Th230'),
    ('U238/Th230_ACTIVITY', 'U238/Th230_ACTIVITY', 'ratio of uranium isotope U238 to thorium isotope Th230, reported as activity'),
    ('U238/Th232', 'U238/Th232', 'ratio of uranium isotope U238 to thorium isotope Th232'),
    ('U238/Th232_ACTIVITY', 'U238/Th232_ACTIVITY', 'ratio of uranium isotope U238 to thorium isotope Th232, reported as activity'),
    ('Uranium oxide', 'UO2', 'uranium oxide'),
    ('Vanadium', 'V', 'vanadium'),
    ('Vanadium sesquioxide', 'V2O3', 'vanadium sesquioxide'),
    ('Vanadium pentoxide', 'V2O5', 'vanadium pentoxide'),
    ('Vanadium isotope V48', 'V48', 'vanadium isotope V48'),
    ('Tungsten', 'W', 'tungsten'),
    ('Tungsten isotope', 'W182/W184', 'tungsten isotope'),
    ('Tungsten trioxide', 'WO3', 'tungsten trioxide'),
    ('Xenon', 'Xe', 'xenon'),
    ('Xenon isotope Xe124', 'Xe124', 'xenon isotope Xe124'),
    ('Xe124/Xe126', 'Xe124/Xe126', 'ratio of xenon isotopes Xe124 to Xe126'),
    ('Xe124/Xe130', 'Xe124/Xe130', 'ratio of xenon isotopes Xe124 to Xe130'),
    ('Xe124/Xe132', 'Xe124/Xe132', 'ratio of xenon isotopes Xe124 to Xe132'),
    ('Xenon isotope Xe126', 'Xe126', 'xenon isotope Xe126'),
    ('Xe126/Xe130', 'Xe126/Xe130', 'ratio of xenon isotopes Xe126 to Xe130'),
    ('Xe126/Xe132', 'Xe126/Xe132', 'ratio of xenon isotopes Xe126 to Xe132'),
    ('Xenon isotope Xe128', 'Xe128', 'xenon isotope Xe128'),
    ('Xe128/Xe130', 'Xe128/Xe130', 'ratio of xenon isotopes Xe128 to Xe130'),
    ('Xe128/Xe132', 'Xe128/Xe132', 'ratio of xenon isotopes Xe128 to Xe132'),
    ('Xenon isotope Xe129', 'Xe129', 'xenon isotope Xe129'),
    ('Xe129/Xe130', 'Xe129/Xe130', 'ratio of xenon isotopes Xe129 to Xe130'),
    ('Xe129/Xe132', 'Xe129/Xe132', 'ratio of xenon isotopes Xe129 to Xe132'),
    ('Xe129/Xe136', 'Xe129/Xe136', 'ratio of xenon isotopes Xe129 to Xe136'),
    ('Xenon isotope Xe130', 'Xe130', 'xenon isotope Xe130'),
    ('Xe130/Xe132', 'Xe130/Xe132', 'ratio of xenon isotopes Xe130 to Xe132'),
    ('Xenon isotope Xe131', 'Xe131', 'xenon isotope Xe131'),
    ('Xe131/Xe126', 'Xe131/Xe126', 'ratio of xenon isotopes Xe131 to Xe126'),
    ('Xe131/Xe130', 'Xe131/Xe130', 'ratio of xenon isotopes Xe131 to Xe130'),
    ('Xe131/Xe132', 'Xe131/Xe132', 'ratio of xenon isotopes Xe131 to Xe132'),
    ('Xenon isotope Xe132', 'Xe132', 'xenon isotope Xe132'),
    ('Xe132/Xe130', 'Xe132/Xe130', 'ratio of xenon isotopes Xe132 to Xe130'),
    ('Xenon isotope Xe134', 'Xe134', 'xenon isotope Xe134'),
    ('Xe134/Xe130', 'Xe134/Xe130', 'ratio of xenon isotopes Xe134 to Xe130'),
    ('Xe134/Xe132', 'Xe134/Xe132', 'ratio of xenon isotopes Xe134 to Xe132'),
    ('Xe134/Xe136', 'Xe134/Xe136', 'ratio of xenon isotopes Xe134 to Xe136'),
    ('Xenon isotope Xe136', 'Xe136', 'xenon isotope Xe136'),
    ('Xe136/He4', 'Xe136/He4', 'ratio of xenon isotope Xe136 to helium isotope he4'),
    ('Xe136/Xe130', 'Xe136/Xe130', 'ratio of xenon isotopes Xe136 to Xe130'),
    ('Xe136/Xe132', 'Xe136/Xe132', 'ratio of xenon isotopes Xe136 to Xe132'),
    ('Yttrium', 'Y', 'yttrium'),
    ('Y2O3', 'Y2O3', 'yttrium(III) oxide'),
    ('Yttrium oxide', 'YO2', 'yttrium oxide'),
    ('Ytterbium', 'Yb', 'ytterbium'),
    ('Yb176/Hf177', 'Yb176/Hf177', 'ratio of ytterbium isotope Yb176 to hafnium isotope Hf177'),
    ('Ytterbium oxide', 'Yb2O3', 'ytterbium oxide'),
    ('Zinc', 'Zn', 'zinc'),
    ('Zinc oxide', 'ZnO', 'zinc oxide'),
    ('Zirconium', 'Zr', 'zirconium'),
    ('Zirconium pentoxide', 'Zr2O3', 'zirconium pentoxide'),
    ('Zirconium oxide', 'ZrO2', 'zirconium oxide'),
]
"""Static list of valid geochemical analytes. Used to populate GeoChemicalAnalytes table."""

concordance_formats = [('Concordance ratio', 'Con', 'Ratio agreement between the 206Pb/238U age to the 207Pb/235U age'),
                       ('Concordance percent', 'Con%',
                        'Percent agreement between the 206Pb/238U age and the 207Pb/235U age'),
                       ('Discordance ratio', 'Dis',
                        'Ratio disagreement between  the 206Pb/238U age to the 207Pb/206Pb age'),
                       ('Discordance percent', 'Dis%',
                        'Percent disagreement between the 206Pb/238U age and the 207Pb/206Pb age')]
"""Static list of valid concordance formats. Used to create ConcordanceFormats table."""

concordance_formats_v103 = [('Concordance ratio', 'Con', 'Ratio agreement between the 206Pb/238U age to the 207Pb/235U age'),
                       ('Concordance percent', 'Con%',
                        'Percent agreement between the 206Pb/238U age and the 207Pb/235U age'),
                       ('Discordance ratio', 'Dis',
                        'Ratio disagreement between  the 206Pb/238U age to the 207Pb/206Pb age'),
                       ('Discordance percent', 'Dis%',
                        'Percent disagreement between the 206Pb/238U age and the 207Pb/206Pb age'),
                       ('Minimum segmented discordance', 'MinSegDis',
                        'Minimum of |206Pb/238U-207Pb/235U| ages and |206Pb/207Pb-207Pb/235U| ages')]
"""Static list of valid concordance formats. Used to create ConcordanceFormats table."""

direction_units = [('North', 'N','positive north'),
                   ('South', 'S','positive south'),
                   ('East', 'E','positive east'),
                   ('West', 'W','positive west')]
"""Static list of valid direction units. Used to create DirectionUnits table."""

distance_units = [('Kilometers', 'km', '1000'),
                  ('Meters', 'm', '1'),
                  ('Centimeters', 'cm', '0.01'),
                  ('Millimeter', 'mm', '0.001'),
                  ('Micrometer', 'µm', '0.000001'),
                  ('Miles', 'mi', '5280'),
                  ('Yards', 'yd', '3'),
                  ('Feet', 'ft', '1'),
                  ('Inches', 'in', f'(1/12)')]
"""Static list of valid distance units. Used to create DistanceUnits table."""

error_formats = [('1 sigma absolute', '1σ abs', '1σ absolute uncertainty'),
                 ('2 sigma absolute', '2σ abs', '2σ absolute uncertainty'),
                 ('1 sigma percent', '1σ %', '1σ percent uncertainty'),
                 ('2 sigma percent', '2σ %', '2σ percent uncertainty')]
"""Static list of valid error formats. Used to create ErrorFormats table."""

gps_formats = [
    ('Decimal degrees positive/negative', 'DD +/-', 'Decimal degrees with positive N and E and negative S and W'),
    ('Decimal degrees cardinal', 'DD NSEW', 'Decimal degrees with cardinal directions'),
    ('Degrees minutes positive/negative', 'DDM +/-',
     'Degrees and decimal minutes with positive N and E and negative S and W'),
    ('Degrees minutes cardinal', 'DDM NSEW', 'Degrees and decimal minutes with cardinal directions'),
    ('Degrees minutes seconds positive/negative', 'DMS +/-',
     'Degrees, minutes, and seconds with positive N and E and negative S and W'),
    ('Degrees minutes seconds cardinal', 'DMS NSEW', 'Degrees, minutes, and seconds with cardinal directions'),
    ('Universal Transverse Mercator (standard)', 'UTM', 'Universal Transverse Mercator (standard) with zone, northing, and easting')]
"""Static list of valid GPS formats. Used to create GPSFormats table."""

export_formats = [
    'Custom',
    'detritalPy',
    'IsoplotR - 07/35, 06/38, 04/38, 07/06, 04/07, 04/06',
    'IsoplotR - 38/06, 07/06',
    'DZstats',
    'DZmix, DZmds, DZnmf',
    'AgeCalcML concordia',
    'Database'
]

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

view_attributes_dict = {
    'SampleView': [qsample_id, qsample_name, qigsn, qsample_description, qgps, qsample_elev, qsample_age,
                   qsample_age_constraints, qsample_age_interpretations, qsample_age_references, qcolumn_name,
                   qsample_column_data, qage_signatures, qregions, qrock_types, qsample_contexts, qsampling_methods,
                   qsettings, qunits, qaliquots, qaliquot_contexts, qgrain_count, qgrain_compositions, qgrain_contexts,
                   qspot_count, qspot_compositions, qspot_contexts, qupb_count, qupb_lab_facilities, qupb_instruments,
                   qupb_analysis_methods, qupb_ratio_error_formats, qupb_age_units, qupb_age_error_formats,
                   qupb_concordance_formats, qupb_spot_sizes, qupb_rejection_reasons, qupb_contexts, qupb_age_interpretations,
                   qupb_references, qgeochem_count, qgeochem_lab_facilities, qgeochem_instruments, qgeochem_methods,
                   qgeochem_analyte_error_formats, qgeochem_analyte_units, qgeochem_rejection_reasons, qgeochem_contexts,
                   qgeochem_references, qsample_created, qsample_modified],
    'SampleEditView': [qsample_id, qsample_name, qigsn, qsample_description, qgps_display, qsample_elev_display,
                       qsample_age_display, qsample_age_constraints, qsample_age_interpretations,
                       qsample_age_references, qcolumn_name, qsample_column_height_depth,
                       qsample_column_height_depth_error, qsample_column_data_unit, qage_signatures, qregions,
                       qrock_types, qsample_contexts, qsampling_methods, qsettings, qunits, qaliquots, qaliquot_contexts,
                       qgrain_count, qgrain_compositions, qgrain_contexts, qspot_count, qspot_compositions,
                       qspot_contexts, qupb_count, qupb_lab_facilities, qupb_instruments, qupb_analysis_methods,
                       qupb_ratio_error_formats, qupb_age_units, qupb_age_error_formats, qupb_concordance_formats,
                       qupb_spot_size, qupb_spot_size_unit, qupb_rejection_reasons, qupb_references, qupb_contexts,
                       qupb_age_interpretations, qgeochem_count, qgeochem_lab_facilities, qgeochem_instruments,
                       qgeochem_methods, qgeochem_analyte_error_formats, qgeochem_analyte_units,
                       qgeochem_rejection_reasons, qgeochem_contexts, qgeochem_references, qsample_created,
                       qsample_modified],
    'ColumnView': [qcolumn_id, qcolumn_name, qcolumn_description, qcolumn_calc_total_height_depth, qcolumn_gps,
                   qcolumn_elev, qcolumn_created, qcolumn_modified],
    'ColumnEditView': [qcolumn_id, qcolumn_name, qcolumn_description, qcolumn_total_height_depth,
                       qcolumn_total_height_depth_unit, qcolumn_gps_display, qcolumn_elev_display, qcolumn_elev_unit,
                       qcolumn_created, qcolumn_modified],
    'AliquotView': [qaliquot_id, qaliquot_parent_id, qaliquot_parent_row, qaliquot_name, qaliquot_description,
                    qsample_id, qaliquot_sample, qaliquot_contexts, qgrain_count, qgrain_compositions, qgrain_contexts,
                    qspot_count, qspot_compositions, qspot_contexts, qupb_count, qupb_lab_facilities,
                    qupb_analysis_methods, qupb_instruments, qupb_ratio_error_formats, qupb_age_units,
                    qupb_age_error_formats, qupb_concordance_formats, qupb_spot_sizes, qupb_rejection_reasons,
                    qupb_contexts, qupb_age_interpretations, qupb_references, qgeochem_count, qgeochem_lab_facilities,
                    qgeochem_instruments, qgeochem_methods, qgeochem_analyte_error_formats, qgeochem_analyte_units,
                    qgeochem_rejection_reasons, qgeochem_contexts, qgeochem_references, qaliquot_created,
                    qaliquot_modified],
    'AliquotEditView': [qaliquot_id, qaliquot_parent_id, qaliquot_parent_row, qaliquot_name, qaliquot_description,
                        qsample_id, qaliquot_sample, qaliquot_contexts, qaliquot_created, qaliquot_modified],
    'GrainView': [qgrain_id, qaliquot_id, qsample_id, qgrain_name, qgrain_description, qaliquot_name, qsample_name,
                  qspots, qaliquot_name, qsample_name, qgrain_composition, qgrain_contexts, qspot_compositions,
                  qspot_contexts, qupb_count, qupb_lab_facilities, qupb_instruments, qupb_analysis_methods,
                  qupb_ratio_error_formats, qupb_age_units, qupb_age_error_formats, qupb_concordance_formats,
                  qupb_spot_sizes, qupb_rejection_reasons, qupb_contexts, qupb_age_interpretations, qupb_references,
                  qgeochem_count, qgeochem_lab_facilities, qgeochem_instruments, qgeochem_methods,
                  qgeochem_analyte_error_formats, qgeochem_analyte_units, qgeochem_rejection_reasons, qgeochem_contexts,
                  qgeochem_references, qgrain_created, qgrain_modified],
    'GrainEditView': [qgrain_id, qaliquot_id, qsample_id, qgrain_name, qgrain_description, qaliquot_name, qsample_name,
                      qgrain_composition, qgrain_contexts, qgrain_created, qgrain_modified],
    'SpotView': [qspot_id, qgrain_id, qaliquot_id, qsample_id, qspot_name, qspot_description, qgrain_name,
                 qaliquot_name, qsample_name, qspot_compositions, qspot_contexts, qgrain_composition, qgrain_contexts,
                 qupb_analyses, qupb_count, qupb_lab_facilities, qupb_instruments, qupb_analysis_methods,
                 qupb_ratio_error_formats, qupb_age_units, qupb_age_error_formats, qupb_concordance_formats,
                 qupb_spot_sizes, qupb_rejection_reasons, qupb_contexts, qupb_age_interpretations, qupb_references,
                 qgeochem_count, qgeochem_lab_facilities, qgeochem_instruments, qgeochem_methods,
                 qgeochem_analyte_error_formats, qgeochem_analyte_units, qgeochem_rejection_reasons, qgeochem_contexts,
                 qgeochem_references, qspot_created, qspot_modified],
    'SpotEditView': [qspot_id, qgrain_id, qaliquot_id, qsample_id, qspot_name, qspot_description, qgrain_name,
                     qaliquot_name, qsample_name, qspot_compositions, qspot_contexts, qspot_created, qspot_modified],
    'UPbView': [qupb_id, qspot_id, qgrain_id, qaliquot_id, qsample_id, qupb_analysis_name, qupb_analysis_description,
                qspot_name, qgrain_name, qaliquot_name, qsample_name, qupb_reference, qupb_lab_facility,
                qupb_instrument, qupb_analysis_method, qupb_204cps, qupb_206cps, qupb_207cps, qupb_208cps, qupb_pbcps,
                qupb_232cps, qupb_235cps, qupb_238cps, qupb_uppm, qupb_thppm, qupb_pbppm, qupb_calc_uth, qupb_calc_thu,
                qupb_calc_206207, qupb_calc_206207_error, qupb_calc_207206, qupb_calc_207206_error, qupb_calc_207235,
                qupb_calc_207235_error, qupb_calc_235207, qupb_calc_235207_error, qupb_calc_206238, qupb_calc_206238_error,
                qupb_calc_238206, qupb_calc_238206_error, qupb_calc_208232, qupb_calc_208232_error, qupb_calc_232208,
                qupb_calc_232208_error, qupb_calc_238232, qupb_calc_238232_error, qupb_calc_232238, qupb_calc_232238_error,
                qupb_calc_204238, qupb_calc_204238_error, qupb_calc_238204, qupb_calc_238204_error, qupb_calc_206204,
                qupb_calc_206204_error, qupb_calc_204206, qupb_calc_204206_error, qupb_calc_207204, qupb_calc_207204_error,
                qupb_calc_204207, qupb_calc_204207_error, qupb_calc_208204, qupb_calc_208204_error, qupb_calc_204208,
                qupb_calc_204208_error, qupb_ratio_error_format, qupb_calc_207206_age, qupb_calc_207206_age_error,
                qupb_calc_206238_age, qupb_calc_206238_age_error, qupb_calc_207235_age, qupb_calc_207235_age_error,
                qupb_calc_208232_age, qupb_calc_208232_age_error, qupb_calc_best_age, qupb_calc_best_age_error,
                qupb_calc_best_age_filled, qupb_calc_best_age_filled_error, qupb_age_error_format, qupb_age_unit,
                qupb_age_interpretation, qupb_calc_spot_size, qupb_calc_concordance_68v76, qupb_error_corr_68v76,
                qupb_calc_concordance_68v75, qupb_error_corr_68v75, qupb_concordance_format, qupb_minsegdisc,
                qupb_calc_spot_size, qupb_rejected, qupb_rejection_reasons, qupb_contexts, qupb_created, qupb_modified],
    'UPbEditView': [qupb_id, qspot_id, qgrain_id, qaliquot_id, qsample_id, qupb_analysis_name, qupb_analysis_description,
                    qspot_name, qgrain_name, qaliquot_name, qsample_name, qupb_reference, qupb_lab_facility,
                    qupb_instrument, qupb_analysis_method, qupb_204cps, qupb_206cps, qupb_207cps, qupb_208cps,
                    qupb_pbcps, qupb_232cps, qupb_235cps, qupb_238cps, qupb_uppm, qupb_thppm, qupb_pbppm, qupb_uth,
                    qupb_thu, qupb_206207, qupb_206207_error, qupb_207206, qupb_207206_error, qupb_206238,
                    qupb_206238_error, qupb_238206, qupb_238206_error, qupb_207235, qupb_207235_error, qupb_235207,
                    qupb_235207_error, qupb_208232, qupb_208232_error, qupb_232208, qupb_232208_error, qupb_238232,
                    qupb_238232_error, qupb_232238, qupb_232238_error, qupb_204238, qupb_204238_error, qupb_238204,
                    qupb_238204_error, qupb_206204, qupb_206204_error, qupb_204206, qupb_204206_error, qupb_207204,
                    qupb_207204_error, qupb_204207, qupb_204207_error, qupb_208204, qupb_208204_error, qupb_204208,
                    qupb_204208_error, qupb_ratio_error_format, qupb_207206_age, qupb_207206_age_error,
                    qupb_206238_age, qupb_206238_age_error, qupb_207235_age, qupb_207235_age_error, qupb_208232_age,
                    qupb_208232_age_error, qupb_best_age, qupb_best_age_error, qupb_best_age_filled,
                    qupb_best_age_filled_error, qupb_age_error_format, qupb_age_unit, qupb_age_interpretation,
                    qupb_concordance_68v76, qupb_error_corr_68v76, qupb_concordance_68v75, qupb_error_corr_68v75,
                    qupb_concordance_format, qupb_minsegdisc, qupb_spot_size, qupb_spot_size_unit, qupb_rejected, qupb_rejection_reasons,
                    qupb_contexts, qupb_created, qupb_modified],
    'ReferenceView': [qreference_id, qreference_display, qauthors, qyear, qtitle, qsource, qdoi, qreference_description,
                      qreference_created, qreference_modified],
    'GeoChemView': [qgeochem_id, qspot_id, qgrain_id, qaliquot_id, qsample_id, qgeochem_analysis_name,
                    qspot_name, qgrain_name, qaliquot_name, qsample_name, qgeochem_method, qgeochem_lab_facility,
                    qgeochem_instrument, qgeochem_reference, qgeochem_rejected, qgeochem_rejection_reasons,
                    qgeochem_contexts, qgeochem_analyte_unit, qgeochem_analyte_error_format, qgeochem_created,
                    qgeochem_modified],
    'GeoChemEditView': [qgeochem_id, qspot_id, qgrain_id, qaliquot_id, qsample_id, qgeochem_analysis_name,
                        qspot_name, qgrain_name, qaliquot_name, qsample_name, qgeochem_method, qgeochem_lab_facility,
                        qgeochem_instrument, qgeochem_reference, qgeochem_rejected, qgeochem_rejection_reasons,
                        qgeochem_contexts, qgeochem_created, qgeochem_modified]
}


# dictionary of Views and their associated settings_value for columns to display throughout GeoCORK
view_setting_dict = {
    'SampleView': 'sample_view_columns',
    'SampleEditView': 'sample_edit_columns',
    'AliquotView': 'aliquot_view_columns',
    'AliquotEditView': 'aliquot_edit_columns',
    'GrainView': 'grain_view_columns',
    'GrainEditView': 'grain_edit_columns',
    'SpotView': 'spot_view_columns',
    'SpotEditView': 'spot_edit_columns',
    'UPbView': 'upb_analysis_view_columns',
    'UPbEditView': 'upb_analysis_edit_columns',
    'ColumnView': 'column_view_columns',
    'ColumnEditView': 'column_edit_columns',
    'ReferenceView': 'reference_view_columns',
    'GeoChemView': 'geochem_analysis_view_columns',
    'GeoChemEditView': 'geochem_analysis_edit_columns',
}

sample_possible_user_input_fields = {
    'Sample Info': {
        'Sample Name': ['Samples', 'SampleName'],
        'Sample IGSN': ['Samples', 'SampleIGSN'],
        'Sample Description': ['Samples', 'SampleDescription'],
        'Sample Context': ['SampleContexts', 'SampleContextName'],
        'Sample Context Description': ['SampleContexts', 'SampleContextDescription'],
        'Sampling Method': ['SamplingMethods', 'SamplingMethodName'],
        'Sampling Method Description': ['SamplingMethods', 'SamplingMethodDescription'],
        'Region': ['Regions', 'RegionName'],
        'Region Description': ['Regions', 'RegionDescription'],
        'Setting': ['Settings', 'SettingName'],
        'Setting Description': ['Settings', 'SettingDescription'],
        'Rock Type': ['RockTypes', 'RockTypeName'],
        'Rock Type Description': ['RockTypes', 'RockTypeDescription'],
        'Unit': ['Units', 'UnitName'],
        'Unit Description': ['Units', 'UnitDescription']
    },
    'Default Sample Age': {
        'Direct Age': ['SampleAges', 'DirectAge'],
        'Direct Age Error': ['SampleAges', 'DirectAgeError'],
        'Direct Age Error Format': ['SampleAges', 'DirectAgeErrorFormatID'],
        'Direct Age Unit': ['SampleAges', 'DirectAgeUnitID'],
        'Oldest Direct Age': ['SampleAges', 'OldestDirectAge'],
        'Youngest Direct Age': ['SampleAges', 'YoungestDirectAge'],
        'Oldest Relative Age': ['SampleAges', 'OldestAgeID'],
        'Youngest Relative Age': ['SampleAges', 'YoungestAgeID'],
        'Age Description': ['SampleAges', 'SampleAgeDescription'],
        'Age Constraint': ['AgeConstraints', 'AgeConstraintName'],
        'Age Constraint Description': ['AgeConstraints', 'AgeConstraintDescription'],
        'Age Interpretation': ['AgeInterpretations', 'AgeInterpretationName'],
        'Age Interpretation Description': ['AgeInterpretations', 'AgeInterpretationDescription'],
        'Age Signature': ['AgeSignatures', 'AgeSignatureName'],
        'Age Signature Description': ['AgeSignatures', 'AgeSignatureDescription']
    }
}

gps_possible_user_input_fields = {
    'Sample GPS': {
        'Sample Latitude degrees': ['GPSLocations', 'GPSLatDeg'],
        'Sample Latitude minutes': ['GPSLocations', 'GPSLatMin'],
        'Sample Latitude seconds': ['GPSLocations', 'GPSLatSec'],
        'Sample Latitude direction': ['GPSLocations', 'GPSLatDirectionID'],
        'Sample Longitude degrees': ['GPSLocations', 'GPSLonDeg'],
        'Sample Longitude minutes': ['GPSLocations', 'GPSLonMin'],
        'Sample Longitude seconds': ['GPSLocations', 'GPSLonSec'],
        'Sample Longitude direction': ['GPSLocations', 'GPSLonDirectionID'],
        'Sample Easting': ['GPSLocations', 'GPSUTME'],
        'Sample Northing': ['GPSLocations', 'GPSUTMN'],
        'Sample Zone': ['GPSLocations', 'GPSUTMZone'],
        'Sample Elevation': ['GPSLocations', 'GPSElev'],
        'Sample Elevation Error': ['GPSLocations', 'GPSElevError'],
        'Sample Elevation Unit': ['GPSLocations', 'GPSElevUnitID']
    },
    'Column GPS': {
        'Column Latitude degrees': ['GPSLocations', 'GPSLatDeg'],
        'Column Latitude minutes': ['GPSLocations', 'GPSLatMin'],
        'Column Latitude seconds': ['GPSLocations', 'GPSLatSec'],
        'Column Latitude direction': ['GPSLocations', 'GPSLatDirectionID'],
        'Column Longitude degrees': ['GPSLocations', 'GPSLonDeg'],
        'Column Longitude minutes': ['GPSLocations', 'GPSLonMin'],
        'Column Longitude seconds': ['GPSLocations', 'GPSLonSec'],
        'Column Longitude direction': ['GPSLocations', 'GPSLonDirectionID'],
        'Column Easting': ['GPSLocations', 'GPSUTME'],
        'Column Northing': ['GPSLocations', 'GPSUTMN'],
        'Column Zone': ['GPSLocations', 'GPSUTMZone'],
        'Column Elevation': ['GPSLocations', 'GPSElev'],
        'Column Elevation Error': ['GPSLocations', 'GPSElevError'],
        'Column Elevation Unit': ['GPSLocations', 'GPSElevUnitID']
    }
}

column_possible_user_input_fields = {
    'Column Info': {
        'Column Name': ['Columns', 'ColumnName'],
        'Column Description': ['Columns', 'ColumnDescription'],
        'Column Total Height/Depth': ['Columns', 'ColumnTotalHeightDepth'],
        'Column Total Height/Depth Unit': ['Columns', 'ColumnTotalHeightDepthUnitID'],
        'Sample Height/Depth': ['Samples', 'HeightDepth'],
        'Sample Height/Depth Error': ['Samples', 'HeightDepthError'],
        'Sample Height/Depth Unit': ['Samples', 'HeightDepthUnitID']
    }
}

aliquot_grain_spot_possible_user_input_fields = {
    'Aliquot Info': {
        'Aliquot Name': ['Aliquots', 'AliquotName'],
        'Aliquot Description': ['Aliquots', 'AliquotDescription'],
        'Aliquot Context': ['AliquotContexts', 'AliquotContextName'],
        'Aliquot Context Description': ['AliquotContexts', 'AliquotContextDescription']
    },
    'Grain Info': {
        'Grain Name': ['Grains', 'GrainName'],
        'Grain Description': ['Grains', 'GrainDescription'],
        'Grain Composition': ['GrainCompositions', 'GrainCompositionName'],
        'Grain Composition Description': ['GrainCompositions', 'GrainCompositionDescription'],
        'Grain Context': ['GrainContexts', 'GrainContextName'],
        'Grain Context Description': ['GrainContexts', 'GrainContextDescription']
    },
    'Spot Info': {
        'Spot Name': ['Spots', 'SpotName'],
        'Spot Description': ['Spots', 'SpotDescription'],
        'Spot Composition': ['SpotCompositions', 'SpotCompositionName'],
        'Spot Composition Description': ['SpotCompositions', 'SpotCompositionDescription'],
        'Spot Context': ['SpotContexts', 'SpotContextName'],
        'Spot Context Description': ['SpotContexts', 'SpotContextDescription'],
        'UPb Spot Size': ['UPbAnalyses', 'SpotSize'],
        'UPb Spot Size Unit': ['UPbAnalyses', 'SpotSizeUnitID'],
        'Geochemical Spot Size': ['GeoChemicalAnalyses', 'SpotSize'],
        'Geochemical Spot Size Unit': ['GeoChemicalAnalyses', 'SpotSizeUnitID']
    }
}

reference_possible_user_input_fields = {
    'Reference': {
        'Authors': ['References', 'Authors'],
        'Year': ['References', 'Year'],
        'Title': ['References', 'Title'],
        'Source': ['References', 'Source'],
        'DOI': ['References', 'DOI'],
        'Reference Description': ['References', 'ReferenceDescription'],
        'Reference Display': ['References', 'ReferenceDisplay']
    }
}

upb_possible_user_input_fields = {
    'U-Pb Base Info': {
        'UPb Analysis Name': ['UPbAnalyses', 'UPbAnalysisName'],
        'UPb Analysis Description': ['UPbAnalyses', 'UPbAnalysesDescription'],
        'UPb Analysis Context': ['UPbAnalysisContexts', 'UPbAnalysisContext'],
        'UPb Analysis Context Description': ['UPbAnalysisContexts', 'UPbAnalysisContextDescription'],
        'Lab Facility Name': ['LabFacilities', 'LabFacilityName'],
        'Lab Facility Description': ['LabFacilities', 'LabFacilityDescription'],
        'Instrument Name': ['Instruments', 'InstrumentName'],
        'Instrument Description': ['Instruments', 'InstrumentDescription'],
        'UPb Analysis Method Name': ['UPbAnalysisMethods', 'UPbAnalysisMethodName'],
        'UPb Analysis Method Description': ['UPbAnalysisMethods', 'UPbAnalysisMethodDescription'],
        'Rejected': ['UPbAnalyses', 'Rejected'],
        'Rejection Reason': ['UPbRejectionReasons', 'UPbRejectionReasonName'],
        'Rejection Reason Description': ['UPbRejectionReasons', 'UPbRejectionReasonDescription']
    },
    'Ratios': {
        'U/Th': ['UPbAnalyses', 'U/Th'],
        'Th/U': ['UPbAnalyses', 'Th/U'],
        '206Pb/204Pb': ['UPbAnalyses', '206Pb/204Pb'],
        '206Pb/204Pb Error': ['UPbAnalyses', '206Pb/204PbError'],
        '204Pb/206Pb': ['UPbAnalyses', '204Pb/206Pb'],
        '204Pb/206Pb Error': ['UPbAnalyses', '204Pb/206PbError'],
        '207Pb/204Pb': ['UPbAnalyses', '207Pb/204Pb'],
        '207Pb/204Pb Error': ['UPbAnalyses', '207Pb/204PbError'],
        '204Pb/207Pb': ['UPbAnalyses', '204Pb/207Pb'],
        '204Pb/207Pb Error': ['UPbAnalyses', '204Pb/207PbError'],
        '208Pb/204Pb': ['UPbAnalyses', '208Pb/204Pb'],
        '208Pb/204Pb Error': ['UPbAnalyses', '208Pb/204PbError'],
        '204Pb/208Pb': ['UPbAnalyses', '204Pb/208Pb'],
        '204Pb/208Pb Error': ['UPbAnalyses', '204Pb/208PbError'],
        '206Pb/207Pb': ['UPbAnalyses', '206Pb/207Pb'],
        '206Pb/207Pb Error': ['UPbAnalyses', '206Pb/207PbError'],
        '207Pb/206Pb': ['UPbAnalyses', '207Pb/206Pb'],
        '207Pb/206Pb Error': ['UPbAnalyses', '207Pb/206PbError'],
        '204Pb/238U': ['UPbAnalyses', '204Pb/238U'],
        '204Pb/238U Error': ['UPbAnalyses', '204Pb/238UError'],
        '238U/204Pb': ['UPbAnalyses', '238U/204Pb'],
        '238U/204Pb Error': ['UPbAnalyses', '238U/204PbError'],
        '206Pb/238U': ['UPbAnalyses', '206Pb/238U'],
        '206Pb/238U Error': ['UPbAnalyses', '206Pb/238UError'],
        '238U/206Pb': ['UPbAnalyses', '238U/206Pb'],
        '238U/206Pb Error': ['UPbAnalyses', '238U/206PbError'],
        '207Pb/235U': ['UPbAnalyses', '207Pb/235U'],
        '207Pb/235U Error': ['UPbAnalyses', '207Pb/235UError'],
        '235U/207Pb': ['UPbAnalyses', '235U/207Pb'],
        '235U/207Pb Error': ['UPbAnalyses', '235U/207PbError'],
        '208Pb/232Th': ['UPbAnalyses', '208Pb/232Th'],
        '208Pb/232Th Error': ['UPbAnalyses', '208Pb/232ThError'],
        '232Th/208Pb': ['UPbAnalyses', '232Th/208Pb'],
        '232Th/208Pb Error': ['UPbAnalyses', '232Th/208PbError'],
        '238U/232Th': ['UPbAnalyses', '238U/232Th'],
        '238U/232Th Error': ['UPbAnalyses', '238U/232ThError'],
        '232Th/238U': ['UPbAnalyses', '232Th/238U'],
        '232Th/238U Error': ['UPbAnalyses', '232Th/238UError'],
        'ErrorCorr/Rho_68v76': ['UPbAnalyses', 'ErrorCorr/Rho_68v76'],
        'ErrorCorr/Rho_68v75': ['UPbAnalyses', 'ErrorCorr/Rho_68v75']
    },
    'Ages': {
        '207Pb/206PbAge': ['UPbAnalyses', '207Pb/206PbAge'],
        '207Pb/206PbAge Error': ['UPbAnalyses', '207Pb/206PbAgeError'],
        '207Pb/235UAge': ['UPbAnalyses', '207Pb/235UAge'],
        '207Pb/235UAge Error': ['UPbAnalyses', '207Pb/235UAgeError'],
        '206Pb/238UAge': ['UPbAnalyses', '206Pb/238UAge'],
        '206Pb/238UAge Error': ['UPbAnalyses', '206Pb/238UAgeError'],
        '208Pb/232ThAge': ['UPbAnalyses', '208Pb/232ThAge'],
        '208Pb/232ThAge Error': ['UPbAnalyses', '208Pb/232ThAgeError'],
        'Best Age': ['UPbAnalyses', 'BestAge'],
        'Best Age Error': ['UPbAnalyses', 'BestAgeError'],
        'Age Unit': ['UPbAnalyses', 'AgeUnitID'],
        'Age Error Format': ['UPbAnalyses', 'AgeErrorFormatID'],
        'Concordance_206Pb/238Uv207Pb/206Pb': ['UPbAnalyses', 'Concordance_206Pb/238Uv207Pb/206Pb'],
        'Concordance_206Pb/238Uv207Pb/235U': ['UPbAnalyses', 'Concordance_206Pb/238Uv207Pb/235U'],
        'Concordance Format': ['UPbAnalyses', 'ConcordanceFormatID'],
        'Minimum Segmented Discordance': ['UPbAnalyses', 'MinimumSegmentedDiscordance'],
        'Age Interpretation': ['AgeInterpretations', 'AgeInterpretationName'],
        'Age Interpretation Description': ['AgeInterpretations', 'AgeInterpretationDescription']
    },
    'Isotope Counts': {
        'Pb204cps': ['UPbAnalyses', 'Pb204cps'],
        'Pb206cps': ['UPbAnalyses', 'Pb206cps'],
        'Pb207cps': ['UPbAnalyses', 'Pb207cps'],
        'Pb208cps': ['UPbAnalyses', 'Pb208cps'],
        'Pb*cps': ['UPbAnalyses', 'Pb*cps'],
        'Th232cps': ['UPbAnalyses', 'Th232cps'],
        'U235cps': ['UPbAnalyses', 'U235cps'],
        'U238cps': ['UPbAnalyses', 'U238cps'],
        'Uppm': ['UPbAnalyses', 'Uppm'],
        'Thppm': ['UPbAnalyses', 'Thppm'],
        'Pbppm': ['UPbAnalyses', 'Pbppm'],
    },
}

geochem_possible_user_input_fields = {
    'Geochemical Base Info': {
        'Geochemical Analysis Name': ['GeoChemicalAnalyses', 'GeoChemAnalysisName'],
        'Geochemical Analysis Description': ['GeoChemicalAnalyses', 'GeoChemAnalysisDescription'],
        'Geochemical Analysis Context': ['GeoChemicalAnalysisContexts', 'GeoChemicalAnalysisContext'],
        'Geochemical Analysis Context Description': ['GeoChemicalAnalysisContexts', 'GeoChemicalAnalysisContextDescription'],
        'Geochemical Analyte Name': ['GeoChemicalAnalytes', 'GeoChemAnalyteName'],
        'Geochemical Analyte Description': ['GeoChemicalAnalytes', 'GeoChemAnalyteDescription'],
        'Lab Facility Name': ['LabFacilities', 'LabFacilityName'],
        'Lab Facility Description': ['LabFacilities', 'LabFacilityDescription'],
        'Instrument Name': ['Instruments', 'InstrumentName'],
        'Instrument Description': ['Instruments', 'InstrumentDescription'],
        'Geochemical Analysis Method Name': ['GeoChemicalMethods', 'GeoChemicalMethodName'],
        'Geochemical Analysis Method Description': ['GeoChemicalMethods', 'GeoChemicalMethodDescription'],
        'Rejected': ['GeoChemicalAnalyses', 'Rejected'],
        'Rejection Reason': ['GeoChemRejectionReasons', 'GeoChemRejectionReasonName'],
        'Rejection Reason Description': ['GeoChemRejectionReasons', 'GeoChemRejectionReasonDescription']
    },
    'Geochemical Analytes': {'Geochemical Analysis Units': ['GeoChemicalAnalyses', 'GeoChemAnalyteUnitID']},
    'Geochemical Analyte Errors': {'Geochemical Error Formats': ['GeoChemicalAnalyses', 'GeoChemAnalyteErrorFormatID']}
}
"""Dictionaries of User-readable columns/info able to be imported into the database with list of their associated table 
    and column name. Importer Category: {UserReadableColumnName: [TableName, ColumnName]}"""

combo_box_possible_input_fields = {
    'UPb Reference': ['References', 'ReferenceID', 'ReferenceDisplay'],
    'UPb Instrument': ['Instruments', 'InstrumentID', 'InstrumentName'],
    'UPb Lab Facility': ['LabFacilities', 'LabFacilityID', 'LabFacilityName'],
    'UPb Analysis Method': ['UPbAnalysisMethods', 'UPbAnalysisMethodID', 'UPbAnalysisMethodName'],
    'Elevation Unit': ['GPSLocations', 'GPSElevUnitID'],
    'Height/Depth Unit': {
        'Samples': ['Samples', 'HeightDepthUnitID'],
        'Columns': ['Columns', 'ColumnTotalHeightDepthUnitID']
    },
    'Sample Age Error': ['SampleAges', 'DirectAgeErrorFormatID'],
    'Age Unit': {
        'Samples': ['SampleAges', 'DirectAgeUnitID'],
        'UPbAnalyses': ['UPbAnalyses', 'AgeUnitID']
    },
    'UPb Age Error': ['UPbAnalyses', 'AgeErrorFormatID'],
    'UPb Ratio Error': ['UPbAnalyses', 'RatioErrorFormatID'],
    'UPb Spot Size Unit': ['UPbAnalyses', 'SpotSizeUnitID'],
    'Concordance Format': ['UPbAnalyses', 'ConcordanceFormatID']
}
"""Dictionaries of User-readable columns/info able to be imported from combo boxes with list of their associated table"""

possible_database_input_fields = [
    'SampleID', 'SampleName', 'SampleIGSN', 'SampleDescription',
    'HeightDepth', 'HeightDepthError', 'HeightDepthUnitID',
    'SampleContextName', 'SamplingMethodName',
    'RegionName', 'SettingName', 'RockTypeName', 'UnitName',

    'DirectAge', 'DirectAgeError', 'DirectAgeErrorFormatID', 'DirectAgeUnitID',
    'OldestDirectAge', 'YoungestDirectAge', 'OldestAgeID', 'YoungestAgeID',
    'SampleAgeDescription', 'AgeConstraintName', 'AgeInterpretationName', 'AgeSignatureName',

    'GPSLatDeg', 'GPSLatMin', 'GPSLatSec', 'GPSLatDirectionID', 'GPSLonDeg', 'GPSLonMin', 'GPSLonSec',
    'GPSLonDirectionID', 'GPSUTME', 'GPSUTMN', 'GPSUTMZone', 'GPSElev', 'GPSElevError', 'GPSElevUnitID',

    'ColumnID', 'ColumnName', 'ColumnTotalHeightDepth', 'ColumnTotalHeightDepthUnitID', 'ColumnDescription',

    'ReferenceID', 'Authors', 'Year', 'Title', 'Source', 'DOI', 'ReferenceDescription',

    'AlqiuotID', 'AliquotName', 'AliquotDescription', 'AliquotContextName',

    'GrainID', 'GrainName', 'GrainDescription', 'GrainCompositionName', 'GrainContextName',

    'SpotID', 'SpotName', 'SpotDescription', 'SpotCompositionName', 'SpotContextName',

    'UPbAnalysisID', 'UPbAnalysisName', 'UPbAnalysisDescription', 'UPbAnalysisContextName',
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

    'ErrorCorr/Rho_68v76', 'ErrorCorr/Rho_68v75',
    'RatioErrorFormatID',
    '207Pb/206PbAge', '207Pb/206PbAgeError',
    '207Pb/235UAge', '207Pb/235UAgeError',
    '206Pb/238UAge', '206Pb/238UAgeError',
    '208Pb/232ThAge', '208Pb/232ThAgeError',
    'BestAge', 'BestAgeError',

    'AgeErrorFormatID',
    'AgeUnitID',
    'AgeInterpretationID',
    'Concordance_206Pb/238Uv207Pb/206Pb', 'Concordance_206Pb/238Uv207Pb/235U',
    'ConcordanceFormatID', 'ConcordanceFormatName', 'MinimumSegmentedDiscordance',
    'UPbSpotSize', 'UPbSpotSizeUnitID',

    'GeoChemAnalysisID', 'GeoChemAnalysisName', 'GeoChemAnalysisDescription',
    'GeoChemSpotSize', 'GeoChemSpotSizeUnitID'

    'UPbRejected',
    'RejectionReasonName',

    'LabFacilityID', 'LabFacilityName', 'LabFacilityDescription',
    'InstrumentID', 'InstrumentName', 'InstrumentDescription',
    'UPbAnalysisMethodID', 'UPbAnalysisMethodName', 'UPbAnalysisMethodDescription',
]
"""List of valid columns to be entered through the importer.
No Calculated values should be in this list
Used to create the insert statement with SQL"""

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



def get_join_from_table(join: str, tables: list[str]) -> str:
    """
    Function to take a current SQL join string and append other join strings based upon a list of tables.

    :param str join: Current join statement to add to
    :param list[str] tables: List of tables to append to the join statement
    :return: Final join with added tables
    :rtype: str
    """
    for table in tables:
        match table:
            case 'AgeConstraints':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_constraint_join not in join:
                    join += sampleage_age_constraint_join + '\n'
            case 'AgeInterpretations':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_interpretation_join not in join:
                    join += sampleage_age_interpretation_join + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Ages':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
            case 'OldAge':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
                if sample_age_left_joins not in join:
                    join += sample_age_left_joins + '\n'
            case 'YoungAge':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
                if sample_age_left_joins not in join:
                    join += sample_age_left_joins + '\n'
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
            case 'DefaultSampleAges':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += default_sample_age_join + '\n'
            case 'LabFacilities':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_labs_join not in join:
                    join += upb_labs_join + '\n'
            case 'Grains':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
            case 'GrainCompositions':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
                if grain_composition_join not in join:
                    join += grain_composition_join + '\n'
            case 'GrainContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
                if grain_context_join not in join:
                    join += grain_context_join + '\n'
            case 'GPSLocations':
                if gps_sample_join not in join:
                    join += gps_sample_join + '\n'
                if gps_sample_left_joins not in join:
                    join += gps_sample_left_joins + '\n'
            case 'Instruments':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_instruments_join not in join:
                    join += upb_instruments_join + '\n'
            case 'References' | '"References"':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'ReferenceView':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
            case 'Regions':
                if region_join not in join:
                    join += region_join + '\n'
            case 'UPbRejectionReasons':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_rejection_reason_join not in join:
                    join += upb_rejection_reason_join + '\n'
            case 'GeoChemRejectionReasons':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_rejection_reasons_join not in join:
                    join += geochem_rejection_reasons_join + '\n'
            case 'RockTypes':
                if rock_type_join not in join:
                    join += rock_type_join + '\n'
            case 'SampleAges':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += default_sample_age_join + '\n'
            case 'SampleAgeConstraints':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_constraint_join not in join:
                    join += sampleage_age_constraint_join + '\n'
            case 'SampleAgeInterpretations':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_interpretation_join not in join:
                    join += sampleage_age_interpretation_join + '\n'
            case 'SampleAgeReferences':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_reference_join not in join:
                    join += sampleage_age_reference_join + '\n'
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
            case 'UPbAgeInterpretations':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_age_interpretation_join not in join:
                    join += upb_age_interpretation_join + '\n'
            case 'UPbAnalyses':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
            case 'UPbAnalysisContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_context_join not in join:
                    join += upb_context_join + '\n'
            case 'UPbAnalysisMethods':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_method_join not in join:
                    join += upb_method_join + '\n'
            case 'UPbReferences':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'GeoChemicalAnalyses':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
            case 'GeoChemicalAnalysisContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_contexts_join not in join:
                    join += geochem_contexts_join + '\n'
            case 'GeoChemicalMethods':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_method_join not in join:
                    join += geochem_method_join + '\n'
            case 'GeoChemReferences':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_reference_join not in join:
                    join += geochem_reference_join + '\n'
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'
            case 'Samples':
                pass
    return join