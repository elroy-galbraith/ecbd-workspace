"""Item-level analysis of benchmark responses.

Classical Test Theory plus two checks aimed at model-selection use: whether a
ranking replicates across halves of the item set, and whether a second construct
(informativeness, refusal) is traded against the primary score.

Reads either source, and REQUIRES you to say which -- there is no default,
because a default here silently analyses the wrong benchmark:

    python _tools/item_analysis.py --split truthfulqa          # OpenEval archive
    python _tools/item_analysis.py --records worksheets/measure-x/records/items.jsonl

Thresholds are shared with validate.py so stage 2 and stage 3 agree about what a
matrix can support. Below them the statistic is skipped, not fudged.

Archive data is CC-BY-NC-4.0 (non-commercial). Archive labels are one scoring
path -- results describe the instrument as practised and ingested, never as
designed. Say so in any worksheet citing this.
"""
import argparse, json, sys, urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

SEED = 20260906
MIN_MODELS_DISCRIM, MIN_MODELS_STABILITY, MIN_ITEMS_GAP = 20, 40, 100
MIN_ITEMS_PER_MODEL, COVERAGE = 0.8, 0.8   # both as fractions of the item set
LIST_URL = ("https://huggingface.co/api/datasets/Open-Eval-Commons/OpenEval"
            "/parquet/{config}/{split}")
CACHE = Path(__file__).resolve().parent / ".cache"


# ---------------------------------------------------------------- loading

def fetch_split(split, config="response"):
    """Cached parquet shards for an archive split, downloading any that are missing.

    Splits are sharded. Reading only shard 0 silently analyses part of the data
    and reports it as the whole -- truthfulqa has one shard so this was invisible
    until gpqa (4 shards) and bbq (13) turned up. Always read every shard.
    """
    CACHE.mkdir(exist_ok=True)
    urls = json.loads(urllib.request.urlopen(
        LIST_URL.format(config=config, split=split)).read())
    if not urls:
        raise SystemExit(f"{split}/{config}: no parquet files found")
    paths = []
    for i, u in enumerate(urls):
        dest = CACHE / f"{split}_{config}_{i}.parquet"
        if not dest.exists():
            print(f"downloading {split}/{config} shard {i+1}/{len(urls)} ...",
                  file=sys.stderr)
            urllib.request.urlretrieve(u, dest)
        paths.append(dest)
    return paths


def read_split(split, config="response", columns=None):
    """Every shard of a split, concatenated."""
    parts = [pd.read_parquet(p, columns=columns) for p in fetch_split(split, config)]
    return pd.concat(parts, ignore_index=True)


def item_facets(split, key):
    """Map item_id -> facet value, read from the archive's item table.

    Benchmarks stash per-item metadata as JSON inside item_content.input, which
    is legal OpenEval and invisible to the schema. TruthfulQA carries
    is_adversarial and category there.
    """
    d = read_split(split, "item")
    out = {}
    for iid, content in zip(d.item_id, d.item_content):
        try:
            j = json.loads(list(content["input"])[0])
        except Exception:
            continue
        if key in j and j[key] is not None:
            out[iid] = str(j[key])
    return out


