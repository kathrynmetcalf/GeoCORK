import sqlite3
import time

from PyQt6 import QtSql as QtS

import Functions.SQLUtils as SQLUtils
import logger_setup
from Functions.Widget_classes import get_headers
from Functions.Settings_manager import settings


def SampleViewQuery():
    # Select columns
    sample_query = f'''
            {SQLUtils.qupb_count_sample_subquery}
            SELECT
                    {SQLUtils.qsample_id},
                    {SQLUtils.qigsn},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qsample_description},
                    {SQLUtils.qsample_gps_id},
                    {SQLUtils.qgps_display},
                    {SQLUtils.qsample_elev_display},
                    {SQLUtils.qsample_elev_unit},
                    {SQLUtils.qgps},
                    {SQLUtils.qsample_elev},
                    {SQLUtils.qsample_age},
                    {SQLUtils.qsample_age_constraint},
                    {SQLUtils.qsample_age_interpretation},
                    {SQLUtils.qsample_age_references},
                    {SQLUtils.qcolumn_name},
                    {SQLUtils.qsample_column_data_display},
                    {SQLUtils.qsample_column_data_unit},
                    {SQLUtils.qsample_column_data},
                    {SQLUtils.qage_signature},
                    {SQLUtils.qregions},
                    {SQLUtils.qrock_types},
                    {SQLUtils.qsample_context},
                    {SQLUtils.qsampling_methods},
                    {SQLUtils.qsettings},
                    {SQLUtils.qunits},
                    {SQLUtils.qaliquots},
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
                    {SQLUtils.qspot_size},
                    {SQLUtils.qspot_size_unit},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_contexts},
                    {SQLUtils.qupb_references},
                    {SQLUtils.qsample_created},
                    {SQLUtils.qsample_modified}
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
                   {SQLUtils.default_sample_age_join}
                   {SQLUtils.sample_age_join}
                   {SQLUtils.sample_age_left_joins}
                   {SQLUtils.sampleage_age_constraint_join}
                   {SQLUtils.sampleage_age_interpretation_join}
                   {SQLUtils.sampleage_age_reference_join}
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
                   {SQLUtils.upb_rejection_reason_join}
                   {SQLUtils.upb_context_join}
                   GROUP BY Samples.SampleID
                   '''

    # print(sample_query)
    return sample_query


