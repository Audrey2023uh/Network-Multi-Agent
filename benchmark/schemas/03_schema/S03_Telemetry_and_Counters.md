# S03 — Telemetry and Counters

All samples include `observed_at TIMESTAMPTZ NOT NULL`. Cadences defined in `G02_Temporal_Model.md`.

---

## 1. `if_counter_sample`

Aligned with OpenConfig `interfaces/interface/state/counters` and IF-MIB conceptual counters.

| Attribute | Type | Null | Src | Scientific / networking / ML motivation |
|-----------|------|------|-----|----------------------------------------|
| `sample_id` | UUID PK | N | | Unique observation |
| `interface_id` | UUID FK | N | | Entity key for XAI |
| `device_id` | UUID FK | N | denorm | Partitioning |
| `observed_at` | TIMESTAMPTZ | N | | Time series |
| `in_octets` | BIGINT | N | OC counters | Traffic volume; congestion precursors |
| `out_octets` | BIGINT | N | | |
| `in_unicast_pkts` | BIGINT | Y | | |
| `out_unicast_pkts` | BIGINT | Y | | |
| `in_broadcast_pkts` | BIGINT | Y | | Storm / loop signals |
| `out_broadcast_pkts` | BIGINT | Y | | |
| `in_multicast_pkts` | BIGINT | Y | | |
| `out_multicast_pkts` | BIGINT | Y | | |
| `in_discards` | BIGINT | Y | | Congestion / ACL / policy drops |
| `out_discards` | BIGINT | Y | | |
| `in_errors` | BIGINT | Y | | Cable/PHY degradation |
| `out_errors` | BIGINT | Y | | |
| `in_fcs_errors` | BIGINT | Y | Ethernet | Physical layer faults |
| `in_unknown_protos` | BIGINT | Y | | |
| `carrier_transitions` | BIGINT | Y | OC | Flapping / intermittent failures |
| `last_clear_at` | TIMESTAMPTZ | Y | | Counter reset awareness |

**Derived features (views, not stored raw unless needed):** utilization, error rate, discard rate, flap rate — computed with monotonic-counter diffs.

**Why not invent exotic counters:** stick to OC/IF-MIB so independent researchers accept realism.

---

## 2. `device_resource_sample`

| Attribute | Type | Null | Src | Motivation |
|-----------|------|------|-----|------------|
| `sample_id` | UUID PK | N | | |
| `device_id` | UUID FK | N | | |
| `observed_at` | TIMESTAMPTZ | N | | |
| `cpu_util_pct` | REAL | N | OC system CPU / AOS-CX | Control-plane stress; STP/BGP storms |
| `cpu_util_user_pct` | REAL | Y | | |
| `cpu_util_system_pct` | REAL | Y | | |
| `mem_used_bytes` | BIGINT | N | OC memory | Memory leak / table exhaustion |
| `mem_total_bytes` | BIGINT | N | | |
| `mem_util_pct` | REAL | N | derived OK | |
| `process_count` | INT | Y | | |
| `control_plane_drop_pct` | REAL | Y | platform if available | |

**ML:** failure prediction (CPU spikes before BGP collapse); anomaly detection baselines.

---

## 3. `env_sensor_sample`

| Attribute | Type | Null | Src | Motivation |
|-----------|------|------|-----|------------|
| `sample_id` | UUID PK | N | | |
| `device_id` | UUID FK | N | | |
| `component_id` | UUID FK | Y | ENTITY-SENSOR / OC | |
| `observed_at` | TIMESTAMPTZ | N | | |
| `sensor_type` | ENUM(`temperature`,`fan_rpm`,`optical_tx_power`,`optical_rx_power`,`optical_temp`,`voltage`) | N | DOM/optics | |
| `value` | REAL | N | | |
| `unit` | TEXT | N | `C`,`rpm`,`dBm`,`V` | |
| `threshold_warning` | REAL | Y | | Supervised threshold exceedance |
| `threshold_critical` | REAL | Y | | |
| `status` | ENUM(`ok`,`warn`,`crit`) | N | | |

**Failure families:** hardware degradation, optics aging, thermal throttling, cable/optic faults.

---

## 4. `power_sample`

| Attribute | Type | Null | Src | Motivation |
|-----------|------|------|-----|------------|
| `sample_id` | UUID PK | N | | |
| `device_id` | UUID FK | N | | |
| `component_id` | UUID FK | Y | PSU | |
| `observed_at` | TIMESTAMPTZ | N | | |
| `input_power_w` | REAL | Y | | |
| `output_power_w` | REAL | Y | | |
| `psu_status` | ENUM(`ok`,`failed`,`not_present`,`degraded`) | N | | Power issue family |
| `redundant_ok` | BOOLEAN | Y | | Dual PSU loss prediction |

---

## 5. Network Analytics Engine (NAE) package

Aligned with AOS-CX NAE scripts/agents/monitors and time-series API.

### `nae_script`
`script_id`, `script_name`, `version`, `description`, `source_ref` (e.g., aruba/nae-scripts family: BGP, link health, hardware)

### `nae_agent`
`agent_id`, `device_id`, `script_id`, `agent_name`, `enabled`, `params` JSONB, `status`

### `nae_monitor`
`monitor_id`, `agent_id`, `monitor_name`, `uri_pattern`, `scrape_interval_s`

### `nae_timeseries_point`
| Attribute | Type | Null | Motivation |
|-----------|------|------|------------|
| `ts_id` | UUID PK | N | |
| `monitor_id` | UUID FK | N | |
| `observed_at` | TIMESTAMPTZ | N | |
| `series_type` | ENUM(`Raw`,`Rate`,`Average`,`Sum`,`Min`,`Max`,...) | N | Matches AOS-CX NAE aggregators |
| `metric_name` | TEXT | N | |
| `metric_value` | DOUBLE | N | |
| `resource_key` | TEXT | Y | Expanded wildcard resource |

**Why NAE is mandatory in this dataset:** It is the on-box analytics plane for AOS-CX; including it makes the dataset credible to Aruba-centric enterprise research and supports “analytics engine output” requirements.

---

## 6. Sampling and storage guidance (for future generation)

| Stream | Default cadence | Retention profile |
|--------|-----------------|-------------------|
| Interface counters | 60 s | 90–180 d |
| Device CPU/mem | 60 s | 90–180 d |
| Sensors | 60–300 s | 90–180 d |
| Power | 60–300 s | 90–180 d |
| NAE | script-defined (often 5–60 s) | 30–90 d raw |
| High-rate debug | optional 1–10 s windows around incidents | incident-centric |

Downsampled aggregates (`*_1m`, `*_5m`, `*_1h`) may be published as derived tables without replacing raw samples near incident windows.
