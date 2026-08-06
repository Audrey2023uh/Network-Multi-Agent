# Comparison with Public Network Datasets & Enterprise Behavior

## Public datasets (qualitative)

| Dataset | Domain | Labels | Topology | Gaps vs ECNetBench |
|---|---|---|---|---|
| MAWI / CAIDA traces | Backbone PCAP | Rarely failure GT | No enterprise L2/L3 inventory | No RCA/incident GT; no device telemetry |
| UGR'16 / CIDDS | NetFlow/IDS | Attack labels | Limited enterprise config | Security-centric; weak control-plane/STP/VSX |
| TON_IoT / CIC IDS | Host+net attacks | Attack taxonomy | Lab IoT | Not campus switching/routing ops |
| METIS / topology zoos | Graphs | None/ops rare | AS/PoP | No telemetry time series |
| Kabsch / datacenter traces (public subsets) | DC traffic | Sparse | Clos-like | Not Aruba campus+branch+VSX |

**ECNetBench niche:** multi-table enterprise ops state (inventory, STP/BGP/VSX, telemetry, incidents, service impact, graph, ML labels) under one seed — scarce in public releases.

## Documented enterprise behavior alignment (checklist)

| Behavior | Present in v1.1? | Notes |
|---|---|---|
| Business-hour traffic/CPU lift | Yes | Supported by statistical validation diurnal checks |
| Heavy-tailed flow sizes | Yes | High skew in ipfix |
| Imperfect monitoring (FN/FP alerts) | Yes | Alerts ≠ incidents 1:1 |
| Syslog bursts on failure | Yes | Multi-message onset/recovery |
| Redundant L2 with blocking ports | Yes | STP alternate/blocking |
| BGP session non-stability during routing incidents | Yes | Temporal BGP samples |
| VSX split-brain state | Yes | vsx_state_sample=split |
| Poll loss / delay | Yes | Dropped/delayed samples |
| Change-induced incidents linked to diffs | Partial | Subset change_induced |
| Multi-vendor mix | No | Aruba-centric synthetic |
| Months-long seasonal drift | No | 14-day window |
| Real ticket/chat ops noise | No | Not modeled |

## Implication for publication

Position as a **synthetic benchmark filling the enterprise multi-layer GT gap**, not as a substitute for production traces. Compare baselines against public IDS/flow sets only at task granularity (e.g., rare-event AP), not absolute topology realism.
