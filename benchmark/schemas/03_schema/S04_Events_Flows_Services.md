# S04 — Events, Flows, Users, Applications, Services

---

## 1. `syslog_event`

Syslog remains the universal enterprise signal; fields align with RFC 5424 concepts and Aruba CX facility practices (AAA, ACL, BGP, OSPF, LACP, hardware).

| Attribute | Type | Null | Motivation |
|-----------|------|------|------------|
| `syslog_id` | UUID PK | N | |
| `device_id` | UUID FK | N | |
| `observed_at` | TIMESTAMPTZ | N | Event time (device) |
| `received_at` | TIMESTAMPTZ | N | Collector skew modeling |
| `facility` | TEXT | N | |
| `severity` | SMALLINT | N | 0–7 |
| `severity_label` | TEXT | N | |
| `app_name` | TEXT | Y | e.g., `bgp`, `lacp`, `aaa` |
| `msg_id` | TEXT | Y | |
| `event_code` | TEXT | Y | Vendor event id if present |
| `message` | TEXT | N | |
| `structured_data` | JSONB | Y | Parsed key-values |
| `interface_id` | UUID FK | Y | Linked entity when parseable |
| `related_user` | TEXT | Y | Auth events |
| `is_parse_success` | BOOLEAN | N | Data quality |

**ML:** sequence models for RCA; burst features; weak supervision for incidents.

---

## 2. `alert`

NMS / Aruba Central–style alerts (logical model, not proprietary dump).

| Attribute | Type | Null | Motivation |
|-----------|------|------|------------|
| `alert_id` | UUID PK | N | |
| `device_id` | UUID FK | Y | |
| `interface_id` | UUID FK | Y | |
| `raised_at` | TIMESTAMPTZ | N | Detection time candidate |
| `cleared_at` | TIMESTAMPTZ | Y | |
| `alert_type` | TEXT | N | e.g., `link_down`,`high_cpu`,`psu_fail` |
| `severity` | ENUM(`info`,`warning`,`major`,`critical`) | N | |
| `title` | TEXT | N | |
| `body` | TEXT | Y | |
| `source_system` | ENUM(`onbox_nae`,`nms`,`siem`,`synthetic_labeler`) | N | |
| `correlated_incident_id` | UUID FK | Y | Link to GT incident |
| `is_false_positive_gt` | BOOLEAN | Y | For alert-quality research |

---

## 3. `event_correlation`

`corr_id`, `created_at`, `window_start`, `window_end`, `member_alert_ids UUID[]`, `member_syslog_ids UUID[]`, `hypothesis` TEXT, `confidence` REAL

Supports multi-alarm RCA tasks without forcing a single alert = single incident.

---

## 4. IPFIX / flow package

Aligned with RFC 7011 and AOS-CX IPFIX (match/collect fields; drop exceptions where applicable).

### `ipfix_exporter`
`exporter_id`, `device_id`, `exporter_ip`, `observation_domain_id`, `template_id`, `export_interval_s`

### `ipfix_record`
| Attribute | Type | Null | IE concept | Motivation |
|-----------|------|------|------------|------------|
| `flow_id` | UUID PK | N | | |
| `exporter_id` | UUID FK | N | | |
| `flow_start` | TIMESTAMPTZ | N | | Temporal |
| `flow_end` | TIMESTAMPTZ | N | | |
| `src_addr` | INET | N | | |
| `dst_addr` | INET | N | | |
| `src_port` | INT | Y | | |
| `dst_port` | INT | Y | | |
| `protocol` | SMALLINT | N | | |
| `in_packets` | BIGINT | N | | Volume |
| `in_bytes` | BIGINT | N | | |
| `ingress_interface_id` | UUID FK | Y | ifIndex map | Topology join |
| `egress_interface_id` | UUID FK | Y | | |
| `tcp_flags` | INT | Y | | |
| `dscp` | SMALLINT | Y | QoS | Class of service |
| `fwd_status` | TEXT | Y | forwarding-status | Drops |
| `drop_reason_codes` | INT[] | Y | AOS-CX private IEs 1200–1233 concept | ACL/QoS/resource drops |
| `application_id` | UUID FK | Y | DPI/NBAR-like mapping if present | Service analytics |
| `exported_at` | TIMESTAMPTZ | N | | |

