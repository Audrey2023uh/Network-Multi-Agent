# ECNetBench + Enterprise Cognitive Network (ECN)

Reproducible benchmark and multi-agent evaluation for enterprise cognitive networking research.

# EEG Pre-Movement Intention Detectability

**Author:** Audrey Rah  
**Department of Electrical and Computer Engineering**  
**University of Houston**

Methods-faithful computational analysis of pre-movement EEG signals from the PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB v1.0.0), supporting rest-versus-motor statistical detectability evaluation for BCI-oriented rehabilitation research.

## Overview

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
interactive_dashboard/  # data-driven React NOC dashboard (GitHub Pages)
docs/               # dataset card, datasheet, model card, specs
tests/              # audit and unit tests
scripts/            # checksums, parquet export, packaging helpers
```

## Interactive dashboard

Static, data-driven NOC UI under [`interactive_dashboard/`](interactive_dashboard/).  
Builds JSON from SQLite + `results/` at build time (`scripts/build_data.py`).  
See [`interactive_dashboard/README.md`](interactive_dashboard/README.md) and [`DATA_PROVENANCE.md`](interactive_dashboard/DATA_PROVENANCE.md).

After GitHub Pages is enabled: https://audrey2023uh.github.io/Network-Multi-Agent/

## Final architecture (ECN-v3)

- **T1:** leakage-safe enriched features + **anchored** fusion (`ECNFusionModel`)
- **T2:** telemetry logistic (recommended head)
- **RCA:** RF + TreeSHAP
- **Stacking:** T1 ablation / negative result

Exact manuscript numbers: `results/manuscript_ready_numbers.json` (authoritative final T1).  
Architecture selection: `reports/FINAL_ARCHITECTURE_SELECTION.md`.  
Provenance of any harness vs selection mismatch: `results/PUBLICATION_PROVENANCE.json`.

**Important:** `results/aggregate_v3.json` is the latest full-suite harness (baselines / deep models). Its `ecn_proposed__full` mean may differ slightly from the architecture-selection final T1 mean (~0.11522). Do **not** overwrite manuscript-final claims with harness re-run means.

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
python -m evaluation.run_full_evaluation
python -m evaluation.sync_publication_artifacts
python paper/overleaf/scripts/generate_latex_tables.py
python paper/overleaf/scripts/regenerate_pub_figures_v3.py
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
