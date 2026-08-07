# Data generation notes (ECNetBench)

## Authoritative store
SQLite (`ecnetbench_v1.sqlite`) per instance folder under `benchmark/instances/`.

## Generator
Companion repository: `benchmark/generator/` (`generate_ecnetbench.py`, realism upgrades, export utilities). Generation constraints are documented in `benchmark/GENERATION_CONSTRAINTS.md`.

## Frozen instances (do not modify)
| Folder | Role |
|--------|------|
| v1 | v1.1.0-INST |
| v1.1-seed101 | seed 101 |
| v1.1-seed202 | seed 202 |
| v1.1-seed303 | seed 303 |
| v1.1-seed404 | seed 404 |
| v1.1-seed505 | seed 505 |

Checksums: `benchmark/INSTANCE_CHECKSUMS.json`.

## Labels
Supervised targets for anomaly windows, failure horizons, RCA categories, impact, degradation, and config risk follow the LBL protocol with temporal freeze.

## Exports
CSV/Parquet are derivatives. Evaluation does not require CSV. Seed404 Parquet may be partial depending on disk; SQLite remains sufficient.
