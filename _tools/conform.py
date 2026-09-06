"""Map a results file to OpenEval-conformant records, or check one first.

Contract for the input:  _shared/results-contract.md
Target schema:           _shared/openeval-schema.md

    python _tools/conform.py --check results.jsonl     # flat rows, or conformed records
    python _tools/conform.py --split truthfulqa        # count an archive split
    python _tools/conform.py results.jsonl --out records/ \
        --benchmark my-eval --benchmark-version 1.0 --run design-my-eval

--check reports what is missing and, more usefully, which statistics the
matrix will support at stage 3 -- so you learn that before you get there.

ECBD capability tags are carried in scores[].metric.extra_artifacts as
{type: "ecbd_capability", content: <name>}. That is a local convention of
this workspace, not part of the OpenEval standard. Say so in 02_conform.md.
"""
import argparse, json, sys
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA_VERSION = "v0.1.0"
REQUIRED = ["item_id", "item_input", "model_name", "request_input",
            "generation_parameters", "response_content", "scores"]
GEN_KEYS = ["temperature", "do_sample", "top_k", "top_p", "max_tokens"]
# Below this many models, discrimination and stability are not meaningful.
MIN_MODELS_DISCRIM, MIN_MODELS_STABILITY, MIN_ITEMS_GAP = 20, 40, 100
# Thresholds are shared with item_analysis.py so stage 2 and stage 3 agree.


def count_split(split):
    """Count an archive split and report coverage of the fields analysis needs.

    Archive records were validated against the schema when the contributor
    ingested them. Re-running a schema check adds nothing. What matters here is
    whether the fields THIS analysis depends on are actually populated -- an
    optional field the schema permits to be empty is a finding for us.
    """
    import pandas as pd
    from item_analysis import fetch_split

    d = pd.read_parquet(fetch_split(split))
    n = len(d)
    items = {"_".join(r.split("_")[:3]) for r in d.response_id}
    models = {m["name"] for m in d.model}

    have = Counter()
    metrics = Counter()
    for mo, ia, sc in zip(d.model, d.get("item_adaptation", [None] * n), d.scores):
        try:
            met = sc["metric"][0]
            metrics[met["name"]] += 1
            ea = met["extra_artifacts"]
            for k in dict(zip(list(ea["type"]), list(ea["content"]))):
                have[f"extra_artifacts.{k}"] += 1
        except Exception:
            pass
        if (mo.get("model_adaptation") or {}).get("generation_parameters"):
            have["model_adaptation.generation_parameters"] += 1
        if ia is not None and len(ia.get("request_input", []) or []):
            have["item_adaptation.request_input"] += 1

    report(len(items), len(models), n, Counter())
    print()
    print("metrics present:", dict(metrics))
    print("field coverage (of %d responses):" % n)
    for f in ["item_adaptation.request_input", "model_adaptation.generation_parameters",
              "extra_artifacts.label", "extra_artifacts.informative",
              "extra_artifacts.ecbd_capability"]:
        c = have.get(f, 0)
        print(f"  {100*c/n:5.1f}%  {f}" + ("" if c else "   <- absent")) 
    return [], ["archive records were validated on ingest; this reports coverage "
                "of the fields the analysis needs, which is the check that matters here."]


def read(path):
    if not Path(path).exists():
        raise SystemExit(f"{path}: no such file. For an OpenEval archive split "
                         f"use --split {path} instead.")
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append((n, json.loads(line)))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path}:{n}: invalid JSON: {e}")
    return rows


def is_nested(rows):
    """Nested OpenEval item records, or flat contract rows?"""
    return bool(rows) and "responses" in rows[0][1] and "item_content" in rows[0][1]


NESTED_REQUIRED = ["item_id", "item_content", "responses", "schema_version"]
RESP_REQUIRED = ["response_id", "model", "item_adaptation", "response_content", "scores"]


def check_records(rows):
    """Validate already-conformed records -- the consume direction."""
    problems, notes = [], []
    missing = Counter()
    items, models, n_resp = set(), set(), 0
    for n, it in rows:
        for f in NESTED_REQUIRED:
            if f not in it or it[f] in (None, "", []):
                missing[f] += 1
        items.add(it.get("item_id"))
        for r in it.get("responses", []):
            n_resp += 1
            for f in RESP_REQUIRED:
                if f not in r or r[f] in (None, "", []):
                    missing[f"responses[].{f}"] += 1
            models.add((r.get("model") or {}).get("name"))
            if not (r.get("item_adaptation") or {}).get("request_input"):
                missing["responses[].item_adaptation.request_input"] += 1
    for f, c in missing.items():
        problems.append(f"{c} records missing {f}")
    notes.append("nested records detected; validated against the OpenEval schema. "
                 "For a submission-grade check use validator.py from open-eval/OpenEval.")
    report(len(items), len(models), n_resp, Counter())
    return problems, notes


def report(n_items, n_models, n_resp, caps):
    print(f"items={n_items} models={n_models} responses={n_resp}")
    print(f"capabilities tagged: {dict(caps) or 'NONE - traceability check will not run'}")
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


