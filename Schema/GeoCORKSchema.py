from Schema.GeoCORKTable import GeoCORKTable, TableAttributes, TableType

# ----------------------------------------------------------------------------------------------- #
# |     Internal Tables                                                                         |
# ----------------------------------------------------------------------------------------------- #

About = GeoCORKTable(table_name='About', table_type=TableType.INTERNAL, static_table=True,
                     attributes=[
                         TableAttributes('AboutID', 'INTEGER', primary_key=True),
                         TableAttributes('Name', 'TEXT', not_null=True, not_empty=True),
                         TableAttributes('Authors', 'TEXT', not_null=True, not_empty=True),
                         TableAttributes('Citation', 'TEXT', not_null=True, not_empty=True),
                         TableAttributes('ReferenceLink', 'TEXT', not_null=True, not_empty=True),
                         TableAttributes('Version', 'TEXT', not_null=True, not_empty=True),
                         TableAttributes('Description', 'TEXT'),
                         TableAttributes('CreatedBy', 'TEXT', not_null=True, not_empty=True)
                     ])

FilterGroups = GeoCORKTable(table_name='FilterGroups', table_type=TableType.INTERNAL,
                            attributes=[
                                TableAttributes('FilterGroupID', 'INTEGER', primary_key=True),
                                TableAttributes('FilterGroupName', 'TEXT', not_null=True, not_empty=True),
                                TableAttributes('SQLQuery', 'TEXT'),
                                TableAttributes('DefaultColor', 'TEXT'),
                                TableAttributes('FilterGroupDescription', 'TEXT')])

# ----------------------------------------------------------------------------------------------- #
# |     Internal Static Unit/Format/Conversion Tables                                           |
# ----------------------------------------------------------------------------------------------- #
AgeUnits = GeoCORKTable(table_name='AgeUnits', table_type=TableType.INTERNAL, static_table=True,
                        contains_foreign_keys=True,
                        as_table_name=['UPbAgeUnits'],
                        attributes=[
                            TableAttributes('AgeUnitID', 'INTEGER', primary_key=True),
                            TableAttributes('AgeUnitName', 'TEXT', not_null=True, not_empty=True),
                            TableAttributes('AgeUnitAbbreviation', 'TEXT', not_null=True, not_empty=True),
                            TableAttributes('AgeUnitDescription', 'TEXT')])

AgeUnitConversions = GeoCORKTable(table_name='AgeUnitConversions', table_type=TableType.INTERNAL, static_table=True,
                                  contains_foreign_keys=True,
                                  attributes=[
                                      TableAttributes('FromAgeUnitID', 'INTEGER', not_null=True, not_empty=True),
                                      TableAttributes('ToAgeUnitID', 'INTEGER', not_null=True, not_empty=True),
                                      TableAttributes('AgeUnitConversionCalculation', 'TEXT', not_null=True,
                                                      not_empty=True)])

ConcordanceFormats = GeoCORKTable(table_name='ConcordanceFormats', table_type=TableType.INTERNAL, static_table=True,
                                  contains_foreign_keys=True,
                                  attributes=[TableAttributes('ConcordanceFormatID', 'INTEGER', primary_key=True),
                                              TableAttributes('ConcordanceFormatName', 'TEXT', not_null=True,
                                                              not_empty=True),
                                              TableAttributes('ConcordanceFormatAbbreviation', 'TEXT', not_null=True,
                                                              not_empty=True),
                                              TableAttributes('ConcordanceFormatDescription', 'TEXT')])

ConcordanceFormatConversions = GeoCORKTable(table_name='ConcordanceFormatConversions', table_type=TableType.INTERNAL,
                                            static_table=True,
                                            contains_foreign_keys=True,
                                            attributes=[
                                                TableAttributes('FromConcordanceFormatID', 'INTEGER', not_null=True,
                                                                not_empty=True),
                                                TableAttributes('ToConcordanceFormatID', 'INTEGER', not_null=True,
                                                                not_empty=True),
                                                TableAttributes('ConcordanceFormatConversionCalculation', 'TEXT',
                                                                not_null=True, not_empty=True)])

DirectionUnits = GeoCORKTable(table_name='DirectionUnits', table_type=TableType.INTERNAL, static_table=True,
                              contains_foreign_keys=True,
                              as_table_name=['SampleLatDirections', 'SampleLonDirections', 'ColumnLatDirections',
                                             'ColumnLonDirections'],
                              attributes=[
                                  TableAttributes('DirectionUnitID', 'INTEGER', primary_key=True),
                                  TableAttributes('DirectionUnitName', 'TEXT', not_null=True, not_empty=True),
                                  TableAttributes('DirectionUnitAbbreviation', 'TEXT', not_null=True, not_empty=True),
                                  TableAttributes('DirectionUnitDescription', 'TEXT')])

