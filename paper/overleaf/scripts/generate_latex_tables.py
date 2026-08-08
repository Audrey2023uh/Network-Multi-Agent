#!/usr/bin/env python3
"""Regenerate IEEE-style LaTeX tables from verified CSV/JSON (presentation only)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def f(x, n: int = 4) -> str:
    return f"{float(x):.{n}f}"


def main() -> None:
    perf = list(csv.DictReader((ROOT / "results" / "tables" / "performance_mean_ci.csv").open(encoding="utf-8")))
    abl = list(csv.DictReader((ROOT / "results" / "tables" / "ablation_ap.csv").open(encoding="utf-8")))
    sig = list(csv.DictReader((ROOT / "results" / "tables" / "significance_vs_proposed.csv").open(encoding="utf-8")))
    agg = json.loads((ROOT / "results" / "aggregate.json").read_text(encoding="utf-8"))
    out = ROOT / "tables"
    out.mkdir(parents=True, exist_ok=True)
    idx = {(r["task"], r["method"], r["metric"]): r for r in perf}

    methods = [
        ("ECN (proposed)", "ecn_proposed__full"),
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
        r"\caption{Multi-seed mean detection metrics on T1 (anomaly) and T2 (failure horizon). Entries are means over six frozen instances; AUPRC is reported with 95\% confidence intervals.}",
        r"\label{tab:t1t2}",
        r"\renewcommand{\arraystretch}{1.2}",
        r"\setlength{\tabcolsep}{4pt}",
        r"{\footnotesize",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccc}",
        r"\toprule",
        r"Method & T1 AUPRC & T1 ROC-AUC & T2 AUPRC & T2 ROC-AUC \\",
        r"\midrule",
    ]
    for name, key in methods:
        t1a = idx[("T1_anomaly", key, "ap")]
        t1r = idx[("T1_anomaly", key, "roc_auc")]
        t2a = idx[("T2_failure", key, "ap")]
        t2r = idx[("T2_failure", key, "roc_auc")]
        row = (
            f"{name} & ${f(t1a['mean'])}$ $[{f(t1a['ci95_lo'])},\\,{f(t1a['ci95_hi'])}]$ & "
            f"${f(t1r['mean'])}$ & ${f(t2a['mean'])}$ $[{f(t2a['ci95_lo'])},\\,{f(t2a['ci95_hi'])}]$ & "
            f"${f(t2r['mean'])}$ \\\\"
        )
        if name.startswith("ECN"):
            row = r"\textbf{" + name + r"} & $\mathbf{" + f(t1a["mean"]) + r"}$ $[" + f(t1a["ci95_lo"]) + r",\," + f(t1a["ci95_hi"]) + r"]$ & $\mathbf{" + f(t1r["mean"]) + r"}$ & $\mathbf{" + f(t2a["mean"]) + r"}$ $[" + f(t2a["ci95_lo"]) + r",\," + f(t2a["ci95_hi"]) + r"]$ & $\mathbf{" + f(t2r["mean"]) + r"}$ \\"
        lines.append(row)
    lines += [r"\bottomrule", r"\end{tabular*}}", r"\end{table*}", ""]
    (out / "tab_t1t2.tex").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Ablation study of mean AUPRC on T1 and T2 (six seeds, 95\% CI).}",
        r"\label{tab:ablation}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"{\footnotesize\begin{tabular}{llcc}",
        r"\toprule",
        r"Task & Ablation & Mean & 95\% CI \\",
        r"\midrule",
    ]
    prev = None
    for r in abl:
        task = r["task"].replace("_", r"\_")
        ab = r["ablation"].replace("_", r"\_")
        task_cell = task if task != prev else ""
        prev = r["task"].replace("_", r"\_")
        lines.append(
            f"{task_cell} & {ab} & ${f(r['ap_mean'])}$ & $[{f(r['ap_ci95_lo'])},\\,{f(r['ap_ci95_hi'])}]$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (out / "tab_ablation.tex").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\caption{Paired Wilcoxon signed-rank tests and Cliff's $\delta$ comparing proposed AUPRC against each baseline across $n{=}6$ seeds.}",
        r"\label{tab:sig}",
        r"\renewcommand{\arraystretch}{1.12}",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"{\scriptsize\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llcccc}",
        r"\toprule",
        r"Task & Baseline & $p$ & Cliff $\delta$ & Proposed & Baseline \\",
        r"\midrule",
    ]
    prev = None
    for r in sig:
        task_raw = r["task"]
        task = task_raw.replace("_", r"\_")
        task_cell = task if task_raw != prev else ""
        prev = task_raw
        base = r["baseline"].replace("_", r"\_")
        lines.append(
            f"{task_cell} & {base} & ${f(r['pvalue'], 3)}$ & ${f(r['cliffs_delta'], 3)}$ & "
            f"${f(r['proposed_ap'])}$ & ${f(r['baseline_ap'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular*}}", r"\end{table*}", ""]
    (out / "tab_significance.tex").write_text("\n".join(lines), encoding="utf-8")

    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Calibration quality measured by Brier score (mean over six seeds with 95\% CI). Lower is better.}",
        r"\label{tab:cal}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"{\footnotesize\begin{tabular}{llcc}",
        r"\toprule",
        r"Task & Method & Mean & 95\% CI \\",
        r"\midrule",
    ]
    for task, key, name in [
        ("T1_anomaly", "ecn_proposed__full", "ECN proposed"),
        ("T1_anomaly", "random_forest__full", "Random forest"),
        ("T1_anomaly", "logistic__full", "Logistic"),
        ("T2_failure", "ecn_proposed__full", "ECN proposed"),
        ("T2_failure", "logistic__full", "Logistic"),
        ("T2_failure", "random_forest__full", "Random forest"),
    ]:
        r = idx[(task, key, "brier")]
        lines.append(
            f"{task.replace('_', r'\_')} & {name} & ${f(r['mean'])}$ & $[{f(r['ci95_lo'])},\\,{f(r['ci95_hi'])}]$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (out / "tab_calibration.tex").write_text("\n".join(lines), encoding="utf-8")

    c = agg["computational_cost"]["per_seed_wall_s"]
    t3 = agg["metrics"]["T3_rca"]["ecn_proposed__full"]["macro_f1"]
    hfull = agg["metrics"]["TR_AUTO_healing"]["healing__full"]["macro_f1"]
    hnorca = agg["metrics"]["TR_AUTO_healing"]["healing__no_rca_cat"]["macro_f1"]
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{RCA accuracy, healing decision-support scores, and evaluation wall-clock cost (six seeds). The \texttt{full} healing setting includes RCA category features; \texttt{no\_rca\_cat} is the honest telemetry-oriented baseline.}",
        r"\label{tab:rcaheal}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"{\footnotesize\begin{tabular}{p{3.1cm}p{2.6cm}c}",
        r"\toprule",
        r"Metric & Setting & Mean [95\% CI] \\",
        r"\midrule",
        f"T3 RCA macro-F1 & proposed & ${f(t3['mean'])}$ $[{f(t3['ci95'][0])},\\,{f(t3['ci95'][1])}]$ \\\\",
        f"Healing macro-F1 & full (w/ RCA cat.) & ${f(hfull['mean'])}$ $[{f(hfull['ci95'][0])},\\,{f(hfull['ci95'][1])}]$ \\\\",
        f"Healing macro-F1 & no\\_rca\\_cat & ${f(hnorca['mean'])}$ $[{f(hnorca['ci95'][0])},\\,{f(hnorca['ci95'][1])}]$ \\\\",
        f"Eval. wall time (s/seed) & full suite & ${f(c['mean'], 2)}$ $[{f(c['ci95'][0], 2)},\\,{f(c['ci95'][1], 2)}]$ \\\\",
        r"\bottomrule",
        r"\end{tabular}}",
        r"\end{table}",
        "",
    ]
    (out / "tab_rca_healing_cost.tex").write_text("\n".join(lines), encoding="utf-8")

    mc = agg["module_contribution"]
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Estimated module AUPRC contribution, defined as AUPRC(full)${-}$AUPRC(ablated). Positive values indicate improvement when the module is present.}",
        r"\label{tab:modules}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"{\footnotesize\begin{tabular}{lccc}",
        r"\toprule",
        r"Task & Telemetry & Neighbor & Digital Twin \\",
        r"\midrule",
    ]
    for task in ["T1_anomaly", "T2_failure"]:
        m = mc[task]
        lines.append(
            f"{task.replace('_', r'\_')} & ${f(m['telemetry'])}$ & ${f(m['neighbor_message_passing'])}$ & ${f(m['digital_twin'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (out / "tab_modules.tex").write_text("\n".join(lines), encoding="utf-8")

    # Static presentation polish for contrib / seeds
    (out / "tab_contrib.tex").write_text(
        r"""\begin{table}[!t]
