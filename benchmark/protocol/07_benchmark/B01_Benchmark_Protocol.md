# B01 — Benchmark Protocol

This protocol is intended to be **normative** for papers claiming results on ECNetBench.

---

## 1. Tracks

| Track ID | Name | Primary tasks |
|----------|------|---------------|
| TR-AD | Anomaly detection | T1 |
| TR-FP | Failure prediction | T2 |
| TR-RCA | Root cause analysis | T3 |
| TR-IMP | Impact prediction | T4 |
| TR-DEG | Service degradation | T5 |
| TR-CFG | Configuration risk | T6 |
| TR-AUTO | Autonomous recovery (optional) | action success / downtime |
| TR-XFER | Cross-topology transfer | T1–T3 on held-out topology category |

---

## 2. Official splits

### 2.1 Temporal freeze split (default)

For each topology instance with duration `[T0, T1]`:

- **Train:** `[T0, T_freeze)`  
- **Validation:** `[T_freeze, T_test)`  
- **Test:** `[T_test, T1]`  

Recommended fractions: 70% / 15% / 15% by time, with boundaries snapped to day starts (UTC).

**Embargo:** drop samples with `t0` in the last `L` minutes of train that would need post-boundary labels spanning val (horizon leakage guard).

### 2.2 Rolling-origin evaluation (required reporting for T2/T5)

Origins `t0 ∈ {τ1…τm}` spaced by stride S (e.g., 1 day). For each origin, train on all data ≤ `τ - g`, test on `(τ, τ+H]` windows. Report mean ± std across origins.

### 2.3 Cross-topology validation (required for novelty claims)

Hold out **entire topology categories**:

| Fold | Train categories | Test category |
|------|------------------|---------------|
| A | campus, branch | dc_evpn |
| B | campus, dc_evpn | branch |
| C | dc_evpn, branch | campus |
| D | all but hybrid | hybrid |

Report per-fold and macro-average. This operationalizes digital-twin generalization requirements.

### 2.4 Forbidden split practices

- Random shuffle of time-adjacent windows into train/test  
- Using `CAUSES`/`IMPACTS` edges as input features  
- Training on test topology nodes via shared global IDs without re-indexing isolation  
- Tuning thresholds on the test set  

---

## 3. Feature leakage checklist

Reviewers/authors must confirm:

1. Features at `t0` use `observed_at ≤ t0` only  
2. Config diffs after `t0` excluded for FP/AD  
3. Service KPI labels not duplicated as features unless causal lag ≥ H  
4. Syslog messages that explicitly name the injected fault script are scrubbed or delayed  

---

## 4. Evaluation metrics

### 4.1 Classification (AD/FP/CFG)

| Metric | Notes |
|--------|-------|
| AUPRC | Primary under imbalance |
| AUROC | Secondary |
| F1 / Precision / Recall | At val-chosen threshold |
| Event-level F1 | Merge consecutive positives |
| Detection delay | Mean/median onset→first alarm |
| False alarms / day | Operator cost |

### 4.2 RCA

| Metric | Notes |
|--------|-------|
| Cause macro-F1 | Categories |
| Top-1 / Top-3 localization | Entity ID |
| Hidden-target accuracy | Slice |
| Compound-fault accuracy | Slice |

### 4.3 Impact / degradation

| Metric | Notes |
|--------|-------|
| Service set F1 | Multi-label |
| Downtime MAE | Seconds |
| SLA breach F1 | |
| Criticality-weighted F1 | Weight by tier |

### 4.4 Recovery / autonomy

| Metric | Notes |
|--------|-------|
| Recovery success rate | |
| Mean downtime | |
| Mean actions to recover | Efficiency |
| Blast-radius reduction | If counterfactual twin available |

### 4.5 Calibration & robustness

- ECE / reliability diagrams for probabilistic models  
- Performance under missing telemetry masks (10%, 30%)  
- Noise injection on syslog parse failures  

---

## 5. Baseline families (must compare against ≥3)

1. **Threshold / EWMA / Isolation Forest** on univariate counters  
2. **Tree ensembles** (XGBoost/LightGBM) on tabular window features  
3. **Sequence models** (TCN/LSTM/Transformer) on multivariate series  
4. **GNN** (GCN/GAT/GraphSAGE/STGNN) on `G_t`  
5. **Log NLP** (TF-IDF + linear, or small Transformer) for RCA  
6. **Oracle detection delay lower bound** using GT onset (for AD delay reporting honesty)

---

## 6. Reporting template (paper checklist)

- [ ] Dataset version + label schema version  
- [ ] Topology profiles used  
- [ ] Split type + freeze timestamps  
- [ ] Horizons H and history L  
- [ ] Class priors in train/test  
- [ ] Metrics with confidence intervals  
- [ ] Cross-topology fold table  
- [ ] Failure category breakdown  
- [ ] Compute budget  
- [ ] Negative results / failure modes  

---

## 7. Statistical testing

For comparing methods on rolling-origin folds, use paired Wilcoxon or Diebold–Mariano where applicable; correct multi-metric multi-task comparisons (e.g., Holm–Bonferroni) when claiming superiority.
