"""Liveness + version."""

from __future__ import annotations

from fastapi import APIRouter

from schema_forge import __version__

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
