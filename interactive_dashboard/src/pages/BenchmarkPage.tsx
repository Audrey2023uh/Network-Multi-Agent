import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { TopologyMap } from "../components/TopologyMap";
import { ProvenanceBadge } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { DashboardGuide } from "../components/DashboardGuide";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";
import {
  deriveDeviceOps,
  deviceTypeBucket,
  deviceTypeLabel,
  STATUS_META,
  type DeviceTypeFilter,
  type OpsStatus,
} from "../lib/deviceStatus";

function AssessmentRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="grid grid-cols-[150px_1fr] gap-2 border-b border-noc-border/40 py-1.5">
      <span className="text-noc-muted">{label}</span>
      <span className="text-noc-text">{value}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: OpsStatus }) {
  const m = STATUS_META[status];
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-semibold"
      style={{ backgroundColor: `${m.color}22`, borderColor: m.border, color: m.color }}
    >
      <span aria-hidden>{m.icon}</span>
      {m.label}
    </span>
  );
}

function DeviceHealthPanel({
  device,
  topology,
  metrics,
  seed,
}: {
  device: any;
  topology: any;
  metrics: any;
  seed: string;
}) {
  const ops = deriveDeviceOps(topology, device);
  const primary = ops.primary;
  const topShap = metrics?.shap?.top_features?.[0];
  const seedT1 = metrics?.T1?.ecn_proposed__full;
  const hasShap = Array.isArray(metrics?.shap?.top_features) && metrics.shap.top_features.length > 0;

  const priority = ops.severity
    ? String(ops.severity)
    : ops.incidents.length
      ? "See incident.severity on related records"
      : "—";

  const evidenceParts: string[] = [];
  if (ops.evidence) evidenceParts.push(ops.evidence);
  if (primary?.detection_source) evidenceParts.push(`detection_source=${primary.detection_source}`);
  if (primary?.onset_at) evidenceParts.push(`onset_at=${primary.onset_at}`);
  if (seedT1?.ap != null) {
    evidenceParts.push(
      `Seed-level T1 AUPRC=${fmt(seedT1.ap)} (benchmark overlay, not live per-device score)`,
    );
  }

  let next: string | null = null;
  if (ops.incidents.length && primary?.category) {
    next = `Inspect interfaces and labeled category “${primary.category}” on this device; then open TreeSHAP for seed-level feature evidence.`;
  } else if (hasShap) {
    next = "No device-linked incident — optional: review seed TreeSHAP / Results for benchmark context.";
  } else if (!ops.incidents.length) {
    next = "No labeled incident on this device in this seed extract.";
  }

  if (topShap?.feature && ops.incidents.length) {
    evidenceParts.push(
      `Top seed TreeSHAP feature: ${topShap.feature} (${fmt(Number(topShap.importance))})`,
    );
  }

  return (
    <div className="rounded-xl border border-noc-accent/40 bg-noc-bg/60 p-3">
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase tracking-wide text-noc-accent">Device Health</div>
        <StatusBadge status={ops.status} />
      </div>
      <p className="mt-1 text-[11px] text-noc-muted">
        Historical benchmark replay — status derived only from labeled failure_incident severity linked to this device.
      </p>
      <div className="mt-2 space-y-1 text-xs">
        <AssessmentRow label="Hostname" value={String(device.hostname || "—")} />
        <AssessmentRow label="Status" value={`${STATUS_META[ops.status].icon} ${STATUS_META[ops.status].label}`} />
        <AssessmentRow label="Priority" value={priority} />
        <AssessmentRow label="Incidents" value={String(ops.incidents.length)} />
        <AssessmentRow
          label="Primary evidence"
          value={evidenceParts.length ? evidenceParts.join(" · ") : "No incident evidence linked in this extract"}
        />
        <AssessmentRow label="Recommended next investigation" value={next} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link
          className={`rounded-lg px-3 py-1.5 text-xs font-medium ${hasShap ? "bg-noc-accent text-white" : "border border-noc-border text-noc-muted"}`}
          to={hasShap ? `/shap?device=${encodeURIComponent(String(device.hostname || device.device_id || ""))}` : "/shap"}
        >
          View Root Cause
        </Link>
        <Link className="rounded-lg border border-noc-border px-3 py-1.5 text-xs" to="/results">
          View Results
        </Link>
        <a className="rounded-lg border border-noc-border px-3 py-1.5 text-xs" href="#device-evidence">
          View Device Evidence
        </a>
        <Link className="rounded-lg border border-noc-border px-3 py-1.5 text-xs" to="/runbook">
          Open Runbook
        </Link>
      </div>
      <div className="mt-2 text-[10px] text-noc-muted">Seed context: {seed}</div>
    </div>
  );
}

