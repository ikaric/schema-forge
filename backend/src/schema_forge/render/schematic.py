"""Render a SPICE netlist to a schematic: a clean SVG and a CircuitJS string.

Two views, per the project's design choice:

* **SchemDraw SVG** — a clean, *connected* static schematic (the deliverable
  view), drawn with real symbols and wires and derived entirely from the parsed
  netlist (so it cannot drift from the verified circuit). A topology-aware layout
  handles common-emitter BJT cascades (Fuzz Face / boost / preamp class); any
  netlist it doesn't recognise falls back to a hand-built component summary card,
  so a valid SVG is *always* produced.
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
from typing import Any

from schema_forge.netlist import Circuit, Element, parse_netlist
from schema_forge.units import parse_si

_GROUND_NETS = {"0", "gnd", "gnd!", "vss", "agnd"}


def _is_ground(node: str) -> bool:
    return node.lower() in _GROUND_NETS


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
def _find_supply(circuit: Circuit) -> str | None:
    """The positive DC rail: a non-signal V-source's non-ground node."""
    for v in circuit.by_kind("V"):
        if len(v.nodes) < 2:
            continue
        a, b = v.nodes[0], v.nodes[1]
        val = (v.value or "").lower()
        if any(w in val for w in ("sin", "pulse", "pwl")):
            continue  # a signal source, not the rail
        if _is_ground(b) and not _is_ground(a):
            return a
        if _is_ground(a) and not _is_ground(b):
            return b
    return None


def _r_between(circuit: Circuit, n1: str, n2: str) -> Element | None:
    want = {n1.lower(), n2.lower()}
    for r in circuit.by_kind("R"):
        if len(r.nodes) >= 2 and {r.nodes[0].lower(), r.nodes[1].lower()} == want:
            return r
    return None


def _cap_on(circuit: Circuit, node: str, used: set[str]) -> tuple[Element | None, str]:
    for cap in circuit.by_kind("C"):
        if cap.name in used or len(cap.nodes) < 2:
            continue
        lo = [n.lower() for n in cap.nodes]
        if node.lower() in lo:
            other = cap.nodes[1] if lo[0] == node.lower() else cap.nodes[0]
            return cap, other
    return None, ""


def _supply_voltage(circuit: Circuit) -> str:
    """DC rail magnitude as a label (e.g. '9 V'), parsed from the supply source."""
    for v in circuit.by_kind("V"):
        val = v.value or ""
        if any(w in val.lower() for w in ("sin", "pulse", "pwl")):
            continue
        m = re.search(r"(?:dc\s*)?(-?\d+(?:\.\d+)?)", val, re.IGNORECASE)
        if m:
            return f"{m.group(1)} V"
    return ""


# Blueprint palette. The schematic sits on its own darker "drawing board" so it
# reads as a distinct surface against the page's lighter blueprint field, with a
# faint grayish-white grid (deliberately quieter than the page grid).
_BP_FIELD = "#091d31"
_BP_INK = "#dceafa"
_BP_GRID = "#d4e2f0"


def _blueprint_frame(svg: str) -> str:
    """Lay a white-ink SchemDraw SVG onto a blueprint field with a fine grid."""
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', svg)
    minx, miny, w, h = m.groups() if m else ("0", "0", "1000", "600")
    overlay = (
        "<defs>"
        '<pattern id="bpg" width="22" height="22" patternUnits="userSpaceOnUse">'
        f'<path d="M22 0H0V22" fill="none" stroke="{_BP_GRID}" '
        'stroke-opacity="0.045" stroke-width="1"/></pattern>'
        '<pattern id="bpG" width="110" height="110" patternUnits="userSpaceOnUse">'
        f'<path d="M110 0H0V110" fill="none" stroke="{_BP_GRID}" '
        'stroke-opacity="0.085" stroke-width="1"/></pattern></defs>'
        f'<rect x="{minx}" y="{miny}" width="{w}" height="{h}" fill="{_BP_FIELD}"/>'
        f'<rect x="{minx}" y="{miny}" width="{w}" height="{h}" fill="url(#bpg)"/>'
        f'<rect x="{minx}" y="{miny}" width="{w}" height="{h}" fill="url(#bpG)"/>'
    )
    return re.sub(r"(<svg\b[^>]*>)", lambda mm: mm.group(1) + overlay, svg, count=1)


