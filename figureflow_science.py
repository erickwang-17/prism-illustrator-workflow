"""Design-explicit scientific analysis and code-generated vector figures.

Optional dependencies are loaded only when needed. No native Prism/AI mutation.
"""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import tempfile
import warnings


METHODS = {
    'independent': {'welch_t', 'anova', 'kruskal', 'descriptive'},
    'paired': {'paired_t'},
    'correlation': {'pearson', 'spearman_permutation'},
    'contingency': {'fisher_exact'},
    'time_series': {'descriptive'},
}
PALETTE = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#000000']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def fields(obj, required, optional=(), where='config'):
    if not isinstance(obj, dict):
        raise ValueError(f'{where}: expected an object')
    missing = set(required) - obj.keys()
    extra = obj.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValueError(f'{where}: missing={sorted(missing)}, unknown={sorted(extra)}')


def finite(value, where):
    if isinstance(value, bool):
        raise ValueError(f'{where}: boolean is not numeric')
    try:
        v = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{where}: expected a number, got {value!r}') from exc
    if not math.isfinite(v):
        raise ValueError(f'{where}: nonfinite value')
    return v


def read_table(path, sheet=None):
    """Read literal cells; reject formula cells rather than trust stale caches."""
    path = Path(path)
    if path.suffix.lower() in ('.csv', '.tsv'):
        if sheet is not None:
            raise ValueError('sheet is only valid for XLSX')
        with path.open(encoding='utf-8-sig', newline='') as stream:
            raw = list(csv.reader(stream, delimiter='\t' if path.suffix.lower() == '.tsv' else ',', strict=True))
    elif path.suffix.lower() == '.xlsx':
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise ValueError('XLSX requires installation with [science]') from exc
        book = load_workbook(path, read_only=True, data_only=False)
        try:
            if sheet is None:
                if len(book.sheetnames) != 1:
                    raise ValueError('Choose sheet explicitly: ' + ', '.join(book.sheetnames))
                sheet = book.sheetnames[0]
            if sheet not in book.sheetnames:
                raise ValueError('Unknown sheet: ' + str(sheet))
            raw = []
            for cells in book[sheet].iter_rows():
                if any(c.data_type == 'f' for c in cells):
                    raise ValueError('Formula cells are not accepted; export reviewed literal values')
                raw.append([c.value for c in cells])
        finally:
            book.close()
    else:
        raise ValueError('Supported tables: UTF-8 CSV, TSV, XLSX')
    if not raw or not raw[0]:
        raise ValueError('Empty table')
    header = raw[0]
    if any(not isinstance(h, str) or not h.strip() for h in header) or len(set(header)) != len(header):
        raise ValueError('Header must contain distinct nonempty text column names')
    rows = []
    for index, values in enumerate(raw[1:], 2):
        if not values or all(v is None or v == '' for v in values):
            continue
        if len(values) != len(header):
            raise ValueError(f'Malformed row {index}: column count differs from header')
        rows.append((index, dict(zip(header, values))))
    if not rows:
        raise ValueError('Table has no data rows')
    return header, rows


def inspect_table(path, sheet=None):
    header, rows = read_table(path, sheet)
    columns = []
    for name in header:
        values = [row[name] for _, row in rows]
        present = [v for v in values if v is not None and v != '']
        numeric = 0
        for value in present:
            try:
                finite(value, name)
                numeric += 1
            except ValueError:
                pass
        columns.append({'name': name, 'missing': len(values) - len(present),
                        'numeric_cells': numeric, 'nonmissing': len(present),
                        'unique_nonmissing': len({str(v) for v in present})})
    return {'status': 'pass', 'rows': len(rows), 'columns': columns, 'source_sha256': digest(path),
            'required_decisions': ['column roles', 'experimental unit and IDs', 'design', 'method',
                                   'units', 'missing-value policy', 'assumptions and comparison family'],
            'scope': 'Structural inspection only; no automatic design or test selection'}


