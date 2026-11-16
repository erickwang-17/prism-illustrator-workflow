# Figure task record

**English** | [简体中文](TASK_TEMPLATE.zh-CN.md)

Copy this file into an ignored local task directory. Populate it from actual files and current instructions. Blank fields mean unresolved, not permission to infer data.

## Scope and current decisions

- Task ID / date:
- Source projects and SHA-256:
- User-edited working project and saved-state check:
- Reference figure / style measurements:
- Final deliverables and destination:
- Panels included / omitted:
- Latest requirements (one explicit statement per row):

| Requirement ID | Current instruction | Affected panels | Supersedes | Acceptance evidence |
|---|---|---|---|---|
| | | | | |

## Scientific decisions

- Biological unit, sample IDs and technical replication:
- Repeated / paired / nested design:
- Source analysis method, parameters, correction and comparison family:
- Planned contrasts, including control and NAtm where requested:
- Explicitly authorized exclusions and separate sensitivity versions:
- Unresolved questions and only the steps they block:

## Execution and checkpoints

| Stage | Inputs + hashes | Parameters / rule version | Output + hash | State | Evidence |
|---|---|---|---|---|---|
| Data fidelity | | | | unresolved | |
| Analysis reproduction | | | | unresolved | |
| Design validity | | | | unresolved | |
| Native graph formatting | | | | unresolved | |
| Significance annotation | | | | unresolved | |
| Export and layout | | | | unresolved | |
| Visual and saved-file review | | | | unresolved | |

Use unresolved / in_progress / blocked / verified / not_applicable. For a blocker, name the missing fact; for N/A, give a reason. These are task-record labels, not the stricter checklist.json status vocabulary. Resume from the last checkpoint whose inputs, parameters, outputs and applicable rules remain unchanged. Do not rerun transformations solely because a chat resumed.

## Final review

- Whole-figure inventory checked, including every C panel and separate CMML/AML legends:
- Supplied manifest agrees with native objects and final render:
- All required checklist IDs covered; no required check silently omitted:
- Local automated tests / native checks / remote CI reported separately:
- Remaining limitations:
