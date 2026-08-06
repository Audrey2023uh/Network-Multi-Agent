# S02 — Configuration Tables

Configuration is the primary missing modality in telemetry-only benchmarks. ECNetBench treats configuration as **versioned, structured, diffable state**, not opaque CLI blobs alone (CLI text may be attached for realism).

---

## 1. `config_snapshot`

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `config_snapshot_id` | UUID PK | N | AOS-CX checkpoint / NMS backup | Twin replay |
| `device_id` | UUID FK | N | | |
| `snapshot_at` | TIMESTAMPTZ | N | | Temporal alignment |
| `trigger` | ENUM(`scheduled`,`pre_change`,`post_change`,`manual`,`incident`) | N | change mgmt | Causal studies |
| `config_hash` | TEXT | N | | Drift detection |
| `schema_version` | TEXT | N | REST/YANG revision | |
| `structured_config` | JSONB | N | REST/OpenConfig JSON | Machine-readable |
| `cli_text` | TEXT | Y | | Human/XAI |
| `is_baseline` | BOOLEAN | N | | Risk vs known-good |
| `change_ticket_id` | TEXT | Y | ITSM | |

**Scientific:** Digital twin literature requires diverse valid configs + misconfigs.  
**ML:** config risk prediction; change-induced incident labeling via `pre_change`/`post_change` pairs.

---

## 2. `config_object_diff`

Fine-grained diffs for RCA and XAI (which object changed).

| Attribute | Type | Null | Why |
|-----------|------|------|-----|
| `diff_id` | UUID PK | N | |
| `before_snapshot_id` | UUID FK | N | |
| `after_snapshot_id` | UUID FK | N | |
| `object_type` | TEXT | N | e.g., `acl_entry`,`bgp_neighbor`,`vlan_membership` |
| `object_key` | TEXT | N | Stable path / URI |
| `change_op` | ENUM(`add`,`remove`,`modify`) | N | |
| `before_value` | JSONB | Y | |
| `after_value` | JSONB | Y | |
| `risk_score_heuristic` | REAL | Y | Optional rule-based prior |
| `diffed_at` | TIMESTAMPTZ | N | |

---

## 3. Routing package

### `routing_instance` (VRF)
`vrf_id`, `device_id`, `vrf_name`, `rd`, `is_default`, `valid_from`, `valid_to`  
Src: OpenConfig network-instance / AOS-CX VRF.

### `ospf_process`
`ospf_id`, `device_id`, `vrf_id`, `process_id`, `router_id`, `area_count`, `admin_state`

### `ospf_interface`
`ospf_if_id`, `ospf_id`, `interface_id`, `area_id`, `network_type`, `cost`, `hello_interval`, `dead_interval`, `state` ENUM(`down`,`init`,`2way`,`full`,...)

### `bgp_process`
`bgp_id`, `device_id`, `vrf_id`, `asn`, `router_id`, `admin_state`

### `bgp_neighbor`
| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `bgp_neighbor_id` | UUID PK | N | OC BGP / AOS-CX | |
| `bgp_id` | UUID FK | N | | |
| `neighbor_ip` | INET | N | | |
| `remote_asn` | INT | N | | |
| `peer_group` | TEXT | Y | | |
| `session_state` | ENUM(`idle`,`connect`,`active`,`opensent`,`openconfirm`,`established`) | N | Classic instability signal | |
| `bfd_enabled` | BOOLEAN | N | | |
| `af_ipv4_unicast` | BOOLEAN | N | | |
| `af_l2vpn_evpn` | BOOLEAN | N | EVPN | |
| `prefixes_received` | INT | Y | | Sudden drops → blackhole |
| `prefixes_sent` | INT | Y | | |
| `last_state_change_at` | TIMESTAMPTZ | Y | | Routing instability |

### `static_route`
`static_id`, `vrf_id`, `prefix` CIDR, `next_hop`, `outgoing_interface_id`, `admin_distance`, `is_floating`

### `bfd_session`
`bfd_id`, `device_id`, `peer_ip`, `interface_id`, `state` ENUM(`up`,`down`,`admin_down`), `tx_interval_ms`, `rx_interval_ms`, `multiplier`, `last_change_at`  
**Rationale:** ClosRCA includes BFD outages; enterprise WAN/DC likewise.

### `rib_entry` / `fib_entry` (sampled)
Periodic or event-driven samples — not full FIB every second (scalability).

`rib_sample_id`, `device_id`, `vrf_id`, `prefix`, `protocol`, `next_hop`, `metric`, `sampled_at`  
`fib_entry` similar with `egress_interface_id`, `drop_flag`

