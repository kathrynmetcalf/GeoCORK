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
qsample_age_constraints = 'REPLACE(GROUP_CONCAT(DISTINCT SampleAgeConstraints.AgeConstraintName), ",", "; ") AS SampleAgeConstraintName'
qsample_age_interpretations = 'REPLACE(GROUP_CONCAT(DISTINCT SampleAgeInterpretations.AgeInterpretationName), ",", "; ") AS SampleAgeInterpretationName'
qsample_age_references = 'REPLACE(GROUP_CONCAT(DISTINCT SampleAgeReferences.ReferenceDisplay), ",", "; ") AS SampleAgeReferenceDisplay'
qsample_description = 'Samples.SampleDescription AS SampleDescription'
qage_signatures = 'REPLACE(GROUP_CONCAT(DISTINCT AgeSignatures.AgeSignatureName), ",", "; ") AS SampleAgeSignatureName'
qregions = 'REPLACE(GROUP_CONCAT(DISTINCT Regions.RegionName), ",", "; ") AS RegionName'
qrock_types = 'REPLACE(GROUP_CONCAT(DISTINCT RockTypes.RockTypeName), ",", "; ") AS RockTypeName'
qsample_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT SampleContexts.SampleContextName), ",", "; ") AS SampleContextName'
qsampling_methods = 'REPLACE(GROUP_CONCAT(DISTINCT SamplingMethods.SamplingMethodName), ",", "; ") AS SamplingMethodName'
qsettings = 'REPLACE(GROUP_CONCAT(DISTINCT Settings.SettingName), ",", "; ") AS SettingName'
qunits = 'REPLACE(GROUP_CONCAT(DISTINCT Units.UnitName), ",", "; ") AS UnitName'
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
qaliquot_labs = 'REPLACE(GROUP_CONCAT(DISTINCT LabFacilties.LabFacilityName), ",", "; ") AS LabFacilityName'
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
    lspuag.GrainID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM LimitedSpotsUPbAnalysesGrains lspuag
    INNER JOIN UPbAnalyses ON lspuag.SpotID = UPbAnalyses.SpotID
    GROUP BY lspuag.GrainID
)
'''
qupb_count_spot_subquery = f'''
DistinctUPbAnalyses AS 
(
    SELECT
    lspuag.SpotID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM LimitedSpotsUPbAnalysesGrains lspuag
    INNER JOIN UPbAnalyses ON lspuag.SpotID = UPbAnalyses.SpotID
    GROUP BY lspuag.SpotID
)
'''
qupb_references = 'REPLACE(GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay), ",", "; ") AS UPbReference'
qupb_reference = 'UPbReferences.ReferenceDisplay AS UPbReference'
qupb_lab_facilities = 'REPLACE(GROUP_CONCAT(DISTINCT LabFacilities.LabFacilityName), ",", "; ") AS LabFacilityName'
qupb_lab_facility = 'LabFacilities.LabFacilityName AS LabFacilityName'
qupb_instruments = 'REPLACE(GROUP_CONCAT(DISTINCT Instruments.InstrumentName), ",", "; ") AS InstrumentName'
qupb_instrument = 'Instruments.InstrumentName AS InstrumentName'
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
qupb_ratio_error_formats = 'REPLACE(GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation), ",", "; ") AS RatioErrorFormatAbbreviation'
qupb_ratio_error_format = 'RatioErrorFormats.ErrorFormatAbbreviation AS RatioErrorFormatAbbreviation'
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
qconcordance_formats = 'REPLACE(GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation), ",", "; ") AS ConcordanceFormatAbbreviation'
qconcordance_format = 'ConcordanceFormats.ConcordanceFormatAbbreviation AS ConcordanceFormatAbbreviation'
qminsegdisc = 'UPbAnalyses.MinimumSegmentedDiscordance AS MinimumSegmentedDiscordance'
qspot_size = 'UPbAnalyses.SpotSize AS SpotSize'
qupb_calc_spot_size = 'UPbAnalyses.CalculatedSpotSize AS CalculatedSpotSize'
qspot_sizes = f'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalyses.CalculatedSpotSize), ",", "; ") AS CalculatedSpotSize'
qspot_size_units = 'REPLACE(GROUP_CONCAT(DISTINCT SpotSizeUnits.DistanceUnitAbbreviation), ",", "; ") AS SpotSizeUnitAbbreviation'
qspot_size_unit = 'SpotSizeUnits.DistanceUnitAbbreviation AS SpotSizeUnitAbbreviation'
rejected_text = "'Rejected'"
accepted_text = "'Accepted'"
qupb_rejected = f'(CASE WHEN UPbAnalyses.Rejected = 1 THEN {rejected_text} ELSE {accepted_text} END) AS Rejected'
qupb_rejection_reasons = 'REPLACE(GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName), ",", "; ") AS RejectionReasonName'
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

# UPbJoins
upb_spot_join = 'INNER JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID'
upb_reference_join = 'LEFT JOIN "References" AS UPbReferences ON UPbAnalyses.ReferenceID = UPbReferences.ReferenceID'
upb_labs_join = 'LEFT JOIN LabFacilities ON UPbAnalyses.LabFacilityID = LabFacilities.LabFacilityID'
upb_instruments_join = 'LEFT JOIN Instruments ON UPbAnalyses.InstrumentID = Instruments.InstrumentID'
upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalyses.UPbAnalysisMethodID = UPbAnalysisMethods.UPbAnalysisMethodID'
upb_ratio_error_format_join = 'LEFT JOIN ErrorFormats AS RatioErrorFormats ON UPbAnalyses.RatioErrorFormatID = RatioErrorFormats.ErrorFormatID'
upb_age_error_format_join = 'LEFT JOIN ErrorFormats AS UPbAgeErrorFormats ON UPbAnalyses.AgeErrorFormatID = UPbAgeErrorFormats.ErrorFormatID'
upb_age_unit_join = 'LEFT JOIN AgeUnits AS UPbAgeUnits ON UPbAnalyses.AgeUnitID = UPbAgeUnits.AgeUnitID'
upb_age_interpretation_join = 'LEFT JOIN AgeInterpretations AS UPbAgeInterpretations ON UPbAnalyses.AgeInterpretationID = UPbAgeInterpretations.AgeInterpretationID'
upb_concordance_format_join = 'LEFT JOIN ConcordanceFormats ON UPbAnalyses.ConcordanceFormatID = ConcordanceFormats.ConcordanceFormatID'
upb_spot_size_unit_join = 'LEFT JOIN DistanceUnits AS SpotSizeUnits ON UPbAnalyses.SpotSizeUnitID = SpotSizeUnits.DistanceUnitID'
upb_rejection_reason_join = '''LEFT JOIN UPbAnalyses_RejectionReasons ON UPbAnalyses.UPbAnalysisID = UPbAnalyses_RejectionReasons.UPbAnalysisID
                                    LEFT JOIN RejectionReasons AS UPbRejectionReasons ON UPbAnalyses_RejectionReasons.RejectionReasonID = UPbRejectionReasons.RejectionReasonID'''
upb_context_join = '''LEFT JOIN UPbAnalyses_UPbAnalysisContexts ON UPbAnalyses.UPbAnalysisID = UPbAnalyses_UPbAnalysisContexts.UPbAnalysisID
                                LEFT JOIN UPbAnalysisContexts ON UPbAnalyses_UPbAnalysisContexts.UPbAnalysisContextID = UPbAnalysisContexts.UPbAnalysisContextID'''
upb_distinct_join_sample = '''LEFT JOIN DistinctUPbAnalyses ON Samples.SampleID = DistinctUPbAnalyses.SampleID'''
upb_distinct_join_aliquot = '''LEFT JOIN DistinctUPbAnalyses ON Aliquots.AliquotID = DistinctUPbAnalyses.AliquotID'''
upb_distinct_join_grain = '''LEFT JOIN DistinctUPbAnalyses ON Grains.GrainID = DistinctUPbAnalyses.GrainID'''
upb_distinct_join_spot = '''LEFT JOIN DistinctUPbAnalyses ON Spots.SpotID = DistinctUPbAnalyses.SpotID'''


# Limited hierarchy joins
limited_sample_aliquot_hierarchy_join = f'''
                        INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON lsa.AliquotID = lspuag.AliquotID
                        '''
limited_spot_upb_grain_hierarchy_join = f'''
                        INNER JOIN LimitedSamplesAliquots lsa ON lspuag.AliquotID = lsa.AliquotID
                        '''
limited_sample_hierarchy_joins = [column_join, column_unit_join]
# Limited tags
# Limit the many-to-many relationships
upb_distinct_join_limited_sample = '''LEFT JOIN DistinctUPbAnalyses ON lsa.SampleID = DistinctUPbAnalyses.SampleID'''
upb_distinct_join_limited_aliquot = '''LEFT JOIN DistinctUPbAnalyses ON lsa.AliquotID = DistinctUPbAnalyses.AliquotID'''
upb_distinct_join_limited_grain = '''LEFT JOIN DistinctUPbAnalyses ON lspuag.GrainID = DistinctUPbAnalyses.GrainID'''
upb_distinct_join_limited_spot = '''LEFT JOIN DistinctUPbAnalyses ON lspuag.SpotID = DistinctUPbAnalyses.SpotID'''
limited_sample_tags = [
        f'''LimitedSamples_AgeSignatures AS (
            SELECT s_ags.SampleID, ags.*
            FROM AgeSignatures ags
            INNER JOIN Samples_AgeSignatures s_ags ON ags.AgeSignatureID = s_ags.AgeSignatureID
            INNER JOIN LimitedSamplesAliquots lsa ON s_ags.SampleID = lsa.SampleID
        )''',
        f'''LimitedSamples_Regions AS (
            SELECT s_re.SampleID, re.*
            FROM Regions re
            INNER JOIN Samples_Regions s_re ON re.RegionID = s_re.RegionID
            INNER JOIN LimitedSamplesAliquots lsa ON s_re.SampleID = lsa.SampleID
        )''',
        f'''LimitedSamples_RockTypes AS (
            SELECT s_rt.SampleID, rt.*
            FROM RockTypes rt
            INNER JOIN Samples_RockTypes s_rt ON rt.RockTypeID = s_rt.RockTypeID
            INNER JOIN LimitedSamplesAliquots lsa ON s_rt.SampleID = lsa.SampleID
        )''',
        f'''LimitedSamples_SampleAges AS (
            SELECT s_sa.SampleID, sa.*, DirectAgeErrorFormats.*, SampleAgeUnits.*
            FROM SampleAges sa
            INNER JOIN Samples_SampleAges s_sa ON sa.SampleAgeID = s_sa.SampleAgeID
            INNER JOIN LimitedSamplesAliquots lsa ON s_sa.SampleID = lsa.SampleID
            {sample_age_left_joins.replace('SampleAges.', 'sa.')}
        )''',
        f'''LimitedSampleAges_AgeConstraints AS (
            SELECT sa_ac.SampleAgeID, ac.*
            FROM AgeConstraints ac
            INNER JOIN SampleAges_AgeConstraints sa_ac ON ac.AgeConstraintID = sa_ac.AgeConstraintID
            INNER JOIN LimitedSamples_SampleAges lssa ON sa_ac.SampleAgeID = lssa.SampleAgeID
        )''',
        f'''LimitedSampleAges_AgeInterpretations AS (
            SELECT sa_ai.SampleAgeID, ai.*
            FROM AgeInterpretations ai
            INNER JOIN SampleAges_AgeInterpretations sa_ai ON ai.AgeInterpretationID = sa_ai.AgeInterpretationID
            INNER JOIN LimitedSamples_SampleAges lssa ON sa_ai.SampleAgeID = lssa.SampleAgeID
        )''',
        f'''LimitedSampleAges_References AS (
            SELECT sa_r.SampleAgeID, r.*
            FROM "References" r
            INNER JOIN SampleAges_References sa_r ON r.ReferenceID = sa_r.ReferenceID
            INNER JOIN LimitedSamples_SampleAges lssa ON sa_r.SampleAgeID = lssa.SampleAgeID
        )''',
        f'''LimitedSamples_SampleContexts AS (
            SELECT s_sc.SampleID, sc.*
            FROM SampleContexts sc
            INNER JOIN Samples_SampleContexts s_sc ON sc.SampleContextID = s_sc.SampleContextID
            INNER JOIN LimitedSamplesAliquots lsa ON s_sc.SampleID = lsa.SampleID
        )''',
        f'''LimitedSamples_SamplingMethods AS (
            SELECT s_sm.SampleID, sm.*
            FROM SamplingMethods sm
            INNER JOIN Samples_SamplingMethods s_sm ON sm.SamplingMethodID = s_sm.SamplingMethodID
            INNER JOIN LimitedSamplesAliquots lsa ON s_sm.SampleID = lsa.SampleID
        )''',
        f'''LimitedSamples_Settings AS (
            SELECT s_se.SampleID, se.*
            FROM Settings se
            INNER JOIN Samples_Settings s_se ON se.SettingID = s_se.SettingID
            INNER JOIN LimitedSamplesAliquots lsa ON s_se.SampleID = lsa.SampleID
        )''',
        f'''LimitedSamples_Units AS (
            SELECT s_u.SampleID, u.*
            FROM Units u
            INNER JOIN Samples_Units s_u ON u.UnitID = s_u.UnitID
            INNER JOIN LimitedSamplesAliquots lsa ON s_u.SampleID = lsa.SampleID
        )'''
        ]
limited_aliquot_tags = [
        f'''LimitedAliquots_AliquotContexts AS (
            SELECT a_ac.AliquotID, ac.*
            FROM AliquotContexts ac
            INNER JOIN Aliquots_AliquotContexts a_ac ON ac.AliquotContextID = a_ac.AliquotContextID
            INNER JOIN LimitedSamplesAliquots lsa ON a_ac.AliquotID = lsa.AliquotID
        )''']
limited_spot_tags = [
        f'''LimitedSpots_SpotContexts AS (
            SELECT s_sc.SpotID, sc.*
            FROM SpotContexts sc
            INNER JOIN Spots_SpotContexts s_sc ON sc.SpotContextID = s_sc.SpotContextID
            INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON s_sc.SpotID = lspuag.SpotID
        )''',
        f'''LimitedGrains_GrainContexts AS (
            SELECT g_gc.GrainID, gc.*
            FROM GrainContexts gc
            INNER JOIN Grains_GrainContexts g_gc ON gc.GrainContextID = g_gc.GrainContextID
            INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON g_gc.GrainID = lspuag.GrainID
        )''']
limited_upb_tags = [
        f'''LimitedUPbAnalyses_UPbAnalysisContexts AS (
            SELECT ua_uac.UPbAnalysisID, ac.*
            FROM UPbAnalysisContexts ac
            INNER JOIN UPbAnalyses_UPbAnalysisContexts ua_uac ON ac.UPbAnalysisContextID = ua_uac.UPbAnalysisContextID
            INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON ua_uac.UPbAnalysisID = lspuag.UPbAnalysisID
        )''',
        f'''LimitedUPbAnalyses_RejectionReasons AS (
            SELECT ua_rr.UPbAnalysisID, rr.*
            FROM RejectionReasons rr
            INNER JOIN UPbAnalyses_RejectionReasons ua_rr ON rr.RejectionReasonID = ua_rr.RejectionReasonID
            INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON ua_rr.UPbAnalysisID = lspuag.UPbAnalysisID
        )''']

limited_grain_tags = [
        f'''LimitedGrains_GrainContexts AS (
            SELECT g_gc.GrainID, gc.*
            FROM GrainContexts gc
            INNER JOIN Grains_GrainContexts g_gc ON gc.GrainContextID = g_gc.GrainContextID
            INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON g_gc.GrainID = lspuag.GrainID
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
    'LEFT JOIN LimitedSpots_SpotContexts lspsc ON lspuag.SpotID = lspsc.SpotID',
    'LEFT JOIN LimitedGrains_GrainContexts lggc ON lspuag.GrainID = lggc.GrainID'
    ]

