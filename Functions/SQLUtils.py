selected_age_unit = 'Ma'
selected_elev_unit = 'm'
selected_heightdepth_unit = 'm'

# ID columns
qsample_id = 'Samples.SampleID'
qaliquot_id = 'Aliquots.AliquotID'
qspot_id = 'Spots.SpotID'

# View columns
qsample_name = 'SampleName AS "Sample Name"'
qage = f'CalculatedDirectAge || "±" || COALESCE(CalculatedDirectAgeError, " ") as "Age {selected_age_unit}"'
qage_range = f'COALESCE(CalculatedOldestDirectAge, " ") || "-" || COALESCE(CalculatedYoungestDirectAge, " ") as "Age Range {selected_age_unit}"'
qgeo_age = 'COALESCE(OldAge.AgeName, " ") || "-" || COALESCE(YoungAge.AgeName, " ") as "Geologic Age"'
qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures"'
qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) as "Measured Column Name"'
qcolumn_data = f'HeightDepth || "±" || COALESCE(HeightDepthError, " " || {selected_heightdepth_unit}) as "Column Data"'
qcolumn_gps = f'''CalculatedBaseGPS as "GPS Coordinates"'''
qgps = f'''CalculatedGPS as "GPS Coordinates"'''
qelev = f'CalculatedElev || "±" || COALESCE(CalculatedElevError, " " || {selected_elev_unit}) as "Elevation"'
qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots"'
qspots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
qsources = 'GROUP_CONCAT(DISTINCT ShortCitation) as "Sources"'
qsample_context = 'GROUP_CONCAT(DISTINCT SampleContextName) as "Sample Contexts"'
qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) as "Sampling Method"'
qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"'
qregions = 'GROUP_CONCAT(DISTINCT RegionName) as "Regions"'
qsettings = 'GROUP_CONCAT(DISTINCT SettingName) as "Settings"'
qunits = 'GROUP_CONCAT(DISTINCT UnitName) as "Units"'
qupb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
qlabs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'
qspot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
qaliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Contexts"'


# Join lines
# SampleAge-Age joins
sample_age_join = 'LEFT JOIN Ages ON SampleAges.OldestAgeID=Ages.AgeID OR SampleAges.YoungestAgeID=Ages.AgeID'
sample_age_error_type_join = 'LEFT JOIN AgeErrorTypes ON AgeErrorTypes.AgeErrorTypeID=SampleAges.DirectAgeErrorTypeID'
sample_age_unit_join = 'LEFT JOIN AgeUnits ON AgeUnits.AgeUnitID=SampleAges.AgeUnitID'
sample_old_age_join = 'LEFT JOIN Ages as OldAge ON SampleAges.OldestAgeID=OldAge.AgeID'
sample_young_age_join = 'LEFT JOIN Ages as YoungAge ON SampleAges.YoungestAgeID=YoungAge.AgeID'
sample_age_constraint_join = 'LEFT JOIN AgeConstraints ON AgeConstraints.AgeConstraintID=SampleAges.AgeConstraintID'
sample_age_interpretation_join = 'LEFT JOIN AgeInterpretations ON AgeInterpretations.AgeInterpretationID=SampleAges.AgeInterpretationID'

# GPSLocation joins
gps_sample_join = 'LEFT JOIN GPSLocations ON Samples.GPSLocationID=GPSLocations.GPSLocationID'
gps_column_join = 'LEFT JOIN GPSLocations AS ColumnGPS ON Columns.ColumnBaseGPSID=GPSLocations.GPSLocationID'

# SampleJoins
age_signature_join = '''LEFT JOIN Samples_AgeSignatures ON Samples.SampleID=Samples_AgeSignatures.SampleID
                                    LEFT JOIN AgeSignatures ON AgeSignatures.AgeSignatureID=Samples_AgeSignatures.AgeSignatureID'''
column_join = 'LEFT JOIN Columns ON Samples.ColumnID=Columns.ColumnID'
region_join = '''LEFT JOIN Samples_Regions ON Samples.SampleID=Samples_Regions.SampleID
                                LEFT JOIN Regions ON Regions.RegionID=Samples_Regions.RegionID'''
rock_type_join = '''LEFT JOIN Samples_RockTypes ON Samples.SampleID=Samples_RockTypes.SampleID
                                LEFT JOIN RockTypes ON RockTypes.RockTypeID=Samples_RockTypes.RockTypeID'''
sample_sampleage_join = '''LEFT JOIN Samples_SampleAges ON Samples.SampleID=Samples_SampleAges.SampleID
                                    LEFT JOIN SampleAges ON SampleAges.SampleAgeID=Samples_SampleAges.SampleAgeID'''
sample_context_join = '''LEFT JOIN Samples_SampleContexts ON Samples.SampleID=Samples_SampleContexts.SampleID
                                LEFT JOIN SampleContexts ON SampleContexts.SampleContextID=Samples_SampleContexts.SampleContextID'''
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
upb_ratio_error_type_join = 'LEFT JOIN ErrorTypes AS RatioErrorTypes ON ErrorTypes.ErrorTypeID=UPbAnalyses.RatioErrorTypeID'
upb_age_error_type_join = 'LEFT JOIN ErrorTypes AS AgeErrorTypes ON ErrorTypes.ErrorTypeID=UPbAnalyses.AgeErrorTypeID'
upb_best_age_error_type_join = 'LEFT JOIN ErrorTypes AS BestAgeErrorTypes ON ErrorTypes.ErrorTypeID=UPbAnalyses.BestAgeErrorTypeID'
upb_age_unit_join = 'LEFT JOIN AgeUnits AS UPbAgeUnits ON AgeUnits.AgeUnitID=UPbAnalyses.AgeUnitID'
upb_concordance_type_join = 'LEFT JOIN ConcordanceTypes ON ConcordanceTypes.ConcordanceTypeID=UPbAnalyses.ConcordanceTypeID'
upb_spot_size_unit_join = 'LEFT JOIN SpotSizeUnits ON UPbAnalyses.SpotSizeUnitID=DistanceUnits.DistanceUnitID'
upb_rejection_reason_join = 'LEFT JOIN RejectionReasons ON UPbAnalyses.RejectionReasonID=RejectionReasons.RejectionReasonID'


user_viewable_tables = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts', 'Columns', 'Instruments', 'LabFacilities',
                        'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts', 'Samples', 'SamplingMethods', 'Settings', 'Sources',
                        'SpotCompositions', 'SpotContexts', 'UPbAnalyses', 'UPbAnalysisMethods', 'Units']
user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts', 'Regions', 'RockTypes', 'SampleContexts',
                       'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContexts', 'UPbAnalysisMethods', 'Units']
conditionally_editable_tables = ['Aliquots', 'GPSLocations', 'SampleAges', 'Spots']
conditionally_editable_trees = ['Aliquots']

# todo: Create generated columns and then join them in the query
# Generated Columns


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