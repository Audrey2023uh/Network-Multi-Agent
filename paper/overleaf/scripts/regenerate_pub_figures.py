#!/usr/bin/env python3
"""Regenerate publication-quality figures from verified per-seed / aggregate JSON.

Does not recompute metrics — only replots stored curves and summary statistics.
Outputs vector PDF (+ 600 dpi PNG fallback) under figures/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
PER = ROOT / "results" / "per_seed"
AGG = ROOT / "results" / "aggregate.json"

# Colorblind-friendly, print-safe palette
COLORS = {
    "ecn_proposed__full": "#0072B2",
    "random_forest__full": "#D55E00",
    "logistic__full": "#009E73",
    "lightgbm__full": "#CC79A7",
    "isolation_forest__full": "#E69F00",
    "ewma__full": "#56B4E9",
    "gnn_graphsage_proxy__full": "#999999",
    "mlp_sequence__full": "#F0E442",
    "majority__full": "#000000",
}
LABELS = {
    "ecn_proposed__full": "ECN (proposed)",
    "random_forest__full": "Random forest",
    "logistic__full": "Logistic",
    "lightgbm__full": "LightGBM",
    "isolation_forest__full": "Isolation Forest",
    "ewma__full": "EWMA",
    "gnn_graphsage_proxy__full": "GNN proxy",
    "mlp_sequence__full": "MLP sequence",
    "majority__full": "Majority",
}
MAIN_METHODS = list(COLORS.keys())


def style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def save(fig: plt.Figure, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    pdf = FIG / f"{stem}.pdf"
    png = FIG / f"{stem}.png"
    fig.savefig(pdf)
    fig.savefig(png, dpi=600)
    plt.close(fig)
    print("wrote", pdf.name, png.name)


def plot_roc_pr(seed_file: Path, task_key: str, task_tag: str, methods: list[str]) -> None:
    data = json.loads(seed_file.read_text(encoding="utf-8"))
    seed_name = data.get("seed_name", seed_file.stem)
    block = data["tasks"][task_key]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.85))
    for method in methods:
        m = block.get(method)
        if not m or not m.get("roc_curve"):
            continue
        color = COLORS.get(method, None)
        lab = LABELS.get(method, method)
        roc = m["roc_curve"]
        axes[0].plot(
            roc["fpr"],
            roc["tpr"],
            color=color,
            label=f"{lab} ({m.get('roc_auc', float('nan')):.3f})",
        )
        pr = m.get("pr_curve")
        if pr:
            axes[1].plot(
                pr["recall"],
                pr["precision"],
                color=color,
                label=f"{lab} ({m.get('ap', float('nan')):.3f})",
            )
    axes[0].plot([0, 1], [0, 1], color="#444444", ls="--", lw=0.9)
    axes[0].set_xlabel("False positive rate")
    axes[0].set_ylabel("True positive rate")
    axes[0].set_title(f"{task_tag} ROC")
    axes[0].set_xlim(0, 1)
    axes[0].set_ylim(0, 1)
    axes[0].grid(True, alpha=0.25, lw=0.5)
    axes[0].legend(loc="lower right", frameon=False, ncol=1)

    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title(f"{task_tag} precision--recall")
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1)
    axes[1].grid(True, alpha=0.25, lw=0.5)
    axes[1].legend(loc="upper right", frameon=False, ncol=1)
    fig.suptitle(f"Instance {seed_name}", fontsize=9, y=1.02)
    fig.tight_layout()
    save(fig, f"{task_tag}_{seed_name}_roc_pr")


def plot_calibration(seed_file: Path, task_key: str, task_tag: str, method: str) -> None:
    data = json.loads(seed_file.read_text(encoding="utf-8"))
    seed_name = data.get("seed_name", seed_file.stem)
    m = data["tasks"][task_key].get(method)
    if not m or not m.get("calibration"):
        return
    cal = m["calibration"]
    fig, ax = plt.subplots(figsize=(3.35, 3.1))
    ax.plot([0, 1], [0, 1], color="#444444", ls="--", lw=0.9, label="Ideal")
    ax.plot(
        cal["mean_predicted"],
        cal["fraction_positives"],
        "o-",
        color=COLORS.get(method, "#0072B2"),
        ms=5,
        label=LABELS.get(method, method),
    )
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title(f"{task_tag} reliability ({seed_name})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.25, lw=0.5)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    save(fig, f"{task_tag}_{seed_name}_calibration")


def plot_cm(seed_file: Path, task_key: str, task_tag: str, method: str) -> None:
    data = json.loads(seed_file.read_text(encoding="utf-8"))
    seed_name = data.get("seed_name", seed_file.stem)
    m = data["tasks"][task_key].get(method)
    if not m or not m.get("confusion_matrix"):
        return
    arr = np.asarray(m["confusion_matrix"], dtype=float)
    labels = m.get("classes") or (["0", "1"] if arr.shape[0] == 2 else [str(i) for i in range(arr.shape[0])])
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    im = ax.imshow(arr, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"{task_tag} confusion ({seed_name})")
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            val = int(arr[i, j])
            ax.text(j, i, str(val), ha="center", va="center", color="white" if arr[i, j] > arr.max() / 2 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    save(fig, f"{task_tag}_{seed_name}_cm")


def plot_baseline_bars(agg: dict) -> None:
    methods = [
        "ecn_proposed__full",
        "random_forest__full",
        "logistic__full",
        "lightgbm__full",
        "isolation_forest__full",
        "ewma__full",
        "gnn_graphsage_proxy__full",
        "mlp_sequence__full",
        "majority__full",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), sharey=False)
    for ax, task, title in [
        (axes[0], "T1_anomaly", "T1 anomaly AUPRC"),
        (axes[1], "T2_failure", "T2 failure AUPRC"),
    ]:
        means, los, his, labs, cols = [], [], [], [], []
        for method in methods:
            ap = agg["metrics"][task][method]["ap"]
            means.append(ap["mean"])
            los.append(ap["mean"] - ap["ci95"][0])
            his.append(ap["ci95"][1] - ap["mean"])
            labs.append(LABELS[method])
            cols.append(COLORS[method])
        x = np.arange(len(methods))
        ax.bar(x, means, yerr=np.vstack([los, his]), color=cols, edgecolor="black", linewidth=0.4, capsize=2.5, error_kw={"lw": 0.8})
        ax.set_xticks(x)
        ax.set_xticklabels(labs, rotation=35, ha="right")
        ax.set_ylabel("AUPRC (mean)")
        ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.25, lw=0.5)
        ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "baseline_auprc_mean_ci")


def plot_ablation_bars(agg: dict) -> None:
    order = ["full", "no_twin", "no_nbr", "telem_only", "twin_only"]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.7))
    for ax, task, title in [
        (axes[0], "T1_anomaly", "T1 ablations"),
        (axes[1], "T2_failure", "T2 ablations"),
    ]:
        means, los, his = [], [], []
        for ab in order:
            ap = agg["ablation"][task][ab]["ap"]
            means.append(ap["mean"])
            los.append(ap["mean"] - ap["ci95"][0])
            his.append(ap["ci95"][1] - ap["mean"])
        x = np.arange(len(order))
        ax.bar(
            x,
            means,
            yerr=np.vstack([los, his]),
            color="#0072B2",
            edgecolor="black",
            linewidth=0.4,
            capsize=2.5,
            error_kw={"lw": 0.8},
        )
        ax.set_xticks(x)
        ax.set_xticklabels(order, rotation=25, ha="right")
        ax.set_ylabel("AUPRC (mean)")
        ax.set_title(title)
        ax.grid(True, axis="y", alpha=0.25, lw=0.5)
        ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "ablation_auprc_mean_ci")


def plot_module_bars(agg: dict) -> None:
    mc = agg["module_contribution"]
    modules = ["telemetry", "neighbor_message_passing", "digital_twin"]
    labs = ["Telemetry", "Neighbor", "Digital Twin"]
    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    x = np.arange(len(modules))
    w = 0.35
    t1 = [mc["T1_anomaly"][m] for m in modules]
    t2 = [mc["T2_failure"][m] for m in modules]
    ax.bar(x - w / 2, t1, w, label="T1", color="#0072B2", edgecolor="black", lw=0.4)
    ax.bar(x + w / 2, t2, w, label="T2", color="#D55E00", edgecolor="black", lw=0.4)
    ax.axhline(0, color="#444444", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labs)
    ax.set_ylabel("AUPRC contribution")
    ax.set_title("Module contribution")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.25, lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "module_contribution")


def main() -> None:
    style()
    agg = json.loads(AGG.read_text(encoding="utf-8"))
    for seed_file in sorted(PER.glob("*.json")):
        data = json.loads(seed_file.read_text(encoding="utf-8"))
        # write temporary: refactor helpers to accept data would be cleaner; keep file-based for now
        plot_roc_pr(seed_file, "T1_anomaly", "T1", MAIN_METHODS)
        plot_roc_pr(seed_file, "T2_failure", "T2", MAIN_METHODS)
        plot_calibration(seed_file, "T1_anomaly", "T1", "ecn_proposed__full")
        plot_calibration(seed_file, "T2_failure", "T2", "ecn_proposed__full")
        plot_cm(seed_file, "T1_anomaly", "T1", "ecn_proposed__full")
        plot_cm(seed_file, "T2_failure", "T2", "ecn_proposed__full")
        if "T3_rca" in data["tasks"]:
            plot_cm(seed_file, "T3_rca", "T3", "ecn_proposed__full")
    plot_baseline_bars(agg)
    plot_ablation_bars(agg)
    plot_module_bars(agg)
    print("done")


if __name__ == "__main__":
    main()
