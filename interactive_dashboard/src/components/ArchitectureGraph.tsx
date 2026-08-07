import { useEffect, useRef } from "react";
import * as d3 from "d3";

/** D3 module graph for architecture overview (layout only; labels from architecture.json). */
export function ArchitectureGraph({
  modules,
  onSelect,
}: {
  modules: { id: string; title: string }[];
  onSelect: (id: string) => void;
}) {
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!ref.current || !modules.length) return;
    const width = ref.current.clientWidth || 640;
    const height = 280;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const nodes = modules.map((m) => ({ ...m }));
    const links = modules.slice(0, -1).map((m, i) => ({ source: m.id, target: modules[i + 1].id }));

    const sim = d3
      .forceSimulation(nodes as any)
      .force(
        "link",
        d3
          .forceLink(links as any)
          .id((d: any) => d.id)
          .distance(90),
      )
      .force("charge", d3.forceManyBody().strength(-220))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append("g")
      .attr("stroke", "#2A3A55")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", 2);

    const node = svg
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .style("cursor", "pointer")
      .on("click", (_e, d) => onSelect(d.id));

    node.append("circle").attr("r", 18).attr("fill", "#1F7A8C").attr("stroke", "#0B1220").attr("stroke-width", 2);
    node
      .append("text")
      .text((d) => d.title.split(" ")[0])
      .attr("text-anchor", "middle")
      .attr("dy", 32)
      .attr("fill", "#E8EEF4")
      .attr("font-size", 10);

    sim.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);
      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      sim.stop();
    };
  }, [modules, onSelect]);

  return <svg ref={ref} className="h-[280px] w-full" role="img" aria-label="ECN module graph" />;
}
