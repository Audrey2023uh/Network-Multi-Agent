import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
// @ts-expect-error no types
import fcose from "cytoscape-fcose";
import type { TopologyPayload } from "../types";

cytoscape.use(fcose);

const ROLE_COLOR: Record<string, string> = {
  core: "#C47B2B",
  aggregation: "#1F7A8C",
  access: "#3D8B6E",
  wan: "#7C5CBF",
  ap: "#4A90A4",
};

export function TopologyMap({
  topology,
  onSelect,
}: {
  topology: TopologyPayload;
  onSelect: (payload: { kind: "device" | "link"; data: any }) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const elements: cytoscape.ElementDefinition[] = [];
    for (const d of topology.devices) {
      const id = String(d.device_id);
      const role = String(d.role || "unknown");
      elements.push({
        data: {
          id,
          label: d.hostname || id.slice(0, 8),
          role,
          raw: d,
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
            "background-color": (ele: any) => ROLE_COLOR[ele.data("role")] || "#4A5568",
            color: "#E8EEF4",
            "font-size": 9,
            "text-valign": "bottom",
            "text-margin-y": 6,
            width: 28,
            height: 28,
            "border-width": 2,
            "border-color": "#0B1220",
          },
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
          selector: ":selected",
          style: {
            "border-color": "#E8EEF4",
            "line-color": "#1F7A8C",
          },
        },
      ],
      layout: { name: "fcose", animate: false, padding: 30 } as any,
    });
    cy.on("tap", "node", (evt) => onSelect({ kind: "device", data: evt.target.data("raw") }));
    cy.on("tap", "edge", (evt) => onSelect({ kind: "link", data: evt.target.data("raw") }));
    cyRef.current = cy;
    return () => {
      cy.destroy();
    };
  }, [topology, onSelect]);

  return <div ref={ref} className="h-[520px] w-full rounded-xl border border-noc-border bg-[#0A101C]" />;
}
