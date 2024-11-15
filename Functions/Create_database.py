import sqlite3
import xml.etree.ElementTree as ET  # xml reader
import Functions.Create_triggers as CT # triggers
import Functions.DB_views as DBV # views

'''Commands to create the database
Foreign keys are set to cascade on update
When a foreign key is deleted, most will be set to null
The only exception is the AliquotID in the Spots table, which will cascade on delete
Names must be unique and are checked for case sensitivity'''
# look under linking aboutmodified to other tables
'''SQL strings to create each table'''

# todo: implement changes for database schema
# create table for DistanceUnits and conversions
# create table for DirectionUnits and conversions
# create table for AgeUnits and conversions
# create table for ErrorTypes and conversions
# create table for ConcordanceTypes and conversions
# create table for AgeInterpretations
# create table for RejectionRegion
# make aliquots table a tree
# expand columns in UPbData table and rename to UPbAnalyses
# add IGSN to samples table


CREATE_ABOUT_TABLE = '''CREATE TABLE IF NOT EXISTS About(
                    AboutID INTEGER PRIMARY KEY,
                    Name TEXT NOT NULL CHECK (Name <> ''),
                    Authors TEXT NOT NULL CHECK (Authors <> ''),
                    Citation TEXT NOT NULL CHECK (Citation <> ''),
                    SourceLink TEXT NOT NULL CHECK (SourceLink <> ''),
                    Version TEXT NOT NULL CHECK (Version <> ''),
                    Description TEXT,
                    CreatedBy TEXT NOT NULL CHECK (CreatedBy <> ''),
                    AboutCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AboutModified DATETIME DEFAULT CURRENT_TIMESTAMP
                    )'''

CREATE_AGE_CONSTRAINTS_TABLE = '''CREATE TABLE IF NOT EXISTS AgeConstraints(
                    AgeConstraintID INTEGER PRIMARY KEY,
                    ParentAgeConstraintID INTEGER,
                    AgeConstraintParentRow INTEGER,
                    AgeConstraintName TEXT NOT NULL CHECK (AgeConstraintName <> ''),
                    AgeConstraintDescription TEXT,
                    AgeConstraintCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AgeConstraintModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AgeConstraintName COLLATE NOCASE),
                    UNIQUE (ParentAgeConstraintID, AgeConstraintParentRow)
                    )'''

CREATE_AGE_INTERPRETATIONS_TABLE = '''CREATE TABLE IF NOT EXISTS AgeInterpretations(
                    AgeInterpretationID INTEGER PRIMARY KEY,
                    ParentAgeInterpretationID INTEGER,
                    AgeInterpretationParentRow INTEGER,
                    AgeInterpretationName TEXT NOT NULL CHECK (AgeInterpretationName <> ''),
                    AgeInterpretationDescription TEXT,
                    AgeInterpretationCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AgeInterpretationModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AgeInterpretationName COLLATE NOCASE),
                    UNIQUE (ParentAgeInterpretationID, AgeInterpretationParentRow)
                    )'''

CREATE_AGE_SIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS AgeSignatures(
                    AgeSignatureID INTEGER PRIMARY KEY,
                    ParentAgeSignatureID INTEGER,
                    AgeSignatureParentRow INTEGER,
                    AgeSignatureName TEXT NOT NULL CHECK (AgeSignatureName <> ''),
                    AgeSignatureDescription TEXT,
                    AgeSignatureCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AgeSignatureModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AgeSignatureName COLLATE NOCASE),
                    UNIQUE (ParentAgeSignatureID, AgeSignatureParentRow)
                    )'''

CREATE_AGE_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS AgeUnits(
                    AgeUnitID INTEGER PRIMARY KEY,
                    AgeUnitName TEXT NOT NULL CHECK(AgeUnitName <> ''),
                    AgeUnitAbbreviation TEXT NOT NULL CHECK(AgeUnitAbbreviation <> ''),
                    AgeUnitDescription TEXT, 
                    AgeUnitCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AgeUnitModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(AgeUnitName COLLATE NOCASE),
                    UNIQUE(AgeUnitAbbreviation COLLATE NOCASE)
                    )'''

