import sqlite3

from Functions.Create_database import CREATE_SAMPLE_AGE_TABLE

'''Commands to create the database triggers'''
'''SQL strings to create each trigger'''

'''Triggers for missing pairs and units, only triggers if there is corresponding data'''
'''e.g. there is latitude but not longitude or an elevation value but no unit'''
CREATE_SAMPLEAGES_TRIGGERS = '''
CREATE TRIGGER IF NOT EXISTS validate_age_units_before_insert BEFORE INSERT ON SampleAges
BEGIN
    SELECT CASE
        WHEN NEW.MaxMa IS NOT NULL AND NEW.MaxMaUnitID IS NULL THEN
            RAISE (ABORT,'Maximum age value with missing units')
        END;
    SELECT CASE
        WHEN NEW.MinMa IS NOT NULL AND NEW.MinMaUnitID IS NULL THEN
            RAISE (ABORT,'Minimum age value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_age_units_before_update BEFORE UPDATE ON SampleAges
BEGIN
    SELECT CASE
        WHEN NEW.MaxMa IS NOT NULL AND NEW.MaxMaUnit IS NULL THEN
            RAISE (ABORT,'Maximum age value with missing units')
        END;
    SELECT CASE
        WHEN NEW.MinMa IS NOT NULL AND NEW.MinMaUnit IS NULL THEN
            RAISE (ABORT,'Minimum age value with missing units')
        END;
    SELECT CASE
        WHEN MaxMa IS NOT NULL AND NEW.MaxMaUnit IS NULL THEN
            RAISE (ABORT,'Maximum age value with missing units')
        END;
    SELECT CASE
        WHEN MinMa IS NOT NULL AND NEW.MinMaUnit IS NULL THEN
            RAISE (ABORT,'Minimum age value with missing units')
        END;
    SELECT CASE
        WHEN NEW.MaxMa IS NOT NULL AND MaxMaUnit IS NULL THEN
            RAISE (ABORT,'Maximum age value with missing units')
        END;
    SELECT CASE
        WHEN NEW.MinMa IS NOT NULL AND MinMaUnit IS NULL THEN
            RAISE (ABORT,'Minimum age value with missing units')
        END;
END;    
CREATE TRIGGER IF NOT EXISTS validate_age_error_before_insert BEFORE INSERT ON SampleAges
BEGIN
    SELECT CASE
        WHEN NEW.AverageAgeError IS NOT NULL AND NEW.AverageAgeErrorUnitID IS NULL THEN
            RAISE (ABORT,'Average age error value with missing units')
        END;
    SELECT CASE
END;
CREATE TRIGGER IF NOT EXISTS validate_age_error_before_update BEFORE UPDATE ON SampleAges
BEGIN
    SELECT CASE
        WHEN NEW.AverageAgeError IS NOT NULL AND NEW.AverageAgeErrorUnit IS NULL THEN
            RAISE (ABORT,'Average age error value with missing units')
        END;
    SELECT CASE
        WHEN AverageAgeError IS NOT NULL AND NEW.AverageAgeErrorUnit IS NULL THEN
            RAISE (ABORT,'Average age error value with missing units')
        END;
    SELECT CASE
        WHEN NEW.AverageAgeError IS NOT NULL AND AverageAgeErrorUnit IS NULL THEN
            RAISE (ABORT,'Average age error value with missing units')
        END;
END;
'''
CREATE_UPBANALYSES_TRIGGERS = '''
CREATE TRIGGER IF NOT EXISTS validate_ratio_error_units_before_insert BEFORE INSERT ON UPbAnalyses
BEGIN
    SELECT CASE
        WHEN ANY(NEW."206Pb/207PbError", NEW."207Pb/206PbError", 
        NEW."207Pb/235UError", NEW."235U/207PbError", 
        NEW."206Pb/238UError", NEW."238U/206PbError", 
        NEW."208Pb/232ThError", NEW."232Th/208PbError", 
        NEW."238U/232ThError", NEW."232Th/238UError", 
        NEW."204Pb/238UError", NEW."238U/204PbError", 
        NEW."206Pb/204PbError", NEW."204Pb/206PbError",
        NEW."207Pb/204PbError", NEW."204Pb/207PbError",
        NEW."208Pb/204PbError", NEW."204Pb/208PbError") IS NOT NULL AND NEW.RatioErrorUnitID IS NULL THEN
            RAISE (ABORT,'Ratio error value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_ratio_error_units_before_update BEFORE UPDATE ON UPbAnalyses
BEGIN
    SELECT CASE
        WHEN ANY(NEW."206Pb/207PbError", NEW."207Pb/206PbError",
        NEW."207Pb/235UError", NEW."235U/207PbError",
        NEW."206Pb/238UError", NEW."238U/206PbError",
        NEW."208Pb/232ThError", NEW."232Th/208PbError",
        NEW."238U/232ThError", NEW."232Th/238UError",
        NEW."204Pb/238UError", NEW."238U/204PbError",
        NEW."206Pb/204PbError", NEW."204Pb/206PbError",
        NEW."207Pb/204PbError", NEW."204Pb/207PbError",
        NEW."208Pb/204PbError", NEW."204Pb/208PbError") IS NOT NULL AND NEW.RatioErrorUnit IS NULL THEN
            RAISE (ABORT,'Ratio error value with missing units')
        END;
    SELECT CASE
        WHEN ANY("206Pb/207PbError", "207Pb/206PbError",
        "207Pb/235UError", "235U/207PbError",
        "206Pb/238UError", "238U/206PbError",
        "208Pb/232ThError", "232Th/208PbError",
        "238U/232ThError", "232Th/238UError",
        "204Pb/238UError", "238U/204PbError",
        "206Pb/204PbError", "204Pb/206PbError",
        "207Pb/204PbError", "204Pb/207PbError",
        "208Pb/204PbError", "204Pb/208PbError") IS NOT NULL AND NEW.RatioErrorUnit IS NULL THEN
            RAISE (ABORT,'Ratio error value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_age_error_units_before_insert BEFORE INSERT ON UPbAnalyses
BEGIN
    SELECT CASE
        WHEN ANY() IS NOT NULL AND NEW.AgeErrorUnitID IS NULL THEN
            RAISE (ABORT,'Age error value with missing units')
        END;
END;

CREATE TRIGGER IF NOT EXISTS validate_concordance_units_before_insert BEFORE INSERT ON UPbAnalyses
BEGIN
    SELECT CASE
        WHEN NEW.“Concordance206Pb/238U-206Pb/207Pb” IS NOT NULL AND NEW.“Concordance206Pb/238U-206Pb/207PbUnitID” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
    SELECT CASE
        WHEN NEW. “Concordance206Pb/238U-208Pb/232Th” IS NOT NULL AND NEW.“Concordance206Pb/238U-208Pb/232ThUnitID” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_concordance_units_before_update BEFORE UPDATE ON UPbAnalyses
BEGIN
    SELECT CASE
        WHEN NEW.“Concordance206Pb/238U-206Pb/207Pb” IS NOT NULL AND NEW.“Concordance206Pb/238U-206Pb/207PbUnit” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
    SELECT CASE
        WHEN NEW.“Concordance206Pb/238U-208Pb/232Th” IS NOT NULL AND NEW.“Concordance206Pb/238U-208Pb/232ThUnit” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
    SELECT CASE
        WHEN “Concordance206Pb/238U-206Pb/207Pb” IS NOT NULL AND NEW.“Concordance206Pb/238U-206Pb/207PbUnit” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
    SELECT CASE
        WHEN “Concordance206Pb/238U-208Pb/232Th” IS NOT NULL AND NEW.“Concordance206Pb/238U-208Pb/232ThUnit” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
    SELECT CASE
        WHEN NEW.“Concordance206Pb/238U-206Pb/207Pb” IS NOT NULL AND “Concordance206Pb/238U-206Pb/207PbUnit” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
    SELECT CASE
        WHEN NEW.“Concordance206Pb/238U-208Pb/232Th” IS NOT NULL AND “Concordance206Pb/238U-208Pb/232ThUnit” IS NULL THEN
            RAISE (ABORT,'Concordance value with missing units')
        END;
END;
'''
CREATE_GPS_TRIGGERS = '''
CREATE TRIGGER IF NOT EXISTS validate_latlon_deg_before_update BEFORE UPDATE ON GPSLocations
BEGIN
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.LonDeg IS NULL THEN
            RAISE (ABORT,'Latitude degrees is missing corresponding longitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LonDeg IS NOT NULL AND NEW.LatDeg IS NULL THEN
            RAISE (ABORT,'Longitude degrees is missing corresponding latitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_utm_before_insert BEFORE INSERT ON GPSLocations
BEGIN
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTMZone IS NULL THEN
            RAISE (ABORT,'UTM coordinates with missing zone')
        END;
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTME IS NULL THEN
            RAISE (ABORT,'UTM northing missing corresponding easting')
        END;
    SELECT CASE
        WHEN NEW.UTME IS NOT NULL AND NEW.UTMN IS NULL THEN
            RAISE (ABORT,'UTM easting missing corresponding northing')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format originally provided.')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_utm_before_update BEFORE UPDATE ON GPSLocations
BEGIN
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTMZone IS NULL THEN
            RAISE (ABORT,'UTM coordinates with missing zone')
        END;
    SELECT CASE
        WHEN NEW.UTMN IS NOT NULL AND NEW.UTME IS NULL THEN
            RAISE (ABORT,'UTM northing missing corresponding easting')
        END;
    SELECT CASE
        WHEN NEW.UTME IS NOT NULL AND NEW.UTMN IS NULL THEN
            RAISE (ABORT,'UTM easting missing corresponding northing')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_hd_units_before_insert BEFORE INSERT ON GPSLocations
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnitID IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_hd_units_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
    SELECT CASE
        WHEN HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_elev_units_before_insert BEFORE INSERT ON GPSLocations
BEGIN
    SELECT CASE
        WHEN NEW.Elev IS NOT NULL AND NEW.ElevUnitID IS NULL THEN
            RAISE (ABORT,'Elevation value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_elev_units_before_update BEFORE UPDATE ON GPSLocations
BEGIN
    SELECT CASE
        WHEN NEW.Elev IS NOT NULL AND NEW.ElevUnit IS NULL THEN
            RAISE (ABORT,'Elevation value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_latlon_deg_before_insert BEFORE INSERT ON GPSLocations
BEGIN
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.LonDeg IS NULL THEN
            RAISE (ABORT,'Latitude degrees is missing corresponding longitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LonDeg IS NOT NULL AND NEW.LatDeg IS NULL THEN
            RAISE (ABORT,'Longitude degrees is missing corresponding latitude degrees')
        END;
    SELECT CASE
        WHEN NEW.LatDeg IS NOT NULL AND NEW.UTMN IS NOT NULL THEN
            RAISE (ABORT, 'Coordinates already exist. Coordinates should be entered in the format orignially provided.')
        END;
END;
'''
CREATE_COLUMN_TRIGGERS = '''
CREATE TRIGGER IF NOT EXISTS validate_column_units_before_insert BEFORE INSERT ON Columns
BEGIN
    SELECT CASE
        WHEN NEW.ColumnTotalHeightDepth IS NOT NULL AND NEW.ColumnTotalHeightDepthUnitID IS NULL THEN
            RAISE (ABORT,'Column total height/depth value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_column_units_before_update BEFORE UPDATE ON Columns
BEGIN
    SELECT CASE
        WHEN NEW.ColumnTotalHeightDepth IS NOT NULL AND NEW.ColumnTotalHeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Column total height/depth value with missing units')
        END;
    SELECT CASE
        WHEN ColumnTotalHeightDepth IS NOT NULL AND NEW.ColumnTotalHeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Column total height/depth value with missing units')
            END;
    SELECT CASE
        WHEN NEW.ColumnTotalHeightDepth IS NOT NULL AND ColumnTotalHeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Column total height/depth value with missing units')
        END;
END;
'''
CREATE_SAMPLES_TRIGGERS = '''
CREATE TRIGGER IF NOT EXISTS validate_sample_heightdepth_before_insert BEFORE INSERT ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnitID IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.ColumnID IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing column')
        END 
END;
CREATE TRIGGER IF NOT EXISTS validate_sample_heightdepth_before_update BEFORE UPDATE ON Samples
BEGIN
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
    SELECT CASE
        WHEN HeightDepth IS NOT NULL AND NEW.HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND HeightDepthUnit IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing units')
        END;
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND NEW.ColumnID IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing column')
        END;
    SELECT CASE
        WHEN HeightDepth IS NOT NULL AND NEW.ColumnID IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing column')
        END;
    SELECT CASE
        WHEN NEW.HeightDepth IS NOT NULL AND ColumnID IS NULL THEN
            RAISE (ABORT,'Height/depth value with missing column')
        END;
END;
'''
CREATE_SPOTSIZE_TRIGGERS = '''
CREATE TRIGGER IF NOT EXISTS validate_spot_units_before_insert BEFORE INSERT ON UPbAnalyses
BEGIN
    SELECT CASE
        WHEN NEW.SpotSize IS NOT NULL AND NEW.SpotSizeUnitID IS NULL THEN
            RAISE (ABORT,'Spot size value with missing units')
        END;
END;
CREATE TRIGGER IF NOT EXISTS validate_spot_units_before_update BEFORE UPDATE ON UPbAnalyses
BEGIN
    SELECT CASE
        WHEN NEW.SpotSize IS NOT NULL AND NEW.SpotSizeUnit IS NULL THEN
            RAISE (ABORT,'Spot size value with missing units')
        END;
END;
'''
# Triggers to update the modified timestamp when a value is updated
SOURCES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_sources AFTER UPDATE ON Sources
BEGIN
    UPDATE Sources SET SourceModified = CURRENT_TIMESTAMP WHERE SourceID = NEW.SourceID OR Authors = NEW.Authors OR Year = NEW.Year OR Title = NEW.Title OR Source = NEW.Source OR doi = NEW.doi OR ShortCitation = NEW.ShortCitation;
