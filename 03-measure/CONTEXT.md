# 03-measure — turn responses into validity evidence

One job per stage, in order. Input is item-level responses — your own eval's, or an archive split for a benchmark under audit. Output is evidence written back into the run that needed it.

## Why this line exists

`01-design/` and `02-audit/` can describe and justify. Neither can *measure*. Every SUPPORT question they leave at `none` is a question this line can answer with arithmetic instead of argument.

Measuring is a different job from designing or reading, and it needs data neither other line produces: a response matrix across many models. That is why it is its own pipeline rather than stages bolted onto the other two.

## The stages

| # | Stage | Writes to the run folder |
|---|---|---|
| 01 | `01_intake` | `01_intake.md` |
| 02 | `02_validate` | `02_validate.md`, `records/` |
| 03 | `03_analyse` | `03_analysis.md` |
| 04 | `04_report-back` | `04_report-back.md`, `release/` |

## Two directions, one pipeline

**Consume** — an audited benchmark has OpenEval coverage. Stage 1 names the split, stage 2 checks it will bear the analysis, stage 4 writes evidence into an audit run.

**Emit** — an eval designed here has been run by your harness, which emitted OpenEval records. Stage 1 names the file, stage 2 validates it, stage 4 also assembles a release bundle.

## Maturity

**Consume: proven.** `measure-truthfulqa` ran all four stages end to end. It found two defects in these contracts — both fixed — and revised two strength labels in the audit it serves.

**Emit: unproven.** It waits on `01-design/` producing a build, and on that build emitting OpenEval records. Expect loop-backs.

## This line does not run evals

`01-design/` ends at a runnable build; something else executes it and hands back **OpenEval records** — the only format accepted, per [../_shared/openeval-schema.md](../_shared/openeval-schema.md). If your harness emits rows, the adapter that nests them is yours. Both decisions are recorded in `docs/decisions/`.

## Starting a run

Copy `_templates/measure-run/` to `worksheets/measure-<slug>/`, add a line to `worksheets/_index/log.md`, then open `01_intake/CONTEXT.md`.

Slug names what is measured, not what requested it: `measure-truthfulqa`, not `measure-for-audit-truthfulqa`. The same responses can serve more than one run.

## Releasing is not a stage

Stage 4 assembles a release-ready bundle and stops. Publishing is a human decision made per benchmark; the reasoning, including the contamination trade-off the method's authors argue for, is in `docs/decisions/2026-09-06-openeval-integration.md`.
