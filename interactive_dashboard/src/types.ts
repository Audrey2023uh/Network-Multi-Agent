export type SeedId =
  | "v1.1.0-INST"
  | "seed101"
  | "seed202"
  | "seed303"
  | "seed404"
  | "seed505";

export interface Provenance {
  source: string;
  field?: string;
}

export interface MetricBlock {
  mean?: number | null;
  std?: number | null;
  ci95?: number[] | null;
  n?: number | null;
}

export interface ModelRow {
  id: string;
  label: string;
  T1_auprc?: MetricBlock | null;
  T1_roc_auc?: MetricBlock | null;
  T2_auprc?: MetricBlock | null;
  T2_roc_auc?: MetricBlock | null;
  T1_brier?: MetricBlock | null;
  source: string;
  note?: string;
  T2_note?: string;
}

export interface AggregatePayload {
  models: ModelRow[];
  manuscript_ready: any;
  final_architecture: any;
  architecture_selection: any;
  calibration: any;
  stats: any;
  tables: Record<string, any[] | null>;
  checksums: any;
  disclaimer: string;
  runtime?: Record<string, any>;
  traceability?: any;
}

export interface TopologyPayload {
  seed: string;
  available: boolean;
  source_db: string;
  n_devices: number;
  n_links: number;
  n_interfaces: number;
  n_incidents: number;
  time_range: { min: string; max: string; column: string } | null;
  schema: { name: string; type: string }[];
  devices: Record<string, any>[];
  links: Record<string, any>[];
  interfaces_by_device: Record<string, Record<string, any>[]>;
  incidents: Record<string, any>[];
  telemetry_sample: Record<string, any>[];
  note: string;
}

export interface SeedMetrics {
  seed: string;
  available: boolean;
  source: string;
  T1: Record<string, any>;
  T2: Record<string, any>;
  T3: Record<string, any>;
  curves: Record<string, any>;
  shap: any;
  rca?: any;
  computational?: any;
}
