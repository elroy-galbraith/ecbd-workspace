# 02_conform — get the records right

One job: bring the responses into OpenEval-conformant records, and validate them.

Bad records produce confident nonsense downstream. This stage exists so that failure is caught here rather than read as a finding at stage 3.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_intake.md` and the source it names
- Reference (every run): ../../_shared/openeval-schema.md
- Reference (every run): ../../_shared/results-contract.md
- Reference (every run): ../../_tools/CONTEXT.md

## Process
1. **Consume direction:** the records already conform. Validate them with `--check`, record the schema version, and note any field the archive leaves empty that the analysis will need. For a submission-grade check use `validator.py` from `open-eval/OpenEval`.
2. **Emit direction:** run `python _tools/conform.py <results.jsonl> --out records/` to map the results file into the schema.
3. Carry ECBD capability tags into `scores[].metric.extra_artifacts` using the convention in openeval-schema.md. Record in the output that these tags are a local convention, not part of the standard.
4. Validate with `python _tools/conform.py --check <file>` — it detects whether the file is flat contract rows or already-conformed records and checks accordingly. Fix violations at source where you can. Where a field genuinely cannot be filled, record which and why — an absent `request_input` means every later claim about adaptation is unsupported.
5. Report the shape actually obtained: items, models, responses, metrics present, coverage per model. Where it differs from stage 1's estimate, say so.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `02_conform.md` → the run folder
- `records/` → the run folder

## Human check
Open three records and read them against the raw source — one typical, one with an unusual score, one from the worst-covered model. Confirm `request_input` holds what the model actually received and not the unrendered template. Every adaptation finding rests on that field, and it is the one most often wrong.