DistanceUnits = GeoCORKTable(table_name='DistanceUnits', table_type=TableType.INTERNAL, static_table=True,
                             contains_foreign_keys=True,
                             as_table_name=['SampleElevationUnits', 'ColumnElevationUnits', 'ColumnHeightDepthUnits',
                                            'SpotSizeUnits'],
                             attributes=[TableAttributes('DistanceUnitID', 'INTEGER', primary_key=True),
                                         TableAttributes('DistanceUnitName', 'TEXT', not_null=True, not_empty=True),
                                         TableAttributes('DistanceUnitAbbreviation', 'TEXT', not_null=True,
                                                         not_empty=True),
                                         TableAttributes('DistanceUnitDescription', 'TEXT')])

DistanceUnitConversions = GeoCORKTable(table_name='DistanceUnitConversions', table_type=TableType.INTERNAL,
                                       static_table=True,
                                       contains_foreign_keys=True,
                                       attributes=[TableAttributes('FromDistanceUnitID', 'INTEGER', not_null=True,
                                                                   not_empty=True),
                                                   TableAttributes('ToDistanceUnitID', 'INTEGER', not_null=True,
                                                                   not_empty=True),
                                                   TableAttributes('DistanceUnitConversionCalculation', 'TEXT',
                                                                   not_null=True, not_empty=True)])

ErrorFormats = GeoCORKTable(table_name='ErrorFormats', table_type=TableType.INTERNAL, static_table=True,
                            contains_foreign_keys=True,
                            as_table_name=['DirectAgeErrorFormats', 'RatioErrorFormats', 'AgeErrorFormats'],
                            attributes=[TableAttributes('ErrorFormatID', 'INTEGER', primary_key=True),
                                        TableAttributes('ErrorFormatName', 'TEXT', not_null=True, not_empty=True),
                                        TableAttributes('ErrorFormatAbbreviation', 'TEXT', not_null=True,
                                                        not_empty=True),
                                        TableAttributes('ErrorFormatDescription', 'TEXT')])

ErrorFormatConversions = GeoCORKTable(table_name='ErrorFormatConversions', table_type=TableType.INTERNAL,
                                      static_table=True, contains_foreign_keys=True,
                                      attributes=[TableAttributes('FromErrorFormatID', 'INTEGER', not_null=True,
                                                                  not_empty=True),
                                                  TableAttributes('ToErrorFormatID', 'INTEGER', not_null=True,
                                                                  not_empty=True),
                                                  TableAttributes('ErrorFormatConversionCalculation', 'TEXT',
                                                                  not_null=True, not_empty=True)])

GPSFormatConversions = GeoCORKTable(table_name='GPSFormatConversions', table_type=TableType.TREE, static_table=True,
                                    contains_foreign_keys=True,
                                    attributes=[
                                        TableAttributes('FromGPSFormatID', 'INTEGER', not_null=True, not_empty=True),
                                        TableAttributes('ToGPSFormatID', 'INTEGER', not_null=True, not_empty=True),
                                        TableAttributes('GPSFormatConversionCalculation', 'TEXT', not_null=True,
                                                        not_empty=True)])

GPSFormats = GeoCORKTable(table_name='GPSFormats', table_type=TableType.INTERNAL, static_table=True,
                          contains_foreign_keys=True,
                          as_table_name=['ColumnGPSFormats'],
                          attributes=[TableAttributes('GPSFormatID', 'INTEGER', primary_key=True),
                                      TableAttributes('GPSFormatName', 'TEXT', not_null=True, not_empty=True),
                                      TableAttributes('GPSFormatAbbreviation', 'TEXT', not_null=True, not_empty=True),
                                      TableAttributes('GPSFormatDescription', 'TEXT')])

# ----------------------------------------------------------------------------------------------- #
#          Tables Used In Other Tables TREES ONLY (Child Tables)
# ----------------------------------------------------------------------------------------------- #

Ages = GeoCORKTable(table_name='Ages', table_type=TableType.TREE,
                    user_viewable=True, static_table=True, as_table_name=['OldAge', 'YoungAge'],
                    attributes=[TableAttributes('AgeID', 'INTEGER', True),
                                TableAttributes('ParentAgeID', 'INTEGER'),
                                TableAttributes('AgeParentRow', 'INTEGER'),
                                TableAttributes('AgeName', 'TEXT', not_null=True, not_empty=True),
                                TableAttributes('OldestAge', 'REAL'),
                                TableAttributes('YoungestAge', 'REAL')])
AgeConstraints = GeoCORKTable(table_name='AgeConstraints', table_type=TableType.TREE,
                              user_viewable=True, conditionally_editable=False, static_table=False,
                              contains_foreign_keys=False, as_table_name='RockTypes',
                              bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                              bridge_from_column='SampleID',
                              attributes=[TableAttributes('AgeConstraintID', 'INTEGER', True),
                                          TableAttributes('ParentAgeConstraintID', 'INTEGER'),
                                          TableAttributes('AgeConstraintParentRow', 'INTEGER'),
                                          TableAttributes('AgeConstraintName', 'TEXT', not_null=True, not_empty=True),
                                          TableAttributes('AgeConstraintDescription', 'TEXT')])
