import sqlite3
import xml.etree.ElementTree as ET  # xml reader

'''Commands to create the database
Foreign keys are set to cascade on update
When a foreign key is deleted, most will be set to null'''

'''SQL strings to create each table'''

CREATE_SAMPLES_TABLE = """CREATE TABLE IF NOT EXISTS Samples(
                    "Sample ID" INTEGER PRIMARY KEY,
                    "Sample Name" TEXT, 
                    "Average Age" REAL,
                    "Average Age error" REAL,
                    "Error Sigma" TEXT,
                    "Oldest Age" REAL,
                    "Youngest Age" REAL,
                    "Oldest Age ID" INTEGER,
                    "Youngest Age ID" INTEGER,
                    "Column ID" INTEGER,
                    "Height Depth" REAL,
                    "Height Depth Error" REAL,
                    "Height Depth Unit" TEXT,
                    "Lat deg" REAL,
                    "Lat min" REAL,
                    "Lat sec" REAL,
                    "Lon deg" REAL,
                    "Lon min" REAL,
                    "Lon sec" REAL,
                    "Elev" REAL,
                    "Elev Error" REAL,
                    "Elev Unit" TEXT,
                    "Description" TEXT,
                    FOREIGN KEY("Column ID") REFERENCES Columns("Column ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )"""