# def SampleViewQuery():
#     # Select columns
#
#     sample_query = f'''
#             {SQLUtils.qupb_count_sample_subquery}
#             SELECT
#                     {SQLUtils.qsample_id},
#                     {SQLUtils.qigsn},
#                     {SQLUtils.qsample_name},
#                     {SQLUtils.qsample_description},
#                     {SQLUtils.qsample_gps_id},
#                     {SQLUtils.qgps_display},
#                     {SQLUtils.qsample_elev_display},
#                     {SQLUtils.qsample_elev_unit},
#                     {SQLUtils.qgps},
#                     {SQLUtils.qsample_elev},
#                     {SQLUtils.qsample_age},
#                     {SQLUtils.qsample_age_constraint},
#                     {SQLUtils.qsample_age_interpretation},
#                     {SQLUtils.qsample_age_references},
#                     {SQLUtils.qcolumn_name},
#                     {SQLUtils.qsample_column_data_display},
#                     {SQLUtils.qsample_column_data_unit},
#                     {SQLUtils.qsample_column_data},
#                     {SQLUtils.qage_signature},
#                     {SQLUtils.qregions},
#                     {SQLUtils.qrock_types},
#                     {SQLUtils.qsample_context},
#                     {SQLUtils.qsampling_methods},
#                     {SQLUtils.qsettings},
#                     {SQLUtils.qunits},
#                     {SQLUtils.qaliquots},
#                     {SQLUtils.qaliquot_contexts},
#                     {SQLUtils.qspot_count},
#                     {SQLUtils.qspot_compositions},
#                     {SQLUtils.qspot_contexts},
#                     {SQLUtils.qupb_count},
#                     {SQLUtils.qupb_lab_facilities},
#                     {SQLUtils.qupb_analysis_methods},
#                     {SQLUtils.qupb_ratio_error_formats},
#                     {SQLUtils.qupb_age_units},
#                     {SQLUtils.qupb_age_error_formats},
#                     {SQLUtils.qconcordance_formats},
#                     {SQLUtils.qspot_sizes},
#                     {SQLUtils.qspot_size},
#                     {SQLUtils.qspot_size_unit},
#                     {SQLUtils.qupb_rejection_reasons},
#                     {SQLUtils.qupb_references},
#                     {SQLUtils.qsample_created},
#                     {SQLUtils.qsample_modified}
#                 FROM Samples
#                 {SQLUtils.age_signature_join}
#                 {SQLUtils.column_join}
#                 {SQLUtils.column_unit_join}
#                 {SQLUtils.region_join}
#                 {SQLUtils.rock_type_join}
#                 {SQLUtils.sample_context_join}
#                 {SQLUtils.sample_sampleage_join}
#                 {SQLUtils.sampling_method_join}
#                 {SQLUtils.setting_join}
#                 {SQLUtils.unit_join}
#                 {SQLUtils.default_sample_age_join}
#                 {SQLUtils.sample_age_join}
#                 {SQLUtils.sample_age_left_joins}
#                 {SQLUtils.sampleage_age_constraint_join}
#                 {SQLUtils.sampleage_age_interpretation_join}
#                 {SQLUtils.sampleage_age_reference_join}
#                 {SQLUtils.gps_sample_join}
#                 {SQLUtils.gps_sample_left_joins}
#                 {SQLUtils.gps_column_join}
#                 {SQLUtils.gps_column_left_joins}
#                 {SQLUtils.sample_aliquot_join}
#                 {SQLUtils.aliquot_context_join}
#                 {SQLUtils.aliquot_spot_join}
#                 {SQLUtils.spot_composition_join}
#                 {SQLUtils.spot_context_join}
#                 {SQLUtils.spot_upb_analysis_join}
#                 {SQLUtils.upb_distinct_join_sample}
#                 {SQLUtils.upb_reference_join}
#                 {SQLUtils.upb_labs_join}
#                 {SQLUtils.upb_instruments_join}
#                 {SQLUtils.upb_method_join}
#                 {SQLUtils.upb_ratio_error_format_join}
#                 {SQLUtils.upb_age_error_format_join}
#                 {SQLUtils.upb_age_unit_join}
#                 {SQLUtils.upb_concordance_format_join}
#                 {SQLUtils.upb_spot_size_unit_join}
#                 {SQLUtils.upb_rejection_reason_join}
#                 GROUP BY Samples.SampleID
#                 '''
#
#     # print(sample_query)
#     return sample_query


def AliquotViewQuery():
    aliquot_query = f'''
                {SQLUtils.qupb_count_aliquot_subquery}
                SELECT
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qaliquot_parent_id},
                    {SQLUtils.qaliquot_parent_row},
                    {SQLUtils.qaliquot_name},
                    {SQLUtils.qsample_id},
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
                    {SQLUtils.qupb_contexts},
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
                {SQLUtils.upb_rejection_reason_join}
                {SQLUtils.upb_context_join}
                GROUP BY Aliquots.AliquotID
                '''

    return aliquot_query


def AliquotEditViewQuery():
    aliquot_query = f'''
                SELECT
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qaliquot_parent_id},
                    {SQLUtils.qaliquot_parent_row},
                    {SQLUtils.qaliquot_name},
                    {SQLUtils.qsample_id},
                    {SQLUtils.qaliquot_sample},
                    {SQLUtils.qaliquot_contexts},
                    {SQLUtils.qaliquot_created},
                    {SQLUtils.qaliquot_modified}
                FROM Aliquots
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.aliquot_context_join}
                GROUP BY Aliquots.AliquotID
                '''

    return aliquot_query


