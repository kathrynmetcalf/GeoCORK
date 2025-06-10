# ID columns
qsample_id = 'Samples.SampleID AS SampleID'
qaliquot_id = 'Aliquots.AliquotID AS AliquotID'
qspot_id = 'Spots.SpotID AS SpotID'
qupb_id = 'UPbAnalyses.UPbAnalysisID AS UPbAnalysisID'
qcolumn_id = 'Columns.ColumnID AS ColumnID'
qreference_id = 'References.ReferenceID AS ReferenceID'

# Sample view columns
qsample_name = 'Samples.SampleName AS SampleName'
qigsn = 'Samples.SampleIGSN AS SampleIGSN'
qgps = 'GPSLocations.GPSLocationConverted AS GPSSampleLocationCalculated'
qgps_display = 'GPSLocations.GPSLocationDisplay AS SampleGPSLocationDisplay'
qsample_gps_id = 'Samples.SampleGPSLocationID AS SampleGPSLocationID'
qsample_elev = 'NULLIF(COALESCE(GPSLocations.CalculatedGPSElev, "") || "±" || COALESCE(GPSLocations.CalculatedGPSElevError, ""), "±") AS SampleElevationCalculated'
qsample_elev_display = 'NULLIF(COALESCE(GPSLocations.GPSElev, "") || "±" || COALESCE(GPSLocations.GPSElevError, ""), "±") AS SampleElevation'
qsample_elev_unit = 'SampleElevationUnits.DistanceUnitAbbreviation AS SampleElevationUnitAbbreviation'
qsample_column_data = 'NULLIF(COALESCE(Samples.CalculatedHeightDepth, "") || "±" || COALESCE(Samples.CalculatedHeightDepthError, ""), "±") AS ColumnHeightDepthCalculated'
qsample_column_data_display = 'NULLIF(COALESCE(Samples.HeightDepth, "") || "±" || COALESCE(Samples.HeightDepthError, ""), "±") AS ColumnHeightDepth'
qsample_column_data_unit = 'ColumnHeightDepthUnits.DistanceUnitAbbreviation AS ColumnHeightDepthUnitAbbreviation'
qsample_age = 'SampleAges.SampleAgeDisplay AS SampleAgeCalculated'
qage_range = 'NULLIF(COALESCE(CalculatedOldestDirectAge, " ") || "-" || COALESCE(CalculatedYoungestDirectAge, " "), " - ") AS SampleAgeRangeCalculated'
qage_range_display = 'NULLIF(COALESCE(OldestDirectAge, " ") || "-" || COALESCE(YoungestDirectAge, " "), " - ") AS SampleAgeRange'
qage_unit = 'DirectAgeUnitAbbreviation AS SampleAgeUnitAbbreviation'
qage_error_format = 'DirectAgeErrorFormatAbbreviation AS SampleAgeErrorFormatAbbreviation'
qsample_age_constraint = 'REPLACE(GROUP_CONCAT(DISTINCT AgeConstraintName), ",", "; ") AS SampleAgeConstraintName'
qsample_age_interpretation = 'REPLACE(GROUP_CONCAT(DISTINCT AgeInterpretationName), ",", "; ") AS SampleAgeInterpretationName'
qsample_age_references = 'GROUP_CONCAT(DISTINCT AgeReferences.ReferenceDisplay) AS SampleAgeReferenceDisplay'
qsample_description = 'Samples.SampleDescription AS SampleDescription'
qage_signature = 'REPLACE(GROUP_CONCAT(DISTINCT AgeSignatureName), ",", "; ") AS SampleAgeSignatureName'
qregions = 'REPLACE(GROUP_CONCAT(DISTINCT RegionName), ",", "; ") AS RegionName'
qrock_types = 'REPLACE(GROUP_CONCAT(DISTINCT RockTypeName), ",", "; ") AS RockTypeName'
qsample_context = 'REPLACE(GROUP_CONCAT(DISTINCT SampleContextName), ",", "; ") AS SampleContextName'
qsampling_methods = 'REPLACE(GROUP_CONCAT(DISTINCT SamplingMethodName), ",", "; ") AS SamplingMethodName'
qsettings = 'REPLACE(GROUP_CONCAT(DISTINCT SettingName), ",", "; ") AS SettingName'
qunits = 'REPLACE(GROUP_CONCAT(DISTINCT UnitName), ",", "; ") AS UnitName'
qsample_created = 'Samples.SampleCreated AS SampleCreated'
qsample_modified = 'Samples.SampleModified AS SampleModified'

#Columns, skip null values
qcolumn_name = 'Columns.ColumnName AS ColumnName'
qcolumn_names = 'REPLACE(GROUP_CONCAT(DISTINCT ColumnName), ",", "; ") AS ColumnName'
qcolumn_data = f'NULLIF(COALESCE(HeightDepth, "") || "±" || COALESCE(HeightDepthError, ""), "±") AS ColumnHeightDepth'
qcolumn_gps = f'ColumnGPS.GPSLocationConverted AS ColumnGPSLocationCalculated'
qcolumn_gps_display = 'ColumnGPS.GPSLocationDisplay AS ColumnGPSLocationDisplay'
qcolumn_gps_id = 'Columns.ColumnBaseGPSID AS ColumnGPSLocationID'
qcolumn_calc_total_height_depth = f'Columns.CalculatedColumnTotalHeightDepth AS ColumnTotalHeightDepthCalculated'
qcolumn_total_height_depth = f'Columns.ColumnTotalHeightDepth AS ColumnTotalHeightDepth'
qcolumn_total_height_depth_unit = f'ColumnUnits.DistanceUnitAbbreviation AS ColumnTotalHeightDepthUnitAbbreviation'
qcolumn_elev = 'NULLIF(COALESCE(ColumnGPS.CalculatedGPSElev, "") || "±" || COALESCE(ColumnGPS.CalculatedGPSElevError, ""), "±") AS ColumnElevationCalculated'
qcolumn_elev_display = 'NULLIF(COALESCE(ColumnGPS.GPSElev, "") || "±" || COALESCE(ColumnGPS.GPSElevError, ""), "±") AS ColumnElevation'
qcolumn_elev_unit = 'ColumnElevationUnits.DistanceUnitAbbreviation AS ColumnElevationUnitAbbreviation'
qcolumn_description = 'ColumnDescription AS ColumnDescription'
qcolumn_created = 'ColumnCreated AS ColumnCreated'
qcolumn_modified = 'ColumnModified AS ColumnModified'

# Aliquot view columns
qaliquot_count = 'COUNT(DISTINCT Aliquots.AliquotID) AS AliquotCount'
qaliquot_name = 'AliquotName AS AliquotName'
qaliquots = 'REPLACE(GROUP_CONCAT(DISTINCT AliquotName), ",", "; ") AS AliquotName'
qaliquot_parent_id = 'ParentAliquotID AS ParentAliquotID'
qaliquot_parent_row = 'AliquotParentRow AS AliquotParentRow'
qaliquot_sample = 'Samples.SampleName AS SampleName'
qaliquot_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT AliquotContextName), ",", "; ") AS AliquotContextName'
qaliquot_spots = 'REPLACE(GROUP_CONCAT(DISTINCT SpotName), ",", "; ") AS SpotName'
qaliquot_spot_context = 'REPLACE(GROUP_CONCAT(DISTINCT SpotContextName), ",", "; ") AS SpotContextName'
qaliquot_spot_compositions = 'REPLACE(GROUP_CONCAT(DISTINCT SpotCompositionName), ",", "; ") AS SpotCompositionName'
qaliquot_references = 'GROUP_CONCAT(DISTINCT ReferenceDisplay) AS UPb Reference'
qaliquot_upb_methods = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalysisMethodName), ",", "; ") AS UPbAnalysisMethodName'
qaliquot_labs = 'REPLACE(GROUP_CONCAT(DISTINCT LabFacilityName), ",", "; ") AS LabFacilityName'
qaliquot_created = 'AliquotCreated AS AliquotCreated'
qaliquot_modified = 'AliquotModified AS AliquotModified'

