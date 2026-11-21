
sample_possible_user_input_fields = {
    'Sample Info': {
        'Sample Name': ['Samples', 'SampleName'],
        'Sample IGSN': ['Samples', 'SampleIGSN'],
        'Sample Description': ['Samples', 'SampleDescription'],
        'Sample Context': ['SampleContexts', 'SampleContextName'],
        'Sample Context Description': ['SampleContexts', 'SampleContextDescription'],
        'Sampling Method': ['SamplingMethods', 'SamplingMethodName'],
        'Sampling Method Description': ['SamplingMethods', 'SamplingMethodDescription'],
        'Region': ['Regions', 'RegionName'],
        'Region Description': ['Regions', 'RegionDescription'],
        'Setting': ['Settings', 'SettingName'],
        'Setting Description': ['Settings', 'SettingDescription'],
        'Rock Type': ['RockTypes', 'RockTypeName'],
        'Rock Type Description': ['RockTypes', 'RockTypeDescription'],
        'Unit': ['Units', 'UnitName'],
        'Unit Description': ['Units', 'UnitDescription']
    },
    'Default Sample Age': {
        'Direct Age': ['SampleAges', 'DirectAge'],
        'Direct Age Error': ['SampleAges', 'DirectAgeError'],
        'Direct Age Error Format': ['SampleAges', 'DirectAgeErrorFormatID'],
        'Direct Age Unit': ['SampleAges', 'DirectAgeUnitID'],
        'Oldest Direct Age': ['SampleAges', 'OldestDirectAge'],
        'Youngest Direct Age': ['SampleAges', 'YoungestDirectAge'],
        'Oldest Relative Age': ['SampleAges', 'OldestAgeID'],
        'Youngest Relative Age': ['SampleAges', 'YoungestAgeID'],
        'Age Description': ['SampleAges', 'SampleAgeDescription'],
        'Age Constraint': ['AgeConstraints', 'AgeConstraintName'],
        'Age Constraint Description': ['AgeConstraints', 'AgeConstraintDescription'],
        'Age Interpretation': ['AgeInterpretations', 'AgeInterpretationName'],
        'Age Interpretation Description': ['AgeInterpretations', 'AgeInterpretationDescription'],
        'Age Signature': ['AgeSignatures', 'AgeSignatureName'],
        'Age Signature Description': ['AgeSignatures', 'AgeSignatureDescription']
    }
}

gps_possible_user_input_fields = {
    'Sample GPS': {
        'Sample Latitude degrees': ['GPSLocations', 'GPSLatDeg'],
        'Sample Latitude minutes': ['GPSLocations', 'GPSLatMin'],
        'Sample Latitude seconds': ['GPSLocations', 'GPSLatSec'],
        'Sample Latitude direction': ['GPSLocations', 'GPSLatDirectionID'],
        'Sample Longitude degrees': ['GPSLocations', 'GPSLonDeg'],
        'Sample Longitude minutes': ['GPSLocations', 'GPSLonMin'],
        'Sample Longitude seconds': ['GPSLocations', 'GPSLonSec'],
        'Sample Longitude direction': ['GPSLocations', 'GPSLonDirectionID'],
        'Sample Easting': ['GPSLocations', 'GPSUTME'],
        'Sample Northing': ['GPSLocations', 'GPSUTMN'],
        'Sample Zone': ['GPSLocations', 'GPSUTMZone'],
        'Sample Elevation': ['GPSLocations', 'GPSElev'],
        'Sample Elevation Error': ['GPSLocations', 'GPSElevError'],
        'Sample Elevation Unit': ['GPSLocations', 'GPSElevUnitID']
    },
    'Column GPS': {
        'Column Latitude degrees': ['GPSLocations', 'GPSLatDeg'],
        'Column Latitude minutes': ['GPSLocations', 'GPSLatMin'],
        'Column Latitude seconds': ['GPSLocations', 'GPSLatSec'],
        'Column Latitude direction': ['GPSLocations', 'GPSLatDirectionID'],
        'Column Longitude degrees': ['GPSLocations', 'GPSLonDeg'],
        'Column Longitude minutes': ['GPSLocations', 'GPSLonMin'],
        'Column Longitude seconds': ['GPSLocations', 'GPSLonSec'],
        'Column Longitude direction': ['GPSLocations', 'GPSLonDirectionID'],
        'Column Easting': ['GPSLocations', 'GPSUTME'],
        'Column Northing': ['GPSLocations', 'GPSUTMN'],
        'Column Zone': ['GPSLocations', 'GPSUTMZone'],
        'Column Elevation': ['GPSLocations', 'GPSElev'],
        'Column Elevation Error': ['GPSLocations', 'GPSElevError'],
        'Column Elevation Unit': ['GPSLocations', 'GPSElevUnitID']
    }
}

