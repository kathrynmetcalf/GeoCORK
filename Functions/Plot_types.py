"""
Plot types for the plot dialog. Each plot declares a category (menu group), the data provider it reads from, its
options, and a draw() that renders into a matplotlib Figure. Register new plots with @register_plot.

Example of a future geochemistry plot (pyrolite):
    @register_plot
    class REESpider(PlotType):
        name = 'REE spider'
        category = 'Geochemistry'
        data = 'geochem'
        def draw(self, fig, df, opts):
            ax = fig.add_subplot()
            for (sample_id, name), group in df.groupby(['SampleID', 'SampleName']):
                group.pyrochem.REE.pyrochem.normalize_to(opts['normalize']).pyroplot.REE(ax=ax, label=name)
"""
import math

import numpy as np
import pandas as pd

from Functions.Plot_data import Option

PLOT_TYPES: dict[str, 'PlotType'] = {}


def register_plot(cls):
    PLOT_TYPES[cls.name] = cls()
    return cls


class PlotType:
    name = ''
    category = ''
    data = ''
    """DATA_PROVIDERS key"""
    options: list[Option] = []

    def draw(self, fig, df: pd.DataFrame, opts: dict) -> str:
        """Draw into fig (already cleared). Return a short status message."""
        raise NotImplementedError


def groups(df: pd.DataFrame, opts: dict) -> list[tuple[str, pd.DataFrame]]:
    """(label, rows) per sample, or one group of all selected samples when opts['grouping'] is 'Combined'."""
    if opts.get('grouping') == 'Combined':
        names = df['SampleName'].unique()
        label = names[0] if len(names) == 1 else f'{len(names)} samples combined'
        return [(label, df)]
    return [(name, group) for name, group in df.groupby('SampleName', sort=True)]


GROUPING = Option('grouping', 'Samples', 'choice', 'Separate', ['Separate', 'Combined'])


# ---------------------------------------------------------------- age distributions (detritalPy)

class AgeDistribution(PlotType):
    category = 'U-Pb'
    data = 'upb'
    common_options = [
        GROUPING,
        Option('layout', 'Layout', 'choice', 'Stacked', ['Stacked', 'Overlay']),
        Option('x1', 'Age min (Ma)', 'float', 0, maximum=4500),
        Option('x2', 'Age max (Ma)', 'float', 4000, maximum=4500),
        Option('log_x', 'Log age axis', 'bool', False),
        Option('show_ages', 'Show individual ages', 'bool', True),
    ]
    max_stacked = 12
    ylabel = 'Probability'
    legend_loc = 'upper right'

    def curves(self, ages: list[np.ndarray], errors: list[np.ndarray], opts: dict):
        """Return (x, [y per group]) from detritalPy."""
        raise NotImplementedError

    def draw(self, fig, df, opts):
        df = df.dropna(subset=['Age'])
        if self.needs_errors:
            df = df.dropna(subset=['Age1s'])
            df = df[df['Age1s'] > 0]
        if df.empty:
            return 'No ages to plot for the selected samples'
        sets = groups(df, opts)
        note = ''
        if opts['layout'] == 'Stacked' and len(sets) > self.max_stacked:
            note = f'; showing first {self.max_stacked} of {len(sets)} samples (use Overlay or Combined for all)'
            sets = sets[:self.max_stacked]
        x1, x2 = sorted((opts['x1'], opts['x2']))
        x, ys = self.curves([g['Age'].to_numpy() for _, g in sets], [g['Age1s'].to_numpy() for _, g in sets],
                            dict(opts, x1=x1, x2=x2))
        stacked = opts['layout'] == 'Stacked' and len(sets) > 1
        axes = fig.subplots(len(sets), 1, sharex=True, squeeze=False)[:, 0] if stacked else [fig.add_subplot()] * len(sets)
        for i, ((label, group), y, ax) in enumerate(zip(sets, ys, axes)):
            color = f'C{i % 10}'
            self.plot_curve(ax, x, y, group, color, f'{label} (n={len(group)})')
            if opts['show_ages']:
                ax.plot(group['Age'], np.zeros(len(group)) - (0.02 + 0.015 * (0 if stacked else i)) * np.nanmax(y),
                        '|', color=color, ms=8, alpha=0.7, transform=ax.transData)
            ax.legend(loc=self.legend_loc, fontsize='small', frameon=False)
            ax.set_ylabel(self.ylabel if not stacked else '')
        for ax in set(axes):
            ax.set_xlim(x1 if not opts['log_x'] else max(x1, 1), x2)
            ax.set_xscale('log' if opts['log_x'] else 'linear')
            if self.ylabel == 'Probability':
                ax.set_yticks([])
            ax.spines[['top', 'right']].set_visible(False)
        axes[-1].set_xlabel('Age (Ma)')
        if stacked:
            fig.supylabel(self.ylabel, fontsize='medium')
        return f'{len(df)} analyses from {df["SampleID"].nunique()} samples{note}'

    def plot_curve(self, ax, x, y, group, color, label):
        ax.fill_between(x, y, color=color, alpha=0.35, lw=0)
        ax.plot(x, y, color=color, lw=1, label=label)

    needs_errors = False


