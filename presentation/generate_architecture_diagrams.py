#!/usr/bin/env python3
"""Generate publication-quality architecture diagrams for the ECN presentation.

Outputs PNG (300 dpi) and PDF under presentation/diagrams/.
Uses a consistent enterprise-networking palette. Does not recompute metrics.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "diagrams"

# Enterprise networking palette (navy / teal / slate / amber)
NAVY = "#0B3A5B"
TEAL = "#1F7A8C"
SLATE = "#4A5568"
AMBER = "#C47B2B"
LIGHT = "#F4F7FA"
BOX = "#E8EEF4"
ACCENT = "#2C5F7C"
GREEN = "#2F6B4F"
ORANGE = "#B85C38"


def style():
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Calibri", "Arial", "DejaVu Sans"],
            "font.size": 11,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save(fig, stem: str):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.15)
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("wrote", stem)


def rounded(ax, xy, w, h, text, fc=BOX, ec=NAVY, fontsize=10, weight="bold", tc=NAVY):
    x, y = xy
    box = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4, edgecolor=ec, facecolor=fc, mutation_aspect=0.5,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color=tc, wrap=True)


def arrow(ax, start, end, color=SLATE):
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6,
                        mutation_scale=14, shrinkA=2, shrinkB=2),
    )


def diagram_ecn_system():
    fig, ax = plt.subplots(figsize=(12.5, 7.2))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    ax.set_title("Enterprise Cognitive Network (ECN-v3) — End-to-End Pipeline",
                 fontsize=15, fontweight="bold", color=NAVY, pad=12)

    stages = [
        (0.25, "Enterprise\nNetwork"),
        (1.45, "Telemetry\nCollection"),
        (2.65, "Digital\nTwin"),
        (3.85, "Feature\nEngineering"),
        (5.05, "Perception\nAgent"),
        (6.25, "Anomaly\nDetection"),
        (7.45, "Failure\nPrediction"),
        (8.65, "RCA +\nTreeSHAP"),
        (9.85, "Impact\nAnalysis"),
        (11.05, "Healing\nDecision\nSupport"),
    ]
    y = 3.4
    w, h = 1.05, 1.55
    for i, (x, lab) in enumerate(stages):
        fc = AMBER if i == len(stages) - 1 else (TEAL if i in (5, 6) else BOX)
        tc = "white" if i == len(stages) - 1 or i in (5, 6) else NAVY
        ec = AMBER if i == len(stages) - 1 else (TEAL if i in (5, 6) else NAVY)
        rounded(ax, (x, y), w, h, lab, fc=fc, ec=ec, fontsize=8.2, tc=tc)
        if i < len(stages) - 1:
            arrow(ax, (x + w + 0.02, y + h / 2), (stages[i + 1][0] - 0.02, y + h / 2))

    # Orchestrator band
    rounded(ax, (6.15, 1.35), 2.5, 0.85, "Orchestrator\nAnchored Fusion (ECNFusionModel)",
            fc=NAVY, ec=NAVY, fontsize=9, tc="white")
    arrow(ax, (7.4, 3.4), (7.4, 2.25), color=NAVY)

    ax.text(6.25, 0.55, "Final T1 head: leakage-safe enriched features + anchored fusion\n"
            "T2 head: telemetry logistic  |  RCA: RF + TreeSHAP",
            ha="center", fontsize=9.5, color=SLATE)
    save(fig, "arch_ecn_system")


def diagram_digital_twin():
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 6.8)
    ax.axis("off")
    ax.set_title("Digital Twin Architecture", fontsize=15, fontweight="bold", color=NAVY, pad=10)

    # Graph panel
    rounded(ax, (0.4, 1.2), 4.6, 4.8, "", fc=LIGHT, ec=TEAL)
    ax.text(2.7, 5.7, "Typed Topology Graph", ha="center", fontsize=12, fontweight="bold", color=NAVY)

    # Simple topology sketch
    nodes = {
        "Core": (1.4, 4.6),
        "Agg": (2.7, 4.6),
        "Access": (4.0, 4.6),
        "WAN": (1.4, 3.2),
        "AP": (2.7, 3.2),
        "Svc": (4.0, 3.2),
    }
    for name, (x, y) in nodes.items():
        circ = plt.Circle((x, y), 0.32, facecolor=TEAL, edgecolor=NAVY, lw=1.2)
        ax.add_patch(circ)
        ax.text(x, y, name, ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")
    for a, b in [("Core", "Agg"), ("Agg", "Access"), ("Core", "WAN"), ("Access", "AP"), ("Agg", "Svc")]:
        ax.plot([nodes[a][0], nodes[b][0]], [nodes[a][1], nodes[b][1]], color=SLATE, lw=1.3, zorder=0)

    ax.text(2.7, 2.2, "Devices · Interfaces · Links · Services", ha="center", fontsize=9, color=SLATE)
    ax.text(2.7, 1.6, "Telemetry sync · Graph updates", ha="center", fontsize=9, color=SLATE)

    # Right side feature extraction
    items = [
        (5.6, 5.2, "Neighbor aggregates"),
        (5.6, 4.3, "Role / degree features"),
        (5.6, 3.4, "Residual contrasts"),
        (5.6, 2.5, "Instability proxies"),
        (5.6, 1.6, "Causal iface deltas"),
    ]
    for x, y, t in items:
        rounded(ax, (x, y), 5.2, 0.7, t, fc=BOX, ec=ACCENT, fontsize=11)
        arrow(ax, (5.0, y + 0.35), (x, y + 0.35), color=TEAL)

    ax.text(8.2, 6.15, "Feature Extraction", ha="center", fontsize=12, fontweight="bold", color=NAVY)
    save(fig, "arch_digital_twin")


def diagram_multi_agent():
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 6.8)
    ax.axis("off")
    ax.set_title("Multi-Agent Architecture with Orchestrated Fusion", fontsize=15,
                 fontweight="bold", color=NAVY, pad=10)

    # Perception
    rounded(ax, (0.4, 2.8), 2.0, 1.4, "Perception\nAgent", fc=TEAL, ec=NAVY, fontsize=11, tc="white")

    agents = [
        (3.0, 5.0, "Anomaly"),
        (5.3, 5.0, "Prediction"),
        (3.0, 3.5, "RCA +\nTreeSHAP"),
        (5.3, 3.5, "Impact"),
        (4.15, 1.9, "Healing"),
    ]
    for x, y, t in agents:
        rounded(ax, (x, y), 1.9, 1.1, t, fc=BOX, ec=NAVY, fontsize=10)

    # Orchestrator
    rounded(ax, (7.8, 3.2), 3.2, 1.8, "Orchestrator\nAnchored Fusion\n(ECNFusionModel)",
            fc=NAVY, ec=NAVY, fontsize=11, tc="white")

    arrow(ax, (2.4, 3.5), (3.0, 5.4))
    arrow(ax, (2.4, 3.5), (5.3, 5.4))
    arrow(ax, (3.95, 5.0), (3.95, 4.6))
    arrow(ax, (4.15, 3.5), (4.15, 3.0))
    arrow(ax, (6.2, 5.55), (7.8, 4.4))
    arrow(ax, (6.2, 4.05), (7.8, 4.1))
    arrow(ax, (6.05, 2.45), (7.8, 3.5))

    ax.text(5.75, 0.6, "Communication: feature matrices → specialist scores → validation-selected fusion → decision support",
            ha="center", fontsize=10, color=SLATE)
    save(fig, "arch_multi_agent")


def diagram_benchmark_gen():
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 6.5)
    ax.axis("off")
    ax.set_title("ECNetBench Generation Architecture", fontsize=15, fontweight="bold", color=NAVY, pad=10)

    flow = [
        (0.35, "Synthetic\nGenerator"),
        (2.0, "Topology\nCreation"),
        (3.65, "Telemetry\nGeneration"),
        (5.3, "Incidents\n& Labels"),
        (6.95, "Realism\nValidation"),
        (8.6, "Multi-seed\nInstances"),
        (10.15, "Frozen\nSQLite"),
    ]
    y, w, h = 3.3, 1.35, 1.5
    for i, (x, lab) in enumerate(flow):
        fc = GREEN if i == len(flow) - 1 else BOX
        tc = "white" if i == len(flow) - 1 else NAVY
        rounded(ax, (x, y), w, h, lab, fc=fc, ec=NAVY, fontsize=9, tc=tc)
        if i < len(flow) - 1:
            arrow(ax, (x + w, y + h / 2), (flow[i + 1][0], y + h / 2))

    notes = [
        "AOS-CX-style inventory, VLAN/ACL/QoS, routing, counters, syslog/alerts",
        "Six frozen instances: v1.1.0-INST + seeds 101–505 (checksum verified)",
        "Leakage-safe label construction with causal incident modeling",
    ]
    for i, n in enumerate(notes):
        ax.text(5.75, 2.2 - i * 0.55, "•  " + n, ha="center", fontsize=10.5, color=SLATE)
    save(fig, "arch_benchmark_generation")


def diagram_evaluation():
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 6.5)
    ax.axis("off")
    ax.set_title("Evaluation Pipeline", fontsize=15, fontweight="bold", color=NAVY, pad=10)

    flow = [
        (0.4, "Frozen\nBenchmark"),
        (2.05, "Temporal\n70/15/15"),
        (3.7, "Baselines\n(telem_only)"),
        (5.35, "ECN-v3\nAnchored"),
        (7.0, "Statistics\nCI / Wilcoxon"),
        (8.65, "Ablation\n& Fusion"),
        (10.2, "Final\nComparison"),
    ]
    y, w, h = 3.4, 1.4, 1.5
    for i, (x, lab) in enumerate(flow):
        fc = AMBER if i == len(flow) - 1 else BOX
        tc = "white" if i == len(flow) - 1 else NAVY
        rounded(ax, (x, y), w, h, lab, fc=fc, ec=NAVY, fontsize=9, tc=tc)
        if i < len(flow) - 1:
            arrow(ax, (x + w, y + h / 2), (flow[i + 1][0], y + h / 2))

    ax.text(5.75, 2.0, "Primary metric: AUPRC  ·  Threshold tuned on validation only  ·  feat_bin = t_start − 30 min",
            ha="center", fontsize=10.5, color=SLATE)
    ax.text(5.75, 1.3, "No nested CV; fixed temporal holdout across six seeds",
            ha="center", fontsize=10.5, color=SLATE)
    save(fig, "arch_evaluation_pipeline")


def diagram_feature_pipeline():
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    ax.set_title("Leakage-Safe Feature Engineering Pipeline", fontsize=15, fontweight="bold", color=NAVY, pad=10)

    cols = [
        (0.4, "Raw\nTelemetry", LIGHT),
        (2.5, "Causal ops\nshift(1)\nroll / EMA / z", BOX),
        (4.6, "Twin\nDynamics", BOX),
        (6.7, "Label Join\nfeat_bin =\nt−30 min", TEAL),
        (8.8, "Train / Val / Test\nMatrices", NAVY),
    ]
    for i, (x, lab, fc) in enumerate(cols):
        tc = "white" if fc in (TEAL, NAVY) else NAVY
        rounded(ax, (x, 2.6), 1.9, 2.2, lab, fc=fc, ec=NAVY, fontsize=10, tc=tc)
        if i < len(cols) - 1:
            arrow(ax, (x + 1.9, 3.7), (cols[i + 1][0], 3.7))

    ax.text(5.75, 1.5, "Expanding z · second differences · error burst/accumulate · neighbor instability",
            ha="center", fontsize=10.5, color=SLATE)
    ax.text(5.75, 0.9, "All temporal operators exclude the current bin (causal)",
            ha="center", fontsize=10.5, color=SLATE)
    save(fig, "arch_feature_pipeline")


def diagram_shap_rca():
    fig, ax = plt.subplots(figsize=(11.0, 5.8))
    ax.set_xlim(0, 11.0)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    ax.set_title("Explainable RCA — TreeSHAP Workflow", fontsize=15, fontweight="bold", color=NAVY, pad=10)

    steps = [
        (0.4, "Incident\nFeatures"),
        (2.5, "RF\nClassifier"),
        (4.6, "TreeSHAP\nAttribution"),
        (6.7, "Category\nPrediction"),
        (8.8, "Operator\nExplanation"),
    ]
    for i, (x, lab) in enumerate(steps):
        fc = GREEN if i == len(steps) - 1 else BOX
        tc = "white" if i == len(steps) - 1 else NAVY
        rounded(ax, (x, 2.4), 1.8, 1.8, lab, fc=fc, ec=NAVY, fontsize=10, tc=tc)
        if i < len(steps) - 1:
            arrow(ax, (x + 1.8, 3.3), (steps[i + 1][0], 3.3))

    ax.text(5.5, 1.3, "Healing decision support consumes RCA outputs as recommendations (not live actuation)",
            ha="center", fontsize=10.5, color=SLATE)
    save(fig, "arch_shap_rca")


def diagram_healing():
    fig, ax = plt.subplots(figsize=(11.0, 5.8))
    ax.set_xlim(0, 11.0)
    ax.set_ylim(0, 5.8)
    ax.axis("off")
    ax.set_title("Healing Recommendation Workflow (Decision Support)", fontsize=15,
                 fontweight="bold", color=NAVY, pad=10)

    steps = [
        (0.35, "Detection /\nRCA Outputs"),
        (2.55, "Impact\nEstimate"),
        (4.75, "Healing\nPolicy Head"),
        (6.95, "Remediation\nClass Scores"),
        (9.15, "Human\nApproval"),
    ]
    for i, (x, lab) in enumerate(steps):
        fc = AMBER if i == len(steps) - 1 else BOX
        tc = "white" if i == len(steps) - 1 else NAVY
        rounded(ax, (x, 2.4), 1.9, 1.8, lab, fc=fc, ec=NAVY, fontsize=10, tc=tc)
        if i < len(steps) - 1:
            arrow(ax, (x + 1.9, 3.3), (steps[i + 1][0], 3.3))

    ax.text(5.5, 1.3, "Honest ablation removes RCA-category features to avoid near-oracle leakage into remediation",
            ha="center", fontsize=10.5, color=SLATE)
    save(fig, "arch_healing_workflow")


def main():
    style()
    diagram_ecn_system()
    diagram_digital_twin()
    diagram_multi_agent()
    diagram_benchmark_gen()
    diagram_evaluation()
    diagram_feature_pipeline()
    diagram_shap_rca()
    diagram_healing()
    print("diagrams ->", OUT)


if __name__ == "__main__":
    main()
