import { useEffect, useState } from "react";
import { connectLiveState, fetchState } from "./api/client";
import { asCurrent, type State } from "./api/types";
import { ProblemHeader } from "./components/ProblemHeader";
import { Roadmap } from "./components/Roadmap";
import { StatusFeed } from "./components/StatusFeed";
import { SpecPanel } from "./components/SpecPanel";
import { Bom } from "./components/Bom";
import { Research } from "./components/Research";
import { Feedback } from "./components/Feedback";
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
    return <div className="loading">connecting to schema-forge…</div>;
  }
  const current = asCurrent(state.current);
  const status = current?.status ?? "none";
  const rev = state.updated_at.replace("T", " ").replace("Z", "");
  const passed = current?.assertions.filter((a) => a.passed).length ?? 0;
  const total = current?.assertions.length ?? 0;

  return (
    <div className="sheet">
      <header className="masthead">
        <div className="wordmark">
          <b>
            SCHEMA<s>·</s>FORGE
          </b>
          <span>schematic design harness</span>
        </div>
        <div className="status-line">
          <span className={`live-dot ${connected ? "" : "off"}`}>
            {connected ? "live" : "offline"}
          </span>
          <span>rev {rev} utc</span>
        </div>
      </header>

      <ProblemHeader
        problem={state.problem}
        initialized={state.initialized}
        current={current}
      />

      <main className="layout">
        <div className="band band-top">
          <div className="stack">
            <Research research={state.research} />
            <div className="hero">
              <SchematicView current={current} />
            </div>
          </div>
          <div className="stack">
            <SpecPanel current={current} spec={state.spec} />
            <Bom components={state.components} />
            <Roadmap roadmap={state.roadmap} />
          </div>
        </div>
        <div className="signals">
          <SignalPlots plots={current?.plots ?? []} />
        </div>
        <div className="band band-bottom">
          <StatusFeed log={state.log} />
          <Feedback feedback={state.feedback} />
        </div>
        <ErrorReports current={current} />
      </main>

      <footer className="footer-tb">
        <div>
          <span className="k">Drawn by</span>
          <span className="v">schema-forge harness</span>
        </div>
        <div>
          <span className="k">Verified by</span>
          <span className="v">ngspice · spec assertions</span>
        </div>
        <div>
          <span className="k">Spec</span>
          <span className={`v t-${status}`}>
            {current ? `${passed} / ${total} pass` : "—"}
          </span>
        </div>
        <div>
          <span className="k">Netlist</span>
          <span className="v">{current?.netlist ?? "—"}</span>
        </div>
        <div>
          <span className="k">Rev</span>
          <span className="v">{rev} utc</span>
        </div>
      </footer>
    </div>
  );
}
