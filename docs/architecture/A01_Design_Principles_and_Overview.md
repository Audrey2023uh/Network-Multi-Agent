# A01 — Design Principles and Dataset Overview

## 1. Design principles

| ID | Principle | Operationalization |
|----|-----------|-------------------|
| P1 | **Realism over convenience** | Attributes map to AOS-CX REST/NAE, OpenConfig, IPFIX IEs, syslog semantics, or established ops practice |
| P2 | **Causal completeness** | Failures have precursors, detection, impact, recovery, and outcome — not isolated labels |
| P3 | **Dual representation** | Relational warehouse (joins, SQL analytics) + typed property graph (GNNs, digital twins) |
| P4 | **Temporal first-class citizens** | Every observation has `observed_at` (UTC); config/topology are versioned snapshots |
| P5 | **Service-centric impact** | Device health alone is insufficient; labels include affected services and downtime |
| P6 | **XAI lineage** | Labels link to evidence entities (interface, ACE, VTEP, AP radio, PSU) |
| P7 | **Scalable instance families** | Schema supports branch (tens of devices) to multi-site enterprise (thousands) without redesign |
| P8 | **Benchmark honesty** | Protocol forbids random shuffling across time; requires topology hold-outs |
| P9 | **No gratuitous fields** | Each attribute justified (scientific + networking + ML) in the catalog |
| P10 | **Generation deferred** | Spec freezes semantics before any synthetic sampling |

---

## 2. Enterprise network scope (what “enterprise” means here)

ECNetBench models a **large multi-site enterprise** using HPE Aruba AOS-CX switching/routing in:

- **Campus access / aggregation / core** (wired + WLAN APs)  
- **Data center leaf-spine** (optional EVPN/VXLAN overlay)  
- **Branch / WAN edge** (routers, firewalls as L3 peers where needed)  
- **Management / OOB** plane (separate VRFs / VRFs as routing instances)

Representative Aruba-class capabilities reflected in schema:

- VSX (Virtual Switching Extension) active-active pairs  
- Multi-Chassis LAG (MCLAG) / LACP aggregation groups  
- VLANs, SVIs, ACLs, QoS queues/classes  
- BGP / OSPF / static routing; BFD where applicable  
- EVPN/VXLAN (VNI, VTEP, ESI) when topology profile includes overlay  
- NAE agents/monitors/time-series  
- IPFIX exporters/monitors  
- Central/NMS-style inventory and alert objects (logical, not proprietary dump)

---

## 3. Logical architecture (four planes)

```
┌─────────────────────────────────────────────────────────────┐
│  SERVICE PLANE: users, endpoints, applications, SLAs        │
├─────────────────────────────────────────────────────────────┤
│  CONTROL / CONFIG PLANE: VLANs, routing, ACL, QoS, STP,     │
│                         VSX, EVPN, firmware, snapshots      │
├─────────────────────────────────────────────────────────────┤
│  DATA / TOPOLOGY PLANE: devices, interfaces, links, LAGs,   │
│                         APs, radios, graph projection       │
├─────────────────────────────────────────────────────────────┤
│  OBSERVABILITY PLANE: counters, NAE, syslog, alerts, IPFIX, │
│                       API responses, incidents & recovery   │
└─────────────────────────────────────────────────────────────┘
```

Cognitive networking tasks consume all four planes. Digital twins require planes 2–4 with service annotations from plane 1.

---

## 4. Instance scale targets (for future generation)

| Profile | Sites | Devices (approx.) | Interfaces | Duration | Purpose |
|---------|-------|-------------------|------------|----------|---------|
| `small_branch` | 1–3 | 15–40 | 200–800 | 14–30 days | Unit tests, few-shot |
| `campus_medium` | 1–2 | 80–200 | 2k–8k | 90 days | Primary campus ML |
| `dc_evpn` | 1 DC | 40–120 | 1k–5k | 60–90 days | Overlay / leaf-spine |
| `enterprise_large` | 10–50 | 500–3000 | 20k–100k | 180 days | Scale stress |
| `hybrid_multi` | campus+DC+branch | mixed | mixed | 180 days | Cross-topology transfer |

Schema must support all profiles without NULLing critical keys; optional overlay tables empty when EVPN unused.

---

## 5. Identifier and naming rules

- Primary keys: `UUID` (UUIDv7 recommended)  
- Natural keys retained: `hostname`, `interface_name` (`1/1/1`, `lag1`, `vlan10`), `vlan_id`, `vni`  
- Soft deletes: `valid_from`, `valid_to` on inventory entities that can be decommissioned  
- Snapshot keys: `(device_id, snapshot_at)` or `(topology_id, snapshot_at)`  

---

## 6. Data quality dimensions (to be enforced at generation time)

1. **Referential integrity** across FKs  
2. **Temporal integrity**: counter timestamps monotonic per `(device, interface)` series  
3. **Causal integrity**: failure onset ≤ detection ≤ recovery start ≤ recovery end (when recovery occurs)  
4. **Topological integrity**: link endpoints exist and share compatible speed/MTU at snapshot time  
5. **Config–state consistency**: admin-down interface cannot show non-zero *live* oper-up traffic without an explicit flap event window  
6. **Statistical realism**: diurnal traffic, heavy-tailed flow sizes, rare multi-fault concurrency  

---

## 7. Privacy and ethics (dataset paper requirements)

Even when synthetic:

- No real MAC/IP/user identifiers from production  
- Pseudonymous `user_id` / `endpoint_id`  
- Document that generation is synthetic and must not be presented as raw production telemetry  
- If a future release includes scrubbed real traces, publish IRB/legal and anonymization method

---

## 8. Deliverable for reviewers

A standalone dataset paper should include:

1. Gap analysis (L01)  
2. Schema + graph model (this folder + 03/04)  
3. Failure taxonomy with observability mapping (F01)  
4. Label definitions (LBL01)  
5. Benchmark protocol + baselines (B01)  
6. Comparative table vs prior datasets (B02)  
7. Datasheet for datasets / dataset nutrition label appendix  
8. (Later) generation code + checksums + license
