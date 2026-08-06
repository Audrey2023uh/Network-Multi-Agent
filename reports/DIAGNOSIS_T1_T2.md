"""
Scientific diagnosis: why logistic > ECN on T1 and RF > ECN on T2
(pre-optimization evidence from six-seed frozen ECNetBench evaluation).

## T1 — logistic vs proposed
**Observation:** Mean AUPRC logistic 0.070 > proposed 0.058. Proposed wins seed101/v1; loses badly on seed202 (0.021 vs 0.076).

### Primary causes
1. **Fusion overfit to validation** — On seed202 proposed ≈ no_twin << logistic. If val-AP fusion correctly selected the telem logistic specialist alone, proposed must weakly dominate that specialist. It does not ⇒ fusion/meta selected a mixture/meta-learner that hurts test ranking.
2. **Miscalibrated agent scores under imbalance** — `class_weight='balanced'` at ~1% prior pushes probability mass high; convex fusion of poorly calibrated scores is not ranking-optimal.
3. **Within-batch rank-normalization of IsolationForest** — val fusion weights see different score geometry than test.

### Secondary
- Extreme class imbalance → high AUPRC variance across seeds
- Benchmark: weak linear telem signal often dominates twin features

## T2 — RF vs proposed
**Observation:** Mean AUPRC RF 0.036 > proposed 0.015. Brier proposed 0.12–0.22 vs RF ~0.02.

### Primary causes
1. **Feature under-specification** — T2 lacked interface error deltas and temporal neighbor aggregates.
2. **Model design / calibration** — balanced fusion yields high Brier; RF ranks better under imbalance.
3. **Class imbalance** — prior ~0.5%.

## Ruled out as sole cause
- Thresholding (AUPRC is threshold-free)
- Hyperparameter search alone

## Justified optimizations
1. Conservative fusion with nesting (best singleton unless mixture improves val AUPRC by margin)
2. Per-agent validation calibration before fusion
3. `scale_pos_weight` for trees + calibration
4. Leakage-safe temporal deltas, device z-scores, interface counters, neighbor aggregates on T1/T2
5. RF specialist in fusion for nonlinear interactions
6. Val-tuned threshold for F1 (secondary metric only)
