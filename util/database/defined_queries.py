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
qgeochemvalue_id = 'GeoChemicalAnalysisValues.GeoChemAnalysisValueID AS GeoChemAnalysisValueID'
qgeochem_analyte_value = 'GeoChemicalAnalysisValues.GeoChemAnalyteValue AS GeoChemAnalyteValue'
qgeochem_analyte_error = 'GeoChemicalAnalysisValues.GeoChemAnalyteError AS GeoChemAnalyteError'
qgeochem_analyte_unit = 'GeoChemAnalyteUnits.AnalyticalUnitAbbreviation AS GeoChemAnalyteUnitAbbreviation'
qgeochem_analyte_units = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemAnalyteUnits.AnalyticalUnitAbbreviation), ",", "; ") AS GeoChemAnalyteUnitAbbreviation'
qgeochem_analyte_error_format = 'GeoChemAnalyteErrorFormats.ErrorFormatAbbreviation AS GeoChemAnalyteErrorFormatAbbreviation'
qgeochem_analyte_error_formats = 'REPLACE(GROUP_CONCAT(DISTINCT GeoChemAnalyteErrorFormats.ErrorFormatAbbreviation), ",", "; ") AS GeoChemAnalyteErrorFormatAbbreviation'
qgeochemvalue_created = 'GeoChemicalAnalysisValues.GeoChemAnalysisValueCreated AS GeoChemAnalysisValueCreated'
qgeochemvalue_modified = 'GeoChemicalAnalysisValues.GeoChemAnalysisValueModified AS GeoChemAnalysisValueModified'
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