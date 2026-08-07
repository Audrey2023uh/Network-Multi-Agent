# T1 Improvement Traceability Report (ECN-v2 → ECN-v3)

**Question.** Is the six-seed mean T1 AUPRC change from **0.05771284608153401** (ECN-v2 anchored) to **0.09987388175137697** (ECN-v3 stack) caused by data leakage, nested-CV violations, test-set threshold tuning, or frozen-benchmark changes?

**Verdict.** **No.** Under an identical evaluation protocol, the gain is attributable to approved algorithmic changes—primarily **leakage-safe feature enrichment**. Stacking alone does not explain the published Δ. Frozen instances are byte-identical to the checksum manifest.

---

## 1. Frozen benchmark integrity

All six ECNetBench SQLite instances match `benchmark/INSTANCE_CHECKSUMS.json` (SHA-256 and byte size):

| Instance key | Bytes | Checksum status |
|---|---|---|
| v1 | 206643200 | OK |
| v1.1-seed101 | 206893056 | OK |
| v1.1-seed202 | 206974976 | OK |
| v1.1-seed303 | 206839808 | OK |
| v1.1-seed404 | 207089664 | OK |
| v1.1-seed505 | 207405056 | OK |

**ALL_CHECKSUMS_OK = True.** No instance files were modified for the v3 evaluation.

Reference aggregates (unchanged protocol, same DBs):

- `results/aggregate_v2_anchored_reference.json` → T1 `ecn_proposed__full` mean AP = **0.05771284608153401**
- `results/aggregate_v3.json` → T1 `ecn_proposed__full` mean AP = **0.09987388175137697**

---

## 2. Evaluation protocol identity vs ECN-v2

Protocol constants and procedures are shared with ECN-v2 except for the approved model/feature changes listed in §4.

| Protocol element | ECN-v2 | ECN-v3 | Identical? |
|---|---|---|---|
| Temporal freeze | `FREEZE_FRAC=0.70`, `VAL_FRAC=0.15` → 70/15/15 | same | Yes |
| Feature–label lag | `feat_bin = t_start − 30 min` | same | Yes |
| Split ordering | train end &lt; val &lt; test (time) | same; re-verified on all six seeds | Yes |
| Classical baselines | `telem_only` feature mode | same | Yes |
| Proposed feature mode (primary) | `full` | `full` (enriched column set) | Protocol same; feature set approved change |
| Fusion hyper-selection | validation AUPRC (+ train consistency) | same locus (val AP); candidate set expanded | Selection still val-only |
| Threshold tuning | `tune_threshold(y_va, …)` validation only | same | Yes |
| Primary T1 metric | AUPRC / average precision on **scores** | same; threshold unused for AP | Yes |
| Nested CV | Not used (fixed temporal holdout) | Not used | N/A — no nested-CV violation possible |

### 2.1 Thresholds do not enter AUPRC

In `framework/ecn/models.py`, `eval_binary` computes:

- F1 / precision / recall from `(scores ≥ threshold)` where `threshold` was tuned on **validation**
- **`ap` = `average_precision_score(y_true, s_norm)`** from continuous scores only

Therefore test-set threshold search cannot inflate the reported T1 AUPRC. Isolation script `evaluation/trace_t1_gain.py` computes AP from raw scores with no threshold at all and recovers the same order of magnitude / v2 exact match on configuration A.

### 2.2 Nested cross-validation

The benchmark does **not** use nested CV. Model and fusion selection use the fixed temporal validation fold; test is evaluated once. There is no outer/inner CV nesting to violate. Train–val consistency guards in stacking (reject mixes/stack if train AP collapses vs best singleton) are nesting-*safe* heuristics on the same val fold used in v2—not peeking at test.

### 2.3 Causal / leakage-safe feature ops (audited)

In `framework/ecn/features.py`:

- Expanding z-scores: `expanding().mean/std().shift(1)`
- Rolling / EMA: `shift(1)` before window / EWM
- Neighbor instability: previous-bin neighbor aggregates vs current
- Label join: features at `t_start − 30min` only

Isolation re-check on all six seeds: `split_temporal_ok=True`, `feat_bin_lag_30min_ok=True`.

---

## 3. Controlled isolation (feature × fusion)

Script: `evaluation/trace_t1_gain.py`  
Artifact: `results/v3_gated/t1_gain_traceability.json`

Four configurations, identical splits / seeds / DBs:

| ID | Features | Fusion | Six-seed mean T1 AP |
|---|---|---|---|
| **A** | Legacy (29 cols, v2 set) | `ECNFusionModel` (anchored v2) | **0.05771284608153401** |
| **B** | Legacy | `ECNStackFusionModel` | 0.05854630936658167 |
| **C** | Full v3 (56 cols) | `ECNFusionModel` (anchored v2) | **0.1153933378137879** |
| **D** | Full v3 | `ECNStackFusionModel` (published v3) | **0.09955161705887557** |

Configuration **A** matches the published v2 mean to floating-point identity → isolation recovers the v2 baseline under current code paths.

Configuration **D** mean (0.09955) matches published v3 (0.09987) within LGBM/sklearn run-to-run noise (~3e-4 absolute).

### 3.1 Attribution of Δ

