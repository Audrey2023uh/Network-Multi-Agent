# G01 — Network Graph Specification

The authoritative topology lives in relational tables (`device`, `interface`, `link`, …). The graph is a **typed property graph projection** for GNNs, digital twins, and RCA.

---

## 1. Graph snapshot

```
G_t = (V_t, E_t, X_v(t), X_e(t), t)
```

- Materialized in `graph_snapshot`, `graph_node`, `graph_edge`
- Built from `topology_snapshot` plus dynamic attributes at time `t`
- Dynamic edges (BGP session, VSX keepalive) may appear/disappear

---

## 2. Node types (`graph_node.node_type`)

| Node type | Source entity | Typical features `X_v` | Used for |
|-----------|---------------|------------------------|----------|
| `Site` | `site` | criticality, type | hierarchical pooling |
| `Device` | `device` | role, platform, CPU, mem, OS ver | RCA localization |
| `Interface` | `interface` | admin/oper, util, errors, speed | link/interface faults |
| `LAG` | `lag_group` | member count, min_links, mclag flag | partial aggregate faults |
| `VLAN` | `vlan` | purpose, id | mismatch / segmentation |
| `VRF` | `routing_instance` | name, rd | routing domains |
| `VTEP` | `vtep` | vtep_ip, status | overlay |
| `VNI` | `vxlan_vni` | vni, l2/l3 | overlay |
| `AP` | `access_point` | group, status | campus |
| `Radio` | `radio` | band, channel, tx | RF |
| `Endpoint` | `endpoint` | type, access | impact |
| `Service` | `service` | criticality | impact heads |
| `Application` | `application` | category, DSCPs | QoS/degradation |
| `ACL` | `acl` | type, ace_count | config risk |
| `QoSPolicy` | `qos_policy` | type | QoS faults |
| `PSU` | `hardware_component` | status | power |
| `Sensor` | component/sensor | value, status | hardware |
| `BGPNeighbor` | `bgp_neighbor` | state, prefixes | routing instability |
| `STPBridge` | `stp_instance` | is_root, priority | loops |
| `User` | `user_account` | dept (coarse) | auth impact |
| `Incident` | `failure_incident` | (label graphs only) | supervision |

Not every snapshot must include all types; minimal twin uses `Device`–`Interface`–`LAG`–`VLAN`–`Service`.

---

## 3. Edge types (`graph_edge.edge_type`)

| Edge type | Endpoints | Directed? | Meaning | Dynamic? |
|-----------|-----------|-----------|---------|----------|
| `LOCATED_IN` | Device→Site / Rack→Floor… | Y | placement | N |
| `HAS_INTERFACE` | Device→Interface | Y | ownership | N |
| `MEMBER_OF_LAG` | Interface→LAG | Y | aggregation | rare |
| `PHYS_LINK` | Interface↔Interface | N | L1 adjacency | Y (cabling changes) |
| `LAG_LINK` | LAG↔LAG or Interface | N | logical agg link | Y |
| `VSX_PEER` | Device↔Device | N | VSX members | N |
| `VSX_ISL` | LAG↔LAG | N | ISL | Y |
| `VSX_KEEPALIVE` | Device↔Device | Y | keepalive path | Y |
| `ACCESS_VLAN` | Interface→VLAN | Y | access mode | Y |
| `TRUNK_VLAN` | Interface→VLAN | Y | tagged | Y |
| `SVI_OF` | Interface→VLAN | Y | L3 interface | Y |
| `IN_VRF` | Interface/Device→VRF | Y | routing-instance | Y |
| `OSPF_ADJ` | Device↔Device (via if) | N | adjacency | Y |
| `BGP_SESSION` | Device↔Device / BGPNeighbor | Y | session | Y |
| `BFD_SESSION` | Device↔Device | N | bfd | Y |
| `EVPN_VTEP_VNI` | VTEP→VNI | Y | mapping | Y |
| `EVPN_ESI_MEMBER` | LAG/Interface→ESI | Y | dual-home | Y |
| `AP_UPLINK` | AP→Interface | Y | backhaul | Y |
| `ASSOC_RADIO` | Endpoint→Radio | Y | Wi-Fi attach | Y |
| `ATTACHED_TO` | Endpoint→Interface | Y | wired attach | Y |
| `SERVES` | Service→Endpoint/Application | Y | service map | Y |
| `DEPENDS_ON` | Service→Service/Device | Y | dependency | Y |
| `ACL_BOUND` | ACL→Interface/VLAN | Y | policy attach | Y |
| `QOS_BOUND` | QoSPolicy→Interface | Y | | Y |
| `POWERED_BY` | Device→PSU | Y | | Y |
| `TRAFFIC_FLOW` | Interface→Interface (agg) | Y | demand edge optional | Y |
| `CAUSES` | Incident→Entity | Y | GT only | label |
| `IMPACTS` | Incident→Service | Y | GT only | label |

---

## 4. Node / edge property schemas

### Common node properties
`node_id`, `node_type`, `ref_table`, `ref_pk`, `name`, `site_id`, `feature_vector` JSONB or columnar side table `graph_node_features(snapshot_id, node_id, features JSONB)`

### Common edge properties
`edge_id`, `edge_type`, `src_node_id`, `dst_node_id`, `is_directed`, `weight`, `link_id` NULLABLE, `attrs` JSONB (speed, utilization, state)

### Time-varying features (examples)
- Device: `cpu_util_pct`, `mem_util_pct`, `bgp_established_frac`
- Interface: `util_in`, `util_out`, `err_rate`, `oper_up`
- Service: `latency_p95`, `loss_pct`, `availability`

---

## 5. Graph construction algorithm (normative)

```
for each topology_snapshot at time t:
  add Site, Device, Interface, LAG, VLAN, VRF nodes
  add HAS_INTERFACE, MEMBER_OF_LAG, PHYS_LINK/LAG_LINK from inventory
  add VSX_* from vsx_pair
  add VLAN edges from vlan_membership
  if EVPN profile: add VTEP/VNI/ESI edges
  add routing adjacency edges from latest neighbor state ≤ t
  add Service/Endpoint edges from service maps valid at t
  attach latest telemetry features with observed_at in (t - Δ, t]
```

Δ default: 60–300s depending on stream.

---

## 6. Recommended GNN task graphs

| Task | Nodes | Edges | Label |
|------|-------|-------|-------|
| Anomaly detection | Device, Interface | PHYS/LAG/VSX | window anomaly |
| Failure prediction | Device, Interface | + telemetry feats | horizon fail |
| RCA | + Incident | CAUSES (train only) | target entity / cause |
| Impact | + Service | DEPENDS_ON, IMPACTS | blast radius |
| Config risk | + ACL, VLAN | ACL_BOUND, TRUNK | risk score |

**Leakage rule:** `CAUSES` / `IMPACTS` edges forbidden in *input* graphs for test inference; only in training supervision or evaluation.
