# 05_assembly — select the set actually used

One job: decide which items from the pool are used, and show the selection gathers sufficient evidence for every capability.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `03_content.md` from the run folder
- Working (this run): `02_capability.md` from the run folder
- Reference (every run): ../../_shared/worksheet-questions.md (Q12–Q14)
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (if it exists): ../../_shared/house-context.md

## Process
1. State the count and the selection rule: all items, sampled, stratified, difficulty-targeted, split-inherited. Include the seed if sampling.
2. Name the constraints that drove the number — compute, money, latency, annotation effort. Assembly choices are usually resource decisions presented as methodological ones; say which this is.
3. Answer Q13 per capability: does the selected subset carry enough evidence for *each* one, not just in aggregate? A capability covered by two items is a rounding error, not a measurement.
4. If splits are inherited from an existing dataset, justify continued use of those splits or say you could not — this is failure mode 7, checked at stage 7.
5. Answer Q14 with a strength label. Note the trade-off you accepted between sample size and measurement error rather than leaving it implicit.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `05_assembly.md` → the run folder
- selection manifest or script → the run folder's `build/items/`

## Human check
Count items per capability from the manifest and compare against the capability list in `02_capability.md`. Any capability with a thin count either gets more items or gets dropped from the claims. Edit in place.
