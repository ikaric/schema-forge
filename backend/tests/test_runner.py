"""The trust root: convergence is decided by the measurement pass, not the
rawfile. These run real ngspice, so they skip where it isn't installed."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from schema_forge.paths import Paths
from schema_forge.sim.runner import run_ngspice
from schema_forge.sim.verify import verify_netlist

needs_ngspice = pytest.mark.skipif(
    shutil.which("ngspice") is None, reason="ngspice not installed"
)

# A legitimate .control-only deck: it solves and prints a named scalar, but writes
# no rawfile (ngspice captures only dot-card analyses under -r).
CONTROL_ONLY = """* control-only divider
V1 in 0 dc 1
R1 in out 1k
R2 out 0 1k
.control
op
let vout = v(out)
print vout
.endc
.end
"""

# References a model that does not exist -> a real ngspice error.
BAD_MODEL = """* undefined model
V1 in 0 dc 1
Q1 c in 0 QBAD
Rc c 0 1k
.op
.end
"""


@needs_ngspice
def test_control_only_converges_without_rawfile(tmp_path: Path) -> None:
    cir = tmp_path / "c.cir"
    cir.write_text(CONTROL_ONLY)
    res = run_ngspice(cir, workdir=tmp_path)
    # The deck solved, so it converged — even though it produced no rawfile.
    assert res.converged is True
    assert res.raw_path is None
    assert not res.errors


@needs_ngspice
def test_real_error_does_not_converge(tmp_path: Path) -> None:
    cir = tmp_path / "b.cir"
    cir.write_text(BAD_MODEL)
    res = run_ngspice(cir, workdir=tmp_path)
    assert res.converged is False
    assert res.errors


@needs_ngspice
def test_verify_control_only_deck_is_verified(tmp_path: Path) -> None:
    """End-to-end regression for the P0 trust-root bug: a fully-solved deck that
    writes no rawfile must be `verified`, never `failed`."""
    (tmp_path / "pyproject.toml").write_text("")
    design = tmp_path / "design"
    (design / "netlists").mkdir(parents=True)
    spec = design / "spec.md"
    spec.write_text(
        "# spec\n```json\n"
        '{"title": "divider", "assertions": ['
        '{"id": "vout", "measure": "vout", "op": "~=", "target": 0.5, "tol": 0.01}'
        "]}\n```\n"
    )
    cir = design / "netlists" / "c.cir"
    cir.write_text(CONTROL_ONLY)

    res = verify_netlist(cir, spec_path=spec, paths=Paths(root=tmp_path))
    assert res.status == "verified"
    assert res.converged is True
    assert res.measured["vout"] == pytest.approx(0.5, abs=1e-3)
    assert res.plots == []  # no rawfile -> no plots, but still verified
