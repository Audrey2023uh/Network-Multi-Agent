import { ProvenanceBadge } from "../components/MetricCard";

const SECTIONS = [
  {
    title: "Methodology overview",
    body: "ECNetBench provides frozen multi-seed enterprise network SQLite instances. ECN-v3 applies leakage-safe feature engineering, specialist anomaly/prediction heads, and anchored fusion (ECNFusionModel) for T1. Stacking is retained only as a negative ablation.",
    math: "AUPRC = ∫ Precision(r) dRecall(r) estimated from score-ranked predictions without threshold tuning on the test set.",
    code: "evaluation/run_full_evaluation.py",
  },
  {
    title: "Leakage-safe features",
    body: "Causal roll/EMA/z features use shift(1). Feature bin timestamp is feat_bin = t_start − 30 minutes so labels never peek into the prediction window.",
    math: "x̃_t = f(x_{≤t−1}); label y_t uses horizon starting at t_start.",
    code: "framework/ecn/features.py",
  },
  {
    title: "Anchored fusion",
    body: "Specialist scores are fused with telemetry-first anchoring. Validation selects among telem≥0.5 constrained candidates. Final architecture is selected by mean AUPRC with a simplicity preference for anchored over stacking.",
    math: "s = Fuse({s_k}) with telem specialist weight constrained; selection argmax_a mean_seed AP(a).",
    code: "framework/ecn/models.py (ECNFusionModel)",
  },
  {
    title: "RCA / TreeSHAP",
    body: "Root-cause categories are predicted with a Random Forest multiclass model; TreeSHAP attributes local and global feature contributions from verified per-seed artifacts.",
    math: "φ_i from TreeExplainer; global importance ≈ E[|φ_i|].",
    code: "framework/ecn/agents/",
  },
  {
    title: "Data provenance rule",
    body: "The dashboard never hard-codes scientific metrics. Build-time adapter scripts/build_data.py materializes public/data/*.json from SQLite + results/*.json.",
    math: null,
    code: "interactive_dashboard/scripts/build_data.py · DATA_PROVENANCE.md",
  },
];

export function DocsPage() {
  return (
    <div className="space-y-4">
      <div className="noc-card p-5">
        <h2 className="text-xl font-semibold">Documentation</h2>
        <p className="mt-1 text-sm text-noc-muted">
          Methodology, formulation, and code pointers for every major dashboard section. Metrics shown elsewhere remain
          bound to repository artifacts.
        </p>
        <ProvenanceBadge className="mt-3" source="paper/overleaf + results/manuscript_ready_numbers.json" />
      </div>
      {SECTIONS.map((s) => (
        <div key={s.title} className="noc-card p-5">
          <h3 className="font-semibold">{s.title}</h3>
          <p className="mt-2 text-sm leading-relaxed text-noc-text/90">{s.body}</p>
          {s.math ? (
            <pre className="mt-3 overflow-x-auto rounded-lg border border-noc-border bg-noc-bg p-3 font-mono text-xs text-noc-accent2">
              {s.math}
            </pre>
          ) : null}
          <div className="mt-3 font-mono text-xs text-noc-muted">Code: {s.code}</div>
        </div>
      ))}
    </div>
  );
}
