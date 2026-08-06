# Datasheet — ECNetBench

## Motivation
Public enterprise NetOps ML resources fragment topology, telemetry, service impact, and recovery labels. ECNetBench provides a joint schema and frozen instances under a normative protocol.

## Composition
Relational SQLite warehouse + CSV/Parquet exports + typed graph projections. Labels: anomaly windows, failure horizons, RCA, impact, degradation, config risk. Recovery actions and service impacts included.

## Collection / generation
Synthetic generator (`benchmark/generator`) with realism constraints (addressing, temporal protocol state, alert FP/FN, telemetry gaps). No production customer packet captures.

## Preprocessing
Evaluation features are built leakage-safely from observations at or before each decision time. Forbidden: future counters, incident free-text descriptions as RCA features, causal edge labels as inputs.

## Uses
Benchmarking detectors, predictors, RCA, and recovery recommenders; ablation of digital-twin features; multi-seed robustness.

## Distribution
GitHub repository with Git LFS for large binaries where applicable. See `docs/DATA_ACCESS.md`.

## Maintenance
Frozen v1 instances must not be overwritten. New seeds use new directories only.
