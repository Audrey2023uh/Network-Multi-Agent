# Data access and large files

## Authoritative format
**SQLite** (`ecnetbench_v1.sqlite`) is the authoritative instance store for evaluation.

## Why SQLite is not in git
Six instances are ~1.2 GB total. Local disk and GitHub LFS free quotas are insufficient to store duplicate copies inside `.git`. Therefore:

1. Git stores **code, checksums, reports, figures, tables**.
2. SQLite binaries are published as a **GitHub Release** tag `ecnetbench-v1.1.0-data`.
3. Fetch with:

```bash
python scripts/download_instances.py
python scripts/verify_instances.py
```

Expected SHA-256 digests: `benchmark/INSTANCE_CHECKSUMS.json`.

## CSV / Parquet
Full CSV trees (~200 MB/instance) are **not** in git. Evaluation does not require CSV.

- **seed404 Parquet:** partial export (25 tables) was generated during packaging when disk allowed; re-run:
  `python scripts/export_parquet.py --db benchmark/instances/v1.1-seed404/ecnetbench_v1.sqlite --out-dir benchmark/instances/v1.1-seed404/parquet`

## Local development alternative
Junction or copy a trusted local archive into `benchmark/instances/` so paths match `evaluation/run_full_evaluation.py`.
