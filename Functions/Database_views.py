import sqlite3
import time

from PyQt6 import QtSql as QtS

import Functions.SQLUtils as SQLUtils
import logger_setup
from Functions.Settings_manager import SettingsManager
settings = SettingsManager().settings

class ViewQuery:
    def __init__(self, table: str, edit_view: bool = False, **kwargs):
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
        self.update_query(table, edit_view, **kwargs)

    def update_query(self, table: str, edit_view: bool = False, **kwargs):
        self.table = table
        self.edit_view = edit_view
        self.kwargs = kwargs
        if self.table == 'Samples' and not self.edit_view:
            self.create_sample_view_query()
        elif self.table == 'Samples' and self.edit_view:
            self.create_sample_edit_view_query()
        elif self.table == 'Aliquots' and not self.edit_view:
            self.create_aliquot_view_query()
        elif self.table == 'Aliquots' and self.edit_view:
            self.create_aliquot_edit_view_query()
        elif self.table == 'Grains' and not self.edit_view:
            self.create_grain_view_query()
        elif self.table == 'Grains' and self.edit_view:
            self.create_grain_edit_view_query()
        elif self.table == 'Spots' and not self.edit_view:
            self.create_spot_view_query()
        elif self.table == 'Spots' and self.edit_view:
            self.create_spot_edit_view_query()
        elif self.table == 'UPbAnalyses' and not self.edit_view:
            self.create_upb_view_query()
        elif self.table == 'UPbAnalyses' and self.edit_view:
            self.create_upb_edit_view_query()
        elif self.table == 'Columns' and not self.edit_view:
            self.create_column_view_query()
        elif self.table == 'Columns' and self.edit_view:
            self.create_column_edit_view_query()
        elif self.table == 'References' or self.table == '"References"':
            self.create_reference_view_query()

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

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        # Select columns
        query_column_list = [SQLUtils.qsample_id,
                        SQLUtils.qigsn,
                        SQLUtils.qsample_name,
                        SQLUtils.qsample_description,
                        SQLUtils.qsample_gps_id,
                        SQLUtils.qgps_display,
                        SQLUtils.qsample_elev_display,
                        SQLUtils.qsample_elev_unit,
                        SQLUtils.qgps,
                        SQLUtils.qsample_elev,
                        SQLUtils.qsample_age,
                        SQLUtils.qsample_age_constraint,
                        SQLUtils.qsample_age_interpretation,
                        SQLUtils.qsample_age_references,
                        SQLUtils.qcolumn_name,
                        SQLUtils.qsample_column_data,
                        SQLUtils.qage_signature,
                        SQLUtils.qregions,
                        SQLUtils.qrock_types,
                        SQLUtils.qsample_context,
                        SQLUtils.qsampling_methods,
                        SQLUtils.qsettings,
                        SQLUtils.qunits,
                        SQLUtils.qaliquots,
                        SQLUtils.qaliquot_contexts,
                        SQLUtils.qgrain_count,
                        SQLUtils.qgrain_compositions,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qspot_count,
                        SQLUtils.qspot_compositions,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qupb_count,
                        SQLUtils.qupb_lab_facilities,
                        SQLUtils.qupb_analysis_methods,
                        SQLUtils.qupb_ratio_error_formats,
                        SQLUtils.qupb_age_units,
                        SQLUtils.qupb_age_error_formats,
                        SQLUtils.qconcordance_formats,
                        SQLUtils.qspot_sizes,
                        SQLUtils.qspot_size,
                        SQLUtils.qspot_size_unit,
                        SQLUtils.qupb_rejection_reasons,
                        SQLUtils.qupb_contexts,
                        SQLUtils.qupb_age_interpretations,
                        SQLUtils.qupb_references,
                        SQLUtils.qsample_created,
                        SQLUtils.qsample_modified]
        lsa_column_list = [SQLUtils.qsample_id,
                             SQLUtils.qigsn,
                             SQLUtils.qsample_name,
                             SQLUtils.qsample_description,
                             SQLUtils.qsample_gps_id,
                             SQLUtils.qgps_display,
                             SQLUtils.qsample_elev_display,
                             SQLUtils.qsample_elev_unit,
                             SQLUtils.qgps,
                             SQLUtils.qsample_elev,
                             SQLUtils.qcolumn_name,
                             SQLUtils.qsample_column_data,
                             SQLUtils.qaliquots,
                             SQLUtils.qsample_created,
                             SQLUtils.qsample_modified]
        lspuag_column_list = [SQLUtils.qgrain_count,
                             SQLUtils.qgrain_compositions,
                             SQLUtils.qspot_count,
                             SQLUtils.qspot_compositions,
                             SQLUtils.qupb_lab_facilities,
                             SQLUtils.qupb_analysis_methods,
                             SQLUtils.qupb_ratio_error_formats,
                             SQLUtils.qupb_age_units,
                             SQLUtils.qupb_age_error_formats,
                             SQLUtils.qconcordance_formats,
                             SQLUtils.qspot_sizes,
                             SQLUtils.qspot_size,
                             SQLUtils.qspot_size_unit,
                             SQLUtils.qupb_age_interpretations,
                             SQLUtils.qupb_references]
        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.',1)[1]}'
        query_columns = query_columns.strip()

        count_sample_subquery = SQLUtils.qupb_count_sample_subquery

        sample_query = f'''
                {self.limited_hierarchy},
                {SQLUtils.limited_sample_tags},
                {SQLUtils.limited_aliquot_tags},
                {SQLUtils.limited_spot_tags},
                {SQLUtils.limited_upb_tags},
                {count_sample_subquery}
                SELECT
                        {query_columns}
                       FROM LimitedSamplesAliquots lsa
                       {SQLUtils.limited_sample_aliquot_hierarchy_join}
                       {SQLUtils.limited_sample_tags_join}
                       {SQLUtils.limited_aliquot_tags_join}
                       {SQLUtils.limited_spot_tags_join}
                       {SQLUtils.limited_upb_tags_join}
                       {SQLUtils.upb_distinct_join_limited_sample}
                        {self.query_where}
                        {self.group_by}
                        {self.order_by}
                        {self.query_limit}
                       '''

        # print(sample_query)
        self.table_query = sample_query

    def create_sample_edit_view_query(self):
        self.show_columns: list = settings.value('sample_edit_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'SampleID'
        self.order_col: str = 'SampleName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        query_column_list = [SQLUtils.qsample_id,
                        SQLUtils.qigsn,
                        SQLUtils.qsample_name,
                        SQLUtils.qsample_description,
                        SQLUtils.qsample_gps_id,
                        SQLUtils.qgps_display,
                        SQLUtils.qsample_elev_display,
                        SQLUtils.qsample_elev_unit,
                        SQLUtils.qgps,
                        SQLUtils.qsample_elev,
                        SQLUtils.qsample_age,
                        SQLUtils.qsample_age_constraint,
                        SQLUtils.qsample_age_interpretation,
                        SQLUtils.qsample_age_references,
                        SQLUtils.qcolumn_name,
                        SQLUtils.qsample_column_data_display,
                        SQLUtils.qsample_column_data_unit,
                        SQLUtils.qage_signature,
                        SQLUtils.qregions,
                        SQLUtils.qrock_types,
                        SQLUtils.qsample_context,
                        SQLUtils.qsampling_methods,
                        SQLUtils.qunits,
                        SQLUtils.qaliquots,
                        SQLUtils.qaliquot_contexts,
                        SQLUtils.qgrain_count,
                        SQLUtils.qgrain_compositions,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qspot_count,
                        SQLUtils.qspot_compositions,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qupb_count,
                        SQLUtils.qupb_lab_facilities,
                        SQLUtils.qupb_analysis_methods,
                        SQLUtils.qupb_ratio_error_formats,
                        SQLUtils.qupb_age_units,
                        SQLUtils.qupb_age_error_formats,
                        SQLUtils.qconcordance_formats,
                        SQLUtils.qspot_sizes,
                        SQLUtils.qspot_size,
                        SQLUtils.qspot_size_unit,
                        SQLUtils.qupb_rejection_reasons,
                        SQLUtils.qupb_contexts,
                        SQLUtils.qupb_age_interpretations,
                        SQLUtils.qupb_references,
                        SQLUtils.qsample_created,
                        SQLUtils.qsample_modified]
        lsa_column_list = [SQLUtils.qsample_id,
                           SQLUtils.qigsn,
                           SQLUtils.qsample_name,
                           SQLUtils.qsample_description,
                           SQLUtils.qsample_gps_id,
                           SQLUtils.qgps_display,
                           SQLUtils.qsample_elev_display,
                           SQLUtils.qsample_elev_unit,
                           SQLUtils.qgps,
                           SQLUtils.qsample_elev,
                           SQLUtils.qcolumn_name,
                           SQLUtils.qsample_column_data_display,
                           SQLUtils.qsample_column_data_unit,
                           SQLUtils.qaliquots,
                           SQLUtils.qsample_created,
                           SQLUtils.qsample_modified]
        lspuag_column_list = [SQLUtils.qgrain_count,
                              SQLUtils.qgrain_compositions,
                              SQLUtils.qspot_count,
                              SQLUtils.qspot_compositions,
                              SQLUtils.qupb_lab_facilities,
                              SQLUtils.qupb_analysis_methods,
                              SQLUtils.qupb_ratio_error_formats,
                              SQLUtils.qupb_age_units,
                              SQLUtils.qupb_age_error_formats,
                              SQLUtils.qconcordance_formats,
                              SQLUtils.qspot_sizes,
                              SQLUtils.qspot_size,
                              SQLUtils.qspot_size_unit,
                              SQLUtils.qupb_age_interpretations,
                              SQLUtils.qupb_references]
        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        count_sample_subquery = SQLUtils.qupb_count_sample_subquery

        sample_query = f'''
                        {self.limited_hierarchy},
                        {SQLUtils.limited_sample_tags},
                        {SQLUtils.limited_aliquot_tags},
                        {SQLUtils.limited_spot_tags},
                        {SQLUtils.limited_upb_tags},
                        {count_sample_subquery}
                        SELECT
                                {query_columns}
                               FROM LimitedSamplesAliquots lsa
                               {SQLUtils.limited_sample_aliquot_hierarchy_join}
                               {SQLUtils.limited_sample_tags_join}
                               {SQLUtils.limited_aliquot_tags_join}
                               {SQLUtils.limited_spot_tags_join}
                               {SQLUtils.limited_upb_tags_join}
                               {SQLUtils.upb_distinct_join_limited_sample}
                                {self.query_where}
                                {self.group_by}
                                {self.order_by}
                                {self.query_limit}
                               '''

        # print(sample_query)
        self.table_query = sample_query

    def create_aliquot_view_query(self):

        self.show_columns: list = settings.value('aliquot_view_columns')
        self.where: str = ''
        self.group_col: str = 'AliquotID'
        self.order_col: str = 'AliquotName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        query_column_list = [SQLUtils.qaliquot_id,
                        SQLUtils.qaliquot_parent_id,
                        SQLUtils.qaliquot_parent_row,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_id,
                        SQLUtils.qaliquot_sample,
                        SQLUtils.qaliquot_contexts,
                        SQLUtils.qgrain_count,
                        SQLUtils.qgrain_compositions,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qspot_count,
                        SQLUtils.qspot_compositions,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qupb_count,
                        SQLUtils.qupb_lab_facilities,
                        SQLUtils.qupb_analysis_methods,
                        SQLUtils.qupb_ratio_error_formats,
                        SQLUtils.qupb_age_units,
                        SQLUtils.qupb_age_error_formats,
                        SQLUtils.qconcordance_formats,
                        SQLUtils.qspot_sizes,
                        SQLUtils.qupb_rejection_reasons,
                        SQLUtils.qupb_contexts,
                        SQLUtils.qupb_age_interpretations,
                        SQLUtils.qupb_references,
                        SQLUtils.qaliquot_created,
                        SQLUtils.qaliquot_modified]
        lsa_column_list = [SQLUtils.qaliquot_id,
                             SQLUtils.qaliquot_parent_id,
                             SQLUtils.qaliquot_parent_row,
                             SQLUtils.qaliquot_name,
                             SQLUtils.qsample_id,
                             SQLUtils.qaliquot_sample,
                             SQLUtils.qaliquot_created,
                             SQLUtils.qaliquot_modified]
        lspuag_column_list = [SQLUtils.qgrain_count,
                             SQLUtils.qgrain_compositions,
                             SQLUtils.qspot_count,
                             SQLUtils.qspot_compositions,
                             SQLUtils.qupb_lab_facilities,
                             SQLUtils.qupb_analysis_methods,
                             SQLUtils.qupb_ratio_error_formats,
                             SQLUtils.qupb_age_units,
                             SQLUtils.qupb_age_error_formats,
                             SQLUtils.qconcordance_formats,
                             SQLUtils.qspot_sizes,
                             SQLUtils.qupb_age_interpretations,
                             SQLUtils.qupb_references]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        count_aliquot_subquery = SQLUtils.qupb_count_aliquot_subquery

        aliquot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_aliquot_tags},
                    {count_aliquot_subquery},
                    {SQLUtils.limited_spot_tags},
                    {SQLUtils.limited_upb_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedSamplesAliquots lsa
                    {SQLUtils.limited_sample_aliquot_hierarchy_join}
                    {SQLUtils.limited_aliquot_tags_join}
                    {SQLUtils.limited_spot_tags_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.upb_distinct_join_limited_aliquot}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    '''

        self.table_query = aliquot_query

    def create_aliquot_edit_view_query(self):
        self.show_columns: list = settings.value('aliquot_edit_columns')
        self.where: str = ''
        self.group_col: str = 'AliquotID'
        self.order_col: str = 'AliquotName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        query_column_list = [SQLUtils.qaliquot_id,
                        SQLUtils.qaliquot_parent_id,
                        SQLUtils.qaliquot_parent_row,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_id,
                        SQLUtils.qaliquot_sample,
                        SQLUtils.qaliquot_contexts,
                        SQLUtils.qaliquot_created,
                        SQLUtils.qaliquot_modified]
        lsa_column_list = [SQLUtils.qaliquot_id,
                        SQLUtils.qaliquot_parent_id,
                        SQLUtils.qaliquot_parent_row,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_id,
                        SQLUtils.qaliquot_sample,
                        SQLUtils.qaliquot_created,
                        SQLUtils.qaliquot_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        aliquot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_aliquot_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedSamplesAliquots lsa
                    {SQLUtils.limited_sample_aliquot_hierarchy_join}
                    {SQLUtils.limited_aliquot_tags_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    '''

        self.table_query = aliquot_query

    def create_grain_view_query(self):

        self.show_columns: list = settings.value('grain_view_columns')
        self.where: str = ''
        self.group_col: str = 'GrainID'
        self.order_col: str = 'GrainName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        query_column_list = [SQLUtils.qgrain_id,
                             SQLUtils.qspot_id,
                             SQLUtils.qaliquot_id,
                             SQLUtils.qsample_id,
                             SQLUtils.qgrain_name,
                             SQLUtils.qgrain_description,
                             SQLUtils.qspot_name,
                             SQLUtils.qaliquot_name,
                             SQLUtils.qsample_name,
                             SQLUtils.qgrain_composition,
                             SQLUtils.qgrain_contexts,
                             SQLUtils.qspot_compositions,
                             SQLUtils.qspot_contexts,
                             SQLUtils.qupb_lab_facilities,
                             SQLUtils.qupb_instruments,
                             SQLUtils.qupb_analysis_methods,
                             SQLUtils.qupb_ratio_error_formats,
                             SQLUtils.qupb_age_units,
                             SQLUtils.qupb_age_error_formats,
                             SQLUtils.qconcordance_formats,
                             SQLUtils.qspot_sizes,
                             SQLUtils.qupb_contexts,
                             SQLUtils.qupb_age_interpretations,
                             SQLUtils.qupb_count,
                             SQLUtils.qupb_rejection_reasons,
                             SQLUtils.qupb_references,
                             SQLUtils.qgrain_created,
                             SQLUtils.qgrain_modified]
        lsa_column_list = [SQLUtils.qaliquot_id,
                             SQLUtils.qsample_id,
                             SQLUtils.qaliquot_name,
                             SQLUtils.qsample_name]
        lspuag_column_list = [SQLUtils.qgrain_id,
                             SQLUtils.qspot_id,
                             SQLUtils.qgrain_name,
                             SQLUtils.qgrain_description,
                             SQLUtils.qspot_name,
                             SQLUtils.qgrain_composition,
                             SQLUtils.qspot_compositions,
                             SQLUtils.qupb_lab_facilities,
                             SQLUtils.qupb_instruments,
                             SQLUtils.qupb_analysis_methods,
                             SQLUtils.qupb_ratio_error_formats,
                             SQLUtils.qupb_age_units,
                             SQLUtils.qupb_age_error_formats,
                             SQLUtils.qconcordance_formats,
                             SQLUtils.qspot_sizes,
                             SQLUtils.qupb_age_interpretations,
                             SQLUtils.qupb_references,
                             SQLUtils.qgrain_created,
                             SQLUtils.qgrain_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        count_grain_subquery = SQLUtils.qupb_count_grain_subquery

        grain_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_spot_tags},
                    {SQLUtils.limited_upb_tags},
                    {count_grain_subquery}
                    SELECT
                        {query_columns}
                    FROM LimitedSpotsUPbAnalysesGrains lspuag
                    {SQLUtils.limited_spot_upb_grain_hierarchy_join}
                    {SQLUtils.limited_spot_tags_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.upb_distinct_join_limited_grain}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''
        grain_query = grain_query.strip()
        self.table_query = grain_query

    def create_grain_edit_view_query(self):
        self.show_columns: list = settings.value('grain_edit_columns')
        self.where: str = ''
        self.group_col: str = 'GrainID'
        self.order_col: str = 'GrainName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        query_column_list = [SQLUtils.qgrain_id,
                        SQLUtils.qgrain_name,
                        SQLUtils.qgrain_description,
                        SQLUtils.qgrain_composition,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qgrain_created,
                        SQLUtils.qgrain_modified]
        lspuag_column_list = [SQLUtils.qgrain_id,
                        SQLUtils.qgrain_name,
                        SQLUtils.qgrain_description,
                        SQLUtils.qgrain_composition,
                        SQLUtils.qgrain_created,
                        SQLUtils.qgrain_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        grain_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_spot_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedSpotsUPbAnalysesGrains lspuag
                    {SQLUtils.limited_spot_upb_grain_hierarchy_join}
                    {SQLUtils.limited_spot_tags_join}
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

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        query_column_list = [SQLUtils.qspot_id,
                        SQLUtils.qaliquot_id,
                        SQLUtils.qsample_id,
                        SQLUtils.qspot_name,
                        SQLUtils.qupb_analyses,
                        SQLUtils.qgrain_name,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_name,
                        SQLUtils.qspot_composition,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qgrain_composition,
                        SQLUtils.qupb_lab_facilities,
                        SQLUtils.qupb_instruments,
                        SQLUtils.qupb_analysis_methods,
                        SQLUtils.qupb_ratio_error_formats,
                        SQLUtils.qupb_age_units,
                        SQLUtils.qupb_age_error_formats,
                        SQLUtils.qconcordance_formats,
                        SQLUtils.qspot_sizes,
                        SQLUtils.qupb_contexts,
                        SQLUtils.qupb_age_interpretations,
                        SQLUtils.qupb_count,
                        SQLUtils.qupb_rejection_reasons,
                        SQLUtils.qupb_references,
                        SQLUtils.qspot_created,
                        SQLUtils.qspot_modified]
        lsa_column_list = [SQLUtils.qaliquot_id,
                             SQLUtils.qsample_id,
                             SQLUtils.qaliquot_name,
                             SQLUtils.qsample_name]
        lspuag_column_list = [SQLUtils.qspot_id,
                             SQLUtils.qspot_name,
                             SQLUtils.qupb_analyses,
                             SQLUtils.qgrain_name,
                             SQLUtils.qspot_composition,
                             SQLUtils.qgrain_composition,
                             SQLUtils.qupb_lab_facilities,
                             SQLUtils.qupb_instruments,
                             SQLUtils.qupb_analysis_methods,
                             SQLUtils.qupb_ratio_error_formats,
                             SQLUtils.qupb_age_units,
                             SQLUtils.qupb_age_error_formats,
                             SQLUtils.qconcordance_formats,
                             SQLUtils.qspot_sizes,
                             SQLUtils.qupb_age_interpretations,
                             SQLUtils.qupb_references,
                             SQLUtils.qspot_created,
                             SQLUtils.qspot_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] == column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        count_spot_subquery = SQLUtils.qupb_count_spot_subquery

        spot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_spot_tags},
                    {SQLUtils.limited_upb_tags},
                    {count_spot_subquery}
                    SELECT
                        {query_columns}
                    FROM LimitedSpotsUPbAnalysesGrains lspuag
                    {SQLUtils.limited_spot_upb_grain_hierarchy_join}
                    {SQLUtils.limited_spot_tags_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.upb_distinct_join_limited_spot}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        self.table_query = spot_query


    def create_spot_edit_view_query(self):
        self.show_columns: list = settings.value('spot_edit_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'SpotID'
        self.order_col: str = 'SpotName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        query_column_list = [SQLUtils.qspot_id,
                        SQLUtils.qaliquot_id,
                        SQLUtils.qsample_id,
                        SQLUtils.qspot_name,
                        SQLUtils.qupb_analyses,
                        SQLUtils.qgrain_name,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_name,
                        SQLUtils.qspot_composition,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qgrain_composition,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qspot_created,
                        SQLUtils.qspot_modified]
        lsa_column_list = [SQLUtils.qaliquot_id,
                                 SQLUtils.qsample_id,
                                 SQLUtils.qaliquot_name,
                                 SQLUtils.qsample_name]
        lspuag_column_list = [SQLUtils.qspot_id,
                        SQLUtils.qspot_name,
                        SQLUtils.qupb_analyses,
                        SQLUtils.qgrain_name,
                        SQLUtils.qspot_composition,
                        SQLUtils.qgrain_composition,
                        SQLUtils.qspot_created,
                        SQLUtils.qspot_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        spot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_spot_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedSpotsUPbAnalysesGrains lspuag
                    {SQLUtils.limited_spot_upb_grain_hierarchy_join}
                    {SQLUtils.limited_spot_tags_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        self.table_query = spot_query


    def create_upb_view_query(self):
        self.show_columns: list = settings.value('upb_analysis_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'UPbAnalysisID'
        self.order_col: str = 'UPbAnalysisName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        upb_query_columns = upb_columns(False)

        query_columns1 = [SQLUtils.qupb_id,
                        SQLUtils.qspot_id,
                        SQLUtils.qaliquot_id,
                        SQLUtils.qsample_id,
                        SQLUtils.qupb_analysis_name,
                        SQLUtils.qspot_name,
                        SQLUtils.qgrain_name,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_name,
                        SQLUtils.qupb_references,
                        SQLUtils.qupb_lab_facilities,
                        SQLUtils.qupb_instruments,
                        SQLUtils.qupb_analysis_methods,]

        query_columns2 = [SQLUtils.qupb_rejected,
                        SQLUtils.qupb_rejection_reasons,
                        SQLUtils.qupb_contexts,
                        SQLUtils.qupb_age_interpretations,
                        SQLUtils.qspot_composition,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qgrain_composition,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qupb_created,
                        SQLUtils.qupb_modified]

        lsa_column_list = [SQLUtils.qaliquot_id,
                          SQLUtils.qsample_id,
                          SQLUtils.qaliquot_name,
                          SQLUtils.qsample_name]

        lspuag_column_list = [SQLUtils.qupb_id,
                          SQLUtils.qspot_id,
                          SQLUtils.qupb_analysis_name,
                          SQLUtils.qspot_name,
                          SQLUtils.qgrain_name,
                          SQLUtils.qupb_references,
                          SQLUtils.qupb_lab_facilities,
                          SQLUtils.qupb_instruments,
                          SQLUtils.qupb_analysis_methods,
                          SQLUtils.qupb_rejected,
                          SQLUtils.qupb_age_interpretations,
                          SQLUtils.qspot_composition,
                          SQLUtils.qgrain_composition,
                          SQLUtils.qupb_created,
                          SQLUtils.qupb_modified]
        lspuag_column_list.extend(upb_query_columns)

        query_column_list = query_columns1 + upb_query_columns + query_columns2
        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        upb_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_upb_tags},
                    {SQLUtils.limited_spot_tags}
                    SELECT 
                        {query_columns}
                    FROM LimitedSpotsUPbAnalysesGrains lspuag
                    {SQLUtils.limited_spot_upb_grain_hierarchy_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.limited_spot_tags_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        self.table_query = upb_query

    def create_upb_edit_view_query(self):
        self.show_columns: list = settings.value('upb_analysis_edit_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'UPbAnalysisID'
        self.order_col: str = 'UPbAnalysisName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        upb_query_columns = upb_columns(True)

        query_columns1 = [SQLUtils.qupb_id,
                        SQLUtils.qspot_id,
                        SQLUtils.qaliquot_id,
                        SQLUtils.qsample_id,
                        SQLUtils.qupb_analysis_name,
                        SQLUtils.qspot_name,
                        SQLUtils.qgrain_name,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_name,
                        SQLUtils.qupb_references,
                        SQLUtils.qupb_lab_facilities,
                        SQLUtils.qupb_instruments,
                        SQLUtils.qupb_analysis_methods]
        query_columns2 = [SQLUtils.qupb_ratio_error_formats,
                        SQLUtils.qupb_age_units,
                        SQLUtils.qupb_age_error_formats,
                        SQLUtils.qconcordance_formats,
                        SQLUtils.qspot_size_unit,
                        SQLUtils.qupb_rejected,
                        SQLUtils.qupb_rejection_reasons,
                        SQLUtils.qupb_contexts,
                        SQLUtils.qupb_age_interpretations,
                        SQLUtils.qspot_composition,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qgrain_composition,
                        SQLUtils.qgrain_contexts,
                        SQLUtils.qupb_created,
                        SQLUtils.qupb_modified]

        lsa_column_list = [SQLUtils.qaliquot_id,
                          SQLUtils.qsample_id,
                          SQLUtils.qaliquot_name,
                          SQLUtils.qsample_name]

        lspuag_column_list = [SQLUtils.qupb_id,
                          SQLUtils.qspot_id,
                          SQLUtils.qupb_analysis_name,
                          SQLUtils.qspot_name,
                          SQLUtils.qgrain_name,
                          SQLUtils.qupb_references,
                          SQLUtils.qupb_lab_facilities,
                          SQLUtils.qupb_instruments,
                          SQLUtils.qupb_analysis_methods,
                          SQLUtils.qupb_ratio_error_formats,
                          SQLUtils.qupb_age_units,
                          SQLUtils.qupb_age_error_formats,
                          SQLUtils.qconcordance_formats,
                          SQLUtils.qspot_size_unit,
                          SQLUtils.qupb_rejected,
                          SQLUtils.qupb_age_interpretations,
                          SQLUtils.qspot_composition,
                          SQLUtils.qgrain_composition,
                          SQLUtils.qupb_created,
                          SQLUtils.qupb_modified]
        lspuag_column_list.extend(upb_query_columns)

        query_column_list = query_columns1 + upb_query_columns + query_columns2
        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col in lsa_column_list:
                        sql_col = f"lsa.{column}"
                    elif col in lspuag_column_list:
                        sql_col = f"lspuag.{column}"
                    else:
                        sql_col = col
                    query_columns.append(sql_col)
                    break
        query_columns = ',\n '.join(query_columns)

        for key, value in SQLUtils.limited_table_abbreviations.items():
            query_columns = query_columns.replace(f' {key}.', f' {value}.')
            query_columns = query_columns.replace(f'({key}.', f'({value}.')
            if query_columns.startswith(f'{key}.'):
                query_columns = f'{value}.{query_columns.split(f'{key}.', 1)[1]}'
        query_columns = query_columns.strip()

        upb_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_upb_tags},
                    {SQLUtils.limited_spot_tags}
                    SELECT 
                        {query_columns}
                    FROM LimitedSpotsUPbAnalysesGrains lspuag
                    {SQLUtils.limited_spot_upb_grain_hierarchy_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.limited_spot_tags_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''
        self.table_query = upb_query

    def create_column_view_query(self):
        self.show_columns: list = settings.value('column_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'Columns.ColumnID'
        self.order_col: str = 'Columns.ColumnName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        # Select columns
        query_column_list = [SQLUtils.qcolumn_id,
                        SQLUtils.qcolumn_name,
                        SQLUtils.qcolumn_calc_total_height_depth,
                        SQLUtils.qcolumn_gps,
                        SQLUtils.qcolumn_elev,
                        SQLUtils.qcolumn_description,
                        SQLUtils.qcolumn_created,
                        SQLUtils.qcolumn_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        column_query = f'''
                    SELECT
                        {query_columns}
                    FROM Columns
                    {SQLUtils.gps_column_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''
        self.table_query = column_query


    def create_column_edit_view_query(self):
        self.show_columns: list = settings.value('column_edit_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'Columns.ColumnID'
        self.order_col: str = 'Columns.ColumnName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        # Select columns
        query_column_list = [SQLUtils.qcolumn_id,
                        SQLUtils.qcolumn_name,
                        SQLUtils.qcolumn_total_height_depth,
                        SQLUtils.qcolumn_total_height_depth_unit,
                        SQLUtils.qcolumn_gps_id,
                        SQLUtils.qcolumn_gps_display,
                        SQLUtils.qcolumn_elev_display,
                        SQLUtils.qcolumn_elev_unit,
                        SQLUtils.qcolumn_description,
                        SQLUtils.qcolumn_created,
                        SQLUtils.qcolumn_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        column_query = f'''
                        SELECT
                            {query_columns}
                        FROM Columns
                        {SQLUtils.column_units_join}
                        {SQLUtils.gps_column_join}
                        {SQLUtils.gps_column_left_joins}
                        {self.query_where}
                        {self.group_by}
                        {self.order_by}
                        {self.query_limit}
                        '''
        # print(column_query)
        self.table_query = column_query


    def create_reference_view_query(self):
        self.show_columns: list = settings.value('reference_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = '"References".ReferenceID'
        self.order_col: str = '"References".ReferenceDisplay'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        # Select columns
        query_column_list = [SQLUtils.qreference_id,
                        SQLUtils.qreference_display,
                        SQLUtils.qauthors,
                        SQLUtils.qyear,
                        SQLUtils.qtitle,
                        SQLUtils.qsource,
                        SQLUtils.qdoi,
                        SQLUtils.qreference_description,
                        SQLUtils.qreference_created,
                        SQLUtils.qreference_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        reference_query = f'''
                    SELECT
                        {query_columns}
                    FROM "References"
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''
        # print(reference_query)
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

        if self.table not in table_abbreviation_dict:
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
                            self.create_temp_id = f"CREATE TEMP TABLE TempIDs ({where_header} INTEGER PRIMARY KEY)"
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
                            self.create_temp_paged = f"""CREATE TEMP TABLE TempPaged AS
                                                            SELECT TempIDs.{where_header} FROM TempIDs
                                                            JOIN {self.table} ON {self.table}.{where_header} = TempIDs.{where_header}
                                                            ORDER BY {self.order_col} {self.limit}
                                                            """
                        else:
                            where_header = headers[0]
                            self.create_temp_paged = f"""CREATE TEMP TABLE TempPaged AS
                                                            SELECT {headers[0]} FROM {self.table}
                                                            ORDER BY {self.order_col} {self.limit}
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
                        self.create_temp_paged = f"""CREATE TEMP TABLE TempPaged AS
                                                        SELECT TempIDs.{where_header} FROM TempIDs
                                                        JOIN {self.table} ON {self.table}.{where_header} = TempIDs.{where_header}
                                                        {self.limit}
                                                        """
                    else:
                        self.create_temp_paged = f"""CREATE TEMP TABLE TempPaged AS
                                                        SELECT {where_header} FROM {self.table}
                                                        {self.limit}
                                                        """
                    hierarchy_where_join = f"INNER JOIN TempPaged tp ON"
                    hierarchy_order_by = ''
                    hierarchy_limit = ''
                    self.query_limit = ''
            else:
                for key in table_abbreviation_dict.keys():
                    if any(header in self.where for header in get_headers(key)):
                        where_table = key
                        # Find which header is in the where clause
                        for header in get_headers(key):
                            if header in self.where:
                                where_header = header
                                break
                        if self.where_ids:
                            self.create_temp_id = f"CREATE TEMP TABLE TempIDs ({where_header} INTEGER PRIMARY KEY)"
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
                                hierarchy_order_by = f'ORDER BY {self.order_col}'
                        break
            if hierarchy_where == '' and hierarchy_where_join == '':
                logger_setup.get_logger().info(f'Where clause {self.where} does not apply to Samples, Aliquots, Spots or UPbAnalyses.')
                logger_setup.get_logger().info(f'Consider simplifying the query or using the filtering query building.')
        elif self.order_col != '' and self.limit != '':
            if self.order_col in headers:
                # Everything applies to the same table, so put them all in the hierarchy query
                where_header = headers[0]
                self.create_temp_paged = f"""CREATE TEMP TABLE TempPaged AS
                                                SELECT {headers[0]} FROM {self.table}
                                                ORDER BY {self.order_col} {self.limit}
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
            self.create_temp_paged = f"""CREATE TEMP TABLE TempPaged AS
                                        SELECT {headers[0]} FROM {self.table}
                                        {self.limit}"""
            hierarchy_limit = ''
            hierarchy_where_join = f"INNER JOIN TempPaged tp ON"
            self.query_limit = ''
        group_lspuag = ''
        group_lsa = ''
        lsa_from_table = 'Aliquots'
        lspuag_from_table = 'Spots'
        lsa_select = ''
        lsa_joins = ''
        lspuag_select = ''
        lspuag_joins = ''
        if where_table in ['Samples', 'Aliquots', 'Spots', 'UPbAnalyses', 'Grains']:
            if where_table in ['Samples', 'Aliquots']:
                if headers[0] in ['SampleID', 'AliquotID']:
                    group_lsa = f'GROUP BY {self.table}.{headers[0]}'
                    group_lspuag = f'GROUP BY lsa.{headers[0]}'
                elif headers[0] in ['SpotID', 'UPbAnalysisID', 'GrainID']:
                    group_lsa = ''
                    group_lspuag = f'GROUP BY {self.table}.{headers[0]}'
            else:
                if headers[0] in ['SpotID', 'UPbAnalysisID', 'GrainID']:
                    group_lspuag = f'GROUP BY {self.table}.{headers[0]}'
                    group_lsa = f'GROUP BY lspuag.{headers[0]}'
                elif headers[0] in ['SampleID', 'AliquotID']:
                    group_lspuag = ''
                    group_lsa = f'GROUP BY {self.table}.{headers[0]}'
            if self.table == 'Samples':
                lsa_from_table = 'Samples'
                lsa_select = f''',
                        {SQLUtils.qigsn},
                        {SQLUtils.qsample_description},
                        {SQLUtils.qsample_gps_id},
                        Samples.DefaultSampleAgeID,
                        {SQLUtils.qcolumn_name},
                        {SQLUtils.qaliquots},
                        {SQLUtils.qsample_created},
                        {SQLUtils.qsample_modified}'''
                lsa_joins = f'''INNER JOIN Aliquots ON Samples.SampleID = Aliquots.SampleID
                       {SQLUtils.column_join}
                       {SQLUtils.gps_sample_join}
                       {SQLUtils.gps_sample_left_joins}
                       {SQLUtils.gps_column_join}
                       {SQLUtils.gps_column_left_joins}'''
                if self.edit_view:
                    lsa_select += f''',\n{SQLUtils.qgps_display},
                                            {SQLUtils.qsample_elev_display},
                                            {SQLUtils.qsample_elev_unit},
                                            {SQLUtils.qsample_column_data_display},
                                            {SQLUtils.qsample_column_data_unit}'''
                    lsa_joins += f'''\n{SQLUtils.column_unit_join}'''
                else:
                    lsa_select += f''',\n{SQLUtils.qgps},
                                            {SQLUtils.qsample_elev},
                                            {SQLUtils.qsample_column_data}'''
                    lsa_joins += f'''\n{SQLUtils.column_units_join}'''
                lspuag_from_table = 'Spots'
                lspuag_select = f''',
                        {SQLUtils.qgrain_count},
                        {SQLUtils.qgrain_compositions},
                        {SQLUtils.qspot_count},
                        {SQLUtils.qspot_compositions},
                        {SQLUtils.qupb_lab_facilities},
                        {SQLUtils.qupb_analysis_methods},
                        {SQLUtils.qupb_ratio_error_formats},
                        {SQLUtils.qupb_age_units},
                        {SQLUtils.qupb_age_error_formats},
                        {SQLUtils.qconcordance_formats},
                        {SQLUtils.qspot_sizes},
                        {SQLUtils.qspot_size},
                        {SQLUtils.qspot_size_unit},
                        {SQLUtils.qupb_references},
                        {SQLUtils.qupb_age_interpretations}'''
                lspuag_joins = f'''INNER JOIN LimitedSamplesAliquots lsa ON Spots.AliquotID = lsa.AliquotID
                    INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
                    {SQLUtils.spot_grain_join}
                    {SQLUtils.grain_composition_join}
                    {SQLUtils.spot_composition_join}
                       {SQLUtils.upb_reference_join}
                       {SQLUtils.upb_labs_join}
                       {SQLUtils.upb_instruments_join}
                       {SQLUtils.upb_method_join}
                       {SQLUtils.upb_ratio_error_format_join}
                       {SQLUtils.upb_age_error_format_join}
                       {SQLUtils.upb_age_unit_join}
                       {SQLUtils.upb_concordance_format_join}
                       {SQLUtils.upb_age_interpretation_join}
                       {SQLUtils.upb_spot_size_unit_join}'''
            elif self.table == 'Aliquots':
                lsa_from_table = 'Aliquots'
                lsa_select = f''',
                        {SQLUtils.qaliquot_parent_id},
                        {SQLUtils.qaliquot_parent_row},
                        {SQLUtils.qaliquot_sample},
                        {SQLUtils.qaliquot_created},
                        {SQLUtils.qaliquot_modified}'''
                lsa_joins = 'INNER JOIN Samples ON Samples.SampleID = Aliquots.SampleID'
                lspuag_from_table = 'Spots'
                if not self.edit_view:
                    lspuag_select = f''',
                            {SQLUtils.qgrain_count},
                            {SQLUtils.qgrain_compositions},
                            {SQLUtils.qspot_count},
                            {SQLUtils.qspot_compositions},
                            {SQLUtils.qupb_lab_facilities},
                            {SQLUtils.qupb_analysis_methods},
                            {SQLUtils.qupb_ratio_error_formats},
                            {SQLUtils.qupb_age_units},
                            {SQLUtils.qupb_age_error_formats},
                            {SQLUtils.qconcordance_formats},
                            {SQLUtils.qspot_sizes},
                            {SQLUtils.qspot_size},
                            {SQLUtils.qspot_size_unit},
                            {SQLUtils.qupb_references},
                            {SQLUtils.qupb_age_interpretations}'''
                    lspuag_joins = f'''INNER JOIN LimitedSamplesAliquots lsa ON Spots.AliquotID = lsa.AliquotID
                    INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
                    {SQLUtils.spot_grain_join}
                    {SQLUtils.grain_composition_join}
                        {SQLUtils.spot_composition_join}
                           {SQLUtils.upb_reference_join}
                           {SQLUtils.upb_labs_join}
                           {SQLUtils.upb_instruments_join}
                           {SQLUtils.upb_method_join}
                           {SQLUtils.upb_ratio_error_format_join}
                           {SQLUtils.upb_age_error_format_join}
                           {SQLUtils.upb_age_unit_join}
                           {SQLUtils.upb_concordance_format_join}
                           {SQLUtils.upb_age_interpretation_join}
                           {SQLUtils.upb_spot_size_unit_join}'''
            elif self.table == 'Spots':
                lspuag_from_table = 'Spots'
                lsa_from_table = 'Aliquots'
                lsa_joins = 'INNER JOIN Samples ON Samples.SampleID = Aliquots.SampleID'
                if self.edit_view:
                    lspuag_select = f''',
                        {SQLUtils.qspot_name},
                        {SQLUtils.qupb_analyses},
                        {SQLUtils.qgrain_name},
                        {SQLUtils.qspot_composition},
                        {SQLUtils.qgrain_composition},
                        {SQLUtils.qspot_created},
                        {SQLUtils.qspot_modified}'''
                    lspuag_joins = f'''INNER JOIN LimitedSamplesAliquots lsa ON Spots.AliquotID = lsa.AliquotID
                    INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
                    {SQLUtils.spot_grain_join}
                    {SQLUtils.grain_composition_join}
                    {SQLUtils.spot_composition_join}'''
                else:
                    lspuag_select = f''',
                            {SQLUtils.qspot_name},
                            {SQLUtils.qupb_analyses},
                            {SQLUtils.qgrain_name},
                            {SQLUtils.qspot_composition},
                            {SQLUtils.qgrain_composition},
                            {SQLUtils.qupb_lab_facilities},
                            {SQLUtils.qupb_instruments},
                            {SQLUtils.qupb_analysis_methods},
                            {SQLUtils.qupb_ratio_error_formats},
                            {SQLUtils.qupb_age_units},
                            {SQLUtils.qupb_age_error_formats},
                            {SQLUtils.qconcordance_formats},
                            {SQLUtils.qspot_sizes},
                            {SQLUtils.qupb_age_interpretations},
                            {SQLUtils.qupb_references},
                            {SQLUtils.qspot_created},
                            {SQLUtils.qspot_modified}'''
                    lspuag_joins = f'''{SQLUtils.grain_composition_join}
                    {SQLUtils.spot_composition_join}
                       {SQLUtils.upb_reference_join}
                       {SQLUtils.upb_labs_join}
                       {SQLUtils.upb_instruments_join}
                       {SQLUtils.upb_method_join}
                       {SQLUtils.upb_ratio_error_format_join}
                       {SQLUtils.upb_age_error_format_join}
                       {SQLUtils.upb_age_unit_join}
                       {SQLUtils.upb_concordance_format_join}
                       {SQLUtils.upb_age_interpretation_join}
                       {SQLUtils.upb_spot_size_unit_join}'''
            elif self.table == 'UPbAnalyses':
                lspuag_from_table = 'UPbAnalyses'
                lsa_from_table = 'Aliquots'
                lsa_joins = 'INNER JOIN Samples ON Samples.SampleID = Aliquots.SampleID'
                upb_query_columns = upb_columns(self.edit_view)
                query_columns = [SQLUtils.qupb_analysis_name,
                                 SQLUtils.qspot_name,
                                 SQLUtils.qgrain_name,
                                 SQLUtils.qupb_references,
                                 SQLUtils.qupb_lab_facilities,
                                 SQLUtils.qupb_instruments,
                                 SQLUtils.qupb_analysis_methods,
                                 SQLUtils.qupb_ratio_error_formats,
                                 SQLUtils.qupb_age_units,
                                 SQLUtils.qupb_age_error_formats,
                                 SQLUtils.qconcordance_formats,
                                 SQLUtils.qspot_size_unit,
                                 SQLUtils.qspot_composition,
                                 SQLUtils.qupb_age_interpretations,
                                 SQLUtils.qgrain_composition,
                                 SQLUtils.qupb_created,
                                 SQLUtils.qupb_modified]
                query_columns.extend(upb_query_columns)
                lspuag_select = f',\n'.join(query_columns)
                lspuag_select = f',\n{lspuag_select}'
                lspuag_joins = f'''INNER JOIN Spots ON UPbAnalyses.SpotID = Spots.SpotID
                    LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID
                    {SQLUtils.upb_reference_join}
                       {SQLUtils.upb_labs_join}
                       {SQLUtils.upb_instruments_join}
                       {SQLUtils.upb_method_join}
                       {SQLUtils.upb_ratio_error_format_join}
                       {SQLUtils.upb_age_error_format_join}
                       {SQLUtils.upb_age_unit_join}
                       {SQLUtils.upb_concordance_format_join}
                       {SQLUtils.upb_age_interpretation_join}
                       {SQLUtils.upb_spot_size_unit_join}
                       {SQLUtils.spot_composition_join}
                       {SQLUtils.grain_composition_join}'''
            elif self.table == 'Grains':
                lspuag_from_table = 'Grains'
                lsa_from_table = 'Aliquots'
                lsa_joins = 'INNER JOIN Samples ON Samples.SampleID = Aliquots.SampleID'
                lspuag_select = f''',
                        {SQLUtils.qgrain_name},
                        {SQLUtils.qgrain_description},
                        {SQLUtils.qspot_name},
                        {SQLUtils.qgrain_composition},
                        {SQLUtils.qspot_compositions},
                        {SQLUtils.qupb_lab_facilities},
                        {SQLUtils.qupb_instruments},
                        {SQLUtils.qupb_analysis_methods},
                        {SQLUtils.qupb_ratio_error_formats},
                        {SQLUtils.qupb_age_units},
                        {SQLUtils.qupb_age_error_formats},
                        {SQLUtils.qconcordance_formats},
                        {SQLUtils.qspot_sizes},
                        {SQLUtils.qupb_age_interpretations},
                        {SQLUtils.qupb_references},
                        {SQLUtils.qgrain_created},
                        {SQLUtils.qgrain_modified}'''
                lspuag_joins = f'''INNER JOIN Spots ON Grains.GrainID = Spots.GrainID
                    INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID 
                    {SQLUtils.grain_composition_join}
                    {SQLUtils.spot_composition_join}
                       {SQLUtils.upb_reference_join}
                       {SQLUtils.upb_labs_join}
                       {SQLUtils.upb_instruments_join}
                       {SQLUtils.upb_method_join}
                       {SQLUtils.upb_ratio_error_format_join}
                       {SQLUtils.upb_age_error_format_join}
                       {SQLUtils.upb_age_unit_join}
                       {SQLUtils.upb_concordance_format_join}
                       {SQLUtils.upb_age_interpretation_join}
                       {SQLUtils.upb_spot_size_unit_join}'''
        if where_table == 'Samples':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    hierarchy_where_join += f" Samples.SampleID = ti.SampleID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SampleID':
                        hierarchy_where_join += f" Samples.SampleID = tp.SampleID"
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedSamplesAliquots AS (
                    SELECT 
                        {SQLUtils.qsample_id},
                        {SQLUtils.qaliquot_id},
                        {SQLUtils.qsample_name},
                        {SQLUtils.qaliquot_name}
                        {lsa_select}
                    FROM {lsa_from_table}
                    {hierarchy_where_join}
                    {lsa_joins}
                    {hierarchy_where} 
                    {group_lsa}
                    {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedSpotsUPbAnalysesGrains AS (
                    SELECT 
                        {SQLUtils.qspot_id},
                        Spots.AliquotID,
                        {SQLUtils.qupb_id},
                        {SQLUtils.qupb_rejected},
                        {SQLUtils.qgrain_id}
                        {lspuag_select}
                    FROM {lspuag_from_table}
                    {lspuag_joins}
                   {group_lspuag}
                )
            '''
        elif where_table == 'Aliquots':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SampleID' in self.where:
                        hierarchy_where_join += f" Samples.SampleID = ti.SampleID"
                    elif 'AliquotID' in self.where:
                        hierarchy_where_join += f" Aliquots.AliquotID = ti.AliquotID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SampleID':
                        hierarchy_where_join += f" Samples.SampleID = tp.SampleID"
                    elif where_header == 'AliquotID':
                        hierarchy_where_join += f" Aliquots.AliquotID = tp.AliquotID"
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedSamplesAliquots AS (
                    SELECT 
                        {SQLUtils.qsample_id},
                        {SQLUtils.qaliquot_id},
                        {SQLUtils.qsample_name},
                        {SQLUtils.qaliquot_name}
                        {lsa_select}
                    FROM {lsa_from_table}
                    {hierarchy_where_join}
                    {lsa_joins}
                    {hierarchy_where} 
                    {group_lsa}
                    {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedSpotsUPbAnalysesGrains AS (
                    SELECT 
                        {SQLUtils.qspot_id},
                        Spots.AliquotID,
                        {SQLUtils.qupb_id},
                        {SQLUtils.qupb_rejected},
                        {SQLUtils.qgrain_id}
                        {lspuag_select}
                    FROM {lspuag_from_table}
                    INNER JOIN LimitedSamplesAliquots lsa ON Spots.AliquotID = lsa.AliquotID
                    INNER JOIN UPbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
                    {SQLUtils.spot_grain_join}
                    {lspuag_joins}
                   {group_lspuag}
                )
            '''
        elif where_table == 'Spots':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SpotID' in self.where:
                        hierarchy_where_join += f" Spots.SpotID = ti.SpotID"
                    elif 'AliquotID' in self.where:
                        hierarchy_where_join += f" Spots.AliquotID = ti.AliquotID"
                    elif 'GrainID' in self.where:
                        hierarchy_where_join += f" Grains.GrainID = ti.GrainID"
                    elif 'UPbAnalysisID' in self.where:
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = ti.UPbAnalysisID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SpotID':
                        hierarchy_where_join += f" Spots.SpotID = tp.SpotID"
                    elif where_header == 'AliquotID':
                        hierarchy_where_join += f" Spots.AliquotID = tp.AliquotID"
                    elif where_header == 'GrainID':
                        hierarchy_where_join += f" Grains.GrainID = tp.GrainID"
                    elif where_header == 'UPbAnalysisID':
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = tp.UPbAnalysisID"
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedSpotsUPbAnalysesGrains AS (
                    SELECT 
                        {SQLUtils.qspot_id},
                        Spots.AliquotID,
                        {SQLUtils.qupb_id},
                        {SQLUtils.qupb_rejected},
                        {SQLUtils.qgrain_id}
                        {lspuag_select}
                    FROM {lspuag_from_table}
                    {hierarchy_where_join}
                    INNER JOIN UpbAnalyses ON Spots.SpotID = UPbAnalyses.SpotID
                    LEFT JOIN Grains ON Spots.GrainID = Grains.GrainID
                    {lspuag_joins}
                    {hierarchy_where} 
                    {group_lspuag}
                    {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedSamplesAliquots AS (
                    SELECT 
                        {SQLUtils.qaliquot_id},
                        {SQLUtils.qsample_id},
                        {SQLUtils.qaliquot_name},
                        {SQLUtils.qsample_name}
                        {lsa_select}
                    FROM {lsa_from_table}
                    INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON Aliquots.AliquotID = lspuag.AliquotID
                    {lsa_joins}
                    {group_lsa}
                )
            '''
        elif where_table == 'UPbAnalyses':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SpotID' in self.where:
                        hierarchy_where_join += f" Spots.SpotID = ti.SpotID"
                    elif 'AliquotID' in self.where:
                        hierarchy_where_join += f" Spots.AliquotID = ti.AliquotID"
                    elif 'GrainID' in self.where:
                        hierarchy_where_join += f" Grains.GrainID = ti.GrainID"
                    elif 'UPbAnalysisID' in self.where:
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = ti.UPbAnalysisID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SpotID':
                        hierarchy_where_join += f" Spots.SpotID = tp.SpotID"
                    elif where_header == 'AliquotID':
                        hierarchy_where_join += f" Spots.AliquotID = tp.AliquotID"
                    elif where_header == 'GrainID':
                        hierarchy_where_join += f" Grains.GrainID = tp.GrainID"
                    elif where_header == 'UPbAnalysisID':
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = tp.UPbAnalysisID"
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedSpotsUPbAnalysesGrains AS (
                    SELECT 
                        {SQLUtils.qspot_id},
                        Spots.AliquotID,
                        {SQLUtils.qupb_id},
                        {SQLUtils.qupb_rejected},
                        {SQLUtils.qgrain_id}
                        {lspuag_select}
                    FROM {lspuag_from_table}
                    {hierarchy_where_join}
                    {lspuag_joins}
                    {hierarchy_where} 
                    {group_lspuag}
                    {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedSamplesAliquots AS (
                    SELECT 
                        {SQLUtils.qaliquot_id},
                        {SQLUtils.qsample_id},
                        {SQLUtils.qaliquot_name},
                        {SQLUtils.qsample_name}
                        {lsa_select}
                    FROM Aliquots
                    INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON Aliquots.AliquotID = lspuag.AliquotID
                    {lsa_joins}
                    {group_lsa}
                )
            '''
        elif where_table == 'Grains':
            if hierarchy_where_join != '':
                if 'TempIDs' in hierarchy_where_join:
                    if 'SpotID' in self.where:
                        hierarchy_where_join += f" Spots.SpotID = ti.SpotID"
                    elif 'AliquotID' in self.where:
                        hierarchy_where_join += f" Spots.AliquotID = ti.AliquotID"
                    elif 'GrainID' in self.where:
                        hierarchy_where_join += f" Grains.GrainID = ti.GrainID"
                    elif 'UPbAnalysisID' in self.where:
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = ti.UPbAnalysisID"
                elif 'TempPaged' in hierarchy_where_join:
                    if where_header == 'SpotID':
                        hierarchy_where_join += f" Spots.SpotID = tp.SpotID"
                    elif where_header == 'AliquotID':
                        hierarchy_where_join += f" Spots.AliquotID = tp.AliquotID"
                    elif where_header == 'GrainID':
                        hierarchy_where_join += f" Grains.GrainID = tp.GrainID"
                    elif where_header == 'UPbAnalysisID':
                        hierarchy_where_join += f" UPbAnalyses.UPbAnalysisID = tp.UPbAnalysisID"
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedSpotsUPbAnalysesGrains AS (
                    SELECT 
                        {SQLUtils.qspot_id},
                        Spots.AliquotID,
                        {SQLUtils.qupb_id},
                        {SQLUtils.qupb_rejected},
                        {SQLUtils.qgrain_id}
                        {lspuag_select}
                    FROM {lspuag_from_table}
                    {hierarchy_where_join}
                    {lspuag_joins}
                    {hierarchy_where} 
                    {group_lspuag}
                    {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedSamplesAliquots AS (
                    SELECT 
                        {SQLUtils.qaliquot_id},
                        {SQLUtils.qsample_id},
                        {SQLUtils.qaliquot_name},
                        {SQLUtils.qsample_name}
                        {lsa_select}
                    FROM Aliquots
                    INNER JOIN LimitedSpotsUPbAnalysesGrains lspuag ON Aliquots.AliquotID = lspuag.AliquotID
                    {lsa_joins}
                    {group_lsa}
                )
            '''
        else:
            # No direct limits on the main hierarchy tables
            self.limited_hierarchy = ''

    def get_group_oder_clauses(self):
        from Functions.Widget_classes import get_headers

        table_abbreviation_dict = SQLUtils.limited_table_abbreviations.copy()
        if self.table not in table_abbreviation_dict:
            self.group_by = f'GROUP BY {self.group_col}'
            self.order_by = f'ORDER BY {self.order_col}'
            return
        table_abbreviation = table_abbreviation_dict[self.table]
        table_abbreviation_dict.pop(self.table)

        self.group_by = ''
        if self.group_col != '':
            if self.group_col in get_headers(self.table):
                self.group_by = f'GROUP BY {table_abbreviation}.{self.group_col}'
            else:
                for key in table_abbreviation_dict.keys():
                    if self.group_col in get_headers(key):
                        self.group_by = f'GROUP BY {table_abbreviation_dict[key]}.{self.group_col}'
                        break

        self.order_by = ''
        if self.order_col != '':
            if self.order_col in get_headers(self.table):
                self.order_by = f'ORDER BY {table_abbreviation}.{self.order_col}'
            else:
                for key in table_abbreviation_dict.keys():
                    if self.order_col in get_headers(key):
                        self.order_by = f'ORDER BY {table_abbreviation_dict[key]}.{self.order_col}'
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