# Final T1 Architecture Selection

**Protocol:** frozen ECNetBench six seeds, temporal 70/15/15, leakage-safe v3 features, validation-only fusion selection.
**Principle:** simplest scientifically defensible model with strongest reproducible performance.
**Manuscript:** not edited (numbers staged for approval).

## Decision: **ANCHORED** (`ECNFusionModel`)

Stacking status: **ablation negative result**.

### Reasons

- Higher mean T1 AUPRC (0.115221 > 0.099746)
- Anchored fusion is simpler (telem≥0.5 convex mixes; no meta-learner)
- Stacking treated as ablation / negative result for T1
- Paired AP Wilcoxon p=0.375, Cliff δ=0.1111, bootstrap P(anch>stack)=0.865

### Tradeoffs (honest)

Primary ranking metric is **AUPRC**. Secondary metrics do **not** all favor anchored:

| Secondary | Winner | Implication |
|---|---|---|
| ROC-AUC | stacking (0.780 vs 0.753) | Discrimination slightly better under stack; not primary claim metric |
| Brier / ECE (raw scores) | stacking | Anchored raw scores are less calibrated; **optional Beta calibration** addresses display probabilities without changing AUPRC ranking |
| Per-seed AP std | stacking (0.032 vs 0.068) | Anchored mean lift is driven partly by seed202; n=6 Wilcoxon not significant |
| Train cost | anchored (slightly) | Negligible |
| Interpretability | **anchored** | Telemetry-first convex mix is operator-explainable |

Selection still prefers **anchored**: strongest mean AUPRC under the frozen protocol, simpler fusion, stacking demoted to ablation. Do not claim paired statistical superiority over stacking on n=6 (p=0.375); claim mean improvement and simplicity.

## Head-to-head (six-seed means)

| Metric | v3-feat + anchored | v3-feat + stacking | RF telem_only | Prefer |
|---|---:|---:|---:|---|
| AUPRC | **0.115221** | 0.099746 | 0.075838 | higher |
| ROC-AUC | 0.753359 | 0.780315 | 0.766066 | higher |
| Brier ↓ | 0.150915 | 0.083438 | 0.022697 | lower |
| ECE ↓ | 0.287995 | 0.157564 | 0.071407 | lower |
| AP std ↓ | 0.067858 | 0.032412 | 0.031608 | lower |
| Train time (s) ↓ | 2.2142 | 2.2838 | 0.5859 | lower |

### 95% CIs (bootstrap mean of seed APs)

- Anchored AUPRC: [0.067898, 0.167973] (parametric [0.0440084397334875, 0.18643312258065362])
- Stacking AUPRC: [0.076262, 0.122512] (parametric [0.06573191631162888, 0.13375981271878135])
- Anchored ROC-AUC: [0.684781, 0.832121]
- Stacking ROC-AUC: [0.725432, 0.843802]

### Paired tests (anchored − stacking)

| Metric | mean Δ | Wilcoxon p | paired t p | Cliff δ | bootstrap P(Δ>0) |
|---|---:|---:|---:|---:|---:|
| ap | 0.015475 | 0.375 | 0.3632841643234252 | 0.1111 | 0.865 |
| roc_auc | -0.026957 | 0.875 | 0.4352475166967484 | -0.1111 | 0.326 |
| brier | 0.067477 | 0.125 | 0.11310724394438726 | 0.5556 | 0.999 |
| ece | 0.130431 | 0.125 | 0.06316384492925223 | 0.6111 | 0.999 |

### Per-seed AUPRC

| Seed | Anchored | Stacking | Δ (A−S) | RF |
|---|---:|---:|---:|---:|
| v1.1.0-INST | 0.107977 | 0.107977 | +0.000000 | 0.098151 |
| seed101 | 0.151926 | 0.119165 | +0.032762 | 0.037956 |
| seed202 | 0.224340 | 0.142541 | +0.081799 | 0.077661 |
| seed303 | 0.024191 | 0.052698 | -0.028506 | 0.037565 |
| seed404 | 0.103686 | 0.103686 | +0.000000 | 0.112829 |
| seed505 | 0.079205 | 0.072410 | +0.006795 | 0.090867 |

## Interpretability

| Aspect | Anchored (`ECNFusionModel`) | Stacking (`ECNStackFusionModel`) |
|---|---|---|
| Fusion form | Convex mixes with **telem weight ≥ 0.5** (or singleton) | Unconstrained mixes + logistic meta-learner on specialist scores |
| Operator story | Telemetry-first ensemble with optional twin specialist | Score-level stacking; harder to explain weight provenance |
| Complexity | Lower | Higher |
| Selection | Validation AUPRC | Validation AUPRC + train-consistency guards |

Anchored fusion is preferred for interpretability when performance is not worse.

## Computational cost

- Mean train time anchored: **2.2142 s**
- Mean train time stacking: **2.2838 s**
- Mean train time RF telem: **0.5859 s**

Specialist training dominates; stacking adds a cheap meta fit. Cost is not decisive.

## Final proposed T1 architecture

1. Leakage-safe enriched features (v3).
2. **`ECNFusionModel` (anchored / telemetry-first fusion)**.
3. Optional Beta calibration for probability display (does not change ranking AUPRC).
4. RCA: RF + TreeSHAP (unchanged).
5. **Stacking:** reported as ablation / negative result for T1 (mean AP lower).

T2 remains hybrid: telem logistic under ultra-rare prior (do not claim stack superiority on T2).

Artifacts: `results/v3_gated/t1_architecture_selection.json`, `results/final_architecture.json`, `results/manuscript_ready_numbers.json`.

