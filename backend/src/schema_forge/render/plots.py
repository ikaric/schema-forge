"""Turn ngspice rawfile plots into Plotly figure JSON for the frontend.

Each analysis becomes one ``<stem>.<kind>.plot.json`` file holding a Plotly
figure (``{"id", "title", "data", "layout"}``). The React ``SignalPlots``
component renders these directly. A transient run additionally yields an FFT
spectrum so the UI can show frequency content (THD itself is asserted via an
ngspice ``.measure``, not recomputed here).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from schema_forge.sim.rawfile import Plot, find_plot

Figure = dict[str, Any]

_MAX_POINTS = 4000


def _downsample(*arrays: np.ndarray, cap: int = _MAX_POINTS) -> list[np.ndarray]:
    n = len(arrays[0])
    if n <= cap:
        return list(arrays)
    step = int(np.ceil(n / cap))
    return [a[::step] for a in arrays]


def _signal_vars(plot: Plot) -> list[str]:
    """Non-independent variables worth plotting (prefer node voltages)."""
    names = [n for n in plot.var_names() if n != plot.x_name]
    volts = [n for n in names if n.lower().startswith("v(")]
    chosen = volts or names
    return chosen[:8]


def _figure(fig_id: str, title: str, data: list[Figure], layout: Figure) -> Figure:
    layout = {
        "title": {"text": title},
        "margin": {"t": 40, "r": 20, "b": 48, "l": 64},
        **layout,
    }
    return {"id": fig_id, "title": title, "data": data, "layout": layout}


def transient_figure(plot: Plot) -> Figure:
    t = np.real(plot.x)
    data: list[Figure] = []
    for name in _signal_vars(plot):
        ds_t, y = _downsample(t, np.real(plot.data[name]))
        data.append(
            {
                "x": ds_t.tolist(),
                "y": y.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": name,
            }
        )
    return _figure(
        "transient",
        "Transient response",
        data,
        {
            "xaxis": {"title": {"text": "Time (s)"}},
            "yaxis": {"title": {"text": "Voltage (V)"}},
        },
    )


def ac_figure(plot: Plot) -> Figure:
    f = np.real(plot.x)
    data: list[Figure] = []
    for name in _signal_vars(plot):
        h = plot.data[name]
        mag_db = 20.0 * np.log10(np.abs(h) + 1e-30)
        ds_f, y = _downsample(f, mag_db)
        data.append(
            {
                "x": ds_f.tolist(),
                "y": y.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": f"|{name}| (dB)",
            }
        )
    # Phase of the first signal on a secondary axis.
    first = _signal_vars(plot)[:1]
    for name in first:
        phase = np.degrees(np.angle(plot.data[name]))
        ds_f, y = _downsample(f, phase)
        data.append(
            {
                "x": ds_f.tolist(),
                "y": y.tolist(),
                "yaxis": "y2",
                "type": "scatter",
                "mode": "lines",
                "line": {"dash": "dot"},
                "name": f"∠{name} (°)",
            }
        )
    return _figure(
        "ac",
        "Frequency response (Bode)",
        data,
        {
            "xaxis": {"title": {"text": "Frequency (Hz)"}, "type": "log"},
            "yaxis": {"title": {"text": "Magnitude (dB)"}},
            "yaxis2": {
                "title": {"text": "Phase (°)"},
                "overlaying": "y",
                "side": "right",
                "showgrid": False,
            },
        },
    )


def fft_figure(plot: Plot, max_freq: float = 8000.0) -> Figure | None:
    """Output spectrum as a bar chart (spectrum-analyzer style), harmonic band."""
    t = np.real(plot.x)
    names = _signal_vars(plot)
    if len(t) < 8 or not names:
        return None
    out = next((n for n in names if "out" in n.lower()), names[-1])
    y = np.real(plot.data[out])
    # FFT the steady-state tail (skip the turn-on) for clean peaks, on a uniform
    # grid (ngspice transient steps are non-uniform).
    t0, t1 = float(t[0]), float(t[-1])
    n = max(len(t), 16)
    t_u = np.linspace(t0 + 0.25 * (t1 - t0), t1, n)
    y_u = np.interp(t_u, t, y)
    dt = (t_u[-1] - t_u[0]) / max(n - 1, 1)
    if dt <= 0:
        return None
    mag = np.abs(np.fft.rfft((y_u - y_u.mean()) * np.hanning(n))) / n * 2.0
    freqs = np.fft.rfftfreq(n, d=dt)
    keep = freqs <= max_freq
    return _figure(
        "fft",
        f"Output spectrum — {out}",
        [
            {
                "x": freqs[keep].tolist(),
                "y": mag[keep].tolist(),
                "type": "bar",
                "name": "spectrum",
                "marker": {"line": {"width": 0}},
            }
        ],
        {
            "xaxis": {
                "title": {"text": "Frequency (Hz)"},
                "dtick": 500,
                "range": [0, max_freq],
            },
            "yaxis": {"title": {"text": "Magnitude (V)"}},
            "bargap": 0.06,
        },
    )


def build_figures(plots: list[Plot]) -> list[Figure]:
    """Return the Plotly figures derived from a set of rawfile plots."""
    figures: list[Figure] = []
    tran = find_plot(plots, "time")
    ac = find_plot(plots, "frequency")
    if tran is not None:
        figures.append(transient_figure(tran))
        fft = fft_figure(tran)
        if fft is not None:
            figures.append(fft)
    if ac is not None:
        figures.append(ac_figure(ac))
    return figures


def write_plots(plots: list[Plot], outdir: Path, stem: str) -> list[Path]:
    """Write one ``<stem>.<id>.plot.json`` per figure; return their paths."""
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for fig in build_figures(plots):
        path = outdir / f"{stem}.{fig['id']}.plot.json"
        path.write_text(json.dumps(fig), encoding="utf-8")
        written.append(path)
    return written