@register_plot
class KDEPlot(AgeDistribution):
    name = 'Kernel density estimate (KDE)'
    options = AgeDistribution.common_options + [
        Option('bw_method', 'Bandwidth', 'choice', 'Fixed', ['Fixed', 'optimizedFixed', 'optimizedVariable', 'ISJ',
                                                              'scott', 'silverman']),
        Option('bw', 'Fixed bandwidth (Myr)', 'float', 10, minimum=0.1, maximum=500),
    ]

    def curves(self, ages, errors, opts):
        import detritalpy.detritalFuncs as dFunc
        bw = opts['bw'] if opts['bw_method'] == 'Fixed' else opts['bw_method']
        return dFunc.KDEcalcAges(ages, x1=opts['x1'], x2=opts['x2'], xdif=1, bw=bw)


@register_plot
class PDPPlot(AgeDistribution):
    name = 'Probability density plot (PDP)'
    needs_errors = True
    options = AgeDistribution.common_options

    def curves(self, ages, errors, opts):
        import detritalpy.detritalFuncs as dFunc
        return dFunc.PDPcalcAges(ages, errors, x1=opts['x1'], x2=opts['x2'], xdif=1)


@register_plot
class KDEHistogram(KDEPlot):
    name = 'KDE + histogram'
    options = KDEPlot.options + [Option('bin_width', 'Bin width (Myr)', 'float', 50, minimum=1, maximum=1000)]

    def draw(self, fig, df, opts):
        self._opts = opts
        return super().draw(fig, df, opts)

    def plot_curve(self, ax, x, y, group, color, label):
        counts, edges = np.histogram(group['Age'], bins=np.arange(min(x), max(x) + self._opts['bin_width'],
                                                                  self._opts['bin_width']))
        twin = ax.twinx()
        twin.bar(edges[:-1], counts, width=np.diff(edges), align='edge', color=color, alpha=0.25, edgecolor='white')
        twin.set_ylabel('Count', fontsize='small')
        twin.spines[['top']].set_visible(False)
        ax.set_zorder(twin.get_zorder() + 1)
        ax.patch.set_visible(False)
        ax.plot(x, y, color=color, lw=1.5, label=label)


@register_plot
class CDFPlot(AgeDistribution):
    name = 'Cumulative distribution (CDF)'
    ylabel = 'Cumulative proportion'
    legend_loc = 'lower right'
    options = [GROUPING, Option('layout', 'Layout', 'choice', 'Overlay', ['Overlay', 'Stacked'])] + \
        AgeDistribution.common_options[2:5]

    def curves(self, ages, errors, opts):
        import detritalpy.detritalFuncs as dFunc
        return dFunc.CDFcalcAges(ages, x1=opts['x1'], x2=opts['x2'], xdif=1)

    def draw(self, fig, df, opts):
        return super().draw(fig, df, dict(opts, show_ages=False))

    def plot_curve(self, ax, x, y, group, color, label):
        ax.plot(x, y, color=color, lw=2, label=label)
        ax.set_ylim(0, 1.02)


# ---------------------------------------------------------------- concordia diagrams

LAMBDA_238 = 1.55125e-10  # Jaffey et al. (1971), 1/yr
LAMBDA_235 = 9.8485e-10
U238_U235 = 137.818  # Hiess et al. (2012)


