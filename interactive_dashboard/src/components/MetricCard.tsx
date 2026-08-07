import { motion } from "framer-motion";
import { MetricTooltip } from "./MetricTooltip";

export function ProvenanceBadge({
  source,
  field,
  className = "",
}: {
  source: string;
  field?: string;
  className?: string;
}) {
  return (
    <details className={`noc-chip cursor-pointer ${className}`}>
      <summary className="list-none">Data provenance</summary>
      <div className="mt-1 max-w-md whitespace-pre-wrap font-mono text-[10px] leading-relaxed text-noc-muted">
        Source: {source}
        {field ? `\nField: ${field}` : ""}
      </div>
    </details>
  );
}

export function MetricCard({
  label,
  value,
  sub,
  explanation,
  source,
  field,
  accent,
  metricTerm,
}: {
  label: string;
  value: string;
  sub?: string;
  explanation?: string;
  source?: string;
  field?: string;
  accent?: boolean;
  metricTerm?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`noc-card p-4 ${accent ? "ring-1 ring-noc-accent/40" : ""}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center text-xs uppercase tracking-wider text-noc-muted">
          {label}
          {metricTerm ? <MetricTooltip term={metricTerm} /> : null}
        </div>
        {source ? <ProvenanceBadge source={source} field={field} /> : null}
      </div>
      <div className={`mt-2 font-mono text-2xl font-semibold ${accent ? "text-noc-accent" : "text-white"}`}>
        {value}
      </div>
      {explanation ? <p className="mt-2 text-xs leading-relaxed text-noc-muted">{explanation}</p> : null}
      {sub ? <div className="mt-1 text-xs text-noc-muted/80">{sub}</div> : null}
    </motion.div>
  );
}
