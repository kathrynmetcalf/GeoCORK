qsample_id = 'Samples.SampleID'
qsample_name = 'SampleName AS "Sample Name"'
qage = 'AverageAge || "±" || COALESCE(AverageAgeError, " ") as "Age (Ma)"'
qage_range = 'COALESCE(OldestAge, " ") || "-" || COALESCE(YoungestAge, " ") as "Age Range (Ma)"'
qgeo_age = 'COALESCE(OldA.AgeName, " ") || "-" || COALESCE(YoungA.AgeName, " ") as "Geologic Age"'
qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures"'
qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) as "Measured Column Name"'
qcolumn_data = 'HeightDepth || "±" || COALESCE(HeightDepthError, " " || HeightDepthUnit) as "Column Data"'
qlat = f'''LatDeg || "°" || LatMin || "'" || LatSec || '"' as "Latitude"'''
qlon = f'''LonDeg || "°" || LonMin || "'" || LonSec || '"' as "Longitude"'''
qutm_zone = 'UTMZone As "UTM Zone"'
qutm_n = 'UTMN As "UTM Northing"'
qutm_e = 'UTME As "UTM Easting"'
qelev = 'Elev || "±" || COALESCE(ElevError, " " || ElevUnit) as "Elevation"'
qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots"'
qspots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
qreferences = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
qcontext = 'GROUP_CONCAT(DISTINCT SampleContextName) as "Sample Context"'
qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) as "Sampling Method"'
qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"'
qregions = 'GROUP_CONCAT(DISTINCT RegionName) as "Regions"'
qsettings = 'GROUP_CONCAT(DISTINCT SettingName) as "Settings"'
qunits = 'GROUP_CONCAT(DISTINCT UnitName) as "Units"'
qupb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
qlabs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'
qspot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Context"'
qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
qaliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Context"'

# Join lines
old_age_join = 'LEFT JOIN Ages as OldA ON Samples.OldestAgeID=OldA.AgeID'
young_age_join = 'LEFT JOIN Ages as YoungA ON Samples.YoungestAgeID=YoungA.AgeID'
age_signature_join = '''LEFT JOIN Samples_AgeSignatures ON Samples.SampleID=Samples_AgeSignatures.SampleID
                                    LEFT JOIN AgeSignatures ON AgeSignatures.AgeSignatureID=Samples_AgeSignatures.AgeSignatureID'''
column_join = '''LEFT JOIN Samples_Columns ON Samples.SampleID=Samples_Columns.SampleID
                                    LEFT JOIN Columns ON Columns.ColumnID=Samples_Columns.ColumnID'''
rock_type_join = '''LEFT JOIN Samples_RockTypes ON Samples.SampleID=Samples_RockTypes.SampleID
                                LEFT JOIN RockTypes ON RockTypes.RockTypeID=Samples_RockTypes.RockTypeID'''
region_join = '''LEFT JOIN Samples_Regions ON Samples.SampleID=Samples_Regions.SampleID
                                LEFT JOIN Regions ON Regions.RegionID=Samples_Regions.RegionID'''
setting_join = '''LEFT JOIN Samples_Settings ON Samples.SampleID=Samples_Settings.SampleID
                                LEFT JOIN Settings ON Settings.SettingID=Samples_Settings.SettingID'''
unit_join = '''LEFT JOIN Samples_Units ON Samples.SampleID=Samples_Units.SampleID
                                LEFT JOIN Units ON Units.UnitID=Samples_Units.UnitID'''
sample_context_join = '''LEFT JOIN Samples_SampleContext ON Samples.SampleID=Samples_SampleContext.SampleID
                                LEFT JOIN SampleContext ON SampleContext.SampleContextID=Samples_SampleContext.SampleContextID'''
sampling_method_join = '''LEFT JOIN Samples_SamplingMethods ON Samples.SampleID=Samples_SamplingMethods.SampleID
                                LEFT JOIN SamplingMethods ON SamplingMethods.SamplingMethodID=Samples_SamplingMethods.SamplingMethodID'''

aliquot_join = 'LEFT JOIN Aliquots ON Aliquots.SampleID=Samples.SampleID'
spot_join = 'LEFT JOIN Spots ON Spots.AliquotID=Aliquots.AliquotID'
upb_data_join = 'LEFT JOIN UPbData ON UPbData.SpotID=Spots.SpotID'
source_join = 'LEFT JOIN Sources ON Sources.SourceID=UPbData.SourceID'
upb_method_join = 'LEFT JOIN UPbAnalysisMethods ON UPbAnalysisMethods.UPbAnalysisMethodID=UPbData.UPbAnalysisMethodID'
instruments_join = 'LEFT JOIN Instruments ON Instruments.InstrumentID=UPbData.InstrumentID'
labs_join = 'LEFT JOIN LabFacilities ON LabFacilities.LabFacilityID=UPbData.LabFacilityID'
spot_context_join = '''LEFT JOIN Spots_SpotContext ON Spots.SpotID=Spots_SpotContext.SpotID
                                LEFT JOIN SpotContext ON SpotContext.SpotContextID=Spots_SpotContext.SpotContextID'''
spot_composition_join = '''LEFT JOIN SpotCompositions ON SpotCompositions.SpotCompositionID=Spots.SpotCompositionID'''
aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContext ON Aliquots.AliquotID=Aliquots_AliquotContext.AliquotID
                                LEFT JOIN AliquotContext ON AliquotContext.AliquotContextID=Aliquots_AliquotContext.AliquotContextID'''