# Spot view columns
qspot_count = 'COUNT(DISTINCT Spots.SpotID) AS SpotCount'
qspot_name = 'SpotName AS SpotName'
qspots = 'REPLACE(GROUP_CONCAT(DISTINCT SpotName), ",", "; ") AS SpotName'
qspot_composition = 'SpotCompositionName AS SpotCompositionName'
qspot_compositions = 'REPLACE(GROUP_CONCAT(DISTINCT SpotCompositionName), ",", "; ") AS SpotCompositionName'
qspot_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT SpotContextName), ",", "; ") AS SpotContextName'
qspot_created = 'SpotCreated AS SpotCreated'
qspot_modified = 'SpotModified AS SpotModified'

# UPb view columns
# qupb_count = 'SUM(CASE WHEN Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS "Accepted/TotalUPbAnalyses"'  # accepted/total
qupb_count = 'DistinctUPbAnalyses.AcceptedTotalUPbAnalyses AS "Accepted/TotalUPbAnalyses"'
qupb_count_sample_subquery = f'''
DistinctUPbAnalyses AS 
(
    SELECT 
    Samples.SampleID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM Samples 
    LEFT JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID
    LEFT JOIN Spots ON Aliquots.AliquotID = Spots.AliquotID
    LEFT JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
    GROUP BY Samples.SampleID
)
'''
qupb_count_aliquot_subquery = f'''
DistinctUPbAnalyses AS 
(
    SELECT
    Aliquots.AliquotID,
    SUM(CASE WHEN UPbAnalyses.Rejected = 0 THEN 1 ELSE 0 END) || "/" || COUNT(DISTINCT UPbAnalyses.UPbAnalysisID) AS AcceptedTotalUPbAnalyses
    FROM Aliquots 
    LEFT JOIN Spots ON Aliquots.AliquotID = Spots.AliquotID
    LEFT JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
    GROUP BY Aliquots.AliquotID
)
'''
qupb_references = 'GROUP_CONCAT(DISTINCT UPbReferences.ReferenceDisplay) AS UPbReference'
qupb_lab_facilities = 'REPLACE(GROUP_CONCAT(DISTINCT LabFacilityName), ",", "; ") AS LabFacilityName'
qupb_instruments = 'REPLACE(GROUP_CONCAT(DISTINCT InstrumentName), ",", "; ") AS InstrumentName'
qupb_analysis_methods = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalysisMethodName), ",", "; ") AS UPbAnalysisMethodName'
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
qupb_calc_207235 = 'UPbAnalyses."Calculated207Pb/225U" AS "Calculated207Pb/235U"'
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
qupb204238 = 'UPbAnalyses."204Pb/238U" AS "204Pb/238U"'
qupb204238_error = 'UPbAnalyses."204Pb/238UError" AS "204Pb/238UError"'
qupb_calc_204238 = 'UPbAnalyses."Calculated204Pb/238U" AS "Calculated204Pb/238U"'
qupb_calc_204238_error = 'UPbAnalyses."Calculated204Pb/238UError" AS "Calculated204Pb/238UError"'
qupb_2382204 = 'UPbAnalyses."238U/204Pb" AS "238U/204Pb"'
qupb_2382204_error = 'UPbAnalyses."238U/204PbError" AS "238U/204PbError"'
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
upb_208204 = 'UPbAnalyses."208Pb/204Pb" AS "208Pb/204Pb"'
qupb_208204_error = 'UPbAnalyses."208Pb/204PbError" AS "208Pb/204PbError"'
qupb_calc_208204 = 'UPbAnalyses."Calculated208Pb/204Pb" AS "Calculated208Pb/204Pb"'
qupb_calc_208204_error = 'UPbAnalyses."Calculated208Pb/204PbError" AS "Calculated208Pb/204Pb"'
upb_204208 = 'UPbAnalyses."204Pb/208Pb" AS "204Pb/208Pb"'
upb_204208_error = 'UPbAnalyses."204Pb/208PbError" AS "204Pb/208PbError"'
qupb_calc_204208 = 'UPbAnalyses."Calculated204Pb/208Pb" AS "Calculated204Pb/208Pb"'
qupb_calc_204208_error = 'UPbAnalyses."Calculated204Pb/208PbError" AS "Calculated204Pb/208Pb"'
qupb_ratio_error_formats = 'REPLACE(GROUP_CONCAT(DISTINCT RatioErrorFormats.ErrorFormatAbbreviation), ",", "; ") AS RatioErrorFormatAbbreviation'
qupb_error_corr = 'UPbAnalyses.ErrorCorr AS ErrorCorr'
qupb_207206_age = 'UPbAnalyses."207Pb/206PbAge" AS "207Pb/206PbAge"'
qupb_207206_age_error = 'UPbAnalyses."207Pb/206PbAgeError" AS "207Pb/206PbAgeError"'
qupb_calc_207206_age = 'UPbAnalyses."Calculated207Pb/206PbAge" AS "Calculated207Pb/206PbAge"'
qupb_calc_207206_age_error = 'UPbAnalyses."Calculated207Pb/206PbAgeError AS "Calculated207Pb/206PbAgeError"'
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
qupb_calc_best_age = 'UPbAnalyses."CalculatedBestAge" AS "CalculatedBestAge"'
qupb_calc_best_age_error = 'UPbAnalyses."CalculatedBestAgeError" AS "CalculatedBestAgeError"'
qupb_age_error_formats = 'REPLACE(GROUP_CONCAT(DISTINCT AgeErrorFormats.ErrorFormatAbbreviation), ",", "; ") AS AgeErrorFormatAbbreviation'
qupb_age_units = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAgeUnits.AgeUnitAbbreviation), ",", "; ") AS AgeUnitAbbreviation'
qupb_age_interpretations = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAgeInterpretations.AgeInterpretationName), ",", "; ") AS AgeInterpretationName'
qupb_concordance = 'UPbAnalyses.Concordance AS Concordance'
qupb_calc_concordance = 'UPbAnalyses."CalculatedConcordance" AS "CalculatedConcordance"'
qconcordance_formats = 'REPLACE(GROUP_CONCAT(DISTINCT ConcordanceFormats.ConcordanceFormatAbbreviation), ",", "; ") AS ConcordanceFormatAbbreviation'
qspot_size = 'UPbAnalyses.SpotSize AS SpotSize'
qspot_sizes = f'REPLACE(GROUP_CONCAT(DISTINCT CalculatedSpotSize), ",", "; ") AS CalculatedSpotSize'
qspot_size_unit = 'REPLACE(GROUP_CONCAT(DISTINCT SpotSizeUnits.DistanceUnitAbbreviation), ",", "; ") AS SpotSizeUnitAbbreviation'
rejected_text = "'Rejected'"
accepted_text = "'Accepted'"
qupb_rejected = f'(CASE WHEN UPbAnalyses.Rejected = 1 THEN {rejected_text} ELSE {accepted_text} END) AS Rejected'
qupb_rejection_reasons = 'REPLACE(GROUP_CONCAT(DISTINCT UPbRejectionReasons.RejectionReasonName), ",", "; ") AS RejectionReasonName'
qupb_contexts = 'REPLACE(GROUP_CONCAT(DISTINCT UPbAnalysisContexts.UPbAnalysisContextName), ",", "; ") AS UPbAnalysisContextName'
qupb_created = 'UPbAnalysisCreated AS UPbAnalysisCreated'
qupb_modified = 'UPbAnalysisModified AS UPbAnalysisModified'

