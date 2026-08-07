# ECNetBench / ECN-v3 — Overleaf Package

**Title:** A Digital-Twin Multi-Agent Framework for Enterprise Cognitive Networking: ECNetBench and Leakage-Safe Multi-Seed Evaluation

**Final architecture:** leakage-safe enriched features + anchored fusion (`ECNFusionModel`) + TreeSHAP RCA. Stacking is a T1 ablation.

## Upload to Overleaf

1. Upload `ECN_Tier1_IEEE_Overleaf.zip` from the repository root (or this folder’s parent packaging script output) via **New Project → Upload Project**.
2. Set the main document to `main.tex`.
3. Compile with **pdfLaTeX + BibTeX + pdfLaTeX ×2**.

This folder is the canonical manuscript source synchronized with GitHub at `paper/overleaf/`.

## Structure

- `main.tex` — IEEE journal manuscript
- `sections/` — numbered sections
- `figures/` — vector PDF + 600 dpi PNG
- `tables/` — IEEE tables from verified metrics
- `results/paper_metrics.json` — compact metrics used for tables/figures
- `scripts/regenerate_pub_figures_v3.py` — regenerate publication figures
- `references.bib` — BibTeX
- `supplementary/` — appendix

## Reproduce numbers (companion repo root)

```bash
pip install -r requirements.txt
python scripts/download_instances.py
python scripts/verify_instances.py
python evaluation/select_t1_architecture.py
python paper/overleaf/scripts/regenerate_pub_figures_v3.py
```

Do not modify frozen benchmark instances.
