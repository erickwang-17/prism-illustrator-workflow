---
name: prism-illustrator-workflow
description: Audit experimental figure data, plan significance annotations from verified results, and coordinate native Prism-to-Illustrator formatting with evidence checks. Use for multi-panel scientific figure production or review.
---

# Prism–Illustrator workflow

Use this skill from a checkout of this repository; keep its supporting files together. It does not supply native application access. Check the host's available tools before promising native edits.

Start with the latest user decisions and the currently saved or user-edited project. For multi-step figure work, copy [TASK_TEMPLATE.md](TASK_TEMPLATE.md) into an ignored local work directory and fill the inputs, affected panels, exceptions, and acceptance conditions. Do not turn historical sample counts, exclusions, or offsets into defaults.

Read only the applicable material:

- [WORKFLOW.md](WORKFLOW.md): data, statistics, native formatting, export and layout requirements. Search the relevant section; retain the full checklist for final delivery.
- [README.md](README.md): exact CLI input/output contracts and available commands.
- [RULES.md](RULES.md): measured figure manifests, rule codes, and regex boundaries when checking formatting.

Keep three decisions separate: data fidelity, reproduction of an existing analysis, and validity of that analysis for the experimental design. Matching raw data does not establish the latter two. `plan` consumes adjusted P values; it never calculates them. Record unresolved design questions and continue independent work.

Preserve native circles, borders, axes, legends and text. Do not simulate borders with offset shapes or substitute screenshots for native edits. Apply a formatting change to every affected panel, then remeasure. Only one relevant native project window should be manipulated at a time; after a failed open, inspect the actual app state before retrying.

Run the appropriate local commands with explicit inputs. Save new reports with `--out` under a fresh task directory. Record source/output hashes and the active rule set. `lint --select` is a scoped check, not full acceptance. Unknown measurements remain unresolved; never fill them with synthetic example values.

At handoff, distinguish generated plans, executed native changes, verified previews and saved files. Reuse prior evidence only when inputs, parameters, outputs, rule versions and scope still match. A changed artifact invalidates its dependent checks. Final acceptance requires actual visual review plus [checklist.json](checklist.json), not just a green CLI report. Do not repeatedly apply an old relative translation.

This skill does not authorize publication, installation, messages or statistics changes beyond the user's task. Use existing session authorization; ask only for missing decisions that block dependent work.
