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
        self.group_col = ''
        self.order_col = ''
        self.limited_hierarchy = ''
        self.group_by = ''
        self.order_by = ''
        self.query_where = ''
        self.query_limit = ''
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
        self.group_col: str = 'SampleID'
        self.order_col: str = 'SampleName'
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
                        SQLUtils.qupb_references,
                        SQLUtils.qsample_created,
                        SQLUtils.qsample_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if column.split(' ')[0] != column:
                        # There is a condition such as DISTINCT or COUNT
                        sql_col = column.replace(col.split(' AS ')[1], col)
                        query_columns.append(sql_col)
                    else:
                        query_columns.append(col)
                    break
        query_columns = ',\n '.join(query_columns)

        count_sample_subquery = SQLUtils.qupb_count_sample_subquery
        count_sample_subquery = count_sample_subquery.replace(' Samples ',' LimitedSamples ls ')
        count_sample_subquery = count_sample_subquery.replace(' Aliquots ',' LimitedAliquots la ')
        count_sample_subquery = count_sample_subquery.replace(' Spots ',' LimitedSpots lsp ')
        count_sample_subquery = count_sample_subquery.replace(' UPbAnalyses ',' LimitedUPbAnalyses lu ')

        sample_query = f'''
                {self.limited_hierarchy},
                {SQLUtils.limited_sample_tags},
                {SQLUtils.limited_aliquot_tags},
                {SQLUtils.limited_spot_tags},
                {SQLUtils.limited_upb_tags},
                {count_sample_subquery}
                SELECT
                        {query_columns}
                       FROM LimitedSamples ls
                       {SQLUtils.limited_sample_hierarchy_join}
                       {SQLUtils.limited_sample_tags_join}
                       {SQLUtils.limited_aliquot_tags_join}
                       {SQLUtils.limited_spot_tags_join}
                       {SQLUtils.limited_upb_tags_join}
                       {SQLUtils.column_join}
                       {SQLUtils.column_unit_join}
                       {SQLUtils.sample_age_join}
                       {SQLUtils.sample_age_left_joins}
                       {SQLUtils.gps_sample_join}
                       {SQLUtils.gps_sample_left_joins}
                       {SQLUtils.gps_column_join}
                       {SQLUtils.gps_column_left_joins}
                       {SQLUtils.spot_composition_join}
                       {SQLUtils.upb_distinct_join_sample}
                       {SQLUtils.upb_reference_join}
                       {SQLUtils.upb_labs_join}
                       {SQLUtils.upb_instruments_join}
                       {SQLUtils.upb_method_join}
                       {SQLUtils.upb_ratio_error_format_join}
                       {SQLUtils.upb_age_error_format_join}
                       {SQLUtils.upb_age_unit_join}
                       {SQLUtils.upb_concordance_format_join}
                       {SQLUtils.upb_spot_size_unit_join}
                        {self.query_where}
                        {self.group_by}
                        {self.order_by}
                        {self.query_limit}
                       '''

        for key, value in SQLUtils.limited_table_abbreviations.items():
            sample_query = sample_query.replace(f' {key}.', f' {value}.')
            sample_query = sample_query.replace(f'({key}.', f'({value}.')
        sample_query = sample_query.strip()

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
                        SQLUtils.qupb_references,
                        SQLUtils.qsample_created,
                        SQLUtils.qsample_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        count_sample_subquery = SQLUtils.qupb_count_sample_subquery
        count_sample_subquery = count_sample_subquery.replace(' Samples ', ' LimitedSamples ls ')
        count_sample_subquery = count_sample_subquery.replace(' Aliquots ', ' LimitedAliquots la ')
        count_sample_subquery = count_sample_subquery.replace(' Spots ', ' LimitedSpots lsp ')
        count_sample_subquery = count_sample_subquery.replace(' UPbAnalyses ', ' LimitedUPbAnalyses lu ')

        sample_query = f'''
                {self.limited_hierarchy},
                {SQLUtils.limited_sample_tags},
                {SQLUtils.limited_aliquot_tags},
                {SQLUtils.limited_spot_tags},
                {SQLUtils.limited_upb_tags},
                {count_sample_subquery}
                SELECT
                        {query_columns}
                    FROM LimitedSamples ls
                    {SQLUtils.limited_sample_hierarchy_join}
                    {SQLUtils.limited_sample_tags_join}
                    {SQLUtils.limited_aliquot_tags_join}
                    {SQLUtils.limited_spot_tags_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.column_join}
                    {SQLUtils.column_unit_join}
                    {SQLUtils.sample_age_join}
                    {SQLUtils.sample_age_left_joins}
                    {SQLUtils.gps_sample_join}
                    {SQLUtils.gps_sample_left_joins}
                    {SQLUtils.gps_column_join}
                    {SQLUtils.gps_column_left_joins}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.upb_distinct_join_sample}
                    {SQLUtils.upb_reference_join}
                    {SQLUtils.upb_labs_join}
                    {SQLUtils.upb_instruments_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_ratio_error_format_join}
                    {SQLUtils.upb_age_error_format_join}
                    {SQLUtils.upb_age_unit_join}
                    {SQLUtils.upb_concordance_format_join}
                    {SQLUtils.upb_spot_size_unit_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        for key, value in SQLUtils.limited_table_abbreviations.items():
            sample_query = sample_query.replace(f' {key}.', f' {value}.')
            sample_query = sample_query.replace(f'({key}.', f'({value}.')
        sample_query = sample_query.strip()

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
                        SQLUtils.qupb_references,
                        SQLUtils.qaliquot_created,
                        SQLUtils.qaliquot_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        count_aliquot_subquery = SQLUtils.qupb_count_aliquot_subquery
        count_aliquot_subquery = count_aliquot_subquery.replace(' Aliquots ', ' LimitedAliquots la ')
        count_aliquot_subquery = count_aliquot_subquery.replace(' Spots ', ' LimitedSpots lsp ')
        count_aliquot_subquery = count_aliquot_subquery.replace(' UPbAnalyses ', ' LimitedUPbAnalyses lu ')

        aliquot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_aliquot_tags},
                    {count_aliquot_subquery},
                    {SQLUtils.limited_spot_tags},
                    {SQLUtils.limited_upb_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedAliquots la
                    {SQLUtils.limited_aliquot_hierarchy_join}
                    {SQLUtils.limited_aliquot_tags_join}
                    {SQLUtils.limited_spot_tags_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.upb_distinct_join_aliquot}
                    {SQLUtils.upb_reference_join}
                    {SQLUtils.upb_labs_join}
                    {SQLUtils.upb_instruments_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_ratio_error_format_join}
                    {SQLUtils.upb_age_error_format_join}
                    {SQLUtils.upb_age_unit_join}
                    {SQLUtils.upb_concordance_format_join}
                    {SQLUtils.upb_spot_size_unit_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    '''

        for key, value in SQLUtils.limited_table_abbreviations.items():
            aliquot_query = aliquot_query.replace(f' {key}.', f' {value}.')
            aliquot_query = aliquot_query.replace(f'({key}.', f'({value}.')
        aliquot_query = aliquot_query.strip()

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

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        aliquot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_aliquot_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedAliquots la
                    {SQLUtils.limited_aliquot_hierarchy_join}
                    {SQLUtils.limited_aliquot_tags_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    '''

        for key, value in SQLUtils.limited_table_abbreviations.items():
            aliquot_query = aliquot_query.replace(f' {key}.', f' {value}.')
            aliquot_query = aliquot_query.replace(f'({key}.', f'({value}.')
        aliquot_query = aliquot_query.strip()

        self.table_query = aliquot_query

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
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_name,
                        SQLUtils.qspot_composition,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qspot_created,
                        SQLUtils.qspot_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        spot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_spot_tags},
                    {SQLUtils.limited_upb_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedSpots lsp
                    {SQLUtils.limited_spot_hierarchy_join}
                    {SQLUtils.limited_spot_tags_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.spot_composition_join}
                    {SQLUtils.upb_reference_join}
                    {SQLUtils.upb_labs_join}
                    {SQLUtils.upb_instruments_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_ratio_error_format_join}
                    {SQLUtils.upb_age_error_format_join}
                    {SQLUtils.upb_age_unit_join}
                    {SQLUtils.upb_concordance_format_join}
                    {SQLUtils.upb_spot_size_unit_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        for key, value in SQLUtils.limited_table_abbreviations.items():
            spot_query = spot_query.replace(f' {key}.', f' {value}.')
            spot_query = spot_query.replace(f'({key}.', f'({value}.')
        spot_query = spot_query.strip()

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
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_name,
                        SQLUtils.qspot_composition,
                        SQLUtils.qspot_contexts,
                        SQLUtils.qspot_created,
                        SQLUtils.qspot_modified]

        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        spot_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_spot_tags}
                    SELECT
                        {query_columns}
                    FROM LimitedSpots lsp
                    {SQLUtils.limited_spot_hierarchy_join}
                    {SQLUtils.limited_spot_tags_join}
                    {SQLUtils.spot_composition_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        for key, value in SQLUtils.limited_table_abbreviations.items():
            spot_query = spot_query.replace(f' {key}.', f' {value}.')
            spot_query = spot_query.replace(f'({key}.', f'({value}.')
        spot_query = spot_query.strip()

        self.table_query = spot_query


    def create_upb_view_query(self):
        self.show_columns: list = settings.value('upb_analysis_view_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'UPbAnalysisID'
        self.order_col: str = 'SpotName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        from Functions.Widget_classes import get_headers

        headers = get_headers(self.table)
        columns = []
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
        upb_query_columns = columns

        query_columns1 = [SQLUtils.qupb_id,
                        SQLUtils.qspot_id,
                        SQLUtils.qaliquot_id,
                        SQLUtils.qsample_id,
                        SQLUtils.qspot_name,
                        SQLUtils.qaliquot_name,
                        SQLUtils.qsample_name,
                        SQLUtils.qupb_references,
                        SQLUtils.qupb_lab_facilities,
                        SQLUtils.qupb_instruments,
                        SQLUtils.qupb_analysis_methods,]

        query_columns2 = [SQLUtils.qupb_rejected,
                        SQLUtils.qupb_rejection_reasons,
                        SQLUtils.qupb_contexts,
                        SQLUtils.qupb_created,
                        SQLUtils.qupb_modified]

        query_column_list = query_columns1 + upb_query_columns + query_columns2
        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        upb_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_upb_tags}
                    SELECT 
                        {query_columns}
                    FROM LimitedUPbAnalyses lu
                    {SQLUtils.limited_upb_hierarchy_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.upb_reference_join}
                    {SQLUtils.upb_labs_join}
                    {SQLUtils.upb_instruments_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_ratio_error_format_join}
                    {SQLUtils.upb_age_error_format_join}
                    {SQLUtils.upb_age_unit_join}
                    {SQLUtils.upb_concordance_format_join}
                    {SQLUtils.upb_spot_size_unit_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''

        for key, value in SQLUtils.limited_table_abbreviations.items():
            upb_query = upb_query.replace(f' {key}.', f' {value}.')
            upb_query = upb_query.replace(f'({key}.', f'({value}.')
        upb_query = upb_query.strip()

        self.table_query = upb_query

    def create_upb_edit_view_query(self):
        self.show_columns: list = settings.value('upb_analysis_edit_columns')
        self.limit: str = ''
        self.where: str = ''
        self.group_col: str = 'UPbAnalysisID'
        self.order_col: str = 'SpotName'
        for key, value in self.kwargs.items():
            setattr(self, key, value)

        self.get_group_oder_clauses()
        self.limited_hierarchy_query()

        from Functions.Widget_classes import get_headers

        headers = get_headers(self.table)
        columns = []
        for header in headers:
            if f'lu."{header}" AS "{header}"' in columns:
                continue
            elif 'ID' in header or 'Rejected' in header or 'Created' in header or 'Modified' in header:
                pass
            elif 'Calculated' in header:
                pass
            else:
                if f'lu."{header}" AS "{header}"' not in columns:
                    columns.append(f'lu."{header}" AS "{header}"')
                if f'{header}Error' in headers and f'lu."{header}Error" AS "{header}Error"' not in columns:
                    columns.append(f'lu."{header}Error" AS "{header}Error"')
        upb_query_columns = columns

        query_columns1 = [SQLUtils.qupb_id,
                        SQLUtils.qspot_id,
                        SQLUtils.qaliquot_id,
                        SQLUtils.qsample_id,
                        SQLUtils.qspot_name,
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
                        SQLUtils.qupb_created,
                        SQLUtils.qupb_modified]
        query_column_list = query_columns1 + upb_query_columns + query_columns2
        query_columns = []
        for column in self.show_columns:
            for col in query_column_list:
                if col.split(' AS ')[1] in column:
                    if col not in query_columns:
                        query_columns.append(col)
                        break
        query_columns = ',\n '.join(query_columns)

        upb_query = f'''
                    {self.limited_hierarchy},
                    {SQLUtils.limited_upb_tags}
                    SELECT 
                        {query_columns}
                    FROM LimitedUPbAnalyses lu
                    {SQLUtils.limited_upb_hierarchy_join}
                    {SQLUtils.limited_upb_tags_join}
                    {SQLUtils.upb_reference_join}
                    {SQLUtils.upb_labs_join}
                    {SQLUtils.upb_instruments_join}
                    {SQLUtils.upb_method_join}
                    {SQLUtils.upb_ratio_error_format_join}
                    {SQLUtils.upb_age_error_format_join}
                    {SQLUtils.upb_age_unit_join}
                    {SQLUtils.upb_concordance_format_join}
                    {SQLUtils.upb_spot_size_unit_join}
                    {self.query_where}
                    {self.group_by}
                    {self.order_by}
                    {self.query_limit}
                    '''
        for key, value in SQLUtils.limited_table_abbreviations.items():
            upb_query = upb_query.replace(f' {key}.', f' {value}.')
            upb_query = upb_query.replace(f'({key}.', f'({value}.')
        upb_query = upb_query.strip()

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
        Construct the query to limit the Samples, Aliquots, Spots, and UPbAnalyses joined in the main query. Begin with
        the table that the where clause applies to. Any ordering or limit that does not also apply to this table get
        set for application in the main query.
        Updates the limited hierarchy query clause, the where clause to use in the main query, and the limit clause to
        use in the main query.
        """
        from Functions.Widget_classes import get_headers

        headers = get_headers(self.table)
        table_abbreviation_dict = SQLUtils.limited_table_abbreviations.copy()

        where_table = self.table
        hierarchy_where = ''
        hierarchy_order_by = ''
        hierarchy_limit = ''
        self.query_where = self.where
        self.query_limit = self.limit

        if self.table not in table_abbreviation_dict:
            return
        table_abbreviation_dict.pop(self.table)

        if self.where != '':
            # Check if any table headers are in the where clause
            if any(header in self.where for header in headers):
                hierarchy_where = self.where
                self.query_where = ''
                if self.order_col != '' and self.limit != '':
                    if self.order_col in headers:
                        # Everything applies to the same table, so put them all in the hierarchy query
                        hierarchy_order_by = f'ORDER BY {self.order_col}'
                        hierarchy_limit = self.limit
                        self.query_limit = ''
                    else:
                        # Ordering by a different table than the where clause, so apply the ordering and limit in the main query
                        hierarchy_order_by = ''
                        hierarchy_limit = ''
                        self.query_limit = self.limit
                        # order gets applied in the main query regardless
                elif self.limit != '':
                    # Everything not blank applies to the same table, so put them all in the hierarchy query
                    hierarchy_order_by = ''
                    hierarchy_limit = self.limit
                    self.query_limit = ''
            else:
                for key in table_abbreviation_dict.keys():
                    if any(header in self.where for header in get_headers(key)):
                        where_table = key
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
            if hierarchy_where == '':
                logger_setup.get_logger().info(f'Where clause {self.where} does not apply to Samples, Aliquots, Spots or UPbAnalyses.')
                logger_setup.get_logger().info(f'Consider simplifying the query or using the filtering query building.')
        elif self.order_col != '' and self.limit != '':
            if self.order_col in headers:
                # Everything applies to the same table, so put them all in the hierarchy query
                hierarchy_order_by = f'ORDER BY {self.order_col}'
                hierarchy_limit = self.limit
                self.query_limit = ''
            else:
                # Ordering by a different table than the where clause, so apply the ordering and limit in the main query
                hierarchy_order_by = ''
                hierarchy_limit = ''
                self.query_limit = self.limit
                # order gets applied in the main query regardless
        elif self.limit != '':
            # Only limit, so apply in the hierarchy
            hierarchy_limit = self.limit
            self.query_limit = ''
        if where_table == 'Samples':
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedSamples AS (
                    SELECT * FROM Samples {hierarchy_where} {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedAliquots AS (
                    SELECT * FROM Aliquots WHERE SampleID IN (SELECT SampleID FROM LimitedSamples)
                ),
                LimitedSpots AS (
                    SELECT * FROM Spots WHERE AliquotID IN (SELECT AliquotID FROM LimitedAliquots)
                ),
                LimitedUPbAnalyses AS (
                    SELECT * FROM UPbAnalyses WHERE SpotID IN (SELECT SpotID FROM LimitedSpots)
                )
            '''
        elif where_table == 'Aliquots':
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedAliquots AS (
                    SELECT * FROM Aliquots {hierarchy_where} {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedSpots AS (
                    SELECT * FROM Spots WHERE AliquotID IN (SELECT AliquotID FROM LimitedAliquots)
                ),
                LimitedUPbAnalyses AS (
                    SELECT * FROM UPbAnalyses WHERE SpotID IN (SELECT SpotID FROM LimitedSpots)
                ),
                LimitedSamples AS (
                    SELECT * FROM Samples WHERE SampleID IN (SELECT SampleID FROM LimitedAliquots)
                )
            '''
        elif where_table == 'Spots':
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedSpots AS (
                    SELECT * FROM Spots {hierarchy_where} {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedUPbAnalyses AS (
                    SELECT * FROM UPbAnalyses WHERE SpotID IN (SELECT SpotID FROM LimitedSpots)
                ),
                LimitedAliquots AS (
                    SELECT * FROM Aliquots WHERE AliquotID IN (SELECT AliquotID FROM LimitedSpots)
                ),
                LimitedSamples AS (
                    SELECT * FROM Samples WHERE SampleID IN (SELECT SampleID FROM LimitedAliquots)
                )
            '''
        elif where_table == 'UPbAnalyses':
            self.limited_hierarchy = f'''
                WITH RECURSIVE LimitedUPbAnalyses AS (
                    SELECT * FROM UPbAnalyses {hierarchy_where} {hierarchy_order_by} {hierarchy_limit}
                ),
                LimitedSpots AS (
                    SELECT * FROM Spots WHERE SpotID IN (SELECT SpotID FROM LimitedUPbAnalyses)
                ),
                LimitedAliquots AS (
                    SELECT * FROM Aliquots WHERE AliquotID IN (SELECT AliquotID FROM LimitedSpots)
                ),
                LimitedSamples AS (
                    SELECT * FROM Samples WHERE SampleID IN (SELECT SampleID FROM LimitedAliquots)
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
