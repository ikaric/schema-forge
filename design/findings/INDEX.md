# Findings index

`findings/` is the shared inter-agent notebook. Agents drop notes here and report
back; only the skills (`/target`, `/research`, `/solve`, `/feedback`, `/vector`,
`/polish`) edit ROADMAP.md or commit. Naming conventions (date = `YYYY-MM-DD`):

- `lit-<topic>-<date>.md` — reference/topology/datasheet survey (librarian);
  `/research` folds these into the canonical `design/research.md`
- `sim-<topic>-<date>.md` — notable simulation finding (simulator)
- `deadend-<topic>-<date>.md` — abandoned topology, with the precise reason
- `review-<topic>-<date>.md` — adversarial design review (critic)
- `decision-<topic>-<date>.md` — an orchestrator decision made without the user
- `pivot-<date>.md` — strategy pivot ceremony (`/vector pivot`)

Read this index before starting a new investigation so work is not repeated.
