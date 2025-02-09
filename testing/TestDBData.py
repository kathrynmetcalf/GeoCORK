import sqlite3
import PyQt6
from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from Functions.Widget_classes import get_headers, get_column_types

def add_data(db_file):
    """
    Connect to the database and execute the sql strings defined above to add data to the database for testing
    :param db_file: Database file with full path
    """
    db = QtS.QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(db_file)
    ok = db.open()
    query = QtS.QSqlQuery(db)
    query.exec('DELETE FROM Samples')
    query.exec('DELETE FROM SampleAges')
    query.exec('DELETE FROM GPSLocations')
    query.exec('DELETE FROM RockTypes')
    query.exec('DELETE FROM Samples_RockTypes')
    query.exec('DELETE FROM AgeSignatures')
    query.exec('DELETE FROM Samples_AgeSignatures')
    query.exec('DELETE FROM Units')
    query.exec('DELETE FROM Samples_Units')
    query.exec('DELETE FROM Aliquots')
    query.exec('DELETE FROM Spots')
    query.exec('DELETE FROM "References"')
    query.exec('DELETE FROM UPbAnalyses')
    query.exec('INSERT INTO RockTypes (RockTypeName, RockTypeDescription) '
              'VALUES("Sedimentary", "Sedimentary rocks types")')
    query.exec('INSERT INTO RockTypes (ParentRockTypeID, RockTypeParentRow, RockTypeName, RockTypeDescription) '
              'VALUES(1, 1, "Sandstone", "All types")')
    query.exec('INSERT INTO RockTypes (ParentRockTypeID, RockTypeParentRow, RockTypeName, RockTypeDescription) '
              'VALUES(1, 0, "Siliciclastic matrix", "Mélange matrix")')
    query.exec('INSERT INTO RockTypes (RockTypeName, RockTypeDescription) '
              'VALUES("Tuffaceous chert", "Chert with volcanic tuff")')
    query.exec('''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeErrorTypeID, DirectAgeUnitID, OldestAgeID, YoungestAgeID)
                VALUES(59, 3, 1, 2, 31, 27)''')
    query.exec('''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeErrorTypeID, DirectAgeUnitID, OldestAgeID, YoungestAgeID)
                VALUES(450, 10, 1, 2, 128, 105)''')
    query.exec('''INSERT INTO SampleAges (DirectAge, DirectAgeError, DirectAgeErrorTypeID, DirectAgeUnitID, OldestAgeID, YoungestAgeID)
                VALUES(18, 1.5, 2, 3, 128, 105)''')
    query.exec('''INSERT INTO GPSLocations(GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                VALUES(33, 59, 34, NULL, -118, 8, 36, NULL, NULL, NULL, NULL, 5, 3545, 5, 2)''')
    query.exec('''INSERT INTO GPSLocations(GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                VALUES(36.457692, NULL, NULL, 1, 118.004853, NULL, NULL, 4, NULL, NULL, NULL, 2, 332, 5, 8)''')
    query.exec('''INSERT INTO GPSLocations(GPSLatDeg, GPSLatMin, GPSLatSec, GPSLatDirectionID, GPSLonDeg, GPSLonMin, GPSLonSec, GPSLonDirectionID, GPSUTMZone, GPSUTMN, GPSUTME, GPSFormatID, GPSElev, GPSElevError, GPSElevUnitID)
                VALUES(NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 11, 3748866.146, 417512.996, 7, 332, 5, 2)''')
    query.exec('''INSERT INTO Samples (SampleName, SampleGPSLocationID, DefaultSampleAgeID, SampleDescription) VALUES ("S1", 1, 3, "Sample 3")''')
    query.exec('''INSERT INTO Samples (SampleName, SampleGPSLocationID, DefaultSampleAgeID, SampleDescription) VALUES ("S2", 2, 2, "Sample 2")''')
    query.exec('''INSERT INTO Samples (SampleName, SampleGPSLocationID, DefaultSampleAgeID, SampleDescription) VALUES ("S3", 3, 3, "Sample 1")''')
    # query.exec('UPDATE Samples SET HeightDepth = 8, HeightDepthUnitID = 5 WHERE SampleID = 1')
    query.exec('INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES(1, 1)')
    query.exec('INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES(2, 2)')
    query.exec('INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES(3, 3)')
    query.exec('INSERT INTO Samples_SampleAges (SampleID, SampleAgeID) VALUES(1, 3)')
    query.exec('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(1, 1)')
    query.exec('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(1, 2)')
    query.exec('INSERT INTO Samples_RockTypes (SampleID, RockTypeID) VALUES(2, 2)')
    query.exec('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
              'VALUES("Triassic", "Young Triassic peak")')
    query.exec('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
              'VALUES("Gondwanan", "Consistent with Gondwana affinity")')
    query.exec('INSERT INTO AgeSignatures (AgeSignatureName, AgeSignatureDescription) '
              'VALUES("Asian", "Consistent with Asian affinity")')
    query.exec('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(1, 1)')
    query.exec('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(1, 2)')
    query.exec('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(2, 2)')
    query.exec('INSERT INTO Samples_AgeSignatures (SampleID, AgeSignatureID) VALUES(2, 3)')
    query.exec('INSERT INTO Units (UnitParentRow, UnitName, UnitDescription) VALUES (0, "Xigaze Group", "Lower Xigaze forearc")')
    query.exec('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                    VALUES (1, 2, "Sangzugang Formation", "Basal Xigaze Group")''')
    query.exec('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                    VALUES (1, 1, "Chongdoi Formation", "Middle Xigaze Group")''')
    query.exec('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                    VALUES (1, 0, "Ngamring Formation", "Upper Xigaze Group")''')
    query.exec('INSERT INTO Units (UnitParentRow, UnitName, UnitDescription) VALUES (1, "Tso-Jiangding Group", "Upper Xigaze forearc")')
    query.exec('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                    VALUES (5, 3, "Padana Formation", "Basal Tso-Jiangding Group")''')
    query.exec('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                    VALUES (5, 2, "Qubeiya Formation", "Middle Tso-Jiangding Group")''')
    query.exec('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                    VALUES (5, 1, "Quxia Formation", "Upper Tso-Jiangding Group")''')
    query.exec('''INSERT INTO Units (ParentUnitID, UnitParentRow, UnitName, UnitDescription) 
                    VALUES (5, 0, "Jialazi Formation", "Upper Tso-Jiangding Group")''')
    query.exec('INSERT INTO Aliquots (AliquotName, SampleID) VALUES("S1", 1)')
    query.exec('INSERT INTO Aliquots (AliquotName, SampleID) VALUES("S2", 1)')
    query.exec('INSERT INTO Aliquots (AliquotName, SampleID) VALUES("S3", 1)')
    query.exec('INSERT INTO Spots (SpotName, AliquotID) VALUES("S1_1", 1)')
    query.exec('INSERT INTO Spots (SpotName, AliquotID) VALUES("S2_2", 1)')
    query.exec('INSERT INTO Spots (SpotName, AliquotID) VALUES("S3_3", 1)')
    query.exec('''INSERT INTO "References" (Authors, Year, Source) 
              VALUES("Kathryn Metcalf, Paul Kapp",2019,"Geological Society of London")''')
    query.exec('''INSERT INTO UPbAnalyses (SpotID, ReferenceID, "U/Th", "206Pb/238UAge", "206Pb/238UAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "207Pb/206PbAge", "207Pb/206PbAgeError", "AgeErrorTypeID", "AgeUnitID") 
                VALUES(1, 1, 325, 59, 3, 58, 8, 77, 20, 1, 2)''')
    query.exec('''INSERT INTO UPbAnalyses (SpotID, ReferenceID, "Th/U", "206Pb/238UAge", "206Pb/238UAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "207Pb/206PbAge", "207Pb/206PbAgeError", "AgeErrorTypeID", "AgeUnitID")
                VALUES(1, 1, 0.0435, 450, 10, 445, 20, 600, 30, 1, 2)''')
    query.exec('''INSERT INTO UPbAnalyses (SpotID, ReferenceID, "206Pb/238UAge", "206Pb/238UAgeError", "207Pb/235UAge", "207Pb/235UAgeError", "207Pb/206PbAge", "207Pb/206PbAgeError", "AgeErrorTypeID", "AgeUnitID")
                VALUES(1, 1, 18, 1.5, 17, 2, 25, 5, 2, 3)''')

