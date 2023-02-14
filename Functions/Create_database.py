import sqlite3
import xml.etree.ElementTree as ET  # xml reader

'''Commands to create the database
Foreign keys are set to cascade on update
When a foreign key is deleted, most will be set to null'''

'''SQL strings to create each table'''

CREATE_SAMPLES_TABLE = """CREATE TABLE IF NOT EXISTS Samples(
                    "Sample ID" INTEGER PRIMARY KEY,
                    "Sample name" TEXT, 
                    "Average age" REAL,
                    "Average age error" REAL,
                    "Error sigma" TEXT,
                    "Oldest age" REAL,
                    "Youngest age" REAL,
                    "Oldest age ID" INTEGER,
                    "Youngest age ID" INTEGER,
                    "Column ID" INTEGER,
                    "Height depth" REAL,
                    "Height depth error" REAL,
                    "Height depth unit" TEXT,
                    "Lat deg" REAL,
                    "Lat min" REAL,
                    "Lat sec" REAL,
                    "Lon deg" REAL,
                    "Lon min" REAL,
                    "Lon sec" REAL,
                    "Elev" REAL,
                    "Elev error" REAL,
                    "Elev unit" TEXT,
                    "Description" TEXT,
                    FOREIGN KEY("Column ID") REFERENCES Columns("Column ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )"""

