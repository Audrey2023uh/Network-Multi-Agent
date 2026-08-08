import { useMemo } from "react";
import { Chart } from "../components/Chart";
import { PageIntro } from "../components/PageIntro";
import { ProvenanceBadge } from "../components/MetricCard";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

export function XaiValidationPage() {
  const { aggregate } = useApp();
  const xai = (aggregate as any)?.xai_validation;
  const summary = xai?.summary || {};
  const freq = (summary.feature_frequency_top10 || []).slice(0, 12);
  const per = xai?.per_seed || [];

  const bar = useMemo(
    () => [
      {
        type: "bar" as const,
        x: freq.map((f: any) => f.feature),
        y: freq.map((f: any) => f.n_seeds),
        marker: { color: "#7A5C8A" },
      },
    ],
    [freq],
  );

  return (
    <div className="space-y-4">
      <PageIntro
        title="Explainability Validation"
        description="Cross-seed rank stability of RCA top features (Jaccard / Spearman). No human-subject understanding study."
      />
      <ProvenanceBadge source="results/xai_validation.json" />
      {xai?.note && <div className="noc-card p-4 text-sm text-noc-muted">{xai.note}</div>}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="noc-card p-4">
          <div className="text-xs text-noc-muted">Mean Jaccard top-10</div>
          <div className="text-xl font-semibold">{fmt(summary.mean_jaccard_top10)}</div>
        </div>
        <div className="noc-card p-4">
          <div className="text-xs text-noc-muted">Mean Spearman ρ</div>
          <div className="text-xl font-semibold">{fmt(summary.mean_spearman_rho)}</div>
        </div>
        <div className="noc-card p-4">
          <div className="text-xs text-noc-muted">Seeds with TreeSHAP</div>
          <div className="text-xl font-semibold">
            {xai?.seeds_with_shap ?? "—"} / {xai?.n_seeds ?? "—"}
          </div>
        </div>
      </div>
      <div className="noc-card p-4">
        <Chart title="Feature frequency in top-10 across seeds" data={bar} />
      </div>
      <div className="noc-card overflow-x-auto p-4">
        <table className="w-full text-left text-sm">
          <thead className="text-noc-muted">
            <tr>
              <th className="py-2">Seed</th>
              <th>Source</th>
              <th>Top features</th>
              <th>RCA macro-F1</th>
            </tr>
          </thead>
          <tbody>
            {per.map((r: any) => (
              <tr key={r.seed} className="border-t border-noc-border/60">
                <td className="py-2">{r.seed}</td>
                <td>{r.source}</td>
                <td className="font-mono text-xs">{(r.top10 || []).slice(0, 5).join(", ")}</td>
                <td>{fmt(r.macro_f1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="noc-card list-disc space-y-1 p-4 pl-8 text-sm text-noc-muted">
        {(xai?.limitations || []).map((l: string) => (
          <li key={l}>{l}</li>
        ))}
      </ul>
    </div>
  );
}
