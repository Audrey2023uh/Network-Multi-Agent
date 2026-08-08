#!/usr/bin/env python3
"""Generate extra LaTeX stubs for extensions_v4 (practical impact + stronger baselines)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OL = Path(__file__).resolve().parents[1]
OUT = OL / "tables"


def f(x, n=4):
    if x is None or x == "":
        return "---"
    return f"{float(x):.{n}f}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pract = list(csv.DictReader((ROOT / "results" / "tables" / "practical_impact.csv").open(encoding="utf-8")))
    t1 = [r for r in pract if r["task"] == "T1_anomaly"]
    t1.sort(key=lambda r: float(r["auprc_mean"] or -1), reverse=True)
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{T1 practical ranking proxies from the full-suite harness (six frozen seeds; AUPRC column uses harness \texttt{ecn\_proposed}, not Table~\ref{tab:t1t2} selection mean). Precision@$k$ and FPR at fixed recall are derived from test scores/labels only.}",
        r"\label{tab:practical_v4}",
        r"{\footnotesize\begin{tabular}{lcccc}",
        r"\toprule",
        r"Method & AUPRC & P@50 & FPR@R0.5 & FPR@R0.8 \\",
        r"\midrule",
    ]
    for r in t1:
        name = r["method"].replace("__full", "").replace("_", r"\_")
        lines.append(
            f"{name} & ${f(r['auprc_mean'])}$ & ${f(r['precision_at_50_mean'])}$ & "
            f"${f(r['fpr_at_recall_0_5_mean'])}$ & ${f(r['fpr_at_recall_0_8_mean'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (OUT / "tab_practical_impact_v4.tex").write_text("\n".join(lines), encoding="utf-8")

    xai = json.loads((ROOT / "results" / "xai_validation.json").read_text(encoding="utf-8"))
    s = xai.get("summary") or {}
    lines = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{RCA explanation rank stability across six seeds (TreeSHAP or impurity fallback). TreeSHAP does not affect T1 AUPRC.}",
        r"\label{tab:xai_stability_v4}",
        r"{\footnotesize\begin{tabular}{lc}",
        r"\toprule",
        r"Metric & Value \\",
        r"\midrule",
        f"Mean Jaccard (top-10) & ${f(s.get('mean_jaccard_top10'))}$ \\\\",
        f"Mean Spearman $\\rho$ & ${f(s.get('mean_spearman_rho'))}$ \\\\",
        f"Seeds with TreeSHAP & ${xai.get('seeds_with_shap')}/{xai.get('n_seeds')}$ \\\\",
        r"\bottomrule",
        r"\end{tabular}}",
        r"\end{table}",
        "",
    ]
    (OUT / "tab_xai_stability_v4.tex").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT / "tab_practical_impact_v4.tex")
    print("wrote", OUT / "tab_xai_stability_v4.tex")


if __name__ == "__main__":
    main()
