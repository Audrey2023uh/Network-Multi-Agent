# S01 — Inventory and Topology Tables

Conventions for all schema docs:

- **Type:** SQL-oriented logical types  
- **Null:** whether NULL allowed  
- **Src:** standards / ops source motivating the field  
- Justifications summarized here; full cross-cutting catalog in `S05`

---

## 1. `organization`

| Attribute | Type | Null | Src | Why it exists |
|-----------|------|------|-----|---------------|
| `org_id` | UUID PK | N | NMS inventory | Tenant root for multi-org releases |
| `org_name` | TEXT | N | ops | Human label |
| `industry_vertical` | TEXT | Y | research meta | Enables stratified evaluation (finance vs edu) |
| `created_at` | TIMESTAMPTZ | N | meta | Provenance |

**ML:** rare as a feature; used for stratified splits and domain adaptation studies.

---

## 2. `site`

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `site_id` | UUID PK | N | inventory | Multi-site enterprise |
| `org_id` | UUID FK | N | | |
| `site_code` | TEXT | N | ops | Stable natural key |
| `site_name` | TEXT | N | | |
| `site_type` | ENUM(`campus`,`datacenter`,`branch`,`colo`,`hq`) | N | enterprise practice | Topology profile conditioning |
| `timezone` | TEXT | N | IANA TZ | Local maintenance windows |
| `geo_lat`,`geo_lon` | DOUBLE | Y | Topology Zoo practice | Spatial models / failure correlation with facilities |
| `address_region` | TEXT | Y | | Privacy-preserving region only |
| `criticality_tier` | SMALLINT | N | ops (1–5) | Impact weighting |
| `valid_from`,`valid_to` | TIMESTAMPTZ | N/Y | bi-temporal | Site open/close |

**Networking:** Enterprises operate multi-site fabrics; outage cost differs by site tier.  
**ML:** site embeddings; hierarchical forecasting; transfer across site types.

---

## 3. `building`, `floor`, `rack`

Spatial hierarchy for AP RF planning, cooling, and power domains.

### `building`
`building_id`, `site_id`, `building_name`, `building_code`

### `floor`
`floor_id`, `building_id`, `floor_number`, `floor_label`

### `rack`
| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `rack_id` | UUID PK | N | DCIM | |
| `floor_id` | UUID FK | Y | | Campuses may omit racks |
| `site_id` | UUID FK | N | | |
| `rack_label` | TEXT | N | | |
| `power_feed_a_kw`,`power_feed_b_kw` | REAL | Y | facilities | Power failure scenarios |
| `cooling_zone_id` | UUID | Y | | Temp anomaly localization |

---

## 4. `device`

Core network element (switch, router, AP controller endpoint, firewall peer as managed L3 device, etc.).

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `device_id` | UUID PK | N | | |
| `site_id` | UUID FK | N | | |
| `rack_id` | UUID FK | Y | | |
| `hostname` | TEXT | N | sysName / OpenConfig system | Operator identity |
| `mgmt_ip` | INET | Y | | OOB/in-band mgmt |
| `device_class` | ENUM(`switch`,`router`,`access_point`,`wireless_controller`,`firewall`,`load_balancer`,`other`) | N | inventory | Graph node typing |
| `platform_model` | TEXT | N | AOS-CX platform (e.g., 8325, 8360, 6400, 6300) | Firmware compatibility faults |
| `serial_number` | TEXT | Y | ENTITY-MIB concept | Hardware degradation tracking |
| `role` | ENUM(`core`,`aggregation`,`access`,`spine`,`leaf`,`border`,`wan_edge`,`ap`,`oob`) | N | Clos/campus roles | GNN role features |
| `os_family` | TEXT | N | e.g., `AOS-CX` | |
| `os_version` | TEXT | N | | Firmware incompatibility labels |
| `ha_mode` | ENUM(`standalone`,`vsx_member`,`vc_member`,`vrrp_pair`) | N | Aruba VSX / HA | |
| `vsx_pair_id` | UUID FK | Y | VSX | |
| `is_managed` | BOOLEAN | N | | Unmanaged devices excluded from config tasks |
| `status` | ENUM(`active`,`maintenance`,`decommissioned`) | N | | |
| `commissioned_at` | TIMESTAMPTZ | N | | Lifetime reliability models |
| `valid_from`,`valid_to` | TIMESTAMPTZ | N/Y | | |

**Scientific motivation:** Device identity is the join key for nearly all telemetry and config studies (Cisco IE, ClosRCA).  
**ML:** node features; failure prediction at device horizon; transfer by `platform_model`.

---

