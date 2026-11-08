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
