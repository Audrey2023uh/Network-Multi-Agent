import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { TopologyMap } from "../components/TopologyMap";
import { ProvenanceBadge } from "../components/MetricCard";
import { PageIntro } from "../components/PageIntro";
import { useApp } from "../lib/store";
import { fmt } from "../lib/data";

function relatedIncidentsForDevice(topology: any, device: any) {
  const host = String(device?.hostname || "");
  const id = String(device?.device_id || "");
  return (topology.incidents || []).filter((inc: any) => {
    const desc = String(inc.description || "");
    const rootId = String(inc.root_entity_id || "");
    const rootType = String(inc.root_entity_type || "").toLowerCase();
    if (id && rootId === id) return true;
    if (host && desc.includes(host)) return true;
    if (id && rootType.includes("device") && rootId === id) return true;
    return false;
  });
}

function devicesWithIncidents(topology: any) {
  const out: { device: any; incidents: any[] }[] = [];
  for (const d of topology.devices || []) {
    const incs = relatedIncidentsForDevice(topology, d);
    if (incs.length) out.push({ device: d, incidents: incs });
  }
  out.sort((a, b) => b.incidents.length - a.incidents.length);
  return out;
}

function AssessmentRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="grid grid-cols-[140px_1fr] gap-2 border-b border-noc-border/40 py-1.5">
      <span className="text-noc-muted">{label}</span>
      <span className="text-noc-text">{value}</span>
    </div>
  );
}

function TechnicianAssessment({
  device,
  incidents,
  metrics,
  seed,
}: {
  device: any;
  incidents: any[];
  metrics: any;
  seed: string;
}) {
  const primary = incidents[0] || null;
  const topShap = metrics?.shap?.top_features?.[0];
  const seedT1 = metrics?.T1?.ecn_proposed__full;
  const hasShap = Array.isArray(metrics?.shap?.top_features) && metrics.shap.top_features.length > 0;

  const statusParts = [
    device.status ? `device.status=${device.status}` : null,
    incidents.length ? `${incidents.length} related labeled incident(s) in this seed` : "no related labeled incident in this seed",
  ].filter(Boolean);

  const severity = primary?.severity
    ? String(primary.severity)
    : incidents.length
      ? "See related incident records (severity field missing on primary)"
      : null;

  const observed =
    primary?.description ||
    (primary?.category ? `Labeled category: ${primary.category}${primary.subcategory ? ` / ${primary.subcategory}` : ""}` : null) ||
    (incidents.length ? null : "No device-linked failure_incident description in this seed extract.");

  const evidenceParts: string[] = [];
  if (seedT1?.ap != null || seedT1?.roc_auc != null) {
    evidenceParts.push(
      `Seed-level T1 (ecn_proposed__full): AUPRC=${fmt(seedT1.ap ?? seedT1.auprc)} · ROC-AUC=${fmt(seedT1.roc_auc)} (not a live per-device score)`,
    );
  }
  if (primary?.detection_source) evidenceParts.push(`detection_source=${primary.detection_source}`);
  if (primary?.onset_at) evidenceParts.push(`onset_at=${primary.onset_at}`);
  if (primary?.detected_at) evidenceParts.push(`detected_at=${primary.detected_at}`);

  const factors: string[] = [];
  if (topShap?.feature) {
    factors.push(
      `Top TreeSHAP feature in seed ${seed} artifact: ${topShap.feature} (importance=${fmt(Number(topShap.importance))}) — seed-level RCA evidence unless a device-local explanation exists`,
    );
  }
  if (primary?.observable_precursors) factors.push(`observable_precursors=${primary.observable_precursors}`);
  if (primary?.trigger_type) factors.push(`trigger_type=${primary.trigger_type}`);
  if (primary?.category) factors.push(`incident.category=${primary.category}`);

  // Only recommend investigation steps grounded in available labels — never invent remediation.
  let recommended: string | null = null;
  if (primary?.category) {
    recommended = `Investigate labeled incident category “${primary.category}” on ${device.hostname || device.device_id} using inventory/interfaces below; confirm against historical telemetry replay. No live healing actuation is available in this dashboard.`;
  } else if (incidents.length === 0) {
    recommended =
      "No device-linked incident label in this extract. Use inventory + interfaces for situational awareness; do not treat this node as a production alert.";
  }

  const nextStep = hasShap
    ? "Open TreeSHAP for seed-level feature contribution evidence, then verify numbers under Results / Reproducibility."
    : "Open Results for seed metrics, then Reproducibility for artifact provenance. TreeSHAP block not present for this seed.";

  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-amber-200">Technician Assessment</div>
      <p className="mt-1 text-[11px] text-noc-muted">
        Historical benchmark replay only — fields appear only when present in verified artifacts.
      </p>
      <div className="mt-2 text-xs">
        <AssessmentRow label="Status" value={statusParts.join(" · ")} />
        <AssessmentRow label="Severity / Priority" value={severity} />
        <AssessmentRow label="Observed issue" value={observed} />
        <AssessmentRow label="Model / benchmark evidence" value={evidenceParts.length ? evidenceParts.join(" | ") : null} />
        <AssessmentRow label="Likely contributing factors" value={factors.length ? factors.join(" | ") : null} />
        <AssessmentRow label="Recommended technician action" value={recommended} />
        <AssessmentRow label="Next investigation step" value={nextStep} />
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
    </div>
  );
}

