#!/usr/bin/env python3
"""
ECNetBench v1 constrained instance generator.

Uses seeded distributional models and causal fault injection.
Does NOT assign independent Uniform noise to correlated metrics.
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from util import clamp, daterange, did, iso, parse_iso, sha16

ROOT = Path(__file__).resolve().parents[1]
# Default frozen path — multi-seed runs MUST call set_instance_paths() to a different directory.
INST = ROOT / "instances" / "v1"
CSV_DIR = INST / "csv"
PARQ_DIR = INST / "parquet"
REP_DIR = INST / "reports"
SQLITE_PATH = INST / "ecnetbench_v1.sqlite"


def set_instance_paths(inst_dir: Path) -> None:
    """Redirect all export paths. Never point this at a frozen instance unless intentionally regenerating."""
    global INST, CSV_DIR, PARQ_DIR, REP_DIR, SQLITE_PATH
    INST = Path(inst_dir)
    CSV_DIR = INST / "csv"
    PARQ_DIR = INST / "parquet"
    REP_DIR = INST / "reports"
    SQLITE_PATH = INST / "ecnetbench_v1.sqlite"
    INST.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    PARQ_DIR.mkdir(parents=True, exist_ok=True)
    REP_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Ctx:
    cfg: dict
    seed: int
    rng: np.random.Generator
    start: datetime
    end: datetime
    tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    validation_log: List[dict] = field(default_factory=list)
    # runtime indexes
    devices: Dict[str, dict] = field(default_factory=dict)
    interfaces: Dict[str, dict] = field(default_factory=dict)
    links: Dict[str, dict] = field(default_factory=dict)
    if_by_device: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    vlan_keys: Dict[Tuple[str, int], str] = field(default_factory=dict)
    services: Dict[str, dict] = field(default_factory=dict)
    # fault state overlays keyed by interface_id / device_id
    if_fault: Dict[str, dict] = field(default_factory=dict)
    device_fault: Dict[str, dict] = field(default_factory=dict)
    incidents: List[dict] = field(default_factory=list)


def log_val(ctx: Ctx, table: str, ok: bool, checks: List[str], extra: dict | None = None):
    entry = {"table": table, "ok": ok, "checks": checks, **(extra or {})}
    ctx.validation_log.append(entry)
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {table}: " + "; ".join(checks[:6]) + (f" (+{len(checks)-6} more)" if len(checks) > 6 else ""))
    if not ok:
        raise RuntimeError(f"Validation failed for {table}: {checks}")


def save_table(ctx: Ctx, name: str, rows: List[dict], fk_map: Dict[str, str] | None = None):
    df = pd.DataFrame(rows)
    if df.empty and name not in ("evpn_esi", "mac_ip_binding", "vxlan_vni", "vtep", "evpn_instance"):
        # allow empty optional overlay tables
        pass
    ctx.tables[name] = df
    checks = [f"rows={len(df)}", f"cols={len(df.columns)}"]
    # PK uniqueness: first column ending with _id or known
    # PK uniqueness: only enforce on clear surrogate primary keys
    COMPOSITE = {
        "lag_member", "vlan_membership", "device_firmware_history", "incident_entity",
        "topology_edge", "graph_node", "graph_edge",
    }
    SURROGATE = {
        "interface_state_sample": "sample_id",
        "bgp_session_sample": "sample_id",
        "vsx_state_sample": "sample_id",
        "stp_port_sample": "sample_id",
        "arp_entry": "arp_id",
        "mac_address_table": "mac_entry_id",
        "organization": "org_id", "site": "site_id", "building": "building_id", "floor": "floor_id",
        "rack": "rack_id", "topology_profile": "topology_profile_id", "maintenance_window": "maint_id",
        "firmware_image": "firmware_id", "device": "device_id", "vsx_pair": "vsx_pair_id",
        "hardware_component": "component_id", "routing_instance": "vrf_id", "lag_group": "lag_group_id",
        "interface": "interface_id", "cable": "cable_id", "link": "link_id", "access_point": "ap_id",
        "radio": "radio_id", "vlan": "vlan_id_key", "vxlan_vni": "vni_id", "vtep": "vtep_id",
        "evpn_instance": "evpn_id", "evpn_esi": "esi_id", "mac_ip_binding": "binding_id",
        "bgp_process": "bgp_id", "bgp_neighbor": "bgp_neighbor_id", "bfd_session": "bfd_id",
        "ospf_process": "ospf_id", "ospf_interface": "ospf_if_id", "static_route": "static_id",
        "rib_entry_sample": "rib_sample_id", "fib_entry_sample": "fib_sample_id",
        "acl": "acl_id", "acl_entry": "ace_id", "acl_binding": "binding_id",
        "qos_policy": "qos_policy_id", "qos_class": "qos_class_id", "qos_queue": "qos_queue_id",
        "qos_binding": "binding_id", "stp_instance": "stp_id", "stp_port": "stp_port_id",
        "aaa_method": "aaa_id", "radius_server": "radius_id", "api_response_archive": "api_response_id",
        "config_snapshot": "config_snapshot_id", "config_object_diff": "diff_id",
        "if_counter_sample": "sample_id", "device_resource_sample": "sample_id",
        "env_sensor_sample": "sample_id", "power_sample": "sample_id",
        "qos_queue_counter_sample": "sample_id", "nae_script": "script_id", "nae_agent": "agent_id",
        "nae_monitor": "monitor_id", "nae_timeseries_point": "ts_id", "syslog_event": "syslog_id",
        "failure_incident": "incident_id", "alert": "alert_id", "event_correlation": "corr_id",
        "ipfix_exporter": "exporter_id", "application": "application_id", "ipfix_record": "flow_id",
        "flow_aggregate_5m": "agg_id", "user_account": "user_id", "endpoint": "endpoint_id",
        "service": "service_id", "sla_objective": "sla_id", "service_dependency": "dep_id",
        "service_endpoint_bind": "bind_id", "service_kpi_sample": "kpi_id",
        "service_impact": "impact_id", "recovery_action": "action_id",
        "topology_snapshot": "topology_snapshot_id", "graph_snapshot": "graph_snapshot_id",
        "label_anomaly_window": "window_id", "label_failure_horizon": "sample_id",
        "label_rca": "rca_id", "label_impact": "impact_label_id", "label_degradation": "deg_id",
        "label_config_risk": "risk_id",
    }
    if not df.empty and name in COMPOSITE:
        checks.append("pk=composite (uniqueness skipped)")
    elif not df.empty and name in SURROGATE and SURROGATE[name] in df.columns:
        pk = SURROGATE[name]
        nuniq = df[pk].nunique(dropna=False)
        checks.append(f"pk[{pk}] unique={nuniq == len(df)}")
        if nuniq != len(df):
            log_val(ctx, name, False, checks + [f"duplicate PK in {pk}"])
    elif not df.empty:
        checks.append("pk=not enforced")
    # FK checks
    if fk_map and not df.empty:
        for col, parent in fk_map.items():
            if col not in df.columns:
                continue
            parent_df = ctx.tables.get(parent)
            if parent_df is None or parent_df.empty:
                continue
            # parent pk guess
            ppk = None
            for c in parent_df.columns:
                if c == col or (c.endswith("_id") and c.split("_")[0] in col):
                    if c == col or parent_df.columns[0] == c:
                        ppk = c
                        break
            if ppk is None:
                ppk = parent_df.columns[0]
            # better: use same column name if exists
            if col in parent_df.columns:
                ppk = col
            elif parent + "_id" in [parent_df.columns[0]] or True:
                # find *exact* matching suffix table pk
                for c in parent_df.columns:
                    if c.endswith("_id"):
                        ppk = c
                        break
            vals = df[col].dropna().unique()
            parent_set = set(parent_df[ppk].astype(str))
            missing = [v for v in vals if str(v) not in parent_set]
            ok_fk = len(missing) == 0
            checks.append(f"fk[{col}->{parent}.{ppk}] ok={ok_fk}" + (f" missing={len(missing)}" if missing else ""))
            if not ok_fk:
                log_val(ctx, name, False, checks, {"missing_sample": missing[:5]})
    # timestamp columns monotonic / parseable
    for c in df.columns:
        if c.endswith("_at") or c in ("t_start", "t_end", "t0", "t_detect", "t_change", "flow_start", "flow_end", "bucket_start", "raised_at", "cleared_at", "onset_at", "detected_at", "recovered_at", "impact_start", "impact_end", "started_at", "ended_at", "window_start", "window_end", "learned_at", "withdrawn_at", "joined_at", "left_at", "valid_from", "valid_to", "commissioned_at", "installed_at", "removed_at", "last_seen_at", "exported_at", "diffed_at", "received_at", "snapshot_at", "last_clear_at", "last_state_change_at", "last_topology_change_at", "last_change_at"):
            if c in df.columns and df[c].notna().any():
                try:
                    pd.to_datetime(df[c].dropna().head(20), utc=True)
                    checks.append(f"ts[{c}] parseable")
                except Exception as e:
                    log_val(ctx, name, False, checks + [f"ts[{c}] fail: {e}"])
    log_val(ctx, name, True, checks, {"ncols": len(df.columns)})


def diurnal_mult(ctx: Ctx, ts: datetime, vlan_purpose: str = "user") -> float:
    stats = ctx.cfg["statistics"]
    hour = ts.hour
    weekday = ts.weekday() < 5
    base = stats["weekday_hour_mult"][hour] if weekday else stats["weekend_hour_mult"][hour]
    if vlan_purpose == "server" and str(hour) in {str(k) for k in stats["night_backup_hour_boost"].keys()}:
        # keys may be int in yaml
        boost = stats["night_backup_hour_boost"].get(hour) or stats["night_backup_hour_boost"].get(str(hour))
        if boost:
            base *= float(boost)
    return float(base)


# ---------------------------------------------------------------------------
# PHASE 1: Organization / sites / spatial
# ---------------------------------------------------------------------------

def gen_org_sites(ctx: Ctx):
    seed = ctx.seed
    org_id = did(seed, "org", "contoso")
    org_rows = [{
        "org_id": org_id,
        "org_name": ctx.cfg["topology"]["org_name"],
        "industry_vertical": "enterprise_research",
        "created_at": iso(ctx.start - timedelta(days=400)),
    }]
    save_table(ctx, "organization", org_rows)

    site_rows, building_rows, floor_rows, rack_rows = [], [], [], []
    for i, s in enumerate(ctx.cfg["topology"]["sites"]):
        sid = did(seed, "site", s["code"])
        site_rows.append({
            "site_id": sid,
            "org_id": org_id,
            "site_code": s["code"],
            "site_name": s["name"],
            "site_type": s["type"],
            "timezone": s["timezone"],
            "geo_lat": 41.88 + 0.02 * i,
            "geo_lon": -87.63 - 0.15 * i,
            "address_region": "US-IL",
            "criticality_tier": s["criticality_tier"],
            "valid_from": iso(ctx.start - timedelta(days=365)),
            "valid_to": None,
        })
        bid = did(seed, "building", s["code"], 1)
        building_rows.append({
            "building_id": bid, "site_id": sid,
            "building_name": f"{s['code']}-B1", "building_code": "B1",
        })
        for fl in (1, 2) if s["type"] == "campus" else (1,):
            fid = did(seed, "floor", s["code"], fl)
            floor_rows.append({
                "floor_id": fid, "building_id": bid,
                "floor_number": fl, "floor_label": f"L{fl}",
            })
            for rk in range(1, 3 if s["type"] == "campus" else 2):
                rid = did(seed, "rack", s["code"], fl, rk)
                rack_rows.append({
                    "rack_id": rid, "floor_id": fid, "site_id": sid,
                    "rack_label": f"R{fl}{rk:02d}",
                    "power_feed_a_kw": 5.0, "power_feed_b_kw": 5.0,
                    "cooling_zone_id": did(seed, "cool", s["code"], fl),
                })
    save_table(ctx, "site", site_rows, {"org_id": "organization"})
    save_table(ctx, "building", building_rows, {"site_id": "site"})
    save_table(ctx, "floor", floor_rows, {"building_id": "building"})
    save_table(ctx, "rack", rack_rows, {"site_id": "site", "floor_id": "floor"})

    tp = [{
        "topology_profile_id": did(seed, "topo_profile", "campus_hybrid_v1"),
        "name": "campus_hybrid_v1",
        "category": "hybrid",
        "description": "HQ campus with VSX aggregation + branch site",
        "device_count_target": 20,
        "has_evpn": False,
        "has_vsx": True,
        "has_wifi": True,
    }]
    save_table(ctx, "topology_profile", tp)

    # maintenance windows: Fri 22:00–Sat 02:00 local ≈ UTC-6 → Sat 04:00–08:00 UTC rough; use fixed UTC windows
    mw = []
    t = ctx.start + timedelta(days=4)  # first Friday-ish from Monday start: Jan 6 2025 is Monday, +4 = Friday
    for w in range(2):
        start = t + timedelta(days=7 * w, hours=4)
        mw.append({
            "maint_id": did(seed, "maint", w),
            "site_id": site_rows[0]["site_id"],
            "start_at": iso(start),
            "end_at": iso(start + timedelta(hours=4)),
            "expected_impact": "firmware_window",
            "suppress_alerts": True,
            "ticket_id": f"CHG{1000+w}",
        })
    save_table(ctx, "maintenance_window", mw, {"site_id": "site"})
    return org_id


# ---------------------------------------------------------------------------
# PHASE 2: Firmware, devices, VSX, interfaces, LAGs, links, VLANs
# ---------------------------------------------------------------------------

def gen_inventory_topology(ctx: Ctx):
    seed = ctx.seed
    sites = {r["site_code"]: r for r in ctx.tables["site"].to_dict("records")}
    racks = ctx.tables["rack"].to_dict("records")
    hq = sites["HQ-CAM"]
    br = sites["BR-01"]
    hq_racks = [r for r in racks if r["site_id"] == hq["site_id"]]
    br_racks = [r for r in racks if r["site_id"] == br["site_id"]]

    fw_rows = [
        {"firmware_id": did(seed, "fw", "10.13.1040"), "os_family": "AOS-CX", "version_string": "10.13.1040",
         "release_train": "10.13", "known_issue_tags": "", "min_compatible_partner_version": "10.13.1000"},
        {"firmware_id": did(seed, "fw", "10.13.1000"), "os_family": "AOS-CX", "version_string": "10.13.1000",
         "release_train": "10.13", "known_issue_tags": "vsx_isl_flap_rare", "min_compatible_partner_version": "10.13.1000"},
        {"firmware_id": did(seed, "fw", "10.12.0001"), "os_family": "AOS-CX", "version_string": "10.12.0001",
         "release_train": "10.12", "known_issue_tags": "incompatible_with_10.13_vsx", "min_compatible_partner_version": "10.12.0001"},
    ]
    save_table(ctx, "firmware_image", fw_rows)

    # Device blueprint (structural campus + branch)
    # HQ: core-a/b VSX, agg-a/b VSX, access-01..06, ap-01..04, wan-edge
    # BR: wan-edge-br, access-br-01, access-br-02, ap-br-01
    device_specs = []

    def add_dev(hostname, site, role, model, rack, ha="standalone", vsx_name=None, cls="switch", ver="10.13.1040"):
        device_specs.append({
            "hostname": hostname, "site": site, "role": role, "model": model,
            "rack": rack, "ha": ha, "vsx_name": vsx_name, "class": cls, "ver": ver,
        })

    add_dev("hq-core-a", hq, "core", "6405", hq_racks[0], "vsx_member", "vsx-core")
    add_dev("hq-core-b", hq, "core", "6405", hq_racks[0], "vsx_member", "vsx-core")
    add_dev("hq-agg-a", hq, "aggregation", "8325", hq_racks[1], "vsx_member", "vsx-agg")
    add_dev("hq-agg-b", hq, "aggregation", "8325", hq_racks[1], "vsx_member", "vsx-agg")
    for i in range(1, 7):
        add_dev(f"hq-acc-{i:02d}", hq, "access", "6300", hq_racks[min(i % len(hq_racks), len(hq_racks)-1)])
    for i in range(1, 5):
        add_dev(f"hq-ap-{i:02d}", hq, "ap", "AP-635", hq_racks[0], cls="access_point")
    add_dev("hq-wan-edge", hq, "wan_edge", "8360", hq_racks[0], cls="router")
    add_dev("br-wan-edge", br, "wan_edge", "8360", br_racks[0], cls="router")
    add_dev("br-acc-01", br, "access", "6300", br_racks[0])
    add_dev("br-acc-02", br, "access", "6300", br_racks[0 if len(br_racks) == 1 else 1])
    add_dev("br-ap-01", br, "ap", "AP-535", br_racks[0], cls="access_point")

    # Create VSX pairs first (members filled after devices)
    vsx_defs = {
        "vsx-core": {"site": hq, "state": "sync"},
        "vsx-agg": {"site": hq, "state": "sync"},
    }
    vsx_rows = []
    for name, meta in vsx_defs.items():
        vsx_rows.append({
            "vsx_pair_id": did(seed, "vsx", name),
            "site_id": meta["site"]["site_id"],
            "system_mac": f"02:00:00:00:00:{'01' if name=='vsx-core' else '02'}",
            "member_a_device_id": None,
            "member_b_device_id": None,
            "isl_lag_id": None,
            "keepalive_src_ip": None,
            "keepalive_dst_ip": None,
            "role_priority_a": 100,
            "oper_state": meta["state"],
            "_name": name,
        })

    device_rows = []
    fw_hist = []
    comp_rows = []
    for d in device_specs:
        site = d["site"]
        did_ = did(seed, "device", d["hostname"])
        vsx_id = did(seed, "vsx", d["vsx_name"]) if d["vsx_name"] else None
        mgmt_third = 10 if site["site_code"] == "HQ-CAM" else 20
        # deterministic last octet from hostname hash
        octet = int(sha16(d["hostname"])[:2], 16) % 200 + 10
        row = {
            "device_id": did_,
            "site_id": site["site_id"],
            "rack_id": d["rack"]["rack_id"],
            "hostname": d["hostname"],
            "mgmt_ip": f"10.{mgmt_third}.255.{octet}",
            "device_class": d["class"],
            "platform_model": d["model"],
            "serial_number": f"SN{sha16(d['hostname'])[:10].upper()}",
            "role": d["role"],
            "os_family": "AOS-CX" if d["class"] != "access_point" else "ArubaOS",
            "os_version": d["ver"] if d["class"] != "access_point" else "8.11.2.0",
            "ha_mode": d["ha"],
            "vsx_pair_id": vsx_id,
            "is_managed": True,
            "status": "active",
            "commissioned_at": iso(ctx.start - timedelta(days=200)),
            "valid_from": iso(ctx.start - timedelta(days=200)),
            "valid_to": None,
        }
        device_rows.append(row)
        ctx.devices[did_] = {**row, **d}
        fw_id = did(seed, "fw", d["ver"]) if d["class"] != "access_point" else did(seed, "fw", "10.13.1040")
        if d["class"] != "access_point":
            fw_hist.append({
                "device_id": did_, "firmware_id": fw_id,
                "installed_at": iso(ctx.start - timedelta(days=60)),
                "removed_at": None, "install_result": "success",
            })
        # components
        for ctype, cname in [("psu", "PSU1"), ("psu", "PSU2"), ("fan", "FAN1"), ("fan", "FAN2")]:
            if d["class"] == "access_point" and ctype == "psu":
                continue
            comp_rows.append({
                "component_id": did(seed, "comp", d["hostname"], cname),
                "device_id": did_,
                "component_type": ctype,
                "name": cname,
                "part_number": f"P-{ctype.upper()}",
                "serial_number": f"C{sha16(d['hostname'], cname)[:8].upper()}",
                "position": cname,
                "oper_status": "ok",
                "valid_from": iso(ctx.start - timedelta(days=200)),
                "valid_to": None,
            })

    # fill VSX members
    for vr in vsx_rows:
        name = vr.pop("_name")
        members = [d for d in device_rows if d["vsx_pair_id"] == vr["vsx_pair_id"]]
        members = sorted(members, key=lambda x: x["hostname"])
        vr["member_a_device_id"] = members[0]["device_id"]
        vr["member_b_device_id"] = members[1]["device_id"]
        vr["keepalive_src_ip"] = members[0]["mgmt_ip"]
        vr["keepalive_dst_ip"] = members[1]["mgmt_ip"]

    save_table(ctx, "device", device_rows, {"site_id": "site", "rack_id": "rack"})
    save_table(ctx, "vsx_pair", vsx_rows, {"site_id": "site", "member_a_device_id": "device", "member_b_device_id": "device"})
    save_table(ctx, "device_firmware_history", fw_hist, {"device_id": "device", "firmware_id": "firmware_image"})
    save_table(ctx, "hardware_component", comp_rows, {"device_id": "device"})

    # VRFs
    vrf_rows = []
    for d in device_rows:
        if d["device_class"] in ("switch", "router"):
            vrf_rows.append({
                "vrf_id": did(seed, "vrf", d["hostname"], "default"),
                "device_id": d["device_id"], "vrf_name": "default", "rd": None,
                "is_default": True, "valid_from": iso(ctx.start), "valid_to": None,
            })
            if d["role"] in ("core", "aggregation", "wan_edge"):
                vrf_rows.append({
                    "vrf_id": did(seed, "vrf", d["hostname"], "mgmt"),
                    "device_id": d["device_id"], "vrf_name": "mgmt", "rd": "65000:100",
                    "is_default": False, "valid_from": iso(ctx.start), "valid_to": None,
                })
    save_table(ctx, "routing_instance", vrf_rows, {"device_id": "device"})

    # Interfaces + LAGs
    lag_rows, if_rows, lag_member_rows = [], [], []
    link_rows, cable_rows = [], []

    def add_iface(dev, name, itype, speed, role_hint="access", lag_id=None, is_member=False):
        iid = did(seed, "if", dev["hostname"], name)
        if iid in ctx.interfaces:
            return iid
        idx = len(ctx.if_by_device[dev["device_id"]]) + 1
        # Deterministic locally-administered MAC from hostname+ifname
        h = sha16(dev["hostname"], name)
        mac = f"02:{h[0:2]}:{h[2:4]}:{h[4:6]}:{h[6:8]}:{h[8:10]}"
        row = {
            "interface_id": iid,
            "device_id": dev["device_id"],
            "if_name": name,
            "if_index": idx,
            "if_type": itype,
            "admin_status": "up",
            "oper_status": "up",
            "speed_bps": speed,
            "mtu": 1500,
            "mac_address": mac,
            "description": role_hint,
            "is_lag_member": is_member,
            "lag_group_id": lag_id,
            "vrf_id": None,
            "ipv4_address": None,
            "ipv6_address": None,
            "enabled_vlans_mode": "trunk" if role_hint in ("uplink", "isl", "peer") else ("access" if role_hint == "access" else "none"),
            "native_vlan_id": 1 if role_hint in ("uplink", "isl", "peer", "access") else None,
            "storm_control_pps": 10000 if role_hint == "access" else None,
            "valid_from": iso(ctx.start - timedelta(days=200)),
            "valid_to": None,
            "_role_hint": role_hint,
            "_hostname": dev["hostname"],
        }
        # mgmt VRF only for mgmt if; APs have no VRF
        if dev["device_class"] == "access_point":
            row["vrf_id"] = None
        elif name.startswith("mgmt") or name == "1/1/48":
            row["vrf_id"] = did(seed, "vrf", dev["hostname"], "mgmt") if any(
                r["device_id"] == dev["device_id"] and r["vrf_name"] == "mgmt" for r in vrf_rows
            ) else did(seed, "vrf", dev["hostname"], "default")
        else:
            row["vrf_id"] = did(seed, "vrf", dev["hostname"], "default")
        # SVI addressing by VLAN id embedded in name vlanN
        if itype == "vlan_svi" and name.startswith("vlan"):
            try:
                vid = int(name.replace("vlan", ""))
            except ValueError:
                vid = 1
            site_code = "10" if "hq" in dev["hostname"] or dev.get("site", {}).get("site_code") == "HQ-CAM" else "20"
            # use device site from row context via hostname prefix
            site_oct = 10 if str(dev["hostname"]).startswith("hq") or str(dev["hostname"]).startswith("HQ") else (
                10 if not str(dev["hostname"]).startswith("br") else 20
            )
            if str(dev["hostname"]).startswith("br"):
                site_oct = 20
            else:
                site_oct = 10
            # third octet = vlan, fourth = role-stable host
            host_oct = {"core": 1, "aggregation": 2, "access": 10, "wan_edge": 1}.get(dev["role"], 5)
            # unique per device: hash nibble
            host_oct = 1 + (int(sha16(dev["hostname"])[:2], 16) % 20)
            row["ipv4_address"] = f"10.{site_oct}.{vid}.{host_oct}"
            row["enabled_vlans_mode"] = "none"
            row["native_vlan_id"] = None
        if_rows.append(row)
        ctx.interfaces[iid] = row
        ctx.if_by_device[dev["device_id"]].append(iid)
        return iid

    def add_lag(dev, lag_name, mclag=False, vsx_name=None):
        lid = did(seed, "lag", dev["hostname"], lag_name)
        lag_rows.append({
            "lag_group_id": lid,
            "device_id": dev["device_id"],
            "lag_name": lag_name,
            "lag_type": "lacp",
            "min_links": 1,
            "lacp_mode": "active",
            "is_mclag": mclag,
            "vsx_pair_id": did(seed, "vsx", vsx_name) if vsx_name else None,
        })
        # LAG logical interface
        add_iface(dev, lag_name, "lag", 200_000_000_000 if "isl" in lag_name or lag_name.startswith("lag1") else 20_000_000_000,
                  role_hint="uplink" if "up" in lag_name or lag_name in ("lag1", "lag10") else ("isl" if "isl" in lag_name else "peer"),
                  lag_id=lid)
        return lid

    def add_link(a_if, b_if, layer="phy", uplink=False, isl=False, media="cu"):
        # Enforce compatible endpoint speeds (take min nonzero)
        sa = ctx.interfaces[a_if].get("speed_bps")
        sb = ctx.interfaces[b_if].get("speed_bps")
        if sa and sb and sa != sb:
            spd = min(sa, sb)
            ctx.interfaces[a_if]["speed_bps"] = spd
            ctx.interfaces[b_if]["speed_bps"] = spd
            for r in if_rows:
                if r["interface_id"] in (a_if, b_if):
                    r["speed_bps"] = spd
        cid = did(seed, "cable", a_if, b_if) if layer == "phy" else None
        if cid:
            cable_rows.append({
                "cable_id": cid, "media_type": media, "length_m": 3.0 if media == "cu" else 30.0,
                "install_date": "2024-06-01", "health_score": 0.98,
            })
        lid = did(seed, "link", a_if, b_if)
        link_rows.append({
            "link_id": lid,
            "a_interface_id": a_if,
            "b_interface_id": b_if,
            "link_layer": layer,
            "discovery_method": "lldp",
            "cable_id": cid,
            "media_type": media,
            "length_m": 3.0 if media == "cu" else 30.0,
            "is_isl": isl,
            "is_uplink": uplink,
            "valid_from": iso(ctx.start - timedelta(days=200)),
            "valid_to": None,
        })
        ctx.links[lid] = link_rows[-1]
        return lid

    # Build per-device ports
    by_host = {d["hostname"]: d for d in device_rows}

    # VSX ISL LAGs for core and agg
    for vsx_name, hosts in [("vsx-core", ("hq-core-a", "hq-core-b")), ("vsx-agg", ("hq-agg-a", "hq-agg-b"))]:
        a, b = by_host[hosts[0]], by_host[hosts[1]]
        lag_a = add_lag(a, "lag100", vsx_name=vsx_name)  # ISL
        lag_b = add_lag(b, "lag100", vsx_name=vsx_name)
        # physical members
        for port in ("1/1/49", "1/1/50"):
            ia = add_iface(a, port, "ethernet", 100_000_000_000, "isl", lag_a, True)
            ib = add_iface(b, port, "ethernet", 100_000_000_000, "isl", lag_b, True)
            lag_member_rows.append({"lag_group_id": lag_a, "interface_id": ia, "actor_key": "1", "partner_key": "2",
                                    "lacp_state": "bundled", "joined_at": iso(ctx.start - timedelta(days=200)), "left_at": None})
            lag_member_rows.append({"lag_group_id": lag_b, "interface_id": ib, "actor_key": "2", "partner_key": "1",
                                    "lacp_state": "bundled", "joined_at": iso(ctx.start - timedelta(days=200)), "left_at": None})
            add_link(ia, ib, "phy", isl=True, media="smf")
        add_link(did(seed, "if", a["hostname"], "lag100"), did(seed, "if", b["hostname"], "lag100"), "lag", isl=True, media="virtual")
        # update vsx isl_lag_id
        for vr in vsx_rows:
            if vr["vsx_pair_id"] == did(seed, "vsx", vsx_name):
                vr["isl_lag_id"] = lag_a

    # Core <-> Agg uplinks (MCLAG style dual-homed)
    for core_h, agg_h, port_c, port_a in [
        ("hq-core-a", "hq-agg-a", "1/1/1", "1/1/1"),
        ("hq-core-a", "hq-agg-b", "1/1/2", "1/1/1"),
        ("hq-core-b", "hq-agg-a", "1/1/1", "1/1/2"),
        ("hq-core-b", "hq-agg-b", "1/1/2", "1/1/2"),
    ]:
        # may create duplicate if names collide — use unique ports carefully
        pass

    # Simpler structured uplinks:
    # Each core connects to both aggs on unique ports
    core_ports = {"hq-core-a": ["1/1/1", "1/1/2"], "hq-core-b": ["1/1/3", "1/1/4"]}
    agg_ports = {"hq-agg-a": ["1/1/3", "1/1/4"], "hq-agg-b": ["1/1/3", "1/1/4"]}
    pairs = [
        ("hq-core-a", "1/1/1", "hq-agg-a", "1/1/3"),
        ("hq-core-a", "1/1/2", "hq-agg-b", "1/1/3"),
        ("hq-core-b", "1/1/3", "hq-agg-a", "1/1/4"),
        ("hq-core-b", "1/1/4", "hq-agg-b", "1/1/4"),
    ]
    for ha, pa, hb, pb in pairs:
        ia = add_iface(by_host[ha], pa, "ethernet", 100_000_000_000, "uplink")
        ib = add_iface(by_host[hb], pb, "ethernet", 100_000_000_000, "uplink")
        add_link(ia, ib, "phy", uplink=True, media="smf")

    # Access dual-homed to agg-a and agg-b
    for i in range(1, 7):
        acc = by_host[f"hq-acc-{i:02d}"]
        # uplink ports
        ia1 = add_iface(acc, "1/1/25", "ethernet", 10_000_000_000, "uplink")
        ia2 = add_iface(acc, "1/1/26", "ethernet", 10_000_000_000, "uplink")
        # agg downlinks — unique ports 1/1/10+i
        p = f"1/1/{10+i}"
        ib1 = add_iface(by_host["hq-agg-a"], p, "ethernet", 10_000_000_000, "downlink")
        ib2 = add_iface(by_host["hq-agg-b"], p, "ethernet", 10_000_000_000, "downlink")
        add_link(ia1, ib1, "phy", uplink=True, media="cu")
        add_link(ia2, ib2, "phy", uplink=True, media="cu")
        # access ports for endpoints
        for pnum in range(1, 9):
            add_iface(acc, f"1/1/{pnum}", "ethernet", 1_000_000_000, "access")

    # APs uplink to access switches
    ap_map = [("hq-ap-01", "hq-acc-01"), ("hq-ap-02", "hq-acc-02"), ("hq-ap-03", "hq-acc-03"), ("hq-ap-04", "hq-acc-04"),
              ("br-ap-01", "br-acc-01")]
    ap_rows, radio_rows = [], []
    for ap_h, acc_h in ap_map:
        ap = by_host[ap_h]
        acc = by_host[acc_h]
        ap_eth = add_iface(ap, "eth0", "ethernet", 1_000_000_000, "uplink")
        # use port 1/1/8 on access if exists else create
        acc_port_name = "1/1/8"
        # find existing
        existing = [iid for iid, r in ctx.interfaces.items() if r["device_id"] == acc["device_id"] and r["if_name"] == acc_port_name]
        if existing:
            acc_if = existing[0]
        else:
            acc_if = add_iface(acc, acc_port_name, "ethernet", 1_000_000_000, "access")
        add_link(ap_eth, acc_if, "phy", uplink=True, media="cu")
        ap_id = did(seed, "ap", ap_h)
        ap_rows.append({
            "ap_id": ap_id, "device_id": ap["device_id"],
            "controller_or_gw_id": by_host["hq-core-a"]["device_id"],
            "ap_group": "default", "eth_uplink_interface_id": ap_eth,
            "ip_address": ap["mgmt_ip"].replace(".255.", ".50.") if False else ap["mgmt_ip"],
            "status": "active",
        })
        for band, ch in [("2.4", 6), ("5", 36), ("6", 37)]:
            if ap_h.startswith("br") and band == "6":
                continue
            radio_rows.append({
                "radio_id": did(seed, "radio", ap_h, band),
                "ap_id": ap_id, "band": band, "channel": ch,
                "channel_width_mhz": 20 if band == "2.4" else 80,
                "tx_power_dbm": 15.0, "oper_status": "up",
            })

    # WAN: hq-wan-edge <-> hq-core-a ; br-wan-edge <-> br-acc ; hq-wan <-> br-wan
    hw, bw = by_host["hq-wan-edge"], by_host["br-wan-edge"]
    for h in (hw, bw):
        add_iface(h, "1/1/1", "ethernet", 10_000_000_000, "uplink")
        add_iface(h, "1/1/2", "ethernet", 1_000_000_000, "wan")
    # Point-to-point WAN addressing consistent with BGP
    hq_wan_if = did(seed, "if", "hq-wan-edge", "1/1/2")
    br_wan_if = did(seed, "if", "br-wan-edge", "1/1/2")
    ctx.interfaces[hq_wan_if]["ipv4_address"] = "172.16.0.1"
    ctx.interfaces[br_wan_if]["ipv4_address"] = "172.16.0.2"
    for r in if_rows:
        if r["interface_id"] == hq_wan_if:
            r["ipv4_address"] = "172.16.0.1"
        if r["interface_id"] == br_wan_if:
            r["ipv4_address"] = "172.16.0.2"
    add_link(did(seed, "if", "hq-wan-edge", "1/1/1"), add_iface(by_host["hq-core-a"], "1/1/10", "ethernet", 10_000_000_000, "uplink"), "phy", uplink=True, media="cu")
    # branch access ports + uplinks
    for bh in ("br-acc-01", "br-acc-02"):
        bdev = by_host[bh]
        for pnum in range(1, 9):
            add_iface(bdev, f"1/1/{pnum}", "ethernet", 1_000_000_000, "access")
        add_iface(bdev, "1/1/25", "ethernet", 1_000_000_000, "uplink")
    add_link(did(seed, "if", "br-wan-edge", "1/1/1"), did(seed, "if", "br-acc-01", "1/1/25"), "phy", uplink=True, media="cu")
    add_link(did(seed, "if", "br-acc-01", "1/1/7"), did(seed, "if", "br-acc-02", "1/1/25") if "1/1/25" in [ctx.interfaces[i]["if_name"] for i in ctx.if_by_device[by_host["br-acc-02"]["device_id"]]] else add_iface(by_host["br-acc-02"], "1/1/26", "ethernet", 1_000_000_000, "uplink"), "phy", uplink=False, media="cu")
    # WAN link between sites
    add_link(did(seed, "if", "hq-wan-edge", "1/1/2"), did(seed, "if", "br-wan-edge", "1/1/2"), "phy", uplink=True, media="smf")

    # SVIs
    for d in device_rows:
        if d["role"] in ("core", "aggregation", "access", "wan_edge"):
            for vlan_id, purpose in [(10, "user"), (20, "voice"), (30, "server"), (100, "mgmt")]:
                if d["role"] == "access" and vlan_id == 30:
                    continue
                add_iface(d, f"vlan{vlan_id}", "vlan_svi", None, purpose)

    # Clean if_rows for export (drop private keys later)
    save_table(ctx, "lag_group", lag_rows, {"device_id": "device"})
    # strip private
    if_export = []
    for r in if_rows:
        e = {k: v for k, v in r.items() if not k.startswith("_")}
        if_export.append(e)
    save_table(ctx, "interface", if_export, {"device_id": "device", "lag_group_id": "lag_group", "vrf_id": "routing_instance"})
    save_table(ctx, "lag_member", lag_member_rows, {"lag_group_id": "lag_group", "interface_id": "interface"})
    save_table(ctx, "cable", cable_rows)
    save_table(ctx, "link", link_rows, {"a_interface_id": "interface", "b_interface_id": "interface", "cable_id": "cable"})
    save_table(ctx, "access_point", ap_rows, {"device_id": "device", "eth_uplink_interface_id": "interface"})
    save_table(ctx, "radio", radio_rows, {"ap_id": "access_point"})

    # VLANs per site
    vlan_rows, vmemb = [], []
    for site in (hq, br):
        for vid, name, purpose in [(10, "USERS", "user"), (20, "VOICE", "voice"), (30, "SERVERS", "server"),
                                   (40, "GUEST", "guest"), (100, "MGMT", "mgmt")]:
            if site["site_code"] == "BR-01" and vid == 30:
                continue
            vk = did(seed, "vlan", site["site_code"], vid)
            ctx.vlan_keys[(site["site_id"], vid)] = vk
            # find an SVI on a core/agg for HQ
            svi = None
            for r in if_rows:
                if r["if_name"] == f"vlan{vid}" and ctx.devices[r["device_id"]]["site_id"] == site["site_id"]:
                    if ctx.devices[r["device_id"]]["role"] in ("core", "aggregation", "wan_edge", "access"):
                        svi = r["interface_id"]
                        if ctx.devices[r["device_id"]]["role"] in ("core", "wan_edge"):
                            break
            vlan_rows.append({
                "vlan_id_key": vk, "site_id": site["site_id"], "vlan_id": vid,
                "vlan_name": name, "vlan_purpose": purpose,
                "l3_svi_interface_id": svi, "dhcp_snooping_enabled": purpose == "user",
                "stretch_domain_id": None,
            })
    save_table(ctx, "vlan", vlan_rows, {"site_id": "site", "l3_svi_interface_id": "interface"})

    # memberships: access ports -> vlan10; trunks allow 10,20,30,100
    for r in if_rows:
        hint = r.get("_role_hint", "")
        site_id = ctx.devices[r["device_id"]]["site_id"]
        if hint == "access" and r["if_type"] == "ethernet":
            vk = ctx.vlan_keys.get((site_id, 10))
            if vk:
                vmemb.append({"interface_id": r["interface_id"], "vlan_id_key": vk, "tagging": "access",
                              "valid_from": iso(ctx.start), "valid_to": None})
        elif hint in ("uplink", "downlink", "isl", "peer") and r["if_type"] in ("ethernet", "lag"):
            for vid in (10, 20, 30, 100):
                vk = ctx.vlan_keys.get((site_id, vid))
                if vk:
                    vmemb.append({"interface_id": r["interface_id"], "vlan_id_key": vk, "tagging": "tagged",
                                  "valid_from": iso(ctx.start), "valid_to": None})
    save_table(ctx, "vlan_membership", vmemb, {"interface_id": "interface", "vlan_id_key": "vlan"})

    # Empty EVPN tables (campus profile without overlay)
    for tname, cols in [
        ("vxlan_vni", ["vni_id", "vni", "vlan_id_key", "l3_vrf_id", "vni_type"]),
        ("vtep", ["vtep_id", "device_id", "vtep_ip", "source_interface_id", "oper_status"]),
        ("evpn_instance", ["evpn_id", "routing_instance_id", "evi", "rd", "rt_import", "rt_export"]),
        ("evpn_esi", ["esi_id", "esi_value", "lag_group_id", "esi_mode"]),
        ("mac_ip_binding", ["binding_id", "vni_id", "mac", "ip", "vtep_id", "seq_number", "learned_at", "withdrawn_at"]),
    ]:
        save_table(ctx, tname, [])

    # Update vsx_pair table with isl_lag_id
    ctx.tables["vsx_pair"] = pd.DataFrame(vsx_rows)
    print("  topology device count:", len(device_rows), "interfaces:", len(if_export), "links:", len(link_rows))
