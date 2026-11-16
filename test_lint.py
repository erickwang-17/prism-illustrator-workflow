import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import figureflow as f
from figureflow_lint import lint_manifest, RULES

ROOT = Path(__file__).resolve().parent


class LintTests(unittest.TestCase):
    def setUp(self):
        self.data = f.load_json(ROOT / 'example_manifest.json')
        self.panel = self.data['panels'][0]
        self.legend = self.panel['legends'][0]

    def codes(self):
        return {d['code'] for d in lint_manifest(self.data)['diagnostics']}

    def test_synthetic_example_passes_all_rules(self):
        report = lint_manifest(self.data)
        self.assertEqual(report['status'], 'pass')
        self.assertEqual(report['selected_rules'], list(RULES))
        self.assertTrue(all(report['rule_evaluations'].values()))

    def test_wrong_control_name_is_not_silently_rewritten(self):
        self.legend['label'] = 'VAV1-Cre (n=3)'
        before = copy.deepcopy(self.data)
        self.assertIn('NAM001', self.codes())
        self.assertEqual(self.data, before)

    def test_sample_count_must_match_audited_count(self):
        for label in ['Vav-Cre', 'Vav-Cre (n=4)', 'Vav-Cre (n=0)',
                      'Vav-Cre (n=３)', 'Vav-Cre (n=3)\n', 'Vav-Cre (n=3) (n=3)']:
            self.legend['label'] = label
            self.assertIn('LEG001', self.codes(), label)

    def test_aml_requires_count_and_native_black_border(self):
        aml = self.panel['legends'][-1]
        aml.update(label='NA⁻/⁻ AML', border_color='Pink', native=False)
        self.assertTrue({'LEG001', 'FMT002'} <= self.codes())

    def test_order_and_italics(self):
        self.legend['n_italic'] = False
        self.panel['legends'][2], self.panel['legends'][4] = self.panel['legends'][4], self.panel['legends'][2]
        self.assertTrue({'LEG002', 'LEG003'} <= self.codes())

    def test_approximate_color_is_rejected(self):
        self.legend['fill'] = '#000001'
        self.assertIn('COL001', self.codes())

    def test_color_case_does_not_change_rgb(self):
        self.panel['legends'][-1]['fill'] = '#ffd5d5'
        self.assertNotIn('COL001', self.codes())

    def test_wrong_star_font_and_size(self):
        self.panel['stars'][0].update(text='*****', font='Times', size_pt=11)
        self.assertIn('STA001', self.codes())

    def test_error_layer_width_and_axes(self):
        self.panel.update(axis_bold=False, x_ticks=True, x_title='XTitle')
        self.panel['error_bars'].update(width_pt=0.5, layer='underneath')
        self.assertTrue({'FMT003', 'FMT004'} <= self.codes())

    def test_every_panel_is_checked(self):
        second = copy.deepcopy(self.panel)
        second.update(id='DEMO_C2', font='Helvetica')
        self.data['panels'].append(second)
        report = lint_manifest(self.data)
        self.assertTrue(any(d['path'] == '$.panels[1].font' for d in report['diagnostics']))

    def test_partial_rule_selection_is_explicit(self):
        self.legend['label'] = 'VAV1-Cre'
        report = lint_manifest(self.data, ['COL001'])
        self.assertFalse(report['full_rule_set'])
        self.assertEqual(report['selected_rules'], ['COL001'])
        for codes in [[], ['COL001', 'COL001'], ['MISSING']]:
            with self.assertRaises(ValueError): lint_manifest(self.data, codes)

    def test_misspelled_field_is_rejected_even_for_partial_selection(self):
        self.legend['n_italics'] = self.legend.pop('n_italic')
        with self.assertRaises(ValueError): lint_manifest(self.data, ['COL001'])

    def test_required_unknown_measurements_not_defaulted(self):
        for field in ['border_width_pt', 'error_width_pt']:
            data = copy.deepcopy(self.data)
            data['reference'][field] = None
            with self.assertRaises(ValueError): lint_manifest(data)

    def test_duplicate_panels_and_legend_groups_rejected(self):
        self.data['panels'].append(copy.deepcopy(self.panel))
        with self.assertRaises(ValueError): lint_manifest(self.data)
        self.data['panels'].pop()
        self.panel['legends'].append(copy.deepcopy(self.legend))
        with self.assertRaises(ValueError): lint_manifest(self.data)

    def test_boolean_not_numeric_and_nonfinite_not_width(self):
        for bad in [True, 0, -1, float('inf'), float('nan')]:
            self.legend['border_width_pt'] = bad
            with self.assertRaises(ValueError): lint_manifest(self.data)

    def test_non_scatter_does_not_require_scatter_tick_policy(self):
        self.panel.update(kind='survival', x_ticks=True, x_title='Days', error_bars=None)
        self.assertEqual(lint_manifest(self.data)['status'], 'pass')


class CliTests(unittest.TestCase):
    def test_summary_preserves_failures_and_does_not_claim_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, status in enumerate(['pass', 'fail']):
                path = Path(directory) / f'report{index}.json'
                path.write_text(json.dumps(dict(report_version=1, tool_version='0.2.0',
                                               command='lint', status=status, full_rule_set=False)))
                paths.append(path)
            report = f.summarize_reports(paths)
            self.assertEqual(report['status'], 'fail')
            self.assertFalse(report['complete_figure_acceptance'])
            self.assertEqual(report['reports'][1]['sha256'], f.sha256(paths[1]))
            self.assertFalse(report['reports'][1]['full_rule_set'])
            with self.assertRaises(ValueError): f.summarize_reports([paths[0], paths[0]])

    def test_summary_rejects_unknown_and_empty_reports(self):
        with self.assertRaises(ValueError): f.summarize_reports([])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'old.json'
            for data in [{'status': 'pass'}, dict(report_version=1, command='hash', status='pass')]:
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError): f.summarize_reports([path])

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text('{"panels": [], "panels": [1]}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'): f.load_json(path)

    def test_json_error_stays_on_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text('{}')
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = f.main(['lint', str(path), '--error-format', 'json'])
            self.assertEqual(code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(json.loads(stderr.getvalue())['code'], 'INPUT001')

    def test_report_version_and_input_hash(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = f.main(['lint', str(ROOT / 'example_manifest.json')])
        report = json.loads(out.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(report['report_version'], 1)
        self.assertEqual(report['input_sha256'], f.sha256(ROOT / 'example_manifest.json'))

    def test_cli_does_not_accept_ambiguous_option_abbreviations(self):
        run = subprocess.run([sys.executable, str(ROOT / 'figureflow.py'), 'lint',
                              str(ROOT / 'example_manifest.json'), '--sel', 'NAM001'], capture_output=True)
        self.assertEqual(run.returncode, 2)

    def test_lint_failure_exit_status_and_text_diagnostics(self):
        data = f.load_json(ROOT / 'example_manifest.json')
        data['panels'][0]['font'] = 'Times'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            path.write_text(json.dumps(data))
            out = io.StringIO()
            with contextlib.redirect_stdout(out): code = f.main(['lint', str(path), '--format', 'text'])
            self.assertEqual(code, 1)
            self.assertIn('FMT001', out.getvalue())


if __name__ == '__main__':
    unittest.main()
