# Dataset Card — ECNetBench v1.1.0-INST

## Identity

| Field | Value |
|---|---|
| Name | ECNetBench |
| Version | 1.1.0-INST (FROZEN) |
| Type | Synthetic enterprise network telemetry + labels |
| Profile | campus_hybrid_v1 (HQ campus + branch, VSX, WAN BGP) |
| Seed | 20260806 |
| Time range | 2025-01-06 → 2025-01-20 (14 days, UTC) |
| Cadence | 5-minute telemetry (documented downsample) |
| Formats | CSV, Parquet, SQLite |
| Instance path | `09_artifacts/instances/v1/` |

## Intended use

- Research benchmark for cognitive networking: anomaly detection, failure prediction, RCA, impact estimation, degradation forecasting.
- Algorithm comparison under **fixed temporal manifests** in `publication_validation/v1.1.0-INST/manifests/`.

## Out of scope

- Not a production traffic replay or anonymized enterprise export.
- EVPN/VXLAN tables empty by campus profile design.
- Not for training models that ingest label oracle fields (`incident_id`, `y_*_gt` scores, incident description text).

## Risks / leakage

See `reports/LEAKAGE_REPORT.md`. Description text encodes failure category; treat as metadata only.

## Evaluation protocol

Use temporal manifests. Report **Average Precision** and ROC-AUC (not accuracy). Document feature exclusions.

## License / citation

To be set by authors for journal release. Cite version `1.1.0-INST` and seed `20260806`.

## Validation package

This folder (`publication_validation/v1.1.0-INST`) is the independent publication-readiness package and does not modify the frozen instance.
