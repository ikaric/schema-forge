"""ngspice .measure / .four output parsing."""

from __future__ import annotations

from schema_forge.sim.measure import parse_measures

LOG = """
Doing analysis at TEMP = 27.0
vout_pp             =  1.402000e+00
f_hi                =  3.301000e+03 targ=  1 trig= 2
gain_db             = -2.5
Measurement corner FAILED

Fourier analysis for v(clip):
Total Harmonic Distortion: 8.421000 percent
"""


def test_scalar_measures() -> None:
    vals, _ = parse_measures(LOG)
    assert abs(vals["vout_pp"] - 1.402) < 1e-9
    assert abs(vals["f_hi"] - 3301.0) < 1e-6
    assert abs(vals["gain_db"] + 2.5) < 1e-9


def test_failed_measure_collected() -> None:
    _, failed = parse_measures(LOG)
    assert "corner" in failed


def test_four_thd_captured() -> None:
    vals, _ = parse_measures(LOG)
    assert abs(vals["thd"] - 8.421) < 1e-6


def test_header_noise_ignored() -> None:
    vals, _ = parse_measures("No. Points: 5\nTitle: x\nreal = 3.0\n")
    assert "no" not in vals and "title" not in vals
    assert vals["real"] == 3.0
