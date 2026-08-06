# ST01 — Standards and Platform Alignment

ECNetBench attributes are chosen to map to real collection mechanisms. This document is the realism contract.

---

## 1. OpenConfig / YANG / gNMI

| Dataset concept | OpenConfig-aligned path / model family |
|-----------------|------------------------------------------|
| Interface admin/oper/speed/counters | `openconfig-interfaces` `/interfaces/interface/...` |
| Ethernet / FEC / optics (where modeled) | `openconfig-if-ethernet`, platform optics |
| CPU / memory | `openconfig-system` CPU & memory |
| Components (PSU, fan, linecard) | `openconfig-platform` |
| Network instance / VRF | `openconfig-network-instance` |
| BGP neighbors / AFI-SAFI | `openconfig-bgp` |
| ACL | `openconfig-acl` |
| QoS | `openconfig-qos` |
| LLDP adjacency (link discovery) | `openconfig-lldp` |
| System config | `openconfig-system` |

AOS-CX exposes OpenConfig via gNMI; Aruba publishes YANG packaging (`aruba/aoscx-yang`) with deviations — ECNetBench stores **logical** fields, not raw YANG only, so deviations do not break the schema.

---

## 2. SNMP MIB *concepts* (legacy collectors)

| Dataset field family | MIB concept |
|----------------------|-------------|
| `if_index`, counters | IF-MIB |
| Entity serial/model | ENTITY-MIB |
| Sensors | ENTITY-SENSOR-MIB |
| Basic host CPU/mem | HOST-RESOURCES-MIB (approx.) |

SNMP is not required for generation, but field semantics remain compatible for hybrid collection papers.

---

## 3. IPFIX (RFC 7011) and AOS-CX flow features

| Dataset column | IPFIX IE concept |
|----------------|------------------|
| src/dst addr, ports, proto | standard 5-tuple IEs |
| packet/byte counters | |
| ingress/egress ifIndex | interface mapping |
| tcpFlags, ipDiffServCodePoint | |
| forwarding status | drop vs forward |
| `drop_reason_codes` | AOS-CX augmented private IEs (document as vendor-aligned, 1200–1233 concept) |

---

## 4. Syslog (RFC 5424) + Aruba CX operational categories

Mapped `app_name` / facilities should cover:

- AAA / auth  
- ACL hits / denials (when logged)  
- BGP / OSPF / BFD  
- LACP / VSX  
- EVPN / VXLAN  
- Hardware / PSU / fan / temperature  
- Port security / storm control  
- Configuration / REST API audit  

Elastic’s HPE Aruba CX integration field list is a useful external checklist for event categories (without copying proprietary schemas wholesale).

---

## 5. AOS-CX REST + NAE

| Dataset table | Platform analog |
|---------------|-----------------|
| `config_snapshot.structured_config` | REST GET of system resources |
| `api_response_archive` | REST/gNMI latency & payloads |
| `nae_script/agent/monitor` | NAE script lifecycle |
| `nae_timeseries_point` | `/system/nae_scripts/.../time_series/{type}` aggregators (`Raw`,`Rate`,`Average`,…) |

Official NAE script themes (BGP, OSPF, EVPN, link health, hardware, security) motivate which monitors exist in enterprise_large profiles.

---

## 6. VSX / LAG / EVPN practice alignment

| Feature | Operational rationale |
|---------|------------------------|
| VSX pair + ISL LAG + keepalive | Aruba AOS-CX HA campus/agg design |
| MCLAG dual-homing | Server/ Tol access resiliency |
| EVPN ESI / VTEP / VNI | DC leaf-spine overlays |
| STP guards | Campus L2 safety |

---

## 7. Mapping policy for future extensions

New attributes may be added only if:

1. Documented in OpenConfig, RFCs, AOS-CX public docs, or peer-reviewed measurement papers; **and**  
2. Needed for a labeled task or twin fidelity; **and**  
3. Added to S05 justification catalog in the same revision.