def SpotViewQuery():
    spot_query = f'''
                SELECT
                    {SQLUtils.qspot_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qsample_id},
                    {SQLUtils.qspot_name},
                    {SQLUtils.qaliquot_name},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qspot_composition},
                    {SQLUtils.qspot_contexts},
                    {SQLUtils.qupb_lab_facilities},
                    {SQLUtils.qupb_analysis_methods},
                    {SQLUtils.qupb_ratio_error_formats},
                    {SQLUtils.qupb_age_units},
                    {SQLUtils.qupb_age_error_formats},
                    {SQLUtils.qconcordance_formats},
                    {SQLUtils.qspot_sizes},
                    {SQLUtils.qupb_rejected},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_contexts},
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
                {SQLUtils.upb_context_join}
                GROUP BY Spots.SpotID
                '''

    return spot_query


def SpotEditViewQuery():
    spot_query = f'''
                SELECT
                    {SQLUtils.qspot_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qsample_id},
                    {SQLUtils.qspot_name},
                    {SQLUtils.qaliquot_name},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qspot_composition},
                    {SQLUtils.qspot_contexts},
                    {SQLUtils.qspot_created},
                    {SQLUtils.qspot_modified}
                FROM Spots
                {SQLUtils.spot_aliquot_join}
                {SQLUtils.aliquot_sample_join}
                {SQLUtils.spot_composition_join}
                {SQLUtils.spot_context_join}
                GROUP BY Spots.SpotID
                '''

    return spot_query


def UPbViewQuery():
    headers = get_headers('UPbAnalyses')
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
    query_columns = ',\n'.join(columns)

    upb_query = f'''
                SELECT 
                    {SQLUtils.qupb_id},
                    {SQLUtils.qspot_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qsample_id},
                    {SQLUtils.qspot_name},
                    {SQLUtils.qaliquot_name},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qupb_references},
                    {SQLUtils.qupb_lab_facilities},
                    {SQLUtils.qupb_instruments},
                    {SQLUtils.qupb_analysis_methods},
                    {query_columns},
                    {SQLUtils.qupb_rejected},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_contexts},
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
                {SQLUtils.upb_context_join}
                GROUP BY UPbAnalyses.UPbAnalysisID
                '''
    return upb_query


def UPbEditViewQuery():
    headers = get_headers('UPbAnalyses')
    columns = []
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
    query_columns = ',\n'.join(columns)

    upb_query = f'''
                SELECT 
                    {SQLUtils.qupb_id},
                    {SQLUtils.qspot_id},
                    {SQLUtils.qaliquot_id},
                    {SQLUtils.qsample_id},
                    {SQLUtils.qspot_name},
                    {SQLUtils.qaliquot_name},
                    {SQLUtils.qsample_name},
                    {SQLUtils.qupb_references},
                    {SQLUtils.qupb_lab_facilities},
                    {SQLUtils.qupb_instruments},
                    {SQLUtils.qupb_analysis_methods},
                    {query_columns},
                    {SQLUtils.qupb_ratio_error_formats},
                    {SQLUtils.qupb_age_units},
                    {SQLUtils.qupb_age_error_formats},
                    {SQLUtils.qconcordance_formats},
                    {SQLUtils.qspot_size_unit},
                    {SQLUtils.qupb_rejected},
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_contexts},
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
                {SQLUtils.upb_context_join}
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
                    {SQLUtils.qcolumn_elev},
                    {SQLUtils.qcolumn_description},
                    {SQLUtils.qcolumn_created},
                    {SQLUtils.qcolumn_modified}
                FROM Columns
                {SQLUtils.gps_column_join}
                GROUP BY Columns.ColumnID
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
                        {SQLUtils.qcolumn_gps_id},
                        {SQLUtils.qcolumn_gps_display},
                        {SQLUtils.qcolumn_elev_display},
                        {SQLUtils.qcolumn_elev_unit},
                        {SQLUtils.qcolumn_description},
                        {SQLUtils.qcolumn_created},
                        {SQLUtils.qcolumn_modified}
                    FROM Columns
                    {SQLUtils.column_units_join}
                    {SQLUtils.gps_column_join}
                    {SQLUtils.gps_column_left_joins}
                    GROUP BY Columns.ColumnID
                    '''
    # print(column_query)
    return column_query


