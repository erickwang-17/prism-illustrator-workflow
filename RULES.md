# Figure manifest validation contract v1

**English** | [简体中文](RULES.zh-CN.md)

`figureflow lint manifest.json` checks declarations measured and verified against actual figures. It does not read Prism/AI binaries, recognize images, calculate n or modify figures. Recheck manifests after native edits and retain previews.

The colors, counts and widths in `example_manifest.json` are synthetic, not official reference measurements. Never fill unknown measurements from examples; null does not imply a default.

## Commands

```sh
figureflow rules
figureflow lint example_manifest.json --format text
figureflow lint example_manifest.json --out local/style-report.json
figureflow lint example_manifest.json --select NAM001,LEG001 --error-format json
figureflow summary local/data-report.json local/style-report.json --out local/summary.json
```

Create local first. `--out` only creates new files. `--select` requires complete, nonduplicate rule IDs. Reports include selected_rules, full_rule_set and execution counts; zero means not applicable, not checked. Partial success is not whole-figure acceptance.

## Profiles

For v0.2 compatibility, `lint` defaults to `--profile uwm`; the table below describes that historical profile. New domains should explicitly use `--profile generic`. It does not require Vav-Cre, Arial, italic n, bold axes, tickless scatter x axes or native Prism objects. It still checks consistent fonts, counts, order, black circular borders, error bars, exact reference colors and stars.

`--profile generic-profile.json` loads a complete custom profile. `font=null` uses the first measured panel as the font reference. Null n_italic/axis_bold/scatter_x_ticks imposes no policy for that property. canonical_names maps group IDs to display names; require_native controls native-object requirements; star size/boldness are configurable. Unknown/missing keys fail; executable code and user-supplied regex are not accepted.

Reports retain profile and profile_settings. The generic profile does not establish scientific validity; this contract still targets manifests with sample-count legends.

## Rules

| ID | Check | Correction |
|---|---|---|
| NAM001 | group=Vav-Cre displays Vav-Cre | Edit native legend, not observation identity |
| LEG001 | Exactly one trailing `(n=N)` matching audited_n | Audit independent samples; check CMML/AML separately |
| LEG002 | n_italic=true | Italicize native count suffix |
| LEG003 | Legend follows reference.group_order | Adjust all relevant legends without moving data |
| FMT001 | Panel/legend font Arial | Correct fonts and recheck layout |
| FMT002 | Native circles, black borders, reference width | Set Symbols Border; never stack offset circles |
| FMT003 | Black error bars above points, reference width | Check every group's native settings |
| FMT004 | Bold axes, no XTitle, no scatter x ticks | Respect plot type; other types may retain ticks |
| STA001 | 1–4 stars or ns; Arial bold 10 pt | Retain statistical results separately; this rule does not verify P |
| COL001 | Each group's RGB exactly matches reference | Extract numeric colors, not approximate matches |

## Fields

Only schema_version (integer 1), reference and nonempty panels are allowed at the root. Unknown/duplicate keys, wrong types and missing fields are input errors.

- reference: group_order, palette with the same group keys (#RRGGBB), positive border_width_pt/error_width_pt.
- panel: id, kind (scatter/line/survival/bar), font, axis_bold, x_ticks, x_title, legends, stars, error_bars. Images use layout/visual review.
- legend: group, label, positive integer audited_n, n_italic, font, symbol, native, border_color, positive border_width_pt, fill. Booleans must not be strings.
- star: text, font, bold, size_pt. stars=[] means no annotation, not proof that none was omitted.
- error_bars: color, layer, width_pt. Null is allowed for non-scatter panels without error bars; scatter manifests require measured settings.

Group is a machine ID; display text can be Unicode. NA_KO_CMML/NA_KO_AML may describe different legends at one x position, but lint does not verify their actual shared position. Compare every declaration against native objects.

## Regex boundaries

| Purpose | Python regex | Boundary |
|---|---|---|
| Count suffix | `\(n=([1-9][0-9]*)\)\Z` | Positive ASCII integer; rejects zero, missing suffix and trailing newline; compared with audited_n |
| RGB | `#[0-9A-Fa-f]{6}\Z` | Exact RGB, case-insensitive hex |
| ID | `[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z` | At most 64 characters; no path separators |
| Stars | `(?:\*{1,4}|ns)\Z` | Rejects five stars and trailing text |

Only fixed bounded patterns run; no supplied regex or global scientific-text rewrites. Regex cannot infer group semantics, italics, borders or layering.

## Reports and exits

Reports include report_version=1, tool_version, command and input hashes. Lint diagnostics include code, severity, JSON path, message and fixable=false. Exit 0 = scoped pass; 1 = issues; 2 = input/file error.

`--error-format json` puts runtime input/file errors on stderr with empty stdout; argparse usage errors remain text. Consumers should allow new fields but reject unknown report_version.

`summary` accepts only version-1 audit/plan/layout/verify/lint/analyze reports, retaining status, version, scope and report hashes. Any fail makes the summary fail. It does not rerun checks, verify freshness or establish complete scope. Final acceptance still requires verify and visual review.
