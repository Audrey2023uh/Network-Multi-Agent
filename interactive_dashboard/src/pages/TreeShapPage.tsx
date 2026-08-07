import { useMemo } from "react";
import { Chart } from "../components/Chart";
import { ProvenanceBadge } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { MetricTooltip } from "../components/MetricTooltip";
import { useApp } from "../lib/store";

export function TreeShapPage() {
  const { metrics, aggregate } = useApp();
  const shap = metrics?.shap || {};
  const global = shap.top_features || shap.feature_importances || metrics?.rca?.global_importance || [];
  const local = metrics?.rca?.local_explanations || shap.local_explanations || [];

  const globalTrace = useMemo(() => {
    const rows = Array.isArray(global)
      ? global
      : Object.entries(global || {}).map(([feature, importance]) => ({ feature, importance }));
    const sorted = [...rows]
      .map((r: any) => ({
        feature: r.feature || r.name || r.feature_name,
        importance: Number(r.importance ?? r.mean_abs_shap ?? r.value ?? 0),
      }))
      .filter((r) => r.feature)
      .sort((a, b) => b.importance - a.importance)
      .slice(0, 20);
    return [
      {
        type: "bar",
        orientation: "h",
        y: sorted.map((r) => r.feature).reverse(),
        x: sorted.map((r) => r.importance).reverse(),
        marker: { color: "#7C5CBF" },
        hovertemplate: "%{y}: %{x:.4f}<extra></extra>",
      },
    ];
  }, [global]);

  const localTrace = useMemo(() => {
    if (!Array.isArray(local) || !local.length) return [];
    const first = local[0];
    const feats = first?.features || first?.shap_values || first?.contributions || [];
    const rows = Array.isArray(feats)
      ? feats.map((f: any) =>
          typeof f === "object"
            ? { feature: f.feature || f.name, value: Number(f.shap ?? f.value ?? f.contribution ?? 0) }
            : null,
        )
      : Object.entries(feats).map(([feature, value]) => ({ feature, value: Number(value) }));
    const cleaned = rows.filter(Boolean).slice(0, 15) as { feature: string; value: number }[];
    return [
      {
        type: "bar",
        orientation: "h",
        y: cleaned.map((r) => r.feature).reverse(),
        x: cleaned.map((r) => r.value).reverse(),
        marker: { color: cleaned.map((r) => (r.value >= 0 ? "#3D8B6E" : "#C47B2B")).reverse() },
      },
    ];
  }, [local]);

  const hasAny = (Array.isArray(global) ? global.length : Object.keys(global || {}).length) > 0;
  const topName = Array.isArray(global) && global[0] ? global[0].feature || global[0].name : null;

  return (
    <div className="space-y-4">
      <PageIntro
        title="TreeSHAP"
        description="Investigate feature contribution and model-based root-cause evidence."
      />
      <div className="noc-card p-4 text-sm">
        <h2 className="flex items-center gap-1 font-semibold">
          TreeSHAP Explorer <MetricTooltip term="TreeSHAP" />
        </h2>
        <p className="mt-1 text-noc-muted">
          RCA explanations from verified evaluation artifacts. Fields appear only when present in the source JSON for
          the active seed. Higher bars indicate stronger average contribution (
          <MetricTooltip term="Feature importance" />
          ).
        </p>
        {topName ? (
          <p className="mt-2 text-xs text-noc-accent">
            Strongest listed feature for this seed artifact: <span className="font-mono">{String(topName)}</span>
          </p>
        ) : null}
        <ProvenanceBadge
          className="mt-2"
          source={shap.source_fields || metrics?.source || "results/per_seed/*.json"}
          field="tasks.T3_rca.*.shap_top_features"
        />
        <div className="mt-2 text-xs text-noc-muted">
          Architecture note: RCA uses RF + TreeSHAP ({String(aggregate?.architecture_selection?.rca || "rf+shap")})
        </div>
      </div>

      {hasAny ? (
        <Chart
          title="Global feature importance (top 20)"
          data={globalTrace as any}
          source={metrics?.source}
          layout={{ margin: { l: 160 } }}
        />
      ) : (
        <div className="noc-card p-4 text-sm text-noc-muted">
          No TreeSHAP/global importance block found in metrics for seed{" "}
          <span className="font-mono">{metrics?.seed}</span>.
        </div>
      )}

      {localTrace.length ? (
        <Chart
          title="Local explanation (first available sample)"
          data={localTrace as any}
          source={metrics?.source}
          layout={{ margin: { l: 160 } }}
        />
      ) : (
        <div className="noc-card p-4 text-sm text-noc-muted">
          No local TreeSHAP explanations in this seed artifact (global top_features still shown when available).
        </div>
      )}
    </div>
  );
}
