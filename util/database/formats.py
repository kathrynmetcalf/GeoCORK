"""
Static format and unit definitions for GeoCORK.

Each format is declared once, as a member of an Enum. The tuple lists that
Create_database.py and other modules read are derived from those enums, so a
format is never declared in two places.

Tuple layout for every member: (name, abbreviation, description)
"""
from enum import Enum


class ConcordanceFormat(Enum):
    """Valid concordance formats. Used to create the ConcordanceFormats table"""

    def __init__(self, label, abbreviation, description):
        self.label = label
        self.abbreviation = abbreviation
        self.description = description

    def __new__(cls, label, abbreviation, description, to_base=None, from_base=None):
        obj = object.__new__(cls)
        obj._value_ = (label, abbreviation, description)  # .value stays the 3-tuple the existing code reads
        return obj

    CONCORDANCE_RATIO = (
        'Concordance ratio',
        'Con',
        'Ratio agreement between the 206Pb/238U age to the 207Pb/235U age'
    )
    CONCORDANCE_PERCENT = (
        'Concordance percent',
        'Con%',
        'Percent agreement between the 206Pb/238U age and the 207Pb/235U age'
    )
    DISCORDANCE_RATIO = (
        'Discordance ratio',
        'Dis',
        'Ratio disagreement between the 206Pb/238U age to the 207Pb/206Pb age'
    )
    DISCORDANCE_PERCENT = (
        'Discordance percent',
        'Dis%',
        'Percent disagreement between the 206Pb/238U age and the 207Pb/206Pb age'
    )
    MINIMUM_SEGMENTED_DISCORDANCE = (
        'Minimum segmented discordance',
        'MinSegDis',
        'Minimum of |206Pb/238U-207Pb/235U| ages and |206Pb/207Pb-207Pb/235U| ages'
    )


# Concordance formats that were in the v1.03 schema but have since been removed.
# They stay in the enum so older databases can still be migrated.
RETIRED_CONCORDANCE_FORMATS = {ConcordanceFormat.MINIMUM_SEGMENTED_DISCORDANCE}

# Current lists, in the same tuple shape the existing code reads.
concordance_formats = [m.value for m in ConcordanceFormat if m not in RETIRED_CONCORDANCE_FORMATS]
concordance_formats_v103 = [m.value for m in ConcordanceFormat]

CONCORDANCE_CONVERSIONS = {
    (ConcordanceFormat.CONCORDANCE_RATIO, ConcordanceFormat.CONCORDANCE_PERCENT): ('x*100', 'x/100'),
    (ConcordanceFormat.CONCORDANCE_RATIO, ConcordanceFormat.DISCORDANCE_RATIO): ('1-x', '1-x'),
    (ConcordanceFormat.CONCORDANCE_RATIO, ConcordanceFormat.DISCORDANCE_PERCENT): ('100*(1-x)', '1-(x/100)'),
    (ConcordanceFormat.CONCORDANCE_PERCENT, ConcordanceFormat.DISCORDANCE_RATIO): ('1-(x/100)', '100*(1-x)'),
    (ConcordanceFormat.CONCORDANCE_PERCENT, ConcordanceFormat.DISCORDANCE_PERCENT): ('100-x', '100-x'),
    (ConcordanceFormat.DISCORDANCE_RATIO, ConcordanceFormat.DISCORDANCE_PERCENT): ('x*100', 'x/100'),
}


class ErrorFormat(Enum):
    """Valid error formats. Used to create the ErrorFormats table."""
    ONE_SIGMA_ABSOLUTE = ('1 sigma absolute', '1σ abs', '1σ absolute uncertainty')
    TWO_SIGMA_ABSOLUTE = ('2 sigma absolute', '2σ abs', '2σ absolute uncertainty')
    ONE_SIGMA_PERCENT = ('1 sigma percent', '1σ %', '1σ percent uncertainty')
    TWO_SIGMA_PERCENT = ('2 sigma percent', '2σ %', '2σ percent uncertainty')


error_formats = [m.value for m in ErrorFormat]

ERROR_CONVERSIONS = {
    (ErrorFormat.ONE_SIGMA_ABSOLUTE, ErrorFormat.TWO_SIGMA_ABSOLUTE): ('x*2', 'x/2'),
    (ErrorFormat.ONE_SIGMA_ABSOLUTE, ErrorFormat.ONE_SIGMA_PERCENT): ('(x/y)*100', '(x/100)*y'),
    (ErrorFormat.ONE_SIGMA_ABSOLUTE, ErrorFormat.TWO_SIGMA_PERCENT): ('(x/y)*200', '(x/200)*y'),
    (ErrorFormat.TWO_SIGMA_ABSOLUTE, ErrorFormat.ONE_SIGMA_PERCENT): ('(x/y)*100/2', '(x/100)*2*y'),
    (ErrorFormat.TWO_SIGMA_ABSOLUTE, ErrorFormat.TWO_SIGMA_PERCENT): ('(x/y)*100', '(x/100)*y'),
    (ErrorFormat.ONE_SIGMA_PERCENT, ErrorFormat.TWO_SIGMA_PERCENT): ('x*2', 'x/2'),
}


class GPSFormat(Enum):
    """Valid GPS formats. Used to create the GPSFormats table."""
    DECIMAL_DEGREES_PM = ('Decimal degrees positive/negative', 'DD +/-',
                          'Decimal degrees with positive N and E and negative S and W')
    DECIMAL_DEGREES_CARDINAL = ('Decimal degrees cardinal', 'DD NSEW',
                                'Decimal degrees with cardinal directions')
    DEGREES_MINUTES_PM = ('Degrees minutes positive/negative', 'DDM +/-',
                          'Degrees and decimal minutes with positive N and E and negative S and W')
    DEGREES_MINUTES_CARDINAL = ('Degrees minutes cardinal', 'DDM NSEW',
                                'Degrees and decimal minutes with cardinal directions')
    DEGREES_MINUTES_SECONDS_PM = ('Degrees minutes seconds positive/negative', 'DMS +/-',
                                  'Degrees, minutes, and seconds with positive N and E and negative S and W')
    DEGREES_MINUTES_SECONDS_CARDINAL = ('Degrees minutes seconds cardinal', 'DMS NSEW',
                                        'Degrees, minutes, and seconds with cardinal directions')
    UTM = ('Universal Transverse Mercator (standard)', 'UTM',
           'Universal Transverse Mercator (standard) with zone, northing, and easting')


gps_formats = [m.value for m in GPSFormat]

