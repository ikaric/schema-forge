"""ASGI entrypoint: ``uvicorn schema_forge.api.asgi:app``."""

from __future__ import annotations

from schema_forge.api.app import create_app

app = create_app()
