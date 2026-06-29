"""Locate the clone's ``design/`` workspace and its well-known files.

Both the CLI (run from the repo root by agents) and the server need a single,
unambiguous notion of where the per-project state lives. We resolve the repo
root by walking up from a starting directory until we find a directory that
contains both ``pyproject.toml`` and a ``design`` folder, falling back to the
current working directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "design").is_dir():
            return candidate
    return here


@dataclass(frozen=True)
class Paths:
    """Resolved locations of every artifact the harness reads or writes."""

    root: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> Paths:
        return cls(root=find_repo_root(start))

    # --- directories -------------------------------------------------------
    @property
    def design(self) -> Path:
        return self.root / "design"

    @property
    def netlists(self) -> Path:
        return self.design / "netlists"

    @property
    def schematics(self) -> Path:
        return self.design / "schematics"

    @property
    def sims(self) -> Path:
        return self.design / "sims"

    @property
    def findings(self) -> Path:
        return self.design / "findings"

    # --- markdown state files ---------------------------------------------
    @property
    def problem_md(self) -> Path:
        return self.design / "PROBLEM.md"

    @property
    def spec_md(self) -> Path:
        return self.design / "spec.md"

    @property
    def roadmap_md(self) -> Path:
        return self.design / "ROADMAP.md"

    @property
    def log_md(self) -> Path:
        return self.design / "LOG.md"

    @property
    def report_md(self) -> Path:
        return self.design / "design-report.md"

    @property
    def research_md(self) -> Path:
        return self.design / "research.md"

    @property
    def feedback_md(self) -> Path:
        return self.design / "feedback.md"

    @property
    def state_json(self) -> Path:
        return self.design / "state.json"

    @property
    def template_marker(self) -> Path:
        return self.design / ".schemaforge-template"

    def ensure_dirs(self) -> None:
        for d in (self.netlists, self.schematics, self.sims, self.findings):
            d.mkdir(parents=True, exist_ok=True)
