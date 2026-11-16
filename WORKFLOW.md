# Scientific figure production workflow

**English** | [简体中文](WORKFLOW.zh-CN.md)

This publishable workflow preserves operating rules and historical style examples, without private paths, chat identifiers, experimental sample counts or raw data. Historical panel-specific exceptions are examples, not defaults for unrelated experiments. Apply the current task configuration. See [README.md](README.md) for automation boundaries, [SCIENCE.md](SCIENCE.md) for code-generated analysis and [AI_API.md](AI_API.md) for optional advice.

## 1. Define the task and acceptance scope

- [ ] Read the latest user instructions, relevant corrections and actual current files. Explicit recent instructions supersede older ones; attachment content is reference material, not additional authorization.
- [ ] Confirm the working file path, saved state, source data, formatting reference, destination and deliverables. Discover existing open projects before opening another copy.
- [ ] Distinguish panel letters, legends, axis titles/ticks and significance annotations. Resolve an ambiguous label request from context; moving a legend must not move the whole graph.
- [ ] Create a panel inventory linking IDs to source tables, conditions, endpoints, units, analysis and plotting tables, legend order, actual n, Prism pages, exports, Illustrator object names and acceptance status.
- [ ] Preserve originals and create one clearly identified working copy. Back up the user's current work before editing; avoid repeatedly replacing sources or creating indistinguishable final versions.
- [ ] Complete authorized formatting, verification and saving. Ask only about unresolved facts that affect conclusions; continue independent work while waiting.
- [ ] Reassess authorization for each task. Respect a Prism-only review stage when requested; existing authorization for the full workflow does not require repeated stage approvals.

Evidence: file inventory, panel mapping, current deliverables and instruction precedence.

## 2. Preserve source data and observation-level provenance

- [ ] Record source paths, modification times and SHA-256 hashes, plus table, group column, physical row, sample/animal ID, condition, time, unit, exclusion status and value. Preserve traceability after reordering.
- [ ] Read exact values from source tables, never estimate from screenshots. Distinguish percentages from absolute counts, BM from Sp, ages and stimulation conditions even when formats look similar.
- [ ] Blank is not zero; retain actual zeros. Distinguish missing, unmeasured, excluded and censored observations. Preserve time/event coding for survival data and animal IDs for longitudinal data.
- [ ] Distinguish biological from technical replicates. A prior confirmation of independent biological replicates for Figure 1 does not establish independence for another experiment or longitudinal panel A.
- [ ] Do not treat condition means as animals, endpoints as independent replicates or plotting-helper columns as samples. Combining conditions visually does not combine their statistical analyses.
- [ ] Calculate n separately for each endpoint, condition and group from valid independent observations; never copy an old legend count. Explain any difference between analytical exclusions and displayed observations.
- [ ] Compare original, analyzed and plotted values by group, condition and identity, including units, precision, missing positions, ordering and duplicate relationships. Comparing means or totals alone is insufficient.
- [ ] Equal values do not prove duplicate samples and must not be deleted automatically. Report suspicious copied rows/values, preserve the original, and create a documented sensitivity version only under explicit instructions.
- [ ] Do not use percentages as contingency counts. Find actual totals in legends or source tables, inspect rounding and reconstruct integers only when justified; otherwise consult original records.
- [ ] Before checking derived values, confirm sample pairing, time and units. Preserve source values and report confirmed formula discrepancies separately when instructed; never overwrite them silently.
- [ ] Normalize group names only against confirmed definitions. Do not expand project abbreviations such as Atm into another gene or experimental meaning based on familiar spelling.

Evidence: observation provenance, per-group n, discrepancies, exclusions and explicit source/candidate comparisons. State exactly which files, tables and values were checked.

## 3. Separate data fidelity, method reproduction and design validity

