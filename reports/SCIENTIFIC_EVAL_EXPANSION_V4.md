# Scientific Evaluation Expansion Report (extensions_v4)

**Date:** 2026-08-07 (local) / 2026-08-08 UTC eval run  
**Repo:** Network-Multi-Agent  
**Protocol:** Frozen ECNetBench six seeds only (`v1.1.0-INST`, `seed101`–`seed505`). No SQLite or checksum modifications.

## 1. What changed (implementation)

| Area | Change |
|------|--------|
| Baselines | Added **XGBoost**, **CatBoost**; promoted **gradient_boosting**, **balanced_rf** into `BINARY_BASELINES` |
| Metrics | `eval_binary` now records Precision@k, FPR@recall, RSS delta |
| Analysis scripts | `compute_practical_impact`, `compute_scientific_stats`, `compute_sensitivity`, `compute_scalability`, `validate_explanations`, `compute_scenario_coverage`, `update_manuscript_extensions_v4` |
| Dashboard | Pages: Practical Impact, Sensitivity, Scalability, Ablation, XAI Validation, Live Prototype |
| Paper | Regenerated `tab_t1t2.tex` with stronger baselines; added `tab_practical_impact_v4.tex`, `tab_xai_stability_v4.tex` |
| Manuscript | Appended `extensions_v4` to `results/manuscript_ready_numbers.json` (**did not overwrite** authoritative `T1_final_proposed`) |

## 2. Experiments run

1. `python -m evaluation.run_full_evaluation` (~323 s wall, six seeds)  
2. Consolidation scripts listed above  
3. `interactive_dashboard/scripts/build_data.py` + validate  
4. Overleaf table/figure regeneration (PDF save may warn on Windows; PNGs written)

## 3. Key measured results (T1 AUPRC mean, six seeds)

| Method | T1 AUPRC |
|--------|----------|
| **ECN proposed (anchored v3)** | **0.1154** |
| Random Forest (telem) | 0.0758 |
| Gradient Boosting | 0.0730 |
| Logistic | 0.0631 |
| Isolation Forest | 0.0575 |
| LightGBM | 0.0570 |
| CatBoost | 0.0528 |
| XGBoost | 0.0471 |
| Balanced RF | 0.0467 |

**Honest takeaway:** Stronger modern GBDTs (**XGBoost/CatBoost**) did **not** beat Random Forest on this rare-event telem_only protocol. ECN remains ahead of the best classical baseline on mean T1 AUPRC; T2 recommended head remains telem logistic (~0.038).

Authoritative manuscript T1 final selection numbers remain those in `T1_final_proposed` (AUPRC ≈ **0.11522**); the re-run mean ≈ 0.11539 (seed RNG / env noise).

## 4. Practical impact / XAI / sensitivity (highlights)

- Practical proxies: see `results/practical_impact.json` (Precision@k, FPR@recall).  
- Stats: Wilcoxon + Cliff’s δ + BH-FDR + paired bootstrap in `results/scientific_stats_v4.json` (n=6; interpret cautiously).  
- XAI: mean top-10 Jaccard ≈ **0.84** across seeds (`results/xai_validation.json`). In this run, RCA explanations used **impurity importances** on all six seeds (TreeSHAP export not present in stored explanations). TreeSHAP remains **explanation-only** on the RCA path and does not change T1 AUPRC.  
- Scenario coverage: **14** distinct incident categories already in frozen DBs (`results/scenario_coverage.json`).  
- Scalability: timing/RSS on **~19-device** fabrics only (`results/scalability_measured.json`).

## 5. Live API prototype

Dashboard route `/live-prototype`: adapter interface with opt-in URL probe; **no synthetic live stream**; clearly separated from historical benchmark replay.

## 6. Limitations (explicit non-claims)

- No new topologies / device-count sweeps / newly injected multi-failure DBs  
- No TabNet / true GraphSAGE (proxy remains LightGBM-on-twin features)  
- No human-rated explanation quality study  
- No fabricated MTTR / dollar ROI  
- Fabric-size scalability **not measured**

## 7. How to reproduce

```bash
pip install -r requirements.txt
python -m evaluation.run_full_evaluation
python -m evaluation.compute_practical_impact
python -m evaluation.compute_scientific_stats
python -m evaluation.compute_sensitivity
python -m evaluation.compute_scalability
python -m evaluation.validate_explanations
python -m evaluation.compute_scenario_coverage
python -m evaluation.update_manuscript_extensions_v4
python interactive_dashboard/scripts/build_data.py
python interactive_dashboard/scripts/validate_dashboard_data.py
```
