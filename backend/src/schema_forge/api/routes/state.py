"""The live state rollup (REST snapshot; the WebSocket pushes the same shape)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from schema_forge.api.dependencies import get_paths
from schema_forge.paths import Paths
from schema_forge.state.reader import build_state

router = APIRouter(tags=["state"])


@router.get("/api/state")
async def get_state(paths: Annotated[Paths, Depends(get_paths)]) -> dict[str, Any]:
    return build_state(paths)
