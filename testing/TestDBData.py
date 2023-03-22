import sqlite3


def add_data(db_file):
    """
    Connect to the database and execute the sql strings defined above to add data to the database for testing
    :param db_file: Database file with full path
    """
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        c.execute('DELETE FROM Samples')
        c.execute('INSERT INTO Samples (SampleName, AverageAge, OldestAgeID, YoungestAgeID, '
                  'LatDeg, LatMin, LatSec, LonDeg, LonMin, LonSec) '
                  'VALUES("S1", 230, 68, 42, 33, 59, 34, -118, 8, 36)')
        c.execute('INSERT INTO Samples (SampleName, AverageAge, OldestAgeID, YoungestAgeID) VALUES("S2", 59, 28, 28)')
        c.execute('INSERT INTO Samples (SampleName) VALUES("S3")')
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
        c.execute('DELETE FROM Aliquots')
        c.execute('INSERT INTO Aliquots (AliquotName, SampleID) VALUES("S1", 1)')
        c.execute('DELETE FROM Spots')
        c.execute('INSERT INTO Spots (SpotName, AliquotID) VALUES("S1_1", 1)')
        c.execute('INSERT INTO Spots (SpotName, AliquotID) VALUES("S1_2", 1)')
        c.execute('INSERT INTO Spots (SpotName, AliquotID) VALUES("S1_3", 1)')
        c.execute('DELETE FROM Sources')
        c.execute('INSERT INTO Sources (Authors, Year, ShortCitation) '
                  'VALUES("Kathryn Metcalf, Paul Kapp",2019,"Metcalf and Kapp, 2019")')
        c.execute('DELETE FROM UPbData')
        c.execute('INSERT INTO UPbData (SpotID, SourceID) VALUES(1, 1)')
        c.execute('INSERT INTO UPbData (SpotID, SourceID) VALUES(2, 1)')
        c.execute('INSERT INTO UPbData (SpotID, SourceID) VALUES(3, 1)')


if __name__ == '__main__':
    db_file = '../TestSchema.db'
    add_data(db_file)