END;'''
SAMPLINGMETHODS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samplingmethods AFTER UPDATE ON SamplingMethods
BEGIN
    UPDATE SamplingMethods SET SamplingMethodModified = CURRENT_TIMESTAMP WHERE SamplingMethodID = NEW.SamplingMethodID OR ParentSamplingMethodID = NEW.ParentSamplingMethodID OR SamplingMethodName = NEW.SamplingMethodName OR SamplingMethodDescription = NEW.SamplingMethodDescription;
END;'''
REGIONS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_regions AFTER UPDATE ON Regions
BEGIN
    UPDATE Regions SET RegionModified = CURRENT_TIMESTAMP WHERE RegionID = NEW.RegionID OR ParentRegionID = NEW.ParentRegionID OR RegionName = NEW.RegionName OR RegionDescription = NEW.RegionDescription;
END;'''
SETTINGS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_settings AFTER UPDATE ON Settings
BEGIN
    UPDATE Settings SET SettingModified = CURRENT_TIMESTAMP WHERE SettingID = NEW.SettingID OR ParentSettingID = NEW.ParentSettingID OR SettingName = NEW.SettingName OR SettingDescription = NEW.SettingDescription;
END;'''
ROCKTYPES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_rocktypes AFTER UPDATE ON RockTypes
BEGIN
    UPDATE RockTypes SET RockTypeModified = CURRENT_TIMESTAMP WHERE RockTypeID = NEW.RockTypeID OR ParentRockTypeID = NEW.ParentRockTypeID OR RockTypeName = NEW.RockTypeName OR RockTypeDescription = NEW.RockTypeDescription;
