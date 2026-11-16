"""Generate and analyze unrelated synthetic examples; no real research data.

Run: python demo_science.py --directory local/general-demo
The destination must not exist. All random generators have explicit seeds.
"""
import argparse
import csv
import json
from pathlib import Path


def config(source, design, method, columns, title, x_label, y_label, unit, **extra):
    return dict(schema_version=1, source={'path': source}, design=design, method=method,
                columns=columns, title=title, x_label=x_label, y_label=y_label, unit=unit,
                missing='error', design_confirmed=True,
                assumptions='Synthetic demonstration only; independent units unless explicitly paired. '
                            'Parametric examples assume normal errors; ANOVA also assumes equal variances. '
                            'Correlation permutation assumes exchangeability.', **extra)


def write_csv(path, header, rows, delimiter=','):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter=delimiter)
        writer.writerow(header); writer.writerows(rows)


def create_cases(directory):
    """Return paths to eight explicit, independently runnable configurations."""
    import numpy as np
    from openpyxl import Workbook
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(8031)
    cases = {}
    write_csv(root/'manufacturing.csv', ['part_serial', 'process', 'diameter_mm'],
              [(f'{g}-{i}', g, float(v)) for g, n, mean, sd in [('Lathe A', 18, 20, .12), ('Lathe B', 27, 20.18, .3)]
               for i, v in enumerate(rng.normal(mean, sd, n))])
    cases['manufacturing'] = config('manufacturing.csv', 'independent', 'welch_t',
        {'id':'part_serial', 'group':'process', 'value':'diameter_mm'},
        'Synthetic manufacturing tolerances', 'Process', 'Diameter', 'mm', group_order=['Lathe A', 'Lathe B'])

    before = np.array([2.1, -1.2, 3.4, .3, -2.2, 1.7, 4.0, -.8])
    after = before + np.array([-.3, .2, -.5, -.1, .4, -.2, -.7, .1])
    rows = [(f'sensor-{i}', 'Before', float(v)) for i, v in enumerate(before)]
    rows += [(f'sensor-{i}', 'After', float(after[i])) for i in [7, 2, 6, 0, 4, 1, 5, 3]]
    write_csv(root/'calibration.tsv', ['device', 'stage', 'bias'], rows, '\t')
    cases['calibration'] = config('calibration.tsv', 'paired', 'paired_t',
        {'id':'device', 'group':'stage', 'value':'bias'}, 'Synthetic sensor calibration', 'Stage', 'Bias', 'mV',
        group_order=['Before', 'After'])

    book = Workbook(); sheet = book.active; sheet.title = 'Yield'
    sheet.append(['plot_id', 'irrigation', 'harvest'])
    for g, center in [('Baseline', 40), ('Drip', 46), ('Mist', 42)]:
        for i, v in enumerate(rng.normal(center, 3, 14)):
            sheet.append([f'{g}-{i}', g, float(v)])
    book.save(root/'agriculture.xlsx'); book.close()
    cases['agriculture'] = config('agriculture.xlsx', 'independent', 'anova',
        {'id':'plot_id', 'group':'irrigation', 'value':'harvest'},
        'Synthetic greenhouse harvest', 'Irrigation', 'Harvest', 'kg',
        group_order=['Baseline', 'Drip', 'Mist'], contrasts=[{'a':'Baseline','b':'Drip'}, {'a':'Baseline','b':'Mist'}],
        pairwise_method='welch_t', correction='holm')
    cases['agriculture']['source']['sheet'] = 'Yield'

    write_csv(root/'website.csv', ['variant','outcome','visitors'],
              [('Original','Converted',6), ('Original','Not converted',2),
               ('New','Converted',1), ('New','Not converted',4)])
    cases['website'] = config('website.csv', 'contingency', 'fisher_exact',
        {'row':'variant','column':'outcome','count':'visitors'}, 'Synthetic website experiment',
        'Page version', 'Visitors', 'count', count_basis='observed_counts')

    # A U-shaped relationship illustrates why the graph matters when Pearson r is small.
    xs = list(range(-7, 8))
    write_csv(root/'nonlinear.csv', ['run','temperature','expansion'],
              [(f'run-{i}', x, x*x + .15*((i%3)-1)) for i, x in enumerate(xs)])
    cases['nonlinear'] = config('nonlinear.csv', 'correlation', 'pearson',
        {'id':'run','x':'temperature','y':'expansion'}, 'Synthetic nonlinear response',
        'Temperature deviation (C)', 'Expansion', 'micrometers')
    cases['nonlinear']['assumptions'] = ('Independent synthetic units. Deliberate nonlinear counterexample: '
        'the bivariate-normal model is inappropriate; P is displayed to demonstrate why this model must not be accepted blindly.')

    write_csv(root/'ranks.csv', ['site','traffic_rank','wait_rank'],
              [(f'site-{i}', x, y) for i,(x,y) in enumerate([(1,1),(2,2),(3,4),(4,3),(5,5),(6,6)])])
    cases['ranks'] = config('ranks.csv', 'correlation', 'spearman_permutation',
        {'id':'site','x':'traffic_rank','y':'wait_rank'}, 'Synthetic service ranks', 'Traffic rank', 'Waiting rank', 'rank')

    write_csv(root/'energy.tsv', ['reading','date','power'],
              [(f'day-{i}', f'2025-02-{i+1:02d}', 120+12*np.sin(i/3)+i*.6) for i in range(24)], '\t')
    cases['energy'] = config('energy.tsv', 'time_series', 'descriptive',
        {'id':'reading','x':'date','y':'power'}, 'Synthetic daily energy demand', 'Date', 'Demand', 'kWh', time_kind='iso_date')

    write_csv(root/'delivery.csv', ['parcel','route','minutes'],
              [(f'{g}-{i}', g, float(v)) for g, values in [('Urban',[14,17,19,25,31,34,43]),
                                                       ('Rural',[20,23,28,31,41,49,62]),
                                                       ('Express',[8,12,15,18,21,27,32])]
               for i,v in enumerate(values)])
    cases['delivery'] = config('delivery.csv', 'independent', 'kruskal',
        {'id':'parcel','group':'route','value':'minutes'}, 'Synthetic skewed delivery times', 'Route', 'Time', 'minutes',
        group_order=['Urban','Rural','Express'], style={'summary':'median_iqr'})
    paths = {}
    for name, settings in cases.items():
        path = root/(name+'.json')
        path.write_text(json.dumps(settings, indent=2)+'\n', encoding='utf-8')
        paths[name] = path
    return paths


def main():
    from figureflow_science import analyze
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    args = parser.parse_args()
    paths = create_cases(args.directory)
    for name, path in paths.items():
        result = analyze(path, path.parent/(name+'-output'))
        print(name, result['status'], 'rows=', result['rows_used'], 'P=', result.get('pvalue', 'not calculated'), flush=True)


if __name__ == '__main__':
    main()
