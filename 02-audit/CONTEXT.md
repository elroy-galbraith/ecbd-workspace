# 02-audit — analyse an existing benchmark

One job per stage, in order. Input is a benchmark someone else built; output is a completed worksheet and a fitness verdict.

## The stages

| # | Stage | Questions | Writes to the run folder |
|---|---|---|---|
| 01 | `01_sources` | Framing | `01_sources.md`, creates the run |
| 02 | `02_intended-use` | Q1–Q2 | `02_intended-use.md` |
| 03 | `03_capability` | Q3–Q5 | `03_capability.md` |
| 04 | `04_instrument` | Q6–Q14 | `04_instrument.md` |
| 05 | `05_evidence` | Q15–Q20 | `05_evidence.md` |
| 06 | `06_findings` | all SUPPORT | `06_findings.md` |

Coarser than the design line on purpose: the decisions are already fixed, so gates are about interpretation rather than choice. Content, adaptation and assembly are usually documented thinly and read together, which is why they share stage 4.

Record every return to an earlier stage in the loop-back table in `RUN.md`, and untick the stages being redone. On an audit the usual trigger is the second reader at stage 6 finding a source read too charitably on the first pass — which is what they are there for.

## Starting a run

Copy `_templates/audit-run/` to `worksheets/audit-<slug>/`, add a line to `worksheets/_index/log.md`, then open `01_sources/CONTEXT.md`.

## The method

Two passes and a second reader; not-stated is a finding; cite everything; audit the version, not the benchmark. The rules are in [../_shared/audit-method.md](../_shared/audit-method.md), which every stage below loads. This file routes — it does not restate them.
