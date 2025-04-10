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
                    {SQLUtils.qgps},
                    {SQLUtils.qsample_elev},
                    {SQLUtils.qsample_age},
                    {SQLUtils.qsample_age_constraint},
                    {SQLUtils.qsample_age_interpretation},
                    {SQLUtils.qsample_age_references},
                    {SQLUtils.qcolumn_name},
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
                    {SQLUtils.qupb_rejection_reasons},
                    {SQLUtils.qupb_references},
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
                {SQLUtils.sampleage_age_constraint_join}
                {SQLUtils.sampleage_age_interpretation_join}
                {SQLUtils.sampleage_age_reference_join}
                {SQLUtils.gps_sample_join}
                {SQLUtils.gps_column_join}
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
                GROUP BY Samples.SampleID
                '''

    # print(sample_query)
    return sample_query


def SampleEditViewQuery():
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
                    {SQLUtils.qsample_age},
                    {SQLUtils.qsample_age_constraint},
                    {SQLUtils.qsample_age_interpretation},
                    {SQLUtils.qsample_age_references},
                    {SQLUtils.qcolumn_name},
                    {SQLUtils.qsample_column_data_display},
                    {SQLUtils.qsample_column_data_unit},
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
                    {SQLUtils.qspot_size},
                    {SQLUtils.qspot_size_unit},
                    {SQLUtils.qupb_rejection_reasons},
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
                GROUP BY Samples.SampleID
                '''

    # print(sample_query)
    return sample_query


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
    sample_query = SampleViewQuery()
    if settings.value('autofill_best_age') == 'true':
        # replace the necessary columns with 'Filled' at the end
        for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge', 'CalculatedBestAgeError'):
            sample_query = sample_query.replace(f'"{column}"', f'"{column}Filled"')
    query = QtS.QSqlQuery()
    if not query.exec(sample_query):
        logger_setup.get_logger().critical('Error creating SampleView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    sample_view = f'CREATE VIEW IF NOT EXISTS SampleView AS {sample_query}'
    logger_setup.get_logger().info(f'Creating SampleView')
    if not query.exec(sample_view):
        logger_setup.get_logger().critical(f'Error creating SampleView)')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created SampleView')


def create_sample_edit_view():
    sample_query = SampleEditViewQuery()
    query = QtS.QSqlQuery()
    if not query.exec(sample_query):
        logger_setup.get_logger().critical('Error creating SampleEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    sample_view = f'CREATE VIEW IF NOT EXISTS SampleEditView AS {sample_query}'
    logger_setup.get_logger().info(f'Creating SampleEditView')
    if not query.exec(sample_view):
        logger_setup.get_logger().critical(f'Error creating SampleEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created SampleEditView')


def create_aliquot_view():
    aliquot_query = AliquotViewQuery()
    if settings.value('autofill_best_age') == 'true':
        # replace the necessary columns with 'Filled' at the end
        for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge', 'CalculatedBestAgeError'):
            aliquot_query = aliquot_query.replace(f'"{column}"', f'"{column}Filled"')
    query = QtS.QSqlQuery()
    if not query.exec(aliquot_query):
        logger_setup.get_logger().critical('Error creating AliquotView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    aliquot_view = f'CREATE VIEW IF NOT EXISTS AliquotView AS {aliquot_query}'
    logger_setup.get_logger().info(f'Creating AliquotView')
    if not query.exec(aliquot_view):
        logger_setup.get_logger().critical(f'Error creating AliquotView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created AliquotView')


def create_aliquot_edit_view():
    aliquot_query = AliquotEditViewQuery()
    query = QtS.QSqlQuery()
    if not query.exec(aliquot_query):
        logger_setup.get_logger().critical('Error creating AliquotEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    aliquot_view = f'CREATE VIEW IF NOT EXISTS AliquotEditView AS {aliquot_query}'
    logger_setup.get_logger().info(f'Creating AliquotEditView')
    if not query.exec(aliquot_view):
        logger_setup.get_logger().critical(f'Error creating AliquotEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created AliquotEditView')


def create_spot_view():
    spot_query = SpotViewQuery()
    if settings.value('autofill_best_age') == 'true':
        # replace the necessary columns with 'Filled' at the end
        for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge', 'CalculatedBestAgeError'):
            spot_query = spot_query.replace(f'"{column}"', f'"{column}Filled"')
    query = QtS.QSqlQuery()
    if not query.exec(spot_query):
        logger_setup.get_logger().critical('Error creating SpotView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    spot_view = f'CREATE VIEW IF NOT EXISTS SpotView AS {spot_query}'
    logger_setup.get_logger().info(f'Creating SpotView')
    if not query.exec(spot_view):
        logger_setup.get_logger().critical(f'Error creating SpotView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created SpotView')


def create_spot_edit_view():
    spot_query = SpotEditViewQuery()
    query = QtS.QSqlQuery()
    if not query.exec(spot_query):
        logger_setup.get_logger().critical('Error creating SpotEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    spot_view = f'CREATE VIEW IF NOT EXISTS SpotEditView AS {spot_query}'
    logger_setup.get_logger().info(f'Creating SpotEditView')
    if not query.exec(spot_view):
        logger_setup.get_logger().critical(f'Error creating SpotEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created SpotEditView')


def create_upb_view():
    upb_query = UPbViewQuery()
    query = QtS.QSqlQuery()
    if not query.exec(upb_query):
        logger_setup.get_logger().critical('Error creating UPbView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    upb_view = f'CREATE VIEW IF NOT EXISTS UPbView AS {upb_query}'
    logger_setup.get_logger().info(f'Creating UPbView')
    if not query.exec(upb_view):
        logger_setup.get_logger().critical(f'Error creating UPbView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created UPbView')


def create_upb_edit_view():
    upb_query = UPbEditViewQuery()
    if settings.value('autofill_best_age') == 'true':
        # replace the necessary columns with 'Filled' at the end
        for column in ('BestAge', 'BestAgeError', 'CalculatedBestAge', 'CalculatedBestAgeError'):
            upb_query = upb_query.replace(f'"{column}"', f'"{column}Filled"')
    query = QtS.QSqlQuery()
    if not query.exec(upb_query):
        logger_setup.get_logger().critical('Error creating UPbEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    upb_view = f'CREATE VIEW IF NOT EXISTS UPbEditView AS {upb_query}'
    logger_setup.get_logger().info(f'Creating UPbEditView')
    if not query.exec(upb_view):
        logger_setup.get_logger().critical(f'Error creating UPbEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created UPbEditView')


def create_column_view():
    column_query = ColumnViewQuery()
    query = QtS.QSqlQuery()
    if not query.exec(column_query):
        logger_setup.get_logger().critical('Error creating ColumnView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    column_view = f'CREATE VIEW IF NOT EXISTS ColumnView AS {column_query}'
    logger_setup.get_logger().info(f'Creating ColumnView')
    if not query.exec(column_view):
        logger_setup.get_logger().critical(f'Error creating ColumnView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created ColumnView')


def create_column_edit_view():
    column_query = ColumnEditViewQuery()
    query = QtS.QSqlQuery()
    if not query.exec(column_query):
        logger_setup.get_logger().critical('Error creating ColumnEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    column_view = f'CREATE VIEW IF NOT EXISTS ColumnEditView AS {column_query}'
    logger_setup.get_logger().info(f'Creating ColumnEditView')
    if not query.exec(column_view):
        logger_setup.get_logger().critical(f'Error creating ColumnEditView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created ColumnEditView')


def create_reference_view():
    reference_query = ReferenceViewQuery()
    query = QtS.QSqlQuery()
    if not query.exec(reference_query):
        logger_setup.get_logger().critical('Error creating ReferenceView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    reference_view = f'CREATE VIEW IF NOT EXISTS ReferenceView AS {reference_query}'
    logger_setup.get_logger().info(f'Creating ReferenceView')
    if not query.exec(reference_view):
        logger_setup.get_logger().critical(f'Error creating ReferenceView')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return False
    logger_setup.get_logger().info(f'Successfully created ReferenceView')


def create_all_views():
    start_time = time.time()
    logger_setup.get_logger().info('Creating all views')
    create_sample_view()
    create_sample_edit_view()
    create_aliquot_view()
    create_aliquot_edit_view()
    create_spot_view()
    create_spot_edit_view()
    create_upb_view()
    create_upb_edit_view()
    create_column_view()
    create_column_edit_view()
    create_reference_view()
    end_time = time.time()
    logger_setup.get_logger().info(f'All views created in {end_time - start_time} seconds')


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
