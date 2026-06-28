"""Fold the markdown workspace + latest sim result into one JSON rollup.

The shape returned by :func:`build_state` is the contract the React frontend
consumes (also written to ``design/state.json`` for a no-server snapshot).
Every parser is deliberately tolerant: a half-written or template file yields
empty/None rather than raising, so the live UI never breaks mid-edit.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from schema_forge.paths import Paths

_TASK_RE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(.+?)\s*$")
_LOG_RE = re.compile(r"^-\s*`([^`]+)`\s+\*\*([^*]+)\*\*\s+—\s+(?:\[(\w+)\]\s+)?(.*)$")
_MAX_LOG = 250


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
    return meta, parts[2].lstrip("\n")


def parse_problem(text: str) -> dict[str, Any]:
    meta, body = _parse_frontmatter(text)
    return {
        "title": meta.get("title", ""),
        "domain": meta.get("domain", ""),
        "tier": meta.get("tier", ""),
        "statement": body.strip(),
    }


def parse_spec(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        from schema_forge.sim.spec import load_spec

        spec = load_spec(path)
    except (ValueError, OSError, json.JSONDecodeError):
        return None
    return {
        "title": spec.title,
        "analyses": spec.analyses,
        "assertions": [a.__dict__ for a in spec.assertions],
    }


def parse_roadmap(text: str) -> dict[str, Any]:
    section = ""
    subgoals: list[dict[str, Any]] = []
    vectors: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.startswith("#"):
            section = line.lstrip("#").strip().lower()
            continue
        m = _TASK_RE.match(line)
        if not m:
            continue
        item = {"text": m.group(2), "done": m.group(1).lower() == "x"}
        if "vector" in section:
            vectors.append(item)
        elif any(k in section for k in ("sub-goal", "subgoal", "required", "block")):
            subgoals.append(item)
    done = sum(1 for s in subgoals if s["done"])
    return {
        "subgoals": subgoals,
        "vectors": vectors,
        "progress": {"done": done, "total": len(subgoals)},
    }


def parse_log(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in text.splitlines():
        m = _LOG_RE.match(line.strip())
        if not m:
            continue
        entries.append(
            {
                "ts": m.group(1),
                "source": m.group(2).strip(),
                "level": (m.group(3) or "info").lower(),
                "message": m.group(4).strip(),
            }
        )
        if len(entries) >= _MAX_LOG:
            break
    return entries


def latest_result(paths: Paths) -> dict[str, Any]:
    if not paths.sims.exists():
        return {}
    results = sorted(
        paths.sims.glob("*.result.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not results:
        return {}
    try:
        data = json.loads(results[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def build_state(paths: Paths | None = None) -> dict[str, Any]:
    """Return the full live state rollup for the frontend."""
    paths = paths or Paths.discover()
    return {
        "initialized": not paths.template_marker.exists(),
        "problem": parse_problem(_read(paths.problem_md)),
        "spec": parse_spec(paths.spec_md),
        "roadmap": parse_roadmap(_read(paths.roadmap_md)),
        "log": parse_log(_read(paths.log_md)),
        "current": latest_result(paths),
        "report_present": paths.report_md.exists(),
        "updated_at": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }
