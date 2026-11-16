import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

import figureflow as f


class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = [dict(panel='C1', condition='baseline', group='Ctrl', observation_id='r1',
                         sample_id='m1', value='0', unit='g'),
                     dict(panel='C1', condition='baseline', group='Ctrl', observation_id='r2',
                          sample_id='m2', value='', unit='g')]

    def write(self, name, rows):
        p = self.root / name
        with p.open('w', newline='') as file:
            w = csv.DictWriter(file, fieldnames=list(self.rows[0]))
            w.writeheader(); w.writerows(rows)
        return p

    def test_reorder_and_decimal_format_preserve_values(self):
        changed = copy.deepcopy(self.rows[::-1]); changed[1]['value'] = '0.00'
        r = f.audit(self.write('a.csv', self.rows), self.write('b.csv', changed))
        self.assertEqual(r['status'], 'pass')
        self.assertEqual(r['candidate_counts'][0]['n_observations'], 1)

    def test_blank_is_not_zero(self):
        changed = copy.deepcopy(self.rows); changed[1]['value'] = '0'
        self.assertEqual(f.audit(self.write('a.csv', self.rows), self.write('b.csv', changed))['status'], 'fail')

    def test_changed_sample_or_unit_is_detected(self):
        for field, value in [('sample_id', 'other'), ('unit', 'mg'), ('value', '0.1')]:
            changed = copy.deepcopy(self.rows); changed[0][field] = value
            self.assertEqual(f.audit(self.write('a.csv', self.rows), self.write('b.csv', changed))['status'], 'fail')

    def test_removal_requires_exact_authorized_entry(self):
        a, b = self.write('a.csv', self.rows), self.write('b.csv', self.rows[:1])
        self.assertEqual(f.audit(a, b)['status'], 'fail')
        exclusion = {k: self.rows[1][k] for k in f.KEY}
        exclusion.update(expected_value='', reason='Synthetic sensitivity example', authorization='demo request')
        self.assertEqual(f.audit(a, b, [exclusion])['status'], 'pass')
        exclusion['expected_value'] = '0'
        with self.assertRaises(ValueError): f.audit(a, b, [exclusion])

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError): f.observations(self.write('a.csv', self.rows[:1] * 2))

    def test_nonfinite_rejected(self):
        for value in ['NaN', 'Infinity', '-Infinity']:
            changed = copy.deepcopy(self.rows); changed[0]['value'] = value
            with self.assertRaises(ValueError): f.observations(self.write('a.csv', changed))

    def test_equal_values_are_not_deduplicated(self):
        rows = copy.deepcopy(self.rows); rows[1]['value'] = '0'
        r = f.audit(self.write('a.csv', rows), self.write('b.csv', rows))
        self.assertEqual(r['candidate_counts'][0]['n_observations'], 2)


class AnnotationTests(unittest.TestCase):
    def data(self, p=('0.001', '0.00001', '0.2', '0.01')):
        return {'group_order': ['Ctrl', 'A', 'B', 'C', 'D'], 'comparisons': [
            dict(panel='X', condition='baseline', reference='Ctrl', target=g, p_adjusted=value,
                 test='ANOVA', correction='Tukey', family='all_pairs') for g, value in zip(['A','B','C','D'], p)]}

    def test_fewest_stars_and_no_bridging_ns(self):
        r = f.annotation_plan(self.data())
        self.assertEqual([a['targets'] for a in r['annotations']], [['A','B'], ['D']])
        self.assertEqual([a['stars'] for a in r['annotations']], ['***', '**'])
        self.assertFalse(r['calculates_p_values'])

    def test_missing_intermediate_comparison_not_bridged(self):
        data = self.data(); data['comparisons'].pop(1)
        self.assertEqual([a['targets'] for a in f.annotation_plan(data)['annotations']], [['A'], ['D']])

    def test_family_and_condition_never_merged(self):
        data = self.data(); data['comparisons'][1]['family'] = 'separate'
        self.assertFalse(any(a['targets'] == ['A','B'] for a in f.annotation_plan(data)['annotations']))

    def test_invalid_p_and_duplicate_rejected(self):
        for p in [-0.1, 1.1, True, 'NaN']:
            data = self.data(); data['comparisons'][0]['p_adjusted'] = p
            with self.assertRaises(ValueError): f.annotation_plan(data)
        data = self.data(); data['comparisons'].append(data['comparisons'][0])
        with self.assertRaises(ValueError): f.annotation_plan(data)

    def test_thresholds(self):
        for p, expected in [('0.05','*'), ('0.01','**'), ('0.001','***'), ('0.0001','****'), ('0.05000001','ns')]:
            self.assertEqual(f.stars(p), expected)

    def test_empty_plan_does_not_claim_pass(self):
        data = self.data(); data['comparisons'] = []
        with self.assertRaises(ValueError): f.annotation_plan(data)