CREATE_ALIQUOTS_TABLE = '''CREATE TABLE IF NOT EXISTS "Aliquots"(
                    "Aliquot ID" INTEGER PRIMARY KEY,
                    "Aliquot Name" TEXT,
                    "Sample ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SPOTS_TABLE = '''CREATE TABLE IF NOT EXISTS "Spots"(
                    "Spot ID" INTEGER PRIMARY KEY,
                    "Spot Name" TEXT,
                    "Aliquot ID" INTEGER,
                    "Spot Composition ID" INTEGER,
                    FOREIGN KEY("Aliquot ID") REFERENCES Aliquots("Aliquot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Spot Composition ID") REFERENCES "Spot Compositions"("Spot Composition ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_SAMPLE_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Sample Context"(
                    "Sample Context ID" INTEGER PRIMARY KEY,
                    "sample Context Name" TEXT,
                    "sample Context Description" TEXT
                    )'''

CREATE_ALIQUOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Aliquot Context"(
                    "Aliquot Context ID" INTEGER PRIMARY KEY,
                    "Aliquot Context Name" TEXT,
                    "Aliquot Context Description" TEXT
                    )'''

CREATE_SPOT_CONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Spot Context"(
                    "Spot Context ID" INTEGER PRIMARY KEY,
                    "Spot Context Name" TEXT,
                    "Spot Context Description" TEXT
                    )'''

CREATE_SPOT_COMPOSITION_TABLE = '''CREATE TABLE IF NOT EXISTS "Spot compositions"(
                    "Spot Composition ID" INTEGER PRIMARY KEY,
                    "Spot Composition Name" TEXT,
                    "Spot Composition Description" TEXT
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
                    "Region Name" TEXT,
                    "Region Description" TEXT
                    )'''

CREATE_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS Settings(
                    "Setting ID" INTEGER PRIMARY KEY,
                    "Setting Name" TEXT,
                    "Setting Description" TEXT
                    )'''

CREATE_COLUMNS_TABLE = '''CREATE TABLE IF NOT EXISTS Columns(
                    "Column ID" INTEGER PRIMARY KEY,
                    "Column Name" TEXT,
                    "Column Description" TEXT
                    )'''

CREATE_SAMPLING_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS "Sampling methods"(
                    "Sampling Method ID" INTEGER PRIMARY KEY,
                    "Sampling Method Name" TEXT,
                    "Sampling Method Description" TEXT
                    )'''

CREATE_ROCK_TYPES_TABLE = '''CREATE TABLE IF NOT EXISTS "Rock Types"(
                    "Rock Type ID" INTEGER PRIMARY KEY,
                    "Rock Type Name" TEXT,
                    "Rock Type Description" TEXT
                    )'''

CREATE_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS Units(
                    "Unit ID" INTEGER PRIMARY KEY,
                    "Parent Unit key" INTEGER,
                    "Unit Name" TEXT,
                    "Unit Description" TEXT
                    )'''

CREATE_AGES_TABLE = '''CREATE TABLE IF NOT EXISTS "Ages"(
                    "Age ID" INTEGER PRIMARY KEY,
                    "Parent Age ID" INTEGER,
                    "Age Name" TEXT,
                    "Max Ma" REAL,
                    "Min Ma" REAL
                    )'''

CREATE_AGE_SIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS "Age Signatures"(
                    "Age Signature ID" INTEGER PRIMARY KEY,
                    "Age Signature Name" TEXT,
                    "Age Signature Description" TEXT
                    )'''

CREATE_UPBDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "UPb Data"(
                    "UPb analysis ID" INTEGER PRIMARY KEY,
                    "Spot ID" INTEGER,
                    "Source ID" INTEGER,
                    "Lab Facility ID" INTEGER,
                    "UPb Analysis Method ID" INTEGER
                    "U ppm" REAL,
                    "206Pb/204Pb" REAL,
                    "U/Th" REAL,
                    "206Pb/207Pb" REAL,
                    "206Pb/207Pb error" REAL,
                    "207Pb/235U" REAL,
                    "207Pb/235U error" REAL,
                    "206Pb/238U" REAL,
                    "206Pb/238U error" REAL,
                    "Error Corr" REAL,
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
                    FOREIGN KEY("Lab Facility ID") REFERENCES "Lab Facilities"("Lab Facility ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    FOREIGN KEY("UPb Analysis Method ID") REFERENCES "UPb Analysis Methods"("UPb analysis method ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )'''

CREATE_GEOCHEMDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "Geochem Data"(
                    "Geochem analysis ID" INTEGER PRIMARY KEY,
                    "Spot ID" INTEGER,
                    "Major Elements" TEXT,
                    "Trace Elements" TEXT,
                    "REEs" TEXT,
                    FOREIGN KEY("Spot ID") REFERENCES Spots("Spot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_LAB_FACILITIES_TABLE = '''CREATE TABLE IF NOT EXISTS "Lab Facilities"(
                    "Lab Facility ID" INTEGER PRIMARY KEY,
                    "Lab Facility Name" TEXT,
                    "Lab Facility Description" TEXT
                    )'''

CREATE_UPB_ANALYSIS_METHODS_TABLE = '''CREATE TABLE IF NOT EXISTS "UPb Analysis Methods"(
                    "UPb Analysis Method ID" INTEGER PRIMARY KEY,
                    "UPb Analysis Name" TEXT,
                    "UPb Analysis Description" TEXT
                    )'''

CREATE_SPOTS_SPOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Spots_SpotContext"(
                    "Spot ID" INTEGER,
                    "Spot Context ID" INTEGER,
                    FOREIGN KEY("Spot ID") REFERENCES Spots("Spot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Spot Context ID") REFERENCES "Spot Context"("Spot Context ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_ALIQUOTS_ALIQUOTCONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Aliquots_AliquotContext"(
                    "Aliquot ID" INTEGER,
                    "Aliquot Context ID" INTEGER,
                    FOREIGN KEY("Aliquot ID") REFERENCES Aliquots("Aliquot ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Aliquot Context ID") REFERENCES "Aliquot Context"("Aliquot Context ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLECONTEXT_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_SampleContext"(
                    "Sample ID" INTEGER,
                    "Sample Context ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Sample Context ID") REFERENCES "Sample Context"("Sample Context ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_AGESIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_AgeSignatures"(
                    "Sample ID" INTEGER,
                    "Age Signature ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Age Signature ID") REFERENCES "Age Signatures"("Age Signature ID")
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
                    "Rock Type ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Rock Type ID") REFERENCES "Regions"("Rock Type ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_SAMPLES_SAMPLINGMETHODS_TABLE = '''CREATE TABLE IF NOT EXISTS "Samples_SamplingMethods"(
                    "Sample ID" INTEGER,
                    "Sampling Method ID" INTEGER,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                    FOREIGN KEY("Sampling Method ID") REFERENCES "Sampling Methods"("Sampling Method ID")
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

CREATE_FILTER_GROUPS_TABLE = '''CREATE TABLE IF NOT EXISTS "Filter Groups"(
                    "Filter Group ID" INTEGER PRIMARY KEY,
                    "Filter Group Name" TEXT,
                    "SQL Query" TEXT,
                    "Default Color" TEXT,
                    "Filter Group Description" TEXT
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
    sql = '''INSERT INTO Ages("Parent age ID", "Age Name", "Max Ma", "Min Ma")
                    VALUES(?,?,?,?)'''
    values = (age[0], age[1], age[2], age[3])
    c.execute(sql, values)


if __name__ == '__main__':
    db_file = '../TestSchema.db'
    create_tables(db_file)
