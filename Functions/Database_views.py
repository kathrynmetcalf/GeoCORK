import sqlite3
import time

from PyQt6 import QtSql as QtS

import Functions.SQLUtils as SQLUtils
import logger_setup
from Functions.SQLUtils import qaliquot_id
from Functions.Settings_manager import SettingsManager

settings = SettingsManager().settings

class ViewQuery:
    def __init__(self, table: str, edit_view: bool = False, **kwargs):
        """
        Class to generate SQL queries for different database views based on the selected table, columns, and filters.
        :param table: Name of the table/view to query (e.g. "Samples", "Aliquots", "Grains", "Spots", "UPbAnalyses",
                      "GeoChemicalAnalyses")
        :param edit_view: Boolean indicating whether the query is for an edit view (True) or a standard view (False)
        Key word arguments can include any of the following to modify the query:
        - show_columns: list of columns to include in the SELECT statement
        - limit: string to limit the number of results (e.g. "LIMIT 100")
        - where: string to filter results (e.g. "WHERE SampleName LIKE 'A%'")
        - where_ids: list of IDs to filter results (e.g. [1, 2, 3])
        - group_col: column name to group results by (e.g. "SampleID")
        - order_col: column name to order results by (e.g. "SampleName")
        The query can be accessed via the `table_query` attribute after initialization.
        The query can be modified by calling `update_query` with new parameters.
        """
        self.table = table
        self.table_query = ''
        self.edit_view = edit_view
        self.kwargs = kwargs
        self.show_columns = []
        self.limit = ''
        self.where = ''
        self.where_ids = []
        self.group_col = ''
        self.order_col = ''
        self.limited_hierarchy = ''
        self.group_by = ''
        self.order_by = ''
        self.query_where = ''
        self.query_limit = ''
        self.create_temp_id = ''
        self.create_temp_paged = ''
        self.query_columns = []
        self.lsa_columns = []
        self.lspag_columns = []
        self.limited_tags = {
            'Samples': SQLUtils.limited_sample_tags,
            'Aliquots': SQLUtils.limited_aliquot_tags,
            'Grains': SQLUtils.limited_grain_tags,
            'Spots': SQLUtils.limited_spot_tags,
            'UPbAnalyses': SQLUtils.limited_upb_tags,
            'GeoChemicalAnalyses': SQLUtils.limited_geochem_tags,
        }
        self.limited_tag_joins = {
            'Samples': SQLUtils.limited_sample_tags_join,
            'Aliquots': SQLUtils.limited_aliquot_tags_join,
            'Grains': SQLUtils.limited_grain_tags_join,
            'Spots': SQLUtils.limited_spot_tags_join,
            'UPbAnalyses': SQLUtils.limited_upb_tags_join,
            'GeoChemicalAnalyses': SQLUtils.limited_geochem_tags_join,
        }
        self.show_items_missing_data = settings.value('show_items_missing_data') == 'true'
        if self.show_items_missing_data:
            # If showing items missing data, use LEFT JOINs so that items with no related records in joined tables will still be included in the results
            # Negatively impacts performance, so only do this if the setting is enabled
            self.join_type = 'LEFT'
        else:
            # If not showing items missing data, use INNER JOINs so that only items with related records in joined tables will be included in the results
            # Improves performance, so use this by default
            self.join_type = 'INNER'
        self.query_tags = {}
        self.query_tags_joins = {}
        self.update_query(table, edit_view, **kwargs)

    def update_query(self, table: str, edit_view: bool = False, **kwargs):
        self.table = table
        self.edit_view = edit_view
        self.kwargs = kwargs
        if self.table == 'Samples':
            self.create_sample_view_query()
        elif self.table == 'Aliquots':
            self.create_aliquot_view_query()
        elif self.table == 'Grains':
            self.create_grain_view_query()
        elif self.table == 'Spots':
            self.create_spot_view_query()
        elif self.table == 'UPbAnalyses':
            self.create_upb_view_query()
        elif self.table == 'Columns':
            self.create_column_view_query()
        elif self.table == 'References' or self.table == '"References"':
            self.create_reference_view_query()
        elif self.table == 'GeoChemicalAnalyses':
            self.create_geochem_view_query()

    def create_sample_view_query(self):
        self.show_columns: list = settings.value('sample_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.where_ids: list = []
        self.group_col: str = 'SampleID'
        self.order_col: str = 'SampleName'
        self.create_temp_id = ''
        self.create_temp_paged = ''
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n'.join(self.query_columns)

        lsa_hierarchy_join = SQLUtils.limited_sample_aliquot_hierarchy_join
        if self.join_type != 'INNER':
            lsa_hierarchy_join = lsa_hierarchy_join.replace('INNER JOIN', f'{self.join_type} JOIN')

        lsa_joins = f'''{f"{'\n'.join(self.query_tags_joins['Samples']) if 'Samples' in self.query_tags_joins else ''}"}
                               {f"{'\n'.join(self.query_tags_joins['Aliquots']) if 'Aliquots' in self.query_tags_joins else ''}"}'''

        # Don't bother joining Spots/Grains/UPbAnalyses/GeoChemicalAnalyses if not needed for the selected columns
        # Spot tags already includes GrainContext, so only add if no Spots tags added
        limited_lspag = f'''
                        {f"{',\n' + ',\n'.join(self.query_tags['Spots']) if 'Spots' in self.query_tags else ''}"}
                        {f"{',\n' + ',\n'.join(self.query_tags['Grains']) if ('Grains' in self.query_tags and 'Spots' not in self.query_tags) else ''}"}
                        {f"{',\n' + ',\n'.join(self.query_tags['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags else ''}"}
                        {f"{',\n' + ',\n'.join(self.query_tags['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags else ''}"}
                        '''
        lspag_joins = f'''
                        {f"{'\n'.join(self.query_tags_joins['Spots']) if 'Spots' in self.query_tags_joins else ''}"}
                        {f"{'\n'.join(self.query_tags_joins['Grains']) if ('Grains' in self.query_tags_joins and 'Spots' not in self.query_tags_joins) else ''}"}
                        {f"{'\n'.join(self.query_tags_joins['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags_joins else ''}"}
                        {f"{'\n'.join(self.query_tags_joins['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags_joins else ''}"}
                        '''
        if '"Accepted/TotalUPbAnalyses"' in query_columns:
            subquery = SQLUtils.qupb_count_sample_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN UPbAnalyses ON', f'{self.join_type} JOIN UPbAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.upb_distinct_join_limited_sample}'
        if '"Accepted/TotalGeoChemicalAnalyses"' in query_columns:
            subquery = SQLUtils.qgeochem_count_sample_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN GeoChemicalAnalyses ON', f'{self.join_type} JOIN GeoChemicalAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.gc_distinct_join_limited_sample}'

        sample_query = f'''
                        {self.limited_hierarchy}
                        {f"{',\n' + ',\n'.join(self.query_tags['Samples']) if 'Samples' in self.query_tags else ''}"}
                        {f"{',\n' + ',\n'.join(self.query_tags['Aliquots']) if 'Aliquots' in self.query_tags else ''}"}
                        {limited_lspag}
                        SELECT
                                {query_columns}
                               FROM LimitedSamplesAliquots lsa
                               {lsa_hierarchy_join if 'LimitedSpotsAnalysesGrains' in self.limited_hierarchy else ''}
                               {lsa_joins}
                               {lspag_joins}
                                {self.query_where}
                                {self.group_by}
                                {self.order_by}
                                {self.query_limit}
                               '''

        sample_query = sample_query.strip()
        self.table_query = sample_query

    def create_aliquot_view_query(self):

        self.show_columns: list = settings.value('aliquot_view_columns')
        self.where: str = ''
        self.group_col: str = 'AliquotID'
        self.order_col: str = ''
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n'.join(self.query_columns)

        lsa_hierarchy_join = SQLUtils.limited_sample_aliquot_hierarchy_join
        if self.join_type != 'INNER':
            lsa_hierarchy_join = lsa_hierarchy_join.replace('INNER JOIN', f'{self.join_type} JOIN')

        lsa_joins = f'''{f"{'\n'.join(self.query_tags_joins['Aliquots']) if 'Aliquots' in self.query_tags_joins else ''}"}
                                       {f"{'\n'.join(self.query_tags_joins['Samples']) if 'Samples' in self.query_tags_joins else ''}"}'''

        # Don't bother joining Spots/Grains/UPbAnalyses/GeoChemicalAnalyses if not needed for the selected columns
        # Spot tags already includes GrainContext, so only add if no Spots tags added
        limited_lspag = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Spots']) if 'Spots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Grains']) if ('Grains' in self.query_tags and 'Spots' not in self.query_tags) else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags else ''}"}
                            '''
        lspag_joins = f'''
                            {f"{'\n'.join(self.query_tags_joins['Spots']) if 'Spots' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['Grains']) if ('Grains' in self.query_tags_joins and 'Spots' not in self.query_tags_joins) else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags_joins else ''}"}
                            '''
        if '"Accepted/TotalUPbAnalyses"' in query_columns:
            subquery = SQLUtils.qupb_count_aliquot_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN UPbAnalyses ON', f'{self.join_type} JOIN UPbAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.upb_distinct_join_limited_aliquot}'
        if '"Accepted/TotalGeoChemicalAnalyses"' in query_columns:
            subquery = SQLUtils.qgeochem_count_grain_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN GeoChemicalAnalyses ON', f'{self.join_type} JOIN GeoChemicalAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.gc_distinct_join_limited_grain}'

        aliquot_query = f'''
                        {self.limited_hierarchy}
                        {f"{',\n' + ',\n'.join(self.query_tags['Aliquots']) if 'Aliquots' in self.query_tags else ''}"}
                        {f"{',\n' + ',\n'.join(self.query_tags['Samples']) if 'Samples' in self.query_tags else ''}"}
                        {limited_lspag}
                        SELECT
                                {query_columns}
                               FROM LimitedSamplesAliquots lsa
                               {lsa_hierarchy_join if 'LimitedSpotsAnalysesGrains' in self.limited_hierarchy else ''}
                               {lsa_joins}
                               {lspag_joins}
                                {self.query_where}
                                {self.group_by}
                                {self.order_by}
                                {self.query_limit}
                               '''

        aliquot_query = aliquot_query.strip()
        self.table_query = aliquot_query

    def create_grain_view_query(self):

        self.show_columns: list = settings.value('grain_view_columns')
        self.where: str = ''
        self.group_col: str = 'GrainID'
        self.order_col: str = 'GrainName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n'.join(self.query_columns)

        lspag_hierarchy_join = SQLUtils.limited_spot_analysis_grain_hierarchy_join
        if self.join_type != 'INNER':
            lspag_hierarchy_join = lspag_hierarchy_join.replace('INNER JOIN', f'{self.join_type} JOIN')

        if (not 'lsa' in query_columns and
                not any('lsa' in string for string in [self.query_where, self.group_by, self.order_by])):
            # Don't bother joining Samples and Aliquots if not needed for the selected columns
            limited_lsa = ''
            lsa_joins = ''
        else:
            limited_lsa = f'''
                        {f"{',\n' + ',\n'.join(self.query_tags['Aliquots']) if 'Aliquots' in self.query_tags else ''}"}
                        {f"{',\n' + ',\n'.join(self.query_tags['Samples']) if 'Samples' in self.query_tags else ''}"}
                        '''
            lsa_joins = f'''
                    {f"{'\n'.join(self.query_tags_joins['Aliquots']) if 'Aliquots' in self.query_tags_joins else ''}"}
                    {f"{'\n'.join(self.query_tags_joins['Samples']) if 'Samples' in self.query_tags_joins else ''}"}
                    '''

        # Don't bother joining Spots/Grains/UPbAnalyses/GeoChemicalAnalyses if not needed for the selected columns
        # Spot tags already includes GrainContext, so only add if no Spots tags added
        limited_lspag = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Spots']) if 'Spots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Grains']) if ('Grains' in self.query_tags and 'Spots' not in self.query_tags) else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags else ''}"}
                            '''
        lspag_joins = f'''
                            {f"{'\n'.join(self.query_tags_joins['Spots']) if 'Spots' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['Grains']) if ('Grains' in self.query_tags_joins and 'Spots' not in self.query_tags_joins) else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags_joins else ''}"}
                            '''
        if '"Accepted/TotalUPbAnalyses"' in query_columns:
            subquery = SQLUtils.qupb_count_grain_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN UPbAnalyses ON', f'{self.join_type} JOIN UPbAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.upb_distinct_join_limited_grain}'
        if '"Accepted/TotalGeoChemicalAnalyses"' in query_columns:
            subquery = SQLUtils.qgeochem_count_grain_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN GeoChemicalAnalyses ON',
                                            f'{self.join_type} JOIN GeoChemicalAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.gc_distinct_join_limited_grain}'

        grain_query = f'''
                                {self.limited_hierarchy}
                                {limited_lspag}
                                {limited_lsa}
                                SELECT
                                        {query_columns}
                                       FROM LimitedSpotsAnalysesGrains lspag
                                       {lspag_hierarchy_join if 'LimitedSamplesAliquots' in self.limited_hierarchy else ''}
                                       {lspag_joins}
                                       {lsa_joins}
                                        {self.query_where}
                                        {self.group_by}
                                        {self.order_by}
                                        {self.query_limit}
                                       '''

        grain_query = grain_query.strip()
        self.table_query = grain_query

    def create_spot_view_query(self):

        self.show_columns: list = settings.value('spot_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'SpotID'
        self.order_col: str = 'SpotName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n'.join(self.query_columns)

        lspag_hierarchy_join = SQLUtils.limited_spot_analysis_grain_hierarchy_join
        if self.join_type != 'INNER':
            lspag_hierarchy_join = lspag_hierarchy_join.replace('INNER JOIN', f'{self.join_type} JOIN')

        if (not 'lsa' in query_columns and
                not any('lsa' in string for string in [self.query_where, self.group_by, self.order_by])):
            # Don't bother joining Samples and Aliquots if not needed for the selected columns
            limited_lsa = ''
            lsa_joins = ''
        else:
            limited_lsa = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Aliquots']) if 'Aliquots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Samples']) if 'Samples' in self.query_tags else ''}"}
                            '''
            lsa_joins = f'''
                            {f"{'\n'.join(self.query_tags_joins['Aliquots']) if 'Aliquots' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['Samples']) if 'Samples' in self.query_tags_joins else ''}"}
                            '''

        # Don't bother joining Spots/Grains/UPbAnalyses/GeoChemicalAnalyses if not needed for the selected columns
        # Spot tags already includes GrainContext, so only add if no Spots tags added
        limited_lspag = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Spots']) if 'Spots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Grains']) if ('Grains' in self.query_tags and 'Spots' not in self.query_tags) else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags else ''}"}
                            '''
        lspag_joins = f'''
                            {f"{'\n'.join(self.query_tags_joins['Spots']) if 'Spots' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['Grains']) if ('Grains' in self.query_tags_joins and 'Spots' not in self.query_tags_joins) else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags_joins else ''}"}
                            '''
        if '"Accepted/TotalUPbAnalyses"' in query_columns:
            subquery = SQLUtils.qupb_count_spot_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN UPbAnalyses ON', f'{self.join_type} JOIN UPbAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.upb_distinct_join_limited_spot}'
        if '"Accepted/TotalGeoChemicalAnalyses"' in query_columns:
            subquery = SQLUtils.qgeochem_count_spot_subquery
            if self.join_type != 'INNER':
                subquery = subquery.replace('INNER JOIN GeoChemicalAnalyses ON', f'{self.join_type} JOIN GeoChemicalAnalyses ON')
            limited_lspag += f',\n{subquery}'
            lspag_joins += f'\n{SQLUtils.gc_distinct_join_limited_spot}'

        spot_query = f'''
                        {self.limited_hierarchy}
                        {limited_lspag}
                        {limited_lsa}
                        SELECT
                                {query_columns}
                               FROM LimitedSpotsAnalysesGrains lspag
                               {lspag_hierarchy_join if 'LimitedSamplesAliquots' in self.limited_hierarchy else ''}
                               {lspag_joins}
                               {lsa_joins}
                                {self.query_where}
                                {self.group_by}
                                {self.order_by}
                                {self.query_limit}
                               '''

        spot_query = spot_query.strip()
        self.table_query = spot_query

    def create_upb_view_query(self):
        self.show_columns: list = settings.value('upb_analysis_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'UPbAnalysisID'
        self.order_col: str = 'UPbAnalysisName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n'.join(self.query_columns)

        lspag_hierarchy_join = SQLUtils.limited_spot_analysis_grain_hierarchy_join
        if self.join_type != 'INNER':
            lspag_hierarchy_join = lspag_hierarchy_join.replace('INNER JOIN', f'{self.join_type} JOIN')

        if (not 'lsa' in query_columns and
                not any('lsa' in string for string in [self.query_where, self.group_by, self.order_by])):
            # Don't bother joining Samples and Aliquots if not needed for the selected columns
            limited_lsa = ''
            lsa_joins = ''
        else:
            limited_lsa = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Aliquots']) if 'Aliquots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Samples']) if 'Samples' in self.query_tags else ''}"}
                            '''
            lsa_joins = f'''
                            {f"{'\n'.join(self.query_tags_joins['Aliquots']) if 'Aliquots' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['Samples']) if 'Samples' in self.query_tags_joins else ''}"}
                            '''

        limited_lspag = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Spots']) if 'Spots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Grains']) if ('Grains' in self.query_tags and 'Spots' not in self.query_tags) else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags else ''}"}
                            '''

        lspag_joins = f'''{f"{'\n'.join(self.query_tags_joins['UPbAnalyses']) if 'UPbAnalyses' in self.query_tags_joins else ''}"}
                               {f"{'\n'.join(self.query_tags_joins['Spots']) if 'Spots' in self.query_tags_joins else ''}"}'''

        upb_query = f'''
                        {self.limited_hierarchy}
                        {limited_lspag}
                        {limited_lsa}
                        SELECT
                                {query_columns}
                               FROM LimitedSpotsAnalysesGrains lspag
                               {lspag_hierarchy_join if 'LimitedSamplesAliquots' in self.limited_hierarchy else ''}
                               {lspag_joins}
                               {lsa_joins}
                                {self.query_where}
                                {self.group_by}
                                {self.order_by}
                                {self.query_limit}
                               '''

        upb_query = upb_query.strip()
        self.table_query = upb_query

    def create_geochem_view_query(self):
        """
        Build the SQL for the GeoChemicalAnalyses view.
        """
        self.show_columns: list = settings.value('geochem_analysis_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'GeoChemAnalysisID'
        self.order_col: str = 'GeoChemAnalysisName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n'.join(self.query_columns)

        lspag_hierarchy_join = SQLUtils.limited_spot_analysis_grain_hierarchy_join
        if self.join_type != 'INNER':
            lspag_hierarchy_join = lspag_hierarchy_join.replace('INNER JOIN', f'{self.join_type} JOIN')

        if (not 'lsa' in query_columns and
                not any('lsa' in string for string in [self.query_where, self.group_by, self.order_by])):
            # Don't bother joining Samples and Aliquots if not needed for the selected columns
            limited_lsa = ''
            lsa_joins = ''
        else:
            limited_lsa = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Aliquots']) if 'Aliquots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Samples']) if 'Samples' in self.query_tags else ''}"}
                            '''
            lsa_joins = f'''
                            {f"{'\n'.join(self.query_tags_joins['Aliquots']) if 'Aliquots' in self.query_tags_joins else ''}"}
                            {f"{'\n'.join(self.query_tags_joins['Samples']) if 'Samples' in self.query_tags_joins else ''}"}
                            '''

        limited_lspag = f'''
                            {f"{',\n' + ',\n'.join(self.query_tags['Spots']) if 'Spots' in self.query_tags else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['Grains']) if ('Grains' in self.query_tags and 'Spots' not in self.query_tags) else ''}"}
                            {f"{',\n' + ',\n'.join(self.query_tags['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags else ''}"}
                            '''

        lspag_joins = f'''{f"{'\n'.join(self.query_tags_joins['GeoChemicalAnalyses']) if 'GeoChemicalAnalyses' in self.query_tags_joins else ''}"}
                               {f"{'\n'.join(self.query_tags_joins['Spots']) if 'Spots' in self.query_tags_joins else ''}"}'''

        geochem_query = f'''
                        {self.limited_hierarchy}
                        {limited_lspag}
                        {limited_lsa}
                        SELECT
                                {query_columns}
                               FROM LimitedSpotsAnalysesGrains lspag
                               {lspag_hierarchy_join if 'LimitedSamplesAliquots' in self.limited_hierarchy else ''}
                               {lspag_joins}
                               {lsa_joins}
                                {self.query_where}
                                {self.group_by}
                                {self.order_by}
                                {self.query_limit}
                               '''

        geochem_query = geochem_query.strip()
        self.table_query = geochem_query

    def create_column_view_query(self):
        self.show_columns: list = settings.value('column_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'Columns.ColumnID'
        self.order_col: str = 'Columns.ColumnName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n '.join(self.query_columns)

        column_query = f'''
                    SELECT
                        {query_columns}
                    FROM Columns
                    {SQLUtils.gps_column_join if any(col in query_columns for col in [SQLUtils.qcolumn_gps, SQLUtils.qcolumn_gps_display, SQLUtils.qcolumn_elev, SQLUtils.qcolumn_elev_display]) else ''}
                    {SQLUtils.column_units_join if any(col in query_columns for col in [SQLUtils.qcolumn_total_height_depth_unit, SQLUtils.qcolumn_elev_unit]) else ''}
                    {SQLUtils.gps_column_left_joins if any(col in query_columns for col in [SQLUtils.qcolumn_gps_display, SQLUtils.qcolumn_elev_display]) else ''}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        column_query = column_query.strip()
        self.table_query = column_query

    def create_reference_view_query(self):
        self.show_columns: list = settings.value('reference_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = '"References".ReferenceID'
        self.order_col: str = '"References".ReferenceDisplay'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_query_columns()
        self.get_group_order_clauses()
        self.limited_hierarchy_query()
        query_columns = ',\n '.join(self.query_columns)

        reference_query = f'''
                    SELECT
                        {query_columns}
                    FROM "References"
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        reference_query = reference_query.strip()
        self.table_query = reference_query

    def limited_hierarchy_query(self):
        """
        Construct the query to limit the Samples, Aliquots, Grains, Spots, and UPbAnalyses joined in the main query. Begin with
        the table that the where clause applies to. Any ordering or limit that does not also apply to this table get
        set for application in the main query.
        Updates the limited hierarchy query clause, the where clause to use in the main query, and the limit clause to
        use in the main query.
        """
        from Functions.Widget_classes import get_headers

        headers = get_headers(self.table)
        table_abbreviation_dict = SQLUtils.limited_table_abbreviations.copy()

        where_table = self.table
        where_header = ''
        hierarchy_where_join = ''
        hierarchy_where = ''
        hierarchy_order_by = ''
        hierarchy_limit = ''
        self.query_where = self.where
        self.query_limit = self.limit

        if self.table not in ('Samples', 'Aliquots', 'Grains', 'Spots', 'UPbAnalyses', 'GeoChemicalAnalyses'):
            return
        table_abbreviation_dict.pop(self.table)

        if self.where != '':
            try:
                # Assumes the where clause is of the form "WHERE item_ID IN (1, 2, 3)"
                where_ids = self.where.split('IN (')[1].split(')')[0].split(', ')
                self.where_ids = [int(id.strip()) for id in where_ids]
            except (IndexError, ValueError):
                try:
                    # Assumes the where clause is of the form "WHERE item_ID = 1"
                    where_id = self.where.split('=')[1].strip()
                    self.where_ids = [int(where_id)]
                except (IndexError, ValueError):
                    # Could not parse where clause, so no IDs to use
                    self.where_ids = []
            # Check if any table headers are in the where clause
            if any(header in self.where for header in headers):
                if self.where_ids:
                    # Find which header is in the where clause
                    for header in headers:
                        if header in self.where:
                            where_header = header
                            self.create_temp_id = f"TempIDs AS (SELECT {where_header} FROM {self.table} {self.where})"
                            hierarchy_where_join = f"INNER JOIN TempIDs ti ON"
                            break
                else:
                    hierarchy_where = self.where
                    where_header = headers[0]
                self.query_where = ''
                if self.order_col != '' and self.limit != '':
                    if self.order_col in headers:
                        # Everything applies to the same table, so put them all in the hierarchy query
                        if self.where_ids:
                            self.create_temp_paged = f"""TempPaged AS (
                                                            SELECT TempIDs.{where_header} FROM TempIDs
                                                            JOIN {self.table} ON {self.table}.{where_header} = TempIDs.{where_header}
                                                            ORDER BY {self.order_col} COLLATE NOCASE {self.limit}
                                                            )
                                                            """
                        else:
                            where_header = headers[0]
                            self.create_temp_paged = f"""TempPaged AS (
                                                            SELECT {headers[0]} FROM {self.table}
                                                            ORDER BY {self.order_col} COLLATE NOCASE {self.limit}
                                                            )
                                                            """
                        hierarchy_where_join = f"INNER JOIN TempPaged tp ON"
                        hierarchy_limit = ''
                        self.query_limit = ''
                    else:
                        # Ordering by a different table than the where clause, so apply the ordering and limit in the main query
                        hierarchy_order_by = ''
                        hierarchy_limit = ''
                        self.query_limit = self.limit
                        # order gets applied in the main query regardless
                elif self.limit != '':
                    # Everything not blank applies to the same table, so put them all in the hierarchy query
                    if self.where_ids:
                        self.create_temp_paged = f"""TempPaged AS (
                                                        SELECT TempIDs.{where_header} FROM TempIDs
                                                        JOIN {self.table} ON {self.table}.{where_header} = TempIDs.{where_header}
                                                        {self.limit}
                                                        )
                                                        """
                    else:
                        self.create_temp_paged = f"""TempPaged AS (
                                                        SELECT {where_header} FROM {self.table}
                                                        {self.limit}
                                                        )
                                                        """
                    hierarchy_where_join = f"INNER JOIN TempPaged tp ON"
                    hierarchy_order_by = ''
                    hierarchy_limit = ''
                    self.query_limit = ''
            else:
                for key in table_abbreviation_dict:
                    if any(header in self.where for header in get_headers(key)):
                        where_table = key
                        # Find which header is in the where clause
                        for header in get_headers(key):
                            if header in self.where:
                                where_header = header
                                break
                        if self.where_ids:
                            self.create_temp_id = f"TempIDs AS (SELECT {where_header} FROM {key} {self.where})"
                            hierarchy_where_join = f"INNER JOIN TempIDs ti ON"
                        else:
                            hierarchy_where = self.where
                        self.query_where = ''
                        # Limit applies to a different table than the where clause, so wait to apply it in the main query
                        hierarchy_limit = ''
                        self.query_limit = self.limit
                        if self.order_col != '':
                            if self.order_col in get_headers(key):
                                # Order applies to same table as where, so apply in the hierarchy query
                                hierarchy_order_by = f'ORDER BY {self.order_col} COLLATE NOCASE'
                        break
            if hierarchy_where == '' and hierarchy_where_join == '':
                logger_setup.get_logger().info(f'Where clause {self.where} does not apply to Samples, Aliquots, Spots or UPbAnalyses.')
                logger_setup.get_logger().info(f'Consider simplifying the query or using the filtering query building.')
        elif self.order_col != '' and self.limit != '':
            if self.order_col in headers:
                # Everything applies to the same table, so put them all in the hierarchy query
                where_header = headers[0]
                self.create_temp_paged = f"""TempPaged AS (
                                                SELECT {headers[0]} FROM {self.table}
                                                ORDER BY {self.order_col} COLLATE NOCASE {self.limit}
                                                )
                                            """
                hierarchy_order_by = ''
                hierarchy_limit = ''
                hierarchy_where_join = f"INNER JOIN TempPaged tp ON"
                self.query_limit = ''
            else:
                # Ordering by a different table than the where clause, so apply the ordering and limit in the main query
                hierarchy_order_by = ''
                hierarchy_limit = ''
                self.query_limit = self.limit
                # order gets applied in the main query regardless
        elif self.limit != '':
            # Only limit, so apply in the hierarchy
            where_header = headers[0]
            self.create_temp_paged = f"""TempPaged AS (
                                        SELECT {headers[0]} FROM {self.table}
                                        {self.limit}
                                        )
                                        """
            hierarchy_limit = ''
            hierarchy_where_join = f"INNER JOIN TempPaged tp ON"
            self.query_limit = ''
        group_lspag = ''
        group_lsa = ''
        lsa_from_table = 'Aliquots'
        lspag_from_table = 'Spots'
        lsa_select_cols = self.lsa_columns
        for id_col in [SQLUtils.qsample_id, SQLUtils.qaliquot_id]:
            lsa_select_cols.remove(id_col) if id_col in lsa_select_cols else None
        lsa_table_joins = SQLUtils.limited_lsa_lspag_joins['LimitedSamplesAliquots'].copy()
        lspag_select_cols = self.lspag_columns
        for id_col in [SQLUtils.qspot_id, SQLUtils.qgrain_id, SQLUtils.qupb_id, SQLUtils.qgeochem_id]:
            lspag_select_cols.remove(id_col) if id_col in lspag_select_cols else None
        if self.table == 'UPbAnalyses' or settings.value('display_analyses') == ['UPbAnalyses']:
            lspag_table_joins = SQLUtils.limited_lsa_lspag_joins['LimitedSpotsUPbAnalysesGrains'].copy()
        elif self.table == 'GeoChemicalAnalyses' or settings.value('display_analyses') == ['GeoChemicalAnalyses']:
            lspag_table_joins = SQLUtils.limited_lsa_lspag_joins['LimitedSpotsGeoChemicalAnalysesGrains'].copy()
        else:
            lspag_table_joins = SQLUtils.limited_lsa_lspag_joins['LimitedSpotsAnalysesGrains'].copy()
        lsa_selects = []
        lsa_joins = []
        lspag_selects = []
        lspag_joins = []
        spot_upb_join_str = f'{self.join_type} JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID'
        spot_geochem_join_str = f'{self.join_type} JOIN GeoChemicalAnalyses ON Spots.SpotID = GeoChemicalAnalyses.SpotID'
        if where_table in ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'GeoChemicalAnalyses', 'Grains']:
            if where_table in ['Samples', 'Aliquots']:
                if headers[0] in ['SampleID', 'AliquotID']:
                    group_lsa = f'GROUP BY {self.table}.{headers[0]}'
                    group_lspag = f'GROUP BY lsa.{headers[0]}'
                elif headers[0] in ['SpotID', 'UPbAnalysisID', 'GeoChemAnalysisID']:
                    group_lsa = ''
                    group_lspag = f'GROUP BY {self.table}.{headers[0]}'
                elif headers[0] == 'GrainID':
                    group_lsa = ''
                    group_lspag = f'GROUP BY Spots.SpotID'
            else:
                if headers[0] in ['SpotID', 'UPbAnalysisID', 'GeoChemAnalysisID']:
                    group_lspag = f'GROUP BY {self.table}.{headers[0]}'
                    group_lsa = f'GROUP BY lspag.{headers[0]}'
                elif headers[0] == 'GrainID':
                    group_lspag = f'GROUP BY Spots.SpotID'
                    group_lsa = f'GROUP BY lspag.SpotID'
                elif headers[0] in ['SampleID', 'AliquotID']:
                    group_lspag = ''
                    group_lsa = f'GROUP BY {self.table}.{headers[0]}'
            if self.table == 'Samples':
                lsa_from_table = 'Samples'
                lsa_select_cols.append('Samples.DefaultSampleAgeID') if any('SampleAge' in col for col in self.show_columns) else lsa_selects
                lspag_from_table = 'Spots'
                lsa_table_joins.append(f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID')
                if 'UPbAnalyses' in settings.value('display_analyses'):
                    lspag_table_joins.append(spot_upb_join_str)
                if 'GeoChemicalAnalyses' in settings.value('display_analyses'):
                    lspag_table_joins.append(spot_geochem_join_str)
                lspag_table_joins.append('LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                lsa_selects = [SQLUtils.qsample_id]
                for col in lsa_select_cols:
                    as_name = col.split(' AS ')[1] if ' AS ' in col else ''
                    if ((as_name and as_name in self.show_columns) or
                            (col in [SQLUtils.qaliquot_id]) or (as_name in self.order_col or as_name in self.group_col
                            or as_name in self.where) or ('ID' in col and not as_name)):
                        if col not in lsa_selects:
                            lsa_selects.append(col)
                        if col.split('.')[0].split(" ")[-1] != self.table:
                            for join in lsa_table_joins:
                                if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                                    if join not in lsa_joins:
                                        if join == f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID':
                                            # Add to the beginning of the list
                                            lsa_joins.insert(0, join)
                                        else:
                                            lsa_joins.append(join)
                                        if 'ON Aliquots.' in join and f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID' not in lsa_joins:
                                            lsa_joins.insert(0,
                                                                f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID')
                                            if SQLUtils.qaliquot_id not in lsa_selects:
                                                lsa_selects.append(SQLUtils.qaliquot_id)
                if where_header == 'AliquotID' and SQLUtils.qaliquot_id not in lsa_selects:
                    lsa_selects.append(SQLUtils.qaliquot_id)
                    if f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID' not in lsa_joins:
                        lsa_joins.insert(0, f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID')
                for col in lspag_select_cols:
                    as_name = col.split(' AS ')[1] if ' AS ' in col else ''
                    if ((as_name and as_name in self.show_columns) or
                            (col in [SQLUtils.qspot_id, SQLUtils.qupb_id, SQLUtils.qgeochem_id, SQLUtils.qgrain_id]) or
                            (as_name in self.order_col or as_name in self.group_col or as_name in self.where) or
                            ('ID' in col and not as_name)):
                        if col not in lspag_selects:
                            lspag_selects.append(col)
                            if 'Spots.SpotID AS SpotID' not in lspag_selects:
                                lspag_selects.insert(0, 'Spots.SpotID AS SpotID')
                            if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                                lspag_selects.insert(1, 'Spots.AliquotID AS AliquotID')
                                if SQLUtils.qaliquot_id not in lsa_selects:
                                    lsa_selects.append(SQLUtils.qaliquot_id)
                            if qaliquot_id not in lsa_selects:
                                lsa_selects.append(SQLUtils.qaliquot_id)
                            if f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID' not in lsa_joins:
                                lsa_joins.insert(0, f'{self.join_type} JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID')
                        if col.split(".")[0].split(" ")[-1] != 'Spots':
                            for join in lspag_table_joins:
                                if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                                    if join not in lspag_joins:
                                        if (join == spot_upb_join_str and
                                                SQLUtils.qupb_id not in lspag_selects):
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qupb_id)
                                            lspag_joins.insert(0, join)
                                        elif (join == spot_geochem_join_str and
                                                SQLUtils.qgeochem_id not in lspag_selects):
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qgeochem_id)
                                            lspag_joins.insert(0, join)
                                        elif (join == 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID' and
                                              'Spots.GrainID AS GrainID' not in lspag_selects):
                                            # Add to the beginning of the list
                                            lspag_selects.append('Spots.GrainID AS GrainID')
                                            lspag_joins.insert(0, join)
                                        else:
                                            lspag_joins.append(join)
                                            if f'ON UPbAnalyses.' in join and spot_upb_join_str not in lspag_joins:
                                                lspag_joins.insert(0, spot_upb_join_str)
                                                if SQLUtils.qupb_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qupb_id)
                                            if 'ON GeoChemicalAnalyses.' in join and spot_geochem_join_str not in lspag_joins:
                                                lspag_joins.insert(0, spot_geochem_join_str)
                                                if SQLUtils.qgeochem_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qgeochem_id)
                                            if 'ON Grains.' in join and 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID' not in lspag_joins:
                                                lspag_joins.insert(0, 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                                                if 'Spots.GrainID AS GrainID' not in lspag_selects:
                                                    lspag_selects.append('Spots.GrainID AS GrainID')
                if where_header == SQLUtils.qupb_id and SQLUtils.qupb_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qupb_id)
                    if spot_upb_join_str not in lspag_joins:
                        lspag_joins.insert(0, spot_upb_join_str)
                elif where_header == SQLUtils.qgeochem_id and SQLUtils.qgeochem_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qgeochem_id)
                    if spot_geochem_join_str not in lspag_joins:
                        lspag_joins.insert(0, spot_geochem_join_str)
            elif self.table == 'Aliquots':
                lsa_from_table = 'Aliquots'
                lspag_from_table = 'Spots'
                lsa_selects = [SQLUtils.qaliquot_id]
                lsa_table_joins.append(f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID')
                lspag_table_joins.append(spot_upb_join_str)
                lspag_table_joins.append(spot_geochem_join_str)
                lspag_table_joins.append('LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                lsa_selects, lsa_joins = self.get_lsa_from_aliquots(lsa_select_cols, lsa_table_joins, lsa_selects)
                if where_header == 'SampleID' and 'Aliquots.SampleID AS SampleID' not in lsa_selects:
                    lsa_selects.append('Aliquots.SampleID AS SampleID')
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')
                for col in lspag_select_cols:
                    as_name = col.split(' AS ')[1] if ' AS ' in col else ''
                    if ((as_name and as_name in self.show_columns) or
                            (col in [SQLUtils.qspot_id, SQLUtils.qupb_id, SQLUtils.qgeochem_id, SQLUtils.qgrain_id]) or
                            (as_name in self.order_col or as_name in self.group_col or as_name in self.where) or
                            ('ID' in col and not as_name)):
                        if col not in lspag_selects:
                            lspag_selects.append(col)
                            if (any('Rejected' in show_col for show_col in self.show_columns)
                                    and SQLUtils.qupb_rejected not in lspag_selects):
                                lspag_selects.append(SQLUtils.qupb_rejected)
                            if 'Spots.SpotID AS SpotID' not in lspag_selects:
                                lspag_selects.insert(0, 'Spots.SpotID AS SpotID')
                            if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                                lspag_selects.insert(1, 'Spots.AliquotID AS AliquotID')
                        if col.split(".")[0].split(" ")[-1] != 'Spots':
                            for join in lspag_table_joins:
                                if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                                    if join not in lspag_joins:
                                        if join == spot_upb_join_str and SQLUtils.qupb_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qupb_id)
                                            lspag_joins.insert(0, join)
                                        elif join == spot_geochem_join_str and SQLUtils.qgeochem_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qgeochem_id)
                                            lspag_joins.insert(0, join)
                                        elif join == SQLUtils.spot_grain_join and SQLUtils.qgrain_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qgrain_id)
                                            lspag_joins.insert(0, join)
                                        else:
                                            lspag_joins.append(join)
                                            if f'ON UPbAnalyses.' in join and spot_upb_join_str not in lspag_joins:
                                                lspag_joins.insert(0, spot_upb_join_str)
                                                if SQLUtils.qupb_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qupb_id)
                                            if 'ON GeoChemicalAnalyses.' in join and spot_geochem_join_str not in lspag_joins:
                                                lspag_joins.insert(0, spot_geochem_join_str)
                                                if SQLUtils.qgeochem_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qgeochem_id)
                                            if 'ON Grains.' in join and 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID' not in lspag_joins:
                                                lspag_joins.insert(0, 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                                                if SQLUtils.qgrain_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qgrain_id)
                if where_header == SQLUtils.qupb_id and SQLUtils.qupb_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qupb_id)
                    if spot_upb_join_str not in lspag_joins:
                        lspag_joins.insert(0, spot_upb_join_str)
                elif where_header == SQLUtils.qgeochem_id and SQLUtils.qgeochem_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qgeochem_id)
                    if spot_geochem_join_str not in lspag_joins:
                        lspag_joins.insert(0, spot_geochem_join_str)

            elif self.table == 'Spots':
                lspag_from_table = 'Spots'
                lsa_from_table = 'Aliquots'
                lspag_selects = [SQLUtils.qspot_id]
                lsa_table_joins.append(f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID')
                lspag_table_joins.append(spot_upb_join_str)
                lspag_table_joins.append(spot_geochem_join_str)
                lspag_table_joins.append('LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                for col in lspag_select_cols:
                    as_name = col.split(' AS ')[1] if ' AS ' in col else ''
                    if ((as_name and as_name in self.show_columns) or
                            (col in [SQLUtils.qspot_id, SQLUtils.qupb_id, SQLUtils.qgeochem_id, SQLUtils.qgrain_id]) or
                            (as_name in self.order_col or as_name in self.group_col or as_name in self.where) or
                            ('ID' in col and not as_name)):
                        if col not in lspag_selects:
                            lspag_selects.append(col)
                            if (any('Rejected' in show_col for show_col in self.show_columns)
                                    and SQLUtils.qupb_rejected not in lspag_selects):
                                lspag_selects.append(SQLUtils.qupb_rejected)
                            if 'Spots.GrainID AS GrainID' not in lspag_selects:
                                lspag_selects.insert(1, 'Spots.GrainID AS GrainID')
                            if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                                lspag_selects.insert(1, 'Spots.AliquotID AS AliquotID')
                        if col.split(".")[0].split(" ")[-1] != 'Spots':
                            for join in lspag_table_joins:
                                if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                                    if join not in lspag_joins:
                                        if join == spot_upb_join_str and SQLUtils.qupb_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qupb_id)
                                            lspag_joins.insert(0, join)
                                        elif join == spot_geochem_join_str and SQLUtils.qgeochem_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qgeochem_id)
                                            lspag_joins.insert(0, join)
                                        elif join == 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID' and SQLUtils.qgrain_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qgrain_id)
                                            lspag_joins.insert(0, join)
                                        else:
                                            lspag_joins.append(join)
                                            if 'ON UPbAnalyses.' in join and spot_upb_join_str not in lspag_joins:
                                                lspag_joins.insert(0, spot_upb_join_str)
                                                if SQLUtils.qupb_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qupb_id)
                                            if 'ON GeoChemicalAnalyses.' in join and spot_geochem_join_str not in lspag_joins:
                                                lspag_joins.insert(0, spot_geochem_join_str)
                                                if SQLUtils.qgeochem_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qgeochem_id)
                                            if 'ON Grains.' in join and 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID' not in lspag_joins:
                                                lspag_joins.insert(0, 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                                                if SQLUtils.qgrain_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qgrain_id)
                if where_header == SQLUtils.qupb_id and SQLUtils.qupb_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qupb_id)
                    if spot_upb_join_str not in lspag_joins:
                        lspag_joins.insert(0, spot_upb_join_str)
                elif where_header == SQLUtils.qgeochem_id and SQLUtils.qgeochem_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qgeochem_id)
                    if spot_geochem_join_str not in lspag_joins:
                        lspag_joins.insert(0, spot_geochem_join_str)
                lsa_selects, lsa_joins = self.get_lsa_from_aliquots(lsa_select_cols, lsa_table_joins, lsa_selects)
                if where_header == 'SampleID' and 'Aliquots.SampleID AS SampleID' not in lsa_selects:
                    lsa_selects.append('Aliquots.SampleID AS SampleID')
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')
                elif where_header == 'AliquotID' and 'Spots.AliquotID AS AliquotID' not in lspag_joins:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')

            elif self.table == 'UPbAnalyses':
                lspag_from_table = 'UPbAnalyses'
                lsa_from_table = 'Aliquots'
                lspag_selects = [SQLUtils.qupb_id]
                lsa_table_joins.append(f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID')
                lspag_table_joins.append(f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID')
                lspag_table_joins.append('LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                for col in lspag_select_cols:
                    as_name = col.split(' AS ')[1] if ' AS ' in col else ''
                    quoted_show_columns = [f'"{col}"' for col in self.show_columns]
                    if ((as_name and as_name in self.show_columns) or ('"' in as_name and as_name in quoted_show_columns) or
                            (col in [SQLUtils.qspot_id, SQLUtils.qupb_id, SQLUtils.qgrain_id]) or
                            (as_name in self.order_col or as_name in self.group_col or as_name in self.where) or
                            ('ID' in col and not as_name)):
                        if col not in lspag_selects:
                            lspag_selects.append(col)
                            if 'UPbAnalyses.SpotID AS SpotID' not in lspag_selects:
                                lspag_selects.insert(1, 'UPbAnalyses.SpotID AS SpotID')
                            if 'Spots.GrainID AS GrainID' not in lspag_selects:
                                lspag_selects.insert(1, 'Spots.GrainID AS GrainID')
                                if f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                    lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID')
                            if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                                lspag_selects.append('Spots.AliquotID AS AliquotID')
                                if f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                    lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID')
                        if col.split(".")[0].split(" ")[-1] != 'UPbAnalyses':
                            for join in lspag_table_joins:
                                if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                                    if join not in lspag_joins:
                                        if (join == f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID' and
                                                col.split(".")[0].split(" ")[-1] == 'Spots'):
                                            # Add to the beginning of the list
                                            lspag_joins.insert(0, join)
                                        elif join == SQLUtils.spot_grain_join and col.split(".")[0].split(" ")[-1] == 'Grains':
                                            if 'Spots.GrainID AS GrainID' not in lspag_selects:
                                                lspag_selects.insert(1, 'Spots.GrainID AS GrainID')
                                            # Add to the beginning of the list
                                            if f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                                lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID')
                                            lspag_joins.insert(1, join)
                                        else:
                                            lspag_joins.append(join)
                                            if 'ON Spots.' in join and f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                                lspag_joins.insert(0,
                                                                    f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID')
                                                if SQLUtils.qspot_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qupb_id)
                                            if 'ON Grains.' in join and SQLUtils.spot_grain_join not in lspag_joins:
                                                if f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                                    lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID')
                                                lspag_joins.insert(1, SQLUtils.spot_grain_join)
                if where_header == 'GrainID' and SQLUtils.qgrain_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qgrain_id)
                    if 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID' not in lspag_joins:
                        lspag_joins.insert(0, 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                        if f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                            lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID')
                lsa_selects, lsa_joins = self.get_lsa_from_aliquots(lsa_select_cols, lsa_table_joins, lsa_selects)
                if where_header == 'SampleID' and 'Aliquots.SampleID AS SampleID' not in lsa_selects:
                    lsa_selects.append('Aliquots.SampleID AS SampleID')
                    if SQLUtils.qaliquot_id not in lsa_selects:
                        lsa_selects.append(SQLUtils.qaliquot_id)
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')
                elif where_header == 'AliquotID' and SQLUtils.qaliquot_id not in lsa_selects:
                    lsa_selects.append(SQLUtils.qaliquot_id)
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')

            elif self.table == 'GeoChemicalAnalyses':
                lspag_from_table = 'GeoChemicalAnalyses'
                lsa_from_table = 'Aliquots'
                lspag_selects = [SQLUtils.qgeochem_id]
                lsa_table_joins.append(f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID')
                lspag_table_joins.append(f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID')
                lspag_table_joins.append('LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                for col in lspag_select_cols:
                    as_name = col.split(' AS ')[1] if ' AS ' in col else ''
                    quoted_show_columns = [f'"{c}"' for c in self.show_columns]
                    if ((as_name and as_name in self.show_columns) or ('"' in as_name and as_name in quoted_show_columns) or
                            (col in [SQLUtils.qspot_id, SQLUtils.qgeochem_id, SQLUtils.qgrain_id]) or
                            (as_name in self.order_col or as_name in self.group_col or as_name in self.where) or
                            ('ID' in col and not as_name)):
                        if col not in lspag_selects:
                            lspag_selects.append(col)
                            if 'GeoChemicalAnalyses.SpotID AS SpotID' not in lspag_selects:
                                lspag_selects.insert(1, 'GeoChemicalAnalyses.SpotID AS SpotID')
                            if 'Spots.GrainID AS GrainID' not in lspag_selects:
                                lspag_selects.insert(1, 'Spots.GrainID AS GrainID')
                                if f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                    lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID')
                            if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                                lspag_selects.append('Spots.AliquotID AS AliquotID')
                                if f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                    lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID')
                        if col.split(".")[0].split(" ")[-1] != 'GeoChemicalAnalyses':
                            for join in lspag_table_joins:
                                if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                                    if join not in lspag_joins:
                                        if (join == f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID' and
                                                col.split(".")[0].split(" ")[-1] == 'Spots'):
                                            lspag_joins.insert(0, join)
                                        elif join == SQLUtils.spot_grain_join and col.split(".")[0].split(" ")[-1] == 'Grains':
                                            if 'Spots.GrainID AS GrainID' not in lspag_selects:
                                                lspag_selects.insert(1, 'Spots.GrainID AS GrainID')
                                            if f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                                lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID')
                                            lspag_joins.insert(1, join)
                                        else:
                                            lspag_joins.append(join)
                                            if 'ON Spots.' in join and f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                                lspag_joins.insert(0,
                                                                    f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID')
                                                if SQLUtils.qspot_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qgeochem_id)
                                            if 'ON Grains.' in join and SQLUtils.spot_grain_join not in lspag_joins:
                                                if f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                                                    lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID')
                                                lspag_joins.insert(1, SQLUtils.spot_grain_join)
                if where_header == 'GrainID' and SQLUtils.qgrain_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qgrain_id)
                    if 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID' not in lspag_joins:
                        lspag_joins.insert(0, 'LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID')
                        if f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID' not in lspag_joins:
                            lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON GeoChemicalAnalyses.SpotID = Spots.SpotID')
                lsa_selects, lsa_joins = self.get_lsa_from_aliquots(lsa_select_cols, lsa_table_joins, lsa_selects)
                if where_header == 'SampleID' and 'Aliquots.SampleID AS SampleID' not in lsa_selects:
                    lsa_selects.append('Aliquots.SampleID AS SampleID')
                    if SQLUtils.qaliquot_id not in lsa_selects:
                        lsa_selects.append(SQLUtils.qaliquot_id)
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')
                elif where_header == 'AliquotID' and SQLUtils.qaliquot_id not in lsa_selects:
                    lsa_selects.append(SQLUtils.qaliquot_id)
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')

            elif self.table == 'Grains':
                group_lspag = ''
                lspag_from_table = 'Grains'
                lsa_from_table = 'Aliquots'
                lspag_selects = [SQLUtils.qgrain_id]
                lsa_table_joins.append(f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID')
                lspag_table_joins.append(f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                lspag_table_joins.append(spot_upb_join_str)
                lspag_table_joins.append(spot_geochem_join_str)
                for col in lspag_select_cols:
                    as_name = col.split(' AS ')[1] if ' AS ' in col else ''
                    if ((as_name and as_name in self.show_columns) or
                            (col in [SQLUtils.qspot_id, SQLUtils.qupb_id, SQLUtils.qgeochem_id, SQLUtils.qgrain_id]) or
                            (as_name in self.order_col or as_name in self.group_col or as_name in self.where) or
                            ('ID' in col and not as_name)):
                        if col not in lspag_selects:
                            lspag_selects.append(col)
                            if (any('Rejected' in show_col for show_col in self.show_columns)
                                    and SQLUtils.qupb_rejected not in lspag_selects):
                                lspag_selects.append(SQLUtils.qupb_rejected)
                            if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                                lspag_selects.append('Spots.AliquotID AS AliquotID')
                        if col.split(".")[0].split(" ")[-1] != 'Grains':
                            for join in lspag_table_joins:
                                if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                                    if join not in lspag_joins:
                                        if join == f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' and SQLUtils.qspot_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            lspag_selects.append(SQLUtils.qgrain_id)
                                            lspag_joins.insert(0, join)
                                        elif join == spot_upb_join_str and SQLUtils.qupb_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                                                lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                                            lspag_selects.append(SQLUtils.qupb_id)
                                            lspag_joins.insert(1, join)
                                        elif join == spot_geochem_join_str and SQLUtils.qgeochem_id not in lspag_selects:
                                            # Add to the beginning of the list
                                            if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                                                lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                                            lspag_selects.append(SQLUtils.qgeochem_id)
                                            lspag_joins.insert(1, join)
                                        else:
                                            lspag_joins.append(join)
                                            if 'ON UPbAnalyses.' in join and spot_upb_join_str not in lspag_joins:
                                                if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                                                    lspag_joins.insert(0,
                                                                        f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                                                lspag_joins.insert(1, spot_upb_join_str)
                                                if SQLUtils.qupb_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qupb_id)
                                            if 'ON GeoChemicalAnalyses.' in join and spot_geochem_join_str not in lspag_joins:
                                                if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                                                    lspag_joins.insert(0,
                                                                       f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                                                lspag_joins.insert(1, spot_geochem_join_str)
                                                if SQLUtils.qgeochem_id not in lspag_selects:
                                                    lspag_selects.append(SQLUtils.qgeochem_id)
                                            if 'ON Spots.' in join and f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                                                lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                                                if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                                                    lspag_selects.append('Spots.AliquotID AS AliquotID')
                if 'Spots.AliquotID AS AliquotID' in lspag_selects and f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                    lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                if where_header == SQLUtils.qupb_id and SQLUtils.qupb_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qupb_id)
                    if spot_upb_join_str not in lspag_joins:
                        if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                            lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                        lspag_joins.insert(1, spot_upb_join_str)
                elif where_header == SQLUtils.qgeochem_id and SQLUtils.qgeochem_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qgeochem_id)
                    if spot_geochem_join_str not in lspag_joins:
                        if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                            lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                        lspag_joins.insert(1, spot_geochem_join_str)
                elif where_header == 'SpotID' and SQLUtils.qspot_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qspot_id)
                    if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                        lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                if SQLUtils.qupb_count.split('AS ')[1].split('"')[1] in self.show_columns:
                    if SQLUtils.qspot_id not in lspag_selects:
                        lspag_selects.append(SQLUtils.qspot_id)
                    if SQLUtils.qupb_id not in lspag_selects:
                        lspag_selects.append(SQLUtils.qupb_id)
                if SQLUtils.qgeochem_count.split('AS ')[1].split('"')[1] in self.show_columns:
                    if SQLUtils.qspot_id not in lspag_selects:
                        lspag_selects.append(SQLUtils.qspot_id)
                    if SQLUtils.qgeochem_id not in lspag_selects:
                        lspag_selects.append(SQLUtils.qgeochem_id)
                lsa_selects, lsa_joins = self.get_lsa_from_aliquots(lsa_select_cols, lsa_table_joins, lsa_selects)
                if lsa_selects and SQLUtils.qspot_id not in lspag_selects:
                    lspag_selects.append(SQLUtils.qspot_id)
                    if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                        lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                if where_header == 'SampleID' and 'Aliquots.SampleID AS SampleID' not in lsa_selects:
                    lsa_selects.append('Aliquots.SampleID AS SampleID')
                    if SQLUtils.qaliquot_id not in lsa_selects:
                        lsa_selects.append(SQLUtils.qaliquot_id)
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')
                        if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                            lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')
                elif where_header == 'AliquotID' and SQLUtils.qaliquot_id not in lsa_selects:
                    lsa_selects.append(SQLUtils.qaliquot_id)
                    if 'Spots.AliquotID AS AliquotID' not in lspag_selects:
                        lspag_selects.append('Spots.AliquotID AS AliquotID')
                        if f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID' not in lspag_joins:
                            lspag_joins.insert(0, f'{self.join_type} JOIN Spots ON Grains.GrainID = Spots.GrainID')

        lsa_select = ',\n'.join(lsa_selects)
        lsa_joins = '\n'.join(lsa_joins)
        lspag_select = ',\n'.join(lspag_selects)
        lspag_joins = '\n'.join(lspag_joins)
        self.limited_hierarchy = (f'''
WITH RECURSIVE ''')
        if self.create_temp_id:
            self.limited_hierarchy += f'{self.create_temp_id},'
        if self.create_temp_paged:
            self.limited_hierarchy += f'{self.create_temp_paged},'
        if where_table == 'Samples':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join and 'Samples.SampleID' in lsa_select:
                    hierarchy_where_join += f" Samples.SampleID = ti.SampleID"
                elif 'TempIDs' in hierarchy_where_join and 'Aliquots.SampleID' in lsa_select:
                    hierarchy_where_join += f" Aliquots.SampleID = ti.SampleID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SampleID' and 'Samples.SampleID' in lsa_select:
                        hierarchy_where_join += f" Samples.SampleID = tp.SampleID"
                    elif where_header == 'SampleID' and 'Aliquots.SampleID' in lsa_select:
                        hierarchy_where_join += f" Aliquots.SampleID = tp.SampleID"
            self.limited_hierarchy += (f'''
                LimitedSamplesAliquots AS (
                    SELECT 
                        {lsa_select}
                    FROM {lsa_from_table}
                    {lsa_joins}
                    {hierarchy_where_join}
                    {hierarchy_where}
                    {hierarchy_order_by} {hierarchy_limit}
                )
                ''')
            if lspag_joins or self.table in ['Spots', 'UPbAnalyses', 'Grains', 'GeoChemicalAnalyses']:
                self.limited_hierarchy += (f''',
                    LimitedSpotsAnalysesGrains AS (
                        SELECT 
                            {lspag_select}
                        FROM {lspag_from_table}
                        {lspag_joins}
                        {self.join_type if self.table in ['Samples', 'Aliquots'] else 'INNER'} JOIN LimitedSamplesAliquots lsa ON Spots.AliquotID = lsa.AliquotID
                    )
                    ''')
        elif where_table == 'Aliquots':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SampleID' in self.where and 'Samples.SampleID' in lsa_select:
                        hierarchy_where_join += f" Samples.SampleID = ti.SampleID"
                    elif 'SampleID' in self.where and 'Aliquots.SampleID' in lsa_select:
                        hierarchy_where_join += f" Aliquots.SampleID = ti.SampleID"
                    elif 'AliquotID' in self.where and 'Aliquots.AliquotID' in lsa_select:
                        hierarchy_where_join += f" Aliquots.AliquotID = ti.AliquotID"
                    elif 'AliquotID' in self.where and not lsa_select:
                        hierarchy_where_join += f" Spots.AliquotID = ti.AliquotID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SampleID' and 'Samples.SampleID' in lsa_select:
                        hierarchy_where_join += f" Samples.SampleID = tp.SampleID"
                    elif where_header == 'SampleID' and 'Aliquots.SampleID' in lsa_select:
                        hierarchy_where_join += f" Aliquots.SampleID = tp.SampleID"
                    elif where_header == 'AliquotID' and 'Aliquots.AliquotID' in lsa_select:
                        hierarchy_where_join += f" Aliquots.AliquotID = tp.AliquotID"
                    elif where_header == 'AliquotID' and not lsa_select:
                        hierarchy_where_join += f" Spots.AliquotID = tp.AliquotID"
            if lsa_selects:
                self.limited_hierarchy += (f'''
                    LimitedSamplesAliquots AS (
                        SELECT 
                            {lsa_select}
                        FROM {lsa_from_table}
                        {lsa_joins}
                        {hierarchy_where_join}
                        {hierarchy_where} 
                        {group_lsa}
                        {hierarchy_order_by} {hierarchy_limit}
                    )
                    ''')
                if lspag_joins or self.table in ['Spots', 'UPbAnalyses', 'Grains', 'GeoChemicalAnalyses']:
                    self.limited_hierarchy += (f''',
                        LimitedSpotsAnalysesGrains AS (
                            SELECT 
                                {lspag_select}
                            FROM {lspag_from_table}
                            {lspag_joins}
                            {self.join_type if self.table in ['Samples', 'Aliquots'] else 'INNER'} JOIN LimitedSamplesAliquots lsa ON Spots.AliquotID = lsa.AliquotID
                           {group_lspag}
                        )
                        ''')
            else:
                self.limited_hierarchy += (f'''
                                LimitedSpotsAnalysesGrains AS (
                                    SELECT 
                                        {lspag_select}
                                    FROM {lspag_from_table}
                                    {hierarchy_where_join}
                                    {lspag_joins}
                                    {hierarchy_where} 
                                    {group_lspag}
                                    {hierarchy_order_by} {hierarchy_limit}
                                )
                                ''')
        elif where_table == 'Spots':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SpotID' in self.where and 'Spots.SpotID' in lspag_select:
                        hierarchy_where_join += f" Spots.SpotID = ti.SpotID"
                    elif 'SpotID' in self.where and 'UPbAnalyses.SpotID' in lspag_select:
                        hierarchy_where_join += f" UPbAnalyses.SpotID = ti.SpotID"
                    elif 'AliquotID' in self.where and 'Spots.AliquotID' in lspag_select:
                        hierarchy_where_join += f" Spots.AliquotID = ti.AliquotID"
                    elif 'GrainID' in self.where and 'Grains.GrainID' in lspag_select:
                        hierarchy_where_join += f" Grains.GrainID = ti.GrainID"
                    elif 'GrainID' in self.where and 'Spots.GrainID' in lspag_select:
                        hierarchy_where_join += f" Spots.GrainID = ti.GrainID"
                    elif 'UPbAnalysisID' in self.where and 'UPbAnalyses.UPbAnalysisID' in lspag_select:
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = ti.UPbAnalysisID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SpotID' and 'Spots.SpotID' in lspag_select:
                        hierarchy_where_join += f" Spots.SpotID = tp.SpotID"
                    elif where_header == 'SpotID' and 'UPbAnalyses.SpotID' in lspag_select:
                        hierarchy_where_join += f" UPbAnalyses.SpotID = tp.SpotID"
                    elif where_header == 'AliquotID' and 'Spots.AliquotID' in lspag_select:
                        hierarchy_where_join += f" Spots.AliquotID = tp.AliquotID"
                    elif where_header == 'GrainID' and 'Grains.GrainID' in lspag_select:
                        hierarchy_where_join += f" Grains.GrainID = tp.GrainID"
                    elif where_header == 'GrainID' and 'Spots.GrainID' in lspag_select:
                        hierarchy_where_join += f" Spots.GrainID = tp.GrainID"
                    elif where_header == 'UPbAnalysisID':
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = tp.UPbAnalysisID"
            self.limited_hierarchy += (f'''
                LimitedSpotsAnalysesGrains AS (
                    SELECT 
                        {lspag_select}
                    FROM {lspag_from_table}
                    {hierarchy_where_join}
                    {lspag_joins}
                    {hierarchy_where} 
                    {group_lspag}
                    {hierarchy_order_by} {hierarchy_limit}
                )
                ''')
            if lsa_joins or self.table in ['Samples', 'Aliquots']:
                self.limited_hierarchy += (f''',
                    LimitedSamplesAliquots AS (
                        SELECT 
                            {lsa_select}
                        FROM {lsa_from_table}
                        {lsa_joins}
                        {self.join_type if self.table in ['Spots', 'Grains', 'UPbAnalyses'] else 'INNER'} JOIN LimitedSpotsAnalysesGrains lspag ON Aliquots.AliquotID = lspag.AliquotID
                       {group_lsa}
                    )
                    ''')
        elif where_table == 'UPbAnalyses':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SpotID' in self.where and 'Spots.SpotID' in lspag_select:
                        hierarchy_where_join += f" Spots.SpotID = ti.SpotID"
                    elif 'SpotID' in self.where and 'UPbAnalyses.SpotID' in lspag_select:
                        hierarchy_where_join += f" UPbAnalyses.SpotID = ti.SpotID"
                    elif 'AliquotID' in self.where:
                        hierarchy_where_join += f" Spots.AliquotID = ti.AliquotID"
                    elif 'GrainID' in self.where and 'Grains.GrainID' in lspag_select:
                        hierarchy_where_join += f" Grains.GrainID = ti.GrainID"
                    elif 'GrainID' in self.where and 'Spots.GrainID' in lspag_select:
                        hierarchy_where_join += f" Spots.GrainID = ti.GrainID"
                    elif 'UPbAnalysisID' in self.where:
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = ti.UPbAnalysisID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SpotID' and 'Spots.SpotID' in lspag_select:
                        hierarchy_where_join += f" Spots.SpotID = tp.SpotID"
                    elif where_header == 'SpotID' and 'UPbAnalyses.SpotID' in lspag_select:
                        hierarchy_where_join += f" UPbAnalyses.SpotID = tp.SpotID"
                    elif where_header == 'AliquotID' and 'Spots.AliquotID' in lspag_select:
                        hierarchy_where_join += f" Spots.AliquotID = tp.AliquotID"
                    elif where_header == 'GrainID' and 'Grains.GrainID' in lspag_select:
                        hierarchy_where_join += f" Grains.GrainID = tp.GrainID"
                    elif where_header == 'GrainID' and 'Spots.GrainID' in lspag_select:
                        hierarchy_where_join += f" Spots.GrainID = tp.GrainID"
                    elif where_header == 'UPbAnalysisID':
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = tp.UPbAnalysisID"
            self.limited_hierarchy += (f'''
                LimitedSpotsAnalysesGrains AS (
                    SELECT 
                        {lspag_select}
                    FROM {lspag_from_table}
                    {hierarchy_where_join}
                    {lspag_joins}
                    {hierarchy_where} 
                    {group_lspag}
                    {hierarchy_order_by} {hierarchy_limit}
                )
                ''')
            if lsa_joins or self.table in ['Samples', 'Aliquots']:
                self.limited_hierarchy += (f''',
                    LimitedSamplesAliquots AS (
                        SELECT 
                            {lsa_select}
                        FROM {lsa_from_table}
                        {lsa_joins}
                        {self.join_type if self.table in ['Spots', 'Grains', 'UPbAnalyses'] else 'INNER'} JOIN LimitedSpotsAnalysesGrains lspag ON Aliquots.AliquotID = lspag.AliquotID
                       {group_lsa}
                    )
                    ''')
        elif where_table == 'Grains':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SpotID' in self.where and 'Spots.SpotID' in lspag_select:
                        hierarchy_where_join += f" Spots.SpotID = ti.SpotID"
                    elif 'SpotID' in self.where and 'UPbAnalyses.SpotID' in lspag_select:
                        hierarchy_where_join += f" UPbAnalyses.SpotID = ti.SpotID"
                    elif 'AliquotID' in self.where:
                        hierarchy_where_join += f" Spots.AliquotID = ti.AliquotID"
                    elif 'GrainID' in self.where and 'Grains.GrainID' in lspag_select:
                        hierarchy_where_join += f" Grains.GrainID = ti.GrainID"
                    elif 'GrainID' in self.where and 'Spots.GrainID' in lspag_select:
                        hierarchy_where_join += f" Spots.GrainID = ti.GrainID"
                    elif 'UPbAnalysisID' in self.where:
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = ti.UPbAnalysisID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SpotID' and 'Spots.SpotID' in lspag_select:
                        hierarchy_where_join += f" Spots.SpotID = tp.SpotID"
                    elif where_header == 'SpotID' and 'UPbAnalyses.SpotID' in lspag_select:
                        hierarchy_where_join += f" UPbAnalyses.SpotID = tp.SpotID"
                    elif where_header == 'AliquotID' and 'Spots.AliquotID' in lspag_select:
                        hierarchy_where_join += f" Spots.AliquotID = tp.AliquotID"
                    elif where_header == 'GrainID' and 'Grains.GrainID' in lspag_select:
                        hierarchy_where_join += f" Grains.GrainID = tp.GrainID"
                    elif where_header == 'GrainID' and 'Spots.GrainID' in lspag_select:
                        hierarchy_where_join += f" Spots.GrainID = tp.GrainID"
                    elif where_header == 'UPbAnalysisID':
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = tp.UPbAnalysisID"
            self.limited_hierarchy += (f'''
                LimitedSpotsAnalysesGrains AS (
                    SELECT 
                        {lspag_select}
                    FROM {lspag_from_table}
                    {hierarchy_where_join}
                    {lspag_joins}
                    {hierarchy_where} 
                    {group_lspag}
                    {hierarchy_order_by} {hierarchy_limit}
                )
                ''')
            if lsa_joins or self.table in ['Samples', 'Aliquots']:
                self.limited_hierarchy += (f''',
                    LimitedSamplesAliquots AS (
                        SELECT 
                            {lsa_select}
                        FROM {lsa_from_table}
                        {lsa_joins}
                        {self.join_type if self.table in ['Spots', 'Grains', 'UPbAnalyses'] else 'INNER'} JOIN LimitedSpotsAnalysesGrains lspag ON Aliquots.AliquotID = lspag.AliquotID
                       {group_lsa}
                    )
                    ''')
        else:
            # No direct limits on the main hierarchy tables
            self.limited_hierarchy = ''
        print()

    def get_lsa_from_aliquots(self, lsa_select_cols, lsa_table_joins, lsa_selects):
        lsa_joins = []
        lsa_select_cols.append('Aliquots.SampleID AS SampleID')
        for col in lsa_select_cols:
            as_name = col.split(' AS ')[1] if ' AS ' in col else ''
            if ((as_name and as_name in self.show_columns) or
                    (col in [SQLUtils.qaliquot_id]) or (as_name in self.order_col or as_name in self.group_col
                                                        or as_name in self.where) or (
                            'ID' in col and not as_name)):
                if col not in lsa_selects:
                    lsa_selects.append(col)
                    if SQLUtils.qaliquot_id not in lsa_selects:
                        lsa_selects.append(SQLUtils.qaliquot_id)
                if col.split('.')[0].split(" ")[-1] != 'Aliquots':
                    for join in lsa_table_joins:
                        if f'JOIN {col.split(".")[0].split(" ")[-1]}' in join or f' AS {col.split(".")[0].split(" ")[-1]}' in join:
                            if join not in lsa_joins:
                                if join == f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID':
                                    # Add to the beginning of the list
                                    lsa_joins.insert(0, join)
                                else:
                                    lsa_joins.append(join)
                                if 'ON Samples.' in join and f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID' not in lsa_joins:
                                    lsa_joins.insert(0,
                                                     f'{self.join_type} JOIN Samples ON Aliquots.SampleID = Samples.SampleID')
                                    if 'Aliquots.SampleID' in lsa_selects:
                                        lsa_selects.remove('Aliquots.SampleID')
                                    if SQLUtils.qsample_id not in lsa_selects:
                                        lsa_selects.append(SQLUtils.qsample_id)
        return lsa_selects, lsa_joins

    def get_group_order_clauses(self):
        from Functions.Widget_classes import get_headers

        table_abbreviation_dict = SQLUtils.limited_table_abbreviations.copy()
        if self.table not in table_abbreviation_dict or self.table not in self.limited_tag_joins:
            self.group_by = f'GROUP BY {self.group_col}'
            self.order_by = f'ORDER BY {self.order_col} COLLATE NOCASE'
            return
        table_abbreviation = table_abbreviation_dict[self.table]
        table_abbreviation_dict.pop(self.table)

        self.group_by = ''
        if self.group_col != '':
            if self.group_col in get_headers(self.table):
                self.group_by = f'GROUP BY {table_abbreviation}.{self.group_col}'
            else:
                for key in table_abbreviation_dict:
                    if self.group_col in get_headers(key):
                        self.group_by = f'GROUP BY {table_abbreviation_dict[key]}.{self.group_col}'
                        break

        self.order_by = ''
        if self.order_col != '':
            if self.order_col in get_headers(self.table):
                self.order_by = f'ORDER BY {table_abbreviation}.{self.order_col} COLLATE NOCASE'
            else:
                for key in table_abbreviation_dict:
                    if self.order_col in get_headers(key):
                        self.order_by = f'ORDER BY {table_abbreviation_dict[key]}.{self.order_col} COLLATE NOCASE'
                        break

    def get_query_columns(self):
        self.query_columns = []
        self.lsa_columns = []
        self.lspag_columns = []
        from Functions.Widget_classes import (get_view_from_table, get_edit_view_from_table)
        if not self.edit_view:
            view_name = get_view_from_table(table=self.table)
        else:
            view_name = get_edit_view_from_table(table=self.table)
        all_view_columns = SQLUtils.view_attributes_dict[view_name]
        for column in all_view_columns:
            if 'UPbAnalyses' not in settings.value('display_analyses') and self.table != 'UPbAnalyses' and 'UPb' in column:
                continue
            if 'GeoChemicalAnalyses' not in settings.value('display_analyses') and self.table!= 'GeoChemicalAnalyses' and 'GeoChem' in column:
                continue
            if (any(leader in column for leader in SQLUtils.limited_column_leaders['LimitedSamplesAliquots'])
                    and "Accepted/Total" not in column):
                if 'REPLACE(GROUP_CONCAT(DISTINCT' in column:
                    column = column.split('DISTINCT ')[1].replace('), ",", "; ")', '')
                    if ' AS ' in column and 'ID' in column:
                        column = f"{column.split(' AS ')[0]} AS {column.split(' AS ')[0].split('.')[1]}"
                elif 'COUNT(DISTINCT' in column:
                    column = column.split('COUNT(DISTINCT ')[1].replace(')', '')
                    if ' AS ' in column and 'ID' in column:
                        column = f"{column.split(' AS ')[0]} AS {column.split(' AS ')[0].split('.')[1]}"
                self.lsa_columns.append(column) if (column not in self.lsa_columns and
                                                    not any(column.split(' AS ')[0] == lsa_column.split(' AS ')[0]
                                                            for lsa_column in self.lsa_columns)) \
                    else None
            elif (any(leader in column for leader in SQLUtils.limited_column_leaders['LimitedSpotsAnalysesGrains'])
                  and "Accepted/Total" not in column):
                if self.table == 'Grains' and 'CONCAT' in column:
                    as_name = column.split(' AS ')[1] if ' AS ' in column else ''
                    for leader in SQLUtils.limited_column_leaders['LimitedSpotsAnalysesGrains']:
                        if leader in column:
                            column_name = column.split(f'{leader}')[1].split(')')[0]
                            ungrouped_column = f'{leader}{column_name} AS {as_name}'
                            if ungrouped_column not in self.lspag_columns:
                                self.lspag_columns.append(ungrouped_column)
                            break
                else:
                    if 'REPLACE(GROUP_CONCAT(DISTINCT' in column:
                        column = column.split('DISTINCT ')[1].replace('), ",", "; ")', '')
                        if ' AS ' in column and 'ID' in column:
                            column = f"{column.split(' AS ')[0]} AS {column.split(' AS ')[0].split('.')[1]}"
                    elif 'COUNT(DISTINCT' in column:
                        column = column.split('COUNT(DISTINCT ')[1].replace(')', '')
                        if ' AS ' in column and 'ID' in column:
                            column = f"{column.split(' AS ')[0]} AS {column.split(' AS ')[0].split('.')[1]}"
                    self.lspag_columns.append(column) if (column not in self.lspag_columns and
                                                           not any(column.split(' AS ')[0] == lspag_column.split(' AS ')
                                                                   for lspag_column in self.lspag_columns)) \
                        else None
        for column in self.show_columns:
            if 'UPbAnalyses' not in settings.value(
                    'display_analyses') and self.table != 'UPbAnalyses' and 'UPb' in column:
                continue
            if 'GeoChemicalAnalyses' not in settings.value(
                    'display_analyses') and self.table != 'GeoChemicalAnalyses' and 'GeoChem' in column:
                continue
            if self.table == 'GeoChemicalAnalyses' and not any(column in view_column for view_column in all_view_columns):
                # This is an abbreviation column
                if 'Value' in column:
                    lspag_column = f'CASE WHEN GeoChemicalAnalytes.GeoChemAnalyteAbbreviation = "{column.split('Value')[0]}" THEN GeoChemicalAnalytes.GeoChemAnalyteValue END AS "{column}"'
                elif 'Unit' in column:
                    lspag_column = f'CASE WHEN GeoChemicalAnalytes.GeoChemAnalyteAbbreviation = "{column.split('Unit')[0]}" THEN GeoChemicalAnalytes.AnalyticalUnitAbbreviation END AS "{column}"'
                elif 'Format' in column:
                    lspag_column = f'CASE WHEN GeoChemicalAnalytes.GeoChemAnalyteAbbreviation = "{column.split('ErrorFormat')[0]}" THEN GeoChemicalAnalytes.ErrorFormatAbbreviation END AS "{column}"'
                elif 'Error' in column:
                    lspag_column = f'CASE WHEN GeoChemicalAnalytes.GeoChemAnalyteAbbreviation = "{column.split('Error')[0]}" THEN GeoChemicalAnalytes.CalculatedGeoChemAnalyteError END AS "{column}"'
                else:
                    lspag_column = f'CASE WHEN GeoChemicalAnalytes.GeoChemAnalyteAbbreviation = "{column}" THEN NULLIF(COALESCE(GeoChemicalAnalyses.CalculatedGeoChemAnalyteValue, "") || "±" || COALESCE(GeoChemicalAnalyses.CalculatedGeoChemAnalyteError, ""), "±") END AS "{column}"'
                self.lspag_columns.append(lspag_column)
                self.query_columns.append(column)
            else:
                for view_column in all_view_columns:
                    if column in view_column:
                        self.query_columns.append(view_column)
                        break

        if self.table in self.limited_tag_joins:
            for col in range(len(self.query_columns)):
                column = self.query_columns[col]
                for key, value in SQLUtils.limited_table_abbreviations.items():
                    if key in ['Spots', 'UPbAnalyses', 'Grains', 'GeoChemicalAnalyses']:
                        value = 'lspag'

                    if value in ('lsa', 'lspag'):
                        if self.table == 'Grains' and 'CONCAT' in column:
                            if key in column:
                                column_name = column.split(f'{key}.')[1].split(')')[0]
                                as_name = column.split(' AS ')[1] if ' AS ' in column else ''
                                column = f'{column.split(' AS ')[0].replace(column_name, as_name)} AS {as_name}'
                        else:
                            if any(pattern in column for pattern in [f' {key}.', f'({key}.']) or column.startswith(key):
                                if ' AS ' in column:
                                    if column in self.lsa_columns or column in self.lspag_columns:
                                        # Replace the longer column selection with the name after ' AS '
                                        column = f'{value}.{column.split(" AS ")[1]}'
                                        self.query_columns[col] = column
                                    elif 'ID' not in column:
                                        as_name = column.split(' AS ')[1]
                                        column_name = column.split('.')[1].split(' AS ')[0]
                                        if ')' in column_name:
                                            column_name = column_name.split(')')[0]
                                        if column_name != as_name:
                                            column = f"{column.split(column_name)[0]}{as_name}{f'{column_name}'.join(column.split(column_name)[1:])}"
                    column = column.replace(f' {key}.', f' {value}.')
                    column = column.replace(f'({key}.', f'({value}.')
                    if column.startswith(f'{key}.'):
                        column = f'{value}.{column.split(f"{key}.", 1)[1]}'
                    if self.query_columns[col] != column and f'{value}.' in column:
                        # Update the column in the query_columns list if it was modified
                        self.query_columns[col] = column
                        break

            for table, limited_tag_join in self.limited_tag_joins.items():
                for join in limited_tag_join:
                    tag_table = join.split(' ')[2]
                    abbreviation = join.split(' ')[3]
                    for key, value in SQLUtils.limited_table_abbreviations.items():
                        if key in ['Spots', 'UPbAnalyses', 'Grains',
                                   'GeoChemicalAnalyses']:
                            value = 'lspag'
                        if abbreviation == value and any(f'{value}.' in col for col in self.query_columns):
                            # Include the limited table and join if any columns from that table are included in the query
                            if table not in self.query_tags_joins:
                                self.query_tags_joins[table] = []
                            if join not in self.query_tags_joins[table]:
                                self.query_tags_joins[table].append(join)
                            for limited_tag in self.limited_tags[table]:
                                if limited_tag.startswith(tag_table):
                                    if table not in self.query_tags:
                                        self.query_tags[table] = []
                                    if limited_tag not in self.query_tags[table]:
                                        self.query_tags[table].append(limited_tag)
                                    break
                            break

def upb_columns(edit: bool) -> list:
    from Functions.Widget_classes import get_headers

    headers = get_headers('UPbAnalyses')
    columns = []
    if not edit:
        for header in headers:
            if f'UPbAnalyses."{header}" AS "{header}"' in columns:
                continue
            if 'Calculated' in header:
                if f'UPbAnalyses."{header}" AS "{header}"' not in columns:
                    columns.append(f'UPbAnalyses."{header}" AS "{header}"')
                if f'{header}Error' in headers and f'UPbAnalyses."{header}Error" AS "{header}Error"' not in columns:
                    columns.append(f'UPbAnalyses."{header}Error" AS "{header}Error"')
            elif f'Calculated{header}' in headers:
                pass
            elif 'ID' in header or 'Rejected' in header or 'Created' in header or 'Modified' in header:
                pass
            elif f'UPbAnalyses."{header}" AS "{header}"' not in columns:
                columns.append(f'UPbAnalyses."{header}" AS "{header}"')

    if edit:
        for header in headers:
            if f'UPbAnalyses."{header}" AS "{header}"' in columns:
                continue
            elif 'ID' in header or 'Rejected' in header or 'Created' in header or 'Modified' in header:
                pass
            elif 'Calculated' in header:
                pass
            else:
                if f'UPbAnalyses."{header}" AS "{header}"' not in columns:
                    columns.append(f'UPbAnalyses."{header}" AS "{header}"')
                if f'{header}Error' in headers and f'UPbAnalyses."{header}Error" AS "{header}Error"' not in columns:
                    columns.append(f'UPbAnalyses."{header}Error" AS "{header}Error"')

    return columns