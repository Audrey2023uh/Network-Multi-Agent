# ECNetBench v1.1.0-INST — Independent Publication Validation

This package validates the **frozen** instance at `../../instances/v1` without modifying it.

## Quick start

```bash
pip install -r requirements.txt
python run_publication_validation.py
```

## Outputs

| Artifact | Path |
|---|---|
| Dataset card | `DATASET_CARD.md` |
| Datasheet | `DATASHEET.md` |
| Benchmark tasks | `BENCHMARK_TASKS.md` |
| Split manifests | `manifests/` |
| Leakage report | `reports/LEAKAGE_REPORT.md` |
| Baselines | `reports/BASELINE_RESULTS.md` |
| Ablations | `reports/ABLATION_REPORT.md` |
| Seed sensitivity | `reports/SEED_SENSITIVITY_REPORT.md` |
| IPRI readiness | `reports/INDEPENDENT_READINESS_SCORE.md` |
| Checksums | `checksums/SHA256SUMS.txt` |

## Important

IPRI is **independent** of the earlier realism audit (52→100). A high realism score does not automatically imply publication readiness under holdout/leakage/seed gates.
