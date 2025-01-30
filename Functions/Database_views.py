import sqlite3

from PyQt6 import QtSql as QtS
from PyQt6 import QtCore as QtC
from PyQt6 import QtWidgets as QtW
import Functions.SQLUtils as SQLUtils
from Functions.SQLUtils import gps_column_join
from Functions.Table_classes import set_table, get_headers
import time


def SampleViewQuery(ids_to_show=None):
    # Select columns
    if ids_to_show is not None:
        ids_to_show = tuple(ids_to_show)
        where_statement = f'''WHERE Samples.SampleID IN {ids_to_show}'''
    else:
        where_statement = ''

    sample_query = f'''
                SELECT
                        {SQLUtils.qsample_id},
                        {SQLUtils.qigsn},
                        {SQLUtils.qsample_name},
                        {SQLUtils.qsample_description},
                        {SQLUtils.qgps},
                        {SQLUtils.qsample_elev},
                        {SQLUtils.qsample_age},
                        {SQLUtils.qsample_age_constraint},
                        {SQLUtils.qsample_age_interpretation},
                        {SQLUtils.qsample_age_references},
                        {SQLUtils.qcolumn_name},
                        {SQLUtils.qcolumn_data},
                        {SQLUtils.qage_signature},
                        {SQLUtils.qregions},
                        {SQLUtils.qrock_types},
                        {SQLUtils.qsample_context},
                        {SQLUtils.qsampling_methods},
                        {SQLUtils.qsettings},
                        {SQLUtils.qunits},
                        {SQLUtils.qaliquots},
                        {SQLUtils.qaliquot_contexts},
                        {SQLUtils.qsample_created},
                        {SQLUtils.qsample_modified}
                    FROM Samples
                    {SQLUtils.age_signature_join}
                    {SQLUtils.column_join}
                    {SQLUtils.region_join}
                    {SQLUtils.rock_type_join}
                    {SQLUtils.sample_context_join}
                    {SQLUtils.sample_sampleage_join}
                    {SQLUtils.sampling_method_join}
                    {SQLUtils.setting_join}
                    {SQLUtils.unit_join}
                    {SQLUtils.sample_age_join}
                    {SQLUtils.sample_age_left_joins}
                    {SQLUtils.gps_sample_join}
                    {SQLUtils.gps_column_join}
                    {SQLUtils.sample_aliquot_join}
                    {SQLUtils.aliquot_context_join}
                    {SQLUtils.aliquot_spot_join}
                    {SQLUtils.spot_composition_join}
                    {where_statement}
                    GROUP BY Samples.SampleName
                    ORDER BY Samples.SampleID
                    '''

    # sample_query = f'''
    #         SELECT
    #                 {SQLUtils.qsample_id},
    #                 {SQLUtils.qigsn},
    #                 {SQLUtils.qsample_name},
    #                 {SQLUtils.qsample_description},
    #                 {SQLUtils.qgps},
    #                 {SQLUtils.qsample_elev},
    #                 {SQLUtils.qsample_age},
    #                 {SQLUtils.qsample_age_constraint},
    #                 {SQLUtils.qsample_age_interpretation},
    #                 {SQLUtils.qsample_age_references},
    #                 {SQLUtils.qcolumn_name},
    #                 {SQLUtils.qcolumn_data},
    #                 {SQLUtils.qage_signature},
    #                 {SQLUtils.qregions},
    #                 {SQLUtils.qrock_types},
    #                 {SQLUtils.qsample_context},
    #                 {SQLUtils.qsampling_methods},
    #                 {SQLUtils.qsettings},
    #                 {SQLUtils.qunits},
    #                 {SQLUtils.qaliquots},
    #                 {SQLUtils.qaliquot_contexts},
    #                 {SQLUtils.qspot_count},
    #                 {SQLUtils.qspot_compositions},
    #                 {SQLUtils.qspot_contexts},
    #                 {SQLUtils.qupb_count},
    #                 {SQLUtils.qupb_lab_facilities},
    #                 {SQLUtils.qupb_analysis_methods},
    #                 {SQLUtils.qupb_ratio_error_formats},
    #                 {SQLUtils.qupb_age_units},
    #                 {SQLUtils.qupb_age_error_formats},
    #                 {SQLUtils.qconcordance_formats},
    #                 {SQLUtils.qspot_sizes},
    #                 {SQLUtils.qupb_rejection_reasons},
    #                 {SQLUtils.qupb_references},
    #                 {SQLUtils.qsample_created},
    #                 {SQLUtils.qsample_modified}
    #             FROM Samples
    #             {SQLUtils.age_signature_join}
    #             {SQLUtils.column_join}
    #             {SQLUtils.region_join}
    #             {SQLUtils.rock_type_join}
    #             {SQLUtils.sample_context_join}
    #             {SQLUtils.sample_sampleage_join}
    #             {SQLUtils.sampling_method_join}
    #             {SQLUtils.setting_join}
    #             {SQLUtils.unit_join}
    #             {SQLUtils.sample_age_join}
    #             {SQLUtils.sample_age_left_joins}
    #             {SQLUtils.gps_sample_join}
    #             {SQLUtils.gps_column_join}
    #             {SQLUtils.sample_aliquot_join}
    #             {SQLUtils.aliquot_context_join}
    #             {SQLUtils.aliquot_spot_join}
    #             {SQLUtils.spot_composition_join}
    #             {SQLUtils.spot_context_join}
    #             {SQLUtils.spot_upb_analysis_join}
    #             {SQLUtils.upb_reference_join}
    #             {SQLUtils.upb_labs_join}
    #             {SQLUtils.upb_instruments_join}
    #             {SQLUtils.upb_method_join}
    #             {SQLUtils.upb_ratio_error_format_join}
    #             {SQLUtils.upb_age_error_format_join}
    #             {SQLUtils.upb_age_unit_join}
    #             {SQLUtils.upb_concordance_format_join}
    #             {SQLUtils.upb_spot_size_unit_join}
    #             {SQLUtils.upb_rejection_reason_join}
    #             {where_statement}
    #             GROUP BY Samples.SampleName
    #             ORDER BY Samples.SampleID
    #             '''

    # print(sample_query)
    return sample_query


