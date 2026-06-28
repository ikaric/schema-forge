"""Run a netlist through ngspice in batch mode and classify convergence.

ngspice's exit code is unreliable (it frequently returns 0 even when an analysis
fails), so we classify the *output* instead: a run "converged" when no
convergence/fatal error markers appear and a non-empty rawfile was produced.
Non-convergence is the harness's free, compiler-error-style correctness gate.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from schema_forge.config import Settings, get_settings

# Substrings (lower-cased) that indicate a real simulation failure.
_ERROR_MARKERS = (
    "no convergence",
    "singular matrix",
    "timestep too small",
    "iteration limit reached",
    "fatal",
    "aborted",
    "is not a valid",
    "unknown subckt",
    "can't find",
    "cannot find",
    "error on line",
    "error:",
)


class NgspiceNotFoundError(RuntimeError):
    """Raised when the ngspice executable is not on PATH."""


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else value.decode("utf-8", "replace")


@dataclass
class NgspiceResult:
    """Outcome of one ngspice batch invocation."""

    returncode: int
    stdout: str
    stderr: str
    raw_path: Path | None
    converged: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def log(self) -> str:
        return f"{self.stdout}\n{self.stderr}"


def _classify(output: str) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for line in output.splitlines():
        low = line.lower().strip()
        if not low:
            continue
        if any(marker in low for marker in _ERROR_MARKERS):
            errors.append(line.strip())
        elif low.startswith("warning") or "warning:" in low:
            warnings.append(line.strip())
    return errors, warnings


def run_ngspice(
    netlist_path: str | Path,
    *,
    settings: Settings | None = None,
    raw_name: str = "out.raw",
    workdir: str | Path | None = None,
) -> NgspiceResult:
    """Invoke ``ngspice -b`` on *netlist_path* and return a classified result."""
    settings = settings or get_settings()
    netlist_path = Path(netlist_path).resolve()
    cwd = Path(workdir).resolve() if workdir else netlist_path.parent
    raw_path = cwd / raw_name

    cmd = [settings.ngspice_bin, "-b", "-r", str(raw_path), str(netlist_path)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.sim_timeout_s,
            cwd=str(cwd),
        )
    except FileNotFoundError as exc:
        raise NgspiceNotFoundError(
            f"'{settings.ngspice_bin}' not found on PATH. Install ngspice "
            "(e.g. `sudo pacman -S ngspice` / `brew install ngspice`)."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        return NgspiceResult(
            returncode=124,
            stdout=_as_text(exc.stdout),
            stderr=_as_text(exc.stderr)
            + f"\nngspice timed out after {settings.sim_timeout_s}s",
            raw_path=raw_path if raw_path.exists() else None,
            converged=False,
            errors=[f"simulation exceeded {settings.sim_timeout_s}s timeout"],
        )

    errors, warnings = _classify(proc.stdout + "\n" + proc.stderr)
    has_raw = raw_path.exists() and raw_path.stat().st_size > 0
    converged = not errors and has_raw

    return NgspiceResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        raw_path=raw_path if has_raw else None,
        converged=converged,
        errors=errors,
        warnings=warnings,
    )
