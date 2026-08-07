import { MetricCard, ProvenanceBadge } from "../components/MetricCard";
import { Chart } from "../components/Chart";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";
import { useMemo } from "react";

export function ResultsPage() {
  const { aggregate, metrics } = useApp();
  const m = aggregate?.manuscript_ready;
  if (!m) return <div className="noc-card p-6">Aggregate metrics not loaded.</div>;

  const t1 = m.T1_final_proposed;
  const t2 = m.T2_recommended;
  const seedT1 = metrics?.T1?.ecn_proposed__full;

  const cost = useMemo(() => {
    const rt = aggregate?.runtime || {};
    const rows = Object.entries(rt)
      .filter(([k, v]) => k !== "source" && typeof v === "number")
      .map(([k, v]) => ({ name: k, sec: v as number }));
    if (metrics?.computational && typeof metrics.computational === "object") {
      for (const [k, v] of Object.entries(metrics.computational)) {
        if (typeof v === "number") rows.push({ name: `${metrics.seed}:${k}`, sec: v });
      }
    }
    if (!rows.length) return [];
    return [
      {
        type: "bar",
        x: rows.map((r) => r.name),
        y: rows.map((r) => r.sec),
        marker: { color: "#4A90A4" },
        hovertemplate: "%{x}: %{y:.3f}s<extra></extra>",
      },
    ];
  }, [aggregate, metrics]);

  const paired = m.T1_paired_anchored_vs_stack;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <ProvenanceBadge source="results/manuscript_ready_numbers.json" field="T1_final_proposed / T2_recommended" />
        <span className="noc-chip">Seed view overlays per-seed curves when available</span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Final T1 AUPRC"
          value={fmt(t1?.auprc_mean)}
          source="results/manuscript_ready_numbers.json"
          field="T1_final_proposed.auprc_mean"
          accent
        />
        <MetricCard
          label="Final T1 ROC-AUC"
          value={fmt(t1?.roc_auc_mean)}
          source="results/manuscript_ready_numbers.json"
          field="T1_final_proposed.roc_auc_mean"
        />
        <MetricCard
          label="T2 AUPRC (telem logistic)"
          value={fmt(t2?.auprc_mean)}
          source={t2?.source || "results/aggregate_v3.json"}
          field="T2_failure.logistic__full.ap.mean"
        />
        <MetricCard
          label="Twin gain (AP)"
          value={fmt(t1?.twin_gain_ap_mean)}
          source="results/manuscript_ready_numbers.json"
          field="T1_final_proposed.twin_gain_ap_mean"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="noc-card p-5 text-sm">
          <h3 className="font-semibold">Statistical / selection summary</h3>
          <dl className="mt-3 space-y-2 font-mono text-xs">
            <div className="flex justify-between gap-4">
              <dt className="text-noc-muted">v2 legacy AUPRC</dt>
              <dd>{fmt(m.T1_vs_v2?.v2_anchored_legacy_auprc_mean)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-noc-muted">RF telem AUPRC</dt>
              <dd>{fmt(m.T1_baselines?.random_forest_telem_only_auprc_mean)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-noc-muted">Stack ablation AUPRC</dt>
              <dd>{fmt(m.T1_stacking_ablation?.auprc_mean)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-noc-muted">Wilcoxon p (AP, anchored vs stack)</dt>
              <dd>{fmt(paired?.wilcoxon_pvalue_ap, 3)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-noc-muted">ECE / Brier (final T1)</dt>
              <dd>
                {fmt(t1?.ece_mean)} / {fmt(t1?.brier_mean)}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-noc-muted">Selected architecture</dt>
              <dd className="text-right text-noc-accent">{String(aggregate?.architecture_selection?.selected || "anchored")}</dd>
            </div>
          </dl>
          <ProvenanceBadge
            className="mt-3"
            source="results/manuscript_ready_numbers.json + results/final_architecture.json"
          />
        </div>

        <div className="noc-card p-5 text-sm">
          <h3 className="font-semibold">Active seed overlay ({metrics?.seed})</h3>
          {seedT1 ? (
            <dl className="mt-3 space-y-2 font-mono text-xs">
              <div className="flex justify-between">
                <dt className="text-noc-muted">Seed T1 AUPRC (ap)</dt>
                <dd>{fmt(seedT1.ap ?? seedT1.auprc ?? seedT1.average_precision)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-noc-muted">Seed T1 ROC-AUC</dt>
                <dd>{fmt(seedT1.roc_auc)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-noc-muted">Seed Brier</dt>
                <dd>{fmt(seedT1.brier)}</dd>
              </div>
            </dl>
          ) : (
            <p className="mt-2 text-noc-muted">No per-seed metrics JSON for this instance (e.g. INST-only topology).</p>
          )}
          <ProvenanceBadge className="mt-3" source={metrics?.source || "n/a"} field="tasks.T1_anomaly.ecn_proposed__full" />
        </div>
      </div>

      {cost.length ? (
        <Chart title="Computational cost / runtime (verified fields only)" data={cost as any} source="manuscript_ready + per-seed computational" />
      ) : (
        <div className="noc-card p-4 text-sm text-noc-muted">No runtime cost fields available in loaded artifacts.</div>
      )}
    </div>
  );
}
