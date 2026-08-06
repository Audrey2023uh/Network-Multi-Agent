# Datasheet for Datasets — ECNetBench v1.1.0-INST

Following Gebru et al., *Datasheets for Datasets* (abridged for synthetic network benchmark).

## Motivation

- **For what purpose was the dataset created?** Provide a reproducible enterprise cognitive-networking benchmark aligned with HPE Aruba AOS-CX campus/branch operations.
- **Who created it?** Synthetic generator under Network_Journal/Data project (seeded).
- **Who funded it?** Not specified in instance metadata.

## Composition

- **What do instances represent?** Devices, interfaces, links, control-plane sessions, telemetry samples, incidents, services, graph snapshots, ML labels.
- **How many instances?** See `instances/v1/reports/manifest.json` (on the order of ~10^5–10^6 telemetry rows; 19 devices; ~37 incidents).
- **Contains confidential data?** No — fully synthetic.
- **Recommended data splits?** Temporal 70/15/15 manifests in this package; optional HQ→branch topology split.

## Collection / generation process

- **How was data acquired?** Procedural generation with diurnal multipliers, causal fault injection, imperfect polling — not Uniform IID fields.
- **Over what timeframe?** Simulated 14 days starting 2025-01-06.
- **Does data reflect people?** Synthetic user/endpoint identifiers only.

## Preprocessing

- Telemetry intentionally includes dropped/delayed samples.
- Labels are ground-truth derived from injected incidents; some oracle fields exist for evaluation only.

## Uses

- **Approved:** ML benchmarking with leakage-safe features; systems research on RCA/impact.
- **Not approved:** Claiming results as production enterprise performance; using description/category text as RCA input.

## Distribution

- Distributed as CSV/Parquet/SQLite with SHA256 checksums in this validation package.

## Maintenance

- **Version frozen:** 1.1.0-INST must not be regenerated in place; future versions get new instance directories.

## Independent validation

- See IPRI score in `reports/INDEPENDENT_READINESS_SCORE.md`.
