# Leakage Report — ECNetBench v1.1.0-INST

Independent evaluation. Instance frozen (read-only).

## Protocol requirements

- Exclude incident_id, y_anomaly_score_gt, category, subcategory, description from model features
- Use temporal split manifests under manifests/
- RCA evaluation must use telemetry/graph only — not free-text description

## Findings

### [PASS] `label_fields_excluded_from_honest_features` (info)

honest_features=['role_access', 'role_aggregation', 'role_ap', 'role_core', 'role_wan_edge', 'cpu_mean', 'cpu_max', 'mem_mean', 'err_sum', 'disc_sum', 'car_sum', 'n_samples']; leak_probe_features include incident_id indicator and y_score

### [PASS] `window_id_label_correlation` (info)

corr(first_hex_nibble,y)=0.0043

### [PASS] `incident_id_is_label_proxy` (critical)

incident_id present in 100% of positives and 0% of negatives — this field is a near-perfect label proxy and is excluded from honest feature sets

### [PASS] `y_anomaly_score_gt_is_oracle` (critical)

AUC(y_anomaly_score_gt→y)=1.0000; oracle field — exclude from features

### [FAIL] `incident_description_encodes_category` (high)

37/37 descriptions contain category token — RCA from description is trivial; use telemetry-only RCA protocol

### [PASS] `window_id_split_overlap` (critical)

window_id overlap train∩test=0

### [PASS] `timestamp_only_predictability` (info)

AUC using hour-of-week empirical prior=0.838 (high ⇒ schedule leakage / too regular injection)

### [PASS] `leaky_vs_honest_gap` (critical)

temporal-test ROC-AUC honest={'roc_auc': 0.8813058328954282, 'ap': 0.11733532750827967} leaky={'roc_auc': 1.0, 'ap': 1.0}
