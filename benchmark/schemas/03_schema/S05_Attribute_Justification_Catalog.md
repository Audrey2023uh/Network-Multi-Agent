# S05 — Attribute Justification Catalog (by family)

This catalog explains **why field families exist**. Individual columns inherit the family justification unless noted in S01–S04.

Justification triad (required for dataset paper):

1. **Scientific motivation** — what research question / causal claim needs it  
2. **Networking motivation** — how operators / standards use it  
3. **ML usefulness** — feature, label precursor, graph attribute, or evaluation weight  

---

## Family F01 — Identity & inventory keys (`*_id`, hostname, serial)

| Scientific | Networking | ML |
|------------|------------|-----|
| Reproducible joins; entity-centric learning; XAI lineage | Asset management, change control | Entity embeddings; multi-task heads per device class |

## Family F02 — Spatial hierarchy (site/building/floor/rack)

| Scientific | Networking | ML |
|------------|------------|-----|
| Spatial correlation of power/cooling faults; multi-site generalization | DCIM / campus ops | Hierarchical models; site hold-out splits |

## Family F03 — Device role & platform

| Scientific | Networking | ML |
|------------|------------|-----|
| Heterogeneous graph learning; transfer across roles | Clos/campus design roles | Role one-hots; platform-conditioned failure rates |

## Family F04 — Firmware versions & compatibility

| Scientific | Networking | ML |
|------------|------------|-----|
| Config/firmware risk as causal factor | VSX/ISL & feature compatibility matrices | Config risk labels; change-impact models |

## Family F05 — Hardware components (PSU/fan/optic)

| Scientific | Networking | ML |
|------------|------------|-----|
| Degradation trajectories; competing risks | RMA / hardware monitoring | Survival analysis; sensor time series |

## Family F06 — Interface state & counters

| Scientific | Networking | ML |
|------------|------------|-----|
| Primary observability for link health (Cisco IE, ClosRCA) | OpenConfig/IF-MIB ops | Anomaly detection; failure prediction; congestion |

## Family F07 — LAG / LACP / MCLAG

| Scientific | Networking | ML |
|------------|------------|-----|
| Partial redundancy failures ≠ single link down | Enterprise dual-homing | Multi-label degradation severity |

## Family F08 — VSX pair state

| Scientific | Networking | ML |
|------------|------------|-----|
| Split-brain / sync loss unique to Aruba-class HA | VSX operational model | RCA localization to ISL vs keepalive vs member |

## Family F09 — VLAN membership & tagging

| Scientific | Networking | ML |
|------------|------------|-----|
| Misconfig causality common in campus outages | Access/trunk design | Config risk; VLAN mismatch classification |

## Family F10 — EVPN/VXLAN/VTEP/ESI

| Scientific | Networking | ML |
|------------|------------|-----|
| Overlay control-plane faults understudied in public sets | Modern DC fabric | Overlay vs underlay disentanglement in RCA |

## Family F11 — Routing neighbors & BFD

| Scientific | Networking | ML |
|------------|------------|-----|
| Instability / blackhole mechanisms | BGP/OSPF/BFD ops | Sequence models on session state transitions |

## Family F12 — ACL / ACE / bindings

| Scientific | Networking | ML |
|------------|------------|-----|
| Policy errors as first-class outages | Security & segmentation | Graph-of-rules risk; hit-count features |

## Family F13 — QoS classes / queues / drops

| Scientific | Networking | ML |
|------------|------------|-----|
| Application-aware degradation | DiffServ / queueing | Service degradation prediction |

## Family F14 — STP roles/states

| Scientific | Networking | ML |
|------------|------------|-----|
| Loop / topology-change dynamics | L2 loop prevention | Rare-event detection; CPU correlation |

## Family F15 — AAA / RADIUS

| Scientific | Networking | ML |
|------------|------------|-----|
| Auth outages ≠ forwarding outages | Campus NAC | Separate failure family; user impact labels |

## Family F16 — Config snapshots & diffs

| Scientific | Networking | ML |
|------------|------------|-----|
| Twin replay; change-induced incidents | Change management | Config risk; causal inference on diffs |

## Family F17 — CPU / memory / sensors / power

| Scientific | Networking | ML |
|------------|------------|-----|
| Resource exhaustion & environmental causes | Platform health | Multivariate forecasting; early warning |

## Family F18 — NAE monitors & series

| Scientific | Networking | ML |
|------------|------------|-----|
| On-box analytics as intermediate representations | AOS-CX NAE | Distillation targets; alert generation studies |

## Family F19 — Syslog / alerts

| Scientific | Networking | ML |
|------------|------------|-----|
| Discrete event sequences for RCA | NOC workflows | NLP/log models; detection latency metrics |

## Family F20 — IPFIX flows & drop reasons

| Scientific | Networking | ML |
|------------|------------|-----|
| Demand matrix; ACL/QoS drop evidence | IPFIX collectors | Traffic forecasting; explainable drop attribution |

## Family F21 — Users / endpoints / apps / services / SLA

| Scientific | Networking | ML |
|------------|------------|-----|
| Business impact & degradation outcomes | ITSM / service mapping | Impact prediction; cost-sensitive learning |

## Family F22 — Incidents / recovery / downtime

| Scientific | Networking | ML |
|------------|------------|-----|
| Supervised GT for autonomous management | Runbooks | RL/IL targets; recovery success classification |

## Family F23 — Graph projections

| Scientific | Networking | ML |
|------------|------------|-----|
| Topology-aware learning & twin state | LLDP maps | GNN node/edge tasks; cross-topology tests |

## Family F24 — API responses

| Scientific | Networking | ML |
|------------|------------|-----|
| Management-plane health; agent tool realism | REST/gNMI | Agent benchmarks; mgmt failure precursors |

---

## Fields explicitly rejected (and why)

| Tempting field | Why rejected |
|----------------|--------------|
| Arbitrary “AI confidence” on devices | Not collected from networks; circular for ML |
| Fake GPS per packet | Not enterprise switching telemetry |
| Payload / user content | Privacy; not needed for cognitive networking ops |
| Unlimited full FIB every second | Unrealistic export volume; use sampled RIB/FIB |
| Vendor-secret undocumented counters without public semantics | Breaks independent reproducibility |

Only add new attributes if they map to OpenConfig/AOS-CX/IPFIX/syslog/ops practice or a cited measurement study.
