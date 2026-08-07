import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { MetricCard } from "../components/MetricCard";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

export function HomePage() {
  const { aggregate, topology } = useApp();
  const ms = aggregate?.manuscript_ready?.T1_final_proposed;
  const rf = aggregate?.manuscript_ready?.T1_baselines?.random_forest_telem_only_auprc_mean;

  return (
    <div className="space-y-8">
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
          <p className="mt-3 text-sm text-noc-muted">
            Audrey Rah · Department of Electrical and Computer Engineering · University of Houston
          </p>
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-noc-text/90">
            Data-driven exploration of the verified ECNetBench multi-seed benchmark and the final ECN-v3 architecture
            (leakage-safe features, anchored fusion, TreeSHAP RCA). All scientific numbers load from repository
            artifacts — this is a historical/replay visualization, not a live production feed.
          </p>
          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <a className="rounded-lg bg-noc-accent px-4 py-2 font-medium text-white" href="https://github.com/Audrey2023uh/Network-Multi-Agent">
              GitHub
            </a>
            <Link className="rounded-lg border border-noc-border px-4 py-2" to="/results">
              Results
            </Link>
            <Link className="rounded-lg border border-noc-border px-4 py-2" to="/repro">
              Reproducibility
            </Link>
            <a className="rounded-lg border border-noc-border px-4 py-2" href="https://github.com/Audrey2023uh/Network-Multi-Agent/tree/main/paper/overleaf">
              Paper / Overleaf
            </a>
            <Link className="rounded-lg border border-noc-border px-4 py-2" to="/docs">
              Documentation
            </Link>
          </div>
        </div>
      </motion.section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Final T1 AUPRC"
          value={fmt(ms?.auprc_mean)}
          sub="Authoritative final architecture"
          source="results/manuscript_ready_numbers.json"
        />
        <MetricCard
          label="T1 ROC-AUC"
          value={fmt(ms?.roc_auc_mean)}
          source="results/manuscript_ready_numbers.json"
        />
        <MetricCard
          label="RF telem_only AUPRC"
          value={fmt(rf)}
          source="results/manuscript_ready_numbers.json"
        />
        <MetricCard
          label="Topology (selected seed)"
          value={topology ? `${topology.n_devices} / ${topology.n_links}` : "—"}
          sub="devices / links from SQLite"
          source={topology?.source_db}
        />
      </div>
    </div>
  );
}
