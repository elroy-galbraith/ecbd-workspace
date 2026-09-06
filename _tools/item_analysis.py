"""Item-level analysis of benchmark responses.

Classical Test Theory plus two checks aimed at model-selection use: whether a
ranking replicates across halves of the item set, and whether a second construct
(informativeness, refusal) is traded against the primary score.

Reads either source, and REQUIRES you to say which -- there is no default,
because a default here silently analyses the wrong benchmark:

    python _tools/item_analysis.py --split truthfulqa          # OpenEval archive
    python _tools/item_analysis.py --records worksheets/measure-x/records/items.jsonl

Thresholds are shared with conform.py so stage 2 and stage 3 agree about what a
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
URL = ("https://huggingface.co/api/datasets/Open-Eval-Commons/OpenEval"
       "/parquet/response/{split}/0.parquet")
CACHE = Path(__file__).resolve().parent / ".cache"


# ---------------------------------------------------------------- loading

def fetch_split(split):
    """Path to the cached parquet for an archive split, downloading if needed."""
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / f"{split}_response.parquet"
    if not dest.exists():
        print(f"downloading {split} ...", file=sys.stderr)
        urllib.request.urlretrieve(URL.format(split=split), dest)
    return dest


def from_split(split, metric="bleurt-20"):
    """OpenEval archive parquet -> long frame. Downloads once, then caches."""
    d = pd.read_parquet(fetch_split(split), columns=["response_id", "model", "scores"])
    rows = []
    for rid, mo, sc in zip(d.response_id, d.model, d.scores):
        try:
            met = sc["metric"][0]
            ea = met["extra_artifacts"]
            a = dict(zip(list(ea["type"]), list(ea["content"])))
        except Exception:
            met, a = {"name": None}, {}
        rows.append(("_".join(rid.split("_")[:3]), mo["name"], met["name"],
                     a.get("label"), a.get("informative"), None))
    df = pd.DataFrame(rows, columns=["item_id", "model", "metric",
                                     "label", "second", "capability"])
    df = df[df.metric == metric].dropna(subset=["label"])
    df["score"] = (df.label == "truthful").astype(float)
    df["second_val"] = (df.second == "true").astype(float)
    return df


def from_records(path):
    """Nested OpenEval records (conform.py output) -> long frame."""
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


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--split", help="OpenEval archive split, e.g. truthfulqa")
    src.add_argument("--records", help="path to conformed items.jsonl")
    ap.add_argument("--metric", default="bleurt-20", help="archive metric to select")
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

    if n_models >= MIN_MODELS_STABILITY:
        rho, swap = stability(piv)
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
    if tr is not None:
        print("\ntraceability by capability:")
        print(tr.to_string(index=False))
    else:
        print("traceability: SKIPPED (no ecbd_capability tags in records)")


if __name__ == "__main__":
    main()
