# Dataset Card — ECNetBench

## Dataset summary
ECNetBench is a synthetic enterprise networking benchmark aligned with HPE Aruba AOS-CX–style semantics. It provides multi-modal telemetry, typed topology, incidents, recovery actions, and supervised labels for anomaly detection, failure prediction, RCA, impact, degradation, and configuration risk.

## Instance versions
- **Frozen:** `benchmark/instances/v1` (v1.1.0-INST, seed 20260806)
- **Robustness seeds:** `v1.1-seed101` … `v1.1-seed505`

## Modalities
Inventory, interfaces/links, routing/VSX/STP samples, counters, syslog/alerts, service KPIs, failure–recovery–impact chain, graph projections, ML labels T1–T6.

## Splits
Official evaluation uses temporal freeze 70/15/15 (train/val/test) by time; features at `t0` use `observed_at ≤ t0` only.

## Intended use
Research on cognitive networking, digital twins, multi-agent NetOps, anomaly/failure prediction, explainable RCA, and recovery decision support.

## Limitations
Synthetic generation; class imbalance is severe (~1% anomaly prior); small RCA/healing holdout counts; some Parquet exports may be absent for alternate seeds (SQLite is authoritative).

## License
MIT (see repository `LICENSE`).
