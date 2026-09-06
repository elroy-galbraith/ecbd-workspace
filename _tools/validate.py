"""Validate OpenEval records, and report what an analysis can do with them.

Schema: _shared/openeval-schema.md. This workspace accepts OpenEval records and
nothing else -- there is no second format and no translation step.

    python _tools/validate.py records.jsonl      # local records
    python _tools/validate.py --split truthfulqa # an archive split

Two checks, and they answer different questions:

  Is this valid OpenEval?      -> validator.py in open-eval/OpenEval. Use it
                                  before submitting anything to the archive.
                                  Not reimplemented here.
  Can the analysis use it?     -> this tool. Structural sanity, plus coverage of
                                  the fields _tools/item_analysis.py depends on.

The second is the one that bites. A field the schema marks optional and the
archive leaves empty is perfectly valid and still sinks a finding -- an absent
item_adaptation.request_input means every claim about adaptation is unsupported.

Thresholds are shared with item_analysis.py so stage 2 and stage 3 agree.
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path

MIN_MODELS_DISCRIM, MIN_MODELS_STABILITY, MIN_ITEMS_GAP = 20, 40, 100

ITEM_REQUIRED = ["item_id", "item_content", "responses"]
RESP_REQUIRED = ["response_id", "model", "item_adaptation", "response_content", "scores"]
# Fields the analysis needs. Optional in the schema; load-bearing for us.
ANALYSIS_FIELDS = [
    "item_adaptation.request_input",
    "model.model_adaptation.generation_parameters",
    "scores[].metric.name",
    "scores[].value",
]


def report(n_items, n_models, n_resp, caps, metrics=None, coverage=None):
    print(f"items={n_items} models={n_models} responses={n_resp}")
    if metrics:
        print("metrics present:", dict(metrics))
    print(f"capabilities tagged: {dict(caps) or 'NONE - traceability check will not run'}")
    if coverage and n_resp:
        print()
        print(f"field coverage (of {n_resp} responses):")
        for f in coverage:
            c = coverage[f]
            print(f"  {100*c/n_resp:5.1f}%  {f}" + ("" if c else "   <- absent"))
    print()
    print("statistics this matrix supports:")
    for name, ok, why in [
        ("item difficulty", n_items > 0, "needs items"),
        ("item discrimination", n_models >= MIN_MODELS_DISCRIM,
         f"needs >= {MIN_MODELS_DISCRIM} models, have {n_models}"),
        ("KR-20 reliability", n_models >= MIN_MODELS_DISCRIM,
         f"needs >= {MIN_MODELS_DISCRIM} models, have {n_models}"),
        ("ranking stability", n_models >= MIN_MODELS_STABILITY,
         f"needs >= {MIN_MODELS_STABILITY} models, have {n_models}"),
        ("separating gap", n_items >= MIN_ITEMS_GAP,
         f"needs >= {MIN_ITEMS_GAP} items, have {n_items}"),
    ]:
        print(f"  {'yes' if ok else 'NO '}  {name}" + ("" if ok else f"  ({why})"))


def validate_file(path):
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"{path}: no such file. For an archive split use "
                         f"--split {path} instead.")
    problems, missing, cover = [], Counter(), Counter()
    items, models, metrics, caps = set(), set(), Counter(), Counter()
    n_resp = 0
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            it = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path}:{n}: invalid JSON: {e}")
        if "responses" not in it or "item_content" not in it:
            raise SystemExit(
                f"{path}:{n}: not an OpenEval item record. This workspace accepts "
                "OpenEval records only -- see _shared/openeval-schema.md. If your "
                "harness emits rows, write an adapter that nests them.")
        for f in ITEM_REQUIRED:
            if not it.get(f):
                missing[f] += 1
        items.add(it.get("item_id"))
        for r in it.get("responses", []):
            n_resp += 1
            for f in RESP_REQUIRED:
                if not r.get(f):
                    missing[f"responses[].{f}"] += 1
            models.add((r.get("model") or {}).get("name"))
            if (r.get("item_adaptation") or {}).get("request_input"):
                cover["item_adaptation.request_input"] += 1
            if ((r.get("model") or {}).get("model_adaptation") or {}).get(
                    "generation_parameters"):
                cover["model.model_adaptation.generation_parameters"] += 1
            for s in r.get("scores") or []:
                m = s.get("metric") or {}
                if m.get("name"):
                    cover["scores[].metric.name"] += 1
                    metrics[m["name"]] += 1
                if s.get("value") is not None:
                    cover["scores[].value"] += 1
                for a in m.get("extra_artifacts") or []:
                    if a.get("type") == "ecbd_capability":
                        caps[a.get("content")] += 1
    for f, c in sorted(missing.items()):
        problems.append(f"{c} records missing {f}")
    report(len(items), len(models), n_resp, caps, metrics,
           {f: cover.get(f, 0) for f in ANALYSIS_FIELDS})
    return problems


def validate_split(split):
    """Archive splits validated on ingest; report analysis-field coverage."""
    from item_analysis import read_split

    d = read_split(split)
    n = len(d)
    items = {"_".join(r.split("_")[:3]) for r in d.response_id}
    models = {m["name"] for m in d.model}
    cover, metrics, caps = Counter(), Counter(), Counter()
    for mo, ia, sc in zip(d.model, d.get("item_adaptation", [None] * n), d.scores):
        try:
            met = sc["metric"][0]
            metrics[met["name"]] += 1
            cover["scores[].metric.name"] += 1
            ea = met["extra_artifacts"]
            for k, v in zip(list(ea["type"]), list(ea["content"])):
                cover[f"extra_artifacts.{k}"] += 1
                if k == "ecbd_capability":
                    caps[v] += 1
        except Exception:
            pass
        if (mo.get("model_adaptation") or {}).get("generation_parameters"):
            cover["model.model_adaptation.generation_parameters"] += 1
        if ia is not None and len(ia.get("request_input", []) or []):
            cover["item_adaptation.request_input"] += 1
    fields = ANALYSIS_FIELDS[:2] + ["scores[].metric.name",
                                    "extra_artifacts.label",
                                    "extra_artifacts.informative",
                                    "extra_artifacts.ecbd_capability"]
    report(len(items), len(models), n, caps, metrics,
           {f: cover.get(f, 0) for f in fields})
    print()
    print("note: archive records were validated against the schema on ingest. "
          "This reports coverage of the fields the analysis needs.", file=sys.stderr)
    return []


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("records", nargs="?", help="path to OpenEval records (JSONL)")
    src.add_argument("--split", help="OpenEval archive split, e.g. truthfulqa")
    a = ap.parse_args()

    problems = validate_split(a.split) if a.split else validate_file(a.records)
    if problems:
        print("\nblocking problems:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
