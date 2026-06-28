import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import { artifactUrl } from "../api/client";

type ReactArgs = Parameters<typeof Plotly.react>;

function PlotFigure({ url }: { url: string }) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    let active = true;
    const el = ref.current;
    fetch(url)
      .then((r) => r.json())
      .then((fig: { data: unknown; layout: unknown }) => {
        if (!active || !el) return;
        void Plotly.react(
          el,
          fig.data as ReactArgs[1],
          { autosize: true, ...(fig.layout as object) } as ReactArgs[2],
          { responsive: true, displaylogo: false } as ReactArgs[3],
        );
      })
      .catch(() => {});
    return () => {
      active = false;
      if (el) Plotly.purge(el);
    };
  }, [url]);
  return <div className="plot" ref={ref} />;
}

export function SignalPlots({ plots }: { plots: string[] }) {
  if (!plots || plots.length === 0) {
    return (
      <section className="card">
        <h3>Signals</h3>
        <p className="muted">No simulation plots yet.</p>
      </section>
    );
  }
  return (
    <section className="card">
      <h3>Signals</h3>
      <div className="plots">
        {plots.map((p) => (
          <PlotFigure key={p} url={artifactUrl(p)} />
        ))}
      </div>
    </section>
  );
}
