#!/usr/bin/env python3
"""Scenario coverage from existing frozen incident categories (not new generation)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "scenario_coverage.json"

SEEDS = [
    ("v1.1.0-INST", ROOT / "benchmark" / "instances" / "v1" / "ecnetbench_v1.sqlite"),
    ("seed101", ROOT / "benchmark" / "instances" / "v1.1-seed101" / "ecnetbench_v1.sqlite"),
    ("seed202", ROOT / "benchmark" / "instances" / "v1.1-seed202" / "ecnetbench_v1.sqlite"),
    ("seed303", ROOT / "benchmark" / "instances" / "v1.1-seed303" / "ecnetbench_v1.sqlite"),
    ("seed404", ROOT / "benchmark" / "instances" / "v1.1-seed404" / "ecnetbench_v1.sqlite"),
    ("seed505", ROOT / "benchmark" / "instances" / "v1.1-seed505" / "ecnetbench_v1.sqlite"),
]


def seed_coverage(name: str, db: Path) -> Dict[str, Any]:
    if not db.exists():
        return {"seed": name, "available": False}
    con = sqlite3.connect(db)
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(failure_incident)")]
        cat_col = "category" if "category" in cols else ("incident_category" if "incident_category" in cols else None)
        sev_col = "severity" if "severity" in cols else None
        n = con.execute("SELECT COUNT(*) FROM failure_incident").fetchone()[0]
        cats: List[Dict[str, Any]] = []
        if cat_col:
            q = f"SELECT {cat_col}, COUNT(*) c FROM failure_incident GROUP BY {cat_col} ORDER BY c DESC"
            cats = [{"category": r[0], "count": int(r[1])} for r in con.execute(q)]
        sevs = []
        if sev_col:
            q = f"SELECT {sev_col}, COUNT(*) c FROM failure_incident GROUP BY {sev_col} ORDER BY c DESC"
            sevs = [{"severity": r[0], "count": int(r[1])} for r in con.execute(q)]
        n_dev = con.execute("SELECT COUNT(*) FROM device").fetchone()[0]
        n_link = 0
        for t in ("link", "links"):
            try:
                n_link = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                break
            except Exception:
                pass
        return {
            "seed": name,
            "available": True,
            "n_incidents": int(n),
            "n_devices": int(n_dev),
            "n_links": int(n_link),
            "categories": cats,
            "severities": sevs,
        }
    finally:
        con.close()


def main() -> None:
    per = [seed_coverage(n, p) for n, p in SEEDS]
    # union of categories
    union: Dict[str, int] = {}
    for s in per:
        for c in s.get("categories") or []:
            union[str(c["category"])] = union.get(str(c["category"]), 0) + int(c["count"])
    out = {
        "note": (
            "Coverage of already-injected incident categories in frozen ECNetBench instances. "
            "This is NOT a claim of newly generated scenarios."
        ),
        "per_seed": per,
        "category_totals_across_seeds": [
            {"category": k, "count": v} for k, v in sorted(union.items(), key=lambda x: -x[1])
        ],
        "n_distinct_categories": len(union),
    }
    # attach RCA confusion classes if available
    rca_classes = {}
    for f in sorted((ROOT / "results" / "per_seed").glob("*.json")):
        if f.name.endswith("_ERROR.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        classes = (
            d.get("tasks", {}).get("T3_rca", {}).get("ecn_proposed__full", {}).get("classes")
        )
        if classes:
            rca_classes[d.get("seed_name") or f.stem] = classes
    out["rca_predicted_classes_per_seed"] = rca_classes
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT, "n_categories", len(union))


if __name__ == "__main__":
    main()
