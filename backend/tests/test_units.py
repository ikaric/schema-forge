"""SI/engineering value parsing."""

from __future__ import annotations

import pytest

from schema_forge.units import parse_si


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("4.7k", 4700.0),
        ("10n", 1e-8),
        ("1meg", 1e6),
        ("100", 100.0),
        ("2.2u", 2.2e-6),
        ("4u7", 4.7e-6),
        ("1k5", 1500.0),
        ("5V", 5.0),
    ],
)
def test_parse_si(text: str, expected: float) -> None:
    got = parse_si(text)
    assert got is not None and abs(got - expected) <= abs(expected) * 1e-9 + 1e-18


def test_parse_si_none() -> None:
    assert parse_si(None) is None
    assert parse_si("abc") is None
