# The results contract

What a runner must emit for `03-measure/` to ingest it. This is the seam that lets you keep your own harness — lm-evaluation-harness, Inspect, promptfoo, or something internal.

**This workspace does not run evals.** `01-design/` ends at a runnable build; something else executes it. That was a deliberate scope decision: running models means credentials, spend, rate limits, retries and caching, and every team already has a tool for it. See `docs/decisions/2026-09-06-openeval-integration.md`.

## The format

JSONL, one object per **model response to one item**. Long and thin, not nested — nesting happens at conform time.

```json
{
  "item_id": "faith-042",
  "item_input": "Summarise the following support ticket...",
  "item_references": ["The customer's refund was processed on the 3rd."],
  "capabilities": ["faithfulness", "completeness"],
  "model_name": "claude-sonnet-4.5",
  "model_version": "20250929",
  "request_input": "You are a support summariser.\n\nTicket: ...",
  "system_instruction": "You are a support summariser.",
  "generation_parameters": {"temperature": 0.0, "do_sample": false,
                            "top_k": null, "top_p": null, "max_tokens": 1024},
  "response_content": "The customer requested a refund, which was processed...",
  "scores": [
    {"metric": "faithfulness_judge", "value": 1.0,
     "judge_models": ["claude-sonnet-4.5"],
     "extra": {"rationale": "every claim is supported by the ticket"}}
  ]
}
```

## Required fields

| Field | Why it is required |
|---|---|
| `item_id` | Stable across models and runs. Without it there is no response matrix, and no item analysis is possible. |
| `item_input` | The item as designed. |
| `model_name` | Identity of the object of evaluation. |
| `request_input` | **What the model actually received, fully rendered.** Not the template. |
| `generation_parameters` | All five keys. Nulls are fine; absence is not. |
| `response_content` | The captured response. |
| `scores` | At least one `{metric, value}`. |

## Optional but strongly advised

| Field | Why |
|---|---|
| `capabilities` | The ECBD tags. Omit them and the analysis can compute reliability but cannot check that evidence traces back to what the eval claims to measure — which is the whole point of pairing this with ECBD. |
| `item_references` | Needed to re-score later under a different metric. |
| `model_version` | Model names are reused across revisions. |
| `judge_models` | Where an LLM judge produced the score. A score whose judge is unrecorded cannot be re-validated when the judge changes. |
| `extra` | Free-form. Becomes `extra_artifacts`. Put a second construct here — informativeness, abstention, refusal — and the analysis can test trade-offs between them. |

## Three rules that decide whether the analysis is worth anything

**Record what happened, not what was specified.** `request_input` and `generation_parameters` must reflect the actual call. If a retry used different parameters, emit the ones used. Every finding about adaptation depends on this being true.

**One row per response, never pre-aggregated.** A mean is not ingestible. The entire argument for this pipeline is that aggregate scores conceal the structure — `audit-truthfulqa` found no adjacent pair in a 145-model ranking to be distinguishable, and that is invisible from means.

**More models than you think.** Item discrimination and ranking stability need a response matrix across many models. `audit-truthfulqa` used 145 and filtered out everything with under 700 items answered. Below roughly 20 models, expect difficulty and per-item summaries to be meaningful while discrimination and stability are not. Stage 3 says which statistics its matrix can support.

## Wiring an existing harness

Most harnesses can emit this with a small post-processing step over their own output. Two things they commonly drop, both of which must be recovered:

- **The rendered prompt.** Many log the template, not the result. `lm-evaluation-harness` writes rendered inputs when run with `--log_samples`.
- **Per-sample rows.** Default outputs are usually aggregated; per-sample logging is generally a flag.

`open-eval/OpenEval` ships `helm_converter.py` as a worked example of converting one harness's output. Read it before writing an adapter.

## Checking a file before ingesting

```bash
python _tools/conform.py --check results.jsonl
```

Reports missing required fields, unstable ids, pre-aggregated rows, and the number of models and items — so you know which statistics stage 3 will be able to compute before you get there.
