"""Parse ngspice rawfiles (binary or ASCII, real or complex, multi-plot).

``ngspice -b -r out.raw`` writes a binary rawfile by default; users who ``set
filetype=ascii`` get the ASCII variant. A single rawfile may concatenate several
plots (e.g. an op point, an AC sweep, and a transient run). We return one
:class:`Plot` per concatenated plot, with variable data as numpy arrays
(complex-valued for AC/``complex`` plots).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_PLOTNAME_RE = re.compile(r"^Plotname:\s*(.*)$", re.MULTILINE)
_FLAGS_RE = re.compile(r"^Flags:\s*(.*)$", re.MULTILINE)
_NVARS_RE = re.compile(r"^No\.\s*Variables:\s*(\d+)", re.MULTILINE)
_NPOINTS_RE = re.compile(r"^No\.\s*Points:\s*(\d+)", re.MULTILINE)


@dataclass
class Plot:
    """One analysis result: named variables sampled over N points."""

    name: str
    flags: str  # "real" or "complex"
    variables: list[tuple[str, str]]  # (name, type) in column order
    data: dict[str, np.ndarray]  # variable name -> values
    n_points: int

    @property
    def is_complex(self) -> bool:
        return self.flags.startswith("complex")

    @property
    def x_name(self) -> str:
        return self.variables[0][0] if self.variables else ""

    @property
    def x(self) -> np.ndarray:
        return self.data[self.x_name]

    def var_names(self) -> list[str]:
        return [n for n, _ in self.variables]


def _parse_header(text: str) -> tuple[str, str, int, int, list[tuple[str, str]]] | None:
    nvars_m = _NVARS_RE.search(text)
    npoints_m = _NPOINTS_RE.search(text)
    if not nvars_m or not npoints_m:
        return None
    nvars = int(nvars_m.group(1))
    npoints = int(npoints_m.group(1))
    name_m = _PLOTNAME_RE.search(text)
    flags_m = _FLAGS_RE.search(text)
    name = name_m.group(1).strip() if name_m else ""
    flags = flags_m.group(1).strip() if flags_m else "real"

    variables: list[tuple[str, str]] = []
    after = text.split("Variables:", 1)
    if len(after) == 2:
        for line in after[1].splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                variables.append((parts[1], parts[2]))
            if len(variables) == nvars:
                break
    return name, flags, nvars, npoints, variables


def _parse_ascii_values(
    text: str, nvars: int, npoints: int, complex_: bool
) -> np.ndarray:
    vals: list[complex | float] = []
    need = nvars * npoints
    for line in text.splitlines():
        if not line.strip():
            continue
        toks = line.split()
        # A point block's first line leads with the integer point index.
        if line[:1] not in (" ", "\t") and toks and toks[0].isdigit():
            toks = toks[1:]
        for t in toks:
            if complex_:
                re_s, _, im_s = t.partition(",")
                vals.append(complex(float(re_s), float(im_s or 0.0)))
            else:
                vals.append(float(t))
            if len(vals) >= need:
                break
        if len(vals) >= need:
            break
    arr = np.array(vals, dtype=complex if complex_ else float)
    return arr.reshape(npoints, nvars)


def parse_raw(path: str | Path) -> list[Plot]:
    """Parse an ngspice rawfile into a list of :class:`Plot` objects."""
    blob = Path(path).read_bytes()
    plots: list[Plot] = []
    pos, n = 0, len(blob)

    while pos < n:
        bin_kw = blob.find(b"Binary:\n", pos)
        val_kw = blob.find(b"Values:\n", pos)
        candidates = [k for k in (bin_kw, val_kw) if k != -1]
        if not candidates:
            break
        kw = min(candidates)
        is_binary = kw == bin_kw

        header = blob[pos:kw].decode("latin-1", errors="replace")
        parsed = _parse_header(header)
        if parsed is None:
            break
        name, flags, nvars, npoints, variables = parsed
        complex_ = flags.startswith("complex")
        if len(variables) < nvars:  # header malformed; bail on this plot
            break

        matrix: np.ndarray
        if is_binary:
            start = kw + len(b"Binary:\n")
            per_value = 16 if complex_ else 8
            byte_len = nvars * npoints * per_value
            chunk = blob[start : start + byte_len]
            flat = np.frombuffer(chunk, dtype="<f8")
            if complex_:
                cube = flat.reshape(npoints, nvars, 2)
                matrix = cube[:, :, 0] + 1j * cube[:, :, 1]
            else:
                matrix = flat.reshape(npoints, nvars)
            pos = start + byte_len
        else:
            start = kw + len(b"Values:\n")
            nxt = blob.find(b"\nTitle:", start)
            end = nxt if nxt != -1 else n
            text = blob[start:end].decode("latin-1", errors="replace")
            matrix = _parse_ascii_values(text, nvars, npoints, complex_)
            pos = end + 1 if nxt != -1 else n

        data = {variables[i][0]: matrix[:, i].copy() for i in range(nvars)}
        plots.append(
            Plot(
                name=name,
                flags=flags,
                variables=variables,
                data=data,
                n_points=npoints,
            )
        )

    return plots


def find_plot(plots: list[Plot], *x_candidates: str) -> Plot | None:
    """Return the first plot whose independent variable matches a candidate."""
    wanted = {c.lower() for c in x_candidates}
    for p in plots:
        if p.x_name.lower() in wanted:
            return p
    return None
