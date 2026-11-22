from enum import Enum


class DirectionUnits(Enum):
    """
    Enum list of valid direction units. Used to create DirectionUnits table
    """
    NORTH = ('North', 'N', 'positive north')
    SOUTH = ('South', 'S', 'positive south')
    EAST = ('East', 'E', 'positive east')
    WEST = ('West', 'W', 'positive west')

direction_units = [member.value for member in DirectionUnits]

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

distance_units = [member.value for member in DistanceUnits]

IMPERIAL_DISTANCE_UNITS = {DistanceUnits.MILES, DistanceUnits.YARDS, DistanceUnits.FEET, DistanceUnits.INCHES}
M_PER_FT = 0.3048  # International foot, exact


def _distance_conversion(from_unit: DistanceUnits, to_unit: DistanceUnits) -> str:
    f_from, f_to = from_unit.value[2], to_unit.value[2]
    from_imperial = from_unit in IMPERIAL_DISTANCE_UNITS
    to_imperial = to_unit in IMPERIAL_DISTANCE_UNITS
    if from_imperial == to_imperial:
        return f'x*{f_from}/{f_to}'
    if to_imperial:  # metric -> imperial
        return f'x*{f_from}/({M_PER_FT}*{f_to})'
    return f'x*({f_from}*{M_PER_FT})/{f_to}'  # imperial -> metric


_members = list(DistanceUnits)
DISTANCE_CONVERSIONS = {
    (a, b): (_distance_conversion(a, b), _distance_conversion(b, a))
    for i, a in enumerate(_members) for b in _members[i + 1:]
}


class AgeUnits(Enum):
    """
    Enum list of valid age units. Used to create AgeUnits table
    """
    BILLION_YEARS = ('Billion years', 'Ga', '1000000000')
    MILLION_YEARS = ('Million years', 'Ma', '1000000')
    THOUSAND_YEARS = ('Thousand years', 'ka', '1000')
    YEARS = ('Years', 'a', '1')

age_units = [member.value for member in AgeUnits]

# Third field of each AgeUnits member is its size in years.
def _age_conversion(from_unit: AgeUnits, to_unit: AgeUnits) -> str:
    return f'x*{from_unit.value[2]}/{to_unit.value[2]}'


_age_members = list(AgeUnits)
AGE_CONVERSIONS = {
    (a, b): (_age_conversion(a, b), _age_conversion(b, a))
    for i, a in enumerate(_age_members) for b in _age_members[i + 1:]
}

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

analytical_units = [member.value for member in AnalyticalUnits]

# Units within a group convert by simple scaling; the factor is the unit's size as a dimensionless fraction.
MASS_FRACTION_FACTORS = {
    AnalyticalUnits.PARTS_PER_MILLION: 1e-6,
    AnalyticalUnits.MILLIGRAMS_PER_KILOGRAM: 1e-6,
    AnalyticalUnits.MICROGRAMS_PER_GRAM: 1e-6,
    AnalyticalUnits.PARTS_PER_BILLION: 1e-9,
    AnalyticalUnits.NANOGRAMS_PER_GRAM: 1e-9,
    AnalyticalUnits.PARTS_PER_TRILLION: 1e-12,
    AnalyticalUnits.WEIGHT_PERCENT: 1e-2,
}
ATOM_FRACTION_FACTORS = {
    AnalyticalUnits.ATOMIC_PERCENT: 1e-2,
    AnalyticalUnits.FRACTIONAL_ABUNDANCE: 1.0,
}
AVOGADRO = '6.02214076e23'  # exact (2019 SI)

# Placeholder for pairs that need outside context (element mass, reference standard, decay constant,
# instrument calibration), e.g. cps -> concentration, delta -> epsilon, initial -> measured ratio.
NO_SIMPLE_CONVERSION = '-'


def _analytical_conversion(from_unit: AnalyticalUnits, to_unit: AnalyticalUnits) -> str:
    for factors in (MASS_FRACTION_FACTORS, ATOM_FRACTION_FACTORS):
        if from_unit in factors and to_unit in factors:
            factor = factors[from_unit] / factors[to_unit]
            return 'x' if factor == 1.0 else f'x*{factor:g}'
    if (from_unit, to_unit) == (AnalyticalUnits.MOLES_PER_GRAM, AnalyticalUnits.ATOMS_PER_GRAM):
        return f'x*{AVOGADRO}'
    if (from_unit, to_unit) == (AnalyticalUnits.ATOMS_PER_GRAM, AnalyticalUnits.MOLES_PER_GRAM):
        return f'x/{AVOGADRO}'
    return NO_SIMPLE_CONVERSION


_analytical_members = list(AnalyticalUnits)
ANALYTICAL_CONVERSIONS = {
    (a, b): (_analytical_conversion(a, b), _analytical_conversion(b, a))
    for i, a in enumerate(_analytical_members) for b in _analytical_members[i + 1:]
}