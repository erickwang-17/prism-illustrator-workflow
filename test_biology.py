"""Offline synthetic tests for the biological case; never download research data in CI."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from scipy import stats
from example_biology import adjust, aggregate, compare, pca_complete, validate_records, run


class BiologyTests(unittest.TestCase):
    def rows(self):
        return [dict(MouseID=f'm{i}_{j}',Genotype='Ts65Dn',Treatment='Saline',Behavior='C/S',
                     **{'class':'t-CS-s','P_N':float(i+j),'source_row':i*15+j+1})
                for i in range(4) for j in range(1,16)]

    def test_technical_repeats_are_not_biological_n(self):
        grouped=validate_records(self.rows(),['P_N'])
        mice,x,n=aggregate(grouped,['P_N'])
        self.assertEqual(x.shape,(4,1));self.assertTrue(np.all(n==15))
        np.testing.assert_allclose(x[:,0],[8,9,10,11])

    def test_repeat_identity_and_metadata_fail(self):
        for mutation in ('duplicate','missing','metadata','group'):
            rows=self.rows()
            if mutation=='duplicate':rows.append(rows[0].copy())
            if mutation=='missing':rows.pop()
            if mutation=='metadata':rows[0]['Treatment']='Memantine'
            if mutation=='group':rows[0].update(Treatment='Memantine',**{'class':'t-CS-m'})
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate_records(rows,['P_N'])

    def test_negative_retained_nonfinite_rejected(self):
        rows=self.rows();rows[0]['P_N']=-.06
        self.assertEqual(validate_records(rows,['P_N'])['m0'][0]['P_N'],-.06)
        for v in [np.nan,np.inf,True]:
            rows[0]['P_N']=v
            with self.assertRaises(ValueError):validate_records(rows,['P_N'])

    def test_missing_coverage_threshold_and_no_imputation(self):
        rows=self.rows()
        for r in rows[:8]:r['P_N']=None
        grouped=validate_records(rows,['P_N']);_,x,n=aggregate(grouped,['P_N'])
        self.assertTrue(np.isnan(x[0,0]));self.assertEqual(n[0,0],7)
        rows[7]['P_N']=4
        _,x,n=aggregate(validate_records(rows,['P_N']),['P_N'])
        self.assertTrue(np.isfinite(x[0,0]));self.assertEqual(n[0,0],8)

    def test_bh_by_known_values_and_independent_library(self):
        p=[.001,.01,.03,.1]
        np.testing.assert_allclose(adjust(p),[.004,.02,.04,.1])
        for method in ['BH','BY']:
            rng=np.random.default_rng(8);p=rng.uniform(size=154)
            np.testing.assert_allclose(adjust(p,method),stats.false_discovery_control(p,method=method.lower()),rtol=1e-12)
        for p in [[],[np.nan],[-.1],[1.1]]:
            with self.assertRaises(ValueError):adjust(p)

    def test_missing_tests_keep_family_and_n(self):
        labels=['t-CS-m']*4+['t-CS-s']*5+['c-CS-s']*3
        x=np.column_stack([np.arange(12,dtype=float),np.full(12,np.nan)])
        result=compare(x,labels,['A_N','missing_N'])
        self.assertEqual(len(result),4)
        self.assertEqual((result[0]['n_a'],result[0]['n_b']),(4,5))
        self.assertEqual(result[1]['status'],'not_testable');self.assertIsNone(result[1]['q_bh'])
        expected=stats.ttest_ind(x[:4,0],x[4:9,0],equal_var=False)
        self.assertAlmostEqual(result[0]['p'],expected.pvalue)
        q=adjust([r.get('p',1.) for r in result]);self.assertAlmostEqual(result[0]['q_bh'],q[0])

    def test_pca_uses_only_complete_variable_features(self):
        x=np.array([[1,2,3,2],[2,4,np.nan,2],[3,5,2,2],[4,8,1,2]],float)
        scores,var,keep=pca_complete(x)
        self.assertEqual(keep.tolist(),[True,True,False,False]);self.assertEqual(scores.shape,(4,2))
        self.assertAlmostEqual(sum(var),1);self.assertTrue(np.isfinite(scores).all())

    def test_corrupt_archive_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.zip';p.write_bytes(b'not approved data');out=Path(t)/'output'
            with self.assertRaises(ValueError):run(p,out)
            self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