column_possible_user_input_fields = {
    'Column Info': {
        'Column Name': ['Columns', 'ColumnName'],
        'Column Description': ['Columns', 'ColumnDescription'],
        'Column Total Height/Depth': ['Columns', 'ColumnTotalHeightDepth'],
        'Column Total Height/Depth Unit': ['Columns', 'ColumnTotalHeightDepthUnitID'],
        'Sample Height/Depth': ['Samples', 'HeightDepth'],
        'Sample Height/Depth Error': ['Samples', 'HeightDepthError'],
        'Sample Height/Depth Unit': ['Samples', 'HeightDepthUnitID']
    }
}

aliquot_grain_spot_possible_user_input_fields = {
    'Aliquot Info': {
        'Aliquot Name': ['Aliquots', 'AliquotName'],
        'Aliquot Description': ['Aliquots', 'AliquotDescription'],
        'Aliquot Context': ['AliquotContexts', 'AliquotContextName'],
        'Aliquot Context Description': ['AliquotContexts', 'AliquotContextDescription']
    },
    'Grain Info': {
        'Grain Name': ['Grains', 'GrainName'],
        'Grain Description': ['Grains', 'GrainDescription'],
        'Grain Composition': ['GrainCompositions', 'GrainCompositionName'],
        'Grain Composition Description': ['GrainCompositions', 'GrainCompositionDescription'],
        'Grain Context': ['GrainContexts', 'GrainContextName'],
        'Grain Context Description': ['GrainContexts', 'GrainContextDescription']
    },
    'Spot Info': {
        'Spot Name': ['Spots', 'SpotName'],
        'Spot Description': ['Spots', 'SpotDescription'],
        'Spot Composition': ['SpotCompositions', 'SpotCompositionName'],
        'Spot Composition Description': ['SpotCompositions', 'SpotCompositionDescription'],
        'Spot Context': ['SpotContexts', 'SpotContextName'],
        'Spot Context Description': ['SpotContexts', 'SpotContextDescription'],
        'UPb Spot Size': ['UPbAnalyses', 'SpotSize'],
        'UPb Spot Size Unit': ['UPbAnalyses', 'SpotSizeUnitID'],
        'Geochemical Spot Size': ['GeoChemicalAnalyses', 'SpotSize'],
        'Geochemical Spot Size Unit': ['GeoChemicalAnalyses', 'SpotSizeUnitID']
    }
}

reference_possible_user_input_fields = {
    'Reference': {
        'Authors': ['References', 'Authors'],
        'Year': ['References', 'Year'],
        'Title': ['References', 'Title'],
        'Source': ['References', 'Source'],
        'DOI': ['References', 'DOI'],
        'Reference Description': ['References', 'ReferenceDescription'],
        'Reference Display': ['References', 'ReferenceDisplay']
    }
}

