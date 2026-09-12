---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
  - path: 04_adaptation.md
    relative_to: run
    access: read
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: 05_assembly.md
    relative_to: run
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 06_evidence.md
    relative_to: run
  - path: build/scoring/
    relative_to: run
---

# 06_evidence — turn responses into measurements

One job: specify extraction (per item: response → observable variable) and accumulation (across items: variables → measurement of the capabilities).

Two components, one module, because the second is meaningless without the first.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_intended-use.md` from the run folder — the decision this number feeds, and the cost asymmetry that places its threshold
- Working (this run): `04_adaptation.md` from the run folder
- Working (this run): `02_capability.md` from the run folder
- Working (this run): `05_assembly.md` from the run folder — per-capability item counts bound what accumulation can claim
- Reference (every run): ../../_shared/worksheet-questions.md (Q15–Q20)
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (if it exists): ../../_shared/house-context.md

## Process
1. **Extraction (Q15).** State which response is captured, choosing from the kinds Q15 enumerates, and how evidence is represented as an observable variable. Include the judge model, rubric, or metric in full if one is used.
2. Answer Q16: why does that observable variable capture the capability? Argue it. "It is the standard metric for this task" is precedent, not justification — failure mode 8, checked at stage 7.
3. **Accumulation (Q18).** State how item-level variables combine: mean, pass rate, weighted score, per-capability breakdown. Name every assumption the aggregation makes about the distribution of item scores.
4. Answer Q19: does the accumulated number measure the capability of interest, or a mixture of capabilities plus item difficulty? If capabilities are averaged together, say what the composite means and whether anyone should act on it.
5. **Operating point.** If the accumulated number gates a decision, state where the line sits, the loss ratio that justifies it, and the switching condition that would move it. Take the ratio and its label from `01_intended-use.md` and carry both forward unchanged; if the label is `absent`, record that this threshold asserts one to one and name who has to be asked. A threshold nobody derived is failure mode 8 wearing a number instead of a metric name.
6. Answer Q17 and Q20 with strength labels. For a judge or automatic metric, correlation against human annotation on a sample is the standard empirical evidence — record whether you have it or plan it.
7. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `06_evidence.md` → the run folder
- scorer and aggregator specs → the run folder's `build/scoring/`, including the operating point if there is one

## Human check
Take the accumulated number. Write the one sentence a user would say about a system that scores it. If that sentence claims more than the extraction and accumulation support, make the claim smaller or make the method better.

If the eval has a pass line, say what it costs to be wrong on each side of that line. A pass line with no cost behind it claims that both errors cost the same. Say that claim out loud and see if the decision-maker agrees.

Edit this file directly.
