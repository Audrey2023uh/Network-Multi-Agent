# TabNet + True GraphSAGE Evaluation Report

**Artifacts:** `results/aggregate_v3.json`, `results/manuscript_ready_numbers.json` → `extensions_v5_deep_baselines`  
**Protocol:** Frozen six seeds; no SQLite modifications.

## Measured T1 AUPRC (mean, n=6)

| Method | AUPRC | Notes |
|--------|------:|-------|
| ECN-v3 final (manuscript) | **0.11522** | Authoritative; not overwritten |
| Random Forest | 0.07584 | Best classical telem baseline |
| TabNet | **0.04924** | pytorch-tabnet; telem_only |
| GNN proxy (LightGBM) | 0.03352 | Historical; not message-passing |
| GraphSAGE (true) | **0.01525** | Pure PyTorch mean-agg on twin graph |

## Measured T2 AUPRC (mean)

| Method | AUPRC |
|--------|------:|
| Telem logistic (recommended) | 0.03804 |
| TabNet | 0.01102 |
| GraphSAGE (true) | 0.00622 |

## Implementation

- `framework/ecn/deep_baselines.py` — TabNet + GraphSAGE
- Eval keys: `tabnet__full`, `graphsage__full`, `gnn_graphsage_proxy__full`
- Deps: `pytorch-tabnet`, `torch` in `requirements.txt`
- **Not implemented:** TabTransformer; GAT/GIN via torch_geometric; live streaming GNN

## Honesty

Deep baselines are reported for completeness. They do **not** replace ECN-v3 (T1) or telem logistic (T2).
