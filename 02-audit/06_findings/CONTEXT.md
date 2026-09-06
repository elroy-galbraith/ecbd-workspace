# 06_findings — say what it is fit for

One job: synthesise the audit into validity threats, a fitness verdict, and usable guidance.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): all of `01_sources.md` through `05_evidence.md`
- Reference (if it exists): ../../_shared/house-context.md
- Reference (every run): ../../_shared/failure-modes.md
- Reference (every run): ../../_shared/ecbd-framework.md — for "What this is not"
- Reference (every run): ../../_shared/audit-method.md
- Reference (every run): ../../_shared/validity-evidence.md

## Process
1. Build the register: every SUPPORT answer with its strength label, and every gap.
2. Walk all nine entries in failure-modes.md against this benchmark. Record each as clear, present with citation, or not determinable from the sources.
3. Rank the validity threats by how much they would change a decision made on these results — not by how easy they were to find.
4. Give the verdict against the use named in stage 1: what interpretations these results support, and which nearby ones they do not. If no use was named, give the verdict per stated intended use instead.
5. Write the mitigations a *user* can apply without the creators: report your own adaptation method where none is prescribed, read per-capability results rather than the composite, treat contested constructs as the specific operationalisation they are.
6. Separate what is a validity threat from what is outside ECBD — the list is in `ecbd-framework.md` under "What this is not". Both matter; conflating them weakens the findings.
7. Set `RUN.md` status to `review` and hand to the second reader named in `house-context.md`, or to whoever the owner nominates.
8. Tick this stage's row in `RUN.md`. Leave `second_reader:`, `closed:` and the final status for the human check below.

## Outputs
- `06_findings.md` → the run folder

## Human check
Have a second reader who did not complete the worksheet examine it against the sources, as the method requires. Resolve disagreements about phrasing and interpretation in the file, not in conversation. Findings that survive a second reader are the ones worth publishing.

When they are done: record them in `second_reader:`, tick "Second reader pass complete", set status to `complete` and fill `closed:`. If they send it back, add a loop-back row and untick the stages being redone.
