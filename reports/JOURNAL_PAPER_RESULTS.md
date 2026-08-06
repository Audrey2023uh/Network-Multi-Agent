# Journal Results: Enterprise Cognitive Network on ECNetBench

**Status:** Framework implemented and evaluated on frozen multi-seed ECNetBench  
**Benchmark:** READ-ONLY (`09_artifacts/instances/v1` + `v1.1-seed{101,202,303,404,505}`)  
**Framework code/results:** `10_framework/` (separate from the benchmark)

---

## 1. What was implemented

Complete **Enterprise Cognitive Network (ECN)** pipeline:

| Component | Role |
|-----------|------|
| Digital Twin | Typed topology graph, structural features, 1-hop neighbor aggregates |
| PerceptionAgent | Twin-aware multi-modal feature construction |
| AnomalyAgent | T1 predictive anomaly detection |
| PredictionAgent | T2 failure-horizon prediction |
| RCAAgent | T3 explainable category RCA + feature attributions |
| ImpactAgent | T4 high-impact incident prediction |
| HealingAgent | TR-AUTO recovery-action recommendation |
| Orchestrator | Val-AP–optimal convex fusion of specialist scores |

**Baselines (B01 families):** threshold, EWMA, Isolation Forest, logistic, RF, LightGBM, MLP sequence proxy, GraphSAGE-style GNN proxy, log-feature RCA proxy.

**Protocol:** temporal freeze 70/15/15; features use only `observed_at ≤ t0`; no frozen dataset modification.

---

## 2. Headline quantitative findings (n=6 seeds, mean ± 95% CI)

### Does the proposed framework significantly outperform all baselines?

**No — not uniformly.**

| Task | Proposed AUPRC | Best baseline | Proposed wins? |
|------|----------------|---------------|----------------|
| T1 anomaly | 0.0579 [0.0148, 0.1009] | logistic 0.0701 [0.0369, 0.1033] | No |
| T2 failure | 0.0147 [0.0081, 0.0212] | random_forest 0.0362 [−0.0063, 0.0787] | No |
| T5 degradation | 0.1162 [0.0820, 0.1504] | logistic/RF ~0.108 | Yes (modest) |

Paired Wilcoxon tests: **3/17** significant wins (p<0.05 and Cliff’s δ>0), mainly vs weak classical detectors (majority / MLP), **not** vs logistic on T1.

### Which module contributes most?

**Telemetry** (T1): removing telemetry (twin-only ablation) drops AUPRC by **~0.039**.

Digital Twin still helps: full − no_twin AUPRC gain ≈ **+0.017 (T1)** and **+0.004 (T2)**.

### Which module contributes least?

**Neighbor message-passing** (1-hop aggregates): near-zero AUPRC change when removed on T2 (full ≈ no_nbr).

### Is the claimed novelty supported?

**Partially / qualified yes.**

Supported:
- End-to-end multi-agent + twin system runs on a frozen multi-seed benchmark
- Twin ablation shows positive AUPRC contribution
- RCA explanations + healing decision support are operational
- Beats several classical detectors; multi-seed CIs and effect sizes reported

Not supported as a blanket claim:
- Proposed does **not** dominate the strongest tabular baseline (logistic) on T1 across seeds
- T2 remains extremely hard under imbalance; RF mean AUPRC higher than proposed

---

## 3. Ablations (T1 AUPRC mean)

| Ablation | AUPRC |
|----------|-------|
| full (proposed) | 0.0579 |
| no_nbr | 0.0427 |
| no_twin / telem_only | 0.0413 |
| twin_only | 0.0187 |

---

## 4. Additional tasks

- **T3 RCA:** proposed macro-F1 ≈ 0.25; syslog ablation hurts strongly (≈0.11); small test-n caveat (≤6 incidents/seed in holdout).
- **TR-AUTO healing:** with post-RCA category features, macro-F1 = 1.0 across seeds; without category ≈ 0.19 → **RCA→healing coupling is the dominant healing signal**.
- **T4 impact:** near-ceiling metrics on redefined high-impact labels (small-n; interpret cautiously).
- **T6 config risk:** insufficient class support in temporal holdout for stable AUPRC (reported n/a).

---

## 5. Artifacts for the paper

| Artifact | Path |
|----------|------|
| Full report | `10_framework/results/ECN_EVALUATION_REPORT.md` |
| Aggregate JSON | `10_framework/results/aggregate.json` |
| Tables (CSV) | `10_framework/results/tables/` |
| ROC/PR, calibration, CM | `10_framework/results/figures/` |
| Per-seed metrics | `10_framework/results/per_seed/` |
| Re-run harness | `10_framework/run_full_evaluation.py` |

---

## 6. Recommended paper framing

Frame ECN as a **complete cognitive NetOps architecture** evaluated honestly on ECNetBench:

1. First multi-agent digital-twin system scored under B01 on this frozen benchmark  
2. Ablations quantify twin vs telemetry vs neighbor readout  
3. Explainable RCA + healing close the detection→action loop  
4. Multi-seed CIs show where classical tabular methods remain competitive — a strength for credibility at TNSM / Computer Networks

Avoid claiming universal superiority over logistic/RF on T1/T2; claim **system completeness + twin contribution + multi-task coverage + rigorous multi-seed statistics**.