AgeInterpretations = GeoCORKTable(table_name='AgeInterpretations', table_type=TableType.TREE,
                                  user_viewable=True, conditionally_editable=False, static_table=False,
                                  contains_foreign_keys=False, as_table_name='RockTypes',
                                  bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                  bridge_from_column='SampleID',
                                  attributes=[TableAttributes('AgeInterpretationID', 'INTEGER', True),
                                              TableAttributes('ParentAgeInterpretationID', 'INTEGER'),
                                              TableAttributes('AgeInterpretationParentRow', 'INTEGER'),
                                              TableAttributes('AgeInterpretationName', 'TEXT', not_null=True,
                                                              not_empty=True),
                                              TableAttributes('AgeInterpretationDescription', 'TEXT')])

AgeSignatures = GeoCORKTable(table_name='AgeSignatures', table_type=TableType.TREE,
                             user_viewable=True, conditionally_editable=False, static_table=False,
                             contains_foreign_keys=False, as_table_name='RockTypes',
                             bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                             bridge_from_column='SampleID',
                             attributes=[TableAttributes('AgeSignatureID', 'INTEGER', True),
                                         TableAttributes('ParentAgeSignatureID', 'INTEGER'),
                                         TableAttributes('AgeSignatureParentRow', 'INTEGER'),
                                         TableAttributes('AgeSignatureName', 'TEXT', not_null=True, not_empty=True),
                                         TableAttributes('AgeSignatureDescription', 'TEXT')])

AliquotContexts = GeoCORKTable(table_name='AliquotContexts', table_type=TableType.TREE,
                               user_viewable=True, conditionally_editable=False, static_table=False,
                               contains_foreign_keys=False, as_table_name='RockTypes',
                               bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                               bridge_from_column='SampleID',
                               attributes=[TableAttributes('AliquotContextID', 'INTEGER', True),
                                           TableAttributes('ParentAliquotContextID', 'INTEGER'),
                                           TableAttributes('AliquotContextParentRow', 'INTEGER'),
                                           TableAttributes('AliquotContextName', 'TEXT', not_null=True, not_empty=True),
                                           TableAttributes('AliquotContextDescription', 'TEXT')])
Columns = GeoCORKTable(table_name='Columns', table_type=TableType.TREE,
                       user_viewable=True, conditionally_editable=False, static_table=False,
                       contains_foreign_keys=True, as_table_name='RockTypes',
                       bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                       bridge_from_column='SampleID',
                       attributes=[TableAttributes('ColumnID', 'INTEGER', True),
                                   TableAttributes('ColumnName', 'TEXT', not_null=True, not_empty=True),
                                   TableAttributes('ColumnTotalHeightDepth', 'REAL'),
                                   TableAttributes('ColumnTotalHeightDepthUnitID', 'INTEGER'),
                                   TableAttributes('ColumnBaseGPSID', 'INTEGER'),
                                   TableAttributes('ColumnDescription', 'TEXT')])

GPSLocations = GeoCORKTable(table_name='GPSLocations', table_type=TableType.TREE,
                            user_viewable=True, contains_foreign_keys=True, as_table_name=['ColumnGPS'],
                            attributes=[TableAttributes('GPSLocationID', 'INTEGER', primary_key=True),
                                        TableAttributes('GPSLocationConverted', 'TEXT'),
                                        TableAttributes('GPSLocationDisplay', 'AS',
                                                        as_case="""CASE WHEN GPSFormatID = 1 THEN GPSLatDeg || "°, " ||  GPSLonDeg || "° " WHEN GPSFormatID = 2 THEN GPSLatDeg || "° " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonDirectionID WHEN GPSFormatID = 3 THEN GPSLatDeg || "° " || GPSLatMin || "', " || GPSLonDeg || "° " || GPSLonMin || "'" WHEN GPSFormatID = 4 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonDirectionID WHEN GPSFormatID = 5 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'', " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "''" WHEN GPSFormatID = 6 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "'' " || GPSLonDirectionID WHEN GPSFormatID = 7 THEN GPSUTMZone || ", " || GPSUTME || "m E, " || GPSUTMN || "m N" ENDCASE WHEN GPSFormatID = 1 THEN GPSLatDeg || "°, " ||  GPSLonDeg || "° " WHEN GPSFormatID = 2 THEN GPSLatDeg || "° " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonDirectionID WHEN GPSFormatID = 3 THEN GPSLatDeg || "° " || GPSLatMin || "', " || GPSLonDeg || "° " || GPSLonMin || "'" WHEN GPSFormatID = 4 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonDirectionID WHEN GPSFormatID = 5 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'', " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "''" WHEN GPSFormatID = 6 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "'' " || GPSLonDirectionID WHEN GPSFormatID = 7 THEN GPSUTMZone || ", " || GPSUTME || "m E, " || GPSUTMN || "m N" END"""),
                                        TableAttributes('GPSLatDeg', 'REAL'),
                                        TableAttributes('GPSLatMin', 'REAL'),
                                        TableAttributes('GPSLatSec', 'REAL'),
                                        TableAttributes('GPSLatDirectionID', 'INTEGER'),
                                        TableAttributes('GPSLonDeg', 'REAL'),
                                        TableAttributes('GPSLonMin', 'REAL'),
                                        TableAttributes('GPSLonSec', 'REAL'),
                                        TableAttributes('GPSLonDirectionID', 'INTEGER'),
                                        TableAttributes('GPSUTMZone', 'TEXT'),
                                        TableAttributes('GPSUTMN', 'REAL'),
                                        TableAttributes('GPSUTME', 'REAL'),
                                        TableAttributes('GPSFormatID', 'INTEGER'),
                                        TableAttributes('GPSElev', 'REAL'),
                                        TableAttributes('GPSElevError', 'REAL'),
                                        TableAttributes('GPSElevUnitID', 'INTEGER')])

