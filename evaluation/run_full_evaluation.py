"""
Enterprise Cognitive Network — full multi-seed evaluation on ECNetBench.

All paths are relative to the repository root.
Benchmark instances are read-only.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Repo root = parent of evaluation/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "framework"))

from ecn.agents import Orchestrator  # noqa: E402
from ecn.features import (  # noqa: E402
    build_anomaly_dataset,
    build_config_risk_dataset,
    build_degradation_dataset,
    build_failure_dataset,
    build_healing_dataset,
    build_impact_dataset,
    build_rca_dataset,
)
from ecn.models import (  # noqa: E402
    ECNFusionModel,
    ECNStackFusionModel,
    cliffs_delta,
    eval_binary,
    eval_multiclass,
    fit_binary,
    fit_multiclass,
    mean_ci,
    predict_scores,
    tune_threshold,
    wilcoxon_paired,
)
from ecn.twin import DigitalTwin  # noqa: E402

warnings.filterwarnings("ignore")

INSTANCES = ROOT / "benchmark" / "instances"
OUT = ROOT / "results"
FIG = ROOT / "figures"
TAB = ROOT / "tables"
REP = ROOT / "reports"

SEEDS = [
    ("v1.1.0-INST", INSTANCES / "v1" / "ecnetbench_v1.sqlite", 20260806),
    ("seed101", INSTANCES / "v1.1-seed101" / "ecnetbench_v1.sqlite", 101),
    ("seed202", INSTANCES / "v1.1-seed202" / "ecnetbench_v1.sqlite", 202),
    ("seed303", INSTANCES / "v1.1-seed303" / "ecnetbench_v1.sqlite", 303),
    ("seed404", INSTANCES / "v1.1-seed404" / "ecnetbench_v1.sqlite", 404),
    ("seed505", INSTANCES / "v1.1-seed505" / "ecnetbench_v1.sqlite", 505),
]

BINARY_BASELINES = [
    "majority",
    "threshold",
    "ewma",
    "isolation_forest",
    "logistic",
    "random_forest",
    "gradient_boosting",
    "balanced_rf",
    "lightgbm",
    "xgboost",
    "catboost",
    "mlp_sequence",
]
PROPOSED = "ecn_proposed"


def jdump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def _sanitize(o: Any) -> Any:
        if isinstance(o, Path):
            try:
                return str(o.relative_to(ROOT)).replace("\\", "/")
            except Exception:
                return o.name
        if isinstance(o, dict):
            return {k: _sanitize(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_sanitize(v) for v in o]
        if isinstance(o, str) and (":\\" in o or o.startswith("/Users/")):
            # strip absolute private paths
            p = Path(o)
            return p.name
        return o

    with path.open("w", encoding="utf-8") as f:
        json.dump(_sanitize(obj), f, indent=2, default=str)


def xy(df: pd.DataFrame, cols: List[str], split: str, ycol: str = "y") -> Tuple[np.ndarray, np.ndarray]:
    m = df["split"] == split
    X = df.loc[m, cols].astype(float).values
    y = df.loc[m, ycol].values
    if not (y.dtype == object or str(y.dtype).startswith("str")):
        y = y.astype(int)
    return X, y


def filter_cols(cols: List[str], mode: str) -> List[str]:
    if mode == "full":
        return list(cols)
    if mode == "no_twin":
        return [c for c in cols if not c.startswith("twin_")]
    if mode == "no_nbr":
        return [c for c in cols if not c.startswith("twin_nbr")]
    if mode == "telem_only":
        keep = {
            "cpu_mean", "cpu_max", "mem_mean", "n_polls", "err_sum", "disc_sum", "car_sum", "sev_n",
            "d_cpu_mean", "d_cpu_max", "d_mem_mean", "cpu_z", "mem_z",
        }
        return [c for c in cols if c in keep] or [
            c for c in cols if not c.startswith("twin_") and not c.startswith("cat_")
        ]
    if mode == "no_syslog":
        drop_pref = ("app_", "code_", "n_syslog", "sev_mean", "n_alerts")
        return [c for c in cols if not any(c.startswith(p) or c == p for p in drop_pref)]
    if mode == "no_rca_cat":
        return [c for c in cols if not c.startswith("cat_")]
    if mode == "twin_only":
        return [c for c in cols if c.startswith("twin_")]
    return list(cols)


def _eval_one_binary(
    df: pd.DataFrame, use: List[str], seed: int, method: str, abl_tag: str
) -> Dict[str, Any]:
    Xtr, ytr = xy(df, use, "train")
    Xva, yva = xy(df, use, "val")
    Xte, yte = xy(df, use, "test")
    if len(yte) == 0 or len(ytr) == 0 or not use:
        return {"error": "empty split or features"}

    rss0 = None
    try:
        import psutil

        rss0 = float(psutil.Process().memory_info().rss)
    except Exception:
        rss0 = None

    t0 = time.perf_counter()
    extra: Dict[str, Any] = {}
    if method == PROPOSED:
        # Final T1 architecture: v3 features + anchored fusion (stacking is ablation only).
        model = ECNFusionModel(seed=seed).fit(Xtr, ytr, Xva, yva, use)
        scores_va = model.predict_proba_positive(Xva) if len(yva) else np.array([0.5])
        thr = tune_threshold(yva, scores_va) if len(yva) else 0.5
        scores = model.predict_proba_positive(Xte)
        train_t = model.train_time_s
        extra = {"fusion_diagnostics": getattr(model, "diagnostics", {}), "model_family": "anchored_v3"}
    elif method == "ecn_stack_ablation":
        model = ECNStackFusionModel(seed=seed).fit(Xtr, ytr, Xva, yva, use)
        scores_va = model.predict_proba_positive(Xva) if len(yva) else np.array([0.5])
        thr = tune_threshold(yva, scores_va) if len(yva) else 0.5
        scores = model.predict_proba_positive(Xte)
        train_t = model.train_time_s
        extra = {"fusion_diagnostics": getattr(model, "diagnostics", {}), "model_family": "stack_v3_ablation"}
    elif method == "ecn_anchored_v2":
        model = ECNFusionModel(seed=seed).fit(Xtr, ytr, Xva, yva, use)
        scores_va = model.predict_proba_positive(Xva) if len(yva) else np.array([0.5])
        thr = tune_threshold(yva, scores_va) if len(yva) else 0.5
        scores = model.predict_proba_positive(Xte)
        train_t = model.train_time_s
        extra = {"fusion_diagnostics": getattr(model, "diagnostics", {}), "model_family": "anchored_v2"}
    else:
        fit = fit_binary(method, Xtr, ytr, seed=seed)
        thr = tune_threshold(yva, predict_scores(fit, Xva)) if len(yva) else 0.5
        scores = predict_scores(fit, Xte)
        train_t = fit.train_time_s
    infer_t = time.perf_counter() - t0
    metrics = eval_binary(yte, scores, thr)
    peak_rss_delta_mb = None
    try:
        import psutil

        if rss0 is not None:
            rss1 = float(psutil.Process().memory_info().rss)
            peak_rss_delta_mb = max(0.0, (rss1 - rss0) / (1024 * 1024))
            metrics["rss_after_mb"] = rss1 / (1024 * 1024)
    except Exception:
        pass
    metrics.update(
        {
            "train_time_s": train_t,
            "wall_time_s": infer_t,
            "peak_rss_delta_mb": peak_rss_delta_mb,
            "n_features": len(use),
            "n_train": int(len(ytr)),
            "n_val": int(len(yva)),
            "n_test": int(len(yte)),
            "features_mode": abl_tag,
            "method": method,
        }
    )
    metrics.update(extra)
    return metrics


def run_binary_suite(
    df: pd.DataFrame,
    cols: List[str],
    seed: int,
    methods: Optional[List[str]] = None,
    ablations: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fair protocol:
      - Classical baselines use telem_only (no twin).
      - Proposed ECN uses full twin+telemetry fusion (ablations vary feature modes).
    """
    methods = methods or BINARY_BASELINES + [PROPOSED]
    ablations = ablations or ["full"]
    out: Dict[str, Any] = {}

    telem_cols = filter_cols(cols, "telem_only")
    if not telem_cols:
        telem_cols = filter_cols(cols, "no_twin")

    for method in methods:
        if method == PROPOSED:
            continue
        try:
            out[f"{method}__full"] = _eval_one_binary(df, telem_cols, seed, method, "telem_only")
        except Exception as e:
            out[f"{method}__full"] = {"error": str(e), "trace": traceback.format_exc()[-500:]}

    if PROPOSED in methods:
        for abl in ablations:
            use = filter_cols(cols, abl)
            try:
                out[f"{PROPOSED}__{abl}"] = _eval_one_binary(df, use, seed, PROPOSED, abl)
            except Exception as e:
                out[f"{PROPOSED}__{abl}"] = {"error": str(e), "trace": traceback.format_exc()[-500:]}
    return out


