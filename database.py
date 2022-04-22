import sqlite3
from sqlite3 import Error

'''Commands to define, create, modify, and query the database
Foreign keys are set to cascade on update, null on delete'''

CREATE_SAMPLES_TABLE = """CREATE TABLE IF NOT EXISTS Samples(
                    "Sample ID" INTEGER PRIMARY KEY,
                    "Sample name" TEXT,
                    "Source ID" INTEGER,
                    "Best ages ID" INTEGER,
                    "Age signature ID" INTEGER, 
                    "UPb data ID" INTEGER, 
                    "GeoChem data ID" INTEGER,
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
                    "Height depth unit" TEXT,
                    "Lat deg" REAL,
                    "Lat min" REAL,
                    "Lat sec" REAL,
                    "Lon deg" REAL,
                    "Lon min" REAL,
                    "Lon sec" REAL,
                    "Elev" REAL,
                    "Elev unit" TEXT,
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
                    FOREIGN KEY ("UPb data ID") REFERENCES "UPb Data" ("UPb data ID")
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
                    Name TEXT,
                    Description TEXT
                    )'''

CREATE_SETTINGS_TABLE = '''CREATE TABLE IF NOT EXISTS Settings(
                    "Setting ID" INTEGER PRIMARY KEY,
                    Name TEXT,
                    Description TEXT
                    )'''

CREATE_ROCKTYPES_TABLE = '''CREATE TABLE IF NOT EXISTS "Rock Types"(
                    "Rock type ID" INTEGER PRIMARY KEY,
                    Name TEXT,
                    Description TEXT
                    )'''

CREATE_UNITS_TABLE = '''CREATE TABLE IF NOT EXISTS Units(
                    "Unit ID" INTEGER PRIMARY KEY,
                    Name TEXT,
                    Description TEXT
                    )'''

CREATE_AGES_TABLE = '''CREATE TABLE IF NOT EXISTS "Ages"(
                    "Age ID" INTEGER PRIMARY KEY,
                    Name TEXT,
                    "Max Ma" REAL,
                    "Min Ma" REAL
                    )'''

CREATE_AGESIGNATURES_TABLE = '''CREATE TABLE IF NOT EXISTS "Age Signatures"(
                    "Age signature ID" INTEGER PRIMARY KEY,
                    Name TEXT,
                    Description TEXT
                    )'''

CREATE_UPBDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "UPb Data"(
                    "UPb data ID" INTEGER PRIMARY KEY,
                    "Sample ID" INTEGER,
                    "Best age" REAL
                    )'''
CREATE_GEOCHEMDATA_TABLE = '''CREATE TABLE IF NOT EXISTS "Geochem Data"(
                    "Geochem data ID" INTEGER PRIMARY KEY,
                    "Sample ID" INTEGER,
                    Name TEXT,
                    Description TEXT
                    )'''


# Commands and queries
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_tables(conn):
    c = conn.cursor()

    c.execute(CREATE_SOURCES_TABLE)

    c.execute(CREATE_REGIONS_TABLE)

    c.execute(CREATE_SETTINGS_TABLE)

    c.execute(CREATE_ROCKTYPES_TABLE)

    c.execute(CREATE_UNITS_TABLE)

    c.execute(CREATE_AGESIGNATURES_TABLE)

    c.execute(CREATE_AGES_TABLE)

    c.execute(CREATE_UPBDATA_TABLE)

    c.execute(CREATE_GEOCHEMDATA_TABLE)

    c.execute(CREATE_SAMPLES_TABLE)


def list_tables(conn):
    """Create a new source in the sources table
    :param conn:
    :param source:
    :return: SourceID"""
    c = conn.cursor()
    sql = '''SELECT name FROM sqlite_schema 
            WHERE type = "table" AND name NOT LIKE "%Data%" 
            ORDER BY name'''
    c.execute(sql)
    tables = c.fetchall()
    tablelist = []
    for item in tables:
        table = item[0]
        tablelist.append(table)
    return tablelist


def retrieve_table(conn, table):
    """Retrieve the headers and data for the specified table
    :param conn:
    :param table:
    :return: entries, headers"""
    c = conn.cursor()
    sql = f'SELECT * FROM "{table}"'  # table name must be in "" to catch spaces in table names
    data = c.execute(sql)
    headers = []
    for column in data.description:
        if 'ID' not in column[0]:  # omit columns with keys
            headers.append(column[0])
    #     else:
    #         if table is 'Samples':
    #             if column[0] is 'Source ID':
    #                 citation =
    # sql = f'SELECT {headers} FROM {table}'
    # c.execute(sql)
    entries = c.fetchall()
    return entries, headers


def create_source(conn, source):
    """Create a new source in the sources table
    :param conn:
    :param source:
    :return: SourceID"""
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
    db_file = 'geochron_samples.db'
    conn = create_connection(db_file)

    if conn is not None:
        create_tables(conn)

        with conn:
            # Create new source
            source = ('Hu et al.', '2016', 'The timing of India-Asia collision onset – Facts, theories, controversies', 'Earth-Science Reviews', '10.1016/j.earscirev.2016.07.014', 'Hu et al., 2016, ESR')
            create_source(conn, source)

    else:
        print("Error! cannot create the database connection.")


if __name__ == '__main__':
    main()

