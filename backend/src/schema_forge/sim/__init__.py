"""Simulation + verification: ngspice batch runs, result parsing, spec asserts.

This package is the harness's *trust root*. A circuit is ``verified`` only when
ngspice **converges** (the free, compiler-error-style gate) **and** every
machine-checkable assertion in the spec passes against the measured results.
Convergence alone never implies correctness — the spec is what carries the
guarantee.

Import submodules directly (``schema_forge.sim.verify``, ``schema_forge.sim.spec``)
to keep this package import side-effect free.
"""

from __future__ import annotations