upb_possible_user_input_fields = {
    'U-Pb Base Info': {
        'UPb Analysis Name': ['UPbAnalyses', 'UPbAnalysisName'],
        'UPb Analysis Description': ['UPbAnalyses', 'UPbAnalysesDescription'],
        'UPb Analysis Context': ['UPbAnalysisContexts', 'UPbAnalysisContext'],
        'UPb Analysis Context Description': ['UPbAnalysisContexts', 'UPbAnalysisContextDescription'],
        'Lab Facility Name': ['LabFacilities', 'LabFacilityName'],
        'Lab Facility Description': ['LabFacilities', 'LabFacilityDescription'],
        'Instrument Name': ['Instruments', 'InstrumentName'],
        'Instrument Description': ['Instruments', 'InstrumentDescription'],
        'UPb Analysis Method Name': ['UPbAnalysisMethods', 'UPbAnalysisMethodName'],
        'UPb Analysis Method Description': ['UPbAnalysisMethods', 'UPbAnalysisMethodDescription'],
        'Rejected': ['UPbAnalyses', 'Rejected'],
        'Rejection Reason': ['UPbRejectionReasons', 'UPbRejectionReasonName'],
        'Rejection Reason Description': ['UPbRejectionReasons', 'UPbRejectionReasonDescription']
    },
    'Ratios': {
        'U/Th': ['UPbAnalyses', 'U/Th'],
        'Th/U': ['UPbAnalyses', 'Th/U'],
        '206Pb/204Pb': ['UPbAnalyses', '206Pb/204Pb'],
        '206Pb/204Pb Error': ['UPbAnalyses', '206Pb/204PbError'],
        '204Pb/206Pb': ['UPbAnalyses', '204Pb/206Pb'],
        '204Pb/206Pb Error': ['UPbAnalyses', '204Pb/206PbError'],
        '207Pb/204Pb': ['UPbAnalyses', '207Pb/204Pb'],
        '207Pb/204Pb Error': ['UPbAnalyses', '207Pb/204PbError'],
        '204Pb/207Pb': ['UPbAnalyses', '204Pb/207Pb'],
        '204Pb/207Pb Error': ['UPbAnalyses', '204Pb/207PbError'],
        '208Pb/204Pb': ['UPbAnalyses', '208Pb/204Pb'],
        '208Pb/204Pb Error': ['UPbAnalyses', '208Pb/204PbError'],
        '204Pb/208Pb': ['UPbAnalyses', '204Pb/208Pb'],
        '204Pb/208Pb Error': ['UPbAnalyses', '204Pb/208PbError'],
        '206Pb/207Pb': ['UPbAnalyses', '206Pb/207Pb'],
        '206Pb/207Pb Error': ['UPbAnalyses', '206Pb/207PbError'],
        '207Pb/206Pb': ['UPbAnalyses', '207Pb/206Pb'],
        '207Pb/206Pb Error': ['UPbAnalyses', '207Pb/206PbError'],
        '204Pb/238U': ['UPbAnalyses', '204Pb/238U'],
        '204Pb/238U Error': ['UPbAnalyses', '204Pb/238UError'],
        '238U/204Pb': ['UPbAnalyses', '238U/204Pb'],
        '238U/204Pb Error': ['UPbAnalyses', '238U/204PbError'],
        '206Pb/238U': ['UPbAnalyses', '206Pb/238U'],
        '206Pb/238U Error': ['UPbAnalyses', '206Pb/238UError'],
        '238U/206Pb': ['UPbAnalyses', '238U/206Pb'],
        '238U/206Pb Error': ['UPbAnalyses', '238U/206PbError'],
        '207Pb/235U': ['UPbAnalyses', '207Pb/235U'],
        '207Pb/235U Error': ['UPbAnalyses', '207Pb/235UError'],
        '235U/207Pb': ['UPbAnalyses', '235U/207Pb'],
        '235U/207Pb Error': ['UPbAnalyses', '235U/207PbError'],
        '208Pb/232Th': ['UPbAnalyses', '208Pb/232Th'],
        '208Pb/232Th Error': ['UPbAnalyses', '208Pb/232ThError'],
        '232Th/208Pb': ['UPbAnalyses', '232Th/208Pb'],
        '232Th/208Pb Error': ['UPbAnalyses', '232Th/208PbError'],
        '238U/232Th': ['UPbAnalyses', '238U/232Th'],
        '238U/232Th Error': ['UPbAnalyses', '238U/232ThError'],
        '232Th/238U': ['UPbAnalyses', '232Th/238U'],
        '232Th/238U Error': ['UPbAnalyses', '232Th/238UError'],
        'ErrorCorr/Rho_68v76': ['UPbAnalyses', 'ErrorCorr/Rho_68v76'],
        'ErrorCorr/Rho_68v75': ['UPbAnalyses', 'ErrorCorr/Rho_68v75']
    },
    'Ages': {
        '207Pb/206PbAge': ['UPbAnalyses', '207Pb/206PbAge'],
        '207Pb/206PbAge Error': ['UPbAnalyses', '207Pb/206PbAgeError'],
        '207Pb/235UAge': ['UPbAnalyses', '207Pb/235UAge'],
        '207Pb/235UAge Error': ['UPbAnalyses', '207Pb/235UAgeError'],
        '206Pb/238UAge': ['UPbAnalyses', '206Pb/238UAge'],
        '206Pb/238UAge Error': ['UPbAnalyses', '206Pb/238UAgeError'],
        '208Pb/232ThAge': ['UPbAnalyses', '208Pb/232ThAge'],
        '208Pb/232ThAge Error': ['UPbAnalyses', '208Pb/232ThAgeError'],
        'Best Age': ['UPbAnalyses', 'BestAge'],
        'Best Age Error': ['UPbAnalyses', 'BestAgeError'],
        'Age Unit': ['UPbAnalyses', 'AgeUnitID'],
        'Age Error Format': ['UPbAnalyses', 'AgeErrorFormatID'],
        'Concordance_206Pb/238Uv207Pb/206Pb': ['UPbAnalyses', 'Concordance_206Pb/238Uv207Pb/206Pb'],
        'Concordance_206Pb/238Uv207Pb/235U': ['UPbAnalyses', 'Concordance_206Pb/238Uv207Pb/235U'],
        'Concordance Format': ['UPbAnalyses', 'ConcordanceFormatID'],
        'Minimum Segmented Discordance': ['UPbAnalyses', 'MinimumSegmentedDiscordance'],
        'Age Interpretation': ['AgeInterpretations', 'AgeInterpretationName'],
        'Age Interpretation Description': ['AgeInterpretations', 'AgeInterpretationDescription']
    },
    'Isotope Counts': {
        'Pb204cps': ['UPbAnalyses', 'Pb204cps'],
        'Pb206cps': ['UPbAnalyses', 'Pb206cps'],
        'Pb207cps': ['UPbAnalyses', 'Pb207cps'],
        'Pb208cps': ['UPbAnalyses', 'Pb208cps'],
        'Pb*cps': ['UPbAnalyses', 'Pb*cps'],
        'Th232cps': ['UPbAnalyses', 'Th232cps'],
        'U235cps': ['UPbAnalyses', 'U235cps'],
        'U238cps': ['UPbAnalyses', 'U238cps'],
        'Uppm': ['UPbAnalyses', 'Uppm'],
        'Thppm': ['UPbAnalyses', 'Thppm'],
        'Pbppm': ['UPbAnalyses', 'Pbppm'],
    },
}