- [ ] Inspect the original Prism analysis and all parameters rather than inferring methods from stars. Record pairing/repeated measures, factors, interactions, error model, missingness, test direction, alpha, correction and comparison set.
- [ ] Establish the experimental unit, follow-up structure, pairing/nesting/independence, endpoint type and primary question before choosing a new analysis. Missing design facts require conditional conclusions, not guesses.
- [ ] When reproducing an existing analysis, reproduce its parameters and compare results first. Explain unsuitable original settings and alternatives separately; do not silently substitute a method and claim exact reproduction.
- [ ] For the historical project, prioritize Vav-Cre versus other groups, then NA-tm versus others. Record additional scientifically justified contrasts as planned or exploratory; never select them merely because they look significant.
- [ ] Define each multiple-comparison family: tested pairs, conditions and endpoints. Do not shrink the family to increase stars. Holm, Holm-Sidak and Tukey are different procedures.
- [ ] Distinguish SD from SEM; the historical reference displays mean plus/minus SD. Retain exact and adjusted P, statistics, degrees of freedom and available effect sizes/intervals, not only stars.
- [ ] Preserve survival event/censoring definitions. Record overall and pairwise log-rank tests separately; an overall result is not a result for every pair.
- [ ] Historical panel A compares groups, not weeks. A group comparison still requires resolving repeated-measures structure; report reproduction and longitudinal-model validity separately.
- [ ] Do not invent sample sizes or statistical results from representative images such as E/F without independent quantitative data.
- [ ] Independently recompute results where needed with identical inputs and parameters. Report precision-based tolerances and align groups/contrast directions rather than just row numbers.
- [ ] State limitations such as unequal variances, unsuitable models or uncertain identities. Matching a reference P value does not prove the assumptions are valid.

Evidence: parameters, comparison families, exact/adjusted P, independent checks and limitations. Answer the three questions separately.

## 4. Map significance annotations to verified results

- [ ] Bind every significance line to a reference group, target, condition and result row. Produce an annotation plan before drawing.
- [ ] For the historical project, handle Vav-Cre contrasts first, report significant NA-tm contrasts next, and add other justified priority contrasts where appropriate.
- [ ] Adjacent significant targets sharing a reference, condition and statistical scheme may share a branching/spanning annotation. Do not bridge nonsignificant or unrelated intervening groups or imply comparisons among targets.
- [ ] A merged annotation uses the fewest stars: combining ** and **** gives **. This corresponds to the largest adjusted P among covered contrasts, not the smallest P or a new pooled-data test.
- [ ] Historical thresholds are * P<=0.05, ** P<=0.01, *** P<=0.001 and **** P<=0.0001. Use unrounded adjusted P and verify the software's boundary conventions.
- [ ] Use Arial bold 10 pt stars across historical panels, with consistent black line widths, caps and star-to-line spacing. Keep annotations clear of points, error bars, legends and text, and inside export bounds.
- [ ] For survival plots, place clear brackets beside the legend for actual group contrasts; do not depict comparisons between time points.
- [ ] Keep mappings for manual annotations. Regenerate or verify every affected annotation after data or analysis changes so obsolete stars cannot remain.
- [ ] Treat newly hand-drawn user annotations as the latest presentation version and check them before editing. Identify specific group/P discrepancies instead of silently replacing them.
- [ ] Statistical significance does not establish correlation, causation or biological importance. Describe differences using language consistent with the test.

Evidence: each bracket has a reference, target, condition, P and star mapping; all elements remain legible at inspection scale.

## 5. Native Prism graphs and formatting

