import { useMemo } from "react";
import { Chart } from "../components/Chart";
import { PageIntro } from "../components/PageIntro";
import { ProvenanceBadge } from "../components/MetricCard";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

export function PracticalImpactPage() {
  const { aggregate } = useApp();
  const pi = (aggregate as any)?.practical_impact;
  const t1 = pi?.tasks?.T1_anomaly?.methods || {};
  const rows = Object.entries(t1).map(([method, block]: [string, any]) => ({
    method,
    ap: block?.ap?.mean,
    p10: block?.precision_at_10?.mean,
    p50: block?.precision_at_50?.mean,
    p100: block?.precision_at_100?.mean,
    fpr05: block?.fpr_at_recall_0_5?.mean,
    fpr08: block?.fpr_at_recall_0_8?.mean,
  }));
  rows.sort((a, b) => (b.ap ?? -1) - (a.ap ?? -1));

  const bar = useMemo(
    () => [
      {
        type: "bar" as const,
        name: "Precision@50",
        x: rows.map((r) => r.method.replace("__full", "")),
        y: rows.map((r) => r.p50),
        marker: { color: "#1F7A8C" },
      },
    ],
    [rows],
  );

  const vs = pi?.tasks?.T1_anomaly?.vs_baselines?.random_forest__full;

  return (
    <div className="space-y-4">
      <PageIntro
        title="Practical Impact"
        description="Workload proxies derived from test scores and labels only (Precision@k, FPR at fixed recall). Not MTTR or dollar ROI."
      />
      <ProvenanceBadge source="results/practical_impact.json" />
      {pi?.note && <div className="noc-card p-4 text-sm text-noc-muted">{pi.note}</div>}
      {vs && (
        <div className="noc-card p-4 text-sm">
          Relative FP reduction vs RF at recall≥0.5:{" "}
          {fmt(vs.relative_fp_reduction_at_recall_0_5?.mean)} · AUPRC Δ vs RF: {fmt(vs.auprc_delta_mean)}
        </div>
      )}
      <div className="noc-card p-4">
        <Chart title="T1 Precision@50 by method" data={bar} />
      </div>
      <div className="noc-card overflow-x-auto p-4">
        <table className="w-full text-left text-sm">
          <thead className="text-noc-muted">
            <tr>
              <th className="py-2">Method</th>
              <th>AUPRC</th>
              <th>P@10</th>
              <th>P@50</th>
              <th>P@100</th>
              <th>FPR@R0.5</th>
              <th>FPR@R0.8</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.method} className="border-t border-noc-border/60">
                <td className="py-2 font-mono text-xs">{r.method}</td>
                <td>{fmt(r.ap)}</td>
                <td>{fmt(r.p10)}</td>
                <td>{fmt(r.p50)}</td>
                <td>{fmt(r.p100)}</td>
                <td>{fmt(r.fpr05)}</td>
                <td>{fmt(r.fpr08)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