CREATE_AGE_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS AgeConversions(
                    FromAgeUnitID INTEGER,
                    ToAgeUnitID INTEGER,
                    AgeConversionCalculation TEXT NOT NULL CHECK(AgeConversionCalculation <> ''), 
                    AgeConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AgeConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    UNIQUE (FromAgeUnitID, ToAgeUnitID),
                    FOREIGN KEY(FromAgeUnitID) REFERENCES AgeUnits(AgeUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToAgeUnitID) REFERENCES AgeUnits(AgeUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_AGES_TABLE = '''CREATE TABLE IF NOT EXISTS Ages(
                    AgeID INTEGER PRIMARY KEY,
                    ParentAgeID INTEGER,
                    AgeParentRow INTEGER,
                    AgeName TEXT NOT NULL CHECK (AgeName <> ''),
                    MaxMa REAL,
                    MinMa REAL,
                    AgeCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AgeModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    UNIQUE (AgeName COLLATE NOCASE),
                    UNIQUE (ParentAgeID, AgeParentRow)
                    )'''

CREATE_ALIQUOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS AliquotContexts(
                    AliquotContextID INTEGER PRIMARY KEY,
                    ParentAliquotContextID INTEGER,
                    AliquotContextParentRow INTEGER,
                    AliquotContextName TEXT NOT NULL CHECK (AliquotContextName <> ''),
                    AliquotContextDescription TEXT,
                    AliquotContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AliquotContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AliquotContextName COLLATE NOCASE),
                    UNIQUE (ParentAliquotContextID, AliquotContextParentRow)
                    )'''

CREATE_ALIQUOTS_TABLE = '''CREATE TABLE IF NOT EXISTS Aliquots(
                    AliquotID INTEGER PRIMARY KEY, 
                    ParentAliquotID INTEGER,
                    AliquotParentRow INTEGER,
                    AliquotName TEXT NOT NULL CHECK (AliquotName <> ''),
                    SampleID INTEGER,
                    AliquotCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AliquotModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AliquotName COLLATE NOCASE), 
                    UNIQUE (ParentAliquotID, AliquotParentRow),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Aliquots_AliquotContexts(
                    AliquotID INTEGER,
                    AliquotContextID INTEGER,
                    Aliquots_AliquotContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Aliquots_AliquotContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AliquotID, AliquotContextID),
                    FOREIGN KEY(AliquotID) REFERENCES Aliquots(AliquotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AliquotContextID) REFERENCES AliquotContexts(AliquotContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ANALYSIS_INTERPRETATIONS_TABLE = '''CREATE TABLE IF NOT EXISTS AnalysisInterpretations(
                    AnalysisInterpretationID INTEGER PRIMARY KEY,
                    ParentAnalysisInterpretationID INTEGER,
                    AnalysisInterpretationParentRow INTEGER,
                    AnalysisInterpretationName TEXT NOT NULL CHECK (AnalysisInterpretationName <> ''),
                    AnalysisInterpretationDescription TEXT,
                    AnalysisInterpretationCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AnalysisInterpretationModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AnalysisInterpretationName COLLATE NOCASE),
                    UNIQUE (ParentAnalysisInterpretationID, AnalysisInterpretationParentRow)
                    )'''

CREATE_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Columns(
                    ColumnID INTEGER PRIMARY KEY,
                    ColumnName TEXT NOT NULL CHECK (ColumnName <> ''), 
                    ColumnTotalHeightDepth REAL, 
                    ColumnTotalHeightDepthUnitID INTEGER, 
                    ColumnBaseGPSID INTEGER,
                    ColumnDescription TEXT, 
                    ColumnCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ColumnModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (ColumnName COLLATE NOCASE)
                    )'''

CREATE_CONCORDANCE_TYPES_TABLE = '''CREATE TABLE IF NOT EXISTS ConcordanceTypes(
                    ConcordanceTypeID INTEGER PRIMARY KEY,
                    ConcordanceTypeName TEXT NOT NULL CHECK(ConcordanceTypeName <> ''),
                    ConcordanceTypeAbbreviation TEXT NOT NULL CHECK(ConcordanceTypeAbbreviation <> ''),
                    ConcordanceTypeDescription TEXT,
                    ConcordanceTypeCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ConcordanceTypeModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ConcordanceTypeName COLLATE NOCASE),
                    UNIQUE(ConcordanceTypeAbbreviation COLLATE NOCASE)
)'''

CREATE_CONCORDANCE_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS ConcordanceConversions(
                    FromConcordanceTypeID INTEGER,
                    ToConcordanceTypeID INTEGER,
                    ConcordanceConversionCalculation TEXT NOT NULL CHECK(ConcordanceConversionCalculation <> ''), 
                    ConcordanceConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ConcordanceConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    UNIQUE (FromConcordanceTypeID, ToConcordanceTypeID),
                    FOREIGN KEY(FromConcordanceTypeID) REFERENCES ConcordanceTypes(ConcordanceTypeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToConcordanceTypeID) REFERENCES ConcordanceTypes(ConcordanceTypeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_DIRECTION_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS DirectionUnits(
                    DirectionUnitID INTEGER PRIMARY KEY,
                    DirectionUnitName TEXT NOT NULL CHECK(DirectionUnitName <> ''),
                    DirectionUnitAbbreviation TEXT NOT NULL CHECK(DirectionUnitAbbreviation <> ''),
                    DirectionUnitCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    DirectionUnitModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(DirectionUnitName COLLATE NOCASE)
)'''

CREATE_DIRECTION_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS DirectionConversions(
                    FromDirectionUnitID INTEGER,
                    ToDirectionUnitID INTEGER,
                    DirectionConversionCalculation TEXT, 
                    DirectionConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    DirectionConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    FOREIGN KEY(FromDirectionUnitID) REFERENCES DirectionUnits(DirectionUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToDirectionUnitID) REFERENCES DirectionUnits(DirectionUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_DISTANCE_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS DistanceUnits(
                    DistanceUnitID INTEGER PRIMARY KEY,
                    DistanceUnitName TEXT NOT NULL CHECK(DistanceUnitName <> ''),
                    DistanceUnitAbbreviation TEXT NOT NULL CHECK(DistanceUnitAbbreviation <> ''),
                    DistanceUnitDescription TEXT,
                    DistanceUnitCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    DistanceUnitModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(DistanceUnitName COLLATE NOCASE),
                    UNIQUE(DistanceUnitAbbreviation COLLATE NOCASE)
)'''

CREATE_DISTANCE_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS DistanceConversions(
                    FromDistanceUnitID INTEGER,
                    ToDistanceUnitID INTEGER,
                    DistanceConversionCalculation TEXT, 
                    DistanceConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    DistanceConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    FOREIGN KEY(FromDistanceUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToDistanceUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ERROR_TYPES_TABLE = '''CREATE TABLE IF NOT EXISTS ErrorTypes(
                    ErrorTypeID INTEGER PRIMARY KEY,
                    ErrorTypeName TEXT NOT NULL CHECK(ErrorTypeName <> ''),
                    ErrorTypeAbbreviation TEXT NOT NULL CHECK(ErrorTypeAbbreviation <> ''),
                    ErrorTypeDescription TEXT,
                    ErrorTypeCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ErrorTypeModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ErrorTypeName COLLATE NOCASE),
                    UNIQUE(ErrorTypeAbbreviation COLLATE NOCASE)
)'''

CREATE_ERROR_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS ErrorConversions(
                    FromErrorTypeID INTEGER,
                    ToErrorTypeID INTEGER,
                    ErrorConversionCalculation TEXT, 
                    ErrorConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ErrorConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    FOREIGN KEY(FromErrorTypeID) REFERENCES ErrorTypes(ErrorTypeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToErrorTypeID) REFERENCES ErrorTypes(ErrorTypeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_GPS_LOCATIONS_TABLE = '''CREATE TABLE IF NOT EXISTS GPSLocations(
                    GPSLocationID INTEGER PRIMARY KEY,
                    GPSLatDeg REAL,
                    GPSLatMin REAL,
                    GPSLatSec REAL,
                    GPSLatDirectionID INTEGER,
                    GPSLonDeg REAL,
                    GPSLonMin REAL,
                    GPSLonSec REAL,
                    GPSLonDirectionID INTEGER,
                    GPSUTMZone TEXT,
                    GPSUTMN REAL,
                    GPSUTME REAL,
                    Elev REAL,
                    ElevError REAL,
                    ElevUnitID INTEGER,
                    GPSLocationCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GPSLocationModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, Elev, ElevError, ElevUnitID)
)'''

CREATE_FILTER_GROUPS_TABLE = '''CREATE TABLE IF NOT EXISTS FilterGroups(
                    FilterGroupID INTEGER PRIMARY KEY,
                    FilterGroupName TEXT NOT NULL CHECK (FilterGroupName <> ''),
                    SQLQuery TEXT,
                    DefaultColor TEXT,
                    FilterGroupDescription TEXT,
                    FilterGroupCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FilterGroupModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (FilterGroupName COLLATE NOCASE)
                    )'''

CREATE_INSTRUMENTS_TABLE = '''CREATE TABLE IF NOT EXISTS Instruments(
                    InstrumentID INTEGER PRIMARY KEY,
                    InstrumentName TEXT NOT NULL CHECK (InstrumentName <> ''),
                    InstrumentDescription TEXT, 
                    InstrumentCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    InstrumentModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (InstrumentName COLLATE NOCASE)
                    )'''

CREATE_LAB_FACILITIES_TABLE = '''CREATE TABLE IF NOT EXISTS LabFacilities(
                    LabFacilityID INTEGER PRIMARY KEY,
                    LabFacilityName TEXT NOT NULL CHECK (LabFacilityName <> ''),
                    LabFacilityDescription TEXT,
                    LabFacilityCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    LabFacilityModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (LabFacilityName COLLATE NOCASE)
                    )'''

CREATE_REGIONS_TABLE = '''CREATE TABLE IF NOT EXISTS Regions(
                    RegionID INTEGER PRIMARY KEY,
                    ParentRegionID INTEGER,
                    RegionParentRow INTEGER,
                    RegionName TEXT NOT NULL CHECK (RegionName <> ''),
                    RegionDescription TEXT,
                    RegionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    RegionModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (RegionName COLLATE NOCASE),
                    UNIQUE (ParentRegionID, RegionParentRow)
                    )'''

CREATE_ROCK_TYPES_TABLE = '''CREATE TABLE IF NOT EXISTS RockTypes(
                    RockTypeID INTEGER PRIMARY KEY,
                    ParentRockTypeID INTEGER,
                    RockTypeParentRow INTEGER,
                    RockTypeName TEXT NOT NULL CHECK (RockTypeName <> ''),
                    RockTypeDescription TEXT,
                    RockTypeCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    RockTypeModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (RockTypeName COLLATE NOCASE),
                    UNIQUE (ParentRockTypeID, RockTypeParentRow)
                    )'''

CREATE_SAMPLE_AGE_TABLE = '''CREATE TABLE IF NOT EXISTS SampleAges(
                    SampleAgeID INTEGER PRIMARY KEY, 
                    AverageAge REAL,
                    AverageAgeError REAL,
                    AverageAgeErrorTypeID INTEGER,
                    OldestAge REAL,
                    YoungestAge REAL, 
                    SampleAgeUnitID INTEGER,
                    OldestAgeID INTEGER,
                    YoungestAgeID INTEGER,
                    SampleAgeDescription TEXT, 
                    SampleAgeCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SampleAgeModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AverageAge, AverageAgeError, AverageAgeErrorTypeID, OldestAge, YoungestAge, SampleAgeUnitID, OldestAgeID, YoungestAgeID),
                    FOREIGN KEY(AverageAgeErrorTypeID) REFERENCES ErrorTypes(ErrorTypeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(SampleAgeUnitID) REFERENCES AgeUnits(AgeUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(OldestAgeID) REFERENCES Ages(AgeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(YoungestAgeID) REFERENCES Ages(AgeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SAMPLE_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS SampleContexts(
                    SampleContextID INTEGER PRIMARY KEY,
                    ParentSampleContextID INTEGER,
                    SampleContextParentRow INTEGER NOT NULL,
                    SampleContextName TEXT NOT NULL CHECK (SampleContextName <> ''), 
                    SampleContextDescription TEXT,
                    SampleContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SampleContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleContextName COLLATE NOCASE),
                    UNIQUE (ParentSampleContextID, SampleContextParentRow)
                    )'''

CREATE_SAMPLEAGES_AGECONSTRAINTS_TABLE = '''CREATE TABLE IF NOT EXISTS SamplesAges_AgeConstraints(
                    SampleAgeID INTEGER,
                    AgeConstraintID INTEGER,
                    SamplesAges_AgeConstraintsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SamplesAges_AgeConstraintsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AgeConstraintID) REFERENCES AgeConstraints(AgeConstraintsID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLEAGES_AGEINTERPRETATIONS_TABLE = '''CREATE TABLE IF NOT EXISTS SamplesAges_AgeInterpretations(
                    SampleAgeID INTEGER,
                    AgeInterpretationID INTEGER,
                    SamplesAges_AgeInterpretationsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SamplesAges_AgeInterpretationsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AgeInterpretationID) REFERENCES AgeInterpretations(AgeInterpretationID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples(
                    SampleID INTEGER PRIMARY KEY,
                    SampleName TEXT NOT NULL CHECK (SampleName <> ''), 
                    SampleIGSN TEXT, 
                    SampleAgeID INTEGER,
                    SampleGPSLocationID INTEGER,
                    SampleColumnID INTEGER,
                    HeightDepth REAL,
                    HeightDepthError REAL,
                    HeightDepthUnitID INTEGER,
                    Description TEXT,
                    SampleCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SampleModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleName COLLATE NOCASE), 
                    FOREIGN KEY(SampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(SampleGPSLocationID) REFERENCES GPLocations(GPSLocationID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(SampleColumnID) REFERENCES Columns(ColumnID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(HeightDepthUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SAMPLES_AGESIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_AgeSignatures(
                    SampleID INTEGER,
                    AgeSignatureID INTEGER,
                    Samples_AgeSignaturesCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_AgeSignaturesModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AgeSignatureID) REFERENCES AgeSignatures(AgeSignatureID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_REGIONS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Regions(
                    SampleID INTEGER,
                    RegionID INTEGER,
                    Samples_RegionsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_RegionsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(RegionID) REFERENCES Regions(RegionID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_ROCKTYPES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_RockTypes(
                    SampleID INTEGER,
                    RockTypeID INTEGER,
                    Samples_RockTypesCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_RockTypesModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(RockTypeID) REFERENCES RockTypes(RockTypeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLECONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_SampleContexts(
                    SampleID INTEGER,
                    SampleContextID INTEGER,
                    Samples_SampleContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_SampleContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SampleContextID) REFERENCES SampleContexts(SampleContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLINGMETHODS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_SamplingMethods(
                    SampleID INTEGER,
                    SamplingMethodID INTEGER,
                    Samples_SamplingMethodsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_SamplingMethodsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SamplingMethodID) REFERENCES SamplingMethods(SamplingMethodID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Settings(
                    SampleID INTEGER,
                    SettingID INTEGER,
                    Samples_SettingsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_SettingsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SettingID) REFERENCES Settings(SettingID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Units(
                    SampleID INTEGER,
                    UnitID INTEGER,
                    Samples_UnitsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_UnitsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(UnitID) REFERENCES Units(UnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLING_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS SamplingMethods(
                    SamplingMethodID INTEGER PRIMARY KEY,
                    ParentSamplingMethodID INTEGER,
                    SamplingMethodParentRow INTEGER,
                    SamplingMethodName TEXT NOT NULL CHECK (SamplingMethodName <> ''),
                    SamplingMethodDescription TEXT, 
                    SamplingMethodCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SamplingMethodModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SamplingMethodName COLLATE NOCASE),
                    UNIQUE (ParentSamplingMethodID, SamplingMethodParentRow)
                    )'''

CREATE_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS Settings(
                    SettingID INTEGER PRIMARY KEY,
                    ParentSettingID INTEGER,
                    SettingParentRow INTEGER,
                    SettingName TEXT NOT NULL CHECK (SettingName <> ''),
                    SettingDescription TEXT,
                    SettingCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SettingModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SettingName COLLATE NOCASE),
                    UNIQUE (ParentSettingID, SettingParentRow)
                    )'''

CREATE_SOURCES_TABLE = '''CREATE TABLE IF NOT EXISTS Sources(
                    SourceID INTEGER PRIMARY KEY,
                    Authors TEXT,
                    Year INTEGER,
                    Title TEXT,
                    Source TEXT,
                    doi TEXT,
                    ShortCitation TEXT NOT NULL CHECK (ShortCitation <> ''), 
                    SourceCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SourceModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (ShortCitation COLLATE NOCASE)
                    )'''

CREATE_SPOT_COMPOSITION_TABLE = '''CREATE TABLE IF NOT EXISTS SpotCompositions(
                    SpotCompositionID INTEGER PRIMARY KEY,
                    ParentSpotCompositionID INTEGER,
                    SpotCompositionParentRow INTEGER,
                    SpotCompositionName TEXT NOT NULL CHECK (SpotCompositionName <> ''),
                    SpotCompositionDescription TEXT, 
                    SpotCompositionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SpotCompositionModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SpotCompositionName COLLATE NOCASE),
                    UNIQUE (ParentSpotCompositionID, SpotCompositionParentRow)
                    )'''

CREATE_SPOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS SpotContexts(
                    SpotContextID INTEGER PRIMARY KEY,
                    ParentSpotContextID INTEGER,
                    SpotContextParentRow INTEGER,
                    SpotContextName TEXT NOT NULL CHECK (SpotContextName <> ''),
                    SpotContextDescription TEXT, 
                    SpotContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SpotContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SpotContextName COLLATE NOCASE),
                    UNIQUE (ParentSpotContextID, SpotContextParentRow)
                    )'''

CREATE_SPOTS_TABLE = '''CREATE TABLE IF NOT EXISTS Spots(
                    SpotID INTEGER PRIMARY KEY,
                    SpotName TEXT NOT NULL CHECK (SpotName <> ''), 
                    AliquotID INTEGER,
                    SpotCompositionID INTEGER,
                    SpotCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SpotModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SpotName COLLATE NOCASE),
                    FOREIGN KEY(AliquotID) REFERENCES Aliquots(AliquotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SpotCompositionID) REFERENCES SpotCompositions(SpotCompositionID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SPOTS_SPOTCOMPOSITION_TABLE = '''CREATE TABLE IF NOT EXISTS Spots_SpotCompositions(
                    SpotID INTEGER,
                    SpotCompositionID INTEGER,
                    Spots_SpotCompositionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Spots_SpotCompositionModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SpotCompositionID) REFERENCES SpotCompositions(SpotCompositionID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SPOTS_SPOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Spots_SpotContexts(
                    SpotID INTEGER,
                    SpotContextID INTEGER,
                    Spots_SpotContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Spots_SpotContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SpotContextID) REFERENCES SpotContexts(SpotContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS Units(
                    UnitID INTEGER PRIMARY KEY,
                    ParentUnitID INTEGER,
                    UnitParentRow INTEGER,
                    UnitName TEXT NOT NULL CHECK (UnitName <> ''),
                    UnitDescription TEXT, 
                    UnitCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UnitModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UnitName COLLATE NOCASE),
                    UNIQUE (ParentUnitID, UnitParentRow)
                    )'''

CREATE_UPBANALYSIS_METHOD_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalysisMethods(
                    UPbAnalysisMethodID INTEGER PRIMARY KEY,
                    UPbAnalysisMethodName TEXT NOT NULL CHECK (UPbAnalysisMethodName <> ''),
                    UPbAnalysisMethodDescription TEXT, 
                    UPbAnalysisMethodCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalysisMethodModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UPbAnalysisMethodName COLLATE NOCASE)
                    )'''

CREATE_UPBANALYSES_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalyses(
                    UPbAnalysisID INTEGER PRIMARY KEY,
                    SpotID INTEGER NOT NULL,
                    SourceID INTEGER,
                    LabFacilityID INTEGER,
                    InstrumentID INTEGER,
                    UPbAnalysisMethodID INTEGER, 
                    Pb204cps REAL, 
                    Pb206cps REAL, 
                    Pb207cps REAL, 
                    Pb208cps REAL, 
                    “Pb*cps” REAL,
                    Th232cps REAL, 
                    U235cps REAL, 
                    U238cps REAL,
                    Uppm REAL,
                    Thppm REAL,
                    "U/Th" REAL,
                    “Th/U” REAL,
                    "206Pb/207Pb" REAL,
                    "206Pb/207PbError" REAL, 
                    "207Pb/206Pb" REAL,
                    "207Pb/206PbError" REAL, 
                    "207Pb/235U" REAL,
                    "207Pb/235UError" REAL, 
                    "235U/207Pb" REAL,
                    "235U/207PbError" REAL, 
                    "206Pb/238U" REAL,
                    "206Pb/238UError" REAL, 
                    "238U/206Pb" REAL,
                    "238U/206PbError" REAL, 
                    "208Pb/232Th" REAL,
                    "208Pb/232ThError" REAL, 
                    "232Th/208Pb" REAL,
                    "232Th/208PbError" REAL, 
                    "238U/232Th" REAL,
                    "238U/232ThError" REAL, 
                    "232Th/238U" REAL,
                    "232Th/238UError" REAL, 
                    "204Pb/238U" REAL,
                    "204Pb/238UError" REAL, 
                    "238U/204Pb" REAL,
                    "238U/204PbError" REAL, 
                    "206Pb/204Pb" REAL,
                    "206Pb/204PbError" REAL, 
                    "204Pb/206Pb" REAL,
                    "204Pb/206PbError" REAL, 
                    "207Pb/204Pb" REAL,
                    "207Pb/204PbError" REAL, 
                    "204Pb/207Pb" REAL,
                    "204Pb/207PbError" REAL, 
                    "208Pb/204Pb" REAL,
                    "208Pb/204PbError" REAL, 
                    "204Pb/208Pb" REAL,
                    "204Pb/208PbError" REAL, 
                    RatioErrorTypeID INTEGER,
                    “ErrorCorr/Rho” REAL,
                    "206Pb/207PbAge" REAL,
                    "206Pb/207PbAgeError" REAL, 
                    "207Pb/206PbAge" REAL,
                    "207Pb/206PbAgeError" REAL, 
                    "207Pb/235UAge" REAL,
                    "207Pb/235UAgeError" REAL, 
                    "235U/207PbAge" REAL,
                    "235U/207PbAgeError" REAL, 
                    "206Pb/238UAge" REAL,
                    "206Pb/238UAgeError" REAL, 
                    "238U/206PbAge" REAL,
                    "238U/206PbAgeError" REAL, 
                    AgeErrorTypeID INTEGER,
                    BestAge REAL,
                    BestAgeError REAL, 
                    BestAgeErrorTypeID INTEGER,
                    “Concordance206Pb/238U-206Pb/207Pb” REAL,
                    “Concordance206Pb/238U-206Pb/207PbTypeID” INTEGER, 
                    “Concordance206Pb/238U-208Pb/232Th” REAL,
                    “Concordance206Pb/238U-208Pb/232ThTypeID” INTEGER,
                    SpotSize REAL,
                    SpotSizeUnitID INTEGER,
                    Accepted BOOL,
                    RejectionReasonID INTEGER,
                    UPbAnalysisCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalysisModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SourceID) REFERENCES Sources(SourceID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(LabFacilityID) REFERENCES LabFacilities(LabFacilityID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(UPbAnalysisMethodID) REFERENCES UPbAnalysisMethods(UPbAnalysisMethodID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(InstrumentID) REFERENCES Instruments(InstrumentID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(RatioErrorTypeID) REFERENCES ErrorTypes(ErrorTypeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(AgeErrorTypeID) REFERENCES ErrorTypes(ErrorTypeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(BestAgeErrorTypeID) REFERENCES ErrorTypes(ErrorTypeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )''' \

CREATE_UPBANALYSES_ANALYSISINTERPRETATIONS_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalyses_AnalysisInterpretations(
                    UPbAnalysisID INTEGER,
                    AnalysisInterpretationID INTEGER,
                    UPbAnalyses_AnalysisInterpretationsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalyses_AnalysisInterpretationsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(UPbAnalysisID) REFERENCES UPbAnalyses(UPbAnalysisID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AnalysisInterpretationID) REFERENCES AnalysisInterpretations(AnalysisInterpretationID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''


'''Commands to create tables and populate default tables'''


def create_tables(db_file):
    """
    Connect to the database and execute the sql strings defined above to create the database tables
    Only creates tables that do not already exist - does not overwrite existing tables
    If the Ages table is empty, it will fill it from the Geologic timescale xml file
    :param db_file: Database file with full path
    """
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()

        # Create the tables
        c.execute(CREATE_ABOUT_TABLE)

        # Create unit and type tables
        c.execute(CREATE_AGE_UNITS_TABLE)
        c.execute(CREATE_CONCORDANCE_TYPES_TABLE)
        c.execute(CREATE_DIRECTION_UNITS_TABLE)
        c.execute(CREATE_DISTANCE_UNITS_TABLE)
        c.execute(CREATE_ERROR_TYPES_TABLE)

        # Create conversion tables
        c.execute(CREATE_AGE_CONVERSIONS_TABLE)
        c.execute(CREATE_CONCORDANCE_CONVERSIONS_TABLE)
        c.execute(CREATE_DIRECTION_CONVERSIONS_TABLE)
        c.execute(CREATE_DISTANCE_CONVERSIONS_TABLE)
        c.execute(CREATE_ERROR_CONVERSIONS_TABLE)

        # Create analysis tag tables
        c.execute(CREATE_ANALYSIS_INTERPRETATIONS_TABLE)
        c.execute(CREATE_INSTRUMENTS_TABLE)
        c.execute(CREATE_LAB_FACILITIES_TABLE)
        c.execute(CREATE_SOURCES_TABLE)
        c.execute(CREATE_UPBANALYSIS_METHOD_TABLE)

        # Create spot tag tables
        c.execute(CREATE_SPOT_COMPOSITION_TABLE)
        c.execute(CREATE_SPOT_CONTEXT_TABLE)

        # Create aliquot tag tables
        c.execute(CREATE_ALIQUOT_CONTEXT_TABLE)

        # Create sample tag tables
        c.execute(CREATE_AGE_CONSTRAINTS_TABLE)
        c.execute(CREATE_AGE_INTERPRETATIONS_TABLE)
        c.execute(CREATE_AGE_SIGNATURES_TABLE)
        c.execute(CREATE_AGES_TABLE)
        c.execute(CREATE_COLUMNS_TABLE)
        c.execute(CREATE_GPS_LOCATIONS_TABLE)
        c.execute(CREATE_REGIONS_TABLE)
        c.execute(CREATE_ROCK_TYPES_TABLE)
        c.execute(CREATE_SAMPLE_AGE_TABLE)
        c.execute(CREATE_SAMPLE_CONTEXT_TABLE)
        c.execute(CREATE_SAMPLEAGES_AGECONSTRAINTS_TABLE)
        c.execute(CREATE_SAMPLEAGES_AGEINTERPRETATIONS_TABLE)
        c.execute(CREATE_SAMPLING_METHODS_TABLE)
        c.execute(CREATE_SETTINGS_TABLE)
        c.execute(CREATE_UNITS_TABLE)

        # Create sample item and analysis tables
        c.execute(CREATE_SAMPLES_TABLE)
        c.execute(CREATE_ALIQUOTS_TABLE)
        c.execute(CREATE_SPOTS_TABLE)
        c.execute(CREATE_UPBANALYSES_TABLE)

        # Create many-to-many sample tables
        c.execute(CREATE_SAMPLES_AGESIGNATURES_TABLE)
        c.execute(CREATE_SAMPLES_REGIONS_TABLE)
        c.execute(CREATE_SAMPLES_ROCKTYPES_TABLE)
        c.execute(CREATE_SAMPLES_SAMPLECONTEXT_TABLE)
        c.execute(CREATE_SAMPLES_SAMPLINGMETHODS_TABLE)
        c.execute(CREATE_SAMPLES_SETTINGS_TABLE)
        c.execute(CREATE_SAMPLES_UNITS_TABLE)

        # Create many-to-many anliquot tables
        c.execute(CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE)

        # Create many-to-many spot tables
        c.execute(CREATE_SPOTS_SPOTCOMPOSITION_TABLE)
        c.execute(CREATE_SPOTS_SPOTCONTEXT_TABLE)

        c.execute(CREATE_FILTER_GROUPS_TABLE)

        CT.create_triggers(c)

        DBV.create_sample_view(c)

        # Populate the age table during initiation
        sql = '''SELECT * FROM Ages'''
        if c.execute(sql):
            out = c.fetchall()
            if not out:  # if there is no output, the table is empty
                populate_ages(conn)  # populate it
        else:
            print(f'query failed')


def populate_ages(conn):
    """
    Connect to the database and add the Geologic timescale tree structure with names and ages
    GSA Geologic Time Scale v. 5.0 as a xml file
    Overwrites any previous changes to this table
    :param conn: Database connection from create_tables
    """

    with conn:
        c = conn.cursor()
        # Begin by deleting all rows in the table to allow for a reset if things get changed
        sql = 'DELETE FROM Ages'
        c.execute(sql)
        xml_file = "./Reference/GeologicTime_Ages.xml"
        tree = ET.parse(xml_file)
        root = tree.getroot()
        eon_row = 0
        era_row = 0
        period_row = 0
        epoch_row = 0
        age_row = 0
        for eon in root.findall('Eon'):
            age_item = ('', eon_row, f'{eon.get("name")}', f'{eon.get("oldest")}', f'{eon.get("youngest")}')
            add_age(c, age_item)
            for era in eon.findall('Era'):
                eon_name = eon.get("name")
                if c.execute(f'SELECT AgeID FROM AGES WHERE AgeName = "{eon_name}"'):
                    out = c.fetchall()
                    eon_id = out[0][0]
                    age_item = (eon_id, era_row, f'{era.get("name")}', f'{era.get("oldest")}', f'{era.get("youngest")}')
                    add_age(c, age_item)
                    for period in era.findall('Period'):
                        era_name = era.get("name")
                        if c.execute(f'SELECT AgeID FROM AGES WHERE AgeName = "{era_name}"'):
                            out = c.fetchall()
                            era_id = out[0][0]
                            age_item = (
                                era_id, period_row, f'{period.get("name")}', f'{period.get("oldest")}', f'{period.get("youngest")}')
                            add_age(c, age_item)
                            for epoch in period.findall('Epoch'):
                                period_name = period.get("name")
                                if c.execute(f'SELECT AgeID FROM AGES WHERE AgeName = "{period_name}"'):
                                    out = c.fetchall()
                                    period_id = out[0][0]
                                    age_item = (period_id, epoch_row, f'{epoch.get("name")}', f'{epoch.get("oldest")}',
                                                f'{epoch.get("youngest")}')
                                    add_age(c, age_item)
                                    for age in epoch.findall('Age'):
                                        epoch_name = epoch.get("name")
                                        # Many epochs have the same name, need to get most recent one
                                        if c.execute(
                                                f'SELECT AgeID FROM AGES WHERE AgeName = "{epoch_name}" '
                                                f'ORDER BY AgeID DESC'):
                                            out = c.fetchall()
                                            epoch_id = out[0][0]
                                            age_item = (epoch_id, age_row, f'{age.get("name")}', f'{age.get("oldest")}',
                                                        f'{age.get("youngest")}')
                                            add_age(c, age_item)
                                        age_row += 1
                                    epoch_row += 1
                                    age_row = 0
                            period_row += 1
                            epoch_row = 0
                    era_row += 1
                    period_row = 0
            eon_row += 1
            era_row = 0


def add_age(c, age):
    """
    Called by populate_ages
    Adds each age item to the table with its parent ID
    :param c: database connection cursor
    :param age: tuple that contains (Parent ageID, age name, Max Ma, Min Ma)
    """
    if age[0]:
        # if there is a parent
        sql = '''INSERT INTO Ages(ParentAgeID, AgeParentRow, AgeName, MaxMa, MinMa)
                        VALUES(?,?,?,?,?)'''
        values = (age[0], age[1], age[2], age[3], age[4])
        if not c.execute(sql, values):
            print(f'failed to add {age[2]}')
    else:
        sql = '''INSERT INTO Ages(AgeParentRow, AgeName, MaxMa, MinMa)
                        VALUES(?,?,?,?)'''
        values = (age[1], age[2], age[3], age[4])
        if not c.execute(sql, values):
            print(f'failed to add {age[2]}')


if __name__ == '__main__':
    db_file = '../TestSchema.db'
    create_tables(db_file)