import sqlite3
from random import randint, randrange

from PyQt6 import QtSql as QtS

def add_upb_data(db_file):
    db = QtS.QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(db_file)
    if db.open():
        query = QtS.QSqlQuery()
        headers = get_headers('UPbAnalyses')
        header_types = get_column_types('UPbAnalyses')
        headers.pop(0)
        header_types.pop(0)
        quoted_headers = [f'"{header}"' for header in headers]
        query_placeholders = ", ".join(['?' for _ in headers])
        query_headers = ", ".join(quoted_headers)
        for entry in range(100):
            values = []
            for header, header_type in zip(headers, header_types):
                if 'ID' in header:
                    values.append(1)
                elif 'Rejected' in header:
                    values.append(0)
                elif header_type == 'INTEGER':
                    values.append(randint(0, 100))
                elif header_type == 'REAL':
                    values.append(randrange(0, 100, 1))
                elif header_type == 'DATETIME':
                    current_datetime = QtC.QDateTime.currentDateTime()
                    values.append(current_datetime)
                else:
                    values.append(''.join(chr(randint(0, 100)) for _ in range(10)))
            query.prepare(f'INSERT INTO UPbAnalyses ({query_headers}) VALUES ({query_placeholders})')
            for i, value in enumerate(values):
                query.bindValue(i, value)
            if not query.exec():
                print('Error inserting data:', query.lastError().text())
                return
    db.close()


if __name__ == '__main__':
    db_file = '../dec_schema.db'
    app = QtC.QCoreApplication([])
    add_data(db_file)
    add_upb_data(db_file)