def ellipse(x, y, sx, sy, rho, scale, n=48):
    """Error ellipse outline for 1σ uncertainties sx, sy and correlation rho, scaled by `scale` sigma."""
    cov = np.array([[sx * sx, rho * sx * sy], [rho * sx * sy, sy * sy]])
    values, vectors = np.linalg.eigh(cov)
    t = np.linspace(0, 2 * np.pi, n)
    circle = np.stack([np.cos(t), np.sin(t)])
    points = vectors @ (np.sqrt(np.clip(values, 0, None))[:, None] * circle) * scale
    return x + points[0], y + points[1]


class Concordia(PlotType):
    category = 'U-Pb'
    data = 'upb'
    x_ratio = y_ratio = rho_column = ''
    xlabel = ylabel = ''
    options = [
        GROUPING,
        Option('sigma', 'Ellipses', 'choice', '2σ', ['1σ', '2σ']),
        Option('fill', 'Fill ellipses', 'bool', True),
        Option('tick_step', 'Concordia tick spacing (Ma, 0 = auto)', 'float', 0, maximum=4500),
    ]

    def curve(self, t_years: np.ndarray):
        raise NotImplementedError

    def rho(self, df, opts) -> pd.Series:
        return df[self.rho_column].fillna(0)

    def draw(self, fig, df, opts):
        x_col, y_col = f'R_{self.x_ratio}', f'R_{self.y_ratio}'
        df = df.dropna(subset=[x_col, y_col, f'{x_col}_1s', f'{y_col}_1s'])
        if df.empty:
            return f'No analyses with {self.x_ratio} and {self.y_ratio} ratios and uncertainties'
        ax = fig.add_subplot()
        scale = 1 if opts['sigma'] == '1σ' else 2
        rho = self.rho(df, opts).clip(-0.999, 0.999)
        for i, (label, group) in enumerate(groups(df, opts)):
            color = f'C{i % 10}'
            for (_, row), r in zip(group.iterrows(), rho.loc[group.index]):
                ex, ey = ellipse(row[x_col], row[y_col], row[f'{x_col}_1s'], row[f'{y_col}_1s'], r, scale)
                ax.fill(ex, ey, facecolor=color if opts['fill'] else 'none', alpha=0.3 if opts['fill'] else 1,
                        edgecolor=color, lw=0.8)
            ax.plot([], [], 's', color=color, alpha=0.5, label=f'{label} (n={len(group)})')
        self.draw_curve(ax, opts)
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.legend(loc='best', fontsize='small', frameon=False)
        ax.spines[['top', 'right']].set_visible(False)
        missing = int((self.rho(df, opts) == 0).sum())
        return (f'{len(df)} analyses, {opts["sigma"]} ellipses' +
                (f'; {missing} without error correlation drawn with rho = 0' if missing else ''))

    def draw_curve(self, ax, opts):
        ax.margins(0.05)
        ax.autoscale_view()
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        t = np.linspace(1e5, 4.6e9, 6000)
        cx, cy = self.curve(t)
        visible = (cx >= xlim[0]) & (cx <= xlim[1]) & (cy >= ylim[0]) & (cy <= ylim[1])
        ax.plot(cx, cy, color='k', lw=1, zorder=0)
        if visible.any():
            low, high = t[visible].min() / 1e6, t[visible].max() / 1e6
            if opts['tick_step']:
                ticks = np.arange(math.ceil(low / opts['tick_step']) * opts['tick_step'], high, opts['tick_step'])
            else:
                ticks = self.spaced_ticks(low, high, xlim, ylim)
            tx, ty = self.curve(ticks * 1e6)
            ax.plot(tx, ty, 'o', color='k', ms=3, zorder=1)
            for age, px, py in zip(ticks, tx, ty):
                ax.annotate(f'{age:g}', (px, py), textcoords='offset points', xytext=(4, -10), fontsize='x-small')
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    def spaced_ticks(self, low, high, xlim, ylim, min_gap=0.07) -> np.ndarray:
        """Round ages (1/2/5 x 10^k Ma, rounder first) at least min_gap apart in axes-fraction space, so ticks stay
        legible where the concordia is stretched (young ages on Tera-Wasserburg) or compressed."""
        candidates = [(rank, m * 10 ** k) for k in range(0, 4) for rank, m in ((0, 1), (1, 5), (2, 2))
                      if low <= m * 10 ** k <= high] + [(0, a) for a in (3000, 4000) if low <= a <= high]
        kept = []
        for _, age in sorted(candidates):
            x, y = self.curve(np.array([age * 1e6]))
            point = ((x[0] - xlim[0]) / (xlim[1] - xlim[0]), (y[0] - ylim[0]) / (ylim[1] - ylim[0]))
            if all(math.dist(point, other) >= min_gap for _, other in kept):
                kept.append((age, point))
        return np.array(sorted(age for age, _ in kept))


