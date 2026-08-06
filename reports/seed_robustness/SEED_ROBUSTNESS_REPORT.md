# ECNetBench Seed Robustness Report

Generated: 2026-08-06T18:01:33.647789+00:00

**Seeds:** [101, 202, 303, 404, 505]

**Frozen instance preserved:** `C:\Users\audre\OneDrive\Network_Journal\Data\09_artifacts\instances\v1`

## Verdict

**Generator robust across seeds:** `True`

**Publication-ready:** `True`

FULLY PUBLICATION-READY — ECNetBench generator is robust across independent seeds (101/202/303/404/505), with consistent topology, protocol dynamics, incident coverage, causal consistency, controlled leakage, and non-trivial temporal-holdout baselines. Suitable for submission to IEEE TNSM, Computer Networks, or IEEE Network as a synthetic enterprise cognitive-networking benchmark, provided papers disclose synthetic generation, seed set, and leakage-safe evaluation protocols.

## Confidence intervals (95%) across seeds

| Metric | Mean | Std | 95% CI | Min | Max | CV |
|---|---:|---:|---|---:|---:|---:|
| n_devices | 19 | 0 | [19, 19] | 19 | 19 | 0 |
| n_interfaces | 168 | 0 | [168, 168] | 168 | 168 | 0 |
| n_links | 31 | 0 | [31, 31] | 31 | 31 | 0 |
| n_incidents | 37.6 | 2.074 | [35.03, 40.17] | 36 | 41 | 0.05515 |
| cpu_mean | 15.39 | 0.009731 | [15.38, 15.4] | 15.38 | 15.41 | 0.0006322 |
| cpu_std | 5.484 | 0.008129 | [5.474, 5.494] | 5.476 | 5.494 | 0.001482 |
| cpu_biz_night_ratio | 1.426 | 0.001647 | [1.424, 1.428] | 1.423 | 1.427 | 0.001155 |
| cpu_acf_1d_mean | 0.6433 | 0.06292 | [0.5651, 0.7214] | 0.5473 | 0.7133 | 0.09782 |
| flow_skew | 18.77 | 11.1 | [4.985, 32.55] | 10.12 | 35.81 | 0.5915 |
| temp_unique_ratio | 0.1024 | 0.0001305 | [0.1022, 0.1025] | 0.1022 | 0.1025 | 0.001275 |
| anomaly_prior | 0.01004 | 0.0008176 | [0.009026, 0.01106] | 0.009306 | 0.01134 | 0.08142 |
| svi_ipv4_frac | 1 | 0 | [1, 1] | 1 | 1 | 0 |
| mac_frac | 1 | 0 | [1, 1] | 1 | 1 | 0 |
| stp_blocking_or_alternate | 6 | 0 | [6, 6] | 6 | 6 | 0 |
| n_alerts | 65.4 | 5.32 | [58.79, 72.01] | 60 | 73 | 0.08134 |
| n_syslog | 267.2 | 14.32 | [249.4, 285] | 256 | 290 | 0.05361 |

## Baseline / score CIs

- **logistic_ap**: mean=0.06805845558036491, CI95=[0.01737869621765499, 0.11873821494307484], min=0.01767270736770408, max=0.12857410107008585
- **logistic_roc_auc**: mean=0.751815821469474, CI95=[0.6327825332614406, 0.8708491096775074], min=0.6614116094986807, max=0.9021567596002105
- **rf_ap**: mean=0.04662615233019293, CI95=[0.014892937102834125, 0.07835936755755174], min=0.019227186119448174, max=0.07920200715672987
- **ipri**: mean=89.6, CI95=[88.91991261934174, 90.28008738065824], min=89.0, max=90.0
- **realism_score**: mean=100.0, CI95=[100.0, 100.0], min=100.0, max=100.0

## Robustness criteria

- [PASS] `topology_invariant_across_seeds` = `True`
- [PASS] `incident_category_jaccard` = `1.0`
- [PASS] `incident_category_set_stable` = `True`
- [PASS] `protocol_behaviors_present_all_seeds` = `True`
- [PASS] `cpu_biz_night_ratio_cv_lt_0.25` = `True`
- [PASS] `anomaly_prior_cv_lt_0.5` = `True`
- [PASS] `logistic_ap_ci_above_prior` = `True`
- [PASS] `logistic_not_perfect_auc` = `True`
- [PASS] `realism_score_mean_ge_90` = `True`
- [PASS] `realism_score_min_ge_85` = `True`
- [PASS] `causal_pass_all_seeds` = `True`
- [PASS] `structural_causal_ok` = `True`
- [PASS] `stats_pass_all_seeds` = `True`
- [PASS] `leakage_controlled_all_seeds` = `True`
- [PASS] `n_seeds` = `5`

## Per-seed realism scores

- seed 101: realism=100, issues=0
- seed 202: realism=100, issues=1
- seed 303: realism=100, issues=0
- seed 404: realism=100, issues=0
- seed 505: realism=100, issues=0

## Per-seed publication summaries

- seed instance `C:\Users\audre\OneDrive\Network_Journal\Data\09_artifacts\instances\v1.1-seed101`: IPRI=90.0, logistic AP=0.12857410107008585, causal=1.0, leak_fail=1
- seed instance `C:\Users\audre\OneDrive\Network_Journal\Data\09_artifacts\instances\v1.1-seed202`: IPRI=89.0, logistic AP=0.04780849842068624, causal=0.9, leak_fail=1
- seed instance `C:\Users\audre\OneDrive\Network_Journal\Data\09_artifacts\instances\v1.1-seed303`: IPRI=89.0, logistic AP=0.01767270736770408, causal=1.0, leak_fail=1
- seed instance `C:\Users\audre\OneDrive\Network_Journal\Data\09_artifacts\instances\v1.1-seed404`: IPRI=90.0, logistic AP=0.07402631396201546, causal=1.0, leak_fail=1
- seed instance `C:\Users\audre\OneDrive\Network_Journal\Data\09_artifacts\instances\v1.1-seed505`: IPRI=90.0, logistic AP=0.0722106570813329, causal=1.0, leak_fail=1

## Interpretation for journals

Cross-seed consistency indicates the generator encodes structural/causal mechanisms rather than a single lucky draw. Residual metric variance (especially rare-event AP) is expected; report mean±CI in papers. Always evaluate with temporal manifests and leakage-safe feature exclusions.
