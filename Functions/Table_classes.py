import sys
from pathlib import Path
import sqlite3

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS


class SampleTableModel(QtS.QSqlQueryModel):
    # tag_IDs = ["Age Signature ID",]
    # tag_names = [AgeSignatures, ]
    # tables = ["Samples_AgeSignatures", "Samples_Columns", ""]

    def __init__(self, db_file):
        super().__init__()

        # Select lines
        sample_name = 'SampleName AS "Sample Name"'
        age = 'AverageAge || "±" || COALESCE(AverageAgeError, " ") as "Age (Ma)"'
        age_range = 'COALESCE(OldestAge, " ") || "-" || COALESCE(YoungestAge, " ") as "Age Range (Ma)"'
        geo_age = 'COALESCE(OldA.AgeName, " ") || "-" || COALESCE(YoungA.AgeName, " ") as "Geologic Age"'
        column_name = 'ColumnName as "Measured Column Name"'
        column_data = 'HeightDepth || "±" || COALESCE(HeightDepthError, " " || HeightDepthUnit) as "Column Data"'
        lat = f'LatDeg || "°" || LatMin || \' || LatSec || \" as "Latitude"'
        lon = f'LonDeg || "°" || LonMin || \' || LonSec || \" as "Longitude"'

        # Join lines
        column_join = 'LEFT JOIN Columns as C ON C.ColumnID=S.ColumnID'
        old_age_join = 'LEFT JOIN Ages as OldA ON S.OldestAgeID=OldA.AgeID'
        young_age_join = 'LEFT JOIN Ages as YoungA ON S.YoungestAgeID=YoungA.AgeID'


        setup_query = f'''
                    SELECT 
                        {sample_name},
                        {age},
                        {age_range},
                        {geo_age},
                        {column_name},
                        {column_data}
                    FROM Samples as S
                    {column_join}
                    {old_age_join}
                    {young_age_join}

                    GROUP BY SampleName
                    '''

        conn = sqlite3.connect(db_file)
        with conn:
            c = conn.cursor()
            c.execute(setup_query)

    # def get_tags(self, tag_name, tag_table, table):
    #     all_tags = f'Select {tag_name} FROM {table}'
# GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots",
# GROUP_CONCAT(DISTINCT SpotName) as "Spots",
# GROUP_CONCAT(DISTINCT ShortCitation) as "References",
# GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures",
# GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"
# LEFT JOIN Samples_AgeSignatures as S_AS
#     ON S.SampleID=S_AS.SampleID
# LEFT JOIN AgeSignatures as AgS
#     ON Ags.AgeSignatureID=S_AS.AgeSignatureID
# LEFT JOIN Samples_RockTypes as S_RT
#     ON S.SampleID=S_RT.SampleID
# LEFT JOIN RockTypes as RT
#     ON RT.RockTypeID=S_RT.RockTypeID
# LEFT JOIN Aliquots as AQ
#     ON AQ.SampleID=S.SampleID
# LEFT JOIN Spots as SP
#     ON SP.AliquotID=AQ.AliquotID
# LEFT JOIN UPbData as UPB
#     ON UPB.SpotID=SP.SpotID
# LEFT JOIN Sources as SO
#     ON SO.SourceID=UPB.SourceID
