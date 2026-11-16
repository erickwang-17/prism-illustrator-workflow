"""Cross-domain numerical, input-integrity, rendering and CLI regressions."""
import contextlib
import copy
import io
import itertools
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

import figureflow as cli
import figureflow_science as science
from demo_science import create_cases, config, write_csv
from figureflow_lint import lint_manifest


class ScienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.paths = create_cases(cls.root/'cases')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def case(self, name):
        c = science.validate_config(cli.load_json(self.paths[name]))
        _, data, _, _, _ = science.prepare(c, self.paths[name].parent)
        return c, data

    def test_welch_matches_manual_t_and_degrees_of_freedom(self):
        c, data = self.case('manufacturing')
        result, _ = science.infer(c, data)
        values = [[r['value'] for r in data if r['group']==g] for g in c['group_order']]
        means = [sum(a)/len(a) for a in values]
        scaled_vars = [sum((x-m)**2 for x in a)/(len(a)-1)/len(a) for a,m in zip(values,means)]
        expected_t = (means[0]-means[1])/math.sqrt(sum(scaled_vars))
        expected_df = sum(scaled_vars)**2/sum(v*v/(len(a)-1) for v,a in zip(scaled_vars,values))
        self.assertAlmostEqual(result['statistic'], expected_t, places=11)
        self.assertAlmostEqual(result['df'], expected_df, places=11)
        self.assertEqual([g['n'] for g in result['groups']], [18,27])
        self.assertLess(result['effect']['ci95'][0], result['effect']['value'])
        self.assertGreater(result['effect']['ci95'][1], result['effect']['value'])

    def test_pairing_by_id_not_row_position(self):
        c, data = self.case('calibration')
        result, groups = science.infer(c, data)
        a,b = groups.values()
        differences = [x['value']-y['value'] for x,y in zip(a,b)]
        mean = sum(differences)/len(differences)
        sd = math.sqrt(sum((x-mean)**2 for x in differences)/(len(differences)-1))
        self.assertAlmostEqual(result['statistic'], mean/(sd/math.sqrt(len(differences))))
        self.assertEqual(science.infer(c, list(reversed(data)))[0], result)

    def test_incomplete_pair_is_rejected(self):
        c, data = self.case('calibration')
        with self.assertRaisesRegex(ValueError, 'Incomplete pairs'): science.infer(c, data[:-1])

    def test_holm_known_answer_and_order(self):
        self.assertEqual(science.holm([.01,.04,.03]), [.03,.06,.06])
        self.assertEqual(science.holm([.8,.9]), [1.,1.])

    def test_explicit_contrast_family(self):
        c, data = self.case('agriculture')
        report, _ = science.infer(c, data)
        self.assertEqual(len(report['comparisons']), 2)
        for comparison in report['comparisons']:
            self.assertGreaterEqual(comparison['p_adjusted'], comparison['pvalue'])
            self.assertEqual(comparison['correction'], 'Holm')
        del c['correction']
        with self.assertRaisesRegex(ValueError, 'explicit pairwise'): science.validate_config(c)

    def test_fisher_against_enumerated_hypergeometric(self):
        c,data = self.case('website'); report,_ = science.infer(c,data)
        # Margins: row1=8, row2=5, col1=7, N=13. Exact two-sided enumeration.
        probability = lambda k: math.comb(7,k)*math.comb(6,8-k)/math.comb(13,8)
        probabilities = [probability(k) for k in range(2,8)]
        expected = sum(p for p in probabilities if p <= probability(6)+1e-14)
        self.assertAlmostEqual(report['pvalue'], expected)
        self.assertAlmostEqual(report['effect']['value'], 12.)
        self.assertEqual(report['n'],13)

    def test_zero_cell_odds_ratio_is_reported_as_unbounded(self):
        c,data = self.case('website'); data[1]['count']=0
        report,_ = science.infer(c,data)
        self.assertIsNone(report['effect']['value'])
        self.assertTrue(report['effect']['unbounded'])
        json.dumps(report,allow_nan=False)

    def test_exact_spearman_small_n_against_exhaustive_permutations(self):
        c,_ = self.case('ranks')
        data=[dict(id=str(i),x=i,y=i) for i in range(4)]
        report,_ = science.infer(c,data)
        # Two perfect monotone permutations out of 4! possible pairings.
        self.assertAlmostEqual(report['pvalue'],2/math.factorial(4))
        self.assertAlmostEqual(report['statistic'],1.)

    def test_nonlinear_counterexample_is_not_hidden_by_summary(self):
        c,data=self.case('nonlinear'); report,_=science.infer(c,data)
        self.assertLess(abs(report['statistic']), .02)
        self.assertGreater(max(r['y'] for r in data)-min(r['y'] for r in data),40)
        self.assertTrue(any('shape' in w for w in report['warnings']))

    def test_time_series_has_no_invented_pvalue(self):
        c,data=self.case('energy'); report,_=science.infer(c,data)
        self.assertNotIn('pvalue',report)
        self.assertEqual(report['n'],24)

    def test_unsupported_design_and_unknown_fields_rejected(self):
        c,_=self.case('calibration')
        for key,value in [('method','welch_t'),('design_confirmed',False),('missing','mean'),('schema_version',True),('unexpected',1)]:
            bad=dict(c);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): science.validate_config(bad)

    def test_missing_policy_logs_source_rows_and_preserves_equal_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            write_csv(root/'data.csv',['id','g','v'],[['a','A',1],['b','A',1],['c','B',2],['d','B',3],['e','B','']])
            c=config('data.csv','independent','welch_t',dict(id='id',group='g',value='v'),'Title','X','Y','mm',group_order=['A','B'])
            with self.assertRaisesRegex(ValueError,'Missing cells'):science.prepare(c,root)
            c['missing']='drop';_,data,dropped,total,_=science.prepare(c,root)
            self.assertEqual(len(data),4);self.assertEqual(total,5)
            self.assertEqual(dropped[0]['source_row'],6)
            self.assertEqual(sum(r['value']==1 for r in data),2)

    def test_duplicate_unit_ids_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            write_csv(root/'data.csv',['id','g','v'],[['a','A',1],['a','B',2]])
            c=config('data.csv','independent','welch_t',dict(id='id',group='g',value='v'),'Title','X','Y','mm',group_order=['A','B'])
            with self.assertRaisesRegex(ValueError,'Duplicate experimental'):science.prepare(c,root)

    def test_nonfinite_and_bool_are_not_numeric(self):
        for value in [True,float('nan'),'NaN','inf','-inf','1,000',None]:
            with self.subTest(value=value),self.assertRaises(ValueError):science.finite(value,'test')

    def test_formula_and_ambiguous_workbook_rejected(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'data.xlsx';book=Workbook();book.active.append(['id','value']);book.active.append(['a','=1+1'])
            book.save(path)
            with self.assertRaisesRegex(ValueError,'Formula cells'):science.read_table(path)
            book.create_sheet('Other');book.save(path);book.close()
            with self.assertRaisesRegex(ValueError,'Choose sheet'):science.read_table(path)

    def test_percentages_require_counts_declaration_and_fractional_counts_rejected(self):
        c,_=self.case('website');c['count_basis']='percentages'
        with self.assertRaisesRegex(ValueError,'observed_counts'):science.validate_config(c)
        # Values 50/50 could be counts: software cannot infer their real provenance.
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write_csv(root/'x.csv',['variant','outcome','visitors'],[['A','yes',1.5]])
            c['source']={'path':'x.csv'};c['count_basis']='observed_counts'
            with self.assertRaisesRegex(ValueError,'exact integers'):science.prepare(c,root)

    def test_degenerate_data_rejected(self):
        c,data=self.case('manufacturing')
        for r in data:r['value']=1.
        with self.assertRaisesRegex(ValueError,'zero variance'):science.infer(c,data)

    def test_generic_profile_allows_unrelated_names_fonts_and_ticks(self):
        manifest=cli.load_json(Path(__file__).parent/'example_manifest.json')
        for p in manifest['panels']:
            p.update(font='DejaVu Sans',axis_bold=False,x_ticks=True)
            for legend in p['legends']:legend.update(font='DejaVu Sans',n_italic=False,native=False)
            for star in p['stars']:star['font']='DejaVu Sans'
        report=lint_manifest(manifest,profile='generic')
        self.assertEqual(report['status'],'pass')
        self.assertEqual(lint_manifest(manifest,profile='uwm')['status'],'fail')
        self.assertEqual(report['profile_settings']['canonical_names'],{})

    def test_inspect_cli_reports_structure_only(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            code=cli.main(['inspect',str(self.paths['manufacturing'].with_suffix('.csv'))])
        report=json.loads(out.getvalue());self.assertEqual(code,0)
        self.assertEqual(report['rows'],45);self.assertIn('no automatic',report['scope'])

    def test_all_eight_domains_render_and_preserve_sources(self):
        from PIL import Image
        for name,path in self.paths.items():
            with self.subTest(name=name):
                c=cli.load_json(path);source=path.parent/c['source']['path'];before=science.digest(source)
                out=self.root/(name+'-render')
                report=science.analyze(path,out)
                self.assertEqual(science.digest(source),before)
                self.assertEqual(report['source_sha256'],before)
                self.assertEqual(report['status'],'pass')
                self.assertFalse(report['render']['native_prism'])
                self.assertTrue(report['render']['visual_review_required'])
                self.assertEqual(set(report['artifacts']),{'figure.svg','figure.pdf','figure.png','normalized.csv','config.json'})
                for filename,digest in report['artifacts'].items():self.assertEqual(science.digest(out/filename),digest)
                tree=ET.parse(out/'figure.svg')
                self.assertIn(c['title'],''.join(tree.getroot().itertext()))
                with Image.open(out/'figure.png') as image:self.assertEqual(image.size,(1260,900))
                self.assertTrue((out/'figure.pdf').read_bytes().startswith(b'%PDF'))
                with self.assertRaisesRegex(ValueError,'already exists'):science.analyze(path,out)

    def test_failed_render_leaves_no_final_output(self):
        path=self.root/'bad-font.json';c=cli.load_json(self.paths['manufacturing'])
        c['source']['path']=str(self.paths['manufacturing'].with_suffix('.csv'))
        c['style']={'font':'DefinitelyMissingFontXYZ'};path.write_text(json.dumps(c))
        out=self.root/'bad-font-output'
        with self.assertRaises(ValueError):science.analyze(path,out)
        self.assertFalse(out.exists())

    def test_input_change_during_render_blocks_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=root/'settings.json';c=cli.load_json(self.paths['manufacturing'])
            c['source']['path']=str(self.paths['manufacturing'].with_suffix('.csv'));path.write_text(json.dumps(c))
            def changed(*args):
                path.write_text(json.dumps(dict(c,title='Changed')))
                return {}
            with mock.patch.object(science,'render',side_effect=changed):
                with self.assertRaisesRegex(ValueError,'Input changed'):science.analyze(path,root/'output')
            self.assertFalse((root/'output').exists())

    def test_invisible_and_duplicate_palette_rejected(self):
        c,data=self.case('manufacturing');report,groups=science.infer(c,data)
        with tempfile.TemporaryDirectory() as temp:
            for palette in [['none','red'],['red','#ff0000'],['red']]:
                c['style']={'palette':palette}
                with self.subTest(palette=palette),self.assertRaises(ValueError):
                    science.render(c,data,report,groups,Path(temp))

    def test_missing_glyphs_rejected_instead_of_replaced(self):
        c,data=self.case('manufacturing');report,groups=science.infer(c,data)
        c['title']='Missing glyph \U0010ffff'
        with tempfile.TemporaryDirectory() as temp,self.assertRaisesRegex(ValueError,'lacks required glyphs'):
            science.render(c,data,report,groups,Path(temp))

    def test_overflowing_labels_are_not_published(self):
        c,data=self.case('manufacturing');report,groups=science.infer(c,data)
        c['x_label']='X'*300
        with tempfile.TemporaryDirectory() as temp,self.assertRaisesRegex(ValueError,'Text exceeds canvas'):
            science.render(c,data,report,groups,Path(temp))

    def test_oversized_counts_are_not_rounded_into_valid_counts(self):
        c,_=self.case('website')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write_csv(root/'x.csv',['variant','outcome','visitors'],[['A','yes','9007199254740993']])
            c['source']={'path':'x.csv'}
            with self.assertRaisesRegex(ValueError,'exact integers'):science.prepare(c,root)

    def test_time_sorting_and_duplicate_times(self):
        c,_=self.case('energy')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);c['source']={'path':'x.csv'}
            write_csv(root/'x.csv',['reading','date','power'],[['a','2025-01-02',2],['b','2025-01-01',1]])
            self.assertEqual(science.prepare(c,root)[1][0]['id'],'b')
            write_csv(root/'x.csv',['reading','date','power'],[['a','2025-01-01',2],['b','2025-01-01',1]])
            with self.assertRaisesRegex(ValueError,'Duplicate time'):science.prepare(c,root)

    def test_custom_profile_records_and_enforces_preferences(self):
        from figureflow_lint import PROFILES
        manifest=cli.load_json(Path(__file__).parent/'example_manifest.json')
        profile=copy.deepcopy(PROFILES['generic']);profile.update(font='Arial',star_size_pt=12)
        report=lint_manifest(manifest,profile=profile)
        self.assertEqual({d['code'] for d in report['diagnostics']},{'STA001'})
        self.assertEqual(report['profile'],'custom')
        profile['surprise']=True
        with self.assertRaises(ValueError):lint_manifest(manifest,profile=profile)


if __name__=='__main__':unittest.main()
