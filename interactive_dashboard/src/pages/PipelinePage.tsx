import { motion } from "framer-motion";

const STEPS = [
  "Raw Enterprise Network",
  "SQLite Benchmark",
  "Feature Engineering",
  "Digital Twin",
  "Perception Agent",
  "Anomaly Agent",
  "Prediction Agent",
  "Anchored Fusion",
  "RCA (TreeSHAP)",
  "Impact Assessment",
  "Healing Recommendation",
];

export function PipelinePage() {
  return (
    <div className="noc-card p-6">
      <h2 className="text-xl font-semibold">End-to-End Pipeline</h2>
      <p className="mt-1 text-sm text-noc-muted">
        Animated historical workflow (benchmark replay). Not a live streaming pipeline.
      </p>
      <div className="mt-8 flex flex-col items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex w-full max-w-xl flex-col items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.08 }}
              className="w-full rounded-xl border border-noc-border bg-gradient-to-r from-noc-panel to-[#152238] px-4 py-3 text-center text-sm font-medium"
            >
              {s}
            </motion.div>
            {i < STEPS.length - 1 ? (
              <motion.div
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ delay: i * 0.08 + 0.05 }}
                className="my-1 h-6 w-px origin-top bg-noc-accent/60"
              />
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
