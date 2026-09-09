# Run log

The catalog: one line per run, added when the run folder is created. It records what exists, not how far it got.

**Status is not here.** A run's state lives in its `RUN.md` and nowhere else — `status:` in the frontmatter, progress in the stage table. A status column here would be a second copy that drifts the moment someone finishes a stage without updating two files. To report status, read this table for what runs exist, then each run's `RUN.md`.

`Subject` is the run's one-line summary from its `RUN.md` title block, trimmed to fit.

| Slug | Mode | Subject | Opened | Owner |
|---|---|---|---|---|
| audit-truthfulqa | audit | TruthfulQA fitness for model selection | 2026-09-06 | |
| measure-truthfulqa | measure | Item-level psychometrics for audit-truthfulqa | 2026-09-06 | |
| audit-gpqa | audit | GPQA fitness for model selection | 2026-09-07 | |
| measure-gpqa | measure | Item-level psychometrics for audit-gpqa | 2026-09-07 | |
| design-failure-mode-id | design | Can a model identify ECBD failure modes from benchmark docs | 2026-09-07 | |
