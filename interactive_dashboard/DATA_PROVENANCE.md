# Dashboard Data Provenance

All scientific values displayed in the interactive dashboard are loaded from verified repository artifacts. None are hard-coded in the frontend.

| Dashboard Element | Source File | Source Field | Transformation |
|---|---|---|---|
| `topology_v1.1.0-INST.json` | `benchmark/instances/v1/ecnetbench_v1.sqlite` | `device,interface,link,incident,telemetry tables` | SQL extract; telemetry capped at 2000–5000 rows; NaN→null |
| `metrics_v1.1.0-INST.json` | `results/per_seed/v1.1.0-INST.json` | `tasks.T1_anomaly / T2_failure / T3_rca` | Subset of AP/ROC/Brier/curves/CM/SHAP fields |
| `topology_seed101.json` | `benchmark/instances/v1.1-seed101/ecnetbench_v1.sqlite` | `device,interface,link,incident,telemetry tables` | SQL extract; telemetry capped at 2000–5000 rows; NaN→null |
| `metrics_seed101.json` | `results/per_seed/seed101.json` | `tasks.T1_anomaly / T2_failure / T3_rca` | Subset of AP/ROC/Brier/curves/CM/SHAP fields |
| `topology_seed202.json` | `benchmark/instances/v1.1-seed202/ecnetbench_v1.sqlite` | `device,interface,link,incident,telemetry tables` | SQL extract; telemetry capped at 2000–5000 rows; NaN→null |
| `metrics_seed202.json` | `results/per_seed/seed202.json` | `tasks.T1_anomaly / T2_failure / T3_rca` | Subset of AP/ROC/Brier/curves/CM/SHAP fields |
| `topology_seed303.json` | `benchmark/instances/v1.1-seed303/ecnetbench_v1.sqlite` | `device,interface,link,incident,telemetry tables` | SQL extract; telemetry capped at 2000–5000 rows; NaN→null |
| `metrics_seed303.json` | `results/per_seed/seed303.json` | `tasks.T1_anomaly / T2_failure / T3_rca` | Subset of AP/ROC/Brier/curves/CM/SHAP fields |
| `topology_seed404.json` | `benchmark/instances/v1.1-seed404/ecnetbench_v1.sqlite` | `device,interface,link,incident,telemetry tables` | SQL extract; telemetry capped at 2000–5000 rows; NaN→null |
| `metrics_seed404.json` | `results/per_seed/seed404.json` | `tasks.T1_anomaly / T2_failure / T3_rca` | Subset of AP/ROC/Brier/curves/CM/SHAP fields |
| `topology_seed505.json` | `benchmark/instances/v1.1-seed505/ecnetbench_v1.sqlite` | `device,interface,link,incident,telemetry tables` | SQL extract; telemetry capped at 2000–5000 rows; NaN→null |
| `metrics_seed505.json` | `results/per_seed/seed505.json` | `tasks.T1_anomaly / T2_failure / T3_rca` | Subset of AP/ROC/Brier/curves/CM/SHAP fields |
| `aggregate.json` | `results/manuscript_ready_numbers.json + results/aggregate_v3.json + results/v3_gated/*` | `multiple` | Merge authoritative final T1 with baseline aggregates; no fabricated metrics |
| `architecture.json` | `results/final_architecture.json` | `architecture_name,components,hybrid_recommendation` | Add module→source-code map for UI navigation |
| `index.json` | `benchmark/instances + results/per_seed` | `seed inventory` | Index only |

## Authoritative T1 numbers

- Final T1 AUPRC / ROC-AUC / twin gain: `results/manuscript_ready_numbers.json`
- Baseline aggregates: `results/aggregate_v3.json`
- Architecture selection A/B/C/D: `results/v3_gated/t1_architecture_selection.json`
- Per-seed curves / CM / calibration / SHAP (if present): `results/per_seed/*.json`
- Topology / incidents / telemetry: `benchmark/instances/*/ecnetbench_v1.sqlite`

## Labeling

The UI labels exploration as **historical benchmark replay**, not live network monitoring.

## Frontend UI element → JSON mapping

| Dashboard Element | Source File | Source Field | Transformation |
|---|---|---|---|
| Home / Results T1 AUPRC card | `public/data/aggregate.json` | `manuscript_ready.T1_final_proposed.auprc_mean` | Display `fmt()`; provenance → `results/manuscript_ready_numbers.json` |
| Home / Results T1 ROC-AUC | `public/data/aggregate.json` | `manuscript_ready.T1_final_proposed.roc_auc_mean` | Display only |
| Results T2 AUPRC | `public/data/aggregate.json` | `manuscript_ready.T2_recommended.auprc_mean` | Copied at build from `aggregate_v3` logistic__full |
| Models table rows | `public/data/aggregate.json` | `models[]` | Merge manuscript final + aggregate_v3 baselines |
| Topology node/link counts | `public/data/topology_<seed>.json` | `n_devices`, `n_links`, `devices`, `links` | SQLite extract |
| Topology inspector fields | `public/data/topology_<seed>.json` | device/link row keys | Show non-null fields only |
| Time slider | `public/data/topology_<seed>.json` | `time_range`, `telemetry_sample` | Distinct timestamps from sample |
| Seed ROC/PR/CM/calibration | `public/data/metrics_<seed>.json` | `T1`/`T2` curves + `curves.*` | From `results/per_seed` |
| TreeSHAP global bars | `public/data/metrics_<seed>.json` | `shap.top_features` | From T3 RCA block |
| Architecture modules | `public/data/architecture.json` | `modules`, `hybrid` | From `final_architecture.json` + code map |
| Seed selector options | `public/data/index.json` | `seeds[].id` | Inventory |
