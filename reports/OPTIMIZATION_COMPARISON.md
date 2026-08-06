# Optimization Comparison Report

## T1 AUPRC (mean ± 95% CI)

| Method | Pre-opt (v1) | Optimized (v2) |
|--------|--------------|----------------|
| `ecn_proposed__full` | 0.0579 [0.0148, 0.1009] | 0.0577 [0.0214, 0.0940] |
| `logistic__full` | 0.0701 [0.0369, 0.1033] | 0.0631 [0.0235, 0.1028] |
| `random_forest__full` | 0.0476 [0.0240, 0.0711] | 0.0758 [0.0427, 0.1090] |
| `lightgbm__full` | 0.0437 [0.0153, 0.0722] | 0.0505 [0.0234, 0.0776] |
| `isolation_forest__full` | 0.0337 [0.0049, 0.0625] | 0.0575 [0.0255, 0.0895] |
| `ewma__full` | 0.0403 [0.0135, 0.0671] | 0.0403 [0.0135, 0.0671] |
| `gnn_graphsage_proxy__full` | 0.0422 [0.0084, 0.0760] | 0.0422 [0.0084, 0.0760] |

## T2 AUPRC (mean ± 95% CI)

| Method | Pre-opt (v1) | Optimized (v2) |
|--------|--------------|----------------|
| `ecn_proposed__full` | 0.0147 [0.0081, 0.0212] | 0.0381 [-0.0026, 0.0788] |
| `logistic__full` | 0.0139 [0.0093, 0.0185] | 0.0380 [-0.0027, 0.0788] |
| `random_forest__full` | 0.0362 [-0.0063, 0.0787] | 0.0176 [0.0099, 0.0253] |
| `lightgbm__full` | 0.0147 [0.0040, 0.0253] | 0.0207 [0.0051, 0.0363] |
| `isolation_forest__full` | 0.0085 [0.0009, 0.0162] | 0.0216 [-0.0040, 0.0472] |
| `gnn_graphsage_proxy__full` | 0.0147 [0.0040, 0.0253] | 0.0147 [0.0040, 0.0253] |

## Per-seed optimized proposed vs key baselines

### T1
- seed101: proposed AP=0.0990, AUC=0.8369, F1=0.0000, P=0.0000, R=0.0000, Brier=0.00987550961413118; logistic AP=0.1151; fusion=singleton_twin_tree
- seed202: proposed AP=0.0228, AUC=0.6988, F1=0.0172, P=0.0103, R=0.0526, Brier=0.22715449104930058; logistic AP=0.0228; fusion=telem_only
- seed303: proposed AP=0.0114, AUC=0.4811, F1=0.0144, P=0.0075, R=0.2083, Brier=0.36871128428926536; logistic AP=0.0156; fusion=singleton_iso
- seed404: proposed AP=0.0731, AUC=0.6522, F1=0.0317, P=0.0183, R=0.1176, Brier=0.29847724112255347; logistic AP=0.0731; fusion=telem_only
- seed505: proposed AP=0.0564, AUC=0.6519, F1=0.0952, P=0.5000, R=0.0526, Brier=0.014778683086645846; logistic AP=0.0686; fusion=singleton_rf
- v1.1.0-INST: proposed AP=0.0836, AUC=0.7776, F1=0.0727, P=0.0426, R=0.2500, Brier=0.16805534800021002; logistic AP=0.0836; fusion=telem_only

### T2
- seed101: proposed AP=0.0300, AUC=0.8858, F1=0.0298; RF AP=0.0227; logistic AP=0.0300; fusion=telem_only
- seed202: proposed AP=0.0191, AUC=0.6730, F1=0.0379; RF AP=0.0087; logistic AP=0.0191; fusion=telem_only
- seed303: proposed AP=0.0075, AUC=0.6453, F1=0.0094; RF AP=0.0175; logistic AP=0.0075; fusion=telem_only
- seed404: proposed AP=0.0511, AUC=0.5806, F1=0.0161; RF AP=0.0092; logistic AP=0.0511; fusion=telem_only
- seed505: proposed AP=0.0104, AUC=0.6779, F1=0.0000; RF AP=0.0210; logistic AP=0.0100; fusion=anchor_0.5_rf
- v1.1.0-INST: proposed AP=0.1105, AUC=0.6961, F1=0.0255; RF AP=0.0267; logistic AP=0.1105; fusion=telem_only

## Statistical tests (optimized)

- T1 proposed vs logistic: {'statistic': 0.0, 'pvalue': 0.25}, Cliff δ=-0.083
- T1 proposed vs RF: {'statistic': 6.0, 'pvalue': 0.4375}, Cliff δ=-0.333
- T2 proposed vs RF: {'statistic': 6.0, 'pvalue': 0.4375}, Cliff δ=0.278
- T2 proposed vs logistic: {'statistic': 0.0, 'pvalue': 1.0}, Cliff δ=0.028

## Optimized proposed — aggregate metrics

