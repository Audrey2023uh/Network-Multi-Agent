import { useMemo } from "react";
import { Chart } from "../components/Chart";
import { PageIntro } from "../components/PageIntro";
import { ProvenanceBadge } from "../components/MetricCard";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

export function ScalabilityPage() {
  const { aggregate } = useApp();
  const sc = (aggregate as any)?.scalability_measured;
  const methods = sc?.methods_T1_T2_pooled || {};
  const rows = Object.entries(methods).map(([id, block]: [string, any]) => ({
    id,
    train: block?.train_time_s?.mean,
    wall: block?.wall_time_s?.mean,
    rss: block?.peak_rss_delta_mb?.mean,
  }));
  rows.sort((a, b) => (b.train ?? -1) - (a.train ?? -1));

  const bar = useMemo(
    () => [
      {
        type: "bar" as const,
        x: rows.map((r) => r.id.replace("__full", "")),
        y: rows.map((r) => r.train),
        marker: { color: "#C27C38" },
        hovertemplate: "%{x}<br>train=%{y:.3f}s<extra></extra>",
      },
    ],
    [rows],
  );

  return (
    <div className="space-y-4">
      <PageIntro
        title="Scalability (Measured)"
        description="Train/wall timing and approximate RSS deltas on frozen ~19-device instances. Fabric-size scalability was not measured."
      />
      <ProvenanceBadge source="results/scalability_measured.json" />
      {sc?.caption && <div className="noc-card p-4 text-sm text-noc-muted">{sc.caption}</div>}
      <div className="noc-card p-4 text-sm">
        Per-seed full-eval wall time: {fmt(sc?.per_seed_eval_wall_s?.mean)} s (mean)
      </div>
      <div className="noc-card p-4">
        <Chart title="Mean train_time_s (T1+T2 pooled)" data={bar} />
      </div>
      <div className="noc-card overflow-x-auto p-4">
        <table className="w-full text-left text-sm">
          <thead className="text-noc-muted">
            <tr>
              <th className="py-2">Method</th>
              <th>Train (s)</th>
              <th>Wall (s)</th>
              <th>RSS Δ (MB)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-noc-border/60">
                <td className="py-2 font-mono text-xs">{r.id}</td>
                <td>{fmt(r.train)}</td>
                <td>{fmt(r.wall)}</td>
                <td>{fmt(r.rss)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
