# ECNetBench / ECN-v3 Interactive NOC Dashboard

Data-driven React dashboard for exploring verified ECNetBench artifacts and the final ECN-v3 architecture.

**This is a historical/replay visualization of repository results — not a live production NOC.**

Live site (after GitHub Pages is enabled):  
https://audrey2023uh.github.io/Network-Multi-Agent/

## Features

- Architecture explorer (Digital Twin → Healing) with D3 graph + module detail
- Animated pipeline view
- Cytoscape topology map from SQLite (devices/links/interfaces/incidents)
- Model comparison (AUPRC, ROC-AUC, CIs) from `results/`
- Plotly interactive figures (ROC, PR, calibration, CM, architecture deltas)
- Results + TreeSHAP explorers with data provenance badges
- Seed selector: `v1.1.0-INST`, `seed101`–`seed505`
- Dark / light toggle, responsive layout

## Data rule

Scientific numbers are **not** hard-coded in the frontend.  
`scripts/build_data.py` converts repository SQLite + `results/*.json` into `public/data/*.json`.  
See [DATA_PROVENANCE.md](./DATA_PROVENANCE.md).

## Quick start

```bash
# from repo root
python interactive_dashboard/scripts/build_data.py
python interactive_dashboard/scripts/validate_dashboard_data.py

cd interactive_dashboard
npm install
npm run dev
```

Open the Vite URL (typically http://localhost:5173/Network-Multi-Agent/).

## Build for GitHub Pages

```bash
cd interactive_dashboard
npm run build:pages
```

Output: `interactive_dashboard/dist/` with base path `/Network-Multi-Agent/`.

See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md).

## Repository layout

```
interactive_dashboard/
  scripts/build_data.py          # artifact → JSON adapter
  scripts/validate_dashboard_data.py
  public/data/                   # static JSON consumed by the app
  src/                           # React + TypeScript UI
  docs/DEPLOYMENT.md
  DATA_PROVENANCE.md
  screenshots/
  README.md
```

## Author

Audrey Rah · Department of Electrical and Computer Engineering · University of Houston