END;'''
UNITS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_units AFTER UPDATE ON Units
BEGIN
    UPDATE Units SET UnitModified = CURRENT_TIMESTAMP WHERE UnitID = NEW.UnitID OR ParentUnitID = NEW.ParentUnitID OR UnitName = NEW.UnitName OR UnitDescription = NEW.UnitDescription;
END;'''
COLUMNS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_columns AFTER UPDATE ON Columns
BEGIN
    UPDATE Columns SET ColumnModified = CURRENT_TIMESTAMP WHERE ColumnID = NEW.ColumnID OR ColumnName = NEW.ColumnName OR ColumnDescription = NEW.ColumnDescription;
END;'''
AGESIGNATURES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_agesignatures AFTER UPDATE ON AgeSignatures
BEGIN
    UPDATE AgeSignatures SET AgeSignatureModified = CURRENT_TIMESTAMP WHERE AgeSignatureID = NEW.AgeSignatureID OR ParentAgeSignatureID = NEW.ParentAgeSignatureID OR AgeSignatureName = NEW.AgeSignatureName OR AgeSignatureDescription = NEW.AgeSignatureDescription;
END;'''
AGES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_ages AFTER UPDATE ON Ages
BEGIN
    UPDATE Ages SET AgeModified = CURRENT_TIMESTAMP WHERE AgeID = NEW.AgeID OR ParentAgeID = NEW.ParentAgeID OR AgeName = NEW.AgeName OR MaxMa = NEW.MaxMa OR MinMa = NEW.MinMa;