limited_upb_tags_join = [
    'LEFT JOIN LimitedUPbAnalyses_UPbAnalysisContexts luac ON lspuag.UPbAnalysisID = luac.UPbAnalysisID',
    'LEFT JOIN LimitedUPbAnalyses_RejectionReasons lurr ON lspuag.UPbAnalysisID = lurr.UPbAnalysisID'
    ]

limited_grain_tags_join = [
    'LEFT JOIN LimitedGrains_GrainContexts lggc ON lspuag.GrainID = lggc.GrainID'
]


limited_lsa_lspuag_joins = {
    'LimitedSamplesAliquots': [column_join,
                    column_unit_join,
                    gps_sample_join,
                    gps_sample_left_joins,
                    gps_column_join,
                    gps_column_left_joins
                ],
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
                    upb_spot_size_unit_join]
}

# Dictionary for limited table abbreviations
limited_table_abbreviations = {
    'Samples': 'lsa',
    'Aliquots': 'lsa',
    'Spots': 'lspuag',
    'UPbAnalyses': 'lspuag',
    'Grains': 'lspuag',
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
    'SpotCompositions': 'lspuag',
    'GrainCompositions': 'lspuag',
    'LabFacilities': 'lspuag',
    'Instruments': 'lspuag',
    'UPbAnalysisMethods': 'lspuag',
    'RatioErrorFormats': 'lspuag',
    'UPbAgeErrorFormats': 'lspuag',
    'ConcordanceFormats': 'lspuag',
    'UPbAgeUnits': 'lspuag',
    'UPbAgeInterpretations': 'lspuag',
    'UPbReferences': 'lspuag',
    'SpotSizeUnits': 'lspuag'
}

