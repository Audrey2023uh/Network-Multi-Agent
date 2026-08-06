# Final Publication-Readiness Verdict

**Publication-ready: True**

FULLY PUBLICATION-READY — ECNetBench generator is robust across independent seeds (101/202/303/404/505), with consistent topology, protocol dynamics, incident coverage, causal consistency, controlled leakage, and non-trivial temporal-holdout baselines. Suitable for submission to IEEE TNSM, Computer Networks, or IEEE Network as a synthetic enterprise cognitive-networking benchmark, provided papers disclose synthetic generation, seed set, and leakage-safe evaluation protocols.

**Disclosure notes for papers:**
- Seed 404 was exported CSV+SQLite only (parquet skipped after a disk-full event); analytics use SQLite.
- Seed 202 had zero alert false-negatives by chance; treat alert FN rate as stochastic, not a structural invariant.
- Rare-event Average Precision varies across seeds (report mean ± 95% CI).

## Evidence package

- Frozen reference: `instances/v1` (v1.1.0-INST) — not modified
- Seed instances: `instances/v1.1-seed{101,202,303,404,505}`
- Per-seed audits: `seed_robustness/per_seed/`
- This report: `seed_robustness/reports/`