END;'''
SAMPLECONTEXT_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samplecontexts AFTER UPDATE ON SampleContexts
BEGIN
    UPDATE SampleContexts SET SampleContextModified = CURRENT_TIMESTAMP WHERE SampleContextID = NEW.SampleContextID OR ParentSampleContextID = NEW.ParentSampleContextID OR SampleContextName = NEW.SampleContextName OR SampleContextDescription = NEW.SampleContextDescription;
END;'''
ALIQUOTCONTEXT_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_aliquotcontexts AFTER UPDATE ON AliquotContexts
BEGIN
    UPDATE AliquotContexts SET AliquotContextModified = CURRENT_TIMESTAMP WHERE AliquotContextID = NEW.AliquotContextID OR ParentAliquotContextID = NEW.ParentAliquotContextID OR AliquotContextName = NEW.AliquotContextName OR AliquotContextDescription = NEW.AliquotContextDescription;
END;'''
SPOTCONTEXT_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_spotcontexts AFTER UPDATE ON SpotContexts
BEGIN
    UPDATE SpotContexts SET SpotContextModified = CURRENT_TIMESTAMP WHERE SpotContextID = NEW.SpotContextID OR ParentSpotContextID = NEW.ParentSpotContextID OR SpotContextName = NEW.SpotContextName OR SpotContextDescription = NEW.SpotContextDescription;
END;'''
SPOTCOMPOSITIONS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_spotcompositions AFTER UPDATE ON SpotCompositions
BEGIN
    UPDATE SpotCompositions SET SpotCompositionModified = CURRENT_TIMESTAMP WHERE SpotCompositionID = NEW.SpotCompositionID OR ParentSpotCompositionID = NEW.ParentSpotCompositionID OR SpotCompositionName = NEW.SpotCompositionName OR SpotCompositionDescription = NEW.SpotCompositionDescription;
