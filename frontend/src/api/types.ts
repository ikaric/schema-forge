// Mirrors the rollup returned by schema_forge.state.reader.build_state.

export interface Problem {
  title: string;
  domain: string;
  tier: string;
  statement: string;
}

export interface SpecAssertion {
  id: string;
  measure: string;
  op: string;
  target: number | number[];
  unit: string;
  desc: string;
  tol: number | null;
}

export interface Spec {
  title: string;
  analyses: Record<string, unknown>;
  assertions: SpecAssertion[];
}

export interface AssertionResult {
  id: string;
  passed: boolean;
  op: string;
  measured: number | null;
  target: number | number[];
  unit: string;
  desc: string;
  message: string;
}

export type Status = "verified" | "converged" | "failed";

export interface CurrentResult {
  netlist: string;
  status: Status;
  converged: boolean;
  measured: Record<string, number>;
  assertions: AssertionResult[];
  errors: string[];
  warnings: string[];
  schematic: { svg?: string; circuitjs?: string };
  plots: string[];
  summary: string;
  timestamp: string;
}

export interface RoadmapItem {
  text: string;
  done: boolean;
}

export interface Roadmap {
  subgoals: RoadmapItem[];
  vectors: RoadmapItem[];
  progress: { done: number; total: number };
}

export interface LogEntry {
  ts: string;
  source: string;
  level: string;
  message: string;
}

export interface Component {
  ref: string;
  kind: string;
  type: string;
  value: string;
  nodes: string[];
}

export interface FeedbackNote {
  from: string;
  msg: string;
  status: string;
  state: "open" | "done" | "planned";
}

export interface State {
  initialized: boolean;
  problem: Problem;
  spec: Spec | null;
  roadmap: Roadmap;
  log: LogEntry[];
  current: CurrentResult | Record<string, never>;
  components: Component[];
  research: string;
  feedback: FeedbackNote[];
  report_present: boolean;
  updated_at: string;
}

export function asCurrent(
  current: State["current"],
): CurrentResult | undefined {
  return "status" in current ? (current as CurrentResult) : undefined;
}
