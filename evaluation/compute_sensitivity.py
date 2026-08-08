#!/usr/bin/env python3
"""Consolidate sensitivity / robustness results into results/sensitivity_analysis.json."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PER = ROOT / "results" / "per_seed"
AGG = ROOT / "results" / "aggregate_v3.json"
OUT = ROOT / "results" / "sensitivity_analysis.json"

SEEDS = [
    ("v1.1.0-INST", ROOT / "benchmark" / "instances" / "v1" / "ecnetbench_v1.sqlite"),
    ("seed101", ROOT / "benchmark" / "instances" / "v1.1-seed101" / "ecnetbench_v1.sqlite"),
    ("seed202", ROOT / "benchmark" / "instances" / "v1.1-seed202" / "ecnetbench_v1.sqlite"),
    ("seed303", ROOT / "benchmark" / "instances" / "v1.1-seed303" / "ecnetbench_v1.sqlite"),
    ("seed404", ROOT / "benchmark" / "instances" / "v1.1-seed404" / "ecnetbench_v1.sqlite"),
    ("seed505", ROOT / "benchmark" / "instances" / "v1.1-seed505" / "ecnetbench_v1.sqlite"),
]


def mean_ci(vals: List[float]) -> Dict[str, Any]:
    a = [float(v) for v in vals if isinstance(v, (int, float))]
    if not a:
        return {"mean": None, "n": 0}
    m = float(np.mean(a))
    s = float(np.std(a, ddof=1)) if len(a) > 1 else 0.0
    se = s / np.sqrt(len(a))
    return {"mean": m, "std": s, "n": len(a), "ci95_lo": m - 1.96 * se, "ci95_hi": m + 1.96 * se, "values": a}


def prevalence_from_db(db: Path) -> Dict[str, Any]:
    if not db.exists():
        return {"available": False}
    con = sqlite3.connect(db)
    try:
        # Prefer label tables if present; else failure_incident count / windows unavailable
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        out: Dict[str, Any] = {"available": True, "tables_present": sorted(tables & {
            "failure_incident", "label_anomaly_window", "device"
        })}
        if "failure_incident" in tables:
            n_inc = con.execute("SELECT COUNT(*) FROM failure_incident").fetchone()[0]
            cats = con.execute(
                "SELECT category, COUNT(*) FROM failure_incident GROUP BY category ORDER BY COUNT(*) DESC"
            ).fetchall()
            out["n_incidents"] = int(n_inc)
            out["incident_categories"] = [{"category": c, "count": int(n)} for c, n in cats]
        if "device" in tables:
            out["n_devices"] = int(con.execute("SELECT COUNT(*) FROM device").fetchone()[0])
        return out
    finally:
        con.close()


def main() -> None:
    missing10, missing30, clean = [], [], []
    prior_t1 = []
    ablations: Dict[str, List[float]] = {
        "full": [],
        "no_twin": [],
        "no_nbr": [],
        "telem_only": [],
        "twin_only": [],
    }
    for f in sorted(PER.glob("*.json")):
        if f.name.endswith("_ERROR.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        t1 = d.get("tasks", {}).get("T1_anomaly", {})
        full = t1.get("ecn_proposed__full", {})
        if isinstance(full.get("ap"), (int, float)):
            clean.append(float(full["ap"]))
            if isinstance(full.get("prior"), (int, float)):
                prior_t1.append(float(full["prior"]))
        for key, lst in (("robust_missing_10", missing10), ("robust_missing_30", missing30)):
            block = t1.get(key) or {}
            # robustness may nest under proposed method or return flat metrics
            ap = block.get("ap")
            if ap is None and isinstance(block.get("ecn_proposed__full"), dict):
                ap = block["ecn_proposed__full"].get("ap")
            if isinstance(ap, (int, float)):
                lst.append(float(ap))
        for abl in ablations:
            mk = f"ecn_proposed__{abl}"
            ap = (t1.get(mk) or {}).get("ap")
            if isinstance(ap, (int, float)):
                ablations[abl].append(float(ap))

    noise = None
    noise_path = ROOT / "results" / "v3_gated" / "noise_missing.json"
    if noise_path.exists():
        noise = json.loads(noise_path.read_text(encoding="utf-8"))

    fabric = []
    for name, db in SEEDS:
        info = prevalence_from_db(db)
        info["seed"] = name
        fabric.append(info)

    out = {
        "note": (
            "Sensitivity on frozen six seeds only. Fabric-size (#devices) sweeps are NOT measured — "
            "all instances are ~19 devices."
        ),
        "missing_telemetry": {
            "clean_proposed_ap": mean_ci(clean),
            "missing_10_ap": mean_ci(missing10),
            "missing_30_ap": mean_ci(missing30),
            "drop_missing_10": (
                None
                if not clean or not missing10
                else float(np.mean(clean[: len(missing10)]) - np.mean(missing10))
            ),
            "drop_missing_30": (
                None
                if not clean or not missing30
                else float(np.mean(clean[: len(missing30)]) - np.mean(missing30))
            ),
        },
        "feature_ablations_T1": {k: mean_ci(v) for k, v in ablations.items()},
        "class_imbalance_T1_prior": mean_ci(prior_t1),
        "noise_missing_from_v3_gated": noise,
        "fabric_descriptive": fabric,
        "limitations": [
            "No topology morphs or device-count sweeps",
            "Noise/missing20 from v3_gated uses historical gated protocol; regenerate if re-running gated",
        ],
    }
    if AGG.exists():
        agg = json.loads(AGG.read_text(encoding="utf-8"))
        out["module_contribution_from_aggregate"] = agg.get("module_contribution")

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
