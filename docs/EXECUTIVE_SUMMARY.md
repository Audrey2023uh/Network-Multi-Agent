# ECNetBench — Executive Specification Summary (for dataset paper drafting)

**Dataset:** ECNetBench (Enterprise Cognitive Networking Benchmark)  
**Release type:** Architecture / schema / protocol only (`1.0.0-SPEC`)  
**Synthetic instances:** not generated (by design)

---

## One-paragraph abstract draft

Enterprise cognitive networking research—predictive analytics, digital twins, explainable RCA, and autonomous remediation—lacks a community benchmark that jointly provides realistic multi-layer configuration semantics, multi-modal telemetry, service-level impact, and structured recovery labels under a temporal and cross-topology evaluation protocol. Existing public resources fragment these needs across topology archives (Topology Zoo, SNDlib), ISP aggregates (CESNET-TimeSeries24), Clos telemetry/RCA artifacts (Cisco IE Telemetry, ClosRCA-Bench), security flow corpora (UNSW-NB15, CIC-IDS, ToN-IoT), and interactive NetOps environments (NetOpsBench). ECNetBench specifies a standards-aligned, Aruba AOS-CX–realistic relational + graph dataset architecture covering inventory, VLAN/ACL/QoS/LAG/VSX/EVPN, routing, configuration snapshots, counters, NAE analytics, syslog/alerts, IPFIX, users/applications/services, and a failure–detection–recovery–impact causal chain with six supervised task families and a normative benchmark protocol suitable for a standalone top-tier dataset paper.

---

## Contributions (C1–C5)

1. **Gap-driven multi-domain schema** for enterprise cognitive networking.  
2. **Typed network graph** with underlay/overlay/policy/service node and edge types.  
3. **Failure taxonomy (≥13 families)** with mandatory detection/recovery/impact fields.  
4. **Six ML task label definitions** with leakage rules.  
5. **Benchmark protocol** (temporal freeze, rolling-origin, cross-topology) + comparison matrix.

---

## Minimal paper outline

1. Introduction & motivation (cognitive networking / digital twins)  
2. Related datasets & limitations (L01)  
3. Design principles & enterprise scope (A01)  
4. Schema & standards alignment (S01–S04, ST01)  
5. Graph & temporal model (G01–G02)  
6. Failure/recovery taxonomy (F01)  
7. Tasks & labels (LBL01)  
8. Benchmark protocol & baselines (B01)  
9. Comparative evaluation (B02)  
10. Limitations, ethics, future instance release  
11. Conclusion  

---

## Absolute path root

`C:\Users\audre\OneDrive\Network_Journal\Data`

Start at `00_README.md`.
