import sys
from pathlib import Path
import sqlite3

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from collections import namedtuple

# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'source_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")


class SampleTableModel(QtS.QSqlQueryModel):
    def setupQuery(self):
        # Select lines
        qsample_id = 'S.SampleID'
        qsample_name = 'SampleName AS "Sample Name"'
        qage = 'AverageAge || "±" || COALESCE(AverageAgeError, " ") as "Age (Ma)"'
        qage_range = 'COALESCE(OldestAge, " ") || "-" || COALESCE(YoungestAge, " ") as "Age Range (Ma)"'
        qgeo_age = 'COALESCE(OldA.AgeName, " ") || "-" || COALESCE(YoungA.AgeName, " ") as "Geologic Age"'
        qage_signature = 'GROUP_CONCAT(DISTINCT AgeSignatureName) as "Age Signatures"'
        qcolumn_name = 'GROUP_CONCAT(DISTINCT ColumnName) as "Measured Column Name"'
        qcolumn_data = 'HeightDepth || "±" || COALESCE(HeightDepthError, " " || HeightDepthUnit) as "Column Data"'
        qlat = f'''LatDeg || "°" || LatMin || "'" || LatSec || '"' as "Latitude"'''
        qlon = f'''LonDeg || "°" || LonMin || "'" || LonSec || '"' as "Longitude"'''
        qutm_zone = 'UTMZone As "UTM Zone"'
        qutm_n = 'UTMN As "UTM Northing"'
        qutm_e = 'UTME As "UTM Easting"'
        qelev = 'Elev || "±" || COALESCE(ElevError, " " || ElevUnit) as "Elevation"'
        qaliquots = 'GROUP_CONCAT(DISTINCT AliquotName) as "Aliquots"'
        qspots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        qreferences = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        qcontext = 'GROUP_CONCAT(DISTINCT SampleContextName) as "Sample Contexts"'
        qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) as "Sampling Methods"'
        qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"'
        qregions = 'GROUP_CONCAT(DISTINCT RegionName) as "Regions"'
        qsettings = 'GROUP_CONCAT(DISTINCT SettingName) as "Settings"'
        qunits = 'GROUP_CONCAT(DISTINCT UnitName) as "Units"'
        qupb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        qlabs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'
        qspot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        qaliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Contexts"'

        # Join lines
        old_age_join = 'LEFT JOIN Ages as OldA ON S.OldestAgeID=OldA.AgeID'
        young_age_join = 'LEFT JOIN Ages as YoungA ON S.YoungestAgeID=YoungA.AgeID'
        age_signature_join = '''LEFT JOIN Samples_AgeSignatures as S_AS ON S.SampleID=S_AS.SampleID
                                LEFT JOIN AgeSignatures as AgS ON Ags.AgeSignatureID=S_AS.AgeSignatureID'''
        column_join = '''LEFT JOIN Samples_Columns as S_C ON S.SampleID=S_C.SampleID
                                LEFT JOIN Columns as C ON C.ColumnID=S_C.ColumnID'''
        rock_type_join = '''LEFT JOIN Samples_RockTypes as S_RT ON S.SampleID=S_RT.SampleID
                            LEFT JOIN RockTypes as RT ON RT.RockTypeID=S_RT.RockTypeID'''
        region_join = '''LEFT JOIN Samples_Regions as S_R ON S.SampleID=S_R.SampleID
                            LEFT JOIN Regions as R ON R.RegionID=S_R.RegionID'''
        setting_join = '''LEFT JOIN Samples_Settings as S_ST ON S.SampleID=S_ST.SampleID
                            LEFT JOIN Settings as ST ON ST.SettingID=S_ST.SettingID'''
        unit_join = '''LEFT JOIN Samples_Units as S_U ON S.SampleID=S_U.SampleID
                            LEFT JOIN Units as U ON U.UnitID=S_U.UnitID'''
        sample_context_join = '''LEFT JOIN Samples_SampleContexts as S_SC ON S.SampleID=S_SC.SampleID
                            LEFT JOIN SampleContexts as SC ON SC.SampleContextID=S_SC.SampleContextID'''
        sampling_method_join = '''LEFT JOIN Samples_SamplingMethods as S_SM ON S.SampleID=S_SM.SampleID
                            LEFT JOIN SamplingMethods as SM ON SM.SamplingMethodID=S_SM.SamplingMethodID'''
        aliquot_join = 'LEFT JOIN Aliquots as AQ ON AQ.SampleID=S.SampleID'
        spot_join = 'LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID'
        upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
        source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'
        upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
        labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'
        spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                            LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
        spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
        aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts as AQ_AQCX ON AQ.AliquotID=AQ_AQCX.AliquotID
                            LEFT JOIN AliquotContexts as AQCX ON AQCX.AliquotContextID=AQ_AQCX.AliquotContextID'''

        sample_query = f'''
                    SELECT
                        {qsample_id},
                        {qsample_name},
                        {qlat},
                        {qlon},
                        {qutm_zone},
                        {qutm_n},
                        {qutm_e},
                        {qelev},
                        {qage},
                        {qage_range},
                        {qgeo_age},
                        {qcolumn_name},
                        {qcolumn_data},
                        {qaliquots},
                        {qspots},
                        {qreferences},
                        {qage_signature},
                        {qcontext},
                        {qrock_types},
                        {qregions},
                        {qsampling_methods},
                        {qsettings},
                        {qunits},
                        {qupb_methods},
                        {qlabs},
                        {qspot_context},
                        {qspot_compositions},
                        {qaliquot_context}
                    FROM Samples as S
                    {column_join}
                    {old_age_join}
                    {young_age_join}
                    {age_signature_join}
                    {rock_type_join}
                    {sample_context_join}
                    {aliquot_join}
                    {spot_join}
                    {upb_data_join}
                    {source_join}
                    {region_join}
                    {sampling_method_join}
                    {setting_join}
                    {unit_join}
                    {upb_method_join}
                    {labs_join}
                    {spot_context_join}
                    {spot_composition_join}
                    {aliquot_context_join}
                    GROUP BY SampleName
					ORDER BY S.SampleID
                    '''

        return sample_query


class AliquotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, sample_ID):
        # Select lines
        aliquots = 'AliquotName as "Aliquots"'
        aliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Contexts"'
        spots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

        # Join lines
        aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts as AQ_AQCX ON AQ.AliquotID=AQ_AQCX.AliquotID
                            LEFT JOIN AliquotContexts as AQCX ON AQCX.AliquotContextID=AQ_AQCX.AliquotContextID'''
        spot_join = 'LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID'
        spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                            LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
        spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
        upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
        source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'
        upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
        labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'

        aliquot_query = f'''
                    SELECT
                        {aliquots},
                        {aliquot_context},
                        {spots},
                        {spot_context},
                        {spot_compositions},
                        {references},
                        {upb_methods},
                        {labs}
                    FROM Aliquots as AQ
                    {aliquot_context_join}
                    {spot_join}
                    {spot_context_join}
                    {spot_composition_join}
                    {upb_data_join}
                    {source_join}
                    {upb_method_join}
                    {labs_join}
                    WHERE SampleID = {sample_ID}
                    GROUP BY AliquotName
                    '''

        return aliquot_query


class SpotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, parent_id, id_type='sample'):
        # Select lines
        spots = 'SpotName as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Contexts"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

        # Join lines'
        spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                            LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
        spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
        upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
        source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'
        upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
        labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'

        # Where statement
        if id_type == 'sample':
            where = f'WHERE SampleID = {parent_id}'
        elif id_type == 'aliquot':
            where = f'WHERE AliquotID = {parent_id}'
        else:
            return 'Error - must select a parent ID'

        spot_query = f'''
                    SELECT
                        {spots},
                        {spot_context},
                        {spot_compositions},
                        {references},
                        {upb_methods},
                        {labs}
                    FROM Spots as SP
                    {spot_context_join}
                    {spot_composition_join}
                    {upb_data_join}
                    {source_join}
                    {upb_method_join}
                    {labs_join}
                    {where}
                    GROUP BY SpotName
                    '''

        return spot_query

class ComboList(QtW.QComboBox):
    def __init__(self, parent, model):
        super().__init__(parent)
        self.setModel(model)
        self.currentTextChanged.connect(self.combo_value)

    def combo_value(self):
        print(self.currentText())

# class table_proxy_model(QtC.QSortFilterProxyModel):
#     def __int__(self):
#         super().__init__()
#
#         sourceModel.dataChanged.connect(self.sourceDataChanged)
#
#     def sourceDataChanged(self, ):
