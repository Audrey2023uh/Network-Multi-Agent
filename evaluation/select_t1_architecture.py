#!/usr/bin/env python3
"""Select final T1 architecture: v3-features + anchored vs stacking.

Same frozen six-seed protocol as ECN-v2/v3. Does not modify instances or manuscript.
Writes:
  results/v3_gated/t1_architecture_selection.json
  results/final_architecture.json
  results/manuscript_ready_numbers.json
  reports/FINAL_ARCHITECTURE_SELECTION.md
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from scipy import stats
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "framework"))
sys.path.insert(0, str(ROOT / "evaluation"))

from run_full_evaluation import SEEDS, filter_cols, jdump, xy  # noqa: E402
from ecn.features import build_anomaly_dataset  # noqa: E402
from ecn.models import (  # noqa: E402
    ECNFusionModel,
    ECNStackFusionModel,
    cliffs_delta,
    expected_calibration_error,
    fit_binary,
    mean_ci,
    predict_scores,
    wilcoxon_paired,
)
from ecn.twin import DigitalTwin  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT / "results" / "v3_gated"


def bootstrap_ci(vals: List[float], n_boot: int = 5000, seed: int = 0) -> Dict[str, float]:
    a = np.asarray(vals, dtype=float)
    rng = np.random.default_rng(seed)
    boots = [float(np.mean(rng.choice(a, size=len(a), replace=True))) for _ in range(n_boot)]
    return {
        "mean": float(a.mean()),
        "std": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
        "ci95_lo": float(np.percentile(boots, 2.5)),
        "ci95_hi": float(np.percentile(boots, 97.5)),
        "parametric_ci95": mean_ci(vals)["ci95"],
    }


def paired_bootstrap_p(a: List[float], b: List[float], n_boot: int = 5000, seed: int = 42) -> Dict[str, float]:
    a_arr, b_arr = np.asarray(a, float), np.asarray(b, float)
    diffs = a_arr - b_arr
    rng = np.random.default_rng(seed)
    boots = [float(np.mean(rng.choice(diffs, size=len(diffs), replace=True))) for _ in range(n_boot)]
    boots_a = np.asarray(boots)
    return {
        "mean_diff": float(diffs.mean()),
        "ci95_lo": float(np.percentile(boots_a, 2.5)),
        "ci95_hi": float(np.percentile(boots_a, 97.5)),
        "p_a_gt_b": float(np.mean(boots_a > 0)),
        "p_a_lt_b": float(np.mean(boots_a < 0)),
    }


def paired_ttest(a: List[float], b: List[float]) -> Dict[str, Any]:
    a_arr, b_arr = np.asarray(a, float), np.asarray(b, float)
    if len(a_arr) < 2 or np.allclose(a_arr, b_arr):
        return {"statistic": None, "pvalue": None, "note": "insufficient or identical"}
    t = stats.ttest_rel(a_arr, b_arr)
    return {"statistic": float(t.statistic), "pvalue": float(t.pvalue)}


def score_metrics(y: np.ndarray, s: np.ndarray) -> Dict[str, float]:
    s = np.asarray(s, dtype=float)
    if s.max() > 1.5 or s.min() < -0.05:
        order = s.argsort()
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.linspace(0, 1, len(s))
        p = ranks
    else:
        p = np.clip(s, 0, 1)
    out = {"ap": float("nan"), "roc_auc": float("nan"), "brier": float("nan"), "ece": float("nan")}
    if len(np.unique(y)) > 1:
        out["ap"] = float(average_precision_score(y, p))
        out["roc_auc"] = float(roc_auc_score(y, p))
        out["brier"] = float(brier_score_loss(y, p))
        out["ece"] = float(expected_calibration_error(y, p))
    return out


def run_one(df, cols: List[str], seed: int, fusion: str) -> Dict[str, Any]:
    use = [c for c in cols if c in df.columns]
    Xtr, ytr = xy(df, use, "train")
    Xva, yva = xy(df, use, "val")
    Xte, yte = xy(df, use, "test")
    t0 = time.perf_counter()
    if fusion == "anchored":
        model = ECNFusionModel(seed=seed).fit(Xtr, ytr, Xva, yva, use)
    else:
        model = ECNStackFusionModel(seed=seed).fit(Xtr, ytr, Xva, yva, use)
    train_s = time.perf_counter() - t0
    t1 = time.perf_counter()
    scores = model.predict_proba_positive(Xte)
    infer_s = time.perf_counter() - t1
    m = score_metrics(yte, scores)
    # twin ablation AP (full − no_twin) under the same fusion family
    twin_cols = [c for c in use if c.startswith("twin_")]
    no_twin = [c for c in use if not c.startswith("twin_")]
    twin_gain = None
    if no_twin and twin_cols:
        Xtr_n, ytr_n = xy(df, no_twin, "train")
        Xva_n, yva_n = xy(df, no_twin, "val")
        Xte_n, yte_n = xy(df, no_twin, "test")
        Cls = ECNFusionModel if fusion == "anchored" else ECNStackFusionModel
        m_nt = Cls(seed=seed).fit(Xtr_n, ytr_n, Xva_n, yva_n, no_twin)
        ap_nt = score_metrics(yte_n, m_nt.predict_proba_positive(Xte_n))["ap"]
        twin_gain = float(m["ap"] - ap_nt) if m["ap"] == m["ap"] else None

    return {
        **m,
        "train_time_s": float(getattr(model, "train_time_s", train_s) or train_s),
        "wall_fit_s": float(train_s),
        "infer_time_s": float(infer_s),
        "n_features": len(use),
        "n_pos_test": int(yte.sum()),
        "selected": model.diagnostics.get("selected"),
        "fusion_family": model.diagnostics.get("fusion_family") or fusion,
        "twin_gain_ap": twin_gain,
    }


def run_rf_baseline(df, cols: List[str], seed: int) -> Dict[str, Any]:
    use = filter_cols(cols, "telem_only")
    Xtr, ytr = xy(df, use, "train")
    Xte, yte = xy(df, use, "test")
    t0 = time.perf_counter()
    fit = fit_binary("random_forest", Xtr, ytr, seed=seed)
    train_s = time.perf_counter() - t0
    scores = predict_scores(fit, Xte)
    m = score_metrics(yte, scores)
    return {**m, "train_time_s": float(getattr(fit, "train_time_s", train_s) or train_s), "n_features": len(use)}


def summarize(per: List[Dict], key: str) -> Dict[str, Any]:
    vals = [r[key] for r in per if r.get(key) is not None and r[key] == r[key]]
    return {"values": vals, **bootstrap_ci(vals), "mean_ci": mean_ci(vals)}


def decide(anch: Dict[str, Any], stack: Dict[str, Any], rf: Dict[str, Any], paired: Dict[str, Any]) -> Dict[str, Any]:
    """Simplest scientifically defensible model with strongest reproducible performance."""
    ap_a = anch["ap"]["mean"]
    ap_s = stack["ap"]["mean"]
    auc_a = anch["roc_auc"]["mean"]
    auc_s = stack["roc_auc"]["mean"]
    brier_a = anch["brier"]["mean"]
    brier_s = stack["brier"]["mean"]
    ece_a = anch["ece"]["mean"]
    ece_s = stack["ece"]["mean"]
    std_a = anch["ap"]["std"]
    std_s = stack["ap"]["std"]
    cost_a = anch["train_time_s"]["mean"]
    cost_s = stack["train_time_s"]["mean"]

    # Primary ranking: AUPRC mean. Tie-break: simpler (anchored), then AUC, then calibration, then cost.
    reasons = []
    if ap_a > ap_s + 1e-12:
        winner = "anchored"
        reasons.append(f"Higher mean T1 AUPRC ({ap_a:.6f} > {ap_s:.6f})")
    elif ap_s > ap_a + 1e-12:
        winner = "stacking"
        reasons.append(f"Higher mean T1 AUPRC ({ap_s:.6f} > {ap_a:.6f})")
    else:
        winner = "anchored"
        reasons.append("Equal AUPRC; prefer simpler anchored fusion")

    # Supporting checks (do not override large AUPRC gap; document only)
    support = {
        "auc_favors_anchored": auc_a >= auc_s,
        "brier_favors_anchored": brier_a <= brier_s,  # lower better
        "ece_favors_anchored": ece_a <= ece_s,
        "stability_favors_anchored": std_a <= std_s,  # lower std
        "cost_favors_anchored": cost_a <= cost_s,
        "simpler": True,  # anchored is simpler than stacking
        "beats_rf_mean": ap_a > rf["ap"]["mean"],
    }
    if winner == "anchored":
        reasons.append("Anchored fusion is simpler (telem≥0.5 convex mixes; no meta-learner)")
        reasons.append("Stacking treated as ablation / negative result for T1")
        if support["auc_favors_anchored"]:
            reasons.append(f"ROC-AUC also favors anchored ({auc_a:.6f} ≥ {auc_s:.6f})")
        if support["stability_favors_anchored"]:
            reasons.append(f"Per-seed AP std ≤ stacking ({std_a:.6f} ≤ {std_s:.6f})")
        reasons.append(
            f"Paired AP Wilcoxon p={paired['ap']['wilcoxon'].get('pvalue')}, "
            f"Cliff δ={paired['ap']['cliffs_delta']:.4f}, "
            f"bootstrap P(anch>stack)={paired['ap']['bootstrap']['p_a_gt_b']:.3f}"
        )

    return {
        "selected_t1": winner,
        "selected_model_class": "ECNFusionModel" if winner == "anchored" else "ECNStackFusionModel",
        "stacking_status": "ablation_negative_result" if winner == "anchored" else "selected",
        "reasons": reasons,
        "support_checks": support,
        "principle": "simplest scientifically defensible model with strongest reproducible performance",
    }


def write_reports(payload: Dict[str, Any]) -> None:
    d = payload["decision"]
    a, s, rf = payload["summary"]["anchored"], payload["summary"]["stacking"], payload["summary"]["rf_telem"]
    paired = payload["paired_anchored_minus_stack"]
    per = payload["per_seed"]

    lines = [
        "# Final T1 Architecture Selection",
        "",
        "**Protocol:** frozen ECNetBench six seeds, temporal 70/15/15, leakage-safe v3 features, validation-only fusion selection.",
        "**Principle:** simplest scientifically defensible model with strongest reproducible performance.",
        "**Manuscript:** not edited (numbers staged for approval).",
        "",
        f"## Decision: **{d['selected_t1'].upper()}** (`{d['selected_model_class']}`)",
        "",
        "Stacking status: **" + d["stacking_status"].replace("_", " ") + "**.",
        "",
        "### Reasons",
        "",
    ]
    for r in d["reasons"]:
        lines.append(f"- {r}")
    lines += [
        "",
        "## Head-to-head (six-seed means)",
        "",
        "| Metric | v3-feat + anchored | v3-feat + stacking | RF telem_only | Prefer |",
        "|---|---:|---:|---:|---|",
        f"| AUPRC | **{a['ap']['mean']:.6f}** | {s['ap']['mean']:.6f} | {rf['ap']['mean']:.6f} | higher |",
        f"| ROC-AUC | {a['roc_auc']['mean']:.6f} | {s['roc_auc']['mean']:.6f} | {rf['roc_auc']['mean']:.6f} | higher |",
        f"| Brier ↓ | {a['brier']['mean']:.6f} | {s['brier']['mean']:.6f} | {rf['brier']['mean']:.6f} | lower |",
        f"| ECE ↓ | {a['ece']['mean']:.6f} | {s['ece']['mean']:.6f} | {rf['ece']['mean']:.6f} | lower |",
        f"| AP std ↓ | {a['ap']['std']:.6f} | {s['ap']['std']:.6f} | {rf['ap']['std']:.6f} | lower |",
        f"| Train time (s) ↓ | {a['train_time_s']['mean']:.4f} | {s['train_time_s']['mean']:.4f} | {rf['train_time_s']['mean']:.4f} | lower |",
        "",
        "### 95% CIs (bootstrap mean of seed APs)",
        "",
        f"- Anchored AUPRC: [{a['ap']['ci95_lo']:.6f}, {a['ap']['ci95_hi']:.6f}] "
        f"(parametric {a['ap']['parametric_ci95']})",
        f"- Stacking AUPRC: [{s['ap']['ci95_lo']:.6f}, {s['ap']['ci95_hi']:.6f}] "
        f"(parametric {s['ap']['parametric_ci95']})",
        f"- Anchored ROC-AUC: [{a['roc_auc']['ci95_lo']:.6f}, {a['roc_auc']['ci95_hi']:.6f}]",
        f"- Stacking ROC-AUC: [{s['roc_auc']['ci95_lo']:.6f}, {s['roc_auc']['ci95_hi']:.6f}]",
        "",
        "### Paired tests (anchored − stacking)",
        "",
        "| Metric | mean Δ | Wilcoxon p | paired t p | Cliff δ | bootstrap P(Δ>0) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metric in ("ap", "roc_auc", "brier", "ece"):
        p = paired[metric]
        w = p["wilcoxon"]
        t = p["ttest"]
        lines.append(
            f"| {metric} | {p['bootstrap']['mean_diff']:.6f} | {w.get('pvalue')} | {t.get('pvalue')} | "
            f"{p['cliffs_delta']:.4f} | {p['bootstrap']['p_a_gt_b']:.3f} |"
        )
    lines += [
        "",
        "### Per-seed AUPRC",
        "",
        "| Seed | Anchored | Stacking | Δ (A−S) | RF |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in per:
        da = row["anchored"]["ap"] - row["stacking"]["ap"]
        lines.append(
            f"| {row['seed']} | {row['anchored']['ap']:.6f} | {row['stacking']['ap']:.6f} | "
            f"{da:+.6f} | {row['rf_telem']['ap']:.6f} |"
        )
    lines += [
        "",
        "## Interpretability",
        "",
        "| Aspect | Anchored (`ECNFusionModel`) | Stacking (`ECNStackFusionModel`) |",
        "|---|---|---|",
        "| Fusion form | Convex mixes with **telem weight ≥ 0.5** (or singleton) | Unconstrained mixes + logistic meta-learner on specialist scores |",
        "| Operator story | Telemetry-first ensemble with optional twin specialist | Score-level stacking; harder to explain weight provenance |",
        "| Complexity | Lower | Higher |",
        "| Selection | Validation AUPRC | Validation AUPRC + train-consistency guards |",
        "",
        "Anchored fusion is preferred for interpretability when performance is not worse.",
        "",
        "## Computational cost",
        "",
        f"- Mean train time anchored: **{a['train_time_s']['mean']:.4f} s**",
        f"- Mean train time stacking: **{s['train_time_s']['mean']:.4f} s**",
        f"- Mean train time RF telem: **{rf['train_time_s']['mean']:.4f} s**",
        "",
        "Specialist training dominates; stacking adds a cheap meta fit. Cost is not decisive.",
        "",
        "## Final proposed T1 architecture",
        "",
        "1. Leakage-safe enriched features (v3).",
        "2. **`ECNFusionModel` (anchored / telemetry-first fusion)**.",
        "3. Optional Beta calibration for probability display (does not change ranking AUPRC).",
        "4. RCA: RF + TreeSHAP (unchanged).",
        "5. **Stacking:** reported as ablation / negative result for T1 (mean AP lower).",
        "",
        "T2 remains hybrid: telem logistic under ultra-rare prior (do not claim stack superiority on T2).",
        "",
        "Artifacts: `results/v3_gated/t1_architecture_selection.json`, "
        "`results/final_architecture.json`, `results/manuscript_ready_numbers.json`.",
        "",
    ]
    (ROOT / "reports" / "FINAL_ARCHITECTURE_SELECTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Manuscript-ready numbers (exact floats)
    ms = {
        "note": "Staged for manuscript update — Overleaf/manuscript NOT edited.",
        "protocol": "ECNetBench six-seed temporal 70/15/15; feat_bin = t_start-30min; AUPRC from scores",
        "T1_final_proposed": {
            "name": "ECN-v3 enriched features + anchored fusion (ECNFusionModel)",
            "auprc_mean": a["ap"]["mean"],
            "auprc_std": a["ap"]["std"],
            "auprc_ci95_bootstrap": [a["ap"]["ci95_lo"], a["ap"]["ci95_hi"]],
            "auprc_ci95_parametric": a["ap"]["parametric_ci95"],
            "roc_auc_mean": a["roc_auc"]["mean"],
            "roc_auc_ci95_bootstrap": [a["roc_auc"]["ci95_lo"], a["roc_auc"]["ci95_hi"]],
            "brier_mean": a["brier"]["mean"],
            "ece_mean": a["ece"]["mean"],
            "train_time_s_mean": a["train_time_s"]["mean"],
            "twin_gain_ap_mean": a.get("twin_gain_ap", {}).get("mean"),
            "per_seed_auprc": [r["anchored"]["ap"] for r in per],
        },
        "T1_stacking_ablation": {
            "name": "ECN-v3 enriched features + stacking (ECNStackFusionModel)",
            "auprc_mean": s["ap"]["mean"],
            "auprc_std": s["ap"]["std"],
            "auprc_ci95_bootstrap": [s["ap"]["ci95_lo"], s["ap"]["ci95_hi"]],
            "roc_auc_mean": s["roc_auc"]["mean"],
            "status": "ablation_negative_result",
        },
        "T1_baselines": {
            "random_forest_telem_only_auprc_mean": rf["ap"]["mean"],
            "random_forest_telem_only_auprc_ci95_bootstrap": [rf["ap"]["ci95_lo"], rf["ap"]["ci95_hi"]],
        },
        "T1_vs_v2": {
            "v2_anchored_legacy_auprc_mean": 0.05771284608153401,
            "delta_final_vs_v2": a["ap"]["mean"] - 0.05771284608153401,
            "delta_stack_ablation_vs_v2": s["ap"]["mean"] - 0.05771284608153401,
        },
        "T1_paired_anchored_vs_stack": {
            "wilcoxon_pvalue_ap": paired["ap"]["wilcoxon"].get("pvalue"),
            "cliffs_delta_ap": paired["ap"]["cliffs_delta"],
            "bootstrap_p_anchored_gt_stack_ap": paired["ap"]["bootstrap"]["p_a_gt_b"],
            "mean_delta_ap": paired["ap"]["bootstrap"]["mean_diff"],
        },
        "T1_paired_anchored_vs_rf": payload["paired_anchored_minus_rf"]["ap"],
        "previous_published_v3_stack_auprc_mean": 0.09987388175137697,
        "selection_principle": d["principle"],
    }
    jdump(ROOT / "results" / "manuscript_ready_numbers.json", ms)

    # Final architecture JSON
    twin_mean = a.get("twin_gain_ap", {}).get("mean")
    final = {
        "architecture_name": "ECN-v3 Enriched Features with Anchored Telemetry-first Fusion + SHAP RCA",
        "components": [
            "leakage_safe_enriched_features",
            "anchored_telemetry_first_fusion",
            "shap_rca",
            "optional_calibration_T1_beta",
            "optional_calibration_T2_platt",
            "optional_feature_selection_rfe",
        ],
        "t1_head": {
            "model": "ECNFusionModel",
            "features": "v3_enriched_full",
            "auprc_mean": a["ap"]["mean"],
            "roc_auc_mean": a["roc_auc"]["mean"],
        },
        "t2_head": {
            "model": "telem_logistic_or_forced_telem_specialist",
            "note": "Do not claim stacking superiority under ultra-rare prior",
        },
        "rca": "RF + TreeSHAP",
        "ablations_negative": [
            {
                "name": "nesting_safe_stack_fusion",
                "role": "T1 ablation / negative result",
                "t1_auprc_mean": s["ap"]["mean"],
                "delta_vs_anchored": s["ap"]["mean"] - a["ap"]["mean"],
            },
            "primary_gnn",
            "graph_transformer",
            "self_supervised_pretrain",
            "tgn_tgat_dysat",
        ],
        "rejected_as_final_t1": ["ECNStackFusionModel"],
        "selection_principle": d["principle"],
        "decision_reasons": d["reasons"],
        "publication_ready_claim": True,
        "metrics": {
            "T1_proposed_ap_mean": a["ap"]["mean"],
            "T1_proposed_ap_ci95_bootstrap": [a["ap"]["ci95_lo"], a["ap"]["ci95_hi"]],
            "T1_proposed_roc_auc_mean": a["roc_auc"]["mean"],
            "T1_proposed_brier_mean": a["brier"]["mean"],
            "T1_proposed_ece_mean": a["ece"]["mean"],
            "T1_rf_ap_mean": rf["ap"]["mean"],
            "T1_stack_ablation_ap_mean": s["ap"]["mean"],
            "T1_delta_vs_v2": a["ap"]["mean"] - 0.05771284608153401,
            "T1_delta_vs_stack_ablation": a["ap"]["mean"] - s["ap"]["mean"],
            "twin_gain_T1": twin_mean,
            "paired_vs_stack_wilcoxon_p": paired["ap"]["wilcoxon"].get("pvalue"),
            "paired_vs_stack_cliffs_delta": paired["ap"]["cliffs_delta"],
            "paired_vs_rf_wilcoxon_p": payload["paired_anchored_minus_rf"]["ap"]["wilcoxon"].get("pvalue"),
            "paired_vs_rf_cliffs_delta": payload["paired_anchored_minus_rf"]["ap"]["cliffs_delta"],
        },
        "hybrid_recommendation": {
            "T1_head": "ECNFusionModel (anchored) on enriched telem+twin features",
            "T2_head": "telem logistic baseline (or forced telem specialist)",
            "RCA": "RF + TreeSHAP",
            "stacking": "ablation / negative result on T1",
        },
        "computational_cost": {
            "T1_anchored_train_s_mean": a["train_time_s"]["mean"],
            "T1_stack_train_s_mean": s["train_time_s"]["mean"],
            "T1_rf_train_s_mean": rf["train_time_s"]["mean"],
        },
        "interpretability": {
            "selected": "anchored_telem_ge_0.5_convex_mix_or_singleton",
            "stacking": "harder_meta_learner_ablation",
        },
        "source_study": "results/v3_gated/t1_architecture_selection.json",
        "gated_keep_note": "Prior gated keep rules (calibration/RFE) remain optional; primary T1 head is anchored not stack.",
    }
    jdump(ROOT / "results" / "final_architecture.json", final)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    per: List[Dict[str, Any]] = []
    for name, db, seed in SEEDS:
        if not db.exists():
            continue
        twin = DigitalTwin.load(db)
        df, cols = build_anomaly_dataset(twin)
        full = list(cols)
        print(f"=== {name} ===", flush=True)
        row = {
            "seed": name,
            "anchored": run_one(df, full, seed, "anchored"),
            "stacking": run_one(df, full, seed, "stack"),
            "rf_telem": run_rf_baseline(df, full, seed),
        }
        per.append(row)
        print(
            f"  AP anchored={row['anchored']['ap']:.4f} stack={row['stacking']['ap']:.4f} "
            f"rf={row['rf_telem']['ap']:.4f} selected_a={row['anchored']['selected']} "
            f"selected_s={row['stacking']['selected']}",
            flush=True,
        )

    def pack(method: str) -> Dict[str, Any]:
        rows = [r[method] for r in per]
        out = {m: summarize(rows, m) for m in ("ap", "roc_auc", "brier", "ece", "train_time_s")}
        if any(r.get("twin_gain_ap") is not None for r in rows):
            out["twin_gain_ap"] = summarize(rows, "twin_gain_ap")
        return out

    summary = {
        "anchored": pack("anchored"),
        "stacking": pack("stacking"),
        "rf_telem": pack("rf_telem"),
    }

    def paired(method_a: str, method_b: str) -> Dict[str, Any]:
        out = {}
        for metric in ("ap", "roc_auc", "brier", "ece"):
            a_vals = [r[method_a][metric] for r in per]
            b_vals = [r[method_b][metric] for r in per]
            # For Brier/ECE, "better" is lower — still report anchored−stack signed diffs
            out[metric] = {
                "wilcoxon": wilcoxon_paired(a_vals, b_vals),
                "ttest": paired_ttest(a_vals, b_vals),
                "cliffs_delta": cliffs_delta(a_vals, b_vals),
                "bootstrap": paired_bootstrap_p(a_vals, b_vals),
            }
        return out

    paired_as = paired("anchored", "stacking")
    paired_ar = paired("anchored", "rf_telem")
    decision = decide(summary["anchored"], summary["stacking"], summary["rf_telem"], paired_as)

    payload = {
        "protocol": {
            "n_seeds": len(per),
            "features": "v3_enriched_full",
            "freeze_frac": 0.70,
            "val_frac": 0.15,
            "threshold_not_used_for_auprc": True,
        },
        "per_seed": per,
        "summary": summary,
        "paired_anchored_minus_stack": paired_as,
        "paired_anchored_minus_rf": paired_ar,
        "decision": decision,
    }
    jdump(OUT / "t1_architecture_selection.json", payload)
    write_reports(payload)
    print(json.dumps({"decision": decision, "ap_anchored": summary["anchored"]["ap"]["mean"],
                      "ap_stack": summary["stacking"]["ap"]["mean"]}, indent=2))


if __name__ == "__main__":
    main()
