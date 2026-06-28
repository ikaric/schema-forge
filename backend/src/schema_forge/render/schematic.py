"""Render a SPICE netlist to a schematic: a clean SVG and a CircuitJS string.

Two views, per the project's design choice:

* **SchemDraw SVG** — a clean static diagram (the deliverable view). We place
  real schematic symbols on a grid with net labels; if SchemDraw is unavailable
  or the layout raises, we fall back to a hand-built SVG "summary card" so a
  valid SVG is *always* produced.
* **CircuitJS string** — an interactive, draggable schematic for the frontend
  iframe. Auto-generated with a deterministic matrix layout (nets are horizontal
  rails, two-terminal devices are vertical rungs). A netlist may override this
  with a hand-authored block between ``* @circuitjs-begin`` / ``* @circuitjs-end``
  comment markers (used by curated examples for a polished look).
"""

from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path

from schema_forge.netlist import Circuit, parse_netlist
from schema_forge.units import parse_si

_GROUND_NETS = {"0", "gnd", "gnd!", "vss", "agnd"}

_EMBED_RE = re.compile(
    r"^\*\s*@circuitjs-begin\s*$(.*?)^\*\s*@circuitjs-end\s*$",
    re.MULTILINE | re.DOTALL,
)


# --------------------------------------------------------------------------- #
# CircuitJS
# --------------------------------------------------------------------------- #
def extract_embedded_circuitjs(netlist_text: str) -> str | None:
    """Return a hand-authored CircuitJS block embedded in the netlist, if any."""
    m = _EMBED_RE.search(netlist_text)
    if not m:
        return None
    lines = []
    for line in m.group(1).splitlines():
        stripped = line.lstrip()
        if stripped.startswith("*"):
            stripped = stripped[1:]
            if stripped.startswith(" "):
                stripped = stripped[1:]
        if stripped.strip():
            lines.append(stripped)
    return "\n".join(lines) + "\n" if lines else None


def _cjs_component(
    kind: str, value: float | None, x1: int, y1: int, x2: int, y2: int
) -> str | None:
    if kind == "R":
        return f"r {x1} {y1} {x2} {y2} 0 {value or 1000}"
    if kind == "C":
        return f"c {x1} {y1} {x2} {y2} 0 {value or 1e-6} 0 0.001"
    if kind == "L":
        return f"l {x1} {y1} {x2} {y2} 0 {value or 1e-3} 0 0.001"
    if kind == "D":
        return f"d {x1} {y1} {x2} {y2} 2 default"
    if kind == "V":
        return f"v {x1} {y1} {x2} {y2} 0 0 40 {value or 5} 0 0 0.5"
    if kind == "I":
        return f"i {x1} {y1} {x2} {y2} 0 {value or 0.001}"
    return None


def to_circuitjs(circuit: Circuit, embedded: str | None = None) -> str:
    """Translate *circuit* to a CircuitJS import string (matrix auto-layout)."""
    if embedded:
        return embedded

    nets = circuit.nodes
    non_ground = [n for n in nets if n.lower() not in _GROUND_NETS]
    ground = [n for n in nets if n.lower() in _GROUND_NETS]
    ordered = non_ground + ground
    net_y = {n: 96 + i * 64 for i, n in enumerate(ordered)}

    lines = ["$ 1 0.000005 10.2 50 5 50 5e-11"]
    x0, dx = 192, 96
    net_points: dict[str, list[tuple[int, int]]] = defaultdict(list)

    col = 0
    for el in circuit.elements:
        if len(el.nodes) < 2:
            continue
        a, b = el.nodes[0], el.nodes[1]
        x = x0 + col * dx
        ya, yb = net_y.get(a, 96), net_y.get(b, 96)
        comp = _cjs_component(el.kind, parse_si(el.value), x, ya, x, yb)
        if comp is None:
            continue
        lines.append(comp)
        net_points[a].append((x, ya))
        net_points[b].append((x, yb))
        col += 1

    # Horizontal rails wiring shared nets together.
    for pts in net_points.values():
        ordered_pts = sorted(set(pts))
        for (x1, y1), (x2, y2) in zip(ordered_pts, ordered_pts[1:], strict=False):
            lines.append(f"w {x1} {y1} {x2} {y2} 0")

    # Ground symbols on ground rails.
    for net in ground:
        if net_points.get(net):
            x, y = sorted(net_points[net])[0]
            lines.append(f"g {x} {y} {x} {y + 40} 0")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# SVG
