import { Link } from "react-router-dom";
import { PageIntro } from "../components/PageIntro";
import { ReplayBanner } from "../components/ReplayBanner";
import { useApp } from "../lib/store";

const STEPS = [
  {
    n: 1,
    title: "Select Seed / Scenario",
    body: "Use the seed selector (upper right) to choose an ECNetBench instance (e.g. seed101).",
    to: null as string | null,
  },
  {
    n: 2,
    title: "Open Benchmark",
    body: "Inspect topology, incidents, and telemetry replay for the selected seed.",
    to: "/benchmark",
  },
  {
    n: 3,
    title: "Identify the affected or suspicious device",
    body: "Prefer devices linked to verified failure_incident records (listed on Benchmark).",
    to: "/benchmark",
  },
  {
    n: 4,
    title: "Click the device in the topology",
    body: "Select a node on the Cytoscape map to load verified inventory fields in the Inspector.",
    to: "/benchmark",
  },
  {
    n: 5,
    title: "Review the Inspector information",
    body: "Read Technician Assessment + raw fields (hostname, mgmt IP, role, interfaces, incidents).",
    to: "/benchmark",
  },
  {
    n: 6,
    title: "View anomaly / model evidence",
    body: "Open Models or Results for seed overlays and manuscript-backed performance metrics.",
    to: "/models",
  },
  {
    n: 7,
    title: "Open TreeSHAP for root-cause evidence",
    body: "Inspect feature importance / RCA attributions when present in per-seed artifacts.",
    to: "/shap",
  },
  {
    n: 8,
    title: "Review the recommended technician action",
    body: "Use only actions supported by artifact fields (incident category/severity). Never treat replay as live alerts.",
    to: "/benchmark",
  },
  {
    n: 9,
    title: "Verify in Results / Reproducibility",
    body: "Confirm metric provenance and reproduction commands before citing any number.",
    to: "/repro",
  },
];

export function RunbookPage() {
  const { seed, topology } = useApp();

  return (
    <div className="space-y-4">
      <PageIntro
        title="Technician Guide / Runbook"
        description="Operational workflow for network and NOC technicians exploring historical ECNetBench replay — not live production monitoring."
      />
      <ReplayBanner />

      <div className="noc-card border-noc-accent/40 p-5">
        <div className="text-xs uppercase tracking-wide text-noc-accent">Start here</div>
        <h2 className="mt-1 text-xl font-semibold">NOC Technician Workflow</h2>
        <p className="mt-2 text-sm text-noc-muted">
          Select scenario → Find affected device → Inspect evidence → Identify likely cause → Review recommended action
        </p>
        <p className="mt-2 text-sm">
          Active seed: <span className="font-mono text-noc-accent">{seed}</span>
          {topology?.available ? (
            <span className="text-noc-muted">
              {" "}
              · {topology.n_devices} devices · {topology.n_links} links · {topology.n_incidents} labeled incidents
            </span>
          ) : null}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link className="rounded-lg bg-noc-accent px-4 py-2 text-sm font-medium text-white" to="/benchmark">
            Open Benchmark
          </Link>
          <Link className="rounded-lg border border-noc-border px-4 py-2 text-sm" to="/shap">
            Open TreeSHAP
          </Link>
          <Link className="rounded-lg border border-noc-border px-4 py-2 text-sm" to="/results">
            Open Results
          </Link>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {STEPS.map((s) => {
          const card = (
            <div className="h-full rounded-xl border border-noc-border bg-noc-bg/50 p-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-noc-accent/20 text-sm font-bold text-noc-accent">
                {s.n}
              </div>
              <div className="mt-3 text-sm font-semibold">{s.title}</div>
              <p className="mt-2 text-xs leading-relaxed text-noc-muted">{s.body}</p>
            </div>
          );
          return s.to ? (
            <Link key={s.n} to={s.to} className="block hover:opacity-95">
              {card}
            </Link>
          ) : (
            <div key={s.n}>{card}</div>
          );
        })}
      </div>

      <div className="noc-card p-5 text-sm">
        <h3 className="font-semibold">What this runbook will not do</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-noc-muted">
          <li>It does not connect to a live network or page on-call engineers.</li>
          <li>It does not invent incidents, root causes, or healing actions missing from artifacts.</li>
          <li>Seed-level model/SHAP metrics are benchmark evidence, not per-packet live scores unless a device field exists.</li>
        </ul>
        <div className="mt-4 text-xs text-noc-muted">
          Designed and developed by Audrey Rah · Department of Electrical and Computer Engineering · University of
          Houston
        </div>
      </div>
    </div>
  );
}
