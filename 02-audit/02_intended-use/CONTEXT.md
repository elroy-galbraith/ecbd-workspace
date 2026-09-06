# 02_intended-use — recover what it was built for

One job: extract the benchmark's stated intended use, and record precisely where it is missing.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_sources.md` and the sources it names
- Reference (every run): ../../_shared/worksheet-questions.md (Q1–Q2)
- Reference (every run): ../../_shared/audit-method.md
- Reference (every run): ../../_shared/ecbd-framework.md

## Process
1. Answer Q1 and Q2 using only what the sources state, with a citation per claim.
2. Separate three registers, visibly: **stated** (the sources say it), **implied** (the sources act as if it, without saying it), **absent**.
3. Quote the strongest statement of intended use verbatim. Vague intent is easiest to see in the creators' own words.
4. Watch for explicit deferral — benchmarks that hand interpretation to users, leaving no stated interpretation to validate. Record it as failure mode 1, which stage 6 checks against the catalogue; it makes every later SUPPORT question harder to answer, which is itself the finding.
5. If you named a use of your own in stage 1, note where it diverges from the stated one. Divergence here predicts most misuse.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `02_intended-use.md` → the run folder

## Human check
Read only the "absent" list. If it is empty, you probably reconstructed intent rather than found it — go back to the sources and check each claim against its citation. Edit in place.
