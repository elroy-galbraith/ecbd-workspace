# 03_content — design the pool of test items

One job: specify the item pool and show each item elicits evidence about the capabilities it targets.

## Inputs
- Working (this run): `RUN.md` — the run's state, stage table and loop-back table; this stage updates it
- Working (this run): `02_capability.md` from the run folder
- Reference (every run): ../../_shared/worksheet-questions.md (Q6–Q8)
- Reference (every run): ../../_shared/validity-evidence.md
- Reference (if it exists): ../../_shared/house-context.md
- Reference (every run): references/item-design.md

Do NOT load: `01_intended-use.md` — it reaches you through the capability file, and reading it directly invites items justified by the use case rather than by the construct.

## Process
1. Characterise the items: what data, obtained how, in what quantity, with what variation. New data or re-purposed?
2. Build the coverage table — item type against capability targeted. An item may target several.
3. Answer Q7 per item type: what about this item's characteristics makes a response to it evidence about that capability? Name the alternative explanation for a wrong answer and say why it is not the dominant one.
4. If any data is re-purposed, justify the re-use explicitly against the new capability. Data built for one purpose does not transfer for free — this is failure mode 5, and stage 7 checks it against the catalogue. Everything you need for this stage is stated here.
5. Answer Q8 with a strength label. External expert review is the usual route to content validity; note whether it happened.
6. Tick this stage's row in `RUN.md` and set `status: in-progress` if it is still `intake`. The tick means the output is written and ready for the human check below, not that it passed.

## Outputs
- `03_content.md` → the run folder
- draft items, if any exist yet → the run folder's `build/items/`

## Human check
Take three items. Answer each one incorrectly on purpose, in the way a competent system would. Then ask why that answer is wrong. If a better reason exists than "the system lacks the capability", the item measures that other reason. Edit this file directly.
