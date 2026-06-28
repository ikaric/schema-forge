"""Watch ``design/`` for changes and stream rebuilt state to subscribers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from watchfiles import awatch

from schema_forge.paths import Paths
from schema_forge.state.reader import build_state


async def watch_state(paths: Paths) -> AsyncIterator[dict[str, Any]]:
    """Yield a fresh state rollup on every change under ``design/``.

    watchfiles coalesces bursts of filesystem events, so a single multi-file
    update from one harness step produces one push, not a storm.
    """
    paths.design.mkdir(parents=True, exist_ok=True)
    async for _changes in awatch(str(paths.design)):
        yield build_state(paths)
