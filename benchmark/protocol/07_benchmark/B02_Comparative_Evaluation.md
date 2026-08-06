# B02 — Comparative Evaluation vs Existing Public Datasets

## 1. Capability matrix

Legend: ● full | ◐ partial | ○ absent

| Capability | Topology Zoo / SNDlib | CAIDA traces | UNSW/CIC/ToN | CESNET-TS24 | Cisco IE Telemetry | ClosRCA-Bench | NetConfEval | NetOpsBench | **ECNetBench (design)** |
|------------|----------------------|--------------|--------------|-------------|--------------------|---------------|-------------|-------------|-------------------------|
| Enterprise campus+DC+branch | ◐/○ | ○ | ○ | ○ | ◐ DC | ○ DC Clos | ○ | ◐ lab | **●** |
| Time-series counters | ○ | ○ | ○ | ● | ● | ● (windowed) | ○ | ◐ live | **●** |
| Flow/IPFIX | ○ | ◐ pkt | ● flows (sec) | ● agg | ○ | ○ | ○ | ◐ | **●** |
| Syslog/alerts | ○ | ○ | ◐ | ○ | ◐ | ○ | ○ | ● | **●** |
| Config snapshots + diffs | ○ | ○ | ○ | ○ | ◐ | ○ | ● gen | ◐ | **●** |
| VLAN/ACL/QoS/STP | ○ | ○ | ○ | ○ | ○ | ○ | ◐ | ◐ | **●** |
| LAG/VSX/EVPN | ○ | ○ | ○ | ○ | ◐ | ◐ | ○ | ◐ | **●** |
| Users/apps/services/SLA | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | **●** |
| Rich failure taxonomy (≥10) | ○ | ○ | ◐ attacks | ◐ | ◐ few | ◐ 4 | ○ | ● faults | **●** |
| Structured recovery actions | ○ | ○ | ○ | ○ | ○ | ◐ counterfactual | ○ | ◐ | **●** |
| Impact / downtime labels | ○ | ○ | ○ | ○ | ○ | ◐ | ○ | ◐ | **●** |
| Graph + relational dual | ● graph | ○ | ○ | ○ | ◐ | ● | ○ | ◐ | **●** |
| Temporal split protocol | ○ | ○ | ◐ | ◐ | ◐ | ● | ○ | ● | **●** |
| Cross-topology protocol | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ◐ scale | **●** |
| OpenConfig/IPFIX/AOS-CX alignment | ○ | ○ | ○ | ○ | vendor tele | vendor tele | FRR | SONiC | **● Aruba-class** |
| Digital twin replay readiness | ○ | ○ | ○ | ○ | ◐ | ● | ○ | ● interactive | **●** |
| XAI entity lineage | ○ | ○ | ○ | ○ | ◐ | ● | ○ | ● | **●** |

---

## 2. What is missing in existing datasets (synthesis)

1. **No public enterprise multi-layer ops warehouse** combining config semantics (ACL/VLAN/QoS/VSX/EVPN) with multi-modal telemetry and service impact.  
2. **Security corpora dominate “network ML”** but answer intrusion questions, not cognitive network management.  
3. **Clos telemetry advances RCA** but underrepresent campus failure modes (STP, VLAN mismatch, AAA, WLAN).  
4. **Topology archives lack dynamics**; **flow archives lack control-plane state**.  
5. **Recovery is rarely a first-class labeled object**, blocking autonomous management evaluation.  
6. **Cross-topology generalization** is discussed in digital-twin literature but seldom enforced as a dataset protocol.

---

## 3. What ECNetBench contributes

1. A **publication-grade schema** realistic for HPE Aruba AOS-CX enterprise estates.  
2. A **failure–detection–recovery–impact causal chain** with ML targets spanning six core tasks.  
3. A **graph type system** covering underlay, overlay, policy, and service nodes/edges.  
4. A **benchmark protocol** with temporal and cross-topology validation.  
5. Explicit **standards alignment** so independent researchers can trust technical realism.  
6. A **spec-first** release strategy reducing synthetic-data confounds before instance publication.

---

## 4. Why this is research novelty (dataset paper thesis)

Novelty is not “another anomaly CSV.” Novelty is a **community benchmark architecture** that makes enterprise cognitive networking results **comparable**, **topology-general**, and **operationally meaningful** (services, recovery, config risk)—a combination absent from Topology Zoo, CESNET-TS24, Cisco IE Telemetry/ClosRCA, IDS corpora, and LLM config benchmarks.

---

## 5. Threats to validity (must discuss in paper)

- Synthetic generation may still understate long-tail ops chaos → mitigate with constraints doc + optional future scrubbed real traces  
- Aruba-centric realism may not transfer to all vendors → mitigate via OpenConfig-aligned attributes  
- Label oracle bias → publish precursor rules and allow hidden-target slices  
- Scale vs fidelity tradeoff → multiple topology profiles
