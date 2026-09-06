# 06_evidence — turn responses into measurements

One job: specify extraction (per item: response → observable variable) and accumulation (across items: variables → measurement of the capabilities).

Two components, one module, because the second is meaningless without the first.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
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
5. Answer Q17 and Q20 with strength labels. For a judge or automatic metric, correlation against human annotation on a sample is the standard empirical evidence — record whether you have it or plan it.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `06_evidence.md` → the run folder
- scorer and aggregator specs → the run folder's `build/scoring/`

## Human check
Take the accumulated number and write the single sentence a user would say about a system scoring it. If that sentence claims more than the extraction and accumulation support, tighten the claim or the method. Edit in place.
