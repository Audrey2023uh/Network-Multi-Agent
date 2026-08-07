import { Link, NavLink } from "react-router-dom";
import {
  ChartBarIcon,
  CircleStackIcon,
  CommandLineIcon,
  CpuChipIcon,
  DocumentTextIcon,
  HomeIcon,
  MapIcon,
  MoonIcon,
  ShareIcon,
  SparklesIcon,
  SunIcon,
} from "@heroicons/react/24/outline";
import { useApp } from "../lib/store";

const nav = [
  { to: "/", label: "Home", icon: HomeIcon },
  { to: "/architecture", label: "Architecture", icon: ShareIcon },
  { to: "/pipeline", label: "Pipeline", icon: CpuChipIcon },
  { to: "/benchmark", label: "Benchmark", icon: CircleStackIcon },
  { to: "/models", label: "Models", icon: ChartBarIcon },
  { to: "/figures", label: "Figures", icon: DocumentTextIcon },
  { to: "/results", label: "Results", icon: SparklesIcon },
  { to: "/shap", label: "TreeSHAP", icon: MapIcon },
  { to: "/repro", label: "Reproducibility", icon: CommandLineIcon },
  { to: "/docs", label: "Documentation", icon: DocumentTextIcon },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const { seed, setSeed, dark, setDark, topology, aggregate, loading, error, index } = useApp();
  const seeds = (index?.seeds?.map((s: any) => s.id) as string[]) || [
    "v1.1.0-INST",
    "seed101",
    "seed202",
    "seed303",
    "seed404",
    "seed505",
  ];

  return (
    <div className={dark ? "dark" : "light"}>
      <div
        className={`min-h-screen text-noc-text ${
          dark
            ? "bg-gradient-to-br from-[#070B14] via-noc-bg to-[#0E1A2E]"
            : "bg-gradient-to-br from-slate-100 via-white to-slate-200 text-slate-900"
        }`}
      >
        <header className="sticky top-0 z-40 border-b border-noc-border/80 bg-noc-bg/85 backdrop-blur-xl">
          <div className="mx-auto flex max-w-[1600px] items-center gap-4 px-4 py-3">
            <Link to="/" className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-noc-accent/20 text-sm font-bold text-noc-accent">
                ECN
              </div>
              <div>
                <div className="text-sm font-semibold tracking-wide">ECNetBench NOC</div>
                <div className="text-[11px] text-noc-muted">Historical benchmark replay · ECN-v3</div>
              </div>
            </Link>
            <div className="ml-auto flex items-center gap-3">
              <label className="text-xs text-noc-muted">Seed</label>
              <select
                className="rounded-lg border border-noc-border bg-noc-panel px-3 py-1.5 text-sm"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
              >
                {seeds.map((s) => (
                  <option key={s} value={s}>
                    {s}
                    {topology && seed === s ? ` · ${topology.n_devices}d/${topology.n_links}l` : ""}
                  </option>
                ))}
              </select>
              <button
                className="rounded-lg border border-noc-border p-2 hover:bg-white/5"
                onClick={() => setDark(!dark)}
                aria-label="Toggle theme"
              >
                {dark ? <SunIcon className="h-4 w-4" /> : <MoonIcon className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <nav className="mx-auto flex max-w-[1600px] gap-1 overflow-x-auto px-4 pb-2">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium ${
                    isActive ? "bg-noc-accent/20 text-white" : "text-noc-muted hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                <item.icon className="h-3.5 w-3.5" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        {(loading || error) && (
          <div className="mx-auto max-w-[1600px] px-4 pt-3 text-xs">
            {loading ? <span className="text-noc-muted">Loading seed artifacts…</span> : null}
            {error ? <span className="text-red-400">Data load error: {error}</span> : null}
          </div>
        )}

        <main className="mx-auto max-w-[1600px] px-4 py-6">{children}</main>

        <footer className="border-t border-noc-border/60 px-4 py-4 text-center text-xs text-noc-muted">
          {aggregate?.disclaimer ||
            "Historical/replay visualization of verified ECNetBench artifacts. Not a live production deployment."}
          {" · "}
          <a className="text-noc-accent underline" href="https://github.com/Audrey2023uh/Network-Multi-Agent">
            GitHub
          </a>
          {" · Data provenance: DATA_PROVENANCE.md"}
        </footer>
      </div>
    </div>
  );
}
