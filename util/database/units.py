from enum import Enum


class DirectionUnits(Enum):
    """
    Enum list of valid direction units. Used to create DirectionUnits table
    """
    NORTH = ('North', 'N', 'positive north')
    SOUTH = ('South', 'S', 'positive south')
    EAST = ('East', 'E', 'positive east')
    WEST = ('West', 'W', 'positive west')


class DistanceUnits(Enum):
    """
    Enum list of valid distance units. Used to create DistanceUnits table
    """
    KILOMETERS = ('Kilometers', 'km', '1000')
    METERS = ('Meters', 'm', '1')
    CENTIMETERS = ('Centimeters', 'cm', '0.01')
    MILLIMETERS = ('Millimeter', 'mm', '0.001')
    MICROMETERS = ('Micrometer', 'µm', '0.000001')
    MILES = ('Miles', 'mi', '5280')
    YARDS = ('Yards', 'yd', '3')
    FEET = ('Feet', 'ft', '1')
    INCHES = ('Inches', 'in', f'(1/12)')


class AgeUnits(Enum):
    """
    Enum list of valid age units. Used to create AgeUnits table
    """
    BILLION_YEARS = ('Billion years', 'Ga', '1000000000')
    MILLION_YEARS = ('Million years', 'Ma', '1000000')
    THOUSAND_YEARS = ('Thousand years', 'ka', '1000')
    YEARS = ('Years', 'a', '1')


class AnalyticalUnits(Enum):
    """
    Enum list of valid analytical units. Used to create AnalyticalUnits table
    """
    PARTS_PER_MILLION = ('Parts per million', 'ppm', 'Concentration in parts per million (mg/kg or μg/g)')
    PARTS_PER_BILLION = ('Parts per billion', 'ppb', 'Concentration in parts per billion (μg/kg or ng/g)')
    PARTS_PER_TRILLION = ('Parts per trillion', 'ppt', 'Concentration in parts per trillion (ng/kg or pg/g)')
    WEIGHT_PERCENT = ('Weight percent', 'wt%', 'Concentration as a percentage by weight')
    MICROGRAMS_PER_GRAM = ('Micrograms per gram', 'μg/g', 'Concentration in micrograms per gram (equivalent to ppm)')
    NANOGRAMS_PER_GRAM = ('Nanograms per gram', 'ng/g', 'Concentration in nanograms per gram (equivalent to ppb)')
    MILLIGRAMS_PER_KILOGRAM = ('Milligrams per kilogram', 'mg/kg',
                               'Concentration in milligrams per kilogram (equivalent to ppm)')
    MOLES_PER_GRAM = ('Moles per gram', 'mol/g', 'Concentration in moles per gram')
    ATOMS_PER_GRAM = ('Atoms per gram', 'atoms/g', 'Concentration in atoms per gram')
    COUNTS_PER_SECOND = ('Counts per second', 'cps', 'Raw signal intensity in counts per second')
    ISOTOPE_RATIO = ('Isotope ratio', 'ratio',
                     'Dimensionless ratio of two isotope abundances (e.g., 206Pb/238U, 87Sr/86Sr)')
    DELTA_NOTATION = ('Delta notation', 'δ‰',
                      'Per mil deviation of an isotope ratio from a reference standard (e.g., δ18O, δ13C)')
    EPSILON_NOTATION = ('Epsilon notation', 'ε',
                        'Parts per 10,000 deviation of an isotope ratio from a reference (e.g., εNd, εHf)')
    INITIAL_RATIO = ('Initial ratio', 'initial',
                     'Isotope ratio corrected for radiogenic ingrowth back to time of formation')
    ATOMIC_PERCENT = ('Atomic percent', 'at%', 'Isotope abundance as a percentage of total atoms of that element')
    FRACTIONAL_ABUNDANCE = ('Fractional abundance', 'fraction',
                            'Isotope abundance as a decimal fraction of total atoms of that element')

direction_units = [member.value for member in DirectionUnits]
distance_units = [member.value for member in DistanceUnits]
age_units = [member.value for member in AgeUnits]
analytical_units = [member.value for member in AnalyticalUnits]