# --------------------------------------------------------------------------- #
def _schemdraw_svg(circuit: Circuit) -> str:
    import schemdraw
    from schemdraw import elements as elm

    schemdraw.use("svg")
    symbols = {
        "R": elm.Resistor,
        "C": elm.Capacitor,
        "L": elm.Inductor,
        "D": elm.Diode,
        "V": elm.SourceV,
        "I": elm.SourceI,
    }
    per_row = 4
    d = schemdraw.Drawing()
    d.config(fontsize=11)
    for i, el in enumerate(circuit.elements):
        row, col = divmod(i, per_row)
        x, y = col * 4.5, -row * 3.0
        sym_cls = symbols.get(el.kind, elm.RBox)
        elem = sym_cls().right().at((x, y))
        label = el.name if not el.value else f"{el.name}\n{el.value}"
        elem.label(label, loc="top", fontsize=10)
        if len(el.nodes) >= 2:
            elem.label(el.nodes[0], loc="left", fontsize=8, color="#2563eb")
            elem.label(el.nodes[-1], loc="right", fontsize=8, color="#2563eb")
        d.add(elem)
    data = d.get_imagedata("svg")
    return data.decode("utf-8") if isinstance(data, bytes) else str(data)


def _card_svg(circuit: Circuit) -> str:
    """A dependency-free fallback: a clean component + net summary card."""
    by_kind: dict[str, list[str]] = defaultdict(list)
    kind_name = {
        "R": "Resistors",
        "C": "Capacitors",
        "L": "Inductors",
        "D": "Diodes",
        "V": "Sources",
        "I": "Sources",
        "Q": "Transistors",
        "M": "MOSFETs",
        "J": "JFETs",
        "X": "Subcircuits",
    }
    for el in circuit.elements:
        label = el.name + (f" = {el.value}" if el.value else "")
        nodes = " · ".join(el.nodes)
        by_kind[kind_name.get(el.kind, "Other")].append(f"{label}  ({nodes})")

    width = 760
    rows: list[str] = []
    y = 84
    for group, items in by_kind.items():
        rows.append(
            f'<text x="28" y="{y}" font-size="14" font-weight="600" '
            f'fill="#0f172a">{html.escape(group)}</text>'
        )
        y += 22
        for item in items:
            rows.append(
                f'<text x="40" y="{y}" font-size="13" font-family="monospace" '
                f'fill="#334155">{html.escape(item)}</text>'
            )
            y += 20
        y += 8
    height = max(y + 24, 160)
    title = html.escape(circuit.title or "Schematic")
    nets = html.escape(", ".join(circuit.nodes))
    body = "\n".join(rows)
    opening = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">'
    )
    return f"""{opening}
  <rect width="{width}" height="{height}" rx="12" fill="#f8fafc" stroke="#e2e8f0"/>
  <text x="28" y="40" font-size="18" font-weight="700" fill="#0f172a">{title}</text>
  <text x="28" y="60" font-size="12" fill="#64748b">Nets: {nets}</text>
  {body}
</svg>"""


def to_svg(circuit: Circuit) -> str:
    """Render *circuit* to an SVG string, never raising."""
    try:
        return _schemdraw_svg(circuit)
    except Exception:
        return _card_svg(circuit)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def render_schematic(
    netlist_path: str | Path, outdir: str | Path, stem: str
) -> dict[str, Path]:
    """Write ``<stem>.svg`` and ``<stem>.circuitjs``; return their paths."""
    netlist_path = Path(netlist_path)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    text = netlist_path.read_text(encoding="utf-8")
    circuit = parse_netlist(text)

    svg_path = outdir / f"{stem}.svg"
    cjs_path = outdir / f"{stem}.circuitjs"
    svg_path.write_text(to_svg(circuit), encoding="utf-8")
    cjs_path.write_text(
        to_circuitjs(circuit, extract_embedded_circuitjs(text)), encoding="utf-8"
    )
    return {"svg": svg_path, "circuitjs": cjs_path}