def SampleIfNullQuery():
    sample_ifnull_query = f'''
    SELECT 
        {SQLUtils.qsample_name_ifnull},
        {SQLUtils.qigsn_ifnull},
        {SQLUtils.qsample_gps_id_ifnull},
        {SQLUtils.qcolumn_names_ifnull},
        {SQLUtils.qheight_depth_ifnull},
        {SQLUtils.qheight_depth_error_ifnull},
        {SQLUtils.qheight_depth_unit_ifnull},
        {SQLUtils.qsample_description_ifnull},
        {SQLUtils.qsample_lat_deg_ifnull},
        {SQLUtils.qsample_lat_min_ifnull},
        {SQLUtils.qsample_lat_sec_ifnull},
        {SQLUtils.qsample_lat_dir_ifnull},
        {SQLUtils.qsample_lon_deg_ifnull},
        {SQLUtils.qsample_lon_min_ifnull},
        {SQLUtils.qsample_lon_sec_ifnull},
        {SQLUtils.qsample_lon_dir_ifnull},
        {SQLUtils.qsample_utm_zone_ifnull},
        {SQLUtils.qsample_utm_northing_ifnull},
        {SQLUtils.qsample_utm_easting_ifnull},
        {SQLUtils.qsample_gps_format_ifnull},
        {SQLUtils.qsample_gps_elev_ifnull},
        {SQLUtils.qsample_gps_elev_error_ifnull},
        {SQLUtils.qsample_gps_elev_unit_ifnull},
        {SQLUtils.qsample_default_age_id_ifnull},
        {SQLUtils.qsample_direct_age_ifnull},
        {SQLUtils.qsample_direct_age_error_ifnull},
        {SQLUtils.qsample_direct_age_error_format_ifnull},
        {SQLUtils.qsample_oldest_direct_age_ifnull},
        {SQLUtils.qsample_youngest_direct_age_ifnull},
        {SQLUtils.qsample_direct_age_unit_ifnull},
        {SQLUtils.qsample_oldest_rel_age_ifnull},
        {SQLUtils.qsample_youngest_rel_age_ifnull},
        {SQLUtils.qsample_age_description_ifnull},
        {SQLUtils.qsample_age_constraint_ifnull},
        {SQLUtils.qsample_age_interpretation_ifnull},
        {SQLUtils.qsample_age_reference_ifnull}

    FROM Samples
    {SQLUtils.age_signature_join}
    {SQLUtils.column_join}
    {SQLUtils.column_unit_join}
    {SQLUtils.region_join}
    {SQLUtils.rock_type_join}
    {SQLUtils.sample_context_join}
    {SQLUtils.sample_sampleage_join}
    {SQLUtils.sampling_method_join}
    {SQLUtils.setting_join}
    {SQLUtils.unit_join}
    {SQLUtils.sample_age_join}
    {SQLUtils.sample_age_left_joins}
    {SQLUtils.gps_sample_join}
    {SQLUtils.gps_sample_left_joins}
    {SQLUtils.gps_column_join}
    {SQLUtils.gps_column_left_joins}
    {SQLUtils.sample_aliquot_join}
    {SQLUtils.aliquot_context_join}
    {SQLUtils.aliquot_spot_join}
    {SQLUtils.spot_composition_join}
    {SQLUtils.spot_context_join}
    {SQLUtils.spot_upb_analysis_join}
    {SQLUtils.upb_reference_join}
    {SQLUtils.upb_labs_join}
    {SQLUtils.upb_instruments_join}
    {SQLUtils.upb_method_join}
    {SQLUtils.upb_ratio_error_format_join}
    {SQLUtils.upb_age_error_format_join}
    {SQLUtils.upb_age_unit_join}
    {SQLUtils.upb_concordance_format_join}
    {SQLUtils.upb_spot_size_unit_join}
    {SQLUtils.upb_rejection_reason_join}
    '''
    # print(sample_ifnull_query)
    return sample_ifnull_query

