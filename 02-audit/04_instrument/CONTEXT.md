# 04_instrument — recover how the test is built and delivered

One job: extract content, adaptation and assembly decisions in one pass — Q6 through Q14.

Three modules, one stage: in practice they are documented together, thinly, and reading them apart means reading the same paragraph three times.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_sources.md` from the run folder, **and the sources it names**
- Working (this run): `03_capability.md` and `02_intended-use.md` from the run folder — Q10 is answered against the objects in Q1
- Reference (every run): ../../_shared/worksheet-questions.md (Q6–Q14)
- Reference (every run): ../../_shared/audit-method.md
- Reference (every run): ../../_shared/failure-modes.md
- Reference (every run): ../../_shared/validity-evidence.md

## Process
1. **Content (Q6–Q8).** Characterise the items and map them to capabilities from Q3. If data is re-purposed, find the justification connecting it to the new capability — failure mode 5 is finding none.
2. **Adaptation (Q9–Q11).** Record how objects are prompted or adapted. If unprescribed, that is failure mode 6: note that results are not comparable across users, and that users should report what they employed.
3. **Assembly (Q12–Q14).** Record counts, splits and selection. Look specifically for caps and splits stated without rationale, and inherited splits whose original construction is undocumented — failure mode 7.
4. Keep the three sections separate in the output even though you read them together. The next stage and the findings stage address them individually.
5. Strength labels on Q8, Q11, Q14.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `04_instrument.md` → the run folder

## Human check
Check the capability coverage: could you reproduce the evaluation set from what the sources say? If not, name the missing information precisely — "the selection process for the 1,000-item cap is not described" is a finding, "underdocumented" is not. Edit in place.
