---
slug: audit-<kebab-slug>
mode: audit
status: intake          # lifecycle values and their meaning: worksheets/CONTEXT.md
benchmark:
benchmark_version:
filing_perspective:     # creator | custodian | user | third-party
audited_for_use:        # the concrete use fitness is judged against, if any
opened: YYYY-MM-DD
closed:
owner:
second_reader:
---

# Audit: <Benchmark name>

One sentence: what this benchmark claims to measure, and why it is being audited. *(Stage 1 writes the title and this line.)*

Frontmatter is the queryable copy of what `01_sources.md` records in full. Where they differ, `01_sources.md` is right.

## Where this run is

Tick a row when that stage has written its output and handed it to the human check. Every stage contract closes by doing this. If the check sends the work back, untick the row and add a loop-back entry below.

| File | Stage | Questions | Done |
|---|---|---|---|
| `01_sources.md` | 01 | Framing | [ ] |
| `02_intended-use.md` | 02 | Q1–Q2 | [ ] |
| `03_capability.md` | 03 | Q3–Q5 | [ ] |
| `04_instrument.md` | 04 | Q6–Q14 | [ ] |
| `05_evidence.md` | 05 | Q15–Q20 | [ ] |
| `06_findings.md` | 06 | all SUPPORT | [ ] |

Second reader pass complete: [ ] *(stage 6 ticks this after the second reader has examined the worksheet against the sources)*

## Loop-backs

**Whenever this run returns to an earlier stage, add a row here before restarting it.** Untick the rows for every stage being redone.

On an audit the usual cause is a source read too charitably on the first pass — which is exactly what the second reader exists to catch.

| Date | From stage | Back to stage | What forced it | What changed |
|---|---|---|---|---|
