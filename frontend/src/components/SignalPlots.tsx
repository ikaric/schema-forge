import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import { artifactUrl } from "../api/client";

type ReactArgs = Parameters<typeof Plotly.react>;

// Blueprint plot theme: transparent field, cyan ink, faint white grid.
const AXIS = {
  gridcolor: "rgba(172,210,238,0.14)",
  zerolinecolor: "rgba(172,210,238,0.28)",
  linecolor: "rgba(172,210,238,0.28)",
  tickfont: { color: "#8db4d6" },
};

function themed(layout: Record<string, unknown>): Record<string, unknown> {
  const fl = layout as Record<string, any>;
  return {
    ...fl,
    paper_bgcolor: "#091d31",
    plot_bgcolor: "#091d31",
    font: { color: "#9db8d6", family: "IBM Plex Mono, monospace", size: 11 },
    colorway: ["#58c5f5", "#46d39a", "#f4b740", "#ff6b6b", "#dcebfb"],
    margin: { t: 32, r: 18, b: 40, l: 58 },
    title: { ...(fl.title ?? {}), font: { color: "#dcebfb", size: 13 } },
    xaxis: { ...(fl.xaxis ?? {}), ...AXIS },
    yaxis: { ...(fl.yaxis ?? {}), ...AXIS },
    ...(fl.yaxis2 ? { yaxis2: { ...fl.yaxis2, ...AXIS } } : {}),
  };
}

function PlotFigure({ url }: { url: string }) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    let active = true;
    const el = ref.current;
    fetch(url)
      .then((r) => r.json())
      .then((fig: { data: unknown; layout: Record<string, unknown> }) => {
        if (!active || !el) return;
        void Plotly.react(
          el,
          fig.data as ReactArgs[1],
          themed(fig.layout) as ReactArgs[2],
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