# Reference view columns
qreference_id = 'ReferenceID AS ReferenceID'
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
                        LEFT JOIN AgeUnits ON SampleAges.DirectAgeUnitID = AgeUnits.AgeUnitID
                        LEFT JOIN Ages AS OldAge ON SampleAges.OldestAgeID = OldAge.AgeID
                        LEFT JOIN Ages AS YoungAge ON SampleAges.YoungestAgeID = YoungAge.AgeID'''
sampleage_age_constraint_join = '''LEFT JOIN SampleAges_AgeConstraints ON SampleAges.SampleAgeID = SampleAges_AgeConstraints.SampleAgeID
                        LEFT JOIN AgeConstraints ON SampleAges_AgeConstraints.AgeConstraintID = AgeConstraints.AgeConstraintID'''
sampleage_age_interpretation_join = '''LEFT JOIN SampleAges_AgeInterpretations ON SampleAges.SampleAgeID = SampleAges_AgeInterpretations.SampleAgeID
                        LEFT JOIN AgeInterpretations ON SampleAges_AgeInterpretations.AgeInterpretationID = AgeInterpretations.AgeInterpretationID'''
sampleage_age_reference_join = '''LEFT JOIN SampleAges_References ON SampleAges.SampleAgeID = SampleAges_References.SampleAgeID
                        LEFT JOIN "References" AS AgeReferences ON SampleAges_References.ReferenceID = AgeReferences.ReferenceID'''

# GPSLocation joins
gps_sample_join = '''LEFT JOIN GPSLocations AS GPSLocations ON Samples.SampleGPSLocationID = GPSLocations.GPSLocationID'''
gps_sample_left_joins = '''LEFT JOIN DirectionUnits AS SampleLatDirections ON GPSLocations.GPSLatDirectionID = SampleLatDirections.DirectionUnitID
                        LEFT JOIN DirectionUnits AS SampleLonDirections ON GPSLocations.GPSLonDirectionID = SampleLonDirections.DirectionUnitID
                        LEFT JOIN DistanceUnits AS SampleElevationUnits ON GPSLocations.GPSElevUnitID = SampleElevationUnits.DistanceUnitID
                        LEFT JOIN GPSFormats AS GPSFormats ON GPSLocations.GPSFormatID = GPSFormats.GPSFormatID'''
gps_column_join = '''LEFT JOIN GPSLocations AS ColumnGPS ON Columns.ColumnBaseGPSID = ColumnGPS.GPSLocationID'''
gps_column_left_joins = '''LEFT JOIN DirectionUnits AS ColumnLatDirections ON ColumnGPS.GPSLatDirectionID = ColumnLatDirections.DirectionUnitID
                        LEFT JOIN DirectionUnits AS ColumnLonDirections ON ColumnGPS.GPSLonDirectionID = ColumnLonDirections.DirectionUnitID
                        LEFT JOIN DistanceUnits AS ColumnElevationUnits ON ColumnGPS.GPSElevUnitID = ColumnElevationUnits.DistanceUnitID
                        LEFT JOIN GPSFormats AS ColumnGPSFormats ON ColumnGPS.GPSFormatID = ColumnGPSFormats.GPSFormatID'''

# ColumnJoins
column_units_join = 'LEFT JOIN DistanceUnits as ColumnUnits ON Columns.ColumnTotalHeightDepthUnitID = ColumnUnits.DistanceUnitID'

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
default_sample_age_join = '''LEFT JOIN SampleAges as DefaultSampleAges ON Samples.DefaultSampleAgeID = DefaultSampleAges.SampleAgeID'''
sampling_method_join = '''LEFT JOIN Samples_SamplingMethods ON Samples.SampleID = Samples_SamplingMethods.SampleID
                                LEFT JOIN SamplingMethods ON Samples_SamplingMethods.SamplingMethodID = SamplingMethods.SamplingMethodID'''
setting_join = '''LEFT JOIN Samples_Settings ON Samples.SampleID = Samples_Settings.SampleID
                                LEFT JOIN Settings ON Samples_Settings.SettingID = Settings.SettingID'''
unit_join = '''LEFT JOIN Samples_Units ON Samples.SampleID = Samples_Units.SampleID
                                LEFT JOIN Units ON Samples_Units.UnitID = Units.UnitID'''
sample_aliquot_join = 'LEFT JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID'

# AliquotJoins
aliquot_sample_join = 'LEFT JOIN Samples ON Aliquots.SampleID = Samples.SampleID'
aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts ON Aliquots.AliquotID = Aliquots_AliquotContexts.AliquotID
                                LEFT JOIN AliquotContexts ON Aliquots_AliquotContexts.AliquotContextID = AliquotContexts.AliquotContextID'''

# Aliquot-spot Join
aliquot_spot_join = 'LEFT JOIN Spots ON Aliquots.AliquotID = Spots.AliquotID'

# SpotJoins
spot_aliquot_join = 'LEFT JOIN Aliquots ON Spots.AliquotID = Aliquots.AliquotID'
spot_composition_join = '''LEFT JOIN SpotCompositions ON Spots.SpotCompositionID = SpotCompositions.SpotCompositionID'''
spot_context_join = '''LEFT JOIN Spots_SpotContexts ON Spots.SpotID = Spots_SpotContexts.SpotID
                                LEFT JOIN SpotContexts ON Spots_SpotContexts.SpotContextID = SpotContexts.SpotContextID'''
spot_upb_analysis_join = 'LEFT JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID'

# UPbJoins
upb_spot_join = 'LEFT JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID'
upb_reference_join = 'LEFT JOIN "References" AS UPbReferences ON UPbAnalyses.ReferenceID = UPbReferences.ReferenceID'
upb_labs_join = 'LEFT JOIN LabFacilities ON UPbAnalyses.LabFacilityID = LabFacilities.LabFacilityID'
upb_instruments_join = 'LEFT JOIN Instruments ON UPbAnalyses.InstrumentID = Instruments.InstrumentID'
upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalyses.UPbAnalysisMethodID = UPbAnalysisMethods.UPbAnalysisMethodID'
upb_ratio_error_format_join = 'LEFT JOIN ErrorFormats AS RatioErrorFormats ON UPbAnalyses.RatioErrorFormatID = RatioErrorFormats.ErrorFormatID'
upb_age_error_format_join = 'LEFT JOIN ErrorFormats AS AgeErrorFormats ON UPbAnalyses.AgeErrorFormatID = AgeErrorFormats.ErrorFormatID'
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


