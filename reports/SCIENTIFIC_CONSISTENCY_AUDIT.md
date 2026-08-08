# Scientific Consistency Audit Report (ECNetBench / ECN-v3)

**Date:** 2026-08-08  
**Scope:** Manuscript numerical claims, architecture terminology, statistics, double-blind safety, reproducibility artifacts, GitHub ↔ Overleaf ↔ PDF synchronization.

## 1. Problems found

| ID | Problem | Severity |
|----|---------|----------|
| P1 | Final T1 AUPRC stated as ~0.11522 in selection artifacts vs ~0.1106 in latest `aggregate_v3.json` harness | Critical (consistency) |
| P2 | Manuscript prose sometimes used parametric CI `[0.0609, 0.1695]` instead of bootstrap `[0.0679, 0.1680]` | High |
| P3 | Ablation / practical-impact tables used harness `ecn_proposed` without labeling as non-final | High |
| P4 | Figure regen wrote parametric CI into `paper_metrics.json` for the final head | Medium |
| P5 | Double-blind Data/Code Availability previously contained identifiable GitHub username URL | Critical (ethics) |
| P6 | Cover letter contained identifiable GitHub URL; `CITATION.cff` in review ZIP would deanonymize | High |
| P7 | Excessive floating-point precision in abstract/intro/results/conclusion | Low (writing) |
| P8 | Historical stacking curve traces could be mistaken for final architecture | Medium (terminology) |

## 2. Root causes

1. **P1:** Two legitimate but different experiment snapshots. Architecture-selection / gated evaluation produced `T1_final_proposed` (mean **0.115220781…**). A later full-suite `run_full_evaluation.py` re-run produced harness `ecn_proposed__full` (mean **~0.11055**) due to RNG / fusion-path differences. Neither value was fabricated; they must not be silently conflated.
2. **P2/P4:** Figure/metrics helper used normal-theory mean±1.96·SE while the manuscript-authoritative interval is the archived bootstrap CI.
3. **P3:** Table generators pulled ablation/practical rows from harness aggregates without captions distinguishing selection vs harness.
4. **P5/P6:** Reproducibility wording reused the public repository URL inside the blinded manuscript package.
5. **P7/P8:** Historical precision and stacking ablations left in prose/curve JSON without always labeling the final anchored head.

## 3. Files changed (this audit pass)

- `evaluation/sync_publication_artifacts.py` (provenance + significance sync from selection vector)
- `results/manuscript_ready_numbers.json` (provenance block)
- `results/PUBLICATION_PROVENANCE.json` (new authoritative map)
- `paper/overleaf/main.tex` (double-blind availability; hypersetup; rounded abstract)
- `paper/overleaf/sections/01_introduction.tex`, `06_results.tex`, `09_conclusion.tex`
- `paper/overleaf/tables/tab_*.tex` (significance, deep baselines, ablation captions, practical caption)
- `paper/overleaf/scripts/regenerate_pub_figures_v3.py` (bootstrap CI for final T1)
- `paper/overleaf/scripts/generate_extensions_v4_tables.py`
- `paper/overleaf/scripts/package_overleaf_zip.py` (exclude `CITATION.cff`)
- `paper/overleaf/cover/cover_letter.txt`, `cover/highlights.md`
- `paper/overleaf/reproducibility_notes.md`, `README.md` (prior sync notes)
- Regenerated figures under `paper/overleaf/figures/` and mirrored metrics JSON
- Fresh ZIP: `paper/releases/ECNetBench_ECNv3_Overleaf_Final.zip`
- Compiled PDF: `paper/overleaf/main.pdf` and `paper/releases/ECNetBench_ECNv3_Manuscript_Final.pdf`

## 4. Numerical claims corrected / synchronized

