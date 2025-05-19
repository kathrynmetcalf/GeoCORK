from Schema.GeoCORKTable import GeoCORKTable, GeoCORKTableAttribute, TableType


class GeoCORKSchema:
    """

    """
    # ----------------------------------------------------------------------------------------------- #
    # |     Internal Tables                                                                         |
    # ----------------------------------------------------------------------------------------------- #

    About = GeoCORKTable(table_name='About', table_type=TableType.INTERNAL, static_table=True,
                         attributes=[
                             GeoCORKTableAttribute('AboutID', 'INTEGER', primary_key=True),
                             GeoCORKTableAttribute('Name', 'TEXT', not_null=True, not_empty=True),
                             GeoCORKTableAttribute('Authors', 'TEXT', not_null=True, not_empty=True),
                             GeoCORKTableAttribute('Citation', 'TEXT', not_null=True, not_empty=True),
                             GeoCORKTableAttribute('ReferenceLink', 'TEXT', not_null=True, not_empty=True),
                             GeoCORKTableAttribute('Version', 'TEXT', not_null=True, not_empty=True),
                             GeoCORKTableAttribute('Description', 'TEXT'),
                             GeoCORKTableAttribute('CreatedBy', 'TEXT', not_null=True, not_empty=True)
                         ])

    FilterGroups = GeoCORKTable(table_name='FilterGroups', table_type=TableType.INTERNAL,
                                attributes=[
                                    GeoCORKTableAttribute('FilterGroupID', 'INTEGER', primary_key=True),
                                    GeoCORKTableAttribute('FilterGroupName', 'TEXT', not_null=True, not_empty=True),
                                    GeoCORKTableAttribute('SQLQuery', 'TEXT'),
                                    GeoCORKTableAttribute('DefaultColor', 'TEXT'),
                                    GeoCORKTableAttribute('FilterGroupDescription', 'TEXT')])

    # ----------------------------------------------------------------------------------------------- #
    # |     Internal Static Unit/Format/Conversion Tables                                           |
    # ----------------------------------------------------------------------------------------------- #
    AgeUnits = GeoCORKTable(table_name='AgeUnits', table_type=TableType.INTERNAL, static_table=True,
                            contains_foreign_keys=True,
                            as_table_name=['UPbAgeUnits'],
                            attributes=[
                                GeoCORKTableAttribute('AgeUnitID', 'INTEGER', primary_key=True),
                                GeoCORKTableAttribute('AgeUnitName', 'TEXT', not_null=True, not_empty=True),
                                GeoCORKTableAttribute('AgeUnitAbbreviation', 'TEXT', not_null=True, not_empty=True),
                                GeoCORKTableAttribute('AgeUnitDescription', 'TEXT')])

    AgeUnitConversions = GeoCORKTable(table_name='AgeUnitConversions', table_type=TableType.INTERNAL, static_table=True,
                                      contains_foreign_keys=True,
                                      attributes=[
                                          GeoCORKTableAttribute('FromAgeUnitID', 'INTEGER', not_null=True,
                                                                not_empty=True),
                                          GeoCORKTableAttribute('ToAgeUnitID', 'INTEGER', not_null=True,
                                                                not_empty=True),
                                          GeoCORKTableAttribute('AgeUnitConversionCalculation', 'TEXT', not_null=True,
                                                                not_empty=True)])

    ConcordanceFormats = GeoCORKTable(table_name='ConcordanceFormats', table_type=TableType.INTERNAL, static_table=True,
                                      contains_foreign_keys=True,
                                      attributes=[
                                          GeoCORKTableAttribute('ConcordanceFormatID', 'INTEGER', primary_key=True),
                                          GeoCORKTableAttribute('ConcordanceFormatName', 'TEXT', not_null=True,
                                                                not_empty=True),
                                          GeoCORKTableAttribute('ConcordanceFormatAbbreviation', 'TEXT',
                                                                not_null=True,
                                                                not_empty=True),
                                          GeoCORKTableAttribute('ConcordanceFormatDescription', 'TEXT')])

    ConcordanceFormatConversions = GeoCORKTable(table_name='ConcordanceFormatConversions',
                                                table_type=TableType.INTERNAL,
                                                static_table=True,
                                                contains_foreign_keys=True,
                                                attributes=[
                                                    GeoCORKTableAttribute('FromConcordanceFormatID', 'INTEGER',
                                                                          not_null=True,
                                                                          not_empty=True),
                                                    GeoCORKTableAttribute('ToConcordanceFormatID', 'INTEGER',
                                                                          not_null=True,
                                                                          not_empty=True),
                                                    GeoCORKTableAttribute('ConcordanceFormatConversionCalculation',
                                                                          'TEXT',
                                                                          not_null=True, not_empty=True)])

    DirectionUnits = GeoCORKTable(table_name='DirectionUnits', table_type=TableType.INTERNAL, static_table=True,
                                  contains_foreign_keys=True,
                                  as_table_name=['SampleLatDirections', 'SampleLonDirections', 'ColumnLatDirections',
                                                 'ColumnLonDirections'],
                                  attributes=[
                                      GeoCORKTableAttribute('DirectionUnitID', 'INTEGER', primary_key=True),
                                      GeoCORKTableAttribute('DirectionUnitName', 'TEXT', not_null=True, not_empty=True),
                                      GeoCORKTableAttribute('DirectionUnitAbbreviation', 'TEXT', not_null=True,
                                                            not_empty=True),
                                      GeoCORKTableAttribute('DirectionUnitDescription', 'TEXT')])

    DistanceUnits = GeoCORKTable(table_name='DistanceUnits', table_type=TableType.INTERNAL, static_table=True,
                                 contains_foreign_keys=True,
                                 as_table_name=['SampleElevationUnits', 'ColumnElevationUnits',
                                                'ColumnHeightDepthUnits',
                                                'SpotSizeUnits'],
                                 attributes=[GeoCORKTableAttribute('DistanceUnitID', 'INTEGER', primary_key=True),
                                             GeoCORKTableAttribute('DistanceUnitName', 'TEXT', not_null=True,
                                                                   not_empty=True),
                                             GeoCORKTableAttribute('DistanceUnitAbbreviation', 'TEXT', not_null=True,
                                                                   not_empty=True),
                                             GeoCORKTableAttribute('DistanceUnitDescription', 'TEXT')])

    DistanceUnitConversions = GeoCORKTable(table_name='DistanceUnitConversions', table_type=TableType.INTERNAL,
                                           static_table=True,
                                           contains_foreign_keys=True,
                                           attributes=[
                                               GeoCORKTableAttribute('FromDistanceUnitID', 'INTEGER', not_null=True,
                                                                     not_empty=True),
                                               GeoCORKTableAttribute('ToDistanceUnitID', 'INTEGER', not_null=True,
                                                                     not_empty=True),
                                               GeoCORKTableAttribute('DistanceUnitConversionCalculation', 'TEXT',
                                                                     not_null=True, not_empty=True)])

    ErrorFormats = GeoCORKTable(table_name='ErrorFormats', table_type=TableType.INTERNAL, static_table=True,
                                contains_foreign_keys=True,
                                as_table_name=['DirectAgeErrorFormats', 'RatioErrorFormats', 'AgeErrorFormats'],
                                attributes=[GeoCORKTableAttribute('ErrorFormatID', 'INTEGER', primary_key=True),
                                            GeoCORKTableAttribute('ErrorFormatName', 'TEXT', not_null=True,
                                                                  not_empty=True),
                                            GeoCORKTableAttribute('ErrorFormatAbbreviation', 'TEXT', not_null=True,
                                                                  not_empty=True),
                                            GeoCORKTableAttribute('ErrorFormatDescription', 'TEXT')])

    ErrorFormatConversions = GeoCORKTable(table_name='ErrorFormatConversions', table_type=TableType.INTERNAL,
                                          static_table=True, contains_foreign_keys=True,
                                          attributes=[
                                              GeoCORKTableAttribute('FromErrorFormatID', 'INTEGER', not_null=True,
                                                                    not_empty=True),
                                              GeoCORKTableAttribute('ToErrorFormatID', 'INTEGER', not_null=True,
                                                                    not_empty=True),
                                              GeoCORKTableAttribute('ErrorFormatConversionCalculation', 'TEXT',
                                                                    not_null=True, not_empty=True)])

    GPSFormatConversions = GeoCORKTable(table_name='GPSFormatConversions', table_type=TableType.TREE, static_table=True,
                                        contains_foreign_keys=True,
                                        attributes=[
                                            GeoCORKTableAttribute('FromGPSFormatID', 'INTEGER', not_null=True,
                                                                  not_empty=True),
                                            GeoCORKTableAttribute('ToGPSFormatID', 'INTEGER', not_null=True,
                                                                  not_empty=True),
                                            GeoCORKTableAttribute('GPSFormatConversionCalculation', 'TEXT',
                                                                  not_null=True,
                                                                  not_empty=True)])

    GPSFormats = GeoCORKTable(table_name='GPSFormats', table_type=TableType.INTERNAL, static_table=True,
                              contains_foreign_keys=True,
                              as_table_name=['ColumnGPSFormats'],
                              attributes=[GeoCORKTableAttribute('GPSFormatID', 'INTEGER', primary_key=True),
                                          GeoCORKTableAttribute('GPSFormatName', 'TEXT', not_null=True, not_empty=True),
                                          GeoCORKTableAttribute('GPSFormatAbbreviation', 'TEXT', not_null=True,
                                                                not_empty=True),
                                          GeoCORKTableAttribute('GPSFormatDescription', 'TEXT')])

    # ----------------------------------------------------------------------------------------------- #
    #          Tables Used In Other Tables TREES ONLY (Child Tables)
    # ----------------------------------------------------------------------------------------------- #

    Ages = GeoCORKTable(table_name='Ages', table_type=TableType.TREE,
                        user_viewable=True, static_table=True, as_table_name=['OldAge', 'YoungAge'],
                        attributes=[GeoCORKTableAttribute('AgeID', 'INTEGER', primary_key=True),
                                    GeoCORKTableAttribute('ParentAgeID', 'INTEGER'),
                                    GeoCORKTableAttribute('AgeParentRow', 'INTEGER'),
                                    GeoCORKTableAttribute('AgeName', 'TEXT', not_null=True, not_empty=True),
                                    GeoCORKTableAttribute('OldestAge', 'REAL'),
                                    GeoCORKTableAttribute('YoungestAge', 'REAL')])

    AgeConstraints = GeoCORKTable(table_name='AgeConstraints', table_type=TableType.TREE,
                                  user_viewable=True,
                                  contains_foreign_keys=False,
                                  bridge_table='SampleAges_AgeConstraints', bridge_to_column='AgeConstraintID',
                                  bridge_from_column='SampleAgeID',
                                  attributes=[GeoCORKTableAttribute('AgeConstraintID', 'INTEGER', primary_key=True),
                                              GeoCORKTableAttribute('ParentAgeConstraintID', 'INTEGER'),
                                              GeoCORKTableAttribute('AgeConstraintParentRow', 'INTEGER'),
                                              GeoCORKTableAttribute('AgeConstraintName', 'TEXT', not_null=True,
                                                                    not_empty=True),
                                              GeoCORKTableAttribute('AgeConstraintDescription', 'TEXT')])

    AgeInterpretations = GeoCORKTable(table_name='AgeInterpretations', table_type=TableType.TREE,
                                      user_viewable=True,
                                      contains_foreign_keys=False, as_table_name=['UPbAgeInterpretations'],
                                      bridge_table='SampleAges_AgeInterpretations',
                                      bridge_to_column='AgeInterpretationID',
                                      bridge_from_column='SampleAgeID',
                                      attributes=[
                                          GeoCORKTableAttribute('AgeInterpretationID', 'INTEGER', primary_key=True),
                                          GeoCORKTableAttribute('ParentAgeInterpretationID', 'INTEGER'),
                                          GeoCORKTableAttribute('AgeInterpretationParentRow', 'INTEGER'),
                                          GeoCORKTableAttribute('AgeInterpretationName', 'TEXT', not_null=True,
                                                                not_empty=True),
                                          GeoCORKTableAttribute('AgeInterpretationDescription', 'TEXT')])

    AgeSignatures = GeoCORKTable(table_name='AgeSignatures', table_type=TableType.TREE,
                                 user_viewable=True,
                                 contains_foreign_keys=False,
                                 bridge_table='SampleAges_AgeSignature', bridge_to_column='AgeSignatureID',
                                 bridge_from_column='SampleAgeID',
                                 attributes=[GeoCORKTableAttribute('AgeSignatureID', 'INTEGER', primary_key=True),
                                             GeoCORKTableAttribute('ParentAgeSignatureID', 'INTEGER'),
                                             GeoCORKTableAttribute('AgeSignatureParentRow', 'INTEGER'),
                                             GeoCORKTableAttribute('AgeSignatureName', 'TEXT', not_null=True,
                                                                   not_empty=True),
                                             GeoCORKTableAttribute('AgeSignatureDescription', 'TEXT')])

    AliquotContexts = GeoCORKTable(table_name='AliquotContexts', table_type=TableType.TREE,
                                   user_viewable=True,
                                   contains_foreign_keys=False,
                                   bridge_table='Aliquots_AliquotContexts', bridge_to_column='AliquotContextID',
                                   bridge_from_column='SampleID',
                                   attributes=[GeoCORKTableAttribute('AliquotContextID', 'INTEGER', primary_key=True),
                                               GeoCORKTableAttribute('ParentAliquotContextID', 'INTEGER'),
                                               GeoCORKTableAttribute('AliquotContextParentRow', 'INTEGER'),
                                               GeoCORKTableAttribute('AliquotContextName', 'TEXT', not_null=True,
                                                                     not_empty=True),
                                               GeoCORKTableAttribute('AliquotContextDescription', 'TEXT')])
    Columns = GeoCORKTable(table_name='Columns', table_type=TableType.TREE,
                           user_viewable=True,
                           contains_foreign_keys=True,
                           bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                           bridge_from_column='SampleID',
                           attributes=[GeoCORKTableAttribute('ColumnID', 'INTEGER', primary_key=True),
                                       GeoCORKTableAttribute('ColumnName', 'TEXT', not_null=True, not_empty=True),
                                       GeoCORKTableAttribute('ColumnTotalHeightDepth', 'REAL'),
                                       GeoCORKTableAttribute('ColumnTotalHeightDepthUnitID', 'INTEGER'),
                                       GeoCORKTableAttribute('ColumnBaseGPSID', 'INTEGER'),
                                       GeoCORKTableAttribute('ColumnDescription', 'TEXT')])

    GPSLocations = GeoCORKTable(table_name='GPSLocations', table_type=TableType.TREE, conditionally_editable=True,
                                contains_foreign_keys=True, as_table_name=['ColumnGPS'],
                                attributes=[GeoCORKTableAttribute('GPSLocationID', 'INTEGER', primary_key=True),
                                            GeoCORKTableAttribute('GPSLocationConverted', 'TEXT'),
                                            GeoCORKTableAttribute('GPSLocationDisplay', 'AS',
                                                                  as_case="""CASE WHEN GPSFormatID = 1 THEN GPSLatDeg || "°, " ||  GPSLonDeg || "° " WHEN GPSFormatID = 2 THEN GPSLatDeg || "° " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonDirectionID WHEN GPSFormatID = 3 THEN GPSLatDeg || "° " || GPSLatMin || "', " || GPSLonDeg || "° " || GPSLonMin || "'" WHEN GPSFormatID = 4 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonDirectionID WHEN GPSFormatID = 5 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'', " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "''" WHEN GPSFormatID = 6 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "'' " || GPSLonDirectionID WHEN GPSFormatID = 7 THEN GPSUTMZone || ", " || GPSUTME || "m E, " || GPSUTMN || "m N" ENDCASE WHEN GPSFormatID = 1 THEN GPSLatDeg || "°, " ||  GPSLonDeg || "° " WHEN GPSFormatID = 2 THEN GPSLatDeg || "° " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonDirectionID WHEN GPSFormatID = 3 THEN GPSLatDeg || "° " || GPSLatMin || "', " || GPSLonDeg || "° " || GPSLonMin || "'" WHEN GPSFormatID = 4 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonDirectionID WHEN GPSFormatID = 5 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'', " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "''" WHEN GPSFormatID = 6 THEN GPSLatDeg || "° " || GPSLatMin || "' " || GPSLatSec || "'' " || GPSLatDirectionID || ", " || GPSLonDeg || "° " || GPSLonMin || "' " || GPSLonSec || "'' " || GPSLonDirectionID WHEN GPSFormatID = 7 THEN GPSUTMZone || ", " || GPSUTME || "m E, " || GPSUTMN || "m N" END"""),
                                            GeoCORKTableAttribute('GPSLatDeg', 'REAL'),
                                            GeoCORKTableAttribute('GPSLatMin', 'REAL'),
                                            GeoCORKTableAttribute('GPSLatSec', 'REAL'),
                                            GeoCORKTableAttribute('GPSLatDirectionID', 'INTEGER'),
                                            GeoCORKTableAttribute('GPSLonDeg', 'REAL'),
                                            GeoCORKTableAttribute('GPSLonMin', 'REAL'),
                                            GeoCORKTableAttribute('GPSLonSec', 'REAL'),
                                            GeoCORKTableAttribute('GPSLonDirectionID', 'INTEGER'),
                                            GeoCORKTableAttribute('GPSUTMZone', 'TEXT'),
                                            GeoCORKTableAttribute('GPSUTMN', 'REAL'),
                                            GeoCORKTableAttribute('GPSUTME', 'REAL'),
                                            GeoCORKTableAttribute('GPSFormatID', 'INTEGER'),
                                            GeoCORKTableAttribute('GPSElev', 'REAL'),
                                            GeoCORKTableAttribute('GPSElevError', 'REAL'),
                                            GeoCORKTableAttribute('GPSElevUnitID', 'INTEGER')])

    Instruments = GeoCORKTable(table_name='Instruments', table_type=TableType.TREE,
                               user_viewable=True,
                               contains_foreign_keys=False,
                               bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                               bridge_from_column='SampleID',
                               attributes=[GeoCORKTableAttribute('InstrumentID', 'INTEGER', primary_key=True),
                                           GeoCORKTableAttribute('InstrumentName', 'TEXT', not_null=True,
                                                                 not_empty=True),
                                           GeoCORKTableAttribute('InstrumentDescription', 'TEXT'), ])

    LabFacilities = GeoCORKTable(table_name='LabFacilities', table_type=TableType.TREE,
                                 user_viewable=True,
                                 contains_foreign_keys=False,
                                 bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                 bridge_from_column='SampleID',
                                 attributes=[GeoCORKTableAttribute('LabFacilityID', 'INTEGER', primary_key=True),
                                             GeoCORKTableAttribute('LabFacilityName', 'TEXT', not_null=True,
                                                                   not_empty=True),
                                             GeoCORKTableAttribute('LabFacilityDescription', 'TEXT')])

    References = GeoCORKTable(table_name='References', table_type=TableType.TREE,
                              user_viewable=True,
                              contains_foreign_keys=False, as_table_name=['AgeReferences', 'UPbReferences'],
                              bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                              bridge_from_column='SampleID',
                              attributes=[GeoCORKTableAttribute('ReferenceID', 'INTEGER', primary_key=True),
                                          GeoCORKTableAttribute('Authors', 'TEXT'),
                                          GeoCORKTableAttribute('Year', 'INTEGER'),
                                          GeoCORKTableAttribute('Title', 'TEXT'),
                                          GeoCORKTableAttribute('Source', 'TEXT'),
                                          GeoCORKTableAttribute('DOI', 'TEXT')])

    Regions = GeoCORKTable(table_name='Regions', table_type=TableType.TREE,
                           user_viewable=True,
                           contains_foreign_keys=False,
                           bridge_table='Samples_Regions', bridge_to_column='RegionID',
                           bridge_from_column='SampleID',
                           attributes=[GeoCORKTableAttribute('RegionID', 'INTEGER', primary_key=True),
                                       GeoCORKTableAttribute('ParentRegionID', 'INTEGER'),
                                       GeoCORKTableAttribute('RegionParentRow', 'INTEGER'),
                                       GeoCORKTableAttribute('RegionName', 'TEXT', not_null=True, not_empty=True),
                                       GeoCORKTableAttribute('RegionDescription', 'TEXT')])

    RejectionReasons = GeoCORKTable(table_name='RejectionReasons', table_type=TableType.TREE,
                                    user_viewable=True,
                                    contains_foreign_keys=False, as_table_name=['UPbRejectionReasons'],
                                    bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                                    bridge_from_column='SampleID',
                                    attributes=[GeoCORKTableAttribute('RejectionReasonID', 'INTEGER', primary_key=True),
                                                GeoCORKTableAttribute('RejectionReasonName', 'TEXT', not_null=True,
                                                                      not_empty=True),
                                                GeoCORKTableAttribute('RejectionReasonDescription', 'TEXT')])

    RockTypes = GeoCORKTable(table_name='RockTypes', table_type=TableType.TREE,
                             user_viewable=True,
                             contains_foreign_keys=False,
                             bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                             bridge_from_column='SampleID',
                             attributes=[GeoCORKTableAttribute('RockTypeID', 'INTEGER', primary_key=True),
                                         GeoCORKTableAttribute('ParentRockTypeID', 'INTEGER'),
                                         GeoCORKTableAttribute('RockTypeParentRow', 'INTEGER'),
                                         GeoCORKTableAttribute('RockTypeName', 'TEXT', not_null=True, not_empty=True),
                                         GeoCORKTableAttribute('RockTypeDescription', 'TEXT')])

    SpotCompositions = GeoCORKTable(table_name='SpotCompositions', table_type=TableType.TREE,
                                    user_viewable=True,
                                    contains_foreign_keys=False,
                                    bridge_table='Spots_SpotCompositions', bridge_to_column='SpotCompositionID',
                                    bridge_from_column='SpotID',
                                    attributes=[GeoCORKTableAttribute('SpotCompositionID', 'INTEGER', primary_key=True),
                                                GeoCORKTableAttribute('ParentSpotCompositionID', 'INTEGER'),
                                                GeoCORKTableAttribute('SpotCompositionParentRow', 'INTEGER'),
                                                GeoCORKTableAttribute('SpotCompositionName', 'TEXT', not_null=True,
                                                                      not_empty=True),
                                                GeoCORKTableAttribute('SpotCompositionDescription', 'TEXT')])

    SpotContexts = GeoCORKTable(table_name='SpotContexts', table_type=TableType.TREE,
                                user_viewable=True,
                                contains_foreign_keys=False,
                                bridge_table='Spots_SpotContexts', bridge_to_column='SpotContextID',
                                bridge_from_column='SpotID',
                                attributes=[GeoCORKTableAttribute('SpotContextID', 'INTEGER', primary_key=True),
                                            GeoCORKTableAttribute('ParentSpotContextID', 'INTEGER'),
                                            GeoCORKTableAttribute('SpotContextParentRow', 'INTEGER'),
                                            GeoCORKTableAttribute('SpotContextName', 'TEXT', not_null=True,
                                                                  not_empty=True),
                                            GeoCORKTableAttribute('SpotContextDescription', 'TEXT')])

    SampleAges = GeoCORKTable(table_name='SampleAges', table_type=TableType.TREE,
                              user_viewable=True, conditionally_editable=True,
                              contains_foreign_keys=True,
                              bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                              bridge_from_column='SampleID',
                              attributes=[GeoCORKTableAttribute('SampleAgeID', 'INTEGER', primary_key=True),
                                          GeoCORKTableAttribute('DirectAge', 'REAL'),
                                          GeoCORKTableAttribute('DirectAgeError', 'REAL'),
                                          GeoCORKTableAttribute('DirectAgeErrorFormatID', 'INTEGER'),
                                          GeoCORKTableAttribute('OldestDirectAge', 'REAL'),
                                          GeoCORKTableAttribute('YoungestDirectAge', 'REAL'),
                                          GeoCORKTableAttribute('DirectAgeUnitID', 'INTEGER'),
                                          GeoCORKTableAttribute('OldestAgeID', 'INTEGER'),
                                          GeoCORKTableAttribute('YoungestAgeID', 'INTEGER'),
                                          GeoCORKTableAttribute('SampleAgeDescription', 'TEXT')])

    SampleContexts = GeoCORKTable(table_name='SampleContexts', table_type=TableType.TREE,
                                  user_viewable=True,
                                  contains_foreign_keys=False,
                                  bridge_table='Samples_SampleContexts', bridge_to_column='SampleContextID',
                                  bridge_from_column='SampleID',
                                  attributes=[GeoCORKTableAttribute('SampleContextID', 'INTEGER', primary_key=True),
                                              GeoCORKTableAttribute('ParentSampleContextID', 'INTEGER'),
                                              GeoCORKTableAttribute('SampleContextParentRow', 'INTEGER', not_null=True),
                                              GeoCORKTableAttribute('SampleContextName', 'TEXT', not_null=True,
                                                                    not_empty=True),
                                              GeoCORKTableAttribute('SampleContextDescription', 'TEXT')])

    SamplingMethods = GeoCORKTable(table_name='SamplingMethods', table_type=TableType.TREE,
                                   user_viewable=True,
                                   contains_foreign_keys=False,
                                   bridge_table='Samples_SamplingMethods', bridge_to_column='SamplingMethodID',
                                   bridge_from_column='SampleID',
                                   attributes=[GeoCORKTableAttribute('SamplingMethodID', 'INTEGER', primary_key=True),
                                               GeoCORKTableAttribute('ParentSamplingMethodID', 'INTEGER'),
                                               GeoCORKTableAttribute('SamplingMethodParentRow', 'INTEGER'),
                                               GeoCORKTableAttribute('SamplingMethodName', 'TEXT', not_null=True,
                                                                     not_empty=True),
                                               GeoCORKTableAttribute('SamplingMethodDescription', 'TEXT')])

    Settings = GeoCORKTable(table_name='Settings', table_type=TableType.TREE,
                            user_viewable=True,
                            contains_foreign_keys=False,
                            bridge_table='Samples_Units', bridge_to_column='UnitID',
                            bridge_from_column='SampleID',
                            attributes=[GeoCORKTableAttribute('SettingID', 'INTEGER', primary_key=True),
                                        GeoCORKTableAttribute('ParentSettingID', 'INTEGER'),
                                        GeoCORKTableAttribute('SettingParentRow', 'INTEGER'),
                                        GeoCORKTableAttribute('SettingName', 'TEXT', not_null=True, not_empty=True),
                                        GeoCORKTableAttribute('SettingDescription', 'TEXT')])

    Units = GeoCORKTable(table_name='Units', table_type=TableType.TREE,
                         user_viewable=True,
                         contains_foreign_keys=False,
                         bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                         bridge_from_column='SampleID',
                         attributes=[GeoCORKTableAttribute('UnitID', 'INTEGER', primary_key=True),
                                     GeoCORKTableAttribute('ParentUnitID', 'INTEGER'),
                                     GeoCORKTableAttribute('UnitParentRow', 'INTEGER'),
                                     GeoCORKTableAttribute('UnitName', 'TEXT', not_null=True, not_empty=True),
                                     GeoCORKTableAttribute('UnitDescription', 'TEXT')])

    UPbAnalysisContexts = GeoCORKTable(table_name='UPbAnalysisContexts', table_type=TableType.TREE,
                                       user_viewable=True,
                                       contains_foreign_keys=False, as_table_name=['UPbAnalysisContexts'],
                                       bridge_table='UPbAnalyses_UPbAnalysisContexts',
                                       bridge_to_column='UPbAnalysisContextID',
                                       bridge_from_column='UPbAnalysisID',
                                       attributes=[
                                           GeoCORKTableAttribute('UPbAnalysisContextID', 'INTEGER', primary_key=True),
                                           GeoCORKTableAttribute('UPbAnalysisContextID', 'INTEGER'),
                                           GeoCORKTableAttribute('UPbAnalysisContextParentRow', 'INTEGER'),
                                           GeoCORKTableAttribute('UPbAnalysisContextName', 'TEXT', not_null=True,
                                                                 not_empty=True),
                                           GeoCORKTableAttribute('UPbAnalysisContextDescription', 'TEXT')])

    UPbAnalysisMethods = GeoCORKTable(table_name='UPbAnalysisMethods', table_type=TableType.TREE,
                                      user_viewable=True,
                                      contains_foreign_keys=False,
                                      bridge_table='UPbAnalyses', bridge_to_column='UPbAnalysisMethodID',
                                      bridge_from_column='UPbAnalysisMethodID',
                                      attributes=[
                                          GeoCORKTableAttribute('UPbAnalysisMethodID', 'INTEGER', primary_key=True),
                                          GeoCORKTableAttribute('ParentUPbAnalysisMethodID', 'INTEGER'),
                                          GeoCORKTableAttribute('UPbAnalysisMethodParentRow', 'INTEGER'),
                                          GeoCORKTableAttribute('UPbAnalysisMethodName', 'TEXT', not_null=True,
                                                                not_empty=True),
                                          GeoCORKTableAttribute('UPbAnalysisMethodDescription', 'TEXT')])

    # ----------------------------------------------------------------------------------------------- #
    #          Main Data Tables for Samples, Aliquots, Spots, UPb
    # ----------------------------------------------------------------------------------------------- #

    Samples = GeoCORKTable(table_name='Samples', table_type=TableType.TABLE,
                           user_viewable=True,
                           contains_foreign_keys=True,
                           bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                           bridge_from_column='SampleID',
                           attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', primary_key=True),
                                       GeoCORKTableAttribute('SampleName', 'TEXT', not_null=True, not_empty=True),
                                       GeoCORKTableAttribute('SampleIGSN', 'TEXT'),
                                       GeoCORKTableAttribute('SampleGPSLocationID', 'INTEGER'),
                                       GeoCORKTableAttribute('SampleColumnID', 'INTEGER'),
                                       GeoCORKTableAttribute('HeightDepth', 'REAL'),
                                       GeoCORKTableAttribute('HeightDepthError', 'REAL'),
                                       GeoCORKTableAttribute('HeightDepthUnitID', 'INTEGER'),
                                       GeoCORKTableAttribute('DefaultSampleAgeID', 'INTEGER'),
                                       GeoCORKTableAttribute('SampleDescription', 'TEXT')])

    Aliquots = GeoCORKTable(table_name='Aliquots', table_type=TableType.TREE,
                            user_viewable=True,
                            conditionally_editable=True,
                            contains_foreign_keys=True,
                            bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                            bridge_from_column='SampleID',
                            attributes=[GeoCORKTableAttribute('AliquotID', 'INTEGER', primary_key=True),
                                        GeoCORKTableAttribute('ParentAliquotID', 'INTEGER'),
                                        GeoCORKTableAttribute('AliquotParentRow', 'INTEGER'),
                                        GeoCORKTableAttribute('AliquotName', 'TEXT', not_null=True, not_empty=True),
                                        GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True, not_empty=True)])

    Spots = GeoCORKTable(table_name='Spots', table_type=TableType.TABLE,
                         user_viewable=True,
                         conditionally_editable=True,
                         contains_foreign_keys=True,
                         bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                         bridge_from_column='SampleID',
                         attributes=[GeoCORKTableAttribute('SpotID', 'INTEGER', primary_key=True),
                                     GeoCORKTableAttribute('SpotName', 'TEXT', not_null=True, not_empty=True),
                                     GeoCORKTableAttribute('AliquotID', 'INTEGER', not_null=True, not_empty=True),
                                     GeoCORKTableAttribute('SpotCompositionID', 'INTEGER')])

    UPbAnalyses = GeoCORKTable(table_name='UPbAnalyses', table_type=TableType.TABLE,
                               user_viewable=True,
                               conditionally_editable=True,
                               contains_foreign_keys=True,
                               bridge_table='Samples_RockTypes', bridge_to_column='RockTypeID',
                               bridge_from_column='SampleID',
                               attributes=[GeoCORKTableAttribute('UPbAnalysisID', 'INTEGER', primary_key=True),
                                           GeoCORKTableAttribute('SpotID', 'INTEGER', not_null=True, not_empty=True),
                                           GeoCORKTableAttribute('ReferenceID', 'INTEGER'),
                                           GeoCORKTableAttribute('LabFacilityID', 'INTEGER'),
                                           GeoCORKTableAttribute('InstrumentID', 'INTEGER'),
                                           GeoCORKTableAttribute('UPbAnalysisMethodID', 'INTEGER'),
                                           GeoCORKTableAttribute('Pb204cps', 'REAL'),
                                           GeoCORKTableAttribute('Pb206cps', 'REAL'),
                                           GeoCORKTableAttribute('Pb207cps', 'REAL'),
                                           GeoCORKTableAttribute('Pb208cps', 'REAL'),
                                           GeoCORKTableAttribute('Pb*cps', 'REAL'),
                                           GeoCORKTableAttribute('Th232cps', 'REAL'),
                                           GeoCORKTableAttribute('U235cps', 'REAL'),
                                           GeoCORKTableAttribute('U238cps', 'REAL'),
                                           GeoCORKTableAttribute('Uppm', 'REAL'),
                                           GeoCORKTableAttribute('Thppm', 'REAL'),
                                           GeoCORKTableAttribute('U/Th', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Th/U', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('CalculatedU/Th', 'AS', not_null=True),
                                           GeoCORKTableAttribute('CalculatedTh/U', 'AS', not_null=True),
                                           GeoCORKTableAttribute('206Pb/207Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('206Pb/207PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('207Pb/206Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('207Pb/206PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated206Pb/207Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated207Pb/206Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('207Pb/235U', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('207Pb/235UError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('235U/207Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('235U/207PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated207Pb/235U', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated235U/207Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('206Pb/238U', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('206Pb/238UError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('238U/206Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('238U/206PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated206Pb/238U', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated238U/206Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('208Pb/232Th', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('208Pb/232ThError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('232Th/208Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('232Th/208PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated208Pb/232Th', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated232Th/208Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('238U/232Th', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('238U/232ThError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('232Th/238U', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('232Th/238UError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated238U/232Th', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated232Th/238U', 'AS', not_null=True),
                                           GeoCORKTableAttribute('204Pb/238U', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('204Pb/238UError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('238U/204Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('238U/204PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated204Pb/238U', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated238U/204Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('206Pb/204Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('206Pb/204PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('204Pb/206Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('204Pb/206PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated206Pb/204Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated204Pb/206Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('207Pb/204Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('207Pb/204PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('204Pb/207Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('204Pb/207PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated207Pb/204Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated204Pb/207Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('208Pb/204Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('208Pb/204PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('204Pb/208Pb', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('204Pb/208PbError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('Calculated208Pb/204Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('Calculated204Pb/208Pb', 'AS', not_null=True),
                                           GeoCORKTableAttribute('RatioErrorFormatID', 'INTEGER',
                                                                 visible_to_user=False),
                                           GeoCORKTableAttribute('ErrorCorr/Rho', 'REAL'),
                                           GeoCORKTableAttribute('207Pb/206PbAge', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('207Pb/206PbAgeError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('207Pb/235UAge', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('207Pb/235UAgeError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('206Pb/238UAge', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('206Pb/238UAgeError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('208Pb/232ThAge', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('208Pb/232ThAgeError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('BestAge', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('BestAgeError', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('AgeErrorFormatID', 'INTEGER', visible_to_user=False),
                                           GeoCORKTableAttribute('AgeUnitID', 'INTEGER', visible_to_user=False),
                                           GeoCORKTableAttribute('AgeInterpretationID', 'INTEGER',
                                                                 visible_to_user=False),
                                           GeoCORKTableAttribute('Concordance', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('ConcordanceFormatID', 'INTEGER',
                                                                 visible_to_user=False),
                                           GeoCORKTableAttribute('SpotSize', 'REAL', visible_to_user=False),
                                           GeoCORKTableAttribute('SpotSizeUnitID', 'INTEGER', visible_to_user=False),
                                           GeoCORKTableAttribute('Rejected', 'INTEGER')])

    # ----------------------------------------------------------------------------------------------- #
    # |     Many-To-Many Tables Using Tables Previously Created                                     |
    # ----------------------------------------------------------------------------------------------- #

    Aliquots_AliquotContexts = GeoCORKTable(table_name='Aliquots_AliquotContexts',
                                            table_type=TableType.MANYTOMANY,
                                            contains_foreign_keys=True,
                                            attributes=[GeoCORKTableAttribute('AliquotID', 'INTEGER'),
                                                        GeoCORKTableAttribute('AliquotContextID', 'INTEGER')])

    SampleAges_AgeConstraints = GeoCORKTable(table_name='SampleAges_AgeConstraints',
                                             table_type=TableType.MANYTOMANY,
                                             contains_foreign_keys=True,
                                             attributes=[GeoCORKTableAttribute('SampleAgeID', 'INTEGER', not_null=True),
                                                         GeoCORKTableAttribute('AgeConstraintID', 'INTEGER',
                                                                               not_null=True)])

    SampleAges_AgeInterpretations = GeoCORKTable(table_name='SampleAges_AgeInterpretations',
                                                 table_type=TableType.MANYTOMANY,
                                                 contains_foreign_keys=True,
                                                 attributes=[
                                                     GeoCORKTableAttribute('SampleAgeID', 'INTEGER', not_null=True),
                                                     GeoCORKTableAttribute('AgeInterpretationID', 'INTEGER',
                                                                           not_null=True)])

    SampleAges_References = GeoCORKTable(table_name='SampleAges_References',
                                         table_type=TableType.MANYTOMANY,
                                         contains_foreign_keys=True,
                                         attributes=[GeoCORKTableAttribute('SampleAgeID', 'INTEGER', not_null=True),
                                                     GeoCORKTableAttribute('ReferenceID', 'INTEGER', not_null=True)])

    Samples_AgeSignatures = GeoCORKTable(table_name='Samples_AgeSignatures',
                                         table_type=TableType.MANYTOMANY,
                                         contains_foreign_keys=True,
                                         attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True),
                                                     GeoCORKTableAttribute('AgeSignatureID', 'INTEGER', not_null=True)])

    Samples_Regions = GeoCORKTable(table_name='Samples_Regions',
                                   table_type=TableType.MANYTOMANY,
                                   contains_foreign_keys=True,
                                   attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True),
                                               GeoCORKTableAttribute('RegionID', 'INTEGER', not_null=True)])

    Samples_RockTypes = GeoCORKTable(table_name='Samples_RockTypes',
                                     table_type=TableType.MANYTOMANY,
                                     contains_foreign_keys=True,
                                     attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER'),
                                                 GeoCORKTableAttribute('RockTypeID', 'INTEGER')])

    Samples_SampleAges = GeoCORKTable(table_name='Samples_SampleAges',
                                      table_type=TableType.MANYTOMANY,
                                      contains_foreign_keys=True,
                                      attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True),
                                                  GeoCORKTableAttribute('SampleAgeID', 'INTEGER', not_null=True)])

    Samples_SampleContexts = GeoCORKTable(table_name='Samples_SampleContexts',
                                          table_type=TableType.MANYTOMANY,
                                          contains_foreign_keys=True,
                                          attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True),
                                                      GeoCORKTableAttribute('SampleContextID', 'INTEGER',
                                                                            not_null=True)])

    Samples_SamplingMethods = GeoCORKTable(table_name='Samples_SamplingMethods',
                                           table_type=TableType.MANYTOMANY,
                                           contains_foreign_keys=True,
                                           attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True),
                                                       GeoCORKTableAttribute('SamplingMethodID', 'INTEGER',
                                                                             not_null=True)])

    Samples_Settings = GeoCORKTable(table_name='Samples_Settings',
                                    table_type=TableType.MANYTOMANY,
                                    contains_foreign_keys=True,
                                    attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True),
                                                GeoCORKTableAttribute('SettingID', 'INTEGER', not_null=True)])

    Samples_Units = GeoCORKTable(table_name='Samples_Units',
                                 table_type=TableType.MANYTOMANY,
                                 contains_foreign_keys=True,
                                 attributes=[GeoCORKTableAttribute('SampleID', 'INTEGER', not_null=True),
                                             GeoCORKTableAttribute('UnitID', 'INTEGER', not_null=True)])

    Spots_SpotContexts = GeoCORKTable(table_name='Spots_SpotContexts',
                                      table_type=TableType.MANYTOMANY,
                                      contains_foreign_keys=True,
                                      attributes=[GeoCORKTableAttribute('SpotID', 'INTEGER', not_null=True),
                                                  GeoCORKTableAttribute('SpotContextID', 'INTEGER', not_null=True)])

    UPbAnalyses_UPbRejectionReasons = GeoCORKTable(table_name='UPbAnalyses_UPbRejectionReasons',
                                                   table_type=TableType.MANYTOMANY,
                                                   contains_foreign_keys=True,
                                                   attributes=[GeoCORKTableAttribute('UPbAnalysisID', 'INTEGER'),
                                                               GeoCORKTableAttribute('RejectionReasonID', 'INTEGER')])

    UPbAnalyses_UPbAnalysisContexts = GeoCORKTable(table_name='UPbAnalyses_UPbAnalysisContexts',
                                                   table_type=TableType.MANYTOMANY,
                                                   contains_foreign_keys=True,
                                                   attributes=[GeoCORKTableAttribute('UPbAnalysisID', 'INTEGER'),
                                                               GeoCORKTableAttribute('UPbAnalysisContextID',
                                                                                     'INTEGER')])




    ordered_tables = [
        About, FilterGroups, AgeUnits, AgeUnitConversions, ConcordanceFormats,
        ConcordanceFormatConversions, DirectionUnits, DistanceUnits, DistanceUnitConversions,
        ErrorFormats, ErrorFormatConversions, GPSFormatConversions, GPSFormats, Ages, AgeConstraints,
        AgeInterpretations, AgeSignatures, AliquotContexts, Columns, GPSLocations, Instruments,
        LabFacilities, References, Regions, RejectionReasons, RockTypes, SpotCompositions, SpotContexts,
        SampleAges, SampleContexts, SamplingMethods, Settings, Units, UPbAnalysisContexts,
        UPbAnalysisMethods, Samples, Aliquots, Spots, UPbAnalyses, Aliquots_AliquotContexts,
        SampleAges_AgeConstraints, SampleAges_AgeInterpretations, SampleAges_References,
        Samples_AgeSignatures, Samples_Regions, Samples_RockTypes, Samples_SampleAges,
        Samples_SampleContexts, Samples_SamplingMethods, Samples_Settings, Samples_Units,
        Spots_SpotContexts, UPbAnalyses_UPbRejectionReasons, UPbAnalyses_UPbAnalysisContexts
    ]
