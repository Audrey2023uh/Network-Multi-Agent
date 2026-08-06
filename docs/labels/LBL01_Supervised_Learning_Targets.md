# LBL01 — Supervised Learning Targets

Labels are **derived from incidents, KPIs, and config diffs** with frozen rules. Methods may not redefine GT; they may only choose which label tables to train on.

---

## 1. Task T1 — Anomaly detection

### Table `label_anomaly_window`

| Attribute | Type | Meaning |
|-----------|------|---------|
| `window_id` | UUID | |
| `topology_snapshot_id` | UUID | Graph/context |
| `entity_type`,`entity_id` | | Device or interface primarily |
| `t_start`,`t_end` | TIMESTAMPTZ | Window |
| `y_anomaly` | BOOLEAN | 1 if overlaps any incident symptomatic/root entity |
| `y_anomaly_score_gt` | REAL | Optional severity prior 0–1 |
| `incident_id` | UUID NULL | If anomalous |
| `point_adjust` | BOOLEAN | For point-adjust eval protocols |

**Positive rule:** window overlaps `[onset_at, recovered_at]` for linked entity (or detection→recovery if studying detectability).  
**Negative rule:** outside all incidents + outside maintenance unless labeled separately.

**Metrics:** AUROC, AUPRC, F1@best, event-level F1, detection delay.

---

## 2. Task T2 — Failure prediction

### Table `label_failure_horizon`

| Attribute | Type | Meaning |
|-----------|------|---------|
| `sample_id` | UUID | |
| `entity_type`,`entity_id` | | |
| `t0` | TIMESTAMPTZ | Prediction time |
| `horizon_s` | INT | H |
| `y_fail` | BOOLEAN | Incident onset in `(t0, t0+H]` |
| `y_category` | ENUM NULL | If fail, category |
| `y_severity` | ENUM NULL | |
| `lead_time_s` | REAL NULL | `onset_at - t0` when positive |

**Features:** only `observed_at ≤ t0`.  
**Horizons published:** {5,15,30,60} minutes.  
**Metrics:** AUPRC (imbalanced), recall@precision=0.8, lead-time distribution, ECE calibration.

---

## 3. Task T3 — Root cause analysis

### Table `label_rca`

| Attribute | Type | Meaning |
|-----------|------|---------|
| `rca_id` | UUID | |
| `incident_id` | UUID | |
| `t_detect` | TIMESTAMPTZ | Usually `detected_at` |
| `y_category` | ENUM | Cause family |
| `y_subcategory` | TEXT | |
| `y_root_entity_type` | TEXT | |
| `y_root_entity_id` | UUID | Localization |
| `y_trigger_type` | ENUM | spontaneous/change/... |
| `candidate_entity_set` | UUID[] | Optional distractors for ranking |
| `hidden_target` | BOOLEAN | Root not directly monitored (ClosRCA-style) |

**Input at inference:** alerts/syslog/telemetry/graph **without** root fields.  
**Metrics:** cause accuracy/macro-F1; top-k localization accuracy; hidden-target slice; explanation faithfulness if XAI (entity overlap with `incident_entity`).

---

## 4. Task T4 — Impact prediction

### Table `label_impact`

| Attribute | Type | Meaning |
|-----------|------|---------|
| `impact_label_id` | UUID | |
| `incident_id` | UUID | |
| `t0` | TIMESTAMPTZ | Early after onset/detection |
| `y_services` | UUID[] | Services impacted within W |
| `y_max_severity` | ENUM | |
| `y_users_affected` | INT | |
| `y_downtime_s` | REAL | |
| `y_sla_breach` | BOOLEAN | |
| `blast_radius_nodes` | INT | Count devices symptomatic |

**Metrics:** set-F1 on services; severity QWK; downtime MAE/sMAPE; SLA F1.

---

## 5. Task T5 — Service degradation prediction

### Table `label_degradation`

| Attribute | Type | Meaning |
|-----------|------|---------|
| `deg_id` | UUID | |
| `service_id` | UUID | |
| `t0` | TIMESTAMPTZ | |
| `horizon_s` | INT | |
| `y_degrade` | BOOLEAN | KPI breach vs SLA in horizon |
| `y_metric` | ENUM | latency/loss/availability |
| `y_breach_value` | REAL | |
| `linked_incident_id` | UUID NULL | If attributable |

**Metrics:** AUPRC; multi-service macro; cost-weighted by `criticality_tier`.

---

## 6. Task T6 — Configuration risk prediction

### Table `label_config_risk`

| Attribute | Type | Meaning |
|-----------|------|---------|
| `risk_id` | UUID | |
| `diff_id` | UUID | `config_object_diff` |
| `after_snapshot_id` | UUID | |
| `t_change` | TIMESTAMPTZ | |
| `y_risk` | BOOLEAN | Incident with `change_induced` in (t_change, t_change+H_risk] |
| `y_risk_score` | REAL | 0–1 GT severity prior |
| `y_category` | ENUM NULL | Resulting failure category |
| `horizon_s` | INT | Default 24h |

**Metrics:** AUPRC; precision@top-k changes/day (operator workload); calibration.

---

## 7. Auxiliary targets (optional but valuable)

| Target | Table | Use |
|--------|-------|-----|
| Recovery success classification | from `recovery_action` | autonomous management |
| Recovery duration regression | `duration_s` | planning |
| Detection latency regression | `detection_latency_s` | sensor placement |
| Alert FP classification | `alert.is_false_positive_gt` | NOC noise reduction |
| Next-step action recommendation | ranked `action_type` | imitation learning |

---

## 8. Label quality controls

1. Dual annotation rule for ambiguous incidents (generator oracle + rule validator).  
2. Inter-rater agreement when human labels added.  
3. Publish label version `label_schema_version`.  
4. Never train on test topology profiles for cross-topology track.