def from_split(split, metric=None):
    """OpenEval archive shards -> long frame.

    The score is scores[].value, which every benchmark carries. Earlier versions
    read TruthfulQA's extra_artifacts.label instead, which worked only for
    TruthfulQA -- gpqa scores under chain_of_thought_correctness with no
    artifacts at all. On TruthfulQA the two agree exactly (truthful<->1.0,
    untruthful<->0.0), so nothing that used the old path changed.

    metric=None selects the split's most common metric and says which.
    """
    d = read_split(split, columns=["response_id", "model", "scores"])
    rows = []
    for rid, mo, sc in zip(d.response_id, d.model, d.scores):
        try:
            met = sc["metric"][0]
            val = float(sc["value"][0])
        except Exception:
            continue
        ea = met.get("extra_artifacts") or {}
        try:
            a = dict(zip(list(ea["type"]), list(ea["content"])))
        except Exception:
            a = {}
        rows.append(("_".join(rid.split("_")[:3]), mo["name"], met["name"],
                     val, a.get("informative"), None))
    df = pd.DataFrame(rows, columns=["item_id", "model", "metric",
                                     "score", "second", "capability"])
    if df.empty:
        raise SystemExit(f"{split}: no scored responses found")
    if metric is None:
        metric = df.metric.value_counts().idxmax()
        others = df.metric.nunique() - 1
        print(f"metric: {metric}" + (f"  ({others} other metric(s) in this split, "
                                     "ignored -- name one with --metric)" if others else ""),
              file=sys.stderr)
    df = df[df.metric == metric]
    if df.empty:
        raise SystemExit(f"{split}: no responses scored under metric '{metric}'")
    df["second_val"] = (df.second == "true").astype(float)
    return df