function SidePanel({
  selection,
  topology,
  metrics,
  seed,
}: {
  selection: { kind: "device" | "link"; data: any } | null;
  topology: any;
  metrics: any;
  seed: string;
}) {
  if (!selection) {
    return (
      <div className="space-y-2 text-sm text-noc-muted">
        <p>Select a device from the map or Needs Attention list.</p>
        <p className="text-xs">Operational Device Health appears first; raw DB fields follow below.</p>
      </div>
    );
  }

  const data = selection.data || {};
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined && v !== "");
  const ifaces =
    selection.kind === "device" ? topology.interfaces_by_device?.[String(data.device_id)] || [] : [];
  const ops = selection.kind === "device" ? deriveDeviceOps(topology, data) : null;

  return (
    <div className="space-y-4 text-sm">
      <div className="text-xs uppercase tracking-wide text-noc-muted">{selection.kind}</div>

      {selection.kind === "device" ? (
        <DeviceHealthPanel device={data} topology={topology} metrics={metrics} seed={seed} />
      ) : null}

      <div id="device-evidence">
        <div className="mb-1 text-xs font-semibold uppercase text-noc-muted">Technical / database fields</div>
        <div className="max-h-[240px] space-y-1 overflow-auto font-mono text-[11px]">
          {entries.map(([k, v]) => (
            <div key={k} className="grid grid-cols-[120px_1fr] gap-2 border-b border-noc-border/40 py-1">
              <span className="text-noc-muted">{k}</span>
              <span className="break-all text-noc-text">{String(v)}</span>
            </div>
          ))}
        </div>
      </div>

      {ifaces.length ? (
        <div>
          <div className="mb-1 text-xs uppercase text-noc-muted">Interfaces ({ifaces.length})</div>
          <ul className="max-h-36 overflow-auto text-xs text-noc-muted">
            {ifaces.slice(0, 20).map((iface: any) => (
              <li key={iface.interface_id}>
                {iface.if_name} · {iface.oper_status} · vlan mode {iface.enabled_vlans_mode}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {ops && ops.incidents.length ? (
        <div>
          <div className="mb-1 text-xs uppercase text-noc-muted">Related labeled incidents</div>
          <ul className="space-y-1 text-xs">
            {ops.incidents.slice(0, 5).map((inc: any) => (
              <li key={inc.incident_id} className="rounded border border-noc-border p-2">
                {inc.category} · {inc.severity} · {inc.onset_at}
                {inc.description ? <div className="mt-1 text-noc-muted">{inc.description}</div> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

const STATUS_FILTERS: Array<OpsStatus | "all"> = [
  "all",
  "critical",
  "degraded",
  "warning",
  "healthy",
  "unknown",
];

const TYPE_FILTERS: DeviceTypeFilter[] = ["all", "ap", "switch", "router", "gateway", "other"];

export function BenchmarkPage() {
  const { topology, metrics, seed } = useApp();
  const [selection, setSelection] = useState<{ kind: "device" | "link"; data: any } | null>(null);
  const [tIdx, setTIdx] = useState(0);
  const [statusFilter, setStatusFilter] = useState<OpsStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<DeviceTypeFilter>("all");

  const onSelect = useCallback((payload: { kind: "device" | "link"; data: any }) => {
    setSelection(payload);
  }, []);

  const telemTimes = useMemo(() => {
    if (!topology?.telemetry_sample?.length || !topology.time_range) return [];
    const col = topology.time_range.column;
    return Array.from(
      new Set(topology.telemetry_sample.map((r) => String(r[col])).filter(Boolean)),
    ).sort();
  }, [topology]);

  const attentionRows = useMemo(() => {
    if (!topology?.available) return [];
    return (topology.devices || [])
      .map((device: any) => {
        const ops = deriveDeviceOps(topology, device);
        return {
          device,
          ops,
          type: deviceTypeLabel(device),
          typeBucket: deviceTypeBucket(device),
        };
      })
      .filter((r) => (statusFilter === "all" ? true : r.ops.status === statusFilter))
      .filter((r) => (typeFilter === "all" ? true : r.typeBucket === typeFilter))
      .sort((a, b) => {
        const dr = STATUS_META[a.ops.status].rank - STATUS_META[b.ops.status].rank;
        if (dr !== 0) return dr;
        return b.ops.incidents.length - a.ops.incidents.length;
      });
  }, [topology, statusFilter, typeFilter]);

  if (!topology?.available) {
    return <div className="noc-card p-6">Topology unavailable for this seed.</div>;
  }

  const slice = telemTimes.length
    ? topology.telemetry_sample.filter((r) => String(r[topology.time_range!.column]) === telemTimes[tIdx])
    : [];

  const selectedId =
    selection?.kind === "device" && selection.data?.device_id ? String(selection.data.device_id) : null;

  return (
    <div className="space-y-4">
      <PageIntro
        title="Benchmark"
        description="Replay and inspect benchmark scenarios for the selected seed."
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(280px,0.95fr)_minmax(0,1.75fr)]">
        <DashboardGuide sticky />

        <div className="min-w-0 space-y-4">
      <div className="noc-card border-noc-accent/40 bg-gradient-to-r from-noc-accent/10 to-transparent p-5">
        <div className="text-xs uppercase tracking-wide text-noc-accent">NOC Technician Workflow</div>
        <p className="mt-2 text-sm font-medium">
          Select scenario → Find affected device → Inspect evidence → Identify likely cause → Review recommended action
        </p>
        <p className="mt-2 text-xs text-noc-muted">
          Historical Benchmark Replay for seed <span className="font-mono text-noc-accent">{seed}</span>. Status colors
          are derived from labeled incidents in this extract — not live production alerts.{" "}
          <Link className="text-noc-accent2 underline" to="/runbook">
            Open Runbook
          </Link>
        </p>
      </div>

      <div className="noc-card flex flex-wrap items-center gap-3 p-4 text-sm">
        <div>
          <span className="font-semibold">{topology.seed}</span>
          <span className="text-noc-muted">
            {" "}
            · {topology.n_devices} devices · {topology.n_links} links · {topology.n_incidents} incidents
          </span>
        </div>
        <ProvenanceBadge
          source={topology.source_db}
          field="device/link/interface/failure_incident (severity→status mapping)"
        />
        <span className="noc-chip">{topology.note}</span>
      </div>

      {/* Filters */}
      <div className="noc-card space-y-3 p-4">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-noc-muted">Status filter</div>
          <div className="flex flex-wrap gap-2">
            {STATUS_FILTERS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setStatusFilter(s)}
                className={`rounded-lg border px-3 py-1.5 text-xs ${
                  statusFilter === s ? "border-noc-accent bg-noc-accent/20 text-white" : "border-noc-border"
                }`}
              >
                {s === "all" ? "All" : STATUS_META[s].label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-noc-muted">Device type</div>
          <div className="flex flex-wrap gap-2">
            {TYPE_FILTERS.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTypeFilter(t)}
                className={`rounded-lg border px-3 py-1.5 text-xs capitalize ${
                  typeFilter === t ? "border-noc-accent bg-noc-accent/20 text-white" : "border-noc-border"
                }`}
              >
                {t === "ap" ? "AP" : t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="noc-card p-4">
        <div className="text-xs font-semibold uppercase text-noc-muted">Device Status Legend</div>
        <div className="mt-3 flex flex-wrap gap-4 text-xs">
          {(Object.keys(STATUS_META) as OpsStatus[]).map((s) => (
            <div key={s} className="flex items-center gap-2">
              <span
                className="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold text-black"
                style={{ backgroundColor: STATUS_META[s].color }}
                aria-hidden
              >
                {STATUS_META[s].icon}
              </span>
              <span>
                {STATUS_META[s].label}
                {s === "unknown" ? " / no sufficient evidence" : ""}
                {s === "healthy" ? " / normal" : ""}
              </span>
            </div>
          ))}
          <div className="flex items-center gap-2 text-noc-muted">
            <span className="inline-block h-3 w-3 rounded-full border-2 border-sky-400" /> Selected (blue ring) ·
            neighbors highlighted
          </div>
        </div>
        <p className="mt-2 text-[11px] text-noc-muted">
          Mapping: incident.severity critical→Critical, high→Degraded, medium/low→Warning; no linked incident→Healthy.
          Shapes also encode status (diamond/triangle/round-rect/ellipse/octagon) for accessibility.
        </p>
      </div>

      {/* Needs Attention */}
      <div className="noc-card p-4">
        <h3 className="text-sm font-semibold">Needs Attention</h3>
        <p className="mt-1 text-xs text-noc-muted">
          Sorted Critical → Degraded → Warning → Unknown → Healthy. Click Inspect to focus the topology node.
        </p>
        <div className="mt-3 max-h-56 overflow-auto">
          <table className="min-w-full text-left text-xs">
            <thead className="sticky top-0 bg-noc-panel text-noc-muted">
              <tr>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Hostname</th>
                <th className="px-2 py-2">Type</th>
                <th className="px-2 py-2">Incidents</th>
                <th className="px-2 py-2">Severity</th>
                <th className="px-2 py-2">Evidence</th>
                <th className="px-2 py-2" />
              </tr>
            </thead>
            <tbody>
              {attentionRows.map(({ device, ops, type }) => (
                <tr key={device.device_id} className="border-t border-noc-border/50 hover:bg-white/5">
                  <td className="px-2 py-2">
                    <StatusBadge status={ops.status} />
                  </td>
                  <td className="px-2 py-2 font-mono">{device.hostname}</td>
                  <td className="px-2 py-2">{type}</td>
                  <td className="px-2 py-2">{ops.incidents.length}</td>
                  <td className="px-2 py-2">{ops.severity || "—"}</td>
                  <td className="max-w-[220px] truncate px-2 py-2 text-noc-muted" title={ops.reason}>
                    {ops.reason}
                  </td>
                  <td className="px-2 py-2">
                    <button
                      type="button"
                      className="rounded border border-noc-border px-2 py-1 hover:border-noc-accent"
                      onClick={() => setSelection({ kind: "device", data: device })}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[1.35fr_0.85fr]">
        <div className="noc-card p-3">
          <TopologyMap
            topology={topology}
            onSelect={onSelect}
            selectedDeviceId={selectedId}
            statusFilter={statusFilter}
            typeFilter={typeFilter}
          />
        </div>
        <div className="noc-card p-4">
          <h3 className="mb-3 font-semibold">Inspector</h3>
          <SidePanel selection={selection} topology={topology} metrics={metrics} seed={seed} />
        </div>
      </div>

      <div className="text-center text-xs text-noc-muted">
        Designed and developed by Audrey Rah · Department of Electrical and Computer Engineering · University of
        Houston
      </div>
        </div>
      </div>
    </div>
  );
}