Instruments = GeoCORKTable(table_name='Instruments', table_type=TableType.TREE,
                           user_viewable=True, conditionally_editable=False, static_table=False,
                           contains_foreign_keys=False, as_table_name='RockTypes',
                           bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                           bridge_from_column='SampleID',
                           attributes=[TableAttributes('InstrumentID', 'INTEGER', primary_key=True),
                                       TableAttributes('InstrumentName', 'TEXT', not_null=True, not_empty=True),
                                       TableAttributes('InstrumentDescription', 'TEXT'), ])

LabFacilities = GeoCORKTable(table_name='LabFacilities', table_type=TableType.TREE,
                             user_viewable=True, conditionally_editable=False, static_table=False,
                             contains_foreign_keys=False, as_table_name='RockTypes',
                             bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                             bridge_from_column='SampleID',
                             attributes=[TableAttributes('LabFacilityID', 'INTEGER', primary_key=True),
                                         TableAttributes('LabFacilityName', 'TEXT', not_null=True, not_empty=True),
                                         TableAttributes('LabFacilityDescription', 'TEXT')])

References = GeoCORKTable(table_name='References', table_type=TableType.TREE,
                          user_viewable=True, conditionally_editable=False, static_table=False,
                          contains_foreign_keys=False, as_table_name='RockTypes',
                          bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                          bridge_from_column='SampleID',
                          attributes=[TableAttributes('ReferenceID', 'INTEGER', True),
                                      TableAttributes('Authors', 'TEXT'),
                                      TableAttributes('Year', 'INTEGER'),
                                      TableAttributes('Title', 'TEXT'),
                                      TableAttributes('Source', 'TEXT'),
                                      TableAttributes('DOI', 'TEXT')])

RejectionReasons = GeoCORKTable(table_name='RejectionReasons', table_type=TableType.TREE,
                                user_viewable=True, conditionally_editable=False, static_table=False,
                                contains_foreign_keys=False, as_table_name='RockTypes',
                                bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                bridge_from_column='SampleID',
                                attributes=[TableAttributes('RejectionReasonID', 'INTEGER', True),
                                            TableAttributes('RejectionReasonName', 'TEXT', not_null=True,
                                                            not_empty=True),
                                            TableAttributes('RejectionReasonDescription', 'TEXT')])

SpotContexts = GeoCORKTable(table_name='SpotContexts', table_type=TableType.TREE,
                            user_viewable=True, conditionally_editable=False, static_table=False,
                            contains_foreign_keys=False, as_table_name='RockTypes',
                            bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                            bridge_from_column='SampleID',
                            attributes=[TableAttributes('SpotContextID', 'INTEGER', True),
                                        TableAttributes('ParentSpotContextID', 'INTEGER'),
                                        TableAttributes('SpotContextParentRow', 'INTEGER'),
                                        TableAttributes('SpotContextName', 'TEXT', not_null=True, not_empty=True),
                                        TableAttributes('SpotContextDescription', 'TEXT')])

SpotCompositions = GeoCORKTable(table_name='SpotCompositions', table_type=TableType.TREE,
                                user_viewable=True, conditionally_editable=False, static_table=False,
                                contains_foreign_keys=False, as_table_name='RockTypes',
                                bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                bridge_from_column='SampleID',
                                attributes=[TableAttributes('SpotCompositionID', 'INTEGER', True),
                                            TableAttributes('ParentSpotCompositionID', 'INTEGER'),
                                            TableAttributes('SpotCompositionParentRow', 'INTEGER'),
                                            TableAttributes('SpotCompositionName', 'TEXT', not_null=True,
                                                            not_empty=True),
                                            TableAttributes('SpotCompositionDescription', 'TEXT')])

Regions = GeoCORKTable(table_name='Regions', table_type=TableType.TREE,
                       user_viewable=True, conditionally_editable=False, static_table=False,
                       contains_foreign_keys=False, as_table_name='RockTypes',
                       bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                       bridge_from_column='SampleID',
                       attributes=[TableAttributes('RegionID', 'INTEGER', True),
                                   TableAttributes('ParentRegionID', 'INTEGER'),
                                   TableAttributes('RegionParentRow', 'INTEGER'),
                                   TableAttributes('RegionName', 'TEXT', not_null=True, not_empty=True),
                                   TableAttributes('RegionDescription', 'TEXT')])

RockTypes = GeoCORKTable(table_name='RockTypes', table_type=TableType.TREE,
                         user_viewable=True, conditionally_editable=False, static_table=False,
                         contains_foreign_keys=False, as_table_name='RockTypes',
                         bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                         bridge_from_column='SampleID',
                         attributes=[TableAttributes('RockTypeID', 'INTEGER', True),
                                     TableAttributes('ParentRockTypeID', 'INTEGER'),
                                     TableAttributes('RockTypeParentRow', 'INTEGER'),
                                     TableAttributes('RockTypeName', 'TEXT', not_null=True, not_empty=True),
                                     TableAttributes('RockTypeDescription', 'TEXT')])

