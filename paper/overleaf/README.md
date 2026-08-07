# ECNetBench / ECN-v3 — Overleaf Package

**Title:** A Digital-Twin Multi-Agent Framework for Enterprise Cognitive Networking: ECNetBench and Leakage-Safe Multi-Seed Evaluation

**Final architecture:** leakage-safe enriched features + anchored fusion (`ECNFusionModel`) + TreeSHAP RCA. Stacking is a T1 ablation.

## Upload to Overleaf

1. Use the standalone ZIP already in this folder:

   **`ECN_Overleaf_Project.zip`**

   Or rebuild from the repository root:

```bash
python scripts/build_overleaf_zip.py
```

2. In Overleaf: **New Project → Upload Project** → select `paper/overleaf/ECN_Overleaf_Project.zip`.
3. Set the main document to `main.tex`.
4. Compile with **pdfLaTeX + BibTeX + pdfLaTeX ×2**.

The ZIP root contains `main.tex` (not nested under an extra folder). It includes `sections/`, `figures/`, `tables/`, `supplementary/`, `references.bib`, and `IEEEtran.cls` / `IEEEtran.bst`. It does **not** include `benchmark/`, `framework/`, `evaluation/`, `results/`, `scripts/`, `baselines/`, or `tests/`.

This folder is the canonical manuscript source synchronized with GitHub at `paper/overleaf/`.

## Structure

- `main.tex` — IEEE journal manuscript
- `sections/` — numbered sections
- `figures/` — vector PDF + 600 dpi PNG
- `tables/` — IEEE tables from verified metrics
- `references.bib` — BibTeX
- `supplementary/` — appendix
- `IEEEtran.cls` / `IEEEtran.bst` — IEEE style files for portable compile

## Reproduce numbers (companion repo root)

```bash
pip install -r requirements.txt
python scripts/download_instances.py
python scripts/verify_instances.py
python evaluation/select_t1_architecture.py
python paper/overleaf/scripts/regenerate_pub_figures_v3.py
```

Do not modify frozen benchmark instances.
