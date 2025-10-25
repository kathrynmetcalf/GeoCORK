import os
import sys
import xml.etree.ElementTree as ET  # xml reader
import sqlite3

from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
from PyQt6.QtWidgets import QMessageBox

import Functions.Database_manager as Database_manager
import Functions.SQLUtils as SQLUtils
import logger_setup
from Functions.Savepoint_manager import create_savepoint, release_savepoint, rollback_savepoint
from Functions.Settings_manager import SettingsManager
from collections import Counter
settings = SettingsManager().settings

'''
Commands to create the database
Foreign keys are set to cascade on update
When a foreign key is deleted, most will be set to null
The only exception is the AliquotID in the Spots table, which will cascade on delete
Names must be unique and are checked for case sensitivity
Analyses where Rejected is 0 are considered accepted, 1 are considered rejected
'''
# look under linking aboutmodified to other tables
'''SQL strings to create each table'''

CREATE_ABOUT_TABLE = '''CREATE TABLE IF NOT EXISTS About(
                    AboutID INTEGER PRIMARY KEY,
                    Name TEXT NOT NULL CHECK (Name <> ''),
                    Authors TEXT NOT NULL CHECK (Authors <> ''),
                    Citation,
                    ReferenceLink,
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

CREATE_AGE_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS AgeUnitConversions(
                    FromAgeUnitID INTEGER NOT NULL CHECK(FromAgeUnitID <> ''),
                    ToAgeUnitID INTEGER NOT NULL CHECK(ToAgeUnitID <> ''),
                    AgeUnitConversionCalculation TEXT NOT NULL CHECK(AgeUnitConversionCalculation <> ''), 
                    AgeUnitConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AgeUnitConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
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
                    OldestAge REAL,
                    YoungestAge REAL,
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
                    SampleID INTEGER NOT NULL,
                    AliquotCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AliquotModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AliquotName COLLATE NOCASE, ParentAliquotID, SampleID),
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

CREATE_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Columns(
                    ColumnID INTEGER PRIMARY KEY,
                    ColumnName TEXT NOT NULL CHECK (ColumnName <> ''), 
                    ColumnTotalHeightDepth REAL, 
                    ColumnTotalHeightDepthUnitID INTEGER, 
                    ColumnBaseGPSID INTEGER,
                    ColumnDescription TEXT, 
                    ColumnCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ColumnModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (ColumnName, ColumnTotalHeightDepth, ColumnTotalHeightDepthUnitID, ColumnBaseGPSID, ColumnDescription),
                    FOREIGN KEY(ColumnTotalHeightDepthUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(ColumnBaseGPSID) REFERENCES GPSLocations(GPSLocationID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_CONCORDANCE_FORMATS_TABLE = '''CREATE TABLE IF NOT EXISTS ConcordanceFormats(
                    ConcordanceFormatID INTEGER PRIMARY KEY,
                    ConcordanceFormatName TEXT NOT NULL CHECK(ConcordanceFormatName <> ''),
                    ConcordanceFormatAbbreviation TEXT NOT NULL CHECK(ConcordanceFormatAbbreviation <> ''),
                    ConcordanceFormatDescription TEXT,
                    ConcordanceFormatCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ConcordanceFormatModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ConcordanceFormatName COLLATE NOCASE),
                    UNIQUE(ConcordanceFormatAbbreviation COLLATE NOCASE)
)'''

CREATE_CONCORDANCE_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS ConcordanceFormatConversions(
                    FromConcordanceFormatID INTEGER NOT NULL CHECK(FromConcordanceFormatID <> ''),
                    ToConcordanceFormatID INTEGER NOT NULL CHECK(ToConcordanceFormatID <> ''),
                    ConcordanceFormatConversionCalculation TEXT NOT NULL CHECK(ConcordanceFormatConversionCalculation <> ''), 
                    ConcordanceFormatConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ConcordanceFormatConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    UNIQUE (FromConcordanceFormatID, ToConcordanceFormatID),
                    FOREIGN KEY(FromConcordanceFormatID) REFERENCES ConcordanceFormats(ConcordanceFormatID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToConcordanceFormatID) REFERENCES ConcordanceFormats(ConcordanceFormatID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_DIRECTION_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS DirectionUnits(
                    DirectionUnitID INTEGER PRIMARY KEY,
                    DirectionUnitName TEXT NOT NULL CHECK(DirectionUnitName <> ''),
                    DirectionUnitAbbreviation TEXT NOT NULL CHECK(DirectionUnitAbbreviation <> ''),
                    DirectionUnitDescription TEXT,
                    DirectionUnitCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    DirectionUnitModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(DirectionUnitName COLLATE NOCASE)
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

CREATE_DISTANCE_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS DistanceUnitConversions(
                    FromDistanceUnitID INTEGER NOT NULL CHECK(FromDistanceUnitID <> ''),
                    ToDistanceUnitID INTEGER NOT NULL CHECK(ToDistanceUnitID <> ''),
                    DistanceUnitConversionCalculation TEXT NOT NULL CHECK(DistanceUnitConversionCalculation <> ''), 
                    DistanceUnitConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    DistanceUnitConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    UNIQUE (FromDistanceUnitID, ToDistanceUnitID),
                    FOREIGN KEY(FromDistanceUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToDistanceUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ERROR_FORMATS_TABLE = '''CREATE TABLE IF NOT EXISTS ErrorFormats(
                    ErrorFormatID INTEGER PRIMARY KEY,
                    ErrorFormatName TEXT NOT NULL CHECK(ErrorFormatName <> ''),
                    ErrorFormatAbbreviation TEXT NOT NULL CHECK(ErrorFormatAbbreviation <> ''),
                    ErrorFormatDescription TEXT,
                    ErrorFormatCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ErrorFormatModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ErrorFormatName COLLATE NOCASE),
                    UNIQUE(ErrorFormatAbbreviation COLLATE NOCASE)
)'''

CREATE_ERROR_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS ErrorFormatConversions(
                    FromErrorFormatID INTEGER NOT NULL CHECK(FromErrorFormatID <> ''),
                    ToErrorFormatID INTEGER NOT NULL CHECK(ToErrorFormatID <> ''),
                    ErrorFormatConversionCalculation TEXT NOT NULL CHECK(ErrorFormatConversionCalculation <> ''), 
                    ErrorFormatConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ErrorFormatConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (FromErrorFormatID, ToErrorFormatID),
                    FOREIGN KEY(FromErrorFormatID) REFERENCES ErrorFormats(ErrorFormatID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToErrorFormatID) REFERENCES ErrorFormats(ErrorFormatID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_GRAINS_TABLE = '''CREATE TABLE IF NOT EXISTS Grains(
                    GrainID INTEGER PRIMARY KEY,
                    GrainName TEXT NOT NULL CHECK (GrainName <> ''),
                    GrainCompositionID INTEGER,
                    GrainDescription TEXT,
                    GrainCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GrainModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (GrainName COLLATE NOCASE),
                    FOREIGN KEY(GrainCompositionID) REFERENCES GrainCompositions(GrainCompositionID)
                        ON UPDATE CASCADE 
                        ON DELETE SET NULL
)'''

CREATE_GRAIN_CONTEXTS_TABLE = '''CREATE TABLE IF NOT EXISTS GrainContexts(
                    GrainContextID INTEGER PRIMARY KEY,
                    ParentGrainContextID INTEGER,
                    GrainContextParentRow INTEGER,
                    GrainContextName TEXT NOT NULL CHECK (GrainContextName <> ''),
                    GrainContextDescription TEXT,
                    GrainContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GrainContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (GrainContextName COLLATE NOCASE),
                    UNIQUE (ParentGrainContextID, GrainContextParentRow)
)'''

CREATE_GRAINS_GRAINCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Grains_GrainContexts(
                    GrainID INTEGER NOT NULL,
                    GrainContextID INTEGER NOT NULL,
                    Grains_GrainContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Grains_GrainContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (GrainID, GrainContextID),
                    FOREIGN KEY(GrainID) REFERENCES Grains(GrainID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(GrainContextID) REFERENCES GrainContexts(GrainContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_GRAIN_COMPOSITION_TABLE = '''CREATE TABLE IF NOT EXISTS GrainCompositions(
                    GrainCompositionID INTEGER PRIMARY KEY,
                    GrainCompositionName TEXT NOT NULL CHECK (GrainCompositionName <> ''),
                    GrainCompositionDescription TEXT,
                    GrainCompositionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GrainCompositionModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (GrainCompositionName COLLATE NOCASE)
)'''

CREATE_GPS_CONVERSIONS_TABLE = '''CREATE TABLE IF NOT EXISTS GPSFormatConversions(
                    FromGPSFormatID INTEGER NOT NULL CHECK(FromGPSFormatID <> ''),
                    ToGPSFormatID INTEGER NOT NULL CHECK(ToGPSFormatID <> ''),
                    GPSFormatConversionCalculation TEXT NOT NULL CHECK(GPSFormatConversionCalculation <> ''),
                    GPSFormatConversionCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GPSFormatConversionModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (FromGPSFormatID, ToGPSFormatID),
                    FOREIGN KEY(FromGPSFormatID) REFERENCES GPSFormats(GPSFormatID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ToGPSFormatID) REFERENCES GPSFormats(GPSFormatID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_GPS_FORMATS_TABLE = '''CREATE TABLE IF NOT EXISTS GPSFormats(
                    GPSFormatID INTEGER PRIMARY KEY,
                    GPSFormatName TEXT NOT NULL CHECK(GPSFormatName <> ''),
                    GPSFormatAbbreviation TEXT NOT NULL CHECK(GPSFormatAbbreviation <> ''),
                    GPSFormatDescription TEXT,
                    GPSFormatCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GPSFormatModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(GPSFormatName COLLATE NOCASE),
                    UNIQUE(GPSFormatAbbreviation COLLATE NOCASE)
)'''

CREATE_GPS_LOCATIONS_TABLE = '''CREATE TABLE IF NOT EXISTS GPSLocations(
                    GPSLocationID INTEGER PRIMARY KEY,
                    GPSLocationConverted TEXT,
                    GPSLocationDisplay AS (CASE
                        WHEN GPSFormatID = 1 THEN GPSLatDeg || "°, " ||  GPSLonDeg || "° "
                        WHEN GPSFormatID = 2 THEN GPSLatDeg || "°" || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonDirectionID
                        WHEN GPSFormatID = 3 THEN GPSLatDeg || "°" || GPSLatMin || "', " || GPSLonDeg || "° " || GPSLonMin || "'"
                        WHEN GPSFormatID = 4 THEN GPSLatDeg || "°" || GPSLatMin || "' " || GPSLatDirectionID || ", " || GPSLonDeg || "°" || GPSLonMin || "' " || GPSLonDirectionID
                        WHEN GPSFormatID = 5 THEN GPSLatDeg || "°" || GPSLatMin || "'" || GPSLatSec || """, " || GPSLonDeg || "°" || GPSLonMin || "'" || GPSLonSec || """"
                        WHEN GPSFormatID = 6 THEN GPSLatDeg || "°" || GPSLatMin || "'" || GPSLatSec || """ " || GPSLatDirectionID || ", " || GPSLonDeg || "°" || GPSLonMin || "'" || GPSLonSec || """ " || GPSLonDirectionID
                        WHEN GPSFormatID = 7 THEN GPSUTMZone || ", " || GPSUTME || "m E, " || GPSUTMN || "m N"
                        END) STORED,
                    GPSLatDeg REAL,
                    GPSLatMin REAL,
                    GPSLatSec REAL,
                    GPSLatDirectionID INTEGER CHECK (GPSLatDirectionID IN (1, 2) OR GPSLatDirectionID IS NULL),
                    GPSLonDeg REAL,
                    GPSLonMin REAL,
                    GPSLonSec REAL,
                    GPSLonDirectionID INTEGER CHECK (GPSLonDirectionID IN (3, 4) OR GPSLonDirectionID IS NULL),
                    GPSUTMZone TEXT,
                    GPSUTMN REAL,
                    GPSUTME REAL,
                    GPSFormatID INTEGER,
                    GPSElev REAL,
                    GPSElevError REAL,
                    GPSElevUnitID INTEGER,
                    GPSLocationCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GPSLocationModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, GPSElev, GPSElevError, GPSElevUnitID),
                    FOREIGN KEY(GPSLatDirectionID) REFERENCES DirectionUnits(DirectionUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(GPSLonDirectionID) REFERENCES DirectionUnits(DirectionUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY (GPSFormatID) REFERENCES GPSFormats(GPSFormatID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(GPSElevUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
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

CREATE_REFERENCES_TABLE = '''CREATE TABLE IF NOT EXISTS "References"(
                    ReferenceID INTEGER PRIMARY KEY,
                    Authors TEXT,
                    Year INTEGER,
                    Title TEXT,
                    Source TEXT,
                    DOI TEXT,
                    ReferenceDescription TEXT,
                    ReferenceCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ReferenceModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (Authors, Year, Title, Source, DOI)
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

CREATE_REJECTION_REASONS_TABLE = '''CREATE TABLE IF NOT EXISTS RejectionReasons(
                    RejectionReasonID INTEGER PRIMARY KEY,
                    RejectionReasonName TEXT NOT NULL CHECK (RejectionReasonName <> ''),
                    RejectionReasonDescription TEXT,
                    RejectionReasonCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    RejectionReasonModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (RejectionReasonName COLLATE NOCASE)
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
                    DirectAge REAL,
                    DirectAgeError REAL,
                    DirectAgeErrorFormatID INTEGER,
                    OldestDirectAge REAL,
                    YoungestDirectAge REAL, 
                    DirectAgeUnitID INTEGER,
                    OldestAgeID INTEGER,
                    YoungestAgeID INTEGER,
                    SampleAgeDescription TEXT,
                    SampleAgeCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SampleAgeModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (DirectAge, DirectAgeError, DirectAgeErrorFormatID, OldestDirectAge, YoungestDirectAge, DirectAgeUnitID, OldestAgeID, YoungestAgeID),
                    FOREIGN KEY(DirectAgeErrorFormatID) REFERENCES ErrorFormats(ErrorFormatID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(DirectAgeUnitID) REFERENCES AgeUnits(AgeUnitID)
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

CREATE_SAMPLEAGES_AGECONSTRAINTS_TABLE = '''CREATE TABLE IF NOT EXISTS SampleAges_AgeConstraints(
                    SampleAgeID INTEGER NOT NULL,
                    AgeConstraintID INTEGER NOT NULL,
                    SamplesAges_AgeConstraintsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SamplesAges_AgeConstraintsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleAgeID, AgeConstraintID),
                    FOREIGN KEY(SampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AgeConstraintID) REFERENCES AgeConstraints(AgeConstraintID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLEAGES_AGEINTERPRETATIONS_TABLE = '''CREATE TABLE IF NOT EXISTS SampleAges_AgeInterpretations(
                    SampleAgeID INTEGER NOT NULL,
                    AgeInterpretationID INTEGER NOT NULL,
                    SamplesAges_AgeInterpretationsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SamplesAges_AgeInterpretationsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleAgeID, AgeInterpretationID),
                    FOREIGN KEY(SampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AgeInterpretationID) REFERENCES AgeInterpretations(AgeInterpretationID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLEAGES_REFERENCES_TABLE = '''CREATE TABLE IF NOT EXISTS SampleAges_References(
                    SampleAgeID INTEGER NOT NULL,
                    ReferenceID INTEGER NOT NULL,
                    SamplesAges_ReferencesCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SamplesAges_ReferencesModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleAgeID, ReferenceID),
                    FOREIGN KEY(SampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ReferenceID) REFERENCES "References"(ReferenceID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples(
                    SampleID INTEGER PRIMARY KEY,
                    SampleName TEXT NOT NULL CHECK (SampleName <> ''), 
                    SampleIGSN TEXT, 
                    SampleGPSLocationID INTEGER,
                    SampleColumnID INTEGER,
                    HeightDepth REAL,
                    HeightDepthError REAL,
                    HeightDepthUnitID INTEGER,
                    DefaultSampleAgeID INTEGER,
                    SampleDescription TEXT,
                    SampleCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SampleModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleName COLLATE NOCASE),
                    UNIQUE (SampleIGSN COLLATE NOCASE), 
                    FOREIGN KEY(SampleGPSLocationID) REFERENCES GPSLocations(GPSLocationID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(SampleColumnID) REFERENCES Columns(ColumnID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(HeightDepthUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(DefaultSampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SAMPLES_AGESIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_AgeSignatures(
                    SampleID INTEGER NOT NULL,
                    AgeSignatureID INTEGER NOT NULL,
                    Samples_AgeSignaturesCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_AgeSignaturesModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleID, AgeSignatureID),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AgeSignatureID) REFERENCES AgeSignatures(AgeSignatureID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_REGIONS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Regions(
                    SampleID INTEGER NOT NULL,
                    RegionID INTEGER NOT NULL,
                    Samples_RegionsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_RegionsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleID, RegionID),
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
                    UNIQUE (SampleID, RockTypeID),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(RockTypeID) REFERENCES RockTypes(RockTypeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLEAGES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_SampleAges(
                    SampleID INTEGER NOT NULL,
                    SampleAgeID INTEGER NOT NULL,
                    Samples_SampleAgesCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_SampleAgesModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleID, SampleAgeID),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SampleAgeID) REFERENCES SampleAges(SampleAgeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLECONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_SampleContexts(
                    SampleID INTEGER NOT NULL,
                    SampleContextID INTEGER NOT NULL,
                    Samples_SampleContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_SampleContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleID, SampleContextID),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SampleContextID) REFERENCES SampleContexts(SampleContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLINGMETHODS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_SamplingMethods(
                    SampleID INTEGER NOT NULL,
                    SamplingMethodID INTEGER NOT NULL,
                    Samples_SamplingMethodsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_SamplingMethodsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleID, SamplingMethodID),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SamplingMethodID) REFERENCES SamplingMethods(SamplingMethodID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Settings(
                    SampleID INTEGER NOT NULL,
                    SettingID INTEGER NOT NULL,
                    Samples_SettingsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_SettingsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleID, SettingID),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SettingID) REFERENCES Settings(SettingID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Units(
                    SampleID INTEGER NOT NULL,
                    UnitID INTEGER NOT NULL,
                    Samples_UnitsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_UnitsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleID, UnitID),
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
                    AliquotID INTEGER NOT NULL,
                    GrainID INTEGER,
                    SpotCompositionID INTEGER,
                    SpotCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SpotModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SpotName COLLATE NOCASE, AliquotID),
                    FOREIGN KEY(AliquotID) REFERENCES Aliquots(AliquotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SpotCompositionID) REFERENCES SpotCompositions(SpotCompositionID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(GrainID) REFERENCES Grains(GrainID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SPOTS_SPOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Spots_SpotContexts(
                    SpotID INTEGER NOT NULL,
                    SpotContextID INTEGER NOT NULL,
                    Spots_SpotContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Spots_SpotContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SpotID, SpotContextID),
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

CREATE_UPBANALYSES_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalyses(
                    UPbAnalysisID INTEGER PRIMARY KEY,
                    UPbAnalysisName TEXT NOT NULL CHECK (UPbAnalysisName <> ''),
                    SpotID INTEGER NOT NULL,
                    ReferenceID INTEGER,
                    LabFacilityID INTEGER,
                    InstrumentID INTEGER,
                    UPbAnalysisMethodID INTEGER, 
                    Pb204cps REAL, 
                    Pb206cps REAL, 
                    Pb207cps REAL, 
                    Pb208cps REAL, 
                    "Pb*cps" REAL,
                    Th232cps REAL, 
                    U235cps REAL, 
                    U238cps REAL,
                    Uppm REAL,
                    Thppm REAL,
                    "U/Th" REAL,
                    "Th/U" REAL,
                    "CalculatedU/Th" AS (CASE
                        WHEN "U/Th" IS NOT NULL THEN "U/Th"
                        WHEN "Th/U" IS NOT NULL THEN 1/"Th/U"
                        ELSE NULL
                        END) STORED,
                    "CalculatedTh/U" AS (CASE
                        WHEN "Th/U" IS NOT NULL THEN "Th/U"
                        WHEN "U/Th" IS NOT NULL THEN 1/"U/Th"
                        ELSE NULL
                        END) STORED,
                    "206Pb/207Pb" REAL,
                    "206Pb/207PbError" REAL, 
                    "207Pb/206Pb" REAL,
                    "207Pb/206PbError" REAL, 
                    "Calculated206Pb/207Pb" AS (CASE
                        WHEN "206Pb/207Pb" IS NOT NULL THEN "206Pb/207Pb"
                        WHEN "207Pb/206Pb" IS NOT NULL THEN 1/"207Pb/206Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated207Pb/206Pb" AS (CASE
                        WHEN "207Pb/206Pb" IS NOT NULL THEN "207Pb/206Pb"
                        WHEN "206Pb/207Pb" IS NOT NULL THEN 1/"206Pb/207Pb"
                        ELSE NULL
                        END) STORED,
                    "207Pb/235U" REAL,
                    "207Pb/235UError" REAL, 
                    "235U/207Pb" REAL,
                    "235U/207PbError" REAL, 
                    "Calculated207Pb/235U" AS (CASE
                        WHEN "207Pb/235U" IS NOT NULL THEN "207Pb/235U"
                        WHEN "235U/207Pb" IS NOT NULL THEN 1/"235U/207Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated235U/207Pb" AS (CASE
                        WHEN "235U/207Pb" IS NOT NULL THEN "235U/207Pb"
                        WHEN "207Pb/235U" IS NOT NULL THEN 1/"207Pb/235U"
                        ELSE NULL
                        END) STORED,
                    "206Pb/238U" REAL,
                    "206Pb/238UError" REAL, 
                    "238U/206Pb" REAL,
                    "238U/206PbError" REAL,
                    "Calculated206Pb/238U" AS (CASE
                        WHEN "206Pb/238U" IS NOT NULL THEN "206Pb/238U"
                        WHEN "238U/206Pb" IS NOT NULL THEN 1/"238U/206Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated238U/206Pb" AS (CASE
                        WHEN "238U/206Pb" IS NOT NULL THEN "238U/206Pb"
                        WHEN "206Pb/238U" IS NOT NULL THEN 1/"206Pb/238U"
                        ELSE NULL
                        END) STORED, 
                    "208Pb/232Th" REAL,
                    "208Pb/232ThError" REAL, 
                    "232Th/208Pb" REAL,
                    "232Th/208PbError" REAL, 
                    "Calculated208Pb/232Th" AS (CASE
                        WHEN "208Pb/232Th" IS NOT NULL THEN "208Pb/232Th"
                        WHEN "232Th/208Pb" IS NOT NULL THEN 1/"232Th/208Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated232Th/208Pb" AS (CASE
                        WHEN "232Th/208Pb" IS NOT NULL THEN "232Th/208Pb"
                        WHEN "208Pb/232Th" IS NOT NULL THEN 1/"208Pb/232Th"
                        ELSE NULL
                        END) STORED,
                    "238U/232Th" REAL,
                    "238U/232ThError" REAL, 
                    "232Th/238U" REAL,
                    "232Th/238UError" REAL, 
                    "Calculated238U/232Th" AS (CASE
                        WHEN "238U/232Th" IS NOT NULL THEN "238U/232Th"
                        WHEN "232Th/238U" IS NOT NULL THEN 1/"232Th/238U"
                        ELSE NULL
                        END) STORED,
                    "Calculated232Th/238U" AS (CASE
                        WHEN "232Th/238U" IS NOT NULL THEN "232Th/238U"
                        WHEN "238U/232Th" IS NOT NULL THEN 1/"238U/232Th"
                        ELSE NULL
                        END) STORED,
                    "204Pb/238U" REAL,
                    "204Pb/238UError" REAL, 
                    "238U/204Pb" REAL,
                    "238U/204PbError" REAL, 
                    "Calculated204Pb/238U" AS (CASE
                        WHEN "204Pb/238U" IS NOT NULL THEN "204Pb/238U"
                        WHEN "238U/204Pb" IS NOT NULL THEN 1/"238U/204Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated238U/204Pb" AS (CASE
                        WHEN "238U/204Pb" IS NOT NULL THEN "238U/204Pb"
                        WHEN "204Pb/238U" IS NOT NULL THEN 1/"204Pb/238U"
                        ELSE NULL
                        END) STORED,
                    "206Pb/204Pb" REAL,
                    "206Pb/204PbError" REAL, 
                    "204Pb/206Pb" REAL,
                    "204Pb/206PbError" REAL, 
                    "Calculated206Pb/204Pb" AS (CASE
                        WHEN "206Pb/204Pb" IS NOT NULL THEN "206Pb/204Pb"
                        WHEN "204Pb/206Pb" IS NOT NULL THEN 1/"204Pb/206Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated204Pb/206Pb" AS (CASE
                        WHEN "204Pb/206Pb" IS NOT NULL THEN "204Pb/206Pb"
                        WHEN "206Pb/204Pb" IS NOT NULL THEN 1/"206Pb/204Pb"
                        ELSE NULL
                        END) STORED,
                    "207Pb/204Pb" REAL,
                    "207Pb/204PbError" REAL, 
                    "204Pb/207Pb" REAL,
                    "204Pb/207PbError" REAL, 
                    "Calculated207Pb/204Pb" AS (CASE
                        WHEN "207Pb/204Pb" IS NOT NULL THEN "207Pb/204Pb"
                        WHEN "204Pb/207Pb" IS NOT NULL THEN 1/"204Pb/207Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated204Pb/207Pb" AS (CASE
                        WHEN "204Pb/207Pb" IS NOT NULL THEN "204Pb/207Pb"
                        WHEN "207Pb/204Pb" IS NOT NULL THEN 1/"207Pb/204Pb"
                        ELSE NULL
                        END) STORED,
                    "208Pb/204Pb" REAL,
                    "208Pb/204PbError" REAL, 
                    "204Pb/208Pb" REAL,
                    "204Pb/208PbError" REAL, 
                    "Calculated208Pb/204Pb" AS (CASE
                        WHEN "208Pb/204Pb" IS NOT NULL THEN "208Pb/204Pb"
                        WHEN "204Pb/208Pb" IS NOT NULL THEN 1/"204Pb/208Pb"
                        ELSE NULL
                        END) STORED,
                    "Calculated204Pb/208Pb" AS (CASE
                        WHEN "204Pb/208Pb" IS NOT NULL THEN "204Pb/208Pb"
                        WHEN "208Pb/204Pb" IS NOT NULL THEN 1/"208Pb/204Pb"
                        ELSE NULL
                        END) STORED,
                    RatioErrorFormatID INTEGER,
                    "ErrorCorr/Rho" REAL,
                    "207Pb/206PbAge" REAL,
                    "207Pb/206PbAgeError" REAL, 
                    "207Pb/235UAge" REAL,
                    "207Pb/235UAgeError" REAL, 
                    "206Pb/238UAge" REAL,
                    "206Pb/238UAgeError" REAL,
                    "208Pb/232ThAge" REAL,
                    "208Pb/232ThAgeError" REAL,
                    BestAge REAL,
                    BestAgeError REAL, 
                    AgeErrorFormatID INTEGER,
                    AgeUnitID INTEGER,
                    AgeInterpretationID INTEGER,
                    Concordance REAL,
                    ConcordanceFormatID INTEGER,
                    SpotSize REAL,
                    SpotSizeUnitID INTEGER,
                    Rejected INTEGER,
                    UPbAnalysisCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalysisModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UPbAnalysisName COLLATE NOCASE),
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ReferenceID) REFERENCES "References"(ReferenceID)
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
                    FOREIGN KEY(RatioErrorFormatID) REFERENCES ErrorFormats(ErrorFormatID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(AgeErrorFormatID) REFERENCES ErrorFormats(ErrorFormatID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL, 
                    FOREIGN KEY(AgeUnitID) REFERENCES AgeUnits(AgeUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(AgeInterpretationID) REFERENCES AgeInterpretations(AgeInterpretationID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(ConcordanceFormatID) REFERENCES ConcordanceFormats(ConcordanceFormatID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(SpotSizeUnitID) REFERENCES DistanceUnits(DistanceUnitID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_UPB_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalysisContexts(
                    UPbAnalysisContextID INTEGER PRIMARY KEY,
                    ParentUPbAnalysisContextID INTEGER,
                    UPbAnalysisContextParentRow INTEGER,
                    UPbAnalysisContextName TEXT NOT NULL CHECK (UPbAnalysisContextName <> ''),
                    UPbAnalysisContextDescription TEXT, 
                    UPbAnalysisContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalysisContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UPbAnalysisContextName COLLATE NOCASE),
                    UNIQUE (ParentUPbAnalysisContextID, UPbAnalysisContextParentRow)
                    )'''

CREATE_UPBANALYSES_UPBANALYSISCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalyses_UPbAnalysisContexts(
                    UPbAnalysisID INTEGER NOT NULL,
                    UPbAnalysisContextID INTEGER NOT NULL,
                    UPbAnalyses_UPbAnalysisContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalyses_UPbAnalysisContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UPbAnalysisID, UPbAnalysisContextID),
                    FOREIGN KEY(UPbAnalysisID) REFERENCES UPbAnalyses(UPbAnalysisID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(UPbAnalysisContextID) REFERENCES UPbAnalysisContexts(UPbAnalysisContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_UPBANALYSES_REJECTIONREASONS_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalyses_RejectionReasons(
                    UPbAnalysisID INTEGER,
                    RejectionReasonID INTEGER,
                    UPbAnalyses_RejectionReasonsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalyses_RejectionReasonsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UPbAnalysisID, RejectionReasonID),
                    FOREIGN KEY(UPbAnalysisID) REFERENCES UPbAnalyses(UPbAnalysisID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(RejectionReasonID) REFERENCES RejectionReasons(RejectionReasonID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_UPBANALYSIS_METHOD_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalysisMethods(
                    UPbAnalysisMethodID INTEGER PRIMARY KEY,
                    ParentUPbAnalysisMethodID INTEGER,
                    UPbAnalysisMethodParentRow INTEGER,
                    UPbAnalysisMethodName TEXT NOT NULL CHECK (UPbAnalysisMethodName <> ''),
                    UPbAnalysisMethodDescription TEXT, 
                    UPbAnalysisMethodCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalysisMethodModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UPbAnalysisMethodName COLLATE NOCASE)
                    )'''

'''Commands to create tables and populate default tables'''


def create_tables(database=None) -> bool:
    """
    Connect to the database and execute the sql strings defined above to create the database tables.
    Only creates tables that do not already exist - does not overwrite existing tables.
    If the Ages table is empty, it will fill it from the Geologic timescale xml file.
    Populates the units, formats, and conversion tables.
    Uses the default database connection if no database is provided.
    :param database: QSqlDatabase instance to create tables in, if None uses the default connection
    :return: True for success, False for failure
    """
    logger_setup.get_logger().info('Creating database tables')
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)

    # Create the tables
    if not query.exec(CREATE_ABOUT_TABLE):
        logger_setup.get_logger().critical(f'Error creating About table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    if not query.exec('SELECT * FROM About'):
        logger_setup.get_logger().critical(f"Failed to query About table")
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
    else:
        if not query.next():  # No rows found
            # insert blank row into about
            if not query.exec(
                    f"INSERT INTO About VALUES (1, 'Name','Authors','','', '{settings.value('default_geocork_version')}','','CreatedBy',NULL,NULL)"):
                logger_setup.get_logger().debug(f"Failed to insert default values into About table")
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            else:
                logger_setup.get_logger().info('About table empty, populated with default values')
        else:
            logger_setup.get_logger().info('About table already populated, updating version info')
            if not query.exec(f"UPDATE About SET Version = '{settings.value('default_geocork_version')}' WHERE AboutID = 1"):
                logger_setup.get_logger().debug(f"Failed to update version in About table")
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')

    # Create unit and formats tables
    if not query.exec(CREATE_AGE_UNITS_TABLE):
        logger_setup.get_logger().critical(f'Error creating AgeUnits table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_CONCORDANCE_FORMATS_TABLE):
        logger_setup.get_logger().critical(f'Error creating ConcordanceFormats table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_DIRECTION_UNITS_TABLE):
        logger_setup.get_logger().critical(f'Error creating DirectionUnits table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_DISTANCE_UNITS_TABLE):
        logger_setup.get_logger().critical(f'Error creating DistanceUnits table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_ERROR_FORMATS_TABLE):
        logger_setup.get_logger().critical(f'Error creating ErrorFormats table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create conversion tables
    if not query.exec(CREATE_AGE_CONVERSIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating AgeConversions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_CONCORDANCE_CONVERSIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating ConcordanceConversions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_DISTANCE_CONVERSIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating DistanceConversions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_ERROR_CONVERSIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating ErrorConversions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create analysis tag tables
    if not query.exec(CREATE_INSTRUMENTS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Instruments table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_LAB_FACILITIES_TABLE):
        logger_setup.get_logger().critical(f'Error creating LabFacilities table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_REJECTION_REASONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating RejectionReasons table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_REFERENCES_TABLE):
        logger_setup.get_logger().critical(f'Error creating References table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_UPB_CONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating UPbAnalysisContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_UPBANALYSIS_METHOD_TABLE):
        logger_setup.get_logger().critical(f'Error creating UPbAnalysisMethods table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create spot tag tables
    if not query.exec(CREATE_SPOT_COMPOSITION_TABLE):
        logger_setup.get_logger().critical(f'Error creating SpotCompositions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SPOT_CONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating SpotContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create grain tag tables
    if not query.exec(CREATE_GRAIN_COMPOSITION_TABLE):
        logger_setup.get_logger().critical(f'Error creating GrainCompositions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_GRAIN_CONTEXTS_TABLE):
        logger_setup.get_logger().critical(f'Error creating GrainContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create aliquot tag tables
    if not query.exec(CREATE_ALIQUOT_CONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating AliquotContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create sample tag tables
    if not query.exec(CREATE_AGE_CONSTRAINTS_TABLE):
        logger_setup.get_logger().critical(f'Error creating AgeConstraints table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_AGE_INTERPRETATIONS_TABLE):  # Shared with upb analyses
        logger_setup.get_logger().critical(f'Error creating AgeInterpretations table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_AGE_SIGNATURES_TABLE):
        logger_setup.get_logger().critical(f'Error creating AgeSignatures table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_AGES_TABLE):
        logger_setup.get_logger().critical(f'Error creating Ages table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_COLUMNS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Columns table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_GPS_CONVERSIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating GPSConversions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_GPS_FORMATS_TABLE):
        logger_setup.get_logger().critical(f'Error creating GPSFormats table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_GPS_LOCATIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating GPSLocations table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_REGIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Regions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_ROCK_TYPES_TABLE):
        logger_setup.get_logger().critical(f'Error creating RockTypes table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLE_AGE_TABLE):
        logger_setup.get_logger().critical(f'Error creating SampleAges table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLE_CONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating SampleContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLEAGES_AGECONSTRAINTS_TABLE):
        logger_setup.get_logger().critical(f'Error creating SampleAges_AgeConstraints table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLEAGES_AGEINTERPRETATIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating SampleAges_AgeInterpretations table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLEAGES_REFERENCES_TABLE):
        logger_setup.get_logger().critical(f'Error creating SampleAges_References table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLING_METHODS_TABLE):
        logger_setup.get_logger().critical(f'Error creating SamplingMethods table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SETTINGS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Settings table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_UNITS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Units table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create sample item and analysis tables
    if not query.exec(CREATE_SAMPLES_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_ALIQUOTS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Aliquots table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SPOTS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Spots table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_GRAINS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Grains table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_UPBANALYSES_TABLE):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create many-to-many sample tables
    if not query.exec(CREATE_SAMPLES_AGESIGNATURES_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_AgeSignatures table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLES_REGIONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_Regions table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLES_ROCKTYPES_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_RockTypes table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLES_SAMPLEAGES_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_SampleAges table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLES_SAMPLECONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_SampleContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLES_SAMPLINGMETHODS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_SamplingMethods table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLES_SETTINGS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_Settings table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_SAMPLES_UNITS_TABLE):
        logger_setup.get_logger().critical(f'Error creating Samples_Units table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create many-to-many anliquot tables
    if not query.exec(CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating Aliquots_AliquotContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create many-to-many spot tables
    if not query.exec(CREATE_SPOTS_SPOTCONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating Spots_SpotContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create many-to-many grain tables
    if not query.exec(CREATE_GRAINS_GRAINCONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating Grains_GrainContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    # Create many-to-many analysis tables
    if not query.exec(CREATE_UPBANALYSES_UPBANALYSISCONTEXT_TABLE):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_UPbAnalysisContexts table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    if not query.exec(CREATE_UPBANALYSES_REJECTIONREASONS_TABLE):
        logger_setup.get_logger().critical(f'Error creating UPbAnalyses_RejectionReasons table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    if not query.exec(CREATE_FILTER_GROUPS_TABLE):
        logger_setup.get_logger().critical(f'Error creating FilterGroups table')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    logger_setup.get_logger().info('Successfully created all database tables')
    # Populate the tables
    if not populate_tables(database):
        return False

    logger_setup.get_logger().info('Successfully populated all database tables')
    return True


def update_schema(version: str, database: QtS.QSqlDatabase = None) -> bool:
    """
    Function to update the database schema to the latest version.
    :param version: Current version of the database schema. If None, defaults to 0.
    :param database: QSqlDatabase instance to use, if None the default database is used.
    :return: True for success, False for failure
    :rtype: bool
    """
    if database is None:
        database = QtS.QSqlDatabase()
    query = QtS.QSqlQuery(database)
    if version is None:
        version = 0
    if version == settings.value('default_geocork_version'):
        logger_setup.get_logger().info('Database schema is up to date')
        return True
    # else:
    #     dialog = QtW.QMessageBox()
    #     dialog.setIcon(QtW.QMessageBox.Icon.Information)
    #     dialog.setWindowTitle('Database Schema Update')
    #     dialog.setText(f'Database schema version {version} is not compatible with this version of GeoCork ({settings.value("default_geocork_version")}).\n\n'
    #                    f'Click OK to back up the database and update the schema to the latest version or cancel to abort.\n\n')
    #     dialog.setStandardButtons(QtW.QMessageBox.StandardButton.Ok | QtW.QMessageBox.StandardButton.Cancel)
    #     dialog.setDefaultButton(QtW.QMessageBox.StandardButton.Ok)
    #     ret = dialog.exec()
    #     if ret != QtW.QMessageBox.StandardButton.Ok:
    #         logger_setup.get_logger().warning('User aborted database schema update')
    #         return False
    #     # Create a backup of the database before updating the schema
    #

    if version == 'v1.0.0' or version == '1.0.0':
        # Update from version 1.0.0 to 1.1.0
        continue_messagebox = QMessageBox.information(None,
                                "Outdated GeoCORK Schema",
                                f"GeoCORK has tried to open an outdated database. The version loaded is v1.0.0 and this version of GeoCORK is {settings.value('default_geocork_version')}. \n \n"
                                f"Would you like to proceed with updating this database to the latest version? If not, use the GeoCORK version associated with this database. \n \n"
                                f"We will attempt to backup the database automatically, but we strongly recommend making your own backups",
                                buttons=
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                defaultButton=QMessageBox.StandardButton.No)

        if continue_messagebox == QMessageBox.StandardButton.No:
            logger_setup.get_logger().info('User rejected updating schema from v1.0.0 to v1.1.0')
            return False

        logger_setup.get_logger().info('Updating database schema from version v1.0.0 to v1.1.0')
        # Grain tables added automatically in Create_database.py
        # Add empty GrainID column to Spots table
        # Add UPbAnalysisName column to UPbAnalyses table and populate with SpotName

        backup_file = Database_manager.backup_database(database)

        if backup_file is None:
            logger_setup.get_logger().critical(f'Error updating database schema. Could not create backup file.')
            return False
        else:
            QMessageBox.information(None,
                "Information Critical",
                f"Successfully backed up the database to {backup_file}.\n Should there be any issues use that file to restore your data.",
                                        buttons=
            QMessageBox.StandardButton.Ok,
            defaultButton = QMessageBox.StandardButton.Ok)

        create_savepoint('before_schema_update')

        create_sql = CREATE_SPOTS_TABLE
        column_creation = create_sql.split(f'CREATE TABLE IF NOT EXISTS Spots')[1]
        if not query.exec(f'CREATE TABLE IF NOT EXISTS Spots_new{column_creation}'):
            logger_setup.get_logger().debug(f"Failed to create new Spots table")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_schema_update')
            return False

        # Copy data from old Spots table to new Spots table
        from Functions.Alter_database import get_columns
        query, virtual, stored, columns = get_columns('Spots_new', database)
        column_str = ', '.join(columns)
        insert_new_table = f'INSERT INTO Spots_new SELECT {column_str} FROM Spots'
        logger_setup.get_logger().info(f'Inserting into new table: Spots_new')
        if not query.exec(insert_new_table):
            logger_setup.get_logger().debug(f'Error inserting values into Spots_new table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_schema_update')
            return False

        # Close and reopen the database to avoid "database table is locked" errors
        if not database.commit():
            if 'no transaction is active' not in database.lastError().text():
                logger_setup.get_logger().critical(f"Error committing database")
                logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
                return False
        if not database.close():
            if 'no transaction is active' not in database.lastError().text():
                logger_setup.get_logger().critical(f"Error closing database")
                logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
                return False
        if not database.open():
            logger_setup.get_logger().critical(f"Error opening database")
            logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
            return False

        # Drop the original table
        drop_original_table = f'DROP TABLE IF EXISTS "Spots"'
        logger_setup.get_logger().info(f'Dropping original table: Spots')
        if not query.exec(drop_original_table):
            logger_setup.get_logger().critical(f'Error dropping original Spots table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            # rollback_savepoint('before_schema_update')
            return False
        logger_setup.get_logger().info(f'Successfully dropped original table: Spots')

        # Rename the new table to the original table name
        alter_table_qry = f'ALTER TABLE Spots_new RENAME TO "Spots"'
        logger_setup.get_logger().info(f'Altering table rename: Spots_new to Spots')
        if not query.exec(alter_table_qry):
            logger_setup.get_logger().critical(f'Error renaming Spots table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            # rollback_savepoint('before_schema_update')
            return False
        logger_setup.get_logger().info(f'Successfully altered table rename: Spots_new to Spots')

        # Create a dictionary of SpotID and SpotName from the Spots table
        spot_dict = {}
        update_names = []
        if not query.exec(f'SELECT SpotID, SpotName FROM Spots'):
            logger_setup.get_logger().debug(f'Error retrieving SpotID and SpotName from Spots table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return False
        while query.next():
            # Find any spots beginning with 'km001' case sensitive and add 16 in front of the name
            if query.value(1).startswith('km001'):
                spot_dict[query.value(0)] = '16' + query.value(1)
                update_names.append(query.value(0))
            else:
                spot_dict[query.value(0)] = query.value(1)

        for spot_id in update_names:
            if not query.exec(f'UPDATE Spots SET SpotName="{spot_dict[spot_id]}" WHERE SpotID={spot_id}'):
                logger_setup.get_logger().debug(f'Error updating SpotName in Spots table')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False

        # Add a new column to the UPbAnalyses table and populate it with the spot name corresponding to the SpotID already in the table
        create_savepoint('before_schema_update')
        if not query.exec(f'ALTER TABLE UPbAnalyses ADD COLUMN UPbAnalysisName TEXT'):
            logger_setup.get_logger().debug(f'Error adding UPbAnalysisName column to UPbAnalyses table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_schema_update')
            return False
        upb_spots = {}
        if not query.exec(f'SELECT UPbAnalysisID, SpotID FROM UPbAnalyses'):
            logger_setup.get_logger().debug(f'Error retrieving UPbAnalysisID and SpotID from UPbAnalyses table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_schema_update')
            return False
        while query.next():
            upb_spots[query.value(0)] = query.value(1)

        key_errors = 0
        missing_spots = 0
        added_spots = 0
        deleted_upb = []
        for upb_analysis_id, spot_id in upb_spots.items():
            try:
                spot_name = spot_dict[spot_id]
            except KeyError:
                key_errors += 1
                spot_name = None
            if spot_name:
                if not query.exec(f'UPDATE UPbAnalyses SET UPbAnalysisName="{spot_name}" WHERE UPbAnalysisID={upb_analysis_id}'):
                    logger_setup.get_logger().debug(f'Error updating UPbAnalysisName in UPbAnalyses table')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_schema_update')
                    return False
                added_spots += 1
                upb_spots[upb_analysis_id] = spot_name
                # print(f'Updated UPbAnalysisID {upb_analysis_id} with UPbAnalysisName {spot_name}')
            else:
                # Delete orphaned UPbAnalysis with no matching SpotID
                if not query.exec(f'DELETE FROM UPbAnalyses WHERE UPbAnalysisID={upb_analysis_id}'):
                    logger_setup.get_logger().debug(f'Error deleting orphaned UPbAnalysisID {upb_analysis_id} from UPbAnalyses table')
                    logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                    logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                    rollback_savepoint('before_schema_update')
                    return False
                logger_setup.get_logger().info(f'Deleted orphaned UPbAnalysisID {upb_analysis_id} with missing SpotID {spot_id}')
                missing_spots += 1
                deleted_upb.append(upb_analysis_id)
        logger_setup.get_logger().info(f'Successfully added UPbAnalysisName column to UPbAnalyses table')
        # Remove deleted analyses from the dictionary
        for deleted in deleted_upb:
            upb_spots.pop(deleted)

        if not query.exec(f'PRAGMA table_xinfo("UPbAnalyses")'):
            logger_setup.get_logger().debug(f"Failed to get columns for UPbAnalyses table")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_schema_update')
            return False
        columns = []
        while query.next():
            columns.append(query.value(1))
        if 'UPbAnalysisName' not in columns:
            logger_setup.get_logger().debug(f"Failed to add UPbAnalysisName column to UPbAnalyses table")
            rollback_savepoint('before_schema_update')
            return False

        # Create new UPbAnalyses table with new create statement
        create_sql = CREATE_UPBANALYSES_TABLE
        column_creation = create_sql.split(f'CREATE TABLE IF NOT EXISTS UPbAnalyses')[1]
        if not query.exec(f'CREATE TABLE IF NOT EXISTS UPbAnalyses_new{column_creation}'):
            logger_setup.get_logger().debug(f"Failed to create new UPbAnalyses table")
            logger_setup.get_logger().debug(f"Error: {query.lastError().text()}")
            logger_setup.get_logger().debug(f"SQL query: {query.lastQuery()}")
            rollback_savepoint('before_schema_update')
            return False

        # Copy data from old UPbAnalyses table to new UPbAnalyses table
        from Functions.Alter_database import get_columns
        query, virtual, stored, columns = get_columns('UPbAnalyses_new', database)
        column_str = ', '.join(columns)
        insert_new_table = f'INSERT INTO UPbAnalyses_new SELECT {column_str} FROM UPbAnalyses'
        logger_setup.get_logger().info(f'Inserting into new table: UPbAnalyses_new')
        if not query.exec(insert_new_table):
            logger_setup.get_logger().debug(f'Error inserting values into UPbAnalyses_new table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            rollback_savepoint('before_schema_update')
            return False
        # for upb_analysis in range(len(upb_spots)):
        #     insert_new_table = f'INSERT INTO UPbAnalyses_new SELECT {column_str} FROM UPbAnalyses WHERE UPbAnalysisID={list(upb_spots.keys())[upb_analysis]}'
        #     logger_setup.get_logger().info(f'Inserting {list(upb_spots.keys())[upb_analysis]} into new table: UPbAnalyses_new')
        #     if not query.exec(insert_new_table):
        #         logger_setup.get_logger().critical(f'Error inserting UPbAnalyses_new table')
        #         logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        #         logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        #         rollback_savepoint('before_schema_update')
        #         return False
        logger_setup.get_logger().info(f'Successfully inserted into new table: UPbAnalyses_new')
        release_savepoint('before_schema_update')

        # Close and reopen the database to avoid "database table is locked" errors
        if not database.commit():
            if 'no transaction is active' not in database.lastError().text():
                logger_setup.get_logger().critical(f"Error committing database")
                logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
                return False
        if not database.close():
            if 'no transaction is active' not in database.lastError().text():
                logger_setup.get_logger().critical(f"Error closing database")
                logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
                return False
        if not database.open():
            logger_setup.get_logger().critical(f"Error opening database")
            logger_setup.get_logger().debug(f'Error: {database.lastError().text()}')
            return False

        # Drop the original table
        drop_original_table = f'DROP TABLE IF EXISTS "UPbAnalyses"'
        logger_setup.get_logger().info(f'Dropping original table: UPbAnalyses')
        if not query.exec(drop_original_table):
            logger_setup.get_logger().critical(f'Error dropping original UPbAnalyses table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            # rollback_savepoint('before_schema_update')
            return False
        logger_setup.get_logger().info(f'Successfully dropped original table: UPbAnalyses')

        # Rename the new table to the original table name
        alter_table_qry = f'ALTER TABLE UPbAnalyses_new RENAME TO "UPbAnalyses"'
        logger_setup.get_logger().info(f'Altering table rename: UPbAnalyses_new to UPbAnalyses')
        if not query.exec(alter_table_qry):
            logger_setup.get_logger().critical(f'Error renaming UPbAnalyses table')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            # rollback_savepoint('before_schema_update')
            return False
        logger_setup.get_logger().info(f'Successfully altered table rename: UPbAnalyses_new to UPbAnalyses')
    release_savepoint('before_schema_update')
    return True

def populate_tables(database=None) -> bool:
    """
    Populate the default values in the static database tables. Uses the default database connection if no database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """
    # Populate the age units table during initiation
    logger_setup.get_logger().info('Populating tables')
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    sql = 'SELECT * FROM AgeUnits'
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error getting AgeUnits')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    out = []
    while query.next(): out.append(query.value(1))
    if not out or len(out) != SQLUtils.age_units:  # if there is no output, the table is empty
        if not populate_age_units(database):  # populate it
            return False
    if not populate_age_conversions(database):
        return False

    # Populate the concordance format table during initiation
    sql = '''SELECT * FROM ConcordanceFormats'''
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error getting ConcordanceFormats')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    out = []
    while query.next(): out.append(query.value(1))
    if not out or len(out) != len(SQLUtils.concordance_formats):  # if there is no output, the table is empty
        if not populate_concordance_formats(database):  # populate it
            return False
    if not populate_concordance_conversions(database):
        return False

    # Populate the direction unit table during initiation
    sql = '''SELECT * FROM DirectionUnits'''
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error getting DirectionUnits')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    out = []
    while query.next(): out.append(query.value(1))
    if not out or len(out) != len(SQLUtils.direction_units):  # if there is no output, the table is empty
        if not populate_direction_units(database):  # populate it
            return False

    # Populate the distance unit table during initiation
    sql = '''SELECT * FROM DistanceUnits'''
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error getting DistanceUnits')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    out = []
    while query.next(): out.append(query.value(1))
    if not out or len(out) != len(SQLUtils.distance_units):  # if there is no output, the table is empty
        if not populate_distance_units(database):  # populate it
            return False
    if not populate_distance_conversions(database):
        return False

    # Populate the error format table during initiation
    sql = '''SELECT * FROM ErrorFormats'''
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error getting ErrorFormats')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    out = []
    while query.next(): out.append(query.value(1))
    if not out or len(out) != len(SQLUtils.error_formats):  # if there is no output, the table is empty
        if not populate_error_formats(database):
            return False
    if not populate_error_conversions(database):
        return False

    # Populate the gps format table during initiation
    sql = '''SELECT * FROM GPSFormats'''
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error getting GPSFormats')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    out = []
    while query.next(): out.append(query.value(2))
    if not out or len(out) != len(SQLUtils.gps_formats):  # if there is no output, the table is empty
        populate_gps_formats(database)
    sql = 'DELETE FROM GPSFormatConversions'
    if not query.exec(sql):
        if 'database is locked' in query.lastError().text():
            logger_setup.get_logger().critical(f'The database is currently locked. Make sure it is not in use elsewhere.')
            return False
        else:
            logger_setup.get_logger().critical(f'Error resetting GPSFormatConversions')
            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return False
    if not populate_gps_conversions(database):
        return False

    # Populate the age table during initiation
    sql = '''SELECT * FROM Ages'''
    if query.exec(sql):
        out = []
        while query.next(): out.append(query.value(3))
        if not out:  # if there is no output, the table is empty
            if not populate_ages(database):  # populate it
                return False
    else:
        logger_setup.get_logger().critical(f'Error selecting all rows from AgeUnits')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False

    return True


def populate_age_units(database=None) -> bool:
    """
    Connect to the database and add the default age units. Uses the default database connection if no database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """

    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    # Begin by deleting all rows in the table to allow for a reset if things get changed
    age_units = SQLUtils.age_units
    for unit in age_units:
        sql = f'''INSERT INTO AgeUnits(AgeUnitName, AgeUnitAbbreviation) VALUES("{unit[0]}","{unit[1]}")'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical(f'Error populating AgeUnits')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False

    return True


def populate_age_conversions(database=None) -> bool:
    """
    Connect to the database and add the default age unit conversions. Uses the default database connection if no database
    is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """
    if database is None:
        query = QtS.QSqlQuery()
        age_conversion_model = QtS.QSqlTableModel()
    else:
        query = QtS.QSqlQuery(database)
        database: QtS.QSqlDatabase
        age_conversion_model = QtS.QSqlTableModel(db=database)
    age_units = SQLUtils.age_units
    age_conversion_model.setTable('AgeUnitConversions')
    age_conversion_model.select()
    while age_conversion_model.canFetchMore():
        age_conversion_model.fetchMore()
    for unit1 in range(len(age_units)):
        for unit2 in range(len(age_units)):
            if unit2 > unit1:
                conversion1to2 = f'x*{age_units[unit1][2]}/{age_units[unit2][2]}'
                conversion2to1 = f'x*{age_units[unit2][2]}/{age_units[unit1][2]}'
                age_conversion_model.setFilter(
                    f'FromAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit1][1]}") AND ToAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit2][1]}")')
                if age_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO AgeUnitConversions(FromAgeUnitID, ToAgeUnitID, AgeUnitConversionCalculation)
                                    VALUES((SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit1][1]}"),(SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit2][1]}"),"{conversion1to2}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical(f'Error populating AgeUnitConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = age_conversion_model.record(0).value('AgeUnitConversionCalculation')
                    if current_conversion != conversion1to2:
                        sql = f'''UPDATE AgeUnitConversions SET AgeUnitConversionCalculation = "{conversion1to2}"
                                    WHERE FromAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit1][1]}") AND ToAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit2][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical(f'Error populating AgeUnitConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
                age_conversion_model.setFilter(
                    f'FromAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit2][1]}") AND ToAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit1][1]}")')
                if age_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO AgeUnitConversions(FromAgeUnitID, ToAgeUnitID, AgeUnitConversionCalculation)
                                    VALUES((SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit2][1]}"),(SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit1][1]}"),"{conversion2to1}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical(f'Error populating AgeUnitConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = age_conversion_model.record(0).value('AgeUnitConversionCalculation')
                    if current_conversion != conversion2to1:
                        sql = f'''UPDATE AgeUnitConversions SET AgeUnitConversionCalculation = "{conversion2to1}"
                                    WHERE FromAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit2][1]}") AND ToAgeUnitID = (SELECT AgeUnitID FROM AgeUnits WHERE AgeUnitAbbreviation = "{age_units[unit1][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical(f'Error populating AgeUnitConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
    return True


def populate_concordance_formats(database=None) -> bool:
    """
    Connect to the database and add the default concordance formats. Uses the default database connection if no database
    is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """

    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    concordance_formats = SQLUtils.concordance_formats
    for concordance_format in concordance_formats:
        sql = f'''INSERT INTO ConcordanceFormats(ConcordanceFormatName, ConcordanceFormatAbbreviation, ConcordanceFormatDescription)
                                VALUES("{concordance_format[0]}","{concordance_format[1]}","{concordance_format[2]}")'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical('Error populating ConcordanceFormats')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False
    return True


def populate_concordance_conversions(database=None) -> bool:
    """
    Connect to the database and add the default concordance format conversions. Uses the default database connection if no
    database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """
    if database is None:
        query = QtS.QSqlQuery()
        concordance_conversion_model = QtS.QSqlTableModel()
    else:
        query = QtS.QSqlQuery(database)
        concordance_conversion_model = QtS.QSqlTableModel(db=database)
    concordance_formats = SQLUtils.concordance_formats
    concordance_conversion_model.setTable('ConcordanceFormatConversions')
    concordance_conversion_model.select()
    while concordance_conversion_model.canFetchMore():
        concordance_conversion_model.fetchMore()
    for format1 in range(len(concordance_formats)):
        for format2 in range(len(concordance_formats)):
            if format2 > format1:
                # print(f'Adding conversion for {concordance_formats[format1][1]} to {concordance_formats[format2][1]}')
                if concordance_formats[format1][1] == 'MinSegDis' or concordance_formats[format2][1] == 'MinSegDis':
                    # One format is MinSegDis and the other is not. There is no simple conversion, so use a placeholder
                    conversion1to2 = '-'
                    conversion2to1 = '-'
                elif concordance_formats[format1][1][-1] == '%' and concordance_formats[format2][1][-1] == '%':
                    # Both formats are percent
                    conversion1to2 = '100-x'
                    conversion2to1 = '100-x'
                elif concordance_formats[format1][1][-1] != '%' and concordance_formats[format2][1][-1] != '%':
                    # Both formats are ratio
                    conversion1to2 = '1-x'
                    conversion2to1 = '1-x'
                elif concordance_formats[format1][1][-1] != '%':
                    # First format is ratio and second format is percent
                    if (concordance_formats[format1][1] == 'Con' and concordance_formats[format2][1] == 'Con%') or (
                            concordance_formats[format1][1] == 'Dis' and concordance_formats[format2][1] == 'Dis%'):
                        # Both formats are concordance or discordance
                        conversion1to2 = 'x*100'
                        conversion2to1 = 'x/100'
                    elif concordance_formats[format1][1] == 'Con' and concordance_formats[format2][1] == 'Dis%':
                        # First format is concordance ratio and second format is discordance percent
                        conversion1to2 = '100*(1-x)'
                        conversion2to1 = '1-(x/100)'
                elif concordance_formats[format1][1][-1] == '%':
                    # First format is percent and second format is ratio
                    if (concordance_formats[format1][1] == 'Con%' and concordance_formats[format2][1] == 'Dis'):
                        # First format is concordance percent and second format is discordance ratio
                        conversion1to2 = '1-(x/100)'
                        conversion2to1 = '100*(1-x)'
                concordance_conversion_model.setFilter(
                    f'FromConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format1][1]}") AND ToConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format2][1]}")')
                if concordance_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO ConcordanceFormatConversions(FromConcordanceFormatID, ToConcordanceFormatID, ConcordanceFormatConversionCalculation)
                                                            VALUES((SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format1][1]}"),(SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format2][1]}"),"{conversion1to2}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical('Error populating ConcordanceFormatConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = concordance_conversion_model.record(0).value(
                        'ConcordanceFormatConversionCalculation')
                    if current_conversion != conversion1to2:
                        sql = f'''UPDATE ConcordanceFormatConversions SET ConcordanceFormatConversionCalculation = "{conversion1to2}"
                                                            WHERE FromConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format1][1]}") AND ToConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format2][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical('Error populating ConcordanceFormatConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
                concordance_conversion_model.setFilter(
                    f'FromConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format2][1]}") AND ToConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format1][1]}")')
                if concordance_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO ConcordanceFormatConversions(FromConcordanceFormatID, ToConcordanceFormatID, ConcordanceFormatConversionCalculation)
                                                            VALUES((SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format2][1]}"),(SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format1][1]}"),"{conversion2to1}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical('Error populating ConcordanceFormatConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = concordance_conversion_model.record(0).value(
                        'ConcordanceFormatConversionCalculation')
                    if current_conversion != conversion2to1:
                        sql = f'''UPDATE ConcordanceFormatConversions SET ConcordanceFormatConversionCalculation = "{conversion2to1}"
                                                            WHERE FromConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format2][1]}") AND ToConcordanceFormatID = (SELECT ConcordanceFormatID FROM ConcordanceFormats WHERE ConcordanceFormatAbbreviation = "{concordance_formats[format1][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical('Error populating ConcordanceFormatConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
    return True


def populate_direction_units(database=None) -> bool:
    """
    Connect to the database and add the default direction units. Uses the default database connection if no database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    # Begin by deleting all rows in the table to allow for a reset if things get changed
    direction_units = SQLUtils.direction_units
    for unit in direction_units:
        sql = f'''INSERT INTO DirectionUnits(DirectionUnitName, DirectionUnitAbbreviation, DirectionUnitAbbreviation)
                                VALUES("{unit[0]}", "{unit[1]}", "{unit[2]}")'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical('Error populating DirectionUnits')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False
    return True


def populate_distance_units(database=None) -> bool:
    """
    Connect to the database and add the default distance units. Uses the default database connection if no database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """

    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    # International standard foot is 0.3048 meters exactly
    distance_units = SQLUtils.distance_units
    for unit in distance_units:
        sql = f'''INSERT INTO DistanceUnits(DistanceUnitName, DistanceUnitAbbreviation)
                                    VALUES("{unit[0]}","{unit[1]}")'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical('Error populating DistanceUnits')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False
    return True


def populate_distance_conversions(database=None) -> bool:
    """
    Connect to the database and add the default distance unit conversions. Uses the default database connection if no database
    is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """
    if database is None:
        query = QtS.QSqlQuery()
        distance_conversion_model = QtS.QSqlTableModel()
    else:
        query = QtS.QSqlQuery(database)
        distance_conversion_model = QtS.QSqlTableModel(db=database)
    distance_units = SQLUtils.distance_units
    distance_conversion_model.setTable('DistanceUnitConversions')
    distance_conversion_model.select()
    while distance_conversion_model.canFetchMore():
        distance_conversion_model.fetchMore()
    # International standard foot is 0.3048 meters exactly
    m_per_ft = 0.3048
    for unit1 in range(len(distance_units)):
        for unit2 in range(len(distance_units)):
            if unit2 > unit1:
                if (distance_units[unit1][1][-1] == 'm' and distance_units[unit2][1][-1] == 'm') or (
                        distance_units[unit1][1][-1] != 'm' and distance_units[unit2][1][-1] != 'm'):
                    # Both units are the same format
                    conversion1to2 = f'x*{distance_units[unit1][2]}/{distance_units[unit2][2]}'
                    conversion2to1 = f'x*{distance_units[unit2][2]}/{distance_units[unit1][2]}'
                elif distance_units[unit1][1][-1] == 'm':
                    # Unit 1 is metric and unit 2 is imperial
                    conversion1to2 = f'x*{distance_units[unit1][2]}/({m_per_ft}*{distance_units[unit2][2]})'
                    conversion2to1 = f'x*({distance_units[unit2][2]}*{m_per_ft})/{distance_units[unit1][2]}'
                else:
                    # Unit 1 is imperial and unit 2 is metric
                    conversion1to2 = f'x*({distance_units[unit1][2]}*{m_per_ft})/{distance_units[unit2][2]}'
                    conversion2to1 = f'x*{distance_units[unit2][2]}/({m_per_ft}*{distance_units[unit1][2]})'
                distance_conversion_model.setFilter(
                    f'FromDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit1][1]}") AND ToDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit2][1]}")')
                if distance_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO DistanceUnitConversions(FromDistanceUnitID, ToDistanceUnitID, DistanceUnitConversionCalculation)
                                            VALUES((SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit1][1]}"),(SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit2][1]}"),"{conversion1to2}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical('Error populating DistanceUnitConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = distance_conversion_model.record(0).value('DistanceUnitConversionCalculation')
                    if current_conversion != conversion1to2:
                        sql = f'''UPDATE DistanceUnitConversions SET DistanceUnitConversionCalculation = "{conversion1to2}"
                                            WHERE FromDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit1][1]}") AND ToDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit2][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical('Error populating DistanceUnitConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
                distance_conversion_model.setFilter(
                    f'FromDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit2][1]}") AND ToDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit1][1]}")')
                if distance_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO DistanceUnitConversions(FromDistanceUnitID, ToDistanceUnitID, DistanceUnitConversionCalculation)
                                            VALUES((SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit2][1]}"),(SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit1][1]}"),"{conversion2to1}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical('Error populating DistanceUnitConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = distance_conversion_model.record(0).value('DistanceUnitConversionCalculation')
                    if current_conversion != conversion2to1:
                        sql = f'''UPDATE DistanceUnitConversions SET DistanceUnitConversionCalculation = "{conversion2to1}"
                                            WHERE FromDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit2][1]}") AND ToDistanceUnitID = (SELECT DistanceUnitID FROM DistanceUnits WHERE DistanceUnitAbbreviation = "{distance_units[unit1][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical('Error populating DistanceUnitConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
    return True


def populate_error_formats(database=None) -> bool:
    """
    Connect to the database and add the default error formats. Uses the default database connection if no database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """

    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    error_formats = SQLUtils.error_formats
    for error_format in error_formats:
        sql = f'''INSERT INTO ErrorFormats(ErrorFormatName, ErrorFormatAbbreviation, ErrorFormatDescription)
                                    VALUES("{error_format[0]}","{error_format[1]}","{error_format[2]}")'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical('Error populating ErrorFormats')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False
    return True


def populate_error_conversions(database=None) -> bool:
    """
    Connect to the database and add the default error format conversions. Uses the default database connection if no database
    is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """
    if database is None:
        query = QtS.QSqlQuery()
        error_conversion_model = QtS.QSqlTableModel()
    else:
        query = QtS.QSqlQuery(database)
        error_conversion_model = QtS.QSqlTableModel(db=database)
    error_formats = SQLUtils.error_formats
    error_conversion_model.setTable('ErrorFormatConversions')
    error_conversion_model.select()
    while error_conversion_model.canFetchMore():
        error_conversion_model.fetchMore()
    for format1 in range(len(error_formats)):
        for format2 in range(len(error_formats)):
            if format2 > format1:
                if (error_formats[format1][1][-1] == '%' and error_formats[format2][1][-1] == '%') or (
                        error_formats[format1][1][-1] != '%' and error_formats[format2][1][-1] != '%'):
                    # Both are the same format, percent or absolute
                    conversion1to2 = 'x*2'
                    conversion2to1 = 'x/2'
                elif error_formats[format1][1][-1] != '%':
                    # First format is absolute and second format is percent
                    if (error_formats[format1][1][0] == '2' and error_formats[format2][1][0] == '2') or (
                            error_formats[format1][1][0] == '1' and error_formats[format2][1][0] == '1'):
                        # Both formats are 1 sigma or 2 sigma, x is the databased error and y is the value it is an error of
                        conversion1to2 = '(x/y)*100'
                        conversion2to1 = '(x/100)*y'
                    elif error_formats[format1][1][0] == '2' and error_formats[format2][1][0] == '1':
                        # 2 sigma absolute to 1 sigma percent, x is the databased error and y is the value it is an error of
                        conversion1to2 = '(x/y)*100/2'
                        # 1 sigma percent to 2 sigma absolute, x is the databased error and y is the value it is an error of
                        conversion2to1 = '(x/100)*2*y'
                    elif error_formats[format1][1][0] == '1' and error_formats[format2][1][0] == '2':
                        # 1 sigma ratio to 2 sigma percent, x is the databased error and y is the value it is an error of
                        conversion1to2 = '(x/y)*200'
                        # 2 sigma percent to 1 sigma absolute, x is the databased error and y is the value it is an error of
                        conversion2to1 = '(x/200)*y'

                error_conversion_model.setFilter(
                    f'FromErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format1][1]}") AND ToErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format2][1]}")')
                if error_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO ErrorFormatConversions(FromErrorFormatID, ToErrorFormatID, ErrorFormatConversionCalculation)
                                        VALUES((SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format1][1]}"),(SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format2][1]}"),"{conversion1to2}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical(f'Error populating ErrorFormatConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = error_conversion_model.record(0).value('ErrorFormatConversionCalculation')
                    if current_conversion != conversion1to2:
                        sql = f'''UPDATE ErrorFormatConversions SET ErrorFormatConversionCalculation = "{conversion1to2}"
                                        WHERE FromErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format1][1]}") AND ToErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format2][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical(f'Error populating ErrorFormatConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
                error_conversion_model.setFilter(
                    f'FromErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format2][1]}") AND ToErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format1][1]}")')
                if error_conversion_model.rowCount() == 0:
                    sql = f'''INSERT INTO ErrorFormatConversions(FromErrorFormatID, ToErrorFormatID, ErrorFormatConversionCalculation)
                                        VALUES((SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format2][1]}"),(SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format1][1]}"),"{conversion2to1}")'''
                    if not query.exec(sql):
                        logger_setup.get_logger().critical(f'Error populating ErrorFormatConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        return False
                else:
                    current_conversion = error_conversion_model.record(0).value('ErrorFormatConversionCalculation')
                    if current_conversion != conversion2to1:
                        sql = f'''UPDATE ErrorFormatConversions SET ErrorFormatConversionCalculation = "{conversion2to1}"
                                        WHERE FromErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format2][1]}") AND ToErrorFormatID = (SELECT ErrorFormatID FROM ErrorFormats WHERE ErrorFormatAbbreviation = "{error_formats[format1][1]}")'''
                        if not query.exec(sql):
                            logger_setup.get_logger().critical(f'Error populating ErrorFormatConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            return False
    return True


def populate_gps_formats(database=None) -> bool:
    """
    Populate the GPSFormats table with the default formats. Add text for code to run later for conversions. Uses the default
    database connection if no database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """

    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    gps_formats = SQLUtils.gps_formats
    for gps_format in gps_formats:
        sql = f'''INSERT INTO GPSFormats(GPSFormatName, GPSFormatAbbreviation, GPSFormatDescription)
                    VALUES("{gps_format[0]}","{gps_format[1]}","{gps_format[2]}")'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical('Error populating GPSFormats')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                return False
    return True


def populate_gps_conversions(database=None) -> bool:
    """
    Populate the GPSFormatConversions table with the conversions between GPS formats. Uses the default database connection
    if no database is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """
    if database is None:
        query = QtS.QSqlQuery()
        gps_format_model = QtS.QSqlTableModel()
        gps_conversion_model = QtS.QSqlTableModel()
    else:
        query = QtS.QSqlQuery(database)
        gps_format_model = QtS.QSqlTableModel(db=database)
        gps_conversion_model = QtS.QSqlTableModel(db=database)
    gps_formats = SQLUtils.gps_formats
    gps_format_model.setTable('GPSFormats')
    gps_format_model.select()
    while gps_format_model.canFetchMore():
        gps_format_model.fetchMore()
    gps_conversion_model.setTable('GPSFormatConversions')
    gps_conversion_model.select()
    while gps_conversion_model.canFetchMore():
        gps_conversion_model.fetchMore()
    for format1 in range(len(gps_formats)):
        for format2 in range(len(gps_formats)):
            if format1 == format2:
                if gps_formats[format1][1] == 'UTM':
                    conversion1to1 = '''converted = f"{GPSUTMZone}, {GPSUTME}m E, {GPSUTMN}m N"'''
                elif gps_formats[format1][1] == 'DD +/-':
                    conversion1to1 = '''converted = f"{GPSLatDeg}°, {GPSLonDeg}°"'''
                elif gps_formats[format1][1] == 'DD NSEW':
                    conversion1to1 = '''GPSLatDirection = GPS.convert_direction_id_to_abbreviation(GPSLatDirectionID)\nGPSLonDirection = GPS.convert_direction_id_to_abbreviation(GPSLonDirectionID)\nconverted = f"{GPSLatDeg}° {GPSLatDirection}, {GPSLonDeg}° {GPSLonDirection}"'''
                elif gps_formats[format1][1] == 'DDM +/-':
                    conversion1to1 = '''converted = f"{GPSLatDeg}°{GPSLatMin}', {GPSLonDeg}°{GPSLonMin}'"'''
                elif gps_formats[format1][1] == 'DDM NSEW':
                    conversion1to1 = '''GPSLatDirection = GPS.convert_direction_id_to_abbreviation(GPSLatDirectionID)\nGPSLonDirection = GPS.convert_direction_id_to_abbreviation(GPSLonDirectionID)\nconverted = f"{GPSLatDeg}°{GPSLatMin}' {GPSLatDirection}, {GPSLonDeg}°{GPSLonMin}' {GPSLonDirection}"'''
                elif gps_formats[format1][1] == 'DMS +/-':
                    conversion1to1 = '''converted = f"{GPSLatDeg}{deg_symbol}{GPSLatMin}{min_symbol}{GPSLatSec}{sec_symbol}, {GPSLonDeg}{deg_symbol}{GPSLonMin}{min_symbol}{GPSLonSec}{sec_symbol}"'''
                elif gps_formats[format1][1] == 'DMS NSEW':
                    conversion1to1 = '''GPSLatDirection = GPS.convert_direction_id_to_abbreviation(GPSLatDirectionID)\nGPSLonDirection = GPS.convert_direction_id_to_abbreviation(GPSLonDirectionID)\nconverted = f"{GPSLatDeg}{deg_symbol}{GPSLatMin}{min_symbol}{GPSLatSec}{sec_symbol} {GPSLatDirection}, {GPSLonDeg}{deg_symbol}{GPSLonMin}{min_symbol}{GPSLonSec}{sec_symbol} {GPSLonDirection}"'''
                gps_format_model.setFilter(f'GPSFormatAbbreviation = "{gps_formats[format1][1]}"')
                id_1 = gps_format_model.record(0).value('GPSFormatID')
                gps_conversion_model.setFilter(f'FromGPSFormatID = {id_1} AND ToGPSFormatID = {id_1}')
                if gps_conversion_model.rowCount() == 0:
                    query.prepare(
                        f'INSERT INTO GPSFormatConversions(FromGPSFormatID, ToGPSFormatID, GPSFormatConversionCalculation) '
                        'VALUES (?, ? ,?)')
                    query.bindValue(0, id_1)
                    query.bindValue(1, id_1)
                    query.bindValue(2, f'''{conversion1to1}''')
                    if not query.exec():
                        logger_setup.get_logger().critical('Error populating GPSFormatConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                        return False
                else:
                    current_conversion = gps_conversion_model.record(0).value('GPSFormatConversionCalculation')
                    if current_conversion != conversion1to1:
                        query.prepare(
                            f'UPDATE GPSFormatConversions SET GPSFormatConversionCalculation = ? '
                            'WHERE FromGPSFormatID = ? AND ToGPSFormatID = ?')
                        query.bindValue(0, f'''{conversion1to1}''')
                        query.bindValue(1, id_1)
                        query.bindValue(2, id_1)
                        if not query.exec():
                            logger_setup.get_logger().critical('Error populating GPSFormatConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                            return False
            if format2 > format1:
                if '+/-' in gps_formats[format1][1] and '+/-' in gps_formats[format2][1]:
                    # Both formats are positive/negative
                    if 'DD' in gps_formats[format1][1] and 'DDM' in gps_formats[format2][1]:
                        conversion1to2 = '''lat, lon = GPS.convert_dd_to_ddm([GPSLatDeg], [GPSLonDeg])\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                        conversion2to1 = '''lat, lon = GPS.convert_ddm_to_dd([GPSLatDeg, GPSLatMin], [GPSLonDeg, GPSLonMin])\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                    elif gps_formats[format1][1] == 'DD +/-' and gps_formats[format2][1] == 'DMS +/-':
                        conversion1to2 = '''lat, lon = GPS.convert_dd_to_dms([GPSLatDeg], [GPSLonDeg])\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                        conversion2to1 = '''lat, lon = GPS.convert_dms_to_dd([GPSLatDeg, GPSLatMin, GPSLatSec], [GPSLonDeg, GPSLonMin, GPSLonSec])\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                    elif gps_formats[format1][1] == 'DDM +/-' and gps_formats[format2][1] == 'DMS +/-':
                        conversion1to2 = '''lat, lon = GPS.convert_ddm_to_dms([GPSLatDeg, GPSLatMin], [GPSLonDeg, GPSLonMin])\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                        conversion2to1 = '''lat, lon = GPS.convert_dms_to_ddm([GPSLatDeg, GPSLatMin, GPSLatSec], [GPSLonDeg, GPSLonMin, GPSLonSec])\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                elif 'NSEW' in gps_formats[format1][1] and 'NSEW' in gps_formats[format2][1]:
                    # Both formats are directional, so convert to sign, then convert to the other format, then convert back to directional
                    convert_dd_to_sign = '''lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatDirectionID], [GPSLonDeg, GPSLonDirectionID])'''
                    convert_ddm_to_sign = '''lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonDirectionID])'''
                    convert_dms_to_sign = '''lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID])'''
                    convert_to_direction = '''lat, lon = GPS.convert_sign_to_direction(lat, lon)'''
                    if gps_formats[format1][1] == 'DD NSEW' and gps_formats[format2][1] == 'DDM NSEW':
                        conversion1to2 = f'''{convert_dd_to_sign}\nlat, lon = GPS.convert_dd_to_ddm(lat, lon)\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2]}, {lon[0]}°{lon[1]}{min_symbol} {lon[2]}"'''
                        conversion2to1 = f'''{convert_ddm_to_sign}\nlat, lon = GPS.convert_ddm_to_dd(lat, lon)\n{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1]}"'''
                    elif gps_formats[format1][1] == 'DD NSEW' and gps_formats[format2][1] == 'DMS NSEW':
                        conversion1to2 = f'''{convert_dd_to_sign}\nlat, lon = GPS.convert_dd_to_dms(lat, lon)\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3]}"'''
                        conversion2to1 = f'''{convert_dms_to_sign}\nlat, lon = GPS.convert_dms_to_dd(lat, lon)\n{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1]}"'''
                    elif gps_formats[format1][1] == 'DDM NSEW' and gps_formats[format2][1] == 'DMS NSEW':
                        conversion1to2 = f'''{convert_ddm_to_sign}\nlat, lon = GPS.convert_ddm_to_dms(lat, lon)\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2]}{sec_symbol} {lat[3]}, {lon[0]}° {lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3]}"'''
                        conversion2to1 = f'''{convert_dms_to_sign}\nlat, lon = GPS.convert_dms_to_ddm(lat, lon)\n{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2], {lon[0]}°{lon[1]}{min_symbol} {lon[2]}"'''
                elif '+/-' in gps_formats[format1][1] and 'NSEW' in gps_formats[format2][1]:
                    # First format is positive/negative and second format is directional
                    convert_dd_to_sign = 'lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatDirectionID], [GPSLonDeg, GPSLonDirectionID])'
                    convert_ddm_to_sign = 'lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonDirectionID])'
                    convert_dms_to_sign = 'lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID])'
                    convert_to_direction = 'lat, lon = GPS.convert_sign_to_direction(lat, lon)'
                    if gps_formats[format1][1] == 'DD +/-' and gps_formats[format2][1] == 'DD NSEW':
                        conversion1to2 = '''lat, lon = GPS.convert_sign_to_direction([GPSLatDeg], [GPSLonDeg])\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1]}"'''
                        conversion2to1 = f'''{convert_dd_to_sign}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                    elif gps_formats[format1][1] == 'DD +/-' and gps_formats[format2][1] == 'DDM NSEW':
                        conversion1to2 = f'''lat, lon = GPS.convert_dd_to_ddm([GPSLatDeg], [GPSLonDeg])\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2]}, {lon[0]}°{lon[1]}{min_symbol} {lon[2]}'"'''
                        conversion2to1 = f'''{convert_ddm_to_sign}\nlat, lon = GPS.convert_ddm_to_dd(lat, lon)'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                    elif gps_formats[format1][1] == 'DD +/-' and gps_formats[format2][1] == 'DMS NSEW':
                        conversion1to2 = f'''lat, lon = GPS.convert_dd_to_dms([GPSLatDeg], [GPSLonDeg])\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3]}"'''
                        conversion2to1 = f'''{convert_dms_to_sign}\nlat, lon = GPS.convert_dms_to_dd(lat, lon)'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                    elif gps_formats[format1][1] == 'DDM +/-' and gps_formats[format2][1] == 'DD NSEW':
                        conversion1to2 = f'''lat, lon = GPS.convert_ddm_to_dd([GPSLatDeg, GPSLatMin], [GPSLonDeg, GPSLonMin])\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1]}"'''
                        conversion2to1 = f'''{convert_dd_to_sign}\nlat, lon = GPS.convert_dd_to_ddm(lat, lon)'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                    elif gps_formats[format1][1] == 'DDM +/-' and gps_formats[format2][1] == 'DDM NSEW':
                        conversion1to2 = '''lat, lon = GPS.convert_sign_to_direction([GPSLatDeg, GPSLatMin], [GPSLonDeg, GPSLonMin])\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2]}, {lon[0]}°{lon[1]}{min_symbol} {lon[2]}'"'''
                        conversion2to1 = f'''{convert_ddm_to_sign}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                    elif gps_formats[format1][1] == 'DDM +/-' and gps_formats[format2][1] == 'DMS NSEW':
                        conversion1to2 = f'''lat, lon = GPS.convert_ddm_to_dms([GPSLatDeg, GPSLatMin], [GPSLonDeg, GPSLonMin])\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3]}"'''
                        conversion2to1 = f'''{convert_dms_to_sign}\nlat, lon = GPS.convert_dms_to_ddm(lat, lon)'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                    elif gps_formats[format1][1] == 'DMS +/-' and gps_formats[format2][1] == 'DD NSEW':
                        conversion1to2 = f'''lat, lon = GPS.convert_dms_to_dd([GPSLatDeg, GPSLatMin, GPSLatSec], [GPSLonDeg, GPSLonMin, GPSLonSec])\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1]}"'''
                        conversion2to1 = f'''{convert_dd_to_sign}\nlat, lon = GPS.convert_dd_to_dms(lat, lon)'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                    elif gps_formats[format1][1] == 'DMS +/-' and gps_formats[format2][1] == 'DDM NSEW':
                        conversion1to2 = f'''lat, lon = GPS.convert_dms_to_ddm([GPSLatDeg, GPSLatMin, GPSLatSec], [GPSLonDeg, GPSLonMin, GPSLonSec])\n{convert_to_direction}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2], {lon[0]}°{lon[1]}{min_symbol} {lon[2]}"'''
                        conversion2to1 = f'''{convert_ddm_to_sign}\nlat, lon = GPS.convert_ddm_to_dms(lat, lon)'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                    elif gps_formats[format1][1] == 'DMS +/-' and gps_formats[format2][1] == 'DMS NSEW':
                        conversion1to2 = '''lat, lon = GPS.convert_sign_to_direction([GPSLatDeg, GPSLatMin, GPSLatSec], [GPSLonDeg, GPSLonMin, GPSLonSec])\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3]}"'''
                        conversion2to1 = f'''{convert_dms_to_sign}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                elif 'NSEW' in gps_formats[format1][1] and '+/-' in gps_formats[format2][1]:
                    # First format is directional and second format is positive/negative
                    convert_dd_to_sign = 'lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatDirectionID], [GPSLonDeg, GPSLonDirectionID])'
                    convert_ddm_to_sign = 'lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonDirectionID])'
                    convert_dms_to_sign = 'lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID])'
                    convert_to_direction = 'lat, lon = GPS.convert_sign_to_direction(lat, lon)'
                    if gps_formats[format1][1] == 'DD NSEW' and gps_formats[format2][1] == 'DD +/-':
                        conversion1to2 = f'''{convert_dd_to_sign}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                        conversion2to1 = '''lat, lon = GPS.convert_sign_to_direction([GPSLatDeg], [GPSLonDeg])\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1}"'''
                    elif gps_formats[format1][1] == 'DD NSEW' and gps_formats[format2][1] == 'DDM +/-':
                        conversion1to2 = f'''{convert_dd_to_sign}\nlat, lon = GPS.convert_dd_to_ddm(lat, lon)'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                        conversion2to1 = f'''lat, lon = GPS.convert_ddm_to_dd(lat, lon)\n{convert_dd_to_sign}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1]}"'''
                    elif gps_formats[format1][1] == 'DD NSEW' and gps_formats[format2][1] == 'DMS +/-':
                        conversion1to2 = f'''{convert_dd_to_sign}\nlat, lon = GPS.convert_dd_to_dms(lat, lon)'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                        conversion2to1 = f'''lat, lon = GPS.convert_dms_to_dd(lat, lon)\n{convert_dd_to_sign}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1}"'''
                    elif gps_formats[format1][1] == 'DDM NSEW' and gps_formats[format2][1] == 'DD +/-':
                        conversion1to2 = f'''{convert_ddm_to_sign}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                        conversion2to1 = f'''lat, lon = GPS.convert_dd_to_ddm(lat, lon)\n{convert_ddm_to_sign}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2]}, {lon[0]}°{lon[1]}{min_symbol} {lon[2]}"'''
                    elif gps_formats[format1][1] == 'DDM NSEW' and gps_formats[format2][1] == 'DDM +/-':
                        conversion1to2 = f'''{convert_ddm_to_sign}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                        conversion2to1 = f'''{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2]}, {lon[0]}°{lon[1]}{min_symbol} {lon[2]}'"'''
                    elif gps_formats[format1][1] == 'DDM NSEW' and gps_formats[format2][1] == 'DMS +/-':
                        conversion1to2 = f'''{convert_ddm_to_sign}\nlat, lon = GPS.convert_ddm_to_dms(lat, lon)'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                        conversion2to1 = f'''lat, lon = GPS.convert_dms_to_ddm([GPSLatDeg, GPSLatMin, GPSLatSec], [GPSLonDeg, GPSLonMin, GPSLonSec])\n{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2], {lon[0]}°{lon[1]}{min_symbol} {lon[2]}"'''
                    elif gps_formats[format1][1] == 'DMS NSEW' and gps_formats[format2][1] == 'DD +/-':
                        conversion1to2 = f'''{convert_dms_to_sign}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                        conversion2to1 = f'''lat, lon = GPS.convert_dd_to_dms(lat, lon)\n{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3}"'''
                    elif gps_formats[format1][1] == 'DMS NSEW' and gps_formats[format2][1] == 'DDM +/-':
                        conversion1to2 = f'''{convert_dms_to_sign}\nlat, lon = GPS.convert_dms_to_ddm(lat, lon)'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}, {lon[0]}°{lon[1]}{min_symbol}"'''
                        conversion2to1 = f'''lat, lon = GPS.convert_ddm_to_dms([GPSLatDeg, GPSLatMin], [GPSLonDeg, GPSLonMin])\n{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3}"'''
                    elif gps_formats[format1][1] == 'DMS NSEW' and gps_formats[format2][1] == 'DMS +/-':
                        conversion1to2 = f'''{convert_dms_to_sign}'''
                        conversion1to2 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                        conversion2to1 = f'''{convert_to_direction}'''
                        conversion2to1 += '''\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3}"'''
                elif '+/-' in gps_formats[format1][1] and 'UTM' in gps_formats[format2][1]:
                    # First format is positive/negative and second format is UTM
                    if gps_formats[format1][1] == 'DD +/-' and gps_formats[format2][1] == 'UTM':
                        conversion1to2 = '''UTMN, UTME, zone_txt = GPS.convert_dd_to_utm([GPSLatDeg], [GPSLonDeg])\nconverted = f"{zone_txt}, {UTME}m E, {UTMN}m N"'''
                        conversion2to1 = '''lat, lon = GPS.convert_utm_to_dd(GPSUTMZone, GPSUTME, GPSUTMN)\nconverted = f"{lat[0]}°, {lon[0]}°"'''
                    elif gps_formats[format1][1] == 'DDM +/-' and gps_formats[format2][1] == 'UTM':
                        conversion1to2 = '''lat, lon = GPS.convert_ddm_to_dd([GPSLatDeg, GPSLatMin], [GPSLonDeg, GPSLonMin])\nlat, lon = GPS.convert_dd_to_utm(lat, lon)\nUTMN, UTME, zone_txt = GPS.convert_dd_to_utm(lat, lon)\nconverted = f"{zone_txt}, {UTME}m E, {UTMN}m N"'''
                        conversion2to1 = '''lat, lon = GPS.convert_utm_to_dd(GPSUTMZone, GPSUTME, GPSUTMN)\nlat, lon = GPS.convert_dd_to_ddm(lat, lon)\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lon[0]}°{lon[1]}{min_symbol}"'''
                    elif gps_formats[format1][1] == 'DMS +/-' and gps_formats[format2][1] == 'UTM':
                        conversion1to2 = '''lat, lon = GPS.convert_dms_to_dd([GPSLatDeg, GPSLatMin, GPSLatSec], [GPSLonDeg, GPSLonMin, GPSLonSec])\nUTMN, UTME, zone_txt = GPS.convert_dd_to_utm(lat, lon)\nconverted = f"{zone_txt}, {UTME}m E, {UTMN}m N"'''
                        conversion2to1 = '''lat, lon = GPS.convert_utm_to_dd(GPSUTMZone, GPSUTME, GPSUTMN)\nlat, lon = GPS.convert_dd_to_dms(lat, lon)\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol}"'''
                elif 'NSEW' in gps_formats[format1][1] and 'UTM' in gps_formats[format2][1]:
                    # First format is directional and second format is UTM
                    if gps_formats[format1][1] == 'DD NSEW' and gps_formats[format2][1] == 'UTM':
                        conversion1to2 = '''lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatDirectionID], [GPSLonDeg, GPSLonDirectionID])\nUTMN, UTME, zone_txt = GPS.convert_dd_to_utm(lat, lon)\nconverted = f"{zone_txt}, {UTME}m E, {UTMN}m N"'''
                        conversion2to1 = '''lat, lon = GPS.convert_utm_to_dd(GPSUTMZone, GPSUTME, GPSUTMN)\nlat, lon = GPS.convert_sign_to_direction(lat, lon)\nconverted = f"{lat[0]}° {lat[1]}, {lon[0]}° {lon[1]}"'''
                    elif gps_formats[format1][1] == 'DDM NSEW' and gps_formats[format2][1] == 'UTM':
                        conversion1to2 = '''lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonDirectionID])\nlat, lon = GPS.convert_ddm_to_dd(lat, lon)\nUTMN, UTME, zone_txt = GPS.convert_dd_to_utm(lat, lon)\nconverted = f"{zone_txt}, {UTME}m E, {UTMN}m N"'''
                        conversion2to1 = '''lat, lon = GPS.convert_utm_to_dd(GPSUTMZone, GPSUTME, GPSUTMN)\nlat, lon = GPS.convert_dd_to_ddm(lat, lon)\nlat, lon = GPS.convert_sign_to_direction(lat, lon)\nconverted = f"{lat[0]}°{lat[1]}{min_symbol} {lat[2]}, {lon[0]}°{lon[1]}{min_symbol} {lon[2]}'"'''
                    elif gps_formats[format1][1] == 'DMS NSEW' and gps_formats[format2][1] == 'UTM':
                        conversion1to2 = '''lat, lon = GPS.convert_direction_to_sign([GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID], [GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID])\nlat, lon = GPS.convert_dms_to_dd(lat, lon)\nUTMN, UTME, zone_txt = GPS.convert_dd_to_utm(lat, lon)\nconverted = f"{zone_txt}, {UTME}m E, {UTMN}m N"'''
                        conversion2to1 = '''lat, lon = GPS.convert_utm_to_dd(GPSUTMZone, GPSUTME, GPSUTMN)\nlat, lon = GPS.convert_dd_to_dms(lat, lon)\nlat, lon = GPS.convert_sign_to_direction(lat, lon)\nconverted = f"{lat[0]}°{lat[1]}{min_symbol}{lat[2]}{sec_symbol} {lat[3]}, {lon[0]}°{lon[1]}{min_symbol}{lon[2]}{sec_symbol} {lon[3]}"'''
                gps_format_model.setFilter(f'GPSFormatAbbreviation = "{gps_formats[format1][1]}"')
                id_1 = gps_format_model.record(0).value('GPSFormatID')
                gps_format_model.setFilter(f'GPSFormatAbbreviation = "{gps_formats[format2][1]}"')
                id_2 = gps_format_model.record(0).value('GPSFormatID')
                gps_conversion_model.setFilter(f'FromGPSFormatID = {id_1} AND ToGPSFormatID = {id_2}')
                if gps_conversion_model.rowCount() == 0:
                    query.prepare(
                        f'INSERT INTO GPSFormatConversions(FromGPSFormatID, ToGPSFormatID, GPSFormatConversionCalculation) '
                        'VALUES (?, ? ,?)')
                    query.bindValue(0, id_1)
                    query.bindValue(1, id_2)
                    query.bindValue(2, f'''{conversion1to2}''')
                    if not query.exec():
                        logger_setup.get_logger().critical('Error populating GPSFormatConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                        return False
                else:
                    current_conversion = gps_conversion_model.record(0).value('GPSFormatConversionCalculation')
                    if current_conversion != conversion1to2:
                        query.prepare(f'UPDATE GPSFormatConversions SET GPSFormatConversionCalculation = ? '
                                      'WHERE FromGPSFormatID = ? AND ToGPSFormatID = ?')
                        query.bindValue(0, f'''{conversion1to2}''')
                        query.bindValue(1, id_1)
                        query.bindValue(2, id_2)
                        if not query.exec():
                            logger_setup.get_logger().critical('Error populating GPSFormatConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                            return False
                gps_conversion_model.setFilter(f'FromGPSFormatID = {id_2} AND ToGPSFormatID = {id_1}')
                if gps_conversion_model.rowCount() == 0:
                    query.prepare(
                        f'INSERT INTO GPSFormatConversions(FromGPSFormatID, ToGPSFormatID, GPSFormatConversionCalculation) '
                        'VALUES (?, ? ,?)')
                    query.bindValue(0, id_2)
                    query.bindValue(1, id_1)
                    query.bindValue(2, f'''{conversion2to1}''')
                    if not query.exec():
                        logger_setup.get_logger().critical('Error populating GPSFormatConversions')
                        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                        logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                        return False
                else:
                    current_conversion = gps_conversion_model.record(0).value('GPSFormatConversionCalculation')
                    if current_conversion != conversion2to1:
                        query.prepare(f'UPDATE GPSFormatConversions SET GPSFormatConversionCalculation = ? '
                                      'WHERE FromGPSFormatID = ? AND ToGPSFormatID = ?')
                        query.bindValue(0, f'''{conversion2to1}''')
                        query.bindValue(1, id_2)
                        query.bindValue(2, id_1)
                        if not query.exec():
                            logger_setup.get_logger().critical('Error populating GPSFormatConversions')
                            logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                            logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                            logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                            return False
    return True


def populate_ages(database=None) -> bool:
    """
    Connect to the database and add the Geologic timescale tree structure with names and ages. GSA Geologic Time Scale
    v. 5.0 as a xml file. Overwrites any previous changes to this table. Uses the default database if none is provided.
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True for success, False for failure
    """

    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    xml_file = os.path.join(base_path, "GeologicTime_Ages.xml")

    tree = ET.parse(xml_file)
    root = tree.getroot()
    eon_row = 0
    era_row = 0
    period_row = 0
    epoch_row = 0
    age_row = 0
    for eon in root.findall('Eon'):
        age_item = ('', eon_row, f'{eon.get("name")}', f'{eon.get("oldest")}', f'{eon.get("youngest")}')
        if not add_age(age_item, database):
            return False
        for era in eon.findall('Era'):
            eon_name = eon.get("name")
            if query.exec(f'SELECT AgeID FROM AGES WHERE AgeName = "{eon_name}"'):
                out = []
                while query.next(): out.append(query.value(0))
                eon_id = out[0]
                age_item = (eon_id, era_row, f'{era.get("name")}', f'{era.get("oldest")}', f'{era.get("youngest")}')
                if not add_age(age_item, database):
                    return False
                for period in era.findall('Period'):
                    era_name = era.get("name")
                    if query.exec(f'SELECT AgeID FROM AGES WHERE AgeName = "{era_name}"'):
                        out = []
                        while query.next(): out.append(query.value(0))
                        era_id = out[0]
                        age_item = (
                            era_id, period_row, f'{period.get("name")}', f'{period.get("oldest")}',
                            f'{period.get("youngest")}')
                        if not add_age(age_item, database):
                            return False
                        for epoch in period.findall('Epoch'):
                            period_name = period.get("name")
                            if query.exec(f'SELECT AgeID FROM AGES WHERE AgeName = "{period_name}"'):
                                out = []
                                while query.next(): out.append(query.value(0))
                                period_id = out[0]
                                age_item = (period_id, epoch_row, f'{epoch.get("name")}', f'{epoch.get("oldest")}',
                                            f'{epoch.get("youngest")}')
                                if not add_age(age_item, database):
                                    return False
                                for age in epoch.findall('Age'):
                                    epoch_name = epoch.get("name")
                                    # Many epochs have the same name, need to get most recent one
                                    if query.exec(
                                            f'SELECT AgeID FROM AGES WHERE AgeName = "{epoch_name}" '
                                            f'ORDER BY AgeID DESC'):
                                        out = []
                                        while query.next(): out.append(query.value(0))
                                        epoch_id = out[0]
                                        age_item = (epoch_id, age_row, f'{age.get("name")}', f'{age.get("oldest")}',
                                                    f'{age.get("youngest")}')
                                        if not add_age(age_item, database):
                                            return False
                                    age_row += 1
                                epoch_row += 1
                                age_row = 0
                        period_row += 1
                        epoch_row = 0
                era_row += 1
                period_row = 0
        eon_row += 1
        era_row = 0

    return True


def add_age(age: tuple, database=None) -> bool:
    """
    Adds each age item to the table with its parent ID. Called by populate_ages. Uses the default database if none is provided.
    :param age: tuple that contains (Parent ageID, age name, Max Ma, Min Ma)
    :param database: QSqlDatabase instance to populate tables in, if None uses the default connection.
    :return: True if successful, False if error
    """
    if database is None:
        query = QtS.QSqlQuery()
    else:
        query = QtS.QSqlQuery(database)
    if age[0]:
        # if there is a parent
        sql = f'''INSERT INTO Ages(ParentAgeID, AgeParentRow, AgeName, OldestAge, YoungestAge)
                        VALUES({age[0]}, {age[1]}, "{age[2]}", {age[3]}, {age[4]})'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical('Error populating Ages')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                return False
    else:
        sql = f'''INSERT INTO Ages(AgeParentRow, AgeName, OldestAge, YoungestAge)
                        VALUES({age[1]}, "{age[2]}", {age[3]}, {age[4]})'''
        if not query.exec(sql):
            if 'UNIQUE constraint failed' not in query.lastError().text():
                logger_setup.get_logger().critical('Error populating Ages')
                logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
                logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
                logger_setup.get_logger().debug(f'Bound values: {query.boundValues()}')
                return False
    return True