SampleAges = GeoCORKTable(table_name='SampleAges', table_type=TableType.TREE,
                          user_viewable=True, conditionally_editable=False, static_table=False,
                          contains_foreign_keys=True, as_table_name='RockTypes',
                          bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                          bridge_from_column='SampleID',
                          attributes=[TableAttributes('SampleAgeID', 'INTEGER', True),
                                      TableAttributes('DirectAge', 'REAL'),
                                      TableAttributes('DirectAgeError', 'REAL'),
                                      TableAttributes('DirectAgeErrorFormatID', 'INTEGER'),
                                      TableAttributes('OldestDirectAge', 'REAL'),
                                      TableAttributes('YoungestDirectAge', 'REAL'),
                                      TableAttributes('DirectAgeUnitID', 'INTEGER'),
                                      TableAttributes('OldestAgeID', 'INTEGER'),
                                      TableAttributes('YoungestAgeID', 'INTEGER'),
                                      TableAttributes('SampleAgeDescription', 'TEXT')])

SampleContexts = GeoCORKTable(table_name='SampleContexts', table_type=TableType.TREE,
                              user_viewable=True, conditionally_editable=False, static_table=False,
                              contains_foreign_keys=False, as_table_name='RockTypes',
                              bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                              bridge_from_column='SampleID',
                              attributes=[TableAttributes('SampleContextID', 'INTEGER', True),
                                          TableAttributes('ParentSampleContextID', 'INTEGER'),
                                          TableAttributes('SampleContextParentRow', 'INTEGER', not_null=True),
                                          TableAttributes('SampleContextName', 'TEXT', not_null=True, not_empty=True),
                                          TableAttributes('SampleContextDescription', 'TEXT')])

SamplingMethods = GeoCORKTable(table_name='SamplingMethods', table_type=TableType.TREE,
                               user_viewable=True, conditionally_editable=False, static_table=False,
                               contains_foreign_keys=False, as_table_name='RockTypes',
                               bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                               bridge_from_column='SampleID',
                               attributes=[TableAttributes('SamplingMethodID', 'INTEGER', True),
                                           TableAttributes('ParentSamplingMethodID', 'INTEGER'),
                                           TableAttributes('SamplingMethodParentRow', 'INTEGER'),
                                           TableAttributes('SamplingMethodName', 'TEXT', not_null=True, not_empty=True),
                                           TableAttributes('SamplingMethodDescription', 'TEXT')])

Settings = GeoCORKTable(table_name='Settings', table_type=TableType.TREE,
                        user_viewable=True, conditionally_editable=False, static_table=False,
                        contains_foreign_keys=False, as_table_name='RockTypes',
                        bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                        bridge_from_column='SampleID',
                        attributes=[TableAttributes('SettingID', 'INTEGER', True),
                                    TableAttributes('ParentSettingID', 'INTEGER'),
                                    TableAttributes('SettingParentRow', 'INTEGER'),
                                    TableAttributes('SettingName', 'TEXT', not_null=True, not_empty=True),
                                    TableAttributes('SettingDescription', 'TEXT')])

Units = GeoCORKTable(table_name='Units', table_type=TableType.TREE,
                     user_viewable=True, conditionally_editable=False, static_table=False,
                     contains_foreign_keys=False, as_table_name='RockTypes',
                     bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                     bridge_from_column='SampleID',
                     attributes=[TableAttributes('UnitID', 'INTEGER', True),
                                 TableAttributes('ParentUnitID', 'INTEGER'),
                                 TableAttributes('UnitParentRow', 'INTEGER'),
                                 TableAttributes('UnitName', 'TEXT', not_null=True, not_empty=True),
                                 TableAttributes('UnitDescription', 'TEXT')])

UPbAnalysisContexts = GeoCORKTable(table_name='UPbAnalysisContexts', table_type=TableType.TREE,
                                   user_viewable=True, conditionally_editable=False, static_table=False,
                                   contains_foreign_keys=False, as_table_name='RockTypes',
                                   bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                   bridge_from_column='SampleID',
                                   attributes=[TableAttributes('UPbAnalysisContextID', 'INTEGER', True),
                                               TableAttributes('UPbAnalysisContextID', 'INTEGER'),
                                               TableAttributes('UPbAnalysisContextParentRow', 'INTEGER'),
                                               TableAttributes('UPbAnalysisContextName', 'TEXT', not_null=True,
                                                               not_empty=True),
                                               TableAttributes('UPbAnalysisContextDescription', 'TEXT')])

