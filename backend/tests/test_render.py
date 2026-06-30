"""Schematic + plot rendering."""

from __future__ import annotations

import numpy as np

from schema_forge.render.plots import (
    _pick,
    _signal_vars,
    build_figures,
    clear_plots,
    fft_figure,
    write_plots,
)
from schema_forge.render.schematic import (
    extract_embedded_circuitjs,
    render_schematic,
    to_circuitjs,
    to_svg,
)
from schema_forge.sim.rawfile import Plot, parse_raw


def _tran(**series: np.ndarray) -> Plot:
    """Build a transient Plot from ``time=..., name=...`` arrays."""
    t = series.pop("time")
    variables = [("time", "time")] + [(n, "voltage") for n in series]
    data = {"time": t, **series}
    return Plot(
        name="Transient Analysis",
        flags="real",
        variables=variables,
        data=data,
        n_points=len(t),
    )


def test_svg_is_valid(sample_circuit) -> None:
    svg = to_svg(sample_circuit)
    assert "<svg" in svg[:300]


def test_circuitjs_matrix_layout(sample_circuit) -> None:
    cjs = to_circuitjs(sample_circuit)
    lines = cjs.splitlines()
    assert lines[0].startswith("$")  # options line
    assert any(line.startswith("r ") for line in lines)  # R1
    assert any(line.startswith("d ") for line in lines)  # diodes
    assert any(line.startswith("g ") for line in lines)  # ground symbol


def test_embedded_circuitjs_override() -> None:
    netlist = "* @circuitjs-begin\n* $ 1 0.1\n* r 1 2 3 4 0 100\n* @circuitjs-end\n"
    emb = extract_embedded_circuitjs(netlist)
    assert emb is not None and "r 1 2 3 4 0 100" in emb
    # to_circuitjs prefers the embedded block verbatim.
    from schema_forge.netlist import parse_netlist

    assert to_circuitjs(parse_netlist("t\nR1 1 2 100\n"), emb) == emb


def test_render_schematic_writes_files(sample_circuit, tmp_path) -> None:
    netlist = tmp_path / "main.cir"
    netlist.write_text("Diode clipper\nR1 in out 4.7k\nC1 out 0 10n\n.end\n")
    out = render_schematic(netlist, tmp_path, "main")
    assert out["svg"].exists() and out["circuitjs"].exists()


def test_build_and_write_plots(multi_plot_raw, tmp_path) -> None:
    plots = parse_raw(multi_plot_raw)
    figs = build_figures(plots)
    ids = {f["id"] for f in figs}
    assert {"transient", "ac"} <= ids
    written = write_plots(plots, tmp_path, "main")
    assert all(p.exists() for p in written)
    assert any(p.name.endswith(".transient.plot.json") for p in written)


def test_signal_vars_drops_dc_rails() -> None:
    t = np.linspace(0, 2e-3, 200)
    plot = _tran(
        time=t,
        **{
            "v(out)": np.sin(2 * np.pi * 1000 * t),  # swings
            "v(vcc)": np.full_like(t, 9.0),  # a flat rail
        },
    )
    assert _signal_vars(plot) == ["v(out)"]  # rail dropped, signal kept


def test_signal_vars_keeps_all_when_every_node_flat() -> None:
    t = np.linspace(0, 1e-3, 50)
    plot = _tran(time=t, **{"v(a)": np.full_like(t, 1.0), "v(b)": np.full_like(t, 2.0)})
    assert set(_signal_vars(plot)) == {"v(a)", "v(b)"}  # never empty


def test_pick_prefers_the_liveliest_transient() -> None:
    t = np.linspace(0, 5e-3, 300)
    flat = _tran(time=t, **{"v(out)": np.full_like(t, 0.7)})  # drive-off run
    live = _tran(time=t, **{"v(out)": np.sin(2 * np.pi * 1000 * t)})  # driven run
    assert _pick([flat, live], "time") is live
    assert _pick([live, flat], "time") is live  # order-independent


def test_fft_is_single_bin_for_an_integer_cycle_tone() -> None:
    t = np.linspace(0, 20e-3, 600)  # 20 ms window
    plot = _tran(time=t, **{"v(out)": np.sin(2 * np.pi * 1000 * t)})
    fig = fft_figure(plot)
    assert fig is not None
    xs, ys = fig["data"][0]["x"], fig["data"][0]["y"]
    k = int(np.argmax(ys))
    assert abs(xs[k] - 1000.0) < 70.0  # peak on the fundamental
    peak = ys[k]
    assert ys[k - 1] < 0.1 * peak and ys[k + 1] < 0.1 * peak  # no smear


def test_write_plots_clears_stale_figures(multi_plot_raw, tmp_path) -> None:
    stale = tmp_path / "main.bogus.plot.json"
    stale.write_text("{}")
    other = tmp_path / "other.transient.plot.json"
    other.write_text("{}")
    write_plots(parse_raw(multi_plot_raw), tmp_path, "main")
    assert not stale.exists()  # a figure this run no longer emits is removed
    assert other.exists()  # a different stem is untouched


def test_clear_plots_removes_only_matching_stem(tmp_path) -> None:
    (tmp_path / "main.transient.plot.json").write_text("{}")
    (tmp_path / "main.ac.plot.json").write_text("{}")
    (tmp_path / "other.ac.plot.json").write_text("{}")
    clear_plots(tmp_path, "main")
    assert not list(tmp_path.glob("main.*.plot.json"))
    assert (tmp_path / "other.ac.plot.json").exists()
