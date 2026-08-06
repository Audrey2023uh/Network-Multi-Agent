# Ablation Report — ECNetBench v1.1.0-INST

| Feature group | AP | ROC-AUC | F1 | #feats |
|---|---:|---:|---:|---:|
| cpu_only | 0.1092 | 0.7255 | 0.0261 | 2 |
| mem_only | 0.0106 | 0.4460 | 0.0000 | 1 |
| interface_counters | 0.0170 | 0.7265 | 0.0148 | 3 |
| role_only | 0.0198 | 0.7919 | 0.0388 | 5 |
| cpu+iface | 0.0778 | 0.7227 | 0.0308 | 5 |
| full | 0.1097 | 0.8642 | 0.0477 | 12 |
| oracle_leak | 1.0000 | 1.0000 | 1.0000 | 14 |

## Ranking (by AP)

- `oracle_leak`: AP=1.0000
- `full`: AP=0.1097
- `cpu_only`: AP=0.1092
- `cpu+iface`: AP=0.0778
- `role_only`: AP=0.0198
- `interface_counters`: AP=0.0170
- `mem_only`: AP=0.0106

## Interpretation

- Oracle leak features dominate — confirms label proxies must stay excluded
- full AP=0.1097; cpu_only=0.1092; iface=0.0170
- CPU load features are primary drivers vs interface counters in this setup
