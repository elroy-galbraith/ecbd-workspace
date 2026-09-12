---
bootstrap: false
inputs:
  - path: RUN.md
    relative_to: run
    access: read-write
  - path: 01_intended-use.md
    relative_to: run
    access: read
  - path: 02_capability.md
    relative_to: run
    access: read
  - path: 03_content.md
    relative_to: run
    access: read
  - path: 04_adaptation.md
    relative_to: run
    access: read
  - path: 05_assembly.md
    relative_to: run
    access: read
  - path: 06_evidence.md
    relative_to: run
    access: read
  - path: _shared/failure-modes.md
    relative_to: repo
    access: read
  - path: _shared/ecbd-framework.md
    relative_to: repo
    access: read
  - path: _shared/validity-evidence.md
    relative_to: repo
    access: read
  - path: _shared/decision-cost.md
    relative_to: repo
    access: read
  - path: _shared/worksheet-questions.md
    relative_to: repo
    access: read
  - path: _shared/house-context.md
    relative_to: repo
    access: read
    optional: true
outputs:
  - path: 07_validity-register.md
    relative_to: run
---

# 07_validity-review — get honest about what this earns

One job: audit the run's own SUPPORT answers, trace every capability end to end, and write the validity register.

The stage the paper exists to force. Everything before this describes and justifies; this one asks what has actually been shown.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): all of `01_intended-use.md` through `06_evidence.md`
- Reference (every run): ../../_shared/failure-modes.md
- Reference (every run): ../../_shared/ecbd-framework.md — for "What this is not"
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (every run): ../../_shared/decision-cost.md — for the cost labels and what `absent` obliges
- Reference (every run): ../../_shared/worksheet-questions.md — the register keys off its numbering
- Reference (if it exists): ../../_shared/house-context.md

## Process
1. Collect every SUPPORT answer (Q5, Q8, Q11, Q14, Q17, Q20) into the register with its strength label. Do not round upward; `precedent-only` is a gap.
2. Run the traceability test: every capability from Q3 must appear in Q6 (items), Q13 (assembly) and Q19 (accumulation). List any that drop out, and any measurement that appears with no capability behind it.
3. Walk all nine entries in failure-modes.md against this run. Record each as clear, present, or accepted-with-reason.
4. Write the decision cost row: cost of failure in both directions from stage 1, the asymmetry and its label, and the operating point with its loss ratio and switching condition from stage 6. A label of `absent` or `assumed`, or an operating point with no ratio behind it, is a gap — carry it into the gaps table at step 5 the way a SUPPORT answer of `none` goes there.
5. For every gap, write what experiment would close it and roughly what it costs. A gap without a next step is a complaint.
6. State the interpretation the results *do* support — the sentence users may say — and the nearby sentences they may not.
7. Note anything real but outside ECBD — the list is in `ecbd-framework.md` under "What this is not". Decision cost is no longer on that list; it has its own row from step 4.
8. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `07_validity-register.md` → the run folder

## Human check
Read the register on its own, without the rest of the worksheet. Then answer two questions.

Would you make a real decision from this eval? At what score would you act, and what does it cost you to act wrongly at that score? A register that cannot answer the second question is not finished, however good its support ledger looks.

If either answer fails, return the run to the stage that caused the problem. That is usually stage 2, or stage 1 if the cost row is empty. Do not weaken the register instead.

Set `RUN.md` status to `review` before you pass the run on. If you return the run, first add a row to the loop-back table in `RUN.md`. Record which stage, what forced it, and what changed. If someone weakened the register instead of returning the run, record that too.