def validate_config(c):
    fields(c, ('schema_version', 'source', 'design', 'method', 'columns', 'missing', 'title',
               'x_label', 'y_label', 'unit', 'design_confirmed', 'assumptions'),
           ('group_order', 'contrasts', 'style', 'time_kind', 'count_basis', 'pairwise_method', 'correction'))
    if type(c['schema_version']) is not int or c['schema_version'] != 1:
        raise ValueError('Supported science config schema_version: integer 1')
    fields(c['source'], ('path',), ('sheet',), 'source')
    if not isinstance(c['source']['path'], str) or not c['source']['path']:
        raise ValueError('source.path must be nonempty text')
    if not isinstance(c['design'], str) or not isinstance(c['method'], str) or c['design'] not in METHODS or c['method'] not in METHODS[c['design']]:
        raise ValueError('Unsupported design/method combination; no fallback will be selected')
    if c['design_confirmed'] is not True:
        raise ValueError('Confirm design before analysis; inspect does not infer independence')
    for key in ('title', 'x_label', 'y_label', 'unit', 'assumptions'):
        if not isinstance(c[key], str) or not c[key].strip() or len(c[key]) > 500:
            raise ValueError(key + ' must be explicit nonempty text, max 500 characters')
    if c['missing'] not in ('error', 'drop'):
        raise ValueError('missing must be error or drop; no imputation is performed')
    design = c['design']
    roles = {'independent': ('group', 'value', 'id'), 'paired': ('group', 'value', 'id'),
             'correlation': ('x', 'y', 'id'), 'time_series': ('x', 'y', 'id'),
             'contingency': ('row', 'column', 'count')}[design]
    fields(c['columns'], roles, where='columns')
    if any(not isinstance(v, str) or not v for v in c['columns'].values()) or len(set(c['columns'].values())) != len(roles):
        raise ValueError('Column roles must map to distinct nonempty source column names')
    if design in ('independent', 'paired'):
        order = c.get('group_order')
        if not isinstance(order, list) or len(order) < 2 or any(not isinstance(g, str) or not g for g in order) or len(set(order)) != len(order):
            raise ValueError('group_order must list at least two distinct group names')
        if c['method'] in ('welch_t', 'paired_t') and len(order) != 2:
            raise ValueError('This test requires exactly two groups')
    elif 'group_order' in c:
        raise ValueError('group_order is only supported for independent/paired designs')
    if design == 'time_series' and c.get('time_kind') not in ('numeric', 'iso_date'):
        raise ValueError('time_series requires time_kind numeric or iso_date')
    if design != 'time_series' and 'time_kind' in c:
        raise ValueError('time_kind only applies to time_series')
    if design == 'contingency' and c.get('count_basis') != 'observed_counts':
        raise ValueError('Contingency analysis requires observed_counts, not percentages')
    if design != 'contingency' and 'count_basis' in c:
        raise ValueError('count_basis only applies to contingency')
    contrasts = c.get('contrasts', [])
    if not isinstance(contrasts, list):
        raise ValueError('contrasts must be a list')
    if contrasts and not (design == 'independent' and c['method'] == 'anova'):
        raise ValueError('Planned pairwise contrasts currently require independent ANOVA; use separate reviewed configurations for other designs')
    seen = set()
    for contrast in contrasts:
        fields(contrast, ('a', 'b'), where='contrast')
        a, b = contrast['a'], contrast['b']
        if a not in c['group_order'] or b not in c['group_order'] or a == b:
            raise ValueError('Unknown/self contrast')
        key = tuple(sorted((a, b)))
        if key in seen:
            raise ValueError('Duplicate/reversed contrast')
        seen.add(key)
    if contrasts:
        if c.get('pairwise_method') != 'welch_t' or c.get('correction') != 'holm':
            raise ValueError('Contrasts require explicit pairwise_method=welch_t and correction=holm')
    elif 'pairwise_method' in c or 'correction' in c:
        raise ValueError('Pairwise method/correction require a nonempty contrasts family')
    style = c.get('style', {})
    fields(style, (), ('font', 'palette', 'width', 'height', 'summary', 'show_significance'), 'style')
    if not isinstance(style.get('font', 'DejaVu Sans'), str) or not style.get('font', 'DejaVu Sans').strip():
        raise ValueError('style.font must be nonempty text')
    if style.get('summary', 'mean_sd') not in ('mean_sd', 'median_iqr'):
        raise ValueError('style.summary must be mean_sd or median_iqr')
    if type(style.get('show_significance', True)) is not bool:
        raise ValueError('style.show_significance must be boolean')
    for key, default in [('width', 7), ('height', 5)]:
        if type(style.get(key, default)) not in (int, float) or not 3 <= finite(style.get(key, default), key) <= 20:
            raise ValueError('Figure width/height must be 3–20 inches')
    return c