**Failure relevance:** routing instability, blackholes, asymmetric paths.

---

## 4. ACL package

### `acl`
`acl_id`, `device_id`, `acl_name`, `acl_type` ENUM(`ipv4`,`ipv6`,`mac`), `is_active`

### `acl_entry` (ACE)
| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `ace_id` | UUID PK | N | ACL models | |
| `acl_id` | UUID FK | N | | |
| `sequence` | INT | N | Order semantics | |
| `action` | ENUM(`permit`,`deny`) | N | | |
| `protocol` | TEXT | Y | | |
| `src_prefix` | CIDR | Y | | |
| `dst_prefix` | CIDR | Y | | |
| `src_port_range` | TEXT | Y | | |
| `dst_port_range` | TEXT | Y | | |
| `hit_count` | BIGINT | Y | platform counters if available | Shadowed ACE detection |
| `is_log` | BOOLEAN | N | | |
| `comment` | TEXT | Y | | |

### `acl_binding`
`binding_id`, `acl_id`, `interface_id` NULLABLE, `vlan_id_key` NULLABLE, `direction` ENUM(`in`,`out`), `valid_from`, `valid_to`

**Misconfiguration failure family:** shadowed denies, wrong binding direction, missing permit for critical service, overly broad permits (security risk label).

---

## 5. QoS package

### `qos_policy`
`qos_policy_id`, `device_id`, `policy_name`, `policy_type` ENUM(`marking`,`queuing`,`policing`,`shaping`)

### `qos_class`
`qos_class_id`, `qos_policy_id`, `class_name`, `match_dscp[]`, `match_cos[]`, `match_acl_id`

### `qos_queue`
`qos_queue_id`, `device_id`, `queue_id`, `scheduler` ENUM(`strict`,`wrr`,`dwrr`), `weight`, `bandwidth_pct`, `buffer_bytes`

### `qos_binding`
`binding_id`, `qos_policy_id`, `interface_id`, `direction`, `valid_from`, `valid_to`

### `qos_queue_counter_sample` (telemetry bridge)
`sample_id`, `qos_queue_id`, `interface_id`, `observed_at`, `tx_packets`, `tx_drops`, `ecn_marked` NULLABLE, `latency_estimate_us` NULLABLE

**Failure family:** QoS mis-scheduling, buffer exhaustion, voice/video class starvation.  
**ML:** service degradation prediction with queue drops as precursors.

---

## 6. STP / loop prevention

### `stp_instance`
`stp_id`, `device_id`, `mode` ENUM(`mstp`,`rstp`,`pvst_like`), `priority`, `bridge_mac`, `is_root`

### `stp_port`
`stp_port_id`, `stp_id`, `interface_id`, `port_role` ENUM(`root`,`designated`,`alternate`,`backup`,`disabled`), `port_state` ENUM(`forwarding`,`blocking`,`learning`,`disabled`), `path_cost`, `bpdu_guard`, `root_guard`, `loop_guard`, `last_topology_change_at`

**Failure family:** STP loop (guard disabled + bridging loop), unexpected root takeover.  
**Observability:** topology change rate, MAC flapping (see events), CPU spikes.

---

## 7. AAA / authentication config

### `aaa_method`
`aaa_id`, `device_id`, `method_list_name`, `auth_type` ENUM(`dot1x`,`mac_auth`,`admin_login`), `server_group`, `fallback_local`

### `radius_server`
`radius_id`, `site_id`, `server_ip`, `timeout_s`, `retransmit`, `status`

**Failure family:** authentication failures (server unreachable, shared-secret mismatch, certificate expiry on related WLAN).

---

## 8. `api_response_archive`

Captures management-plane realism (AOS-CX REST / gNMI get responses).

| Attribute | Type | Null | Why |
|-----------|------|------|-----|
| `api_response_id` | UUID PK | N | |
| `device_id` | UUID FK | N | |
| `observed_at` | TIMESTAMPTZ | N | |
| `protocol` | ENUM(`rest`,`gnmi`,`netconf`) | N | |
| `method` | TEXT | N | GET/SET/... |
| `resource_path` | TEXT | N | URI / OC path |
| `http_status` | INT | Y | |
| `latency_ms` | REAL | Y | Control-plane health |
| `response_hash` | TEXT | N | |
| `response_body` | JSONB | Y | Size-capped |
| `error_code` | TEXT | Y | |

**ML:** API latency/error bursts as precursors to mgmt isolation; used in agent benchmarks.
