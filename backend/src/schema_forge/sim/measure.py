"""Parse ngspice ``.measure`` scalar results out of the batch-run log.

In batch mode ngspice prints each measurement as a line like::

    gain_db             =  2.054321e+01
    f_hi                =  4.812000e+03 targ=  ... trig= ...

and prints a failure as a line containing the measure name and ``failed``.
We scan every output line, capture the leading ``name = value`` pairs, and
separately collect the names ngspice reported as failed.
"""

from __future__ import annotations

import re

_MEASURE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\b"
)
_FAILED_RE = re.compile(r"\bmeasure(?:ment)?\s+([A-Za-z_]\w*)\b.*\bfail", re.IGNORECASE)
# ngspice `.four` prints e.g. "Total Harmonic Distortion: 12.345678 percent".
_THD_RE = re.compile(
    r"total harmonic distortion:\s*([0-9.]+)\s*(?:percent|%)", re.IGNORECASE
)


def parse_measures(log: str) -> tuple[dict[str, float], list[str]]:
    """Return ``(values, failed_names)`` parsed from ngspice output *log*."""
    values: dict[str, float] = {}
    failed: list[str] = []
    for line in log.splitlines():
        fail = _FAILED_RE.search(line)
        if fail:
            failed.append(fail.group(1).lower())
            continue
        m = _MEASURE_RE.match(line)
        if not m:
            continue
        name = m.group(1).lower()
        # Skip header-ish noise that happens to look like an assignment.
        if name in {"no", "title", "date", "plotname", "flags", "variables"}:
            continue
        try:
            values[name] = float(m.group(2))
        except ValueError:  # pragma: no cover - regex already constrained
            continue
    thd = _THD_RE.search(log)
    if thd:
        values.setdefault("thd", float(thd.group(1)))
    # A value that later parsed successfully overrides an earlier "failed".
    failed = [f for f in failed if f not in values]
    return values, failed
