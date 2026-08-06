#!/usr/bin/env python3
"""Verify benchmark instance SQLite files exist and match expected seeds."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "benchmark" / "instances"

EXPECTED = {
    "v1": 20260806,
    "v1.1-seed101": 101,
    "v1.1-seed202": 202,
    "v1.1-seed303": 303,
    "v1.1-seed404": 404,
    "v1.1-seed505": 505,
}


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> int:
    report = {}
    ok = True
    for folder in EXPECTED:
        db = INST / folder / "ecnetbench_v1.sqlite"
        entry = {"path": str(db.relative_to(ROOT)).replace("\\", "/"), "exists": db.exists()}
        if db.exists():
            entry["bytes"] = db.stat().st_size
            entry["sha256"] = sha256(db)
        else:
            ok = False
        report[folder] = entry
        print(folder, "OK" if db.exists() else "MISSING", entry.get("bytes"))
    out = ROOT / "benchmark" / "instances" / "CHECKSUMS.json"
    # If junction, writing may go to source — prefer repo-local file
    out_local = ROOT / "benchmark" / "INSTANCE_CHECKSUMS.json"
    out_local.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Wrote", out_local)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
