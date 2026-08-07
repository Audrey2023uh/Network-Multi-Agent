# ECNetBench Schema Realism Mapping

Comparison of generated entities/telemetry against public vendor and standards documentation.
No proprietary enterprise traces were used.

| ECNetBench field / entity | Realistic counterpart | Source class |
|---------------------------|----------------------|--------------|
| `device`, role (core/agg/access/wan/ap) | Campus/DC switch/AP inventory roles | Aruba AOS-CX, Cisco Catalyst/Nexus role practice |
| `interface`, VLAN membership, LAG | Interface + VLAN/trunk/LAG config | AOS-CX VLAN/LAG; OpenConfig `interfaces`, `vlan` |
| ACL / QoS policy tables | ACL entries, QoS classes/queues | AOS-CX ACL/QoS; OpenConfig `acl`, `qos` |
| BGP/OSPF/BFD session samples | Control-plane neighbor state | AOS-CX routing; OpenConfig `network-instance` |
| `if_counter_sample` (errors, discards, carrier) | Interface counters / IF-MIB style | AOS-CX show interface counters; OpenConfig interface counters |
| `device_resource_sample` (CPU/mem) | Control-plane resource telemetry | AOS-CX system resource; Cisco `process cpu` |
| Syslog / alert streams | Syslog severity + NAE-like alerts | Aruba NAE; RFC5424 syslog practice |
| Flow aggregates / IPFIX-like | Flow export aggregates | IPFIX/NetFlow operational practice |
| Config snapshot / diff | Running-config archive + diff | AOS-CX checkpoint/config; Cisco archive |
| NAE script/monitor analogues | On-switch analytics agents | Aruba Network Analytics Engine docs |
| Failure incident + recovery action | Incident/RCA/remediation tickets | NetOps / ITSM practice (abstracted) |
| Service / SLA / impact labels | Service dependency + impact | Enterprise assurance models; OpenTelemetry resource semantics (loose) |

## Notes

- ECNetBench is **synthetic** but field names and causal chains are aligned to public documentation concepts.
- OpenTelemetry is mapped at the semantic level (resources, metrics), not as a wire protocol in the SQLite store.
- This mapping supports external realism claims without claiming bit-identical vendor schemas.
