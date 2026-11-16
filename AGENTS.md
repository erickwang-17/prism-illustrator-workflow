# Working in this repository

This repository provides figure workflow documentation and local verification tools. It is not a native Prism/Illustrator replacement.

For a figure task, read README.md and WORKFLOW.md. Apply the latest explicit user requirements before historical style examples. Keep raw data and native projects outside the tracked source tree, normally under ignored local/ or data/ directories.

Do not silently select or change a statistical test. Distinguish source-data fidelity, reproduction of an existing analysis, and experimental-design validity. The plan command consumes supplied adjusted P values; it does not perform statistical testing. Missing biological design information blocks dependent conclusions, not unrelated formatting work.

Use real native Prism points/borders/legends and Illustrator vector objects. Never fake native edits with screenshots or stacked circles. Avoid undocumented binary mutations and repeated opening/replacing of native projects. Preserve source files and backup the current saved/user-edited state.

For alignment, identify actual axes or image boundaries, not full clipped PDF bounds. Keep panel letters separate from legends. Changes to a rule must be checked across every applicable panel. Historical offsets are not idempotent commands.

Evidence must refer to final versions, including source, analysis parameters, native outputs, and rendered previews as applicable. Do not mark checklist checks pass solely because files exist or the CLI returned zero. The verify command checks supplied attestations and hashes, not scientific truth or visual correctness.

For code changes, run `python3 -m unittest -v test_figureflow.py` and the affected example commands. Add a regression case for meaningful failure modes. Keep Python runtime dependencies limited to the standard library unless a concrete feature requires otherwise. Do not add real experimental data to tests or CI.

For publishing, inspect the tracked file list and diff. Never commit credentials, private account details, full chat logs, raw project files, or local absolute paths. Report local tests and remote CI separately. No zero-error guarantees.
