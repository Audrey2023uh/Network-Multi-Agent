import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { AppCtx } from "./lib/store";
import { loadAggregate, loadArchitecture, loadIndex, loadMetrics, loadTopology } from "./lib/data";
import type { AggregatePayload, SeedMetrics, TopologyPayload } from "./types";
import { HomePage } from "./pages/HomePage";
import { ArchitecturePage } from "./pages/ArchitecturePage";
import { PipelinePage } from "./pages/PipelinePage";
import { BenchmarkPage } from "./pages/BenchmarkPage";
import { ModelsPage } from "./pages/ModelsPage";
import { FiguresPage } from "./pages/FiguresPage";
import { ResultsPage } from "./pages/ResultsPage";
import { TreeShapPage } from "./pages/TreeShapPage";
import { ReproPage } from "./pages/ReproPage";
import { DocsPage } from "./pages/DocsPage";

function AppProvider({ children }: { children: React.ReactNode }) {
  const [seed, setSeed] = useState("seed101");
  const [dark, setDark] = useState(true);
  const [aggregate, setAggregate] = useState<AggregatePayload | null>(null);
  const [architecture, setArchitecture] = useState<any>(null);
  const [index, setIndex] = useState<any>(null);
  const [topology, setTopology] = useState<TopologyPayload | null>(null);
  const [metrics, setMetrics] = useState<SeedMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [agg, arch, idx] = await Promise.all([loadAggregate(), loadArchitecture(), loadIndex()]);
        if (cancelled) return;
        setAggregate(agg);
        setArchitecture(arch);
        setIndex(idx);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const [topo, met] = await Promise.all([loadTopology(seed), loadMetrics(seed)]);
        if (cancelled) return;
        setTopology(topo);
        setMetrics(met);
        setError(null);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [seed]);

  const value = useMemo(
    () => ({
      seed,
      setSeed,
      dark,
      setDark,
      aggregate,
      topology,
      metrics,
      architecture,
      index,
      loading,
      error,
    }),
    [seed, dark, aggregate, topology, metrics, architecture, index, loading, error],
  );

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "") || "/"}>
      <AppProvider>
        <Shell>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/architecture" element={<ArchitecturePage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/benchmark" element={<BenchmarkPage />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/figures" element={<FiguresPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/shap" element={<TreeShapPage />} />
            <Route path="/repro" element={<ReproPage />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Shell>
      </AppProvider>
    </BrowserRouter>
  );
}
