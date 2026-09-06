# The OpenEval schema

The record format `03-measure/` reads and writes. One home for these field definitions; stage contracts cite them and never restate them.

**Authority:** [`item_schema.json`](https://github.com/open-eval/OpenEval/blob/master/item_schema.json) on the `master` branch of `open-eval/OpenEval`, checked 2026-09-06 against live records in `Open-Eval-Commons/OpenEval`. Where this file and that one disagree, that one wins — re-read it before a conform run.

Method paper: Jiang et al. (2026), [arXiv:2604.03244](https://arxiv.org/abs/2604.03244). **The paper's Appendix C places `item_adaptation` at the item level; the schema and the live records place it on the response.** Follow the schema.

## Shape

One item, nested, with its responses inside it:

```
item
├─ item_id                    [str | auto]
├─ item_metadata
│  ├─ ingestion_time          [str | auto]  ISO 8601
│  ├─ contributor             {name, email, affiliation}   all optional
│  └─ source
│     ├─ benchmark_name       [str | non-empty]
│     ├─ benchmark_version    [str | required]
│     ├─ paper_url            [str | optional]
│     ├─ dataset_url          [str | optional]
│     └─ benchmark_tags       [list[str] | optional]
├─ item_content
│  ├─ input                   [list[str,dict] | non-empty]   the question / dialogue / options
│  └─ references              [list[str,dict] | required]    reference answers for the metric
├─ responses[]
│  ├─ response_id             [str | auto]
│  ├─ model
│  │  ├─ name                 [str | non-empty]
│  │  ├─ size                 [str | optional]
│  │  └─ model_adaptation
│  │     ├─ system_instruction     [str | required]
│  │     ├─ generation_parameters  {temperature, do_sample, top_k, top_p, max_tokens}  all required
│  │     └─ tools[]                {type, content}
│  ├─ item_adaptation
│  │  ├─ request_input        [list[str,dict] | non-empty]   what the model ACTUALLY received
│  │  ├─ demonstrations       [list[str] | optional]
│  │  └─ external_resources[] {type, content}
│  ├─ response_content        [list[str,dict] | non-empty]
│  └─ scores[]
│     ├─ metric
│     │  ├─ name              [str | non-empty]
│     │  ├─ models            [list[str] | required]   judge models used to compute it
│     │  └─ extra_artifacts[] {type, content}
│     └─ value                [int,float,bool | non-empty]
└─ schema_version             [str | auto]
```

On HuggingFace this is flattened into three tables — `bench`, `item`, `response` — with complex fields JSON-stringified for Parquet. `item` and `response` join on the `item_id` prefix of `response_id`.

## Where ECBD capabilities live

**The schema has no field for capabilities.** ECBD's spine is that every item targets named constructs and evidence traces back to them; OpenEval does not model that.

Use `scores[].metric.extra_artifacts`, which is a free `{type, content}` list. This is not a workaround — it is how the schema is already used in practice. The TruthfulQA contributor carried a second construct there: `extra_artifacts` holds `informative` alongside `label`, which is exactly how stage 5 of `audit-truthfulqa` was able to test the abstention effect at all.

Convention for records this workspace emits:

| `type` | `content` |
|---|---|
| `ecbd_capability` | capability name, verbatim from the originating run's capability file — `02_capability.md` for a design run, `03_capability.md` for an audit |
| `ecbd_run` | the originating run slug, e.g. `design-support-faithfulness` |
| `ecbd_worksheet` | path to the worksheet justifying this item. Not emitted by `conform.py` today — add it by hand where a record will be published |

Declared in `02_conform.md` of the measure run that writes them, so a later reader knows the tags are a local convention rather than part of the standard.

## The fields that matter most, and why

**`item_adaptation.request_input` — what the model *actually* received.** Not the template, the rendered result. This is the field that makes a record auditable: it is the only place the adaptation module's Q9 answer becomes checkable after the fact. A record without it is a score with no provenance.

**`model_adaptation.generation_parameters` — all five required.** Temperature, sampling, top-k, top-p, max tokens. ECBD failure mode 6 is adaptation left unprescribed; this schema refuses to let you omit it.

**`scores[].metric.models` — the judge.** Where an LLM judge produced the score, it is named here. A score whose judge is unrecorded cannot be re-validated when the judge changes.

## Licence

Data in the archive is **CC-BY-NC-4.0** — non-commercial. This constrains the *consume* path for commercial work and is unresolved; see `docs/decisions/2026-09-06-openeval-integration.md`. It does not constrain records you generate yourself and choose not to publish.

## Tooling in the upstream repo

`open-eval/OpenEval` (`master`) ships `validator.py`, which checks a submission against the schema and reports field violations, and `helm_converter.py`, a worked example of converting an existing harness's output. Read both before extending `_tools/conform.py`; do not reimplement what the validator already does.