def AliquotViewQuery():

    aliquot_query = f'''
                SELECT
                    {SQLUtils.qsample_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qaliquot_parent_id},
                    {SQLUtils.qaliquot_parent_row},
                    {SQLUtils.qaliquot},
                    {SQLUtils.qaliquot_sample},
                    {SQLUtils.qaliquot_contexts},
                    {SQLUtils.qspot_count},
                    {SQLUtils.qspot_compositions},
                    {SQLUtils.qspot_contexts},
                    {SQLUtils.qupb_count},
                    {SQLUtils.qupb_lab_facilities},
                    {SQLUtils.qupb_analysis_methods},
                    {SQLUtils.qupb_ratio_error_formats},
                    {SQLUtils.qupb_age_units},
                    {SQLUtils.qupb_age_error_formats},
                    {SQLUtils.qconcordance_formats},
                    {SQLUtils.qspot_sizes},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_references},
                    {SQLUtils.qaliquot_created},
                    {SQLUtils.qaliquot_modified}
                FROM Aliquots
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.aliquot_context_join}
                {SQLUtils.aliquot_spot_join}
                {SQLUtils.spot_composition_join}
                {SQLUtils.spot_context_join}
                {SQLUtils.spot_upb_analysis_join}
                {SQLUtils.upb_reference_join}
                {SQLUtils.upb_labs_join}
                {SQLUtils.upb_instruments_join}
                {SQLUtils.upb_method_join}
                {SQLUtils.upb_ratio_error_format_join}
                {SQLUtils.upb_age_error_format_join}
                {SQLUtils.upb_age_unit_join}
                {SQLUtils.upb_concordance_format_join}
                {SQLUtils.upb_spot_size_unit_join}
                {SQLUtils.upb_rejection_reason_join}
                GROUP BY AliquotName
                '''

    return aliquot_query

def AliquotEditViewQuery():

    aliquot_query = f'''
                SELECT
                    {SQLUtils.qsample_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qaliquot_parent_id},
                    {SQLUtils.qaliquot_parent_row},
                    {SQLUtils.qaliquot},
                    {SQLUtils.qaliquot_sample},
                    {SQLUtils.qaliquot_contexts},
                    {SQLUtils.qaliquot_created},
                    {SQLUtils.qaliquot_modified}
                FROM Aliquots
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.aliquot_context_join}
                GROUP BY AliquotName
                '''

    return aliquot_query

