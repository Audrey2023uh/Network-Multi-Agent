import type { AggregatePayload, SeedMetrics, TopologyPayload } from "../types";

const BASE = import.meta.env.BASE_URL;

async function getJson<T>(path: string): Promise<T> {
  const url = `${BASE}${path.replace(/^\//, "")}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`);
  return res.json() as Promise<T>;
}

export async function loadIndex() {
  return getJson<{
    seeds: {
      id: string;
      topology: string;
      metrics: string;
      n_devices: number;
      n_links: number;
      label?: string;
      source?: string;
      available?: boolean;
    }[];
    mode: string;
    generated_at?: string;
    generated_from?: string;
  }>("data/index.json");
}

export async function loadAggregate() {
  return getJson<AggregatePayload>("data/aggregate.json");
}

export async function loadArchitecture() {
  return getJson<any>("data/architecture.json");
}

export async function loadTopology(seed: string) {
  return getJson<TopologyPayload>(`data/topology_${seed}.json`);
}

export async function loadMetrics(seed: string) {
  return getJson<SeedMetrics>(`data/metrics_${seed}.json`);
}

export function fmt(n: number | null | undefined, digits = 4): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return Number(n).toFixed(digits);
}
