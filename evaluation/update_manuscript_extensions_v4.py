#!/usr/bin/env python3
"""Append extensions_v4 to manuscript_ready_numbers.json from measured artifacts only."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "results" / "manuscript_ready_numbers.json"
AGG = ROOT / "results" / "aggregate_v3.json"
PRACT = ROOT / "results" / "practical_impact.json"
STATS = ROOT / "results" / "scientific_stats_v4.json"
XAI = ROOT / "results" / "xai_validation.json"
SENS = ROOT / "results" / "sensitivity_analysis.json"
SCAL = ROOT / "results" / "scalability_measured.json"
SCEN = ROOT / "results" / "scenario_coverage.json"


def mget(d: Optional[Dict], *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return default if cur is None else cur


def main() -> None:
    ms = json.loads(MS.read_text(encoding="utf-8")) if MS.exists() else {}
    agg = json.loads(AGG.read_text(encoding="utf-8")) if AGG.exists() else {}
    pract = json.loads(PRACT.read_text(encoding="utf-8")) if PRACT.exists() else {}
    stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
    xai = json.loads(XAI.read_text(encoding="utf-8")) if XAI.exists() else {}
    sens = json.loads(SENS.read_text(encoding="utf-8")) if SENS.exists() else {}
    scal = json.loads(SCAL.read_text(encoding="utf-8")) if SCAL.exists() else {}
    scen = json.loads(SCEN.read_text(encoding="utf-8")) if SCEN.exists() else {}

    t1 = (agg.get("metrics") or {}).get("T1_anomaly") or {}
    baselines = {}
    for mk in (
        "xgboost__full",
        "catboost__full",
        "lightgbm__full",
        "gradient_boosting__full",
        "balanced_rf__full",
        "random_forest__full",
        "logistic__full",
        "ecn_proposed__full",
    ):
        ap = mget(t1, mk, "ap", "mean")
        if ap is not None:
            baselines[mk] = {
                "auprc_mean": ap,
                "auprc_ci95": mget(t1, mk, "ap", "ci95"),
                "precision_at_50_mean": mget(t1, mk, "precision_at_50", "mean"),
                "train_time_s_mean": mget(t1, mk, "train_time_s", "mean"),
            }

    ext: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "extensions_v4 measured on frozen six seeds only; does not overwrite "
            "T1_final_proposed selection unless re-selection is re-run."
        ),
        "T1_stronger_baselines": baselines,
        "practical_impact_T1": {
            "proposed_precision_at_50": mget(
                pract, "tasks", "T1_anomaly", "methods", "ecn_proposed__full", "precision_at_50"
            ),
            "proposed_fpr_at_recall_0_5": mget(
                pract, "tasks", "T1_anomaly", "methods", "ecn_proposed__full", "fpr_at_recall_0_5"
            ),
            "vs_random_forest": mget(
                pract, "tasks", "T1_anomaly", "vs_baselines", "random_forest__full"
            ),
        },
        "scientific_stats_headline_T1": mget(stats, "tasks", "T1_anomaly", "headline"),
        "xai_rank_stability": mget(xai, "summary"),
        "sensitivity_missing": mget(sens, "missing_telemetry"),
        "scalability_19node": {
            "caption": mget(scal, "caption"),
            "per_seed_wall": mget(scal, "per_seed_eval_wall_s"),
            "proposed_train_time": mget(
                scal, "methods_T1_T2_pooled", "ecn_proposed__full", "train_time_s"
            ),
        },
        "scenario_coverage": {
            "n_distinct_categories": mget(scen, "n_distinct_categories"),
            "category_totals": mget(scen, "category_totals_across_seeds"),
        },
        "ablation_note_TreeSHAP": (
            "TreeSHAP is explanation-only on the RCA path; removing it does not change T1 AUPRC."
        ),
    }
    ms["extensions_v4"] = ext
    MS.write_text(json.dumps(ms, indent=2), encoding="utf-8")
    print("updated", MS)


if __name__ == "__main__":
    main()