## 5. `firmware_image`

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `firmware_id` | UUID PK | N | | |
| `os_family` | TEXT | N | | |
| `version_string` | TEXT | N | AOS-CX versioning | |
| `release_train` | TEXT | Y | | |
| `known_issue_tags` | TEXT[] | Y | PSIRT/release notes concept | Config/firmware risk |
| `min_compatible_partner_version` | TEXT | Y | VSX/ISL compatibility | Firmware incompatibility failures |

`device_firmware_history(device_id, firmware_id, installed_at, removed_at, install_result)`

---

## 6. `hardware_component`

PSU, fan, transceiver, fabric module — required for hardware degradation and power failures.

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `component_id` | UUID PK | N | OpenConfig platform component / ENTITY | |
| `device_id` | UUID FK | N | | |
| `component_type` | ENUM(`psu`,`fan`,`transceiver`,`line_card`,`fabric`,`cpu_complex`,`sensor`,`other`) | N | | |
| `name` | TEXT | N | e.g., `PSU1`, `1/1/1` DOM | |
| `part_number` | TEXT | Y | | |
| `serial_number` | TEXT | Y | | |
| `position` | TEXT | Y | | |
| `oper_status` | ENUM(`ok`,`fault`,`missing`,`unknown`) | N | | |
| `valid_from`,`valid_to` | TIMESTAMPTZ | N/Y | | |

---

## 7. `access_point` and `radio`

WLAN is essential for campus enterprise realism (missing from Clos-only datasets).

### `access_point`
| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `ap_id` | UUID PK | N | | |
| `device_id` | UUID FK | N | AP as device | |
| `controller_or_gw_id` | UUID FK | Y | | |
| `ap_group` | TEXT | Y | Central/group | |
| `eth_uplink_interface_id` | UUID FK | Y | | Wired backhaul |
| `ip_address` | INET | Y | | |
| `status` | ENUM | N | | |

### `radio`
`radio_id`, `ap_id`, `band` ENUM(`2.4`,`5`,`6`), `channel`, `channel_width_mhz`, `tx_power_dbm`, `oper_status`

**ML:** RF congestion vs wired congestion disentanglement; auth failure localization (dot1x).

---

## 8. `interface`

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `interface_id` | UUID PK | N | OpenConfig `/interfaces/interface` | |
| `device_id` | UUID FK | N | | |
| `if_name` | TEXT | N | `1/1/1`, `lag1`, `vlan100`, `lo0` | |
| `if_index` | INT | Y | IF-MIB ifIndex | SNMP join |
| `if_type` | ENUM(`ethernet`,`lag`,`vlan_svi`,`loopback`,`mgmt`,`vxlan_tunnel`,`other`) | N | | |
| `admin_status` | ENUM(`up`,`down`) | N | OC interface config | |
| `oper_status` | ENUM(`up`,`down`,`dormant`,`testing`,`unknown`) | N | OC/IF-MIB | Core anomaly signal |
| `speed_bps` | BIGINT | Y | | Utilization denominators |
| `mtu` | INT | Y | | MTU mismatch faults |
| `mac_address` | MACADDR | Y | | |
| `description` | TEXT | Y | | Weak semantic feature |
| `is_lag_member` | BOOLEAN | N | LACP | |
| `lag_group_id` | UUID FK | Y | | |
| `vrf_id` | UUID FK | Y | routing-instance | |
| `ipv4_address` | INET | Y | | |
| `ipv6_address` | INET | Y | | |
| `enabled_vlans_mode` | ENUM(`access`,`trunk`,`native_tagged`,`none`) | Y | | VLAN mismatch |
| `native_vlan_id` | INT | Y | | |
| `storm_control_pps` | BIGINT | Y | | Congestion / storm |
| `valid_from`,`valid_to` | TIMESTAMPTZ | N/Y | | |

**ML:** primary entity for interface failure, cable failure, congestion prediction.

---

## 9. `lag_group` and `lag_member`

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `lag_group_id` | UUID PK | N | LACP / AOS-CX LAG | |
| `device_id` | UUID FK | N | | |
| `lag_name` | TEXT | N | `lag1` | |
| `lag_type` | ENUM(`lacp`,`static`) | N | | |
| `min_links` | INT | Y | | Partial LAG failure |
| `lacp_mode` | ENUM(`active`,`passive`,`on`) | Y | | |
| `is_mclag` | BOOLEAN | N | VSX MCLAG | Dual-homing |
| `vsx_pair_id` | UUID FK | Y | | |

`lag_member(lag_group_id, interface_id, actor_key, partner_key, lacp_state, joined_at, left_at)`

**Networking:** LAG/MCLAG failures are first-class enterprise incidents distinct from single PHY down.  
**ML:** multi-link degradation vs total LAG down classification.

---

