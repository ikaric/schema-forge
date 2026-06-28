"""schema-forge — an LLM harness for simulation-verified electronic schematic design.

The package powers two consumers from one implementation:

* an **agent-facing CLI** (``python -m schema_forge.sim`` / ``.render``) that
  runs ngspice, asserts measured results against the spec, and renders
  schematics + signal plots into ``design/``; and
* a **human-facing FastAPI server** (`schema_forge.api`) that reads ``design/`` and
  streams it live to the React frontend on http://127.0.0.1:8000.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
