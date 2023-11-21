import sqlite3


def SampleViewQuery():
    # Create the complex query for the sample view
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
    qcontext = 'GROUP_CONCAT(DISTINCT SampleContextName) as "Sample Context"'
    qsampling_methods = 'GROUP_CONCAT(DISTINCT SamplingMethodName) as "Sampling Method"'
    qrock_types = 'GROUP_CONCAT(DISTINCT RockTypeName) as "Rock Types"'
    qregions = 'GROUP_CONCAT(DISTINCT RegionName) as "Regions"'
    qsettings = 'GROUP_CONCAT(DISTINCT SettingName) as "Settings"'
    qunits = 'GROUP_CONCAT(DISTINCT UnitName) as "Units"'
    qupb_methods = 'GROUP_CONCAT(DISTINCT UPbAnalysisMethodName) as "UPb Analysis Methods"'
    qlabs = 'GROUP_CONCAT(DISTINCT LabFacilityName) as "Lab Facilities"'
    qspot_context = 'GROUP_CONCAT(DISTINCT SpotContextName) as "Spot Context"'
    qspot_compositions = 'GROUP_CONCAT(DISTINCT SpotCompositionName) as "Spot Compositions"'
    qaliquot_context = 'GROUP_CONCAT(DISTINCT AliquotContextName) as "Aliquot Context"'

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
    sample_context_join = '''LEFT JOIN Samples_SampleContext as S_SC ON S.SampleID=S_SC.SampleID
                        LEFT JOIN SampleContext as SC ON SC.SampleContextID=S_SC.SampleContextID'''
    sampling_method_join = '''LEFT JOIN Samples_SamplingMethods as S_SM ON S.SampleID=S_SM.SampleID
                        LEFT JOIN SamplingMethods as SM ON SM.SamplingMethodID=S_SM.SamplingMethodID'''
    aliquot_join = 'LEFT JOIN Aliquots as AQ ON AQ.SampleID=S.SampleID'
    spot_join = 'LEFT JOIN Spots as SP ON SP.AliquotID=AQ.AliquotID'
    upb_data_join = 'LEFT JOIN UPbData as UPB ON UPB.SpotID=SP.SpotID'
    source_join = 'LEFT JOIN Sources as SO ON SO.SourceID=UPB.SourceID'
    upb_method_join = 'LEFT JOIN UPbAnalysisMethods as UAM ON UAM.UPbAnalysisMethodID=UPB.UPbAnalysisMethodID'
    labs_join = 'LEFT JOIN LabFacilities as LF ON LF.LabFacilityID=UPB.LabFacilityID'
    spot_context_join = '''LEFT JOIN Spots_SpotContext as SP_SPCX ON SP.SpotID=SP_SPCX.SpotID
                        LEFT JOIN SpotContext as SPCX ON SPCX.SpotContextID=SP_SPCX.SpotContextID'''
    spot_composition_join = '''LEFT JOIN SpotCompositions as SPC ON SPC.SpotCompositionID=SP.SpotCompositionID'''
    aliquot_context_join = '''LEFT JOIN Aliquots_AliquotContext as AQ_AQCX ON AQ.AliquotID=AQ_AQCX.AliquotID
                        LEFT JOIN AliquotContext as AQCX ON AQCX.AliquotContextID=AQ_AQCX.AliquotContextID'''

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
                ORDER BY SampleName
                '''

    sample_view = f'CREATE VIEW IF NOT EXISTS SampleView AS {sample_query}'
    return sample_view

def create_views(c):
    """
    Take database cursor and execute the sql strings defined above to create the database triggers
    :param c: Cursor of database connection
    """
    SAMPLE_VIEW = SampleViewQuery()
    c.execute(SAMPLE_VIEW)


if __name__ == '__main__':
    db_file = '../TestSchema.db'
    conn = sqlite3.connect(db_file)
    with conn:
        c = conn.cursor()
        create_views(db_file)