#!/usr/bin/env python3
"""
Export Parquet tables from an instance SQLite (read-only on DB).
Used to regenerate missing Parquet for seed404 when disk allows.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--max-tables", type=int, default=0, help="0 = all tables")
    args = ap.parse_args()

    if not args.db.exists():
        print("DB missing", args.db)
        return 1
    free_gb = None
    try:
        import shutil

        free_gb = shutil.disk_usage(args.out_dir.parent if args.out_dir.parent.exists() else Path(".")).free / (1 << 30)
        print(f"free_gb={free_gb:.2f}")
        if free_gb < 0.5:
            print("Insufficient disk (<0.5 GiB free); refusing Parquet export.")
            return 2
    except Exception:
        pass

    args.out_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    if args.max_tables:
        tables = tables[: args.max_tables]
    for t in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {t}", con)
            out = args.out_dir / f"{t}.parquet"
            df.to_parquet(out, index=False)
            print("wrote", out.name, len(df))
        except Exception as e:
            print("skip", t, e)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
