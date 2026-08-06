# Independent Publication Readiness Index (IPRI)

**Score: 88.1/100**

**Claim: CONDITIONAL — credible under temporal holdout and leakage protocol, but NOT fully publication-ready until alternate generation seeds are produced and compared**

Prior REALISM_AUDIT scored generative fidelity (up to 100/100). IPRI scores benchmark scientific validity (holdout, leakage, baselines, seed). A high realism score does not imply IPRI publication readiness.

## Dimensions

| Dimension | Points |
|---|---:|
| statistical_fidelity | 10.0 |
| causal_consistency | 10.0 |
| leakage_resistance | 12.0 |
| split_hygiene | 10.0 |
| prediction_difficulty | 10.0 |
| baseline_credibility | 8.0 |
| temporal_holdout | 9.0 |
| cross_topology | 5.0 |
| ablation_coherence | 5.0 |
| seed_reproducibility | 5.5 |
| external_comparability | 4.0 |
| engineer_checklist | 4.0 |

## Gates

- [PASS] `no_critical_leakage_failures`
- [PASS] `temporal_holdout_evaluated`
- [PASS] `simple_model_not_perfect`
- [PASS] `checksums_present`
- [FAIL] `multi_seed_generation_verified`

## Interpretation

Publication readiness is **not** granted solely from generative realism. IPRI requires temporal holdout credibility, leakage-safe protocols, non-trivial baselines, and multi-seed generation verification. The frozen v1.1.0-INST instance fails the multi-seed gate by design of this validation scope.