def SpotViewQuery():

    spot_query = f'''
                SELECT
                    {SQLUtils.qsample_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qspot_id},
                    {SQLUtils.qspots},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qaliquot},
                    {SQLUtils.qspot_compositions},
                    {SQLUtils.qspot_contexts},
                    {SQLUtils.qupb_count},
                    {SQLUtils.qupb_lab_facilities},
                    {SQLUtils.qupb_analysis_methods},
                    {SQLUtils.qupb_ratio_error_formats},
                    {SQLUtils.qupb_age_units},
                    {SQLUtils.qupb_age_error_formats},
                    {SQLUtils.qconcordance_formats},
                    {SQLUtils.qspot_sizes},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_references},
                    {SQLUtils.qspot_created},
                    {SQLUtils.qspot_modified}
                FROM Spots
                {SQLUtils.spot_aliquot_join}
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.spot_composition_join}
                {SQLUtils.spot_context_join}
                {SQLUtils.spot_upb_analysis_join}
                {SQLUtils.upb_reference_join}
                {SQLUtils.upb_labs_join}
                {SQLUtils.upb_instruments_join}
                {SQLUtils.upb_method_join}
                {SQLUtils.upb_ratio_error_format_join}
                {SQLUtils.upb_age_error_format_join}
                {SQLUtils.upb_age_unit_join}
                {SQLUtils.upb_concordance_format_join}
                {SQLUtils.upb_spot_size_unit_join}
                {SQLUtils.upb_rejection_reason_join}
                GROUP BY SpotName
                '''

    return spot_query

def SpotEditViewQuery():

    spot_query = f'''
                SELECT
                    {SQLUtils.qsample_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qspot_id},
                    {SQLUtils.qspots},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qaliquot},
                    {SQLUtils.qspot_compositions},
                    {SQLUtils.qspot_contexts},
                    {SQLUtils.qspot_created},
                    {SQLUtils.qspot_modified}
                FROM Spots
                {SQLUtils.spot_aliquot_join}
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.spot_composition_join}
                {SQLUtils.spot_context_join}
                GROUP BY SpotName
                '''

    return spot_query

def UPbViewQuery():
    headers = get_headers('UPbAnalyses')
    columns = []
    for header in headers:
        if f'UPbAnalyses."{header}"' in columns:
            continue
        if 'Calculated' in header:
            columns.append(f'UPbAnalyses."{header}"')
            if f'{header}Error' in headers:
                columns.append(f'UPbAnalyses."{header}Error"')
        elif f'Calculated{header}' in headers:
            pass
        elif 'ID' in header or 'Rejected' in header or 'Created' in header or 'Modified' in header:
            pass
        else:
            columns.append(f'UPbAnalyses."{header}"')
    query_columns = ',\n'.join(columns)

    upb_query = f'''
                SELECT 
                    {SQLUtils.qsample_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qspot_id},
                    {SQLUtils.qupb_id},
                    {SQLUtils.qspot},
                    {SQLUtils.qaliquot},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qupb_references},
                    {SQLUtils.qupb_lab_facilities},
                    {SQLUtils.qupb_instruments},
                    {SQLUtils.qupb_analysis_methods},
                    {query_columns},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_created},
                    {SQLUtils.qupb_modified}
                FROM UPbAnalyses 
                {SQLUtils.upb_spot_join}
                {SQLUtils.spot_aliquot_join}
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.upb_reference_join}
                {SQLUtils.upb_labs_join}
                {SQLUtils.upb_instruments_join}
                {SQLUtils.upb_method_join}
                {SQLUtils.upb_ratio_error_format_join}
                {SQLUtils.upb_age_error_format_join}
                {SQLUtils.upb_age_unit_join}
                {SQLUtils.upb_concordance_format_join}
                {SQLUtils.upb_spot_size_unit_join}
                {SQLUtils.upb_rejection_reason_join}
                GROUP BY UPbAnalyses.UPbAnalysisID
                '''
    return upb_query

