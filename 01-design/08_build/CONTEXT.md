# 08_build — make it runnable

One job: emit the eval the worksheet justifies, with every artefact traceable to the decision that produced it.

All paths below are inside the run folder — `worksheets/design-<slug>/build/`. This stage writes nothing into `01-design/`.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `03_content.md`, `04_adaptation.md`, `05_assembly.md`, `06_evidence.md`
- Working (this run): `07_validity-register.md`
- Working (this run): `02_capability.md` — for capability names only; every item must carry them verbatim
- Working (this run): whatever stages 3–6 already wrote into the run's `build/` — items, manifest, prompts, scorer specs
- Reference (every run): references/build-contract.md
- Reference (every run): ../../_shared/openeval-schema.md — the record format your runner must emit
- Reference (if it exists): ../../_shared/house-context.md

Do NOT load: other runs, or superseded revisions of the module files. The run's own `build/` contents are inputs, not drafts. Read `02_capability.md` for names only — rationale reaches you through the module files; if something needed here is missing from them, fix that file rather than reasoning from the capability cards.

## Process
1. Complete `build/items/` — the pool from stage 3 and the manifest from stage 5, as data, each item naming the capabilities it targets verbatim.
2. Complete `build/adaptation/` — prompt templates, config, decoding parameters, parser, exactly as specified in stage 4.
3. Complete `build/scoring/` — the extraction scorer and the accumulation logic, with per-capability breakdown preserved alongside any composite.
4. Write `build/README.md`: how to run it, what it emits, and the traceability table. State the results format explicitly: **OpenEval records**, per `_shared/openeval-schema.md`. A build whose output cannot be ingested by `03-measure/` can never have its validity gaps closed by measurement.
5. Copy the register's supported-interpretation sentence into `build/README.md` **and into whatever the runner emits with the results**. Both halves are required — the caveat must travel with the number, not sit beside the code.
6. Fill `capabilities:` in `RUN.md` frontmatter from `02_capability.md`.
7. Tick this stage's row in `RUN.md`. Leave `status` and `closed:` for the human check — this stage's gate is the one that decides whether the run is finished.

## Outputs
- `build/` → the run folder

## Human check
Run the eval end to end against one object of evaluation and read the output. Confirm the per-capability breakdown is present, and that the reported claim matches the register rather than exceeding it.

Only then set `RUN.md` status to `complete` and fill `closed:`. If the run fails here, untick stage 8 and add a loop-back row.