function SidePanel({
  selection,
  topology,
  metrics,
  seed,
  onPickDevice,
}: {
  selection: { kind: "device" | "link"; data: any } | null;
  topology: any;
  metrics: any;
  seed: string;
  onPickDevice: (d: any) => void;
}) {
  if (!selection) {
    return (
      <div className="space-y-3 text-sm text-noc-muted">
        <p>Select a node or link on the map to inspect verified fields.</p>
        <p className="text-xs">Tip: start with devices listed under “Devices with labeled incidents”.</p>
      </div>
    );
  }
  const data = selection.data || {};
  const entries = Object.entries(data).filter(([, v]) => v !== null && v !== undefined && v !== "");
  const ifaces =
    selection.kind === "device" ? topology.interfaces_by_device?.[String(data.device_id)] || [] : [];
  const relatedIncidents = selection.kind === "device" ? relatedIncidentsForDevice(topology, data) : [];

  return (
    <div className="space-y-4 text-sm">
      <div className="text-xs uppercase tracking-wide text-noc-muted">{selection.kind}</div>

      {selection.kind === "device" ? (
        <TechnicianAssessment device={data} incidents={relatedIncidents} metrics={metrics} seed={seed} />
      ) : null}

      <div id="device-evidence">
        <div className="mb-1 text-xs font-semibold uppercase text-noc-muted">Verified fields</div>
        <div className="max-h-[280px] space-y-1 overflow-auto font-mono text-[11px]">
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
                {inc.description ? <div className="mt-1 text-noc-muted">{inc.description}</div> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : selection.kind === "device" ? (
        <button
          type="button"
          className="text-xs text-noc-accent underline"
          onClick={() => {
            const flagged = devicesWithIncidents(topology)[0]?.device;
            if (flagged) onPickDevice(flagged);
          }}
        >
          Jump to a device with labeled incidents
        </button>
      ) : null}
    </div>
  );
}

export function BenchmarkPage() {
  const { topology, metrics, seed } = useApp();
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

  const flagged = useMemo(() => (topology?.available ? devicesWithIncidents(topology) : []), [topology]);

  if (!topology?.available) {
    return <div className="noc-card p-6">Topology unavailable for this seed.</div>;
  }

  const slice = telemTimes.length
    ? topology.telemetry_sample.filter((r) => String(r[topology.time_range!.column]) === telemTimes[tIdx])
    : [];

  return (
    <div className="space-y-4">
      <PageIntro
        title="Benchmark"
        description="Replay and inspect benchmark scenarios for the selected seed."
      />

      <div className="noc-card border-noc-accent/40 bg-gradient-to-r from-noc-accent/10 to-transparent p-5">
        <div className="text-xs uppercase tracking-wide text-noc-accent">NOC Technician Workflow</div>
        <p className="mt-2 text-sm font-medium text-noc-text">
          Select scenario → Find affected device → Inspect evidence → Identify likely cause → Review recommended action
        </p>
        <p className="mt-2 text-xs text-noc-muted">
          Historical replay of seed <span className="font-mono text-noc-accent">{seed}</span>. Not a live production alert
          console.{" "}
          <Link className="underline text-noc-accent2" to="/runbook">
            Open full Runbook
          </Link>
        </p>
      </div>

      <div className="noc-card flex flex-wrap items-center gap-3 p-4 text-sm">
        <div>
          <span className="font-semibold">{topology.seed}</span>
          <span className="text-noc-muted">
            {" "}
            · {topology.n_devices} devices · {topology.n_links} links · {topology.n_incidents} incidents ·{" "}
            {topology.schema.length} tables
          </span>
        </div>
        <ProvenanceBadge
          source={topology.source_db}
          field="device/link/interface/failure_incident/device_resource_sample"
        />
        <span className="noc-chip">{topology.note}</span>
      </div>

      {flagged.length ? (
        <div className="noc-card p-4">
          <h3 className="text-sm font-semibold">Devices with labeled incidents (start here)</h3>
          <p className="mt-1 text-xs text-noc-muted">
            Derived by matching incident description/root_entity_id to device hostname/id in this seed extract.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {flagged.slice(0, 12).map(({ device, incidents }) => (
              <button
                key={device.device_id}
                type="button"
                onClick={() => setSelection({ kind: "device", data: device })}
                className="rounded-lg border border-noc-border bg-noc-bg px-3 py-1.5 text-xs hover:border-noc-accent"
              >
                <span className="font-mono">{device.hostname}</span>
                <span className="text-noc-muted"> · {incidents.length} incident(s)</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}

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
          <SidePanel
            selection={selection}
            topology={topology}
            metrics={metrics}
            seed={seed}
            onPickDevice={(d) => setSelection({ kind: "device", data: d })}
          />
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
