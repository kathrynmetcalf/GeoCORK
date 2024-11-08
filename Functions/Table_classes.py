import sys
from pathlib import Path
import sqlite3
from random import sample

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
    def setupQuery(self, ids_to_show=None, rows_per_page=None, offset=None):
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
                    FROM Samples
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
                    {f"WHERE Samples.SampleID IN {ids_to_show}" if ids_to_show is not None else ""}
                    GROUP BY Samples.SampleName
					ORDER BY Samples.SampleID
					{f"LIMIT {rows_per_page}" if rows_per_page is not None else ""}
					{f"OFFSET {offset}" if offset is not None else ""}
                    '''

        print(sample_query)
        return sample_query


class AliquotTableModel(QtS.QSqlQueryModel):
    def setupQuery(self):
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
                        Aliquots.AliquotID,
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
                    GROUP BY AliquotName
                    ORDER BY Aliquots.AliquotID
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
                        Spots.SpotID,
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
                    GROUP BY SpotName
                    ORDER BY Spots.SpotID
                    '''

        return spot_query