END;'''
SAMPLES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples AFTER UPDATE ON Samples
BEGIN
    UPDATE Samples SET SampleModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR SampleName = NEW.SampleName OR AverageAge = NEW.AverageAge OR AverageAgeError = NEW.AverageAgeError OR ErrorSigma = NEW.ErrorSigma OR OldestAge = NEW.OldestAge OR YoungestAge = NEW.YoungestAge OR OldestAgeID = NEW.OldestAgeID OR YoungestAgeID = NEW.YoungestAgeID OR HeightDepth = NEW.HeightDepth OR HeightDepthError = NEW.HeightDepthError OR HeightDepthUnit = NEW.HeightDepthUnit OR LatDeg = NEW.LatDeg OR LatMin = NEW.LatMin OR LatSec = NEW.LatSec OR LonDeg = NEW.LonDeg OR LonMin = NEW.LonMin OR LonSec = NEW.LonSec OR UTMZone = NEW.UTMZone OR UTMN = NEW.UTMN OR UTME = NEW.UTME OR Elev = NEW.Elev OR ElevError = NEW.ElevError OR ElevUnit = NEW.ElevUnit OR Description = NEW.Description;
END;'''
ALIQUOTS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_aliquots AFTER UPDATE ON Aliquots
BEGIN
    UPDATE Aliquots SET AliquotModified = CURRENT_TIMESTAMP WHERE AliquotID = NEW.AliquotID OR AliquotName = NEW.AliquotName OR SampleID = NEW.SampleID;
END;'''
SPOTS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_spots AFTER UPDATE ON Spots
BEGIN
    UPDATE Spots SET SpotModified = CURRENT_TIMESTAMP WHERE SpotID = NEW.SpotID OR SpotName = NEW.SpotName OR AliquotID = NEW.AliquotID OR SpotCompositionID = NEW.SpotCompositionID;
END;'''
LABFACILITIES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_labfacilities AFTER UPDATE ON LabFacilities
BEGIN
    UPDATE LabFacilities SET LabFacilityModified = CURRENT_TIMESTAMP WHERE LabFacilityID = NEW.LabFacilityID OR LabFacilityName = NEW.LabFacilityName OR LabFacilityDescription = NEW.LabFacilityDescription;