# Limited hierarchy joins
limited_sample_hierarchy_join = f'''
                        JOIN LimitedAliquots la ON ls.SampleID = la.SampleID
                        JOIN LimitedSpots lsp ON la.AliquotID = lsp.AliquotID
                        JOIN LimitedUPbAnalyses lu ON lsp.SpotID = lu.SpotID
                        '''
limited_aliquot_hierarchy_join = f'''
                        JOIN LimitedSamples ls ON la.SampleID = ls.SampleID
                        JOIN LimitedSpots lsp ON la.AliquotID = lsp.AliquotID
                        JOIN LimitedUPbAnalyses lu ON lsp.SpotID = lu.SpotID
                        '''
limited_spot_hierarchy_join = f'''
                        JOIN LimitedAliquots la ON lsp.AliquotID = la.AliquotID
                        JOIN LimitedSamples ls ON la.SampleID = ls.SampleID
                        JOIN LimitedUPbAnalyses lu ON lsp.SpotID = lu.SpotID
                        '''
limited_upb_hierarchy_join = f'''
                        JOIN LimitedSpots lsp ON lu.SpotID = lsp.SpotID
                        JOIN LimitedAliquots la ON lsp.AliquotID = la.AliquotID
                        JOIN LimitedSamples ls ON la.SampleID = ls.SampleID
                    '''

# Limited tags
# Limit the many-to-many relationships
limited_sample_tags = f'''
        LimitedSamples_AgeSignatures AS (
            SELECT s_ags.SampleID, ags.*
            FROM AgeSignatures ags
            JOIN Samples_AgeSignatures s_ags ON ags.AgeSignatureID = s_ags.AgeSignatureID
            WHERE s_ags.SampleID in (SELECT SampleID FROM LimitedSamples)
        ),
        LimitedSamples_Regions AS (
            SELECT s_re.SampleID, re.*
            FROM Regions re
            JOIN Samples_Regions s_re ON re.RegionID = s_re.RegionID
            WHERE s_re.SampleID in (SELECT SampleID FROM LimitedSamples)
        ),
        LimitedSamples_RockTypes AS (
            SELECT s_rt.SampleID, rt.*
            FROM RockTypes rt
            JOIN Samples_RockTypes s_rt ON rt.RockTypeID = s_rt.RockTypeID
            WHERE s_rt.SampleID in (SELECT SampleID FROM LimitedSamples)
        ),
        LimitedSamples_SampleAges AS (
            SELECT s_sa.SampleID, sa.*
            FROM SampleAges sa
            JOIN Samples_SampleAges s_sa ON sa.SampleAgeID = s_sa.SampleAgeID
            WHERE s_sa.SampleID in (SELECT SampleID FROM LimitedSamples)
        ),
        LimitedSampleAges_AgeConstraints AS (
            SELECT sa_ac.SampleAgeID, ac.*
            FROM AgeConstraints ac
            JOIN SampleAges_AgeConstraints sa_ac ON ac.AgeConstraintID = sa_ac.AgeConstraintID
            WHERE sa_ac.SampleAgeID in (SELECT SampleAgeID FROM LimitedSamples_SampleAges)
        ),
        LimitedSampleAges_AgeInterpretations AS (
            SELECT sa_ai.SampleAgeID, ai.*
            FROM AgeInterpretations ai
            JOIN SampleAges_AgeInterpretations sa_ai ON ai.AgeInterpretationID = sa_ai.AgeInterpretationID
            WHERE sa_ai.SampleAgeID in (SELECT SampleAgeID FROM LimitedSamples_SampleAges)
        ),
        LimitedSampleAges_References AS (
            SELECT sa_r.SampleAgeID, r.*
            FROM "References" r
            JOIN SampleAges_References sa_r ON r.ReferenceID = sa_r.ReferenceID
            WHERE sa_r.SampleAgeID in (SELECT SampleAgeID FROM LimitedSamples_SampleAges)
        ),
        LimitedSamples_SampleContexts AS (
            SELECT s_sc.SampleID, sc.*
            FROM SampleContexts sc
            JOIN Samples_SampleContexts s_sc ON sc.SampleContextID = s_sc.SampleContextID
            WHERE s_sc.SampleID in (SELECT SampleID FROM LimitedSamples)
        ),
        LimitedSamples_SamplingMethods AS (
            SELECT s_sm.SampleID, sm.*
            FROM SamplingMethods sm
            JOIN Samples_SamplingMethods s_sm ON sm.SamplingMethodID = s_sm.SamplingMethodID
            WHERE s_sm.SampleID in (SELECT SampleID FROM LimitedSamples)
        ),
        LimitedSamples_Settings AS (
            SELECT s_se.SampleID, se.*
            FROM Settings se
            JOIN Samples_Settings s_se ON se.SettingID = s_se.SettingID
            WHERE s_se.SampleID in (SELECT SampleID FROM LimitedSamples)
        ),
        LimitedSamples_Units AS (
            SELECT s_u.SampleID, u.*
            FROM Units u
            JOIN Samples_Units s_u ON u.UnitID = s_u.UnitID
            WHERE s_u.SampleID in (SELECT SampleID FROM LimitedSamples)
        )
    '''
limited_aliquot_tags = f'''
        LimitedAliquots_AliquotContexts AS (
            SELECT a_ac.AliquotID, ac.*
            FROM AliquotContexts ac
            JOIN Aliquots_AliquotContexts a_ac ON ac.AliquotContextID = a_ac.AliquotContextID
            WHERE a_ac.AliquotID in (SELECT AliquotID FROM LimitedAliquots)
        )
    '''
limited_spot_tags = f'''
        LimitedSpots_SpotContexts AS (
            SELECT s_sc.SpotID, sc.*
            FROM SpotContexts sc
            JOIN Spots_SpotContexts s_sc ON sc.SpotContextID = s_sc.SpotContextID
            WHERE s_sc.SpotID in (SELECT SpotID FROM LimitedSpots)
        )
    '''
limited_upb_tags = f'''
        LimitedUPbAnalyses_UpbAnalysisContexts AS (
            SELECT ua_uac.UPbAnalysisID, ac.*
            FROM UPbAnalysisContexts ac
            JOIN UPbAnalyses_UPbAnalysisContexts ua_uac ON ac.UPbAnalysisContextID = ua_uac.UPbAnalysisContextID
            WHERE ua_uac.UPbAnalysisID in (SELECT UPbAnalysisID FROM LimitedUPbAnalyses)
        ),
        LimitedUPbAnalyses_RejectionReasons AS (
            SELECT ua_rr.UPbAnalysisID, rr.*
            FROM RejectionReasons rr
            JOIN UPbAnalyses_RejectionReasons ua_rr ON rr.RejectionReasonID = ua_rr.RejectionReasonID
            WHERE ua_rr.UPbAnalysisID in (SELECT UPbAnalysisID FROM LimitedUPbAnalyses)
        )
    '''


