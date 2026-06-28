"""SPICE/engineering value parsing (e.g. ``10k`` -> 10000.0, ``4u7`` -> 4.7e-6)."""

from __future__ import annotations

import re

# Order matters: "meg" must be tried before "m".
_SUFFIXES: list[tuple[str, float]] = [
    ("meg", 1e6),
    ("mil", 25.4e-6),
    ("f", 1e-15),
    ("p", 1e-12),
    ("n", 1e-9),
    ("u", 1e-6),
    ("µ", 1e-6),
    ("m", 1e-3),
    ("k", 1e3),
    ("g", 1e9),
    ("t", 1e12),
]

_NUM_RE = re.compile(r"^([-+]?\d*\.?\d+)\s*([A-Za-zµ]*)")


def parse_si(text: str | None) -> float | None:
    """Parse a SPICE value with an optional SI/engineering suffix.

    Handles the RKM/"4u7" convention where the suffix sits between digits.
    Returns ``None`` when *text* has no leading numeric value.
    """
    if not text:
        return None
    token = text.strip().split()[0]
    # RKM notation: 4u7 -> 4.7u, 1k5 -> 1.5k
    rkm = re.fullmatch(r"([-+]?\d+)([a-zA-Zµ])(\d+)", token)
    if rkm:
        token = f"{rkm.group(1)}.{rkm.group(3)}{rkm.group(2)}"
    m = _NUM_RE.match(token)
    if not m:
        return None
    value = float(m.group(1))
    suffix = m.group(2).lower()
    if not suffix:
        return value
    for name, mult in _SUFFIXES:
        if suffix.startswith(name):
            return value * mult
    return value  # unknown trailing unit (e.g. "5V") -> bare number
