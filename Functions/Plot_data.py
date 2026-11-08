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
        columns = ([SQLUtils.qsample_id, SQLUtils.qsample_name, SQLUtils.qupb_id, SQLUtils.qupb_analysis_name,
                    SQLUtils.qupb_rejected, SQLUtils.qupb_error_corr_68v76, SQLUtils.qupb_error_corr_68v75]
                   + [column for pair in AGE_COLUMNS.values() for column in pair]
                   + [column for pair in RATIO_PAIRS.values() for ratio in pair for column in ratio]
                   + CONCORDANCE_COLUMNS)
        sql = (f'SELECT {", ".join(columns)}\nFROM UPbAnalyses\n{SQLUtils.upb_spot_join}\n'
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