\centering
\caption{Qualitative comparison of ECNetBench against common public resource classes for enterprise cognitive NetOps research.}
\label{tab:contrib}
\renewcommand{\arraystretch}{1.15}
{\footnotesize\begin{tabular}{p{2.15cm}cccc}
\toprule
Resource class & Config. & Telemetry & RCA/heal & Multi-seed leak protocol \\
\midrule
Topology archives & Partial & No & No & Rare \\
Security flow sets & Low & Flows & Limited & Varies \\
Clos/telemetry RCA & Fabric-spec. & Yes & RCA-focused & Varies \\
\textbf{ECNetBench} & \textbf{Yes} & \textbf{Yes} & \textbf{Yes} & \textbf{Yes} \\
\bottomrule
\end{tabular}}
\end{table}
""",
        encoding="utf-8",
    )

    (out / "tab_seeds_schema.tex").write_text(
        r"""\begin{table}[!t]
\centering
\caption{Frozen evaluation instances used in this study (authoritative SQLite stores).}
\label{tab:seeds}
\renewcommand{\arraystretch}{1.15}
{\footnotesize\begin{tabular}{llc}
\toprule
Instance folder & Role & Devices / links \\
\midrule
\texttt{v1} (v1.1.0-INST) & Primary frozen instance & 19 / 31 \\
\texttt{v1.1-seed101} & Independent seed & 19 / 31 \\
\texttt{v1.1-seed202} & Independent seed & 19 / 31 \\
\texttt{v1.1-seed303} & Independent seed & 19 / 31 \\
\texttt{v1.1-seed404} & Independent seed & 19 / 31 \\
\texttt{v1.1-seed505} & Independent seed & 19 / 31 \\
\bottomrule
\end{tabular}}
\end{table}

