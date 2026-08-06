# Baseline Results — ECNetBench v1.1.0-INST

Task: device anomaly window classification (30-min), temporal 70/15/15 holdout.
Features: prior-bin CPU/mem, interface error/discard/carrier deltas, role one-hots.
Excluded: `incident_id`, `y_anomaly_score_gt`, free-text fields.

## Class imbalance

```json
{
  "temporal_train_prior": 0.010280478265728015,
  "temporal_val_prior": 0.010422094841063054,
  "temporal_test_prior": 0.008337675872850442
}
```

## Anomaly detection — temporal test

| Model | ROC-AUC | AP | F1 | Precision | Recall | Brier |
|---|---:|---:|---:|---:|---:|---:|
| majority | 0.5000 | 0.0083 | 0.0000 | 0.0000 | 0.0000 | 0.0083 |
| prior_random | 0.4916 | 0.0083 | 0.0000 | 0.0000 | 0.0000 | 0.0250 |
| logistic | 0.8642 | 0.1097 | 0.0529 | 0.0272 | 1.0000 | 0.1340 |
| random_forest | 0.9086 | 0.0493 | 0.0543 | 0.0279 | 1.0000 | 0.0383 |
| gradient_boosting | 0.8598 | 0.0290 | 0.0000 | 0.0000 | 0.0000 | 0.0410 |

## Cross-site (HQ→Branch)

Feasible: **True**

| Model | ROC-AUC | AP | F1 |
|---|---:|---:|---:|
| logistic | 0.6927 | 0.0166 | 0.0311 |
| random_forest | 0.6588 | 0.0125 | 0.0201 |

## Failure horizon (3600s)

| Model | ROC-AUC | AP | F1 |
|---|---:|---:|---:|
| majority | 0.5000 | 0.0052 | 0.0000 |
| logistic | 0.7761 | 0.0132 | 0.0196 |
| random_forest | 0.7777 | 0.0165 | 0.0169 |

## Difficulty assessment

```json
{
  "simple_model_near_perfect": false,
  "majority_nontrivial_gap": true,
  "stronger_beats_simple": false,
  "notes": []
}
```
