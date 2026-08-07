import { InformationCircleIcon } from "@heroicons/react/24/outline";

/** Plain-English glossary for technical metric terms. Values only; never used as scientific results. */
export const METRIC_GLOSSARY: Record<string, string> = {
  AUPRC:
    "Area Under the Precision–Recall Curve. Summarizes precision vs recall across thresholds. Preferred when positives (failures/anomalies) are rare.",
  "ROC-AUC":
    "Area Under the Receiver Operating Characteristic curve. Measures how well scores rank positives above negatives across thresholds (0.5 ≈ chance, 1.0 ≈ perfect).",
  Precision: "Among cases predicted positive, the fraction that are truly positive.",
  Recall: "Among truly positive cases, the fraction the model correctly detects (also called sensitivity / true-positive rate).",
  F1: "Harmonic mean of precision and recall; balances false positives and false negatives at a chosen threshold.",
  Threshold: "Score cutoff used to convert continuous risk scores into binary alerts. Reported thresholds come from evaluation artifacts, not live tuning.",
  "Feature importance":
    "Relative contribution of each input feature to model predictions (global) or to a specific decision (local), typically from TreeSHAP attributions.",
  TreeSHAP:
    "TreeSHAP attributes prediction contributions to features for tree ensembles using Shapley values. Used here for RCA evidence, not live remediation.",
  Brier: "Mean squared error of probabilistic forecasts. Lower is better calibrated/accurate probabilities.",
  ECE: "Expected Calibration Error. Average gap between predicted confidence and observed frequency across bins.",
  Twin: "Digital-twin derived graph/topology features (degree, neighbor roles, residuals) used alongside telemetry.",
};

export function MetricTooltip({ term, text }: { term: string; text?: string }) {
  const body = text || METRIC_GLOSSARY[term] || `Technical term: ${term}`;
  return (
    <span className="group relative inline-flex align-middle">
      <button
        type="button"
        className="ml-1 rounded text-noc-muted hover:text-noc-accent"
        aria-label={`About ${term}`}
        title={body}
      >
        <InformationCircleIcon className="h-3.5 w-3.5" />
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 hidden w-64 -translate-x-1/2 rounded-lg border border-noc-border bg-noc-bg p-2 text-left text-[11px] leading-relaxed text-noc-text shadow-xl group-hover:block group-focus-within:block"
      >
        <span className="font-semibold text-noc-accent">{term}</span>
        <span className="mt-1 block text-noc-muted">{body}</span>
      </span>
    </span>
  );
}
