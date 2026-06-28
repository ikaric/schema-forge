"""Evaluate measured ngspice results against the spec's assertions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from schema_forge.sim.spec import Assertion, Spec


@dataclass
class AssertionResult:
    """The outcome of checking one :class:`Assertion` against a measurement."""

    id: str
    passed: bool
    op: str
    measured: float | None
    target: float | list[float]
    unit: str
    desc: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _fmt(value: float, unit: str) -> str:
    text = f"{value:.4g}"
    return f"{text} {unit}".strip()


def _check(a: Assertion, measured: float) -> tuple[bool, str]:
    op, target, unit = a.op, a.target, a.unit
    m = _fmt(measured, unit)
    if op == "between":
        lo, hi = float(target[0]), float(target[1])  # type: ignore[index]
        ok = lo <= measured <= hi
        return ok, f"{m} {'in' if ok else 'NOT in'} [{lo:.4g}, {hi:.4g}] {unit}".strip()
    t = float(target)  # type: ignore[arg-type]
    tt = _fmt(t, unit)
    if op == "~=":
        tol = a.tol if a.tol is not None else abs(t) * 0.05
        ok = abs(measured - t) <= tol
        return ok, f"{m} {'≈' if ok else '≉'} {tt} (±{tol:.4g})"
    ops = {
        ">=": (measured >= t, "≥"),
        "<=": (measured <= t, "≤"),
        ">": (measured > t, ">"),
        "<": (measured < t, "<"),
        "==": (math.isclose(measured, t, rel_tol=1e-9, abs_tol=1e-12), "="),
    }
    if op not in ops:
        return False, f"unknown operator '{op}'"
    ok, sym = ops[op]
    return ok, f"{m} {sym if ok else '!' + sym} {tt}"


def evaluate(
    spec: Spec,
    measured: dict[str, float],
    failed_measures: list[str] | None = None,
) -> list[AssertionResult]:
    """Return one :class:`AssertionResult` per assertion in *spec*."""
    failed = set(failed_measures or [])
    results: list[AssertionResult] = []
    for a in spec.assertions:
        if a.measure in failed or a.measure not in measured:
            results.append(
                AssertionResult(
                    id=a.id,
                    passed=False,
                    op=a.op,
                    measured=None,
                    target=a.target,
                    unit=a.unit,
                    desc=a.desc,
                    message=f"measure '{a.measure}' not produced by the simulation",
                )
            )
            continue
        value = measured[a.measure]
        ok, msg = _check(a, value)
        results.append(
            AssertionResult(
                id=a.id,
                passed=ok,
                op=a.op,
                measured=value,
                target=a.target,
                unit=a.unit,
                desc=a.desc,
                message=msg,
            )
        )
    return results


def all_pass(results: list[AssertionResult]) -> bool:
    return bool(results) and all(r.passed for r in results)
