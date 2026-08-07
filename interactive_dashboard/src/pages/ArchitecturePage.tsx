import { useCallback, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useApp } from "../lib/store";
import { ProvenanceBadge } from "../components/MetricCard";
import { ArchitectureGraph } from "../components/ArchitectureGraph";

const DESCRIPTIONS: Record<string, { inputs: string; outputs: string; algo: string }> = {
  digital_twin: {
    inputs: "SQLite inventory, interfaces, links",
    outputs: "Typed graph + neighbor aggregates",
    algo: "Adjacency, degree, role fractions, residual contrasts",
  },
  perception: {
    inputs: "Telemetry windows + twin features",
    outputs: "Leakage-safe feature matrices",
    algo: "Causal roll/EMA/z with shift(1); feat_bin = t_start−30min",
  },
  anomaly: {
    inputs: "Feature matrix (T1)",
    outputs: "Anomaly scores",
    algo: "Specialist models (telem LR, RF, LGBM, IF, twin)",
  },
  prediction: {
    inputs: "Feature matrix (T2)",
    outputs: "Failure-horizon risk scores",
    algo: "Same specialists; ultra-rare prior → telem logistic head",
  },
  fusion: {
    inputs: "Specialist score vectors",
    outputs: "Fused T1 score",
    algo: "ECNFusionModel anchored telem≥0.5 validation selection",
  },
  rca: {
    inputs: "Incident features",
    outputs: "Category + TreeSHAP attributions",
    algo: "RF multiclass + TreeExplainer",
  },
  impact: {
    inputs: "Service / incident labels",
    outputs: "Impact scores",
    algo: "Supervised impact head on twin+telem features",
  },
  healing: {
    inputs: "RCA / telem features",
    outputs: "Remediation class recommendations",
    algo: "Decision-support classifier (no live actuation)",
  },
};

export function ArchitecturePage() {
  const { architecture } = useApp();
  const modules = architecture?.modules || [];
  const [active, setActive] = useState<string | null>(modules[0]?.id ?? null);
  const detail = useMemo(() => modules.find((m: any) => m.id === active), [modules, active]);
  const desc = active ? DESCRIPTIONS[active] : null;
  const onSelect = useCallback((id: string) => setActive(id), []);

  return (
    <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
      <div className="noc-card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">{architecture?.name || "ECN-v3 Architecture"}</h2>
          <ProvenanceBadge source={architecture?.source || "results/final_architecture.json"} />
        </div>
        <ArchitectureGraph modules={modules} onSelect={onSelect} />
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {modules.map((m: any, i: number) => (
            <motion.button
              key={m.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              onClick={() => setActive(m.id)}
              className={`rounded-xl border p-4 text-left transition ${
                active === m.id ? "border-noc-accent bg-noc-accent/15" : "border-noc-border hover:bg-white/5"
              }`}
            >
              <div className="text-sm font-semibold">{m.title}</div>
              <div className="mt-1 font-mono text-[11px] text-noc-muted">{m.code}</div>
            </motion.button>
          ))}
        </div>
        <p className="mt-4 text-xs text-noc-muted">
          Hybrid: {architecture?.hybrid?.T1_head} · {architecture?.hybrid?.T2_head} · {architecture?.hybrid?.RCA}
        </p>
      </div>

      <div className="noc-card p-6">
        <h3 className="text-lg font-semibold">{detail?.title || "Select a module"}</h3>
        {desc ? (
          <div className="mt-4 space-y-3 text-sm">
            <div>
              <div className="text-xs uppercase text-noc-muted">Inputs</div>
              <p>{desc.inputs}</p>
            </div>
            <div>
              <div className="text-xs uppercase text-noc-muted">Outputs</div>
              <p>{desc.outputs}</p>
            </div>
            <div>
              <div className="text-xs uppercase text-noc-muted">Algorithm</div>
              <p>{desc.algo}</p>
            </div>
            <div>
              <div className="text-xs uppercase text-noc-muted">Source code</div>
              <a
                className="font-mono text-noc-accent underline"
                href={`https://github.com/Audrey2023uh/Network-Multi-Agent/blob/main/${detail.code.split("#")[0]}`}
              >
                {detail.code}
              </a>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
