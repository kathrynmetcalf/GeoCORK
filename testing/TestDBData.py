import sqlite3

samples = '''
            INSERT INTO Samples (SampleName, AverageAge)
            VALUES("S1", 200)
            '''


def add_data(db_file):
    """
    Connect to the database and execute the sql strings defined above to add data to the database for testing
    :param db_file: Database file with full path
    """
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        c.execute('DELETE FROM Samples')
        c.execute('INSERT INTO Samples (SampleName, AverageAge) VALUES("S1", 230)')
        c.execute('INSERT INTO Samples (SampleName, AverageAge) VALUES("S2", 59)')
        c.execute('DELETE FROM RockTypes')
        c.execute('INSERT INTO RockTypes (RockTypeName, RockTypeDescription) '
                  'VALUES("Sandstone", "All types")')
        c.execute('INSERT INTO RockTypes (RockTypeName, RockTypeDescription) '
                  'VALUES("Siliciclastic matrix", "Melange matrix")')
        c.execute('INSERT INTO RockTypes (RockTypeName, RockTypeDescription) '
                  'VALUES("Tuffaceous chert", "Chert with volcanic tuff")')
        c.execute('DELETE FROM Samples_RockTypes')
        c.execute('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(1, 1)')
        c.execute('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(1, 2)')
        c.execute('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(2, 2)')
        c.execute('DELETE FROM AgeSignatures')
        c.execute('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
                  'VALUES("Triassic", "Young Triassic peak")')
        c.execute('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
                  'VALUES("Gondwanan", "Consistent with Gondwana affinity")')
        c.execute('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
                  'VALUES("Asian", "Consistent with Asian affinity")')
        c.execute('DELETE FROM Samples_AgeSignatures')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(1, 1)')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(1, 2)')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(2, 2)')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(2, 3)')


if __name__ == '__main__':
    db_file = '../TestSchema.db'
    add_data(db_file)
