import { Link, NavLink } from "react-router-dom";
import {
  ChartBarIcon,
  CircleStackIcon,
  ClipboardDocumentCheckIcon,
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
import { ReplayBanner } from "./ReplayBanner";

const nav: { to: string; label: string; icon: typeof HomeIcon; emphasize?: boolean }[] = [
  { to: "/", label: "Home", icon: HomeIcon },
  { to: "/runbook", label: "Runbook", icon: ClipboardDocumentCheckIcon, emphasize: true },
  { to: "/benchmark", label: "Benchmark", icon: CircleStackIcon },
  { to: "/architecture", label: "Architecture", icon: ShareIcon },
  { to: "/pipeline", label: "Pipeline", icon: CpuChipIcon },
  { to: "/models", label: "Models", icon: ChartBarIcon },
  { to: "/practical", label: "Practical Impact", icon: ChartBarIcon },
  { to: "/sensitivity", label: "Sensitivity", icon: SparklesIcon },
  { to: "/scalability", label: "Scalability", icon: CpuChipIcon },
  { to: "/ablation", label: "Ablation", icon: ShareIcon },
  { to: "/xai-validation", label: "XAI Validation", icon: MapIcon },
  { to: "/live-prototype", label: "Live Prototype", icon: CommandLineIcon },
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
              <label className="text-xs text-noc-muted" htmlFor="seed-select">
                Seed
              </label>
              <select
                id="seed-select"
                className="rounded-lg border border-noc-border bg-noc-panel px-3 py-1.5 text-sm"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                title="Select an ECNetBench evaluation seed"
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
                    isActive
                      ? "bg-noc-accent/20 text-white"
                      : item.emphasize
                        ? "border border-noc-accent/40 text-noc-accent hover:bg-noc-accent/10"
                        : "text-noc-muted hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                <item.icon className="h-3.5 w-3.5" />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <ReplayBanner compact />
        </header>

        {(loading || error) && (
          <div className="mx-auto max-w-[1600px] px-4 pt-3 text-xs">
            {loading ? <span className="text-noc-muted">Loading seed artifacts…</span> : null}
            {error ? <span className="text-red-400">Data load error: {error}</span> : null}
          </div>
        )}

        <main className="mx-auto max-w-[1600px] px-4 py-6">{children}</main>

        <footer className="border-t border-noc-border/60 px-4 py-5 text-center text-xs text-noc-muted">
          <div className="font-medium text-noc-text/80">ECNetBench / ECN-v3 Interactive NOC Dashboard</div>
          <div className="mt-1">Designed and developed by Audrey Rah</div>
          <div>Department of Electrical and Computer Engineering, University of Houston</div>
          <div className="mt-2">
            {aggregate?.disclaimer ||
              "Historical/replay visualization of verified ECNetBench artifacts. Not a live production deployment."}
          </div>
          <div className="mt-2">
            <a className="text-noc-accent underline" href="https://github.com/Audrey2023uh/Network-Multi-Agent">
              GitHub
            </a>
            {" · "}
            <a
              className="text-noc-accent underline"
              href="https://github.com/Audrey2023uh/Network-Multi-Agent/blob/main/interactive_dashboard/DATA_PROVENANCE.md"
            >
              DATA_PROVENANCE.md
            </a>
            {" · "}
            <a className="text-noc-accent underline" href="https://audrey2023uh.github.io/Network-Multi-Agent/">
              Live Pages
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}