# Limited tag joins
limited_sample_tags_join = f'''
    LEFT JOIN LimitedSamples_AgeSignatures lsas ON ls.SampleID = lsas.SampleID
    LEFT JOIN LimitedSamples_Regions lsre ON ls.SampleID = lsre.SampleID
    LEFT JOIN LimitedSamples_RockTypes lsrt ON ls.SampleID = lsrt.SampleID
    LEFT JOIN LimitedSamples_SampleAges lssa ON ls.DefaultSampleAgeID = lssa.SampleAgeID
    LEFT JOIN LimitedSampleAges_AgeConstraints lsaac ON ls.DefaultSampleAgeID = lsaac.SampleAgeID
    LEFT JOIN LimitedSampleAges_AgeInterpretations lsaai ON ls.DefaultSampleAgeID = lsaai.SampleAgeID
    LEFT JOIN LimitedSampleAges_References AS AgeReferences ON ls.DefaultSampleAgeID = AgeReferences.SampleAgeID
    LEFT JOIN LimitedSamples_SampleContexts lssc ON ls.SampleID = lssc.SampleID
    LEFT JOIN LimitedSamples_SamplingMethods lssm ON ls.SampleID = lssm.SampleID
    LEFT JOIN LimitedSamples_Settings lss ON ls.SampleID = lss.SampleID
    LEFT JOIN LimitedSamples_Units lsu ON ls.SampleID = lsu.SampleID
'''

limited_aliquot_tags_join = f'''
    LEFT JOIN LimitedAliquots_AliquotContexts laac ON la.AliquotID = laac.AliquotID
'''

limited_spot_tags_join = f'''
    LEFT JOIN LimitedSpots_SpotContexts lspsc ON lsp.SpotID = lspsc.SpotID
'''

limited_upb_tags_join = f'''
    LEFT JOIN LimitedUPbAnalyses_UpbAnalysisContexts luac ON lu.UPbAnalysisID = luac.UPbAnalysisID
    LEFT JOIN LimitedUPbAnalyses_RejectionReasons AS UPbRejectionReasons ON lu.UPbAnalysisID = UPbRejectionReasons.UPbAnalysisID
'''

# Dictionary for limited table abbreviations
limited_table_abbreviations = {
    'Samples': 'ls',
    'Aliquots': 'la',
    'Spots': 'lsp',
    'UPbAnalyses': 'lu',
    'AgeSignatures': 'lsas',
    'Regions': 'lsre',
    'RockTypes': 'lsrt',
    'SampleAges': 'lssa',
    'AgeConstraints': 'lsaac',
    'AgeInterpretations': 'lsaai',
    'SampleContexts': 'lssc',
    'SamplingMethods': 'lssm',
    'Settings': 'lss',
    'Units': 'lsu',
    'AliquotContexts': 'laac',
    'SpotContexts': 'lssc',
    'UPbAnalysisContexts': 'luac',
    'RejectionReasons': 'lurr'
}

# Information for settings

sample_view_columns = [qsample_id, qigsn, qsample_name, qgps, qsample_elev, qcolumn_gps, qcolumn_data, qsample_age,
                       qage_range, qsample_age_constraint, qsample_age_interpretation,
                       qsample_age_references, qsample_description, qage_signature, qregions, qrock_types,
                       qsample_context, qsampling_methods, qsettings, qunits, qaliquots, qaliquot_contexts,
                       qspots, qspot_compositions, qspot_contexts, qupb_references, qupb_lab_facilities,
                       qupb_instruments,
                       qupb_analysis_methods, qupb_ratio_error_formats, qupb_age_error_formats, qupb_age_units,
                       qupb_age_interpretations, qconcordance_formats, qspot_sizes, qupb_rejection_reasons, qupb_contexts]

# Many-to-many columns for each table key, key-value pairs for column in the view and table to edit that information, populate multiple selection dropdowns
many_editable = {
    'Samples': {'SampleAgeSignatureName': 'AgeSignatures', 'RegionName': 'Regions', 'RockTypeName': 'RockTypes',
                'SampleContexName': 'SampleContexts', 'SamplingMethodName': 'SamplingMethods',
                'SettingName': 'Settings',
                'UnitName': 'Units'},
    'Aliquots': {'AliquotContextName': 'AliquotContexts'},
    'Spots': {'SpotCompositionName': 'SpotCompositions', 'SpotContextName': 'SpotContexts'},
    'UPbAnalyses': {'RejectionReasonName': 'RejectionReasons', 'UPbAnalysisContextName': 'UPbAnalysisContexts'},
    'References': {}
}
# One-to-many columns for each table key, key-value pairs for column in the view and table to edit that information, populate single selection dropdowns
one_editable = {
    'Samples': {'SampleGPSLocationDisplay': 'GPSLocations', 'SampleAgeCalculated': 'SampleAges',
                'ColumnName': 'Columns',
                'ColumnHeightDepthUnitAbbreviation': 'DistanceUnits', 'AliquotName': 'Aliquots'},
    'Columns': {'ColumnTotalHeightDepthUnitAbbreviation': 'DistanceUnits', 'ColumnBaseGPSDisplay': 'GPSLocations'},
    'Aliquots': {'SampleName': 'Samples', 'SpotName': 'Spots'},
    'Spots': {'AliquotName': 'Aliquots', 'SpotCompositionName': 'SpotCompositions'},
    'UPbAnalyses': {'SpotName': 'Spots', 'AliquotName': 'Aliquots', 'SampleName': 'Samples',
                    'UPbReference': 'References',
                    'LabFacilityName': 'LabFacilities', 'InstrumentName': 'Instruments',
                    'UPbAnalysisMethodName': 'UPbAnalysisMethods',
                    'RatioErrorFormatAbbreviation': 'ErrorFormats', 'AgeUnitAbbreviation': 'AgeUnits',
                    'AgeErrorFormatAbbreviation': 'ErrorFormats', 'ConcordanceFormatAbbreviation': 'ConcordanceFormats',
                    'SpotSizeUnitAbbreviation': 'DistanceUnits'},
    'References': {}
}

non_editable = {
    'Samples': ['SpotCount', 'Accepted/TotalUPbAnalyses', 'RejectionReasonName', 'SampleCreated', 'SampleModified'],
    'Columns': ['ColumnCreated', 'ColumnModified'],
    'Aliquots': ['AliquotCreated', 'AliquotModified'],
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
    'UPbAnalyses': ['SpotName', 'AliquotName', 'SampleName']
}
"Tables that are the basis for view and their columns that cannot be null"

user_viewable_tables = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts',
                        'Columns', 'Instruments', 'LabFacilities', 'References', 'Regions', 'RejectionReasons',
                        'RockTypes', 'SampleContexts', 'Samples', 'SamplingMethods', 'Settings', 'SpotCompositions',
                        'SpotContexts', 'UPbAnalysisMethods', 'UPbAnalysisContexts', 'Units']
"""List of all user-viewable tables and trees used throughout GeoCORK."""

user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts', 'Aliquots',
                       'Regions', 'RockTypes', 'SampleContexts', 'SamplingMethods', 'Settings', 'SpotCompositions',
                       'SpotContexts', 'UPbAnalysisMethods', 'UPbAnalysisContexts', 'Units']
"""List of all user-viewable trees used throughout GeoCORK. If a table is included in this list it is assumed to be in the correct format"""

