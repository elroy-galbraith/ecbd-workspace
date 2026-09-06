# 07_validity-review — get honest about what this earns

One job: audit the run's own SUPPORT answers, trace every capability end to end, and write the validity register.

The stage the paper exists to force. Everything before this describes and justifies; this one asks what has actually been shown.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): all of `01_intended-use.md` through `06_evidence.md`
- Reference (every run): ../../_shared/failure-modes.md
- Reference (every run): ../../_shared/ecbd-framework.md — for "What this is not"
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (every run): ../../_shared/worksheet-questions.md — the register keys off its numbering
- Reference (if it exists): ../../_shared/house-context.md

## Process
1. Collect every SUPPORT answer (Q5, Q8, Q11, Q14, Q17, Q20) into the register with its strength label. Do not round upward; `precedent-only` is a gap.
2. Run the traceability test: every capability from Q3 must appear in Q6 (items), Q13 (assembly) and Q19 (accumulation). List any that drop out, and any measurement that appears with no capability behind it.
3. Walk all nine entries in failure-modes.md against this run. Record each as clear, present, or accepted-with-reason.
4. For every gap, write what experiment would close it and roughly what it costs. A gap without a next step is a complaint.
5. State the interpretation the results *do* support — the sentence users may say — and the nearby sentences they may not.
6. Note anything real but outside ECBD — the list is in `ecbd-framework.md` under "What this is not".
7. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `07_validity-register.md` → the run folder

## Human check
Read the register alone, without the rest of the worksheet, and decide whether you would ship a decision on this eval. If the answer is no, the fix is a loop back to the stage that caused it — most often stage 2 — not a softer register.

Set `RUN.md` status to `review` before handing on. If you send the run back, add a row to the loop-back table in `RUN.md` first: which stage, what forced it, what changed. A run whose register got softer instead of looping back should show that in the table too.
