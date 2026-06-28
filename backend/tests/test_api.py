"""HTTP surface: health, state, artifacts."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from schema_forge.api.app import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def test_health(client) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and "version" in body


def test_state_shape(client) -> None:
    body = client.get("/api/state").json()
    for key in ("initialized", "problem", "spec", "roadmap", "log", "current"):
        assert key in body


def test_artifact_served(client) -> None:
    # PROBLEM.md exists in the template design/ workspace.
    resp = client.get("/api/artifacts/PROBLEM.md")
    assert resp.status_code == 200


def test_artifact_missing_is_404(client) -> None:
    assert client.get("/api/artifacts/does/not/exist.json").status_code == 404
