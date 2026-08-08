import { useMemo } from "react";
import { Chart } from "../components/Chart";
import { PageIntro } from "../components/PageIntro";
import { ProvenanceBadge } from "../components/MetricCard";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

export function SensitivityPage() {
  const { aggregate } = useApp();
  const s = (aggregate as any)?.sensitivity_analysis;
  const miss = s?.missing_telemetry || {};
  const abl = s?.feature_ablations_T1 || {};

  const ablBar = useMemo(() => {
    const keys = Object.keys(abl);
    return [
      {
        type: "bar" as const,
        x: keys,
        y: keys.map((k) => abl[k]?.mean ?? null),
        marker: { color: "#4A90A4" },
      },
    ];
  }, [abl]);

  const cats = ((aggregate as any)?.scenario_coverage?.category_totals_across_seeds || []).slice(0, 14);

  return (
    <div className="space-y-4">
      <PageIntro
        title="Sensitivity Analysis"
        description="Missing-telemetry robustness, feature ablations, and descriptive class imbalance on frozen seeds. Fabric-size sweeps are not measured."
      />
      <ProvenanceBadge source="results/sensitivity_analysis.json + results/scenario_coverage.json" />
      {s?.note && <div className="noc-card p-4 text-sm text-noc-muted">{s.note}</div>}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="noc-card p-4">
          <div className="text-xs text-noc-muted">Clean T1 AP</div>
          <div className="text-xl font-semibold">{fmt(miss.clean_proposed_ap?.mean)}</div>
        </div>
        <div className="noc-card p-4">
          <div className="text-xs text-noc-muted">Missing 10% AP</div>
          <div className="text-xl font-semibold">{fmt(miss.missing_10_ap?.mean)}</div>
          <div className="text-xs text-noc-muted">Δ={fmt(miss.drop_missing_10)}</div>
        </div>
        <div className="noc-card p-4">
          <div className="text-xs text-noc-muted">Missing 30% AP</div>
          <div className="text-xl font-semibold">{fmt(miss.missing_30_ap?.mean)}</div>
          <div className="text-xs text-noc-muted">Δ={fmt(miss.drop_missing_30)}</div>
        </div>
      </div>
      <div className="noc-card p-4">
        <Chart title="T1 feature ablations (proposed AUPRC)" data={ablBar} />
      </div>
      <div className="noc-card p-4 text-sm">
        T1 positive prior (mean): {fmt(s?.class_imbalance_T1_prior?.mean)}
      </div>
      <div className="noc-card overflow-x-auto p-4">
        <h3 className="mb-2 text-sm font-semibold">Scenario coverage (existing categories)</h3>
        <table className="w-full text-left text-sm">
          <thead className="text-noc-muted">
            <tr>
              <th className="py-2">Category</th>
              <th>Count (all seeds)</th>
            </tr>
          </thead>
          <tbody>
            {cats.map((c: any) => (
              <tr key={c.category} className="border-t border-noc-border/60">
                <td className="py-2">{c.category}</td>
                <td>{c.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
