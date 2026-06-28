"""Netlist parser."""

from __future__ import annotations

from schema_forge.netlist import parse_netlist


def test_title_strips_comment_marker(sample_circuit) -> None:
    assert sample_circuit.title == "Diode clipper"


def test_elements_and_nodes(sample_circuit) -> None:
    names = [e.name for e in sample_circuit.elements]
    assert names == ["V1", "R1", "D1", "D2", "C1"]
    assert sample_circuit.nodes == ["in", "0", "out"]


def test_kinds_and_values(sample_circuit) -> None:
    r1 = next(e for e in sample_circuit.elements if e.name == "R1")
    assert r1.kind == "R" and r1.nodes == ["in", "out"] and r1.value == "4.7k"


def test_directives_and_analyses(sample_circuit) -> None:
    assert sample_circuit.analyses() == ["tran", "ac"]
    assert any(d.startswith(".model") for d in sample_circuit.directives)


def test_continuation_lines_join() -> None:
    c = parse_netlist("title\nR1 a b 1k\n+ tc=0.1\n.end\n")
    assert c.elements[0].value is not None and "tc=0.1" in c.elements[0].value


def test_transistor_gets_three_nodes() -> None:
    c = parse_netlist("title\nQ1 c bb e QMOD\n.end\n")
    assert c.elements[0].nodes == ["c", "bb", "e"]