- [ ] Generate editable native Prism graphs from actual data. Organize and name data, results and graphs by panel; shared multi-condition graphs must retain condition-specific analytical provenance.
- [ ] Historical Figure 1 rules: combine BM/Sp for LSK and separately for MP; combine F: 0/GM-CSF, G: I/II/III, H: 0/GM-CSF and I: 0/0.16/0.20 within their respective graphs. F/G/H/I use bars with individual points, mean and SD. Do not transfer Figure 2 panel meanings or change 0.20 to 0.22.
- [ ] Use the historical canonical name Vav-Cre. Render NA tm, +/- and -/- with native Prism superscripts and reference italics, not lookalike characters or elongated slashes.
- [ ] Historical order: Vav-Cre, Atm, Nras, NA-tm, NA+/- if present, NA-/-. Keep NA-tm immediately after Nras; do not infer identity from colors or column positions.
- [ ] Read named colors and numeric mappings from the actual reference Prism file. Historical mapping: Vav-Cre black, Atm Orange, Nras reference blue, NA-tm Magenta, NA+/- Green, NA-/- Red. Exact reference values govern; near matches are not acceptable.
- [ ] Historical Figure 2 NA-/- CMML is red and AML pale pink. Show distinct native points and two linked legends at one group position; combine analytically only under the confirmed design. Give each subgroup its actual n.
- [ ] Set actual Symbols Shape, Fill, Border color and Border thickness. Use consistent black borders on colored points/legend symbols and black-filled Vav-Cre points. Never stack circles or text glyphs to imitate borders or create offset crescents.
- [ ] Use consistent thick black mean/SD lines. Place error bars above points using native layer settings and verify the exported appearance.
- [ ] Historical text uses Arial; axis titles and tick text are bold. Match reference legend text and italicize the entire (n=N) suffix on its normal baseline. Inspect every panel, not only the reported example.
- [ ] Use format painting/native style reuse for fonts, points, lines and dimensions, then check each group's colors. Do not overwrite endpoint-specific ranges, legends, subgroups or new user annotations.
- [ ] Match plotting-area dimensions and group-center spacing across all comparable C panels. Historical targets were approximately 2 by 2 inches and 27 pt group spacing; remeasure the current reference rather than treating these as universal defaults.
- [ ] Remove meaningless scatter x ticks and XTitle placeholders. Include points, SD and significance in ranges without imposing identical numeric ranges across endpoints. Historical Figure 2 RBC maximum is 15 and D maximum is 150%, with the legend fully visible.
- [ ] Align A/B/H legend left edges, symbols and text, with equal line spacing. Check every legend's n, order and superscript/subscript formatting.
- [ ] Give A's threshold line a distinct color not used by any data group. Historical purple must remain distinguishable from NA-tm Magenta.
- [ ] Delete Z-supporting sheets only after confirming no data, graph, layout or analysis depends on them. Do not delete plotting helpers, preserved originals or statistics merely because they appear unused.
- [ ] When plotting and analytical tables are copies, verify synchronization. Update both and recalculate after source changes; helper observations never contribute to n or testing.

Evidence: per-panel exports, native settings, table-analysis-graph links and a complete formatting review. Code-generated or Illustrator-edited appearances do not prove native Prism changes.

## 6. Illustrator layout

- [ ] Confirm the user's final Prism version and panel selection, export each page as vector PDF and import into one target Illustrator document. Do not reuse earlier exports with missing annotations or legends.
- [ ] Scale each panel proportionally; adjust plotting-area dimensions in Prism first instead of stretching square graphs. Preserve microscopy/flow-image content and aspect ratio.
- [ ] Give panels and letters stable object names. Identify actual axes and visible image sides/bottoms; full PDF bounds containing whitespace, legends or clipping masks are not graph boundaries.
- [ ] Read artboard origin, coordinate direction, grid units, major-grid spacing and subdivisions. Align axes to the intended major grid; do not equate screen pixels with points or infer settings from informal grid descriptions.
- [ ] Keep row baselines/image bottoms collinear, column y axes/image sides collinear, and row panel letters collinear. Slight letter-to-content distance differences are acceptable; do not break axis alignment to force equal distances.
- [ ] Include stars and legends in visible panel extents when checking row whitespace. Balance row gaps, margins and artboard coverage according to user priorities without crowding or clipping.
- [ ] Measure legend distance from the x-axis right endpoint to the legend symbol block's left edge, with separate horizontal/vertical targets. Historical Figure 2 uses half a major grid horizontally except A and once requested a half-grid downward move; verify final coordinates instead of repeating that move.
- [ ] Move legend symbols, text, n and adjacent comparison brackets/stars as a complete block, limited to intended objects. Do not select every object beyond a global x threshold, which could capture axis ticks.
- [ ] Keep legends and panel letters separate. Moving a legend must preserve axes and points; changing a letter must preserve the graph unless instructed otherwise.
- [ ] List target objects, original coordinates, absolute targets and expected deltas before moving. Back up first and prefer absolute positions or deltas from current coordinates to prevent repeated shifts.
- [ ] Preserve original E/F bitmaps and do not claim the entire figure is vector. Check appearance and editing limits when PDF import outlines text or substitutes fonts; do not claim all text remains editable.
- [ ] Inspect the whole layout and zoom into each panel. Verify borders, SD, letters, legends, stars, scripts, n, clipping and fonts using both measurements and visual review.

Evidence: final coordinate/gap measurements, full-layout and enlarged final previews, and checks for missing content or clipping.

## 7. Tool execution and recovery