### `flow_aggregate_5m`
Pre-aggregates for scalability: `device_id`, `interface_id`, `application_id`, `dscp`, `bytes`, `packets`, `flows`, `bucket_start`

**Why flows matter:** Congestion, ACL drops, and application degradation are not fully visible from SNMP counters alone.

---

## 5. Users and endpoints

### `user_account`
`user_id`, `org_id`, `user_name_hash`, `department`, `role`, `is_privileged`, `valid_from`, `valid_to`  
(Hashes only — privacy.)

### `endpoint`
| Attribute | Type | Null | Motivation |
|-----------|------|------|------------|
| `endpoint_id` | UUID PK | N | |
| `site_id` | UUID FK | N | |
| `mac` | MACADDR | Y | Pseudonymized OUI-preserving optional |
| `ip_address` | INET | Y | |
| `hostname` | TEXT | Y | |
| `endpoint_type` | ENUM(`laptop`,`phone`,`printer`,`camera`,`ot_device`,`server`,`vm`,`iot`,`other`) | N | |
| `os_family` | TEXT | Y | |
| `access_type` | ENUM(`wired`,`wifi`,`vpn`) | N | |
| `attached_interface_id` | UUID FK | Y | Access switch/AP path |
| `ap_id` | UUID FK | Y | |
| `auth_method` | ENUM(`dot1x`,`mab`,`open`,`vpn_cert`,`other`) | Y | Auth failure studies |
| `vlan_id_key` | UUID FK | Y | |
| `last_seen_at` | TIMESTAMPTZ | N | |

---

## 6. Applications and services

### `application`
`application_id`, `app_name`, `app_category` ENUM(`voice`,`video`,`erp`,`email`,`web`,`backup`,`dns`,`auth`,`ot`,`other`), `default_dscp`, `port_hints` INT[], `sensitivity_latency_ms`, `sensitivity_loss_pct`

### `service`
| Attribute | Type | Null | Motivation |
|-----------|------|------|------------|
| `service_id` | UUID PK | N | Business service |
| `service_name` | TEXT | N | e.g., `SAP-Prod`,`VoIP` |
| `owner_team` | TEXT | Y | |
| `criticality_tier` | SMALLINT | N | Impact weighting |
| `primary_site_id` | UUID FK | Y | |
| `sla_id` | UUID FK | Y | |

### `service_dependency`
`dep_id`, `service_id`, `depends_on_service_id` NULLABLE, `depends_on_device_id` NULLABLE, `depends_on_application_id` NULLABLE, `dependency_type` ENUM(`network_path`,`auth`,`dns`,`db`,`api`), `weight`

### `service_endpoint_bind`
`bind_id`, `service_id`, `endpoint_id`, `role` ENUM(`client`,`server`,`both`)

### `sla_objective`
`sla_id`, `service_id`, `metric` ENUM(`availability`,`latency_ms`,`loss_pct`,`jitter_ms`), `target_value`, `window` ENUM(`monthly`,`weekly`,`rolling_24h`)

### `service_kpi_sample`
`kpi_id`, `service_id`, `observed_at`, `availability_pct`, `latency_p50_ms`, `latency_p95_ms`, `loss_pct`, `jitter_ms`, `active_users`

**ML targets:** service degradation prediction; impact prediction uses these as outcomes.

---

## 7. Why the service plane is non-optional

Existing public telemetry sets stop at devices/interfaces. Enterprise cognitive networking papers targeting IEEE TNSM / Network must answer **“so what?”** — blast radius to services and users. Without `service_*` tables, impact and degradation labels lack grounding.
