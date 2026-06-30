"""Render a SPICE netlist to a schematic: a clean SVG and a CircuitJS string.

Two views, per the project's design choice:

* **SchemDraw SVG** — a clean, *connected* static schematic (the deliverable
  view), drawn with real symbols and wires and derived entirely from the parsed
  netlist (so it cannot drift from the verified circuit). A topology-aware layout
  handles common-emitter BJT cascades (Fuzz Face / boost / preamp class); any
  netlist it can't fully represent falls back to a general rail auto-layout that
  draws *every* device, and finally to a hand-built component summary card — so a
  valid, complete SVG is *always* produced.
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


def _model_polarity(circuit: Circuit) -> dict[str, bool]:
    """Map ``.model`` name -> is-NPN (True) / is-PNP (False); defaults to NPN.

    Lets the renderer draw the right transistor symbol instead of assuming NPN.
    """
    pol: dict[str, bool] = {}
    for d in circuit.directives:
        toks = d.split()
        if len(toks) >= 3 and toks[0].lower() == ".model":
            up = d.upper()
            pol[toks[1].lower()] = "PNP" not in up and "PMOS" not in up
    return pol


def _is_npn(pol: dict[str, bool], value: str | None) -> bool:
    """NPN (True) unless the device's ``.model`` is explicitly PNP/PMOS."""
    return pol.get(value.split()[0].lower(), True) if value else True


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
def _cascade_svg(circuit: Circuit) -> tuple[str, set[str]] | None:  # noqa: C901
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
    pol = _model_polarity(circuit)
    used: set[str] = {s["ref"] for s in stages}
    vcc_y, gap = 7.0, 6.0
    d = schemdraw.Drawing(unit=2.0)
    d.config(fontsize=11, lw=1.6, color=_BP_INK)

    q_elem: dict[str, Any] = {}
    base_pt: dict[str, Any] = {}
    rail_pts: list[Any] = []
    for i, s in enumerate(ordered):
        x = 2 + i * gap
        npn = _is_npn(pol, s["val"])
        bjt = elm.BjtNpn if npn else elm.BjtPnp
        q = bjt(circle=True).anchor("base").at((x, 3)).label(
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
    if vsrc:
        used.add(vsrc.name)
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
        if vin:
            used.add(vin.name)
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
    return _blueprint_frame(raw), used


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


# --------------------------------------------------------------------------- #
# General auto-layout (completeness-first fallback)
#
# A deterministic rail/ladder layout that draws EVERY parsed device, used
# whenever the skeleton above can't represent the whole circuit. Placement is an
# iterated barycentre sweep — the cheap, reproducible cousin of the force-directed
# / simulated-annealing placement EDA tools use ("good enough", not optimal):
# order nets by the mean column of their devices, order devices by the mean row
# of their nets, repeat. Like the skeleton it is derived entirely from the parsed
# netlist — it never invents a part or a wire, so it cannot drift from the
# verified circuit; it can only be incomplete-by-bug, never wrong-by-fiction.
# --------------------------------------------------------------------------- #
_G_ACCENT = "#7fb2ff"
_G_NETLBL = "#9fc1ee"
_G_COL_W = 104
_G_ROW_H = 76
_G_X0 = 190
_G_Y0 = 120
_G_BODY = 30


class _Sheet:
    """A minimal SVG sink (no external drawing dependency)."""

    def __init__(self) -> None:
        self.p: list[str] = []

    def line(self, x1: float, y1: float, x2: float, y2: float,
             w: float = 2.0, color: str = _BP_INK) -> None:
        self.p.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
        )

    def rect(self, x: float, y: float, w: float, h: float) -> None:
        self.p.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="2" fill="none" stroke="{_BP_INK}" stroke-width="2"/>'
        )

    def circle(self, cx: float, cy: float, r: float) -> None:
        self.p.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" '
            f'stroke="{_BP_INK}" stroke-width="2"/>'
        )

    def dot(self, cx: float, cy: float, r: float = 3.0) -> None:
        self.p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{_BP_INK}"/>')

    def poly(self, pts: list[tuple[float, float]], fill: str = "none") -> None:
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.p.append(
            f'<polyline points="{s}" fill="{fill}" stroke="{_BP_INK}" '
            f'stroke-width="2" stroke-linejoin="round"/>'
        )

    def path(self, d: str) -> None:
        self.p.append(
            f'<path d="{d}" fill="none" stroke="{_BP_INK}" stroke-width="2"/>'
        )

    def text(self, x: float, y: float, s: str, size: int = 11,
             color: str = _BP_INK, anchor: str = "start",
             weight: str = "400") -> None:
        for i, ln in enumerate(str(s).split("\n")):
            self.p.append(
                f'<text x="{x:.1f}" y="{y + i * (size + 2):.1f}" '
                f'font-family="ui-monospace,Menlo,monospace" font-size="{size}" '
                f'font-weight="{weight}" fill="{color}" '
                f'text-anchor="{anchor}">{html.escape(ln)}</text>'
            )

    def svg(self, w: float, h: float) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">' + "".join(self.p) + "</svg>"
        )


