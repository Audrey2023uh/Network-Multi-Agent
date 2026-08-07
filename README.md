# ECNetBench + Enterprise Cognitive Network (ECN)

Reproducible benchmark and multi-agent evaluation for enterprise cognitive networking research.

**Repository:** https://github.com/Audrey2023uh/Network-Multi-Agent

## Layout

```
benchmark/          # generator, schemas, protocol, frozen instances
framework/          # Digital Twin + multi-agent ECN implementation
baselines/          # B01 baseline registry
evaluation/         # multi-seed evaluation harness
results/            # per-seed JSON, aggregate metrics, mirrored tables/figures
figures/            # ROC/PR, calibration, confusion matrices
tables/             # CSV performance / ablation / significance tables
reports/            # journal framing, audits, validation reports
paper/overleaf/     # IEEE manuscript (canonical Overleaf source; always synced)
presentation/       # journal PowerPoint + architecture diagrams + build script
docs/               # dataset card, datasheet, model card, specs
tests/              # audit and unit tests
scripts/            # checksums, parquet export, packaging helpers
```

## Final architecture (ECN-v3)

- **T1:** leakage-safe enriched features + **anchored** fusion (`ECNFusionModel`)
- **T2:** telemetry logistic (recommended head)
- **RCA:** RF + TreeSHAP
- **Stacking:** T1 ablation / negative result

Exact manuscript numbers: `results/manuscript_ready_numbers.json`.  
Architecture selection: `reports/FINAL_ARCHITECTURE_SELECTION.md`.

## Manuscript / Overleaf

Canonical LaTeX project: [`paper/overleaf/`](paper/overleaf/).  
Upload-ready ZIP is generated as `ECN_Tier1_IEEE_Overleaf.zip` at the repository root.

## Quick start

```bash
# Python 3.11 recommended
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Optional: Git LFS for large instance files
git lfs install
git lfs pull

# Verify instances
python scripts/verify_instances.py

# Tests
pytest -q

# Full six-seed evaluation (read-only on benchmark/)
python evaluation/run_full_evaluation.py
```

## Benchmark instances

| ID | Path | Seed |
|----|------|------|
| v1.1.0-INST (frozen) | `benchmark/instances/v1/` | 20260806 |
| seed101 … seed505 | `benchmark/instances/v1.1-seed{N}/` | 101…505 |

Each instance provides SQLite (`ecnetbench_v1.sqlite`). CSV and Parquet are included where disk/Git LFS budgets allow; see `docs/DATA_ACCESS.md`.

**Do not modify frozen instances.**

## Protocol

- Temporal freeze split **70% / 15% / 15%**
- Features at time `t0` use only observations with `observed_at ≤ t0`
- Primary ranking metric under imbalance: **AUPRC**
- Multi-seed mean ± 95% CI; paired Wilcoxon + Cliff’s δ

## Reports

- `reports/JOURNAL_FRAMING_OPTIMIZED.md` — defensible paper claims
- `reports/ECN_EVALUATION_REPORT.md` — full metrics
- `reports/CODE_AUDIT.md` — correctness / leakage audit
- `reports/TRACEABILITY.csv` — metric → script → file map
- `docs/REPRODUCIBILITY_CHECKLIST.md`

## Citation

See `CITATION.cff` and `LICENSE` (MIT).
