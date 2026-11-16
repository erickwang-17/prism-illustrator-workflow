# Working in this repository

**English** | [简体中文](AGENTS.zh-CN.md)

This repository provides figure workflow documentation and local verification tools. It is not a native Prism/Illustrator replacement.

For a figure task, read README.md and WORKFLOW.md. General code-generated analysis also follows SCIENCE.md; use the optional [science] dependencies and preserve explicit design/method decisions. Apply the latest explicit user requirements before historical style examples. Keep raw data and native projects outside the tracked source tree, normally under ignored local/ or data/ directories.

Do not silently select or change a statistical test. Distinguish source-data fidelity, reproduction of an existing analysis, and experimental-design validity. The plan command consumes supplied adjusted P values; it does not perform statistical testing. Missing biological design information blocks dependent conclusions, not unrelated formatting work.

Use real native Prism points/borders/legends and Illustrator vector objects. Never fake native edits with screenshots or stacked circles. Avoid undocumented binary mutations and repeated opening/replacing of native projects. Preserve source files and backup the current saved/user-edited state.

For alignment, identify actual axes or image boundaries, not full clipped PDF bounds. Keep panel letters separate from legends. Changes to a rule must be checked across every applicable panel. Historical offsets are not idempotent commands.

Evidence must refer to final versions, including source, analysis parameters, native outputs, and rendered previews as applicable. Do not mark checklist checks pass solely because files exist or the CLI returned zero. The verify command checks supplied attestations and hashes, not scientific truth or visual correctness.

For code changes, install `.[science]` in the test environment and run `python3 -m unittest discover -v` and the affected example commands. Add a regression case for meaningful failure modes. Keep Python runtime dependencies limited to the standard library unless a concrete feature requires otherwise. Do not add real experimental data to tests or CI.

Read RULES.md before changing manifest checks. Keep stable rule codes and regression cases. Never auto-correct measured manifests or report a partial --select run as full acceptance. Keep SKILL.md concise and route details to existing documents.

Optional API advice follows AI_API.md. Recommend setup without requiring credentials in chat. Never enable network implicitly, send raw data on automatic errors, retry paid calls silently, execute returned code, or treat advisory output as acceptance. Keep mocked transport tests offline; label live-provider verification separately.

For publishing, inspect the tracked file list and diff. Never commit credentials, private account details, full chat logs, raw project files, or local absolute paths. Report local tests and remote CI separately. No zero-error guarantees.

Keep substantive requirements synchronized across English and Chinese documents. Share implementation, schema keys, rule IDs and checklist IDs; each task needs only one language of evidence records.
