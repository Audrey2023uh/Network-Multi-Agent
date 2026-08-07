import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { MetricCard } from "../components/MetricCard";
import { ReplayBanner } from "../components/ReplayBanner";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

const HOW_TO = [
  {
    step: "1",
    title: "Select a seed",
    body: "Choose an ECNetBench seed from the selector in the upper-right corner (v1.1.0-INST or seed101–505).",
    to: null as string | null,
  },
  {
    step: "2",
    title: "Inspect topology",
    body: "Open Architecture or Benchmark to inspect devices, links, and the scenario for the selected seed.",
    to: "/benchmark",
  },
  {
    step: "3",
    title: "Review model outputs",
    body: "Use Models and Results to compare ROC-AUC, AUPRC, baselines, and the final ECN-v3 architecture.",
    to: "/results",
  },
  {
    step: "4",
    title: "Investigate decisions",
    body: "Open TreeSHAP to inspect feature importance and root-cause evidence behind model outputs.",
    to: "/shap",
  },
  {
    step: "5",
    title: "Verify provenance",
    body: "Use Reproducibility and Documentation to confirm sources and reproduction steps.",
    to: "/repro",
  },
];

const PIPELINE = [
  "ECNetBench / ECN-v3 experiments",
  "Model / agent execution",
  "SQLite + result artifacts",
  "build_data.py",
  "JSON datasets (public/data)",
  "Interactive dashboard",
];

