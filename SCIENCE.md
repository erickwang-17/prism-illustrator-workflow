# General analysis and code-generated figures · v0.3

**English** | [简体中文](SCIENCE.zh-CN.md)

This module supports explicitly declared designs in long-form data, with study-specific groups, units and domains. It computes statistics and creates real Matplotlib vector objects. It does not present code plots as native Prism projects or infer experimental design from a table alone.

## From examples to your data

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[science]'
.venv/bin/python demo_science.py --directory local/demo
.venv/bin/figureflow inspect local/demo/manufacturing.csv
.venv/bin/figureflow analyze local/demo/manufacturing.json --output-dir local/my-first-run
```

Use a new output directory. The demo creates eight entirely synthetic cases, source tables, explicit configurations and outputs with fixed seeds, without reading experiments. Copy a suitable configuration into your task directory and review mappings, units, experimental-unit IDs, order, design and method. Changing a title alone does not adapt a study.

Base audits require only `pip install .`; analysis and complete tests require `[science]`. Installation may download build tools/dependencies.

## Supported methods

| design / method | Structure and minimum conditions | Results and figure |
|---|---|---|
| independent / welch_t | Exactly two groups, ≥2 independent units each; globally unique IDs | Two-sided Welch t, mean difference A−B, 95% CI, df, P; raw points and summary |
| paired / paired_t | Two conditions, ≥2 matching IDs; exactly one row per ID/condition | ID-matched two-sided paired t, mean difference, 95% CI, df, P; paired lines |
| independent / anova | ≥2 groups, ≥2 units each; review independence, normal errors and equal variance | Ordinary one-way omnibus F/P; optional explicit Welch contrasts with Holm correction |
| independent / kruskal | ≥2 groups, ≥5 independent units each | Omnibus Kruskal–Wallis H/P; no automatic pairwise conclusions/brackets |
| independent / descriptive | ≥2 groups, ≥2 units each | Raw observations, mean/SD/median/quartiles; no P |
| correlation / pearson | ≥4 independent pairs; nonconstant x/y | Pearson r, two-sided P, Fisher-transformed 95% CI; scatter plot |
| correlation / spearman_permutation | ≥4 independent pairs; nonconstant x/y; exchangeability for permutation | Spearman rho, two-sided permutation P, up to 9,999 requested resamples, seed=0, exhaustive for small samples; no CI |
| contingency / fisher_exact | Complete 2×2 actual-count table, nonnegative integers, nonzero row/column margins | Two-sided Fisher P, sample odds ratio; count bars; no OR CI |
| time_series / descriptive | Unique numeric times or YYYY-MM-DD dates, explicit time type | Chronologically sorted line; no trend test, across-time P or causal inference |

ANOVA/Kruskal omnibus P values are upper-tail tests, not pairwise P values. t, correlation and Fisher tests are two-sided. Separate configuration files are not automatically corrected together; declare and handle their shared comparison family separately when applicable.

Optional ANOVA contrasts explicitly use Welch, not Tukey/Dunnett, and are not selected based on omnibus significance. Holm includes every configured contrast, including ns. Both raw and adjusted P are retained. Pairwise 95% CIs are unadjusted, not simultaneous intervals. Adding Welch contrasts does not repair invalid omnibus ANOVA assumptions.

Pearson P/CI require model assumptions; a normality test does not automatically select the model. Kruskal tests rank distributions and is not simply a median test without additional shape assumptions. Counts reflect analyzed records/pairs, but unique IDs cannot prove biological independence.

## Configuration contract

```json
{
  "schema_version": 1,
  "source": {"path": "measurements.csv"},
  "design": "independent",
  "method": "welch_t",
  "columns": {"id": "part_serial", "group": "process", "value": "diameter_mm"},
  "group_order": ["Lathe A", "Lathe B"],
  "missing": "error",
  "design_confirmed": true,
  "assumptions": "Different parts are independent units; review normal-error assumptions for this small-sample comparison.",
  "title": "Manufacturing tolerances",
  "x_label": "Process",
  "y_label": "Diameter",
  "unit": "mm",
  "style": {"font": "DejaVu Sans", "width": 7, "height": 5, "summary": "mean_sd", "show_significance": true}
}
```

- Unknown keys, duplicate JSON keys, misspelled methods and unconfirmed designs fail; no fallback test is chosen.
- `source.path` is relative to the configuration. CSV/TSV use UTF-8 with optional BOM. Multiple-sheet XLSX requires `source.sheet`. Formula cells are rejected to avoid stale cached values. Headers must be unique, nonempty text.
- `columns` maps source names to distinct, complete roles: groups use `id/group/value`, correlation/time use `id/x/y`, contingency uses `row/column/count`. No implicit renaming, unit conversion, reshape or technical-replicate aggregation occurs.
- `group_order` must exactly cover observed groups. Omitting a group cannot filter it. Independent IDs are globally unique; paired IDs repeat only across conditions. Equal values are retained.
- Explicit `missing=error` is the default policy. `drop` removes only rows with blank mapped fields and records original rows/reasons. No imputation, outlier removal or silent deletion of incomplete pairs occurs; incomplete pairing fails. Blank strings/Excel cells are missing; `NA`, `NaN`, infinity and comma-formatted numbers are not silently converted.
- Contingency requires `count_basis=observed_counts`, nonnegative integer counts below 2^53. The numbers 50/50 alone cannot establish counts versus percentages or total n; operators verify provenance.
- Time series require `time_kind=numeric` or `iso_date`; intraday, duplicate or non-ISO date coordinates are rejected.
- ANOVA contrasts require `contrasts=[{"a":"Baseline","b":"Drip"}, ...]`, `pairwise_method=welch_t`, `correction=holm`. Duplicate/reversed pairs fail.
- `style` supports `font/palette/width/height/summary/show_significance`. Dimensions: 3–20 inches; summary: mean_sd or median_iqr. Defaults: 7×5, DejaVu Sans. Colors must be opaque, distinct and cover all groups. The default palette covers up to seven; supply a larger palette explicitly when needed. Unavailable fonts or missing glyphs fail rather than silently substituting.

A knowledgeable data owner must confirm IDs, units and design. `design_confirmed=true` records an assertion, not software certification. Do not blindly copy synthetic assumptions.

## Outputs and provenance

Each run creates a fresh directory:

- `analysis.json`: method, declared assumptions, statistics, available effects/CI, group n, P/adjusted P, missing rows, warnings, source/configuration hashes, dependency versions and output hashes.
- `normalized.csv`: analyzed role columns, numeric values and source row numbers. Floating-point representation does not replace original data or exact Decimal auditing.
- `config.json`: reviewed snapshot with the source reduced to a basename to avoid local-path disclosure. It is not a self-contained reproducibility package; retain original sources/configuration and hashes.
- `figure.svg`, `figure.pdf`, `figure.png`: vectors and 180 dpi preview. SVG retains text and requires recipient fonts; Matplotlib handles PDF font embedding.

Sources are never overwritten. Input hashes are checked before/after reading and before publication. Calculation/rendering complete in temporary staging before publishing to a nonexistent directory. Publication I/O failures attempt an `INCOMPLETE` marker; hard termination or disk failure still requires integrity checks. The report excludes its own hash; save final evidence with `hash/verify` separately.

All scatter observations remain visible as objects; error bars are above points. Seed=0 jitter changes positions, not values. Brackets represent explicit calculated contrasts; stars are 10 pt. Two-group tests receive no additional multiplicity correction. ns does not prove equivalence. Automatic limits include data/error bars, and visible text is checked against canvas edges. Text overlap, legends covering data and interpretation still need visual review.

`status=pass` means supported calculation/export completed. Reports explicitly state `native_prism=false`, `visual_review_required=true`; neither assumptions nor publication readiness are guaranteed. `summary` aggregation is not complete workflow acceptance.

## Integrating with native production

1. `inspect`, confirm design/units/IDs/families, then choose a supported method. Unsupported analysis pauses that dependent step.
2. Review raw data, results and every preview after `analyze`. Reproducing an existing Prism analysis also requires comparing its parameters/results; module defaults must not replace the original method.
3. Native Prism follows [WORKFLOW.md](WORKFLOW.md). Code PDF/SVG may be placed in Illustrator with provenance/method/font information. There is no automatic .prism/.ai writing feature.
4. Measure actual axes/image edges for layout. Historical rows, letters, counts and legend gaps do not transfer to unrelated studies.
5. Use `lint --profile generic` or a custom profile; historical projects may use `uwm`. Complete preview review and `verify` evidence.

Not implemented: survival/Cox, multifactor/mixed-effects models, repeated measures beyond two conditions, nesting, complex survey weights, omics multiplicity, spatial data, automatic image segmentation, arbitrary formats or automatic best-chart selection. Extensions require independent design, numerical benchmarks and visual tests.

## Synthetic tests

| Domain | Coverage |
|---|---|
| Manufacturing | Unequal n/variance; manually checked Welch statistic/df |
| Sensor calibration | Negative values, shuffled rows; pairing by ID |
| Agriculture | XLSX, ANOVA, two prespecified contrasts and Holm family |
| Website conversion | Actual 2×2 counts; hypergeometric enumeration for Fisher P |
| Nonlinear materials | U-shaped response with small Pearson r; demonstrates model inadequacy rather than absence of a relationship |
| Service rankings | Small-sample Spearman; exhaustive 4! two-sided probability check |
| Daily energy | TSV, dates, sorting; explicitly descriptive |
| Logistics | Skewed data, omnibus Kruskal, median/IQR |

Additional checks cover missingness logs, degeneracy, duplicate IDs, formulas, percentage declarations, invalid numbers, changed inputs, output overwrite, fonts/glyphs, text clipping, palettes and generic styling.

Official implementation references: [Welch t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html), [paired t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html), [ANOVA](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html), [Kruskal](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html), [Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html), [Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html), [Fisher](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html), [Matplotlib export](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html), [openpyxl](https://openpyxl.readthedocs.io/en/stable/tutorial.html).
