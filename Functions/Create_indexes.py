import sqlite3

'''Commands to create the database indexes'''
'''SQL strings to create each index'''

'''Indexes to improve search performance'''
SEARCH_INDEXES = '''

'''

def create_indexes(db_file):
    """
    Connect to the database and execute the sql strings defined above to create the database indexes
    :param db_file: Database file with full path
    """
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()

        c.execute(SEARCH_INDEXES)

if __name__ == '__main__':
    db_file = '../TestSchema.db'
    create_indexes(db_file)