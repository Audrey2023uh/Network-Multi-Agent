# ALGORITHM_INVESTIGATION_V3 — Final Report

**Benchmark:** frozen ECNetBench v1.1.0-INST + seeds 101–505 (read-only).  
**Protocol:** temporal 70/15/15, leakage-safe features, multi-seed aggregation.  
**Manuscript:** not modified (pending approval).  
**Architecture selection update:** T1 final head is **anchored fusion** (not stacking). See `reports/FINAL_ARCHITECTURE_SELECTION.md`.

---

## 1. Diagnosis (why LR/RF matched or beat ECN-v2)

| Cause | Evidence | Fix in v3 |
|-------|----------|-----------|
| Anchored fusion on **legacy** features underperformed RF | v2 proposed T1 AUPRC 0.0577 &lt; RF 0.0758 | Leakage-safe feature enrichment (dominant gain) |
| RF nonlinear advantage on telem | RF T1 AUPRC 0.0758 | Specialists still include RF/LGBM under val selection |
| Twin hurt T1 under bad fusion (v2) | Twin ΔAP T1 −0.0108 (v2) | Richer causal twin dynamics; twin gain under final anchored head is near-zero mean (seed-dependent) |
| Ultra-rare T2 val noise | Mixes overfit ~10 positives | T2 head: telem logistic (do not claim fusion superiority) |
| Stacking complexity without T1 gain | Isolation: stack on v3 features **hurts** mean AP vs anchored | **Stacking demoted to ablation / negative result** |

**Rejected as primary detectors (negative results):** GAT, Graph Transformer, GIN, TGN/TGAT/DySAT, self-supervised pretraining. Existing GNN proxy T1 AUPRC ≈0.042 ≪ RF.  
**Rejected as final T1 fusion:** `ECNStackFusionModel` (mean AP lower than anchored; more complex).

---

## 2. Exact results (six seeds)

### Headline (means) — **final proposed = v3 features + anchored**

| Task / config | Mean AUPRC | Notes |
|------|-----------------|---------------|
| ECN-v2 proposed (legacy + anchored) | **0.05771284608153401** | reference |
| ECN-v3 **stack ablation** (enriched + stack) | **0.0997458645152051** | ≈ prior published 0.09987; **not final** |
| ECN-v3 **final proposed** (enriched + anchored) | **0.11522078115707056** | selected |
| Best baseline RF telem_only | **0.07583814878524626** | final beats RF mean |

ΔT1 final vs v2: **+0.05750793507553655**  
ΔT1 final vs stack ablation: **+0.01547491664186545**  
Twin AUPRC gain (full−no_twin) under final anchored: **≈ +0.00035** (near zero mean)  

Exact staged floats: `results/manuscript_ready_numbers.json`.

### T1 architecture selection (anchored vs stack)

| Metric | Anchored (final) | Stacking (ablation) |
|---|---:|---:|
| AUPRC | **0.115221** | 0.099746 |
| ROC-AUC | 0.753359 | **0.780315** |
| Brier ↓ | 0.150915 | **0.083438** |
| ECE ↓ | 0.287995 | **0.157564** |
| AP std ↓ | 0.067858 | **0.032412** |
| Train time (s) | **2.214** | 2.284 |

Paired (anchored − stack) AUPRC: Wilcoxon **p=0.375**, Cliff δ **+0.111**, bootstrap P(anch&gt;stack)=**0.865**.  
Do **not** claim significant paired superiority over stacking (n=6 underpowered). Claim: higher mean AUPRC + simpler model.

### T1 vs RF (paired, final anchored)

- Wilcoxon p ≈ **0.6875** (n=6)  
- Cliff’s δ ≈ **+0.389**  
- Bootstrap P(anchored &gt; RF) ≈ **0.915**  
- Anchored AUPRC 95% CI (bootstrap): **[0.0679, 0.1680]**

### Ablations (module contribution)

- Feature enrichment is the dominant T1 gain (legacy→v3 under anchored ≈ +0.058).  
- Stacking on v3 features reduces mean T1 AUPRC vs anchored → **negative result**.  
- Telemetry remains dominant; twin mean gain under final head is negligible.

Artifacts: `results/v3_gated/t1_architecture_selection.json`, `results/v3_gated/t1_gain_traceability.json`, `results/aggregate_v3.json` (historical stack run), `results/final_architecture.json`.

---

## 3. Gated investigations (keep rules)

### Calibration
- Raw-score Brier/ECE favor stacking; for the **final anchored** head, keep **optional Beta** for probability display (does not change AUPRC ranking).  
- T2: optional Platt. Primary ranking metric remains AUPRC on task scores.

### Cost-sensitive / feature selection / stats / realism
Unchanged from prior gated study (`results/v3_gated/`). Compact RFE optional for deployment; full enriched set for primary claims.

### Efficiency
- Anchored mean train ≈ **2.21 s**; stacking ≈ **2.28 s**; RF ≈ **0.59 s**. Cost not decisive.

---

## 4. Final architecture (recommended)

**Name:** ECN-v3 Enriched Features with Anchored Telemetry-first Fusion + SHAP RCA

1. **Leakage-safe enriched features** — rolling/EMA/gradients/error accumulation/neighbor instability/centrality proxies (`framework/ecn/features.py`).  
2. **T1 head:** `ECNFusionModel` — telem≥0.5 anchored convex mixes / singletons on validation AUPRC.  
3. **T2 head:** telem logistic under ultra-rare prior; do **not** claim fusion/stack superiority on T2.  
4. **RCA:** RF multiclass + TreeSHAP explanations.  
5. **Optional:** Beta/Platt calibration for probability UI; RFE compact features for deployment.  
6. **Ablation / negative:** `ECNStackFusionModel` on T1 (lower mean AUPRC, higher complexity).  
7. **Explicitly excluded:** deep GNN/temporal GNN/self-supervised primary detectors.

Selection principle: **simplest scientifically defensible model with strongest reproducible performance** (primary = AUPRC).

Code path: `evaluation/run_full_evaluation.py` proposed method uses `ECNFusionModel`; stacking available as `ecn_stack_ablation`.

---

## 5. Publication recommendation

**Suitable for Tier-1 submission (TNSM / JNSM / Computer Networks) with honest framing:**

**Claim (staged — manuscript not yet edited):**  
> On ECNetBench’s six frozen seeds, leakage-safe temporal enrichment with **anchored telemetry-first fusion** raises T1 AUPRC from **0.0577 to 0.1152** and exceeds RF telem_only (**0.0758**) in mean. Nesting-safe stacking was evaluated and **does not improve** mean T1 AUPRC relative to anchored fusion (0.0997 vs 0.1152); it is reported as an ablation. T2 remains best served by telem logistic under extreme rarity. The contribution is a reproducible multi-agent cognitive NetOps pipeline with explainable RCA—not universal detector dominance.

**Do not claim:** paired significance of anchored vs stack (p=0.375); uniform superiority on T2; GNN SOTA; live switch actuation; that raw anchored scores are better calibrated than stack (use optional Beta for probabilities).

**Next (optional, post-approval):** update Overleaf with these staged numbers only after you approve.

---

## 6. Reproduction

```text
python evaluation/trace_t1_gain.py
python evaluation/select_t1_architecture.py
python evaluation/run_full_evaluation.py
```

Frozen instances under `benchmark/instances/` must remain unchanged.
