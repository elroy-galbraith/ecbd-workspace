# 02_capability — name and ground what you are measuring

One job: define the capabilities of interest and connect them to the intended use.

This is the pivot of the whole run. Everything downstream is judged against what you write here, and most validity failures are traceable to this file.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `01_intended-use.md` from the run folder
- Reference (every run): ../../_shared/capability-conventions.md
- Reference (every run): ../../_shared/worksheet-questions.md (Q3–Q5)
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (if it exists): ../../_shared/house-context.md

Do NOT load: content or evidence references — item and metric thinking at this stage is how constructs get collapsed into their measurements.

## Process
1. Write one card per capability, in the shape given by capability-conventions.md: name, definition, context, distinguished-from, grounding, attainability.
2. Define each construct without naming any metric. If the definition cannot survive that constraint, it is a measurement wearing a capability's name.
3. If a capability decomposes, draw the tree and label every edge with why the sub-capability contributes to the parent — and whether the children exhaust it or merely sample it.
4. Answer Q4: connect each capability to the intended use, and confirm the objects of evaluation could in principle possess it.
5. Answer Q5 with a strength label per capability. `none` is a normal answer here.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `02_capability.md` → the run folder

## Human check
Read each definition to someone who works in the domain but not on this eval, and ask them to argue with it. A definition nobody can disagree with is usually too vague to measure. Edit in place.
