import { createContext, useContext } from "react";
import type { AggregatePayload, SeedMetrics, TopologyPayload } from "../types";

export interface AppState {
  seed: string;
  setSeed: (s: string) => void;
  dark: boolean;
  setDark: (v: boolean) => void;
  aggregate: AggregatePayload | null;
  topology: TopologyPayload | null;
  metrics: SeedMetrics | null;
  architecture: any;
  index: any;
  loading: boolean;
  error: string | null;
}

export const AppCtx = createContext<AppState | null>(null);

export function useApp() {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp outside provider");
  return ctx;
}