geochem_possible_user_input_fields = {
    'Geochemical Base Info': {
        'Geochemical Analysis Name': ['GeoChemicalAnalyses', 'GeoChemAnalysisName'],
        'Geochemical Analysis Description': ['GeoChemicalAnalyses', 'GeoChemAnalysisDescription'],
        'Geochemical Analysis Context': ['GeoChemicalAnalysisContexts', 'GeoChemicalAnalysisContext'],
        'Geochemical Analysis Context Description': ['GeoChemicalAnalysisContexts', 'GeoChemicalAnalysisContextDescription'],
        'Geochemical Analyte Name': ['GeoChemicalAnalytes', 'GeoChemAnalyteName'],
        'Geochemical Analyte Description': ['GeoChemicalAnalytes', 'GeoChemAnalyteDescription'],
        'Lab Facility Name': ['LabFacilities', 'LabFacilityName'],
        'Lab Facility Description': ['LabFacilities', 'LabFacilityDescription'],
        'Instrument Name': ['Instruments', 'InstrumentName'],
        'Instrument Description': ['Instruments', 'InstrumentDescription'],
        'Geochemical Analysis Method Name': ['GeoChemicalMethods', 'GeoChemicalMethodName'],
        'Geochemical Analysis Method Description': ['GeoChemicalMethods', 'GeoChemicalMethodDescription'],
        'Rejected': ['GeoChemicalAnalyses', 'Rejected'],
        'Rejection Reason': ['GeoChemRejectionReasons', 'GeoChemRejectionReasonName'],
        'Rejection Reason Description': ['GeoChemRejectionReasons', 'GeoChemRejectionReasonDescription']
    },
    'Geochemical Analytes': {'Geochemical Analysis Units': ['GeoChemicalAnalysisValues', 'GeoChemAnalyteUnitID']},
    'Geochemical Analyte Errors': {'Geochemical Error Formats': ['GeoChemicalAnalysisValues', 'GeoChemAnalyteErrorFormatID']}
}
"""Dictionaries of User-readable columns/info able to be imported into the database with list of their associated table 
    and column name. Importer Category: {UserReadableColumnName: [TableName, ColumnName]}"""

