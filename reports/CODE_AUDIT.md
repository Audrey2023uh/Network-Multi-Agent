# Code correctness and leakage audit

**Date:** 2026-08-06  
**Scope:** `framework/`, `evaluation/`, `baselines/`, `benchmark/` (read-only instances)

## Component coverage

| Component | Status | Location |
|-----------|--------|----------|
| ECNetBench SQLite load (RO URI) | Pass | `framework/ecn/twin.py` `DigitalTwin.load` / `open_ro` |
| Temporal 70/15/15 | Pass | `framework/ecn/features.py` `temporal_masks` |
| Leakage-safe features | Pass | feat_bin = t0 − 30min; expanding z uses `shift(1)`; RCA excludes incident description |
| Digital Twin graph | Pass | adjacency, structural + neighbor aggregates |
| PerceptionAgent | Pass | `framework/ecn/agents/core.py` |
| Anomaly/Prediction/RCA/Impact/Healing | Pass | agents + evaluation harness |
| Orchestrator + anchored fusion | Pass | `ECNFusionModel` telem-anchored nesting |
| Baselines | Pass | threshold/EWMA/IF/logistic/RF/LGBM/MLP; telem_only features |
| Ablations | Pass | full/no_twin/no_nbr/telem_only/twin_only |
| Imbalance handling | Pass | class_weight / scale_pos_weight |
| Calibration reporting | Pass | reliability curves + Brier in `eval_binary` |
| Stats + multi-seed CI | Pass | `mean_ci`, Wilcoxon, Cliff’s δ, aggregate |

## Issues checked

| Risk | Verdict |
|------|---------|
| Future information in features | Mitigated (past bins / expanding history shift) |
| Train/val/test contamination | Mitigated (disjoint temporal masks) |
| Hardcoded absolute paths in harness | Fixed (relative to repo root) |
| Hardcoded metrics | None in code; metrics computed at runtime |
| Cached-result reuse as “fresh” | Reference aggregate stored separately as `aggregate_reference.json`; reproduction regenerates `aggregate.json` |
| Fusion nesting | Anchored fusion requires telem weight ≥ 0.5 unless telem_only |
| Baseline unfairness | Baselines use telem_only; proposed uses twin+telem (documented) |
| Healing category features | Documented as post-RCA oracle features; ablation `no_rca_cat` required |
| ERROR JSON / private paths in old results | Excluded from commit; regenerating cleans outputs |

## Residual limitations

- RCA/healing test support is small (few incidents in holdout) → wide CIs.
- Proposed T1 does not dominate RF/logistic under multi-seed tests (see framing report).
- Full CSV trees may be LFS/release-hosted due to size.

## Verdict
**PASS with residual scientific limitations documented.** Suitable for reproducible evaluation after clean six-seed rerun.
