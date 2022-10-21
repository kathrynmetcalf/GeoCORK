import sqlite3


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

