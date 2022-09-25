import sqlite3
import xml.etree.ElementTree as ET  # xml reader

'''Commands to define, create, modify, and query the database
Foreign keys are set to cascade on update, null on delete'''

CREATE_SAMPLES_TABLE = """CREATE TABLE IF NOT EXISTS Samples(
                    "Sample ID" INTEGER PRIMARY KEY,
                    "Sample name" TEXT,
                    "Source ID" INTEGER,
                    "Age signature ID" INTEGER, 
                    "Average age" REAL,
                    "Average age error" REAL,
                    "Error type" TEXT,
                    "Oldest age" REAL,
                    "Youngest age" REAL,
                    "Oldest age ID" INTEGER,
                    "Youngest age ID" INTEGER,
                    "Rock type ID" INTEGER,
                    "Unit ID" INTEGER,
                    "Region ID" INTEGER,
                    "Setting ID" INTEGER,
                    "Sampling method" TEXT,
                    "Column name" TEXT,
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
                    FOREIGN KEY("Source ID") REFERENCES Sources("Source ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Region ID") REFERENCES Regions ("Region ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Setting ID") REFERENCES Settings ("Setting ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Oldest age ID") REFERENCES Ages ("Age ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Youngest age ID") REFERENCES Ages ("Age ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Rock type ID") REFERENCES "Rock Types" ("Rock type ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Unit ID") REFERENCES Units ("Unit ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Age signature ID") REFERENCES "Age Signatures" ("Age signature ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL,
                    FOREIGN KEY ("Region ID") REFERENCES Regions ("Region ID")
                        ON UPDATE CASCADE
                        ON DELETE SET NULL
                    )"""

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

CREATE_ROCKTYPES_TABLE = '''CREATE TABLE IF NOT EXISTS "Rock Types"(
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

CREATE_AGESIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS "Age Signatures"(
                    "Age signature ID" INTEGER PRIMARY KEY,
                    "Age signature name" TEXT,
                    "Age signature description" TEXT
                    )'''

CREATE_UPBDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "UPb Data"(
                    "UPb analysis ID" INTEGER PRIMARY KEY,
                    "Sample ID" INTEGER,
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
                    "Location" TEXT,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''

CREATE_GEOCHEMDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "Geochem Data"(
                    "Geochem analysis ID" INTEGER PRIMARY KEY,
                    "Sample ID" INTEGER,
                    "Major elements" TEXT,
                    "Trace elements" TEXT,
                    FOREIGN KEY("Sample ID") REFERENCES Samples("Sample ID")
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    )'''


# Commands and queries
def create_tables(db_file):
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()

        c.execute(CREATE_SOURCES_TABLE)

        c.execute(CREATE_REGIONS_TABLE)

        c.execute(CREATE_SETTINGS_TABLE)

        c.execute(CREATE_ROCKTYPES_TABLE)

        c.execute(CREATE_UNITS_TABLE)

        c.execute(CREATE_AGESIGNATURES_TABLE)

        c.execute(CREATE_AGES_TABLE)

        c.execute(CREATE_SAMPLES_TABLE)

        c.execute(CREATE_UPBDATA_TABLE)

        c.execute(CREATE_GEOCHEMDATA_TABLE)

        # Populate the age table during initiation
        sql = '''SELECT * FROM Ages'''
        if c.execute(sql):
            out = c.fetchall()
            if not out:
                populate_ages(conn)
        else:
            print(f'query failed')


def populate_ages(conn):
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
                                                f'SELECT "Age ID" FROM AGES WHERE "Age name" = "{epoch_name}" ORDER BY "Age ID" DESC'):
                                            out = c.fetchall()
                                            epoch_id = out[0][0]
                                            age_item = (epoch_id, f'{age.get("name")}', f'{age.get("oldest")}',
                                                        f'{age.get("youngest")}')
                                            add_age(c, age_item)


def add_age(c, age):
    sql = '''INSERT INTO Ages("Parent age ID", "Age name", "Max Ma", "Min Ma")
                    VALUES(?,?,?,?)'''
    values = (age[0], age[1], age[2], age[3])
    c.execute(sql, values)


def list_tables(db_file):
    """Create a new source in the sources table
    :param conn:
    :param source:
    :return: SourceID"""
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        sql = '''SELECT name FROM sqlite_schema 
                WHERE type = "table"
                ORDER BY name'''
        c.execute(sql)
        tables = c.fetchall()
        tablelist = []
        for item in tables:
            table = item[0]
            tablelist.append(table)
        return tablelist


def retrieve_table(query, table):
    """Retrieve the headers and data for the specified table
    :param conn:
    :param table:
    :return: entries, headers"""
    sql = f'SELECT * FROM "{table}"'  # table name must be in "" to catch spaces in table names
    query.exec(sql)
    data = []
    while query.next():
        data.append(query.value)
    return data


def create_source(conn, source):
    """

    :param conn:
    :param source:
    :return:
    """
    c = conn.cursor()
    sql = '''INSERT INTO sources(Authors,Year,Title,Source,doi,"Short Citation")
            VALUES(?,?,?,?,?,?)'''
    c.execute(sql, source)
    conn.commit()
    return c.lastrowid


def commit_changes(conn, model_list):
    # look through the table views for edits
    conn.commit()


def main():
    pass


if __name__ == '__main__':
    main()

