# 03_analyse — compute what the records support

One job: produce the psychometric evidence, and state plainly what the matrix cannot support.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `02_conform.md` and the run's `records/`
- Working (this run): `01_intake.md` — for the claimed capabilities and the matrix shape
- Reference (every run): ../../_tools/CONTEXT.md
- Reference (every run): ../../_shared/validity-evidence.md

Do NOT load: the originating run's findings or register. Compute first, compare at stage 4. Reading the conclusion before running the numbers is how an analysis comes to confirm what someone hoped.

## Process
1. Run the analysis, naming the source explicitly — `--records <path>` for a conformed file, `--split <name>` for an archive split. The tool refuses to guess. Record the exact command and its output verbatim.
2. Report item difficulty and discrimination, and KR-20 reliability. Say how many items fail to discriminate.
3. Report ranking stability: split-half rank correlation, and how often a model pair swaps order between halves. The tool prints `SKIPPED` with the reason where the matrix is too small — record that verbatim rather than reaching for a number that cannot bear weight.
4. Compute the **separating gap** — the score difference two models need before their ordering is supported — and compare it to the gaps actually observed. This is the most decision-relevant number the pipeline produces.
5. **Run the traceability check.** The tool reports it per capability when `ecbd_capability` tags are present. Confirm every capability from `01_intake.md` appears, and that its items discriminate. A capability whose items do not discriminate is measured in name only; one absent from the table is not measured at all.
6. Where a second construct is present in `extra_artifacts`, test the trade-off between it and the primary score.
7. State what is **not** computable from this matrix, and what data would make it so.
8. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `03_analysis.md` → the run folder

## Human check
Read the numbers looking for the disagreement, not the confirmation. An analysis that agrees with every claim has usually been read charitably. Check specifically whether the separating gap is smaller than the differences anyone is already acting on.