END;'''
INSTRUMENTS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_instruments AFTER UPDATE ON Instruments
BEGIN
    UPDATE Instruments SET InstrumentModified = CURRENT_TIMESTAMP WHERE InstrumentID = NEW.InstrumentID OR InstrumentName = NEW.InstrumentName OR InstrumentDescription = NEW.InstrumentDescription;
END;'''
UPBANALYSISMETHODS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_upbanalysismethods AFTER UPDATE ON UPbAnalysisMethods
BEGIN
    UPDATE UPbAnalysisMethods SET UPbAnalysisMethodModified = CURRENT_TIMESTAMP WHERE UPbAnalysisMethodID = NEW.UPbAnalysisMethodID OR UPbAnalysisMethodName = NEW.UPbAnalysisMethodName OR UPbAnalysisMethodDescription = NEW.UPbAnalysisMethodDescription;
END;'''
UPBANALYSES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_upbdata AFTER UPDATE ON UPbData
BEGIN
    UPDATE UPbData SET UPbAnalysisModified = CURRENT_TIMESTAMP WHERE UPbAnalysisID = NEW.UPbAnalysisID OR SpotID = NEW.SpotID OR SourceID = NEW.SourceID OR LabFacilityID = NEW.LabFacilityID OR InstrumentID = NEW.InstrumentID OR UPbAnalysisMethodID = NEW.UPbAnalysisMethodID OR Uppm = NEW.Uppm OR "206Pb/204Pb" = NEW."206Pb/204Pb" OR "U/Th" = NEW."U/Th" OR "206Pb/207Pb" = NEW."206Pb/207Pb" OR "206Pb/207Pberror" = NEW."206Pb/207Pberror" OR "207Pb/235U" = NEW."207Pb/235U" OR "207Pb/235Uerror" = NEW."207Pb/235Uerror" OR "206Pb/238U" = NEW."206Pb/238U" OR "206Pb/238Uerror" = NEW."206Pb/238Uerror" OR ErrorCorr = NEW.ErrorCorr OR "206Pb/207PbAge" = NEW."206Pb/207PbAge" OR "206Pb/207PbAgeError" = NEW."206Pb/207PbAgeError" OR "207Pb/235UAge" = NEW."207Pb/235UAge" OR "207Pb/235UAgeError" = NEW."207Pb/235UAgeError" OR "206Pb/238UAge" = NEW."206Pb/238UAge" OR "206Pb/238UAgeError" = NEW."206Pb/238UAgeError" OR BestAge = NEW.BestAge OR Error = NEW.Error OR Conc = NEW.Conc OR SpotSize = NEW.SpotSize OR SpotSizeUnit = NEW.SpotSizeUnit OR Accepted = NEW.Accepted;
END;'''
SAMPLES_AGESIGNATURES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_agesignatures AFTER UPDATE ON Samples_AgeSignatures
BEGIN
    UPDATE Samples_AgeSignatures SET Samples_AgeSignaturesModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR AgeSignatureID = NEW.AgeSignatureID;
END;'''
SAMPLES_COLUMNS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_columns AFTER UPDATE ON Samples_Columns
BEGIN
    UPDATE Samples_Columns SET Samples_ColumnsModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR ColumnID = NEW.ColumnID;
END;'''
SAMPLES_REGIONS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_regions AFTER UPDATE ON Samples_Regions
BEGIN
    UPDATE Samples_Regions SET Samples_RegionsModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR RegionID = NEW.RegionID;
END;'''
SAMPLES_ROCKTYPES_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_rocktypes AFTER UPDATE ON Samples_RockTypes
BEGIN
    UPDATE Samples_RockTypes SET Samples_RockTypesModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR RockTypeID = NEW.RockTypeID;
END;'''
SAMPLES_SAMPLECONTEXT_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_samplecontexts AFTER UPDATE ON Samples_SampleContexts
BEGIN
    UPDATE Samples_SampleContext SET Samples_SampleContextModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR SampleContextID = NEW.SampleContextID;
END;'''
SAMPLES_SAMPLINGMETHODS_MODIFIED_RIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_samplingmethods AFTER UPDATE ON Samples_SamplingMethods
BEGIN
    UPDATE Samples_SamplingMethods SET Samples_SamplingMethodsModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR SamplingMethodID = NEW.SamplingMethodID;
END;'''
SAMPLES_SETTINGS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_settings AFTER UPDATE ON Samples_Settings
BEGIN
    UPDATE Samples_Settings SET Samples_SettingsModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR SettingID = NEW.SettingID;
