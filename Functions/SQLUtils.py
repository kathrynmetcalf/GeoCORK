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
qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) AS "Age Signatures"'
qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) AS "Measured Column Name"'
qcolumn_data = f'HeightDepth || "±" || HeightDepthError AS "Column Data ({selected_heightdepth_unit})"'
qcolumn_gps = f'''ColumnGPS.CalculatedBaseGPS AS "GPS Coordinates"'''
qgps = f'''SampleGPS.CalculatedGPSCoordinates AS "GPS Coordinates"'''
qelev = f'SampleGPS.CalculatedGPSElev || "±" || SampleGPS.CalculatedGPSElevError AS "Elevation ({selected_elev_unit})"'
qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName) AS "Aliquots"'
qspots = 'GROUP_CONCAT(DISTINCT SpotName) AS "Spots"'
qsources = 'GROUP_CONCAT(DISTINCT ShortCitation) AS "Sources"'
qsample_context = 'GROUP_CONCAT(DISTINCT SampleContextName) AS "Sample Contexts"'
qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) AS "Sampling Method"'
qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) AS "Rock Types"'
qregions = 'GROUP_CONCAT(DISTINCT RegionName) AS "Regions"'
qsettings = 'GROUP_CONCAT(DISTINCT SettingName) AS "Settings"'
qunits = 'GROUP_CONCAT(DISTINCT UnitName) AS "Units"'
qupb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) AS "UPb Analysis Methods"'
qlabs = 'GROUP_CONCAT(DISTINCT LabFacilityName) AS "Lab Facilities"'
qspot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) AS "Spot Contexts"'
qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) AS "Spot Compositions"'
qaliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) AS "Aliquot Contexts"'


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

# GPSLocation joins
gps_sample_join = 'LEFT JOIN GPSLocations AS SampleGPS ON Samples.SampleGPSLocationID=SampleGPS.GPSLocationID'
gps_column_join = 'LEFT JOIN GPSLocations AS ColumnGPS ON Columns.ColumnBaseGPSID=ColumnGPS.GPSLocationID'

# SampleJoins
age_signature_join = '''LEFT JOIN Samples_AgeSignatures ON Samples.SampleID=Samples_AgeSignatures.SampleID
                                    LEFT JOIN AgeSignatures ON AgeSignatures.AgeSignatureID=Samples_AgeSignatures.AgeSignatureID'''
column_join = 'LEFT JOIN Columns ON Samples.SampleColumnID=Columns.ColumnID'
region_join = '''LEFT JOIN Samples_Regions ON Samples.SampleID=Samples_Regions.SampleID
                                LEFT JOIN Regions ON Regions.RegionID=Samples_Regions.RegionID'''
rock_type_join = '''LEFT JOIN Samples_RockTypes ON Samples.SampleID=Samples_RockTypes.SampleID
                                LEFT JOIN RockTypes ON RockTypes.RockTypeID=Samples_RockTypes.RockTypeID'''
sample_context_join = '''LEFT JOIN Samples_SampleContexts ON Samples.SampleID=Samples_SampleContexts.SampleID
                                LEFT JOIN SampleContexts ON SampleContexts.SampleContextID=Samples_SampleContexts.SampleContextID'''
sample_sampleage_join = '''LEFT JOIN Samples_SampleAges ON Samples.SampleID=Samples_SampleAges.SampleID
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
                        'SpotCompositions', 'SpotContexts', 'UPbAnalyses', 'UPbAnalysisMethods', 'Units']
user_viewable_trees = ['AgeConstraints', 'AgeInterpretations', 'AgeSignatures', 'Ages', 'AliquotContexts', 'Regions', 'RejectionReasons', 'RockTypes', 'SampleContexts',
                       'SamplingMethods', 'Settings', 'SpotCompositions', 'SpotContexts', 'UPbAnalysisMethods', 'Units']
conditionally_editable_tables = ['Aliquots', 'GPSLocations', 'SampleAges', 'Spots']
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