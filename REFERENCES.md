# Design references and tradeoffs

**English** | [简体中文](REFERENCES.zh-CN.md)

Review date: 2026-11-16. These are design references, not dependencies, partnerships or endorsements. GitHub stars, paper citations and downstream adoption measure different things. No reproducible citation-count dataset was obtained, so these projects are not claimed to rank highest on a shared metric.

Previously reviewed page snapshots on that date showed approximately 92.0k stars for uv, 2.9k for Snakemake and 331 for nf-core/tools. These are dated observations, not current rankings or measures of scientific validity. No unverified counts are supplied for other projects.

| Project / primary source | Pattern adopted | Implementation and limits |
|---|---|---|
| [uv](https://github.com/astral-sh/uv), [project layout](https://docs.astral.sh/uv/concepts/projects/layout/) | Consistent CLI and metadata | pyproject.toml, installable figureflow, --version; direct Python entry retained, no uv runtime dependency |
| [Ruff rules](https://docs.astral.sh/ruff/rules/) | Numbered diagnostics and selection | rules/lint, JSON paths and correction descriptions; not Ruff rules or automatic fixes |
| [Snakemake configuration](https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html) | Separate configuration and validate before execution | Version-1 manifests, strict fields/types; not a general JSON Schema engine |
| [nf-core/tools](https://nf-co.re/docs/nf-core-tools) | Templates, lint and acceptance documentation | Task template, 81 checks, format rules and CI; no imposed nf-core statistical model |
| [Anthropic Skills](https://github.com/anthropics/skills) | Skill metadata and on-demand resources | Root skill entry routes to repository docs; no wholesale external skill copying or plugin installation |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | Traceable requirements, tasks and results | TASK_TEMPLATE records current/superseded instructions, scope and evidence; no large specification required for trivial edits |
| [Superpowers](https://github.com/obra/superpowers) | Staged work, tests and final verification | Checkpoints, evidence and historical regression cases; not all agent behaviors imported |
| [pre-commit](https://pre-commit.com/) | Repeatable pre-commit checks | Optional local hook uses CI's unittest discovery; no global hook edits |
| [pytest parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html) | Multiple boundary cases per behavior | Table-driven count, numeric and regex cases in standard-library unittest; no pytest dependency |
| [MultiQC](https://docs.seqera.io/multiqc) | Aggregate existing results | summary retains statuses/hashes; no P calculation or complete acceptance claim |
| [Nextflow resume](https://docs.seqera.io/nextflow/cache-and-resume) | Reuse depends on inputs/state | Checkpoint records compare inputs, parameters, outputs and rules; no native-app caching executor |
| [Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/README.html) | Templates reduce omissions | Copyable task records and explicitly synthetic manifests; no external template hooks |

## Adoption criteria

Every mechanism needs a purpose, scope and tests where automation permits. Native operations, scientific judgments and final previews remain independently reviewed. Compare manifests to real projects/previews. New rules need concrete failure cases; historical preferences are not universal experimental laws.

Implementation was written independently, without copying upstream source or entire documents or assuming upstream trademarks, licensing or endorsement. Any later source reuse requires separate license review and attribution.

Frameworks are not all installed merely to collect features. Base audits/API use the standard library, installation uses setuptools, and scientific computing uses the optional `[science]` dependencies. Automatic native-object recognition, Prism style extraction, statistical model selection and GUI recovery were not implemented by this reference review.