def prepare(c, base):
    source = (Path(base) / c['source']['path']).resolve()
    initial_hash = digest(source)
    header, raw = read_table(source, c['source'].get('sheet'))
    if initial_hash != digest(source):
        raise ValueError('Source changed while reading')
    if not set(c['columns'].values()).issubset(header):
        raise ValueError('Mapped columns missing from source table')
    data, dropped = [], []
    for number, row in raw:
        mapped = {role: row[col] for role, col in c['columns'].items()}
        absent = [k for k, v in mapped.items() if v is None or v == '']
        if absent:
            if c['missing'] == 'error':
                raise ValueError(f'Missing cells at source row {number}: {absent}')
            dropped.append({'source_row': number, 'reason': 'missing mapped fields', 'fields': absent})
            continue
        for role, value in list(mapped.items()):
            if role == 'count':
                try:
                    count = Decimal(str(value))
                except InvalidOperation as exc:
                    raise ValueError('Counts must be exact integers') from exc
                if not count.is_finite() or count < 0 or count != count.to_integral_value() or count >= 2**53:
                    raise ValueError('Counts must be nonnegative exact integers below 2**53')
                mapped[role] = int(count)
            elif role in ('value', 'y') or (role == 'x' and c.get('time_kind') != 'iso_date'):
                mapped[role] = finite(value, f'row {number}, {role}')
            elif role == 'x':
                if isinstance(value, datetime):
                    if value.time().isoformat() != '00:00:00':
                        raise ValueError('iso_date accepts dates only, not intraday timestamps')
                    value = value.date().isoformat()
                value = str(value)
                parsed = datetime.strptime(value, '%Y-%m-%d').date()
                if parsed.isoformat() != value:
                    raise ValueError('Dates must use YYYY-MM-DD')
                mapped[role] = value
            else:
                mapped[role] = str(value)
                if not mapped[role].strip():
                    raise ValueError(f'Blank identity/category at row {number}')
        mapped['source_row'] = number
        data.append(mapped)
    if not data:
        raise ValueError('No complete observations remain')
    if c['design'] in ('independent', 'paired'):
        if set(r['group'] for r in data) != set(c['group_order']):
            raise ValueError('Observed groups differ from group_order; filtering is never implicit')
        keys = [(r['group'], r['id']) if c['design'] == 'paired' else r['id'] for r in data]
    elif c['design'] == 'contingency':
        keys = [(r['row'], r['column']) for r in data]
        if any(r['count'] < 0 or r['count'] != int(r['count']) or r['count'] > 2**53 for r in data):
            raise ValueError('Counts must be nonnegative exact integers up to 2**53')
    else:
        keys = [r['id'] for r in data]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate experimental-unit IDs/cells; resolve technical repeats explicitly')
    if c['design'] == 'time_series':
        if len(set(r['x'] for r in data)) != len(data):
            raise ValueError('Duplicate time coordinates; aggregate under a reviewed rule first')
        data.sort(key=lambda r: r['x'])
    return source, data, dropped, len(raw), initial_hash


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=pvalues.__getitem__)
    adjusted, last = [0.0] * len(order), 0.0
    for rank, index in enumerate(order):
        last = max(last, min(1.0, (len(order) - rank) * pvalues[index]))
        adjusted[index] = last
    return adjusted


def infer(c, data):
    import numpy as np
    from scipy import stats
    result = {'method': c['method'], 'design': c['design'], 'alternative': 'two-sided',
              'assumptions_declared': c['assumptions'], 'confidence_level': 0.95,
              'comparisons': [], 'warnings': [], 'scope': 'Declared design; assumptions are not proven by software'}
    if c['method'] in ('anova', 'kruskal'):
        result['alternative'] = 'upper-tail'
    elif c['method'] == 'descriptive':
        result['alternative'] = None
    groups = {}
    if c['design'] in ('independent', 'paired'):
        groups = {g: [r for r in data if r['group'] == g] for g in c['group_order']}
        if any(len(rows) < 2 for rows in groups.values()):
            raise ValueError('Each group requires at least two independent units/pairs')
        if c['design'] == 'paired':
            a, b = groups.values()
            if {r['id'] for r in a} != {r['id'] for r in b}:
                raise ValueError('Incomplete pairs; IDs must match exactly across conditions')
            groups = {g: sorted(rows, key=lambda r: r['id']) for g, rows in groups.items()}
        arrays = [np.asarray([r['value'] for r in rows]) for rows in groups.values()]
        result['groups'] = [dict(group=g, n=len(a), mean=float(np.mean(a)), sd=float(np.std(a, ddof=1)),
                                 median=float(np.median(a)), q1=float(np.quantile(a, .25)),
                                 q3=float(np.quantile(a, .75))) for g, a in zip(groups, arrays)]
        if c['method'] in ('welch_t', 'paired_t'):
            a, b = arrays
            if c['method'] == 'paired_t' and np.std(a-b, ddof=1) == 0:
                raise ValueError('Zero variance in paired differences; t inference is degenerate')
            if c['method'] == 'welch_t' and all(np.std(x, ddof=1) == 0 for x in arrays):
                raise ValueError('Both groups have zero variance; t inference is degenerate')
            test = stats.ttest_ind(a, b, equal_var=False) if c['method'] == 'welch_t' else stats.ttest_rel(a, b)
            interval = test.confidence_interval(.95)
            result.update(statistic=float(test.statistic), pvalue=float(test.pvalue), df=float(test.df),
                          effect={'name': 'mean_difference_a_minus_b', 'a': c['group_order'][0],
                                  'b': c['group_order'][1], 'value': float(np.mean(a)-np.mean(b)),
                                  'ci95': [float(interval.low), float(interval.high)]})
        elif c['method'] == 'anova':
            test = stats.f_oneway(*arrays)
            result.update(statistic=float(test.statistic), pvalue=float(test.pvalue))
            for pair in c.get('contrasts', []):
                a, b = [np.asarray([r['value'] for r in groups[pair[key]]]) for key in ('a', 'b')]
                test = stats.ttest_ind(a, b, equal_var=False)
                interval = test.confidence_interval(.95)
                result['comparisons'].append(dict(pair, method='welch_t', pvalue=float(test.pvalue),
                    mean_difference=float(np.mean(a)-np.mean(b)), ci95_unadjusted=[float(interval.low), float(interval.high)]))
            for pair, adjusted in zip(result['comparisons'], holm([p['pvalue'] for p in result['comparisons']])):
                pair.update(p_adjusted=adjusted, correction='Holm', family='all_declared_contrasts')
            result['warnings'].append('ANOVA assumes equal population variances and independent errors; contrast CIs are unadjusted.')
        elif c['method'] == 'kruskal':
            if any(len(a) < 5 for a in arrays):
                raise ValueError('Kruskal asymptotic mode requires at least five observations per group')
            test = stats.kruskal(*arrays)
            result.update(statistic=float(test.statistic), pvalue=float(test.pvalue))
            result['warnings'].append('Omnibus rank test; no pairwise difference or pure median shift is established.')
    elif c['design'] == 'correlation':
        x, y = [np.asarray([r[k] for r in data]) for k in ('x', 'y')]
        if len(x) < 4 or np.std(x) == 0 or np.std(y) == 0:
            raise ValueError('Correlation requires at least four units and nonconstant x/y')
        if c['method'] == 'pearson':
            test = stats.pearsonr(x, y)
            interval = test.confidence_interval(.95)
            result.update(statistic=float(test.statistic), pvalue=float(test.pvalue),
                          effect={'name': 'Pearson r', 'value': float(test.statistic),
                                  'ci95': [float(interval.low), float(interval.high)]})
        else:
            # Permute ranked x only, avoiding the small-n asymptotic Spearman P approximation.
            rx, ry = stats.rankdata(x), stats.rankdata(y)
            rx, ry = rx-rx.mean(), ry-ry.mean()
            norm = np.linalg.norm(rx)*np.linalg.norm(ry)
            def statistic(a):
                return float(np.dot(a, ry)/norm)
            perm = stats.permutation_test((rx,), statistic, permutation_type='pairings',
                                           n_resamples=9999, random_state=0, alternative='two-sided')
            result.update(statistic=statistic(rx), pvalue=float(perm.pvalue),
                          effect={'name': 'Spearman rho', 'value': statistic(rx), 'ci95': None},
                          permutation={'seed': 0, 'requested_resamples': 9999,
                                       'actual_resamples': len(perm.null_distribution),
                                       'exact': math.factorial(len(x)) <= 9999, 'alternative': 'two-sided'})
            result['warnings'].append('Permutation requires exchangeable independent units; no correlation CI is implemented for this method.')
        result['n'] = len(data)
        result['warnings'].append('Correlation is not causation; inspect shape and influential points even when r and P agree.')
    elif c['design'] == 'contingency':
        row_names = list(dict.fromkeys(r['row'] for r in data))
        column_names = list(dict.fromkeys(r['column'] for r in data))
        if len(row_names) != 2 or len(column_names) != 2 or len(data) != 4:
            raise ValueError('Fisher mode requires all four cells of a 2x2 count table')
        table = [[int(next(r['count'] for r in data if r['row']==a and r['column']==b)) for b in column_names] for a in row_names]
        if any(sum(row) == 0 for row in table) or any(sum(col) == 0 for col in zip(*table)):
            raise ValueError('Zero table margin; no estimable contingency contrast')
        test = stats.fisher_exact(table, alternative='two-sided')
        odds = float(test.statistic)
        result.update(pvalue=float(test.pvalue), effect={'name': 'odds_ratio',
            'value': odds if math.isfinite(odds) else None, 'unbounded': not math.isfinite(odds), 'ci95': None},
            table=table, row_names=row_names, column_names=column_names, n=sum(map(sum, table)))
        result['warnings'].append('Odds ratio orientation follows displayed row/column order; no odds-ratio CI is implemented.')
    else:
        result.update(n=len(data), warnings=['Time series is descriptive only; autocorrelation/repeated measures inference is not implemented.'])
    if 'pvalue' in result and (not math.isfinite(result['pvalue']) or not 0 <= result['pvalue'] <= 1):
        raise ValueError('Undefined inference; inspect constant data and test assumptions')
    def reject_nonfinite(x):
        if isinstance(x, dict):
            for value in x.values(): reject_nonfinite(value)
        elif isinstance(x, list):
            for value in x: reject_nonfinite(value)
        elif isinstance(x, float) and not math.isfinite(x):
            raise ValueError('Nonfinite result; refusing a misleading report')
    reject_nonfinite(result)
    return result, groups