| Claim | Authoritative value | Source |
|-------|---------------------|--------|
| Final T1 AUPRC mean | **0.1152** (exact 0.11522078115707056) | `results/manuscript_ready_numbers.json` → `T1_final_proposed` |
| Final T1 bootstrap 95% CI | **[0.0679, 0.1680]** | same (`auprc_ci95_bootstrap`) |
| RF T1 AUPRC | 0.0758 | harness / selection RF telem |
| ECN-v2 T1 AUPRC | 0.0577 | architecture selection |
| Stacking ablation T1 | 0.0997 | architecture selection |
| T2 telem logistic | 0.0380 | `aggregate_v3` recommended head |
| TabNet / GraphSAGE T1 | 0.0492 / 0.0152 | harness |
| Harness ablation `full` | 0.1106 | `aggregate_v3` (labeled as harness, not final) |
| Twin contribution | ≈ +0.00035 | manuscript_ready |

Policy: **do not overwrite** `T1_final_proposed` with harness means.

## 5. Experiments rerun / scripts executed

- `python evaluation/sync_publication_artifacts.py`
- `python paper/overleaf/scripts/regenerate_pub_figures_v3.py`
- `python interactive_dashboard/scripts/build_data.py`
- `python interactive_dashboard/scripts/validate_dashboard_data.py` (OK; manuscript AUPRC match)
- `pytest -q` / `tests/test_audit.py` (**8 passed**)
- `pdflatex` ×3 + `bibtex` (9-page PDF)
- `python paper/overleaf/scripts/package_overleaf_zip.py`

**Not re-run in this pass (frozen artifacts retained):** full six-seed `run_full_evaluation.py` wall-clock (~minutes–hours with TabNet/GraphSAGE). Prior measured deep-baseline numbers remain in `aggregate_v3.json`.

## 6. Tests passed

- `tests/test_audit.py`: 8 passed
- Dashboard validation: manuscript T1 AUPRC match `0.115220781…`
- PDF metadata: `/Author` empty; title/subject set for double-blind
- Overleaf ZIP: no `Audrey2023uh` / identifiable GitHub URL in packaged text artifacts; `CITATION.cff` excluded

## 7. Remaining limitations

- With **n=6**, paired Wilcoxon tests vs RF / stacking are underpowered; manuscript correctly reports non-significance where applicable.
- Harness vs selection means will diverge again if `run_full_evaluation.py` is re-run without regenerating architecture selection; always re-run `sync_publication_artifacts.py` after harness updates.
- Full clean-venv end-to-end reproduction (download instances → full eval) was not wall-clock completed in this audit session; documented workflow remains in README.
- Local historical reports under `reports/` may still contain absolute OneDrive paths from older audits; they are **not** in the Overleaf ZIP and are not cited as manuscript-final numbers.
- Camera-ready should restore real GitHub URL and `CITATION.cff` after acceptance.

## 8. Exact Git commit hash

*(filled after commit/push in the closing step of this audit.)*

## 9. Final Overleaf ZIP location

`paper/releases/ECNetBench_ECNv3_Overleaf_Final.zip`  
(mirror: `paper/overleaf/ECNetBench_ECNv3_Overleaf_Final.zip`)

Final PDF: `paper/releases/ECNetBench_ECNv3_Manuscript_Final.pdf`  
(source build: `paper/overleaf/main.pdf`)

## 10. Synchronization confirmation

| Artifact | Status |
|----------|--------|
| `results/manuscript_ready_numbers.json` | Authoritative final T1 |
| `results/PUBLICATION_PROVENANCE.json` | Maps selection vs harness |
| Overleaf tables / prose | Aligned to bootstrap CI and rounded means |
| Figures regenerated from selection + harness | Yes |
| Dashboard data | Validated against manuscript AUPRC |
| Double-blind manuscript wording | No identifiable GitHub username |
| Compiled PDF | 9 pages; empty author metadata |
| Overleaf ZIP | Fresh; excludes `CITATION.cff` |

**Verdict:** GitHub working tree, Overleaf source, generated figures/tables, JSON artifacts, and compiled PDF are synchronized under the dual-source policy (selection = final T1; harness = baselines/ablations/deep models with explicit labels).
