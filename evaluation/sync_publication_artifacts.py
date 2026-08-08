#!/usr/bin/env python3
"""Synchronize publication tables/text helpers from authoritative artifacts.

Source of truth for final T1 head:
  results/manuscript_ready_numbers.json  (architecture selection / gated)
  results/v3_gated/t1_architecture_selection.json

Full-suite harness re-runs write results/aggregate_v3.json and may show a slightly
different ecn_proposed__full mean (~0.1106) due to eval-path / RNG differences.
Those values are valid for baseline comparison in the latest harness, but must NOT
silently replace the architecture-selection final T1 claim.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "results" / "manuscript_ready_numbers.json"
SEL = ROOT / "results" / "v3_gated" / "t1_architecture_selection.json"
PER = ROOT / "results" / "per_seed"
AGG = ROOT / "results" / "aggregate_v3.json"
OUT_TAB = ROOT / "results" / "tables"
OL_TAB = ROOT / "paper" / "overleaf" / "tables"
OL_RES = ROOT / "paper" / "overleaf" / "results"


def f(x: Any, n: int = 4) -> str:
    if x is None:
        return "---"
    return f"{float(x):.{n}f}"


def cliffs_delta(a: List[float], b: List[float]) -> float:
    aa, bb = np.asarray(a, float), np.asarray(b, float)
    gt = sum(x > y for x in aa for y in bb)
    lt = sum(x < y for x in aa for y in bb)
    return float((gt - lt) / (len(aa) * len(bb)))


def wilcoxon(a: List[float], b: List[float]) -> Dict[str, Any]:
    aa, bb = np.asarray(a, float), np.asarray(b, float)
    if len(aa) < 3 or np.allclose(aa, bb):
        return {"statistic": None, "pvalue": None}
    try:
        w = stats.wilcoxon(aa, bb)
        return {"statistic": float(w.statistic), "pvalue": float(w.pvalue)}
    except Exception as e:
        return {"statistic": None, "pvalue": None, "note": str(e)}


def load_baseline_aps(seeds: List[str], method: str) -> List[float]:
    out = []
    for s in seeds:
        d = json.loads((PER / f"{s}.json").read_text(encoding="utf-8"))
        out.append(float(d["tasks"]["T1_anomaly"][method]["ap"]))
    return out


def main() -> None:
    ms = json.loads(MS.read_text(encoding="utf-8"))
    sel = json.loads(SEL.read_text(encoding="utf-8"))
    agg = json.loads(AGG.read_text(encoding="utf-8")) if AGG.exists() else {}

    # Provenance block
    harness_mean = (
        (((agg.get("metrics") or {}).get("T1_anomaly") or {}).get("ecn_proposed__full") or {})
        .get("ap", {})
        .get("mean")
    )
    provenance = {
        "authoritative_T1_final": {
            "source": "results/manuscript_ready_numbers.json -> T1_final_proposed",
            "supporting": "results/v3_gated/t1_architecture_selection.json",
            "auprc_mean": ms["T1_final_proposed"]["auprc_mean"],
            "auprc_ci95_bootstrap": ms["T1_final_proposed"]["auprc_ci95_bootstrap"],
            "auprc_ci95_parametric": ms["T1_final_proposed"]["auprc_ci95_parametric"],
            "note": "Use bootstrap CI in manuscript prose unless parametric is explicitly named.",
        },
        "full_suite_harness_rerun": {
            "source": "results/aggregate_v3.json -> metrics.T1_anomaly.ecn_proposed__full",
            "auprc_mean": harness_mean,
            "note": (
                "Latest run_full_evaluation.py may differ slightly from architecture-selection "
                "means due to RNG / fusion path differences. Do not overwrite T1_final_proposed."
            ),
        },
        "baselines_and_deep_models": {
            "source": "results/aggregate_v3.json + results/per_seed/*.json",
            "note": "TabNet, GraphSAGE, XGBoost, etc. come from the full-suite harness.",
        },
    }
    ms["publication_provenance"] = provenance
    ms["note"] = (
        "Authoritative final T1 = architecture-selection anchored ECN-v3 "
        "(T1_final_proposed). aggregate_v3 is the latest full-suite harness for baselines/"
        "deep models/ablation matrices and may show a slightly different proposed mean."
    )
    MS.write_text(json.dumps(ms, indent=2), encoding="utf-8")
    (ROOT / "results" / "PUBLICATION_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )

    # Rebuild significance using architecture-selection proposed vs harness baselines
    seeds = [r["seed"] for r in sel["per_seed"]]
    prop = [float(r["anchored"]["ap"]) for r in sel["per_seed"]]
    baselines = [
        "tabnet__full",
        "graphsage__full",
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
    ]
    sig_rows = []
    for mk in baselines:
        try:
            base = load_baseline_aps(seeds, mk)
        except Exception:
            continue
        if len(base) != len(prop):
            continue
        w = wilcoxon(prop, base)
        sig_rows.append(
            {
                "task": "T1_anomaly",
                "baseline": mk,
                "wilcoxon_p": w.get("pvalue"),
                "cliffs_delta": cliffs_delta(prop, base),
                "proposed_ap_mean": float(np.mean(prop)),
                "baseline_ap_mean": float(np.mean(base)),
            }
        )
    # T2: proposed fusion vs logistic etc from harness (T2 recommended is logistic)
    t2_prop, t2_lr = [], []
    for s in seeds:
        d = json.loads((PER / f"{s}.json").read_text(encoding="utf-8"))
        t2_prop.append(float(d["tasks"]["T2_failure"]["ecn_proposed__full"]["ap"]))
        t2_lr.append(float(d["tasks"]["T2_failure"]["logistic__full"]["ap"]))
    for mk, vals in [
        ("logistic__full", t2_lr),
        ("random_forest__full", [float(json.loads((PER / f"{s}.json").read_text(encoding="utf-8"))["tasks"]["T2_failure"]["random_forest__full"]["ap"]) for s in seeds]),
    ]:
        w = wilcoxon(t2_prop, vals)
        sig_rows.append(
            {
                "task": "T2_failure",
                "baseline": mk,
                "wilcoxon_p": w.get("pvalue"),
                "cliffs_delta": cliffs_delta(t2_prop, vals),
                "proposed_ap_mean": float(np.mean(t2_prop)),
                "baseline_ap_mean": float(np.mean(vals)),
            }
        )

    OUT_TAB.mkdir(parents=True, exist_ok=True)
    with (OUT_TAB / "significance_vs_proposed.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "task",
                "baseline",
                "wilcoxon_p",
                "cliffs_delta",
                "proposed_ap_mean",
                "baseline_ap_mean",
            ],
        )
        w.writeheader()
        w.writerows(sig_rows)

    # Write significance tex with authoritative proposed mean
    lines = [
        r"\begin{table*}[!t]",
        r"\centering",
        r"\caption{Paired Wilcoxon signed-rank tests and Cliff's $\delta$ on per-seed AUPRC. For T1, the proposed vector is the architecture-selection anchored head (\texttt{manuscript\_ready\_numbers.json}, mean $0.1152$); baselines are from the latest full-suite harness. $n{=}6$ tests are underpowered; non-significant $p$-values must not be over-claimed.}",
        r"\label{tab:sig}",
        r"\renewcommand{\arraystretch}{1.12}",
        r"\setlength{\tabcolsep}{3.5pt}",
        r"{\scriptsize\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llcccc}",
        r"\toprule",
        r"Task & Baseline & $p$ & Cliff $\delta$ & Proposed & Baseline \\",
        r"\midrule",
    ]
    prev = None
    for r in sig_rows:
        task_raw = r["task"]
        task = task_raw.replace("_", r"\_")
        task_cell = task if task_raw != prev else ""
        prev = task_raw
        base = r["baseline"].replace("_", r"\_")
        pv = r["wilcoxon_p"]
        pv_s = f"{pv:.3f}" if isinstance(pv, float) else "---"
        lines.append(
            f"{task_cell} & {base} & ${pv_s}$ & ${f(r['cliffs_delta'], 3)}$ & "
            f"${f(r['proposed_ap_mean'])}$ & ${f(r['baseline_ap_mean'])}$ \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular*}}", r"\end{table*}", ""]
    OL_TAB.mkdir(parents=True, exist_ok=True)
    (OL_TAB / "tab_significance.tex").write_text("\n".join(lines), encoding="utf-8")

    # Deep baselines table with correct bootstrap CI
    ci = ms["T1_final_proposed"]["auprc_ci95_bootstrap"]
    t1m = (agg.get("metrics") or {}).get("T1_anomaly") or {}
    t2m = (agg.get("metrics") or {}).get("T2_failure") or {}

    def ap_ci(block: Dict[str, Any]) -> Tuple[Any, Any, Any]:
        ap = (block or {}).get("ap") or {}
        return ap.get("mean"), (ap.get("ci95") or [None, None])[0], (ap.get("ci95") or [None, None])[1]

    deep = [
        r"\begin{table}[!t]",
        r"\centering",
        r"\caption{Deep baselines on frozen six-seed T1/T2. ECN-v3 final uses architecture-selection numbers (\texttt{manuscript\_ready\_numbers.json}, bootstrap 95\% CI). TabNet and true GraphSAGE use the full-suite harness. The historical GNN proxy is LightGBM, not message-passing.}",
        r"\label{tab:deep_baselines_v5}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"{\footnotesize\begin{tabular}{lcc}",
        r"\toprule",
        r"Method & T1 AUPRC & T2 AUPRC \\",
        r"\midrule",
        f"ECN-v3 final (manuscript) & ${f(ms['T1_final_proposed']['auprc_mean'])}$ $[{f(ci[0])},{f(ci[1])}]$ & --- \\\\",
    ]
    for label, key in [
        ("TabNet", "tabnet__full"),
        ("GraphSAGE (true GNN)", "graphsage__full"),
        ("GNN proxy (LightGBM)", "gnn_graphsage_proxy__full"),
        ("Random forest (telem)", "random_forest__full"),
    ]:
        m1, lo1, hi1 = ap_ci(t1m.get(key))
        m2, lo2, hi2 = ap_ci(t2m.get(key))
        deep.append(
            f"{label} & ${f(m1)}$ $[{f(lo1)},{f(hi1)}]$ & ${f(m2)}$ $[{f(lo2)},{f(hi2)}]$ \\\\"
        )
    deep += [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""]
    (OL_TAB / "tab_deep_baselines_v5.tex").write_text("\n".join(deep), encoding="utf-8")

    # Ablation caption note file (table values remain harness; labeled)
    abl_note = (
        "% Ablation means below are from the latest full-suite harness (aggregate_v3).\n"
        "% They must not be confused with the architecture-selection final T1 mean 0.11522.\n"
    )
    abl_path = OL_TAB / "tab_ablation.tex"
    if abl_path.exists():
        txt = abl_path.read_text(encoding="utf-8")
        if "architecture-selection final" not in txt:
            txt = txt.replace(
                r"\caption{Ablation study of mean AUPRC on T1 and T2 (six seeds, 95\% CI).}",
                r"\caption{Ablation study of mean AUPRC on T1 and T2 from the latest full-suite harness (six seeds, 95\% CI). The \texttt{full} row is a harness re-run and may differ slightly from the architecture-selection final T1 mean ($0.1152$) reported in Table~\ref{tab:t1t2}.}",
            )
            abl_path.write_text(abl_note + txt, encoding="utf-8")

    # Mirror manuscript_ready into overleaf results
    OL_RES.mkdir(parents=True, exist_ok=True)
    (OL_RES / "manuscript_ready_numbers.json").write_text(MS.read_text(encoding="utf-8"), encoding="utf-8")
    (OUT_TAB / "significance_vs_proposed.csv").write_text(
        (OUT_TAB / "significance_vs_proposed.csv").read_text(encoding="utf-8"), encoding="utf-8"
    )
    print("updated", MS)
    print("wrote", ROOT / "results" / "PUBLICATION_PROVENANCE.json")
    print("wrote", OL_TAB / "tab_significance.tex")
    print("wrote", OL_TAB / "tab_deep_baselines_v5.tex")


if __name__ == "__main__":
    main()
