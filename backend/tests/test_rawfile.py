"""ngspice rawfile parsing (binary real + complex, multi-plot)."""

from __future__ import annotations

import numpy as np

from schema_forge.sim.rawfile import find_plot, parse_raw


def test_multi_plot_split(multi_plot_raw) -> None:
    plots = parse_raw(multi_plot_raw)
    assert len(plots) == 2
    assert plots[0].name == "Transient Analysis"
    assert plots[1].name == "AC Analysis"


def test_real_values(multi_plot_raw) -> None:
    tran = find_plot(parse_raw(multi_plot_raw), "time")
    assert tran is not None
    assert np.allclose(tran.data["time"], [0, 1e-3, 2e-3])
    assert np.allclose(tran.data["v(out)"], [0, 0.5, -0.5])


def test_complex_values(multi_plot_raw) -> None:
    ac = find_plot(parse_raw(multi_plot_raw), "frequency")
    assert ac is not None and ac.is_complex
    assert np.allclose(ac.data["v(out)"], [1 + 0j, 0.5 - 0.1j])


def test_ascii_rawfile(tmp_path) -> None:
    text = (
        "Plotname: AC Analysis\nFlags: complex\n"
        "No. Variables: 2\nNo. Points: 2\nVariables:\n"
        "\t0\tfrequency\tfrequency\n\t1\tv(out)\tvoltage\nValues:\n"
        "0\t1.0,0.0\n\t2.0,1.0\n"
        "1\t10.0,0.0\n\t0.5,-0.5\n"
    )
    p = tmp_path / "a.raw"
    p.write_bytes(text.encode("latin-1"))
    ac = parse_raw(p)[0]
    assert np.allclose(ac.data["frequency"], [1 + 0j, 10 + 0j])
    assert np.allclose(ac.data["v(out)"], [2 + 1j, 0.5 - 0.5j])