\begin{table}[!t]
\centering
\caption{Summary of ECNetBench relational schema families.}
\label{tab:schema}
\renewcommand{\arraystretch}{1.15}
{\footnotesize\begin{tabular}{p{2.4cm}p{5.3cm}}
\toprule
Family & Representative contents \\
\midrule
Inventory/topology & Devices, interfaces, topology snapshots, graph nodes/edges \\
Configuration & VLAN/ACL/QoS, routing processes, configuration snapshots/diffs \\
Telemetry & Interface counters, resources, syslog/alerts, flow aggregates \\
Services & Applications, services, SLA and impact bindings \\
Incidents/labels & Failure incidents, recovery actions, supervised label tables \\
\bottomrule
\end{tabular}}
\end{table}
""",
        encoding="utf-8",
    )

    (out / "tab_threats.tex").write_text(
        r"""\begin{table}[!t]
\centering
\caption{Threats to validity and corresponding mitigations.}
\label{tab:threats}
\renewcommand{\arraystretch}{1.2}
{\footnotesize\begin{tabular}{p{2.3cm}p{5.4cm}}
\toprule
Threat & Mitigation / residual risk \\
\midrule
Synthetic data & Realism audits; still not a substitute for production traces. \\
External validity & AOS-CX-style assumptions; other vendors/fabrics may differ. \\
Label leakage & Temporal freeze and feature audits; healing full vs.\ \texttt{no\_rca\_cat}. \\
Small $n$ seeds & Six seeds with confidence intervals; tests remain underpowered. \\
Topology scale & 19 devices / 31 links; scalability to large fabrics unproven. \\
Healing semantics & Decision support only; no live actuation evidence. \\
\bottomrule
\end{tabular}}
\end{table}
""",
        encoding="utf-8",
    )
    print("Wrote polished IEEE tables to", out)


if __name__ == "__main__":
    main()