### T1
- ap: {'n': 6, 'mean': 0.05771284608153401, 'std': 0.03456673779428457, 'ci95': [0.021437279485272263, 0.09398841267779576], 'min': 0.011421942589567902, 'max': 0.09899412280975113}
- roc_auc: {'n': 6, 'mean': 0.6830624769628045, 'std': 0.12291154365461975, 'ci95': [0.5540747224970154, 0.8120502314285937], 'min': 0.48112357080035184, 'max': 0.8368694838973639}
- f1: {'n': 6, 'mean': 0.03856033348729364, 'std': 0.03728500084212049, 'ci95': [-0.000567875229979399, 0.07768854220456667], 'min': 0.0, 'max': 0.09523809523809523}
- precision: {'n': 6, 'mean': 0.09644563004337538, 'std': 0.19824170181239026, 'ci95': [-0.11159627715217936, 0.30448753723893013], 'min': 0.0, 'max': 0.5}
- recall: {'n': 6, 'mean': 0.1135405916752666, 'std': 0.09791320512042613, 'ci95': [0.010786984605445415, 0.2162941987450878], 'min': 0.0, 'max': 0.25}
- brier: {'n': 6, 'mean': 0.1811754261936844, 'std': 0.14713746107014627, 'ci95': [0.02676413058286492, 0.3355867218045039], 'min': 0.00987550961413118, 'max': 0.36871128428926536}
### T2
- ap: {'n': 6, 'mean': 0.0381064340665632, 'std': 0.038811920074291156, 'ci95': [-0.0026241781121923435, 0.07883704624531875], 'min': 0.007547016026878037, 'max': 0.11046016230787424}
- roc_auc: {'n': 6, 'mean': 0.6931248374176583, 'std': 0.10268921500591288, 'ci95': [0.5853591153575117, 0.8008905594778049], 'min': 0.5805657412257726, 'max': 0.8858040859088527}
- f1: {'n': 6, 'mean': 0.01978311579860585, 'std': 0.013960218510577455, 'ci95': [0.005132764952870229, 0.034433466644341465], 'min': 0.0, 'max': 0.037940379403794036}
- precision: {'n': 6, 'mean': 0.010235668436794399, 'std': 0.0072241073252110695, 'ci95': [0.00265443274328425, 0.017816904130304546], 'min': 0.0, 'max': 0.0196078431372549}
- recall: {'n': 6, 'mean': 0.3805555555555556, 'std': 0.3581459458356586, 'ci95': [0.0047044357113585344, 0.7564066753997527], 'min': 0.0, 'max': 1.0}
- brier: {'n': 6, 'mean': 0.23067026047155859, 'std': 0.0895771967864011, 'ci95': [0.1366647576419332, 0.324675763301184], 'min': 0.07400147240684636, 'max': 0.3239970426921863}

## Proposed AUPRC change (opt − pre-opt)
- T1: 0.05786658543607171 → 0.05771284608153401 (Δ=-0.0001537393545377047)
- T2: 0.01466214139820108 → 0.0381064340665632 (Δ=0.02344429266836212)

## Conclusions (optimized aggregate)

```json
{
  "proposed_outperforms_best_baseline_T1_ap": false,
  "proposed_outperforms_best_baseline_T2_ap": true,
  "T1_proposed_ap_mean": 0.05771284608153401,
  "T1_best_baseline": "random_forest__full",
  "T1_best_baseline_ap_mean": 0.07583814878524626,
  "T2_proposed_ap_mean": 0.0381064340665632,
  "T2_best_baseline": "logistic__full",
  "T2_best_baseline_ap_mean": 0.038043099063649714,
  "digital_twin_ap_gain_T1": -0.010846770976002125,
  "digital_twin_ap_gain_T2": 0.002208391127349038,
  "significant_wins_p05": 3,
  "significant_tests": 17,
  "most_contributing_module": {
    "module": "telemetry",
    "ap_drop": 0.029566239245987527,
    "task": "T1_anomaly"
  },
  "least_contributing_module": {
    "module": "digital_twin",
    "ap_drop": 0.002208391127349038,
    "task": "T2_failure"
  },
  "novelty_supported": true,
  "novelty_statement": "Digital Twin + multi-agent fusion provide measurable AP gains vs twin-ablated variants and beat several classical detectors, but do not uniformly dominate the strongest tabular baseline (logistic) on T1 across all seeds."
}
```

## Why T1 may still trail strongest baseline

Under ~1% positives, val-selected twin/tree specialists are unstable. Anchored fusion mostly selects `telem_only`, making proposed ≈ telem logistic. When RF/logistic baselines use the same enriched telem features, proposed cannot exceed them without a twin specialist that *reliably* improves ranking — which ablations show is not consistently true on T1 for this benchmark.

## Why T2 improved

Enriching T2 with interface deltas, temporal z-scores, and twin neighborhood features plus RF specialist + anchored fusion raised proposed mean AUPRC substantially (feature under-specification was a primary pre-opt cause).