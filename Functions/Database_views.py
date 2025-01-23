import sqlite3
import PyQt6
from PyQt6 import QtSql as QtS
from PyQt6 import QtWidgets as QtW
import Functions.SQLUtils as SQLUtils
from Functions.SQLUtils import gps_column_join


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
                    {SQLUtils.qreferences},
                    {SQLUtils.qage_signature},
                    {SQLUtils.qregions},
                    {SQLUtils.qrock_types},
                    {SQLUtils.qsample_context},
                    {SQLUtils.qsampling_methods},
                    {SQLUtils.qsettings},
                    {SQLUtils.qunits},
                    {SQLUtils.qaliquots},
                    {SQLUtils.qaliquot_contexts},
                    {SQLUtils.qspots},
                    {SQLUtils.qspot_compositions},
                    {SQLUtils.qspot_contexts},
                    {SQLUtils.qlab_facilities},
                    {SQLUtils.qupb_analysis_methods},
                    {SQLUtils.qupb_ratio_error_formats},
                    {SQLUtils.qupb_age_units},
                    {SQLUtils.qupb_age_error_formats},
                    {SQLUtils.qconcordance_formats},
                    {SQLUtils.qspot_sizes},
                    {SQLUtils.qupb_rejection_reasons},
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
                {SQLUtils.aliquot_join}
                {SQLUtils.aliquot_context_join}
                {SQLUtils.spot_join}
                {SQLUtils.spot_composition_join}
                {SQLUtils.spot_context_join}
                {SQLUtils.upb_analysis_join}
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
                {where_statement}
                GROUP BY Samples.SampleName
                ORDER BY Samples.SampleID
                '''

    # print(sample_query)
    return sample_query


def SampleIfNullQuery():
    sample_ifnull_query = f'''
    SELECT 
        {SQLUtils.qsample_name_ifnull},
        {SQLUtils.qigsn_ifnull},
        {SQLUtils.qsample_gps_id_ifnull},
        {SQLUtils.qcolumn_name_ifnull},
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
    {SQLUtils.aliquot_join}
    {SQLUtils.aliquot_context_join}
    {SQLUtils.spot_join}
    {SQLUtils.spot_composition_join}
    {SQLUtils.spot_context_join}
    {SQLUtils.upb_analysis_join}
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

def AliquotViewQuery(sample_ids: list):
    if len(sample_ids) == 1:
        where_statement = f'WHERE SampleID = {sample_ids[0]}'
    else:
        where_statement = f'WHERE SampleID IN {tuple(sample_ids)}'
    # Select columns
    aliquots = 'AliquotName as "Aliquots"'
    aliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Context"'
    spots = 'GROUP_CONCAT(DISTINCT SpotName) as "Spots"'
    spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Context"'
    spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
    references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
    upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
    labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

    # Join columns
    aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContexts as AQ_AQCX ON AQ.AliquotID=AQ_AQCX.AliquotID
                        LEFT JOIN AliquotContexts as AQCX ON AQCX.AliquotContextID=AQ_AQCX.AliquotContextID'''
    spot_join = 'LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID'
    spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                        LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
    spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
    upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
    reference_join = 'LEFT JOIN "References" as SO ON SO.ReferenceID=UPB.ReferenceID'
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
                {reference_join}
                {upb_method_join}
                {labs_join}
                {where_statement}
                GROUP BY AliquotName
                '''

    aliquot_view = f'CREATE VIEW IF NOT EXISTS Sample{sample_ids}_AliquotView AS {aliquot_query}'
    return aliquot_view

def SpotViewQuery(parent_id, id_type='sample'):
    # Select columns
    spots = 'SpotName as "Spots"'
    spot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Context"'
    spot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
    references = 'GROUP_CONCAT(DISTINCT ShortCitation) as "References"'
    upb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
    labs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'

    # Join columns
    spot_context_join = '''LEFT JOIN Spots_SpotContexts as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                        LEFT JOIN SpotContexts as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
    spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
    upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
    reference_join = 'LEFT JOIN "References" as SO ON SO.ReferenceID=UPB.ReferenceID'
    upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
    labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'

    # Where statement
    if id_type == 'sample':
        where = f'WHERE SampleID = {parent_id}'
        parent_text = f'Sample{parent_id}'
    elif id_type == 'aliquot':
        where = f'WHERE AliquotID = {parent_id}'
        parent_text = f'Aliquot{parent_id}'
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
                {reference_join}
                {upb_method_join}
                {labs_join}
                {where}
                GROUP BY SpotName
                '''

    spot_view = f'CREATE VIEW IF NOT EXISTS {parent_text}_SpotView AS {spot_query}'
    return spot_view

def ColumnViewQuery():
    # Select columns
    columns = 'ColumnName'

    column_query = f'''
                SELECT
                    {SQLUtils.qcolumn_id},
                    {columns},
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
                        {columns},
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

def create_sample_view(conditions: str = None):
    base_query = SampleViewQuery()
    if conditions:
        sample_query = f'{base_query} {conditions}'
    else:
        sample_query = base_query
    sample_view = f'CREATE VIEW IF NOT EXISTS SampleView AS {sample_query}'
    # print(sample_view)
    query = QtS.QSqlQuery()
    if not query.exec(sample_view):
        print('Sample view creation failed')
        return False

def create_aliquot_view(sample_IDs, conditions: str = None):
    base_query = create_aliquot_view(sample_IDs)
    if conditions:
        aliquot_query = f'{base_query} {conditions}'
    else:
        aliquot_query = base_query
    query = QtS.QSqlQuery()
    if not query.exec(aliquot_query):
        print('Aliquot view creation failed')
        return False

# def create_spot_view(c, parent_ID, parent_type):
#     """
#     Take database cursor and sample ID and execute the sql strings defined above to create the spot view
#     :param c: Cursor of database connection
#     :param parent_ID: ID of parent sample
#     :param parent_type: 'sample' or 'aliquot'
#     """
#     SPOT_VIEW = create_spot_view(parent_ID, parent_type)
#     c.execute(SPOT_VIEW)

def create_column_view():
    column_query = ColumnViewQuery()
    print(column_query)
    column_view = f'CREATE VIEW IF NOT EXISTS ColumnView AS {column_query}'
    query = QtS.QSqlQuery()
    if not query.exec(column_view):
        print('Column view creation failed')
        return False

def create_column_edit_view():
    column_query = ColumnEditViewQuery()
    column_view = f'CREATE VIEW IF NOT EXISTS ColumnEditView AS {column_query}'
    query = QtS.QSqlQuery()
    if not query.exec(column_view):
        print('Column edit view creation failed')
        return False

def create_all_views():
    create_sample_view()
    create_column_view()
    create_column_edit_view()

def drop_view(view: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'DROP VIEW IF EXISTS {view}'):
        print(f'Failed to drop {view}: {query.lastError().text()}')
        return False


if __name__ == '__main__':
    db_file = '../TestSchema.db'
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        create_sample_view(c)