export function HomePage() {
  const { aggregate, topology, seed } = useApp();
  const ms = aggregate?.manuscript_ready?.T1_final_proposed;
  const rf = aggregate?.manuscript_ready?.T1_baselines?.random_forest_telem_only_auprc_mean;
  const v2 = aggregate?.manuscript_ready?.T1_vs_v2?.v2_anchored_legacy_auprc_mean;
  const stack = aggregate?.manuscript_ready?.T1_stacking_ablation?.auprc_mean;
  const finalAp = ms?.auprc_mean as number | undefined;
  const rfAp = rf as number | undefined;

  let comparison = "Comparison unavailable until aggregate artifacts load.";
  if (finalAp != null && rfAp != null) {
    const delta = finalAp - rfAp;
    const better = delta >= 0 ? "higher" : "lower";
    comparison = `Final ECN-v3 T1 AUPRC (${fmt(finalAp)}) is ${better} than the telemetry-only Random Forest baseline (${fmt(rfAp)}; Δ=${fmt(delta)}). Stacking ablation AUPRC is ${fmt(stack)} (negative result vs anchored). Legacy v2 anchored mean AUPRC is ${fmt(v2)}.`;
  }

  return (
    <div className="space-y-8">
      <ReplayBanner />

      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="noc-card relative overflow-hidden p-8"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(31,122,140,0.25),transparent_45%)]" />
        <div className="relative">
          <p className="text-xs uppercase tracking-[0.2em] text-noc-accent">Enterprise Cognitive Networking</p>
          <h1 className="mt-2 max-w-4xl text-3xl font-bold leading-tight md:text-4xl">
            ECNetBench / ECN-v3 Interactive NOC Dashboard
          </h1>
          <div className="mt-3 space-y-0.5 text-sm text-noc-text/90">
            <p className="font-medium">Designed and developed by Audrey Rah</p>
            <p className="text-noc-muted">Department of Electrical and Computer Engineering</p>
            <p className="text-noc-muted">University of Houston</p>
          </div>
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-noc-text/90">
            Guided exploration of the verified ECNetBench multi-seed benchmark and the final ECN-v3 architecture
            (leakage-safe features, anchored fusion, TreeSHAP RCA). Use this dashboard to understand{" "}
            <em>what the system does</em>, <em>which model performed better</em>, and <em>where every number came from</em>.
          </p>
          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <a
              className="rounded-lg bg-noc-accent px-4 py-2 font-medium text-white"
              href="https://github.com/Audrey2023uh/Network-Multi-Agent"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
            <Link className="rounded-lg border border-noc-border px-4 py-2" to="/benchmark">
              Start: Benchmark
            </Link>
            <Link className="rounded-lg border border-noc-border px-4 py-2" to="/results">
              Results
            </Link>
            <Link className="rounded-lg border border-noc-border px-4 py-2" to="/repro">
              Reproducibility
            </Link>
            <a
              className="rounded-lg border border-noc-border px-4 py-2"
              href="https://github.com/Audrey2023uh/Network-Multi-Agent/tree/main/paper/overleaf"
              target="_blank"
              rel="noreferrer"
            >
              Paper / Overleaf
            </a>
            <Link className="rounded-lg border border-noc-border px-4 py-2" to="/docs">
              Documentation
            </Link>
          </div>
        </div>
      </motion.section>

      <section className="noc-card p-6">
        <h2 className="text-xl font-semibold">How to Use This Dashboard</h2>
        <p className="mt-1 text-sm text-noc-muted">
          Follow these five steps. The seed selector (upper right) controls topology and per-seed overlays site-wide.
          Active seed: <span className="font-mono text-noc-accent">{seed}</span>
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-5">
          {HOW_TO.map((s, i) => {
            const inner = (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="h-full rounded-xl border border-noc-border bg-noc-bg/60 p-4"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-noc-accent/20 text-sm font-bold text-noc-accent">
                  {s.step}
                </div>
                <div className="mt-3 text-sm font-semibold">{s.title}</div>
                <p className="mt-2 text-xs leading-relaxed text-noc-muted">{s.body}</p>
              </motion.div>
            );
            return s.to ? (
              <Link key={s.step} to={s.to} className="block transition hover:opacity-95">
                {inner}
              </Link>
            ) : (
              <div key={s.step}>{inner}</div>
            );
          })}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="noc-card p-6">
          <h2 className="text-lg font-semibold">Technical User Quick Start</h2>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-noc-text/90">
            <li>Select a seed in the upper-right corner.</li>
            <li>
              Open <Link className="text-noc-accent2 underline" to="/benchmark">Benchmark</Link> to inspect the scenario.
            </li>
            <li>
              Open <Link className="text-noc-accent2 underline" to="/models">Models</Link> or{" "}
              <Link className="text-noc-accent2 underline" to="/results">Results</Link> to inspect detection performance.
            </li>
            <li>
              Open <Link className="text-noc-accent2 underline" to="/shap">TreeSHAP</Link> to investigate contributing
              features.
            </li>
            <li>
              Open <Link className="text-noc-accent2 underline" to="/repro">Reproducibility</Link> to verify the source of
              each displayed result.
            </li>
          </ol>
        </section>

        <section className="noc-card p-6">
          <h2 className="text-lg font-semibold">What happens behind the dashboard?</h2>
          <p className="mt-1 text-xs text-noc-muted">
            The UI reads verified repository artifacts. It does not invent or recompute scientific results in the
            browser.
          </p>
          <div className="mt-4 flex flex-col items-stretch gap-1">
            {PIPELINE.map((label, i) => (
              <div key={label} className="flex flex-col items-center">
                <div className="w-full rounded-lg border border-noc-border bg-noc-bg px-3 py-2 text-center text-xs font-medium">
                  {label}
                </div>
                {i < PIPELINE.length - 1 ? <div className="my-1 text-noc-accent">↓</div> : null}
              </div>
            ))}
          </div>
        </section>
      </div>

      <section>
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold">Key performance indicators</h2>
            <p className="text-sm text-noc-muted">
              Authoritative means from manuscript-ready artifacts. Use the info icons on each card for metric
              definitions (AUPRC, ROC-AUC, etc.).
            </p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Final T1 AUPRC"
            value={fmt(ms?.auprc_mean)}
            metricTerm="AUPRC"
            explanation="Precision–recall performance of the final T1 ECN-v3 model (enriched features + anchored fusion). Especially informative when the positive class is relatively rare."
            sub="Authoritative final architecture"
            source="results/manuscript_ready_numbers.json"
            field="T1_final_proposed.auprc_mean"
            accent
          />
          <MetricCard
            label="T1 ROC-AUC"
            value={fmt(ms?.roc_auc_mean)}
            metricTerm="ROC-AUC"
            explanation="Measures how well the final T1 model separates positive and negative cases across classification thresholds."
            source="results/manuscript_ready_numbers.json"
            field="T1_final_proposed.roc_auc_mean"
          />
          <MetricCard
            label="RF TELEM_ONLY AUPRC"
            value={fmt(rf)}
            metricTerm="AUPRC"
            explanation="Telemetry-only Random Forest baseline AUPRC. Use this to compare the final ECN-v3 architecture against a simpler model family."
            source="results/manuscript_ready_numbers.json"
            field="T1_baselines.random_forest_telem_only_auprc_mean"
          />
          <MetricCard
            label="Topology (selected seed)"
            value={topology ? `${topology.n_devices} / ${topology.n_links}` : "—"}
            explanation={`For seed ${seed}: device count / link count extracted from the verified benchmark topology (SQLite → JSON).`}
            sub="devices / links"
            source={topology?.source_db}
            field="n_devices / n_links"
          />
        </div>
      </section>

      <section className="noc-card border-noc-accent/30 p-5">
        <h2 className="text-lg font-semibold">Clear comparison (final vs baselines)</h2>
        <p className="mt-2 text-sm leading-relaxed text-noc-text/90">{comparison}</p>
        <p className="mt-2 text-xs text-noc-muted">
          Seed-specific overlays (ROC/PR/TreeSHAP) update when you change the seed selector; aggregate manuscript means
          stay fixed as the authoritative six-seed summary.
        </p>
      </section>
    </div>
  );
}
