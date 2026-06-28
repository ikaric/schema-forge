"""Shared request dependencies."""

from __future__ import annotations

from fastapi import Request

from schema_forge.paths import Paths


def get_paths(request: Request) -> Paths:
    """Return the clone's resolved :class:`Paths`, cached on app state."""
    return request.app.state.paths  # type: ignore[no-any-return]
