# Validation record

**English** | [简体中文](VALIDATION.zh-CN.md)

## v0.5 · Public biological case

Local Python 3.13: 103 tests passed. Eight new tests use synthetic data only. The real-data run audited 1,080 records/72 mice/77 proteins, 1,396 missing measurements and one negative value, preserving the source workbook hash. All 154 Welch results/CI and BH/BY vectors were cross-checked against SciPy. The eight-panel PNG was visually reviewed. The pinned dataset was downloaded explicitly outside CI. See [case](EXAMPLE_BIOLOGY.md) and [remaining improvements](IMPROVEMENTS.md); no source-paper replication, native-app edit or universally valid biological inference is claimed.

## v0.4.1 · Bilingual documentation

On 2026-11-16, local Python 3.13 passed all 95 tests after localization. Eleven English/Chinese document pairs have valid local links; both 81-item workflows and checklist IDs/non-description fields match. Both checklists retain unresolved initial states. These are documentation/compatibility checks, not new scientific or live-API acceptance.

## v0.4 · Optional API assistance

On 2026-11-16, local Python 3.13 passed 95 tests, including 21 new API cases. Configuration creation, request preparation and preview-only ai-ask were exercised; scientific regressions remained passing.

API tests use synthetic keys and mocked transport. Coverage includes both protocols, headers/timeouts/body limits, 401/429/network failures, no retries, redirect rejection, configuration/request mismatch, key substitution, refusals/tool calls/truncation and preservation of original analysis failures. Tests and CI do not call paid services.

No live service acceptance has been performed with user API credentials. ai-doctor is local only. Follow [AI_API.md](AI_API.md), set a key and send one synthetic question to verify your endpoint, model permissions and quota separately. Advice does not mean resolution.

## v0.3 · Scientific computing and figures

Local review date: 2026-11-16. This records performed checks, not guarantees about all data or assumptions.

- Python 3.13: 74 tests passed with `python -m unittest discover -v`.
- Eight complete synthetic workflows produced SVG/PDF/PNG, result JSON and normalized tables with source rows; source hashes remained unchanged.
- Independent Welch t/df calculations, hypergeometric Fisher enumeration, exhaustive small-sample Spearman and known Holm results passed.
- Website example [[6,2],[1,4]]: two-sided Fisher P=0.10256410256410256, sample odds ratio=12.
- Shuffled pairs matched by ID; equal values retained. Unconfirmed designs, duplicate IDs, missing pairs, formula cells, nonfinite values, fractional counts and changing inputs were rejected.
- Every figure preview was reviewed for raw points, error bars, limits, titles, n, brackets and dates. Long-text clipping, missing glyphs/fonts and transparent/duplicate colors have failure tests.
- Installed figureflow 0.3.0 exercised inspect/analyze; SKILL.md validation passed.
- That scientific environment used NumPy 2.5.5, SciPy 1.18.1, Matplotlib 3.11.2, openpyxl 3.1.5. Each run records its own versions.

[Eight-case gallery](demo-gallery.png). Regenerate with `python demo_science.py --directory local/demo` after installing `.[science]`. Platform/dependency changes may affect numerics or font layout slightly; identical PNG bytes are not the scientific acceptance criterion.

Remote [GitHub Actions](https://github.com/erickwang-17/prism-illustrator-workflow/actions/workflows/ci.yml) separately checks Python 3.10/3.13, tests, eight demos and installed commands. Inspect the actual run for the relevant commit; local success does not imply remote success.

Proprietary Prism/Illustrator host automation is not validated in CI. Unsupported survival/mixed-effects/advanced models have no implemented inference. See [SCIENCE.md](SCIENCE.md).
