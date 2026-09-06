"""Item-level analysis of OpenEval benchmark data.

Classical Test Theory plus two checks aimed at model-selection use:
whether a ranking replicates across halves of the item set, and whether
low-informativeness models are flattered by a truthfulness-only score.

First written for `audit-truthfulqa` stage 5; see that run's 05_evidence.md.
Prototype of `03-measure/` -- see docs/decisions/2026-09-06-openeval-integration.md.

Data: HF Open-Eval-Commons/OpenEval, CC-BY-NC-4.0 (non-commercial).

Scope, and it matters: these are OpenEval's `bleurt-20` labels, NOT the
originating paper's human evaluation. Results describe the instrument as
practised and ingested, never as designed. Say so in any worksheet citing this.

Usage:  python _tools/item_analysis.py <split>        e.g. truthfulqa
"""
import sys, urllib.request
from pathlib import Path

import numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr

SEED, MIN_ITEMS, COVERAGE = 20260906, 700, 0.8
URL = ("https://huggingface.co/api/datasets/Open-Eval-Commons/OpenEval"
       "/parquet/response/{split}/0.parquet")
CACHE = Path(__file__).resolve().parent / ".cache"


def fetch(split):
    """Download the split's response parquet if not already cached."""
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / f"{split}_response.parquet"
    if not dest.exists():
        print(f"downloading {split} ...", file=sys.stderr)
        urllib.request.urlretrieve(URL.format(split=split), dest)
    return dest


def load(path):
    d = pd.read_parquet(path, columns=["response_id", "model", "scores"])
    rows = []
    for rid, mo, sc in zip(d.response_id, d.model, d.scores):
        try:
            met = sc["metric"][0]
            ea = met["extra_artifacts"]
            a = dict(zip(list(ea["type"]), list(ea["content"])))
        except Exception:
            met, a = {"name": None}, {}
        rows.append(("_".join(rid.split("_")[:3]), mo["name"], met["name"],
                     a.get("label"), a.get("informative")))
    df = pd.DataFrame(rows, columns=["item_id", "model", "metric", "label", "informative"])
    b = (df[df.metric == "bleurt-20"].dropna(subset=["label"])
           .drop_duplicates(subset=["item_id", "model"]).copy())
    b["truthful"] = (b.label == "truthful").astype(int)
    b["informative"] = (b.informative == "true").astype(int)
    cov = b.groupby("model").size()
    return b[b.model.isin(cov[cov >= MIN_ITEMS].index)]

def matrix(m):
    piv = m.pivot_table(index="model", columns="item_id", values="truthful")
    piv = piv.dropna(axis=1, thresh=int(COVERAGE * piv.shape[0]))
    return piv.apply(lambda c: c.fillna(c.mean()))

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
        perm = rng.permutation(cols)
        ra, rb = piv[perm[:k // 2]].mean(axis=1), piv[perm[k // 2:]].mean(axis=1)
        rhos.append(spearmanr(ra, rb).statistic)
        i, j = rng.choice(len(piv), 2, replace=False)
        swaps.append(np.sign(ra.iloc[i] - ra.iloc[j]) != np.sign(rb.iloc[i] - rb.iloc[j]))
    return np.mean(rhos), np.mean(swaps)

def abstention(m):
    a = m.groupby("model").agg(truthful=("truthful", "mean"),
                               informative=("informative", "mean"))
    a["both"] = m.assign(b=m.truthful * m.informative).groupby("model").b.mean()
    a["penalty"] = a.both.rank(ascending=False) - a.truthful.rank(ascending=False)
    return a, spearmanr(a.informative, a.penalty)

if __name__ == "__main__":
    split = sys.argv[1] if len(sys.argv) > 1 else "truthfulqa"
    m = load(fetch(split))
    piv = matrix(m)
    diff, disc, kr20 = ctt(piv)
    rho, swap = stability(piv)
    agg, (r_abst, p_abst) = abstention(m)
    sc = piv.mean(axis=1)
    se = np.sqrt(sc * (1 - sc) / piv.shape[1]).mean()

    print(f"split={split}  items={piv.shape[1]}  models={piv.shape[0]}")
    print(f"KR-20={kr20:.3f}")
    print(f"discrimination<=0: {100*(disc<=0).mean():.1f}%  <0.1: {100*(disc<0.1).mean():.1f}%")
    print(f"split-half rank rho={rho:.3f}  pair swap rate={100*swap:.1f}%")
    print(f"per-model SE={100*se:.1f}pts  separating gap={100*2*1.96*se:.1f}pts")
    print(f"abstention: corr(informativeness, rank penalty)={r_abst:.3f} p={p_abst:.2g}")
