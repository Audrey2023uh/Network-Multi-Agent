/** Derive technician-facing device status only from verified incident labels. */

export type OpsStatus = "critical" | "degraded" | "warning" | "healthy" | "unknown";

export const STATUS_META: Record<
  OpsStatus,
  { label: string; color: string; border: string; icon: string; rank: number }
> = {
  critical: { label: "Critical", color: "#DC2626", border: "#FECACA", icon: "!", rank: 0 },
  degraded: { label: "Degraded", color: "#EA580C", border: "#FED7AA", icon: "▲", rank: 1 },
  warning: { label: "Warning", color: "#CA8A04", border: "#FEF08A", icon: "●", rank: 2 },
  unknown: { label: "Unknown", color: "#6B7280", border: "#D1D5DB", icon: "?", rank: 3 },
  healthy: { label: "Healthy", color: "#16A34A", border: "#BBF7D0", icon: "✓", rank: 4 },
};

export type DeviceTypeFilter = "all" | "ap" | "switch" | "router" | "gateway" | "other";

export function relatedIncidentsForDevice(topology: any, device: any): any[] {
  const host = String(device?.hostname || "");
  const id = String(device?.device_id || "");
  return (topology?.incidents || []).filter((inc: any) => {
    const desc = String(inc.description || "");
    const rootId = String(inc.root_entity_id || "");
    const rootType = String(inc.root_entity_type || "").toLowerCase();
    if (id && rootId === id) return true;
    if (host && desc.includes(host)) return true;
    if (id && rootType.includes("device") && rootId === id) return true;
    return false;
  });
}

/** Map labeled incident.severity → ops status. No fabrication. */
export function severityToOps(sev: string | null | undefined): OpsStatus | null {
  const s = String(sev || "").toLowerCase();
  if (!s) return null;
  if (s === "critical") return "critical";
  if (s === "high") return "degraded";
  if (s === "medium" || s === "low" || s === "warning") return "warning";
  return null;
}

export function worstStatus(statuses: OpsStatus[]): OpsStatus {
  return [...statuses].sort((a, b) => STATUS_META[a].rank - STATUS_META[b].rank)[0] || "unknown";
}

export function deriveDeviceOps(topology: any, device: any): {
  status: OpsStatus;
  incidents: any[];
  primary: any | null;
  severity: string | null;
  reason: string;
  evidence: string | null;
} {
  const incidents = relatedIncidentsForDevice(topology, device);
  if (!device || (!device.hostname && !device.device_id)) {
    return {
      status: "unknown",
      incidents: [],
      primary: null,
      severity: null,
      reason: "Insufficient device identity in extract",
      evidence: null,
    };
  }

  if (!incidents.length) {
    return {
      status: "healthy",
      incidents: [],
      primary: null,
      severity: null,
      reason: "No labeled failure_incident linked in this seed extract",
      evidence: null,
    };
  }

  const mapped = incidents
    .map((i) => severityToOps(i.severity))
    .filter(Boolean) as OpsStatus[];
  const status = mapped.length ? worstStatus(mapped) : "warning";
  // Prefer highest-severity incident as primary
  const ordered = [...incidents].sort((a, b) => {
    const sa = severityToOps(a.severity);
    const sb = severityToOps(b.severity);
    const ra = sa ? STATUS_META[sa].rank : 99;
    const rb = sb ? STATUS_META[sb].rank : 99;
    return ra - rb;
  });
  const primary = ordered[0];
  const evidence =
    primary?.description ||
    (primary?.category
      ? `Labeled category: ${primary.category}${primary.subcategory ? ` / ${primary.subcategory}` : ""}`
      : null);

  return {
    status,
    incidents: ordered,
    primary,
    severity: primary?.severity ? String(primary.severity) : null,
    reason: evidence || `${incidents.length} labeled incident(s)`,
    evidence,
  };
}

export function deviceTypeBucket(device: any): DeviceTypeFilter {
  const cls = String(device?.device_class || "").toLowerCase();
  const role = String(device?.role || "").toLowerCase();
  if (cls.includes("access_point") || role === "ap") return "ap";
  if (cls.includes("switch") || role === "access" || role === "aggregation" || role === "core") return "switch";
  if (cls.includes("router") || role.includes("wan")) return "router";
  if (cls.includes("gateway") || role.includes("gateway")) return "gateway";
  if (cls || role) return "other";
  return "other";
}

export function deviceTypeLabel(device: any): string {
  return String(device?.device_class || device?.role || "unknown");
}

export function neighborIds(topology: any, deviceId: string): Set<string> {
  const out = new Set<string>();
  for (const l of topology?.links || []) {
    const s = String(l._source || "");
    const t = String(l._target || "");
    if (s === deviceId && t) out.add(t);
    if (t === deviceId && s) out.add(s);
  }
  return out;
}
