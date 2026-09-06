# Run log

The catalog: one line per run, added when the run folder is created. It records what exists, not how far it got.

**Status is not here.** A run's state lives in its `RUN.md` and nowhere else — `status:` in the frontmatter, progress in the stage table. A status column here would be a second copy that drifts the moment someone finishes a stage without updating two files. To report status, read this table for what runs exist, then each run's `RUN.md`.

`Subject` is the run's one-line summary from its `RUN.md` title block, trimmed to fit.

| Slug | Mode | Subject | Opened | Owner |
|---|---|---|---|---|

<!-- Example rows, delete when the first real run lands:
| design-support-summary-faithfulness | design | Faithfulness of customer-support summaries | 2026-09-06 | |
| audit-mmlu | audit | MMLU for legal-research model selection | 2026-09-06 | |
-->
