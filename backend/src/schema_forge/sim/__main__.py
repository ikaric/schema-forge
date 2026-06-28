"""``python -m schema_forge.sim`` — the agent-facing simulation CLI.

    python -m schema_forge.sim run design/netlists/main.cir --spec design/spec.md

Runs ngspice, asserts measured results against the spec, renders the schematic +
signal plots into ``design/``, prints a concise human summary, and exits:
    0 = verified (converged + all specs pass)
    1 = failed   (non-convergent)
    2 = converged but one or more specs unmet
"""

from __future__ import annotations

import argparse
import sys

from schema_forge.logging import configure_logging
from schema_forge.paths import Paths
from schema_forge.sim.runner import NgspiceNotFoundError
from schema_forge.sim.verify import verify_netlist


def _cmd_run(args: argparse.Namespace) -> int:
    paths = Paths.discover()
    try:
        result = verify_netlist(
            args.netlist,
            spec_path=args.spec,
            paths=paths,
            render=not args.no_render,
        )
    except NgspiceNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    icon = {"verified": "✓", "converged": "≈", "failed": "✗"}[result.status]
    print(f"{icon} {result.summary}")
    for a in result.assertions:
        mark = "✓" if a["passed"] else "✗"
        print(f"    {mark} {a['id']}: {a['message']}")
    if result.errors:
        print("  errors:")
        for e in result.errors[:10]:
            print(f"    - {e}")
    return result.exit_code()


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(prog="schema_forge.sim")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="simulate a netlist and assert vs spec")
    run.add_argument("netlist", help="path to the SPICE netlist (.cir)")
    run.add_argument(
        "--spec",
        default=None,
        help="path to spec.md (default: design/spec.md in the clone)",
    )
    run.add_argument(
        "--no-render",
        action="store_true",
        help="skip schematic/plot rendering (verify only)",
    )
    run.set_defaults(func=_cmd_run)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
