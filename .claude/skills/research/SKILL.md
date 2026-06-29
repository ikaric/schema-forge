---
name: research
description: Prior-art survey for this clone's circuit. Run after /target, before /solve — dispatch the librarian to gather known topologies, datasheets, reference component values, and cited sources into design/research.md (rendered live in the Research panel on :8000). Re-runnable; never designs or simulates.
argument-hint: ""
---

# /research — survey the prior art before designing

Run **after `/target`, before `/solve`**. It fills the **Research** panel on
:8000 with a grounded survey of how this circuit class is built in the wild, so
`/solve` starts from known topologies and real component values instead of
reinventing. Read `CLAUDE.md` first. This skill is **autonomous** — do not call
AskUserQuestion.

**Survey only — do NOT draft a netlist, design, or simulate here.** Like
`/target`, `/research` has one job and then stops; building and verifying the
circuit is entirely `/solve`'s. Keeping that boundary is what makes `/research`
finite. You only ever write to `design/` (markdown + findings); never touch the
`schema_forge` backend.

## Step 0 — preconditions

- If `design/.schemaforge-template` exists → not targeted yet; tell the user to
  run `/target` first, then stop.
- `design/spec.md` must exist. If not, stop and point to `/target`.
- Ensure the UI is up (start `make dev` / uvicorn on :8000 in the background if
  nothing is serving) so the survey renders live as it lands.

## Step 1 — frame the search

Read `design/PROBLEM.md`, `design/spec.md`, `design/ROADMAP.md`, and
`design/findings/INDEX.md`. In 2–3 sentences, fix the circuit class and the
specific questions the design must answer (the spec assertions: gain, corners,
swing, bias, THD, supply…). Append a `/research` LOG line.

## Step 2 — dispatch the librarian (anti-reinvention)

Dispatch the **librarian** (and the relevant domain specialist —
`analog-designer` / `filter-designer` / `power-designer` — when it sharpens the
search). Ask for, with **citations**:

- **Similar topologies** for this circuit class, each with its real component
  values and bias points (e.g. classic variants, reference designs).
- **Datasheets & device models** — the parts and SPICE models that fit the spec.
- **Reference component values** — typical starting values for each stage.
- **Open questions** — where the literature disagrees or the spec is demanding,
  flagged for `/solve` to resolve by simulation.

Use WebSearch/WebFetch where available; otherwise draw on deep domain knowledge
and say so. Raw notes go to `design/findings/lit-<topic>-<date>.md`.

## Step 3 — fold into design/research.md (the canonical survey)

Assemble the librarian's findings into **`design/research.md`** — the curated
document the Research panel renders (markdown, scrollable). Suggested sections:

```markdown
# Research — <circuit>

## Similar topologies
… each with real component values + bias points, cited …

## Datasheets & device models
…

## Reference component values
…

## Open questions for the design
… handed to /solve to settle by simulation …

## Sources
… cited links / app notes / analyses …
```

Keep it honest: cite sources, mark anything uncertain, never invent a value as
if it were measured. Re-running `/research` **augments** this file (merge new
findings; don't duplicate).

## Step 4 — record + commit

- Refresh the rollup: `uv run schema-forge state > /dev/null`.
- Append a `/research` LOG line summarising what was gathered.
- Commit `research: prior-art survey for <circuit>` (author = the user; **no**
  Claude co-author trailer) and push.

**Stop here** and tell the user to run **`/solve`** to begin the design loop —
it will consult `design/research.md` in its reference-check step.