UPbAnalysisMethods = GeoCORKTable(table_name='UPbAnalysisMethods', table_type=TableType.TREE,
                                  user_viewable=True, conditionally_editable=False, static_table=False,
                                  contains_foreign_keys=False, as_table_name='RockTypes',
                                  bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                  bridge_from_column='SampleID',
                                  attributes=[TableAttributes('UPbAnalysisMethodID', 'INTEGER', True),
                                              TableAttributes('ParentUPbAnalysisMethodID', 'INTEGER'),
                                              TableAttributes('UPbAnalysisMethodParentRow', 'INTEGER'),
                                              TableAttributes('UPbAnalysisMethodName', 'TEXT', not_null=True,
                                                              not_empty=True),
                                              TableAttributes('UPbAnalysisMethodDescription', 'TEXT')])

# ----------------------------------------------------------------------------------------------- #
#          Main Data Tables for Samples, Aliquots, Spots, UPb
# ----------------------------------------------------------------------------------------------- #

Samples = GeoCORKTable(table_name='Samples', table_type=TableType.TABLE,
                       user_viewable=True, conditionally_editable=False, static_table=False,
                       contains_foreign_keys=True, as_table_name='RockTypes',
                       bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                       bridge_from_column='SampleID',
                       attributes=[TableAttributes('SampleID', 'INTEGER', True),
                                   TableAttributes('SampleName', 'TEXT', not_null=True, not_empty=True),
                                   TableAttributes('SampleIGSN', 'TEXT'),
                                   TableAttributes('SampleGPSLocationID', 'INTEGER'),
                                   TableAttributes('SampleColumnID', 'INTEGER'),
                                   TableAttributes('HeightDepth', 'REAL'),
                                   TableAttributes('HeightDepthError', 'REAL'),
                                   TableAttributes('HeightDepthUnitID', 'INTEGER'),
                                   TableAttributes('DefaultSampleAgeID', 'INTEGER'),
                                   TableAttributes('SampleDescription', 'TEXT')])

Aliquots = GeoCORKTable(table_name='Aliquots', table_type=TableType.TREE,
                        user_viewable=True, conditionally_editable=False, static_table=False,
                        contains_foreign_keys=True, as_table_name='RockTypes',
                        bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                        bridge_from_column='SampleID',
                        attributes=[TableAttributes('AliquotID', 'INTEGER', True),
                                    TableAttributes('ParentAliquotID', 'INTEGER'),
                                    TableAttributes('AliquotParentRow', 'INTEGER'),
                                    TableAttributes('AliquotName', 'TEXT', not_null=True, not_empty=True),
                                    TableAttributes('SampleID', 'INTEGER')])

Spots = GeoCORKTable(table_name='Spots', table_type=TableType.TABLE,
                     user_viewable=True, conditionally_editable=False, static_table=False,
                     contains_foreign_keys=True, as_table_name='RockTypes',
                     bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                     bridge_from_column='SampleID',
                     attributes=[TableAttributes('SpotID', 'INTEGER', True),
                                 TableAttributes('SpotName', 'TEXT', not_null=True, not_empty=True),
                                 TableAttributes('AliquotID', 'INTEGER'),
                                 TableAttributes('SpotCompositionID', 'INTEGER')])

