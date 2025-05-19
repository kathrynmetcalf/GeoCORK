from Schema.GeoCORKTable import GeoCORKTable, TableAttributes

# ----------------------------------------------------------------------------------------------- #
# |     Internal Tables                                                                         |
# ----------------------------------------------------------------------------------------------- #

About = GeoCORKTable(table_name='About', table_type=TableType.INTERNAL, static_table=True
                        attributes=attributes)

FilterGroups = GeoCORKTable(table_name='FilterGroups', table_type=TableType.INTERNAL,
                            attributes=[TableAttributes('FilterGroupID', 'INTEGER', True)])

# ----------------------------------------------------------------------------------------------- #
# |     Internal Static Unit/Format/Conversion Tables                                           |
# ----------------------------------------------------------------------------------------------- #
AgeUnits = GeoCORKTable(table_name='AgeUnits', table_type=TableType.INTERNAL, static_table=True,
                        contains_foreign_keys=True
                        as_table_name=['UPbAgeUnits']
                        attributes=attributes)

AgeUnitConversions = GeoCORKTable(table_name='AgeUnitConversions', table_type=TableType.INTERNAL, static_table=True,
                                  contains_foreign_keys=True,
                        attributes=attributes)

DirectionUnits = GeoCORKTable(table_name='DirectionUnits', table_type=TableType.INTERNAL, static_table=True, contains_foreign_keys=True,
                              as_table_name=['SampleLatDirections', 'SampleLonDirections', 'ColumnLatDirections', 'ColumnLonDirections']
                        attributes=attributes)

DistanceUnits = GeoCORKTable(table_name='DistanceUnits', table_type=TableType.INTERNAL, static_table=True, contains_foreign_keys=True,
                             as_table_name=['SampleElevationUnits', 'ColumnElevationUnits', 'ColumnHeightDepthUnits', 'SpotSizeUnits']
                        attributes=attributes)

DistanceUnitConversions = GeoCORKTable(table_name='DistanceUnitConversions', table_type=TableType.INTERNAL, static_table=True,
                                       contains_foreign_keys=True,
                        attributes=attributes)

ErrorFormats = GeoCORKTable(table_name='ErrorFormats', table_type=TableType.INTERNAL, static_table=True,
                            contains_foreign_keys=True,
                            as_table_name=['DirectAgeErrorFormats', 'RatioErrorFormats', 'AgeErrorFormats']
                        attributes=attributes)

ErrorFormatConversions = GeoCORKTable(table_name='ErrorFormatConversions', table_type=TableType.INTERNAL,
                                      static_table=True, contains_foreign_keys=True,
                                      attributes=attributes)

ConcordanceFormats = GeoCORKTable(table_name='ConcordanceFormats', table_type=TableType.INTERNAL, static_table=True,
                                  contains_foreign_keys=True,
                        attributes=attributes)

ConcordanceFormatConversions = GeoCORKTable(table_name='ConcordanceFormatConversions', table_type=TableType.INTERNAL, static_table=True,
                                            contains_foreign_keys=True,
                        attributes=attributes)

GPSFormatConversions = GeoCORKTable(table_name='GPSFormatConversions', table_type=TableType.TREE, static_table=True,
                                    contains_foreign_keys=True,
                              attributes=attributes)

GPSFormats = GeoCORKTable(table_name='GPSFormats', table_type=TableType.INTERNAL, static_table=True,
                          contains_foreign_keys=True,
                          as_table_name=['ColumnGPSFormats'],
                          attributes=attributes)

# ----------------------------------------------------------------------------------------------- #
# |         Tables Used In Other Tables (Child Tables)                                          |
# ----------------------------------------------------------------------------------------------- #

GPSLocations = GeoCORKTable(table_name='GPSLocations', table_type=TableType.TREE,
                            user_viewable=True, contains_foreign_keys=True, as_table_name=['ColumnGPS'],
                            attributes=attributes)

Instruments = GeoCORKTable(table_name='Instruments', attributes=attributes, table_type=TableType.TREE,
                           user_viewable=True, conditionally_editable=False, static_table=False,
                           contains_foreign_keys=False, as_table_name='RockTypes',
                           bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                           bridge_from_column='SampleID')

LabFacilities = GeoCORKTable(table_name='LabFacilities', attributes=attributes, table_type=TableType.TREE,
                             user_viewable=True, conditionally_editable=False, static_table=False,
                             contains_foreign_keys=False, as_table_name='RockTypes',
                             bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                             bridge_from_column='SampleID')