export_database_tables_viewable = sorted(user_viewable_tables + ['UPbAnalyses', 'Aliquots', 'Spots'])
"""List of all tables to be viewed in the ExporterWidget for exporting a database. Extra tables are included for sanity checking."""

conditionally_editable_tables = ['GPSLocations', 'SampleAges', 'Spots', 'UPbAnalyses']
conditionally_editable_trees = ['Aliquots']

trigger_tables = ['Columns', 'ColumnEditView', 'GPSLocations', 'SampleAges', 'Samples', 'SampleEditView','Spots',
                  'SpotEditView', 'UPbAnalyses', 'UPbView', 'UPbEditView']

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
        'bridge_table': 'SampleAges_AgeSignature',
        'bridge_from_column': 'SampleAgeID',
        'bridge_to_column': 'AgeSignatureID',
    },
    'Ages.[AgeName]': {
        'id_column': 'AgeID',
        'name_column': 'AgeName',
        'parent_column': 'ParentAgeID',
        'cte_name': 'RecursiveAges'
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
    'SpotCompositions.[SpotCompositionName]': {
        'id_column': 'SpotCompositionID',
        'name_column': 'SpotCompositionName',
        'parent_column': 'ParentSpotCompositionID',
        'cte_name': 'RecursiveSpotCompositions',
        'bridge_table': 'Spots_SpotCompositions',
        'bridge_from_column': 'SpotID',
        'bridge_to_column': 'SpotCompositionID',
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
                           'AgeConversions',
                           'ConcordanceConversions',
                           'DistanceConversions',
                           'ErrorConversions',
                           'Instruments',
                           'LabFacilities',
                           'RejectionReasons',
                           'References',
                           'UPbAnalysisContexts',
                           'UPbAnalysisMethods',
                           'SpotCompositions',
                           'SpotContexts',
                           'AliquotContexts',
                           'AgeConstraints',
                           'AgeInterpretations',
                           'AgeSignatures',
                           'Ages',
                           'Columns',
                           'GPSConversions',
                           'GPSFormats',
                           'GPSLocations',
                           'Regions',
                           'RockTypes',
                           'SampleAges',
                           'SampleContexts',
                           'SampleAges_AgeConstraints',
                           'SampleAges_AgeInterpretations',
                           'SampleAges_References',
                           'SamplingMethods',
                           'Settings',
                           'Units',
                           'Samples',
                           'Aliquots',
                           'Spots',
                           'UPbAnalyses',
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
                           'FilterGroups'
                           ]
"""Used in MergeDatabase.py as the order of tables to merge first to last. Since the database is relational it must 
be merged so the related data is merged last so updated primary keys can be properly generated"""

views = ['SampleView', 'SampleEditView', 'AliquotView', 'AliquotEditView', 'SpotView', 'SpotEditView', 'UPbView',
         'UPbEditView', 'ColumnView', 'ColumnEditView', 'ReferenceView']
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
                        'Percent disagreement between the 206Pb/238U age and the 207Pb/206Pb age'),
                       ('Minimum segmented discordance', 'MinSegDis',
                        'Minimum of |206Pb/238U-207Pb/235U| aged and |206Pb/207Pb-207Pb/235U| ages')]
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

