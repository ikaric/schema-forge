"""WebSocket: push the full state rollup on connect and on every change."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from schema_forge.logging import get_logger
from schema_forge.paths import Paths
from schema_forge.state.reader import build_state
from schema_forge.state.watcher import watch_state

log = get_logger("schema_forge.api.events")

router = APIRouter()


@router.websocket("/ws")
async def ws_state(websocket: WebSocket) -> None:
    paths: Paths = websocket.app.state.paths
    await websocket.accept()
    try:
        await websocket.send_json(build_state(paths))
        async for state in watch_state(paths):
            await websocket.send_json(state)
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # don't let one socket crash the worker
        log.warning("websocket closed on error: %s", exc)
