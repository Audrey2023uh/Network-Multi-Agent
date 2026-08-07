import { ProvenanceBadge } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { useApp } from "../lib/store";

const COMMANDS = [
  {
    title: "Build dashboard data",
    cmd: "python interactive_dashboard/scripts/build_data.py",
    note: "Reads SQLite instances + results/*.json → public/data/",
  },
  {
    title: "Install & run locally",
    cmd: "cd interactive_dashboard && npm install && npm run dev",
    note: "Vite static app; no backend",
  },
  {
    title: "Build for GitHub Pages",
    cmd: "cd interactive_dashboard && npm run build:pages",
    note: "base path /Network-Multi-Agent/",
  },
  {
    title: "Full evaluation (repo root)",
    cmd: "python -m evaluation.run_full_evaluation",
    note: "Regenerates results artifacts used by the adapter",
  },
];

export function ReproPage() {
  const { index, aggregate } = useApp();

  return (
    <div className="space-y-4">
      <PageIntro
        title="Reproducibility"
        description="Inspect seeds, artifacts, configuration, and provenance needed to reproduce the benchmark."
      />
      <div className="noc-card p-5">
        <h2 className="text-xl font-semibold">Reproducibility Center</h2>
        <p className="mt-1 text-sm text-noc-muted">
          Static GitHub Pages deployment. All metrics and topology come from verified repository artifacts — not live
          production telemetry.
        </p>
        <ProvenanceBadge className="mt-3" source="interactive_dashboard/DATA_PROVENANCE.md" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="noc-card p-5">
          <h3 className="font-semibold">Frozen seeds / instances</h3>
          <ul className="mt-3 space-y-2 text-sm">
            {((index?.seeds || []) as Array<{ id: string; label?: string; source?: string }>).map((s) => (
              <li key={s.id} className="flex justify-between gap-2 border-b border-noc-border/40 py-2">
                <span className="font-mono text-xs">{s.id}</span>
                <span className="truncate text-xs text-noc-muted">{s.label || s.source || ""}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="noc-card p-5">
          <h3 className="font-semibold">Commands</h3>
          <div className="mt-3 space-y-3">
            {COMMANDS.map((c) => (
              <div key={c.title} className="rounded-lg border border-noc-border bg-noc-bg p-3">
                <div className="text-sm font-medium">{c.title}</div>
                <pre className="mt-2 overflow-x-auto text-xs text-noc-accent2">{c.cmd}</pre>
                <div className="mt-1 text-xs text-noc-muted">{c.note}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="noc-card p-5 text-sm">
        <h3 className="font-semibold">Traceability</h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-noc-muted">
          <li>Manuscript numbers: results/manuscript_ready_numbers.json</li>
          <li>Architecture decision: results/final_architecture.json</li>
          <li>Per-seed metrics: results/per_seed/*.json</li>
          <li>Frozen DBs: benchmark/instances/*.sqlite (+ INSTANCE_CHECKSUMS.json)</li>
          <li>Dashboard mapping: interactive_dashboard/DATA_PROVENANCE.md</li>
          <li>
            Selected T1: {String(aggregate?.architecture_selection?.selected || "anchored")} · Generated{" "}
            {index?.generated_at || "—"}
          </li>
        </ul>
        <div className="mt-4 flex flex-wrap gap-3 text-sm">
          <a
            className="text-noc-accent2 underline"
            href="https://github.com/Audrey2023uh/Network-Multi-Agent"
            target="_blank"
            rel="noreferrer"
          >
            GitHub repository
          </a>
          <a
            className="text-noc-accent2 underline"
            href="https://github.com/Audrey2023uh/Network-Multi-Agent/tree/main/paper/overleaf"
            target="_blank"
            rel="noreferrer"
          >
            Manuscript (Overleaf source)
          </a>
          <a
            className="text-noc-accent2 underline"
            href={`${import.meta.env.BASE_URL}data/index.json`}
            target="_blank"
            rel="noreferrer"
          >
            Download data index
          </a>
        </div>
      </div>
    </div>
  );
}
