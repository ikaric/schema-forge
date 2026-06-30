"""The top-level ``schema-forge`` dispatcher."""

from __future__ import annotations

from pathlib import Path

from schema_forge.cli import main
from schema_forge.paths import Paths


def _workspace(tmp_path: Path) -> Paths:
    (tmp_path / "pyproject.toml").write_text("")
    paths = Paths(root=tmp_path)
    paths.design.mkdir()
    paths.ensure_dirs()
    return paths


def test_state_prints_without_persisting(tmp_path, monkeypatch, capsys) -> None:
    paths = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["state"]) == 0
    assert capsys.readouterr().out.strip().startswith("{")  # printed JSON
    assert not paths.state_json.exists()  # ...but did not write the snapshot


def test_state_write_persists_snapshot(tmp_path, monkeypatch) -> None:
    paths = _workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert main(["state", "--write"]) == 0
    assert paths.state_json.exists()  # --write persists design/state.json


def test_unknown_command_usage(capsys) -> None:
    assert main(["nope"]) == 1
    assert "usage:" in capsys.readouterr().out
