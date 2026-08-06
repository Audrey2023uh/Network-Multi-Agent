#!/usr/bin/env python3
"""Config, services, telemetry, incidents, labels, export for ECNetBench v1."""
from __future__ import annotations

import json
import math
import sqlite3
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml

from generate_ecnetbench import (
    Ctx,
    diurnal_mult,
    gen_inventory_topology,
    gen_org_sites,
    log_val,
    save_table,
)
import generate_ecnetbench as gben
from util import clamp, daterange, did, iso, parse_iso, sha16


def gen_config_policy(ctx: Ctx):
    seed = ctx.seed
    devices = ctx.tables["device"].to_dict("records")
    interfaces = ctx.tables["interface"].to_dict("records")

    # BGP between hq-wan and br-wan
    bgp_proc, bgp_nei, ospf_proc, ospf_if, static_r, bfd = [], [], [], [], [], []
    wan = [d for d in devices if d["role"] == "wan_edge"]
    for i, d in enumerate(wan):
        bgp_id = did(seed, "bgp", d["hostname"])
        bgp_proc.append({
            "bgp_id": bgp_id, "device_id": d["device_id"],
            "vrf_id": did(seed, "vrf", d["hostname"], "default"),
            "asn": 65001 if "hq" in d["hostname"] else 65002,
            "router_id": d["mgmt_ip"], "admin_state": "up",
        })
        peer = wan[1 - i]
        neighbor_ip = "172.16.0.2" if "hq" in d["hostname"] else "172.16.0.1"
        bgp_nei.append({
            "bgp_neighbor_id": did(seed, "bgpnei", d["hostname"], peer["hostname"]),
            "bgp_id": bgp_id, "neighbor_ip": neighbor_ip,
            "remote_asn": 65002 if "hq" in d["hostname"] else 65001,
            "peer_group": "WAN", "session_state": "established",
            "bfd_enabled": True, "af_ipv4_unicast": True, "af_l2vpn_evpn": False,
            "prefixes_received": 12, "prefixes_sent": 8,
            "last_state_change_at": iso(ctx.start - timedelta(days=10)),
        })
        bfd.append({
            "bfd_id": did(seed, "bfd", d["hostname"]),
            "device_id": d["device_id"], "peer_ip": neighbor_ip,
            "interface_id": next(r["interface_id"] for r in interfaces
                                 if r["device_id"] == d["device_id"] and r["if_name"] == "1/1/2"),
            "state": "up", "tx_interval_ms": 300, "rx_interval_ms": 300, "multiplier": 3,
            "last_change_at": iso(ctx.start - timedelta(days=10)),
        })

    # OSPF on campus core/agg
    for d in devices:
        if d["role"] in ("core", "aggregation") and d["site_id"] == ctx.tables["site"].query("site_code=='HQ-CAM'").iloc[0]["site_id"]:
            oid = did(seed, "ospf", d["hostname"])
            ospf_proc.append({
                "ospf_id": oid, "device_id": d["device_id"],
                "vrf_id": did(seed, "vrf", d["hostname"], "default"),
                "process_id": 1, "router_id": d["mgmt_ip"], "admin_state": "up",
            })
            for r in interfaces:
                if r["device_id"] == d["device_id"] and r["description"] in ("uplink", "isl", "downlink") and r["if_type"] == "ethernet":
                    ospf_if.append({
                        "ospf_if_id": did(seed, "ospfif", r["interface_id"]),
                        "ospf_id": oid, "interface_id": r["interface_id"],
                        "area_id": "0.0.0.0", "network_type": "point-to-point",
                        "cost": 10 if r["description"] != "isl" else 5,
                        "hello_interval": 10, "dead_interval": 40, "state": "full",
                    })

    save_table(ctx, "bgp_process", bgp_proc, {"device_id": "device"})
    save_table(ctx, "bgp_neighbor", bgp_nei, {"bgp_id": "bgp_process"})
    save_table(ctx, "bfd_session", bfd, {"device_id": "device", "interface_id": "interface"})
    save_table(ctx, "ospf_process", ospf_proc, {"device_id": "device"})
    save_table(ctx, "ospf_interface", ospf_if, {"ospf_id": "ospf_process", "interface_id": "interface"})
    save_table(ctx, "static_route", [], )
    save_table(ctx, "rib_entry_sample", [])
    save_table(ctx, "fib_entry_sample", [])

    # ACLs
    acl_rows, ace_rows, abind = [], [], []
    for d in devices:
        if d["role"] == "access":
            aid = did(seed, "acl", d["hostname"], "USER-IN")
            acl_rows.append({"acl_id": aid, "device_id": d["device_id"], "acl_name": "USER-IN",
                             "acl_type": "ipv4", "is_active": True})
            ace_rows += [
                {"ace_id": did(seed, "ace", aid, 10), "acl_id": aid, "sequence": 10, "action": "permit",
                 "protocol": "udp", "src_prefix": "10.0.0.0/8", "dst_prefix": "0.0.0.0/0",
                 "src_port_range": None, "dst_port_range": "53", "hit_count": 0, "is_log": False, "comment": "dns"},
                {"ace_id": did(seed, "ace", aid, 20), "acl_id": aid, "sequence": 20, "action": "permit",
                 "protocol": "tcp", "src_prefix": "10.0.0.0/8", "dst_prefix": "0.0.0.0/0",
                 "src_port_range": None, "dst_port_range": "443", "hit_count": 0, "is_log": False, "comment": "https"},
                {"ace_id": did(seed, "ace", aid, 100), "acl_id": aid, "sequence": 100, "action": "deny",
                 "protocol": "ip", "src_prefix": "0.0.0.0/0", "dst_prefix": "0.0.0.0/0",
                 "src_port_range": None, "dst_port_range": None, "hit_count": 0, "is_log": True, "comment": "deny-any"},
            ]
            # bind to first access ethernet
            for r in interfaces:
                if r["device_id"] == d["device_id"] and r["description"] == "access" and r["if_name"] == "1/1/1":
                    abind.append({"binding_id": did(seed, "aclb", aid, r["interface_id"]),
                                  "acl_id": aid, "interface_id": r["interface_id"], "vlan_id_key": None,
                                  "direction": "in", "valid_from": iso(ctx.start), "valid_to": None})
                    break
    save_table(ctx, "acl", acl_rows, {"device_id": "device"})
    save_table(ctx, "acl_entry", ace_rows, {"acl_id": "acl"})
    save_table(ctx, "acl_binding", abind, {"acl_id": "acl", "interface_id": "interface"})

    # QoS
    qos_pol, qos_cls, qos_q, qos_b = [], [], [], []
    for d in devices:
        if d["role"] in ("access", "aggregation"):
            pid = did(seed, "qosp", d["hostname"])
            qos_pol.append({"qos_policy_id": pid, "device_id": d["device_id"],
                            "policy_name": "EDGE-QOS", "policy_type": "queuing"})
            qos_cls.append({"qos_class_id": did(seed, "qosc", pid, "voice"), "qos_policy_id": pid,
                            "class_name": "VOICE", "match_dscp": [46], "match_cos": [5], "match_acl_id": None})
            qos_cls.append({"qos_class_id": did(seed, "qosc", pid, "default"), "qos_policy_id": pid,
                            "class_name": "DEFAULT", "match_dscp": [0], "match_cos": [0], "match_acl_id": None})
            for qid, sched, w in [(0, "strict", None), (1, "wrr", 40), (2, "wrr", 60)]:
                qos_q.append({"qos_queue_id": did(seed, "qosq", d["hostname"], qid), "device_id": d["device_id"],
                              "queue_id": qid, "scheduler": sched, "weight": w, "bandwidth_pct": None,
                              "buffer_bytes": 1_000_000})
            for r in interfaces:
                if r["device_id"] == d["device_id"] and r["description"] == "uplink" and r["if_type"] == "ethernet":
                    qos_b.append({"binding_id": did(seed, "qosb", pid, r["interface_id"]),
                                  "qos_policy_id": pid, "interface_id": r["interface_id"],
                                  "direction": "out", "valid_from": iso(ctx.start), "valid_to": None})
                    break
    save_table(ctx, "qos_policy", qos_pol, {"device_id": "device"})
    save_table(ctx, "qos_class", qos_cls, {"qos_policy_id": "qos_policy"})
    save_table(ctx, "qos_queue", qos_q, {"device_id": "device"})
    save_table(ctx, "qos_binding", qos_b, {"qos_policy_id": "qos_policy", "interface_id": "interface"})

    # STP
    stp_i, stp_p = [], []
    for d in devices:
        if d["device_class"] == "switch" and d["role"] in ("core", "aggregation", "access"):
            sid = did(seed, "stp", d["hostname"])
            is_root = d["hostname"] == "hq-core-a"
            stp_i.append({"stp_id": sid, "device_id": d["device_id"], "mode": "rstp",
                          "priority": 0 if is_root else (4096 if d["role"] == "core" else 32768),
                          "bridge_mac": f"02:11:22:33:44:{sha16(d['hostname'])[:2]}",
                          "is_root": is_root})
            for r in interfaces:
                if r["device_id"] == d["device_id"] and r["if_type"] == "ethernet" and r["description"] in ("uplink", "downlink", "access", "isl"):
                    role = "root" if r["description"] == "uplink" and not is_root else ("designated" if is_root or r["description"] != "uplink" else "root")
                    if r["description"] == "access":
                        role = "designated"
                    stp_p.append({
                        "stp_port_id": did(seed, "stpp", r["interface_id"]),
                        "stp_id": sid, "interface_id": r["interface_id"],
                        "port_role": role, "port_state": "forwarding", "path_cost": 20000,
                        "bpdu_guard": r["description"] == "access", "root_guard": False,
                        "loop_guard": r["description"] in ("uplink", "isl"),
                        "last_topology_change_at": iso(ctx.start - timedelta(days=30)),
                    })
    save_table(ctx, "stp_instance", stp_i, {"device_id": "device"})
    save_table(ctx, "stp_port", stp_p, {"stp_id": "stp_instance", "interface_id": "interface"})

    # AAA
    aaa, radius = [], []
    hq_site = ctx.tables["site"].query("site_code=='HQ-CAM'").iloc[0]["site_id"]
    radius.append({"radius_id": did(seed, "radius", 1), "site_id": hq_site,
                   "server_ip": "10.10.100.20", "timeout_s": 3, "retransmit": 2, "status": "up"})
    radius.append({"radius_id": did(seed, "radius", 2), "site_id": hq_site,
                   "server_ip": "10.10.100.21", "timeout_s": 3, "retransmit": 2, "status": "up"})
    for d in devices:
        if d["role"] in ("access", "ap") or d["device_class"] == "access_point":
            aaa.append({"aaa_id": did(seed, "aaa", d["hostname"]), "device_id": d["device_id"],
                        "method_list_name": "default", "auth_type": "dot1x",
                        "server_group": "RADIUS-HQ", "fallback_local": False})
    save_table(ctx, "radius_server", radius, {"site_id": "site"})
    save_table(ctx, "aaa_method", aaa, {"device_id": "device"})

    # Config snapshots every 6h + maintenance-aligned
    snaps, diffs = [], []
    cadence_h = ctx.cfg["time"]["config_cadence_hours"]
    for d in devices:
        if not d["is_managed"] or d["device_class"] == "access_point":
            # still snapshot APs lightly
            pass
        t = ctx.start
        prev = None
        n = 0
        while t <= ctx.end:
            sid = did(seed, "cfgsnap", d["hostname"], iso(t))
            structured = {
                "hostname": d["hostname"], "os_version": d["os_version"],
                "role": d["role"], "vlans": [10, 20, 100],
                "bgp_established": d["role"] == "wan_edge",
            }
            body = json.dumps(structured, sort_keys=True)
            snaps.append({
                "config_snapshot_id": sid, "device_id": d["device_id"],
                "snapshot_at": iso(t), "trigger": "scheduled",
                "config_hash": sha16(body), "schema_version": "aoscx-rest-10.13",
                "structured_config": body, "cli_text": f"! hostname {d['hostname']}\n",
                "is_baseline": n == 0, "change_ticket_id": None,
            })
            if prev is not None and n % 8 == 0 and d["role"] == "access":
                # planned benign ACL comment change
                diff_id = did(seed, "diff", sid)
                diffs.append({
                    "diff_id": diff_id, "before_snapshot_id": prev, "after_snapshot_id": sid,
                    "object_type": "acl_entry", "object_key": "USER-IN/seq:10",
                    "change_op": "modify",
                    "before_value": json.dumps({"comment": "dns"}),
                    "after_value": json.dumps({"comment": "dns-primary"}),
                    "risk_score_heuristic": 0.05, "diffed_at": iso(t),
                })
            prev = sid
            n += 1
            t += timedelta(hours=cadence_h)
    save_table(ctx, "config_snapshot", snaps, {"device_id": "device"})
    save_table(ctx, "config_object_diff", diffs, {"before_snapshot_id": "config_snapshot", "after_snapshot_id": "config_snapshot"})

    # API archive samples (hourly subset of devices)
    api = []
    sample_devs = [d for d in devices if d["role"] in ("core", "aggregation", "wan_edge")]
    for d in sample_devs:
        for t in daterange(ctx.start, ctx.end, 3600):
            lat = 15.0 + 5.0 * math.sin(t.timestamp() / 3600.0)
            api.append({
                "api_response_id": did(seed, "api", d["hostname"], iso(t)),
                "device_id": d["device_id"], "observed_at": iso(t),
                "protocol": "rest", "method": "GET",
                "resource_path": "/rest/v10.13/system",
                "http_status": 200, "latency_ms": round(lat, 2),
                "response_hash": sha16(d["hostname"], iso(t)),
                "response_body": json.dumps({"hostname": d["hostname"]}),
                "error_code": None,
            })
    save_table(ctx, "api_response_archive", api, {"device_id": "device"})