## 10. `vsx_pair`

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `vsx_pair_id` | UUID PK | N | AOS-CX VSX | |
| `site_id` | UUID FK | N | | |
| `system_mac` | MACADDR | Y | VSX system ID concept | |
| `member_a_device_id` | UUID FK | N | | |
| `member_b_device_id` | UUID FK | N | | |
| `isl_lag_id` | UUID FK | Y | Inter-Switch Link | |
| `keepalive_src_ip` | INET | Y | | Split-brain precursors |
| `keepalive_dst_ip` | INET | Y | | |
| `role_priority_a` | INT | Y | | |
| `oper_state` | ENUM(`sync`,`sync_progress`,`out_of_sync`,`split`) | N | | Critical RCA label source |

---

## 11. `link` (physical/logical adjacency)

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `link_id` | UUID PK | N | LLDP/CDP GT (cf. Cisco telemetry docs) | |
| `a_interface_id` | UUID FK | N | | |
| `b_interface_id` | UUID FK | N | | |
| `link_layer` | ENUM(`phy`,`lag`,`virtual`) | N | | |
| `discovery_method` | ENUM(`lldp`,`manual`,`inferred`) | N | | |
| `cable_id` | UUID | Y | cable plant | Cable failure entity |
| `media_type` | ENUM(`cu`,`smf`,`mmf`,`dac`,`virtual`) | Y | | DOM/temperature relevance |
| `length_m` | REAL | Y | | |
| `is_isl` | BOOLEAN | N | VSX ISL | |
| `is_uplink` | BOOLEAN | N | | Impact priors |
| `valid_from`,`valid_to` | TIMESTAMPTZ | N/Y | | |

`cable(cable_id, media_type, length_m, install_date, health_score)` optional asset table.

---

## 12. `vlan` and `vlan_membership`

| Attribute | Type | Null | Src | Why |
|-----------|------|------|-----|-----|
| `vlan_id_key` | UUID PK | N | | Surrogate (vlan_id not globally unique) |
| `site_id` | UUID FK | N | | |
| `vlan_id` | INT | N | 1–4094 | |
| `vlan_name` | TEXT | N | | |
| `vlan_purpose` | ENUM(`user`,`voice`,`server`,`mgmt`,`guest`,`ot`,`transit`,`other`) | N | | Impact priors |
| `l3_svi_interface_id` | UUID FK | Y | | |
| `dhcp_snooping_enabled` | BOOLEAN | Y | security ops | |
| `stretch_domain_id` | UUID | Y | DCI | |

`vlan_membership(interface_id, vlan_id_key, tagging ENUM(access,tagged,native), valid_from, valid_to)`

**Failure relevance:** VLAN mismatch (tagging disagreement across link).

---

## 13. EVPN / VXLAN (conditional package)

### `vxlan_vni`
`vni_id` (UUID), `vni` INT, `vlan_id_key` NULLABLE, `l3_vrf_id` NULLABLE, `vni_type` ENUM(`l2`,`l3`)

### `vtep`
`vtep_id`, `device_id`, `vtep_ip` INET, `source_interface_id`, `oper_status`

### `evpn_instance`
`evpn_id`, `routing_instance_id`, `evi`, `rd`, `rt_import[]`, `rt_export[]`

### `evpn_esi`
`esi_id`, `esi_value` TEXT, `lag_group_id` NULLABLE, `type` (single-active/all-active)

### `mac_ip_binding` (control-plane learned)
`binding_id`, `vni_id`, `mac`, `ip` NULLABLE, `vtep_id`, `seq_number`, `learned_at`, `withdrawn_at`

**Why included:** Leaf-spine EVPN is standard in modern enterprise DC; ClosRCA lacks overlay semantics. Empty for pure L2 campus profiles.

---

## 14. `topology_snapshot` and `topology_edge`

Versioned graph freeze for digital twins and cross-time joins.

| Attribute | Type | Null | Why |
|-----------|------|------|-----|
| `topology_snapshot_id` | UUID PK | N | |
| `topology_profile_id` | UUID FK | N | Which designed topology family |
| `snapshot_at` | TIMESTAMPTZ | N | |
| `node_count` | INT | N | QC |
| `edge_count` | INT | N | QC |
| `hash` | TEXT | N | Reproducibility |

`topology_edge(topology_snapshot_id, link_id, a_node_id, b_node_id, edge_type, attrs JSONB)`

---

## 15. `topology_profile`

Metadata for cross-topology validation:

`topology_profile_id`, `name`, `category` ENUM(`campus`,`dc_evpn`,`branch`,`hybrid`), `generator_seed` (future), `description`, `device_count_target`, `has_evpn`, `has_vsx`, `has_wifi`