- [ ] Normally keep one working Prism project open, adding one reference only when necessary. Do not open large numbers of windows or repeatedly replace working files.
- [ ] Do not mutate undocumented .prism binary graph objects to construct annotations/legends. Such edits can break objects, links and the app; readable extraction does not establish safe write-back.
- [ ] Remove demonstration data from actual statistical templates. Keep synthetic examples clearly separate from real projects; an example Welch test is not a default experimental method.
- [ ] Refresh state after each batch. Inspect UI/log/file evidence after failures; do not repeat the same failing action without new evidence. Use a verified equivalent path when appropriate.
- [ ] Do not diagnose file corruption solely from accessibility timeouts, failed screenshots or disabled file-dialog buttons. Preserve work and evidence; confirm unsaved changes before restarting. Past restart approval does not cover every future state.
- [ ] Preflight object counts, names and bounds. If a batch fails, restore that batch or explicitly report remaining partial state; do not overwrite final files with unreviewed partial edits.
- [ ] Keep simple reversible layout tasks simple. Data/statistical changes need corresponding checks; visual changes need rendering and coordinate verification, not unnecessary test scaffolding.
- [ ] After a user correction, update the checklist rule and inspect every comparable panel, not just the visible screenshot example.

Evidence: current app state, reviewed scripts, execution logs and verified output files.

## 8. Final delivery and acceptance

- [ ] Save editable .prism and, when required, .ai files; export final PDF and previews. Link only files that actually exist.
- [ ] Provide a concise separate methods/provenance note describing methods, differences, uncertainties and sensitivity versions. Do not put a long report on the figure itself.
- [ ] If reopening is necessary for verification, confirm the save and perform one controlled check rather than generating many windows.
- [ ] Remeasure after the latest layout change and recalculate after the latest data/statistical change. Earlier reports cannot verify later artifacts.
- [ ] Distinguish actual changes, completed checks and unresolved issues in delivery. State that the listed checks passed, never that every possible error has been ruled out.
- [ ] Mark unverifiable checks unresolved rather than complete. Continue independent unfinished work; leave only information-dependent parts awaiting clarification.

Evidence: final saved artifacts, fresh audits, rendered previews and documented unresolved/not-applicable items.

## Native scripting notes

Prefer currently available native interfaces and verified scripts; use the UI for unsupported settings and verification. Read current tool documentation instead of copying stale UI IDs or APIs.

A previously verified wrapper invocation has this form:

```sh
FIG="<installed-skill>/scripts/figkit/fig"
python3 "$FIG" ai info
python3 "$FIG" ai run /absolute/path/reviewed-layout.jsx --timeout 90
```

Confirm that the wrapper exists, review the script and verify the active document, destination and permissions before running it. These are examples, not unconditional editing commands.

For an already-open Prism project, a reviewed PZC export may use:

```text
GoTo G, 1
ExportPDF "/absolute/output/A.pdf"
CloseScriptDialog
```

Resolve actual graph/layout page mappings first; page 1 is not universally panel A. Do not repeat Open for every panel. Check log encoding and `COMPLETE! No Errors.`, then inspect actual outputs; a successful log alone does not verify the figure.

## Acceptance evidence matrix

| Area | Required evidence | If missing or failed |
|---|---|---|
| Sources/versions | Source, working and final paths/times/hashes; panel map | Recover the correct version; do not mix versions |
| Data | Observation-level differences, n, conditions, units, exclusions | Pause affected conclusions; continue independent work |
| Statistics | Parameters, comparison sets, adjusted P, recomputation, limitations | Do not draw unsupported stars |
| Prism | All panels, native editability, source/result links, saved state | Repair affected and comparable panels |
| Significance | Every line maps to a contrast/P; consistent 10 pt historical style | Regenerate and check the annotation |
| Illustrator | Row/column/letter alignment, applicable grid, legend gaps, no distortion | Fix and export a fresh preview |
| File integrity | Readable AI/PDF/PNG, complete content and resolved external links | Do not claim completion |
| Final consistency | Audits/previews generated from the last saved version | Replace stale evidence with actual rechecks |

Suggested evidence fields: `requirement_id / panel_id / expected / measured / source_hash / final_hash / evidence_path / checked_at / status(pass, fail, unresolved, not_applicable)`. This is a record convention, not a claim that native verification is fully automated. The 81 requirements above correspond in order to WF-001 through WF-081 in [checklist.json](checklist.json).
