import { useMemo, useState } from "react";
import { PageIntro } from "../components/PageIntro";

/**
 * Live API Prototype — intentionally separated from historical benchmark replay.
 * Does not fabricate a live incident stream. Adapter fetch is opt-in via URL.
 */

export type LiveTelemetryAdapter = {
  /** Optional endpoint returning JSON health/status. Empty/unset → not connected. */
  statusUrl?: string;
  fetchStatus: (url: string) => Promise<{ ok: boolean; body?: unknown; error?: string }>;
};

const defaultAdapter: LiveTelemetryAdapter = {
  fetchStatus: async (url: string) => {
    try {
      const res = await fetch(url, { method: "GET" });
      if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
      const body = await res.json().catch(() => null);
      return { ok: true, body };
    } catch (e: any) {
      return { ok: false, error: e?.message || String(e) };
    }
  },
};

export function LivePrototypePage() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<{ ok: boolean; body?: unknown; error?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const adapter = useMemo(() => defaultAdapter, []);

  async function probe() {
    setBusy(true);
    setResult(null);
    try {
      if (!url.trim()) {
        setResult({ ok: false, error: "No URL configured — adapter disabled by default." });
        return;
      }
      setResult(await adapter.fetchStatus(url.trim()));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageIntro
        title="Live API Prototype"
        description="Prototype adapter interface only. Not connected to production telemetry. Historical Benchmark pages remain the scientific source of truth."
      />
      <div className="rounded-xl border border-amber-500/50 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
        <strong>Not a live operations console.</strong> No synthetic incident stream is generated here.
        Configure an optional status URL to exercise the client adapter; unset URLs report disconnected.
      </div>

      <div className="noc-card grid gap-6 p-6 md:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm font-semibold">Historical Benchmark</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-noc-muted">
            <li>Frozen ECNetBench SQLite seeds</li>
            <li>Verified AUPRC / ROC / SHAP artifacts</li>
            <li>NOC replay topology + Runbook</li>
          </ul>
        </div>
        <div>
          <h3 className="mb-2 text-sm font-semibold">Live API Prototype</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-noc-muted">
            <li>
              <code className="text-xs">LiveTelemetryAdapter</code> TypeScript interface
            </li>
            <li>Opt-in HTTP probe only</li>
            <li>Fails closed when URL unset</li>
          </ul>
        </div>
      </div>

      <div className="noc-card space-y-3 p-4">
        <label className="block text-xs text-noc-muted" htmlFor="live-url">
          Optional status URL
        </label>
        <div className="flex flex-wrap gap-2">
          <input
            id="live-url"
            className="min-w-[240px] flex-1 rounded-lg border border-noc-border bg-noc-bg px-3 py-2 text-sm"
            placeholder="https://example.invalid/health (leave empty)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button
            type="button"
            className="rounded-lg bg-noc-accent/80 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            disabled={busy}
            onClick={probe}
          >
            {busy ? "Probing…" : "Probe adapter"}
          </button>
        </div>
        {result && (
          <pre className="overflow-x-auto rounded-lg bg-black/30 p-3 text-xs text-noc-muted">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
