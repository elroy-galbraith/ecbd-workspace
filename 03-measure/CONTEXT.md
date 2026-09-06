# 03-measure — turn responses into validity evidence

One job per stage, in order. Input is item-level responses — your own eval's, or an archive split for a benchmark under audit. Output is evidence written back into the run that needed it.

## Why this line exists

`01-design/` and `02-audit/` can describe and justify. Neither can *measure*. Every SUPPORT question they leave at `none` is a question this line can answer with arithmetic instead of argument.

Measuring is a different job from designing or reading, and it needs data neither other line produces: a response matrix across many models. That is why it is its own pipeline rather than stages bolted onto the other two.

## The stages

| # | Stage | Writes to the run folder |
|---|---|---|
| 01 | `01_intake` | `01_intake.md` |
| 02 | `02_conform` | `02_conform.md`, `records/` |
| 03 | `03_analyse` | `03_analysis.md` |
| 04 | `04_report-back` | `04_report-back.md`, `release/` |

## Two directions, one pipeline

**Consume** — an audited benchmark has OpenEval coverage. Stage 1 names the split, stage 2 is mostly validation, stage 4 writes evidence into an audit run.

**Emit** — an eval designed here has been run by your harness. Stage 1 names the results file, stage 2 conforms it, stage 4 also assembles a release bundle.

## Neither direction has been run through these stages

Be clear about this. `audit-truthfulqa` invoked `_tools/item_analysis.py` **inline from audit stage 5**, before this pipeline existed. That produced the evidence these contracts were written from, and it is why the analysis is trustworthy — but it is not the same as a measure run, and `worksheets/_index/log.md` holds no `measure-` row.

The consume path is therefore *derived from* something that worked. The emit path is not: it additionally waits on `01-design/` producing a build, and on that build conforming to the results contract. Expect loop-backs in both.

## This line does not run evals

`01-design/` ends at a runnable build; something else executes it. Results arrive through [../_shared/results-contract.md](../_shared/results-contract.md). That scope decision and its reasoning are in `docs/decisions/2026-09-06-openeval-integration.md`.

## Starting a run

Copy `_templates/measure-run/` to `worksheets/measure-<slug>/`, add a line to `worksheets/_index/log.md`, then open `01_intake/CONTEXT.md`.

Slug names what is measured, not what requested it: `measure-truthfulqa`, not `measure-for-audit-truthfulqa`. The same responses can serve more than one run.

## Releasing is not a stage

Stage 4 assembles a release-ready bundle and stops. Publishing is a human decision made per benchmark; the reasoning, including the contamination trade-off the method's authors argue for, is in `docs/decisions/2026-09-06-openeval-integration.md`.
