# F01 — Failure and Recovery Taxonomy

Ground-truth operational semantics for supervised learning and autonomous management.

---

## 1. Core tables

### `failure_incident`

| Attribute | Type | Null | Definition |
|-----------|------|------|------------|
| `incident_id` | UUID PK | N | |
| `topology_profile_id` | UUID FK | N | |
| `category` | ENUM | N | See §2 |
| `subcategory` | TEXT | N | Fine type |
| `severity` | ENUM(`low`,`medium`,`high`,`critical`) | N | |
| `onset_at` | TIMESTAMPTZ | N | True fault start (GT) |
| `detected_at` | TIMESTAMPTZ | Y | First correct detection time |
| `detection_source` | ENUM(`syslog`,`alert`,`nae`,`kpi`,`human`,`oracle`) | Y | |
| `detection_latency_s` | REAL | Y | `detected_at - onset_at` |
| `recovered_at` | TIMESTAMPTZ | Y | Service restored |
| `recovery_duration_s` | REAL | Y | Sum/action span |
| `recovery_success` | BOOLEAN | Y | |
| `downtime_s` | REAL | Y | Service-impacting downtime |
| `root_entity_type` | TEXT | N | interface/device/... |
| `root_entity_id` | UUID | N | |
| `trigger_type` | ENUM(`spontaneous`,`change_induced`,`dependent`,`cascaded`,`injected`) | N | |
| `change_diff_id` | UUID FK | Y | If change-induced |
| `parent_incident_id` | UUID FK | Y | Cascades |
| `description` | TEXT | N | |
| `observable_precursors` | JSONB | N | Expected signals for falsifiability |

### `incident_entity`
`incident_id`, `entity_type`, `entity_id`, `role` ENUM(`root`,`symptomatic`,`collateral`)

### `service_impact`
`impact_id`, `incident_id`, `service_id`, `impact_start`, `impact_end`, `severity`, `users_affected`, `sla_breach` BOOLEAN

### `recovery_action`

| Attribute | Type | Null | Definition |
|-----------|------|------|------------|
| `action_id` | UUID PK | N | |
| `incident_id` | UUID FK | N | |
| `sequence` | INT | N | Order |
| `action_type` | ENUM | N | See §3 |
| `action_params` | JSONB | Y | e.g., interface name |
| `started_at` | TIMESTAMPTZ | N | |
| `ended_at` | TIMESTAMPTZ | Y | |
| `duration_s` | REAL | Y | |
| `success` | BOOLEAN | N | |
| `actor` | ENUM(`human`,`script`,`nae`,`orchestrator`,`self_heal`) | N | |
| `runbook_id` | TEXT | Y | |
| `notes` | TEXT | Y | |

---

## 2. Failure categories (required coverage)

Each category lists: **mechanism**, **observable precursors**, **typical recovery**, **primary labels**.

### C01 — Interface failure
- **Mechanism:** admin shut, PHY down, transceiver pull, driver fault  
- **Precursors:** `oper_status` down, carrier transitions ↑, syslog link down, RX power collapse  
- **Recovery:** `no_shut`, reseat optic, replace optic, failover to LAG member  
- **Labels:** anomaly, fail-predict, RCA target=interface, impact via uplink dependency  

### C02 — Cable failure
- **Mechanism:** cut, bent fiber, dirty connector, intermittent contact  
- **Precursors:** FCS/CRC ↑, DOM RX low, flapping, both ends correlated errors  
- **Recovery:** recable, clean connector, move to spare strand  
- **Distinct from C01:** `cable_id` root entity; both endpoints symptomatic  

### C03 — Congestion
- **Mechanism:** demand > capacity; microburst; ECMP imbalance  
- **Precursors:** util → 1, out_discards ↑, queue drops, latency KPI ↑, no hard down  
- **Recovery:** reshape/QoS tune, add capacity, reroute, storm-control  
- **Labels:** degradation prediction; not always “failure_down”  

### C04 — Routing instability
- **Mechanism:** BGP flap, OSPF adjacency loss, BFD down, route churn, blackhole  
- **Precursors:** session state transitions, prefix count drops, CPU ↑, syslog bgp  
- **Recovery:** stabilize timer, restore peer, withdraw bad route, BFD tune  
- **Labels:** RCA cause=`routing_instability`; ClosRCA-compatible subset  

### C05 — ACL misconfiguration
- **Mechanism:** wrong ACE order, deny critical traffic, wrong binding direction, shadowed rules  
- **Precursors:** config diff on ACL, IPFIX drop reasons, service reachability loss, counters on deny ACE  
- **Recovery:** rollback snapshot, fix ACE, rebind  
- **Labels:** config risk; change-induced trigger  

