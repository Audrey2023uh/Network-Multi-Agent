#!/usr/bin/env python3
"""Build static dashboard JSON from verified repository artifacts.

Does not invent metrics. Missing fields are omitted or marked unavailable.
Writes to interactive_dashboard/public/data/
Also writes DATA_PROVENANCE.md mapping dashboard elements to sources.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "public" / "data"
PROV = Path(__file__).resolve().parents[1] / "DATA_PROVENANCE.md"

SEEDS = [
    ("v1.1.0-INST", REPO / "benchmark" / "instances" / "v1" / "ecnetbench_v1.sqlite", "results/per_seed/v1.1.0-INST.json"),
    ("seed101", REPO / "benchmark" / "instances" / "v1.1-seed101" / "ecnetbench_v1.sqlite", "results/per_seed/seed101.json"),
    ("seed202", REPO / "benchmark" / "instances" / "v1.1-seed202" / "ecnetbench_v1.sqlite", "results/per_seed/seed202.json"),
    ("seed303", REPO / "benchmark" / "instances" / "v1.1-seed303" / "ecnetbench_v1.sqlite", "results/per_seed/seed303.json"),
    ("seed404", REPO / "benchmark" / "instances" / "v1.1-seed404" / "ecnetbench_v1.sqlite", "results/per_seed/seed404.json"),
    ("seed505", REPO / "benchmark" / "instances" / "v1.1-seed505" / "ecnetbench_v1.sqlite", "results/per_seed/seed505.json"),
]

PROVENANCE_ROWS: List[Dict[str, str]] = []


def jload(rel: str) -> Any:
    p = REPO / rel
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def sanitize(obj: Any) -> Any:
    """Make JSON-serializable; convert NaN/Inf to null (invalid in JSON.parse)."""
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, tuple):
        return [sanitize(v) for v in obj]
    # numpy scalars
    try:
        import numpy as np

        if isinstance(obj, (np.floating,)):
            v = float(obj)
            if v != v or v in (float("inf"), float("-inf")):
                return None
            return v
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return sanitize(obj.tolist())
    except Exception:
        pass
    return obj


def dump(name: str, obj: Any, source: str, field: str = "*", transform: str = "passthrough / subset") -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    clean = sanitize(obj)
    (OUT / name).write_text(json.dumps(clean, indent=2, allow_nan=False, default=str), encoding="utf-8")
    PROVENANCE_ROWS.append(
        {
            "element": name,
            "source": source,
            "field": field,
            "transform": transform,
        }
    )
    print("wrote", name)


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    r = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,)
    ).fetchone()
    return r is not None


def safe_sql_df(con: sqlite3.Connection, sql: str) -> pd.DataFrame:
    try:
        return pd.read_sql(sql, con)
    except Exception:
        return pd.DataFrame()


def extract_topology(db: Path, seed: str) -> Dict[str, Any]:
    if not db.exists():
        return {"seed": seed, "available": False, "reason": "sqlite_missing", "source": str(db)}
    con = sqlite3.connect(db)
    devices = safe_sql_df(con, "SELECT * FROM device")
    interfaces = safe_sql_df(con, "SELECT * FROM interface") if table_exists(con, "interface") else pd.DataFrame()
    links = safe_sql_df(
        con,
        "SELECT * FROM link" if table_exists(con, "link") else "SELECT * FROM links",
    )
    # incidents / labels if present
    incidents = pd.DataFrame()
    for cand in ("failure_incident", "incident", "incidents", "anomaly_label"):
        if table_exists(con, cand):
            incidents = safe_sql_df(con, f"SELECT * FROM {cand}")
            break
    # telemetry sample (bounded) — prefer device_resource_sample
    telem = pd.DataFrame()
    for cand in ("device_resource_sample", "if_counter_sample", "device_telemetry", "telemetry", "poll_sample"):
        if table_exists(con, cand):
            telem = safe_sql_df(con, f"SELECT * FROM {cand} LIMIT 5000")
            break
    schema = [
        {"name": r[0], "type": r[1]}
        for r in con.execute("SELECT name, type FROM sqlite_master WHERE type='table' ORDER BY 1")
    ]
    con.close()

    # normalize link endpoints via interface → device map
    iface_to_dev = {}
    if not interfaces.empty and "interface_id" in interfaces.columns and "device_id" in interfaces.columns:
        iface_to_dev = dict(zip(interfaces["interface_id"].astype(str), interfaces["device_id"].astype(str)))

    link_records = []
    if not links.empty:
        cols = {c.lower(): c for c in links.columns}
        a = cols.get("a_interface_id") or cols.get("a_device_id") or cols.get("src_device_id")
        b = cols.get("b_interface_id") or cols.get("b_device_id") or cols.get("dst_device_id")
        for _, row in links.iterrows():
            rec = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            if a and b:
                sa, sb = str(row[a]), str(row[b])
                rec["_source"] = iface_to_dev.get(sa, sa)
                rec["_target"] = iface_to_dev.get(sb, sb)
                rec["_a_interface_id"] = sa if a.endswith("interface_id") or "interface" in a else None
                rec["_b_interface_id"] = sb if b.endswith("interface_id") or "interface" in b else None
            link_records.append(rec)

    device_records = []
    if not devices.empty:
        for _, row in devices.iterrows():
            device_records.append({k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()})

    # timestamps from telemetry if available
    time_range = None
    telem_records = []
    if not telem.empty:
        tcol = None
        for c in telem.columns:
            if "time" in c.lower() or c.lower() in ("ts", "observed_at", "timestamp"):
                tcol = c
                break
        if tcol:
            ts = pd.to_datetime(telem[tcol], errors="coerce").dropna()
            if len(ts):
                time_range = {"min": str(ts.min()), "max": str(ts.max()), "column": tcol}
        # keep compact sample for replay
        telem_records = [
            {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            for _, row in telem.head(2000).iterrows()
        ]

    incident_records = []
    if not incidents.empty:
        incident_records = [
            {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            for _, row in incidents.head(2000).iterrows()
        ]

    iface_by_dev: Dict[str, List[Dict[str, Any]]] = {}
    if not interfaces.empty and "device_id" in interfaces.columns:
        for did, g in interfaces.groupby("device_id"):
            iface_by_dev[str(did)] = [
                {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
                for _, row in g.head(50).iterrows()
            ]

    return {
        "seed": seed,
        "available": True,
        "source_db": str(db.relative_to(REPO)).replace("\\", "/"),
        "n_devices": int(len(device_records)),
        "n_links": int(len(link_records)),
        "n_interfaces": int(len(interfaces)) if not interfaces.empty else 0,
        "n_incidents": int(len(incident_records)),
        "n_telemetry_rows_sampled": int(len(telem_records)),
        "time_range": time_range,
        "schema": schema,
        "devices": device_records,
        "links": link_records,
        "interfaces_by_device": iface_by_dev,
        "incidents": incident_records,
        "telemetry_sample": telem_records,
        "note": "Historical benchmark snapshot. Not a live production NOC feed.",
    }


def extract_per_seed_metrics(rel: str, seed: str) -> Dict[str, Any]:
    data = jload(rel)
    if not data:
        return {"seed": seed, "available": False, "source": rel}
    tasks = data.get("tasks", data)
    out: Dict[str, Any] = {
        "seed": seed,
        "available": True,
        "source": rel,
        "T1": {},
        "T2": {},
        "T3": {},
        "curves": {},
        "shap": None,
        "computational": data.get("computational_cost") or data.get("wall_time_s"),
    }
    # T1 methods
    t1 = tasks.get("T1_anomaly") or {}
    for method, block in t1.items():
        if not isinstance(block, dict):
            continue
        entry = {
            "ap": block.get("ap"),
            "roc_auc": block.get("roc_auc"),
            "brier": block.get("brier"),
            "f1": block.get("f1"),
            "precision": block.get("precision"),
            "recall": block.get("recall"),
            "precision_at_10": block.get("precision_at_10"),
            "precision_at_50": block.get("precision_at_50"),
            "precision_at_100": block.get("precision_at_100"),
            "precision_at_top1pct": block.get("precision_at_top1pct"),
            "fpr_at_recall_0_5": block.get("fpr_at_recall_0_5"),
            "fpr_at_recall_0_8": block.get("fpr_at_recall_0_8"),
            "peak_rss_delta_mb": block.get("peak_rss_delta_mb"),
            "threshold": block.get("threshold"),
            "train_time_s": block.get("train_time_s"),
            "confusion_matrix": block.get("confusion_matrix"),
            "calibration": block.get("calibration"),
            "roc_curve": block.get("roc_curve"),
            "pr_curve": block.get("pr_curve"),
            "fusion_diagnostics": block.get("fusion_diagnostics"),
            "model_family": block.get("model_family"),
        }
        # drop Nones deeply later in UI
        out["T1"][method] = entry
        if method == "ecn_proposed__full" and block.get("roc_curve"):
            out["curves"]["T1_roc"] = block.get("roc_curve")
            out["curves"]["T1_pr"] = block.get("pr_curve")
            out["curves"]["T1_calibration"] = block.get("calibration")
            out["curves"]["T1_cm"] = block.get("confusion_matrix")

    t2 = tasks.get("T2_failure") or {}
    for method, block in t2.items():
        if not isinstance(block, dict):
            continue
        out["T2"][method] = {
            "ap": block.get("ap"),
            "roc_auc": block.get("roc_auc"),
            "brier": block.get("brier"),
            "roc_curve": block.get("roc_curve"),
            "pr_curve": block.get("pr_curve"),
            "calibration": block.get("calibration"),
            "confusion_matrix": block.get("confusion_matrix"),
        }
        if method == "ecn_proposed__full":
            out["curves"]["T2_roc"] = block.get("roc_curve")
            out["curves"]["T2_pr"] = block.get("pr_curve")

    t3 = tasks.get("T3_rca") or {}
    for method, block in t3.items():
        if not isinstance(block, dict):
            continue
        out["T3"][method] = {
            "macro_f1": block.get("macro_f1"),
            "confusion_matrix": block.get("confusion_matrix"),
            "classes": block.get("classes"),
            "shap_top_features": block.get("shap_top_features") or block.get("explanations"),
            "feature_importances": block.get("feature_importances"),
        }
        if method == "ecn_proposed__full":
            out["shap"] = {
                "top_features": block.get("shap_top_features") or block.get("explanations"),
                "feature_importances": block.get("feature_importances"),
                "source_fields": "tasks.T3_rca.ecn_proposed__full.shap_top_features|feature_importances",
            }
            out["curves"]["T3_cm"] = block.get("confusion_matrix")
            out["curves"]["T3_classes"] = block.get("classes")
    return out


def build_aggregate_models() -> Dict[str, Any]:
    agg = jload("results/aggregate_v3.json") or jload("results/aggregate.json") or {}
    ms = jload("results/manuscript_ready_numbers.json") or {}
    sel = jload("results/v3_gated/t1_architecture_selection.json") or {}
    metrics = agg.get("metrics", {})
    t1 = metrics.get("T1_anomaly", {})
    t2 = metrics.get("T2_failure", {})

    def pack(block: Dict[str, Any], key: str = "ap") -> Optional[Dict[str, Any]]:
        if not block or key not in block:
            return None
        b = block[key]
        return {
            "mean": b.get("mean"),
            "std": b.get("std"),
            "ci95": b.get("ci95"),
            "n": b.get("n"),
            "min": b.get("min"),
            "max": b.get("max"),
        }

    models = []
    # Final proposed from manuscript_ready (authoritative for T1 final)
    models.append(
        {
            "id": "ecn_v3_final",
            "label": "ECN-v3 final (anchored)",
            "T1_auprc": {
                "mean": ms.get("T1_final_proposed", {}).get("auprc_mean"),
                "std": ms.get("T1_final_proposed", {}).get("auprc_std"),
                "ci95": ms.get("T1_final_proposed", {}).get("auprc_ci95_bootstrap")
                or ms.get("T1_final_proposed", {}).get("auprc_ci95_parametric"),
            },
            "T1_roc_auc": {"mean": ms.get("T1_final_proposed", {}).get("roc_auc_mean")},
            "T2_auprc": None,  # hybrid T2 head = logistic; filled below
            "source": "results/manuscript_ready_numbers.json",
            "note": "Authoritative final T1 architecture selection numbers",
        }
    )
    name_map = [
        ("xgboost__full", "XGBoost"),
        ("catboost__full", "CatBoost"),
        ("gradient_boosting__full", "Gradient Boosting"),
        ("balanced_rf__full", "Balanced RF"),
        ("random_forest__full", "Random Forest"),
        ("logistic__full", "Logistic"),
        ("lightgbm__full", "LightGBM"),
        ("isolation_forest__full", "Isolation Forest"),
        ("ewma__full", "EWMA"),
        ("gnn_graphsage_proxy__full", "GNN proxy"),
        ("mlp_sequence__full", "MLP sequence"),
        ("majority__full", "Majority"),
        ("ecn_proposed__full", "ECN (historical stack run in aggregate_v3)"),
    ]
    for key, label in name_map:
        models.append(
            {
                "id": key,
                "label": label,
                "T1_auprc": pack(t1.get(key, {}), "ap"),
                "T1_roc_auc": pack(t1.get(key, {}), "roc_auc"),
                "T2_auprc": pack(t2.get(key, {}), "ap"),
                "T2_roc_auc": pack(t2.get(key, {}), "roc_auc"),
                "T1_brier": pack(t1.get(key, {}), "brier"),
                "source": "results/aggregate_v3.json" if Path(REPO / "results/aggregate_v3.json").exists() else "results/aggregate.json",
            }
        )

    # patch T2 for final as telem logistic
    t2_logistic = pack(t2.get("logistic__full", {}), "ap")
    t2_logistic_roc = pack(t2.get("logistic__full", {}), "roc_auc")
    for m in models:
        if m["id"] == "ecn_v3_final":
            m["T2_auprc"] = t2_logistic
            m["T2_roc_auc"] = t2_logistic_roc
            m["T2_note"] = "Recommended T2 head = telem logistic (results/aggregate_v3.json logistic__full)"

    # Enrich manuscript_ready with hybrid T2 pointer (not hard-coded; from aggregate_v3)
    ms_out = dict(ms) if isinstance(ms, dict) else {}
    if t2_logistic:
        per_seed_ap = None
        block = t2.get("logistic__full", {}).get("ap", {})
        if isinstance(block, dict):
            per_seed_ap = block.get("per_seed") or block.get("values")
        ms_out["T2_recommended"] = {
            "name": "telem logistic (hybrid T2 head)",
            "auprc_mean": t2_logistic.get("mean"),
            "auprc_std": t2_logistic.get("std"),
            "auprc_ci95": t2_logistic.get("ci95"),
            "roc_auc_mean": (t2_logistic_roc or {}).get("mean"),
            "per_seed_auprc": per_seed_ap,
            "source": "results/aggregate_v3.json -> metrics.T2_failure.logistic__full",
        }

    # architecture selection rows
    arch_sel = {
        "source": "results/v3_gated/t1_architecture_selection.json",
        "summary": (sel.get("summary") if isinstance(sel, dict) else None),
        "decision": (sel.get("decision") if isinstance(sel, dict) else None),
        "per_seed": (sel.get("per_seed") if isinstance(sel, dict) else None),
        "selected": (jload("results/final_architecture.json") or {}).get("architecture_name")
        or "anchored",
        "rca": "RF + TreeSHAP",
    }

    runtime = {
        "T1_final_train_time_s_mean": ms_out.get("T1_final_proposed", {}).get("train_time_s_mean"),
        "source": "results/manuscript_ready_numbers.json -> T1_final_proposed.train_time_s_mean",
    }

    return {
        "models": models,
        "architecture_selection": arch_sel,
        "manuscript_ready": ms_out,
        "final_architecture": jload("results/final_architecture.json"),
        "checksums": jload("benchmark/INSTANCE_CHECKSUMS.json"),
        "calibration": jload("results/v3_gated/calibration.json"),
        "stats": jload("results/v3_gated/statistical_validation.json"),
        "scientific_stats_v4": jload("results/scientific_stats_v4.json"),
        "practical_impact": jload("results/practical_impact.json"),
        "sensitivity_analysis": jload("results/sensitivity_analysis.json"),
        "scalability_measured": jload("results/scalability_measured.json"),
        "xai_validation": jload("results/xai_validation.json"),
        "scenario_coverage": jload("results/scenario_coverage.json"),
        "extensions_v4": ms_out.get("extensions_v4"),
        "traceability": jload("results/v3_gated/t1_gain_traceability.json"),
        "runtime": runtime,
        "tables": {
            "performance_mean_ci": _csv("results/tables/performance_mean_ci.csv"),
            "significance": _csv("results/tables/significance_vs_proposed.csv"),
            "ablation": _csv("results/tables/ablation_ap.csv"),
            "v2_v3": _csv("results/tables/v2_v3_comparison.csv"),
            "practical_impact": _csv("results/tables/practical_impact.csv"),
        },
        "disclaimer": "Dashboard is a historical/replay visualization of verified benchmark artifacts. Not a live production deployment.",
    }


def _csv(rel: str) -> Optional[List[Dict[str, Any]]]:
    p = REPO / rel
    if not p.exists():
        return None
    df = pd.read_csv(p)
    return df.to_dict(orient="records")


def write_provenance() -> None:
    lines = [
        "# Dashboard Data Provenance",
        "",
        "All scientific values displayed in the interactive dashboard are loaded from verified repository artifacts. None are hard-coded in the frontend.",
        "",
        "| Dashboard Element | Source File | Source Field | Transformation |",
        "|---|---|---|---|",
    ]
    for r in PROVENANCE_ROWS:
        lines.append(f"| `{r['element']}` | `{r['source']}` | `{r['field']}` | {r['transform']} |")
    lines += [
        "",
        "## Authoritative T1 numbers",
        "",
        "- Final T1 AUPRC / ROC-AUC / twin gain: `results/manuscript_ready_numbers.json`",
        "- Baseline aggregates: `results/aggregate_v3.json`",
        "- Architecture selection A/B/C/D: `results/v3_gated/t1_architecture_selection.json`",
        "- Per-seed curves / CM / calibration / SHAP (if present): `results/per_seed/*.json`",
        "- Topology / incidents / telemetry: `benchmark/instances/*/ecnetbench_v1.sqlite`",
        "",
        "## Labeling",
        "",
        "The UI labels exploration as **historical benchmark replay**, not live network monitoring.",
        "",
        "## Frontend UI element → JSON mapping",
        "",
        "| Dashboard Element | Source File | Source Field | Transformation |",
        "|---|---|---|---|",
        "| Home / Results T1 AUPRC card | `public/data/aggregate.json` | `manuscript_ready.T1_final_proposed.auprc_mean` | Display `fmt()`; provenance → `results/manuscript_ready_numbers.json` |",
        "| Home / Results T1 ROC-AUC | `public/data/aggregate.json` | `manuscript_ready.T1_final_proposed.roc_auc_mean` | Display only |",
        "| Results T2 AUPRC | `public/data/aggregate.json` | `manuscript_ready.T2_recommended.auprc_mean` | Copied at build from `aggregate_v3` logistic__full |",
        "| Models table rows | `public/data/aggregate.json` | `models[]` | Merge manuscript final + aggregate_v3 baselines |",
        "| Topology node/link counts | `public/data/topology_<seed>.json` | `n_devices`, `n_links`, `devices`, `links` | SQLite extract |",
        "| Topology inspector fields | `public/data/topology_<seed>.json` | device/link row keys | Show non-null fields only |",
        "| Time slider | `public/data/topology_<seed>.json` | `time_range`, `telemetry_sample` | Distinct timestamps from sample |",
        "| Seed ROC/PR/CM/calibration | `public/data/metrics_<seed>.json` | `T1`/`T2` curves + `curves.*` | From `results/per_seed` |",
        "| TreeSHAP global bars | `public/data/metrics_<seed>.json` | `shap.top_features` | From T3 RCA block |",
        "| Architecture modules | `public/data/architecture.json` | `modules`, `hybrid` | From `final_architecture.json` + code map |",
        "| Seed selector options | `public/data/index.json` | `seeds[].id` | Inventory |",
        "",
    ]
    PROV.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", PROV)


def load_committed_topology(seed: str) -> Optional[Dict[str, Any]]:
    """CI/GitHub Pages: SQLite instances are gitignored; reuse committed JSON."""
    p = OUT / f"topology_{seed}.json"
    if not p.exists():
        return None
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(obj, dict) or not obj.get("available"):
        return None
    if not obj.get("n_devices") or not obj.get("links"):
        return None
    return obj


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = {
        "seeds": [],
        "generated_from": str(REPO.name),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "historical_benchmark_replay",
    }

    for seed, db, per_rel in SEEDS:
        topo = extract_topology(db, seed)
        topo_source = str(db.relative_to(REPO)).replace("\\", "/") if db.exists() else "missing"
        topo_transform = "SQL extract; telemetry capped at 2000-5000 rows; NaN->null"
        if not topo.get("available"):
            reused = load_committed_topology(seed)
            if reused is not None:
                topo = reused
                topo_source = f"interactive_dashboard/public/data/topology_{seed}.json (committed; sqlite not in checkout)"
                topo_transform = "Reuse committed topology JSON because benchmark/instances/** is gitignored"
                print(f"reuse committed topology_{seed}.json (sqlite missing on this machine/CI)")
            else:
                print(f"WARNING: no sqlite and no committed topology for {seed}")
        dump(
            f"topology_{seed}.json",
            topo,
            source=topo_source,
            field="device,interface,link,incident,telemetry tables",
            transform=topo_transform,
        )
        metrics = extract_per_seed_metrics(per_rel, seed)
        dump(
            f"metrics_{seed}.json",
            metrics,
            source=per_rel,
            field="tasks.T1_anomaly / T2_failure / T3_rca",
            transform="Subset of AP/ROC/Brier/curves/CM/SHAP fields",
        )
        index["seeds"].append(
            {
                "id": seed,
                "topology": f"data/topology_{seed}.json",
                "metrics": f"data/metrics_{seed}.json",
                "n_devices": topo.get("n_devices"),
                "n_links": topo.get("n_links"),
                "available": bool(topo.get("available")) and bool(metrics.get("available")),
            }
        )

    agg = build_aggregate_models()
    dump(
        "aggregate.json",
        agg,
        source="results/manuscript_ready_numbers.json + results/aggregate_v3.json + results/v3_gated/*",
        field="multiple",
        transform="Merge authoritative final T1 with baseline aggregates; no fabricated metrics",
    )
    dump(
        "architecture.json",
        {
            "name": (agg.get("final_architecture") or {}).get("architecture_name"),
            "components": (agg.get("final_architecture") or {}).get("components"),
            "hybrid": (agg.get("final_architecture") or {}).get("hybrid_recommendation"),
            "modules": [
                {"id": "digital_twin", "title": "Digital Twin", "code": "framework/ecn/twin.py"},
                {"id": "perception", "title": "Perception", "code": "framework/ecn/features.py"},
                {"id": "anomaly", "title": "Anomaly Agent", "code": "framework/ecn/agents/"},
                {"id": "prediction", "title": "Prediction Agent", "code": "framework/ecn/agents/"},
                {"id": "fusion", "title": "Anchored Fusion", "code": "framework/ecn/models.py#ECNFusionModel"},
                {"id": "rca", "title": "RCA (TreeSHAP)", "code": "framework/ecn/agents/core.py"},
                {"id": "impact", "title": "Impact", "code": "framework/ecn/features.py"},
                {"id": "healing", "title": "Healing", "code": "framework/ecn/agents/"},
            ],
            "source": "results/final_architecture.json",
        },
        source="results/final_architecture.json",
        field="architecture_name,components,hybrid_recommendation",
        transform="Add module→source-code map for UI navigation",
    )
    dump("index.json", index, source="benchmark/instances + results/per_seed", field="seed inventory", transform="Index only")
    write_provenance()
    # validation against manuscript-ready file on disk (not a duplicated constant)
    ms = agg["manuscript_ready"]
    ms_disk = jload("results/manuscript_ready_numbers.json") or {}
    t1 = ms.get("T1_final_proposed", {}).get("auprc_mean")
    t1_disk = ms_disk.get("T1_final_proposed", {}).get("auprc_mean")
    assert t1 is not None and t1_disk is not None and abs(float(t1) - float(t1_disk)) < 1e-15, (t1, t1_disk)
    print("validation_ok manuscript T1 AUPRC", t1)


if __name__ == "__main__":
    main()
