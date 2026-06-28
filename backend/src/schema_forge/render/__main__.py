"""``python -m schema_forge.render`` — render schematics / plots from the CLI.

python -m schema_forge.render schematic design/netlists/main.cir
python -m schema_forge.render plots design/sims/main.raw
"""

from __future__ import annotations

import argparse

from schema_forge.paths import Paths
from schema_forge.render.plots import write_plots
from schema_forge.render.schematic import render_schematic
from schema_forge.sim.rawfile import parse_raw


def _cmd_schematic(args: argparse.Namespace) -> int:
    paths = Paths.discover()
    outdir = args.out_dir or paths.schematics
    stem = args.stem or args.netlist.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    written = render_schematic(args.netlist, outdir, stem)
    for key, path in written.items():
        print(f"{key}: {path}")
    return 0


def _cmd_plots(args: argparse.Namespace) -> int:
    paths = Paths.discover()
    outdir = args.out_dir or paths.sims
    stem = args.stem or args.rawfile.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    written = write_plots(parse_raw(args.rawfile), outdir, stem)
    for path in written:
        print(path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schema_forge.render")
    sub = parser.add_subparsers(dest="command", required=True)

    sch = sub.add_parser("schematic", help="render a netlist to SVG + CircuitJS")
    sch.add_argument("netlist")
    sch.add_argument("--out-dir", default=None)
    sch.add_argument("--stem", default=None)
    sch.set_defaults(func=_cmd_schematic)

    plt = sub.add_parser("plots", help="render Plotly figures from a rawfile")
    plt.add_argument("rawfile")
    plt.add_argument("--out-dir", default=None)
    plt.add_argument("--stem", default=None)
    plt.set_defaults(func=_cmd_plots)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
