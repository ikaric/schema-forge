"""Serve design artifacts (schematic SVG/CircuitJS, plot JSON, netlists)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from schema_forge.api.dependencies import get_paths
from schema_forge.paths import Paths

router = APIRouter(tags=["artifacts"])

_MEDIA = {
    ".svg": "image/svg+xml",
    ".json": "application/json",
    ".circuitjs": "text/plain; charset=utf-8",
    ".cir": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


@router.get("/api/artifacts/{path:path}")
async def get_artifact(
    path: str, paths: Annotated[Paths, Depends(get_paths)]
) -> FileResponse:
    base = paths.design.resolve()
    target = (base / path).resolve()
    # Path-traversal guard: the resolved target must stay inside design/.
    if base != target and base not in target.parents:
        raise HTTPException(status_code=403, detail="forbidden")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(target, media_type=_MEDIA.get(target.suffix))
