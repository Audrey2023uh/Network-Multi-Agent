#!/usr/bin/env python3
"""Consolidate stronger statistical comparisons for ECN extensions_v4.

Uses per_seed AUPRC vectors; Wilcoxon + Cliff's delta + paired bootstrap + BH-FDR.
Does not invent significance. Writes results/scientific_stats_v4.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "framework"))
sys.path.insert(0, str(ROOT / "evaluation"))

from run_v3_gated import bh_fdr, bootstrap_ci  # noqa: E402
from ecn.models import cliffs_delta, wilcoxon_paired  # noqa: E402

PER = ROOT / "results" / "per_seed"
OUT = ROOT / "results" / "scientific_stats_v4.json"

BASELINES = [
    "xgboost__full",
    "catboost__full",
    "lightgbm__full",
    "gradient_boosting__full",
    "balanced_rf__full",
    "random_forest__full",
    "logistic__full",
    "isolation_forest__full",
    "ewma__full",
    "threshold__full",
    "mlp_sequence__full",
    "gnn_graphsage_proxy__full",
    "majority__full",
]
PROPOSED = "ecn_proposed__full"


def load_metric(task: str, method: str, metric: str = "ap") -> Tuple[List[str], List[float]]:
    names, vals = [], []
    for f in sorted(PER.glob("*.json")):
        if f.name.endswith("_ERROR.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        m = d.get("tasks", {}).get(task, {}).get(method, {})
        v = m.get(metric)
        if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)):
            names.append(d.get("seed_name") or f.stem)
            vals.append(float(v))
    return names, vals


def paired_bootstrap_p(a: List[float], b: List[float], n_boot: int = 5000, seed: int = 0) -> Dict[str, float]:
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    diff = aa - bb
    rng = np.random.default_rng(seed)
    boots = [float(np.mean(rng.choice(diff, size=len(diff), replace=True))) for _ in range(n_boot)]
    return {
        "mean_diff": float(diff.mean()),
        "ci95_lo": float(np.percentile(boots, 2.5)),
        "ci95_hi": float(np.percentile(boots, 97.5)),
        "p_a_gt_b": float(np.mean(np.asarray(boots) > 0)),
        "p_a_lt_b": float(np.mean(np.asarray(boots) < 0)),
    }


def compare(task: str, method_a: str, method_b: str) -> Dict[str, Any]:
    names_a, a = load_metric(task, method_a)
    names_b, b = load_metric(task, method_b)
    if names_a != names_b or len(a) < 3:
        return {"error": "insufficient_or_misaligned", "n_a": len(a), "n_b": len(b)}
    return {
        "n": len(a),
        "seeds": names_a,
        "a": {"method": method_a, "bootstrap": bootstrap_ci(a), "values": a},
        "b": {"method": method_b, "bootstrap": bootstrap_ci(b), "values": b},
        "wilcoxon": wilcoxon_paired(a, b),
        "cliffs_delta": cliffs_delta(a, b),
        "paired_bootstrap": paired_bootstrap_p(a, b),
    }


def main() -> None:
    out: Dict[str, Any] = {
        "note": "Paired tests across six frozen seeds; n=6 is small — interpret FDR cautiously.",
        "protocol": "temporal 70/15/15; AUPRC primary",
        "tasks": {},
    }
    for task in ["T1_anomaly", "T2_failure"]:
        _, prop = load_metric(task, PROPOSED)
        tests = []
        for base in BASELINES:
            # skip if baseline missing entirely
            _, bv = load_metric(task, base)
            if len(bv) < 3:
                continue
            block = compare(task, PROPOSED, base)
            block["baseline"] = base
            tests.append(block)
        pvals = []
        for t in tests:
            pv = (t.get("wilcoxon") or {}).get("pvalue")
            pvals.append(float(pv) if pv is not None else 1.0)
        fdr = bh_fdr(pvals) if pvals else []
        for t, q in zip(tests, fdr):
            t["bh_fdr_q"] = q
        # also vs RF for strongest classical reference
        vs_rf = compare(task, PROPOSED, "random_forest__full")
        vs_xgb = compare(task, PROPOSED, "xgboost__full") if load_metric(task, "xgboost__full")[1] else None
        out["tasks"][task] = {
            "proposed_bootstrap_ap": bootstrap_ci(prop) if prop else None,
            "vs_baselines": tests,
            "headline": {
                "vs_random_forest": vs_rf,
                "vs_xgboost": vs_xgb,
            },
        }

    # calibration surface from gated if present
    gated = ROOT / "results" / "v3_gated"
    calib_path = gated / "calibration.json"
    if calib_path.exists():
        out["calibration_from_v3_gated"] = json.loads(calib_path.read_text(encoding="utf-8"))
    else:
        out["calibration_from_v3_gated"] = None

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
