"""Spec parsing + assertion evaluation."""

from __future__ import annotations

import pytest

from schema_forge.sim.assertions import all_pass, evaluate
from schema_forge.sim.spec import load_spec_text

SPEC_MD = """# Spec
```json
{"title":"Clipper","assertions":[
 {"id":"a","measure":"vout_pp","op":"<=","target":1.6,"unit":"V"},
 {"id":"b","measure":"f_hi","op":"between","target":[2000,6000],"unit":"Hz"},
 {"id":"c","measure":"g","op":">=","target":10,"unit":"dB"},
 {"id":"d","measure":"x","op":"~=","target":100,"tol":5}
]}
```
"""


@pytest.fixture
def spec():
    return load_spec_text(SPEC_MD)


def test_spec_parses(spec) -> None:
    assert spec.title == "Clipper"
    assert [a.id for a in spec.assertions] == ["a", "b", "c", "d"]


def test_all_pass(spec) -> None:
    res = evaluate(spec, {"vout_pp": 1.4, "f_hi": 3300, "g": 12, "x": 102})
    assert all_pass(res)


def test_failures_reported(spec) -> None:
    res = evaluate(spec, {"vout_pp": 2.0, "f_hi": 9000, "g": 5, "x": 120})
    assert not any(r.passed for r in res)


def test_missing_measure_is_failure(spec) -> None:
    res = evaluate(spec, {"vout_pp": 1.0, "f_hi": 3000, "g": 11})  # no "x"
    by_id = {r.id: r for r in res}
    assert by_id["d"].passed is False
    assert "not produced" in by_id["d"].message


def test_tolerance_operator(spec) -> None:
    assert evaluate(spec, {"vout_pp": 1, "f_hi": 3000, "g": 11, "x": 104})[3].passed
    assert not evaluate(spec, {"vout_pp": 1, "f_hi": 3000, "g": 11, "x": 106})[3].passed


def test_missing_json_block_raises() -> None:
    with pytest.raises(ValueError):
        load_spec_text("# no json here")
