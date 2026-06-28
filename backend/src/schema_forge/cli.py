"""Top-level ``schema-forge`` command: a thin dispatcher over the subtools.

schema-forge sim run design/netlists/main.cir
schema-forge render schematic design/netlists/main.cir
schema-forge state
schema-forge serve
"""

from __future__ import annotations

import json
import sys

_USAGE = """usage: schema-forge <command> [args]

commands:
  sim ...       run/verify a netlist        (see: schema-forge sim run -h)
  render ...    render schematics/plots     (see: schema-forge render -h)
  state         print the live state rollup as JSON
  serve         run the FastAPI server on the configured host/port
"""


def _serve() -> int:
    import uvicorn

    from schema_forge.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "schema_forge.api.asgi:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(_USAGE)
        return 1
    command, rest = argv[0], argv[1:]

    if command == "sim":
        from schema_forge.sim.__main__ import main as sim_main

        return sim_main(rest)
    if command == "render":
        from schema_forge.render.__main__ import main as render_main

        return render_main(rest)
    if command == "state":
        from schema_forge.paths import Paths
        from schema_forge.state.reader import build_state

        print(json.dumps(build_state(Paths.discover()), indent=2))
        return 0
    if command == "serve":
        return _serve()

    print(_USAGE)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
