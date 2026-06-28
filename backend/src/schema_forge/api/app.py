"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from schema_forge import __version__
from schema_forge.api.exceptions import register_exception_handlers
from schema_forge.api.lifespan import lifespan
from schema_forge.api.routes import build_router
from schema_forge.api.static import mount_spa


def create_app() -> FastAPI:
    """Create and configure the schema-forge server."""
    app = FastAPI(
        title="schema-forge",
        description="Live view of a simulation-verified schematic design loop",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    register_exception_handlers(app)
    app.include_router(build_router())
    # The SPA mount is a catch-all at "/", so it must be registered last.
    mount_spa(app)
    return app