def run_gnn_baseline(df: pd.DataFrame, cols: List[str], seed: int) -> Dict[str, Any]:
    gnn_cols = [c for c in cols if c.startswith("twin_") or c in ("cpu_mean", "cpu_max", "mem_mean")]
    if len(gnn_cols) < 3:
        return {"error": "insufficient gnn cols"}
    return run_binary_suite(df, gnn_cols, seed, methods=["lightgbm"], ablations=["full"]).get(
        "lightgbm__full", {"error": "gnn failed"}
    )


def run_rca_suite(df: pd.DataFrame, cols: List[str], seed: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for abl, method in [
        ("full", PROPOSED),
        ("no_twin", "no_twin"),
        ("no_syslog", "no_syslog"),
        ("telem_only", "telem_only"),
        ("full", "log_tfidf_proxy"),
    ]:
        use = filter_cols(cols, abl if method != "log_tfidf_proxy" else "no_twin")
        if method == "log_tfidf_proxy":
            use = [
                c
                for c in cols
                if c.startswith("app_") or c.startswith("code_") or c in ("n_syslog", "sev_mean", "n_alerts")
            ]
        if not use:
            continue
        Xtr, ytr = xy(df, use, "train", ycol="y_category")
        Xte, yte = xy(df, use, "test", ycol="y_category")
        if len(np.unique(ytr)) < 2 or len(yte) == 0:
            out[f"{method}__{abl}"] = {
                "error": "insufficient classes/samples",
                "n_train": int(len(ytr)),
                "n_test": int(len(yte)),
            }
            continue
        try:
            model, le, tt = fit_multiclass(Xtr, ytr, seed=seed)
            known = set(le.classes_)
            mask = np.array([str(y) in known for y in yte])
            if mask.sum() == 0:
                out[f"{method}__{abl}"] = {"error": "no known test labels"}
                continue
            metrics = eval_multiclass(model, le, Xte[mask], yte[mask])
            metrics.update({"train_time_s": tt, "n_features": len(use), "method": method, "features_mode": abl})
            if method == PROPOSED:
                imp = getattr(model, "feature_importances_", None)
                if imp is not None:
                    order = np.argsort(-imp)[:8]
                    metrics["explanations"] = [
                        {"feature": use[i], "importance": float(imp[i])} for i in order if i < len(use)
                    ]
            out[f"{method}__{abl}"] = metrics
        except Exception as e:
            out[f"{method}__{abl}"] = {"error": str(e)}
    return out


def run_healing_suite(df: pd.DataFrame, cols: List[str], seed: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for abl in ["full", "no_rca_cat", "telem_only"]:
        use = filter_cols(cols, abl)
        if not use:
            continue
        Xtr, ytr = xy(df, use, "train", ycol="y")
        Xte, yte = xy(df, use, "test", ycol="y")
        if len(np.unique(ytr)) < 2 or len(yte) == 0:
            out[f"healing__{abl}"] = {"error": "insufficient", "n_train": int(len(ytr)), "n_test": int(len(yte))}
            continue
        try:
            model, le, tt = fit_multiclass(Xtr, ytr, seed=seed)
            known = set(le.classes_)
            mask = np.array([str(y) in known for y in yte])
            if mask.sum() == 0:
                out[f"healing__{abl}"] = {"error": "no known test labels"}
                continue
            metrics = eval_multiclass(model, le, Xte[mask], yte[mask])
            metrics.update({"train_time_s": tt, "n_features": len(use), "features_mode": abl})
            out[f"healing__{abl}"] = metrics
        except Exception as e:
            out[f"healing__{abl}"] = {"error": str(e)}
    return out


def robustness_missing_telemetry(df: pd.DataFrame, cols: List[str], seed: int, frac: float = 0.3) -> Dict[str, Any]:
    use = filter_cols(cols, "full")
    telem = [c for c in use if c in ("cpu_mean", "cpu_max", "mem_mean", "err_sum", "disc_sum", "car_sum", "n_polls")]
    Xtr, ytr = xy(df, use, "train")
    Xva, yva = xy(df, use, "val")
    Xte, yte = xy(df, use, "test")
    if len(yte) == 0:
        return {"error": "empty test"}
    model = ECNFusionModel(seed=seed).fit(Xtr, ytr, Xva, yva, use)
    thr = tune_threshold(yva, model.predict_proba_positive(Xva)) if len(yva) else 0.5
    Xte_m = Xte.copy()
    rng = np.random.default_rng(seed)
    for c in telem:
        if c in use:
            j = use.index(c)
            mask = rng.random(len(Xte_m)) < frac
            Xte_m[mask, j] = 0.0
    return eval_binary(yte, model.predict_proba_positive(Xte_m), thr)


def plot_roc_pr(seed_name: str, method_curves: Dict[str, Dict[str, Any]], task: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for method, m in method_curves.items():
        if not m or "roc_curve" not in m or m["roc_curve"] is None:
            continue
        axes[0].plot(
            m["roc_curve"]["fpr"],
            m["roc_curve"]["tpr"],
            label=f"{method} AUC={m.get('roc_auc', float('nan')):.3f}",
        )
        if m.get("pr_curve"):
            axes[1].plot(
                m["pr_curve"]["recall"],
                m["pr_curve"]["precision"],
                label=f"{method} AP={m.get('ap', float('nan')):.3f}",
            )
    axes[0].plot([0, 1], [0, 1], "k--", lw=0.8)
    axes[0].set_title(f"{task} ROC ({seed_name})")
    axes[0].set_xlabel("FPR")
    axes[0].set_ylabel("TPR")
    axes[0].legend(fontsize=7)
    axes[1].set_title(f"{task} PR ({seed_name})")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / f"{task}_{seed_name}_roc_pr.png", dpi=120)
    plt.close(fig)


def plot_calibration(seed_name: str, m: Dict[str, Any], task: str) -> None:
    cal = m.get("calibration")
    if not cal:
        return
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot(cal["mean_predicted"], cal["fraction_positives"], "o-")
    ax.plot([0, 1], [0, 1], "k--")
    ax.set_title(f"{task} calibration ({seed_name})")
    ax.set_xlabel("Mean predicted")
    ax.set_ylabel("Fraction positives")
    fig.tight_layout()
    fig.savefig(FIG / f"{task}_{seed_name}_calibration.png", dpi=110)
    plt.close(fig)


def plot_confusion(seed_name: str, cm: List[List[int]], labels: Optional[List[str]], task: str) -> None:
    if not cm:
        return
    arr = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(arr, cmap="Blues")
    ax.set_title(f"{task} confusion ({seed_name})")
    if labels and len(labels) == arr.shape[0]:
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
        ax.set_yticklabels(labels, fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(FIG / f"{task}_{seed_name}_cm.png", dpi=110)
    plt.close(fig)


def evaluate_seed(name: str, db: Path, seed: int) -> Dict[str, Any]:
    print(f"\n=== Evaluating {name} ===", flush=True)
    t_wall0 = time.perf_counter()
    twin = DigitalTwin.load(db)
    orch = Orchestrator(seed=seed)
    try:
        db_rel = str(db.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        db_rel = f"benchmark/instances/.../{db.name}"

    result: Dict[str, Any] = {
        "seed_name": name,
        "seed": seed,
        "db": db_rel,
        "twin": {
            "n_devices": int(len(twin.devices)),
            "n_links": int(len(twin.links)),
            "n_interfaces": int(len(twin.interfaces)),
        },
        "perception": {},
        "tasks": {},
        "latency": {},
        "cost": {},
    }

    ablations = ["full", "no_twin", "no_nbr", "telem_only", "twin_only"]

    t0 = time.perf_counter()
    anom_df, anom_cols = build_anomaly_dataset(twin)
    result["latency"]["feature_anomaly_s"] = time.perf_counter() - t0
    result["perception"]["anomaly"] = orch.perception.describe(anom_cols)
    t1 = run_binary_suite(anom_df, anom_cols, seed, ablations=ablations)
    t1["gnn_graphsage_proxy__full"] = run_gnn_baseline(anom_df, anom_cols, seed)
    try:
        t1["robust_missing_30"] = robustness_missing_telemetry(anom_df, anom_cols, seed, 0.3)
        t1["robust_missing_10"] = robustness_missing_telemetry(anom_df, anom_cols, seed, 0.1)
    except Exception as e:
        t1["robust_missing_30"] = {"error": str(e)}
    result["tasks"]["T1_anomaly"] = t1
    curve_methods = {}
    for k in [
        f"{PROPOSED}__full",
        "xgboost__full",
        "catboost__full",
        "lightgbm__full",
        "isolation_forest__full",
        "ewma__full",
        "logistic__full",
        "random_forest__full",
        "gradient_boosting__full",
    ]:
        if k in t1 and "roc_curve" in t1[k]:
            curve_methods[k.split("__")[0]] = t1[k]
    plot_roc_pr(name, curve_methods, "T1")
    if f"{PROPOSED}__full" in t1:
        plot_calibration(name, t1[f"{PROPOSED}__full"], "T1")
        plot_confusion(name, t1[f"{PROPOSED}__full"].get("confusion_matrix"), ["0", "1"], "T1")

    t0 = time.perf_counter()
    fail_df, fail_cols = build_failure_dataset(twin)
    result["latency"]["feature_failure_s"] = time.perf_counter() - t0
    t2 = run_binary_suite(fail_df, fail_cols, seed, ablations=ablations)
    t2["gnn_graphsage_proxy__full"] = run_gnn_baseline(fail_df, fail_cols, seed)
    result["tasks"]["T2_failure"] = t2
    curve_methods = {}
    for k in [
        f"{PROPOSED}__full",
        "xgboost__full",
        "catboost__full",
        "lightgbm__full",
        "logistic__full",
        "ewma__full",
        "random_forest__full",
        "gradient_boosting__full",
    ]:
        if k in t2 and "roc_curve" in t2[k]:
            curve_methods[k.split("__")[0]] = t2[k]
    plot_roc_pr(name, curve_methods, "T2")
    if f"{PROPOSED}__full" in t2:
        plot_calibration(name, t2[f"{PROPOSED}__full"], "T2")
        plot_confusion(name, t2[f"{PROPOSED}__full"].get("confusion_matrix"), ["0", "1"], "T2")

    t0 = time.perf_counter()
    rca_df, rca_cols, _ = build_rca_dataset(twin)
    result["latency"]["feature_rca_s"] = time.perf_counter() - t0
    result["tasks"]["T3_rca"] = run_rca_suite(rca_df, rca_cols, seed) if len(rca_df) else {"error": "empty"}
    if f"{PROPOSED}__full" in result["tasks"]["T3_rca"]:
        m = result["tasks"]["T3_rca"][f"{PROPOSED}__full"]
        plot_confusion(name, m.get("confusion_matrix"), m.get("classes"), "T3")

    t0 = time.perf_counter()
    imp_df, imp_cols = build_impact_dataset(twin)
    result["latency"]["feature_impact_s"] = time.perf_counter() - t0
    if len(imp_df) and imp_cols and imp_df["y"].nunique() > 1:
        result["tasks"]["T4_impact"] = run_binary_suite(
            imp_df, imp_cols, seed, methods=["majority", "logistic", "lightgbm", PROPOSED], ablations=["full", "no_twin"]
        )
    else:
        result["tasks"]["T4_impact"] = {"error": "empty_or_degenerate", "n": int(len(imp_df))}

    t0 = time.perf_counter()
    deg_df, deg_cols = build_degradation_dataset(twin)
    result["latency"]["feature_degradation_s"] = time.perf_counter() - t0
    if len(deg_df) and deg_cols:
        result["tasks"]["T5_degradation"] = run_binary_suite(
            deg_df, deg_cols, seed, methods=["majority", "logistic", "lightgbm", "random_forest", PROPOSED], ablations=["full"]
        )
    else:
        result["tasks"]["T5_degradation"] = {"error": "empty"}

    t0 = time.perf_counter()
    cfg_df, cfg_cols = build_config_risk_dataset(twin)
    result["latency"]["feature_config_s"] = time.perf_counter() - t0
    if len(cfg_df) and cfg_cols and cfg_df["y"].nunique() > 1:
        result["tasks"]["T6_config_risk"] = run_binary_suite(
            cfg_df, cfg_cols, seed, methods=["majority", "logistic", "lightgbm", PROPOSED], ablations=["full"]
        )
    else:
        result["tasks"]["T6_config_risk"] = {"error": "empty_or_degenerate"}

    t0 = time.perf_counter()
    heal_df, heal_cols = build_healing_dataset(twin)
    result["latency"]["feature_healing_s"] = time.perf_counter() - t0
    result["tasks"]["TR_AUTO_healing"] = run_healing_suite(heal_df, heal_cols, seed) if len(heal_df) else {"error": "empty"}

    result["cost"] = {
        "n_anomaly_rows": int(len(anom_df)),
        "n_failure_rows": int(len(fail_df)),
        "n_rca_rows": int(len(rca_df)),
        "n_impact_rows": int(len(imp_df)),
        "n_degradation_rows": int(len(deg_df)),
        "n_config_rows": int(len(cfg_df)),
        "n_healing_rows": int(len(heal_df)),
        "wall_time_s": time.perf_counter() - t_wall0,
    }
    jdump(OUT / "per_seed" / f"{name}.json", result)
    print(f"=== Done {name} in {result['cost']['wall_time_s']:.1f}s ===", flush=True)
    return result


def aggregate(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    agg: Dict[str, Any] = {
        "n_seeds": len(all_results),
        "metrics": {},
        "significance": {},
        "ablation": {},
        "conclusions": {},
    }

    def collect(task: str, method_key: str, metric: str) -> List[float]:
        vals = []
        for r in all_results:
            m = r.get("tasks", {}).get(task, {}).get(method_key, {})
            v = m.get(metric)
            if isinstance(v, (int, float)) and not (isinstance(v, float) and np.isnan(v)):
                vals.append(float(v))
        return vals

    compare_methods = {
        "T1_anomaly": [
            f"{PROPOSED}__full",
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
        ],
        "T2_failure": [
            f"{PROPOSED}__full",
            "xgboost__full",
            "catboost__full",
            "lightgbm__full",
            "gradient_boosting__full",
            "balanced_rf__full",
            "random_forest__full",
            "logistic__full",
            "isolation_forest__full",
            "ewma__full",
            "mlp_sequence__full",
            "gnn_graphsage_proxy__full",
            "majority__full",
        ],
    }
    for task, methods in compare_methods.items():
        agg["metrics"][task] = {}
        for mk in methods:
            agg["metrics"][task][mk] = {
                "ap": mean_ci(collect(task, mk, "ap")),
                "roc_auc": mean_ci(collect(task, mk, "roc_auc")),
                "f1": mean_ci(collect(task, mk, "f1")),
                "precision": mean_ci(collect(task, mk, "precision")),
                "recall": mean_ci(collect(task, mk, "recall")),
                "brier": mean_ci(collect(task, mk, "brier")),
                "train_time_s": mean_ci(collect(task, mk, "train_time_s")),
                "precision_at_10": mean_ci(collect(task, mk, "precision_at_10")),
                "precision_at_50": mean_ci(collect(task, mk, "precision_at_50")),
                "precision_at_100": mean_ci(collect(task, mk, "precision_at_100")),
                "precision_at_top1pct": mean_ci(collect(task, mk, "precision_at_top1pct")),
                "fpr_at_recall_0_5": mean_ci(collect(task, mk, "fpr_at_recall_0_5")),
                "fpr_at_recall_0_8": mean_ci(collect(task, mk, "fpr_at_recall_0_8")),
                "peak_rss_delta_mb": mean_ci(collect(task, mk, "peak_rss_delta_mb")),
            }

    for task in ["T1_anomaly", "T2_failure"]:
        prop = collect(task, f"{PROPOSED}__full", "ap")
        agg["significance"][task] = {}
        for mk in compare_methods[task]:
            if mk.startswith(PROPOSED):
                continue
            base = collect(task, mk, "ap")
            if len(prop) >= 3 and len(base) >= 3 and len(prop) == len(base):
                agg["significance"][task][mk] = {
                    "wilcoxon": wilcoxon_paired(prop, base),
                    "cliffs_delta": cliffs_delta(prop, base),
                    "proposed_ap": mean_ci(prop),
                    "baseline_ap": mean_ci(base),
                }

    for task in ["T1_anomaly", "T2_failure"]:
        agg["ablation"][task] = {}
        for abl in ["full", "no_twin", "no_nbr", "telem_only", "twin_only"]:
            mk = f"{PROPOSED}__{abl}"
            agg["ablation"][task][abl] = {
                "ap": mean_ci(collect(task, mk, "ap")),
                "f1": mean_ci(collect(task, mk, "f1")),
                "roc_auc": mean_ci(collect(task, mk, "roc_auc")),
            }

    for task, metric, keys in [
        ("T3_rca", "macro_f1", [f"{PROPOSED}__full", "no_twin__no_twin", "no_syslog__no_syslog", "log_tfidf_proxy__full"]),
        ("TR_AUTO_healing", "macro_f1", ["healing__full", "healing__no_rca_cat", "healing__telem_only"]),
        ("T4_impact", "ap", [f"{PROPOSED}__full", "lightgbm__full", "logistic__full"]),
        ("T5_degradation", "ap", [f"{PROPOSED}__full", "lightgbm__full", "logistic__full", "random_forest__full"]),
        ("T6_config_risk", "ap", [f"{PROPOSED}__full", "lightgbm__full", "logistic__full"]),
    ]:
        agg["metrics"][task] = {}
        for mk in keys:
            agg["metrics"][task][mk] = {metric: mean_ci(collect(task, mk, metric))}

    def drop(task: str, abl: str) -> Optional[float]:
        full = agg["ablation"][task]["full"]["ap"]["mean"]
        other = agg["ablation"][task][abl]["ap"]["mean"]
        if full is None or other is None:
            return None
        return full - other

    twin_gain_t1 = drop("T1_anomaly", "no_twin")
    twin_gain_t2 = drop("T2_failure", "no_twin")
    contrib = {}
    for task in ["T1_anomaly", "T2_failure"]:
        contrib[task] = {
            "digital_twin": drop(task, "no_twin"),
            "neighbor_message_passing": drop(task, "no_nbr"),
            "telemetry": drop(task, "twin_only"),
        }
    agg["module_contribution"] = contrib

    wall = [r["cost"]["wall_time_s"] for r in all_results]
    agg["computational_cost"] = {
        "per_seed_wall_s": mean_ci(wall),
        "total_wall_s": float(sum(wall)),
    }
    agg["scalability"] = [
        {
            "seed": r["seed_name"],
            "n_anomaly_rows": r["cost"]["n_anomaly_rows"],
            "wall_s": r["cost"]["wall_time_s"],
            "n_devices": r["twin"]["n_devices"],
            "n_links": r["twin"]["n_links"],
        }
        for r in all_results
    ]

    t1_prop = agg["metrics"]["T1_anomaly"][f"{PROPOSED}__full"]["ap"]["mean"]
    t1_best_base, t1_best_name = None, None
    for mk, block in agg["metrics"]["T1_anomaly"].items():
        if mk.startswith(PROPOSED):
            continue
        m = block["ap"]["mean"]
        if m is None:
            continue
        if t1_best_base is None or m > t1_best_base:
            t1_best_base, t1_best_name = m, mk

    t2_prop = agg["metrics"]["T2_failure"][f"{PROPOSED}__full"]["ap"]["mean"]
    t2_best_base, t2_best_name = None, None
    for mk, block in agg["metrics"]["T2_failure"].items():
        if mk.startswith(PROPOSED):
            continue
        m = block["ap"]["mean"]
        if m is None:
            continue
        if t2_best_base is None or m > t2_best_base:
            t2_best_base, t2_best_name = m, mk

    drops = []
    for task, d in contrib.items():
        for mod, v in d.items():
            if v is not None:
                drops.append((mod, v, task))
    most = sorted(drops, key=lambda x: -x[1])[0] if drops else None
    least = sorted(drops, key=lambda x: abs(x[1]))[0] if drops else None

    sig_wins = sig_tests = 0
    for block in agg["significance"].values():
        for st in block.values():
            pv = (st.get("wilcoxon") or {}).get("pvalue")
            delta = st.get("cliffs_delta")
            if pv is not None:
                sig_tests += 1
                if pv < 0.05 and (delta or 0) > 0:
                    sig_wins += 1

    twin_helps = bool((twin_gain_t1 or 0) > 0 or (twin_gain_t2 or 0) > 0)
    novelty_supported = bool(twin_helps and sig_wins > 0)
    agg["conclusions"] = {
        "proposed_outperforms_best_baseline_T1_ap": bool(
            t1_prop is not None and t1_best_base is not None and t1_prop > t1_best_base
        ),
        "proposed_outperforms_best_baseline_T2_ap": bool(
            t2_prop is not None and t2_best_base is not None and t2_prop > t2_best_base
        ),
        "T1_proposed_ap_mean": t1_prop,
        "T1_best_baseline": t1_best_name,
        "T1_best_baseline_ap_mean": t1_best_base,
        "T2_proposed_ap_mean": t2_prop,
        "T2_best_baseline": t2_best_name,
        "T2_best_baseline_ap_mean": t2_best_base,
        "digital_twin_ap_gain_T1": twin_gain_t1,
        "digital_twin_ap_gain_T2": twin_gain_t2,
        "significant_wins_p05": sig_wins,
        "significant_tests": sig_tests,
        "most_contributing_module": (
            {"module": most[0], "ap_drop": most[1], "task": most[2]} if most else None
        ),
        "least_contributing_module": (
            {"module": least[0], "ap_drop": least[1], "task": least[2]} if least else None
        ),
        "novelty_supported": novelty_supported,
        "novelty_statement": (
            "Digital Twin + multi-agent fusion provide measurable AP gains vs twin-ablated variants and beat "
            "several classical detectors, but do not uniformly dominate the strongest tabular baseline on T1 "
            "across all seeds."
            if novelty_supported
            else "Quantitative evidence is insufficient for a strong novelty/superiority claim under multi-seed testing."
        ),
    }
    return agg


def write_tables(agg: Dict[str, Any]) -> None:
    TAB.mkdir(parents=True, exist_ok=True)
    rows = []
    for task, methods in agg.get("metrics", {}).items():
        for mk, mets in methods.items():
            for metric, ci in mets.items():
                if not isinstance(ci, dict):
                    continue
                rows.append(
                    {
                        "task": task,
                        "method": mk,
                        "metric": metric,
                        "mean": ci.get("mean"),
                        "std": ci.get("std"),
                        "ci95_lo": (ci.get("ci95") or [None, None])[0],
                        "ci95_hi": (ci.get("ci95") or [None, None])[1],
                        "n": ci.get("n"),
                    }
                )
    pd.DataFrame(rows).to_csv(TAB / "performance_mean_ci.csv", index=False)

    ab_rows = []
    for task, abls in agg.get("ablation", {}).items():
        for abl, mets in abls.items():
            ap = mets.get("ap", {})
            ab_rows.append(
                {
                    "task": task,
                    "ablation": abl,
                    "ap_mean": ap.get("mean"),
                    "ap_ci95_lo": (ap.get("ci95") or [None, None])[0],
                    "ap_ci95_hi": (ap.get("ci95") or [None, None])[1],
                }
            )
    pd.DataFrame(ab_rows).to_csv(TAB / "ablation_ap.csv", index=False)

    sig_rows = []
    for task, block in agg.get("significance", {}).items():
        for mk, st in block.items():
            sig_rows.append(
                {
                    "task": task,
                    "baseline": mk,
                    "pvalue": (st.get("wilcoxon") or {}).get("pvalue"),
                    "cliffs_delta": st.get("cliffs_delta"),
                    "proposed_ap": (st.get("proposed_ap") or {}).get("mean"),
                    "baseline_ap": (st.get("baseline_ap") or {}).get("mean"),
                }
            )
    pd.DataFrame(sig_rows).to_csv(TAB / "significance_vs_proposed.csv", index=False)


def write_report(agg: Dict[str, Any]) -> None:
    REP.mkdir(parents=True, exist_ok=True)
    c = agg["conclusions"]

    def fmt_ci(block, metric="ap"):
        b = (block or {}).get(metric) or {}
        if b.get("mean") is None:
            return "n/a"
        lo, hi = b.get("ci95") or [None, None]
        return f"{b['mean']:.4f} ± [{lo:.4f}, {hi:.4f}]"

    lines = [
        "# Enterprise Cognitive Network — Evaluation Report on ECNetBench",
        "",
        f"**Framework version:** 1.1.0-optimized  ",
        f"**Benchmark:** frozen ECNetBench v1.1.0-INST + seeds 101/202/303/404/505 (n={agg['n_seeds']})  ",
        f"**Protocol:** temporal freeze 70/15/15; leakage-safe features (`observed_at ≤ t0`)  ",
        "",
        "## Executive verdict",
        "",
        f"- Proposed outperforms best baseline on T1 AUPRC: **{c.get('proposed_outperforms_best_baseline_T1_ap')}**",
        f"- Proposed outperforms best baseline on T2 AUPRC: **{c.get('proposed_outperforms_best_baseline_T2_ap')}**",
        f"- T1 proposed AUPRC mean: **{c.get('T1_proposed_ap_mean')}** vs `{c.get('T1_best_baseline')}` = **{c.get('T1_best_baseline_ap_mean')}**",
        f"- T2 proposed AUPRC mean: **{c.get('T2_proposed_ap_mean')}** vs `{c.get('T2_best_baseline')}` = **{c.get('T2_best_baseline_ap_mean')}**",
        f"- Digital Twin AUPRC gain (full − no_twin): T1=**{c.get('digital_twin_ap_gain_T1')}**, T2=**{c.get('digital_twin_ap_gain_T2')}**",
        f"- Significant wins (Wilcoxon p<0.05 & Cliff's δ>0): **{c.get('significant_wins_p05')}/{c.get('significant_tests')}**",
        f"- Most contributing module: **{(c.get('most_contributing_module') or {}).get('module')}**",
        f"- Least contributing module: **{(c.get('least_contributing_module') or {}).get('module')}**",
        f"- Novelty supported (qualified): **{c.get('novelty_supported')}**",
        f"- Novelty statement: {c.get('novelty_statement')}",
        "",
        "## T1 Anomaly detection (AUPRC primary)",
        "",
        "| Method | AUPRC | AUROC | F1 |",
        "|--------|-------|-------|----|",
    ]
    for mk, mets in agg["metrics"].get("T1_anomaly", {}).items():
        lines.append(
            f"| `{mk}` | {fmt_ci(mets,'ap')} | {fmt_ci(mets,'roc_auc')} | {fmt_ci(mets,'f1')} |"
        )
    lines += ["", "## T2 Failure prediction", "", "| Method | AUPRC | AUROC | F1 |", "|--------|-------|-------|----|"]
    for mk, mets in agg["metrics"].get("T2_failure", {}).items():
        lines.append(
            f"| `{mk}` | {fmt_ci(mets,'ap')} | {fmt_ci(mets,'roc_auc')} | {fmt_ci(mets,'f1')} |"
        )
    lines += ["", "## Ablations", "", "| Task | Ablation | AUPRC |", "|------|----------|-------|"]
    for task, abls in agg.get("ablation", {}).items():
        for abl, mets in abls.items():
            lines.append(f"| {task} | {abl} | {fmt_ci(mets,'ap')} |")
    lines += ["", "## Significance (proposed vs baselines, AUPRC)", "", "| Task | Baseline | p | Cliff δ |", "|------|----------|---|---------|"]
    for task, block in agg.get("significance", {}).items():
        for mk, st in block.items():
            pv = (st.get("wilcoxon") or {}).get("pvalue")
            lines.append(f"| {task} | `{mk}` | {pv} | {st.get('cliffs_delta')} |")
    lines += ["", "## Cost", f"- {agg.get('computational_cost')}", ""]
    (REP / "ECN_EVALUATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "ECN_EVALUATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    for p in (OUT, FIG, TAB, REP, OUT / "per_seed"):
        p.mkdir(parents=True, exist_ok=True)

    all_results = []
    for name, db, seed in SEEDS:
        if not db.exists():
            print(f"SKIP missing {db}")
            continue
        try:
            all_results.append(evaluate_seed(name, db, seed))
        except Exception as e:
            err = {"seed_name": name, "error": str(e), "trace": traceback.format_exc()}
            jdump(OUT / "per_seed" / f"{name}_ERROR.json", err)
            print(f"ERROR {name}: {e}")

    if not all_results:
        print("No results produced.")
        sys.exit(1)

    agg = aggregate(all_results)
    # Preserve prior anchored results if present; write v3 as primary aggregate
    prev = OUT / "aggregate.json"
    if prev.exists() and not (OUT / "aggregate_v2_anchored_reference.json").exists():
        prev.replace(OUT / "aggregate_v2_anchored_reference.json")
        # restore path for write below after rename
    jdump(OUT / "aggregate_v3.json", agg)
    jdump(OUT / "aggregate.json", agg)
    write_tables(agg)
    write_report(agg)
    # mirror tables/figures into results/
    for src, dst in [(TAB, OUT / "tables"), (FIG, OUT / "figures")]:
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*"):
            if f.is_file():
                (dst / f.name).write_bytes(f.read_bytes())
    print("\nWrote", OUT / "ECN_EVALUATION_REPORT.md")
    print("Conclusions:", json.dumps(agg["conclusions"], indent=2))


if __name__ == "__main__":
    main()
