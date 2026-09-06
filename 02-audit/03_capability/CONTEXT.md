# 03_capability — recover what it claims to measure

One job: extract the capabilities of interest as the benchmark conceptualises them, and assess how well they are defined and grounded.

The paper's deepest findings live here. Give it its own gate.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_sources.md` from the run folder, **and the sources it names**
- Working (this run): `02_intended-use.md` from the run folder
- Reference (every run): ../../_shared/capability-conventions.md
- Reference (every run): ../../_shared/worksheet-questions.md (Q3–Q5)
- Reference (every run): ../../_shared/audit-method.md
- Reference (every run): ../../_shared/validity-evidence.md

## Process
1. Answer Q3: list the capabilities named, with the benchmark's own definition and the context it assumes, cited. Where a term is used without definition, record the term and mark the definition absent.
2. Draw the decomposition tree as the benchmark presents it. Mark every unexplained edge — a sub-capability introduced as self-evidently relevant to the parent is failure mode 2, checked at stage 6, and it is common.
3. Check for constructs defined by their measurement — failure mode 3, checked at stage 6. Quote the definition if so.
4. Flag contested constructs used as though uncontroversial: fairness, bias, toxicity, quality, helpfulness. Note whose definition is in play and whether anyone affected was consulted.
5. Answer Q4 and Q5 with strength labels. `none` will be the common answer; that is the result, not a gap in your work.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `03_capability.md` → the run folder

## Human check
Choose one capability. Try to write a test item for it, using only the benchmark's own definition. If you cannot tell what a passing answer looks like, the construct is underspecified. Every later stage of this audit inherits that problem. Edit this file directly.
