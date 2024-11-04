import sys
from pathlib import Path
import sqlite3

from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
from PyQt6 import QtGui as QtG
from PyQt6 import QtSql as QtS
from collections import namedtuple

from Functions import SQLUtils

# Map model column names back to database items
table_model_cols = namedtuple('table_model_cols', ['model_col_name', 'source_table', 'table_cols', 'tag_table'])
sample_name = table_model_cols("Sample Name", "Samples", ["SampleName"], '')
age = table_model_cols("Age (Ma)", "Samples", ["AverageAge", "AverageAgeError"], '')
age_signature = table_model_cols("Age Signatures", "AgeSignatures", ["AgeSignatureName"], "Samples_AgeSignatures")


class SampleTableModel(QtS.QSqlQueryModel):
    def setupQuery(self):
        sample_query = f'''
                    SELECT
                        {SQLUtils.qsample_id},
                        {SQLUtils.qsample_name},
                        {SQLUtils.qlat},
                        {SQLUtils.qlon},
                        {SQLUtils.qutm_zone},
                        {SQLUtils.qutm_n},
                        {SQLUtils.qutm_e},
                        {SQLUtils.qelev},
                        {SQLUtils.qage},
                        {SQLUtils.qage_range},
                        {SQLUtils.qgeo_age},
                        {SQLUtils.qcolumn_name},
                        {SQLUtils.qcolumn_data},
                        {SQLUtils.qaliquots},
                        {SQLUtils.qspots},
                        {SQLUtils.qreferences},
                        {SQLUtils.qage_signature},
                        {SQLUtils.qcontext},
                        {SQLUtils.qrock_types},
                        {SQLUtils.qregions},
                        {SQLUtils.qsampling_methods},
                        {SQLUtils.qsettings},
                        {SQLUtils.qunits},
                        {SQLUtils.qupb_methods},
                        {SQLUtils.qlabs},
                        {SQLUtils.qspot_context},
                        {SQLUtils.qspot_compositions},
                        {SQLUtils.qaliquot_context}
                    FROM Samples as S
                    {SQLUtils.column_join}
                    {SQLUtils.old_age_join}
                    {SQLUtils.young_age_join}
                    {SQLUtils.age_signature_join}
                    {SQLUtils.rock_type_join}
                    {SQLUtils.sample_context_join}
                    {SQLUtils.aliquot_join}
                    {SQLUtils.spot_join}
                    {SQLUtils.upb_data_join}
                    {SQLUtils.source_join}
                    {SQLUtils.region_join}
                    {SQLUtils.sampling_method_join}
                    {SQLUtils.setting_join}
                    {SQLUtils.unit_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.labs_join}
                    {SQLUtils.spot_context_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.aliquot_context_join}
                    GROUP BY SampleName
					ORDER BY S.SampleID
                    '''

        return sample_query


class AliquotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, sample_IDs):
        # Select lines
        aliquots = 'AliquotName as "Aliquots"'
        aliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Context"'
        spots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Context"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

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
                    FROM Aliquots
                    {SQLUtils.aliquot_context_join}
                    {SQLUtils.spot_join}
                    {SQLUtils.spot_context_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.upb_data_join}
                    {SQLUtils.source_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.labs_join}
                    WHERE SampleID IN {sample_IDs}
                    GROUP BY AliquotName
                    '''

        return aliquot_query


class SpotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self, ids_to_show):
        # Select lines
        spots = 'SpotName as "Spots"'
        spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Context"'
        spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
        references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
        upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
        labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

        spot_query = f'''
                    SELECT
                        {spots},
                        {spot_context},
                        {spot_compositions},
                        {references},
                        {upb_methods},
                        {labs}
                    FROM Spots
                    {SQLUtils.spot_context_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.upb_data_join}
                    {SQLUtils.source_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.labs_join}
                    WHERE Spots.SpotID IN {ids_to_show}
                    GROUP BY SpotName
                    '''

        return spot_query