def ReferenceViewQuery():
    # Select columns

    reference_query = f'''
                SELECT
                    {SQLUtils.qreference_id},
                    {SQLUtils.qreference_display},
                    {SQLUtils.qauthors},
                    {SQLUtils.qyear},
                    {SQLUtils.qtitle},
                    {SQLUtils.qsource},
                    {SQLUtils.qdoi},
                    {SQLUtils.qreference_description},
                    {SQLUtils.qreference_created},
                    {SQLUtils.qreference_modified}
                FROM "References"
                '''
    # print(reference_query)
    return reference_query


def create_sample_view():
    start_time = time.time()
    sample_query = SampleViewQuery()
    if settings.value('autofill_best_age') == 'true':
        # replace the necessary columns with 'Filled' at the end
        for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge', 'CalculatedBestAgeError'):
            sample_query = sample_query.replace(f'"{column}"', f'"{column}Filled"')

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(sample_query)
        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating SampleView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {sample_query}')
        return False

    sample_view = f'CREATE VIEW IF NOT EXISTS SampleView AS {sample_query}'
    logger_setup.get_logger().info(f'Creating SampleView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(sample_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating SampleView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {sample_view}')
        return False
    logger_setup.get_logger().info(f'Successfully created SampleView {time.time() - start_time} seconds')
    return True

# def create_sample_edit_view():
#     sample_query = SampleViewQuery()
#     query = QtS.QSqlQuery()
#     if not query.exec(sample_query):
#         logger_setup.get_logger().critical('Error creating SampleView')
#         logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
#         logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
#         return False
#     sample_view = f'CREATE VIEW IF NOT EXISTS SampleView AS {sample_query}'
#     logger_setup.get_logger().info(f'Creating SampleView')
#     if not query.exec(sample_view):
#         logger_setup.get_logger().critical(f'Error creating SampleView')
#         logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
#         logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
#         return False
#     logger_setup.get_logger().info(f'Successfully created SampleView')


