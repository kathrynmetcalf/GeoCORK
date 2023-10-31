import sqlite3
import xml.etree.ElementTree as ET  # xml reader

'''Commands to create the database
Foreign keys are set to cascade on update
When a foreign key is deleted, most will be set to null'''

'''SQL strings to create each table'''

CREATE_SAMPLES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples(
                    SampleID INTEGER PRIMARY KEY,
                    SampleName TEXT, 
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
                    FOREIGN KEY(OldestAgeID) REFERENCES Ages(AgeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    FOREIGN KEY(YoungestAgeID) REFERENCES Ages(AgeID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_ALIQUOTS_TABLE = '''CREATE TABLE IF NOT EXISTS Aliquots(
                    AliquotID INTEGER PRIMARY KEY,
                    AliquotName TEXT,
                    SampleID INTEGER,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SPOTS_TABLE = '''CREATE TABLE IF NOT EXISTS Spots(
                    SpotID INTEGER PRIMARY KEY,
                    SpotName TEXT,
                    AliquotID INTEGER,
                    SpotCompositionID INTEGER,
                    FOREIGN KEY(AliquotID) REFERENCES Aliquots(AliquotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SpotCompositionID) REFERENCES SpotCompositions(SpotCompositionID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SAMPLE_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS SampleContext(
                    SampleContextID INTEGER PRIMARY KEY,
                    ParentSampleContextID INTEGER,
                    SampleContextName TEXT,
                    SampleContextDescription TEXT
                    )'''

CREATE_ALIQUOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS AliquotContext(
                    AliquotContextID INTEGER PRIMARY KEY,
                    ParentAliquotContextID INTEGER,
                    AliquotContextName TEXT,
                    AliquotContextDescription TEXT
                    )'''

CREATE_SPOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS SpotContext(
                    SpotContextID INTEGER PRIMARY KEY,
                    ParentSpotContextID INTEGER,
                    SpotContextName TEXT,
                    SpotContextDescription TEXT
                    )'''

CREATE_SPOT_COMPOSITION_TABLE = '''CREATE TABLE IF NOT EXISTS SpotCompositions(
                    SpotCompositionID INTEGER PRIMARY KEY,
                    ParentSpotCompositionID INTEGER,
                    SpotCompositionName TEXT,
                    SpotCompositionDescription TEXT
                    )'''

CREATE_SOURCES_TABLE = '''CREATE TABLE IF NOT EXISTS Sources(
                    SourceID INTEGER PRIMARY KEY,
                    Authors TEXT,
                    Year INTEGER,
                    Title TEXT,
                    Source TEXT,
                    doi TEXT,
                    ShortCitation TEXT
                    )'''

CREATE_REGIONS_TABLE = '''CREATE TABLE IF NOT EXISTS Regions(
                    RegionID INTEGER PRIMARY KEY,
                    ParentRegionID INTEGER,
                    RegionName TEXT,
                    RegionDescription TEXT
                    )'''

CREATE_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS Settings(
                    SettingID INTEGER PRIMARY KEY,
                    ParentSettingID INTEGER,
                    SettingName TEXT,
                    SettingDescription TEXT
                    )'''

CREATE_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Columns(
                    ColumnID INTEGER PRIMARY KEY,
                    ColumnName TEXT,
                    ColumnDescription TEXT
                    )'''

CREATE_SAMPLING_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS SamplingMethods(
                    SamplingMethodID INTEGER PRIMARY KEY,
                    ParentSamplingMethodID INTEGER,
                    SamplingMethodName TEXT,
                    SamplingMethodDescription TEXT
                    )'''

CREATE_ROCK_TYPES_TABLE = '''CREATE TABLE IF NOT EXISTS RockTypes(
                    RockTypeID INTEGER PRIMARY KEY,
                    ParentRockTypeID INTEGER,
                    RockTypeName TEXT,
                    RockTypeDescription TEXT
                    )'''

CREATE_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS Units(
                    UnitID INTEGER PRIMARY KEY,
                    ParentUnitID INTEGER,
                    UnitName TEXT,
                    UnitDescription TEXT
                    )'''

CREATE_AGES_TABLE = '''CREATE TABLE IF NOT EXISTS Ages(
                    AgeID INTEGER PRIMARY KEY,
                    ParentAgeID INTEGER,
                    AgeName TEXT,
                    MaxMa REAL,
                    MinMa REAL
                    )'''

CREATE_AGE_SIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS AgeSignatures(
                    AgeSignatureID INTEGER PRIMARY KEY,
                    ParentAgeSignatureID INTEGER,
                    AgeSignatureName TEXT,
                    AgeSignatureDescription TEXT
                    )'''

CREATE_UPBDATA_TABLE = '''CREATE TABLE IF NOT EXISTS UPbData(
                    UPbAnalysisID INTEGER PRIMARY KEY,
                    SpotID INTEGER,
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
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    FOREIGN KEY(SourceID) REFERENCES Sources(SourceID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    FOREIGN KEY(LabFacilityID) REFERENCES LabFacilities(LabFacilityID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    FOREIGN KEY(UPbAnalysisMethodID) REFERENCES UPbAnalysisMethods(UPbAnalysisMethodID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    FOREIGN KEY(InstrumentID) REFERENCES Instruments(InstrumentID)
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_GEOCHEMDATA_TABLE = '''CREATE TABLE IF NOT EXISTS GeochemData(
                    GeochemAnalysisID INTEGER PRIMARY KEY,
                    SpotID INTEGER,
                    MajorElements TEXT,
                    TraceElements TEXT,
                    REEs TEXT,
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_LAB_FACILITIES_TABLE = '''CREATE TABLE IF NOT EXISTS LabFacilities(
                    LabFacilityID INTEGER PRIMARY KEY,
                    LabFacilityName TEXT,
                    LabFacilityDescription TEXT
                    )'''

CREATE_UPB_ANALYSIS_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS UPbAnalysisMethods(
                    UPbAnalysisMethodID INTEGER PRIMARY KEY,
                    UPbAnalysisName TEXT,
                    UPbAnalysisDescription TEXT
                    )'''

CREATE_INSTRUMENTS_TABLE = '''CREATE TABLE IF NOT EXISTS Instruments(
                    InstrumentID INTEGER PRIMARY KEY,
                    InstrumentName TEXT,
                    InstrumentDescription TEXT
                    )'''

CREATE_SPOTS_SPOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Spots_SpotContext(
                    SpotID INTEGER,
                    SpotContextID INTEGER,
                    FOREIGN KEY(SpotID) REFERENCES Spots(SpotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SpotContextID) REFERENCES SpotContext(SpotContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Aliquots_AliquotContext(
                    AliquotID INTEGER,
                    AliquotContextID INTEGER,
                    FOREIGN KEY(AliquotID) REFERENCES Aliquots(AliquotID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(AliquotContextID) REFERENCES AliquotContext(AliquotContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLECONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_SampleContext(
                    SampleID INTEGER,
                    SampleContextID INTEGER,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(SampleContextID) REFERENCES SampleContext(SampleContextID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_AGESIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_AgeSignatures(
                    SampleID INTEGER,
                    AgeSignatureID INTEGER,
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
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(RegionID) REFERENCES Regions(RegionID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_Columns(
                    SampleID INTEGER,
                    ColumnID INTEGER,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(ColumnID) REFERENCES Columns(ColumnID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_ROCKTYPES_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_RockTypes(
                    SampleID INTEGER,
                    RockTypeID INTEGER,
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(RockTypeID) REFERENCES RockTypes(RockTypeID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLINGMETHODS_TABLE = '''CREATE TABLE IF NOT EXISTS Samples_SamplingMethods(
                    SampleID INTEGER,
                    SamplingMethodID INTEGER,
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
                    FOREIGN KEY(SampleID) REFERENCES Samples(SampleID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY(UnitID) REFERENCES Units(UnitID)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_FILTER_GROUPS_TABLE = '''CREATE TABLE IF NOT EXISTS FilterGroups(
                    FilterGroupID INTEGER PRIMARY KEY,
                    FilterGroupName TEXT,
                    SQLQuery TEXT,
                    DefaultColor TEXT,
                    FilterGroupDescription TEXT
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

        c.execute(CREATE_UPB_ANALYSIS_METHODS_TABLE)

        c.execute(CREATE_UPBDATA_TABLE)

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

        # Populate the age table during initiation
        sql = '''SELECT * FROM Ages'''
        if c.execute(sql):
            out = c.fetchall()
            if not out:
                populate_ages(conn)
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
        xml_file = "../Reference/GeologicTime_Ages.xml"
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for eon in root.findall('Eon'):
            age_item = ('', f'{eon.get("name")}', f'{eon.get("oldest")}', f'{eon.get("youngest")}')
            add_age(c, age_item)
            for era in eon.findall('Era'):
                eon_name = eon.get("name")
                if c.execute(f'SELECT AgeID FROM AGES WHERE AgeName = "{eon_name}"'):
                    out = c.fetchall()
                    eon_id = out[0][0]
                    age_item = (eon_id, f'{era.get("name")}', f'{era.get("oldest")}', f'{era.get("youngest")}')
                    add_age(c, age_item)
                    for period in era.findall('Period'):
                        era_name = era.get("name")
                        if c.execute(f'SELECT AgeID FROM AGES WHERE AgeName = "{era_name}"'):
                            out = c.fetchall()
                            era_id = out[0][0]
                            age_item = (
                                era_id, f'{period.get("name")}', f'{period.get("oldest")}', f'{period.get("youngest")}')
                            add_age(c, age_item)
                            for epoch in period.findall('Epoch'):
                                period_name = period.get("name")
                                if c.execute(f'SELECT AgeID FROM AGES WHERE AgeName = "{period_name}"'):
                                    out = c.fetchall()
                                    period_id = out[0][0]
                                    age_item = (period_id, f'{epoch.get("name")}', f'{epoch.get("oldest")}',
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
                                            age_item = (epoch_id, f'{age.get("name")}', f'{age.get("oldest")}',
                                                        f'{age.get("youngest")}')
                                            add_age(c, age_item)


def add_age(c, age):
    """
    Called by populate_ages
    Adds each age item to the table with its parent ID
    :param c: database connection cursor
    :param age: tuple that contains (Parent ageID, age name, Max Ma, Min Ma)
    """
    if age[0]:
        # if there is a parent
        sql = '''INSERT INTO Ages(ParentAgeID, AgeName, MaxMa, MinMa)
                        VALUES(?,?,?,?)'''
        values = (age[0], age[1], age[2], age[3])
        c.execute(sql, values)
    else:
        sql = '''INSERT INTO Ages(AgeName, MaxMa, MinMa)
                        VALUES(?,?,?)'''
        values = (age[1], age[2], age[3])
        c.execute(sql, values)


if __name__ == '__main__':
    db_file = '../TestSchema.db'
    create_tables(db_file)
