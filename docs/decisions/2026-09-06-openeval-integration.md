---
date: 2026-09-06
status: implemented
decision: add a third pipeline `03-measure/` for OpenEval emit + consume + psychometrics
---

# Integrating OpenEval

## What OpenEval is

A standardized item-level data release schema and a public archive — not an eval harness.

Jiang, Zhang, Zhu, Bai, Truong, Yi, Koyejo, Xie & Xiao (2026), *AI Evaluation Should Require Standardized Item-Level Data Releases*, [arXiv:2604.03244](https://arxiv.org/abs/2604.03244). Published as v1 under the title *Position: Science of AI Evaluation Requires Item-level Benchmark Data*.

- Archive: [huggingface.co/datasets/Open-Eval-Commons/OpenEval](https://huggingface.co/datasets/Open-Eval-Commons/OpenEval) — 158,043 items, 10.75M responses, 28 benchmarks, ~70 models per benchmark. Tables: `bench`, `item`, `response`. Parquet. (`human-centered-eval/OpenEval`, cited in some sources, redirects here.)
- Tooling and schema: [github.com/open-eval/OpenEval](https://github.com/open-eval/OpenEval) — `item_schema.json`, `validator.py`.
- Site: [open-eval.com](http://open-eval.com/)
- **Licence: CC-BY-NC-4.0.** Non-commercial.

The schema is recorded once, in `_shared/openeval-schema.md`, from the live records rather than the paper's appendix — the two disagree about where `item_adaptation` sits, and the live schema wins.

## Why it belongs here

ECBD is design-time: argue that the instrument is valid. OpenEval is release-time: publish the data that lets anyone check. They are two halves of one problem, and the same people are behind both — Ziang Xiao co-authored both papers, and Susu Zhang, an OpenEval author, is thanked in ECBD's acknowledgements.

The join matters because this workspace's most-cited finding is failure mode 9, *validity evidence absent entirely*. Item-level data is what makes the missing evidence cheap: Classical Test Theory gives item difficulty and discrimination, and Item Factor Analysis would show whether a benchmark measures one coherent construct or construct-irrelevant variance. Both are `empirical-direct` under `_shared/validity-evidence.md` — the top of the strength scale.

**Only CTT was built.** `_tools/item_analysis.py` implements difficulty, discrimination, KR-20, ranking stability and a second-construct check. Item Factor Analysis is not implemented and is not claimed anywhere in the pipeline. It remains the obvious next addition.

Neither paper cites the other. The join is ours to make.

## Decision

**Approach 2: a third pipeline, `03-measure/`.**

It takes either a built eval from a design run or archive data for an audited benchmark, produces or ingests OpenEval-conformant records, validates them against the schema, computes psychometrics, and writes results back into the originating run's validity register.

Rejected alternatives:

- **Extend the existing stages in place.** Cheapest, but `08_build` would claim to emit records containing responses it has no way to obtain, and both lines would grow divergent half-copies of the analysis instructions — the duplication that already forced `_shared/audit-method.md` out of the audit routing file.
- **New terminal stages on each line.** Honest about sequencing but duplicates near-identical contracts and the Python surface across two pipelines. The analysis is the same arithmetic over the same schema either way.

## What forced a third pipeline

The design line ends at a *runnable* eval; it never runs one. OpenEval records need `response_content` and `scores`, and CTT and IFA need a response matrix spanning many models. Measuring is a different job from designing, and it did not previously exist here.

## Deferred, deliberately

Implementation waits until one real run has gone through an existing line. The method's own guardrail is to build structure for work that is actually repeating; a third pipeline for a loop nobody has closed once is the kind of thing that ossifies wrong.

## Implemented

`03-measure/` exists: four stages, `_shared/openeval-schema.md`, `_shared/results-contract.md`, `_tools/conform.py`, and `_templates/measure-run/`.

**Neither direction has been run through the stages.** `audit-truthfulqa` invoked the analysis inline from audit stage 5, before this pipeline existed; the log holds no `measure-` row. The contracts are derived from work that succeeded, which is not the same as work that has been repeated.

One scope decision was taken during the build and is not in the original approval: **the pipeline does not run evals.** It ingests results through a documented contract, so teams keep their own harness. Execution means credentials, spend, rate limits, retries and caching — and two well-maintained harnesses already exist. The consequence is that the emit path cannot be proven until `01-design/` produces a build and something else runs it.

## Status after the first run

`audit-truthfulqa` exercised the consume path's substance inline and answered three of the five questions below. Question 2 (does the CC-BY-NC licence bind commercial use?) is **still unresolved**. Question 4 (inline or cited artefact?) was answered *both* ways and needs a rule — see below. The working prototype is `_tools/item_analysis.py`; the evidence it produced is in that run's `05_evidence.md`. Read both before building `03-measure/`.

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
