# Improvement log: real biological example

**English** | [简体中文](IMPROVEMENTS.zh-CN.md)

This is an execution log, not a list of claimed universal capabilities. Entries are added as evidence is examined. 2026-11-16.

| Stage | Finding | Response / evidence | State |
|---|---|---|---|
| Scope | User requested biology after initial transport-data exploration | Discard transport example from deliverables; select UCI mouse cortex RPPA | Done |
| Provenance | Examples lacked a real public source and reuse terms | Pin archive/member hashes; cite UCI DOI and CC BY 4.0; explicit download, no private research files | Done |
| Design | 1,080 rows represent 72 mice, with 15 technical/dilution measurements each | Parse mouse identity and validate complete repeat IDs; inference at mouse level | Done |
| Documentation | UCI describes rows as independent; primary article describes within-mouse repeats | Follow biological unit from methods; document conflict, do not count 1,080 animals | Done |
| Reproduction | Original work used SOM, class imputation/outlier exclusion and discussed hierarchical modeling | Label this an exploratory reanalysis; explicitly list changed methods; no false reproduction claim | Done |
| Missingness | Protein availability may differ by mouse | Audit missingness before aggregation; no group-mean imputation for tests; endpoint-specific n | Done |
| Multiplicity | A large protein panel needs a declared comparison family | Freeze two contrasts × 77 proteins; BH plus BY sensitivity, including unavailable slots | Done |
| Visualization | Simple scatter examples omit experiment structure and QC | Build overview, missingness, PCA, volcano and four prespecified protein panels | Done |
| Scientific scope | Dilution hierarchy, litter and batch can matter | Median/mean sensitivity; mixed-effects and metadata recovery remain follow-up work | Open |
| Source validation | A provided RRP1_N value is negative; a nonnegative validator incorrectly rejected it | Preserve the finite source value, flag it; do not invent a background-correction explanation or change to zero | Fixed |
| First analysis | 19 nominal P < 0.05 results disappear after the declared 154-test correction | Publish all results: both contrasts have 0 BH/BY discoveries; no threshold or exclusion changed | Done |
| PCA missingness | Filling from class averages would leak labels into an unsupervised view | Use 69 fully observed proteins and all 72 mice; no PCA imputation | Done |
| Numerical verification | Custom result tables need independent numerical checks | Cross-check every Welch t/df/P/CI and full BH/BY vectors against SciPy; eight synthetic failure tests added | Done |
| Visual verification | Need one-mouse-per-dot n, unambiguous SD vs CI, readable QC indices | Inspect final eight-panel PNG; source-order indices changed to 1-based labels; vector PDF/SVG retained | Done |
| Scope clarity | Generic XLS/omics support could be overstated by a successful special case | Separate fixed case adapter from generic CLI; retain synthetic fixtures and explicit unsupported methods | Done |
| Coverage sensitivity | The 8/15 technical-coverage cutoff is a design choice | Threshold sensitivity, dilution-aware modeling and mouse-level robust/permutation analysis require further independent validation | Open |
| Packaging | Real case depends on public source availability | Explicit bounded download, checksum pin and offline ZIP path; no live download in CI | Done |
