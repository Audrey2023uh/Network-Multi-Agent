import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape from "cytoscape";
// @ts-expect-error no types
import fcose from "cytoscape-fcose";
import type { TopologyPayload } from "../types";
import {
  deriveDeviceOps,
  deviceTypeBucket,
  neighborIds,
  STATUS_META,
  type DeviceTypeFilter,
  type OpsStatus,
} from "../lib/deviceStatus";

cytoscape.use(fcose);

export function TopologyMap({
  topology,
  onSelect,
  selectedDeviceId,
  statusFilter,
  typeFilter,
}: {
  topology: TopologyPayload;
  onSelect: (payload: { kind: "device" | "link"; data: any }) => void;
  selectedDeviceId?: string | null;
  statusFilter?: OpsStatus | "all";
  typeFilter?: DeviceTypeFilter;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [tip, setTip] = useState<{
    x: number;
    y: number;
    hostname: string;
    deviceType: string;
    status: string;
    severity: string;
    incidents: number;
    issue: string;
    mgmtIp: string;
  } | null>(null);

  const statusById = useMemo(() => {
    const m = new Map<string, ReturnType<typeof deriveDeviceOps>>();
    for (const d of topology.devices || []) {
      m.set(String(d.device_id), deriveDeviceOps(topology, d));
    }
    return m;
  }, [topology]);

  useEffect(() => {
    if (!ref.current) return;
    const elements: cytoscape.ElementDefinition[] = [];
    for (const d of topology.devices) {
      const id = String(d.device_id);
      const ops = statusById.get(id)!;
      const meta = STATUS_META[ops.status];
      elements.push({
        data: {
          id,
          label: `${meta.icon} ${d.hostname || id.slice(0, 8)}`,
          status: ops.status,
          statusLabel: meta.label,
          color: meta.color,
          border: meta.border,
          typeBucket: deviceTypeBucket(d),
          raw: d,
          ops,
        },
      });
    }
    for (const l of topology.links) {
      const s = l._source;
      const t = l._target;
      if (!s || !t) continue;
      elements.push({
        data: {
          id: String(l.link_id || `${s}-${t}`),
          source: String(s),
          target: String(t),
          raw: l,
        },
      });
    }

    if (cyRef.current) cyRef.current.destroy();
    const cy = cytoscape({
      container: ref.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "background-color": "data(color)",
            color: "#E8EEF4",
            "font-size": 9,
            "text-valign": "bottom",
            "text-margin-y": 6,
            width: 30,
            height: 30,
            "border-width": 3,
            "border-color": "data(border)",
            "text-outline-width": 2,
            "text-outline-color": "#0A101C",
          },
        },
        {
          selector: "node[status = 'critical']",
          style: { shape: "diamond", width: 34, height: 34 },
        },
        {
          selector: "node[status = 'degraded']",
          style: { shape: "triangle", width: 32, height: 32 },
        },
        {
          selector: "node[status = 'warning']",
          style: { shape: "round-rectangle", width: 30, height: 26 },
        },
        {
          selector: "node[status = 'healthy']",
          style: { shape: "ellipse" },
        },
        {
          selector: "node[status = 'unknown']",
          style: { shape: "octagon", "background-opacity": 0.7 },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#2A3A55",
            "curve-style": "bezier",
          },
        },
        {
          selector: "node.selected-device",
          style: {
            "border-color": "#38BDF8",
            "border-width": 5,
            "overlay-color": "#38BDF8",
            "overlay-opacity": 0.15,
            "overlay-padding": 6,
          },
        },
        {
          selector: "node.neighbor-device",
          style: {
            "border-color": "#7DD3FC",
            "border-width": 4,
            "line-color": "#38BDF8",
          },
        },
        {
          selector: "edge.neighbor-edge",
          style: {
            width: 3,
            "line-color": "#38BDF8",
          },
        },
        {
          selector: "node.filtered-out",
          style: {
            opacity: 0.12,
            "text-opacity": 0.15,
          },
        },
        {
          selector: "edge.filtered-out",
          style: { opacity: 0.08 },
        },
      ],
      layout: { name: "fcose", animate: false, padding: 30 } as any,
    });

    cy.on("tap", "node", (evt) => {
      const raw = evt.target.data("raw");
      onSelect({ kind: "device", data: raw });
    });
    cy.on("tap", "edge", (evt) => onSelect({ kind: "link", data: evt.target.data("raw") }));

    cy.on("mouseover", "node", (evt) => {
      const n = evt.target;
      const raw = n.data("raw");
      const ops = n.data("ops") as ReturnType<typeof deriveDeviceOps>;
      const rp = n.renderedBoundingBox();
      setTip({
        x: (rp.x1 + rp.x2) / 2,
        y: rp.y1 - 8,
        hostname: String(raw.hostname || raw.device_id),
        deviceType: String(raw.device_class || raw.role || "—"),
        status: STATUS_META[ops.status].label,
        severity: ops.severity || "—",
        incidents: ops.incidents.length,
        issue: ops.evidence || ops.reason,
        mgmtIp: String(raw.mgmt_ip || "—"),
      });
    });
    cy.on("mouseout", "node", () => setTip(null));

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [topology, statusById, onSelect]);

  // Selection + neighbor highlight + filters
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.batch(() => {
      cy.nodes().removeClass("selected-device neighbor-device filtered-out");
      cy.edges().removeClass("neighbor-edge filtered-out");

      const sf = statusFilter || "all";
      const tf = typeFilter || "all";
      cy.nodes().forEach((n) => {
        const st = n.data("status") as OpsStatus;
        const tb = n.data("typeBucket") as DeviceTypeFilter;
        const hide = (sf !== "all" && st !== sf) || (tf !== "all" && tb !== tf);
        if (hide) n.addClass("filtered-out");
      });
      cy.edges().forEach((e) => {
        if (e.source().hasClass("filtered-out") || e.target().hasClass("filtered-out")) {
          e.addClass("filtered-out");
        }
      });

      if (selectedDeviceId) {
        const node = cy.getElementById(selectedDeviceId);
        if (node.nonempty()) {
          node.addClass("selected-device");
          const nbrs = neighborIds(topology, selectedDeviceId);
          nbrs.forEach((nid) => {
            const nn = cy.getElementById(nid);
            if (nn.nonempty()) nn.addClass("neighbor-device");
          });
          cy.edges().forEach((e) => {
            const s = e.source().id();
            const t = e.target().id();
            if (
              (s === selectedDeviceId && nbrs.has(t)) ||
              (t === selectedDeviceId && nbrs.has(s))
            ) {
              e.addClass("neighbor-edge");
            }
          });
          cy.animate({ fit: { eles: node.closedNeighborhood(), padding: 80 }, duration: 250 });
        }
      }
    });
  }, [selectedDeviceId, statusFilter, typeFilter, topology]);

  return (
    <div className="relative h-[520px] w-full rounded-xl border border-noc-border bg-[#0A101C]">
      <div ref={ref} className="h-full w-full" />
      {tip ? (
        <div
          className="pointer-events-none absolute z-20 max-w-xs -translate-x-1/2 -translate-y-full rounded-lg border border-noc-border bg-noc-bg/95 p-2 text-[11px] shadow-xl"
          style={{ left: tip.x, top: tip.y }}
        >
          <div className="font-semibold text-white">{tip.hostname}</div>
          <div className="text-noc-muted">Type: {tip.deviceType}</div>
          <div>
            Status: <span className="font-medium text-noc-accent">{tip.status}</span>
          </div>
          <div>Severity: {tip.severity}</div>
          <div>Incidents: {tip.incidents}</div>
          <div className="mt-1 text-noc-muted">Issue: {tip.issue}</div>
          <div className="font-mono">mgmt_ip: {tip.mgmtIp}</div>
        </div>
      ) : null}
    </div>
  );
}
