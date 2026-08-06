"""Realism upgrades for ECNetBench v1.1 — temporal state, L3, events, graph, telemetry gaps."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd

from generate_ecnetbench import Ctx, diurnal_mult, log_val, save_table
from util import clamp, daterange, did, iso, parse_iso, sha16


def patch_stp_blocking(ctx: Ctx):
    """Introduce realistic alternate/blocking ports on redundant access uplinks."""
    stp_p = ctx.tables["stp_port"].to_dict("records")
    iface = {r["interface_id"]: r for r in ctx.tables["interface"].to_dict("records")}
    changed = 0
    for r in stp_p:
        ifr = iface.get(r["interface_id"], {})
        # Second uplink on access switches becomes alternate/blocking
        if ifr.get("description") == "uplink" and ifr.get("if_name") == "1/1/26":
            r["port_role"] = "alternate"
            r["port_state"] = "blocking"
            changed += 1
    ctx.tables["stp_port"] = pd.DataFrame(stp_p)
    print(f"  STP blocking/alternate ports set: {changed}")


def gen_l3_state(ctx: Ctx):
    seed = ctx.seed
    devices = ctx.tables["device"].to_dict("records")
    interfaces = ctx.tables["interface"].to_dict("records")
    endpoints = ctx.tables["endpoint"].to_dict("records")
    svis = [r for r in interfaces if r["if_type"] == "vlan_svi" and r.get("ipv4_address")]

    static_r, rib, fib, arp, macs = [], [], [], [], []

    # Static default on branch wan toward HQ
    for d in devices:
        if d["hostname"] == "br-wan-edge":
            vrf = did(seed, "vrf", d["hostname"], "default")
            wan_if = next(r["interface_id"] for r in interfaces if r["device_id"] == d["device_id"] and r["if_name"] == "1/1/2")
            static_r.append({
                "static_id": did(seed, "static", d["hostname"], "default"),
                "vrf_id": vrf, "prefix": "0.0.0.0/0", "next_hop": "172.16.0.1",
                "outgoing_interface_id": wan_if, "admin_distance": 1, "is_floating": False,
            })
        if d["hostname"] == "hq-wan-edge":
            vrf = did(seed, "vrf", d["hostname"], "default")
            wan_if = next(r["interface_id"] for r in interfaces if r["device_id"] == d["device_id"] and r["if_name"] == "1/1/2")
            static_r.append({
                "static_id": did(seed, "static", d["hostname"], "branch"),
                "vrf_id": vrf, "prefix": "10.20.0.0/16", "next_hop": "172.16.0.2",
                "outgoing_interface_id": wan_if, "admin_distance": 1, "is_floating": False,
            })

    # RIB/FIB samples every 6h on L3 devices
    l3devs = [d for d in devices if d["role"] in ("core", "aggregation", "wan_edge")]
    prefixes = [
        ("10.10.10.0/24", "connected", 0),
        ("10.10.20.0/24", "connected", 0),
        ("10.10.30.0/24", "connected", 0),
        ("10.10.100.0/24", "connected", 0),
        ("10.20.10.0/24", "bgp", 20),
        ("172.16.0.0/30", "connected", 0),
        ("0.0.0.0/0", "static", 1),
    ]
    for d in l3devs:
        vrf = did(seed, "vrf", d["hostname"], "default")
        # pick an SVI or uplink as egress
        eg = next((r for r in interfaces if r["device_id"] == d["device_id"] and r["if_type"] == "vlan_svi"), None)
        if eg is None:
            eg = next((r for r in interfaces if r["device_id"] == d["device_id"] and r["if_type"] == "ethernet"), None)
        for t in daterange(ctx.start, ctx.end, 6 * 3600):
            for pref, proto, metric in prefixes:
                if pref.startswith("10.20") and d["hostname"].startswith("hq") is False and "wan" not in d["hostname"]:
                    continue
                rib.append({
                    "rib_sample_id": did(seed, "rib", d["hostname"], pref, iso(t)),
                    "device_id": d["device_id"], "vrf_id": vrf, "prefix": pref,
                    "protocol": proto,
                    "next_hop": "172.16.0.1" if proto != "connected" else None,
                    "metric": metric, "sampled_at": iso(t),
                })
                fib.append({
                    "fib_sample_id": did(seed, "fib", d["hostname"], pref, iso(t)),
                    "device_id": d["device_id"], "vrf_id": vrf, "prefix": pref,
                    "egress_interface_id": eg["interface_id"] if eg else None,
                    "next_hop": "172.16.0.1" if proto != "connected" else None,
                    "drop_flag": False, "sampled_at": iso(t),
                })

    # ARP + MAC tables from endpoints (wired + wireless via AP uplink)
    ap_uplink = {}
    if "access_point" in ctx.tables and not ctx.tables["access_point"].empty:
        for _, ap in ctx.tables["access_point"].iterrows():
            up_if = ap.get("eth_uplink_interface_id")
            if up_if and up_if in ctx.interfaces:
                peer = ctx.interfaces[up_if]
                # uplink interface on AP side — find switch peer via link
                for _, L in ctx.tables["link"].iterrows():
                    if L["a_interface_id"] == up_if:
                        peer = ctx.interfaces[L["b_interface_id"]]
                        ap_uplink[ap["ap_id"]] = (peer["device_id"], L["b_interface_id"])
                        break
                    if L["b_interface_id"] == up_if:
                        peer = ctx.interfaces[L["a_interface_id"]]
                        ap_uplink[ap["ap_id"]] = (peer["device_id"], L["a_interface_id"])
                        break
            # fallback: AP device ethernet linked to access
            if ap["ap_id"] not in ap_uplink:
                ap_dev = ap.get("device_id")
                for r in interfaces:
                    if r["device_id"] == ap_dev and r["if_type"] == "ethernet":
                        for _, L in ctx.tables["link"].iterrows():
                            if L["a_interface_id"] == r["interface_id"]:
                                peer = ctx.interfaces[L["b_interface_id"]]
                                ap_uplink[ap["ap_id"]] = (peer["device_id"], L["b_interface_id"])
                                break
                            if L["b_interface_id"] == r["interface_id"]:
                                peer = ctx.interfaces[L["a_interface_id"]]
                                ap_uplink[ap["ap_id"]] = (peer["device_id"], L["a_interface_id"])
                                break
                        break

    for ep in endpoints:
        if not ep.get("ip_address") or not ep.get("mac"):
            continue
        # attach device from interface or AP uplink switch
        dev_id = None
        if_id = ep.get("attached_interface_id")
        if if_id:
            ifr = next((r for r in interfaces if r["interface_id"] == if_id), None)
            if ifr:
                dev_id = ifr["device_id"]
        elif ep.get("ap_id") and ep["ap_id"] in ap_uplink:
            dev_id, if_id = ap_uplink[ep["ap_id"]]
        if not dev_id:
            continue
        vlan_key = ep.get("vlan_id_key")
        vlan_id = 10
        if vlan_key and "vlan" in ctx.tables:
            vr = ctx.tables["vlan"][ctx.tables["vlan"]["vlan_id_key"] == vlan_key]
            if len(vr):
                vlan_id = int(vr.iloc[0]["vlan_id"])
        arp.append({
            "arp_id": did(seed, "arp", ep["endpoint_id"]),
            "device_id": dev_id,
            "vrf_id": did(seed, "vrf", ctx.devices[dev_id]["hostname"], "default") if dev_id in ctx.devices else None,
            "ip_address": ep["ip_address"],
            "mac_address": ep["mac"],
            "interface_id": if_id,
            "vlan_id": vlan_id,
            "entry_type": "dynamic",
            "age_s": 60 + (int(sha16(ep["endpoint_id"])[:4], 16) % 500),
            "observed_at": iso(ctx.end),
        })
        macs.append({
            "mac_entry_id": did(seed, "mact", ep["endpoint_id"]),
            "device_id": dev_id,
            "mac_address": ep["mac"],
            "vlan_id": vlan_id,
            "interface_id": if_id,
            "entry_type": "dynamic",
            "is_local": False,
            "observed_at": iso(ctx.end),
        })

    # Also MAC for each interface itself (local)
    for r in interfaces:
        if r.get("mac_address") and r["if_type"] in ("ethernet", "lag", "vlan_svi"):
            macs.append({
                "mac_entry_id": did(seed, "mactlocal", r["interface_id"]),
                "device_id": r["device_id"],
                "mac_address": r["mac_address"],
                "vlan_id": r.get("native_vlan_id") or 1,
                "interface_id": r["interface_id"],
                "entry_type": "static",
                "is_local": True,
                "observed_at": iso(ctx.start),
            })

    save_table(ctx, "static_route", static_r, {"vrf_id": "routing_instance", "outgoing_interface_id": "interface"})
    save_table(ctx, "rib_entry_sample", rib, {"device_id": "device"})
    save_table(ctx, "fib_entry_sample", fib, {"device_id": "device", "egress_interface_id": "interface"})
    save_table(ctx, "arp_entry", arp, {"device_id": "device", "interface_id": "interface"})
    save_table(ctx, "mac_address_table", macs, {"device_id": "device", "interface_id": "interface"})


def gen_telemetry_v2(ctx: Ctx):
    """Telemetry with gaps, richer events, temporal control-plane/interface/VSX/STP/BGP state."""
    seed = ctx.seed
    rng = ctx.rng
    cadence = ctx.cfg["time"]["telemetry_cadence_s"]
    stats = ctx.cfg["statistics"]
    plan = ctx.incidents
    devices = ctx.tables["device"].to_dict("records")
    interfaces = [r for r in ctx.tables["interface"].to_dict("records") if r["if_type"] in ("ethernet", "lag")]
    all_ifs = ctx.tables["interface"].to_dict("records")
    qos_queues = ctx.tables["qos_queue"].to_dict("records") if "qos_queue" in ctx.tables else []
    bgp_nei = ctx.tables["bgp_neighbor"].to_dict("records")
    vsx_rows = ctx.tables["vsx_pair"].to_dict("records")
    stp_ports = ctx.tables["stp_port"].to_dict("records")

    cum = {
        r["interface_id"]: {
            "in_o": 0, "out_o": 0, "in_u": 0, "out_u": 0, "in_b": 0, "out_b": 0,
            "in_m": 0, "out_m": 0, "in_d": 0, "out_d": 0, "in_e": 0, "out_e": 0,
            "fcs": 0, "carrier": 0,
        }
        for r in interfaces
    }

    if_samples, dev_samples, env_samples, power_samples = [], [], [], []
    syslog, alerts, corr = [], [], []
    kpi = []
    if_state, bgp_state, vsx_state, stp_state = [], [], [], []
    qos_cs = []

    comps = ctx.tables["hardware_component"].to_dict("records")
    psu_by_dev = defaultdict(list)
    for c in comps:
        if c["component_type"] == "psu":
            psu_by_dev[c["device_id"]].append(c)

    def base_mbps(desc, role):
        if desc == "isl":
            return 800.0
        if desc in ("uplink", "downlink"):
            return 200.0 if role == "access" else 600.0
        if desc == "wan":
            return 80.0
        if desc == "access":
            return 15.0
        return 5.0

    def incident_overlay(plan, ts, interface_id, device_id):
        mod = {"oper_down": False, "util_boost": 0.0, "err_boost": 0.0, "disc_boost": 0.0,
               "cpu_boost": 0.0, "bcast_boost": 0.0, "carrier_boost": 0, "psu_fail": False}
        for p in plan:
            if not (p["onset"] <= ts <= p.get("rec_end", p["onset"])):
                continue
            cat = p["category"]
            hit = p["interface_id"] == interface_id or p["device_id"] == device_id
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
                mod["oper_down"] = ts >= p["onset"] + timedelta(minutes=2)
            if cat == "stp_loop":
                mod["bcast_boost"] = 5000
                mod["cpu_boost"] = 45
            if cat == "routing_instability" and p["device_id"] == device_id:
                mod["cpu_boost"] = 20
            if cat == "qos_problems" and p["interface_id"] == interface_id:
                mod["disc_boost"] = 30
                mod["util_boost"] = 0.2
            if cat == "hardware_degradation" and p["device_id"] == device_id:
                mod["err_boost"] = 15
            if cat == "power_issues" and p["device_id"] == device_id:
                mod["psu_fail"] = True
                mod["oper_down"] = True
            if cat == "intermittent_failures" and p["interface_id"] == interface_id:
                mod["oper_down"] = (int(ts.timestamp()) // 300) % 2 == 0
                mod["carrier_boost"] = 3
            if cat == "vsx_split_brain" and p["device_id"] == device_id:
                mod["oper_down"] = True
            if cat in ("acl_misconfiguration", "vlan_mismatch") and p["interface_id"] == interface_id:
                mod["disc_boost"] = 20
        return mod

    times = list(daterange(ctx.start, ctx.end, cadence))
    print(f"  telemetry_v2 timesteps: {len(times)}, interfaces: {len(interfaces)}")

    alert_seq = 0
    emitted_onset = set()
    emitted_rec = set()
    all_if_map = {r["interface_id"]: r for r in all_ifs}
    qos_bind_rows = ctx.tables["qos_binding"].to_dict("records") if "qos_binding" in ctx.tables else []
    default_qif = interfaces[0]["interface_id"] if interfaces else None

    for ti, ts in enumerate(times):
        if ti % 500 == 0:
            print(f"    t-step {ti}/{len(times)}")

        # Drop ~2% of poll cycles globally (collector loss)
        drop_cycle = (rng.random() < 0.02)
        # Delayed poll: shift observed_at by 0-45s sometimes
        delay_s = int(rng.integers(0, 46)) if rng.random() < 0.08 else 0
        obs_ts = ts + timedelta(seconds=delay_s)

        if not drop_cycle:
            for d in devices:
                # per-device miss ~1%
                if rng.random() < 0.01:
                    continue
                role = d["role"]
                cpu_base = stats["cpu_base_by_role"].get(role, 15.0)
                hour_m = diurnal_mult(ctx, ts)
                cpu = cpu_base * (0.7 + 0.6 * hour_m)
                for p in plan:
                    if p["device_id"] == d["device_id"] and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                        md = incident_overlay(plan, ts, p["interface_id"], d["device_id"])
                        cpu += md["cpu_boost"]
                        if md["psu_fail"]:
                            cpu = min(cpu, 5)
                cpu = clamp(cpu + float(rng.normal(0, 1.2)), 1.0, 99.0)
                mem_total = 8_000_000_000 if role != "ap" else 2_000_000_000
                mem_util = clamp(35 + 10 * hour_m + float(rng.normal(0, 1.0)), 10, 92)
                dev_samples.append({
                    "sample_id": did(seed, "devres", d["hostname"], iso(obs_ts), ti),
                    "device_id": d["device_id"], "observed_at": iso(obs_ts),
                    "cpu_util_pct": round(cpu, 3), "cpu_util_user_pct": round(cpu * 0.4, 3),
                    "cpu_util_system_pct": round(cpu * 0.6, 3),
                    "mem_used_bytes": int(mem_total * mem_util / 100),
                    "mem_total_bytes": mem_total, "mem_util_pct": round(mem_util, 3),
                    "process_count": 120 + int(role == "core") * 40,
                    "control_plane_drop_pct": 0.0,
                })
                # Temperature: continuous sensor with device bias + fine noise
                ambient = 22.0 + 3.0 * math.sin(2 * math.pi * (ts.timetuple().tm_yday / 365))
                bias = (int(sha16(d["hostname"])[:4], 16) % 200) / 100.0  # 0–2C per device
                temp = (
                    ambient + bias + 18 * (cpu / 100)
                    + float(rng.normal(0, 0.85))
                    + 0.25 * math.sin(ts.timestamp() / 700.0)
                    + 0.08 * math.sin(ts.timestamp() / 113.0)
                )
                env_samples.append({
                    "sample_id": did(seed, "env", d["hostname"], "temp", iso(obs_ts), ti),
                    "device_id": d["device_id"], "component_id": None, "observed_at": iso(obs_ts),
                    "sensor_type": "temperature", "value": round(temp, 3), "unit": "C",
                    "threshold_warning": 70, "threshold_critical": 85,
                    "status": "crit" if temp > 85 else ("warn" if temp > 70 else "ok"),
                })
                for psu in psu_by_dev.get(d["device_id"], [])[:2]:
                    fail = False
                    for p in plan:
                        if p["category"] == "power_issues" and p["device_id"] == d["device_id"] and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                            fail = psu["name"] == "PSU1"
                    power_samples.append({
                        "sample_id": did(seed, "pwr", psu["component_id"], iso(obs_ts), ti),
                        "device_id": d["device_id"], "component_id": psu["component_id"],
                        "observed_at": iso(obs_ts), "input_power_w": 0 if fail else round(110 + float(rng.normal(0, 3)), 2),
                        "output_power_w": 0 if fail else round(95 + float(rng.normal(0, 2)), 2),
                        "psu_status": "failed" if fail else "ok",
                        "redundant_ok": not fail,
                    })

            for r in interfaces:
                if rng.random() < 0.015:  # per-interface miss
                    continue
                desc = r["description"] or "other"
                role = ctx.devices[r["device_id"]]["role"]
                speed = r["speed_bps"] or 1_000_000_000
                mbps = base_mbps(desc, role) * diurnal_mult(ctx, ts)
                factor = 0.5 + (int(sha16(r["interface_id"])[:4], 16) % 1000) / 1000.0
                mbps *= factor
                mod = incident_overlay(plan, ts, r["interface_id"], r["device_id"])
                mbps = mbps * (1.0 + mod["util_boost"]) + mod["util_boost"] * (speed / 1e6) * 0.5
                oper_down = mod["oper_down"]
                admin_down = False
                # during recovery window after rec_start, admin up / oper recovering
                for p in plan:
                    if p["interface_id"] == r["interface_id"] and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                        if p["category"] in ("interface_failure", "cable_failure", "power_issues", "vsx_split_brain"):
                            if ts < p.get("rec_start", p["onset"]):
                                admin_down = p["category"] == "interface_failure"
                                oper_down = True
                            else:
                                admin_down = False
                                oper_down = ts < p.get("rec_start", p["onset"]) + timedelta(minutes=2)
                if oper_down:
                    mbps = 0.0
                util = clamp(mbps * 1e6 / speed, 0.0, 0.99)
                interval = cadence
                out_bytes = int(util * speed * interval / 8 * 0.55)
                in_bytes = int(util * speed * interval / 8 * 0.45)
                pkts = max(1, int((in_bytes + out_bytes) / 800)) if not oper_down else 0
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
                c["carrier"] += int(mod["carrier_boost"]) + (1 if oper_down else 0)
                if_samples.append({
                    "sample_id": did(seed, "ifc", r["interface_id"], iso(obs_ts), ti),
                    "interface_id": r["interface_id"], "device_id": r["device_id"],
                    "observed_at": iso(obs_ts),
                    "in_octets": c["in_o"], "out_octets": c["out_o"],
                    "in_unicast_pkts": c["in_u"], "out_unicast_pkts": c["out_u"],
                    "in_broadcast_pkts": c["in_b"], "out_broadcast_pkts": c["out_b"],
                    "in_multicast_pkts": c["in_m"], "out_multicast_pkts": c["out_m"],
                    "in_discards": c["in_d"], "out_discards": c["out_d"],
                    "in_errors": c["in_e"], "out_errors": c["out_e"],
                    "in_fcs_errors": c["fcs"], "in_unknown_protos": 0,
                    "carrier_transitions": c["carrier"], "last_clear_at": None,
                })
                # interface state sample each tick for faulted ifs; hourly for all
                if oper_down or admin_down or (ti % 12 == 0):
                    if_state.append({
                        "sample_id": did(seed, "ifst", r["interface_id"], iso(obs_ts), ti),
                        "interface_id": r["interface_id"], "device_id": r["device_id"],
                        "observed_at": iso(obs_ts),
                        "admin_status": "down" if admin_down else "up",
                        "oper_status": "down" if oper_down else "up",
                    })

            # QoS queue counters hourly on bound uplinks
            if ti % 12 == 0 and qos_queues:
                for q in qos_queues[:40]:
                    drops = 0
                    for p in plan:
                        if p["category"] == "qos_problems" and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                            drops = int(50 + rng.integers(0, 200))
                    qif = default_qif
                    for b in qos_bind_rows:
                        qif = b["interface_id"]
                        break
                    qos_cs.append({
                        "sample_id": did(seed, "qoscnt", q["qos_queue_id"], iso(obs_ts)),
                        "qos_queue_id": q["qos_queue_id"],
                        "interface_id": qif,
                        "observed_at": iso(obs_ts),
                        "tx_packets": int(10000 + rng.integers(0, 5000)),
                        "tx_drops": drops,
                        "ecn_marked": int(drops * 0.1),
                        "latency_estimate_us": float(max(50.0, 200 + drops * 5 + float(rng.normal(0, 10)))),
                    })

        # Service KPIs (also allow sparse misses)
        if rng.random() >= 0.01:
            for sid, meta in ctx.services.items():
                deg = 0.0
                linked = None
                for p in plan:
                    if p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                        if p["category"] in ("congestion", "qos_problems", "stp_loop", "routing_instability", "acl_misconfiguration"):
                            deg = max(deg, 0.4)
                            linked = p["incident_id"]
                        if p["category"] == "authentication_failures" and meta["name"] == "NAC-Auth":
                            deg = max(deg, 0.7)
                            linked = p["incident_id"]
                        if p["category"] in ("interface_failure", "power_issues", "vsx_split_brain"):
                            deg = max(deg, 0.5)
                            linked = p["incident_id"]
                lat = meta.get("tier", 3) * 10 + 20 * diurnal_mult(ctx, ts) + 200 * deg + float(rng.normal(0, 3))
                loss = 0.01 + 2.0 * deg
                avail = 100 - 15 * deg
                kpi.append({
                    "kpi_id": did(seed, "kpi", sid, iso(ts), ti), "service_id": sid, "observed_at": iso(ts),
                    "availability_pct": round(avail, 3), "latency_p50_ms": round(max(1, lat * 0.6), 2),
                    "latency_p95_ms": round(max(1, lat), 2), "loss_pct": round(max(0, loss), 3),
                    "jitter_ms": round(max(0, 2 + 20 * deg + float(rng.normal(0, 0.3))), 2),
                    "active_users": int(40 * diurnal_mult(ctx, ts) * (1 - 0.5 * deg)),
                    "_linked_incident_id": linked,
                })

        # --- Temporal BGP / VSX / STP state (every tick, lightweight) ---
        for bn in bgp_nei:
            state = "established"
            prefs = 12
            for p in plan:
                if p["category"] == "routing_instability" and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                    # flap pattern
                    slot = int((ts - p["onset"]).total_seconds() // 300)
                    state = "idle" if slot % 2 == 0 else "active"
                    rs = p.get("rec_start", p["onset"])
                    if ts >= rs:
                        state = "opensent" if ts < rs + timedelta(minutes=3) else "established"
                    prefs = 0 if state != "established" else 12
            if ti % 3 == 0 or state != "established":
                bgp_state.append({
                    "sample_id": did(seed, "bgps", bn["bgp_neighbor_id"], iso(ts), ti),
                    "bgp_neighbor_id": bn["bgp_neighbor_id"],
                    "observed_at": iso(ts),
                    "session_state": state,
                    "prefixes_received": prefs,
                    "prefixes_sent": 8 if state == "established" else 0,
                })

        for vr in vsx_rows:
            st = "sync"
            for p in plan:
                if p["category"] != "vsx_split_brain":
                    continue
                if not (p["onset"] <= ts <= p.get("rec_end", p["onset"])):
                    continue
                members = (vr["member_a_device_id"], vr["member_b_device_id"])
                same_site = ctx.devices.get(p["device_id"], {}).get("site_id") == vr.get("site_id")
                if p["device_id"] in members or same_site:
                    rs = p.get("rec_start", p["onset"])
                    if ts < rs:
                        st = "split"
                    else:
                        st = "sync_progress" if ts < rs + timedelta(minutes=10) else "sync"
            if ti % 6 == 0 or st != "sync":
                vsx_state.append({
                    "sample_id": did(seed, "vsxs", vr["vsx_pair_id"], iso(ts), ti),
                    "vsx_pair_id": vr["vsx_pair_id"],
                    "observed_at": iso(ts),
                    "oper_state": st,
                })

        for sp in stp_ports:
            role, pstate = sp["port_role"], sp["port_state"]
            ifr = all_if_map.get(sp["interface_id"], {})
            for p in plan:
                if p["category"] == "stp_loop" and p["onset"] <= ts <= p.get("rec_end", p["onset"]):
                    if sp["interface_id"] == p["interface_id"] or (ti % 2 == 0):
                        pstate = "learning" if ts < p.get("rec_start", p["onset"]) else "forwarding"
                        if sp.get("port_role") == "alternate" and ts < p.get("rec_start", p["onset"]):
                            role = "designated"
                            pstate = "forwarding"
                    if ts >= p.get("rec_start", p["onset"]):
                        if sp.get("port_role") == "alternate" or ifr.get("if_name") == "1/1/26":
                            role, pstate = "alternate", "blocking"
            if ti % 12 == 0 or pstate != sp["port_state"] or role != sp["port_role"]:
                stp_state.append({
                    "sample_id": did(seed, "stps", sp["stp_port_id"], iso(ts), ti),
                    "stp_port_id": sp["stp_port_id"],
                    "interface_id": sp["interface_id"],
                    "observed_at": iso(ts),
                    "port_role": role,
                    "port_state": pstate,
                })

        # --- Syslog bursts & alerts around incidents (once per phase) ---
        for p in plan:
            if p["incident_id"] not in emitted_onset and abs((ts - p["onset"]).total_seconds()) < cadence:
                emitted_onset.add(p["incident_id"])
                syslog.extend(_syslog_burst(seed, p, ts, "onset"))
                if rng.random() > 0.05:
                    alert_seq += 1
                    alerts.append(_alert(seed, p, alert_seq, raised=p["detected"], cleared=p["rec_end"],
                                         atype=p["category"], fp=False, title=f"{p['category']} detected"))
                    if rng.random() < 0.25:
                        alert_seq += 1
                        alerts.append(_alert(seed, p, alert_seq,
                                             raised=p["detected"] + timedelta(seconds=30),
                                             cleared=p["detected"] + timedelta(minutes=2),
                                             atype=p["category"], fp=False, title=f"{p['category']} re-raised"))
                    if rng.random() < 0.2:
                        alert_seq += 1
                        alerts.append(_alert(seed, p, alert_seq,
                                             raised=p["detected"] + timedelta(minutes=1),
                                             cleared=p["detected"] + timedelta(minutes=3),
                                             atype=p["category"], fp=False, title=f"{p['category']} flap"))
                corr.append({
                    "corr_id": did(seed, "corr", p["incident_id"]),
                    "created_at": iso(p["detected"]),
                    "window_start": iso(p["onset"] - timedelta(minutes=5)),
                    "window_end": iso(p["rec_end"]),
                    "member_alert_ids": None,
                    "member_syslog_ids": None,
                    "hypothesis": p["category"],
                    "confidence": 0.85,
                })
            if p["incident_id"] not in emitted_rec and abs((ts - p.get("rec_start", p["onset"])).total_seconds()) < cadence:
                emitted_rec.add(p["incident_id"])
                syslog.extend(_syslog_burst(seed, p, ts, "recovery"))

        # False-positive high-CPU noise once per night around 03:00
        if ts.hour == 3 and ts.minute < 5:
            alert_seq += 1
            victim = devices[int(rng.integers(0, len(devices)))]
            alerts.append({
                "alert_id": did(seed, "alfp", alert_seq, iso(ts)),
                "device_id": victim["device_id"], "interface_id": None,
                "raised_at": iso(ts), "cleared_at": iso(ts + timedelta(minutes=15)),
                "alert_type": "high_cpu", "severity": "warning",
                "title": "Transient high CPU (cleared)", "body": "noise",
                "source_system": "nms", "correlated_incident_id": None,
                "is_false_positive_gt": True,
            })

    scripts = [("link_health", "1.0", "Link health"), ("bgp_mon", "1.0", "BGP monitor"), ("hw_health", "1.0", "Hardware")]
    scr, agents, mons, pts = [], [], [], []
    for name, ver, desc in scripts:
        scr.append({"script_id": did(seed, "naes", name), "script_name": name, "version": ver,
                    "description": desc, "source_ref": "aruba/nae-scripts"})
    for d in devices:
        if d["role"] in ("core", "aggregation", "wan_edge"):
            for name, _, _ in scripts:
                aid = did(seed, "naea", d["hostname"], name)
                agents.append({"agent_id": aid, "device_id": d["device_id"], "script_id": did(seed, "naes", name),
                               "agent_name": f"{name}-agent", "enabled": True, "params": json.dumps({}), "status": "running"})
                mid = did(seed, "naem", aid)
                mons.append({"monitor_id": mid, "agent_id": aid, "monitor_name": "primary",
                             "uri_pattern": "/rest/v10.13/system", "scrape_interval_s": 60})
                for t in daterange(ctx.start, ctx.end, 3600):
                    score = 0.95
                    for p in plan:
                        if p["device_id"] == d["device_id"] and p["onset"] <= t <= p.get("rec_end", p["onset"]):
                            score = 0.4
                    pts.append({"ts_id": did(seed, "naets", mid, iso(t)), "monitor_id": mid,
                                "observed_at": iso(t), "series_type": "Average",
                                "metric_name": "health_score", "metric_value": score,
                                "resource_key": d["hostname"]})

    # Update current interface/bgp/vsx tables to end-state (all healthy)
    iface_df = ctx.tables["interface"].copy()
    iface_df["admin_status"] = "up"
    iface_df["oper_status"] = "up"
    ctx.tables["interface"] = iface_df
    bgp_df = ctx.tables["bgp_neighbor"].copy()
    bgp_df["session_state"] = "established"
    ctx.tables["bgp_neighbor"] = bgp_df
    vsx_df = ctx.tables["vsx_pair"].copy()
    vsx_df["oper_state"] = "sync"
    ctx.tables["vsx_pair"] = vsx_df

    for k in kpi:
        k.pop("_linked_incident_id", None)

    save_table(ctx, "if_counter_sample", if_samples, {"interface_id": "interface", "device_id": "device"})
    save_table(ctx, "device_resource_sample", dev_samples, {"device_id": "device"})
    save_table(ctx, "env_sensor_sample", env_samples, {"device_id": "device"})
    save_table(ctx, "power_sample", power_samples, {"device_id": "device", "component_id": "hardware_component"})
    save_table(ctx, "service_kpi_sample", kpi, {"service_id": "service"})
    save_table(ctx, "syslog_event", syslog, {"device_id": "device", "interface_id": "interface"})
    save_table(ctx, "alert", alerts, {"device_id": "device"})
    save_table(ctx, "event_correlation", corr)
    save_table(ctx, "qos_queue_counter_sample", qos_cs, {"qos_queue_id": "qos_queue", "interface_id": "interface"})
    save_table(ctx, "interface_state_sample", if_state, {"interface_id": "interface", "device_id": "device"})
    save_table(ctx, "bgp_session_sample", bgp_state, {"bgp_neighbor_id": "bgp_neighbor"})
    save_table(ctx, "vsx_state_sample", vsx_state, {"vsx_pair_id": "vsx_pair"})
    save_table(ctx, "stp_port_sample", stp_state, {"stp_port_id": "stp_port", "interface_id": "interface"})
    save_table(ctx, "nae_script", scr)
    save_table(ctx, "nae_agent", agents, {"device_id": "device", "script_id": "nae_script"})
    save_table(ctx, "nae_monitor", mons, {"agent_id": "nae_agent"})
    save_table(ctx, "nae_timeseries_point", pts, {"monitor_id": "nae_monitor"})


def _syslog_burst(seed, p, ts, phase: str) -> List[dict]:
    """Multi-message syslog stream for an incident phase."""
    base = [
        ("port", "LINK_DOWN" if phase == "onset" else "LINK_UP", 3 if phase == "onset" else 5,
         f"Interface event ({p['category']}) {phase}"),
        ("lacp", "LACP_STATE", 4, f"LACP state change during {p['category']}"),
        ("hpe-smm", "EVENT", 5, f"NAE correlated symptom for {p['category']}"),
    ]
    if p["category"] == "routing_instability":
        base += [("bgp", "BGP_DOWN" if phase == "onset" else "BGP_UP", 3, "BGP neighbor state change"),
                 ("bfd", "BFD_SESSION", 3, "BFD session down/up")]
    if p["category"] == "stp_loop":
        base += [("stp", "TOPOLOGY_CHANGE", 2, "STP topology change storm"),
                 ("mac", "MAC_FLAP", 3, "MAC flapping detected")]
    if p["category"] == "vsx_split_brain":
        base += [("vsx", "VSX_SPLIT", 2, "VSX sync lost"), ("vsx", "KEEPALIVE", 3, "VSX keepalive failure")]
    if p["category"] == "authentication_failures":
        base += [("aaa", "RADIUS_TIMEOUT", 3, "RADIUS server unreachable"),
                 ("aaa", "AUTH_FAIL", 4, "802.1X authentication failure")]
    out = []
    for i, (app, code, sev, msg) in enumerate(base):
        out.append({
            "syslog_id": did(seed, "log", p["incident_id"], phase, i),
            "device_id": p["device_id"],
            "observed_at": iso(ts + timedelta(seconds=i * 2)),
            "received_at": iso(ts + timedelta(seconds=i * 2 + 1)),
            "facility": "local0", "severity": sev,
            "severity_label": {0: "emerg", 1: "alert", 2: "crit", 3: "err", 4: "warning", 5: "notice"}.get(sev, "info"),
            "app_name": app, "msg_id": code, "event_code": code,
            "message": f"{msg} host={p['hostname']}",
            "structured_data": json.dumps({"category": p["category"], "phase": phase, "seq": i}),
            "interface_id": p["interface_id"], "related_user": None, "is_parse_success": True,
        })
    return out


def _alert(seed, p, seq, raised, cleared, atype, fp, title):
    return {
        "alert_id": did(seed, "al", p["incident_id"], seq),
        "device_id": p["device_id"], "interface_id": p["interface_id"],
        "raised_at": iso(raised) if not isinstance(raised, str) else raised,
        "cleared_at": iso(cleared) if cleared is not None and not isinstance(cleared, str) else cleared,
        "alert_type": atype, "severity": "major" if not fp else "warning",
        "title": title, "body": p["hostname"],
        "source_system": "nms",
        "correlated_incident_id": None if fp else p["incident_id"],
        "is_false_positive_gt": fp,
    }


def gen_graph_and_labels_v2(ctx: Ctx):
    seed = ctx.seed
    topo_pid = ctx.tables["topology_profile"].iloc[0]["topology_profile_id"]
    devices = ctx.tables["device"]
    links = ctx.tables["link"]
    interfaces = ctx.tables["interface"]
    lags = ctx.tables["lag_group"]
    vlans = ctx.tables["vlan"]
    services = ctx.tables["service"]
    vrfs = ctx.tables["routing_instance"]

    ts_rows, te_rows, gs_rows, gn_rows, ge_rows = [], [], [], [], []

    # Hourly snapshots with rich node types
    for t in daterange(ctx.start, ctx.end, ctx.cfg["time"]["topology_cadence_hours"] * 3600):
        tsid = did(seed, "toposnap", iso(t))
        gsid = did(seed, "gsnap", iso(t))
        node_ids = []
        # Device nodes
        for _, d in devices.iterrows():
            nid = did(seed, "gnode", "Device", d["device_id"], iso(t))
            node_ids.append(nid)
            gn_rows.append({
                "graph_snapshot_id": gsid, "node_id": nid, "node_type": "Device",
                "ref_table": "device", "ref_pk": d["device_id"], "name": d["hostname"],
                "site_id": d["site_id"], "features": json.dumps({"role": d["role"]}),
            })
        # Interface nodes (ethernet/lag/svi only to bound size)
        for _, ifr in interfaces.iterrows():
            if ifr["if_type"] not in ("ethernet", "lag", "vlan_svi"):
                continue
            nid = did(seed, "gnode", "Interface", ifr["interface_id"], iso(t))
            node_ids.append(nid)
            gn_rows.append({
                "graph_snapshot_id": gsid, "node_id": nid, "node_type": "Interface",
                "ref_table": "interface", "ref_pk": ifr["interface_id"], "name": ifr["if_name"],
                "site_id": None, "features": json.dumps({"if_type": ifr["if_type"]}),
            })
            # HAS_INTERFACE edge
            ge_rows.append({
                "graph_snapshot_id": gsid, "edge_id": did(seed, "gedge", "HAS_IF", ifr["interface_id"], iso(t)),
                "edge_type": "HAS_INTERFACE",
                "src_node_id": did(seed, "gnode", "Device", ifr["device_id"], iso(t)),
                "dst_node_id": nid, "is_directed": True, "weight": 1.0,
                "link_id": None, "attrs": json.dumps({}),
            })
        for _, lg in lags.iterrows():
            nid = did(seed, "gnode", "LAG", lg["lag_group_id"], iso(t))
            node_ids.append(nid)
            gn_rows.append({
                "graph_snapshot_id": gsid, "node_id": nid, "node_type": "LAG",
                "ref_table": "lag_group", "ref_pk": lg["lag_group_id"], "name": lg["lag_name"],
                "site_id": None, "features": json.dumps({"is_mclag": bool(lg["is_mclag"])}),
            })
        for _, v in vlans.iterrows():
            nid = did(seed, "gnode", "VLAN", v["vlan_id_key"], iso(t))
            node_ids.append(nid)
            gn_rows.append({
                "graph_snapshot_id": gsid, "node_id": nid, "node_type": "VLAN",
                "ref_table": "vlan", "ref_pk": v["vlan_id_key"], "name": v["vlan_name"],
                "site_id": v["site_id"], "features": json.dumps({"vlan_id": int(v["vlan_id"])}),
            })
        for _, s in services.iterrows():
            nid = did(seed, "gnode", "Service", s["service_id"], iso(t))
            node_ids.append(nid)
            gn_rows.append({
                "graph_snapshot_id": gsid, "node_id": nid, "node_type": "Service",
                "ref_table": "service", "ref_pk": s["service_id"], "name": s["service_name"],
                "site_id": s.get("primary_site_id"), "features": json.dumps({"tier": int(s["criticality_tier"])}),
            })
        for _, vrf in vrfs.iterrows():
            nid = did(seed, "gnode", "VRF", vrf["vrf_id"], iso(t))
            node_ids.append(nid)
            gn_rows.append({
                "graph_snapshot_id": gsid, "node_id": nid, "node_type": "VRF",
                "ref_table": "routing_instance", "ref_pk": vrf["vrf_id"], "name": vrf["vrf_name"],
                "site_id": None, "features": json.dumps({}),
            })

        # PHYS_LINK between interface nodes
        edges = 0
        for _, L in links.iterrows():
            eid = did(seed, "gedge", L["link_id"], iso(t))
            ge_rows.append({
                "graph_snapshot_id": gsid, "edge_id": eid,
                "edge_type": "PHYS_LINK" if L["link_layer"] == "phy" else "LAG_LINK",
                "src_node_id": did(seed, "gnode", "Interface", L["a_interface_id"], iso(t)),
                "dst_node_id": did(seed, "gnode", "Interface", L["b_interface_id"], iso(t)),
                "is_directed": False, "weight": 1.0, "link_id": L["link_id"],
                "attrs": json.dumps({"is_uplink": bool(L["is_uplink"]), "is_isl": bool(L["is_isl"])}),
            })
            te_rows.append({
                "topology_snapshot_id": tsid, "link_id": L["link_id"],
                "a_node_id": did(seed, "gnode", "Interface", L["a_interface_id"], iso(t)),
                "b_node_id": did(seed, "gnode", "Interface", L["b_interface_id"], iso(t)),
                "edge_type": "PHYS_LINK" if L["link_layer"] == "phy" else "LAG_LINK",
                "attrs": json.dumps({}),
            })
            edges += 1
            # also device-level link for convenience
            a_dev = ctx.interfaces[L["a_interface_id"]]["device_id"]
            b_dev = ctx.interfaces[L["b_interface_id"]]["device_id"]
            ge_rows.append({
                "graph_snapshot_id": gsid,
                "edge_id": did(seed, "gedge", "DEVLINK", L["link_id"], iso(t)),
                "edge_type": "PHYS_LINK",
                "src_node_id": did(seed, "gnode", "Device", a_dev, iso(t)),
                "dst_node_id": did(seed, "gnode", "Device", b_dev, iso(t)),
                "is_directed": False, "weight": 1.0, "link_id": L["link_id"],
                "attrs": json.dumps({"level": "device"}),
            })

        # DEPENDS_ON service -> core device
        core = devices[devices["hostname"] == "hq-core-a"].iloc[0]["device_id"]
        for _, s in services.iterrows():
            ge_rows.append({
                "graph_snapshot_id": gsid,
                "edge_id": did(seed, "gedge", "DEP", s["service_id"], iso(t)),
                "edge_type": "DEPENDS_ON",
                "src_node_id": did(seed, "gnode", "Service", s["service_id"], iso(t)),
                "dst_node_id": did(seed, "gnode", "Device", core, iso(t)),
                "is_directed": True, "weight": 1.0, "link_id": None, "attrs": json.dumps({}),
            })

        h = sha16(tsid, len(node_ids), edges)
        ts_rows.append({"topology_snapshot_id": tsid, "topology_profile_id": topo_pid,
                        "snapshot_at": iso(t), "node_count": len(node_ids), "edge_count": edges, "hash": h})
        gs_rows.append({"graph_snapshot_id": gsid, "topology_snapshot_id": tsid,
                        "snapshot_at": iso(t), "schema_version": "1.1.0-INST"})

    save_table(ctx, "topology_snapshot", ts_rows, {"topology_profile_id": "topology_profile"})
    save_table(ctx, "topology_edge", te_rows, {"topology_snapshot_id": "topology_snapshot", "link_id": "link"})
    save_table(ctx, "graph_snapshot", gs_rows, {"topology_snapshot_id": "topology_snapshot"})
    save_table(ctx, "graph_node", gn_rows, {"graph_snapshot_id": "graph_snapshot"})
    save_table(ctx, "graph_edge", ge_rows, {"graph_snapshot_id": "graph_snapshot"})

    # Labels (reuse structure from v1 with degradation linking)
    incidents = ctx.tables["failure_incident"].to_dict("records")
    anom, failh, rca, impact, deg, risk = [], [], [], [], [], []

    for d in ctx.tables["device"].to_dict("records"):
        for t in daterange(ctx.start, ctx.end, 1800):
            t2 = t + timedelta(minutes=30)
            y = False
            inc_id = None
            for inc in incidents:
                onset = parse_iso(inc["onset_at"])
                end = parse_iso(inc["recovered_at"]) if inc["recovered_at"] else onset + timedelta(hours=2)
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
            for H in (300, 900, 1800, 3600):
                yf, cat, sev, lead = False, None, None, None
                for inc in incidents:
                    onset = parse_iso(inc["onset_at"])
                    ents = ctx.tables["incident_entity"]
                    involved = ents[(ents["incident_id"] == inc["incident_id"]) & (ents["entity_id"] == d["device_id"])]
                    if len(involved) and t < onset <= t + timedelta(seconds=H):
                        yf, cat, sev = True, inc["category"], inc["severity"]
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
            "y_trigger_type": inc["trigger_type"], "candidate_entity_set": None, "hidden_target": False,
        })
        imps = ctx.tables["service_impact"][ctx.tables["service_impact"]["incident_id"] == inc["incident_id"]]
        svcs = list(imps["service_id"]) if len(imps) else []
        impact.append({
            "impact_label_id": did(seed, "implbl", inc["incident_id"]),
            "incident_id": inc["incident_id"], "t0": inc["detected_at"],
            "y_services": json.dumps(svcs), "y_max_severity": inc["severity"],
            "y_users_affected": int(imps["users_affected"].sum()) if len(imps) else 0,
            "y_downtime_s": inc["downtime_s"],
            "y_sla_breach": bool(imps["sla_breach"].any()) if len(imps) else False,
            "blast_radius_nodes": int(len(ctx.tables["incident_entity"][ctx.tables["incident_entity"]["incident_id"] == inc["incident_id"]])),
        })

    kpi = ctx.tables["service_kpi_sample"]
    for sid in ctx.services:
        for t in daterange(ctx.start, ctx.end, 3600):
            for H in (1800, 3600):
                future = kpi[(kpi["service_id"] == sid) & (kpi["observed_at"] > iso(t)) &
                             (kpi["observed_at"] <= iso(t + timedelta(seconds=H)))]
                y = False
                metric = None
                breach = None
                linked = None
                if len(future):
                    breached = (future["latency_p95_ms"] > 150).any() or (future["availability_pct"] < 99).any()
                    if breached:
                        # require temporal incident link for positive label quality
                        cands = []
                        for inc in incidents:
                            onset = parse_iso(inc["onset_at"])
                            end = parse_iso(inc["recovered_at"]) if inc["recovered_at"] else onset + timedelta(hours=2)
                            if t + timedelta(seconds=H) < onset or t > end:
                                continue
                            imps = ctx.tables["service_impact"]
                            hit = imps[(imps["incident_id"] == inc["incident_id"]) & (imps["service_id"] == sid)]
                            cands.append((2 if len(hit) else 1, inc["incident_id"]))
                        if cands:
                            cands.sort(key=lambda x: -x[0])
                            linked = cands[0][1]
                            y = True
                            metric = "latency_ms" if (future["latency_p95_ms"] > 150).any() else "availability"
                            breach = float(future["latency_p95_ms"].max())
                deg.append({
                    "deg_id": did(seed, "deg", sid, iso(t), H), "service_id": sid,
                    "t0": iso(t), "horizon_s": H, "y_degrade": y, "y_metric": metric,
                    "y_breach_value": breach, "linked_incident_id": linked,
                })

    for _, diff in ctx.tables["config_object_diff"].iterrows():
        yrisk, cat = False, None
        for inc in incidents:
            if inc.get("change_diff_id") == diff["diff_id"]:
                yrisk, cat = True, inc["category"]
                break
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
    rate = float(pd.Series([a["y_anomaly"] for a in anom]).mean())
    log_val(ctx, "label_anomaly_window/prior", rate < 0.35, [f"anomaly_rate={rate:.4f}"])