def render(c, data, result, groups, output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt, font_manager, colors
    from matplotlib.ft2font import FT2Font
    style = c.get('style', {})
    font = style.get('font', 'DejaVu Sans')
    font_path = font_manager.findfont(font, fallback_to_default=False)
    charmap = FT2Font(font_path).get_charmap()
    labels = [c[k] for k in ('title', 'x_label', 'y_label', 'unit')] + c.get('group_order', [])
    if c['design'] == 'contingency':
        labels += result['row_names'] + result['column_names']
    missing_glyphs = {ch for text in labels for ch in text if not ch.isspace() and ord(ch) not in charmap}
    if missing_glyphs:
        raise ValueError('Chosen font lacks required glyphs; choose an installed font supporting: ' + ''.join(sorted(missing_glyphs)))
    palette = style.get('palette', PALETTE)
    count = max(len(groups), 2)
    if not isinstance(palette, list) or len(palette) < count or any(not isinstance(p, str) or not colors.is_color_like(p) for p in palette):
        raise ValueError('Palette must supply a valid distinct color for every group')
    if any(colors.to_rgba(p)[3] != 1 for p in palette):
        raise ValueError('Palette must use opaque colors')
    if len(set(colors.to_rgba(p) for p in palette[:count])) != count:
        raise ValueError('Palette colors must be distinct')
    with plt.rc_context({'font.family': font, 'font.size': 11, 'axes.spines.top': False,
                         'axes.spines.right': False, 'svg.fonttype': 'none', 'svg.hashsalt': 'figureflow-v1',
                         'axes.formatter.useoffset': False, 'text.usetex': False, 'text.parse_math': False}):
        fig, ax = plt.subplots(figsize=(style.get('width', 7), style.get('height', 5)), layout='constrained')
        try:
            ax.set_title(c['title'], pad=14, wrap=True)
            ax.set_xlabel(c['x_label'])
            ax.set_ylabel(c['y_label'] + ' (' + c['unit'] + ')')
            if groups:
                rng = np.random.default_rng(0)
                if c['design'] == 'paired':
                    rows = list(groups.values())
                    for a, b in zip(*rows):
                        ax.plot([0, 1], [a['value'], b['value']], color='#AAAAAA', linewidth=.8, zorder=1)
                for i, (name, rows) in enumerate(groups.items()):
                    values = np.array([r['value'] for r in rows])
                    jitter = np.zeros(len(rows)) if c['design'] == 'paired' else rng.uniform(-.13, .13, len(rows))
                    ax.scatter(i+jitter, values, color=palette[i], edgecolors='black', linewidths=.7, s=35, zorder=3)
                    if style.get('summary', 'mean_sd') == 'mean_sd':
                        center, low, high = values.mean(), values.std(ddof=1), values.std(ddof=1)
                    else:
                        q1, center, q3 = np.quantile(values, [.25, .5, .75]); low, high = center-q1, q3-center
                    ax.errorbar(i, center, yerr=[[low], [high]], fmt='_', color='black', capsize=5, linewidth=1.2, zorder=4)
                ax.set_xticks(range(len(groups)), [f'{g}\n(n={len(rows)})' for g, rows in groups.items()])
                if any(len(g) > 16 for g in groups):
                    plt.setp(ax.get_xticklabels(), rotation=20, ha='right')
                ax.set_xlim(-.6, len(groups)-.4)
                if style.get('show_significance', True):
                    pairs = result['comparisons']
                    if c['method'] in ('welch_t', 'paired_t'):
                        pairs = [{'a': c['group_order'][0], 'b': c['group_order'][1], 'p_adjusted': result['pvalue']}]
                    lo, hi = ax.get_ylim(); step = max(hi-lo, 1)*.12
                    for index, pair in enumerate(pairs):
                        x1, x2 = [c['group_order'].index(pair[k]) for k in ('a', 'b')]
                        y = hi+step*index
                        ax.plot([x1, x1, x2, x2], [y, y+step*.2, y+step*.2, y], color='black', lw=1)
                        p = pair['p_adjusted']
                        star = next((s for t, s in [(.0001,'****'),(.001,'***'),(.01,'**'),(.05,'*')] if p <= t), 'ns')
                        ax.text((x1+x2)/2, y+step*.25, star, ha='center', va='bottom', fontsize=10, weight='bold')
                    if pairs: ax.set_ylim(lo, hi+step*(len(pairs)+.65))
            elif c['design'] in ('correlation', 'time_series'):
                x = [datetime.strptime(r['x'], '%Y-%m-%d') if c.get('time_kind') == 'iso_date' else r['x'] for r in data]
                y = [r['y'] for r in data]
                if c['design'] == 'time_series': ax.plot(x, y, marker='o', color=palette[0])
                else: ax.scatter(x, y, color=palette[0], edgecolors='black', s=38)
                if c.get('time_kind') == 'iso_date':
                    from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
                    locator = AutoDateLocator(); ax.xaxis.set_major_locator(locator); ax.xaxis.set_major_formatter(ConciseDateFormatter(locator))
            else:
                for j, name in enumerate(result['column_names']):
                    ax.bar(np.arange(2)+(j-.5)*.36, [r[j] for r in result['table']], width=.36,
                           color=palette[j], edgecolor='black', label=name)
                ax.set_xticks([0, 1], [f'{name}\n(n={sum(row)})' for name,row in zip(result['row_names'],result['table'])])
                ax.set_ylim(bottom=0); ax.legend(frameon=False)
            caption = c['method']
            if groups: caption += ' | ' + style.get('summary', 'mean_sd').replace('_', ' ')
            elif 'n' in result: caption += f" | n={result['n']}"
            if c['design'] == 'correlation': caption += f" | {'r' if c['method']=='pearson' else 'rho'}={result['statistic']:.3g}"
            if 'pvalue' in result: caption += f" | {'omnibus ' if c['method'] in ('anova','kruskal') else ''}P={result['pvalue']:.4g}"
            if result['comparisons']: caption += ' | pairwise Welch + Holm'
            fig.supxlabel(caption, fontsize=9)
            fig.canvas.draw()
            width, height = fig.canvas.get_width_height()
            renderer = fig.canvas.get_renderer()
            # Axis locators include off-axis ticks which Matplotlib does not draw.
            # Check only displayed ticks plus labels, annotations and legends.
            texts = [ax.title, ax.xaxis.label, ax.yaxis.label, ax.xaxis.get_offset_text(),
                     ax.yaxis.get_offset_text(), *ax.texts, *fig.texts]
            legend = ax.get_legend()
            if legend: texts.extend(legend.get_texts())
            for axis, limits in [(ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())]:
                low, high = sorted(limits)
                for minor in (False, True):
                    for position, label in zip(axis.get_ticklocs(minor=minor), axis.get_ticklabels(minor=minor)):
                        if low <= position <= high: texts.append(label)
            for item in texts:
                if item.get_visible() and item.get_text():
                    box = item.get_window_extent(renderer)
                    if box.x0 < -2 or box.y0 < -2 or box.x1 > width+2 or box.y1 > height+2:
                        raise ValueError('Text exceeds canvas: ' + repr(item.get_text()) + '; increase style.width/height or shorten labels')
            for extension in ('svg', 'pdf', 'png'):
                metadata = {'Date': None} if extension == 'svg' else ({'CreationDate': None} if extension == 'pdf' else {})
                fig.savefig(output / ('figure.'+extension), dpi=180, metadata=metadata)
            return {'backend': 'Matplotlib Agg', 'font': font, 'font_file_sha256': digest(font_path),
                    'summary': style.get('summary', 'mean_sd') if groups else None,
                    'jitter_seed': 0, 'text_bounds_checked': True, 'native_prism': False,
                    'visual_review_required': True}
        finally:
            plt.close(fig)


def analyze(config_path, output_dir):
    from figureflow import load_json, __version__
    try:
        import numpy, scipy, matplotlib
    except ImportError as exc:
        raise ValueError('Analysis requires: pip install ".[science]"') from exc
    path = Path(config_path).resolve()
    config_hash = digest(path)
    c = validate_config(load_json(path))
    if digest(path) != config_hash:
        raise ValueError('Config changed while reading')
    target = Path(output_dir).resolve()
    if target.exists():
        raise ValueError('Output directory already exists; use a new directory')
    source, data, dropped, total, source_hash = prepare(c, path.parent)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result, groups = infer(c, data)
    result['warnings'] += [str(w.message) for w in caught]
    result.update(status='pass', report_version=1, tool_version=__version__, command='analyze',
                  source_sha256=source_hash, config_sha256=config_hash, rows_read=total,
                  rows_used=len(data), dropped_rows=dropped,
                  design_confirmed_by_config=True, missing_policy=c['missing'],
                  versions={name: importlib.metadata.version(name) for name in ('numpy','scipy','matplotlib','openpyxl')})
    target.parent.mkdir(parents=True, exist_ok=True)
    # Build privately first. Claim final directory only after every file is valid.
    with tempfile.TemporaryDirectory(prefix='.figureflow-', dir=target.parent) as temporary:
        stage = Path(temporary)
        with warnings.catch_warnings(record=True) as render_warnings:
            warnings.simplefilter('always')
            result['render'] = render(c, data, result, groups, stage)
        result['warnings'] += [str(w.message) for w in render_warnings]
        with (stage/'normalized.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
        safe_config = dict(c, source=dict(c['source'], path=source.name))
        (stage/'config.json').write_text(json.dumps(safe_config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        result['artifacts'] = {p.name: digest(p) for p in sorted(stage.iterdir())}
        (stage/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
        if digest(source) != source_hash or digest(path) != config_hash:
            raise ValueError('Input changed during analysis; output not published')
        target.mkdir()  # Atomic refusal if another writer claimed the destination.
        try:
            for item in stage.iterdir(): os.replace(item, target/item.name)
        except OSError:
            (target/'INCOMPLETE').write_text('Publication interrupted; do not treat this directory as complete.\n')
            raise
    return result
