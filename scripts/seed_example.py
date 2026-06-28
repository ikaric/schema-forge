#!/usr/bin/env python3
"""Seed one of the bundled examples into ``design/`` (``make seed-*``).

A shortcut so you can watch the harness work without running ``/target`` first.
It copies an example's problem + spec into the live ``design/`` workspace,
generates a roadmap from the spec, drops the template marker, and refreshes
``state.json``.

Two flavours of example:

* **target-only** (e.g. ``fuzzface``) — problem + spec only, no netlist. This is
  the go-to test of the harness: run ``/solve`` and watch it *design* the circuit.
* **with-reference** (e.g. ``overdrive``) — also ships a known-good netlist, so
  ``schema-forge sim run`` works immediately to exercise the pipeline.

Usage:
    python scripts/seed_example.py [name]      # default: fuzzface
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend" / "src"))

from schema_forge.paths import Paths  # noqa: E402
from schema_forge.sim.spec import load_spec  # noqa: E402
from schema_forge.state.store import append_log, refresh_state  # noqa: E402


def _roadmap(spec_title: str, tier: str, assertions: list) -> str:
    goals = "\n".join(
        f"- [ ] {a.id}: {a.desc or a.measure} "
        f"(`{a.measure}` {a.op} {a.target} {a.unit})".rstrip()
        for a in assertions
    )
    return f"""# Roadmap — {spec_title}

Scope tier: {tier}

## Sub-goals

One per spec assertion; a sub-goal is done when its assertion passes in a
`verified` simulation.

{goals}

## Attack vectors

- [ ] V1: known reference topology (have the librarian fetch it, then design to spec)

## Progress

0 / {len(assertions)} sub-goals verified.
"""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    name = argv[0] if argv else "fuzzface"
    example = REPO / "examples" / name
    if not (example / "spec.md").exists():
        print(f"error: no example named '{name}' in examples/", file=sys.stderr)
        return 1

    paths = Paths.discover(REPO)
    paths.ensure_dirs()

    shutil.copy2(example / "spec.md", paths.spec_md)
    shutil.copy2(example / "PROBLEM.md", paths.problem_md)

    # Copy a reference netlist only if the example ships one.
    netlist = example / f"{name}.cir"
    seeded_netlist = netlist.exists()
    if seeded_netlist:
        shutil.copy2(netlist, paths.netlists / f"{name}.cir")

    spec = load_spec(paths.spec_md)
    meta = (example / "PROBLEM.md").read_text(encoding="utf-8")
    tier = next(
        (line.split(":", 1)[1].strip() for line in meta.splitlines()
         if line.lower().startswith("tier:")),
        "T2",
    )
    paths.roadmap_md.write_text(
        _roadmap(spec.title, tier, spec.assertions), encoding="utf-8"
    )

    paths.template_marker.unlink(missing_ok=True)
    append_log(paths, "seed", f"Seeded the '{name}' example.")
    refresh_state(paths)

    print(f"Seeded the '{name}' example into design/. Next:")
    if seeded_netlist:
        print(f"  schema-forge sim run design/netlists/{name}.cir")
    else:
        print("  /solve   (in Claude Code — watch the harness design it on :8000)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