def create_aliquot_view():
    start_time = time.time()
    aliquot_query = AliquotViewQuery()
    if settings.value('autofill_best_age') == 'true':
        for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge',
                       'CalculatedBestAgeError'):
            aliquot_query = aliquot_query.replace(f'"{column}"', f'"{column}Filled"')

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(aliquot_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating AliquotView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {aliquot_query}')
        return False

    aliquot_view = f'CREATE VIEW IF NOT EXISTS AliquotView AS {aliquot_query}'
    logger_setup.get_logger().info('Creating AliquotView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(aliquot_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating AliquotView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {aliquot_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created AliquotView {time.time() - start_time} seconds')
    return True


def create_aliquot_edit_view():
    start_time = time.time()
    aliquot_query = AliquotEditViewQuery()

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(aliquot_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating AliquotEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {aliquot_query}')
        return False

    aliquot_view = f'CREATE VIEW IF NOT EXISTS AliquotEditView AS {aliquot_query}'
    logger_setup.get_logger().info('Creating AliquotEditView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(aliquot_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating AliquotEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {aliquot_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created AliquotEditView {time.time() - start_time} seconds')
    return True

def create_spot_view():
    start_time = time.time()
    spot_query = SpotViewQuery()
    if settings.value('autofill_best_age') == 'true':
        for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge',
                       'CalculatedBestAgeError'):
            spot_query = spot_query.replace(f'"{column}"', f'"{column}Filled"')

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(spot_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating SpotView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {spot_query}')
        return False

    spot_view = f'CREATE VIEW IF NOT EXISTS SpotView AS {spot_query}'
    logger_setup.get_logger().info('Creating SpotView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(spot_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating SpotView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {spot_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created SpotView {time.time() - start_time} seconds')
    return True

def create_spot_edit_view():
    start_time = time.time()
    spot_query = SpotEditViewQuery()

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(spot_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating SpotEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {spot_query}')
        return False

    spot_view = f'CREATE VIEW IF NOT EXISTS SpotEditView AS {spot_query}'
    logger_setup.get_logger().info('Creating SpotEditView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(spot_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating SpotEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {spot_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created SpotEditView {time.time() - start_time} seconds')
    return True

def create_upb_view():
    start_time = time.time()
    upb_query = UPbViewQuery()

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(upb_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating UPbView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {upb_query}')
        return False

    upb_view = f'CREATE VIEW IF NOT EXISTS UPbView AS {upb_query}'
    logger_setup.get_logger().info('Creating UPbView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(upb_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating UPbView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {upb_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created UPbView {time.time() - start_time} seconds')
    return True

def create_upb_edit_view():
    start_time = time.time()
    upb_query = UPbEditViewQuery()
    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(upb_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating UPbEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {upb_query}')
        return False

    upb_view = f'CREATE VIEW IF NOT EXISTS UPbEditView AS {upb_query}'
    logger_setup.get_logger().info('Creating UPbEditView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(upb_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating UPbEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {upb_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created UPbEditView in {time.time() - start_time} seconds')
    return True

def create_column_view():
    start_time = time.time()
    column_query = ColumnViewQuery()

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(column_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating ColumnView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {column_query}')
        return False

    column_view = f'CREATE VIEW IF NOT EXISTS ColumnView AS {column_query}'
    logger_setup.get_logger().info('Creating ColumnView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(column_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating ColumnView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {column_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created ColumnView {time.time() - start_time} seconds')
    return True

def create_column_edit_view():
    start_time = time.time()
    column_query = ColumnEditViewQuery()

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(column_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating ColumnEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {column_query}')
        return False

    column_view = f'CREATE VIEW IF NOT EXISTS ColumnEditView AS {column_query}'
    logger_setup.get_logger().info('Creating ColumnEditView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(column_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating ColumnEditView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {column_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created ColumnEditView {time.time() - start_time} seconds')
    return True

def create_reference_view():
    start_time = time.time()
    reference_query = ReferenceViewQuery()

    database = settings._instance.value('db_file', type=str)
    uri = f'file:{database}'

    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(reference_query)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating ReferenceView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {reference_query}')
        return False

    reference_view = f'CREATE VIEW IF NOT EXISTS ReferenceView AS {reference_query}'
    logger_setup.get_logger().info('Creating ReferenceView')
    try:
        conn = sqlite3.connect(uri, uri=True)
        with conn:
            cursor = conn.cursor()
            cursor.execute(reference_view)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger_setup.get_logger().critical('Error creating ReferenceView')
        logger_setup.get_logger().debug(f'Error: {e}')
        logger_setup.get_logger().debug(f'SQL query: {reference_view}')
        return False
    logger_setup.get_logger().info(
        f'Successfully created ReferenceView {time.time() - start_time} seconds')
    return True

def create_all_views():
    start_time = time.time()
    from Functions.Settings_manager import settings
    logger_setup.get_logger().info('Creating all views')

    if not create_sample_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    # create_sample_edit_view()
    if not create_aliquot_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_aliquot_edit_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_spot_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_spot_edit_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_upb_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_upb_edit_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_column_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_column_edit_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    if not create_reference_view():
        logger_setup.get_logger().critical('Error creating views')
        return False
    end_time = time.time()
    logger_setup.get_logger().info(f'All views created in {end_time - start_time} seconds')
    return True

def drop_view(view: str):
    query = QtS.QSqlQuery()
    sql = f'DROP VIEW IF EXISTS {view}'
    logger_setup.get_logger().info(f'Dropping view: {view}')
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error dropping view: {view}')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully dropped view: {view}')


def drop_all_views():
    start_time = time.time()
    logger_setup.get_logger().info('Dropping all views')
    query = QtS.QSqlQuery()
    sql = 'SELECT name FROM sqlite_master WHERE type="view"'
    if not query.exec(sql):
        logger_setup.get_logger().critical(f'Error getting all views from database')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    views = []
    while query.next():
        views.append(query.value(0))
    for view in views:
        drop_view(view)
    end_time = time.time()
    logger_setup.get_logger().info(f'All views dropped in {end_time - start_time} seconds')



if __name__ == '__main__':
    print('CREATE VIEW IF NOT EXISTS SampleView AS'  + SampleViewQuery())