#!/usr/bin/env python3
"""Download ECNetBench SQLite instances from a GitHub Release into benchmark/instances/."""
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "Audrey2023uh/Network-Multi-Agent"
DEFAULT_TAG = "ecnetbench-v1.1.0-data"
ASSETS = {
    "v1": "ecnetbench_v1_frozen.sqlite",
    "v1.1-seed101": "ecnetbench_v1.1-seed101.sqlite",
    "v1.1-seed202": "ecnetbench_v1.1-seed202.sqlite",
    "v1.1-seed303": "ecnetbench_v1.1-seed303.sqlite",
    "v1.1-seed404": "ecnetbench_v1.1-seed404.sqlite",
    "v1.1-seed505": "ecnetbench_v1.1-seed505.sqlite",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--tag", default=DEFAULT_TAG)
    ap.add_argument("--checksums", type=Path, default=ROOT / "benchmark" / "INSTANCE_CHECKSUMS.json")
    args = ap.parse_args()

    expected = {}
    if args.checksums.exists():
        raw = json.loads(args.checksums.read_text(encoding="utf-8"))
        for folder, meta in raw.items():
            expected[folder] = meta.get("sha256")

    # If benchmark/instances is a junction, downloads write into the linked tree.
    # Prefer a real directory when creating fresh clones.
    inst = ROOT / "benchmark" / "instances"
    inst.mkdir(parents=True, exist_ok=True)

    ctx = ssl.create_default_context()
    for folder, asset in ASSETS.items():
        url = f"https://github.com/{args.repo}/releases/download/{args.tag}/{asset}"
        dest_dir = inst / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "ecnetbench_v1.sqlite"
        print("GET", url)
        try:
            with urllib.request.urlopen(url, context=ctx) as resp, dest.open("wb") as out:
                while True:
                    b = resp.read(1 << 20)
                    if not b:
                        break
                    out.write(b)
        except Exception as e:
            print("FAILED", folder, e)
            print("If the release is not published yet, copy SQLite files manually into benchmark/instances/<folder>/")
            return 1
        digest = sha256(dest)
        print(folder, "bytes", dest.stat().st_size, "sha256", digest)
        if expected.get(folder) and expected[folder] != digest:
            print("CHECKSUM MISMATCH for", folder)
            return 2
    print("All instances downloaded and verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