| Contrast | Δ mean AP | Interpretation |
|---|---|---|
| B − A (stack on legacy) | **+0.00083** | Stacking alone ≈ null on legacy features |
| C − A (v3 features on anchored) | **+0.05768** | **Dominant driver** of T1 gain |
| D − B (v3 features on stack) | **+0.04101** | Features still dominate under stack fusion |
| D − C (stack on v3 features) | **−0.01584** | Stack slightly *hurts* mean T1 vs anchored+v3feat |
| D − A (published path) | **+0.04184** | Net published-style improvement |

**Conclusion.** The move from ~0.0577 to ~0.0999 is **not** produced by stacking, threshold tuning, leakage, or DB edits. It is produced by the **27 new leakage-safe columns** (second differences, causal roll/EMA, burst/accumulate error counters, neighbor instability / centrality proxies). Stacking was an approved nesting-safe fusion change; on T1 alone it is not the source of the lift (and is slightly worse than anchored fusion given the same enriched features).

### 3.2 Per-seed AUPRC (isolation)

| Seed | A legacy+anchored | B legacy+stack | C v3feat+anchored | D v3feat+stack |
|---|---:|---:|---:|---:|
| v1.1.0-INST | 0.0836 | 0.0588 | 0.1090 | 0.1086 |
| seed101 | 0.0990 | 0.0620 | 0.1519 | 0.1173 |
| seed202 | 0.0228 | 0.0228 | 0.2243 | 0.1425 |
| seed303 | 0.0114 | 0.0114 | 0.0242 | 0.0527 |
| seed404 | 0.0731 | 0.1398 | 0.1037 | 0.1037 |
| seed505 | 0.0564 | 0.0564 | 0.0792 | 0.0724 |

---

## 4. Exact approved algorithmic changes (traceable)

### 4.1 Feature engineering (`framework/ecn/features.py`)

**Legacy columns retained (29):**  
`cpu_mean`, `cpu_max`, `mem_mean`, `n_polls`, `err_sum`, `disc_sum`, `car_sum`, `d_cpu_mean`, `d_cpu_max`, `d_mem_mean`, `cpu_z`, `mem_z`, twin degree/role/neighbor aggregates as in v2.

**v3-only columns (27), all causal / prior-bin:**

- Second differences: `dd_cpu_mean`, `dd_cpu_max`, `dd_mem_mean`
- Causal rolls: `cpu_roll{3,6}_{mean,std}`, `mem_roll{3,6}_mean`
- Causal EMA: `cpu_ema`, `cpu_vs_ema`, `err_ema`, `disc_ema`, `car_ema`
- Causal accumulate/burst: `{err,disc,car}_{acc3,acc6,burst}`
- Twin dynamics: `twin_centrality_proxy`, `twin_nbr_cpu_delta`, `twin_nbr_err_delta`, `twin_nbr_instability`

These are the features that account for C−A ≈ +0.058 mean AP.

### 4.2 Fusion (`framework/ecn/models.py`)

| | ECN-v2 `ECNFusionModel` | ECN-v3 `ECNStackFusionModel` |
|---|---|---|
| Specialists | telem LR, twin tree/LR, RF, LGBM, IF | same training |
| Selection | telem≥0.5 anchored mixes + singletons on **val AP** | unconstrained mixes + logistic stack meta on specialist scores; margin over best singleton; optional force telem if train prior &lt; 0.008 (T2-oriented) |
| Test use | scores only for AP | same |

Stacking is nesting-safe relative to the fixed val fold (no test in selection). Isolation shows it is **not** the primary T1 gain mechanism.

### 4.3 What did *not* change

- Frozen SQLite instances / labels / topology
- 70/15/15 temporal split constants
- 30-minute feature lag
- Baseline `telem_only` protocol
- Validation-only threshold tuning
- AUPRC definition (score-based)

---

## 5. Leakage / protocol risk checklist

| Risk | Status | Evidence |
|---|---|---|
| Future telemetry in features | Cleared | `shift(1)` on expanding/rolling/EMA; prior-bin neighbors |
| Same-bin label leakage | Cleared | `feat_bin = t_start − 30min`; lag check true on 6/6 seeds |
| Train/val/test time overlap | Cleared | `split_temporal_ok` true on 6/6 seeds |
| Threshold tuned on test | Cleared | `tune_threshold(yva, …)` only; AP ignores threshold |
| Nested-CV protocol broken | N/A / cleared | No nested CV; single temporal holdout as in v2 |
| Frozen benchmark mutated | Cleared | SHA-256 match all six instances |
| Stacking peeks at test | Cleared | Selection on val (+ train consistency); test scored once |
| Gain from stacking only | Cleared | B−A ≈ +0.0008; features C−A ≈ +0.058 |

---

## 6. Bottom line

1. **Protocol identical to ECN-v2** except approved feature enrichment and stacking fusion.
2. **Improvement is real under that protocol**, not an artifact of leakage, nested-CV abuse, test threshold tuning, or benchmark edits.
3. **Traceable cause:** leakage-safe feature enrichment (~+0.058 mean AP under anchored fusion). Stacking contributes negligibly on legacy features and slightly reduces mean T1 AP relative to anchored fusion on the enriched set; published v3 still improves substantially over v2 (A→D ≈ +0.042).

Reproduce:

```bash
python evaluation/trace_t1_gain.py
# → results/v3_gated/t1_gain_traceability.json
```
