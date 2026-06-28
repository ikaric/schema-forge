"""Application lifespan: resolve paths, configure logging, seed state.json."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from schema_forge.config import get_settings
from schema_forge.logging import configure_logging, get_logger
from schema_forge.paths import Paths
from schema_forge.state.store import refresh_state

log = get_logger("schema_forge.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    paths = Paths.discover()
    app.state.settings = settings
    app.state.paths = paths
    try:
        paths.ensure_dirs()
        refresh_state(paths)
    except Exception as exc:  # never block startup on a half-written workspace
        log.warning("could not seed initial state: %s", exc)
    log.info("schema-forge serving design workspace at %s", paths.design)
    yield
