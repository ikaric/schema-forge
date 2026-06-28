"""Assemble the application router."""

from __future__ import annotations

from fastapi import APIRouter

from schema_forge.api.routes import artifacts, events, health, state


def build_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health.router)
    router.include_router(state.router)
    router.include_router(artifacts.router)
    router.include_router(events.router)
    return router
