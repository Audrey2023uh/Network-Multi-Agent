# Scientific Optimization — Final Framing for Journal Submission

**Benchmark:** frozen (unchanged).  
**Compared:** pre-opt ECN (v1) vs optimized ECN (v2) on six seeds.  
**Artifacts:** `DIAGNOSIS_T1_T2.md`, `OPTIMIZATION_COMPARISON.md`, `aggregate_v1_pre_opt.json`, `aggregate.json`

---

## 1. Diagnosis (pre-optimization)

| Gap | Primary causes (evidence-backed) | Not sole causes |
|-----|----------------------------------|-----------------|
| **T1: logistic > proposed** | (1) Fusion/meta overfit to validation (nesting violation vs telem specialist); (2) unstable specialist selection under ~1% positives; (3) IF score geometry mismatch across splits | Thresholding (AUPRC is threshold-free); HP search alone |
| **T2: RF > proposed** | (1) **Feature under-specification** (no iface deltas / temporal z / nbr aggregates); (2) poor score quality (Brier 0.12–0.22 vs RF ~0.02); (3) extreme imbalance (~0.5% prior) | Thresholding alone |

Full write-up: `results/DIAGNOSIS_T1_T2.md`.

---

## 2. Justified optimizations applied

| Change | Scientific rationale |
|--------|----------------------|
| Leakage-safe temporal deltas + expanding device z-scores | Change detection / relative load; causal (`shift(1)` history) |
| Interface error/discard/carrier deltas on T1 **and T2** | Precursors to link/device failure; fixes T2 under-specification |
| Twin residuals (`cpu_vs_nbr`, nbr error aggregates, nbr degree sum) | Digital-twin contrast / structural risk, not raw topology only |
| Anchored fusion (telem weight ≥ 0.5 or telem-only) | Encodes stable telem prior; restores nesting vs logistic specialist |
| Train–val consistency before leaving telem | Reduces rare-event val overfit |
| `scale_pos_weight` for LGBM; RF specialist in fusion | Standard imbalance handling; nonlinear interactions |
| Train empirical CDF for IsolationForest | Stable anomaly score mapping across splits |
| **Rejected:** isotonic-before-ranking | Improved Brier but **hurt AUPRC** with few positives (empirically verified) |

No benchmark edits. No new modules. No metric hacking.

---

## 3. Results after optimization (n=6, mean [95% CI])

### T1 anomaly (primary: AUPRC)

| Method | AUPRC | Notes |
|--------|-------|-------|
| **ECN proposed** | **0.0577 [0.0214, 0.0940]** | ≈ pre-opt (Δ≈0) |
| Logistic | 0.0631 [0.0235, 0.1028] | |
| **Random forest** | **0.0758 [0.0427, 0.1090]** | strongest T1 baseline after feature enrichment |
| LightGBM | 0.0505 [0.0234, 0.0776] | |

Proposed T1 metrics: ROC-AUC 0.683 [0.554, 0.812]; F1 0.039; precision 0.096; recall 0.114; Brier 0.181.

Wilcoxon proposed vs logistic: p=0.25, Cliff δ=−0.08 (**not significant**).  
vs RF: p=0.44, δ=−0.33 (**not significant**, RF favored).

### T2 failure

| Method | AUPRC | Notes |
|--------|-------|-------|
| **ECN proposed** | **0.0381 [−0.0026, 0.0788]** | **+0.023 vs pre-opt** |
| Logistic | 0.0380 [−0.0027, 0.0788] | essentially tied with proposed |
| Random forest | 0.0176 [0.0099, 0.0253] | pre-opt leader; **now below** proposed/logistic on enriched features |

Wilcoxon proposed vs RF: p=0.44, δ=+0.28 (direction favors proposed, **not significant** at α=0.05).  
vs logistic: p≈1.0, δ≈0 (**tied** — fusion usually selects `telem_only`).

---

## 4. Direct answers

### Does optimized ECN outperform logistic (T1) or RF (T2)?

- **T1 vs logistic:** No. Proposed remains slightly below; difference not significant.
- **T1 vs RF:** No. RF is strongest after shared telem enrichment.
- **T2 vs RF:** Mean AUPRC higher for proposed, but **not statistically significant** (n=6).
- **T2 vs logistic:** Effectively **tied** (same telem specialist under anchored fusion).

### If still not superior, why?

1. **Benchmark signal structure:** At ~1% positives, linear telem features carry most recoverable ranking signal. Twin features do not consistently improve T1 AUPRC (ablation: twin gain T1 ≈ **−0.011** after opt).
2. **Nesting:** Correct fusion → proposed ≈ best stable specialist ≈ telem logistic. It cannot beat logistic while selecting telem-only.
3. **Shared feature uplift:** Temporal/iface enrichment raised **all** telem-using methods; RF gained most on T1; proposed’s T2 gain is largely the same enrichment, not unique multi-agent magic.
4. **n=6 seeds:** Paired tests underpowered; large CIs.

### What *is* supported?

- Pre-opt T2 gap was largely **feature under-specification** — fixing it **more than doubled** proposed T2 AUPRC (0.015 → 0.038).
- Anchored fusion **removes nesting violations** (proposed no longer collapses below its telem specialist on average).
- Telemetry remains the **most contributing** module; multi-agent orchestration is a **selection/robustness** layer, not an automatic accuracy win.
- Complete ECN pipeline (twin, agents, RCA, healing) remains a system contribution evaluated under B01 multi-seed protocol.

---

## 5. Strongest defensible publication framing

**Do claim**
1. First end-to-end Enterprise Cognitive Network (twin + multi-agent detection/prediction/RCA/healing) evaluated on frozen multi-seed ECNetBench under B01.
2. Diagnosis-driven optimization: T2 failure prediction was limited by missing temporal/iface/twin precursors; correcting that yields large AUPRC gains.
3. Ablations: telemetry dominates; twin contribution is **task-dependent and modest**; neighbor readout least impactful.
4. Honest multi-seed CIs, Cliff’s δ, Wilcoxon — including **non-superiority** vs strong tabular baselines on T1.
5. Operational story: RCA attributions + healing decision support close the loop even when detector AUPRC is comparable to logistic/RF.

**Do not claim**
- Uniform statistical superiority over logistic/RF on T1/T2.
- That multi-agent fusion alone beats strong tabular baselines.
- That Digital Twin is the main T1 accuracy driver on this instance family.

**Recommended thesis sentence**

> On ECNetBench, an Enterprise Cognitive Network matching strong telem baselines via anchored fusion, while Twin/temporal enrichment materially improves failure-horizon ranking and enables explainable RCA and healing—establishing a complete, rigorously evaluated cognitive NetOps architecture rather than a universal detector champion.

---

## 6. File index

| File | Role |
|------|------|
| `results/DIAGNOSIS_T1_T2.md` | Pre-opt causal diagnosis |
| `results/OPTIMIZATION_COMPARISON.md` | v1 vs v2 tables + per-seed |
| `results/JOURNAL_FRAMING_OPTIMIZED.md` | This document |
| `results/ECN_EVALUATION_REPORT.md` | Full optimized metric report |
| `results/aggregate_v1_pre_opt.json` | Frozen pre-opt aggregate |
| `results/aggregate.json` | Optimized aggregate |
