"""The verification loop: run a netlist, measure, assert, render, persist.

This is the single entry the ``simulator`` agent calls (via ``python -m
schema_forge.sim run``). It performs the whole verify cycle and writes every
artifact the frontend renders, so one invocation moves the live UI forward.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from schema_forge.logging import get_logger
from schema_forge.paths import Paths
from schema_forge.sim.assertions import AssertionResult, all_pass, evaluate
from schema_forge.sim.measure import parse_measures
from schema_forge.sim.rawfile import parse_raw
from schema_forge.sim.runner import run_ngspice
from schema_forge.sim.spec import load_spec

log = get_logger("schema_forge.sim.verify")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class VerifyResult:
    """Everything a single verification produced, mirrored to ``*.result.json``."""

    netlist: str
    status: str  # "verified" | "converged" | "failed"
    converged: bool
    measured: dict[str, float]
    assertions: list[dict[str, Any]]
    errors: list[str]
    warnings: list[str]
    schematic: dict[str, str]
    plots: list[str]
    summary: str
    timestamp: str = field(default_factory=_now)

    @property
    def passed(self) -> bool:
        return self.status == "verified"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    def exit_code(self) -> int:
        return {"verified": 0, "converged": 2, "failed": 1}.get(self.status, 1)


def _rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def verify_netlist(
    netlist_path: str | Path,
    *,
    spec_path: str | Path | None = None,
    paths: Paths | None = None,
    render: bool = True,
) -> VerifyResult:
    """Simulate *netlist_path*, assert vs spec, render artifacts, persist state."""
    paths = paths or Paths.discover()
    paths.ensure_dirs()
    netlist_path = Path(netlist_path).resolve()
    stem = netlist_path.stem

    spec = load_spec(spec_path or paths.spec_md)
    res = run_ngspice(netlist_path, raw_name=f"{stem}.raw", workdir=paths.sims)
    measured, failed = parse_measures(res.log)
    assertion_results: list[AssertionResult] = evaluate(spec, measured, failed)

    plot_rel: list[str] = []
    try:
        from schema_forge.render.plots import clear_plots, write_plots

        # Always clear last run's plot JSONs first, so a run that newly fails or
        # drops an analysis (e.g. no longer sweeps AC) can't leave a stale figure
        # on the dashboard. Then (re)render only for a converged run that wrote a
        # rawfile — a converged .control-only deck legitimately produces none, and
        # we don't want to plot the partial output of an aborted run.
        clear_plots(paths.sims, stem)
        if res.converged and res.raw_path is not None:
            plots = parse_raw(res.raw_path)
            for p in write_plots(plots, paths.sims, stem):
                plot_rel.append(_rel(p, paths.design))
    except Exception as exc:  # rendering must never fail verification
        log.warning("plot rendering failed: %s", exc)

    schematic_rel: dict[str, str] = {}
    if render:
        try:
            from schema_forge.render.schematic import render_schematic

            for key, p in render_schematic(
                netlist_path, paths.schematics, stem
            ).items():
                schematic_rel[key] = _rel(p, paths.design)
        except Exception as exc:
            log.warning("schematic rendering failed: %s", exc)

    if not res.converged:
        status = "failed"
    elif all_pass(assertion_results):
        status = "verified"
    else:
        status = "converged"

    n_pass = sum(1 for a in assertion_results if a.passed)
    n_total = len(assertion_results)
    if status == "failed":
        first = res.errors[0] if res.errors else "ngspice produced no usable output"
        summary = f"Simulated `{netlist_path.name}`: non-convergent — {first}"
    else:
        verb = "→ verified" if status == "verified" else "(specs unmet)"
        summary = (
            f"Simulated `{netlist_path.name}`: converged, "
            f"{n_pass}/{n_total} specs pass {verb}"
        )

    result = VerifyResult(
        netlist=netlist_path.name,
        status=status,
        converged=res.converged,
        measured=measured,
        assertions=[a.to_dict() for a in assertion_results],
        errors=res.errors,
        warnings=res.warnings,
        schematic=schematic_rel,
        plots=plot_rel,
        summary=summary,
    )

    (paths.sims / f"{stem}.result.json").write_text(
        json.dumps(result.to_dict(), indent=2), encoding="utf-8"
    )

    # Append to the activity log + refresh the rollup the frontend reads.
    from schema_forge.state.store import append_log, refresh_state

    append_log(
        paths,
        "simulator",
        summary,
        level="error" if status == "failed" else "info",
    )
    refresh_state(paths)

    return result