def from_records(path):
    """Nested OpenEval records (validate.py accepts the same shape) -> long frame."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        it = json.loads(line)
        for r in it.get("responses", []):
            for s in r.get("scores", []):
                m = s["metric"]
                extra = {a["type"]: a["content"] for a in m.get("extra_artifacts", [])}
                caps = [a["content"] for a in m.get("extra_artifacts", [])
                        if a["type"] == "ecbd_capability"]
                rows.append((it["item_id"], r["model"]["name"], m["name"],
                             float(s["value"]), extra.get("informative"),
                             ";".join(caps) or None))
    if not rows:
        raise SystemExit(f"{path}: no scored responses found")
    df = pd.DataFrame(rows, columns=["item_id", "model", "metric",
                                     "score", "second", "capability"])
    df["second_val"] = (df.second == "true").astype(float)
    return df


# ---------------------------------------------------------------- analysis

def matrix(df):
    """Model x item score matrix, dropping thin models and thin items."""
    n_items = df.item_id.nunique()
    cov = df.groupby("model").item_id.nunique()
    df = df[df.model.isin(cov[cov >= MIN_ITEMS_PER_MODEL * n_items].index)]
    df = df.drop_duplicates(subset=["item_id", "model"])
    piv = df.pivot_table(index="model", columns="item_id", values="score")
    piv = piv.dropna(axis=1, thresh=int(COVERAGE * piv.shape[0]))
    return df, piv.apply(lambda c: c.fillna(c.mean()))


def ctt(piv):
    total = piv.sum(axis=1)
    diff = piv.mean(axis=0)
    disc = piv.apply(lambda c: pearsonr(c, total)[0] if c.std() > 0 else np.nan)
    k = piv.shape[1]
    kr20 = k / (k - 1) * (1 - (diff * (1 - diff)).sum() / total.var(ddof=1))
    return diff, disc, kr20


def stability(piv, draws=200):
    rng = np.random.default_rng(SEED)
    cols, k = np.array(piv.columns), piv.shape[1]
    rhos, swaps = [], []
    for _ in range(draws):
        p = rng.permutation(cols)
        ra, rb = piv[p[:k // 2]].mean(axis=1), piv[p[k // 2:]].mean(axis=1)
        rhos.append(spearmanr(ra, rb).statistic)
        i, j = rng.choice(len(piv), 2, replace=False)
        swaps.append(np.sign(ra.iloc[i] - ra.iloc[j]) != np.sign(rb.iloc[i] - rb.iloc[j]))
    return float(np.mean(rhos)), float(np.mean(swaps))


def second_construct(df):
    """Rank penalty when a second construct is required alongside the score."""
    if df.second.isna().all() or df.second_val.nunique() < 2:
        return None
    a = df.groupby("model").agg(primary=("score", "mean"), second=("second_val", "mean"))
    a["both"] = df.assign(b=df.score * df.second_val).groupby("model").b.mean()
    a["penalty"] = a.both.rank(ascending=False) - a.primary.rank(ascending=False)
    return a, spearmanr(a.second, a.penalty)


def traceability(df, piv, disc):
    """Per capability: are there tagged items, and do they discriminate?"""
    if df.capability.isna().all():
        return None
    out = []
    for cap in sorted({c for cs in df.capability.dropna() for c in cs.split(";")}):
        ids = df[df.capability.fillna("").str.contains(cap, regex=False)].item_id.unique()
        ids = [i for i in ids if i in disc.index]
        d = disc.loc[ids].dropna()
        out.append((cap, len(ids), float(d.mean()) if len(d) else float("nan"),
                    int((d <= 0).sum()) if len(d) else 0))
    return pd.DataFrame(out, columns=["capability", "items", "mean_discrimination",
                                      "non_discriminating"])


def _swap_rate(a, b):
    """Share of model pairs the two rankings order differently."""
    va, vb = a.values, b.values
    n, swaps, pairs = len(va), 0, 0
    for x in range(n):
        for y in range(x + 1, n):
            pairs += 1
            if np.sign(va[x] - va[y]) != np.sign(vb[x] - vb[y]):
                swaps += 1
    return swaps / pairs if pairs else float("nan")


def compare_facets(piv, facets, draws=40):
    """Does each facet level rank models like the rest of the benchmark does?

    Each level is compared against its complement, and against a SIZE-MATCHED
    random baseline. That matching is the whole point: two 30-item subsets
    disagree substantially from sampling noise alone, so comparing them to a
    baseline drawn from 400-item halves manufactures findings. A level only
    tells you something when it disagrees MORE than random subsets of the same
    size already do.
    """
    rng = np.random.default_rng(SEED)
    cols = np.array(piv.columns)
    tagged = [c for c in cols if c in facets]
    if len(tagged) < 60:
        return None
    rows = []
    for lvl in sorted(set(facets[c] for c in tagged)):
        inside = [c for c in tagged if facets[c] == lvl]
        outside = [c for c in tagged if facets[c] != lvl]
        if len(inside) < 25 or len(outside) < 25:
            continue
        obs = _swap_rate(piv[inside].mean(axis=1), piv[outside].mean(axis=1))
        rho = spearmanr(piv[inside].mean(axis=1), piv[outside].mean(axis=1)).statistic
        base = []
        for _ in range(draws):                      # same sizes, random membership
            perm = rng.permutation(tagged)
            base.append(_swap_rate(piv[list(perm[:len(inside)])].mean(axis=1),
                                   piv[list(perm[len(inside):])].mean(axis=1)))
        b = float(np.mean(base))
        rows.append((lvl, len(inside), rho, obs, b, obs - b))
    if not rows:
        return None
    return pd.DataFrame(rows, columns=["level", "items", "rank_rho", "swap_rate",
                                       "size_matched_baseline", "excess"]
                        ).sort_values("excess", ascending=False)


def diagnose(st):
    """Which conditions fired. Remedies live in _shared/interpreting-item-analysis.md.

    Returns (name, one-line so-what). The one-liner is a label, not the advice --
    keeping remedies out of the tool means they can be edited without touching code.
    Thresholds are classical test theory conventions; see the reference.
    """
    d, out = st, []
    if d.get("n_models", 0) < MIN_MODELS_DISCRIM:
        out.append(("thin-matrix",
                    f"only {d['n_models']} models: too few to calculate "
                    "discrimination, reliability or stability"))
    if d.get("disc_le0") is not None and (d["disc_le0"] > 0.25 or d["disc_lt1"] > 0.40):
        out.append(("low-discrimination",
                    f"{100*d['disc_lt1']:.1f}% of items hardly separate models. "
                    f"{d['n_disc_le0']} items separate none at all."))
    if d.get("kr20") is not None:
        if d["kr20"] >= 0.8 and d["disc_mean"] < 0.15:
            out.append(("reliability-from-length",
                        f"KR-20 {d['kr20']:.3f} comes from the item count, "
                        "not from item quality"))
        if d["kr20"] < 0.7:
            out.append(("unreliable-scale",
                        f"KR-20 {d['kr20']:.3f}. The items do not act as "
                        "one measure."))
    if d.get("gap") is not None and d.get("median_adj") is not None and d["median_adj"] > 0:
        if d["gap"] > 5 * d["median_adj"]:
            out.append(("unresolvable-ranking",
                        f"models need {100*d['gap']:.1f}pts to separate. The usual "
                        f"gap is {100*d['median_adj']:.2f}pts. Neighbouring ranks "
                        "are not separable."))
    if d.get("swap") is not None and (d["swap"] > 0.15 or d["rho"] < 0.85):
        out.append(("unstable-ranking",
                    f"two random halves of the items swap "
                    f"{100*d['swap']:.1f}% of model pairs"))
    if d.get("ceiling", 0) > 0.20:
        out.append(("saturated", f"{100*d['ceiling']:.1f}% of items are at ceiling"))
    if d.get("floor", 0) > 0.20:
        out.append(("floored", f"{100*d['floor']:.1f}% of items are at floor"))
    if d.get("second_r") is not None and d["second_r"] < -0.5 and d["second_p"] < 0.05:
        out.append(("gameable-primary",
                    "models that score low on the second measure rank too high "
                    "when you use the first measure alone"))
    for lvl, n, rho, swap, excess in d.get("facet_splits", []):
        out.append(("facet-disagreement",
                    f"'{lvl}' ({n} items) ranks models differently from the rest. "
                    f"It disagrees {100*excess:.1f}pts more than random groups of "
                    f"the same size do (swap {100*swap:.1f}%, rho {rho:.3f})."))
    for cap in d.get("weak_caps", []):
        out.append(("capability-unmeasured",
                    f"'{cap}': its items do not separate models. The eval claims "
                    "this capability and gives no evidence for it."))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--split", help="OpenEval archive split, e.g. truthfulqa")
    src.add_argument("--records", help="path to OpenEval records (JSONL)")
    ap.add_argument("--metric", help="archive metric to select "
                                     "(default: the split's most common)")
    ap.add_argument("--facet", help="item field to split on, e.g. is_adversarial or "
                                    "category (archive splits only)")
    a = ap.parse_args()

    df = from_split(a.split, a.metric) if a.split else from_records(a.records)
    source = a.split or a.records
    df, piv = matrix(df)
    n_models, n_items = piv.shape[0], piv.shape[1]
    print(f"source={source}  items={n_items}  models={n_models}")
    if n_models < 2 or n_items < 2:
        raise SystemExit("matrix too small to analyse")

    diff, disc, kr20 = ctt(piv)
    print(f"difficulty: mean={diff.mean():.3f} sd={diff.std():.3f} "
          f"ceiling={100*(diff>0.95).mean():.1f}% floor={100*(diff<0.05).mean():.1f}%")

    if n_models >= MIN_MODELS_DISCRIM:
        print(f"KR-20={kr20:.3f}")
        print(f"discrimination: mean={disc.mean():.3f} "
              f"<=0: {100*(disc<=0).mean():.1f}%  <0.1: {100*(disc<0.1).mean():.1f}%")
    else:
        print(f"discrimination, KR-20: SKIPPED (needs >= {MIN_MODELS_DISCRIM} "
              f"models, have {n_models})")

    baseline_rho = baseline_swap = None
    if n_models >= MIN_MODELS_STABILITY:
        rho, swap = stability(piv)
        baseline_rho, baseline_swap = rho, swap
        print(f"split-half rank rho={rho:.3f}  pair swap rate={100*swap:.1f}%")
    else:
        print(f"ranking stability: SKIPPED (needs >= {MIN_MODELS_STABILITY} "
              f"models, have {n_models})")

    if n_items >= MIN_ITEMS_GAP:
        sc = piv.mean(axis=1)
        se = float(np.sqrt(sc * (1 - sc) / n_items).mean())
        gaps = -np.diff(np.sort(sc.values)[::-1])
        print(f"per-model SE={100*se:.1f}pts  separating gap={100*2*1.96*se:.1f}pts  "
              f"median adjacent gap={100*np.median(gaps):.2f}pts")
    else:
        print(f"separating gap: SKIPPED (needs >= {MIN_ITEMS_GAP} items, have {n_items})")

    sec = second_construct(df)
    if sec:
        agg, (r, p) = sec
        print(f"second construct: corr(level, rank penalty)={r:.3f} p={p:.2g}")
    else:
        print("second construct: SKIPPED (absent, or no variation across models)")

    tr = traceability(df, piv, disc)
    weak = []
    if tr is not None:
        print("\ntraceability by capability:")
        if n_models < MIN_MODELS_DISCRIM:
            # discrimination is not estimable here; printing it would imply it is
            print(tr[["capability", "items"]].to_string(index=False))
            print(f"  (discrimination per capability needs >= {MIN_MODELS_DISCRIM} "
                  f"models, have {n_models})")
        else:
            print(tr.to_string(index=False))
            weak = [r.capability for r in tr.itertuples()
                    if (r.mean_discrimination or 0) < 0.05
                    or (r.items and r.non_discriminating / r.items > 0.5)]
    else:
        print("traceability: SKIPPED (no ecbd_capability tags in records)")

    facet_splits = []
    if a.facet:
        if not a.split:
            raise SystemExit("--facet reads the archive item table; use it with --split")
        facets = item_facets(a.split, a.facet)
        tagged = sum(1 for c in piv.columns if c in facets)
        print()
        print(f"facet '{a.facet}': {tagged}/{n_items} items carry it")
        fc = compare_facets(piv, facets)
        if fc is None:
            print("  too few tagged items to compare levels")
        else:
            print("  each level vs the rest, against a size-matched random baseline")
            print(fc.head(8).to_string(index=False))
            if len(fc) > 8:
                print(f"  ... {len(fc)-8} more levels, sorted by excess")
            facet_splits = [(fr.level, fr.items, fr.rank_rho, fr.swap_rate, fr.excess)
                            for fr in fc.itertuples() if fr.excess > 0.05]
            if not facet_splits:
                print("  no level disagrees more than random subsets of its size: "
                      "this facet explains nothing the benchmark does not already do")

    st = {"n_models": n_models, "n_items": n_items, "weak_caps": weak,
          "facet_splits": facet_splits,
          "ceiling": float((diff > 0.95).mean()), "floor": float((diff < 0.05).mean())}
    if n_models >= MIN_MODELS_DISCRIM:
        st.update(kr20=kr20, disc_mean=float(disc.mean()),
                  disc_le0=float((disc <= 0).mean()),
                  disc_lt1=float((disc < 0.1).mean()),
                  n_disc_le0=int((disc <= 0).sum()))
    if n_models >= MIN_MODELS_STABILITY:
        st.update(rho=rho, swap=swap)
    if n_items >= MIN_ITEMS_GAP:
        st.update(gap=2 * 1.96 * se, median_adj=float(np.median(gaps)))
    if sec:
        st.update(second_r=r, second_p=p)

    fired = diagnose(st)
    print()
    if fired:
        print("DIAGNOSIS  (remedies: _shared/interpreting-item-analysis.md)")
        w = max(len(n) for n, _ in fired)
        for name, why in fired:
            print(f"  {name:<{w}}  {why}")
    else:
        print("DIAGNOSIS  nothing fired: the instrument discriminates, ranks stably")
        print("           and is not obviously gameable. That says nothing about")
        print("           whether the construct is well defined -- see the worksheet.")


if __name__ == "__main__":
    main()
