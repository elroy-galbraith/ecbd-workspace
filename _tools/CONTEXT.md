# _tools — runnable analysis

Factory, not product. Code that computes validity evidence, stable across runs, kept apart from the worksheets it serves.

| File | What it does | Used by |
|---|---|---|
| `item_analysis.py` | Classical Test Theory over OpenEval item-level data: item difficulty and discrimination, KR-20 reliability, split-half ranking stability, and the second-construct rank-penalty test | measure stage 3; audit stage 5 |
| `conform.py` | Validates a results file and maps it into OpenEval records. Detects whether the input is flat contract rows or already-conformed records and checks accordingly. Every run reports which statistics the matrix will support, so you learn that before stage 3 rather than during it | measure stages 1 and 2 |

## Why this exists

Until now the workspace was markdown with no dependencies. This is the first code in it, and it arrived the way the method prefers — written to answer a real question in a real run (`audit-truthfulqa`), not designed in advance.

`item_analysis.py` began as the prototype for `03-measure/`, which now exists. Design and reasoning: [../docs/decisions/2026-09-06-openeval-integration.md](../docs/decisions/2026-09-06-openeval-integration.md).

## Running it

```
python _tools/item_analysis.py truthfulqa
python _tools/conform.py --check results.jsonl
```

Downloads the split to a cache directory on first run (~100 MB for TruthfulQA), then prints the statistics. Requires `pandas`, `pyarrow`, `numpy`, `scipy` — nothing beyond a normal scientific Python install.

## What it is not

**Not a scorer.** It analyses evidence someone else already extracted; it does not run models or judge answers.

**Not general across benchmarks yet.** It assumes OpenEval's `bleurt-20` records with `label` and `informative` in `extra_artifacts`. Other splits carry other metrics and will need their own accessor. Verify before reusing.

**Not a substitute for reading the paper.** Every number it produces is about the instrument *as ingested by OpenEval* — one particular scoring path — never about the instrument as designed. Any worksheet citing it must say so.

## Licence note

OpenEval data is **CC-BY-NC-4.0**. This script downloads it. Commercial use of the data is restricted; the code here is not.
