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

`PROBLEM.md`, `spec.md`, `ROADMAP.md`, and `LOG.md` already exist in template
form, so **Read each before overwriting it** (the editor requires a read first);
`design-report.md` is new. Write, using the user's answers:

- **`design/PROBLEM.md`** — frontmatter (`title`, `domain`, `tier`) + the
  statement as the markdown body.
- **`design/spec.md`** — human-readable prose + a fenced ```json block holding
  `{title, analyses, assertions:[{id, measure, op, target, unit, desc}]}`.
  Each assertion's `measure` is the exact name of an ngspice `.measure`/`.four`
  result the netlist will produce. Ops: `>=` `<=` `>` `<` `==` `~=` (with `tol`)
  `between` (target `[lo,hi]`). The prose table is for humans; the ```json block
  is what the harness parses.
- **`design/ROADMAP.md`** — one sub-goal checkbox per assertion, an
  `## Attack vectors` section (seed at least one candidate topology), and a
  `## Progress` line `0 / N sub-goals verified.`
- **`design/design-report.md`** — a short skeleton: title, problem, spec table,
  and "Design in progress." sections for schematic / measured results / BOM.
- **`design/research.md`** — a one-line stub (e.g. `_Pending — run /research for
  the prior-art survey._`) so the Research panel reads clean until the survey lands.
- **`design/feedback.md`** — a `# Feedback` heading only; notes arrive via `/feedback`.
- Append a `/target` entry to **`design/LOG.md`**.

## 3. Activate + bring up the live UI

- Remove the template marker: `rm design/.schemaforge-template`.
- Refresh the rollup: `uv run schema-forge state > /dev/null` (writes `design/state.json`).
- **Set up and serve in one shot — the user should never need a second terminal
  for `make dev`.** Run `make setup` (installs backend + frontend deps; safe to
  re-run), then **`make up`** — it builds the SPA and serves it + the live
  WebSocket on :8000 **detached in the background** (idempotent; a no-op if a
  server is already on :8000, and it survives this session). Poll
  `http://127.0.0.1:8000/api/health` until it returns `ok` (a few seconds; tail
  `.claude/local/server.log` if it doesn't come up), then tell the user it is
  **live at http://127.0.0.1:8000** — research, the design loop, and plots all
  update there in realtime. `make down` stops it. (Clones share :8000, so if it's
  occupied by another clone, `make down` there first or run `PORT=<n> make up`.)

**Bootstrap only — do NOT design, draft a netlist, or simulate here.** `/target`
scaffolds the problem and then stops. Drafting netlists, running ngspice, and
iterating to meet the spec are entirely `/solve`'s job — keeping that boundary is
what makes `/target` fast and finite (no design loop to get stuck in). Even a
"known" reference circuit (T1) still needs `/solve` to build and verify it.

## 4. Commit

Commit `target: initialize <circuit name>` (author = the user; **no** Claude
co-author trailer). Push. **Stop here** and tell the user to run **`/research`**
(survey the prior art), then **`/solve`** to begin the design loop.
