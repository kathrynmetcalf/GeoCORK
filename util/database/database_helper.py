from util.database.defined_joins import *


def get_join_from_table(join: str, tables: list[str]) -> str:
    """
    Function to take a current SQL join string and append other join strings based upon a list of tables.

    :param str join: Current join statement to add to
    :param list[str] tables: List of tables to append to the join statement
    :return: Final join with added tables
    :rtype: str
    """
    for table in tables:
        match table:
            case 'AgeConstraints':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_constraint_join not in join:
                    join += sampleage_age_constraint_join + '\n'
            case 'AgeInterpretations':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_interpretation_join not in join:
                    join += sampleage_age_interpretation_join + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Ages':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
            case 'OldAge':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
                if sample_age_left_joins not in join:
                    join += sample_age_left_joins + '\n'
            case 'YoungAge':
                if sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sample_age_join not in join:
                    join += sample_age_join + '\n'
                if sample_age_left_joins not in join:
                    join += sample_age_left_joins + '\n'
            case 'AgeSignatures':
                if age_signature_join not in join:
                    join += age_signature_join + '\n'
            case 'Aliquots':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
            case 'AliquotContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_context_join not in join:
                    join += aliquot_context_join + '\n'
            case 'Columns':
                if column_join not in join:
                    join += column_join + '\n'
            case 'DefaultSampleAges':
                if sample_sampleage_join not in join and default_sample_age_join not in join:
                    join += default_sample_age_join + '\n'
            case 'LabFacilities':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_labs_join not in join:
                    join += upb_labs_join + '\n'
            case 'Grains':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
            case 'GrainCompositions':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
                if grain_composition_join not in join:
                    join += grain_composition_join + '\n'
            case 'GrainContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_grain_join not in join:
                    join += spot_grain_join + '\n'
                if grain_context_join not in join:
                    join += grain_context_join + '\n'
            case 'GPSLocations':
                if gps_sample_join not in join:
                    join += gps_sample_join + '\n'
                if gps_sample_left_joins not in join:
                    join += gps_sample_left_joins + '\n'
            case 'Instruments':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_instruments_join not in join:
                    join += upb_instruments_join + '\n'
            case 'References' | '"References"':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'ReferenceView':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
            case 'Regions':
                if region_join not in join:
                    join += region_join + '\n'
            case 'UPbRejectionReasons':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_rejection_reason_join not in join:
                    join += upb_rejection_reason_join + '\n'
            case 'GeoChemRejectionReasons':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_rejection_reasons_join not in join:
                    join += geochem_rejection_reasons_join + '\n'
            case 'RockTypes':
                if rock_type_join not in join:
                    join += rock_type_join + '\n'
            case 'SampleAges':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += default_sample_age_join + '\n'
            case 'SampleAgeConstraints':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_constraint_join not in join:
                    join += sampleage_age_constraint_join + '\n'
            case 'SampleAgeInterpretations':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_interpretation_join not in join:
                    join += sampleage_age_interpretation_join + '\n'
            case 'SampleAgeReferences':
                if default_sample_age_join not in join and sample_sampleage_join not in join:
                    join += sample_sampleage_join + '\n'
                if sampleage_age_reference_join not in join:
                    join += sampleage_age_reference_join + '\n'
            case 'SampleContexts':
                if sample_context_join not in join:
                    join += sample_context_join + '\n'
            case 'SamplingMethods':
                if sampling_method_join not in join:
                    join += sampling_method_join + '\n'
            case 'Settings':
                if setting_join not in join:
                    join += setting_join + '\n'
            case 'Spots':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
            case 'SpotCompositions':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_composition_join not in join:
                    join += spot_composition_join + '\n'
            case 'SpotContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_context_join not in join:
                    join += spot_context_join + '\n'
            case 'UPbAgeInterpretations':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_age_interpretation_join not in join:
                    join += upb_age_interpretation_join + '\n'
            case 'UPbAnalyses':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
            case 'UPbAnalysisContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_context_join not in join:
                    join += upb_context_join + '\n'
            case 'UPbAnalysisMethods':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_method_join not in join:
                    join += upb_method_join + '\n'
            case 'UPbReferences':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_upb_analysis_join not in join:
                    join += spot_upb_analysis_join + '\n'
                if upb_reference_join not in join:
                    join += upb_reference_join + '\n'
            case 'GeoChemicalAnalyses':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
            case 'GeoChemicalAnalysisContexts':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_contexts_join not in join:
                    join += geochem_contexts_join + '\n'
            case 'GeoChemicalMethods':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_method_join not in join:
                    join += geochem_method_join + '\n'
            case 'GeoChemReferences':
                if sample_aliquot_join not in join:
                    join += sample_aliquot_join + '\n'
                if aliquot_spot_join not in join:
                    join += aliquot_spot_join + '\n'
                if spot_geochem_analysis_join not in join:
                    join += spot_geochem_analysis_join + '\n'
                if geochem_reference_join not in join:
                    join += geochem_reference_join + '\n'
            case 'Units':
                if unit_join not in join:
                    join += unit_join + '\n'
            case 'Samples':
                pass
    return join