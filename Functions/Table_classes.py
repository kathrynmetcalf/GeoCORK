import sys
from pathlib import Path
import sqlite3

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS


class SampleTableModel(QtS.QSqlQueryModel):
    def setupQuery(self):
        # Select lines
        sample_name = 'SampleName AS "Sample Name"'
        age = 'AverageAge || "±" || COALESCE(AverageAgeError, " ") as "Age (Ma)"'
        age_range = 'COALESCE(OldestAge, " ") || "-" || COALESCE(YoungestAge, " ") as "Age Range (Ma)"'
        geo_age = 'COALESCE(OldA.AgeName, " ") || "-" || COALESCE(YoungA.AgeName, " ") as "Geologic Age"'
        column_name = 'ColumnName as "Measured Column Name"'
        column_data = 'HeightDepth || "±" || COALESCE(HeightDepthError, " " || HeightDepthUnit) as "Column Data"'
        lat = f'LatDeg || "°" || LatMin || \' || LatSec || \" as "Latitude"'
        lon = f'LonDeg || "°" || LonMin || \' || LonSec || \" as "Longitude"'
        aliquots = 'GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots"'
        spots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        age_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures"'
        rock_type = 'GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"'

        # Join lines
        column_join = 'LEFT JOIN Columns as C ON C.ColumnID=S.ColumnID'
        old_age_join = 'LEFT JOIN Ages as OldA ON S.OldestAgeID=OldA.AgeID'
        young_age_join = 'LEFT JOIN Ages as YoungA ON S.YoungestAgeID=YoungA.AgeID'
        age_signature_join = '''LEFT JOIN Samples_AgeSignatures as S_AS ON S.SampleID=S_AS.SampleID
                                LEFT JOIN AgeSignatures as AgS ON Ags.AgeSignatureID=S_AS.AgeSignatureID'''
        rock_type_join = '''LEFT JOIN Samples_RockTypes as S_RT ON S.SampleID=S_RT.SampleID
                            LEFT JOIN RockTypes as RT ON RT.RockTypeID=S_RT.RockTypeID'''
        aliquot_join = 'LEFT JOIN Aliquots as AQ ON AQ.SampleID=S.SampleID'
        spot_join = 'LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID'
        upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
        source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'

        # Omit lat/lon for now
        sample_query = f'''
                    SELECT 
                        {sample_name},
                        {age},
                        {age_range},
                        {geo_age},
                        {column_name},
                        {column_data},
                        {aliquots},
                        {spots},
                        {references},
                        {age_signature},
                        {rock_type}
                    FROM Samples as S
                    {column_join}
                    {old_age_join}
                    {young_age_join}
                    {age_signature_join}
                    {rock_type_join}
                    {aliquot_join}
                    {spot_join}
                    {upb_data_join}
                    {source_join}
                    GROUP BY SampleName
                    '''

        return sample_query