@register_plot
class Wetherill(Concordia):
    name = 'Wetherill concordia'
    x_ratio, y_ratio, rho_column = '207Pb/235U', '206Pb/238U', 'rho_68v75'
    xlabel, ylabel = '$^{207}$Pb/$^{235}$U', '$^{206}$Pb/$^{238}$U'

    def curve(self, t):
        return np.expm1(LAMBDA_235 * t), np.expm1(LAMBDA_238 * t)


@register_plot
class TeraWasserburg(Concordia):
    name = 'Tera-Wasserburg'
    x_ratio, y_ratio, rho_column = '206Pb/238U', '207Pb/206Pb', 'rho_68v76'
    xlabel, ylabel = '$^{238}$U/$^{206}$Pb', '$^{207}$Pb/$^{206}$Pb'
    options = Concordia.options + [
        Option('flip_rho', 'Rho 68v76 is for 206Pb/238U (invert sign)', 'bool', False,
               tooltip='Leave off if ErrorCorr/Rho_68v76 was reported for 238U/206Pb v 207Pb/206Pb'),
    ]

    def draw(self, fig, df, opts):
        df = df.copy()
        ratio, error = df['R_206Pb/238U'], df['R_206Pb/238U_1s']
        df['R_206Pb/238U'], df['R_206Pb/238U_1s'] = 1 / ratio, error / ratio ** 2  # plotted as 238U/206Pb
        return super().draw(fig, df, opts)

    def rho(self, df, opts):
        rho = df[self.rho_column].fillna(0)
        return -rho if opts.get('flip_rho') else rho

    def curve(self, t):
        e238, e235 = np.expm1(LAMBDA_238 * t), np.expm1(LAMBDA_235 * t)
        return 1 / e238, e235 / (U238_U235 * e238)


# ---------------------------------------------------------------- geochemistry (pyrolite)

from Functions.Plot_data import REFERENCE_COMPOSITIONS

