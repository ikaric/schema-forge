import type { Component } from "../api/types";

const SVG = {
  width: 30,
  height: 16,
  viewBox: "0 0 30 16",
  fill: "none",
  stroke: "#dcebfb",
  strokeWidth: 1.3,
  strokeLinejoin: "round" as const,
  strokeLinecap: "round" as const,
};

function Glyph({ kind }: { kind: string }) {
  switch (kind) {
    case "R":
      return (
        <svg {...SVG}>
          <path d="M0 8h6l1.5-4 3 8 3-8 3 8 1.5-4h6" />
        </svg>
      );
    case "C":
      return (
        <svg {...SVG}>
          <path d="M0 8h12M18 8h12M12 2v12M18 2v12" />
        </svg>
      );
    case "L":
      return (
        <svg {...SVG}>
          <path d="M0 8h5M25 8h5" />
          <path d="M5 8a2.5 2.5 0 015 0M10 8a2.5 2.5 0 015 0M15 8a2.5 2.5 0 015 0M20 8a2.5 2.5 0 015 0" />
        </svg>
      );
    case "D":
      return (
        <svg {...SVG}>
          <path d="M0 8h11M19 8h11M11 3l8 5-8 5zM19 3v10" />
        </svg>
      );
    case "Q":
    case "M":
    case "J":
      return (
        <svg {...SVG}>
          <circle cx="16" cy="8" r="6.5" />
          <path d="M2 8h7M11 4.5v7M11 7l5-3M11 9l5 3" />
        </svg>
      );
    case "V":
    case "I":
      return (
        <svg {...SVG}>
          <circle cx="15" cy="8" r="6.5" />
          <path d="M0 8h8.5M21.5 8h8.5M15 4.5v3M13.5 6h3M13.5 10h3" />
        </svg>
      );
    default:
      return (
        <svg {...SVG}>
          <rect x="6" y="3.5" width="18" height="9" />
          <path d="M0 8h6M24 8h6" />
        </svg>
      );
  }
}

export function Bom({ components }: { components: Component[] }) {
  if (!components || components.length === 0) return null;
  return (
    <section className="card">
      <h3>
        Components <span className="muted">{components.length} parts</span>
      </h3>
      <ul className="bom">
        {components.map((c) => (
          <li key={c.ref}>
            <span className="bom-sym">
              <Glyph kind={c.kind} />
            </span>
            <span className="bom-ref">{c.ref}</span>
            <span className="bom-val">{c.value || "—"}</span>
            <span className="bom-type muted">{c.type}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
