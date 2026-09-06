# 01-design — design a new eval

One job per stage, in order. Input is a fuzzy "we need to measure X"; output is a justified eval design plus the artefacts that implement it.

## The stages

| # | Stage | Questions | Writes to the run folder |
|---|---|---|---|
| 01 | `01_intended-use` | Framing, Q1–Q2 | `01_intended-use.md`, creates the run |
| 02 | `02_capability` | Q3–Q5 | `02_capability.md` |
| 03 | `03_content` | Q6–Q8 | `03_content.md` |
| 04 | `04_adaptation` | Q9–Q11 | `04_adaptation.md` |
| 05 | `05_assembly` | Q12–Q14 | `05_assembly.md` |
| 06 | `06_evidence` | Q15–Q20 | `06_evidence.md` |
| 07 | `07_validity-review` | all SUPPORT | `07_validity-register.md` |
| 08 | `08_build` | — | `build/` |

## Starting a run

Copy `_templates/design-run/` to `worksheets/design-<slug>/`, add a line to `worksheets/_index/log.md`, then open `01_intended-use/CONTEXT.md`. Do not begin at stage 2 because the capability seems obvious — an unstated intended use is the first documented failure mode.

## The shape of the work

Stages 1–2 set direction and take the heaviest human editing. Stages 3–6 are constrained on both sides and move faster. Stage 7 is where the run gets honest, and stage 8 is where it becomes real.

Expect to loop back: a validity review that sends you to stage 2 is the pipeline working, not failing. Record every loop-back in the table in `RUN.md`, which explains why that table is worth keeping.

## Every stage, same three moves

Describe the decision, justify it as a hypothesis about how the module fulfils its role, then support it with validity evidence — or record `none` and move on. The rules are in [../_shared/validity-evidence.md](../_shared/validity-evidence.md); no stage restates them.
