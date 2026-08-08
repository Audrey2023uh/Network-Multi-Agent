#!/usr/bin/env python3
"""Derive practical-impact / workload proxies from per-seed binary metrics.

Reads results/per_seed/*.json after run_full_evaluation. Does not invent metrics.
Writes results/practical_impact.json and results/tables/practical_impact.csv.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PER = ROOT / "results" / "per_seed"
OUT = ROOT / "results" / "practical_impact.json"
TAB = ROOT / "results" / "tables" / "practical_impact.csv"

TASKS = ["T1_anomaly", "T2_failure"]
METHODS = [
    "ecn_proposed__full",
    "xgboost__full",
    "catboost__full",
    "lightgbm__full",
    "gradient_boosting__full",
    "balanced_rf__full",
    "random_forest__full",
    "logistic__full",
    "isolation_forest__full",
    "ewma__full",
]
PRACTICAL_KEYS = [
    "ap",
    "precision_at_10",
    "precision_at_50",
    "precision_at_100",
    "precision_at_top1pct",
    "fpr_at_recall_0_5",
    "fpr_at_recall_0_8",
    "precision_at_recall_0_5",
    "precision_at_recall_0_8",
    "train_time_s",
]


def mean_ci(vals: List[float]) -> Dict[str, Any]:
    a = [float(v) for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not a:
        return {"mean": None, "std": None, "n": 0, "ci95_lo": None, "ci95_hi": None}
    m = float(np.mean(a))
    s = float(np.std(a, ddof=1)) if len(a) > 1 else 0.0
    se = s / np.sqrt(len(a)) if len(a) else 0.0
    return {
        "mean": m,
        "std": s,
        "n": len(a),
        "ci95_lo": m - 1.96 * se,
        "ci95_hi": m + 1.96 * se,
        "per_seed": a,
    }


def load_seeds() -> List[Dict[str, Any]]:
    rows = []
    for f in sorted(PER.glob("*.json")):
        if f.name.endswith("_ERROR.json"):
            continue
        rows.append(json.loads(f.read_text(encoding="utf-8")))
    return rows


def collect(seeds: List[Dict[str, Any]], task: str, method: str, key: str) -> List[float]:
    out = []
    for r in seeds:
        m = r.get("tasks", {}).get(task, {}).get(method, {})
        v = m.get(key)
        if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)):
            out.append(float(v))
    return out


def relative_fp_reduction(
    seeds: List[Dict[str, Any]], task: str, method: str, baseline: str, recall_key: str
) -> Optional[Dict[str, Any]]:
    """Relative FP reduction at matched recall target: 1 - fpr_m / fpr_b (when both defined)."""
    diffs = []
    for r in seeds:
        fm = r.get("tasks", {}).get(task, {}).get(method, {}).get(recall_key)
        fb = r.get("tasks", {}).get(task, {}).get(baseline, {}).get(recall_key)
        if isinstance(fm, (int, float)) and isinstance(fb, (int, float)) and fb > 0:
            diffs.append(1.0 - float(fm) / float(fb))
    if not diffs:
        return None
    return mean_ci(diffs)


def main() -> None:
    seeds = load_seeds()
    if not seeds:
        raise SystemExit("No per_seed results found")

    out: Dict[str, Any] = {
        "note": "Workload proxies derived from test scores+labels only; not MTTR/ROI claims.",
        "n_seeds": len(seeds),
        "seed_names": [s.get("seed_name") for s in seeds],
        "tasks": {},
    }

    csv_rows: List[Dict[str, Any]] = []
    for task in TASKS:
        out["tasks"][task] = {"methods": {}, "vs_baselines": {}}
        for method in METHODS:
            block = {}
            for key in PRACTICAL_KEYS:
                block[key] = mean_ci(collect(seeds, task, method, key))
            out["tasks"][task]["methods"][method] = block
            csv_rows.append(
                {
                    "task": task,
                    "method": method,
                    "auprc_mean": block["ap"]["mean"],
                    "precision_at_10_mean": block["precision_at_10"]["mean"],
                    "precision_at_50_mean": block["precision_at_50"]["mean"],
                    "precision_at_100_mean": block["precision_at_100"]["mean"],
                    "precision_at_top1pct_mean": block["precision_at_top1pct"]["mean"],
                    "fpr_at_recall_0_5_mean": block["fpr_at_recall_0_5"]["mean"],
                    "fpr_at_recall_0_8_mean": block["fpr_at_recall_0_8"]["mean"],
                }
            )

        prop = "ecn_proposed__full"
        for base in ("random_forest__full", "logistic__full", "xgboost__full", "lightgbm__full"):
            out["tasks"][task]["vs_baselines"][base] = {
                "relative_fp_reduction_at_recall_0_5": relative_fp_reduction(
                    seeds, task, prop, base, "fpr_at_recall_0_5"
                ),
                "relative_fp_reduction_at_recall_0_8": relative_fp_reduction(
                    seeds, task, prop, base, "fpr_at_recall_0_8"
                ),
                "auprc_delta_mean": (
                    None
                    if out["tasks"][task]["methods"][prop]["ap"]["mean"] is None
                    or out["tasks"][task]["methods"].get(base, {}).get("ap", {}).get("mean") is None
                    else out["tasks"][task]["methods"][prop]["ap"]["mean"]
                    - out["tasks"][task]["methods"][base]["ap"]["mean"]
                ),
            }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    TAB.parent.mkdir(parents=True, exist_ok=True)
    with TAB.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)
    print("wrote", OUT)
    print("wrote", TAB)


if __name__ == "__main__":
    main()