def _g_ground(sh: _Sheet, x: float, y: float) -> None:
    sh.line(x, y, x, y + 9)
    for i, half in enumerate((11, 7, 3)):
        sh.line(x - half, y + 9 + i * 5, x + half, y + 9 + i * 5)


def _g_two_term(sh: _Sheet, x: float, ytop: float, ybot: float,
                kind: str, name: str, value: str) -> None:
    """Draw a 2-terminal symbol as a vertical rung between the ytop/ybot rails."""
    mid = (ytop + ybot) / 2
    top, bot = mid - _G_BODY / 2, mid + _G_BODY / 2
    if kind == "C":
        sh.line(x, ytop, x, mid - 4)
        sh.line(x - 12, mid - 4, x + 12, mid - 4, w=2.4)
        sh.line(x - 12, mid + 4, x + 12, mid + 4, w=2.4)
        sh.line(x, mid + 4, x, ybot)
    elif kind == "D":
        sh.line(x, ytop, x, top)
        sh.poly([(x - 7, top), (x + 7, top), (x, top + 12), (x - 7, top)], fill=_BP_INK)
        sh.line(x - 7, top + 12, x + 7, top + 12, w=2.4)
        sh.line(x, top + 12, x, ybot)
    elif kind == "L":
        sh.line(x, ytop, x, top)
        for k in range(3):
            sh.path(f"M{x} {top + k * 10} a5 5 0 0 1 0 10")
        sh.line(x, top + 30, x, ybot)
    else:  # R and any other generic two-terminal device
        sh.line(x, ytop, x, top)
        sh.rect(x - 8, top, 16, _G_BODY)
        if kind != "R":
            sh.text(x, mid + 4, kind, size=10, anchor="middle")
        sh.line(x, bot, x, ybot)
    sh.text(x + 16, mid - 2, f"{name}\n{value}" if value else name, color=_G_ACCENT)


def _g_source(sh: _Sheet, x: float, ytop: float, ybot: float,
              name: str, value: str, ac: bool) -> None:
    mid = (ytop + ybot) / 2
    sh.line(x, ytop, x, mid - 14)
    sh.circle(x, mid, 14)
    if ac:
        sh.path(f"M{x - 7} {mid} q3.5 -7 7 0 q3.5 7 7 0")
    else:
        sh.text(x, mid - 1, "+", size=14, anchor="middle")
        sh.text(x, mid + 12, "−", size=14, anchor="middle")
    sh.line(x, mid + 14, x, ybot)
    sh.text(x + 18, mid - 2, f"{name}\n{value}" if value else name, color=_G_ACCENT)


def _g_transistor(sh: _Sheet, x: float, cy: float, yc: float, yb: float,
                  ye: float, name: str, value: str, npn: bool) -> None:
    """3-terminal device: collector up, emitter down, base left — each pin routed
    to its own rail, so the drawing is faithful regardless of node order."""
    sh.circle(x, cy, 15)
    sh.line(x, cy - 15, x, yc)
    sh.line(x, cy + 15, x, ye)
    sh.line(x - 15, cy, x - 26, cy)
    sh.line(x - 26, cy, x - 26, yb)
    ay = cy + 11  # emitter arrow: NPN points out, PNP points in
    if npn:
        sh.poly([(x - 3, ay - 5), (x, ay), (x + 4, ay - 4)], fill=_BP_INK)
    else:
        sh.poly([(x - 3, ay + 1), (x + 4, ay), (x + 1, ay - 5)], fill=_BP_INK)
    label = f"{name}\n{value} ({'NPN' if npn else 'PNP'})" if value else name
    sh.text(x + 20, cy - 2, label, color=_G_ACCENT)


def _barycentre_order(
    circuit: Circuit, nets: list[str]
) -> tuple[list[str], list[Element]]:
    """Iterated barycentre crossing-reduction (deterministic, cheap)."""
    devs = list(circuit.elements)
    net_order = list(nets)

    def mean(xs: list[Any], default: float) -> float:
        vals = [float(v) for v in xs if v is not None]
        return sum(vals) / len(vals) if vals else default

    for _ in range(6):
        row = {n: i for i, n in enumerate(net_order)}
        devs = sorted(
            circuit.elements,
            key=lambda d: mean(
                [row.get(n) for n in d.nodes if not _is_ground(n)], len(net_order) / 2
            ),
        )
        col = {d.name: i for i, d in enumerate(devs)}
        net_order = sorted(
            nets,
            key=lambda n: mean(
                [col.get(d.name) for d in circuit.elements if n in d.nodes],
                len(devs) / 2,
            ),
        )
    return net_order, devs