# Dictionary of column leaders that could be included in select statements for LimitedSamplesAliquots and LimitedSpotsUPbAnalysesGrains
limited_column_leaders = {
    'LimitedSamplesAliquots': [],
    'LimitedSpotsUPbAnalysesGrains': []
}
for table, abbreviation in limited_table_abbreviations.items():
    limited_column_leaders['LimitedSamplesAliquots'].append(f'{table}.') if abbreviation == 'lsa' else None
    limited_column_leaders['LimitedSpotsUPbAnalysesGrains'].append(f'{table}.') if abbreviation == 'lspuag' else None

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
                    'LabFacilityName': 'LabFacilities', 'InstrumentName': 'Instruments',
                    'UPbAnalysisMethodName': 'UPbAnalysisMethods',
                    'RatioErrorFormatAbbreviation': 'ErrorFormats', 'UPbAgeUnitAbbreviation': 'AgeUnits',
                    'UPbAgeErrorFormatAbbreviation': 'ErrorFormats', 'ConcordanceFormatAbbreviation': 'ConcordanceFormats',
                    'SpotSizeUnitAbbreviation': 'DistanceUnits'},
    'References': {}
}

non_editable = {
    'Samples': ['SpotCount', 'Accepted/TotalUPbAnalyses', 'RejectionReasonName', 'SampleCreated', 'SampleModified'],
    'Columns': ['ColumnCreated', 'ColumnModified'],
    'Aliquots': ['AliquotCreated', 'AliquotModified'],
    'Grains': ['GrainCreated', 'GrainModified'],
    'Spots': ['SpotCreated', 'SpotModified'],
    'UPbAnalyses': ['UPbAnalysisCreated', 'UPbAnalysisModified'],
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

user_viewable_tables = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'AliquotContexts',
                        'Columns', 'GrainContexts', 'GrainCompositions', 'Instruments', 'LabFacilities', 'References', 'Regions', 'RejectionReasons',
                        'RockTypes', 'SampleContexts', 'Samples', 'SamplingMethods', 'Settings', 'SpotCompositions',
                        'SpotContexts', 'UPbAnalysisMethods', 'UPbAnalysisContexts', 'Units']