UPbAnalyses = GeoCORKTable(table_name='UPbAnalyses', table_type=TableType.TABLE,
                           user_viewable=True, conditionally_editable=False, static_table=False,
                           contains_foreign_keys=True,
                           bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                           bridge_from_column='SampleID',
                           attributes=[TableAttributes('UPbAnalysisID', 'INTEGER', True),
                                       TableAttributes('SpotID', 'INTEGER', not_null=True),
                                       TableAttributes('ReferenceID', 'INTEGER'),
                                       TableAttributes('LabFacilityID', 'INTEGER'),
                                       TableAttributes('InstrumentID', 'INTEGER'),
                                       TableAttributes('UPbAnalysisMethodID', 'INTEGER'),
                                       TableAttributes('Pb204cps', 'REAL'),
                                       TableAttributes('Pb206cps', 'REAL'),
                                       TableAttributes('Pb207cps', 'REAL'),
                                       TableAttributes('Pb208cps', 'REAL'),
                                       TableAttributes('Pb*cps', 'REAL'),
                                       TableAttributes('Th232cps', 'REAL'),
                                       TableAttributes('U235cps', 'REAL'),
                                       TableAttributes('U238cps', 'REAL'),
                                       TableAttributes('Uppm', 'REAL'),
                                       TableAttributes('Thppm', 'REAL'),
                                       TableAttributes('U/Th', 'REAL'),
                                       TableAttributes('Th/U', 'REAL'),
                                       TableAttributes('CalculatedU/Th', 'AS', not_null=True),
                                       TableAttributes('CalculatedTh/U', 'AS', not_null=True),
                                       TableAttributes('206Pb/207Pb', 'REAL'),
                                       TableAttributes('206Pb/207PbError', 'REAL'),
                                       TableAttributes('207Pb/206Pb', 'REAL'),
                                       TableAttributes('207Pb/206PbError', 'REAL'),
                                       TableAttributes('Calculated206Pb/207Pb', 'AS', not_null=True),
                                       TableAttributes('Calculated207Pb/206Pb', 'AS', not_null=True),
                                       TableAttributes('207Pb/235U', 'REAL'),
                                       TableAttributes('207Pb/235UError', 'REAL'),
                                       TableAttributes('235U/207Pb', 'REAL'),
                                       TableAttributes('235U/207PbError', 'REAL'),
                                       TableAttributes('Calculated207Pb/235U', 'AS', not_null=True),
                                       TableAttributes('Calculated235U/207Pb', 'AS', not_null=True),
                                       TableAttributes('206Pb/238U', 'REAL'),
                                       TableAttributes('206Pb/238UError', 'REAL'),
                                       TableAttributes('238U/206Pb', 'REAL'),
                                       TableAttributes('238U/206PbError', 'REAL'),
                                       TableAttributes('Calculated206Pb/238U', 'AS', not_null=True),
                                       TableAttributes('Calculated238U/206Pb', 'AS', not_null=True),
                                       TableAttributes('208Pb/232Th', 'REAL'),
                                       TableAttributes('208Pb/232ThError', 'REAL'),
                                       TableAttributes('232Th/208Pb', 'REAL'),
                                       TableAttributes('232Th/208PbError', 'REAL'),
                                       TableAttributes('Calculated208Pb/232Th', 'AS', not_null=True),
                                       TableAttributes('Calculated232Th/208Pb', 'AS', not_null=True),
                                       TableAttributes('238U/232Th', 'REAL'),
                                       TableAttributes('238U/232ThError', 'REAL'),
                                       TableAttributes('232Th/238U', 'REAL'),
                                       TableAttributes('232Th/238UError', 'REAL'),
                                       TableAttributes('Calculated238U/232Th', 'AS', not_null=True),
                                       TableAttributes('Calculated232Th/238U', 'AS', not_null=True),
                                       TableAttributes('204Pb/238U', 'REAL'),
                                       TableAttributes('204Pb/238UError', 'REAL'),
                                       TableAttributes('238U/204Pb', 'REAL'),
                                       TableAttributes('238U/204PbError', 'REAL'),
                                       TableAttributes('Calculated204Pb/238U', 'AS', not_null=True),
                                       TableAttributes('Calculated238U/204Pb', 'AS', not_null=True),
                                       TableAttributes('206Pb/204Pb', 'REAL'),
                                       TableAttributes('206Pb/204PbError', 'REAL'),
                                       TableAttributes('204Pb/206Pb', 'REAL'),
                                       TableAttributes('204Pb/206PbError', 'REAL'),
                                       TableAttributes('Calculated206Pb/204Pb', 'AS', not_null=True),
                                       TableAttributes('Calculated204Pb/206Pb', 'AS', not_null=True),
                                       TableAttributes('207Pb/204Pb', 'REAL'),
                                       TableAttributes('207Pb/204PbError', 'REAL'),
                                       TableAttributes('204Pb/207Pb', 'REAL'),
                                       TableAttributes('204Pb/207PbError', 'REAL'),
                                       TableAttributes('Calculated207Pb/204Pb', 'AS', not_null=True),
                                       TableAttributes('Calculated204Pb/207Pb', 'AS', not_null=True),
                                       TableAttributes('208Pb/204Pb', 'REAL'),
                                       TableAttributes('208Pb/204PbError', 'REAL'),
                                       TableAttributes('204Pb/208Pb', 'REAL'),
                                       TableAttributes('204Pb/208PbError', 'REAL'),
                                       TableAttributes('Calculated208Pb/204Pb', 'AS', not_null=True),
                                       TableAttributes('Calculated204Pb/208Pb', 'AS', not_null=True),
                                       TableAttributes('RatioErrorFormatID', 'INTEGER'),
                                       TableAttributes('ErrorCorr/Rho', 'REAL'),
                                       TableAttributes('207Pb/206PbAge', 'REAL'),
                                       TableAttributes('207Pb/206PbAgeError', 'REAL'),
                                       TableAttributes('207Pb/235UAge', 'REAL'),
                                       TableAttributes('207Pb/235UAgeError', 'REAL'),
                                       TableAttributes('206Pb/238UAge', 'REAL'),
                                       TableAttributes('206Pb/238UAgeError', 'REAL'),
                                       TableAttributes('208Pb/232ThAge', 'REAL'),
                                       TableAttributes('208Pb/232ThAgeError', 'REAL'),
                                       TableAttributes('BestAge', 'REAL'),
                                       TableAttributes('BestAgeError', 'REAL'),
                                       TableAttributes('AgeErrorFormatID', 'INTEGER'),
                                       TableAttributes('AgeUnitID', 'INTEGER'),
                                       TableAttributes('AgeInterpretationID', 'INTEGER'),
                                       TableAttributes('Concordance', 'REAL'),
                                       TableAttributes('ConcordanceFormatID', 'INTEGER'),
                                       TableAttributes('SpotSize', 'REAL'),
                                       TableAttributes('SpotSizeUnitID', 'INTEGER'),
                                       TableAttributes('Rejected', 'INTEGER')])

# ----------------------------------------------------------------------------------------------- #
# |     Many-To-Many Tables Using Tables Previously Created                                     |
# ----------------------------------------------------------------------------------------------- #

