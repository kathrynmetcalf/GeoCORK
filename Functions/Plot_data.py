"""
Data providers for the plot dialog. A provider loads one kind of data for a set of SampleIDs and returns a pandas
DataFrame with at least SampleID and SampleName columns. Plot types declare which provider they use by key.

Adding a data source (e.g. geochemistry for pyrolite REE spider plots):
    @register_provider
    class GeoChemData(DataProvider):
        key = 'geochem'
        label = 'Geochemistry'
        options = [Option('normalize', 'Normalize to', 'choice', 'Chondrite_PON', ['Chondrite_PON', 'PM_PON'])]
        def fetch(self, sample_ids): ...   # one row per analysis or sample, columns per analyte
        def prepare(self, df, opts): ...  # unit conversion / filtering
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from PyQt6 import QtSql as QtS

import Functions.SQLUtils as SQLUtils
import logger_setup
from Functions.Settings_manager import SettingsManager

settings = SettingsManager().settings


@dataclass
class Option:
    """User-adjustable setting shown in the plot dialog. kind: 'float', 'int', 'bool', 'choice' or 'text'."""
    name: str
    label: str
    kind: str
    default: object
    choices: list = field(default_factory=list)
    minimum: float = 0
    maximum: float = 1e9
    tooltip: str = ''


DATA_PROVIDERS: dict[str, 'DataProvider'] = {}


def register_provider(cls):
    DATA_PROVIDERS[cls.key] = cls()
    return cls


class DataProvider:
    key = ''
    label = ''
    options: list[Option] = []

    def __init__(self):
        self._cache: dict[tuple, pd.DataFrame] = {}

    def load(self, sample_ids: list[int], opts: dict) -> pd.DataFrame:
        """Cached fetch for the sample set, then option-dependent preparation."""
        key = tuple(sorted(sample_ids))
        if key not in self._cache:
            self._cache = {key: self.fetch(list(key))}  # keep only the latest set
        return self.prepare(self._cache[key].copy(), opts)

    def clear_cache(self):
        self._cache = {}

    def fetch(self, sample_ids: list[int]) -> pd.DataFrame:
        raise NotImplementedError

    def prepare(self, df: pd.DataFrame, opts: dict) -> pd.DataFrame:
        return df


def query_frame(sql: str) -> pd.DataFrame:
    query = QtS.QSqlQuery()
    if not query.exec(sql):
        logger_setup.get_logger().critical('Error loading plot data')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        logger_setup.get_logger().debug(f'SQL query: {query.lastQuery()}')
        return pd.DataFrame()
    fields = [query.record().fieldName(i) for i in range(query.record().count())]
    rows = []
    while query.next():
        rows.append([None if query.isNull(i) else query.value(i) for i in range(len(fields))])
    return pd.DataFrame(rows, columns=fields)


def lookup(table: str, id_column: str, value_column: str, row_id) -> str:
    query = QtS.QSqlQuery()
    query.prepare(f'SELECT {value_column} FROM {table} WHERE {id_column} = ?')
    query.addBindValue(row_id)
    if query.exec() and query.next():
        return query.value(0)
    return ''


def error_to_1s_relative(error: pd.Series, value: pd.Series, error_format: str) -> pd.Series:
    """Errors in an ErrorFormats abbreviation ('1σ abs', '2σ abs', '1σ %', '2σ %') to 1σ relative."""
    error = pd.to_numeric(error, errors='coerce')
    value = pd.to_numeric(value, errors='coerce')
    relative = error / 100 if '%' in error_format else error / value.abs()
    return relative / 2 if error_format.startswith('2') else relative


AGE_UNIT_TO_MA = {unit[1]: float(unit[2]) / 1e6 for unit in SQLUtils.age_units}
"""AgeUnits abbreviation: factor to Ma, from SQLUtils.age_units (years per unit)"""

AGE_COLUMNS = {
    'Best age (filled)': (SQLUtils.qupb_calc_best_age_filled, SQLUtils.qupb_calc_best_age_filled_error),
    'Best age': (SQLUtils.qupb_calc_best_age, SQLUtils.qupb_calc_best_age_error),
    '206Pb/238U': (SQLUtils.qupb_calc_206238_age, SQLUtils.qupb_calc_206238_age_error),
    '207Pb/206Pb': (SQLUtils.qupb_calc_207206_age, SQLUtils.qupb_calc_207206_age_error),
    '207Pb/235U': (SQLUtils.qupb_calc_207235_age, SQLUtils.qupb_calc_207235_age_error),
    '208Pb/232Th': (SQLUtils.qupb_calc_208232_age, SQLUtils.qupb_calc_208232_age_error),
}
"""Display name: (age column, age error column) as SQLUtils select strings"""

RATIO_PAIRS = {
    '206Pb/238U': ((SQLUtils.qupb_calc_206238, SQLUtils.qupb_calc_206238_error),
                   (SQLUtils.qupb_calc_238206, SQLUtils.qupb_calc_238206_error)),
    '207Pb/206Pb': ((SQLUtils.qupb_calc_207206, SQLUtils.qupb_calc_207206_error),
                    (SQLUtils.qupb_calc_206207, SQLUtils.qupb_calc_206207_error)),
    '207Pb/235U': ((SQLUtils.qupb_calc_207235, SQLUtils.qupb_calc_207235_error),
                   (SQLUtils.qupb_calc_235207, SQLUtils.qupb_calc_235207_error)),
}
"""Ratio: ((ratio, error), (reciprocal, error)). Reciprocal ratios share the same relative uncertainty."""

CONCORDANCE_COLUMNS = [SQLUtils.qupb_calc_concordance_68v76, SQLUtils.qupb_calc_concordance_68v75]


def alias(select: str) -> str:
    """Output column name of a SQLUtils select string ('... AS "Alias"')."""
    return select.rsplit(' AS ', 1)[1].strip('"')


def discordance_percent(values: pd.Series, concordance_format: str) -> pd.Series:
    """Stored concordance in a ConcordanceFormats abbreviation (Con, Con%, Dis, Dis%) to discordance in %."""
    values = pd.to_numeric(values, errors='coerce')
    return {'Con': (1 - values) * 100, 'Con%': 100 - values, 'Dis': values * 100}.get(concordance_format, values)


@register_provider
class UPbData(DataProvider):
    """
    U-Pb analyses for the selected samples. prepare() returns Age/Age1s in Ma and 1σ absolute, plus ratio columns
    R_<ratio>, R_<ratio>_1s (1σ absolute) and rho_68v76/rho_68v75, after rejection and discordance filters.
    """
    key = 'upb'
    label = 'U-Pb analyses'
    options = [
        Option('age_column', 'Age', 'choice', 'Best age (filled)', list(AGE_COLUMNS)),
        Option('exclude_rejected', 'Exclude rejected', 'bool', True),
        Option('max_discordance', 'Max |discordance| (%)', 'float', 0, minimum=0, maximum=100,
               tooltip='0 disables the filter. Uses 206Pb/238U v 207Pb/206Pb concordance, else v 207Pb/235U.'),
    ]

    def fetch(self, sample_ids: list[int]) -> pd.DataFrame:
        if not sample_ids:
            return pd.DataFrame()
        columns = ([SQLUtils.qsample_id, SQLUtils.qsample_name, SQLUtils.qspot_id, SQLUtils.qgrain_id,
                    SQLUtils.qupb_id, SQLUtils.qupb_analysis_name,
                    SQLUtils.qupb_rejected, SQLUtils.qupb_error_corr_68v76, SQLUtils.qupb_error_corr_68v75]
                   + [column for pair in AGE_COLUMNS.values() for column in pair]
                   + [column for pair in RATIO_PAIRS.values() for ratio in pair for column in ratio]
                   + CONCORDANCE_COLUMNS)
        sql = (f'SELECT {", ".join(columns)}\nFROM UPbAnalyses\n{SQLUtils.upb_spot_join}\n{SQLUtils.spot_grain_join}\n'
               f'{SQLUtils.spot_aliquot_join}\n{SQLUtils.aliquot_sample_join}\n'
               f'WHERE Samples.SampleID IN ({", ".join(str(int(i)) for i in sample_ids)})')
        return query_frame(sql)

    def prepare(self, df: pd.DataFrame, opts: dict) -> pd.DataFrame:
        if df.empty:
            return df
        to_ma = AGE_UNIT_TO_MA.get(lookup('AgeUnits', 'AgeUnitID', 'AgeUnitAbbreviation',
                                          settings.value('age_unit_id')), 1.0)
        age_format = lookup('ErrorFormats', 'ErrorFormatID', 'ErrorFormatAbbreviation',
                            settings.value('age_error_format_id'))
        ratio_format = lookup('ErrorFormats', 'ErrorFormatID', 'ErrorFormatAbbreviation',
                              settings.value('ratio_error_format_id'))
        concordance_format = lookup('ConcordanceFormats', 'ConcordanceFormatID', 'ConcordanceFormatAbbreviation',
                                    settings.value('concordance_format_id'))

        age_column, error_column = (alias(c) for c in AGE_COLUMNS[opts.get('age_column', 'Best age (filled)')])
        age = pd.to_numeric(df[age_column], errors='coerce')
        df['Age'] = age * to_ma
        df['Age1s'] = error_to_1s_relative(df[error_column], age, age_format) * df['Age']

        for ratio, ((value_col, error_col), (recip_col, recip_error_col)) in RATIO_PAIRS.items():
            value = pd.to_numeric(df[alias(value_col)], errors='coerce')
            relative = error_to_1s_relative(df[alias(error_col)], value, ratio_format)
            relative = relative.fillna(error_to_1s_relative(df[alias(recip_error_col)], df[alias(recip_col)], ratio_format))
            df[f'R_{ratio}'] = value
            df[f'R_{ratio}_1s'] = relative * value
        df['rho_68v76'] = pd.to_numeric(df['ErrorCorr/Rho_68v76'], errors='coerce')
        df['rho_68v75'] = pd.to_numeric(df['ErrorCorr/Rho_68v75'], errors='coerce')

        df['Discordance%'] = discordance_percent(df[alias(CONCORDANCE_COLUMNS[0])], concordance_format).fillna(
            discordance_percent(df[alias(CONCORDANCE_COLUMNS[1])], concordance_format))
        if opts.get('exclude_rejected', True):
            df = df[df['Rejected'] != 'Rejected']
        if opts.get('max_discordance'):
            df = df[df['Discordance%'].isna() | (df['Discordance%'].abs() <= opts['max_discordance'])]
        return df.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------- geochemistry

PPM_FACTORS = {'Parts per million': 1, 'Micrograms per gram': 1, 'Milligrams per kilogram': 1,
               'Parts per billion': 1e-3, 'Nanograms per gram': 1e-3, 'Parts per trillion': 1e-6,
               'Weight percent': 1e4}
"""AnalyticalUnits name: factor to ppm for mass-fraction units"""
UNIT_TO_PPM = {unit[1]: PPM_FACTORS[unit[0]] for unit in SQLUtils.analytical_units if unit[0] in PPM_FACTORS}
"""AnalyticalUnits abbreviation (from SQLUtils.analytical_units): factor to ppm"""

GEOCHEM_ANALYTE_JOIN = ('LEFT JOIN GeoChemicalAnalytes '
                        'ON GeoChemicalAnalysisValues.GeoChemAnalyteID = GeoChemicalAnalytes.GeoChemAnalyteID')
"""SQLUtils.geochem_analyte_join joins on GeoChemicalAnalyses.GeoChemAnalyteID, which is not a column of the current
GeoChemicalAnalyses table; GeoChemAnalyteID is in GeoChemicalAnalysisValues."""

REFERENCE_COMPOSITIONS = [
    'Chondrite_PON', 'Chondrite_MS95', 'Chondrite_SM89', 'ChondriteREE_ON', 'PM_PON', 'PM_SM89', 'Pyrolite_MS95',
    'DMM_WH2005', 'E-DMM_WH2005', 'D-DMM_WH2005', 'DM_SS2004', 'NMORB_Gale2013', 'NMORB_SM89', 'EMORB_Gale2013',
    'EMORB_SM89', 'DMORB_Gale2013', 'MORB_Gale2013', 'OIB_SM89', 'UCC_McLennan2001', 'UCC_RG2003', 'UCC_RG2014',
    'MCC_RG2014', 'LCC_McLennan2001', 'LCC_RG2003', 'LCC_RG2014', 'BCC_McLennan2001', 'BCC_RG2003', 'BCC_RG2014',
    'PAAS_Pourmand2012', 'PAAS_TM1985', 'NASC_Gromet1984', 'EUS_Bau2018', 'PHS_Condie1993', 'PRS_Condie1993',
    'ARS_Condie1993', 'MUQ_Kamber2005', 'GLOSS_P2014', 'GLOSS2_P2014']
"""pyrolite.geochem.norm reference compositions offered for normalization"""


@register_provider
class GeoChemData(DataProvider):
    """
    Geochemical analyses for the selected samples, pivoted to one row per analysis (or per sample) with one column per
    GeoChemAnalyteAbbreviation in ppm. Values in non-mass-fraction units (cps, ratios, delta, epsilon, ...) are excluded
    and counted in attrs['excluded_values'].
    """
    key = 'geochem'
    label = 'Geochemical analyses'
    options = [
        Option('level', 'Plot', 'choice', 'Analyses', ['Analyses', 'Sample mean']),
        Option('exclude_rejected', 'Exclude rejected', 'bool', True),
    ]
    index = ['SampleID', 'SampleName', 'GeoChemAnalysisID', 'GeoChemAnalysisName']

    def fetch(self, sample_ids: list[int]) -> pd.DataFrame:
        if not sample_ids:
            return pd.DataFrame()
        columns = [SQLUtils.qsample_id, SQLUtils.qsample_name, SQLUtils.qgeochem_id, SQLUtils.qgeochem_analysis_name,
                   SQLUtils.qgeochem_rejected, SQLUtils.qgeochem_analyte_abbreviation, SQLUtils.qgeochem_analyte_value,
                   SQLUtils.qgeochem_analyte_unit, SQLUtils.qgeochem_analyte_error, SQLUtils.qgeochem_analyte_error_format]
        sql = (f'SELECT {", ".join(columns)}\nFROM GeoChemicalAnalyses\n{SQLUtils.geochem_spot_join}\n'
               f'{SQLUtils.spot_aliquot_join}\n{SQLUtils.aliquot_sample_join}\n{SQLUtils.geochem_analyte_value_join}\n'
               f'{GEOCHEM_ANALYTE_JOIN}\n{SQLUtils.geochem_analyte_unit_join}\n{SQLUtils.geochem_analyte_error_format_join}\n'
               f'WHERE Samples.SampleID IN ({", ".join(str(int(i)) for i in sample_ids)})')
        return query_frame(sql)

    def prepare(self, df: pd.DataFrame, opts: dict) -> pd.DataFrame:
        if df.empty:
            return df
        if opts.get('exclude_rejected', True):
            df = df[df['Rejected'] != 'Rejected']
        factor = df['GeoChemAnalyteUnitAbbreviation'].map(UNIT_TO_PPM)
        excluded = int((factor.isna() & df['GeoChemAnalyteValue'].notna()).sum())
        df = df[factor.notna()].assign(ppm=pd.to_numeric(df['GeoChemAnalyteValue'], errors='coerce') * factor)
        if df.empty:
            out = pd.DataFrame(columns=self.index)
        else:
            out = df.pivot_table(index=self.index, columns='GeoChemAnalyteAbbreviation', values='ppm',
                                 aggfunc='mean').reset_index()
            out.columns.name = None
            if opts.get('level') == 'Sample mean':
                out = out.drop(columns=['GeoChemAnalysisID', 'GeoChemAnalysisName']).groupby(
                    ['SampleID', 'SampleName'], as_index=False).mean()
        out.attrs['excluded_values'] = excluded
        return out


# ---------------------------------------------------------------- U-Pb age paired with epsilon Hf

HF_ANALYTES = ['E_Hf', 'E_Hf(T)']
"""GeoChemAnalyteAbbreviation values read as stored (not calculated from 176Hf/177Hf)"""


@register_provider
class UPbHfData(DataProvider):
    """
    Stored epsilon Hf values (GeoChemicalAnalysisValues, any unit) paired with the U-Pb age of the same spot, or
    optionally of the same grain. prepare() returns one row per Hf value with Age/Age1s (Ma, 1σ) and EHf/EHf1s (1σ).
    U-Pb filters (age column, rejected, discordance) are the same as for the U-Pb plots.
    """
    key = 'upb_hf'
    label = 'U-Pb age + εHf'
    options = UPbData.options + [
        Option('hf_analyte', 'εHf analyte', 'choice', 'E_Hf', HF_ANALYTES),
        Option('match', 'Pair age by', 'choice', 'Spot', ['Spot', 'Spot, then grain'],
               tooltip='Spot: U-Pb analysis on the same spot. Spot, then grain: otherwise any U-Pb analysis on the same grain.'),
    ]

    def fetch(self, sample_ids: list[int]) -> dict:
        if not sample_ids:
            return {'upb': pd.DataFrame(), 'hf': pd.DataFrame()}
        columns = [SQLUtils.qsample_id, SQLUtils.qsample_name, SQLUtils.qspot_id, SQLUtils.qgrain_id,
                   SQLUtils.qgeochem_id, SQLUtils.qgeochem_analysis_name, SQLUtils.qgeochem_rejected,
                   SQLUtils.qgeochem_analyte_abbreviation, SQLUtils.qgeochem_analyte_value,
                   SQLUtils.qgeochem_analyte_error, SQLUtils.qgeochem_analyte_error_format]
        analytes = ', '.join(f"'{a}'" for a in HF_ANALYTES)
        sql = (f'SELECT {", ".join(columns)}\nFROM GeoChemicalAnalyses\n{SQLUtils.geochem_spot_join}\n'
               f'{SQLUtils.spot_grain_join}\n{SQLUtils.spot_aliquot_join}\n{SQLUtils.aliquot_sample_join}\n'
               f'{SQLUtils.geochem_analyte_value_join}\n{GEOCHEM_ANALYTE_JOIN}\n{SQLUtils.geochem_analyte_error_format_join}\n'
               f'WHERE Samples.SampleID IN ({", ".join(str(int(i)) for i in sample_ids)}) '
               f'AND GeoChemicalAnalytes.GeoChemAnalyteAbbreviation IN ({analytes})')
        return {'upb': DATA_PROVIDERS['upb'].fetch(sample_ids), 'hf': query_frame(sql)}

    def load(self, sample_ids: list[int], opts: dict) -> pd.DataFrame:
        key = tuple(sorted(sample_ids))
        if key not in self._cache:
            self._cache = {key: self.fetch(list(key))}
        return self.prepare({name: df.copy() for name, df in self._cache[key].items()}, opts)

    def prepare(self, frames: dict, opts: dict) -> pd.DataFrame:
        hf = frames['hf']
        if hf.empty:
            return hf
        hf = hf[hf['GeoChemAnalyteAbbreviation'] == opts.get('hf_analyte', 'E_Hf')]
        if opts.get('exclude_rejected', True):
            hf = hf[hf['Rejected'] != 'Rejected']
        value = pd.to_numeric(hf['GeoChemAnalyteValue'], errors='coerce')
        error_1s = [error_to_1s_relative(pd.Series([e]), pd.Series([v]), f or '1σ abs').iloc[0] * abs(v)
                    for e, v, f in zip(hf['GeoChemAnalyteError'], value, hf['GeoChemAnalyteErrorFormatAbbreviation'])]
        hf = hf.assign(EHf=value, EHf1s=error_1s).dropna(subset=['EHf'])

        upb = DATA_PROVIDERS['upb'].prepare(frames['upb'], opts) if not frames['upb'].empty else frames['upb']
        upb = upb.dropna(subset=['Age']) if not upb.empty else upb
        if upb.empty:
            return hf.assign(Age=np.nan, Age1s=np.nan, PairedBy='')
        by_spot = upb.groupby('SpotID')[['Age', 'Age1s']].mean()
        out = hf.join(by_spot, on='SpotID')
        out['PairedBy'] = np.where(out['Age'].notna(), 'Spot', '')
        if opts.get('match') == 'Spot, then grain':
            by_grain = upb.dropna(subset=['GrainID']).groupby('GrainID')[['Age', 'Age1s']].mean()
            grain = out[['GrainID']].join(by_grain, on='GrainID')
            fill = out['Age'].isna() & grain['Age'].notna()
            out.loc[fill, ['Age', 'Age1s']] = grain.loc[fill, ['Age', 'Age1s']].to_numpy()
            out.loc[fill, 'PairedBy'] = 'Grain'
        return out