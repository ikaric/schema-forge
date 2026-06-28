import { useEffect, useState } from "react";
import { connectLiveState, fetchState } from "./api/client";
import { asCurrent, type State } from "./api/types";
import { ProblemHeader } from "./components/ProblemHeader";
import { Roadmap } from "./components/Roadmap";
import { StatusFeed } from "./components/StatusFeed";
import { SpecPanel } from "./components/SpecPanel";
import { SchematicView } from "./components/SchematicView";
import { SignalPlots } from "./components/SignalPlots";
import { ErrorReports } from "./components/ErrorReports";

export default function App() {
  const [state, setState] = useState<State | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    fetchState().then(setState).catch(() => {});
    return connectLiveState(setState, setConnected);
  }, []);

  if (!state) {
    return <div className="loading">Connecting to schema-forge…</div>;
  }
  const current = asCurrent(state.current);
  const updated = state.updated_at.replace("T", " ").replace("Z", " UTC");

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="spark" />
          schema-forge
        </div>
        <div className="top-right">
          {current && (
            <span className={`badge status-${current.status}`}>
              {current.status}
            </span>
          )}
          <span className={`conn ${connected ? "on" : "off"}`}>
            {connected ? "live" : "offline"}
          </span>
          <span className="muted small">updated {updated}</span>
        </div>
      </header>

      <ProblemHeader
        problem={state.problem}
        initialized={state.initialized}
        current={current}
      />

      <main className="grid">
        <div className="col-main">
          <SchematicView current={current} />
          <SignalPlots plots={current?.plots ?? []} />
          <SpecPanel current={current} spec={state.spec} />
          <ErrorReports current={current} />
        </div>
        <aside className="col-side">
          <Roadmap roadmap={state.roadmap} />
          <StatusFeed log={state.log} />
        </aside>
      </main>
    </div>
  );
}
