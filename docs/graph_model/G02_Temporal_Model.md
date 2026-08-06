# G02 — Temporal Model

## 1. Time axioms

1. All stored timestamps are **UTC** `TIMESTAMPTZ`.  
2. Every observational fact has `observed_at` (entity time) and optionally `ingested_at` (collector time).  
3. Inventory/config use **bi-temporal validity** (`valid_from`, `valid_to`) plus snapshot times.  
4. Incident timeline must satisfy:

```
onset_at ≤ detected_at ≤ recovery_started_at ≤ recovery_ended_at
```
(with NULLs allowed only for undetected or unrecovered cases, explicitly flagged).

5. No future leakage: features at prediction time `t0` may use data with `observed_at ≤ t0` only.

---

## 2. Cadences

| Stream | Cadence | Alignment |
|--------|---------|-----------|
| Interface counters | 60 s | floor to minute |
| Device resources | 60 s | |
| Env/power | 60–300 s | |
| NAE | per agent (5–60 s) | |
| Syslog/alerts | event-time | |
| IPFIX | export timer / flow end | |
| Service KPI | 60–300 s | |
| Config snapshot | 15–60 min + on change | |
| Topology snapshot | 5–15 min + on link event | |
| Graph materialization | 60–300 s | |

---

## 3. Windows for ML

| Window | Definition | Use |
|--------|------------|-----|
| `W_obs` | `[t0 - L, t0]` | feature history length L (e.g., 30–120 min) |
| `W_pred` | `(t0, t0 + H]` | prediction horizon H (e.g., 5–60 min) |
| `W_incident` | `[onset, recovery_end]` | supervision span |
| `W_impact` | incident ∩ service KPI | degradation labels |
| `W_change` | `[pre_snapshot, post_snapshot]` | config risk |

Published benchmark must fix default `(L, H)` per task but allow ablation.

---

## 4. Clock skew and missingness

Tables support:

- `received_at - observed_at` skew modeling for syslog  
- Explicit missing samples (do not impute in GT storage; imputation is a method choice)  
- Counter resets via `last_clear_at` / negative diffs flagged invalid

---

## 5. Diurnal and calendar structure

Future generators must preserve:

- Business-hour traffic vs night backup  
- Change windows (e.g., Fri 22:00 local) correlating with config snapshots  
- Maintenance schedules in `maintenance_window(site_id, start_at, end_at, ticket_id)`

`maintenance_window` table:

| Attribute | Type | Why |
|-----------|------|-----|
| `maint_id` | UUID | |
| `site_id` | UUID | |
| `start_at`,`end_at` | TIMESTAMPTZ | |
| `expected_impact` | TEXT | |
| `suppress_alerts` | BOOLEAN | alert FP research |

---

## 6. Temporal validation (preview; full in B01)

- **Freeze-time split:** train `< T_freeze`, val `[T_freeze, T_test)`, test `≥ T_test`  
- **Rolling-origin:** multiple origins with embargo gap `g` to avoid autocorrelation leak  
- **Incident-aware:** ensure entire incident windows do not straddle train/test unless explicitly studying early detection
