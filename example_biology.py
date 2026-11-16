"""Audited UCI mouse-protein case study; download only with --download.

Run: python example_biology.py --download --directory local/mice-case
Offline: python example_biology.py --archive local/uci-mice.zip --directory local/mice-case
This explicit exploratory workflow is not the generic analyze command or the source paper's model.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import importlib.metadata
import json
from pathlib import Path
import re
import tempfile
import urllib.request
import zipfile

import numpy as np
from scipy import stats

GROUPS = ['c-CS-s','c-CS-m','c-SC-s','c-SC-m','t-CS-s','t-CS-m','t-SC-s','t-SC-m']
COLORS = ['#0072B2','#56B4E9','#009E73','#006644','#D55E00','#CC79A7','#E69F00','#666666']
COUNTS = [9,10,9,10,7,9,9,9]
DISPLAY = ['DYRK1A_N','pERK_N','pAKT_N','pCREB_N']
CONTRASTS = [('trisomy_CS_drug','t-CS-m','t-CS-s'),('CS_genotype_saline','t-CS-s','c-CS-s')]
ARCHIVE_HASH = '5b46e1f4e104506397db9c1968e7ea43adceec844a2f55ed5cb38a944057a26d'
MEMBER_HASH = 'af7e7fa94ffb82f4edb4590d46d9c9075b71b2c3ede8d37934bef569c251e3c1'
URL = 'https://archive.ics.uci.edu/static/public/342/mice+protein+expression.zip'
MEMBER = 'Data_Cortex_Nuclear.xls'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def adjust(pvalues, method='BH'):
    """BH or BY adjusted P, retaining declared family slots. Nonfinite values fail."""
    p = np.asarray(pvalues, dtype=float)
    if p.ndim != 1 or len(p) == 0 or not np.all(np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError('Expected a nonempty finite P vector in [0,1]')
    if method not in ('BH','BY'):
        raise ValueError('Unknown adjustment')
    order = np.argsort(p, kind='stable'); m = len(p)
    factor = np.sum(1 / np.arange(1,m+1)) if method == 'BY' else 1.
    ranked = np.minimum.accumulate((p[order] * m * factor / np.arange(1,m+1))[::-1])[::-1]
    out = np.empty(m); out[order] = np.minimum(ranked,1)
    return out


def validate_records(records, proteins, expected_repeats=15):
    """No silently changing class labels, duplicate repeats, missing repeat IDs or nonfinite cells."""
    grouped = defaultdict(list); seen = set()
    for row in records:
        match = re.fullmatch(r'(.+)_([1-9][0-9]*)', str(row['MouseID']))
        if not match: raise ValueError('MouseID must end in an explicit repeat number')
        mouse, repeat = match.group(1), int(match.group(2))
        if (mouse,repeat) in seen: raise ValueError('Duplicate mouse/repeat identity')
        seen.add((mouse,repeat))
        if row['class'] not in GROUPS: raise ValueError('Unknown biological group')
        c,behavior,treatment = row['class'].split('-')
        expected = ('Control' if c=='c' else 'Ts65Dn', 'Memantine' if treatment=='m' else 'Saline', 'C/S' if behavior=='CS' else 'S/C')
        if tuple(row[k] for k in ('Genotype','Treatment','Behavior')) != expected:
            raise ValueError('Class disagrees with biological metadata')
        for p in proteins:
            v = row[p]
            if v is not None and (isinstance(v,bool) or not np.isfinite(v)):
                raise ValueError('Invalid protein expression value')
        grouped[mouse].append(row)
    for mouse,rows in grouped.items():
        if len({r['class'] for r in rows}) != 1: raise ValueError('Mouse changes biological group')
        repeats = {int(r['MouseID'].rsplit('_',1)[1]) for r in rows}
        if repeats != set(range(1,expected_repeats+1)): raise ValueError('Incomplete technical repeat identity set')
    return grouped


def aggregate(grouped, proteins, minimum=8, method='median'):
    if method not in ('median','mean'): raise ValueError('Unknown aggregation')
    if not isinstance(minimum,int) or minimum < 1: raise ValueError('Invalid minimum')
    mice = sorted(grouped, key=lambda m:(GROUPS.index(grouped[m][0]['class']),m))
    matrix = np.full((len(mice),len(proteins)),np.nan); available = np.zeros_like(matrix,dtype=int)
    for i,m in enumerate(mice):
        for j,p in enumerate(proteins):
            values = [r[p] for r in grouped[m] if r[p] is not None]
            available[i,j] = len(values)
            if len(values)>=minimum:
                matrix[i,j] = float(getattr(np,method)(values))
    return mice, matrix, available


def compare(matrix, labels, proteins):
    records=[]
    for contrast,a,b in CONTRASTS:
        for j,p in enumerate(proteins):
            x=matrix[np.array(labels)==a,j]; y=matrix[np.array(labels)==b,j]
            x=x[np.isfinite(x)]; y=y[np.isfinite(y)]
            r=dict(contrast=contrast,protein=p,a=a,b=b,n_a=len(x),n_b=len(y),status='not_testable')
            if min(len(x),len(y))>=3:
                va=np.var(x,ddof=1)/len(x); vb=np.var(y,ddof=1)/len(y)
                if va+vb>0:
                    se=np.sqrt(va+vb); df=(va+vb)**2/(va**2/(len(x)-1)+vb**2/(len(y)-1))
                    effect=float(np.mean(x)-np.mean(y)); t=effect/se
                    pval=float(2*stats.t.sf(abs(t),df)); delta=float(stats.t.ppf(.975,df)*se)
                    fold=float(np.log2(np.mean(x)/np.mean(y))) if min(np.mean(x),np.mean(y))>0 else None
                    r.update(status='tested',mean_a=float(np.mean(x)),mean_b=float(np.mean(y)),
                             difference=effect,ci_low=effect-delta,ci_high=effect+delta,
                             log2_ratio_of_means=fold,t=float(t),df=float(df),p=pval)
            records.append(r)
    # Missing tests occupy their planned family position but never receive an inferential result.
    pvals=[r.get('p',1.) for r in records]
    bh=adjust(pvals); by=adjust(pvals,'BY')
    for r,q,qby in zip(records,bh,by):
        r.update(q_bh=float(q) if r['status']=='tested' else None,q_by=float(qby) if r['status']=='tested' else None)
    return records


def pca_complete(matrix):
    keep=np.all(np.isfinite(matrix),axis=0) & (np.nanstd(matrix,axis=0,ddof=1)>0)
    if np.sum(keep)<2: raise ValueError('PCA needs at least two complete variable proteins')
    x=matrix[:,keep]; z=(x-x.mean(0))/x.std(0,ddof=1)
    u,s,vt=np.linalg.svd(z,full_matrices=False)
    return u[:,:2]*s[:2], (s*s/np.sum(s*s))[:2],keep


def stars(p):
    return '****' if p<=.0001 else '***' if p<=.001 else '**' if p<=.01 else '*' if p<=.05 else 'ns'


def render(out,mice,labels,proteins,matrix,available,results,coords,explained):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.text import Text
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelweight':'bold',
                         'axes.titleweight':'bold','svg.fonttype':'none','pdf.fonttype':42})
    fig,axes=plt.subplots(4,2,figsize=(14,18),layout='constrained')
    fig.suptitle('Mouse cortex protein expression | UCI 342\n72 mice, 77 proteins, 1,080 technical measurements',fontsize=17)
    for letter,ax in zip('ABCDEFGH',axes.flat):
        ax.text(-.13,1.06,letter,transform=ax.transAxes,fontweight='bold',fontsize=16)
        ax.spines[['top','right']].set_visible(False)
    ax=axes[0,0]; counts=[labels.count(g) for g in GROUPS]
    ax.bar(np.arange(8),counts,color=COLORS,edgecolor='black')
    ax.set_xticks(range(8),GROUPS,rotation=35,ha='right'); ax.set_ylim(0,12)
    for i,n in enumerate(counts):ax.text(i,n+.15,f'n={n}',ha='center',fontstyle='italic')
    ax.set(title='Experimental groups: biological n',ylabel='Mice')
    ax=axes[0,1]; im=ax.imshow(available.T,aspect='auto',vmin=0,vmax=15,cmap='viridis',interpolation='nearest')
    ax.set(title='QC: available measurements per mouse/protein',xlabel='Mice ordered by group',ylabel='Protein index (source order)')
    ax.set_yticks([0,19,39,59,76],[1,20,40,60,77])
    bounds=np.cumsum(counts)
    for b in bounds[:-1]:ax.axvline(b-.5,color='white',lw=.7)
    fig.colorbar(im,ax=ax,label='Available of 15 measurements',ticks=[0,5,8,10,15])
    ax=axes[1,0]
    for g,c in zip(GROUPS,COLORS):
        mask=np.array(labels)==g;ax.scatter(coords[mask,0],coords[mask,1],s=34,c=c,edgecolors='black',linewidths=.6,label=f'{g} (n={int(mask.sum())})')
    ax.set(title='Descriptive PCA: complete proteins only',xlabel=f'PC1 ({explained[0]:.1%})',ylabel=f'PC2 ({explained[1]:.1%})')
    ax.legend(fontsize=8,ncol=2,loc='upper center',bbox_to_anchor=(.5,-.2),frameon=False)
    ax=axes[1,1];primary=[r for r in results if r['contrast']==CONTRASTS[0][0] and r['status']=='tested' and r['log2_ratio_of_means'] is not None]
    for sig,c,label in [(False,'#888888','BH q > 0.05'),(True,'#A02060','BH q ≤ 0.05')]:
        selected=[r for r in primary if (r['q_bh']<=.05)==sig]
        ax.scatter([r['log2_ratio_of_means'] for r in selected],[-np.log10(max(r['q_bh'],1e-300)) for r in selected],c=c,s=28,edgecolor='black',lw=.4,label=f'{label} ({len(selected)})')
    ax.axhline(-np.log10(.05),ls='--',c='black',lw=.8); ax.axvline(0,c='black',lw=.7)
    ax.set(title='Trisomy CS: memantine − saline',xlabel='log2 ratio of group means',ylabel='−log10 BH-adjusted P (154-test family)');ax.legend(fontsize=8,frameon=False)
    order=['c-CS-s','t-CS-s','t-CS-m'];rng=np.random.default_rng(342)
    for ax,p in zip(axes[2:,:].flat,DISPLAY):
        j=proteins.index(p); allvalues=[]; upper=[]
        for i,g in enumerate(order):
            v=matrix[np.array(labels)==g,j];v=v[np.isfinite(v)];allvalues.extend(v)
            ax.scatter(i+rng.uniform(-.12,.12,len(v)),v,s=40,c=COLORS[GROUPS.index(g)],edgecolor='black',lw=.8,zorder=3)
            mean=np.mean(v);sd=np.std(v,ddof=1);upper.extend([mean+sd,max(v)])
            ax.errorbar(i,mean,yerr=sd,fmt='_',ms=22,color='black',capsize=5,elinewidth=1.2,zorder=5)
        span=max(max(upper)-min(allvalues),.05);start=max(upper)+.14*span
        for level,(cid,a,b) in enumerate(CONTRASTS[::-1]):
            r=next(r for r in results if r['protein']==p and r['contrast']==cid)
            x1,x2=sorted((order.index(a),order.index(b)));y=start+level*.25*span
            ax.plot([x1,x1,x2,x2],[y-.05*span,y,y,y-.05*span],c='black',lw=1)
            ax.text((x1+x2)/2,y+.02*span,stars(r['q_bh']) if r['q_bh'] is not None else 'NA',ha='center',va='bottom',fontsize=10,fontweight='bold')
        ax.set_ylim(bottom=min(0,min(allvalues)-.1*span),top=start+.55*span)
        ax.set_xticks(range(3),[f'{g}\n(n={int(np.isfinite(matrix[np.array(labels)==g,j]).sum())})' for g in order])
        ax.set(title=p+' | prespecified display',ylabel='Provided expression units');ax.tick_params(axis='x',length=0)
    fig.supxlabel('Exploratory mouse-level reanalysis • E–H: one point per mouse; mean ± SD • stars use BH q across both contrasts × 77 proteins',fontsize=10)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();box=fig.bbox
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text():
            b=t.get_window_extent(renderer)
            if b.x0 < -2 or b.y0 < -2 or b.x1>box.width+2 or b.y1>box.height+2:
                raise ValueError('Text outside figure: '+t.get_text())
    for ext in ('png','svg','pdf'):fig.savefig(out/f'figure.{ext}',dpi=160)
    plt.close(fig)


def write_csv(path, rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def run(archive, directory):
    import xlrd
    raw=Path(archive).read_bytes()
    if sha(raw)!=ARCHIVE_HASH:raise ValueError('UCI archive hash changed; review source before updating the pin')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info=z.getinfo(MEMBER)
        if info.file_size>5_000_000:raise ValueError('Oversized source member')
        source=z.read(MEMBER)
    if sha(source)!=MEMBER_HASH:raise ValueError('Source workbook hash differs')
    book=xlrd.open_workbook(file_contents=source);s=book.sheet_by_name('Hoja1');header=s.row_values(0)
    proteins=header[1:-4]
    if len(header)!=82 or len(proteins)!=77 or len(set(header))!=82 or any(not p.endswith('_N') for p in proteins):raise ValueError('Unexpected source schema')
    records=[]
    for i in range(1,s.nrows):
        r=dict(zip(header,s.row_values(i)));r['source_row']=i+1
        for p in proteins:
            r[p]=None if r[p]=='' else float(r[p])
        records.append(r)
    grouped=validate_records(records,proteins)
    if len(records)!=1080 or len(grouped)!=72:raise ValueError('Unexpected source dimensions')
    if Counter(rows[0]['class'] for rows in grouped.values())!=dict(zip(GROUPS,COUNTS)):raise ValueError('Source group counts differ')
    mice,matrix,available=aggregate(grouped,proteins);labels=[grouped[m][0]['class'] for m in mice]
    results=compare(matrix,labels,proteins)
    _,means,_=aggregate(grouped,proteins,method='mean');sensitivity=compare(means,labels,proteins)
    for r,sens in zip(results,sensitivity):
        r.update(mean_aggregation_p=sens.get('p'),mean_aggregation_q_bh=sens['q_bh'],mean_aggregation_difference=sens.get('difference'))
    coords,explained,keep=pca_complete(matrix)
    report=dict(schema_version=1,command='public_biology_example',status='computed_exploratory',
                source_url=URL,dataset_doi='10.24432/C50S3Z',license='CC BY 4.0',archive_sha256=sha(raw),workbook_sha256=sha(source),
                source_rows=len(records),biological_mice=len(mice),proteins=len(proteins),groups=dict(zip(GROUPS,COUNTS)),
                negative_measurements=[{'record':r['MouseID'],'protein':p,'value':r[p]} for r in records for p in proteins if r[p] is not None and r[p]<0],
                missing_measurement_cells=sum(r[p] is None for r in records for p in proteins),
                unavailable_mouse_protein_cells=int(np.isnan(matrix).sum()),
                mice_with_unavailable_proteins={m:int(np.isnan(matrix[i]).sum()) for i,m in enumerate(mice) if np.isnan(matrix[i]).any()},
                executed_settings={'primary_aggregation':'median','minimum_measurements':8,'sensitivity_aggregation':'mean','test':'two-sided Welch t','family_size':154,'primary_correction':'BH','sensitivity_correction':'BY','alpha':.05,'imputation_for_tests':False,'confidence_intervals':'pointwise 95%, unadjusted','jitter_seed':342},
                family_size=len(results),tested=sum(r['status']=='tested' for r in results),
                bh_significant={cid:sum(r['contrast']==cid and r['q_bh'] is not None and r['q_bh']<=.05 for r in results) for cid,_,_ in CONTRASTS},
                by_significant={cid:sum(r['contrast']==cid and r['q_by'] is not None and r['q_by']<=.05 for r in results) for cid,_,_ in CONTRASTS},
                aggregation_decision_changes=sum((r['q_bh'] is not None and r['q_bh']<=.05)!=(r['mean_aggregation_q_bh'] is not None and r['mean_aggregation_q_bh']<=.05) for r in results),
                pca_proteins=[p for p,k in zip(proteins,keep) if k],pca_explained_variance=explained.tolist(),
                pca_imputation=False,excluded_mice=[],native_prism=False,visual_review_required=True,
                versions={k:importlib.metadata.version(k) for k in ('numpy','scipy','matplotlib','xlrd')},
                plan=json.loads(Path(__file__).with_name('example_biology_plan.json').read_text()))
    # Numerical cross-check against SciPy's implementation for EVERY test, not only selected hits.
    for r in results:
        if r['status']=='tested':
            j=proteins.index(r['protein']);x=matrix[np.array(labels)==r['a'],j];y=matrix[np.array(labels)==r['b'],j]
            check=stats.ttest_ind(x[np.isfinite(x)],y[np.isfinite(y)],equal_var=False)
            ci=check.confidence_interval()
            if not np.allclose([r['t'],r['df'],r['p'],r['ci_low'],r['ci_high']],[check.statistic,check.df,check.pvalue,ci.low,ci.high],rtol=1e-10,atol=1e-14):raise ValueError('Welch cross-check failed')
    for method,key in [('bh','q_bh'),('by','q_by')]:
        reference=stats.false_discovery_control([r.get('p',1.) for r in results],method=method)
        if not np.allclose([r[key] if r[key] is not None else reference[i] for i,r in enumerate(results)],reference,rtol=1e-12):raise ValueError('FDR cross-check failed')
    if sha(Path(archive).read_bytes())!=sha(raw):raise ValueError('Source changed during run')
    out=Path(directory)
    if out.exists():raise FileExistsError('Output must be a new directory')
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent,prefix='.mice-stage-') as tmp:
        stage=Path(tmp);(stage/MEMBER).write_bytes(source)
        write_csv(stage/'contrasts.csv',results)
        summaries=[]
        for i,m in enumerate(mice):
            for j,p in enumerate(proteins):
                summaries.append(dict(mouse=m,group=labels[i],protein=p,value=None if np.isnan(matrix[i,j]) else float(matrix[i,j]),
                                      available=int(available[i,j]),source_rows=';'.join(str(r['source_row']) for r in grouped[m])))
        write_csv(stage/'mouse_summaries.csv',summaries)
        write_csv(stage/'source_values.csv',records)
        render(stage,mice,labels,proteins,matrix,available,results,coords,explained)
        report['output_sha256']={p.name:sha(p.read_bytes()) for p in sorted(stage.iterdir())}
        report['script_sha256']=sha(Path(__file__).read_bytes())
        report['plan_sha256']=sha(Path(__file__).with_name('example_biology_plan.json').read_bytes())
        (stage/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        stage.rename(out)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True);source.add_argument('--archive');source.add_argument('--download',action='store_true')
    parser.add_argument('--directory',required=True);args=parser.parse_args()
    if Path(args.directory).exists():parser.error('Output directory already exists')
    try:
        if args.download:
            with urllib.request.urlopen(URL,timeout=45) as response:
                raw=response.read(5_000_001)
            if len(raw)>5_000_000:raise ValueError('Download exceeds limit')
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'source.zip';p.write_bytes(raw);report=run(p,args.directory)
        else:report=run(args.archive,args.directory)
    except (ValueError,OSError,zipfile.BadZipFile) as exc:parser.exit(2,str(exc)+'\n')
    print(json.dumps({k:report[k] for k in ('status','biological_mice','proteins','missing_measurement_cells','tested','bh_significant','by_significant','aggregation_decision_changes')},indent=2))


if __name__=='__main__':main()