def UPbEditViewQuery():
    headers = get_headers('UPbAnalyses')
    columns = []
    for header in headers:
        if f'UPbAnalyses."{header}"' in columns:
            continue
        elif 'ID' in header or 'Rejected' in header or 'Created' in header or 'Modified' in header:
            pass
        elif 'Calculated' in header:
            pass
        else:
            columns.append(f'UPbAnalyses."{header}"')
            if f'{header}Error' in headers:
                columns.append(f'UPbAnalyses."{header}Error"')
    query_columns = ',\n'.join(columns)

    upb_query = f'''
                SELECT 
                    {SQLUtils.qsample_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qspot_id},
                    {SQLUtils.qupb_id},
                    {SQLUtils.qspot},
                    {SQLUtils.qaliquot},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qupb_references},
                    {SQLUtils.qupb_lab_facilities},
                    {SQLUtils.qupb_instruments},
                    {SQLUtils.qupb_analysis_methods},
                    {query_columns},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_created},
                    {SQLUtils.qupb_modified}
                FROM UPbAnalyses 
                {SQLUtils.upb_spot_join}
                {SQLUtils.spot_aliquot_join}
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.upb_reference_join}
                {SQLUtils.upb_labs_join}
                {SQLUtils.upb_instruments_join}
                {SQLUtils.upb_method_join}
                {SQLUtils.upb_ratio_error_format_join}
                {SQLUtils.upb_age_error_format_join}
                {SQLUtils.upb_age_unit_join}
                {SQLUtils.upb_concordance_format_join}
                {SQLUtils.upb_spot_size_unit_join}
                {SQLUtils.upb_rejection_reason_join}
                GROUP BY UPbAnalyses.UPbAnalysisID
                '''
    return upb_query

def ColumnViewQuery():
    # Select columns

    column_query = f'''
                SELECT
                    {SQLUtils.qcolumn_id},
                    {SQLUtils.qcolumn_name},
                    {SQLUtils.qcolumn_calc_total_height_depth},
                    {SQLUtils.qcolumn_gps},
                    {SQLUtils.qcolumn_description},
                    {SQLUtils.qcolumn_created},
                    {SQLUtils.qcolumn_modified}
                FROM Columns
                {gps_column_join}
                GROUP BY ColumnName
                '''
    return column_query

def ColumnEditViewQuery():
    # Select columns
    columns = 'ColumnName'

    column_query = f'''
                    SELECT
                        {SQLUtils.qcolumn_id},
                        {SQLUtils.qcolumn_name},
                        {SQLUtils.qcolumn_total_height_depth},
                        {SQLUtils.qcolumn_total_height_depth_unit},
                        {SQLUtils.qcolumn_gps_display},
                        {SQLUtils.qcolumn_description},
                        {SQLUtils.qcolumn_created},
                        {SQLUtils.qcolumn_modified}
                    FROM Columns
                    {SQLUtils.column_units_join}
                    {SQLUtils.gps_column_join}
                    GROUP BY ColumnName
                    '''
    return column_query

def ColumnIfNullQuery():
    column_ifnull_query = f'''
    SELECT 
        {SQLUtils.qcolumn_id},
        {SQLUtils.qcolumn_gps_id_ifnull},
        {SQLUtils.qcolumn_gps_converted_ifnull},
        {SQLUtils.qcolumn_lat_deg_ifnull},
        {SQLUtils.qcolumn_lat_min_ifnull},
        {SQLUtils.qcolumn_lat_sec_ifnull},
        {SQLUtils.qcolumn_lat_dir_ifnull},
        {SQLUtils.qcolumn_lon_deg_ifnull},
        {SQLUtils.qcolumn_lon_min_ifnull},
        {SQLUtils.qcolumn_lon_sec_ifnull},
        {SQLUtils.qcolumn_lon_dir_ifnull},
        {SQLUtils.qcolumn_utm_zone_ifnull},
        {SQLUtils.qcolumn_utm_northing_ifnull},
        {SQLUtils.qcolumn_utm_easting_ifnull},
        {SQLUtils.qcolumn_gps_format_id_ifnull},
        {SQLUtils.qcolumn_gps_format_ifnull},
        {SQLUtils.qcolumn_gps_elev_ifnull},
        {SQLUtils.qcolumn_gps_elev_error_ifnull},
        {SQLUtils.qcolumn_gps_elev_unit_ifnull}
    FROM Columns
    {SQLUtils.gps_column_join}
    {SQLUtils.gps_column_left_joins}
    '''
    return column_ifnull_query

