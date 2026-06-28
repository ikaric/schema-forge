"""Serve the built React SPA (or a helpful placeholder when not yet built)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

_PLACEHOLDER = """<!doctype html>
<html><head><meta charset="utf-8"><title>schema-forge</title>
<style>
  body{font:15px/1.6 system-ui,sans-serif;max-width:42rem;
       margin:4rem auto;padding:0 1rem;color:#0f172a}
  code{background:#f1f5f9;padding:.1rem .35rem;border-radius:.25rem}
  a{color:#2563eb}
</style></head>
<body>
<h1>schema-forge</h1>
<p>The backend is running, but the React UI has not been built yet.</p>
<p>Build it once with <code>make build</code> (or <code>make dev</code>),
then reload.</p>
<p>Live data is already available:
<a href="/api/state">/api/state</a> · <a href="/docs">/docs</a></p>
</body></html>"""


def mount_spa(app: FastAPI) -> None:
    """Mount the built SPA at ``/`` if present; else serve a placeholder page."""
    if (STATIC_DIR / "index.html").exists():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")
    else:

        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def _placeholder() -> str:
            return _PLACEHOLDER
