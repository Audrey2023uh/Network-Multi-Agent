# Reproducibility checklist

- [ ] `git clone https://github.com/Audrey2023uh/Network-Multi-Agent.git`
- [ ] `git lfs install && git lfs pull`
- [ ] `pip install -r requirements.txt` (Python 3.11)
- [ ] `python scripts/verify_instances.py` (all six SQLite present)
- [ ] `pytest -q`
- [ ] `python evaluation/run_full_evaluation.py`
- [ ] Compare `results/aggregate.json` T1/T2 AUPRC means to `reports/JOURNAL_FRAMING_OPTIMIZED.md`
- [ ] Confirm no absolute user paths in `results/per_seed/*.json`
- [ ] Confirm frozen instances were not modified (checksums unchanged)
