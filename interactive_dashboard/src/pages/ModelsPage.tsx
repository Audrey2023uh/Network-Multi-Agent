import { useMemo, useState } from "react";
import { Chart } from "../components/Chart";
import { ProvenanceBadge } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { MetricTooltip } from "../components/MetricTooltip";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

export function ModelsPage() {
  const { aggregate } = useApp();
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"T1" | "T2" | "name">("T1");

  const rows = useMemo(() => {
    let m = [...(aggregate?.models || [])];
    if (q) m = m.filter((r) => r.label.toLowerCase().includes(q.toLowerCase()));
    m.sort((a, b) => {
      if (sort === "name") return a.label.localeCompare(b.label);
      const av = sort === "T1" ? a.T1_auprc?.mean ?? -1 : a.T2_auprc?.mean ?? -1;
      const bv = sort === "T1" ? b.T1_auprc?.mean ?? -1 : b.T2_auprc?.mean ?? -1;
      return (bv as number) - (av as number);
    });
    return m;
  }, [aggregate, q, sort]);

  const bar = useMemo(() => {
    const labels = rows.map((r) => r.label);
    const y = rows.map((r) => r.T1_auprc?.mean ?? null);
    const err = rows.map((r) => {
      const ci = r.T1_auprc?.ci95;
      const mean = r.T1_auprc?.mean;
      if (!ci || mean == null) return [0, 0];
      return [mean - ci[0], ci[1] - mean];
    });
    return [
      {
        type: "bar" as const,
        x: labels,
        y,
        error_y: {
          type: "data" as const,
          symmetric: false,
          array: err.map((e) => e[1]),
          arrayminus: err.map((e) => e[0]),
          color: "#8BA0B8",
        },
        marker: { color: "#1F7A8C" },
        hovertemplate: "%{x}<br>AUPRC=%{y:.4f}<extra></extra>",
      },
    ];
  }, [rows]);

  const best = rows[0];
  const final = rows.find((r) => r.id === "ecn_v3_final");
  const rf = rows.find((r) => r.id === "random_forest__full");
  let takeaway = "Load aggregate artifacts to compare model families.";
  if (final?.T1_auprc?.mean != null && rf?.T1_auprc?.mean != null) {
    const d = final.T1_auprc.mean - rf.T1_auprc.mean;
    takeaway = `Final ECN-v3 (${fmt(final.T1_auprc.mean)} AUPRC) vs RF telem baseline (${fmt(rf.T1_auprc.mean)}): Δ=${fmt(d)}. Table is sorted so the top row is the strongest T1 AUPRC among currently filtered models (${best?.label || "—"}).`;
  }

  return (
    <div className="space-y-4">
      <PageIntro title="Models" description="Compare model families and performance metrics." />
      <div className="noc-card border-noc-accent/30 p-4 text-sm leading-relaxed text-noc-text/90">{takeaway}</div>
      <div className="noc-card flex flex-wrap items-center gap-3 p-4">
        <input
          className="rounded-lg border border-noc-border bg-noc-bg px-3 py-2 text-sm"
          placeholder="Filter models…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="rounded-lg border border-noc-border bg-noc-bg px-3 py-2 text-sm"
          value={sort}
          onChange={(e) => setSort(e.target.value as any)}
        >
          <option value="T1">Sort by T1 AUPRC</option>
          <option value="T2">Sort by T2 AUPRC</option>
          <option value="name">Sort by name</option>
        </select>
        <ProvenanceBadge source="results/manuscript_ready_numbers.json + results/aggregate_v3.json" />
      </div>

      <Chart
        title="T1 AUPRC comparison (with CI when available)"
        data={bar as any}
        source="aggregate.json ← manuscript_ready + aggregate_v3"
      />

      <div className="noc-card overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-noc-border text-xs uppercase text-noc-muted">
            <tr>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">
                T1 AUPRC <MetricTooltip term="AUPRC" />
              </th>
              <th className="px-4 py-3">
                T1 ROC-AUC <MetricTooltip term="ROC-AUC" />
              </th>
              <th className="px-4 py-3">
                T2 AUPRC <MetricTooltip term="AUPRC" />
              </th>
              <th className="px-4 py-3">Source</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-noc-border/50 hover:bg-white/5">
                <td className="px-4 py-3 font-medium">{r.label}</td>
                <td className="px-4 py-3 font-mono">{fmt(r.T1_auprc?.mean ?? null)}</td>
                <td className="px-4 py-3 font-mono">{fmt(r.T1_roc_auc?.mean ?? null)}</td>
                <td className="px-4 py-3 font-mono">{fmt(r.T2_auprc?.mean ?? null)}</td>
                <td className="px-4 py-3 text-xs text-noc-muted">{r.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