as_table_dict = {
    'DirectAgeErrorFormats': 'ErrorFormats',
    'OldAge': 'Ages',
    'YoungAge': 'Ages',
    'AgeReferences': 'References',
    'SampleLatDirections': 'DirectionUnits',
    'SampleLonDirections': 'DirectionUnits',
    'SampleElevationUnits': 'DistanceUnits',
    'ColumnGPS': 'GPSLocations',
    'ColumnLatDirections': 'DirectionUnits',
    'ColumnLonDirections': 'DirectionUnits',
    'ColumnElevationUnits': 'DistanceUnits',
    'ColumnGPSFormats': 'GPSFormats',
    'ColumnHeightDepthUnits': 'DistanceUnits',
    'UPbReferences': 'References',
    'UPbReferenceView': 'ReferenceView',
    'RatioErrorFormats': 'ErrorFormats',
    'AgeErrorFormats': 'ErrorFormats',
    'UPbAgeUnits': 'AgeUnits',
    'UPbAgeInterpretations': 'AgeInterpretations',
    'SpotSizeUnits': 'DistanceUnits',
    'UPbRejectionReasons': 'RejectionReasons',
    'UPbAnalysisContexts': 'UPbAnalysisContexts'
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
        "AliquotName", "AliquotCreated", "AliquotModified"
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

        "ErrorCorr/Rho",

        "CalculatedConcordance",
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

view_attributes_dict = {
    'SampleView': [
        f"{qsample_id.split('AS ')[1]}", f"{qigsn.split('AS ')[1]}", f"{qsample_name.split('AS ')[1]}",
        f"{qsample_description.split('AS ')[1]}", f"{qgps.split('AS ')[1]}", f"{qsample_elev.split('AS ')[1]}",
        f"{qsample_age.split('AS ')[1]}", f"{qsample_age_constraint.split('AS ')[1]}", f"{qsample_age_interpretation.split('AS ')[1]}",
        f"{qsample_age_references.split('AS ')[1]}", f"{qcolumn_name.split('AS ')[1]}", f"{qsample_column_data.split('AS ')[1]}",
        f"{qage_signature.split('AS ')[1]}", f"{qregions.split('AS ')[1]}", f"{qrock_types.split('AS ')[1]}",
        f"{qsample_context.split('AS ')[1]}", f"{qsampling_methods.split('AS ')[1]}", f"{qsettings.split('AS ')[1]}",
        f"{qunits.split('AS ')[1]}", f"{qaliquots.split('AS ')[1]}", f"{qaliquot_contexts.split('AS ')[1]}",
        f"{qspot_count.split('AS ')[1]}", f"{qspot_compositions.split('AS ')[1]}", f"{qspot_contexts.split('AS ')[1]}",
        f"{qupb_count.split('AS ')[1]}", f"{qupb_lab_facilities.split('AS ')[1]}", f"{qupb_analysis_methods.split('AS ')[1]}",
        f"{qupb_ratio_error_formats.split('AS ')[1]}", f"{qupb_age_units.split('AS ')[1]}", f"{qupb_age_error_formats.split('AS ')[1]}",
        f"{qconcordance_formats.split('AS ')[1]}", f"{qspot_sizes.split('AS ')[1]}", f"{qupb_rejection_reasons.split('AS ')[1]}",
        f"{qupb_contexts.split('AS ')[1]}", f"{qupb_references.split('AS ')[1]}", f"{qsample_created.split('AS ')[1]}",
        f"{qsample_modified.split('AS ')[1]}"
        ],
    'SampleEditView': [
        f"{qsample_id.split('AS ')[1]}", f"{qigsn.split('AS ')[1]}", f"{qsample_name.split('AS ')[1]}",
        f"{qsample_description.split('AS ')[1]}", f"{qgps_display.split('AS ')[1]}",
        f"{qsample_elev_display.split('AS ')[1]}",
        f"{qsample_elev_unit.split('AS ')[1]}", f"{qsample_age_constraint.split('AS ')[1]}",
        f"{qsample_age_interpretation.split('AS ')[1]}",
        f"{qsample_age_references.split('AS ')[1]}", f"{qcolumn_name.split('AS ')[1]}",
        f"{qsample_column_data_display.split('AS ')[1]}", f"{qsample_column_data_unit.split('AS ')[1]}",
        f"{qage_signature.split('AS ')[1]}", f"{qregions.split('AS ')[1]}", f"{qrock_types.split('AS ')[1]}",
        f"{qsample_context.split('AS ')[1]}", f"{qsampling_methods.split('AS ')[1]}", f"{qsettings.split('AS ')[1]}",
        f"{qunits.split('AS ')[1]}", f"{qaliquots.split('AS ')[1]}", f"{qaliquot_contexts.split('AS ')[1]}",
        f"{qspot_count.split('AS ')[1]}", f"{qspot_compositions.split('AS ')[1]}", f"{qspot_contexts.split('AS ')[1]}",
        f"{qupb_count.split('AS ')[1]}", f"{qupb_lab_facilities.split('AS ')[1]}",
        f"{qupb_analysis_methods.split('AS ')[1]}", f"{qupb_ratio_error_formats.split('AS ')[1]}",
        f"{qupb_age_units.split('AS ')[1]}",
        f"{qupb_age_error_formats.split('AS ')[1]}", f"{qconcordance_formats.split('AS ')[1]}",
        f"{qspot_size.split('AS ')[1]}", f"{qspot_size_unit.split('AS ')[1]}", f"{qupb_rejection_reasons.split('AS ')[1]}",
        f"{qupb_references.split('AS ')[1]}",
        f"{qsample_created.split('AS ')[1]}", f"{qsample_modified.split('AS ')[1]}"
        ],
    'ColumnView': [
        f"{qcolumn_id.split('AS ')[1]}", f"{qcolumn_name.split('AS ')[1]}", f"{qcolumn_calc_total_height_depth.split('AS ')[1]}", f"{qcolumn_gps.split('AS ')[1]}",
        f"{qcolumn_description.split('AS ')[1]}", f"{qcolumn_created.split('AS ')[1]}", f"{qcolumn_modified.split('AS ')[1]}"
    ],
    'ColumnEditView': [
        f"{qcolumn_id.split('AS ')[1]}", f"{qcolumn_name.split('AS ')[1]}", f"{qcolumn_total_height_depth.split('AS ')[1]}", f"{qcolumn_total_height_depth_unit.split('AS ')[1]}",
        f"{qcolumn_gps_display.split('AS ')[1]}", f"{qcolumn_description.split('AS ')[1]}", f"{qcolumn_created.split('AS ')[1]}", f"{qcolumn_modified.split('AS ')[1]}"
    ],
    'AliquotView': [
        f"{qaliquot_id.split('AS ')[1]}", f"{qaliquot_parent_id.split('AS ')[1]}",
        f"{qaliquot_parent_row.split('AS ')[1]}", f"{qaliquot_name.split('AS ')[1]}", f"{qsample_id.split('AS ')[1]}",
        f"{qaliquot_sample.split('AS ')[1]}", f"{qaliquot_contexts.split('AS ')[1]}", f"{qspot_count.split('AS ')[1]}",
        f"{qspot_compositions.split('AS ')[1]}", f"{qspot_contexts.split('AS ')[1]}", f"{qupb_count.split('AS ')[1]}",
        f"{qupb_lab_facilities.split('AS ')[1]}", f"{qupb_analysis_methods.split('AS ')[1]}",
        f"{qupb_ratio_error_formats.split('AS ')[1]}", f"{qupb_age_units.split('AS ')[1]}",
        f"{qupb_age_error_formats.split('AS ')[1]}", f"{qconcordance_formats.split('AS ')[1]}",
        f"{qspot_sizes.split('AS ')[1]}", f"{qupb_rejection_reasons.split('AS ')[1]}",
        f"{qupb_contexts.split('AS ')[1]}",
        f"{qupb_references.split('AS ')[1]}", f"{qaliquot_created.split('AS ')[1]}",
        f"{qaliquot_modified.split('AS ')[1]}"
    ],
    'AliquotEditView': [
        f"{qaliquot_id.split('AS ')[1]}", f"{qaliquot_parent_id.split('AS ')[1]}",
        f"{qaliquot_parent_row.split('AS ')[1]}", f"{qaliquot_name.split('AS ')[1]}", f"{qsample_id.split('AS ')[1]}",
        f"{qaliquot_sample.split('AS ')[1]}", f"{qaliquot_contexts.split('AS ')[1]}",
        f"{qaliquot_created.split('AS ')[1]}", f"{qaliquot_modified.split('AS ')[1]}"
    ],
    'SpotView': [
        f"{qspot_id.split('AS ')[1]}", f"{qsample_id.split('AS ')[1]}", f"{qaliquot_id.split('AS ')[1]}",
        f"{qspots.split('AS ')[1]}",
        f"{qsample_name.split('AS ')[1]}", f"{qaliquot_name.split('AS ')[1]}", f"{qspot_compositions.split('AS ')[1]}",
        f"{qspot_contexts.split('AS ')[1]}",
        f"{qupb_lab_facilities.split('AS ')[1]}", f"{qupb_analysis_methods.split('AS ')[1]}",
        f"{qupb_ratio_error_formats.split('AS ')[1]}", f"{qupb_age_units.split('AS ')[1]}",
        f"{qupb_age_error_formats.split('AS ')[1]}", f"{qconcordance_formats.split('AS ')[1]}",
        f"{qspot_sizes.split('AS ')[1]}", f"{qupb_rejected.split('AS ')[1]}",
        f"{qupb_rejection_reasons.split('AS ')[1]}", f"{qupb_contexts.split('AS ')[1]}",
        f"{qupb_references.split('AS ')[1]}", f"{qspot_created.split('AS ')[1]}", f"{qspot_modified.split('AS ')[1]}"
    ],
    'SpotEditView': [
        f"{qspot_id.split('AS ')[1]}", f"{qsample_id.split('AS ')[1]}", f"{qaliquot_id.split('AS ')[1]}",
        f"{qspots.split('AS ')[1]}", f"{qsample_name.split('AS ')[1]}", f"{qaliquot_name.split('AS ')[1]}",
        f"{qspot_compositions.split('AS ')[1]}", f"{qspot_contexts.split('AS ')[1]}",
        f"{qspot_created.split('AS ')[1]}", f"{qspot_modified.split('AS ')[1]}"
    ],
    'UPbView': [
        f"{qupb_id.split('AS ')[1]}", f"{qspot_name.split('AS ')[1]}", f"{qaliquot_name.split('AS ')[1]}",
        f"{qsample_name.split('AS ')[1]}", f"{qupb_references.split('AS ')[1]}",
        f"{qupb_lab_facilities.split('AS ')[1]}",
        f"{qupb_instruments.split('AS ')[1]}", f"{qupb_analysis_methods.split('AS ')[1]}", '"Pb204cps"', '"Pb206cps"',
        '"Pb207cps"', '"Pb208cps"', '"Pb*cps"', '"Th232cps"',
        '"U235cps"', '"U238cps"', '"Uppm"', '"Thppm"',
        '"CalculatedU/Th"', '"CalculatedTh/U"',
        '"Calculated206Pb/207Pb"', '"Calculated206Pb/207PbError"',
        '"Calculated207Pb/206Pb"', '"Calculated207Pb/206PbError"',
        '"Calculated207Pb/235U"', '"Calculated207Pb/235UError"',
        '"Calculated235U/207Pb"', '"Calculated235U/207PbError"',
        '"Calculated206Pb/238U"', '"Calculated206Pb/238UError"',
        '"Calculated238U/206Pb"', '"Calculated238U/206PbError"',
        '"Calculated208Pb/232Th"', '"Calculated208Pb/232ThError"',
        '"Calculated232Th/208Pb"', '"Calculated232Th/208PbError"',
        '"Calculated238U/232Th"', '"Calculated238U/232ThError"',
        '"Calculated232Th/238U"', '"Calculated232Th/238UError"',
        '"Calculated204Pb/238U"', '"Calculated204Pb/238UError"',
        '"Calculated238U/204Pb"', '"Calculated238U/204PbError"',
        '"Calculated206Pb/204Pb"', '"Calculated206Pb/204PbError"',
        '"Calculated204Pb/206Pb"', '"Calculated204Pb/206PbError"',
        '"Calculated207Pb/204Pb"', '"Calculated207Pb/204PbError"',
        '"Calculated204Pb/207Pb"', '"Calculated204Pb/207PbError"',
        '"Calculated208Pb/204Pb"', '"Calculated208Pb/204PbError"',
        '"Calculated204Pb/208Pb"', '"Calculated204Pb/208PbError"', '"ErrorCorr/Rho"',
        '"Calculated207Pb/206PbAge"', '"Calculated207Pb/206PbAgeError"',
        '"Calculated206Pb/238UAge"', '"Calculated206Pb/238UAgeError"',
        '"Calculated207Pb/235UAge"', '"Calculated207Pb/235UAgeError"',
        '"Calculated208Pb/232ThAge"', '"Calculated208Pb/232ThAgeError"',
        '"CalculatedBestAgeFilled"', '"CalculatedBestAgeErrorFilled"',
        '"CalculatedSpotSize"', '"CalculatedConcordance"',
        f"{qupb_rejected.split('AS ')[1]}", f"{qupb_rejection_reasons.split('AS ')[1]}",
        f"{qupb_contexts.split('AS ')[1]}",
        f"{qupb_created.split('AS ')[1]}", f"{qupb_modified.split('AS ')[1]}"
    ],
    'UPbEditView': [
        f"{qupb_id.split('AS ')[1]}", f"{qsample_id.split('AS ')[1]}", f"{qaliquot_id.split('AS ')[1]}",
        f"{qspot_id.split('AS ')[1]}", f"{qspot_name.split('AS ')[1]}", f"{qaliquot_name.split('AS ')[1]}",
        f"{qsample_name.split('AS ')[1]}",
        f"{qupb_references.split('AS ')[1]}", f"{qupb_lab_facilities.split('AS ')[1]}",
        f"{qupb_instruments.split('AS ')[1]}", f"{qupb_analysis_methods.split('AS ')[1]}",
        '"Pb204cps"', '"Pb206cps"',
        '"Pb207cps"', '"Pb208cps"', '"Pb*cps"', '"Th232cps"',
        '"U235cps"', '"U238cps"', '"Uppm"', '"Thppm"',
        '"U/Th"', '"Th/U"',
        '"206Pb/207Pb"', '"206Pb/207PbError"',
        '"207Pb/206Pb"', '"207Pb/206PbError"',
        '"206Pb/238U"', '"206Pb/238UError"',
        '"238U/206Pb"', '"238U/206PbError"',
        '"207Pb/235U"', '"207Pb/235UError"',
        '"235U/207Pb"', '"235U/207PbError"',
        '"208Pb/232Th"', '"208Pb/232ThError"',
        '"232Th/208Pb"', '"232Th/208PbError"',
        '"238U/232Th"', '"238U/232ThError"',
        '"232Th/238U"', '"232Th/238UError"',
        '"204Pb/238U"', '"204Pb/238UError"',
        '"238U/204Pb"', '"238U/204PbError"',
        '"206Pb/204Pb"', '"206Pb/204PbError"',
        '"204Pb/206Pb"', '"204Pb/206PbError"',
        '"207Pb/204Pb"', '"207Pb/204PbError"',
        '"204Pb/207Pb"', '"204Pb/207PbError"',
        '"208Pb/204Pb"', '"208Pb/204PbError"',
        '"204Pb/208Pb"', '"204Pb/208PbError"',
        f"{qupb_ratio_error_formats.split('AS ')[1]}", '"ErrorCorr/Rho"',
        '"207Pb/206PbAge"', '"207Pb/206PbAgeError"',
        '"207Pb/235UAge"', '"207Pb/235UAgeError"',
        '"206Pb/238UAge"', '"206Pb/238UAgeError"',
        '"208Pb/232ThAge"', '"208Pb/232ThAgeError"',
        '"BestAge"', '"BestAgeError"',
        '"BestAgeFilled"', '"BestAgeErrorFilled"',
        f"{qupb_age_error_formats.split('AS ')[1]}", f"{qupb_age_units.split('AS ')[1]}", '"Concordance"',
        f"{qconcordance_formats.split('AS ')[1]}",
        '"SpotSize"', f"{qspot_size_unit.split('AS ')[1]}", f"{qupb_rejected.split('AS ')[1]}",
        f"{qupb_rejection_reasons.split('AS ')[1]}", f"{qupb_contexts.split('AS ')[1]}",
        f"{qupb_created.split('AS ')[1]}", f"{qupb_modified.split('AS ')[1]}"
    ],
    'ReferenceView': [
        f"{qreference_id.split('AS ')[1]}", f"{qreference_display.split('AS ')[1]}", f"{qauthors.split('AS ')[1]}",
        f"{qyear.split('AS ')[1]}", f"{qtitle.split('AS ')[1]}", f"{qsource.split('AS ')[1]}",
        f"{qdoi.split('AS ')[1]}",
        f"{qreference_description.split('AS ')[1]}", f"{qreference_created.split('AS ')[1]}",
        f"{qreference_modified.split('AS ')[1]}"
    ]
}


# dictionary of Views and their associated settings_value for columns to display throughout GeoCORK
view_setting_dict = {
    'SampleView': 'sample_view_columns',
    'SampleEditView': 'sample_edit_columns',
    'AliquotView': 'aliquot_view_columns',
    'AliquotEditView': 'aliquot_edit_columns',
    'SpotView': 'spot_view_columns',
    'SpotEditView': 'spot_edit_columns',
    'UPbView': 'upb_analysis_view_columns',
    'UPbEditView': 'upb_analysis_edit_columns',
    'ColumnView': 'column_view_columns',
    'ColumnEditView': 'column_edit_columns',
    'ReferenceView': 'reference_view_columns',
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
"""List of valid columns to be entered through the importer.
No Calculated values should be in this list
Used to create the insert statement with SQL"""

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
"""List of User-readable columns/info able to be imported into the database"""


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
            case 'ColumnView':
                if column_view_join not in join:
                    join += column_view_join + '\n'
            case 'LabFacilities':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_labs_join not in join:
                    join += upb_labs_join + '\n'
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
                if upb_reference_view_join not in join:
                    join += upb_reference_view_join + '\n'
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
            case 'UPbReferenceView':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_view_join not in join:
                    join += upb_reference_view_join + '\n'
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'
            case 'Samples':
                pass
    return join
