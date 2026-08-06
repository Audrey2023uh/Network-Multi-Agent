# L01 — Literature Review and Gap Analysis

**Document role:** Ground ECNetBench in prior public datasets and published network-management / digital-twin research. Every subsequent schema choice must address a documented gap.

---

## 1. Scope of the review

We surveyed public artifacts used for:

1. **Enterprise / ISP telemetry and anomaly detection**  
2. **Topology and traffic engineering graphs**  
3. **Intrusion / security flow datasets** (often misused as “network management” benchmarks)  
4. **Configuration and intent / LLM networking benchmarks**  
5. **Root-cause analysis and NetOps agent benchmarks**  
6. **Digital twin enabling literature** (dataset requirements, not always public data)

Sources include peer-reviewed papers, IEEE DataPort / institutional releases, and maintained GitHub research artifacts current as of mid-2026.

---

## 2. Dataset families and what they provide

### 2.1 Telemetry-centric operational datasets

| Dataset | Domain | What it contains | Labels | Topology | Config | Recovery |
|---------|--------|------------------|--------|----------|--------|----------|
| **Cisco IE Telemetry** (cisco-ie/telemetry; BigDama’18 / INFOCOM demos) | DC Clos / testbed | Interface counters, BGP/BFD-related signals, CPU, topology docs | Event/case files for induced anomalies (BGP clear, port flap, transceiver pull, admin shut) | Yes (Clos maps, CDP GT) | Limited / scenario-level | Implicit (event end), not structured recovery actions |
| **ClosRCA-Bench** | DC Clos derived from Cisco IE | Graph windows (11 nodes × 30 features × 6 steps), cause/target labels | Anomaly, cause family, target device; remediation validation hooks | Fixed Clos | No full config snapshots | Counterfactual remediation *evaluation*, not enterprise multi-layer recovery logs |
| **CESNET-TimeSeries24** | ISP / NREN | 40 weeks IP-level aggregates (10 min / 1 h / 1 day) from ~66B flows | Anomaly-rich ISP traffic (detection/forecasting) | Institutional / subnet aggregates, not L2/L3 enterprise fabric | No | No |
| **CAIDA anonymized traces** | Backbone | Packet headers / passive traces | Traffic characterization; not ops failures | Link-level capture points | No | No |

**Scientific takeaway:** Strong for *counter / flow time series*, weak for *enterprise multi-layer configuration causality*, *service impact*, and *structured recovery*.

### 2.2 Topology-only datasets

| Dataset | Contents | Limitation for cognitive networking |
|---------|----------|-------------------------------------|
| **Internet Topology Zoo** | ~250 ISP/enterprise *logical* maps (GraphML/GML) | Static graphs; little/no telemetry, no failures, outdated refresh |
| **SNDlib** | Traffic matrices + topologies for TE | Optimization-oriented; not ops telemetry or config drift |
| **Topology Bench** (optical core) | Homogenized optical graphs with spatial attributes | Optical core, not campus/DC switching with VLANs/ACLs/QoS |

**Scientific takeaway:** Topology Zoo-style graphs support structural ML but cannot train failure prediction that depends on interface state, ACL semantics, or QoS queues.

### 2.3 Security / IDS datasets (frequently cited, often the wrong task)

| Dataset | Contents | Why insufficient for enterprise cognitive networking |
|---------|----------|------------------------------------------------------|
| **UNSW-NB15** | Hybrid normal + synthetic attacks, 49 features | Security classification; no enterprise L2/L3 control-plane ops model |
| **CIC-IDS2017 / CIC-IDS2018** | Labeled attack flows | Same; statistical gap vs real traffic documented in “Benchmarking the Benchmark” style studies |
| **ToN-IoT** | IoT telemetry + OS logs + network | IIoT security; not Aruba-class campus/DC switching ops |

**Scientific takeaway:** These datasets optimize *attack detection*, not *network management intelligence* (config risk, VSX peer loss, VLAN mismatch, QoS starvation, STP loops).

### 2.4 Configuration and LLM/NetOps benchmarks

| Dataset / bench | Contents | Gap |
|-----------------|----------|-----|
| **NetConfEval** | NL → formal policy / API / FRR configs | Configuration *generation*, not longitudinal telemetry + failure labels |
| **NetOpsBench** | Interactive SONiC-VS faults, agent traces | Excellent for *agent* troubleshooting; not a multi-month multi-table enterprise warehouse with users/apps/QoS/VSX/EVPN campus realism |
| **NIKA** (troubleshooting reasoning traces) | Incident reasoning traces | Trace-centric; not a full observational data warehouse |

### 2.5 Digital twin literature (dataset requirements)

Ruiz et al. and related IEEE Communications Magazine / digital-twin surveys emphasize that twin fidelity requires:

- Diverse topologies and traffic profiles  
- Edge cases (failures, misconfigurations, congestion) that are unethical/impractical to induce in production  
- Generalization to *unseen* customer topologies  

**Implication for ECNetBench:** The dataset must be *multi-topology*, *multi-fault-family*, *config-aware*, and include *explicit train/test topology hold-outs*.

---

## 3. Cross-cutting limitations of existing public data

