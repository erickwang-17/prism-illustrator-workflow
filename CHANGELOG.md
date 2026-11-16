# Changelog

**English** | [简体中文](CHANGELOG.zh-CN.md)

## 0.5.0 — 2026-11-16

- Replace the main synthetic example with a licensed public mouse-protein case, pinned download, biological-unit/QC audit, 154 planned tests, BH/BY correction, aggregation sensitivity and eight-panel vector output.
- Publish all comparison results and provenance; retain nonsignificant findings and original values.
- Add bilingual case documentation and a running improvement log; retain small synthetic regression fixtures.
- Add eight offline synthetic tests and xlrd to the science extra for the case-specific original XLS reader. Generic analyze designs remain unchanged.

## 0.4.1 — 2026-11-16

- Add complete English and Simplified Chinese documentation with language links, including task/agent guidance and all 81 checklist requirements.
- Preserve shared commands, schemas, rule IDs and statistical behavior; checklist evidence states remain unresolved in both languages.
- Use an English automatic API troubleshooting prompt; manual questions may use either language.

## 0.4.0 — 2026-11-16

- Add optional API setup, local checks, request previews and explicit single-call advice; recommend setup while preserving offline use.
- Support Responses and Chat Completions text protocols, configurable endpoints/models and two chat token parameters.
- `analyze --ai-help` sends only a fixed failure category; advice and original errors remain separate and failure exits are preserved.
- Read keys only from environment variables; bound input/output/body sizes and I/O timeouts; reject redirects and automatic retries.
- Never execute model output, silently modify data/tests or treat advice as acceptance.
- Add offline contract/error/leak-protection tests; verify real credentials, model permissions and billing separately after configuration.

## 0.3.0 — 2026-11-16

- Add inspect/analyze for explicit CSV/TSV/XLSX mappings and designs.
- Add Welch, paired t, ordinary ANOVA, Kruskal, Pearson, Spearman permutation, Fisher and descriptive series.
- Explicit contrasts use Welch + Holm; record n, supported effects/CI, missingness, warnings and hashes.
- Generate real SVG/PDF/PNG with raw points, error bars above points, explicit brackets and canvas text checks.
- Add generic/custom profiles; uwm remains the legacy lint default without imposing its style on general analysis.
- Add eight unrelated synthetic domains, independent numerical benchmarks and invalid-input/provenance/rendering checks.
- Keep standard-library audits independent; full analysis/tests require `[science]`.
- No native Prism/Illustrator automatic writing or universal data/design support.

## 0.2.0 — 2026-11-16

- Add ten numbered format rules, strict manifests and rules/lint/summary commands.
- Add version, installed CLI, versioned JSON reports and optional JSON runtime errors.
- Reject duplicate JSON keys and ambiguous option abbreviations.
- Add agent skill, task template, rules/references and optional pre-commit hook.
- Add historical regression cases; CI tests all cases and installed commands.
- Preserve the original six subcommands without changing statistical models/native files.

Compatibility: reports gained fields; duplicate JSON keys and abbreviated options are now explicitly rejected. Old reports lacking report_version cannot enter summary. Rerun original inputs instead of fabricating a version field.

## 0.1.0 — 2026-11-16

Initial data audits, significance plans, layout checks, evidence verification, export scripts and 81-item workflow.