"""List of all user-viewable tables and trees used throughout GeoCORK."""

user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'AliquotContexts', 'Aliquots',
                       'GrainContexts', 'Regions', 'RockTypes', 'SampleContexts', 'SamplingMethods', 'Settings', 'SpotCompositions',
                       'SpotContexts', 'UPbAnalysisMethods', 'UPbAnalysisContexts', 'Units']
"""List of all user-viewable trees used throughout GeoCORK. If a table is included in this list it is assumed to be in the correct format"""

export_database_tables_viewable = sorted(user_viewable_tables + ['UPbAnalyses', 'Aliquots', 'Spots'])
"""List of all tables to be viewed in the ExporterWidget for exporting a database. Extra tables are included for sanity checking."""

conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Grains', 'Spots', 'UPbAnalyses']
conditionally_editable_trees = ['Aliquots']

trigger_tables = ['Columns', 'ColumnEditView', 'GPSLocations', 'SampleAges', 'Samples', 'SampleEditView', 'Spots',
                  'SpotEditView', 'UPbAnalyses', 'UPbView', 'UPbEditView', 'Grains', 'GrainEditView']

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
    'GPSFormats'
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
                 'GPSFormats']
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
    'Columns'
]
"""List of all tables that have foreign key references to other tables in the database."""