### C06 — VLAN mismatch
- **Mechanism:** access↔trunk disagreement, native VLAN mismatch, missing allowed VLAN  
- **Precursors:** config asymmetry on `PHYS_LINK` ends, CDP/LLDP VLAN TLV mismatch (if modeled), connectivity loss without PHY down  
- **Recovery:** align tagging, restore allowed VLAN list  
- **Labels:** config risk + RCA  

### C07 — STP loop
- **Mechanism:** guard disabled + redundant L2 without blocking; bridging loop  
- **Precursors:** broadcast storm (bcast pps ↑), CPU ↑, MAC flapping syslog, topology changes  
- **Recovery:** shut victim ports, enable BPDU guard, fix STP priority, remove loop  
- **Labels:** rare-event AD; high severity impact  

### C08 — Firmware incompatibility
- **Mechanism:** VSX members on incompatible trains; feature mismatch after upgrade  
- **Precursors:** `device_firmware_history` divergence, VSX `out_of_sync`, unexpected protocol flaps post-upgrade  
- **Recovery:** align firmware, rollback image  
- **Labels:** config/firmware risk  

### C09 — QoS problems
- **Mechanism:** wrong class match, insufficient queue weight, policer too tight  
- **Precursors:** class-specific drops, DSCP remark anomalies, app KPI loss with moderate link util  
- **Recovery:** retune policy, rollback QoS binding  
- **Labels:** service degradation (voice/video)  

### C10 — Authentication failures
- **Mechanism:** RADIUS down, shared secret mismatch, cert expiry, mis-ordered AAA list  
- **Precursors:** AAA syslog rejects, new endpoints fail attach, existing sessions may survive  
- **Recovery:** restore RADIUS, fix secret, failover server group  
- **Labels:** impact on user attach; may not affect transit forwarding  

### C11 — Hardware degradation
- **Mechanism:** fan wear, optic aging, memory errors, line card faults  
- **Precursors:** sensor warn/crit trends, increasing FCS, soft errors in syslog  
- **Recovery:** replace component, redundant failover  
- **Labels:** survival / remaining-useful-life style prediction  

### C12 — Power issues
- **Mechanism:** PSU fail, dual feed loss, site PDU event  
- **Precursors:** `psu_status`, power samples, sudden multi-device correlated downs  
- **Recovery:** replace PSU, restore feed, graceful shutdown policies  
- **Labels:** multi-device cascade parent incidents  

### C13 — Intermittent failures
- **Mechanism:** flapping optics, loose cable, thermal intermittent  
- **Precursors:** short down pulses, carrier transitions, oscillating KPIs  
- **Recovery:** reseat, replace, hysteresis thresholds  
- **Labels:** hard for AD (non-stationary); explicit subcategory  

### Optional extensions (recommended for completeness)
- **C14 EVPN/VXLAN faults:** VTEP reachability loss, ESI imbalance, MAC mobility storms  
- **C15 VSX split-brain:** ISL + keepalive dual failure  
- **C16 DHCP/helper misconfig:** (campus) — only if DHCP relay modeled in config  

---

## 3. Recovery action types (`action_type`)

| action_type | Typical categories |
|-------------|--------------------|
| `interface_admin_up` | C01 |
| `interface_admin_down` | C07 containment |
| `replace_transceiver` | C01/C02/C11 |
| `replace_cable` | C02 |
| `lacp_reinit` / `failover_lag_member` | C01/C02 |
| `bgp_neighbor_reset` | C04 |
| `route_rollback` | C04 |
| `config_rollback` | C05/C06/C09/C08 |
| `acl_update` | C05 |
| `vlan_tagging_fix` | C06 |
| `stp_guard_enable` | C07 |
| `qos_policy_update` | C09 |
| `radius_restore` | C10 |
| `firmware_align_rollback` | C08 |
| `psu_replace` | C12 |
| `device_reboot` | last resort |
| `capacity_augment` | C03 |
| `traffic_reroute` | C03/C04 |
| `nae_script_remediation` | automated |
| `no_action_self_clear` | intermittent clear |

---

## 4. Required fields per incident (checklist)

Every GT incident MUST populate:

- [ ] category + subcategory  
- [ ] onset_at  
- [ ] detected_at (or explicit `undetected=true`)  
- [ ] detection_latency_s if detected  
- [ ] ≥1 recovery_action OR `self_cleared=true`  
- [ ] recovery_success  
- [ ] downtime_s (0 if non-service-impacting)  
- [ ] ≥1 service_impact row OR explicit `no_service_impact=true`  
- [ ] root entity  
- [ ] observable_precursors non-empty  

This checklist is what makes autonomous network management *evaluable*.

---

## 5. Concurrent and cascading faults

- `parent_incident_id` encodes cascades (power → multi-link → routing)  
- Benchmark slices: `single_fault`, `compound_fault`, `cascade`  
- Compound faults must remain minority class to match realism, but enough for stress tests (cf. ClosRCA compound slices)
