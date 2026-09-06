# The OpenEval schema

**The only record format this workspace accepts.** There is no second shape and no translation step — a decision taken on 2026-09-07 and recorded in `docs/decisions/`. One home for these field definitions; stage contracts cite them and never restate them.

**Authority:** [`item_schema.json`](https://github.com/open-eval/OpenEval/blob/master/item_schema.json) on the `master` branch of `open-eval/OpenEval`, checked 2026-09-06 against live records in `Open-Eval-Commons/OpenEval`. Where this file and that one disagree, that one wins — re-read it before a measure run.

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
| `ecbd_worksheet` | path to the worksheet justifying this item. Not emitted by `validate.py` today — add it by hand where a record will be published |

Declared in `02_validate.md` of the measure run that writes them, so a later reader knows the tags are a local convention rather than part of the standard.

## The fields that matter most, and why

**`item_adaptation.request_input` — what the model *actually* received.** Not the template, the rendered result. This is the field that makes a record auditable: it is the only place the adaptation module's Q9 answer becomes checkable after the fact. A record without it is a score with no provenance.

**`model_adaptation.generation_parameters` — all five required.** Temperature, sampling, top-k, top-p, max tokens. ECBD failure mode 6 is adaptation left unprescribed; this schema refuses to let you omit it.

**`scores[].metric.models` — the judge.** Where an LLM judge produced the score, it is named here. A score whose judge is unrecorded cannot be re-validated when the judge changes.

## Licence

Data in the archive is **CC-BY-NC-4.0** — non-commercial. This constrains the *consume* path for commercial work and is unresolved; see `docs/decisions/2026-09-06-openeval-integration.md`. It does not constrain records you generate yourself and choose not to publish.

## Getting your results into this shape

This workspace does not run evals. `01-design/` ends at a runnable build; something else executes it and hands back OpenEval records.

Most harnesses emit one row per response, and OpenEval nests responses inside items. Bridging that is an adapter's job, and the adapter is yours to write — we deliberately do not ship a second documented format to translate from, because two vocabularies for the same fields is how a schema rots. `open-eval/OpenEval` ships `helm_converter.py` as a worked example.

Two things harnesses commonly drop, both of which the adapter must recover:

- **The rendered prompt.** Many log the template, not the result. `lm-evaluation-harness` writes rendered inputs under `--log_samples`.
- **Per-sample rows.** Default outputs are usually aggregated; per-sample logging is generally a flag.

### Three rules that decide whether the analysis is worth anything

**Record what happened, not what was specified.** `item_adaptation.request_input` and `generation_parameters` must reflect the actual call. If a retry used different parameters, record the ones used. Every finding about adaptation depends on this being true.

**One response per response, never pre-aggregated.** A mean is not ingestible. The whole argument for `03-measure/` is that aggregate scores conceal structure — `audit-truthfulqa` found no adjacent pair in a 149-model ranking to be distinguishable, and that is invisible from means.

**More models than you think.** Discrimination and ranking stability need a matrix across many models. `audit-truthfulqa` used 149. Below roughly 20 models, difficulty and per-item summaries are meaningful while discrimination and stability are not; below 40, stability is not. `_tools/validate.py` says which statistics your matrix supports before stage 3 gets there.

### Checking records before analysing them

```bash
python _tools/validate.py records.jsonl        # local records
python _tools/validate.py --split truthfulqa   # an archive split
```

Reports structural problems and, more usefully, coverage of the fields the analysis depends on. A field the schema marks optional and your harness leaves empty is valid OpenEval and still sinks a finding.

For submission-grade validation before releasing to the archive, use `validator.py` upstream. This tool does not reimplement it.

## Tooling in the upstream repo

`open-eval/OpenEval` (`master`) ships `validator.py`, which checks a submission against the schema and reports field violations, and `helm_converter.py`, a worked example of converting an existing harness's output. Read both before extending `_tools/validate.py`; do not reimplement what the validator already does.