database_ordered_tables = ['AgeUnits',
                           'ConcordanceFormats',
                           'DirectionUnits',
                           'DistanceUnits',
                           'ErrorFormats',
                           'GPSFormats',
                           'AgeUnitConversions',
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
         'SpotEditView', 'UPbView', 'UPbEditView', 'ColumnView', 'ColumnEditView', 'ReferenceView']
"""List of all views in the database. These views pull information from other tables for a comprehensive view of data
See Database_views.py for further"""

age_units = [('Billion years', 'Ga', '1000000000'),
             ('Million years', 'Ma', '1000000'),
             ('Thousand years', 'ka', '1000'),
             ('Years', 'a', '1')]
"""Static list of valid age units. Used to create AgeUnits table."""

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
    ('Universal Transverse Mercator', 'UTM', 'Universal Transverse Mercator with zone, northing, and easting')]
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
    'UPbReferences': 'References',
    'RatioErrorFormats': 'ErrorFormats',
    'UPbAgeErrorFormats': 'ErrorFormats',
    'UPbAgeUnits': 'AgeUnits',
    'UPbAgeInterpretations': 'AgeInterpretations',
    'SpotSizeUnits': 'DistanceUnits',
    'UPbRejectionReasons': 'RejectionReasons',
    'UPbAnalysisContexts': 'UPbAnalysisContexts',
    'DefaultSampleAges': 'SampleAges'
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
        "CalculatedSpotSize",

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
                   qconcordance_formats, qspot_sizes, qupb_rejection_reasons, qupb_contexts, qupb_age_interpretations,
                   qupb_references, qsample_created, qsample_modified],
    'SampleEditView': [qsample_id, qsample_name, qigsn, qsample_description, qgps_display, qsample_elev_display,
                       qsample_age_display, qsample_age_constraints, qsample_age_interpretations,
                       qsample_age_references, qcolumn_name, qsample_column_height_depth,
                       qsample_column_height_depth_error, qsample_column_data_unit, qage_signatures, qregions,
                       qrock_types, qsample_contexts, qsampling_methods, qsettings, qunits, qaliquots, qaliquot_contexts,
                       qgrain_count, qgrain_compositions, qgrain_contexts, qspot_count, qspot_compositions,
                       qspot_contexts, qupb_count, qupb_lab_facilities, qupb_instruments, qupb_analysis_methods,
                       qupb_ratio_error_formats, qupb_age_units, qupb_age_error_formats, qconcordance_formats,
                       qspot_size, qspot_size_unit, qupb_rejection_reasons, qupb_references, qupb_contexts,
                       qupb_age_interpretations, qsample_created, qsample_modified],
    'ColumnView': [qcolumn_id, qcolumn_name, qcolumn_description, qcolumn_calc_total_height_depth, qcolumn_gps,
                   qcolumn_elev, qcolumn_created, qcolumn_modified],
    'ColumnEditView': [qcolumn_id, qcolumn_name, qcolumn_description, qcolumn_total_height_depth,
                       qcolumn_total_height_depth_unit, qcolumn_gps_display, qcolumn_elev_display, qcolumn_elev_unit,
                       qcolumn_created, qcolumn_modified],
    'AliquotView': [qaliquot_id, qaliquot_parent_id, qaliquot_parent_row, qaliquot_name, qaliquot_description,
                    qsample_id, qaliquot_sample, qaliquot_contexts, qgrain_count, qgrain_compositions, qgrain_contexts,
                    qspot_count, qspot_compositions, qspot_contexts, qupb_count, qupb_lab_facilities,
                    qupb_analysis_methods, qupb_instruments, qupb_ratio_error_formats, qupb_age_units,
                    qupb_age_error_formats, qconcordance_formats, qspot_sizes, qupb_rejection_reasons, qupb_contexts,
                    qupb_age_interpretations, qupb_references, qaliquot_created, qaliquot_modified],
    'AliquotEditView': [qaliquot_id, qaliquot_parent_id, qaliquot_parent_row, qaliquot_name, qaliquot_description,
                        qsample_id, qaliquot_sample, qaliquot_contexts, qaliquot_created, qaliquot_modified],
    'GrainView': [qgrain_id, qaliquot_id, qsample_id, qgrain_name, qgrain_description, qaliquot_name, qsample_name,
                  qspots, qaliquot_name, qsample_name, qgrain_composition, qgrain_contexts, qspot_compositions,
                  qspot_contexts, qupb_count, qupb_lab_facilities, qupb_instruments, qupb_analysis_methods,
                  qupb_ratio_error_formats, qupb_age_units, qupb_age_error_formats, qconcordance_formats, qspot_sizes,
                  qupb_rejection_reasons, qupb_contexts, qupb_age_interpretations, qupb_references, qgrain_created,
                  qgrain_modified],
    'GrainEditView': [qgrain_id, qaliquot_id, qsample_id, qgrain_name, qgrain_description, qaliquot_name, qsample_name,
                      qgrain_composition, qgrain_contexts, qgrain_created, qgrain_modified],
    'SpotView': [qspot_id, qgrain_id, qaliquot_id, qsample_id, qspot_name, qspot_description, qgrain_name,
                 qaliquot_name, qsample_name, qspot_compositions, qspot_contexts, qgrain_composition, qgrain_contexts,
                 qupb_analyses, qupb_count, qupb_lab_facilities, qupb_instruments, qupb_analysis_methods,
                 qupb_ratio_error_formats, qupb_age_units, qupb_age_error_formats, qconcordance_formats, qspot_sizes,
                 qupb_rejection_reasons, qupb_contexts, qupb_age_interpretations, qupb_references, qspot_created,
                 qspot_modified],
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
                qupb_calc_concordance_68v75, qupb_error_corr_68v75, qconcordance_format, qminsegdisc,
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
                    qconcordance_format, qminsegdisc, qspot_size, qspot_size_unit, qupb_rejected, qupb_rejection_reasons,
                    qupb_contexts, qupb_created, qupb_modified],
    'ReferenceView': [qreference_id, qreference_display, qauthors, qyear, qtitle, qsource, qdoi, qreference_description,
                      qreference_created, qreference_modified]
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
        'Spot Size': ['UPbAnalyses', 'SpotSize'],
        'Spot Size Unit': ['UPbAnalyses', 'SpotSizeUnitID']
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
        'Rejection Reason Description': ['UPbRejectionReasons', 'UPbRejectionReasonDescription'],
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
"""Dictionaries of User-readable columns/info able to be imported into the database with list of their associated table 
    and column name. ImporterCategroy: {UserReadableColumnName: [TableName, ColumnName]}"""

combo_box_possible_input_fields = {
    'Reference': ['References', 'ReferenceID', 'ReferenceDisplay'],
    'Intrument': ['Instruments', 'InstrumentID', 'InstrumentName'],
    'Lab Facility': ['LabFacilities', 'LabFacilityID', 'LabFacilityName'],
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
    'U-Pb Age Error': ['UPbAnalyses', 'AgeErrorFormatID'],
    'Ratio Error': ['UPbAnalyses', 'RatioErrorFormatID'],
    'Spot Size Unit': ['UPbAnalyses', 'SpotSizeUnitID'],
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

    'UPbAnalysisName',
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
    'SpotSize', 'SpotSizeUnitID',
    'Rejected',
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
spotsize_unit_affected = [['UPbAnalyses', 'SpotSizeUnitID', 'SpotSize']]
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
            case 'RejectionReasons' | 'UPbRejectionReasons':
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
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'
            case 'Samples':
                pass
    return join
