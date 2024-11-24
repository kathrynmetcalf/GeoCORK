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
        c.execute('DELETE FROM SampleAges')
        c.execute('DELETE FROM GPSLocations')
        c.execute('DELETE FROM RockTypes')
        c.execute('DELETE FROM Samples_RockTypes')
        c.execute('DELETE FROM AgeSignatures')
        c.execute('DELETE FROM Samples_AgeSignatures')
        c.execute('DELETE FROM Units')
        c.execute('DELETE FROM Samples_Units')
        c.execute('DELETE FROM Aliquots')
        c.execute('DELETE FROM Spots')
        c.execute('DELETE FROM Sources')
        c.execute('DELETE FROM UPbAnalyses')
        c.execute('INSERT INTO RockTypes (RockTypeName, RockTypeDescription) '
                  'VALUES("Sedimentary", "Sedimentary rocks types")')
        c.execute('INSERT INTO RockTypes (ParentRockTypeID, RockTypeParentRow, RockTypeName, RockTypeDescription) '
                  'VALUES(1, 1, "Sandstone", "All types")')
        c.execute('INSERT INTO RockTypes (ParentRockTypeID, RockTypeParentRow, RockTypeName, RockTypeDescription) '
                  'VALUES(1, 0, "Siliciclastic matrix", "Mélange matrix")')
        c.execute('INSERT INTO RockTypes (RockTypeName, RockTypeDescription) '
                  'VALUES("Tuffaceous chert", "Chert with volcanic tuff")')
        c.execute('''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeErrorTypeID, DirectAgeUnitID, OldestAgeID, YoungestAgeID)
                    VALUES(59, 3, 1, 2, 31, 27)''')
        c.execute('''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeErrorTypeID, DirectAgeUnitID, OldestAgeID, YoungestAgeID)
                    VALUES(450, 10, 1, 2, 128, 105)''')
        c.execute('''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeErrorTypeID, DirectAgeUnitID, OldestAgeID, YoungestAgeID)
                    VALUES(18, 1.5, 2, 3, 128, 105)''')
        c.execute('''INSERT INTO GPSLocations(GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                    VALUES(33, 59, 34, NULL, -118, 8, 36, NULL, NULL, NULL, NULL, 5, 3545, 5, 2)''')
        c.execute('''INSERT INTO GPSLocations(GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                    VALUES(36.457692, NULL, NULL, 1, 118.004853, NULL, NULL, 4, NULL, NULL, NULL, 2, 332, 5, 8)''')
        c.execute('''INSERT INTO GPSLocations(GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                    VALUES(NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 11, 3748866.146, 417512.996, 7, 332, 5, 2)''')
        c.execute('''INSERT INTO Samples (SampleName, SampleGPSLocationID, SampleDescription) VALUES ("S1", 1, "Sample 3")''')
        c.execute('''INSERT INTO Samples (SampleName, SampleGPSLocationID, SampleDescription) VALUES ("S2", 2, "Sample 2")''')
        c.execute('''INSERT INTO Samples (SampleName, SampleGPSLocationID, SampleDescription) VALUES ("S3", 3, "Sample 1")''')
        c.execute('INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES(1, 1)')
        c.execute('INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES(2, 2)')
        c.execute('INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES(3, 3)')
        c.execute('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(1, 1)')
        c.execute('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(1, 2)')
        c.execute('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(2, 2)')
        c.execute('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
                  'VALUES("Triassic", "Young Triassic peak")')
        c.execute('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
                  'VALUES("Gondwanan", "Consistent with Gondwana affinity")')
        c.execute('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
                  'VALUES("Asian", "Consistent with Asian affinity")')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(1, 1)')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(1, 2)')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(2, 2)')
        c.execute('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(2, 3)')
        c.execute('INSERT INTO Units (UnitParentRow, UnitName, UnitDescription) VALUES (0, "Xigaze Group", "Lower Xigaze forearc")')
        c.execute('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                        VALUES (1, 2, "Sangzugang Formation", "Basal Xigaze Group")''')
        c.execute('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                        VALUES (1, 1, "Chongdoi Formation", "Middle Xigaze Group")''')
        c.execute('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                        VALUES (1, 0, "Ngamring Formation", "Upper Xigaze Group")''')
        c.execute('INSERT INTO Units (UnitParentRow, UnitName, UnitDescription) VALUES (1, "Tso-Jiangding Group", "Upper Xigaze forearc")')
        c.execute('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                        VALUES (5, 3, "Padana Formation", "Basal Tso-Jiangding Group")''')
        c.execute('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                        VALUES (5, 2, "Qubeiya Formation", "Middle Tso-Jiangding Group")''')
        c.execute('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                        VALUES (5, 1, "Quxia Formation", "Upper Tso-Jiangding Group")''')
        c.execute('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                        VALUES (5, 0, "Jialazi Formation", "Upper Tso-Jiangding Group")''')
        c.execute('INSERT INTO Aliquots (AliquotName, SampleID) VALUES("S1", 1)')
        c.execute('INSERT INTO Aliquots (AliquotName, SampleID) VALUES("S2", 1)')
        c.execute('INSERT INTO Aliquots (AliquotName, SampleID) VALUES("S3", 1)')
        c.execute('INSERT INTO Spots (SpotName, AliquotID) VALUES("S1_1", 1)')
        c.execute('INSERT INTO Spots (SpotName, AliquotID) VALUES("S2_2", 1)')
        c.execute('INSERT INTO Spots (SpotName, AliquotID) VALUES("S3_3", 1)')
        c.execute('''INSERT INTO Sources (Authors, Year, ShortCitation) 
                  VALUES("Kathryn Metcalf, Paul Kapp",2019,"Metcalf and Kapp, 2019")''')
        c.execute('''INSERT INTO UPbAnalyses (SpotID, SourceID, "U/Th", "206Pb/238UAge", "206Pb/238UAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "207Pb/206PbAge", "207Pb/206PbAgeError", "AgeErrorTypeID", "AgeUnitID") 
                    VALUES(1, 1, 325, 59, 3, 58, 8, 77, 20, 1, 2)''')
        c.execute('''INSERT INTO UPbAnalyses (SpotID, SourceID, "Th/U", "206Pb/238UAge", "206Pb/238UAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "207Pb/206PbAge", "207Pb/206PbAgeError", "AgeErrorTypeID", "AgeUnitID")
                    VALUES(1, 1, 0.0435, 450, 10, 445, 20, 600, 30, 1, 2)''')
        c.execute('''INSERT INTO UPbAnalyses (SpotID, SourceID, "206Pb/238UAge", "206Pb/238UAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "207Pb/206PbAge", "207Pb/206PbAgeError", "AgeErrorTypeID", "AgeUnitID")
                    VALUES(1, 1, 18, 1.5, 17, 2, 25, 5, 2, 3)''')


if __name__ == '__main__':
    db_file = '../novschema.db'
    add_data(db_file)
