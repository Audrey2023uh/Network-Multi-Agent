import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";

export function ReplayBanner({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <div className="border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-center text-xs text-amber-100">
        <strong>Historical Benchmark Replay</strong> — verified ECNetBench artifacts only; not a live production NOC
        feed.
      </div>
    );
  }
  return (
    <div className="noc-card border-amber-500/40 bg-gradient-to-r from-amber-500/15 via-noc-panel to-noc-panel p-4">
      <div className="flex gap-3">
        <ExclamationTriangleIcon className="mt-0.5 h-6 w-6 shrink-0 text-amber-400" />
        <div>
          <div className="text-sm font-semibold uppercase tracking-wide text-amber-200">Historical Benchmark Replay</div>
          <p className="mt-1 text-sm leading-relaxed text-noc-text/90">
            This dashboard visualizes previously generated ECNetBench / ECN-v3 benchmark artifacts. It is{" "}
            <strong>not</strong> connected to a live production network and does <strong>not</strong> execute the agents
            in real time.
          </p>
        </div>
      </div>
    </div>
  );
}
