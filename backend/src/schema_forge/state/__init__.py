"""Project state: parse the markdown workspace into a JSON rollup + watch it.

Inter-agent state flows through markdown (``PROBLEM.md``, ``spec.md``,
``ROADMAP.md``, ``LOG.md``, ``findings/``) and simulation result JSON — never
GitHub Issues. :func:`schema_forge.state.reader.build_state` folds all of it into
one dict the frontend renders; :mod:`schema_forge.state.watcher` streams changes.
"""

from __future__ import annotations