# Inherently branchy: each optional part (Rc, Re, Cin, Cout, Rload, feedback)
# adds a layout path. Kept as one routine so the drawing reads top-to-bottom.
def _cascade_svg(circuit: Circuit) -> str | None:  # noqa: C901
    """Draw a common-emitter BJT cascade (Fuzz Face / boost / preamp class).

    Returns ``None`` if the netlist isn't a recognisable CE cascade so the caller
    can fall back. The whole drawing is derived from the parsed netlist — symbols,
    values, and wiring all come from the verified circuit, never invented.
    """
    supply = _find_supply(circuit)
    bjts = circuit.by_kind("Q")
    if supply is None or not bjts:
        return None
    stages = []
    for q in bjts:
        if len(q.nodes) < 3:
            return None
        stages.append({"ref": q.name, "val": q.value or "",
                       "c": q.nodes[0], "b": q.nodes[1], "e": q.nodes[2]})
    collectors = {s["c"].lower() for s in stages}
    by_base = {s["b"].lower(): s for s in stages}
    firsts = [s for s in stages if s["b"].lower() not in collectors]
    if len(firsts) != 1:
        return None
    ordered = [firsts[0]]
    while True:
        nxt = by_base.get(ordered[-1]["c"].lower())
        if not nxt or nxt in ordered:
            break
        ordered.append(nxt)
    if len(ordered) != len(stages):
        return None  # not a simple chain

    import schemdraw
    from schemdraw import elements

    schemdraw.use("svg")
    elm: Any = elements  # schemdraw element constructors are partially untyped
    volt = _supply_voltage(circuit)
    used: set[str] = {s["ref"] for s in stages}
    vcc_y, gap = 7.0, 6.0
    d = schemdraw.Drawing(unit=2.0)
    d.config(fontsize=11, lw=1.6, color=_BP_INK)

    q_elem: dict[str, Any] = {}
    base_pt: dict[str, Any] = {}
    rail_pts: list[Any] = []
    for i, s in enumerate(ordered):
        x = 2 + i * gap
        q = elm.BjtNpn(circle=True).anchor("base").at((x, 3)).label(
            f"{s['ref']}\n{s['val']}", "right", ofst=(0.1, -0.6))
        d += q
        q_elem[s["ref"]] = q
        base_pt[s["b"].lower()] = q.base
        rc = _r_between(circuit, s["c"], supply)
        if rc:
            used.add(rc.name)
            d += elm.Resistor().at(q.collector).toy(vcc_y).label(
                f"{rc.name}\n{rc.value}"
            )
        else:
            d += elm.Line().at(q.collector).toy(vcc_y)
        rail_pts.append(d.here)
        if _is_ground(s["e"]):
            d += elm.Line().at(q.emitter).toy(0.0)
            d += elm.Ground()
        else:
            re_ = _r_between(circuit, s["e"], "0") or _r_between(circuit, s["e"], "gnd")
            if re_:
                used.add(re_.name)
                d += elm.Resistor().at(q.emitter).toy(0.6).label(
                    f"{re_.name}\n{re_.value}"
                )
                d += elm.Line().toy(0.0)
                d += elm.Ground()

    # inter-stage wiring: collector[i] -> base[i+1]
    for i in range(len(ordered) - 1):
        d += elm.Wire("-|").at(q_elem[ordered[i]["ref"]].collector).to(
            q_elem[ordered[i + 1]["ref"]].base)

    # Vcc rail across the collector resistor tops + battery on the far left
    rail_label = (
        f"+{volt}" if volt
        else ("+V" if supply.lower() in {"vcc", "vdd", "v+"} else f"+{supply}")
    )
    d += elm.Line().at(rail_pts[0]).tox(-4.0).label(rail_label, "left")
    rail_left = d.here
    for p in rail_pts:
        d += elm.Dot().at(p)
    d += elm.Line().at(rail_pts[0]).to(rail_pts[-1])
    vsrc = next((v for v in circuit.by_kind("V")
                 if "sin" not in (v.value or "").lower()), None)
    batt_label = (
        f"{vsrc.name}\n{volt}" if vsrc and volt else (vsrc.name if vsrc else "V1")
    )
    d += elm.Line().at(rail_left).toy(4.4)
    d += elm.SourceV().toy(1.4).label(batt_label, "left").reverse()
    d += elm.Line().toy(0.0)
    d += elm.Ground()

    # input: signal source -> Cin -> first base
    first_b = ordered[0]["b"]
    cin, _src = _cap_on(circuit, first_b, used)
    if cin:
        used.add(cin.name)
        d += elm.Line().at(base_pt[first_b.lower()]).tox(
            base_pt[first_b.lower()][0] - 1.4
        )
        d += elm.Capacitor().left().label(f"{cin.name}\n{cin.value}")
        in_pt = d.here
        vin = next((v for v in circuit.by_kind("V")
                    if "sin" in (v.value or "").lower()), None)
        d += elm.Line().at(in_pt).toy(2.2)
        d += elm.SourceSin().toy(0.8).label(f"{vin.name}\nin" if vin else "in", "left")
        d += elm.Line().toy(0.0)
        d += elm.Ground()

    # output: last collector -> Cout -> load -> ground
    last_c = ordered[-1]["c"]
    cout, vol = _cap_on(circuit, last_c, used)
    if cout:
        used.add(cout.name)
        tip = q_elem[ordered[-1]["ref"]].collector
        d += elm.Line().at(tip).tox(tip[0] + 1.4)
        d += elm.Capacitor().right().label(f"{cout.name}\n{cout.value}")
        d += elm.Dot()
        out_pt = d.here
        rload = _r_between(circuit, vol, "0") or _r_between(circuit, vol, "gnd")
        if rload:
            used.add(rload.name)
            d += elm.Resistor().at(out_pt).toy(0).label(f"{rload.name}\n{rload.value}")
            d += elm.Ground()

    # feedback: a leftover resistor from a later emitter back to an earlier base
    for r in circuit.by_kind("R"):
        if r.name in used or len(r.nodes) < 2:
            continue
        n1, n2 = r.nodes[0], r.nodes[1]
        if n2.lower() in base_pt and not _is_ground(n1):
            tgt, src = n2, n1
        elif n1.lower() in base_pt and not _is_ground(n2):
            tgt, src = n1, n2
        else:
            continue
        used.add(r.name)
        src_q = next(
            (q_elem[s["ref"]] for s in ordered if s["e"].lower() == src.lower()),
            None,
        )
        start = src_q.emitter if src_q else base_pt[tgt.lower()]
        d += elm.Line().at(start).toy(-1.2)
        d += elm.Resistor().tox(base_pt[tgt.lower()][0] - 1.0).label(
            f"{r.name} {r.value}"
        )
        d += elm.Wire("|-").to(base_pt[tgt.lower()])

    data = d.get_imagedata("svg")
    raw = data.decode("utf-8") if isinstance(data, bytes) else str(data)
    return _blueprint_frame(raw)


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
    """Render *circuit* to an SVG string, never raising.

    Prefers the topology-aware connected schematic; falls back to the component
    summary card for circuits the layout doesn't recognise.
    """
    try:
        svg = _cascade_svg(circuit)
    except Exception:
        return _card_svg(circuit)
    return svg if svg is not None else _card_svg(circuit)


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
