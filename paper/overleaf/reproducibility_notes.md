# Reproducibility Notes (double-blind review version)

## Source of truth (numerical)
- Authoritative final T1 head: `results/manuscript_ready_numbers.json` → `T1_final_proposed`
  - mean AUPRC: `0.11522078115707056`
  - bootstrap 95% CI: `[0.0678984305675343, 0.16797282350001838]`
  - supporting selection: `results/v3_gated/t1_architecture_selection.json`
- Authoritative RF telem baseline T1 AUPRC mean: `0.07583814878524626`
- Authoritative T2 recommended head (telem logistic) AUPRC mean: `0.038043099063649714`
- Latest full-suite harness (`results/aggregate_v3.json`) may show a slightly different
  `ecn_proposed__full` mean (~0.1106). That is a harness re-run, **not** a replacement of
  the architecture-selection final claim. See `results/PUBLICATION_PROVENANCE.json`.

## Code / data for review
Provide the anonymized archive for double-blind review. Camera-ready may restore the public
repository URL. Evaluation uses **relative paths only** from the repository root.

## Relative paths only
Private absolute paths must not appear in committed result JSON.

## Environment
See `requirements.txt` / `environment.yml`. Python 3.10+ recommended (3.11 preferred).

## Full evaluation
```text
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_instances.py
python scripts/verify_instances.py
pytest -q
python evaluation/select_t1_architecture.py
python -m evaluation.run_full_evaluation
python -m evaluation.sync_publication_artifacts
python paper/overleaf/scripts/generate_latex_tables.py
python paper/overleaf/scripts/regenerate_pub_figures_v3.py
python -m evaluation.update_manuscript_extensions_v4
```

## Large data
SQLite instances (~1.2 GB total) are distributed via release tag `ecnetbench-v1.1.0-data`
and verified with `benchmark/INSTANCE_CHECKSUMS.json`.

## Healing caveat
Report `healing__no_rca_cat` for honest decision-support performance; `healing__full` uses RCA category features and reaches macro-F1 1.0 on this synthetic setup.