import_formats = {
    'USGS Geochron U-Th-Pb in situ': {
        'template': 'U-Th-Pb_insitu_Template.xlsx',
        'header_label': 'Field',
        'header_rows': 4,
        'upb_sheet': 'U-Th-Pb insitu Data',
        'sheets': {
            'U-Th-Pb insitu Summary': {
                'Sample_ID': 'Sample Name',
                'SampleDesc': 'Sample Description',
                'IGSN': 'Sample IGSN',
                'GeologicalUnit': 'Unit',
                'SampleSrc': 'Sample Context',
                'CollectMethod': 'Sampling Method',
                'RockClass': 'Rock Type',
                'Lat': 'Sample Latitude degrees',
                'Long': 'Sample Longitude degrees',
                'Elevation': 'Sample Elevation',
                'Country': 'Region',
                'Age_Text': 'Direct Age',
                'AgeUnc_Text': 'Direct Age Error',
                'AgeIntpnType': 'Age Constraint',
                'AgeIntpnClass': 'Age Interpretation',
            },
            'U-Th-Pb insitu Data': {
                'Sample_ID': 'Sample Name',
                'SampleMaterial': 'Aliquot Name',
                'Analysis_ID': 'Spot Name',
                'U': 'Uppm',
                'Th': 'Thppm',
                'Pb': 'Pbppm',
                'Pb206Pb204': '206Pb/204Pb',
                'Pb206Pb204Unc': '206Pb/204Pb Error',
                'Pb208Pb204': '208Pb/204Pb',
                'Pb208Pb204Unc': '208Pb/204Pb Error',
                'Pb204Pb206': '204Pb/206Pb',
                'UTh': 'U/Th',
                'ThU': 'Th/U',
                'Pb206Pb207': '206Pb/207Pb',
                'Pb206Pb207Unc': '206Pb/207Pb Error',
                'Pb207U235': '207Pb/235U',
                'Pb207U235Unc': '207Pb/235U Error',
                'Pb206U238': '206Pb/238U',
                'Pb206U238Unc': '206Pb/238U Error',
                'RHOWetherill': 'ErrorCorr/Rho_68v75',
                'U238Pb206': '238U/206Pb',
                'U238Pb206Unc': '238U/206Pb Error',
                'Pb207Pb206': '207Pb/206Pb',
                'Pb207Pb206Unc': '207Pb/206Pb Error',
                'RHOTeraWasserburg': 'ErrorCorr/Rho_68v76',
                'Pb208Th232': '208Pb/232Th',
                'Pb208Th232Unc': '208Pb/232Th Error',
                'Th232U238': '232Th/238U',
                'Pb206U238Age': '206Pb/238UAge',
                'Pb206U238AgeUnc': '206Pb/238UAge Error',
                'Pb207U235Age': '207Pb/235UAge',
                'Pb207U235AgeUnc': '207Pb/235UAge Error',
                'Pb207Pb206Age': '207Pb/206PbAge',
                'Pb207Pb206AgeUnc2S': '207Pb/206PbAge Error',
                'Pb208Th232Age': '208Pb/232ThAge',
                'Pb208Th232AgeUnc': '208Pb/232ThAge Error',
                'Age_Text': 'Best Age',
                'AgeUnc_Text': 'Best Age Error',
                'PctDiscordW': 'Concordance_206Pb/238Uv207Pb/235U',
                'PctDiscordTW': 'Concordance_206Pb/238Uv207Pb/206Pb',
                'AgeIntpnClass': 'Age Interpretation',
                'DomainAnalyzed': 'Spot Context',
                'DomainDescript': 'Spot Description',
            }
        },
        'units_formats': {
            'Elevation Unit': 'm',
            'Sample Age Error': '2σ abs',
            'Age Unit': 'Ma',
            'U-Pb Age Error': '2σ abs',
            'Ratio Error': '2σ abs',
            'Concordance Format': 'Dis%'
        }
    }
}
"""Predefined input formats detected by the ImportWizard. Each format ships a static template workbook
(template) next to ImportWizard.py. A workbook matches when every template sheet has a sheet whose header_label row has
identical headings. header_rows template rows are disabled on input. upb_sheet is the template sheet set as the U-Pb
sheet. sheets maps template headings to importer fields from the *_possible_user_input_fields dictionaries.
units_formats keys are ImportWizard static_combos keys, values are combo display texts."""