def create_sample_view(conditions: str = None):
    base_query = SampleViewQuery()
    if conditions:
        sample_query = f'{base_query} {conditions}'
    else:
        sample_query = base_query
    query = QtS.QSqlQuery()
    sample_view = f'CREATE VIEW IF NOT EXISTS SampleView AS {sample_query}'
    # print(sample_view)
    create_view_begin = time.time()
    print("Creating SampleView")
    if not query.exec(sample_view):
        print('Sample view creation failed')
        return False
    create_view_end = time.time()
    print(f"Create SampleView time: {create_view_end - create_view_begin}")

def create_sample_ifnull_view():
    sample_query = SampleIfNullQuery()
    # print(sample_query)
    sample_view = f'CREATE VIEW IF NOT EXISTS SampleIfNullView AS {sample_query}'
    query = QtS.QSqlQuery()
    # print(sample_view)
    if not query.exec(sample_view):
        print('Sample ifnull view creation failed')
        return False

def create_aliquot_view():
    aliquot_query = AliquotViewQuery()
    # print(aliquot_query)
    aliquot_view = f'CREATE VIEW IF NOT EXISTS AliquotView AS {aliquot_query}'
    query = QtS.QSqlQuery()
    # print(aliquot_view)
    if not query.exec(aliquot_view):
        print('Aliquot view creation failed')
        return False

def create_aliquot_edit_view():
    aliquot_query = AliquotEditViewQuery()
    # print(aliquot_query)
    aliquot_view = f'CREATE VIEW IF NOT EXISTS AliquotEditView AS {aliquot_query}'
    query = QtS.QSqlQuery()
    # print(aliquot_view)
    if not query.exec(aliquot_view):
        print('Aliquot edit view creation failed')
        return False

def create_spot_view():
    spot_query = SpotViewQuery()
    # print(spot_query)
    spot_view = f'CREATE VIEW IF NOT EXISTS SpotView AS {spot_query}'
    query = QtS.QSqlQuery()
    # print(spot_view)
    if not query.exec(spot_view):
        print('Spot view creation failed')
        return False

def create_spot_edit_view():
    spot_query = SpotEditViewQuery()
    # print(spot_query)
    spot_view = f'CREATE VIEW IF NOT EXISTS SpotEditView AS {spot_query}'
    query = QtS.QSqlQuery()
    # print(spot_view)
    if not query.exec(spot_view):
        print('Spot edit view creation failed')
        return False

def create_upb_view():
    upb_query = UPbViewQuery()
    # print(upb_query)
    upb_view = f'CREATE VIEW IF NOT EXISTS UPbView AS {upb_query}'
    query = QtS.QSqlQuery()
    # print(upb_view)
    if not query.exec(upb_view):
        print('UPb view creation failed')
        return False

def create_upb_edit_view():
    upb_query = UPbEditViewQuery()
    # print(upb_query)
    upb_view = f'CREATE VIEW IF NOT EXISTS UPbEditView AS {upb_query}'
    query = QtS.QSqlQuery()
    # print(upb_view)
    if not query.exec(upb_view):
        print('UPb edit view creation failed: ', query.lastError().text())
        return False

def create_column_view():
    column_query = ColumnViewQuery()
    # print(column_query)
    column_view = f'CREATE VIEW IF NOT EXISTS ColumnView AS {column_query}'
    query = QtS.QSqlQuery()
    # print(column_view)
    if not query.exec(column_view):
        print('Column view creation failed')
        return False

def create_column_edit_view():
    column_query = ColumnEditViewQuery()
    column_view = f'CREATE VIEW IF NOT EXISTS ColumnEditView AS {column_query}'
    query = QtS.QSqlQuery()
    # print(column_view)
    if not query.exec(column_view):
        print('Column edit view creation failed')
        return False

def create_all_views():
    create_sample_view()
    create_sample_ifnull_view()
    create_aliquot_view()
    create_aliquot_edit_view()
    create_spot_view()
    create_spot_edit_view()
    create_upb_view()
    create_upb_edit_view()
    create_column_view()
    create_column_edit_view()

def drop_view(view: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'DROP VIEW IF EXISTS {view}'):
        print(f'Failed to drop {view}: {query.lastError().text()}')
        return False

def drop_all_views():
    query = QtS.QSqlQuery()
    query.exec('SELECT name FROM sqlite_master WHERE type="view"')
    views = []
    while query.next():
        views.append(query.value(0))
    for view in views:
        drop_view(view)