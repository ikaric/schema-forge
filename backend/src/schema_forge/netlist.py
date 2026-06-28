"""A small, forgiving SPICE netlist parser shared by simulation and rendering.

We deliberately keep this lightweight: the netlist is the source of truth that
ngspice consumes verbatim, so we only need enough structure to (a) lay out a
schematic and (b) reason about connectivity. Unknown element types degrade
gracefully to a generic two-terminal view rather than raising.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# How many leading tokens after the element name are node names, by first letter.
# Anything not listed defaults to 2 (the overwhelmingly common two-terminal case).
_NODE_COUNT: dict[str, int] = {
    "R": 2,
    "C": 2,
    "L": 2,
    "D": 2,
    "V": 2,
    "I": 2,
    "Q": 3,
    "J": 3,
    "Z": 3,  # BJT / JFET / MESFET
    "M": 4,  # MOSFET
    "E": 4,
    "G": 4,
    "F": 2,
    "H": 2,  # controlled sources
}

_DIRECTIVE_RE = re.compile(r"^\.(\w+)", re.IGNORECASE)


@dataclass
class Element:
    """A single circuit element (one device line of the netlist)."""

    kind: str  # canonical first letter, uppercased (R, C, D, Q, X, ...)
    name: str  # full reference designator, e.g. "R1", "Q3", "XU1"
    nodes: list[str]  # connected net names, in netlist order
    value: str | None  # value / model token(s), best-effort
    raw: str  # the original (joined) source line


@dataclass
class Circuit:
    """A parsed netlist: title, device elements, and dot-directives."""

    title: str
    elements: list[Element] = field(default_factory=list)
    directives: list[str] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)

    @property
    def nodes(self) -> list[str]:
        """Distinct net names in first-appearance order ('0'/'gnd' kept)."""
        seen: dict[str, None] = {}
        for el in self.elements:
            for n in el.nodes:
                seen.setdefault(n, None)
        return list(seen)

    def by_kind(self, kind: str) -> list[Element]:
        return [e for e in self.elements if e.kind == kind.upper()]

    def analyses(self) -> list[str]:
        """The analysis directives present (op/ac/tran/dc/...), lower-cased."""
        out: list[str] = []
        for d in self.directives:
            m = _DIRECTIVE_RE.match(d)
            if m and m.group(1).lower() in {"op", "ac", "tran", "dc", "noise", "disto"}:
                out.append(m.group(1).lower())
        return out


def _join_continuations(text: str) -> list[str]:
    """Merge SPICE ``+`` continuation lines into their logical line."""
    logical: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("+") and logical:
            logical[-1] = logical[-1].rstrip() + " " + line.lstrip()[1:].strip()
        else:
            logical.append(line)
    return logical


def parse_netlist(text: str) -> Circuit:
    """Parse netlist source into a :class:`Circuit`.

    The first non-blank line is taken as the title per SPICE convention.
    """
    logical = _join_continuations(text)

    title = ""
    body_start = 0
    for i, line in enumerate(logical):
        if line.strip():
            # SPICE always treats line 1 as the title; strip a comment marker
            # so a "* My Circuit" header displays cleanly.
            title = line.strip().lstrip("*").strip()
            body_start = i + 1
            break

    circuit = Circuit(title=title, raw_lines=logical)

    for line in logical[body_start:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("*"):
            continue
        if stripped.startswith("."):
            circuit.directives.append(stripped)
            continue
        # Strip inline comments ('$' and ';' are common ngspice inline markers).
        for marker in (" ;", " $"):
            idx = stripped.find(marker)
            if idx != -1:
                stripped = stripped[:idx].strip()
        tokens = stripped.split()
        if not tokens:
            continue
        name = tokens[0]
        kind = name[0].upper()
        n_nodes = _NODE_COUNT.get(kind, 2)
        nodes = tokens[1 : 1 + n_nodes]
        value = " ".join(tokens[1 + n_nodes :]) or None
        circuit.elements.append(
            Element(kind=kind, name=name, nodes=nodes, value=value, raw=stripped)
        )

    return circuit
