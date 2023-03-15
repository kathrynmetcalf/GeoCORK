import sys
from pathlib import Path
import sqlite3

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS


class SampleTableModel(QtS.QSqlQueryModel):
    tag_IDs = ["Age Signature ID",]
    tag_names = [AgeSignatures, ]
    tables = ["Samples_AgeSignatures", "Samples_Columns", ""]

    def __init__(self, filename):
        super().__init__()
        setup_query = '''
                    SELECT 
                        SampleName as "Sample Name",
                        ColumnName as "Measured Column Name"
                        
                        GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures"
                        GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"
                    FROM Samples as S
                    LEFT JOIN Columns as C
                        ON C.ColumnID=S.ColumnID
                    LEFT JOIN Samples_AgeSignatures as S_AS
                        ON S.SampleID=S_AS.SampleID
                    LEFT JOIN AgeSignatures as AgS
                        ON Ags.AgeSignatureID=S_AS.AgeSignatureID
                    LEFT JOIN Samples_RockTypes as S_RT
                        ON S.SampleID=S_RT.SampleID
                    LEFT JOIN RockTypes as RT
                        ON RT.RockTypeID=S_RT.RockTypeID
                    LEFT JOIN Aliquots as AQ
                        ON AQ.SampleID=S.SampleID
                    GROUP BY SampleName
                    '''
    def get_tags(self, tag_name, tag_table, table):
        all_tags = f'Select {tag_name} FROM {table}'
