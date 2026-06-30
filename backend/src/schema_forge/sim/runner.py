"""Run a netlist through ngspice in batch mode and classify convergence.

ngspice's exit code is unreliable (it frequently returns 0 even when an analysis
fails), so we classify the *output of the measurement pass* instead: a run
"converged" when no convergence/fatal error markers appear in it. The rawfile is
written only for the signal plots and never gates the verdict — conflating the
two would fail a perfectly solved deck merely for its *style* (a ``.control``-only
deck writes no rawfile). Non-convergence is the harness's free,
compiler-error-style correctness gate.
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


def _run_once(
    cmd: list[str], settings: Settings, cwd: Path
) -> tuple[int, str, str]:
    """Run one ngspice invocation; return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.sim_timeout_s,
            cwd=str(cwd),
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return (
            124,
            _as_text(exc.stdout),
            _as_text(exc.stderr)
            + f"\nngspice timed out after {settings.sim_timeout_s}s",
        )


def run_ngspice(
    netlist_path: str | Path,
    *,
    settings: Settings | None = None,
    raw_name: str = "out.raw",
    workdir: str | Path | None = None,
) -> NgspiceResult:
    """Run a netlist through ngspice (batch) and classify convergence.

    Two passes are required: ``ngspice -b -r <rawfile>`` *disables* ``.measure``
    and ``.four`` ("No .measure possible in batch mode (-b) with -r rawfile
    set!"). So we run once **without** ``-r`` to capture the measurement output
    that verification depends on, and once **with** ``-r`` to write the rawfile
    used only for the signal plots. The measures (the trust root) and the
    convergence verdict both come from pass 1 alone; the rawfile pass only feeds
    plots, so its absence or timeout degrades plots, never the verdict.
    """
    settings = settings or get_settings()
    netlist_path = Path(netlist_path).resolve()
    cwd = Path(workdir).resolve() if workdir else netlist_path.parent
    raw_path = cwd / raw_name
    base = [settings.ngspice_bin, "-b"]

    # Pass 1 — measurements (no -r). Authoritative for convergence + measures.
    try:
        m_rc, m_out, m_err = _run_once(base + [str(netlist_path)], settings, cwd)
    except FileNotFoundError as exc:
        raise NgspiceNotFoundError(
            f"'{settings.ngspice_bin}' not found on PATH. Install ngspice "
            "(e.g. `sudo pacman -S ngspice` / `brew install ngspice`)."
        ) from exc
    # Pass 2 — rawfile for plots (with -r). Measures are intentionally disabled.
    # Clear any stale rawfile first: ngspice writes the file only when a dot-card
    # analysis runs, so without this a deck that no longer emits one would inherit
    # the *previous* run's rawfile and plot stale signals.
    raw_path.unlink(missing_ok=True)
    _run_once(base + ["-r", str(raw_path), str(netlist_path)], settings, cwd)

    # Convergence is read from the measurement pass (pass 1) alone: no
    # convergence/fatal markers in its output. A missing/empty rawfile (a legit
    # .control-only deck writes none) or a pass-2 timeout never flips the verdict.
    errors, warnings = _classify(f"{m_out}\n{m_err}")
    if m_rc == 124:
        errors.append(f"simulation exceeded {settings.sim_timeout_s}s timeout")
    if not f"{m_out}{m_err}".strip():
        errors.append("ngspice produced no output (the netlist did not run)")
    converged = not errors

    has_raw = raw_path.exists() and raw_path.stat().st_size > 0
    return NgspiceResult(
        returncode=m_rc,
        stdout=m_out,
        stderr=m_err,
        raw_path=raw_path if has_raw else None,
        converged=converged,
        errors=errors,
        warnings=warnings,
    )
