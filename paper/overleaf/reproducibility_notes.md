# Reproducibility Notes

## Source of truth
- Code/data: https://github.com/Audrey2023uh/Network-Multi-Agent
- Verified aggregate: `results/aggregate.json`
- Exact T1 proposed AUPRC mean: `0.05771284608153401`
- Exact T1 RF AUPRC mean: `0.07583814878524626`
- Exact T2 proposed AUPRC mean: `0.0381064340665632`
- Exact T2 logistic AUPRC mean: `0.038043099063649714`

## Relative paths only
All scripts in this package and the GitHub harness use relative paths from the repository root. Private Windows paths must not appear in committed result JSON.

## Environment
See `requirements.txt` / `environment.yml` in the GitHub repository. Python 3.10+ recommended.

## Full evaluation
```text
python evaluation/run_full_evaluation.py
python scripts/generate_latex_tables.py   # from this Overleaf package
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Large data
SQLite instances (~1.2 GB total) are distributed via GitHub Release `ecnetbench-v1.1.0-data` and verified with `benchmark/INSTANCE_CHECKSUMS.json`.

## Healing caveat
Report `healing__no_rca_cat` for honest decision-support performance; `healing__full` uses RCA category features and reaches macro-F1 1.0 on this synthetic setup.
