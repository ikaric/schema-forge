"""Shared test fixtures: synthetic ngspice rawfiles and a sample circuit."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from schema_forge.netlist import Circuit, parse_netlist

SAMPLE_NETLIST = """Diode clipper
V1 in 0 SIN(0 0.5 1k) AC 1
R1 in out 4.7k
D1 out 0 DMOD
D2 0 out DMOD
C1 out 0 10n
.model DMOD D(Is=2.52n)
.tran 10u 5m
.ac dec 20 10 100k
.end
"""


def real_raw_bytes() -> bytes:
    hdr = (
        "Title: t\nDate: d\nPlotname: Transient Analysis\nFlags: real\n"
        "No. Variables: 2\nNo. Points: 3\nVariables:\n"
        "\t0\ttime\ttime\n\t1\tv(out)\tvoltage\nBinary:\n"
    )
    data = np.array([[0, 0], [1e-3, 0.5], [2e-3, -0.5]], dtype="<f8").tobytes()
    return hdr.encode("latin-1") + data


def complex_raw_bytes() -> bytes:
    hdr = (
        "Plotname: AC Analysis\nFlags: complex\n"
        "No. Variables: 2\nNo. Points: 2\nVariables:\n"
        "\t0\tfrequency\tfrequency\n\t1\tv(out)\tvoltage\nBinary:\n"
    )
    flat = np.array([10, 0, 1, 0, 100, 0, 0.5, -0.1], dtype="<f8").tobytes()
    return hdr.encode("latin-1") + flat


@pytest.fixture
def multi_plot_raw(tmp_path: Path) -> Path:
    p = tmp_path / "out.raw"
    p.write_bytes(real_raw_bytes() + complex_raw_bytes())
    return p


@pytest.fixture
def sample_circuit() -> Circuit:
    return parse_netlist(SAMPLE_NETLIST)
