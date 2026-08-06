"""Digital Twin: typed graph + temporal state accessors over ECNetBench SQLite (read-only)."""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


@dataclass
class DigitalTwin:
    """Enterprise network digital twin projected from ECNetBench."""

    db_path: Path
    devices: pd.DataFrame = field(default_factory=pd.DataFrame)
    interfaces: pd.DataFrame = field(default_factory=pd.DataFrame)
    links: pd.DataFrame = field(default_factory=pd.DataFrame)
    adjacency: Dict[str, Set[str]] = field(default_factory=dict)
    if_to_dev: Dict[str, str] = field(default_factory=dict)
    degree: Dict[str, int] = field(default_factory=dict)
    role: Dict[str, str] = field(default_factory=dict)
    site: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, db_path: Path) -> "DigitalTwin":
        db_path = Path(db_path)
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            devices = pd.read_sql("SELECT device_id, hostname, role, site_id FROM device", con)
            interfaces = pd.read_sql(
                "SELECT interface_id, device_id, if_name, if_type, description, speed_bps FROM interface",
                con,
            )
            links = pd.read_sql(
                "SELECT link_id, a_interface_id, b_interface_id, is_uplink, is_isl, link_layer FROM link",
                con,
            )
        finally:
            con.close()

        twin = cls(db_path=db_path, devices=devices, interfaces=interfaces, links=links)
        twin._build_graph()
        return twin

    def _build_graph(self) -> None:
        self.if_to_dev = dict(zip(self.interfaces["interface_id"], self.interfaces["device_id"]))
        self.role = dict(zip(self.devices["device_id"], self.devices["role"]))
        self.site = dict(zip(self.devices["device_id"], self.devices["site_id"]))
        adj: Dict[str, Set[str]] = defaultdict(set)
        for _, L in self.links.iterrows():
            a = self.if_to_dev.get(L["a_interface_id"])
            b = self.if_to_dev.get(L["b_interface_id"])
            if a and b and a != b:
                adj[a].add(b)
                adj[b].add(a)
        self.adjacency = dict(adj)
        self.degree = {d: len(self.adjacency.get(d, ())) for d in self.devices["device_id"]}

    def neighbors(self, device_id: str, hops: int = 1) -> Set[str]:
        seen = {device_id}
        frontier = {device_id}
        for _ in range(hops):
            nxt = set()
            for u in frontier:
                nxt |= self.adjacency.get(u, set())
            nxt -= seen
            seen |= nxt
            frontier = nxt
        return seen - {device_id}

    def structural_features(self, device_id: str) -> Dict[str, float]:
        """Twin-derived structural risk features (topology plane)."""
        deg = float(self.degree.get(device_id, 0))
        nbrs = self.neighbors(device_id, 1)
        roles = [self.role.get(n, "") for n in nbrs]
        return {
            "twin_degree": deg,
            "twin_n_neighbors": float(len(nbrs)),
            "twin_frac_core_nbr": float(sum(r == "core" for r in roles) / max(len(roles), 1)),
            "twin_frac_agg_nbr": float(sum(r == "aggregation" for r in roles) / max(len(roles), 1)),
            "twin_frac_wan_nbr": float(sum(r == "wan_edge" for r in roles) / max(len(roles), 1)),
            "twin_is_core": 1.0 if self.role.get(device_id) == "core" else 0.0,
            "twin_is_access": 1.0 if self.role.get(device_id) == "access" else 0.0,
            "twin_is_wan": 1.0 if self.role.get(device_id) == "wan_edge" else 0.0,
            "twin_is_ap": 1.0 if self.role.get(device_id) == "ap" else 0.0,
        }

    def neighbor_aggregate(self, device_id: str, values: Dict[str, float]) -> Dict[str, float]:
        """1-hop message-passing aggregate (GNN-style twin readout)."""
        nbrs = self.neighbors(device_id, 1)
        vals = [values[n] for n in nbrs if n in values]
        if not vals:
            return {"twin_nbr_mean": 0.0, "twin_nbr_max": 0.0, "twin_nbr_std": 0.0}
        arr = np.asarray(vals, dtype=float)
        return {
            "twin_nbr_mean": float(arr.mean()),
            "twin_nbr_max": float(arr.max()),
            "twin_nbr_std": float(arr.std()) if len(arr) > 1 else 0.0,
        }

    def open_ro(self) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
