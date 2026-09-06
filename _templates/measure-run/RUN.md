---
slug: measure-<kebab-slug>
mode: measure
status: intake          # lifecycle values and their meaning: worksheets/CONTEXT.md
direction:              # consume | emit
serves:                 # slug of the design or audit run this evidence is for
source:                 # archive split, or results file + the runner that produced it
items:                  # matrix shape, filled at stage 1
models:
opened: YYYY-MM-DD
closed:
owner:
---

# Measure: <what is being measured>

One sentence: whose responses these are and which question they answer. *(Stage 1 writes the title and this line.)*

## Where this run is

Tick a row when that stage has written its output and handed it to the human check. Every stage contract closes by doing this. If the check sends the work back, untick the row and add a loop-back entry below.

| File | Stage | Done |
|---|---|---|
| `01_intake.md` | 01 | [ ] |
| `02_conform.md` + `records/` | 02 | [ ] |
| `03_analysis.md` | 03 | [ ] |
| `04_report-back.md` | 04 | [ ] |

Originating run updated: [ ] *(stage 4 ticks this once the evidence is written into `serves`)*

## Loop-backs

**Whenever this run returns to an earlier stage, add a row here before restarting it.** Untick the rows for every stage being redone.

On a measure run the usual cause is stage 3 revealing that the matrix cannot support a statistic stage 1 assumed it would — too few models, or coverage too thin.

| Date | From stage | Back to stage | What forced it | What changed |
|---|---|---|---|---|
