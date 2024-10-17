import sqlite3
import xml.etree.ElementTree as ET  # xml reader
import Functions.Create_triggers as CT # triggers
import Functions.DB_views as DBV # views

#todo add this:
# **Filter Table**
# ID, Description
# 1, 10 Purchases with a total amount over 100 dollars
#
# **Predicate Table**
# Filter ID, Condition ID, Table, Column, Operator, Value, LogicalOperator(NULL if last)
# 1,1,PurchaseCount,GreaterThanEqual,10, AND
# 2,1,PurchaseAmount,GreaterThan,100
#
'''Commands to create the database
Foreign keys are set to cascade on update
When a foreign key is deleted, most will be set to null
The only exception is the AliquotID in the Spots table, which will cascade on delete
Names must be unique and are checked for case sensitivity'''
# look under linking aboutmodified to other tables
'''SQL strings to create each table'''

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
                    AboutModified DATETIME DEFAULT CURRENT_TIMESTAMP)
                    '''

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
                    AliquotName TEXT NOT NULL CHECK (AliquotName <> ''),
                    SampleID INTEGER,
                    AliquotCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AliquotModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AliquotName COLLATE NOCASE),
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Aliquots_AliquotContexts(
                    AliquotID INTEGER,
                    AliquotContextID INTEGER,
                    Aliquots_AliquotContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Aliquots_AliquotContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(AliquotID) REFERENCES Aliquots(AliquotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AliquotContextID) REFERENCES AliquotContext(AliquotContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ANALYSIS_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS AnalysisMethods(
                    AnalysisMethodID INTEGER PRIMARY KEY,
                    ParentAnalysisMethodID INTEGER,
                    AnalysisMethodParentRow INTEGER,
                    AnalysisMethodName TEXT NOT NULL CHECK (AnalysisMethodName <> ''),
                    AnalysisMethodDescription TEXT,
                    AnalysisMethodCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    AnalysisMethodModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (AnalysisMethodName COLLATE NOCASE),
                    UNIQUE (ParentAnalysisMethodID, AnalysisMethodParentRow)
                    )'''

