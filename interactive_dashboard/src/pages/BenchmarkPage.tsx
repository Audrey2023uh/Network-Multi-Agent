import { useMemo, useState } from "react";
import { TopologyMap } from "../components/TopologyMap";
import { ProvenanceBadge } from "../components/MetricCard";
import { useApp } from "../lib/store";

function SidePanel({
  selection,
  topology,
}: {
  selection: { kind: "device" | "link"; data: any } | null;
  topology: any;
}) {
  if (!selection) {
    return <div className="text-sm text-noc-muted">Select a node or link to inspect verified fields.</div>;
  }
  const data = selection.data || {};
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined && v !== "");
  const ifaces =
    selection.kind === "device" ? topology.interfaces_by_device?.[String(data.device_id)] || [] : [];
  const relatedIncidents =
    selection.kind === "device"
      ? (topology.incidents || []).filter((inc: any) => {
          const desc = String(inc.description || "");
          const host = String(data.hostname || "");
          return host && desc.includes(host);
        })
      : [];

  return (
    <div className="space-y-4 text-sm">
      <div className="text-xs uppercase tracking-wide text-noc-muted">{selection.kind}</div>
      <div className="max-h-[420px] space-y-1 overflow-auto font-mono text-[11px]">
        {entries.map(([k, v]) => (
          <div key={k} className="grid grid-cols-[120px_1fr] gap-2 border-b border-noc-border/40 py-1">
            <span className="text-noc-muted">{k}</span>
            <span className="break-all text-noc-text">{String(v)}</span>
          </div>
        ))}
      </div>
      {ifaces.length ? (
        <div>
          <div className="mb-1 text-xs uppercase text-noc-muted">Interfaces ({ifaces.length})</div>
          <ul className="max-h-40 overflow-auto text-xs text-noc-muted">
            {ifaces.slice(0, 20).map((iface: any) => (
              <li key={iface.interface_id}>
                {iface.if_name} · {iface.oper_status} · vlan mode {iface.enabled_vlans_mode}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {relatedIncidents.length ? (
        <div>
          <div className="mb-1 text-xs uppercase text-noc-muted">Related incidents</div>
          <ul className="space-y-1 text-xs">
            {relatedIncidents.slice(0, 5).map((inc: any) => (
              <li key={inc.incident_id} className="rounded border border-noc-border p-2">
                {inc.category} · {inc.severity} · {inc.onset_at}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function BenchmarkPage() {
  const { topology } = useApp();
  const [selection, setSelection] = useState<{ kind: "device" | "link"; data: any } | null>(null);
  const [tIdx, setTIdx] = useState(0);

  const telemTimes = useMemo(() => {
    if (!topology?.telemetry_sample?.length || !topology.time_range) return [];
    const col = topology.time_range.column;
    const times = Array.from(
      new Set(topology.telemetry_sample.map((r) => String(r[col])).filter(Boolean)),
    ).sort();
    return times;
  }, [topology]);

  if (!topology?.available) {
    return <div className="noc-card p-6">Topology unavailable for this seed.</div>;
  }

  const slice = telemTimes.length
    ? topology.telemetry_sample.filter((r) => String(r[topology.time_range!.column]) === telemTimes[tIdx])
    : [];

  return (
    <div className="space-y-4">
      <div className="noc-card flex flex-wrap items-center gap-3 p-4 text-sm">
        <div>
          <span className="font-semibold">{topology.seed}</span>
          <span className="text-noc-muted">
            {" "}
            · {topology.n_devices} devices · {topology.n_links} links · {topology.n_incidents} incidents ·{" "}
            {topology.schema.length} tables
          </span>
        </div>
        <ProvenanceBadge source={topology.source_db} field="device/link/interface/failure_incident/device_resource_sample" />
        <span className="noc-chip">{topology.note}</span>
      </div>

      {telemTimes.length ? (
        <div className="noc-card p-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span>Historical telemetry replay ({topology.time_range?.column})</span>
            <span className="font-mono text-xs text-noc-muted">{telemTimes[tIdx]}</span>
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(0, telemTimes.length - 1)}
            value={tIdx}
            onChange={(e) => setTIdx(Number(e.target.value))}
            className="w-full"
          />
          <div className="mt-2 text-xs text-noc-muted">
            Samples at cursor: {slice.length} (from telemetry_sample; capped at build time)
          </div>
        </div>
      ) : (
        <div className="noc-card p-3 text-xs text-noc-muted">
          No usable telemetry timestamps in the sampled extract for a time slider on this seed.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
        <div className="noc-card p-3">
          <TopologyMap topology={topology} onSelect={setSelection} />
        </div>
        <div className="noc-card p-4">
          <h3 className="mb-3 font-semibold">Inspector</h3>
          <SidePanel selection={selection} topology={topology} />
        </div>
      </div>

      <div className="noc-card p-4">
        <h3 className="mb-2 font-semibold">SQLite schema (tables)</h3>
        <div className="flex flex-wrap gap-2">
          {topology.schema.map((t) => (
            <span key={t.name} className="noc-chip">
              {t.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