def gen_services_users(ctx: Ctx):
    seed = ctx.seed
    org_id = ctx.tables["organization"].iloc[0]["org_id"]
    hq = ctx.tables["site"].query("site_code=='HQ-CAM'").iloc[0]
    br = ctx.tables["site"].query("site_code=='BR-01'").iloc[0]
    apps = [
        ("voip", "voice", 46, 30, 0.5),
        ("sap-erp", "erp", 18, 150, 0.1),
        ("email", "email", 0, 200, 1.0),
        ("web-intranet", "web", 0, 300, 1.0),
        ("dns", "dns", 0, 20, 0.1),
        ("radius-auth", "auth", 0, 50, 0.1),
        ("backup", "backup", 0, 500, 2.0),
    ]
    app_rows = []
    for name, cat, dscp, lat, loss in apps:
        app_rows.append({
            "application_id": did(seed, "app", name), "app_name": name, "app_category": cat,
            "default_dscp": dscp, "port_hints": json.dumps([443] if cat != "dns" else [53]),
            "sensitivity_latency_ms": lat, "sensitivity_loss_pct": loss,
        })
    save_table(ctx, "application", app_rows)

    # services + SLA circular: create services first without sla, then sla, then update — use sla embedded
    svc_defs = [
        ("Voice-Collab", 1, "voip"),
        ("ERP-SAP", 1, "sap-erp"),
        ("Email", 2, "email"),
        ("Intranet-Web", 3, "web-intranet"),
        ("DNS-Internal", 1, "dns"),
        ("NAC-Auth", 1, "radius-auth"),
        ("Nightly-Backup", 4, "backup"),
    ]
    sla_rows, svc_rows = [], []
    for sname, tier, app in svc_defs:
        sid = did(seed, "svc", sname)
        sla_id = did(seed, "sla", sname)
        svc_rows.append({
            "service_id": sid, "service_name": sname, "owner_team": "NetOps",
            "criticality_tier": tier, "primary_site_id": hq["site_id"], "sla_id": sla_id,
        })
        ctx.services[sid] = {"name": sname, "app": app, "tier": tier}
        sla_rows.append({
            "sla_id": sla_id, "metric": "availability", "target_value": 99.9 if tier <= 2 else 99.0,
            "window": "rolling_24h", "service_id": sid,
        })
    save_table(ctx, "service", svc_rows, {"primary_site_id": "site"})
    save_table(ctx, "sla_objective", sla_rows, {"service_id": "service"})

    # dependencies: services depend on core/agg devices and apps
    deps = []
    core_a = ctx.tables["device"].query("hostname=='hq-core-a'").iloc[0]["device_id"]
    for sid, meta in ctx.services.items():
        deps.append({"dep_id": did(seed, "dep", sid, "app"), "service_id": sid,
                     "depends_on_service_id": None, "depends_on_device_id": None,
                     "depends_on_application_id": did(seed, "app", meta["app"]),
                     "dependency_type": "api", "weight": 1.0})
        deps.append({"dep_id": did(seed, "dep", sid, "core"), "service_id": sid,
                     "depends_on_service_id": None, "depends_on_device_id": core_a,
                     "depends_on_application_id": None, "dependency_type": "network_path", "weight": 1.0})
        if meta["name"] != "NAC-Auth":
            deps.append({"dep_id": did(seed, "dep", sid, "auth"), "service_id": sid,
                         "depends_on_service_id": did(seed, "svc", "NAC-Auth"),
                         "depends_on_device_id": None, "depends_on_application_id": None,
                         "dependency_type": "auth", "weight": 0.5})
    save_table(ctx, "service_dependency", deps, {"service_id": "service"})

    # users + endpoints
    users, endpoints, binds = [], [], []
    access_ifs = ctx.tables["interface"].query("description=='access' and if_type=='ethernet'")
    aps = ctx.tables["access_point"].to_dict("records")
    for i in range(80):
        uid = did(seed, "user", i)
        users.append({
            "user_id": uid, "org_id": org_id,
            "user_name_hash": sha16("user", i),
            "department": ["eng", "finance", "hr", "sales"][i % 4],
            "role": "employee", "is_privileged": i % 20 == 0,
            "valid_from": iso(ctx.start - timedelta(days=100)), "valid_to": None,
        })
        site = hq if i < 65 else br
        wired = i % 3 != 0
        if wired and len(access_ifs):
            ifr = access_ifs.iloc[i % len(access_ifs)]
            ep = {
                "endpoint_id": did(seed, "ep", i), "site_id": site["site_id"],
                "mac": f"02:00:00:{i:02x}:{(i*3)%256:02x}:{(i*7)%256:02x}",
                "ip_address": f"10.{10 if site['site_code']=='HQ-CAM' else 20}.10.{(i%200)+1}",
                "hostname": f"ep-{i:03d}", "endpoint_type": "laptop",
                "os_family": "Windows", "access_type": "wired",
                "attached_interface_id": ifr["interface_id"], "ap_id": None,
                "auth_method": "dot1x",
                "vlan_id_key": ctx.vlan_keys.get((site["site_id"], 10)),
                "last_seen_at": iso(ctx.end),
            }
        else:
            ap = aps[i % len(aps)]
            ep = {
                "endpoint_id": did(seed, "ep", i), "site_id": site["site_id"],
                "mac": f"02:00:01:{i:02x}:{(i*3)%256:02x}:{(i*7)%256:02x}",
                "ip_address": f"10.{10 if site['site_code']=='HQ-CAM' else 20}.11.{(i%200)+1}",
                "hostname": f"epw-{i:03d}", "endpoint_type": "phone" if i % 5 == 0 else "laptop",
                "os_family": "iOS" if i % 5 == 0 else "Windows", "access_type": "wifi",
                "attached_interface_id": None, "ap_id": ap["ap_id"],
                "auth_method": "dot1x",
                "vlan_id_key": ctx.vlan_keys.get((site["site_id"], 10)),
                "last_seen_at": iso(ctx.end),
            }
        endpoints.append(ep)
        # bind to a couple services
        for sname in ("Intranet-Web", "Email", "Voice-Collab"):
            binds.append({"bind_id": did(seed, "bind", i, sname), "service_id": did(seed, "svc", sname),
                          "endpoint_id": ep["endpoint_id"], "role": "client"})
    # servers
    for i, sname in enumerate(["erp-srv", "mail-srv", "dns-srv"]):
        endpoints.append({
            "endpoint_id": did(seed, "srv", sname), "site_id": hq["site_id"],
            "mac": f"02:10:00:00:00:{i:02x}", "ip_address": f"10.10.30.{10+i}",
            "hostname": sname, "endpoint_type": "server", "os_family": "Linux",
            "access_type": "wired",
            "attached_interface_id": access_ifs.query("if_name=='1/1/1'").iloc[0]["interface_id"] if len(access_ifs) else None,
            "ap_id": None, "auth_method": "mab",
            "vlan_id_key": ctx.vlan_keys.get((hq["site_id"], 30)),
            "last_seen_at": iso(ctx.end),
        })
    save_table(ctx, "user_account", users, {"org_id": "organization"})
    save_table(ctx, "endpoint", endpoints, {"site_id": "site"})
    save_table(ctx, "service_endpoint_bind", binds, {"service_id": "service", "endpoint_id": "endpoint"})


