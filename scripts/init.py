#!/usr/bin/env python3
"""One-time per-clone setup for a schema-forge clone.

Substitutes the three template placeholders across the repo:

    <GH_USERNAME>     GitHub username (referenced in README.md, CLAUDE.md)
    <GIT_USER_NAME>   Full name for git commit authorship
    <GIT_USER_EMAIL>  Email for git commit authorship

Also writes the repo-local user.name / user.email so subsequent commits
carry the expected identity (never Claude / Anthropic — this repo is
presented as the user's own work).

Idempotent: a second invocation finds no placeholders and exits 0 with a
"nothing to do" message. Safe to re-run if you mistyped a value (reset by
`git checkout -- .` before re-running).

Usage:
    make init

Non-interactive form (CI, scripted setups):
    GH_USERNAME=foo GIT_USER_NAME='Foo Bar' \\
      GIT_USER_EMAIL=foo@bar.example make init
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

PLACEHOLDERS = ("<GH_USERNAME>", "<GIT_USER_NAME>", "<GIT_USER_EMAIL>")
SKIP_DIR_NAMES = {
    ".git", ".venv", "node_modules", "build", "dist",
    "__pycache__", ".cache", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}

REPO = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()


def is_skipped(rel: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in rel.parts)


def find_target_files() -> list[Path]:
    """Files anywhere in the repo containing at least one placeholder.

    Excludes this script itself (it stores the placeholders as Python string
    literals, which substitution would corrupt).
    """
    targets: list[Path] = []
    for p in REPO.rglob("*"):
        if not p.is_file() or p.resolve() == SELF:
            continue
        if is_skipped(p.relative_to(REPO)):
            continue
        try:
            content = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(tok in content for tok in PLACEHOLDERS):
            targets.append(p)
    return targets


def prompt(env_name: str, label: str, validator) -> str:
    val = os.environ.get(env_name, "").strip()
    while True:
        if not val:
            try:
                val = input(f"{label}: ").strip()
            except EOFError:
                sys.exit(
                    f"\nerror: {env_name} required (set the env var or "
                    f"run interactively)"
                )
        err = validator(val)
        if err is None:
            return val
        print(f"  invalid: {err}", file=sys.stderr)
        val = ""


def v_gh(v: str) -> str | None:
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}", v):
        return "must match GitHub username rules (alphanumeric + single hyphens, 1-39 chars)"
    return None


def v_name(v: str) -> str | None:
    if not v.strip():
        return "must be non-empty"
    if "<" in v or ">" in v:
        return "must not contain angle brackets"
    return None


def v_email(v: str) -> str | None:
    if "@" not in v or " " in v or "<" in v or ">" in v:
        return "must look like an email address (no spaces, no angle brackets)"
    return None


def main() -> int:
    targets = find_target_files()
    if not targets:
        print("init: no placeholders found — this clone is already initialised.")
        return 0

    print("schema-forge — one-time clone init.")
    print(f"Found {len(targets)} file(s) with template placeholders.\n")

    gh = prompt("GH_USERNAME", "GitHub username", v_gh)
    name = prompt("GIT_USER_NAME", "Full name (git author)", v_name)
    email = prompt("GIT_USER_EMAIL", "Email (git author)", v_email)

    subs = {
        "<GH_USERNAME>": gh,
        "<GIT_USER_NAME>": name,
        "<GIT_USER_EMAIL>": email,
    }

    print("\nSubstituting:")
    for p in targets:
        text = p.read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        p.write_text(text, encoding="utf-8")
        print(f"  - {p.relative_to(REPO)}")

    print("\nSetting repo-local git identity:")
    subprocess.run(["git", "config", "user.name", name], cwd=REPO, check=True)
    subprocess.run(["git", "config", "user.email", email], cwd=REPO, check=True)
    print(f"  user.name  = {name}")
    print(f"  user.email = {email}")

    print(
        "\nDone. Suggested next steps:\n"
        "  1. make setup                   (install backend + frontend deps)\n"
        "  2. git add -A && git commit -m 'init: per-clone setup'\n"
        "  3. /target  (in Claude Code, to scaffold the circuit problem)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