CREATE_ALIQUOTS_TABLE = '''CREATE TABLE IF NOT EXISTS "Aliquots"(
                    "Aliquot ID" INTEGER PRIMARY KEY,
                    "Aliquot name" TEXT,
                    "Sample ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SPOTS_TABLE = '''CREATE TABLE IF NOT EXISTS "Spots"(
                    "Spot ID" INTEGER PRIMARY KEY,
                    "Spot name" TEXT,
                    "Aliquot ID" INTEGER,
                    "Spot composition ID" INTEGER,
                    FOREIGN KEY("Aliquot ID") REFERENCES Aliquots("Aliquot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Spot composition ID") REFERENCES "Spot compositions"("Spot composition ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SAMPLE_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Sample context"(
                    "Sample context ID" INTEGER PRIMARY KEY,
                    "sample context name" TEXT,
                    "sample context description" TEXT
                    )'''

CREATE_ALIQUOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Aliquot context"(
                    "Aliquot context ID" INTEGER PRIMARY KEY,
                    "Aliquot context name" TEXT,
                    "Aliquot context description" TEXT
                    )'''

CREATE_SPOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Spot context"(
                    "Spot context ID" INTEGER PRIMARY KEY,
                    "Spot context name" TEXT,
                    "Spot context description" TEXT
                    )'''

CREATE_SPOT_COMPOSITION_TABLE = '''CREATE TABLE IF NOT EXISTS "Spot compositions"(
                    "Spot composition ID" INTEGER PRIMARY KEY,
                    "Spot composition name" TEXT,
                    "Spot composition description" TEXT
                    )'''

CREATE_SOURCES_TABLE = '''CREATE TABLE IF NOT EXISTS Sources(
                    "Source ID" INTEGER PRIMARY KEY,
                    Authors TEXT,
                    Year INTEGER,
                    Title TEXT,
                    Source TEXT,
                    doi TEXT,
                    "Short Citation" TEXT
                    )'''

CREATE_REGIONS_TABLE = '''CREATE TABLE IF NOT EXISTS Regions(
                    "Region ID" INTEGER PRIMARY KEY,
                    "Region name" TEXT,
                    "Region description" TEXT
                    )'''

CREATE_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS Settings(
                    "Setting ID" INTEGER PRIMARY KEY,
                    "Setting name" TEXT,
                    "Setting description" TEXT
                    )'''

CREATE_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Columns(
                    "Column ID" INTEGER PRIMARY KEY,
                    "Column name" TEXT,
                    "Column description" TEXT
                    )'''

CREATE_SAMPLING_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS "Sampling methods"(
                    "Sampling method ID" INTEGER PRIMARY KEY,
                    "Sampling method name" TEXT,
                    "Sampling method description" TEXT
                    )'''

CREATE_ROCK_TYPES_TABLE = '''CREATE TABLE IF NOT EXISTS "Rock Types"(
                    "Rock type ID" INTEGER PRIMARY KEY,
                    "Rock type name" TEXT,
                    "Rock type description" TEXT
                    )'''

CREATE_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS Units(
                    "Unit ID" INTEGER PRIMARY KEY,
                    "Parent unit key" INTEGER,
                    "Unit name" TEXT,
                    "Unit description" TEXT
                    )'''

CREATE_AGES_TABLE = '''CREATE TABLE IF NOT EXISTS "Ages"(
                    "Age ID" INTEGER PRIMARY KEY,
                    "Parent age ID" INTEGER,
                    "Age name" TEXT,
                    "Max Ma" REAL,
                    "Min Ma" REAL
                    )'''

CREATE_AGE_SIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS "Age Signatures"(
                    "Age signature ID" INTEGER PRIMARY KEY,
                    "Age signature name" TEXT,
                    "Age signature description" TEXT
                    )'''

CREATE_UPBDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "UPb Data"(
                    "UPb analysis ID" INTEGER PRIMARY KEY,
                    "Spot ID" INTEGER,
                    "Source ID" INTEGER,
                    "Lab facility ID" Integer,
                    "UPb analysis method ID" Integer
                    "U ppm" REAL,
                    "206Pb/204Pb" REAL,
                    "U/Th" REAL,
                    "206Pb/207Pb" REAL,
                    "206Pb/207Pb error" REAL,
                    "207Pb/235U" REAL,
                    "207Pb/235U error" REAL,
                    "206Pb/238U" REAL,
                    "206Pb/238U error" REAL,
                    "Error corr" REAL,
                    "206Pb/207Pb age" REAL,
                    "206Pb/207Pb age error" REAL,
                    "207Pb/235U age" REAL,
                    "207Pb/235U age error" REAL,
                    "206Pb/238U age" REAL,
                    "206Pb/238U age error" REAL,
                    "Best age" REAL,
                    "Error" REAL,
                    "Conc" REAL,
                    "Accepted" INTEGER,
                    FOREIGN KEY("Spot ID") REFERENCES Spots("Spot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    FOREIGN KEY("Source ID") REFERENCES Sources("Source ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    FOREIGN KEY("Lab facility ID") REFERENCES "Lab facilities"("Lab facility ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    FOREIGN KEY("UPb analysis method ID") REFERENCES "UPb analysis methods"("UPb analysis method ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_GEOCHEMDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "Geochem Data"(
                    "Geochem analysis ID" INTEGER PRIMARY KEY,
                    "Spot ID" INTEGER,
                    "Major elements" TEXT,
                    "Trace elements" TEXT,
                    "REEs" TEXT,
                    FOREIGN KEY("Spot ID") REFERENCES Spots("Spot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_LAB_FACILITIES_TABLE = '''CREATE TABLE IF NOT EXISTS "Lab facilities"(
                    "Lab facility ID" INTEGER PRIMARY KEY,
                    "Lab facility name" TEXT,
                    "Lab facility description" TEXT
                    )'''

CREATE_UPB_ANALYSIS_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS "UPb analysis methods"(
                    "UPb analysis method ID" INTEGER PRIMARY KEY,
                    "UPb analysis name" TEXT,
                    "UPb analysis description" TEXT
                    )'''

CREATE_SPOTS_SPOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Spots_SpotContext"(
                    "Spot ID" INTEGER,
                    "Spot context ID" Integer,
                    FOREIGN KEY("Spot ID") REFERENCES Spots("Spot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Spot context ID") REFERENCES "Spot context"("Spot context ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Aliquots_AliquotContext"(
                    "Aliquot ID" INTEGER,
                    "Aliquot context ID" Integer,
                    FOREIGN KEY("Aliquot ID") REFERENCES Aliquots("Aliquot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Aliquot context ID") REFERENCES "Aliquot context"("Aliquot context ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLECONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_SampleContext"(
                    "Sample ID" INTEGER,
                    "Sample context ID" Integer,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Sample context ID") REFERENCES "Sample context"("Sample context ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_AGESIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_AgeSignatures"(
                    "Sample ID" INTEGER,
                    "Age signature ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Age signature ID") REFERENCES "Age signatures"("Age signature ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_REGIONS_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_Regions"(
                    "Sample ID" INTEGER,
                    "Region ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Region ID") REFERENCES "Regions"("Region ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_Columns"(
                    "Sample ID" INTEGER,
                    "Column ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Column ID") REFERENCES "Column"("Region ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_ROCKTYPES_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_RockTypes"(
                    "Sample ID" INTEGER,
                    "Rock type ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Rock type ID") REFERENCES "Regions"("Rock type ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLINGMETHODS_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_SamplingMethods"(
                    "Sample ID" INTEGER,
                    "Sampling method ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Sampling method ID") REFERENCES "Sampling methods"("Sampling method ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_Settings"(
                    "Sample ID" INTEGER,
                    "Setting ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Setting ID") REFERENCES "Settings"("Setting ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_Units"(
                    "Sample ID" INTEGER,
                    "Unit ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Unit ID") REFERENCES "Units"("Unit ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''


'''Commands to create tables and populate default tables'''


def create_tables(db_file):
    """
    Connect to the database and execute the sql strings defined above to create the database tables
    Only creates tables that do not already exist - does not overwrite existing tables
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

        # Populate the age table during initiation
        sql = '''SELECT * FROM Ages'''
        if c.execute(sql):
            out = c.fetchall()
            if not out:
                populate_ages(conn)
        else:
            print(f'query failed')


def populate_ages(db_file):
    """
    Connect to the database and add the Geologic Times scale tree structure with names and ages
    GSA Geologic Time Scale v. 5.0 as a xml file
    Overwrites any previous changes to this table
    :param db_file: Database file with full path
    """
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        # Begin by deleting all rows in the table to allow for a reset if things get changed
        sql = 'DELETE FROM Ages'
        c.execute(sql)
        xml_file = "GeologicTime_Ages.xml"
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for eon in root.findall('Eon'):
            age_item = ('', f'{eon.get("name")}', f'{eon.get("oldest")}', f'{eon.get("youngest")}')
            add_age(c, age_item)
            for era in eon.findall('Era'):
                eon_name = eon.get("name")
                if c.execute(f'SELECT "Age ID" FROM AGES WHERE "Age name" = "{eon_name}"'):
                    out = c.fetchall()
                    eon_id = out[0][0]
                    age_item = (eon_id, f'{era.get("name")}', f'{era.get("oldest")}', f'{era.get("youngest")}')
                    add_age(c, age_item)
                    for period in era.findall('Period'):
                        era_name = era.get("name")
                        if c.execute(f'SELECT "Age ID" FROM AGES WHERE "Age name" = "{era_name}"'):
                            out = c.fetchall()
                            era_id = out[0][0]
                            age_item = (
                                era_id, f'{period.get("name")}', f'{period.get("oldest")}', f'{period.get("youngest")}')
                            add_age(c, age_item)
                            for epoch in period.findall('Epoch'):
                                period_name = period.get("name")
                                if c.execute(f'SELECT "Age ID" FROM AGES WHERE "Age name" = "{period_name}"'):
                                    out = c.fetchall()
                                    period_id = out[0][0]
                                    age_item = (period_id, f'{epoch.get("name")}', f'{epoch.get("oldest")}',
                                                f'{epoch.get("youngest")}')
                                    add_age(c, age_item)
                                    for age in epoch.findall('Age'):
                                        epoch_name = epoch.get("name")
                                        # Many epochs have the same name, need to get most recent one
                                        if c.execute(
                                                f'SELECT "Age ID" FROM AGES WHERE "Age name" = "{epoch_name}" '
                                                f'ORDER BY "Age ID" DESC'):
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
    :param age: tuple that contains (Parent age ID, age name, Max Ma, Min Ma)
    """
    sql = '''INSERT INTO Ages("Parent age ID", "Age name", "Max Ma", "Min Ma")
                    VALUES(?,?,?,?)'''
    values = (age[0], age[1], age[2], age[3])
    c.execute(sql, values)
