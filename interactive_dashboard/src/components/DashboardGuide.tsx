import { useState } from "react";
import { ChevronDownIcon, ChevronUpIcon } from "@heroicons/react/24/outline";
import { STATUS_META, type OpsStatus } from "../lib/deviceStatus";

const LEGEND_COPY: Record<OpsStatus, string> = {
  healthy: "Normal benchmark state",
  warning: "Benchmark indicates elevated observations",
  degraded: "Benchmark shows stronger evidence requiring investigation",
  critical: "Highest benchmark priority within the selected scenario",
  unknown: "Insufficient benchmark evidence",
};

export function DashboardGuide({ sticky = true }: { sticky?: boolean }) {
  const [open, setOpen] = useState(true);

  return (
    <aside
      className={`noc-card border-noc-accent/50 ${
        sticky ? "sticky top-[7.5rem] z-30" : ""
      } overflow-hidden bg-noc-panel/95 shadow-xl backdrop-blur`}
      aria-label="Dashboard Guide"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left hover:bg-white/5"
        aria-expanded={open}
      >
        <div>
          <div className="text-base font-semibold text-white">Understanding This Dashboard</div>
          <div className="mt-0.5 text-xs text-noc-accent">
            Research Benchmark • Historical Replay • Explainable AI
          </div>
        </div>
        {open ? <ChevronUpIcon className="h-5 w-5 shrink-0 text-noc-muted" /> : <ChevronDownIcon className="h-5 w-5 shrink-0 text-noc-muted" />}
      </button>

      {open ? (
        <div className="max-h-[min(70vh,720px)] space-y-4 overflow-y-auto border-t border-noc-border px-4 pb-4 text-sm">
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-noc-muted">What this dashboard shows</h3>
            <p className="mt-2 leading-relaxed text-noc-text/90">
              This dashboard visualizes historical ECNetBench / ECN-v3 benchmark data.
            </p>
            <p className="mt-2 leading-relaxed text-noc-text/90">
              It presents objective evidence generated from benchmark artifacts, model outputs, and explainable AI
              analyses.
            </p>
            <p className="mt-2 font-medium text-amber-200">It is NOT connected to a live production network.</p>
          </section>

          <hr className="border-noc-border/80" />

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-noc-muted">What you can inspect</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-noc-text/90">
              <li>Device name</li>
              <li>Device type</li>
              <li>Benchmark status</li>
              <li>Historical benchmark events</li>
              <li>Associated performance metrics</li>
              <li>Model confidence (when available)</li>
              <li>TreeSHAP feature importance</li>
              <li>Connected devices</li>
              <li>Provenance of the displayed results</li>
            </ul>
          </section>

          <hr className="border-noc-border/80" />

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-noc-muted">Status Legend</h3>
            <ul className="mt-3 space-y-2">
              {(Object.keys(STATUS_META) as OpsStatus[]).map((s) => (
                <li key={s} className="flex gap-3">
                  <span
                    className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-black"
                    style={{ backgroundColor: STATUS_META[s].color }}
                    aria-hidden
                  >
                    {STATUS_META[s].icon}
                  </span>
                  <div>
                    <div className="font-medium text-white">{STATUS_META[s].label}</div>
                    <div className="text-xs text-noc-muted">{LEGEND_COPY[s]}</div>
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-noc-muted">
              These represent benchmark classifications only and NOT live operational alarms.
            </p>
          </section>

          <hr className="border-noc-border/80" />

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-amber-200">Important Notice</h3>
            <p className="mt-2 leading-relaxed text-noc-text/90">
              This interface displays objective benchmark evidence only.
            </p>
            <p className="mt-2 text-noc-text/90">It does NOT recommend operational actions such as:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-noc-muted">
              <li>replacing hardware</li>
              <li>rebooting devices</li>
              <li>changing configurations</li>
              <li>checking cables</li>
              <li>replacing SFP modules</li>
            </ul>
            <p className="mt-2 text-xs text-noc-muted">
              unless those actions are explicitly supported by the benchmark dataset.
            </p>
          </section>

          <hr className="border-noc-border/80" />

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-noc-muted">Scientific Transparency</h3>
            <p className="mt-2 leading-relaxed text-noc-text/90">
              All displayed metrics originate from repository benchmark artifacts.
            </p>
            <p className="mt-2 leading-relaxed text-noc-text/90">
              The dashboard does not generate or invent scientific results in the browser.
            </p>
          </section>

          <hr className="border-noc-border/80" />

          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-noc-muted">User Workflow</h3>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-noc-text/90">
              <li>Select a benchmark seed.</li>
              <li>Inspect the topology.</li>
              <li>Select a device.</li>
              <li>Review benchmark evidence.</li>
              <li>Examine TreeSHAP explanations.</li>
              <li>Compare model outputs.</li>
              <li>Verify provenance and reproducibility.</li>
            </ol>
          </section>

          <div className="border-t border-noc-border pt-3 text-center text-[11px] leading-relaxed text-noc-muted">
            <div>Designed and developed by Audrey Rah</div>
            <div>Department of Electrical and Computer Engineering</div>
            <div>University of Houston</div>
          </div>
        </div>
      ) : (
        <div className="border-t border-noc-border px-4 py-2 text-xs text-noc-muted">
          Guide collapsed — click to expand. Historical research benchmark replay · not live NOC alarms.
        </div>
      )}
    </aside>
  );
}
