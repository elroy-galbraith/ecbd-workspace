---
date: 2026-09-06
status: approved, implementation deferred
decision: add a third pipeline `03-measure/` for OpenEval emit + consume + psychometrics
---

# Integrating OpenEval

## What OpenEval is

A standardized item-level data release schema and a public archive — not an eval harness.

Jiang, Zhang, Zhu, Bai, Truong, Yi, Koyejo, Xie & Xiao (2026), *AI Evaluation Should Require Standardized Item-Level Data Releases*, [arXiv:2604.03244](https://arxiv.org/abs/2604.03244). Published as v1 under the title *Position: Science of AI Evaluation Requires Item-level Benchmark Data*.

- Archive: [huggingface.co/datasets/human-centered-eval/OpenEval](https://huggingface.co/datasets/human-centered-eval/OpenEval) — 158,043 items, 10.75M responses, 28 benchmarks, ~70 models per benchmark. Tables: `bench`, `item`, `response`. Parquet.
- Tooling and schema: [github.com/open-eval/OpenEval](https://github.com/open-eval/OpenEval) — `item_schema.json`, `validator.py`.
- Site: [open-eval.com](http://open-eval.com/)
- **Licence: CC-BY-NC-4.0.** Non-commercial.

Schema nests: item (`item_id`, `benchmark_id`, `item_content`, `item_adaptation`) → responses (`response_id`, `response_content`) → model (`model_name`, `model_version`, `model_adaptation`) and scores (`metric_name`, `metric_value`, `extra_artifacts`).

## Why it belongs here

ECBD is design-time: argue that the instrument is valid. OpenEval is release-time: publish the data that lets anyone check. They are two halves of one problem, and the same people are behind both — Ziang Xiao co-authored both papers, and Susu Zhang, an OpenEval author, is thanked in ECBD's acknowledgements.

The join matters because this workspace's most-cited finding is failure mode 9, *validity evidence absent entirely*. Item-level data is what makes the missing evidence cheap: Classical Test Theory gives item difficulty and discrimination, Item Factor Analysis shows whether a benchmark measures one coherent construct or construct-irrelevant variance. Both are `empirical-direct` under `_shared/validity-evidence.md` — the top of the strength scale.

Neither paper cites the other. The join is ours to make.

## Decision

**Approach 2: a third pipeline, `03-measure/`.**

It takes either a built eval from a design run or archive data for an audited benchmark, produces or ingests OpenEval-conformant records, validates them against the schema, computes CTT and IFA, and writes results back into the originating run's validity register.

Rejected alternatives:

- **Extend the existing stages in place.** Cheapest, but `08_build` would claim to emit records containing responses it has no way to obtain, and both lines would grow divergent half-copies of the analysis instructions — the duplication that already forced `_shared/audit-method.md` out of the audit routing file.
- **New terminal stages on each line.** Honest about sequencing but duplicates near-identical contracts and the Python surface across two pipelines. The analysis is the same arithmetic over the same schema either way.

## What forced a third pipeline

The design line ends at a *runnable* eval; it never runs one. OpenEval records need `response_content` and `scores`, and CTT and IFA need a response matrix spanning many models. Measuring is a different job from designing, and it did not previously exist here.

## Deferred, deliberately

Implementation waits until one real run has gone through an existing line. The method's own guardrail is to build structure for work that is actually repeating; a third pipeline for a loop nobody has closed once is the kind of thing that ossifies wrong.

## Status after the first run

`audit-truthfulqa` ran the consume path end to end and answered all five questions below. The working prototype is `_tools/item_analysis.py`; the evidence it produced is in that run's `05_evidence.md`. Read both before building `03-measure/`.

## Open questions the first run should answer

1. **Where do capabilities live?** OpenEval has no field for them. ECBD's spine is that every item targets named capabilities and evidence traces back to them. Candidates: `item_adaptation`, `extra_artifacts`, or a documented local extension. The run should show which survives contact with real records.
2. **Does the non-commercial licence bind us?** CC-BY-NC-4.0 on archive data may rule out the consume path for commercial product evals. Establish this before building on it.
3. **How much archive data is enough?** CTT and IFA need many models per item. Find the real floor rather than assuming.
4. **Does an audit actually want the analysis inline, or as a cited artefact?** Determines whether `03-measure/` is a detour from the audit line or a separate run that links back.
5. **What does the code surface cost?** This workspace has no dependencies today. Establish what Python for CTT and factor analysis actually drags in.

## Consequence to accept

Adding code changes what this workspace is: dependencies, a test burden, and a chance of environment drift where there is currently none. Judged worth it, but it is a change in kind.

## Releasing is not a pipeline step

The paper is candid that item-level release worsens contamination risk and argues the trade is worth it. That judgement is made per benchmark by a person. `03-measure/` should produce a release-ready bundle and stop; uploading stays an explicit human act.
