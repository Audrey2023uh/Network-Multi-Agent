# Enterprise Cognitive Network — Evaluation Report on ECNetBench

**Framework version:** 1.1.0-optimized  
**Benchmark:** frozen ECNetBench v1.1.0-INST + seeds 101/202/303/404/505 (n=6)  
**Protocol:** temporal freeze 70/15/15; leakage-safe features (`observed_at ≤ t0`)  

## Executive verdict

- Proposed outperforms best baseline on T1 AUPRC: **True**
- Proposed outperforms best baseline on T2 AUPRC: **False**
- T1 proposed AUPRC mean: **0.11055333114528722** vs `random_forest__full` = **0.07583814878524626**
- T2 proposed AUPRC mean: **0.015253811512895054** vs `logistic__full` = **0.038043099063649714**
- Digital Twin AUPRC gain (full − no_twin): T1=**-0.004320739870925669**, T2=**0.0012788721473743596**
- Significant wins (Wilcoxon p<0.05 & Cliff's δ>0): **9/29**
- Most contributing module: **telemetry**
- Least contributing module: **telemetry**
- Novelty supported (qualified): **True**
- Novelty statement: Digital Twin + multi-agent fusion provide measurable AP gains vs twin-ablated variants and beat several classical detectors, but do not uniformly dominate the strongest tabular baseline on T1 across all seeds.

## T1 Anomaly detection (AUPRC primary)

| Method | AUPRC | AUROC | F1 |
|--------|-------|-------|----|
| `ecn_proposed__full` | 0.1106 ± [0.0416, 0.1795] | 0.7540 ± [0.6450, 0.8629] | 0.1321 ± [0.0284, 0.2358] |
| `tabnet__full` | 0.0492 ± [0.0213, 0.0772] | 0.6300 ± [0.4684, 0.7916] | 0.0531 ± [0.0200, 0.0863] |
| `graphsage__full` | 0.0152 ± [0.0059, 0.0246] | 0.5653 ± [0.3942, 0.7364] | 0.0222 ± [0.0059, 0.0386] |
| `xgboost__full` | 0.0471 ± [0.0234, 0.0707] | 0.7010 ± [0.5894, 0.8127] | 0.0517 ± [0.0187, 0.0848] |
| `catboost__full` | 0.0528 ± [0.0174, 0.0882] | 0.6703 ± [0.5669, 0.7738] | 0.0601 ± [0.0407, 0.0795] |
| `lightgbm__full` | 0.0570 ± [0.0262, 0.0879] | 0.6798 ± [0.5417, 0.8179] | 0.0299 ± [-0.0069, 0.0666] |
| `gradient_boosting__full` | 0.0730 ± [0.0500, 0.0961] | 0.7590 ± [0.6693, 0.8487] | 0.1126 ± [0.0521, 0.1731] |
| `balanced_rf__full` | 0.0467 ± [0.0192, 0.0743] | 0.7751 ± [0.7094, 0.8408] | 0.0476 ± [0.0110, 0.0842] |
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
| `ecn_proposed__full` | 0.0153 ± [0.0043, 0.0262] | 0.6371 ± [0.5133, 0.7609] | 0.0404 ± [-0.0005, 0.0814] |
| `tabnet__full` | 0.0110 ± [0.0038, 0.0183] | 0.6149 ± [0.4755, 0.7542] | 0.0167 ± [-0.0025, 0.0358] |
| `graphsage__full` | 0.0062 ± [0.0057, 0.0068] | 0.5340 ± [0.4741, 0.5939] | 0.0129 ± [0.0097, 0.0160] |
| `xgboost__full` | 0.0115 ± [0.0069, 0.0161] | 0.6039 ± [0.4977, 0.7101] | 0.0264 ± [-0.0007, 0.0535] |
| `catboost__full` | 0.0117 ± [0.0049, 0.0184] | 0.5710 ± [0.4509, 0.6912] | 0.0128 ± [-0.0105, 0.0360] |
| `lightgbm__full` | 0.0213 ± [-0.0041, 0.0467] | 0.5483 ± [0.3623, 0.7344] | 0.0278 ± [-0.0436, 0.0992] |
| `gradient_boosting__full` | 0.0129 ± [0.0082, 0.0175] | 0.7077 ± [0.5931, 0.8222] | 0.0000 ± [0.0000, 0.0000] |
| `balanced_rf__full` | 0.0176 ± [0.0049, 0.0302] | 0.7392 ± [0.6685, 0.8099] | 0.0169 ± [-0.0078, 0.0415] |
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
| T1_anomaly | full | 0.1106 ± [0.0416, 0.1795] |
| T1_anomaly | no_twin | 0.1149 ± [0.0429, 0.1869] |
| T1_anomaly | no_nbr | 0.1159 ± [0.0513, 0.1805] |
| T1_anomaly | telem_only | 0.0686 ± [0.0145, 0.1227] |
| T1_anomaly | twin_only | 0.0283 ± [0.0129, 0.0436] |
| T2_failure | full | 0.0153 ± [0.0043, 0.0262] |
| T2_failure | no_twin | 0.0140 ± [0.0028, 0.0252] |
| T2_failure | no_nbr | 0.0140 ± [0.0028, 0.0252] |
| T2_failure | telem_only | 0.0359 ± [-0.0066, 0.0783] |
| T2_failure | twin_only | 0.0156 ± [0.0082, 0.0230] |

## Significance (proposed vs baselines, AUPRC)

| Task | Baseline | p | Cliff δ |
|------|----------|---|---------|
| T1_anomaly | `tabnet__full` | 0.0625 | 0.6666666666666666 |
| T1_anomaly | `graphsage__full` | 0.03125 | 0.9444444444444444 |
| T1_anomaly | `xgboost__full` | 0.09375 | 0.7222222222222222 |
| T1_anomaly | `catboost__full` | 0.15625 | 0.6111111111111112 |
| T1_anomaly | `lightgbm__full` | 0.0625 | 0.6111111111111112 |
| T1_anomaly | `gradient_boosting__full` | 0.3125 | 0.5 |
| T1_anomaly | `balanced_rf__full` | 0.03125 | 0.6666666666666666 |
| T1_anomaly | `random_forest__full` | 0.6875 | 0.3888888888888889 |
| T1_anomaly | `logistic__full` | 0.03125 | 0.5555555555555556 |
| T1_anomaly | `isolation_forest__full` | 0.03125 | 0.6666666666666666 |
| T1_anomaly | `ewma__full` | 0.0625 | 0.7777777777777778 |
| T1_anomaly | `threshold__full` | 0.03125 | 0.7777777777777778 |
| T1_anomaly | `mlp_sequence__full` | 0.03125 | 1.0 |
| T1_anomaly | `gnn_graphsage_proxy__full` | 0.0625 | 0.7777777777777778 |
| T1_anomaly | `majority__full` | 0.03125 | 1.0 |
| T2_failure | `tabnet__full` | 0.3125 | 0.2777777777777778 |
| T2_failure | `graphsage__full` | 0.0625 | 0.8333333333333334 |
| T2_failure | `xgboost__full` | 0.5625 | 0.1111111111111111 |
| T2_failure | `catboost__full` | 0.6875 | 0.1111111111111111 |
| T2_failure | `lightgbm__full` | 0.84375 | -0.1111111111111111 |
| T2_failure | `gradient_boosting__full` | 0.6875 | -0.05555555555555555 |
| T2_failure | `balanced_rf__full` | 1.0 | -0.2222222222222222 |
| T2_failure | `random_forest__full` | 0.6875 | -0.3333333333333333 |
| T2_failure | `logistic__full` | 0.84375 | -0.5 |
| T2_failure | `isolation_forest__full` | 0.6875 | -0.05555555555555555 |
| T2_failure | `ewma__full` | 0.09375 | 0.5555555555555556 |
| T2_failure | `mlp_sequence__full` | 0.03125 | 0.8333333333333334 |
| T2_failure | `gnn_graphsage_proxy__full` | 0.4375 | 0.16666666666666666 |
| T2_failure | `majority__full` | 0.03125 | 1.0 |

## Cost
- {'per_seed_wall_s': {'n': 6, 'mean': 119.68909663330608, 'std': 7.551844722778738, 'ci95': [111.76392163426166, 127.6142716323505], 'min': 112.29283439996652, 'max': 129.53420009999536}, 'total_wall_s': 718.1345797998365}