def plan_incidents(ctx: Ctx) -> List[dict]:
    """Create causally planned incidents with onset times (no overlapping beyond cap)."""
    seed = ctx.seed
    rng = ctx.rng
    cats = list(ctx.cfg["incidents"]["categories"])
    target = ctx.cfg["incidents"]["target_count"]
    # ensure each category at least twice
    plan = []
    t = ctx.start + timedelta(hours=18)
    devices = ctx.tables["device"].to_dict("records")
    interfaces = ctx.tables["interface"].to_dict("records")
    links = ctx.tables["link"].to_dict("records")
    access_uplinks = [r for r in interfaces if r["description"] == "uplink" and r["if_type"] == "ethernet"
                      and ctx.devices[r["device_id"]]["role"] == "access"]
    phy_links = [L for L in links if L["link_layer"] == "phy" and not L["is_isl"]]

    def pick_if(role_hint="uplink"):
        cands = [r for r in access_uplinks] if access_uplinks else [r for r in interfaces if r["if_type"] == "ethernet"]
        return cands[int(rng.integers(0, len(cands)))]

    cat_cycle = (cats * ((target // len(cats)) + 2))[:target]
    isl_ifs = [r for r in interfaces if r.get("description") == "isl" and r["if_type"] == "ethernet"]
    wan_ifs = [r for r in interfaces if r.get("description") == "wan" and r["if_type"] == "ethernet"]
    for i, cat in enumerate(cat_cycle):
        # spacing ~6–10h with jitter from lognormal hours
        gap_h = float(clamp(rng.lognormal(mean=math.log(8.0), sigma=0.25), 4.0, 16.0))
        t = t + timedelta(hours=gap_h)
        if t >= ctx.end - timedelta(hours=6):
            break
        if cat == "vsx_split_brain" and isl_ifs:
            ifr = isl_ifs[i % len(isl_ifs)]
        elif cat == "routing_instability" and wan_ifs:
            ifr = wan_ifs[i % len(wan_ifs)]
        else:
            ifr = pick_if()
        dev = ctx.devices[ifr["device_id"]]
        link = phy_links[i % len(phy_links)] if phy_links else None
        plan.append({
            "idx": i, "category": cat, "onset": t,
            "interface_id": ifr["interface_id"], "device_id": ifr["device_id"],
            "hostname": dev["hostname"], "link_id": link["link_id"] if link else None,
            "cable_id": link["cable_id"] if link else None,
        })
    ctx.incidents = plan
    return plan


def active_faults_at(plan: List[dict], ts: datetime) -> List[dict]:
    out = []
    for inc in plan:
        onset = inc["onset"]
        # recovery ends stored later; during planning use provisional duration
        dur_h = inc.get("duration_h", 1.5)
        if onset <= ts <= onset + timedelta(hours=dur_h):
            out.append(inc)
    return out


def gen_incidents_and_effects(ctx: Ctx):
    """Finalize incident GT, recovery, and side-effect timelines used by telemetry."""
    seed = ctx.seed
    rng = ctx.rng
    plan = plan_incidents(ctx)
    # detection latency (lognormal seconds), recovery durations by category
    det_params = {
        "interface_failure": (4.5, 0.5), "cable_failure": (5.0, 0.5), "congestion": (6.0, 0.4),
        "routing_instability": (4.8, 0.55), "acl_misconfiguration": (6.5, 0.5),
        "vlan_mismatch": (6.2, 0.5), "stp_loop": (4.2, 0.45), "firmware_incompatibility": (7.0, 0.4),
        "qos_problems": (6.3, 0.5), "authentication_failures": (5.5, 0.5),
        "hardware_degradation": (7.5, 0.4), "power_issues": (3.8, 0.4),
        "intermittent_failures": (5.8, 0.6), "vsx_split_brain": (4.0, 0.4),
    }
    rec_minutes = {
        "interface_failure": 25, "cable_failure": 55, "congestion": 40, "routing_instability": 35,
        "acl_misconfiguration": 45, "vlan_mismatch": 35, "stp_loop": 30, "firmware_incompatibility": 120,
        "qos_problems": 50, "authentication_failures": 40, "hardware_degradation": 180,
        "power_issues": 90, "intermittent_failures": 60, "vsx_split_brain": 70,
    }
    action_map = {
        "interface_failure": "interface_admin_up", "cable_failure": "replace_cable",
        "congestion": "traffic_reroute", "routing_instability": "bgp_neighbor_reset",
        "acl_misconfiguration": "config_rollback", "vlan_mismatch": "vlan_tagging_fix",
        "stp_loop": "stp_guard_enable", "firmware_incompatibility": "firmware_align_rollback",
        "qos_problems": "qos_policy_update", "authentication_failures": "radius_restore",
        "hardware_degradation": "replace_transceiver", "power_issues": "psu_replace",
        "intermittent_failures": "replace_transceiver", "vsx_split_brain": "interface_admin_up",
    }

    incidents, entities, impacts, actions = [], [], [], []
    topo_pid = ctx.tables["topology_profile"].iloc[0]["topology_profile_id"]
    # change-induced subset: attach to existing diffs
    diffs = ctx.tables["config_object_diff"]
    for i, p in enumerate(plan):
        cat = p["category"]
        mu, sigma = det_params[cat]
        det_s = float(clamp(rng.lognormal(mu, sigma), 30, 7200))
        onset = p["onset"]
        detected = onset + timedelta(seconds=det_s)
        rec_m = rec_minutes[cat] * float(clamp(rng.lognormal(0, 0.2), 0.7, 1.5))
        rec_start = detected + timedelta(minutes=5)
        rec_end = rec_start + timedelta(minutes=rec_m)
        success = True if cat != "intermittent_failures" or i % 5 else True
        # rare unsuccessful
        if cat == "hardware_degradation" and i % 7 == 0:
            success = False
            rec_end = rec_start + timedelta(minutes=rec_m)
        downtime = (rec_end - onset).total_seconds() if cat not in ("congestion", "qos_problems", "hardware_degradation") else (rec_end - onset).total_seconds() * 0.3
        p["duration_h"] = (rec_end - onset).total_seconds() / 3600.0
        p["detected"] = detected
        p["rec_end"] = rec_end
        p["rec_start"] = rec_start
        p["success"] = success

        trigger = "spontaneous"
        diff_id = None
        if cat in ("acl_misconfiguration", "vlan_mismatch", "qos_problems", "firmware_incompatibility") and len(diffs):
            trigger = "change_induced"
            diff_id = diffs.iloc[i % len(diffs)]["diff_id"]

        iid = did(seed, "inc", i, cat)
        p["incident_id"] = iid
        precursors = {
            "interface_failure": ["oper_status=down", "carrier_transitions++", "syslog:link_down"],
            "cable_failure": ["in_fcs_errors++", "optical_rx_power low", "both_ends_errors"],
            "congestion": ["utilization>0.9", "out_discards++", "latency_kpi++"],
            "routing_instability": ["bgp_session_state!=established", "prefix_drop", "syslog:bgp"],
            "acl_misconfiguration": ["config_diff:acl", "ipfix_drop_reason", "service_reachability_loss"],
            "vlan_mismatch": ["tagging_asymmetry", "no_phy_down", "connectivity_loss"],
            "stp_loop": ["broadcast_storm", "cpu_spike", "mac_flap_syslog"],
            "firmware_incompatibility": ["fw_version_diverge", "vsx_out_of_sync"],
            "qos_problems": ["voice_queue_drops", "app_kpi_degrade"],
            "authentication_failures": ["aaa_reject_syslog", "new_endpoint_fail"],
            "hardware_degradation": ["sensor_warn", "fcs_trend_up"],
            "power_issues": ["psu_status=failed", "correlated_downs"],
            "intermittent_failures": ["carrier_transitions_burst", "short_downs"],
            "vsx_split_brain": ["isl_down", "keepalive_down", "vsx_split"],
        }[cat]

        incidents.append({
            "incident_id": iid, "topology_profile_id": topo_pid, "category": cat,
            "subcategory": cat, "severity": "critical" if cat in ("stp_loop", "power_issues", "vsx_split_brain") else (
                "high" if cat in ("routing_instability", "acl_misconfiguration") else "medium"),
            "onset_at": iso(onset), "detected_at": iso(detected), "detection_source": "alert",
            "detection_latency_s": round(det_s, 2),
            "recovered_at": iso(rec_end) if success else None,
            "recovery_duration_s": round((rec_end - rec_start).total_seconds(), 2),
            "recovery_success": success,
            "downtime_s": round(downtime, 2),
            "root_entity_type": "cable" if cat == "cable_failure" else ("device" if cat in ("power_issues", "firmware_incompatibility", "vsx_split_brain") else "interface"),
            "root_entity_id": p["cable_id"] or p["device_id"] if cat in ("cable_failure", "power_issues", "firmware_incompatibility", "vsx_split_brain") else p["interface_id"],
            "trigger_type": trigger, "change_diff_id": diff_id, "parent_incident_id": None,
            "description": f"Injected {cat} on {p['hostname']}",
            "observable_precursors": json.dumps(precursors),
            "undetected": False, "self_cleared": False, "no_service_impact": cat == "hardware_degradation" and i % 3 == 0,
        })
        # fix root entity for cable
        if cat == "cable_failure":
            incidents[-1]["root_entity_id"] = p["cable_id"] or p["interface_id"]
            incidents[-1]["root_entity_type"] = "cable" if p["cable_id"] else "interface"
        elif cat in ("power_issues", "firmware_incompatibility", "vsx_split_brain"):
            incidents[-1]["root_entity_id"] = p["device_id"]
            incidents[-1]["root_entity_type"] = "device"
        else:
            incidents[-1]["root_entity_id"] = p["interface_id"]
            incidents[-1]["root_entity_type"] = "interface"

        entities.append({"incident_id": iid, "entity_type": incidents[-1]["root_entity_type"],
                         "entity_id": incidents[-1]["root_entity_id"], "role": "root"})
        entities.append({"incident_id": iid, "entity_type": "device", "entity_id": p["device_id"], "role": "symptomatic"})
        entities.append({"incident_id": iid, "entity_type": "interface", "entity_id": p["interface_id"], "role": "symptomatic"})

        # service impact via dependency on core or auth
        if not incidents[-1]["no_service_impact"]:
            for sname, sev in [("Intranet-Web", "medium"), ("Email", "medium"), ("Voice-Collab", "high"), ("ERP-SAP", "high")]:
                if cat in ("authentication_failures",) and sname != "NAC-Auth":
                    # auth impacts NAC and dependents
                    pass
                sid = did(seed, "svc", sname)
                if cat == "authentication_failures":
                    sid = did(seed, "svc", "NAC-Auth")
                    impacts.append({
                        "impact_id": did(seed, "imp", iid, "NAC-Auth"), "incident_id": iid,
                        "service_id": sid, "impact_start": iso(onset), "impact_end": iso(rec_end),
                        "severity": "high", "users_affected": 40, "sla_breach": True,
                    })
                    break
                if cat in ("congestion", "qos_problems") and sname != "Voice-Collab":
                    continue
                impacts.append({
                    "impact_id": did(seed, "imp", iid, sname), "incident_id": iid,
                    "service_id": sid, "impact_start": iso(onset), "impact_end": iso(rec_end),
                    "severity": sev, "users_affected": 20 if sev != "high" else 50,
                    "sla_breach": sev == "high",
                })
                if cat in ("congestion", "qos_problems"):
                    break

        actor = "orchestrator" if cat in ("interface_failure", "routing_instability") else "human"
        actions.append({
            "action_id": did(seed, "act", iid, 1), "incident_id": iid, "sequence": 1,
            "action_type": action_map[cat],
            "action_params": json.dumps({"interface_id": p["interface_id"], "hostname": p["hostname"]}),
            "started_at": iso(rec_start), "ended_at": iso(rec_end),
            "duration_s": round((rec_end - rec_start).total_seconds(), 2),
            "success": success, "actor": actor, "runbook_id": f"RB-{cat}",
            "notes": "constraint-satisfying remediation",
        })

    save_table(ctx, "failure_incident", incidents, {"topology_profile_id": "topology_profile"})
    save_table(ctx, "incident_entity", entities, {"incident_id": "failure_incident"})
    save_table(ctx, "service_impact", impacts, {"incident_id": "failure_incident", "service_id": "service"})
    save_table(ctx, "recovery_action", actions, {"incident_id": "failure_incident"})
    ctx.incidents = plan


def incident_overlay(plan: List[dict], ts: datetime, interface_id: str, device_id: str) -> dict:
    """Return fault modifiers for telemetry at ts."""
    mod = {"oper_down": False, "util_boost": 0.0, "err_boost": 0.0, "disc_boost": 0.0,
           "cpu_boost": 0.0, "bcast_boost": 0.0, "carrier_boost": 0, "psu_fail": False,
           "optical_low": False, "bgp_down": False, "auth_fail": False, "vsx_split": False}
    for p in plan:
        if not (p["onset"] <= ts <= p.get("rec_end", p["onset"])):
            continue
        cat = p["category"]
        hit = p["interface_id"] == interface_id or p["device_id"] == device_id
        # cable faults affect both ends — approximate via same link interfaces not tracked; use device/interface match
        if not hit and cat != "stp_loop":
            continue
        if cat in ("interface_failure", "cable_failure", "vsx_split_brain", "power_issues"):
            if p["interface_id"] == interface_id or (cat == "power_issues" and p["device_id"] == device_id):
                mod["oper_down"] = True
        if cat == "congestion" and p["interface_id"] == interface_id:
            mod["util_boost"] = 0.55
            mod["disc_boost"] = 50
        if cat == "cable_failure" and p["interface_id"] == interface_id:
            mod["err_boost"] = 80
            mod["optical_low"] = True
            mod["oper_down"] = ts >= p["onset"] + timedelta(minutes=2)
        if cat == "stp_loop":
            mod["bcast_boost"] = 5000
            mod["cpu_boost"] = 45
        if cat == "routing_instability" and p["device_id"] == device_id:
            mod["bgp_down"] = True
            mod["cpu_boost"] = 20
        if cat == "qos_problems" and p["interface_id"] == interface_id:
            mod["disc_boost"] = 30
            mod["util_boost"] = 0.2
        if cat == "authentication_failures":
            mod["auth_fail"] = True
        if cat == "hardware_degradation" and p["device_id"] == device_id:
            mod["err_boost"] = 15
            mod["optical_low"] = True
        if cat == "power_issues" and p["device_id"] == device_id:
            mod["psu_fail"] = True
            mod["oper_down"] = True
        if cat == "intermittent_failures" and p["interface_id"] == interface_id:
            # flap every other 5-min sample
            slot = int(ts.timestamp()) // 300
            mod["oper_down"] = slot % 2 == 0
            mod["carrier_boost"] = 3
        if cat == "vsx_split_brain" and p["device_id"] == device_id:
            mod["vsx_split"] = True
            mod["oper_down"] = True
        if cat in ("acl_misconfiguration", "vlan_mismatch") and p["interface_id"] == interface_id:
            mod["disc_boost"] = 20
    return mod


def gen_telemetry(ctx: Ctx):
    seed = ctx.seed
    rng = ctx.rng
    cadence = ctx.cfg["time"]["telemetry_cadence_s"]
    stats = ctx.cfg["statistics"]
    plan = ctx.incidents
    devices = ctx.tables["device"].to_dict("records")
    interfaces = [r for r in ctx.tables["interface"].to_dict("records") if r["if_type"] in ("ethernet", "lag")]

    # cumulative counters per interface
    cum = {r["interface_id"]: {"in_o": 0, "out_o": 0, "in_u": 0, "out_u": 0, "in_b": 0, "out_b": 0,
                                "in_m": 0, "out_m": 0, "in_d": 0, "out_d": 0, "in_e": 0, "out_e": 0,
                                "fcs": 0, "carrier": 0} for r in interfaces}

    if_samples, dev_samples, env_samples, power_samples = [], [], [], []
    syslog, alerts = [], []
    qos_cs = []
    kpi = []
    emitted_events = set()

    # role base Mbps
    def base_mbps(desc, role):
        if desc in ("isl",):
            return 800.0
        if desc in ("uplink", "downlink"):
            return 200.0 if role == "access" else 600.0
        if desc == "wan":
            return 80.0
        if desc == "access":
            return 15.0
        return 5.0

    times = list(daterange(ctx.start, ctx.end, cadence))
    print(f"  telemetry timesteps: {len(times)}, interfaces: {len(interfaces)}")

    # preindex components
    comps = ctx.tables["hardware_component"].to_dict("records")
    psu_by_dev = defaultdict(list)
    for c in comps:
        if c["component_type"] == "psu":
            psu_by_dev[c["device_id"]].append(c)

    for ti, ts in enumerate(times):
        if ti % 500 == 0:
            print(f"    t-step {ti}/{len(times)}")
        for d in devices:
            role = d["role"]
            cpu_base = stats["cpu_base_by_role"].get(role, 15.0)
            # traffic-correlated cpu: average util proxy via hour
            hour_m = diurnal_mult(ctx, ts)
            cpu = cpu_base * (0.7 + 0.6 * hour_m)
            mod_d = incident_overlay(plan, ts, "", d["device_id"])
            # check any interface of device — use device-level mods from plan
            for p in plan:
                if p["device_id"] == d["device_id"] and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                    md = incident_overlay(plan, ts, p["interface_id"], d["device_id"])
                    cpu += md["cpu_boost"]
                    if md["psu_fail"]:
                        cpu = min(cpu, 5)
            cpu = clamp(cpu + float(rng.normal(0, 0.8)), 1.0, 99.0)  # small sensor noise only
            mem_total = 8_000_000_000 if role != "ap" else 2_000_000_000
            mem_util = clamp(35 + 10 * hour_m + float(rng.normal(0, 0.5)), 10, 92)
            dev_samples.append({
                "sample_id": did(seed, "devres", d["hostname"], iso(ts)),
                "device_id": d["device_id"], "observed_at": iso(ts),
                "cpu_util_pct": round(cpu, 3), "cpu_util_user_pct": round(cpu * 0.4, 3),
                "cpu_util_system_pct": round(cpu * 0.6, 3),
                "mem_used_bytes": int(mem_total * mem_util / 100),
                "mem_total_bytes": mem_total, "mem_util_pct": round(mem_util, 3),
                "process_count": 120 + int(role == "core") * 40,
                "control_plane_drop_pct": 0.0,
            })
            # sensors every step (light)
            temp = 35 + 8 * (cpu / 100) + float(rng.normal(0, stats["sensor_noise_sigma"]))
            env_samples.append({
                "sample_id": did(seed, "env", d["hostname"], "temp", iso(ts)),
                "device_id": d["device_id"], "component_id": None, "observed_at": iso(ts),
                "sensor_type": "temperature", "value": round(temp, 2), "unit": "C",
                "threshold_warning": 70, "threshold_critical": 85,
                "status": "crit" if temp > 85 else ("warn" if temp > 70 else "ok"),
            })
            for psu in psu_by_dev.get(d["device_id"], [])[:2]:
                fail = False
                for p in plan:
                    if p["category"] == "power_issues" and p["device_id"] == d["device_id"] and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                        fail = psu["name"] == "PSU1"
                power_samples.append({
                    "sample_id": did(seed, "pwr", psu["component_id"], iso(ts)),
                    "device_id": d["device_id"], "component_id": psu["component_id"],
                    "observed_at": iso(ts), "input_power_w": 0 if fail else 120.0,
                    "output_power_w": 0 if fail else 100.0,
                    "psu_status": "failed" if fail else "ok",
                    "redundant_ok": not fail,
                })

        for r in interfaces:
            desc = r["description"] or "other"
            role = ctx.devices[r["device_id"]]["role"]
            speed = r["speed_bps"] or 1_000_000_000
            mbps = base_mbps(desc, role) * diurnal_mult(ctx, ts, "server" if "server" in desc else "user")
            # interface-specific stable factor from id hash
            factor = 0.5 + (int(sha16(r["interface_id"])[:4], 16) % 1000) / 1000.0
            mbps *= factor
            mod = incident_overlay(plan, ts, r["interface_id"], r["device_id"])
            mbps = mbps * (1.0 + mod["util_boost"]) + mod["util_boost"] * (speed / 1e6) * 0.5
            if mod["oper_down"]:
                mbps = 0.0
            util = clamp(mbps * 1e6 / speed, 0.0, 0.99)
            # bytes in this interval (approx half duplex split)
            interval = cadence
            out_bytes = int(util * speed * interval / 8 * 0.55)
            in_bytes = int(util * speed * interval / 8 * 0.45)
            pkts = max(1, int((in_bytes + out_bytes) / 800)) if not mod["oper_down"] else 0
            c = cum[r["interface_id"]]
            c["in_o"] += in_bytes
            c["out_o"] += out_bytes
            c["in_u"] += int(pkts * 0.45)
            c["out_u"] += int(pkts * 0.45)
            c["in_b"] += int(pkts * 0.02) + int(mod["bcast_boost"])
            c["out_b"] += int(pkts * 0.02) + int(mod["bcast_boost"])
            c["in_m"] += int(pkts * 0.03)
            c["out_m"] += int(pkts * 0.03)
            c["out_d"] += int(mod["disc_boost"])
            c["in_e"] += int(mod["err_boost"])
            c["fcs"] += int(mod["err_boost"] * 0.8)
            c["carrier"] += int(mod["carrier_boost"]) + (1 if mod["oper_down"] and ti > 0 else 0)
            if_samples.append({
                "sample_id": did(seed, "ifc", r["interface_id"], iso(ts)),
                "interface_id": r["interface_id"], "device_id": r["device_id"],
                "observed_at": iso(ts),
                "in_octets": c["in_o"], "out_octets": c["out_o"],
                "in_unicast_pkts": c["in_u"], "out_unicast_pkts": c["out_u"],
                "in_broadcast_pkts": c["in_b"], "out_broadcast_pkts": c["out_b"],
                "in_multicast_pkts": c["in_m"], "out_multicast_pkts": c["out_m"],
                "in_discards": c["in_d"], "out_discards": c["out_d"],
                "in_errors": c["in_e"], "out_errors": c["out_e"],
                "in_fcs_errors": c["fcs"], "in_unknown_protos": 0,
                "carrier_transitions": c["carrier"], "last_clear_at": None,
            })
            # syslog/alerts on fault edges (once per incident)
            for p in plan:
                if p["interface_id"] != r["interface_id"]:
                    continue
                if abs((ts - p["onset"]).total_seconds()) < cadence:
                    key = ("onset", p["incident_id"])
                    if key in emitted_events:
                        continue
                    emitted_events.add(key)
                    syslog.append({
                        "syslog_id": did(seed, "log", p["incident_id"], "onset"),
                        "device_id": r["device_id"], "observed_at": iso(ts), "received_at": iso(ts + timedelta(seconds=1)),
                        "facility": "local0", "severity": 3, "severity_label": "err",
                        "app_name": "port", "msg_id": "LINK", "event_code": "LINK_DOWN",
                        "message": f"Interface {r['if_name']} link down ({p['category']})",
                        "structured_data": json.dumps({"if": r["if_name"], "category": p["category"]}),
                        "interface_id": r["interface_id"], "related_user": None, "is_parse_success": True,
                    })
                    alerts.append({
                        "alert_id": did(seed, "al", p["incident_id"], "raise"),
                        "device_id": r["device_id"], "interface_id": r["interface_id"],
                        "raised_at": iso(p["detected"]), "cleared_at": iso(p["rec_end"]),
                        "alert_type": p["category"], "severity": "major",
                        "title": f"{p['category']} detected", "body": p["hostname"],
                        "source_system": "nms", "correlated_incident_id": p["incident_id"],
                        "is_false_positive_gt": False,
                    })

        # service KPIs
        for sid, meta in ctx.services.items():
            deg = 0.0
            for p in plan:
                if p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                    if p["category"] in ("congestion", "qos_problems", "stp_loop", "routing_instability", "acl_misconfiguration"):
                        deg = max(deg, 0.4)
                    if p["category"] == "authentication_failures" and meta["name"] == "NAC-Auth":
                        deg = max(deg, 0.7)
                    if p["category"] in ("interface_failure", "power_issues", "vsx_split_brain"):
                        deg = max(deg, 0.5)
            lat = meta.get("tier", 3) * 10 + 20 * diurnal_mult(ctx, ts) + 200 * deg
            loss = 0.01 + 2.0 * deg
            avail = 100 - 15 * deg
            kpi.append({
                "kpi_id": did(seed, "kpi", sid, iso(ts)), "service_id": sid, "observed_at": iso(ts),
                "availability_pct": round(avail, 3), "latency_p50_ms": round(lat * 0.6, 2),
                "latency_p95_ms": round(lat, 2), "loss_pct": round(loss, 3),
                "jitter_ms": round(2 + 20 * deg, 2), "active_users": int(40 * diurnal_mult(ctx, ts) * (1 - 0.5 * deg)),
            })

    save_table(ctx, "if_counter_sample", if_samples, {"interface_id": "interface", "device_id": "device"})
    save_table(ctx, "device_resource_sample", dev_samples, {"device_id": "device"})
    save_table(ctx, "env_sensor_sample", env_samples, {"device_id": "device"})
    save_table(ctx, "power_sample", power_samples, {"device_id": "device", "component_id": "hardware_component"})
    save_table(ctx, "service_kpi_sample", kpi, {"service_id": "service"})
    save_table(ctx, "syslog_event", syslog, {"device_id": "device", "interface_id": "interface"})
    save_table(ctx, "alert", alerts, {"device_id": "device", "correlated_incident_id": "failure_incident"})
    save_table(ctx, "event_correlation", [])
    save_table(ctx, "qos_queue_counter_sample", [])

    # NAE
    scripts = [
        ("link_health", "1.0", "Link health monitor"),
        ("bgp_mon", "1.0", "BGP session monitor"),
        ("hw_health", "1.0", "Hardware health"),
    ]
    scr, agents, mons, pts = [], [], [], []
    for name, ver, desc in scripts:
        sid = did(seed, "naes", name)
        scr.append({"script_id": sid, "script_name": name, "version": ver, "description": desc, "source_ref": "aruba/nae-scripts"})
    for d in devices:
        if d["role"] in ("core", "aggregation", "wan_edge"):
            for name, _, _ in scripts:
                aid = did(seed, "naea", d["hostname"], name)
                agents.append({"agent_id": aid, "device_id": d["device_id"], "script_id": did(seed, "naes", name),
                               "agent_name": f"{name}-agent", "enabled": True,
                               "params": json.dumps({}), "status": "running"})
                mid = did(seed, "naem", aid)
                mons.append({"monitor_id": mid, "agent_id": aid, "monitor_name": "primary",
                             "uri_pattern": "/rest/v10.13/system", "scrape_interval_s": 60})
                # downsample NAE points hourly to limit size
                for t in daterange(ctx.start, ctx.end, 3600):
                    pts.append({"ts_id": did(seed, "naets", mid, iso(t)), "monitor_id": mid,
                                "observed_at": iso(t), "series_type": "Average",
                                "metric_name": "health_score", "metric_value": 0.95,
                                "resource_key": d["hostname"]})
    save_table(ctx, "nae_script", scr)
    save_table(ctx, "nae_agent", agents, {"device_id": "device", "script_id": "nae_script"})
    save_table(ctx, "nae_monitor", mons, {"agent_id": "nae_agent"})
    save_table(ctx, "nae_timeseries_point", pts, {"monitor_id": "nae_monitor"})


def gen_flows(ctx: Ctx):
    seed = ctx.seed
    rng = ctx.rng
    mu = ctx.cfg["statistics"]["flow_lognormal_mu"]
    sigma = ctx.cfg["statistics"]["flow_lognormal_sigma"]
    exporters, flows, aggs = [], [], []
    wan_devs = ctx.tables["device"].query("role=='wan_edge'").to_dict("records")
    apps = ctx.tables["application"].to_dict("records")
    for d in wan_devs:
        eid = did(seed, "ipfix", d["hostname"])
        exporters.append({"exporter_id": eid, "device_id": d["device_id"], "exporter_ip": d["mgmt_ip"],
                          "observation_domain_id": 1, "template_id": 256, "export_interval_s": 60})
        # generate flows each 15 min: 20 flows
        for t in daterange(ctx.start, ctx.end, 900):
            for k in range(20):
                nbytes = int(rng.lognormal(mu, sigma))
                app = apps[k % len(apps)]
                flows.append({
                    "flow_id": did(seed, "flow", d["hostname"], iso(t), k),
                    "exporter_id": eid,
                    "flow_start": iso(t), "flow_end": iso(t + timedelta(seconds=30 + k)),
                    "src_addr": f"10.10.10.{(k % 200)+1}", "dst_addr": f"10.20.30.{(k % 50)+1}",
                    "src_port": 40000 + k, "dst_port": 443 if "web" in app["app_name"] or True else 53,
                    "protocol": 6, "in_packets": max(1, nbytes // 800), "in_bytes": nbytes,
                    "ingress_interface_id": None, "egress_interface_id": None,
                    "tcp_flags": 18, "dscp": app["default_dscp"], "fwd_status": "forwarded",
                    "drop_reason_codes": None, "application_id": app["application_id"],
                    "exported_at": iso(t + timedelta(seconds=60)),
                })
            # 5m aggregates approximate
            for j in range(3):
                bt = t + timedelta(seconds=300 * j)
                if bt > ctx.end:
                    break
                aggs.append({
                    "agg_id": did(seed, "fagg", d["hostname"], iso(bt)),
                    "device_id": d["device_id"], "interface_id": None,
                    "application_id": apps[j % len(apps)]["application_id"],
                    "dscp": apps[j % len(apps)]["default_dscp"],
                    "bytes": int(rng.lognormal(mu + 2, 0.8)), "packets": int(rng.lognormal(6, 0.5)),
                    "flows": 20, "bucket_start": iso(bt),
                })
    save_table(ctx, "ipfix_exporter", exporters, {"device_id": "device"})
    save_table(ctx, "ipfix_record", flows, {"exporter_id": "ipfix_exporter", "application_id": "application"})
    save_table(ctx, "flow_aggregate_5m", aggs, {"device_id": "device", "application_id": "application"})


def gen_graph_and_labels(ctx: Ctx):
    seed = ctx.seed
    # topology snapshots hourly
    topo_pid = ctx.tables["topology_profile"].iloc[0]["topology_profile_id"]
    devices = ctx.tables["device"]
    links = ctx.tables["link"]
    ts_rows, te_rows, gs_rows, gn_rows, ge_rows = [], [], [], [], []
    for t in daterange(ctx.start, ctx.end, ctx.cfg["time"]["topology_cadence_hours"] * 3600):
        tsid = did(seed, "toposnap", iso(t))
        nodes = []
        for _, d in devices.iterrows():
            nid = did(seed, "gnode", "Device", d["device_id"], iso(t))
            nodes.append(nid)
            gn_rows.append({
                "graph_snapshot_id": None,  # fill later
                "_tsid": tsid, "node_id": nid, "node_type": "Device",
                "ref_table": "device", "ref_pk": d["device_id"], "name": d["hostname"],
                "site_id": d["site_id"], "features": json.dumps({"role": d["role"]}),
            })
        # edges from links
        edges = []
        for _, L in links.iterrows():
            a_dev = ctx.interfaces[L["a_interface_id"]]["device_id"]
            b_dev = ctx.interfaces[L["b_interface_id"]]["device_id"]
            eid = did(seed, "gedge", L["link_id"], iso(t))
            edges.append(eid)
            ge_rows.append({
                "graph_snapshot_id": None, "_tsid": tsid, "edge_id": eid,
                "edge_type": "PHYS_LINK" if L["link_layer"] == "phy" else "LAG_LINK",
                "src_node_id": did(seed, "gnode", "Device", a_dev, iso(t)),
                "dst_node_id": did(seed, "gnode", "Device", b_dev, iso(t)),
                "is_directed": False, "weight": 1.0, "link_id": L["link_id"],
                "attrs": json.dumps({"is_uplink": L["is_uplink"], "is_isl": L["is_isl"]}),
            })
            te_rows.append({
                "topology_snapshot_id": tsid, "link_id": L["link_id"],
                "a_node_id": did(seed, "gnode", "Device", a_dev, iso(t)),
                "b_node_id": did(seed, "gnode", "Device", b_dev, iso(t)),
                "edge_type": "PHYS_LINK" if L["link_layer"] == "phy" else "LAG_LINK",
                "attrs": json.dumps({}),
            })
        h = sha16(tsid, len(nodes), len(edges))
        ts_rows.append({"topology_snapshot_id": tsid, "topology_profile_id": topo_pid,
                        "snapshot_at": iso(t), "node_count": len(nodes), "edge_count": len(edges), "hash": h})
        gsid = did(seed, "gsnap", iso(t))
        gs_rows.append({"graph_snapshot_id": gsid, "topology_snapshot_id": tsid,
                        "snapshot_at": iso(t), "schema_version": "1.0.0-SPEC"})
        for r in gn_rows:
            if r.get("_tsid") == tsid:
                r["graph_snapshot_id"] = gsid
        for r in ge_rows:
            if r.get("_tsid") == tsid:
                r["graph_snapshot_id"] = gsid

    for r in gn_rows:
        r.pop("_tsid", None)
    for r in ge_rows:
        r.pop("_tsid", None)
    save_table(ctx, "topology_snapshot", ts_rows, {"topology_profile_id": "topology_profile"})
    save_table(ctx, "topology_edge", te_rows, {"topology_snapshot_id": "topology_snapshot", "link_id": "link"})
    save_table(ctx, "graph_snapshot", gs_rows, {"topology_snapshot_id": "topology_snapshot"})
    save_table(ctx, "graph_node", gn_rows, {"graph_snapshot_id": "graph_snapshot"})
    save_table(ctx, "graph_edge", ge_rows, {"graph_snapshot_id": "graph_snapshot"})

    # Labels
    incidents = ctx.tables["failure_incident"].to_dict("records")
    # T1 anomaly windows: 30-min windows stride 30 on devices
    anom, failh, rca, impact, deg, risk = [], [], [], [], [], []
    for d in ctx.tables["device"].to_dict("records"):
        for t in daterange(ctx.start, ctx.end, 1800):
            t2 = t + timedelta(minutes=30)
            y = False
            inc_id = None
            for inc in incidents:
                onset = parse_iso(inc["onset_at"])
                end = parse_iso(inc["recovered_at"]) if inc["recovered_at"] else parse_iso(inc["onset_at"]) + timedelta(hours=2)
                # device involved?
                ents = ctx.tables["incident_entity"]
                involved = ents[(ents["incident_id"] == inc["incident_id"]) & (ents["entity_id"] == d["device_id"])]
                if len(involved) and not (t2 < onset or t > end):
                    y = True
                    inc_id = inc["incident_id"]
                    break
            anom.append({
                "window_id": did(seed, "aw", d["device_id"], iso(t)),
                "topology_snapshot_id": None, "entity_type": "device", "entity_id": d["device_id"],
                "t_start": iso(t), "t_end": iso(t2), "y_anomaly": y,
                "y_anomaly_score_gt": 0.9 if y else 0.0, "incident_id": inc_id, "point_adjust": False,
            })
            # T2 horizons
            for H in (300, 900, 1800, 3600):
                yf = False
                cat = None
                sev = None
                lead = None
                for inc in incidents:
                    onset = parse_iso(inc["onset_at"])
                    ents = ctx.tables["incident_entity"]
                    involved = ents[(ents["incident_id"] == inc["incident_id"]) & (ents["entity_id"] == d["device_id"])]
                    if len(involved) and t < onset <= t + timedelta(seconds=H):
                        yf = True
                        cat = inc["category"]
                        sev = inc["severity"]
                        lead = (onset - t).total_seconds()
                        break
                failh.append({
                    "sample_id": did(seed, "fh", d["device_id"], iso(t), H),
                    "entity_type": "device", "entity_id": d["device_id"],
                    "t0": iso(t), "horizon_s": H, "y_fail": yf, "y_category": cat,
                    "y_severity": sev, "lead_time_s": lead,
                })

    for inc in incidents:
        rca.append({
            "rca_id": did(seed, "rca", inc["incident_id"]),
            "incident_id": inc["incident_id"], "t_detect": inc["detected_at"],
            "y_category": inc["category"], "y_subcategory": inc["subcategory"],
            "y_root_entity_type": inc["root_entity_type"], "y_root_entity_id": inc["root_entity_id"],
            "y_trigger_type": inc["trigger_type"], "candidate_entity_set": None,
            "hidden_target": False,
        })
        imps = ctx.tables["service_impact"][ctx.tables["service_impact"]["incident_id"] == inc["incident_id"]]
        svcs = list(imps["service_id"]) if len(imps) else []
        impact.append({
            "impact_label_id": did(seed, "implbl", inc["incident_id"]),
            "incident_id": inc["incident_id"], "t0": inc["detected_at"],
            "y_services": json.dumps(svcs),
            "y_max_severity": inc["severity"],
            "y_users_affected": int(imps["users_affected"].sum()) if len(imps) else 0,
            "y_downtime_s": inc["downtime_s"], "y_sla_breach": bool(imps["sla_breach"].any()) if len(imps) else False,
            "blast_radius_nodes": int(len(ctx.tables["incident_entity"][ctx.tables["incident_entity"]["incident_id"] == inc["incident_id"]])),
        })

    # degradation labels hourly per service
    for sid in ctx.services:
        for t in daterange(ctx.start, ctx.end, 3600):
            for H in (1800, 3600):
                # look at future kpi
                future = ctx.tables["service_kpi_sample"]
                future = future[(future["service_id"] == sid) & (future["observed_at"] > iso(t)) &
                                (future["observed_at"] <= iso(t + timedelta(seconds=H)))]
                y = False
                metric = None
                breach = None
                if len(future):
                    if (future["latency_p95_ms"] > 150).any() or (future["availability_pct"] < 99).any():
                        y = True
                        metric = "latency_ms" if (future["latency_p95_ms"] > 150).any() else "availability"
                        breach = float(future["latency_p95_ms"].max())
                deg.append({
                    "deg_id": did(seed, "deg", sid, iso(t), H), "service_id": sid,
                    "t0": iso(t), "horizon_s": H, "y_degrade": y, "y_metric": metric,
                    "y_breach_value": breach, "linked_incident_id": None,
                })

    for _, diff in ctx.tables["config_object_diff"].iterrows():
        tchg = parse_iso(diff["diffed_at"])
        yrisk = False
        cat = None
        for inc in incidents:
            if inc["change_diff_id"] == diff["diff_id"]:
                yrisk = True
                cat = inc["category"]
                break
            onset = parse_iso(inc["onset_at"])
            if inc["trigger_type"] == "change_induced" and tchg < onset <= tchg + timedelta(hours=24):
                # approximate
                pass
        risk.append({
            "risk_id": did(seed, "risk", diff["diff_id"]),
            "diff_id": diff["diff_id"], "after_snapshot_id": diff["after_snapshot_id"],
            "t_change": diff["diffed_at"], "y_risk": yrisk, "y_risk_score": 0.8 if yrisk else 0.05,
            "y_category": cat, "horizon_s": 86400,
        })

    save_table(ctx, "label_anomaly_window", anom)
    save_table(ctx, "label_failure_horizon", failh)
    save_table(ctx, "label_rca", rca, {"incident_id": "failure_incident"})
    save_table(ctx, "label_impact", impact, {"incident_id": "failure_incident"})
    save_table(ctx, "label_degradation", deg, {"service_id": "service"})
    save_table(ctx, "label_config_risk", risk, {"diff_id": "config_object_diff"})

    # anomaly prior sanity
    rate = float(pd.Series([a["y_anomaly"] for a in anom]).mean())
    log_val(ctx, "label_anomaly_window/prior", rate < 0.35, [f"anomaly_rate={rate:.4f} (expect <<0.5)"])


def final_integrity(ctx: Ctx):
    checks = []
    # incident temporal
    inc = ctx.tables["failure_incident"]
    bad = 0
    for _, r in inc.iterrows():
        onset = parse_iso(r["onset_at"])
        det = parse_iso(r["detected_at"])
        if det < onset:
            bad += 1
        if r["recovered_at"]:
            if parse_iso(r["recovered_at"]) < onset:
                bad += 1
    checks.append(f"incident_temporal_ok={bad==0} bad={bad}")
    # counter monotonic sample check on one interface
    ifs = ctx.tables["if_counter_sample"].sort_values(["interface_id", "observed_at"])
    mono_bad = 0
    for iid, g in ifs.groupby("interface_id"):
        diffs = g["in_octets"].diff().dropna()
        if (diffs < 0).any():
            mono_bad += 1
    checks.append(f"counter_monotonic_interfaces_ok={mono_bad==0} bad={mono_bad}")
    # graph endpoints exist (fast set membership)
    gn = ctx.tables["graph_node"]
    ge = ctx.tables["graph_edge"]
    node_keys = set(zip(gn["graph_snapshot_id"].astype(str), gn["node_id"].astype(str)))
    miss = 0
    for a, b in zip(ge["graph_snapshot_id"].astype(str), ge["src_node_id"].astype(str)):
        if (a, b) not in node_keys:
            miss += 1
    for a, b in zip(ge["graph_snapshot_id"].astype(str), ge["dst_node_id"].astype(str)):
        if (a, b) not in node_keys:
            miss += 1
    checks.append(f"graph_endpoints_ok={miss==0} missing={miss}")
    # recovery FK
    acts = ctx.tables["recovery_action"]
    inc_ids = set(inc["incident_id"])
    orphan = sum(1 for x in acts["incident_id"] if x not in inc_ids)
    checks.append(f"recovery_fk_ok={orphan==0}")
    ok = bad == 0 and mono_bad == 0 and miss == 0 and orphan == 0
    log_val(ctx, "FINAL_INTEGRITY", ok, checks)


def export_all(ctx: Ctx):
    import os
    CSV_DIR = gben.CSV_DIR
    PARQ_DIR = gben.PARQ_DIR
    REP_DIR = gben.REP_DIR
    SQLITE_PATH = gben.SQLITE_PATH
    skip_parquet = os.environ.get("ECNETBENCH_SKIP_PARQUET", "").strip() in ("1", "true", "True", "yes")
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    if not skip_parquet:
        PARQ_DIR.mkdir(parents=True, exist_ok=True)
    REP_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_PATH.exists():
        SQLITE_PATH.unlink()
    conn = sqlite3.connect(SQLITE_PATH)
    manifest = []
    for name, df in ctx.tables.items():
        # stringify list-like
        df2 = df.copy()
        if df2.empty:
            # keep schema placeholder for empty optional tables
            if len(df2.columns) == 0:
                df2 = pd.DataFrame({"_placeholder": pd.Series(dtype="object")})
            csv_path = CSV_DIR / f"{name}.csv"
            df2.to_csv(csv_path, index=False)
            pq_bytes = 0
            if not skip_parquet:
                pq_path = PARQ_DIR / f"{name}.parquet"
                df2.to_parquet(pq_path, index=False)
                pq_bytes = pq_path.stat().st_size
            # skip sqlite for zero-column placeholders
            if "_placeholder" not in df2.columns:
                df2.to_sql(name, conn, index=False, if_exists="replace")
            manifest.append({
                "table": name, "rows": 0, "cols": int(len(df.columns)),
                "csv_bytes": csv_path.stat().st_size, "parquet_bytes": pq_bytes,
                "columns": list(df.columns),
            })
            print(f"  exported {name}: 0 rows (empty)")
            continue
        for c in df2.columns:
            if df2[c].dtype == object:
                df2[c] = df2[c].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
        csv_path = CSV_DIR / f"{name}.csv"
        df2.to_csv(csv_path, index=False)
        pq_bytes = 0
        if not skip_parquet:
            pq_path = PARQ_DIR / f"{name}.parquet"
            try:
                df2.to_parquet(pq_path, index=False)
            except Exception:
                df2.astype(str).to_parquet(pq_path, index=False)
            pq_bytes = pq_path.stat().st_size
        df2.to_sql(name, conn, index=False, if_exists="replace")
        manifest.append({
            "table": name, "rows": int(len(df2)), "cols": int(len(df2.columns)),
            "csv_bytes": csv_path.stat().st_size, "parquet_bytes": pq_bytes,
            "columns": list(df2.columns),
        })
        print(f"  exported {name}: {len(df2)} rows")
    conn.close()
    with open(REP_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(REP_DIR / "validation_log.json", "w", encoding="utf-8") as f:
        json.dump(ctx.validation_log, f, indent=2)
    return manifest


def write_reports(ctx: Ctx, manifest: list):
    REP_DIR = gben.REP_DIR
    INST = gben.INST
    CSV_DIR = gben.CSV_DIR
    PARQ_DIR = gben.PARQ_DIR
    SQLITE_PATH = gben.SQLITE_PATH
    ver = ctx.cfg["dataset"].get("version", "INST")
    # Data dictionary
    lines = ["# ECNetBench Data Dictionary\n", f"Generated: seed={ctx.seed}\n",
             f"Version: {ver}\n",
             f"Time range: {iso(ctx.start)} → {iso(ctx.end)}\n",
             f"Profile: {ctx.cfg['dataset']['profile']}\n\n"]
    for m in manifest:
        lines.append(f"## `{m['table']}`\n")
        lines.append(f"- Rows: **{m['rows']}**\n- Columns: **{m['cols']}**\n")
        lines.append(f"- CSV bytes: {m['csv_bytes']}\n- Parquet bytes: {m['parquet_bytes']}\n")
        lines.append("- Columns: " + ", ".join(f"`{c}`" for c in m["columns"]) + "\n\n")
    (REP_DIR / "DATA_DICTIONARY.md").write_text("".join(lines), encoding="utf-8")

    # Validation report
    fails = [v for v in ctx.validation_log if not v["ok"]]
    vr = ["# ECNetBench Validation Report\n\n",
          f"- Tables validated: {len(ctx.validation_log)}\n",
          f"- Failures: {len(fails)}\n",
          f"- Seed: {ctx.seed}\n",
          f"- Version: {ver}\n",
          f"- SQLite: `{SQLITE_PATH}`\n",
          f"- CSV dir: `{CSV_DIR}`\n",
          f"- Parquet dir: `{PARQ_DIR}`\n\n",
          "## Per-table checks\n\n"]
    for v in ctx.validation_log:
        vr.append(f"- **{v['table']}**: {'PASS' if v['ok'] else 'FAIL'} — {'; '.join(v['checks'][:8])}\n")
    # distribution summaries
    vr.append("\n## Distribution summaries\n\n")
    if "if_counter_sample" in ctx.tables and len(ctx.tables["if_counter_sample"]):
        cpu = ctx.tables["device_resource_sample"]["cpu_util_pct"]
        vr.append(f"- CPU util pct: mean={cpu.mean():.2f}, p50={cpu.median():.2f}, p95={cpu.quantile(0.95):.2f}\n")
    if "failure_incident" in ctx.tables:
        vc = ctx.tables["failure_incident"]["category"].value_counts().to_dict()
        vr.append(f"- Incidents by category: `{json.dumps(vc)}`\n")
        vr.append(f"- Incident count: {len(ctx.tables['failure_incident'])}\n")
    if "label_anomaly_window" in ctx.tables:
        rate = ctx.tables["label_anomaly_window"]["y_anomaly"].mean()
        vr.append(f"- Anomaly window positive rate: {rate:.4f}\n")
    (REP_DIR / "VALIDATION_REPORT.md").write_text("".join(vr), encoding="utf-8")

    # README for instance
    (INST / "README.md").write_text(
        f"""# ECNetBench Instance {ver}

Seeded, constraint-driven synthetic enterprise networking dataset.

- **Seed:** {ctx.seed}
- **Version:** {ver}
- **Range:** {iso(ctx.start)} to {iso(ctx.end)}
- **Exports:** `csv/`, `parquet/`, `ecnetbench_v1.sqlite`
- **Reports:** `reports/DATA_DICTIONARY.md`, `reports/VALIDATION_REPORT.md`

Generation uses distributional models (diurnal traffic, lognormal flows/detection latency)
and causal fault injection — not independent Uniform random fields.
""",
        encoding="utf-8",
    )


def main(argv: List[str] | None = None):
    import argparse

    from generate_ecnetbench import set_instance_paths

    parser = argparse.ArgumentParser(description="ECNetBench instance generator")
    parser.add_argument("--seed", type=int, default=None, help="Override config seed")
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Instance output directory (REQUIRED for non-default seeds; never overwrite frozen v1)",
    )
    parser.add_argument("--version", type=str, default=None, help="Dataset version string")
    args = parser.parse_args(argv)

    cfg_path = Path(__file__).parent / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if args.seed is not None:
        cfg["dataset"]["seed"] = int(args.seed)
    if args.version is not None:
        cfg["dataset"]["version"] = args.version

    frozen = (Path(__file__).resolve().parents[1] / "instances" / "v1").resolve()
    if args.out_dir:
        out = Path(args.out_dir).resolve()
        if out == frozen:
            raise SystemExit(
                "Refusing to write to frozen instances/v1. Choose a different --out-dir."
            )
        set_instance_paths(out)
    else:
        if args.seed is not None and int(args.seed) != 20260806:
            raise SystemExit("When using --seed other than 20260806, --out-dir is required.")
        # No out-dir: leave default paths (dangerous for regeneration). Require explicit opt-in.
        if args.seed is not None or args.version is not None:
            raise SystemExit("Refusing to write without --out-dir (protects frozen instances/v1).")
        raise SystemExit("Specify --out-dir (and typically --seed/--version). Frozen v1 must not be overwritten.")

    seed = int(cfg["dataset"]["seed"])
    start = parse_iso(cfg["time"]["start"])
    end = start + timedelta(days=int(cfg["time"]["days"]))
    ctx = Ctx(cfg=cfg, seed=seed, rng=np.random.default_rng(seed), start=start, end=end)

    from realism_upgrade import (
        gen_graph_and_labels_v2,
        gen_l3_state,
        gen_telemetry_v2,
        patch_stp_blocking,
    )

    print(f"=== ECNetBench generate seed={seed} version={cfg['dataset']['version']} ===")
    print(f"=== Output: {gben.INST} ===")
    print("=== PHASE 1: org/sites ===")
    gen_org_sites(ctx)
    print("=== PHASE 2: inventory/topology ===")
    gen_inventory_topology(ctx)
    print("=== PHASE 3: config/policy ===")
    gen_config_policy(ctx)
    print("=== PHASE 3b: STP blocking ports ===")
    patch_stp_blocking(ctx)
    print("=== PHASE 4: users/services ===")
    gen_services_users(ctx)
    print("=== PHASE 4b: L3 ARP/MAC/RIB/FIB ===")
    gen_l3_state(ctx)
    print("=== PHASE 5: incidents (GT timeline) ===")
    gen_incidents_and_effects(ctx)
    print("=== PHASE 6: telemetry/events/state samples (v2) ===")
    gen_telemetry_v2(ctx)
    print("=== PHASE 7: flows ===")
    gen_flows(ctx)
    print("=== PHASE 8: graph + labels (v2) ===")
    gen_graph_and_labels_v2(ctx)
    print("=== PHASE 9: final integrity ===")
    final_integrity(ctx)
    print("=== PHASE 10: export ===")
    manifest = export_all(ctx)
    write_reports(ctx, manifest)
    print("DONE. Tables:", len(manifest), "SQLite:", gben.SQLITE_PATH)


if __name__ == "__main__":
    main()