class LayoutTests(unittest.TestCase):
    def data(self):
        return {'tolerance_pt': 0.1, 'grid_pt': 72, 'panels': [
            dict(id='A', row=1, column=1, baseline_pt=144, x_origin_pt=72, label_top_pt=20, grid_required=True),
            dict(id='B', row=1, column=2, baseline_pt=144, x_origin_pt=288, label_top_pt=20, grid_required=True)]}

    def test_aligned(self): self.assertEqual(f.layout_audit(self.data())['status'], 'pass')

    def test_baseline_and_letters_checked_separately(self):
        for field in ['baseline_pt', 'label_top_pt']:
            data = self.data(); data['panels'][1][field] += 1
            self.assertEqual(f.layout_audit(data)['status'], 'fail')

    def test_offgrid_exception_does_not_skip_collinearity(self):
        data = self.data()
        for p in data['panels']: p.update(grid_required=False, baseline_pt=145)
        self.assertEqual(f.layout_audit(data)['status'], 'pass')
        data['panels'][1]['baseline_pt'] = 146
        self.assertEqual(f.layout_audit(data)['status'], 'fail')

    def test_legend_horizontal_and_vertical_checked(self):
        data = self.data(); data['panels'][0].update(legend_gap_pt=36, expected_legend_gap_pt=36,
                                                    legend_bottom_gap_pt=72, expected_legend_bottom_gap_pt=36)
        self.assertEqual(f.layout_audit(data)['status'], 'fail')

    def test_missing_measurement_not_silently_skipped(self):
        data = self.data(); del data['panels'][0]['label_top_pt']
        with self.assertRaises(ValueError): f.layout_audit(data)

    def test_string_false_is_not_boolean(self):
        data = self.data(); data['panels'][0]['grid_required'] = 'false'
        with self.assertRaises(ValueError): f.layout_audit(data)


class EvidenceTests(unittest.TestCase):
    def test_stale_evidence_and_missing_checks_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'figure.txt'; path.write_text('v1')
            record = {'required_checks':['visual'], 'checks':[dict(id='visual', status='pass', reviewer='demo',
                reason='Synthetic test only', checked_at='2026-01-01T00:00:00+00:00',
                artifacts=[dict(path='figure.txt', sha256=f.sha256(path))])]}
            self.assertEqual(f.verify_evidence(record, directory)['status'], 'pass')
            path.write_text('v2')
            self.assertEqual(f.verify_evidence(record, directory)['status'], 'fail')
            record['checks'] = []
            self.assertEqual(f.verify_evidence(record, directory)['status'], 'fail')

    def test_na_requires_evidence(self):
        r = f.verify_evidence({'required_checks':['x'], 'checks':[{'id':'x','status':'not_applicable'}]}, '.')
        self.assertEqual(r['status'], 'fail')


class ExportTests(unittest.TestCase):
    def test_export_plan_has_no_open_or_save(self):
        with tempfile.TemporaryDirectory() as directory:
            script = f.prism_export_script({'panels':[dict(id='A',section='G',page=1)]}, directory)
            self.assertIn('GoTo G, 1', script)
            self.assertNotIn('Open', script)
            self.assertNotIn('Save', script)
            (Path(directory)/'A.pdf').touch()
            with self.assertRaises(ValueError): f.prism_export_script({'panels':[dict(id='A',section='G',page=1)]}, directory)

    def test_script_injection_rejected(self):
        with self.assertRaises(ValueError):
            f.prism_export_script({'panels':[dict(id='A\nOpen x', section='G',page=1)]}, '.')


if __name__ == '__main__': unittest.main()
