# 03_analyse — compute what the records support

One job: produce the psychometric evidence, and state plainly what the matrix cannot support.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `02_validate.md` and the run's `records/`
- Working (this run): `01_intake.md` — for the claimed capabilities and the matrix shape
- Reference (every run): ../../_tools/CONTEXT.md
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (every run): ../../_shared/interpreting-item-analysis.md — the remedies keyed to what fired

Do NOT load: the originating run's findings or register. Compute first, compare at stage 4. Reading the conclusion before running the numbers is how an analysis comes to confirm what someone hoped.

## Process
1. Run the analysis, naming the source explicitly — `--records <path>` for local records, `--split <name>` for an archive split. The tool refuses to guess. Record the exact command and its output verbatim.
2. **Where the source is an archive split, run `--facet` on any item field worth splitting on** — construction method, category, source. The tool compares each level against a size-matched random baseline, so it reports only the levels that disagree more than chance already does. Without the size match the comparison manufactures findings.
3. Report item difficulty and discrimination, and KR-20 reliability. Say how many items fail to discriminate.
4. Report ranking stability: split-half rank correlation, and how often a model pair swaps order between halves. The tool prints `SKIPPED` with the reason where the matrix is too small — record that verbatim rather than reaching for a number that cannot bear weight.
5. Compute the **separating gap** — the score difference two models need before their ordering is supported — and compare it to the gaps actually observed. This is the most decision-relevant number the pipeline produces.
6. **Run the traceability check.** The tool reports it per capability when `ecbd_capability` tags are present. Confirm every capability from `01_intake.md` appears, and that its items discriminate. A capability whose items do not discriminate is measured in name only; one absent from the table is not measured at all.
7. Where a second construct is present in `extra_artifacts`, test the trade-off between it and the primary score.
8. **Write the interpretation, not just the numbers.** For each condition in the tool's `DIAGNOSIS` block, take the entry of the same name from `interpreting-item-analysis.md` and say what it means *here* — what to try if this eval is yours, what to do if it is not, and the trap named there. A reader who is not a psychometrician should finish this section knowing what to change.
9. State what is **not** computable from this matrix, and what data would make it so.
10. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `03_analysis.md` → the run folder

## Human check
Read the numbers to find where they disagree with the run, not where they agree. An analysis that confirms every claim has usually been read too kindly. Check one thing in particular: is the separating gap larger than the differences people are already acting on?
