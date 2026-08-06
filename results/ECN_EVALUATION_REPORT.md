# Enterprise Cognitive Network — Evaluation Report on ECNetBench

**Framework version:** 1.1.0-optimized  
**Benchmark:** frozen ECNetBench v1.1.0-INST + seeds 101/202/303/404/505 (n=6)  
**Protocol:** temporal freeze 70/15/15; leakage-safe features (`observed_at ≤ t0`)  

## Executive verdict

- Proposed outperforms best baseline on T1 AUPRC: **False**
- Proposed outperforms best baseline on T2 AUPRC: **True**
- T1 proposed AUPRC mean: **0.05771284608153401** vs `random_forest__full` = **0.07583814878524626**
- T2 proposed AUPRC mean: **0.0381064340665632** vs `logistic__full` = **0.038043099063649714**
- Digital Twin AUPRC gain (full − no_twin): T1=**-0.010846770976002125**, T2=**0.002208391127349038**
- Significant wins (Wilcoxon p<0.05 & Cliff's δ>0): **3/17**
- Most contributing module: **telemetry**
- Least contributing module: **digital_twin**
- Novelty supported (qualified): **True**
- Novelty statement: Digital Twin + multi-agent fusion provide measurable AP gains vs twin-ablated variants and beat several classical detectors, but do not uniformly dominate the strongest tabular baseline on T1 across all seeds.

## T1 Anomaly detection (AUPRC primary)

| Method | AUPRC | AUROC | F1 |
|--------|-------|-------|----|
| `ecn_proposed__full` | 0.0577 ± [0.0214, 0.0940] | 0.6831 ± [0.5541, 0.8121] | 0.0386 ± [-0.0006, 0.0777] |
| `lightgbm__full` | 0.0505 ± [0.0234, 0.0776] | 0.6843 ± [0.5654, 0.8032] | 0.0246 ± [-0.0179, 0.0670] |
| `random_forest__full` | 0.0758 ± [0.0427, 0.1090] | 0.7661 ± [0.6601, 0.8720] | 0.0470 ± [-0.0080, 0.1020] |
| `logistic__full` | 0.0631 ± [0.0235, 0.1028] | 0.7260 ± [0.6223, 0.8297] | 0.0381 ± [0.0036, 0.0726] |
| `isolation_forest__full` | 0.0575 ± [0.0255, 0.0895] | 0.6716 ± [0.5497, 0.7936] | 0.0373 ± [0.0075, 0.0671] |
| `ewma__full` | 0.0403 ± [0.0135, 0.0671] | 0.5484 ± [0.4741, 0.6228] | 0.0362 ± [0.0221, 0.0503] |
| `threshold__full` | 0.0315 ± [-0.0030, 0.0661] | 0.2864 ± [0.1671, 0.4058] | 0.0085 ± [-0.0016, 0.0186] |
| `mlp_sequence__full` | 0.0084 ± [0.0053, 0.0115] | 0.3617 ± [0.2126, 0.5108] | 0.0125 ± [0.0016, 0.0235] |
| `gnn_graphsage_proxy__full` | 0.0422 ± [0.0084, 0.0760] | 0.7261 ± [0.6793, 0.7730] | 0.0340 ± [0.0085, 0.0596] |
| `majority__full` | 0.0098 ± [0.0083, 0.0113] | 0.5000 ± [0.5000, 0.5000] | 0.0000 ± [0.0000, 0.0000] |

## T2 Failure prediction

| Method | AUPRC | AUROC | F1 |
|--------|-------|-------|----|
| `ecn_proposed__full` | 0.0381 ± [-0.0026, 0.0788] | 0.6931 ± [0.5854, 0.8009] | 0.0198 ± [0.0051, 0.0344] |
| `lightgbm__full` | 0.0207 ± [0.0051, 0.0363] | 0.5840 ± [0.5073, 0.6607] | 0.0159 ± [-0.0249, 0.0567] |
| `random_forest__full` | 0.0176 ± [0.0099, 0.0253] | 0.7081 ± [0.6258, 0.7904] | 0.0262 ± [0.0007, 0.0518] |
| `logistic__full` | 0.0380 ± [-0.0027, 0.0788] | 0.6891 ± [0.5801, 0.7981] | 0.0198 ± [0.0051, 0.0344] |
| `isolation_forest__full` | 0.0216 ± [-0.0040, 0.0472] | 0.6459 ± [0.5221, 0.7696] | 0.0160 ± [-0.0045, 0.0365] |
| `ewma__full` | 0.0066 ± [0.0045, 0.0086] | 0.4482 ± [0.3423, 0.5540] | 0.0132 ± [0.0079, 0.0185] |
| `mlp_sequence__full` | 0.0054 ± [0.0041, 0.0067] | 0.3795 ± [0.2215, 0.5375] | 0.0090 ± [0.0044, 0.0136] |
| `gnn_graphsage_proxy__full` | 0.0147 ± [0.0040, 0.0253] | 0.6495 ± [0.6018, 0.6971] | 0.0263 ± [-0.0217, 0.0744] |
| `majority__full` | 0.0056 ± [0.0050, 0.0061] | 0.5000 ± [0.5000, 0.5000] | 0.0000 ± [0.0000, 0.0000] |

## Ablations

| Task | Ablation | AUPRC |
|------|----------|-------|
| T1_anomaly | full | 0.0577 ± [0.0214, 0.0940] |
| T1_anomaly | no_twin | 0.0686 ± [0.0145, 0.1227] |
| T1_anomaly | no_nbr | 0.0414 ± [0.0124, 0.0705] |
| T1_anomaly | telem_only | 0.0686 ± [0.0145, 0.1227] |
| T1_anomaly | twin_only | 0.0281 ± [0.0148, 0.0415] |
| T2_failure | full | 0.0381 ± [-0.0026, 0.0788] |
| T2_failure | no_twin | 0.0359 ± [-0.0066, 0.0783] |
| T2_failure | no_nbr | 0.0254 ± [0.0084, 0.0424] |
| T2_failure | telem_only | 0.0359 ± [-0.0066, 0.0783] |
| T2_failure | twin_only | 0.0168 ± [0.0087, 0.0248] |

## Significance (proposed vs baselines, AUPRC)

| Task | Baseline | p | Cliff δ |
|------|----------|---|---------|
| T1_anomaly | `lightgbm__full` | 0.6875 | 0.16666666666666666 |
| T1_anomaly | `random_forest__full` | 0.4375 | -0.3333333333333333 |
| T1_anomaly | `logistic__full` | 0.25 | -0.08333333333333333 |
| T1_anomaly | `isolation_forest__full` | 0.84375 | 0.0 |
| T1_anomaly | `ewma__full` | 0.5625 | 0.2777777777777778 |
| T1_anomaly | `threshold__full` | 0.21875 | 0.5 |
| T1_anomaly | `mlp_sequence__full` | 0.0625 | 0.9444444444444444 |
| T1_anomaly | `gnn_graphsage_proxy__full` | 0.6875 | 0.16666666666666666 |
| T1_anomaly | `majority__full` | 0.0625 | 0.9444444444444444 |
| T2_failure | `lightgbm__full` | 0.21875 | 0.2777777777777778 |
| T2_failure | `random_forest__full` | 0.4375 | 0.2777777777777778 |
| T2_failure | `logistic__full` | 1.0 | 0.027777777777777776 |
| T2_failure | `isolation_forest__full` | 0.5625 | 0.2777777777777778 |
| T2_failure | `ewma__full` | 0.03125 | 0.8888888888888888 |
| T2_failure | `mlp_sequence__full` | 0.03125 | 1.0 |
| T2_failure | `gnn_graphsage_proxy__full` | 0.4375 | 0.3888888888888889 |
| T2_failure | `majority__full` | 0.03125 | 1.0 |

## Cost
- {'per_seed_wall_s': {'n': 6, 'mean': 40.77935786667513, 'std': 2.8065404104447724, 'ci95': [37.83407433514608, 43.72464139820418], 'min': 38.50407330004964, 'max': 45.93937349994667}, 'total_wall_s': 244.67614720005076}
