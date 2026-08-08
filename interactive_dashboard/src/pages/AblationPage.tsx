import { useMemo } from "react";
import { Chart } from "../components/Chart";
import { PageIntro } from "../components/PageIntro";
import { ProvenanceBadge } from "../components/MetricCard";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

export function AblationPage() {
  const { aggregate } = useApp();
  const ablRows = (aggregate as any)?.tables?.ablation || [];
  const sens = (aggregate as any)?.sensitivity_analysis?.feature_ablations_T1 || {};
  const ext = (aggregate as any)?.extensions_v4;

  const bar = useMemo(() => {
    const keys = Object.keys(sens);
    return [
      {
        type: "bar" as const,
        x: keys,
        y: keys.map((k) => sens[k]?.mean ?? null),
        marker: { color: "#1F7A8C" },
      },
    ];
  }, [sens]);

  return (
    <div className="space-y-4">
      <PageIntro
        title="Expanded Ablation"
        description="Module/feature ablations for the proposed model. TreeSHAP is explanation-only on RCA and does not change T1 AUPRC."
      />
      <ProvenanceBadge source="results/aggregate_v3.json ablation + sensitivity_analysis.json" />
      {ext?.ablation_note_TreeSHAP && (
        <div className="noc-card border-noc-accent/40 p-4 text-sm">{ext.ablation_note_TreeSHAP}</div>
      )}
      <div className="noc-card p-4">
        <Chart title="T1 proposed AUPRC by ablation" data={bar} />
      </div>
      <div className="noc-card overflow-x-auto p-4">
        <table className="w-full text-left text-sm">
          <thead className="text-noc-muted">
            <tr>
              {Object.keys(ablRows[0] || { task: "", ablation: "", ap_mean: "" }).map((h) => (
                <th key={h} className="py-2 pr-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ablRows.map((r: any, i: number) => (
              <tr key={i} className="border-t border-noc-border/60">
                {Object.keys(ablRows[0] || {}).map((h) => (
                  <td key={h} className="py-2 pr-3 font-mono text-xs">
                    {typeof r[h] === "number" ? fmt(r[h]) : String(r[h] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
