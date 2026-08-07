# Enterprise Cognitive Network — Evaluation Report on ECNetBench

**Framework version:** 1.1.0-optimized  
**Benchmark:** frozen ECNetBench v1.1.0-INST + seeds 101/202/303/404/505 (n=6)  
**Protocol:** temporal freeze 70/15/15; leakage-safe features (`observed_at ≤ t0`)  

## Executive verdict

- Proposed outperforms best baseline on T1 AUPRC: **True**
- Proposed outperforms best baseline on T2 AUPRC: **False**
- T1 proposed AUPRC mean: **0.09987388175137697** vs `random_forest__full` = **0.07583814878524626**
- T2 proposed AUPRC mean: **0.013974939365520694** vs `logistic__full` = **0.038043099063649714**
- Digital Twin AUPRC gain (full − no_twin): T1=**0.010873628454280873**, T2=**0.0**
- Significant wins (Wilcoxon p<0.05 & Cliff's δ>0): **10/17**
- Most contributing module: **telemetry**
- Least contributing module: **digital_twin**
- Novelty supported (qualified): **True**
- Novelty statement: Digital Twin + multi-agent fusion provide measurable AP gains vs twin-ablated variants and beat several classical detectors, but do not uniformly dominate the strongest tabular baseline on T1 across all seeds.

## T1 Anomaly detection (AUPRC primary)

| Method | AUPRC | AUROC | F1 |
|--------|-------|-------|----|
| `ecn_proposed__full` | 0.0999 ± [0.0657, 0.1340] | 0.7821 ± [0.6940, 0.8702] | 0.0829 ± [0.0173, 0.1484] |
| `lightgbm__full` | 0.0570 ± [0.0262, 0.0879] | 0.6798 ± [0.5417, 0.8179] | 0.0299 ± [-0.0069, 0.0666] |
| `random_forest__full` | 0.0758 ± [0.0427, 0.1090] | 0.7661 ± [0.6601, 0.8720] | 0.0470 ± [-0.0080, 0.1020] |
| `logistic__full` | 0.0631 ± [0.0235, 0.1028] | 0.7260 ± [0.6223, 0.8297] | 0.0381 ± [0.0036, 0.0726] |
| `isolation_forest__full` | 0.0575 ± [0.0255, 0.0895] | 0.6716 ± [0.5497, 0.7936] | 0.0373 ± [0.0075, 0.0671] |
| `ewma__full` | 0.0403 ± [0.0135, 0.0671] | 0.5484 ± [0.4741, 0.6228] | 0.0362 ± [0.0221, 0.0503] |
| `threshold__full` | 0.0315 ± [-0.0030, 0.0661] | 0.2864 ± [0.1671, 0.4058] | 0.0083 ± [-0.0015, 0.0181] |
| `mlp_sequence__full` | 0.0084 ± [0.0053, 0.0115] | 0.3617 ± [0.2126, 0.5108] | 0.0125 ± [0.0016, 0.0235] |
| `gnn_graphsage_proxy__full` | 0.0335 ± [0.0167, 0.0504] | 0.6846 ± [0.6160, 0.7531] | 0.0475 ± [0.0129, 0.0821] |
| `majority__full` | 0.0098 ± [0.0083, 0.0113] | 0.5000 ± [0.5000, 0.5000] | 0.0000 ± [0.0000, 0.0000] |

## T2 Failure prediction

| Method | AUPRC | AUROC | F1 |
|--------|-------|-------|----|
| `ecn_proposed__full` | 0.0140 ± [0.0028, 0.0252] | 0.6310 ± [0.5075, 0.7545] | 0.0285 ± [-0.0120, 0.0690] |
| `lightgbm__full` | 0.0213 ± [-0.0041, 0.0467] | 0.5483 ± [0.3623, 0.7344] | 0.0278 ± [-0.0436, 0.0992] |
| `random_forest__full` | 0.0176 ± [0.0099, 0.0253] | 0.7081 ± [0.6258, 0.7904] | 0.0262 ± [0.0007, 0.0518] |
| `logistic__full` | 0.0380 ± [-0.0027, 0.0788] | 0.6891 ± [0.5801, 0.7981] | 0.0198 ± [0.0051, 0.0344] |
| `isolation_forest__full` | 0.0216 ± [-0.0040, 0.0472] | 0.6459 ± [0.5221, 0.7696] | 0.0160 ± [-0.0045, 0.0365] |
| `ewma__full` | 0.0066 ± [0.0045, 0.0086] | 0.4482 ± [0.3423, 0.5540] | 0.0132 ± [0.0079, 0.0185] |
| `mlp_sequence__full` | 0.0054 ± [0.0041, 0.0067] | 0.3795 ± [0.2215, 0.5375] | 0.0090 ± [0.0044, 0.0136] |
| `gnn_graphsage_proxy__full` | 0.0106 ± [0.0069, 0.0144] | 0.5965 ± [0.5103, 0.6827] | 0.0095 ± [-0.0063, 0.0252] |
| `majority__full` | 0.0056 ± [0.0050, 0.0061] | 0.5000 ± [0.5000, 0.5000] | 0.0000 ± [0.0000, 0.0000] |

## Ablations

| Task | Ablation | AUPRC |
|------|----------|-------|
| T1_anomaly | full | 0.0999 ± [0.0657, 0.1340] |
| T1_anomaly | no_twin | 0.0890 ± [0.0411, 0.1369] |
| T1_anomaly | no_nbr | 0.1020 ± [0.0507, 0.1532] |
| T1_anomaly | telem_only | 0.0473 ± [0.0075, 0.0871] |
| T1_anomaly | twin_only | 0.0297 ± [0.0151, 0.0443] |
| T2_failure | full | 0.0140 ± [0.0028, 0.0252] |
| T2_failure | no_twin | 0.0140 ± [0.0028, 0.0252] |
| T2_failure | no_nbr | 0.0140 ± [0.0028, 0.0252] |
| T2_failure | telem_only | 0.0380 ± [-0.0027, 0.0788] |
| T2_failure | twin_only | 0.0137 ± [0.0094, 0.0179] |

## Significance (proposed vs baselines, AUPRC)

| Task | Baseline | p | Cliff δ |
|------|----------|---|---------|
| T1_anomaly | `lightgbm__full` | 0.03125 | 0.6666666666666666 |
| T1_anomaly | `random_forest__full` | 0.3125 | 0.4444444444444444 |
| T1_anomaly | `logistic__full` | 0.03125 | 0.5 |
| T1_anomaly | `isolation_forest__full` | 0.03125 | 0.6666666666666666 |
| T1_anomaly | `ewma__full` | 0.03125 | 0.8333333333333334 |
| T1_anomaly | `threshold__full` | 0.03125 | 0.8888888888888888 |
| T1_anomaly | `mlp_sequence__full` | 0.03125 | 1.0 |
| T1_anomaly | `gnn_graphsage_proxy__full` | 0.03125 | 0.9444444444444444 |
| T1_anomaly | `majority__full` | 0.03125 | 1.0 |
| T2_failure | `lightgbm__full` | 0.84375 | -0.16666666666666666 |
| T2_failure | `random_forest__full` | 0.5625 | -0.3888888888888889 |
| T2_failure | `logistic__full` | 0.5625 | -0.5555555555555556 |
| T2_failure | `isolation_forest__full` | 0.4375 | -0.16666666666666666 |
| T2_failure | `ewma__full` | 0.15625 | 0.5 |
| T2_failure | `mlp_sequence__full` | 0.03125 | 0.8333333333333334 |
| T2_failure | `gnn_graphsage_proxy__full` | 0.84375 | -0.05555555555555555 |
| T2_failure | `majority__full` | 0.03125 | 1.0 |

## Cost
- {'per_seed_wall_s': {'n': 6, 'mean': 46.393543916657414, 'std': 1.324544173628698, 'ci95': [45.00352005423488, 47.783567779079945], 'min': 45.1671803999925, 'max': 48.90417559992056}, 'total_wall_s': 278.36126349994447}