TIO2_PER_TI = 79.866 / 47.867
MAJOR_OXIDES = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3T', 'MnO', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5']
MULTI_ELEMENT = ['Cs', 'Rb', 'Ba', 'Th', 'U', 'Nb', 'Ta', 'K', 'La', 'Ce', 'Pb', 'Pr', 'Sr', 'P', 'Nd', 'Zr', 'Hf',
                 'Sm', 'Eu', 'Ti', 'Gd', 'Tb', 'Dy', 'Y', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']
"""Extended multi-element (spider) set, ordered by pyrolite by_incompatibility when plotted"""
TAS_EXAMPLE_IDS = ['Pc', 'Ba', 'Bs', 'O1', 'O2', 'U1', 'U2', 'U3', 'S1', 'S2', 'S3']


def element_ppm(df: pd.DataFrame) -> pd.DataFrame:
    """Element columns in ppm; elements reported only as oxides (e.g. K2O, TiO2, P2O5, FeOT) are converted with pyrolite."""
    from pyrolite.geochem.ind import common_elements, common_oxides, get_cations
    from pyrolite.geochem.transform import oxide_conversion
    elements, oxides = common_elements(as_set=True), common_oxides(as_set=True) - {'LOI'}  # LOI is not a formula
    out = df[[c for c in df.columns if c in elements]].copy()
    for oxide in [c for c in df.columns if c in oxides]:
        formula = oxide[:-1] if oxide.endswith('T') else oxide  # Fe2O3T / FeOT: total iron
        cations = [str(c) for c in get_cations(formula)]
        if len(cations) == 1:  # fill rows missing the element (column may exist from other analyses)
            converted = oxide_conversion(formula, cations[0])(df[oxide])
            out[cations[0]] = out[cations[0]].fillna(converted) if cations[0] in out else converted
    return out


def major_oxides_wt(df: pd.DataFrame, anhydrous: bool) -> pd.DataFrame:
    """Major oxides in wt% with Fe as Fe2O3T; optionally renormalized to 100% volatile-free (LOI/H2O excluded)."""
    wt = pd.DataFrame(index=df.index)
    for oxide in MAJOR_OXIDES:
        if oxide in df:
            wt[oxide] = df[oxide] / 1e4
    missing = pd.Series(np.nan, index=df.index)
    fe2o3_plus_feo = df.get('Fe2O3', missing) + df.get('FeO', missing) * 1.11134
    wt['Fe2O3T'] = wt.get('Fe2O3T', missing).fillna(df.get('FeOT', missing) * 1.11134 / 1e4).fillna(
        fe2o3_plus_feo.fillna(df.get('Fe2O3', missing)) / 1e4)
    wt['TiO2'] = wt.get('TiO2', missing).fillna(df.get('Ti', missing) * TIO2_PER_TI / 1e4)
    wt = wt.dropna(axis=1, how='all')
    if anhydrous:
        wt = wt.div(wt.sum(axis=1, min_count=1), axis=0) * 100
    return wt


def expand_log_limits(ax, x: pd.Series, y: pd.Series, pad=1.3):
    """Widen a template's fixed log limits so data outside them stay visible."""
    for values, get, set_ in ((x, ax.get_xlim, ax.set_xlim), (y, ax.get_ylim, ax.set_ylim)):
        values = values[np.isfinite(values) & (values > 0)]
        if len(values):
            low, high = get()
            set_(min(low, values.min() / pad), max(high, values.max() * pad))


class GeoChemPlot(PlotType):
    category = 'Geochemistry'
    data = 'geochem'

    def status(self, df, plotted: int, needed: str) -> str:
        message = f'{plotted} of {len(df)} {"samples" if "GeoChemAnalysisID" not in df else "analyses"} plotted'
        if plotted < len(df):
            message += f' (others missing {needed})'
        if df.attrs.get('excluded_values'):
            message += f'; {df.attrs["excluded_values"]} values in non-concentration units ignored'
        return message

    @staticmethod
    def legend(ax, loc='best'):
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc=loc, fontsize='small', frameon=False)


@register_plot
class TASPlot(GeoChemPlot):
    name = 'Total alkali-silica (TAS)'
    options = [
        GROUPING,
        Option('anhydrous', 'Renormalize to 100% anhydrous', 'bool', True),
        Option('labels', 'Field labels', 'choice', 'volcanic', ['volcanic', 'intrusive', 'ID', 'None']),
        Option('fields', 'Fields', 'choice', 'All', ['All', 'Pc, Ba, Bs, O1-O2, U1-U3, S1-S3']),
    ]

    def draw(self, fig, df, opts):
        from pyrolite.plot.templates import TAS
        wt = major_oxides_wt(df, opts['anhydrous'])
        data = df.assign(SiO2_wt=wt.get('SiO2'), alkali_wt=wt.get('Na2O', np.nan) + wt.get('K2O', np.nan))
        data = data.dropna(subset=['SiO2_wt', 'alkali_wt'])
        ax = fig.add_subplot()
        TAS(ax=ax, linewidth=0.5, add_labels=opts['labels'] != 'None', which_model='LeMaitre',
            which_labels=opts['labels'] if opts['labels'] != 'None' else 'ID',
            which_ids=None if opts['fields'] == 'All' else TAS_EXAMPLE_IDS)
        for i, (label, group) in enumerate(groups(data, opts)):
            ax.scatter(group['SiO2_wt'], group['alkali_wt'], s=18, color=f'C{i % 10}', edgecolor='k', lw=0.3,
                       zorder=3, label=f'{label} (n={len(group)})')
        ax.set_xlabel('SiO$_2$ (wt%)')
        ax.set_ylabel('Na$_2$O + K$_2$O (wt%)')
        self.legend(ax, 'upper left')
        return self.status(df, len(data), 'SiO2, Na2O or K2O')


