"""The target spec: structured, machine-checkable assertions.

``design/spec.md`` is human-readable prose *plus* a single fenced ```json block
that the harness parses. Keeping the structured form as embedded JSON means the
spec renders nicely in the frontend, the ``/target`` skill can author it, and we
parse it with the stdlib (no YAML dependency).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


@dataclass
class Assertion:
    """One checkable claim: ``<measure> <op> <target>``."""

    id: str
    measure: str  # name of the .measure scalar this checks
    op: str  # ">=", "<=", ">", "<", "==", "~=", "between"
    target: float | list[float]
    unit: str = ""
    desc: str = ""
    tol: float | None = None  # absolute tolerance for "~="

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Assertion:
        return cls(
            id=str(d["id"]),
            measure=str(d.get("measure", d["id"])),
            op=str(d.get("op", ">=")),
            target=d["target"],
            unit=str(d.get("unit", "")),
            desc=str(d.get("desc", "")),
            tol=(float(d["tol"]) if d.get("tol") is not None else None),
        )


@dataclass
class Spec:
    """A parsed target spec."""

    title: str
    assertions: list[Assertion] = field(default_factory=list)
    analyses: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Spec:
        return cls(
            title=str(d.get("title", "")),
            assertions=[Assertion.from_dict(a) for a in d.get("assertions", [])],
            analyses=dict(d.get("analyses", {})),
            raw=d,
        )

    def to_dict(self) -> dict[str, Any]:
        return self.raw or {
            "title": self.title,
            "analyses": self.analyses,
            "assertions": [a.__dict__ for a in self.assertions],
        }


def extract_spec_json(markdown: str) -> dict[str, Any]:
    """Return the first fenced ```json block in *markdown* as a dict.

    Raises ``ValueError`` if there is no parseable JSON object.
    """
    m = _JSON_BLOCK_RE.search(markdown)
    if not m:
        raise ValueError("spec.md contains no ```json block")
    data = json.loads(m.group(1))
    if not isinstance(data, dict):
        raise ValueError("spec.md json block must be an object")
    return data


def load_spec_text(markdown: str) -> Spec:
    return Spec.from_dict(extract_spec_json(markdown))


def load_spec(path: str | Path) -> Spec:
    return load_spec_text(Path(path).read_text(encoding="utf-8"))
