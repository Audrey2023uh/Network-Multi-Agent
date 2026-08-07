import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-basic-dist-min";
import type { Data, Layout } from "plotly.js";

const Plot = createPlotlyComponent(Plotly);

const layoutBase: Partial<Layout> = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#E8EEF4", family: "IBM Plex Sans" },
  margin: { t: 40, r: 20, b: 50, l: 55 },
  legend: { bgcolor: "rgba(0,0,0,0)" },
};

export function Chart({
  title,
  data,
  layout,
  source,
}: {
  title: string;
  data: Data[];
  layout?: Partial<Layout>;
  source?: string;
}) {
  return (
    <div className="noc-card p-3">
      <div className="mb-1 flex items-center justify-between gap-2 px-1">
        <h3 className="text-sm font-semibold">{title}</h3>
        {source ? <span className="noc-chip">Source: {source}</span> : null}
      </div>
      <Plot
        data={data}
        layout={{ ...layoutBase, title: undefined, ...layout }}
        config={{ responsive: true, displaylogo: false, toImageButtonOptions: { format: "png", filename: title } }}
        style={{ width: "100%", height: 360 }}
        useResizeHandler
      />
    </div>
  );
}