@register_plot
class PearcePlot(GeoChemPlot):
    name = 'Pearce Th/Yb, TiO2/Yb v Nb/Yb'
    options = [GROUPING]

    def draw(self, fig, df, opts):
        from pyrolite.plot.templates import pearceThNbYb, pearceTiNbYb
        from pyrolite.util.plot.axes import share_axes
        el = element_ppm(df)
        tio2 = major_oxides_wt(df, False).get('TiO2', np.nan)
        data = df.assign(NbYb=el.get('Nb') / el.get('Yb'), ThYb=el.get('Th') / el.get('Yb'),
                         TiYb=tio2 / el.get('Yb') if 'Yb' in el else np.nan)
        ax = fig.subplots(1, 2)
        share_axes(ax, which='x')
        pearceThNbYb(ax=ax[0])
        pearceTiNbYb(ax=ax[1])
        for i, (label, group) in enumerate(groups(data, opts)):
            for axis, y in ((ax[0], 'ThYb'), (ax[1], 'TiYb')):
                g = group.dropna(subset=['NbYb', y])
                axis.scatter(g['NbYb'], g[y], s=18, color=f'C{i % 10}', edgecolor='k', lw=0.3, zorder=3,
                             label=f'{label} (n={len(g)})')
        for axis, y in ((ax[0], 'ThYb'), (ax[1], 'TiYb')):
            expand_log_limits(axis, data['NbYb'], data[y])
        ax[1].set_ylabel('TiO$_2$ (wt%) / Yb (ppm)')
        self.legend(ax[0], 'upper left')
        plotted = int(data[['NbYb', 'ThYb']].notna().all(axis=1).sum())
        return self.status(df, plotted, 'Nb, Th or Yb') + f'; {int(data[["NbYb", "TiYb"]].notna().all(axis=1).sum())} with TiO2/Yb'


class NormalizedPlot(GeoChemPlot):
    show_option = Option('show', 'Show', 'choice', 'Analyses', ['Analyses', 'Analyses + sample median', 'Sample median'])
    reference_option = Option('reference', 'Normalize to', 'choice', 'Chondrite_PON', REFERENCE_COMPOSITIONS)

    def columns(self, el: pd.DataFrame, opts) -> list[str]:
        raise NotImplementedError

    def plot_group(self, ax, frame, color, opts, **kwargs):
        raise NotImplementedError

    def draw(self, fig, df, opts):
        el = element_ppm(df)
        columns = self.columns(el, opts)
        norm = el[columns].pyrochem.normalize_to(opts['reference'], units='ppm') if columns else pd.DataFrame()
        norm = norm.dropna(axis=1, how='all').dropna(axis=0, how='all')
        if norm.empty:
            return f'No {self.needed} with values in {opts["reference"]}'
        ax = fig.add_subplot()
        data = df.loc[norm.index]
        for i, (label, group) in enumerate(groups(data, opts)):
            color, rows = f'C{i % 10}', norm.loc[group.index]
            if opts['show'] != 'Sample median':
                self.plot_group(ax, rows, color, opts, alpha=0.4 if len(rows) > 1 else 0.9, lw=0.8)
            if opts['show'] != 'Analyses':
                self.plot_group(ax, rows.median().to_frame().T, color, opts, lw=2.2)
            ax.plot([], [], color=color, lw=2, label=f'{label} (n={len(rows)})')
        values = norm.to_numpy(dtype=float)
        values = values[np.isfinite(values) & (values > 0)]
        ax.set_ylim(10 ** np.floor(np.log10(values.min())), 10 ** np.ceil(np.log10(values.max())))  # all groups
        if opts.get('unity_line', True):
            ax.axhline(1, color='0.5', lw=0.8, ls='--', zorder=0)
        ax.set_ylabel(f'Sample / {opts["reference"]}')
        self.legend(ax)
        return self.status(df, len(norm), self.needed)


