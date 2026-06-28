"""Write-side helpers: append to the activity log and refresh ``state.json``."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from schema_forge.paths import Paths
from schema_forge.state.reader import build_state

_LOG_HEADER = "# Activity log\n\nNewest first. Each entry is one harness action.\n\n"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def append_log(
    paths: Paths,
    source: str,
    message: str,
    level: str = "info",
) -> None:
    """Prepend one entry to ``design/LOG.md`` (newest first)."""
    paths.design.mkdir(parents=True, exist_ok=True)
    tag = "" if level == "info" else f"[{level}] "
    entry = f"- `{_now()}` **{source}** — {tag}{message}\n"

    log = paths.log_md
    if log.exists():
        content = log.read_text(encoding="utf-8")
        head, sep, rest = content.partition("\n\n")
        new = f"{head}{sep}{entry}{rest}" if sep else _LOG_HEADER + entry
    else:
        new = _LOG_HEADER + entry
    log.write_text(new, encoding="utf-8")


def refresh_state(paths: Paths) -> dict[str, Any]:
    """Rebuild the state rollup and persist it to ``design/state.json``."""
    state = build_state(paths)
    paths.design.mkdir(parents=True, exist_ok=True)
    paths.state_json.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state
