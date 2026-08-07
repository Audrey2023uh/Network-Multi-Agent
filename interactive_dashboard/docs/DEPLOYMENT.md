# Deployment Guide — ECNetBench NOC Dashboard

Static site. No backend. Compatible with GitHub Pages.

## Prerequisites

- Python 3.10+ with project deps used by `build_data.py` (`pandas`, stdlib `sqlite3`)
- Node.js 18+ and npm

## 1. Materialize data

From the **repository root**:

```bash
python interactive_dashboard/scripts/build_data.py
python interactive_dashboard/scripts/validate_dashboard_data.py
```

This writes `interactive_dashboard/public/data/*.json` from:

- `benchmark/instances/*/ecnetbench_v1.sqlite`
- `results/manuscript_ready_numbers.json`
- `results/aggregate_v3.json`
- `results/per_seed/*.json`
- `results/final_architecture.json`
- related gated / table artifacts when present

## 2. Build

```bash
cd interactive_dashboard
npm install
npm run build:pages
```

`vite.config.ts` sets `base: "/Network-Multi-Agent/"` for the GitHub project site.

## 3. Publish options

### A. GitHub Actions (recommended)

Workflow: `.github/workflows/dashboard-pages.yml`

1. Push to `main`
2. Enable **Settings → Pages → Source: GitHub Actions**
3. The workflow builds and deploys `interactive_dashboard/dist`

### B. Manual `docs/` publish

```bash
cd interactive_dashboard
npm run build:pages
# copy dist contents to repo docs/ (or docs/dashboard/)
```

Then set Pages source to `/docs` on `main`. If using a subfolder, adjust `base` accordingly.

### C. Local preview of production build

```bash
cd interactive_dashboard
npm run build
npm run preview
```

## Validation checklist

- [ ] `validate_dashboard_data.py` exits 0
- [ ] Home metric cards match `results/manuscript_ready_numbers.json`
- [ ] Topology shows 19 devices / 31 links per seed
- [ ] Seed switch reloads `topology_*.json` / `metrics_*.json`
- [ ] Footer states historical/replay (not live)
- [ ] No scientific literals for final AUPRC in `src/`

## URL

https://audrey2023uh.github.io/Network-Multi-Agent/
