#!/usr/bin/env python3
"""Measured computational cost on frozen 19-device instances only.

Writes results/scalability_measured.json. Does not claim fabric-size scalability.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PER = ROOT / "results" / "per_seed"
AGG = ROOT / "results" / "aggregate_v3.json"
OUT = ROOT / "results" / "scalability_measured.json"

METHODS = [
    "ecn_proposed__full",
    "xgboost__full",
    "catboost__full",
    "lightgbm__full",
    "gradient_boosting__full",
    "balanced_rf__full",
    "random_forest__full",
    "logistic__full",
    "mlp_sequence__full",
]


def mean_ci(vals: List[float]) -> Dict[str, Any]:
    a = [float(v) for v in vals if isinstance(v, (int, float))]
    if not a:
        return {"mean": None, "n": 0}
    m = float(np.mean(a))
    s = float(np.std(a, ddof=1)) if len(a) > 1 else 0.0
    se = s / np.sqrt(len(a))
    return {"mean": m, "std": s, "n": len(a), "ci95_lo": m - 1.96 * se, "ci95_hi": m + 1.96 * se}


def main() -> None:
    per_method: Dict[str, Dict[str, List[float]]] = {
        m: {"train_time_s": [], "wall_time_s": [], "peak_rss_delta_mb": []} for m in METHODS
    }
    seed_walls = []
    n_devices = []
    for f in sorted(PER.glob("*.json")):
        if f.name.endswith("_ERROR.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        seed_walls.append(float((d.get("cost") or {}).get("wall_time_s") or 0))
        # topology counts if present
        topo = d.get("topology") or {}
        if isinstance(topo.get("n_devices"), int):
            n_devices.append(topo["n_devices"])
        for task in ("T1_anomaly", "T2_failure"):
            block = d.get("tasks", {}).get(task, {})
            for m in METHODS:
                met = block.get(m) or {}
                for key in ("train_time_s", "wall_time_s", "peak_rss_delta_mb"):
                    v = met.get(key)
                    if isinstance(v, (int, float)):
                        per_method[m][key].append(float(v))

    methods_out = {}
    for m, keys in per_method.items():
        methods_out[m] = {k: mean_ci(v) for k, v in keys.items()}

    agg_cost = None
    if AGG.exists():
        agg_cost = json.loads(AGG.read_text(encoding="utf-8")).get("computational_cost")

    out = {
        "caption": (
            "Computational cost on frozen ~19-device / ~31-link ECNetBench instances; "
            "fabric-size scalability was NOT measured."
        ),
        "n_devices_observed": sorted(set(n_devices)) if n_devices else [19],
        "per_seed_eval_wall_s": mean_ci(seed_walls),
        "methods_T1_T2_pooled": methods_out,
        "aggregate_computational_cost": agg_cost,
        "limitations": [
            "No horizontal scaling experiment across fabric sizes",
            "peak_rss_delta_mb is process RSS delta during fit/score (approximate), not allocator peak",
        ],
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
