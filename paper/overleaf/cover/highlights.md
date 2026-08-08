# ECNetBench / ECN-v3 manuscript highlights (authoritative)

1. Final T1 head = leakage-safe enriched features + **anchored** fusion (`ECNFusionModel`).
2. Authoritative T1 AUPRC mean = **0.1152** (bootstrap 95% CI [0.0679, 0.1680]) from `results/manuscript_ready_numbers.json` (exact float archived there).
3. Strongest classical telem baseline RF T1 AUPRC mean = **0.07583814878524626**.
4. Prior v2 configuration T1 AUPRC mean = **0.05771284608153401**.
5. Stacking on the same enriched features is a **negative ablation** (mean ≈ 0.0997).
6. Recommended T2 head = telem logistic (mean AUPRC **0.038043099063649714**).
7. Twin predictive gain under the final T1 head is near zero (≈ +0.00035); twin remains architectural / RCA context.
8. TabNet and true GraphSAGE are reported deep baselines; they do **not** replace the final heads.
9. Historical GNN proxy is LightGBM-based and is **not** a true message-passing GNN.
