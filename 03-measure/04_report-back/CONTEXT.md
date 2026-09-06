# 04_report-back — write the evidence where it belongs

One job: put the findings into the run that needed them, and assemble a release bundle.

Analysis that stays in its own folder changes nothing. The originating run is where a SUPPORT question sits at `none`; this stage is what fills it.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_intake.md` and `03_analysis.md`
- Working (this run): the run's `records/` — needed to assemble `release/`
- Working (this run): the originating run's `RUN.md`, and its register or findings — `07_validity-register.md` for a design run, `06_findings.md` for an audit
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (every run): ../../_shared/openeval-schema.md
- Reference (if it exists): ../../_shared/house-context.md

## Process
1. Write the evidence summary: what was measured, what it shows, what it does not.
2. Assign a strength label to each SUPPORT question this evidence bears on. Direct measurement on these records is `empirical-direct` — but name the scoring path, because evidence about one metric is not evidence about another.
3. **Update the originating run.** Append a cited section to its register or findings naming this measure run, and revise the affected strength labels. If that run is `complete`, add a loop-back row and hand it back to its owner to re-gate — the human check below covers this. A Process step may write evidence into a run; only a person moves it out of `complete`.
4. Where the evidence contradicts a claim in the originating run, say so **in that run's file**, not only here. A contradiction recorded only in the measuring run is one nobody will find.
5. **Emit direction only:** assemble `release/` — conformant records, plus a README naming the benchmark version, contributor, licence, and the worksheet path that justifies the eval.
6. Tick this stage's row in `RUN.md`, tick "Originating run updated", and set `status: review`.

## Outputs
- `04_report-back.md` → the run folder
- `release/` → the run folder, emit direction only

## Human check
Read the originating run's register again, from start to finish. It should now say something it could not say before. Where a strength label improved, confirm the evidence describes the same scoring path that the run uses.

If the originating run was `complete`, set it back to `review` yourself. A reopen is a gate, and a person passes every gate.

Then set this run's status to `complete` and fill `closed:`. For an emit run, decide about publication first. `docs/decisions/2026-09-06-openeval-integration.md` sets out the trade-off. The bundle is ready; you decide whether it goes out, not the pipeline. Record your decision in `04_report-back.md`.
