# Benchmark Tasks — ECNetBench v1.1.0-INST

Fixed protocols. Use manifests under `manifests/`.

## Task T1 — Anomaly window detection

- **Input:** Features from telemetry **strictly before** `t_start` (use prior 30-min bin).
- **Label:** `label_anomaly_window.y_anomaly`.
- **Split:** `manifests/temporal_{train,val,test}.csv`.
- **Forbidden features:** `incident_id`, `y_anomaly_score_gt`, any future telemetry, alert.`correlated_incident_id`.
- **Metrics:** Average Precision (primary), ROC-AUC, F1 at val-tuned threshold, Brier score.

## Task T2 — Failure horizon prediction

- **Input:** Telemetry before `t0`.
- **Label:** `label_failure_horizon.y_fail` for horizons {300,900,1800,3600}s.
- **Split:** Temporal by `t0` using same freeze fractions as T1.
- **Metrics:** AP, ROC-AUC per horizon.

## Task T3 — Root-cause category (RCA)

- **Input:** Telemetry + graph neighborhood around `t_detect` (±30 min), **no** `description`/`category`/`subcategory` text.
- **Label:** `label_rca.y_category` / `y_root_entity_id`.
- **Metrics:** Macro-F1 (category), Hit@k for root entity.

## Task T4 — Service impact

- **Input:** Incident context without `service_impact` table targets.
- **Label:** `label_impact` fields.
- **Metrics:** F1 for SLA breach; MAE for users_affected / downtime.

## Task T5 — Degradation forecast

- **Input:** Service KPIs before `t0`.
- **Label:** `label_degradation.y_degrade`.
- **Metrics:** AP; require reporting link-aware evaluation if using `linked_incident_id` only as GT metadata.

## Task T6 — Cross-site generalization

- **Train:** `topology_train_hq.csv` **Test:** `topology_test_branch.csv`.
- **Metrics:** Same as T1; report prior shift.

## Reporting card (required)

1. Feature list + exclusions
2. Split manifest hashes
3. Seed / code commit
4. AP + ROC-AUC + calibration
5. Ablation table
