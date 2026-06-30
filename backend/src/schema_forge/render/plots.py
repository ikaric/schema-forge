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

from schema_forge.sim.rawfile import Plot

Figure = dict[str, Any]

_MAX_POINTS = 4000


def _downsample(*arrays: np.ndarray, cap: int = _MAX_POINTS) -> list[np.ndarray]:
    n = len(arrays[0])
    if n <= cap:
        return list(arrays)
    step = int(np.ceil(n / cap))
    return [a[::step] for a in arrays]


def _span(arr: np.ndarray) -> float:
    """Peak-to-peak magnitude of a signal (~0 for a constant, e.g. a DC rail)."""
    a = np.abs(arr) if np.iscomplexobj(arr) else np.real(arr)
    return float(np.ptp(a)) if a.size else 0.0


def _signal_vars(plot: Plot) -> list[str]:
    """Node voltages worth plotting, busiest first.

    Prefers ``v(...)`` nodes and drops DC **rails** — a supply held constant
    across the sweep. A flat −9 V trace adds nothing on a transient and, as a
    ~−600 dB image, crushes a Bode plot's autoscale. Rails are kept only when
    *every* node is flat, so the figure is never empty.
    """
    names = [n for n in plot.var_names() if n != plot.x_name]
    volts = [n for n in names if n.lower().startswith("v(")]
    chosen = volts or names
    spans = {n: _span(plot.data[n]) for n in chosen}
    top = max(spans.values(), default=0.0)
    if top > 0.0:
        moving = [n for n in chosen if spans[n] > 1e-6 * top]
        chosen = moving or chosen
    chosen.sort(key=lambda n: spans[n], reverse=True)  # busiest first under the cap
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


def _fundamental(y: np.ndarray, dt: float) -> float:
    """Dominant non-DC frequency of *y* via a Hann-windowed FFT (0.0 if none)."""
    n = len(y)
    mag = np.abs(np.fft.rfft(y * np.hanning(n)))
    if mag.size <= 1:
        return 0.0
    k = int(np.argmax(mag[1:])) + 1
    return float(np.fft.rfftfreq(n, d=dt)[k])


def _spectrum_bar(
    out: str, freqs: np.ndarray, mag: np.ndarray, max_freq: float
) -> Figure:
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


def fft_figure(plot: Plot, max_freq: float = 8000.0) -> Figure | None:
    """Output spectrum as a bar chart (spectrum-analyzer style), harmonic band.

    The transient tail is resampled onto a uniform grid (ngspice steps are
    non-uniform), then — when a fundamental is detectable — trimmed to a *whole*
    number of its periods so a settled tone lands in a single bin (rectangular
    window, no spectral leakage). A plain Hann window otherwise smears every
    harmonic across ~3 bins even for an integer-cycle signal. Falls back to Hann
    for noise-like content with no clear fundamental.
    """
    t = np.real(plot.x)
    names = _signal_vars(plot)
    if len(t) < 8 or not names:
        return None
    out = next((n for n in names if "out" in n.lower()), names[-1])
    y = np.real(plot.data[out])
    t0, t1 = float(t[0]), float(t[-1])
    tail0 = t0 + 0.25 * (t1 - t0)  # skip the turn-on transient
    if t1 <= tail0:
        return None
    n = max(len(t), 256)

    # First pass: locate the fundamental on a uniform resample of the tail.
    t_u = np.linspace(tail0, t1, n)
    y_u = np.interp(t_u, t, y)
    y_u = y_u - y_u.mean()
    dt = (t1 - tail0) / (n - 1)
    f0 = _fundamental(y_u, dt)

    # Second pass: resample a whole number of fundamental periods (rectangular
    # window) so the tone and its harmonics fall on exact bins.
    cycles = int((t1 - tail0) * f0) if f0 > 0.0 else 0
    if cycles >= 2:
        span = cycles / f0
        t_w = np.linspace(t1 - span, t1, n, endpoint=False)
        y_w = np.interp(t_w, t, y)
        y_w = y_w - y_w.mean()
        mag = np.abs(np.fft.rfft(y_w)) / n * 2.0
        return _spectrum_bar(out, np.fft.rfftfreq(n, d=span / n), mag, max_freq)

    mag = np.abs(np.fft.rfft(y_u * np.hanning(n))) / n * 2.0
    return _spectrum_bar(out, np.fft.rfftfreq(n, d=dt), mag, max_freq)


def _pick(plots: list[Plot], *x_names: str) -> Plot | None:
    """The *liveliest* plot whose independent variable matches — the one whose
    signals actually move. With several transient runs in one rawfile (e.g. a
    drive-off bias run plus the driven run), this avoids plotting a dead line.
    """
    wanted = {x.lower() for x in x_names}
    cands = [p for p in plots if p.x_name.lower() in wanted]
    if not cands:
        return None
    return max(
        cands,
        key=lambda p: max((_span(p.data[n]) for n in _signal_vars(p)), default=0.0),
    )


def build_figures(plots: list[Plot]) -> list[Figure]:
    """Return the Plotly figures derived from a set of rawfile plots."""
    figures: list[Figure] = []
    tran = _pick(plots, "time")
    ac = _pick(plots, "frequency")
    if tran is not None:
        figures.append(transient_figure(tran))
        fft = fft_figure(tran)
        if fft is not None:
            figures.append(fft)
    if ac is not None:
        figures.append(ac_figure(ac))
    return figures


def clear_plots(outdir: Path, stem: str) -> None:
    """Remove existing ``<stem>.*.plot.json`` figures so a re-render can't leave a
    stale plot (e.g. an AC figure from a previous run that no longer sweeps AC)."""
    for old in Path(outdir).glob(f"{stem}.*.plot.json"):
        old.unlink()


def write_plots(plots: list[Plot], outdir: Path, stem: str) -> list[Path]:
    """Write one ``<stem>.<id>.plot.json`` per figure; return their paths."""
    outdir.mkdir(parents=True, exist_ok=True)
    clear_plots(outdir, stem)
    written: list[Path] = []
    for fig in build_figures(plots):
        path = outdir / f"{stem}.{fig['id']}.plot.json"
        path.write_text(json.dumps(fig), encoding="utf-8")
        written.append(path)
    return written
