---
date: 2026-09-07
status: implemented
decision: accept OpenEval records as the only format; one home for the analysis
supersedes: the results contract introduced 2026-09-06
---

# OpenEval only

## Decision

**One record format: OpenEval.** `_shared/results-contract.md` is deleted. `_tools/conform.py` is gone; `_tools/validate.py` replaces it. Nothing translates between shapes, because there is no second shape.

**One home for the analysis.** `02-audit/05_evidence` no longer computes psychometrics. Where a benchmark has archive coverage it records that fact, names the split, states which SUPPORT questions a measure run could answer, and stops. `03-measure/` owns the computation.

## Why the second format had to go

The results contract did not just define another shape. It defined another **vocabulary** for the same fields:

| Results contract | OpenEval |
|---|---|
| `item_input` | `item_content.input` |
| `model_name` | `model.name` |
| `request_input` | `item_adaptation.request_input` |
| `generation_parameters` | `model_adaptation.generation_parameters` |

Two names for one fact, with a translation layer between them. That is precisely the drift `_shared/CONTEXT.md` exists to prevent, introduced three days after the rule was written down.

The "not an industry standard" objection is real and cuts the other way. OpenEval is a 2026 proposal carried by 28 benchmarks and one public archive. The bespoke contract was carried by nobody. Choosing between a young standard and a private one, the young standard wins on every axis: a published schema, an upstream `validator.py` this workspace was reimplementing badly, a worked converter example, and records that are releasable by construction rather than after a translation step.

## The cost, accepted

Nested records mean a runner buffers all responses for an item before writing. Fine at 817 items; mildly annoying for long agent evals where streaming append is easier.

More importantly, **the adapter is now the user's problem.** Most harnesses emit rows. Nesting them is real work that this workspace no longer does for you. `open-eval/OpenEval` ships `helm_converter.py` as a worked example, and `_shared/openeval-schema.md` names the two things harnesses commonly drop.

Quality-of-life adapters may be added later. They would be conveniences that produce OpenEval, never a second accepted format.

## Why the audit stopped computing

`02-audit/05_evidence` ran the analysis inline; `03-measure/` ran the same analysis as a pipeline. Both shipped. `measure-truthfulqa` therefore recomputed what the audit already held, and its only original contribution was noticing the audit had not written its own numbers into its own ledger.

Computing psychometrics is a different job from reading documentation: different inputs, different failure modes, its own gates. That was the argument for creating the pipeline. Inline was expedient while the pipeline did not exist; it does now.

This closes open question 4 of `2026-09-06-openeval-integration.md`, which claimed to be answered and was not.

## Consequences

- `03-measure/02_conform` is renamed `02_validate`. With nothing to translate, the stage checks that records are sound OpenEval and that the fields the analysis needs are populated — a distinction the tool now reports directly, since a field the schema marks optional can be valid and still sink a finding.
- `01-design/08_build` targets OpenEval directly. A build whose output cannot be ingested can never have its validity gaps closed by measurement.
- `audit-truthfulqa` stage 5 was written under the old rule and computed inline. It stands as a record of what was done, with a loop-back noting the rule changed under it.

## What is not decided

Whether `validate.py` should eventually vendor or call upstream `validator.py` for submission-grade checks. Today it does neither — it checks what the analysis needs and points at upstream for the rest. Revisit when a release actually goes out.