@register_plot
class SpiderPlot(NormalizedPlot):
    name = 'Multi-element spider'
    needed = 'trace elements'
    options = [GROUPING, NormalizedPlot.reference_option,
               Option('elements', 'Elements', 'choice', 'Extended multi-element', ['Extended multi-element', 'All available']),
               Option('order', 'Order', 'choice', 'incompatibility', ['incompatibility', 'number']),
               NormalizedPlot.show_option, Option('unity_line', 'Unity line', 'bool', True)]

    def columns(self, el, opts):
        return [c for c in el.columns if opts['elements'] == 'All available' or c in MULTI_ELEMENT]

    def plot_group(self, ax, frame, color, opts, **kwargs):
        frame.pyroplot.spider(ax=ax, index_order=opts['order'], color=color, **kwargs)


@register_plot
class REEPlot(NormalizedPlot):
    name = 'REE spider'
    needed = 'rare earth elements'
    options = [GROUPING, NormalizedPlot.reference_option,
               Option('index', 'x axis', 'choice', 'elements', ['elements', 'radii']),
               NormalizedPlot.show_option, Option('unity_line', 'Unity line', 'bool', True)]

    def columns(self, el, opts):
        from pyrolite.geochem.ind import REE
        return [c for c in REE() if c in el.columns]

    def plot_group(self, ax, frame, color, opts, **kwargs):
        frame.pyroplot.REE(ax=ax, index=opts['index'], color=color, **kwargs)


# ---------------------------------------------------------------- age v epsilon Hf

LAMBDA_176LU = 1.867e-11  # Söderlund et al. (2004), 1/yr
CHUR_HF, CHUR_LU = 0.282785, 0.0336  # 176Hf/177Hf, 176Lu/177Hf; Bouvier et al. (2008)
DM_HF, DM_LU = 0.28325, 0.0384  # Griffin et al. (2000)


def epsilon_hf_dm(t_ma: np.ndarray) -> np.ndarray:
    """Depleted-mantle epsilon Hf at t (Ma) relative to CHUR."""
    growth = np.expm1(LAMBDA_176LU * t_ma * 1e6)
    return ((DM_HF - DM_LU * growth) / (CHUR_HF - CHUR_LU * growth) - 1) * 1e4


@register_plot
class AgeEpsilonHf(PlotType):
    name = 'Age v εHf'
    category = 'U-Pb'
    data = 'upb_hf'
    options = [
        GROUPING,
        Option('error_bars', 'Error bars', 'choice', '2σ', ['2σ', '1σ', 'None']),
        Option('dm_line', 'Depleted mantle and CHUR', 'bool', True,
               tooltip='DM: Griffin et al. (2000); CHUR: Bouvier et al. (2008); λ176Lu: Söderlund et al. (2004)'),
    ]

    def draw(self, fig, df, opts):
        data = df.dropna(subset=['Age', 'EHf'])
        if data.empty:
            return (f'{len(df)} εHf values, none paired with a U-Pb age '
                    '(try "Spot, then grain" or relax the U-Pb filters)' if len(df) else 'No εHf values for the selected samples')
        ax = fig.add_subplot()
        scale = {'2σ': 2, '1σ': 1}.get(opts['error_bars'])
        for i, (label, group) in enumerate(groups(data, opts)):
            color = f'C{i % 10}'
            if scale:
                ax.errorbar(group['Age'], group['EHf'], xerr=group['Age1s'] * scale, yerr=group['EHf1s'] * scale,
                            fmt='none', ecolor=color, elinewidth=0.6, alpha=0.6, zorder=2)
            ax.scatter(group['Age'], group['EHf'], s=20, color=color, edgecolor='k', lw=0.3, zorder=3,
                       label=f'{label} (n={len(group)})')
        right = max(ax.get_xlim()[1], 100)
        if opts['dm_line']:
            t = np.linspace(0, right, 300)
            ax.plot(t, epsilon_hf_dm(t), color='0.25', lw=1, label='Depleted mantle')
            ax.axhline(0, color='0.5', lw=0.8, ls='--', label='CHUR')
        ax.set_xlim(0, right)
        ax.set_xlabel('Age (Ma)')
        ax.set_ylabel('εHf')
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(loc='best', fontsize='small', frameon=False)
        message = f'{len(data)} of {len(df)} εHf values paired with a U-Pb age'
        if (data['PairedBy'] == 'Grain').any():
            message += f' ({int((data["PairedBy"] == "Grain").sum())} by grain)'
        return message