def check(rows):
    """Return (problems, notes). Problems block; notes shape expectations."""
    problems, notes = [], []
    missing = Counter()
    for n, r in rows:
        for f in REQUIRED:
            if f not in r or r[f] in (None, "", []):
                missing[f] += 1
        gp = r.get("generation_parameters")
        if isinstance(gp, dict):
            for k in GEN_KEYS:
                if k not in gp:
                    missing[f"generation_parameters.{k}"] += 1
        if r.get("request_input") and r.get("request_input") == r.get("item_input"):
            notes.append(f"line {n}: request_input equals item_input verbatim — "
                         "confirm this is the rendered prompt, not the raw item")
    for f, c in missing.items():
        problems.append(f"{c} rows missing {f}")

    pairs = Counter((r.get("item_id"), r.get("model_name")) for _, r in rows)
    dupes = [k for k, c in pairs.items() if c > 1]
    if dupes:
        notes.append(f"{len(dupes)} item/model pairs appear more than once "
                     "(repeats are fine; pre-aggregated rows are not)")

    items = {r.get("item_id") for _, r in rows}
    models = {r.get("model_name") for _, r in rows}
    per_model = Counter(r.get("model_name") for _, r in rows)
    caps = Counter(c for _, r in rows for c in (r.get("capabilities") or []))

    print(f"rows={len(rows)} items={len(items)} models={len(models)}")
    if per_model:
        print(f"coverage per model: min={min(per_model.values())} "
              f"median={sorted(per_model.values())[len(per_model)//2]} "
              f"max={max(per_model.values())}")
    print(f"capabilities tagged: {dict(caps) or 'NONE — traceability check will not run'}")

    print("\nstatistics this matrix supports:")
    n_models = len(models)
    for name, ok, why in [
        ("item difficulty", len(items) > 0, "needs items"),
        ("item discrimination", n_models >= MIN_MODELS_DISCRIM,
         f"needs >= {MIN_MODELS_DISCRIM} models, have {n_models}"),
        ("KR-20 reliability", n_models >= MIN_MODELS_DISCRIM,
         f"needs >= {MIN_MODELS_DISCRIM} models, have {n_models}"),
        ("ranking stability", n_models >= MIN_MODELS_STABILITY,
         f"needs >= {MIN_MODELS_STABILITY} models, have {n_models}"),
        ("separating gap", len(items) >= 100, f"needs >= 100 items, have {len(items)}"),
    ]:
        print(f"  {'yes' if ok else 'NO '}  {name}" + ("" if ok else f"  ({why})"))
    return problems, notes


def conform(rows, benchmark, version, run, paper=None, dataset=None):
    """Nest flat rows into OpenEval item records."""
    by_item = defaultdict(list)
    content = {}
    for _, r in rows:
        by_item[r["item_id"]].append(r)
        content.setdefault(r["item_id"], (r.get("item_input"), r.get("item_references")))

    out = []
    for item_id, rs in by_item.items():
        inp, refs = content[item_id]
        responses = []
        for i, r in enumerate(rs):
            scores = []
            for s in r["scores"]:
                extra = [{"type": k, "content": v} for k, v in (s.get("extra") or {}).items()]
                extra += [{"type": "ecbd_capability", "content": c}
                          for c in (r.get("capabilities") or [])]
                if run:
                    extra.append({"type": "ecbd_run", "content": run})
                scores.append({
                    "metric": {"name": s["metric"],
                               "models": s.get("judge_models", []),
                               "extra_artifacts": extra},
                    "value": s["value"]})
            responses.append({
                "response_id": f"{item_id}_{r['model_name']}_{i}",
                "model": {"name": r["model_name"], "size": r.get("model_version"),
                          "model_adaptation": {
                              "system_instruction": r.get("system_instruction", ""),
                              "generation_parameters": r["generation_parameters"],
                              "tools": r.get("tools", [])}},
                "item_adaptation": {
                    "request_input": [r["request_input"]],
                    "demonstrations": r.get("demonstrations", []),
                    "external_resources": r.get("external_resources", [])},
                "response_content": [r["response_content"]],
                "scores": scores})
        out.append({
            "item_id": item_id,
            "item_metadata": {"source": {"benchmark_name": benchmark,
                                         "benchmark_version": version,
                                         "paper_url": paper, "dataset_url": dataset,
                                         "benchmark_tags": []}},
            "item_content": {"input": [inp], "references": refs or []},
            "responses": responses,
            "schema_version": SCHEMA_VERSION})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("results", nargs="?", help="flat contract rows, or conformed records")
    src.add_argument("--split", help="OpenEval archive split to count, e.g. truthfulqa")
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    ap.add_argument("--out")
    ap.add_argument("--benchmark", default="unnamed")
    ap.add_argument("--benchmark-version", default="unversioned")
    ap.add_argument("--run", help="originating run slug, tagged into extra_artifacts")
    ap.add_argument("--paper-url")
    ap.add_argument("--dataset-url")
    a = ap.parse_args()

    if a.split:
        problems, notes = count_split(a.split)
        for n in notes:
            print(f"note: {n}", file=sys.stderr)
        raise SystemExit(0)

    rows = read(a.results)
    nested = is_nested(rows)
    problems, notes = (check_records(rows) if nested else check(rows))
    if nested and not a.check:
        raise SystemExit("input is already conformed; use --check to validate it")
    for n in notes:
        print(f"note: {n}", file=sys.stderr)
    if problems:
        print("\nblocking problems:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        if not a.check:
            raise SystemExit("refusing to conform an invalid results file")

    if a.check:
        raise SystemExit(1 if problems else 0)
    if not a.out:
        raise SystemExit("--out is required unless --check")

    recs = conform(rows, a.benchmark, a.benchmark_version, a.run,
                   a.paper_url, a.dataset_url)
    dest = Path(a.out)
    dest.mkdir(parents=True, exist_ok=True)
    f = dest / "items.jsonl"
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n",
                 encoding="utf-8")
    print(f"\nwrote {len(recs)} item records to {f}")


if __name__ == "__main__":
    main()