RejectionReasons = GeoCORKTable(table_name='RejectionReasons', attributes=attributes, table_type=TableType.TREE,
                                user_viewable=True, conditionally_editable=False, static_table=False,
                                contains_foreign_keys=False, as_table_name='RockTypes',
                                bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                bridge_from_column='SampleID')

References = GeoCORKTable(table_name='References', attributes=attributes, table_type=TableType.TREE,
                          user_viewable=True, conditionally_editable=False, static_table=False,
                          contains_foreign_keys=False, as_table_name='RockTypes',
                          bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                          bridge_from_column='SampleID')

UPbAnalysisContexts = GeoCORKTable(table_name='UPbAnalysisContexts', attributes=attributes, table_type=TableType.TREE,
                                   user_viewable=True, conditionally_editable=False, static_table=False,
                                   contains_foreign_keys=False, as_table_name='RockTypes',
                                   bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                   bridge_from_column='SampleID')

UPbAnalysisMethods = GeoCORKTable(table_name='UPbAnalysisMethods', attributes=attributes, table_type=TableType.TREE,
                                  user_viewable=True, conditionally_editable=False, static_table=False,
                                  contains_foreign_keys=False, as_table_name='RockTypes',
                                  bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                  bridge_from_column='SampleID')

SpotCompositions = GeoCORKTable(table_name='SpotCompositions', attributes=attributes, table_type=TableType.TREE,
                                user_viewable=True, conditionally_editable=False, static_table=False,
                                contains_foreign_keys=False, as_table_name='RockTypes',
                                bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                bridge_from_column='SampleID')

SpotContexts = GeoCORKTable(table_name='SpotContexts', attributes=attributes, table_type=TableType.TREE,
                            user_viewable=True, conditionally_editable=False, static_table=False,
                            contains_foreign_keys=False, as_table_name='RockTypes',
                            bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                            bridge_from_column='SampleID')

AliquotContexts = GeoCORKTable(table_name='AliquotContexts', attributes=attributes, table_type=TableType.TREE,
                               user_viewable=True, conditionally_editable=False, static_table=False,
                               contains_foreign_keys=False, as_table_name='RockTypes',
                               bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                               bridge_from_column='SampleID')

AgeConstraints = GeoCORKTable(table_name='AgeConstraints', attributes=attributes, table_type=TableType.TREE,
                              user_viewable=True, conditionally_editable=False, static_table=False,
                              contains_foreign_keys=False, as_table_name='RockTypes',
                              bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                              bridge_from_column='SampleID')

AgeInterpretations = GeoCORKTable(table_name='AgeInterpretations', attributes=attributes, table_type=TableType.TREE,
                                  user_viewable=True, conditionally_editable=False, static_table=False,
                                  contains_foreign_keys=False, as_table_name='RockTypes',
                                  bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                  bridge_from_column='SampleID')

AgeSignatures = GeoCORKTable(table_name='AgeSignatures', attributes=attributes, table_type=TableType.TREE,
                             user_viewable=True, conditionally_editable=False, static_table=False,
                             contains_foreign_keys=False, as_table_name='RockTypes',
                             bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                             bridge_from_column='SampleID')

Ages = GeoCORKTable(table_name='Ages', table_type=TableType.TREE,
                    user_viewable=True, static_table=True, as_table_name=['OldAge', 'YoungAge'],
                    attributes=attributes)

Columns = GeoCORKTable(table_name='Columns', attributes=attributes, table_type=TableType.TREE,
                       user_viewable=True, conditionally_editable=False, static_table=False,
                       contains_foreign_keys=True, as_table_name='RockTypes',
                       bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                       bridge_from_column='SampleID')

Regions = GeoCORKTable(table_name='Regions', attributes=attributes, table_type=TableType.TREE,
                       user_viewable=True, conditionally_editable=False, static_table=False,
                       contains_foreign_keys=False, as_table_name='RockTypes',
                       bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                       bridge_from_column='SampleID')

RockTypes = GeoCORKTable(table_name='RockTypes', attributes=attributes, table_type=TableType.TREE,
                         user_viewable=True, conditionally_editable=False, static_table=False,
                         contains_foreign_keys=False, as_table_name='RockTypes',
                         bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                         bridge_from_column='SampleID')

