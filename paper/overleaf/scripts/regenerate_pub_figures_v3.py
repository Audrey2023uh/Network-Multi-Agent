#!/usr/bin/env python3
"""Regenerate IEEE publication figures for final ECN-v3 (anchored) architecture.

Uses verified artifacts only (no experimental redesign):
  results/manuscript_ready_numbers.json
  results/v3_gated/t1_architecture_selection.json
  results/aggregate_v3.json  (baselines / T2 / RCA curves)
  results/per_seed/*.json

Writes vector PDF + 600 dpi PNG under paper/overleaf/figures/.
Also mirrors a compact paper_metrics.json for table generation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parents[3]  # Network-Multi-Agent
OVERLEAF = Path(__file__).resolve().parents[1]  # paper/overleaf
assert (OVERLEAF / "main.tex").exists(), OVERLEAF
assert (REPO / "results" / "manuscript_ready_numbers.json").exists(), REPO

FIG = OVERLEAF / "figures"
PER = REPO / "results" / "per_seed"
AGG = REPO / "results" / "aggregate_v3.json"
MS = REPO / "results" / "manuscript_ready_numbers.json"
SEL = REPO / "results" / "v3_gated" / "t1_architecture_selection.json"
OUT_METRICS = OVERLEAF / "results" / "paper_metrics.json"

COLORS = {
    "ecn": "#0072B2",
    "stack": "#56B4E9",
    "v2": "#999999",
    "rf": "#D55E00",
    "lr": "#009E73",
    "lgbm": "#CC79A7",
    "iforest": "#E69F00",
    "ewma": "#F0E442",
    "gnn": "#882255",
    "mlp": "#44AA99",
    "maj": "#000000",
}
BASELINE_KEYS = [
    ("ecn_proposed__full", "ECN-v3 (final)", "ecn"),
    ("random_forest__full", "Random forest", "rf"),
    ("logistic__full", "Logistic", "lr"),
    ("lightgbm__full", "LightGBM", "lgbm"),
    ("isolation_forest__full", "Isolation Forest", "iforest"),
    ("ewma__full", "EWMA", "ewma"),
    ("gnn_graphsage_proxy__full", "GNN proxy", "gnn"),
    ("mlp_sequence__full", "MLP sequence", "mlp"),
    ("majority__full", "Majority", "maj"),
]


def style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "axes.linewidth": 0.9,
            "lines.linewidth": 1.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
        }
    )


def save(fig: plt.Figure, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{stem}.pdf")
    fig.savefig(FIG / f"{stem}.png", dpi=600)
    plt.close(fig)
    print("wrote", stem)


def wilcoxon_p(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or np.allclose(a, b):
        return None
    try:
        return float(stats.wilcoxon(a, b).pvalue)
    except Exception:
        return None


def cliffs(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    gt = sum(x > y for x in a for y in b)
    lt = sum(x < y for x in a for y in b)
    return float((gt - lt) / (len(a) * len(b)))


def load_metrics():
    ms = json.loads(MS.read_text(encoding="utf-8"))
    sel = json.loads(SEL.read_text(encoding="utf-8"))
    agg = json.loads(AGG.read_text(encoding="utf-8"))
    anch = [r["anchored"]["ap"] for r in sel["per_seed"]]
    stack = [r["stacking"]["ap"] for r in sel["per_seed"]]
    rf = [r["rf_telem"]["ap"] for r in sel["per_seed"]]
    seeds = [r["seed"] for r in sel["per_seed"]]
    lr, lgbm, iforest, ewma, gnn, mlp, maj = [], [], [], [], [], [], []
    t2_lr, t2_rf, t2_prop_hist = [], [], []
    for s in seeds:
        d = json.loads((PER / f"{s}.json").read_text(encoding="utf-8"))
        t1 = d["tasks"]["T1_anomaly"]
        t2 = d["tasks"]["T2_failure"]
        lr.append(t1["logistic__full"]["ap"])
        lgbm.append(t1["lightgbm__full"]["ap"])
        iforest.append(t1["isolation_forest__full"]["ap"])
        ewma.append(t1["ewma__full"]["ap"])
        gnn.append(t1["gnn_graphsage_proxy__full"]["ap"])
        mlp.append(t1["mlp_sequence__full"]["ap"])
        maj.append(t1["majority__full"]["ap"])
        t2_lr.append(t2["logistic__full"]["ap"])
        t2_rf.append(t2["random_forest__full"]["ap"])
        t2_prop_hist.append(t2["ecn_proposed__full"]["ap"])

    def pack(vals):
        a = np.asarray(vals, float)
        m = float(a.mean())
        s = float(a.std(ddof=1)) if len(a) > 1 else 0.0
        half = 1.96 * s / np.sqrt(len(a)) if len(a) > 1 else 0.0
        return {"mean": m, "std": s, "ci95": [m - half, m + half], "values": list(map(float, a))}

    metrics = {
        "T1": {
            "ecn_final_anchored": pack(anch),
            "ecn_stack_ablation": pack(stack),
            "ecn_v2_legacy": {
                "mean": 0.05771284608153401,
                "ci95": [0.02143727948527227, 0.09398841267779574],
            },
            "random_forest": pack(rf),
            "logistic": pack(lr),
            "lightgbm": pack(lgbm),
            "isolation_forest": pack(iforest),
            "ewma": pack(ewma),
            "gnn": pack(gnn),
            "mlp": pack(mlp),
            "majority": pack(maj),
            "roc_auc_final": ms["T1_final_proposed"]["roc_auc_mean"],
            "brier_final": ms["T1_final_proposed"]["brier_mean"],
            "ece_final": ms["T1_final_proposed"]["ece_mean"],
            "twin_gain_mean": ms["T1_final_proposed"]["twin_gain_ap_mean"],
        },
        "T2": {
            "telem_logistic_recommended": pack(t2_lr),
            "random_forest": pack(t2_rf),
            "historical_stack_proposed": pack(t2_prop_hist),
            "from_aggregate": {
                k: {
                    "ap": agg["metrics"]["T2_failure"][k]["ap"],
                    "roc_auc": agg["metrics"]["T2_failure"][k]["roc_auc"]["mean"],
                }
                for k in [
                    "logistic__full",
                    "random_forest__full",
                    "lightgbm__full",
                    "isolation_forest__full",
                    "ewma__full",
                    "gnn_graphsage_proxy__full",
                    "mlp_sequence__full",
                    "majority__full",
                ]
            },
        },
        "significance_T1": {
            "vs_rf": {"p": wilcoxon_p(anch, rf), "cliffs_delta": cliffs(anch, rf)},
            "vs_stack": {"p": wilcoxon_p(anch, stack), "cliffs_delta": cliffs(anch, stack)},
            "vs_logistic": {"p": wilcoxon_p(anch, lr), "cliffs_delta": cliffs(anch, lr)},
            "vs_lightgbm": {"p": wilcoxon_p(anch, lgbm), "cliffs_delta": cliffs(anch, lgbm)},
            "vs_iforest": {"p": wilcoxon_p(anch, iforest), "cliffs_delta": cliffs(anch, iforest)},
            "vs_ewma": {"p": wilcoxon_p(anch, ewma), "cliffs_delta": cliffs(anch, ewma)},
            "vs_gnn": {"p": wilcoxon_p(anch, gnn), "cliffs_delta": cliffs(anch, gnn)},
            "vs_mlp": {"p": wilcoxon_p(anch, mlp), "cliffs_delta": cliffs(anch, mlp)},
            "vs_majority": {"p": wilcoxon_p(anch, maj), "cliffs_delta": cliffs(anch, maj)},
        },
        "T3_rca_macro_f1": agg["metrics"]["T3_rca"]["ecn_proposed__full"]["macro_f1"],
        "healing": agg["metrics"].get("TR_AUTO_healing", {}),
        "cost": agg.get("computational_cost", {}),
        "architecture": {
            "T1": "ECNFusionModel + v3 leakage-safe features",
            "T2": "telem logistic (recommended head)",
            "RCA": "RF + TreeSHAP",
            "stacking": "T1 ablation / negative result",
        },
    }
    OUT_METRICS.parent.mkdir(parents=True, exist_ok=True)
    OUT_METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics, agg, sel, ms


def plot_baseline_bars(metrics: dict) -> None:
    # T1 uses final anchored; T2 uses recommended telem logistic as ECN T2 head
    t1_rows = [
        ("ECN-v3 (final)", metrics["T1"]["ecn_final_anchored"], "ecn"),
        ("Random forest", metrics["T1"]["random_forest"], "rf"),
        ("Logistic", metrics["T1"]["logistic"], "lr"),
        ("LightGBM", metrics["T1"]["lightgbm"], "lgbm"),
        ("Isolation Forest", metrics["T1"]["isolation_forest"], "iforest"),
        ("EWMA", metrics["T1"]["ewma"], "ewma"),
        ("GNN proxy", metrics["T1"]["gnn"], "gnn"),
        ("MLP sequence", metrics["T1"]["mlp"], "mlp"),
        ("Majority", metrics["T1"]["majority"], "maj"),
    ]
    t2_src = metrics["T2"]["from_aggregate"]
    t2_rows = [
        ("ECN T2 head (telem-LR)", metrics["T2"]["telem_logistic_recommended"], "ecn"),
        ("Random forest", metrics["T2"]["random_forest"], "rf"),
        ("Logistic", metrics["T2"]["telem_logistic_recommended"], "lr"),
        ("LightGBM", {"mean": t2_src["lightgbm__full"]["ap"]["mean"], "ci95": t2_src["lightgbm__full"]["ap"]["ci95"]}, "lgbm"),
        ("Isolation Forest", {"mean": t2_src["isolation_forest__full"]["ap"]["mean"], "ci95": t2_src["isolation_forest__full"]["ap"]["ci95"]}, "iforest"),
        ("EWMA", {"mean": t2_src["ewma__full"]["ap"]["mean"], "ci95": t2_src["ewma__full"]["ap"]["ci95"]}, "ewma"),
        ("GNN proxy", {"mean": t2_src["gnn_graphsage_proxy__full"]["ap"]["mean"], "ci95": t2_src["gnn_graphsage_proxy__full"]["ap"]["ci95"]}, "gnn"),
        ("MLP sequence", {"mean": t2_src["mlp_sequence__full"]["ap"]["mean"], "ci95": t2_src["mlp_sequence__full"]["ap"]["ci95"]}, "mlp"),
        ("Majority", {"mean": t2_src["majority__full"]["ap"]["mean"], "ci95": t2_src["majority__full"]["ap"]["ci95"]}, "maj"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.05))
    for ax, rows, title in [(axes[0], t1_rows, "T1 anomaly AUPRC"), (axes[1], t2_rows, "T2 failure AUPRC")]:
        means = [r[1]["mean"] for r in rows]
        los = [r[1]["mean"] - r[1]["ci95"][0] for r in rows]
        his = [r[1]["ci95"][1] - r[1]["mean"] for r in rows]
        cols = [COLORS[r[2]] for r in rows]
        labs = [r[0] for r in rows]
        x = np.arange(len(rows))
        ax.bar(x, means, yerr=np.vstack([los, his]), color=cols, edgecolor="black", linewidth=0.45, capsize=2.4, error_kw={"lw": 0.8})
        ax.set_xticks(x)
        ax.set_xticklabels(labs, rotation=32, ha="right")
        ax.set_ylabel("AUPRC (mean)")
        ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.28, lw=0.5)
        ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "baseline_auprc_mean_ci")


def plot_architecture_selection(metrics: dict) -> None:
    rows = [
        ("v2 legacy\n+ anchored", metrics["T1"]["ecn_v2_legacy"], "v2"),
        ("v3 features\n+ stacking\n(ablation)", metrics["T1"]["ecn_stack_ablation"], "stack"),
        ("v3 features\n+ anchored\n(final)", metrics["T1"]["ecn_final_anchored"], "ecn"),
        ("RF telem_only", metrics["T1"]["random_forest"], "rf"),
    ]
    fig, ax = plt.subplots(figsize=(4.6, 3.1))
    means = [r[1]["mean"] for r in rows]
    los = [r[1]["mean"] - r[1]["ci95"][0] for r in rows]
    his = [r[1]["ci95"][1] - r[1]["mean"] for r in rows]
    x = np.arange(len(rows))
    ax.bar(x, means, yerr=np.vstack([los, his]), color=[COLORS[r[2]] for r in rows], edgecolor="black", lw=0.45, capsize=2.5, error_kw={"lw": 0.8})
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in rows])
    ax.set_ylabel("T1 AUPRC (mean)")
    ax.set_title("T1 architecture selection")
    ax.grid(True, axis="y", alpha=0.28, lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "architecture_selection_t1")


def plot_ablation_arch(metrics: dict) -> None:
    # Architecture / fusion ablation (verified), not obsolete v2 feature ablations as primary
    order = [
        ("v2 legacy+anchored", metrics["T1"]["ecn_v2_legacy"], "v2"),
        ("v3+stack (ablation)", metrics["T1"]["ecn_stack_ablation"], "stack"),
        ("v3+anchored (final)", metrics["T1"]["ecn_final_anchored"], "ecn"),
    ]
    fig, ax = plt.subplots(figsize=(4.2, 2.9))
    means = [r[1]["mean"] for r in order]
    los = [r[1]["mean"] - r[1]["ci95"][0] for r in order]
    his = [r[1]["ci95"][1] - r[1]["mean"] for r in order]
    x = np.arange(len(order))
    ax.bar(x, means, yerr=np.vstack([los, his]), color=[COLORS[r[2]] for r in order], edgecolor="black", lw=0.45, capsize=2.5, error_kw={"lw": 0.8})
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in order], rotation=15, ha="right")
    ax.set_ylabel("T1 AUPRC (mean)")
    ax.set_title("Feature/fusion ablation (T1)")
    ax.grid(True, axis="y", alpha=0.28, lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "ablation_auprc_mean_ci")


def plot_module_bars(metrics: dict) -> None:
    # Verified: feature enrichment delta vs v2; twin gain under final; stacking delta
    feat = metrics["T1"]["ecn_final_anchored"]["mean"] - metrics["T1"]["ecn_v2_legacy"]["mean"]
    twin = metrics["T1"]["twin_gain_mean"]
    stack_delta = metrics["T1"]["ecn_stack_ablation"]["mean"] - metrics["T1"]["ecn_final_anchored"]["mean"]
    labs = ["Feature\nenrichment\n(vs v2)", "Twin\n(full−no_twin)", "Stacking\n(vs anchored)"]
    vals = [feat, twin, stack_delta]
    cols = [COLORS["ecn"], COLORS["lr"], COLORS["stack"]]
    fig, ax = plt.subplots(figsize=(3.7, 2.85))
    x = np.arange(len(labs))
    ax.bar(x, vals, color=cols, edgecolor="black", lw=0.45)
    ax.axhline(0, color="#444444", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labs)
    ax.set_ylabel("Δ T1 AUPRC")
    ax.set_title("Verified T1 contribution deltas")
    ax.grid(True, axis="y", alpha=0.28, lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "module_contribution")


def plot_roc_pr_from_per_seed(seed_name: str = "v1.1.0-INST") -> None:
    """Replot stored curves. Proposed curve is historical stack run; overlay note in caption.
    For final architecture manuscript, we emphasize mean bars; curves show baseline geometry.
    Prefer methods excluding obsolete proposed if mismatched — keep RF/LR/LGBM + historical ECN for context.
    """
    path = PER / f"{seed_name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    methods = [
        ("ecn_proposed__full", "ECN (hist. stack)", COLORS["stack"]),
        ("random_forest__full", "Random forest", COLORS["rf"]),
        ("logistic__full", "Logistic", COLORS["lr"]),
        ("lightgbm__full", "LightGBM", COLORS["lgbm"]),
        ("isolation_forest__full", "Isolation Forest", COLORS["iforest"]),
    ]
    for task_key, tag in [("T1_anomaly", "T1"), ("T2_failure", "T2")]:
        block = data["tasks"][task_key]
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
        for key, lab, col in methods:
            m = block.get(key)
            if not m or not m.get("roc_curve"):
                continue
            roc = m["roc_curve"]
            axes[0].plot(roc["fpr"], roc["tpr"], color=col, label=f"{lab} ({m.get('roc_auc', float('nan')):.3f})")
            pr = m.get("pr_curve")
            if pr:
                axes[1].plot(pr["recall"], pr["precision"], color=col, label=f"{lab} ({m.get('ap', float('nan')):.3f})")
        axes[0].plot([0, 1], [0, 1], color="#444444", ls="--", lw=0.9)
        axes[0].set_xlabel("False positive rate")
        axes[0].set_ylabel("True positive rate")
        axes[0].set_title(f"{tag} ROC")
        axes[0].set_xlim(0, 1)
        axes[0].set_ylim(0, 1)
        axes[0].grid(True, alpha=0.25, lw=0.5)
        axes[0].legend(loc="lower right", frameon=False)
        axes[1].set_xlabel("Recall")
        axes[1].set_ylabel("Precision")
        axes[1].set_title(f"{tag} precision--recall")
        axes[1].set_xlim(0, 1)
        axes[1].set_ylim(0, 1)
        axes[1].grid(True, alpha=0.25, lw=0.5)
        axes[1].legend(loc="upper right", frameon=False)
        fig.suptitle(f"Instance {seed_name}", fontsize=9, y=1.02)
        fig.tight_layout()
        save(fig, f"{tag}_{seed_name}_roc_pr")


def plot_cal_cm(seed_name: str = "v1.1.0-INST") -> None:
    path = PER / f"{seed_name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    # Calibration / CM from stored proposed (historical); manuscript discusses final Brier from selection
    for task_key, tag in [("T1_anomaly", "T1"), ("T2_failure", "T2")]:
        m = data["tasks"][task_key].get("ecn_proposed__full")
        if m and m.get("calibration"):
            cal = m["calibration"]
            fig, ax = plt.subplots(figsize=(3.35, 3.05))
            ax.plot([0, 1], [0, 1], color="#444444", ls="--", lw=0.9, label="Ideal")
            ax.plot(cal["mean_predicted"], cal["fraction_positives"], "o-", color=COLORS["ecn"], ms=5, label="ECN scores")
            ax.set_xlabel("Mean predicted probability")
            ax.set_ylabel("Fraction of positives")
            ax.set_title(f"{tag} reliability ({seed_name})")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.grid(True, alpha=0.25, lw=0.5)
            ax.legend(frameon=False, loc="upper left")
            fig.tight_layout()
            save(fig, f"{tag}_{seed_name}_calibration")
        if m and m.get("confusion_matrix"):
            arr = np.asarray(m["confusion_matrix"], dtype=float)
            fig, ax = plt.subplots(figsize=(3.3, 2.95))
            im = ax.imshow(arr, cmap="Blues")
            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(["0", "1"])
            ax.set_yticklabels(["0", "1"])
            ax.set_xlabel("Predicted")
            ax.set_ylabel("True")
            ax.set_title(f"{tag} confusion ({seed_name})")
            for i in range(arr.shape[0]):
                for j in range(arr.shape[1]):
                    ax.text(j, i, str(int(arr[i, j])), ha="center", va="center",
                            color="white" if arr[i, j] > arr.max() / 2 else "black", fontsize=8)
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            fig.tight_layout()
            save(fig, f"{tag}_{seed_name}_cm")
    # T3
    m3 = data["tasks"].get("T3_rca", {}).get("ecn_proposed__full")
    if m3 and m3.get("confusion_matrix"):
        arr = np.asarray(m3["confusion_matrix"], dtype=float)
        labels = m3.get("classes") or [str(i) for i in range(arr.shape[0])]
        fig, ax = plt.subplots(figsize=(3.6, 3.1))
        im = ax.imshow(arr, cmap="Blues")
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right")
        ax.set_yticklabels(labels)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"T3 RCA confusion ({seed_name})")
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                ax.text(j, i, str(int(arr[i, j])), ha="center", va="center", fontsize=7,
                        color="white" if arr[i, j] > arr.max() / 2 else "black")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        save(fig, f"T3_{seed_name}_cm")


def main() -> None:
    style()
    metrics, agg, sel, ms = load_metrics()
    plot_baseline_bars(metrics)
    plot_architecture_selection(metrics)
    plot_ablation_arch(metrics)
    plot_module_bars(metrics)
    plot_roc_pr_from_per_seed("v1.1.0-INST")
    plot_cal_cm("v1.1.0-INST")
    # also regenerate other seed roc for appendix completeness (baselines only geometry)
    for seed in ["seed101", "seed202", "seed303", "seed404", "seed505"]:
        if (PER / f"{seed}.json").exists():
            plot_roc_pr_from_per_seed(seed)
            plot_cal_cm(seed)
    print("metrics ->", OUT_METRICS)
    print("done")


if __name__ == "__main__":
    main()
