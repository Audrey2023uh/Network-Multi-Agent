# ECNetBench: Enterprise Cognitive Networking Benchmark Dataset

**Version:** 1.0.0-INST (specification + first constrained instance)  
**Target venues:** IEEE TNSM, Computer Networks, IEEE Network (dataset / systems paper track)  
**Infrastructure alignment:** HPE Aruba AOS-CX, Aruba Central, Network Analytics Engine (NAE), OpenConfig/YANG, IPFIX, syslog, REST  
**Status:** Design complete; instance v1 exported under `09_artifacts/instances/v1/`

---

## Purpose

ECNetBench is designed as a community-adoptable benchmark for enterprise **cognitive networking**: predictive analytics, digital twins, explainable AI, root-cause analysis, configuration risk assessment, and autonomous network management.

This repository currently contains the **complete design**: literature gaps, entity–relationship schema, graph model, temporal semantics, failure/recovery taxonomy, supervised labels, benchmark protocol, and standards alignment. **Synthetic data generation is intentionally deferred** until the schema and causal constraints are frozen.

---

## Document map

| Path | Contents |
|------|----------|
| [`01_literature/L01_Literature_Review_and_Gap_Analysis.md`](01_literature/L01_Literature_Review_and_Gap_Analysis.md) | Survey of public datasets; limitations; novelty claims |
| [`02_architecture/A01_Design_Principles_and_Overview.md`](02_architecture/A01_Design_Principles_and_Overview.md) | Design principles, scope, multi-site enterprise model |
| [`02_architecture/A02_Entity_Relationship_Overview.md`](02_architecture/A02_Entity_Relationship_Overview.md) | ER overview, domains, cardinality |
| [`03_schema/S01_Inventory_and_Topology_Tables.md`](03_schema/S01_Inventory_and_Topology_Tables.md) | Devices, sites, racks, interfaces, links, VLANs, LAGs, VSX, EVPN/VXLAN |
| [`03_schema/S02_Configuration_Tables.md`](03_schema/S02_Configuration_Tables.md) | Snapshots, routing, ACL, QoS, AAA, STP, firmware |
| [`03_schema/S03_Telemetry_and_Counters.md`](03_schema/S03_Telemetry_and_Counters.md) | Interface/CPU/memory/temp/power counters; NAE; API |
| [`03_schema/S04_Events_Flows_Services.md`](03_schema/S04_Events_Flows_Services.md) | Syslog, alerts, IPFIX, users, endpoints, apps, services |
| [`03_schema/S05_Attribute_Justification_Catalog.md`](03_schema/S05_Attribute_Justification_Catalog.md) | Scientific / networking / ML motivation per attribute family |
| [`04_graph_model/G01_Network_Graph_Specification.md`](04_graph_model/G01_Network_Graph_Specification.md) | Node types, edge types, dynamic graphs |
| [`04_graph_model/G02_Temporal_Model.md`](04_graph_model/G02_Temporal_Model.md) | Timestamps, cadences, causality windows |
| [`05_failures/F01_Failure_and_Recovery_Taxonomy.md`](05_failures/F01_Failure_and_Recovery_Taxonomy.md) | Failure categories, detection, recovery, downtime |
| [`06_labels/LBL01_Supervised_Learning_Targets.md`](06_labels/LBL01_Supervised_Learning_Targets.md) | Labels for AD, FP, RCA, impact, degradation, config risk |
| [`07_benchmark/B01_Benchmark_Protocol.md`](07_benchmark/B01_Benchmark_Protocol.md) | Splits, temporal/cross-topology validation, metrics |
| [`07_benchmark/B02_Comparative_Evaluation.md`](07_benchmark/B02_Comparative_Evaluation.md) | ECNetBench vs existing public datasets |
| [`08_standards/ST01_Standards_Alignment.md`](08_standards/ST01_Standards_Alignment.md) | OpenConfig, SNMP MIB concepts, IPFIX, AOS-CX REST/NAE |
| [`09_artifacts/DDL_postgresql.sql`](09_artifacts/DDL_postgresql.sql) | Reference PostgreSQL DDL |
| [`09_artifacts/graph_schema.json`](09_artifacts/graph_schema.json) | Machine-readable graph type system |
| [`09_artifacts/label_schema.json`](09_artifacts/label_schema.json) | Machine-readable label definitions |
| [`09_artifacts/generation_constraints.md`](09_artifacts/generation_constraints.md) | Rules for *future* synthetic generation (no data yet) |

---

## Naming convention

- **Dataset short name:** `ECNetBench`
- **Dataset full name:** Enterprise Cognitive Networking Benchmark
- **Topology instances:** `topo_campus_*`, `topo_datacenter_*`, `topo_branch_*`, `topo_hybrid_*`
- **Time zone:** all timestamps stored as UTC (`timestamptz`); local site TZ recorded in `site.timezone`
- **Identifiers:** UUIDv7 preferred for time-sortable primary keys; human-readable `*_name` fields retained for operator interpretability

---

## What is intentionally *not* included yet

- No synthetic CSV/Parquet instances  
- No trained models  
- No privacy-scrubbed production dumps  

Generation must follow [`09_artifacts/generation_constraints.md`](09_artifacts/generation_constraints.md) so that temporal, causal, and topological consistency are preserved.

---

## Suggested citation skeleton (pre-publication)

> Authors (Year). *ECNetBench: A Benchmark Dataset Architecture for Enterprise Cognitive Networking*. Specification v1.0.0-SPEC.

---

## Change log

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0-SPEC | 2026-08-06 | Initial complete architecture; literature review; full schema; benchmark protocol |
