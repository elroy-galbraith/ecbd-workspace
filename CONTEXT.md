# The workspace in one screen

Two pipelines over one framework. Both walk the same twenty questions ([_shared/worksheet-questions.md](_shared/worksheet-questions.md)); they differ in what the answers are *for*.

```
                      _shared/  (framework, questions, glossary, rules)
                          |
        +-----------------+-----------------+
        |                                   |
   01-design/                          02-audit/
   decisions you are making       decisions someone already made
   8 stages                             6 stages
        |                                   |
        +-----------------+-----------------+
                          |
                    worksheets/<run-slug>/
                    one record per run
```

## The two lines

**`01-design/` — you are deciding.** Eight stages: one per ECBD boundary, plus a validity synthesis and a build step. Fine-grained on purpose, because each stage constrains everything downstream and correction is cheapest early — a capability definition fixed at stage 2 costs a conversation; the same fix after items are written costs the item pool.

**`02-audit/` — you are reading.** Six stages. Coarser on purpose: the decisions are already fixed and recoverable only from documentation, so gates are about interpretation rather than choice. Content, adaptation and assembly are documented thinly and read together, so they share one stage.

Both lines write into the same record shape, so an eval designed here can be audited here later without translation.

## Where the product lives

Stages hold contracts and references only. **All run artefacts live in `worksheets/<run-slug>/`**, created at the first stage by copying a template. Two runs never collide, and a run folder read top to bottom is the complete worksheet.

## The one piece of code

`_tools/` holds analysis that computes validity evidence from item-level benchmark data. It is factory, not product: stable across runs, cited by worksheets, never edited during one. It arrived from a real run rather than by design, and it is the prototype of a third pipeline recorded in `docs/decisions/`.

## Status is derivable

`RUN.md` is the **only** file recording a run's state: `status:` in its frontmatter for the lifecycle, the stage table and loop-back table in its body for how far the run got and where it has been. To report status: read `worksheets/_index/log.md` for what runs exist, then each run's `RUN.md` for how far it got. The log carries no status column, deliberately.

The five lifecycle values and who sets each are defined once, in `worksheets/CONTEXT.md`.

## Naming

Run slugs are kebab-case, prefixed by mode: `design-medical-summary-faithfulness`, `audit-mmlu`. Each pipeline's first stage restates this, so a mid-run agent never needs this file. The slug is the folder name, the log id, and the record's identity everywhere.

## What this workspace does not do

ECBD assesses **validity** — whether results can be interpreted as intended. It does not cover everything that makes a benchmark sound; the out-of-scope list is in `_shared/ecbd-framework.md` under "What this is not". Those are real requirements and they are out of scope here; note them under "outside ECBD" in the run's final file — `07_validity-register.md` for a design run, `06_findings.md` for an audit rather than letting a clean worksheet imply a sound benchmark.
