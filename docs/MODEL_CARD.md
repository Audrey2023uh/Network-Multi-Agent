# Model Card — Enterprise Cognitive Network (ECN)

## Model details
Multi-agent cognitive NetOps framework: Digital Twin, Perception, Anomaly, Prediction, RCA, Impact, Healing agents, with anchored score fusion for T1/T2.

## Intended use
Research evaluation on ECNetBench; not a production controller.

## Training data
Temporal train split of each ECNetBench instance (70% by time).

## Evaluation data
Held-out temporal test split (final 15%) across six seeds.

## Metrics
Primary: AUPRC. Secondary: ROC-AUC, F1/precision/recall at val-tuned threshold, Brier, calibration curves, macro-F1 for RCA/healing.

## Ethical considerations
Synthetic data only; no personal user identifiers. Do not deploy without operator oversight.

## Caveats
Does not uniformly dominate strong tabular baselines (logistic/RF) on T1 under multi-seed testing. See `reports/JOURNAL_FRAMING_OPTIMIZED.md`.
