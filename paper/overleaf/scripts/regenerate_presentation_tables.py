#!/usr/bin/env python3
"""Regenerate IEEE presentation tables with 3-decimal rounding (display only)."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OL = Path(__file__).resolve().parents[1]
OUT = OL / "tables"
PERF = REPO / "results" / "tables" / "performance_mean_ci.csv"
ABL = REPO / "results" / "tables" / "ablation_ap.csv"
SIG = REPO / "results" / "tables" / "significance_vs_proposed.csv"
MS = REPO / "results" / "manuscript_ready_numbers.json"
AGG = REPO / "results" / "aggregate_v3.json"
SEL = REPO / "results" / "v3_gated" / "t1_architecture_selection.json"


def r3(x) -> str:
    return f"{float(x):.3f}"


def ci3(lo, hi) -> str:
    return f"[{r3(lo)},\\,{r3(hi)}]"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    perf = list(csv.DictReader(PERF.open(encoding="utf-8")))
    idx = {(r["task"], r["method"], r["metric"]): r for r in perf}
    ms = json.loads(MS.read_text(encoding="utf-8"))
    agg = json.loads(AGG.read_text(encoding="utf-8"))
    t1f = ms["T1_final_proposed"]

    methods = [
        ("ECN-v3 (T1)", "ecn_proposed__full"),
        ("TabNet", "tabnet__full"),
        ("GraphSAGE (true)", "graphsage__full"),
        ("XGBoost", "xgboost__full"),
        ("CatBoost", "catboost__full"),
        ("Gradient boosting", "gradient_boosting__full"),
        ("Balanced RF", "balanced_rf__full"),
        ("Random forest", "random_forest__full"),
        ("Logistic", "logistic__full"),
        ("LightGBM", "lightgbm__full"),
        ("Isolation Forest", "isolation_forest__full"),
        ("EWMA", "ewma__full"),
        ("GNN proxy", "gnn_graphsage_proxy__full"),
        ("MLP sequence", "mlp_sequence__full"),
        ("Majority", "majority__full"),
    ]

    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\caption{Multi-seed mean T1/T2 ranking metrics (six instances; 95\% CI). ECN-v3 (T1) is the final anchored head; recommended T2 head is Logistic (telem).}",
        r"\label{tab:t1t2}",
        r"\renewcommand{\arraystretch}{1.12}",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"{\footnotesize",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccc}",
        r"\toprule",
        r"Method & T1 AUPRC & T1 ROC-AUC & T2 AUPRC & T2 ROC-AUC \\",
        r"\midrule",
    ]
    for name, key in methods:
        t1a, t1r = idx[("T1_anomaly", key, "ap")], idx[("T1_anomaly", key, "roc_auc")]
        t2a, t2r = idx[("T2_failure", key, "ap")], idx[("T2_failure", key, "roc_auc")]
        if name.startswith("ECN"):
            ci = t1f["auprc_ci95_bootstrap"]
            row = (
                r"\textbf{" + name + r"} & $\mathbf{" + r3(t1f["auprc_mean"]) + r"}$ $"
                + ci3(ci[0], ci[1]) + r"$ & $\mathbf{" + r3(t1f["roc_auc_mean"]) + r"}$ & $"
                + r3(t2a["mean"]) + r"$ $" + ci3(t2a["ci95_lo"], t2a["ci95_hi"])
                + "$ & $" + r3(t2r["mean"]) + "$ \\\\"
            )
        else:
            row = (
                f"{name} & ${r3(t1a['mean'])}$ ${ci3(t1a['ci95_lo'], t1a['ci95_hi'])}$ & "
                f"${r3(t1r['mean'])}$ & ${r3(t2a['mean'])}$ ${ci3(t2a['ci95_lo'], t2a['ci95_hi'])}$ & "
                f"${r3(t2r['mean'])}$ \\\\"
            )
        lines.append(row)
    lines += [r"\bottomrule", r"\end{tabular*}}", r"\end{table*}", ""]
    (OUT / "tab_t1t2.tex").write_text("\n".join(lines), encoding="utf-8")

    # Significance
    name_map = {
        "tabnet": "TabNet",
        "graphsage": "GraphSAGE",
        "xgboost": "XGBoost",
        "catboost": "CatBoost",
        "lightgbm": "LightGBM",
        "gradient_boosting": "Gradient boosting",
        "balanced_rf": "Balanced RF",
        "random_forest": "Random forest",
        "logistic": "Logistic",
        "isolation_forest": "Isolation Forest",
        "ewma": "EWMA",
        "threshold": "Threshold",
        "mlp_sequence": "MLP sequence",
        "gnn_graphsage_proxy": "GNN proxy",
        "majority": "Majority",
    }
    sig = list(csv.DictReader(SIG.open(encoding="utf-8")))
    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\caption{Paired Wilcoxon tests and Cliff's $\delta$ on per-seed T1/T2 AUPRC ($n{=}6$).}",
        r"\label{tab:sig}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"{\footnotesize\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llcccc}",
        r"\toprule",
        r"Task & Baseline & $p$ & Cliff $\delta$ & Proposed & Baseline \\",
        r"\midrule",
    ]
    prev = None
    for r in sig:
        task_raw = r["task"]
        task_disp = {"T1_anomaly": "T1", "T2_failure": "T2"}.get(task_raw, task_raw.replace("_", r"\_"))
        task_cell = task_disp if task_raw != prev else ""
        prev = task_raw
        key = r["baseline"].replace("__full", "")
        base = name_map.get(key, key.replace("_", " "))
        p = float(r.get("wilcoxon_p", r.get("pvalue")))
        dlt = float(r["cliffs_delta"])
        prop = float(r.get("proposed_ap_mean", r.get("proposed_ap")))
        bap = float(r.get("baseline_ap_mean", r.get("baseline_ap")))
        lines.append(
            f"{task_cell} & {base} & ${p:.3f}$ & ${dlt:+.3f}$ & ${r3(prop)}$ & ${r3(bap)}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular*}}", r"\end{table*}", ""]
    (OUT / "tab_significance.tex").write_text("\n".join(lines), encoding="utf-8")

    # Ablation
    abl = list(csv.DictReader(ABL.open(encoding="utf-8")))
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Ablation mean AUPRC on T1/T2 (six seeds, 95\% CI).}",
        r"\label{tab:ablation}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"{\footnotesize\begin{tabular}{llcc}",
        r"\toprule",
        r"Task & Ablation & Mean & 95\% CI \\",
        r"\midrule",
    ]
    prev = None
    for r in abl:
        task_disp = {"T1_anomaly": "T1", "T2_failure": "T2"}.get(r["task"], r["task"].replace("_", r"\_"))
        task_cell = task_disp if r["task"] != prev else ""
        prev = r["task"]
        abl_name = r["ablation"].replace("_", r"\_")
        lines.append(
            f"{task_cell} & {abl_name} & ${r3(r['ap_mean'])}$ & "
            f"${ci3(r['ap_ci95_lo'], r['ap_ci95_hi'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (OUT / "tab_ablation.tex").write_text("\n".join(lines), encoding="utf-8")

    # Modules
    mc = agg["module_contribution"]
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Module AUPRC contribution ($\mathrm{full}-\mathrm{ablated}$) from full-suite ablations.}",
        r"\label{tab:modules}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"{\footnotesize\begin{tabular}{lccc}",
        r"\toprule",
        r"Task & Telemetry & Neighbor & Digital Twin \\",
        r"\midrule",
    ]
    for task, m in mc.items():
        task_disp = {"T1_anomaly": "T1", "T2_failure": "T2"}.get(task, task.replace("_", r"\_"))
        lines.append(
            f"{task_disp} & ${r3(m['telemetry'])}$ & ${r3(m['neighbor_message_passing'])}$ & ${r3(m['digital_twin'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (OUT / "tab_modules.tex").write_text("\n".join(lines), encoding="utf-8")

    # Calibration
    sel = json.loads(SEL.read_text(encoding="utf-8"))
    bvals = [float(r["anchored"]["brier"]) for r in sel["per_seed"]]
    bm = sum(bvals) / len(bvals)
    bstd = math.sqrt(sum((x - bm) ** 2 for x in bvals) / (len(bvals) - 1))
    bhalf = 1.96 * bstd / math.sqrt(len(bvals))
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Calibration quality (Brier score; lower is better).}",
        r"\label{tab:cal}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"{\footnotesize\begin{tabular}{llcc}",
        r"\toprule",
        r"Task & Method & Mean & 95\% CI \\",
        r"\midrule",
        f"T1 & ECN-v3 (selection) & ${r3(t1f['brier_mean'])}$ & ${ci3(bm - bhalf, bm + bhalf)}$ \\\\",
    ]
    for task, key, name in [
        ("T1_anomaly", "random_forest__full", "Random forest"),
        ("T1_anomaly", "logistic__full", "Logistic"),
        ("T2_failure", "ecn_proposed__full", "ECN proposed"),
        ("T2_failure", "logistic__full", "Logistic"),
        ("T2_failure", "random_forest__full", "Random forest"),
    ]:
        r = idx[(task, key, "brier")]
        task_disp = {"T1_anomaly": "T1", "T2_failure": "T2"}[task]
        lines.append(
            f"{task_disp} & {name} & ${r3(r['mean'])}$ & ${ci3(r['ci95_lo'], r['ci95_hi'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (OUT / "tab_calibration.tex").write_text("\n".join(lines), encoding="utf-8")

    # RCA / healing / cost
    c = agg["computational_cost"]["per_seed_wall_s"]
    t3 = agg["metrics"]["T3_rca"]["ecn_proposed__full"]["macro_f1"]
    hfull = agg["metrics"]["TR_AUTO_healing"]["healing__full"]["macro_f1"]
    hnorca = agg["metrics"]["TR_AUTO_healing"]["healing__no_rca_cat"]["macro_f1"]
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{RCA macro-F1, healing scores, and evaluation wall-clock cost (six seeds).}",
        r"\label{tab:rcaheal}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"{\footnotesize\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}llc}",
        r"\toprule",
        r"Metric & Setting & Mean [95\% CI] \\",
        r"\midrule",
        f"T3 RCA macro-F1 & proposed & ${r3(t3['mean'])}$ ${ci3(t3['ci95'][0], t3['ci95'][1])}$ \\\\",
        f"Healing macro-F1 & with RCA category & ${r3(hfull['mean'])}$ ${ci3(hfull['ci95'][0], hfull['ci95'][1])}$ \\\\",
        f"Healing macro-F1 & without RCA category & ${r3(hnorca['mean'])}$ ${ci3(hnorca['ci95'][0], hnorca['ci95'][1])}$ \\\\",
        f"Eval.\\ wall time (s/seed) & full suite & ${float(c['mean']):.1f}$ $[{float(c['ci95'][0]):.1f},\\,{float(c['ci95'][1]):.1f}]$ \\\\",
        r"\bottomrule",
        r"\end{tabular*}}",
        r"\end{table}",
        "",
    ]
    (OUT / "tab_rca_healing_cost.tex").write_text("\n".join(lines), encoding="utf-8")

    # Deep baselines
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Deep baselines versus ECN-v3 and RF on T1/T2 (six-seed means, 95\% CI).}",
        r"\label{tab:deep_baselines_v5}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"{\footnotesize\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}lcc}",
        r"\toprule",
        r"Method & T1 AUPRC & T2 AUPRC \\",
        r"\midrule",
        f"ECN-v3 final & ${r3(t1f['auprc_mean'])}$ ${ci3(*t1f['auprc_ci95_bootstrap'])}$ & --- \\\\",
    ]
    for name, key in [
        ("TabNet", "tabnet__full"),
        ("GraphSAGE (true)", "graphsage__full"),
        ("GNN proxy (LightGBM)", "gnn_graphsage_proxy__full"),
        ("Random forest (telem)", "random_forest__full"),
    ]:
        t1a = idx[("T1_anomaly", key, "ap")]
        t2a = idx[("T2_failure", key, "ap")]
        lines.append(
            f"{name} & ${r3(t1a['mean'])}$ ${ci3(t1a['ci95_lo'], t1a['ci95_hi'])}$ & "
            f"${r3(t2a['mean'])}$ ${ci3(t2a['ci95_lo'], t2a['ci95_hi'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular*}}", r"\end{table}", ""]
    (OUT / "tab_deep_baselines_v5.tex").write_text("\n".join(lines), encoding="utf-8")
    print("wrote presentation tables to", OUT)


if __name__ == "__main__":
    main()