| Gap ID | Limitation | Why it blocks top-tier cognitive networking research |
|--------|------------|------------------------------------------------------|
| G1 | **Single modality dominance** (flows *or* counters *or* topology) | Cognitive networking needs fused observability (config + telemetry + events + services) |
| G2 | **Missing configuration semantics** (ACL, VLAN, QoS, LAG, VSX, EVPN) | Most “ops” failures in enterprises are config/intent mismatches, not only link downs |
| G3 | **Weak or absent service / user / application layer** | Impact prediction requires blast radius to business services, not only device CPU |
| G4 | **Sparse failure taxonomies** | Cisco IE / ClosRCA cover few cause families; campus STP/VLAN/ACL/auth failures absent |
| G5 | **No structured recovery actions** | Autonomous management needs (action, duration, success, downtime) as first-class labels |
| G6 | **No temporal train/test discipline published as community protocol** | Random IID splits leak future information in time series |
| G7 | **DC Clos bias** | Enterprise cognitive networking includes campus, branch, WLAN AP, VSX pairs, EVPN overlays |
| G8 | **Vendor-agnostic but standards-loose schemas** | Hard to map to OpenConfig/YANG, IPFIX IEs, syslog facilities, REST resources used in real ops |
| G9 | **Explainability-hostile feature dumps** | Flat CSVs without entity lineage hinder XAI (which interface, which ACL ACE, which VTEP) |
| G10 | **Digital twin incompleteness** | Without config snapshots + topology versions + traffic, twins cannot replay counterfactuals |

---

## 4. How ECNetBench addresses each gap

| Gap | ECNetBench mechanism |
|-----|----------------------|
| G1 | Multi-domain relational warehouse + property graph projection (inventory, config, telemetry, events, flows, services) |
| G2 | First-class tables for VLAN, ACL/ACE, QoS class/queue, LAG, VSX, EVPN/VXLAN, routing instances, STP |
| G3 | `user`, `endpoint`, `application`, `service`, `service_dependency`, SLA and degradation labels |
| G4 | ≥12 failure families with subtypes (interface, cable, congestion, routing instability, ACL misconfig, VLAN mismatch, STP loop, firmware incompatibility, QoS, auth, hardware degradation, power, intermittent) |
| G5 | `failure_incident`, `recovery_action`, detection/recovery timestamps, success, downtime, affected services |
| G6 | Published protocol: temporal freeze, rolling origin, topology hold-out, metrics suite |
| G7 | Campus + DC + branch + hybrid topologies with APs and wired access |
| G8 | Attribute alignment to OpenConfig paths, AOS-CX REST/NAE, IPFIX, syslog semantics, SNMP MIB *concepts* |
| G9 | Entity-keyed observations + incident→entity evidence links for XAI |
| G10 | Versioned `config_snapshot` + `topology_snapshot` + time-aligned telemetry for twin replay |

---

## 5. Novelty claim (for a standalone dataset paper)

ECNetBench is novel as a **community benchmark architecture** because it jointly provides:

1. An **enterprise-realistic multi-layer schema** grounded in AOS-CX / OpenConfig / IPFIX / syslog practices;  
2. A **graph + relational dual representation** suitable for GNNs and classical ML;  
3. A **failure–detection–recovery–impact** causal chain with supervised targets spanning anomaly detection, failure prediction, RCA, impact, service degradation, and configuration risk;  
4. A **reproducible evaluation protocol** with temporal and cross-topology validation—explicitly required by digital-twin generalization arguments;  
5. Separation of **design (this release)** from **instance generation**, enabling peer review of scientific validity before synthetic sampling biases enter the literature.

No existing public dataset simultaneously covers campus/DC enterprise switching features (VLAN/ACL/QoS/LAG/VSX/EVPN), multi-modal telemetry, service impact, and structured recovery at publication-benchmark depth.

---

## 6. Related work positioning (paper outline fragment)

**Positioning sentence for IEEE TNSM / Computer Networks:**

> Unlike intrusion-detection corpora (UNSW-NB15, CIC-IDS, ToN-IoT), topology archives (Topology Zoo, SNDlib), ISP aggregate series (CESNET-TimeSeries24), and Clos telemetry benchmarks (Cisco IE Telemetry, ClosRCA-Bench), ECNetBench targets *enterprise cognitive networking* by releasing a standards-aligned, multi-topology, config-aware observational model with explicit failure–recovery–impact labels and a temporal/cross-topology benchmark protocol suitable for digital twins and autonomous network management.

---

## 7. Key references (indicative; expand in camera-ready BibTeX)

1. Cisco IE Telemetry datasets — anomaly ML for network telemetry (BigDama / community release).  
2. ClosRCA-Bench — topology-grounded RCA + remediation validation.  
3. CESNET-TimeSeries24 — long-horizon ISP IP time series.  
4. CAIDA anonymized passive traces — backbone traffic realism.  
5. Internet Topology Zoo (Knight et al., IEEE JSAC 2011).  
6. SNDlib — TE topologies and matrices.  
7. Topology Bench — homogenized optical topologies.  
8. UNSW-NB15; CIC-IDS2017; ToN-IoT — security corpora and known generalization critiques.  
9. NetConfEval (ACM) — LLM configuration benchmarks.  
10. NetOpsBench — agentic NetOps interactive faults.  
11. Network digital twin surveys (e.g., IEEE Commun. Mag. digital twin context papers) — dataset requirements for generalization.  
12. HPE Aruba AOS-CX Monitoring / NAE / IPFIX / gNMI OpenConfig documentation — operational ground truth for schema realism.  
13. OpenConfig public YANG models; RFC 7011 (IPFIX); relevant SNMP MIB conceptual mappings (IF-MIB, HOST-RESOURCES, ENTITY-SENSOR).  

---

## 8. Review conclusions that constrain schema design

1. Prefer **entity-normalized tables** over opaque feature matrices ( ClosRCA-style windows can be *derived views*).  
2. Every fault family must have **observable precursors** in telemetry/events/config diffs (scientific falsifiability).  
3. Recovery must be **action-typed** and linked to incidents (enables autonomous management benchmarks).  
4. Topology must be **versioned in time** (links appear/disappear; VSX roles change).  
5. Do **not** invent fields without OpenConfig/AOS-CX/IPFIX/syslog/ops rationale (see `08_standards` and attribute catalog).