Aliquots_AliquotContexts = GeoCORKTable(table_name='Aliquots_AliquotContexts',
                                        table_type=TableType.MANYTOMANY,
                                        contains_foreign_keys=True,
                                        attributes=[TableAttributes('AliquotID', 'INTEGER'),
                                                    TableAttributes('AliquotContextID', 'INTEGER')])

SampleAges_AgeConstraints = GeoCORKTable(table_name='SampleAges_AgeConstraints',
                                         table_type=TableType.MANYTOMANY,
                                         contains_foreign_keys=True,
                                         attributes=[TableAttributes('SampleAgeID', 'INTEGER', not_null=True),
                                                     TableAttributes('AgeConstraintID', 'INTEGER', not_null=True)])

SampleAges_AgeInterpretations = GeoCORKTable(table_name='SampleAges_AgeInterpretations',
                                             table_type=TableType.MANYTOMANY,
                                             contains_foreign_keys=True,
                                             attributes=[TableAttributes('SampleAgeID', 'INTEGER', not_null=True),
                                                         TableAttributes('AgeInterpretationID', 'INTEGER',
                                                                         not_null=True)])

SampleAges_References = GeoCORKTable(table_name='SampleAges_References',
                                     table_type=TableType.MANYTOMANY,
                                     contains_foreign_keys=True,
                                     attributes=[TableAttributes('SampleAgeID', 'INTEGER', not_null=True),
                                                 TableAttributes('ReferenceID', 'INTEGER', not_null=True)])

Samples_AgeSignatures = GeoCORKTable(table_name='Samples_AgeSignatures',
                                     table_type=TableType.MANYTOMANY,
                                     contains_foreign_keys=True,
                                     attributes=[TableAttributes('SampleID', 'INTEGER', not_null=True),
                                                 TableAttributes('AgeSignatureID', 'INTEGER', not_null=True)])

Samples_Regions = GeoCORKTable(table_name='Samples_Regions',
                               table_type=TableType.MANYTOMANY,
                               contains_foreign_keys=True,
                               attributes=[TableAttributes('SampleID', 'INTEGER', not_null=True),
                                           TableAttributes('RegionID', 'INTEGER', not_null=True)])

Samples_RockTypes = GeoCORKTable(table_name='Samples_RockTypes',
                                 table_type=TableType.MANYTOMANY,
                                 contains_foreign_keys=True,
                                 attributes=[TableAttributes('SampleID', 'INTEGER'),
                                             TableAttributes('RockTypeID', 'INTEGER')])

Samples_SampleAges = GeoCORKTable(table_name='Samples_SampleAges',
                                  table_type=TableType.MANYTOMANY,
                                  contains_foreign_keys=True,
                                  attributes=[TableAttributes('SampleID', 'INTEGER', not_null=True),
                                              TableAttributes('SampleAgeID', 'INTEGER', not_null=True)])

Samples_SampleContexts = GeoCORKTable(table_name='Samples_SampleContexts',
                                      table_type=TableType.MANYTOMANY,
                                      contains_foreign_keys=True,
                                      attributes=[TableAttributes('SampleID', 'INTEGER', not_null=True),
                                                  TableAttributes('SampleContextID', 'INTEGER', not_null=True)])

Samples_SamplingMethods = GeoCORKTable(table_name='Samples_SamplingMethods',
                                       table_type=TableType.MANYTOMANY,
                                       contains_foreign_keys=True,
                                       attributes=[TableAttributes('SampleID', 'INTEGER', not_null=True),
                                                   TableAttributes('SamplingMethodID', 'INTEGER', not_null=True)])

Samples_Settings = GeoCORKTable(table_name='Samples_Settings',
                                table_type=TableType.MANYTOMANY,
                                contains_foreign_keys=True,
                                attributes=[TableAttributes('SampleID', 'INTEGER', not_null=True),
                                            TableAttributes('SettingID', 'INTEGER', not_null=True)])

Samples_Units = GeoCORKTable(table_name='Samples_Units',
                             table_type=TableType.MANYTOMANY,
                             contains_foreign_keys=True,
                             attributes=[TableAttributes('SampleID', 'INTEGER', not_null=True),
                                         TableAttributes('UnitID', 'INTEGER', not_null=True)])

Spots_SpotContexts = GeoCORKTable(table_name='Spots_SpotContexts',
                                  table_type=TableType.MANYTOMANY,
                                  contains_foreign_keys=True,
                                  attributes=[TableAttributes('SpotID', 'INTEGER', not_null=True),
                                              TableAttributes('SpotContextID', 'INTEGER', not_null=True)])

UPbAnalyses_UPbRejectionReasons = GeoCORKTable(table_name='UPbAnalyses_UPbRejectionReasons',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=[TableAttributes('UPbAnalysisID', 'INTEGER'),
                                                           TableAttributes('RejectionReasonID', 'INTEGER')])

UPbAnalyses_UPbAnalysisContexts = GeoCORKTable(table_name='UPbAnalyses_UPbAnalysisContexts',
                                               table_type=TableType.MANYTOMANY,
                                               contains_foreign_keys=True,
                                               attributes=[TableAttributes('UPbAnalysisID', 'INTEGER'),
                                                           TableAttributes('UPbAnalysisContextID', 'INTEGER')])