CREATE_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Columns(
                    ColumnID INTEGER PRIMARY KEY,
                    ColumnName TEXT NOT NULL CHECK (ColumnName <> ''),
                    ColumnDescription TEXT, 
                    ColumnCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ColumnModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (ColumnName COLLATE NOCASE)
                    )'''

CREATE_GEOCHEMDATA_TABLE = '''CREATE TABLE IF NOT EXISTS GeochemData(
                    GeochemAnalysisID INTEGER PRIMARY KEY,
                    SpotID INTEGER NOT NULL,
                    SourceID INTEGER,
                    LabFacilityID INTEGER,
                    InstrumentID INTEGER,
                    AnalysisMethodID INTEGER,
                    MajorElements TEXT,
                    TraceElements TEXT,
                    REEs TEXT,
                    GeochemAnalysisCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    GeochemAnalysisModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SourceID) REFERENCES Sources(SourceID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(LabFacilityID) REFERENCES LabFacilities(LabFacilityID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(AnalysisMethodID) REFERENCES AnalysisMethods(AnalysisMethodID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(InstrumentID) REFERENCES Instruments(InstrumentID)
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

CREATE_SAMPLES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples(
                    SampleID INTEGER PRIMARY KEY,
                    SampleName TEXT NOT NULL CHECK (SampleName <> ''), 
                    AverageAge REAL,
                    AverageAgeError REAL,
                    ErrorSigma TEXT,
                    OldestAge REAL,
                    YoungestAge REAL,
                    OldestAgeID INTEGER,
                    YoungestAgeID INTEGER,
                    HeightDepth REAL,
                    HeightDepthError REAL,
                    HeightDepthUnit TEXT,
                    LatDeg REAL,
                    LatMin REAL,
                    LatSec REAL,
                    LonDeg REAL,
                    LonMin REAL,
                    LonSec REAL,
                    UTMZone TEXT,
                    UTMN REAL,
                    UTME REAL,
                    Elev REAL,
                    ElevError REAL,
                    ElevUnit TEXT,
                    Description TEXT,
                    SampleCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    SampleModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (SampleName COLLATE NOCASE),
                    FOREIGN KEY(OldestAgeID) REFERENCES Ages(AgeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY(YoungestAgeID) REFERENCES Ages(AgeID)
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

CREATE_SAMPLES_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Columns(
                    SampleID INTEGER,
                    ColumnID INTEGER,
                    Samples_ColumnsCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Samples_ColumnsModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ColumnID) REFERENCES Columns(ColumnID)
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
                    FOREIGN KEY(SampleContextID) REFERENCES SampleContext(SampleContextID)
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

CREATE_SPOTS_SPOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Spots_SpotContexts(
                    SpotID INTEGER,
                    SpotContextID INTEGER,
                    Spots_SpotContextCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Spots_SpotContextModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SpotContextID) REFERENCES SpotContext(SpotContextID)
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

CREATE_UPBANALYSIS_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalysisMethods(
                    UPbAnalysisMethodID INTEGER PRIMARY KEY,
                    UPbAnalysisMethodName TEXT NOT NULL CHECK (UPbAnalysisMethodName <> ''),
                    UPbAnalysisMethodDescription TEXT, 
                    UPbAnalysisMethodCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UPbAnalysisMethodModified DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (UPbAnalysisMethodName COLLATE NOCASE)
                    )'''

CREATE_UPBDATA_TABLE = '''CREATE TABLE IF NOT EXISTS UPbData(
                    UPbAnalysisID INTEGER PRIMARY KEY,
                    SpotID INTEGER NOT NULL,
                    SourceID INTEGER,
                    LabFacilityID INTEGER,
                    InstrumentID INTEGER,
                    UPbAnalysisMethodID INTEGER,
                    Uppm REAL,
                    "206Pb/204Pb" REAL,
                    "U/Th" REAL,
                    "206Pb/207Pb" REAL,
                    "206Pb/207Pberror" REAL,
                    "207Pb/235U" REAL,
                    "207Pb/235Uerror" REAL,
                    "206Pb/238U" REAL,
                    "206Pb/238Uerror" REAL,
                    ErrorCorr REAL,
                    "206Pb/207PbAge" REAL,
                    "206Pb/207PbAgeError" REAL,
                    "207Pb/235UAge" REAL,
                    "207Pb/235UAgeError" REAL,
                    "206Pb/238UAge" REAL,
                    "206Pb/238UAgeError" REAL,
                    BestAge REAL,
                    Error REAL,
                    Conc REAL,
                    SpotSize Real,
                    SpotSizeUnit TEXT,
                    Accepted INTEGER,
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
                        ON DELETE SET NULL
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

        c.execute(CREATE_SOURCES_TABLE)

        c.execute(CREATE_SAMPLING_METHODS_TABLE)

        c.execute(CREATE_REGIONS_TABLE)

        c.execute(CREATE_SETTINGS_TABLE)

        c.execute(CREATE_ANALYSIS_METHODS_TABLE)

        c.execute(CREATE_ROCK_TYPES_TABLE)

        c.execute(CREATE_UNITS_TABLE)

        c.execute(CREATE_COLUMNS_TABLE)

        c.execute(CREATE_AGE_SIGNATURES_TABLE)

        c.execute(CREATE_AGES_TABLE)

        c.execute(CREATE_SAMPLE_CONTEXT_TABLE)

        c.execute(CREATE_ALIQUOT_CONTEXT_TABLE)

        c.execute(CREATE_SPOT_CONTEXT_TABLE)

        c.execute(CREATE_SPOT_COMPOSITION_TABLE)

        c.execute(CREATE_SAMPLES_TABLE)

        c.execute(CREATE_ALIQUOTS_TABLE)

        c.execute(CREATE_SPOTS_TABLE)

        c.execute(CREATE_LAB_FACILITIES_TABLE)

        c.execute(CREATE_INSTRUMENTS_TABLE)

        c.execute(CREATE_UPBDATA_TABLE)

        c.execute(CREATE_UPBANALYSIS_TABLE)

        c.execute(CREATE_GEOCHEMDATA_TABLE)

        c.execute(CREATE_SAMPLES_AGESIGNATURES_TABLE)

        c.execute(CREATE_SAMPLES_COLUMNS_TABLE)

        c.execute(CREATE_SAMPLES_REGIONS_TABLE)

        c.execute(CREATE_SAMPLES_ROCKTYPES_TABLE)

        c.execute(CREATE_SAMPLES_SAMPLECONTEXT_TABLE)

        c.execute(CREATE_SAMPLES_SAMPLINGMETHODS_TABLE)

        c.execute(CREATE_SAMPLES_SETTINGS_TABLE)

        c.execute(CREATE_SAMPLES_UNITS_TABLE)

        c.execute(CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE)

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
