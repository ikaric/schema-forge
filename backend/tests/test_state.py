"""Markdown workspace parsing + state rollup."""

from __future__ import annotations

import json
from pathlib import Path

from schema_forge.paths import Paths
from schema_forge.state.reader import (
    build_state,
    parse_feedback,
    parse_log,
    parse_problem,
    parse_research,
    parse_roadmap,
)
from schema_forge.state.store import append_log, refresh_state


def _seed(tmp_path: Path) -> Paths:
    paths = Paths(root=tmp_path)
    paths.design.mkdir()
    paths.ensure_dirs()
    return paths


def test_parse_problem_frontmatter() -> None:
    p = parse_problem("---\ntitle: Overdrive\ndomain: audio\ntier: T2\n---\n\nClip it.")
    assert p == {
        "title": "Overdrive",
        "domain": "audio",
        "tier": "T2",
        "statement": "Clip it.",
    }


def test_parse_roadmap_buckets_and_progress() -> None:
    md = (
        "# Roadmap\n## Sub-goals\n- [x] g1: done\n- [ ] g2: todo\n"
        "## Attack vectors\n- [ ] V1: diodes\n"
    )
    r = parse_roadmap(md)
    assert r["progress"] == {"done": 1, "total": 2}
    assert len(r["vectors"]) == 1 and r["vectors"][0]["text"] == "V1: diodes"


def test_parse_log_entries() -> None:
    md = (
        "# Activity log\n\n"
        "- `2026-06-28T20:00:00Z` **simulator** — [error] non-convergent\n"
        "- `2026-06-28T19:00:00Z` **/solve** — picked sub-goal\n"
    )
    entries = parse_log(md)
    assert entries[0]["source"] == "simulator" and entries[0]["level"] == "error"
    assert entries[1]["level"] == "info"


def test_build_state_initialized_flag(tmp_path) -> None:
    paths = _seed(tmp_path)
    paths.template_marker.write_text("marker")
    assert build_state(paths)["initialized"] is False
    paths.template_marker.unlink()
    assert build_state(paths)["initialized"] is True


def test_append_log_prepends_newest(tmp_path) -> None:
    paths = _seed(tmp_path)
    append_log(paths, "simulator", "first")
    append_log(paths, "critic", "second")
    entries = parse_log(paths.log_md.read_text())
    assert entries[0]["message"] == "second"  # newest first
    assert entries[1]["message"] == "first"


def test_refresh_state_writes_json(tmp_path) -> None:
    paths = _seed(tmp_path)
    state = refresh_state(paths)
    assert paths.state_json.exists()
    assert json.loads(paths.state_json.read_text())["updated_at"] == state["updated_at"]


def test_parse_feedback_states_and_fields() -> None:
    md = (
        "# Feedback\n\n"
        "- [ ] **user** — Bias too low for symmetric clip · open\n"
        "- [x] **critic** — Check bias at 0 C · addressed · pass 2\n"
        "- [ ] **user** — Try germanium devices · queued\n"
        "not a note line\n"
    )
    notes = parse_feedback(md)
    assert [n["state"] for n in notes] == ["open", "done", "planned"]
    assert notes[0]["from"] == "user"
    assert notes[1]["status"] == "addressed · pass 2"  # status keeps inner separators
    assert notes[2]["msg"] == "Try germanium devices"


def test_parse_research_prefers_research_md_then_findings(tmp_path) -> None:
    paths = _seed(tmp_path)
    assert parse_research(paths) == ""  # nothing yet → placeholder in the UI
    (paths.findings / "lit-fuzz-2026-06-29.md").write_text("# Fuzz Face\n\nA classic.")
    survey = parse_research(paths)
    assert "Fuzz Face" in survey and "lit-fuzz" in survey  # stitched from findings
    paths.research_md.write_text("# Curated\n\nThe real survey.")
    assert parse_research(paths) == "# Curated\n\nThe real survey."  # research.md wins


def test_build_state_includes_research_and_feedback(tmp_path) -> None:
    paths = _seed(tmp_path)
    state = build_state(paths)
    assert state["research"] == "" and state["feedback"] == []
    paths.feedback_md.write_text("- [ ] **user** — make it louder · open\n")
    assert build_state(paths)["feedback"][0]["msg"] == "make it louder"


def test_latest_result_picked_by_mtime(tmp_path) -> None:
    paths = _seed(tmp_path)
    (paths.sims / "a.result.json").write_text(json.dumps({"status": "failed"}))
    (paths.sims / "b.result.json").write_text(json.dumps({"status": "verified"}))
    # b is newer (written second); build_state should surface it.
    assert build_state(paths)["current"]["status"] == "verified"