END;'''
SAMPLES_UNITS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_samples_units AFTER UPDATE ON Samples_Units
BEGIN
    UPDATE Samples_Units SET Samples_UnitsModified = CURRENT_TIMESTAMP WHERE SampleID = NEW.SampleID OR UnitID = NEW.UnitID;
END;'''
ALIQUOTS_ALIQUOTCONTEXT_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_aliquots_aliquotcontexts AFTER UPDATE ON Aliquots_AliquotContexts
BEGIN
    UPDATE Aliquots_AliquotContexts SET Aliquots_AliquotContextModified = CURRENT_TIMESTAMP WHERE AliquotID = NEW.AliquotID OR AliquotContextID = NEW.AliquotContextID;
END;'''
SPOTS_SPOTCONTEXT_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_spots_spotcontexts AFTER UPDATE ON Spots_SpotContexts
BEGIN
    UPDATE Spots_SpotContexts SET Spots_SpotContextModified = CURRENT_TIMESTAMP WHERE SpotID = NEW.SpotID OR SpotContextID = NEW.SpotContextID;
END;'''
FILTERGROUPS_MODIFIED_TRIGGER = '''
CREATE TRIGGER IF NOT EXISTS update_modified_filtergroups AFTER UPDATE ON FilterGroups
BEGIN
    UPDATE FilterGroups SET FilterGroupModified = CURRENT_TIMESTAMP WHERE FilterGroupID = NEW.FilterGroupID OR FilterGroupName = NEW.FilterGroupName OR SQLQuery = NEW.SQLQuery OR DefaultColor = NEW.DefaultColor OR FilterGroupDescription = NEW.FilterGroupDescription;
END;'''

def create_triggers(c):
    """
    Take database cursor and execute the sql strings defined above to create the database triggers
    :param c: Cursor of database connection
    """
    c.execute(INSERT_HD_TRIGGER)
    c.execute(INSERT_ELEV_TRIGGER)
    c.execute(INSERT_SPOT_TRIGGER)
    c.execute(INSERT_LATLON_TRIGGER)
    c.execute(INSERT_UTM_TRIGGER)
    c.execute(UPDATE_HD_TRIGGER)
    c.execute(UPDATE_ELEV_TRIGGER)
    c.execute(UPDATE_SPOT_TRIGGER)
    c.execute(UPDATE_LATLON_TRIGGER)
    c.execute(UPDATE_UTM_TRIGGER)
    c.execute(SOURCES_TRIGGER)
    c.execute(SAMPLINGMETHODS_TRIGGER)
    c.execute(REGIONS_TRIGGER)
    c.execute(SETTINGS_TRIGGER)
    c.execute(ROCKTYPES_TRIGGER)
    c.execute(UNITS_TRIGGER)
    c.execute(COLUMNS_TRIGGER)
    c.execute(AGESIGNATURES_TRIGGER)
    c.execute(AGES_TRIGGER)
    c.execute(SAMPLECONTEXT_TRIGGER)
    c.execute(ALIQUOTCONTEXT_TRIGGER)
    c.execute(SPOTCONTEXT_TRIGGER)
    c.execute(SPOTCOMPOSITIONS_TRIGGER)
    c.execute(SAMPLES_TRIGGER)
    c.execute(ALIQUOTS_TRIGGER)
    c.execute(SPOTS_TRIGGER)
    c.execute(LABFACILITIES_TRIGGER)
    c.execute(INSTRUMENTS_TRIGGER)
    c.execute(UPBANALYSISMETHODS_TRIGGER)
    c.execute(UPBDATA_TRIGGER)
    c.execute(GEOCHEMDATA_TRIGGER)
    c.execute(SAMPLES_AGESIGNATURES_TRIGGER)
    c.execute(SAMPLES_COLUMNS_TRIGGER)
    c.execute(SAMPLES_REGIONS_TRIGGER)
    c.execute(SAMPLES_ROCKTYPES_TRIGGER)
    c.execute(SAMPLES_SAMPLECONTEXT_TRIGGER)
    c.execute(SAMPLES_SAMPLINGMETHODS_TRIGGER)
    c.execute(SAMPLES_SETTINGS_TRIGGER)
    c.execute(SAMPLES_UNITS_TRIGGER)
    c.execute(ALIQUOTS_ALIQUOTCONTEXT_TRIGGER)
    c.execute(SPOTS_SPOTCONTEXT_TRIGGER)
    c.execute(FILTERGROUPS_TRIGGER)


if __name__ == '__main__':
    db_file = '../DataTestSchema.db'
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        create_triggers(db_file)