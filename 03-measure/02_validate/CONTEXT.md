# 02_validate — check the records will bear the analysis

One job: confirm the records are sound OpenEval and that the fields the analysis depends on are actually populated.

Bad records produce confident nonsense downstream. This stage exists so that failure is caught here rather than read as a finding at stage 3.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_intake.md` and the source it names
- Reference (every run): ../../_shared/openeval-schema.md
- Reference (every run): ../../_tools/CONTEXT.md

## Process
1. Run `python _tools/validate.py <records.jsonl>` for local records, or `--split <name>` for an archive split.
2. **The two checks answer different questions, and only one is this tool's job.** Whether the records are valid OpenEval is settled by `validator.py` upstream — run it before releasing anything, and do not reimplement it. Whether the analysis can *use* them is settled here.
3. Record the schema version, the metrics present, and the coverage figures verbatim.
4. **Treat an absent optional field as a finding, not a formality.** A record with no `item_adaptation.request_input` is valid OpenEval and makes every later claim about adaptation unsupported. Say which fields are missing and which findings that forecloses.
5. Record capability tags if present. Archive records will not have them — the `ecbd_capability` convention is this workspace's, and a third-party contributor had no reason to follow it. Say so rather than treating it as damage.
6. Report the shape obtained: items, models, responses, metrics. Where it differs from stage 1's count, say which number is which — a split total, a per-metric subset and a post-filter matrix are three different things and all three are correct.
7. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `02_validate.md` → the run folder
- `records/` → the run folder, where records are held locally

## Human check
Open three records and read them against the raw source — one typical, one with an unusual score, one from the worst-covered model. Confirm `item_adaptation.request_input` holds what the model actually received and not the unrendered template. Every adaptation finding rests on that field, and it is the one most often wrong.
