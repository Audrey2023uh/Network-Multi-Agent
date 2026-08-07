import { useMemo } from "react";
import { Chart } from "../components/Chart";
import { PageIntro } from "../components/PageIntro";
import { useApp } from "../lib/store";

function multiMethodCurves(methods: Record<string, any>, kind: "roc" | "pr") {
  const colors = ["#1F7A8C", "#C47B2B", "#3D8B6E", "#7C5CBF", "#4A90A4", "#B85C38", "#8BA0B8", "#5B8C5A"];
  const traces: any[] = [];
  let i = 0;
  for (const [name, block] of Object.entries(methods || {})) {
    const c = kind === "roc" ? block?.roc_curve : block?.pr_curve;
    if (!c) continue;
    const x = kind === "roc" ? c.fpr : c.recall;
    const y = kind === "roc" ? c.tpr : c.precision;
    if (!x || !y) continue;
    traces.push({
      type: "scatter",
      mode: "lines",
      name: name.replace(/__/g, " · "),
      x,
      y,
      line: { color: colors[i % colors.length], width: name.includes("ecn_proposed__full") ? 3 : 1.5 },
      opacity: name.includes("ecn_proposed__full") ? 1 : 0.75,
      hovertemplate: `%{x:.3f}, %{y:.3f}<extra>${name}</extra>`,
    });
    i += 1;
  }
  return traces;
}

export function FiguresPage() {
  const { metrics, aggregate } = useApp();
  const t1roc = useMemo(() => multiMethodCurves(metrics?.T1 || {}, "roc"), [metrics]);
  const t1pr = useMemo(() => multiMethodCurves(metrics?.T1 || {}, "pr"), [metrics]);
  const t2roc = useMemo(() => multiMethodCurves(metrics?.T2 || {}, "roc"), [metrics]);
  const t2pr = useMemo(() => multiMethodCurves(metrics?.T2 || {}, "pr"), [metrics]);

  const archBar = useMemo(() => {
    const final = aggregate?.manuscript_ready;
    if (!final) return [];
    return [
      {
        type: "bar",
        x: ["v2 legacy+anchored", "v3+stack ablation", "v3+anchored final", "RF telem_only"],
        y: [
          final.T1_vs_v2?.v2_anchored_legacy_auprc_mean,
          final.T1_stacking_ablation?.auprc_mean,
          final.T1_final_proposed?.auprc_mean,
          final.T1_baselines?.random_forest_telem_only_auprc_mean,
        ],
        marker: { color: ["#8BA0B8", "#4A90A4", "#1F7A8C", "#C47B2B"] },
        hovertemplate: "%{x}: %{y:.6f}<extra></extra>",
      },
    ];
  }, [aggregate]);

  const contrib = useMemo(() => {
    const final = aggregate?.manuscript_ready;
    if (!final) return [];
    const feat =
      (final.T1_final_proposed?.auprc_mean ?? 0) - (final.T1_vs_v2?.v2_anchored_legacy_auprc_mean ?? 0);
    const twin = final.T1_final_proposed?.twin_gain_ap_mean ?? 0;
    const stackDelta = (final.T1_stacking_ablation?.auprc_mean ?? 0) - (final.T1_final_proposed?.auprc_mean ?? 0);
    return [
      {
        type: "bar",
        x: ["Feature enrichment vs v2", "Twin gain", "Stacking − anchored"],
        y: [feat, twin, stackDelta],
        marker: { color: ["#1F7A8C", "#3D8B6E", "#C47B2B"] },
        hovertemplate: "%{x}: %{y:.6f}<extra></extra>",
      },
    ];
  }, [aggregate]);

  const cal = metrics?.curves?.T1_calibration;
  const calTrace = cal
    ? [
        {
          type: "scatter",
          mode: "lines",
          name: "Ideal",
          x: [0, 1],
          y: [0, 1],
          line: { dash: "dash", color: "#8BA0B8" },
        },
        {
          type: "scatter",
          mode: "lines+markers",
          name: "ECN proposed",
          x: cal.mean_predicted,
          y: cal.fraction_positives,
          marker: { color: "#1F7A8C" },
        },
      ]
    : [];

  const cm = metrics?.curves?.T1_cm;
  const cmTrace = cm
    ? [
        {
          type: "heatmap",
          z: cm,
          x: ["Pred 0", "Pred 1"],
          y: ["True 0", "True 1"],
          colorscale: "Blues",
          hovertemplate: "%{y} / %{x}: %{z}<extra></extra>",
        },
      ]
    : [];

  const t2seed = useMemo(() => {
    const t2per = aggregate?.manuscript_ready?.T2_recommended?.per_seed_auprc;
    const t1per = aggregate?.manuscript_ready?.T1_final_proposed?.per_seed_auprc;
    const traces: any[] = [];
    if (Array.isArray(t1per)) {
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: "T1 final AUPRC",
        x: t1per.map((_: number, i: number) => i + 1),
        y: t1per,
        marker: { color: "#1F7A8C" },
        hovertemplate: "seed #%{x}: %{y:.4f}<extra>T1</extra>",
      });
    }
    if (Array.isArray(t2per)) {
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: "T2 telem logistic AUPRC",
        x: t2per.map((_: number, i: number) => i + 1),
        y: t2per,
        marker: { color: "#C47B2B" },
        hovertemplate: "seed #%{x}: %{y:.4f}<extra>T2</extra>",
      });
    }
    return traces;
  }, [aggregate]);

  return (
    <div>
      <PageIntro
        title="Figures"
        description="Explore publication-ready benchmark figures and visual analyses."
      />
      <p className="mb-4 text-sm text-noc-muted">
        Curves below are for the <span className="font-mono text-noc-accent">{metrics?.seed}</span> seed overlay.
        Architecture / contribution bars use six-seed manuscript means. Bold ECN proposed traces highlight the
        evaluation head when present.
      </p>
    <div className="grid gap-4 lg:grid-cols-2">
      <Chart
        title={`T1 ROC (${metrics?.seed})`}
        data={t1roc}
        source={metrics?.source}
        layout={{ xaxis: { title: { text: "FPR" } }, yaxis: { title: { text: "TPR" } } }}
      />
      <Chart
        title={`T1 Precision–Recall (${metrics?.seed})`}
        data={t1pr}
        source={metrics?.source}
        layout={{ xaxis: { title: { text: "Recall" } }, yaxis: { title: { text: "Precision" } } }}
      />
      <Chart title={`T2 ROC (${metrics?.seed})`} data={t2roc} source={metrics?.source} />
      <Chart title={`T2 Precision–Recall (${metrics?.seed})`} data={t2pr} source={metrics?.source} />
      <Chart title="Architecture selection (verified means)" data={archBar as any} source="results/manuscript_ready_numbers.json" />
      <Chart title="Contribution deltas (verified)" data={contrib as any} source="results/manuscript_ready_numbers.json" />
      <Chart title="T1 reliability / calibration" data={calTrace as any} source={metrics?.source} />
      <Chart title="T1 confusion matrix" data={cmTrace as any} source={metrics?.source} />
      <Chart
        title="Per-seed AUPRC (verified manuscript / aggregate)"
        data={t2seed as any}
        source="results/manuscript_ready_numbers.json (T1) + aggregate_v3 logistic (T2 if present)"
      />
    </div>
    </div>
  );
}
