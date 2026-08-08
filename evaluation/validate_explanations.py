#!/usr/bin/env python3
"""XAI validation: SHAP/impurity rank stability across seeds for T3 RCA.

No human-subject study. Writes results/xai_validation.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
PER = ROOT / "results" / "per_seed"
OUT = ROOT / "results" / "xai_validation.json"


def feature_rank_list(explanations: Sequence[Dict[str, Any]], k: int = 10) -> List[str]:
    scored: List[Tuple[float, str]] = []
    for e in explanations or []:
        feat = e.get("feature")
        if not feat:
            continue
        score = e.get("mean_abs_shap")
        if score is None:
            score = e.get("importance")
        if score is None:
            continue
        scored.append((float(score), str(feat)))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:k]]


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def rank_correlation(a: Sequence[str], b: Sequence[str]) -> Optional[float]:
    universe = list(dict.fromkeys(list(a) + list(b)))
    if len(universe) < 3:
        return None
    ra = {f: i for i, f in enumerate(a)}
    rb = {f: i for i, f in enumerate(b)}
    # missing features get worst rank
    xa = [ra.get(f, len(a) + universe.index(f)) for f in universe]
    xb = [rb.get(f, len(b) + universe.index(f)) for f in universe]
    rho, _ = spearmanr(xa, xb)
    if rho != rho:
        return None
    return float(rho)


def main() -> None:
    per_seed_ranks = []
    shap_present = 0
    impurity_present = 0
    for f in sorted(PER.glob("*.json")):
        if f.name.endswith("_ERROR.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        m = d.get("tasks", {}).get("T3_rca", {}).get("ecn_proposed__full", {})
        expl = m.get("explanations") or m.get("shap_top_features") or []
        ranks = feature_rank_list(expl, k=10)
        uses_shap = any("mean_abs_shap" in (e or {}) for e in expl)
        uses_imp = any("importance" in (e or {}) and "mean_abs_shap" not in (e or {}) for e in expl)
        if uses_shap:
            shap_present += 1
        if uses_imp:
            impurity_present += 1
        per_seed_ranks.append(
            {
                "seed": d.get("seed_name") or f.stem,
                "top10": ranks,
                "source": "shap" if uses_shap else ("impurity" if uses_imp else "unknown"),
                "macro_f1": m.get("macro_f1"),
            }
        )

    pairs = []
    jacs, rhos = [], []
    for i in range(len(per_seed_ranks)):
        for j in range(i + 1, len(per_seed_ranks)):
            a = per_seed_ranks[i]["top10"]
            b = per_seed_ranks[j]["top10"]
            jac = jaccard(a, b)
            rho = rank_correlation(a, b)
            jacs.append(jac)
            if rho is not None:
                rhos.append(rho)
            pairs.append(
                {
                    "seed_a": per_seed_ranks[i]["seed"],
                    "seed_b": per_seed_ranks[j]["seed"],
                    "jaccard_top10": jac,
                    "spearman_rho": rho,
                }
            )

    # feature frequency across seeds
    freq: Dict[str, int] = {}
    for row in per_seed_ranks:
        for ftr in row["top10"]:
            freq[ftr] = freq.get(ftr, 0) + 1
    stable = sorted(freq.items(), key=lambda x: -x[1])

    out = {
        "note": (
            "Rank stability of RCA explanatory features across seeds. "
            "TreeSHAP does not affect T1 AUPRC (explanation-only on RCA path)."
        ),
        "n_seeds": len(per_seed_ranks),
        "seeds_with_shap": shap_present,
        "seeds_with_impurity_fallback": impurity_present,
        "per_seed": per_seed_ranks,
        "pairwise": pairs,
        "summary": {
            "mean_jaccard_top10": float(np.mean(jacs)) if jacs else None,
            "mean_spearman_rho": float(np.mean(rhos)) if rhos else None,
            "feature_frequency_top10": [{"feature": f, "n_seeds": n} for f, n in stable],
        },
        "limitations": [
            "No human-rated explanation quality study",
            "If TreeSHAP fails, impurity importances are used (recorded per seed)",
            "Removing TreeSHAP does not change T1 detection scores",
        ],
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("mean Jaccard", out["summary"]["mean_jaccard_top10"])


if __name__ == "__main__":
    main()
