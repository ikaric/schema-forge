"""Schematic + plot rendering."""

from __future__ import annotations

from schema_forge.render.plots import build_figures, write_plots
from schema_forge.render.schematic import (
    extract_embedded_circuitjs,
    render_schematic,
    to_circuitjs,
    to_svg,
)
from schema_forge.sim.rawfile import parse_raw


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
