import { useEffect, useState } from "react";
import LZString from "lz-string";
import { artifactUrl } from "../api/client";
import type { CurrentResult } from "../api/types";

type Tab = "svg" | "circuitjs";

export function SchematicView({ current }: { current?: CurrentResult }) {
  const svg = current?.schematic?.svg;
  const cjs = current?.schematic?.circuitjs;
  const [tab, setTab] = useState<Tab>("svg");
  const [cjsText, setCjsText] = useState("");

  useEffect(() => {
    if (!cjs) {
      setCjsText("");
      return;
    }
    let active = true;
    fetch(artifactUrl(cjs))
      .then((r) => r.text())
      .then((t) => active && setCjsText(t))
      .catch(() => active && setCjsText(""));
    return () => {
      active = false;
    };
  }, [cjs]);

  if (!svg && !cjs) {
    return (
      <section className="card schematic">
        <h3>Schematic</h3>
        <p className="muted">No schematic yet — run a simulation.</p>
      </section>
    );
  }

  // Falstad CircuitJS loads an arbitrary circuit from a compressed URL param.
  const falstadUrl = cjsText
    ? `https://www.falstad.com/circuit/circuitjs.html?hideSidebar=true&running=true&ctz=${LZString.compressToEncodedURIComponent(
        cjsText,
      )}`
    : "";

  return (
    <section className="card schematic">
      <div className="tabs">
        <h3>Schematic</h3>
        <div className="tab-buttons">
          <button
            className={tab === "svg" ? "active" : ""}
            onClick={() => setTab("svg")}
          >
            Diagram
          </button>
          <button
            className={tab === "circuitjs" ? "active" : ""}
            onClick={() => setTab("circuitjs")}
          >
            Interactive
          </button>
        </div>
      </div>

      {tab === "svg" ? (
        svg ? (
          <img className="schematic-svg" src={artifactUrl(svg)} alt="schematic" />
        ) : (
          <p className="muted">No static diagram.</p>
        )
      ) : (
        <div className="circuitjs">
          {falstadUrl ? (
            <iframe
              title="CircuitJS"
              className="circuitjs-frame"
              src={falstadUrl}
            />
          ) : (
            <p className="muted">No interactive circuit.</p>
          )}
          <div className="circuitjs-actions">
            {falstadUrl && (
              <a href={falstadUrl} target="_blank" rel="noreferrer">
                Open in CircuitJS ↗
              </a>
            )}
            <details>
              <summary>CircuitJS source</summary>
              <pre className="cjs-src">{cjsText}</pre>
            </details>
          </div>
        </div>
      )}
    </section>
  );
}
