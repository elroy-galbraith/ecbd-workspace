# 05_evidence — recover how scores are made

One job: extract evidence extraction and accumulation — Q15 through Q20 — and assess whether the numbers land back on the capabilities.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_sources.md` from the run folder, **and the sources it names**
- Working (this run): `04_instrument.md` and `03_capability.md` from the run folder
- Reference (every run): ../../_shared/worksheet-questions.md (Q15–Q20)
- Reference (every run): ../../_shared/audit-method.md
- Reference (if the benchmark has OpenEval coverage): ../../_tools/CONTEXT.md — item-level analysis
- Reference (every run): ../../_shared/validity-evidence.md

## Process
1. **Extraction (Q15–Q17).** Record which responses are captured, and how evidence is represented — the metric, judge, or rubric in full, cited.
2. **Accumulation (Q18–Q20).** Record how item-level scores combine, and what assumptions the aggregation makes about their distribution. Note whether per-capability results survive or are averaged away.
3. Look for justification-by-precedent: metrics called standard or default, or chosen to follow prior work. That is failure mode 8, checked at stage 6, and it is the usual finding — including where the benchmark introduces a *new* metric, which still needs a case that it measures what it claims.
4. Run the traceability test against the capabilities from Q3: does each one have items targeting it, assembly covering it, and accumulation measuring it? Name every capability that drops out, and every number reported with no capability behind it.
5. Strength labels on Q17 and Q20.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `05_evidence.md` → the run folder

## Human check
Take the benchmark's headline number and write the sentence its users actually say about a system that scores well. Compare that sentence against what extraction and accumulation support. The distance between them is the audit's main result. Edit in place.