SampleAges = GeoCORKTable(table_name='SampleAges', attributes=attributes, table_type=TableType.TREE,
                          user_viewable=True, conditionally_editable=False, static_table=False,
                          contains_foreign_keys=True, as_table_name='RockTypes',
                          bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                          bridge_from_column='SampleID')

SampleContexts = GeoCORKTable(table_name='SampleContexts', attributes=attributes, table_type=TableType.TREE,
                              user_viewable=True, conditionally_editable=False, static_table=False,
                              contains_foreign_keys=False, as_table_name='RockTypes',
                              bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                              bridge_from_column='SampleID')

SamplingMethods = GeoCORKTable(table_name='SamplingMethods', attributes=attributes, table_type=TableType.TREE,
                               user_viewable=True, conditionally_editable=False, static_table=False,
                               contains_foreign_keys=False, as_table_name='RockTypes',
                               bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                               bridge_from_column='SampleID')

Settings = GeoCORKTable(table_name='Settings', attributes=attributes, table_type=TableType.TREE,
                        user_viewable=True, conditionally_editable=False, static_table=False,
                        contains_foreign_keys=False, as_table_name='RockTypes',
                        bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                        bridge_from_column='SampleID')

Units = GeoCORKTable(table_name='Units', attributes=attributes, table_type=TableType.TREE,
                     user_viewable=True, conditionally_editable=False, static_table=False,
                     contains_foreign_keys=False, as_table_name='RockTypes',
                     bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                     bridge_from_column='SampleID')

Samples = GeoCORKTable(table_name='Samples', table_type=TableType.TABLE,
                       user_viewable=True, conditionally_editable=False, static_table=False,
                       contains_foreign_keys=True, as_table_name='RockTypes',
                       bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                       bridge_from_column='SampleID',
                       attributes=attributes)

Aliquots = GeoCORKTable(table_name='Aliquots', table_type=TableType.TREE,
                        user_viewable=True, conditionally_editable=False, static_table=False,
                        contains_foreign_keys=True, as_table_name='RockTypes',
                        bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                        bridge_from_column='SampleID',
                        attributes=attributes)

Spots = GeoCORKTable(table_name='Spots', table_type=TableType.TABLE,
                     user_viewable=True, conditionally_editable=False, static_table=False,
                     contains_foreign_keys=True, as_table_name='RockTypes',
                     bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                     bridge_from_column='SampleID',
                     attributes=attributes)

UPbAnalyses = GeoCORKTable(table_name='UPbAnalyses', table_type=TableType.TABLE,
                           user_viewable=True, conditionally_editable=False, static_table=False,
                           contains_foreign_keys=True,
                           bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                           bridge_from_column='SampleID',
                           attributes=attributes)

# ----------------------------------------------------------------------------------------------- #
# |     Many-To-Many Tables Using Tables Previously Created                                     |
# ----------------------------------------------------------------------------------------------- #

SampleAges_AgeConstraints = GeoCORKTable(table_name='SampleAges_AgeConstraints',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

SampleAges_AgeInterpretations = GeoCORKTable(table_name='SampleAges_AgeInterpretations',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

SampleAges_References = GeoCORKTable(table_name='SampleAges_References',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_AgeSignatures = GeoCORKTable(table_name='Samples_AgeSignatures',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_Regions = GeoCORKTable(table_name='Samples_Regions',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_RockTypes = GeoCORKTable(table_name='Samples_RockTypes',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_SampleAges = GeoCORKTable(table_name='Samples_SampleAges',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_SampleContexts = GeoCORKTable(table_name='Samples_SampleContexts',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_SamplingMethods = GeoCORKTable(table_name='Samples_SamplingMethods',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_Settings = GeoCORKTable(table_name='Samples_Settings',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Samples_Units = GeoCORKTable(table_name='Samples_Units',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Aliquots_AliquotContexts = GeoCORKTable(table_name='Aliquots_AliquotContexts',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

Spots_SpotContexts = GeoCORKTable(table_name='Spots_SpotContexts',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

UPbAnalyses_UPbRejectionReasons = GeoCORKTable(table_name='UPbAnalyses_UPbRejectionReasons',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)

UPbAnalyses_UPbAnalysisContexts = GeoCORKTable(table_name='UPbAnalyses_UPbAnalysisContexts',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=attributes)



class GeoCORKSchema()
    def __init__(self):