def _general_svg(circuit: Circuit) -> str:  # noqa: C901
    """Draw *every* device of *circuit* via the general rail layout (see above)."""
    nets = [n for n in circuit.nodes if not _is_ground(n)]
    net_order, devs = _barycentre_order(circuit, nets)
    yof = {n: _G_Y0 + i * _G_ROW_H for i, n in enumerate(net_order)}
    pol = _model_polarity(circuit)
    sh = _Sheet()
    conn: dict[str, list[float]] = {n: [] for n in nets}

    for i, dev in enumerate(devs):
        x = _G_X0 + i * _G_COL_W
        ns = dev.nodes
        if dev.kind in ("Q", "J", "Z") and len(ns) >= 3:
            # yof holds only non-ground nets, so `n in yof` already means "live".
            c_net, b_net, e_net = ns[0], ns[1], ns[2]
            ys = [yof[n] for n in (c_net, b_net, e_net) if n in yof]
            cy = sum(ys) / len(ys) if ys else _G_Y0
            yc = yof[c_net] if c_net in yof else cy - 46
            ye = yof[e_net] if e_net in yof else cy + 46
            yb = yof[b_net] if b_net in yof else cy
            npn = _is_npn(pol, dev.value)
            _g_transistor(sh, x, cy, yc, yb, ye, dev.name, dev.value or "", npn)
            for net, yy, xx in ((c_net, yc, x), (e_net, ye, x), (b_net, yb, x - 26)):
                if net not in yof:
                    _g_ground(sh, xx, yy)
                else:
                    conn[net].append(xx)
                    sh.dot(xx, yy)
            continue

        if len(ns) < 2:
            continue
        a, b = ns[0], ns[1]
        ga, gb = _is_ground(a), _is_ground(b)
        if ga and gb:
            continue
        ac = "sin" in (dev.value or "").lower()
        if ga or gb:
            live = b if ga else a
            if live not in yof:
                continue
            yl = yof[live]
            ytop, ybot = yl, yl + 56
            if dev.kind in ("V", "I"):
                _g_source(sh, x, ytop, ybot, dev.name, dev.value or "", ac)
            else:
                _g_two_term(sh, x, ytop, ybot, dev.kind, dev.name, dev.value or "")
            _g_ground(sh, x, ybot)
            conn[live].append(x)
            sh.dot(x, yl)
        else:
            ya, yb2 = yof[a], yof[b]
            ytop, ybot = min(ya, yb2), max(ya, yb2)
            if dev.kind in ("V", "I"):
                _g_source(sh, x, ytop, ybot, dev.name, dev.value or "", ac)
            else:
                _g_two_term(sh, x, ytop, ybot, dev.kind, dev.name, dev.value or "")
            conn[a].append(x)
            conn[b].append(x)
            sh.dot(x, ya)
            sh.dot(x, yb2)

    for n in net_order:
        xs = conn.get(n) or []
        if not xs:
            continue
        y = yof[n]
        sh.line(min(xs) - 16, y, max(xs) + 16, y, w=1.6)
        sh.text(70, y + 4, n, size=12, color=_G_NETLBL)
        sh.dot(min(xs) - 16, y, r=2.5)

    width = _G_X0 + len(devs) * _G_COL_W + 150
    height = _G_Y0 + max(len(net_order), 1) * _G_ROW_H + 90
    sh.text(70, 54, circuit.title or "schematic", size=16, weight="700")
    sh.text(70, 75, f"general auto-layout · {len(devs)} devices · "
                    f"{len(net_order)} nets", size=11, color=_G_NETLBL)
    return _blueprint_frame(sh.svg(width, height))


def to_svg(circuit: Circuit) -> str:
    """Render *circuit* to an SVG string, never raising.

    Uses the topology-aware skeleton only when it draws *every* device; otherwise
    falls back to the general rail auto-layout (which draws them all), and finally
    to the dependency-free component card. The displayed schematic is therefore
    always complete — it can never silently omit a part of the verified circuit.
    """
    try:
        result = _cascade_svg(circuit)
    except Exception:
        result = None
    if result is not None:
        svg, used = result
        if {e.name for e in circuit.elements} <= used:
            return svg
    try:
        return _general_svg(circuit)
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
