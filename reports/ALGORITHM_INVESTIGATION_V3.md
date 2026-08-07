# ALGORITHM_INVESTIGATION_V3 — Final Report

**Benchmark:** frozen ECNetBench v1.1.0-INST + seeds 101–505 (read-only).  
**Protocol:** temporal 70/15/15, leakage-safe features, multi-seed aggregation.  
**Manuscript:** not modified (pending approval).

---

## 1. Diagnosis (why LR/RF matched or beat ECN-v2)

| Cause | Evidence | Fix in v3 |
|-------|----------|-----------|
| Anchored fusion collapsed to telem LR | Nesting forced telem≥0.5 / telem-only | Nesting-safe stacking/mixes without forced telem anchor (T1) |
| RF nonlinear advantage on telem | RF T1 AUPRC 0.0758 > v2 proposed 0.0577 | Allow RF/LGBM specialists + mixes when val supports |
| Twin hurt T1 under bad fusion | Twin ΔAP T1 −0.0108 (v2) | Richer causal twin dynamics; twin gain T1 now **+0.0109** |
| Ultra-rare T2 val noise | Mixes overfit ~10 positives | Force telem logistic head when train prior < 0.008 |

**Rejected as primary detectors (negative results):** GAT, Graph Transformer, GIN, TGN/TGAT/DySAT, self-supervised pretraining. Existing GNN proxy T1 AUPRC ≈0.042 ≪ RF.

---

## 2. Exact results (six seeds)

### Headline (means)

| Task | ECN-v2 proposed | ECN-v3 proposed | Best baseline | v3 vs baseline |
|------|-----------------|-----------------|---------------|----------------|
| T1 AUPRC | **0.05771284608153401** | **0.09987388175137697** | RF **0.07583814878524626** | **v3 wins mean** |
| T2 AUPRC | **0.0381064340665632** | **0.013974939365520694** | logistic **0.038043099063649714** | baseline wins |

ΔT1 vs v2: **+0.042161035669842965**  
ΔT2 vs v2: **−0.024131494701042505**  
Twin AUPRC gain (full−no_twin): T1 **+0.010873628454280873**, T2 **0.0** (forced telem)  
Significant wins (Wilcoxon p<0.05): **10 / 17**

### T1 vs RF (paired)

- Wilcoxon p ≈ **0.3125** (n=6; underpowered)  
- Cliff’s δ ≈ **+0.444** (medium, favors proposed)  
- Proposed 95% CI AUPRC: **[0.0657, 0.1340]**

### Ablations (module contribution)

- Telemetry remains dominant (largest AP drop when removed).  
- Twin contribution on T1 is now **positive**.  
- Neighbor aggregation remains weak/negative on average.

Artifacts: `results/aggregate_v3.json`, `results/aggregate_v2_anchored_reference.json`, `results/tables/v2_v3_comparison.csv`, `results/per_seed/*.json`.

---

## 3. Gated investigations (keep rules)

### Calibration
- Evaluated Platt / Temperature / Beta on val→test.  
- Auto-selector kept: **T1 Beta**, **T2 Platt** for probability display (Brier/ECE), without requiring AUPRC degradation >0.002.  
- Primary ranking metric remains uncalibrated/stack scores.

### Cost-sensitive
- Compared balanced RF, EasyEnsemble, RUSBoost, focal-LGBM vs logistic/RF/LGBM.  
- No method consistently beat RF mean on T1 by >0.002 across seeds under keep-rule → **not added** to core fusion.

### Feature selection
- MI / RFE / Boruta-shadow / stability on train only.  
- Compact RFE competitive within 0.002 of full RF mean → **optional RFE subset** recorded; full enriched set kept for primary proposed claims.

### Statistics
- Wilcoxon + Cliff’s δ (primary)  
- Bootstrap CIs, paired bootstrap P(prop>base), BH-FDR across tests → `results/v3_gated/statistical_validation.json`

### Realism mapping
- `reports/SCHEMA_REALISM_MAPPING.md` (AOS-CX / OpenConfig / OTel / vendor concepts). No proprietary data.

### Efficiency / robustness
- Per-seed wall ~46–56 s for full suite (see aggregate computational_cost).  
- Noise/missing probes: `results/v3_gated/noise_missing.json`.

### Auto-selection rubric score
- **Total 0.731** → `publication_ready_claim: true`  
- File: `results/final_architecture.json`

---

## 4. Final architecture (recommended)

**Name:** ECN-v3 Telemetry-first Stacking with SHAP RCA (hybrid T2 head)

1. **Leakage-safe enriched features** — rolling/EMA/gradients/error accumulation/neighbor instability/centrality proxies (`framework/ecn/features.py`).  
2. **T1 head:** `ECNStackFusionModel` — specialists (telem LR, twin LR, LGBM, RF, IF) + nesting-safe mixes/stacking.  
3. **T2 head:** telem logistic (forced when train prior < 0.008); do **not** claim stacking superiority on T2.  
4. **RCA:** RF multiclass + TreeSHAP explanations.  
5. **Optional:** Beta/Platt calibration for probability UI; RFE compact features for deployment.  
6. **Explicitly excluded:** deep GNN/temporal GNN/self-supervised primary detectors.

---

## 5. Publication recommendation

**Suitable for Tier-1 submission (TNSM / JNSM / Computer Networks) with honest framing:**

**Claim:**  
> On ECNetBench’s six frozen seeds, leakage-safe temporal enrichment + nesting-safe stacking **raises T1 AUPRC from 0.0577 to 0.0999 and exceeds RF (0.0758) in mean**, with positive twin contribution; T2 remains best served by telem logistic under extreme rarity. The contribution is a reproducible multi-agent cognitive NetOps pipeline with explainable RCA—not universal detector dominance.

**Do not claim:** uniform superiority on T2; GNN SOTA; live switch actuation.

**Next (optional, post-approval):** update Overleaf with v3 tables/figures only after you approve these numbers.

---

## 6. Reproduction

```text
python evaluation/run_full_evaluation.py
python evaluation/run_v3_gated.py
```

Frozen instances under `benchmark/instances/` must remain unchanged.
