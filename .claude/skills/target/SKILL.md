---
name: target
description: One-time bootstrap. Define this clone's circuit problem and machine-checkable target spec, scaffold design/, start the live UI on :8000, and open the roadmap. Run once per clone, before /solve.
argument-hint: ""
---

# /target — bootstrap this clone's circuit problem

Run **once** per clone, after `make init` and `make setup`. It turns the template
into a project aimed at one circuit. Read `CLAUDE.md` first.

## 0. Preconditions

- Confirm template state: `design/.schemaforge-template` exists. If it does not,
  this clone is already targeted — stop and tell the user to use `/solve` or
  `/vector` instead.
- Confirm `make init` ran: there must be no `<GH_USERNAME>` / `<GIT_USER_NAME>` /
  `<GIT_USER_EMAIL>` placeholders left (`grep -rl '<GH_USERNAME>' --exclude-dir=.git .`).
  If any remain, tell the user to run `make init` first, then stop.
- Check `ngspice -v`. If missing, warn (the design loop needs it) but continue.

## 1. Gather the problem (interactive)

Use **AskUserQuestion** to collect:

1. **Circuit name** (e.g. "Diode Clipping Overdrive").
2. **Domain** — audio / power / filter / RF / digital / mixed.
3. **Problem statement** — what the circuit must do, in a few sentences.
4. **Target spec** — the measurable acceptance criteria. Press for concrete,
   simulatable numbers: gain (dB), −3 dB corner(s), output swing, clipping
   threshold, THD, bias points, supply, load. Each becomes one assertion.
5. **Scope tier** — T1 (known reference design), T2 (bounded), T3 (novel).

If the user is vague on the spec, propose a reasonable one from the domain and
confirm it — but never invent acceptance you can't simulate.

## 2. Scaffold `design/`

Write, using the user's answers:

- **`design/PROBLEM.md`** — frontmatter (`title`, `domain`, `tier`) + the
  statement as the body. Match `examples/overdrive/PROBLEM.md`.
- **`design/spec.md`** — human-readable prose + a fenced ```json block holding
  `{title, analyses, assertions:[{id, measure, op, target, unit, desc}]}`.
  Each assertion's `measure` is the exact name of an ngspice `.measure`/`.four`
  result the netlist will produce. Ops: `>=` `<=` `>` `<` `==` `~=` (with `tol`)
  `between` (target `[lo,hi]`). Model it on `examples/overdrive/spec.md`.
- **`design/ROADMAP.md`** — one sub-goal checkbox per assertion, an
  `## Attack vectors` section (seed at least one candidate topology), and a
  `## Progress` line `0 / N sub-goals verified.`
- **`design/design-report.md`** — a short skeleton: title, problem, spec table,
  and "Design in progress." sections for schematic / measured results / BOM.
- Append a `/target` entry to **`design/LOG.md`**.

## 3. Activate

- Remove the template marker: `rm design/.schemaforge-template`.
- Refresh the rollup: `schema-forge state > /dev/null` (writes `design/state.json`).
- Ensure the UI is up so the user can watch: if nothing is serving :8000, start
  it in the background — `make dev` (or `uv run uvicorn schema_forge.api.asgi:app
  --port 8000`). Tell the user to open **http://127.0.0.1:8000**.
- For a **T1** clone, you may immediately ask the librarian for the known
  reference topology, have the circuit-designer draft it, and run one
  `schema-forge sim run` so the user sees a first result.

## 4. Commit

Commit `target: initialize <circuit name>` (author = the user; **no** Claude
co-author trailer). Push. Then tell the user to run **`/solve`**.
