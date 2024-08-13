import sys
from pathlib import Path
import sqlite3
# import pandas as pd
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS


class Window(QtW.QWidget):
    def __init__(self):
        super().__init__()
        self.db_file = '../DataTestSchema.db'
        self.db = QtS.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(self.db_file)

        self.view = QtW.QTableView()
        self.query = 'SELECT * FROM Sources'
        # self.query = '''SELECT
        #         SampleName AS "Sample Name",
        #         AverageAge || "±" || COALESCE(AverageAgeError, " ") as "Age (Ma)",
        #         COALESCE(OldestAge, " ") || "-" || COALESCE(YoungestAge, " ") as "Age Range (Ma)",
        #         COALESCE(OldA.AgeName, " ") || "-" || COALESCE(YoungA.AgeName, " ") as "Geologic Age",
        #         ColumnName as "Measured Column Name",
        #         HeightDepth || "±" || COALESCE(HeightDepthError, " " || HeightDepthUnit) as "Column Data",
        #         LatDeg || "°" || LatMin || ' || LatSec || " as "Latitude",
        #         LonDeg || "°" || LonMin || ' || LonSec || " as "Longitude",
        #         GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots",
        #         GROUP_CONCAT(DISTINCT SpotName) as "Spots",
        #         GROUP_CONCAT(DISTINCT ShortCitation) as "References",
        #         GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures",
        #         GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"
        #         FROM Samples as S
        #         LEFT JOIN Columns as C ON C.ColumnID=S.ColumnID
        #         LEFT JOIN Ages as OldA ON S.OldestAgeID=OldA.AgeID
        #         LEFT JOIN Ages as YoungA ON S.YoungestAgeID=YoungA.AgeID
        #         LEFT JOIN Samples_AgeSignatures as S_AS ON S.SampleID=S_AS.SampleID
        #         LEFT JOIN AgeSignatures as AgS ON Ags.AgeSignatureID=S_AS.AgeSignatureID
        #         LEFT JOIN Samples_RockTypes as S_RT ON S.SampleID=S_RT.SampleID
        #         LEFT JOIN RockTypes as RT ON RT.RockTypeID=S_RT.RockTypeID
        #         LEFT JOIN Aliquots as AQ ON AQ.SampleID=S.SampleID
        #         LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID
        #         LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID
        #         LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID
        #         GROUP BY SampleName'''
        if self.db.open():
            print('db opened')
            dataView = self.displayData(self.query)
            dataView.show()
        else:
            print('db did not open')



    def displayData(self, sqlStatement):
        print('processing query...')
        qry = QtS.QSqlQuery(self.db)
        qry.prepare(sqlStatement)
        qry.exec()

        model = QtS.QSqlQueryModel()
        model.setQuery(qry)

        view = QtW.QTableView()
        view.setModel(model)
        return view


if __name__ == "__main__":
    app = QtW.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
