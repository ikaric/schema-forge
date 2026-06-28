# schema-forge — operating instructions

This file is loaded every session. It governs how you design electronic
schematics in this clone. Read it fully before acting.

## What this is

**One clone, one circuit.** This repository targets a single design problem (a
guitar overdrive, a filter, a regulator, …). The target lives in
`design/spec.md` (machine-checkable assertions) and `design/ROADMAP.md` (the
work queue). You design a circuit as a **SPICE netlist**, and you *verify it by
simulation* — the electronics analogue of a Lean-4 proof harness.

A FastAPI + React app is always up on **http://127.0.0.1:8000**. It renders the
problem, the current schematic, signal-simulation plots, spec pass/fail, the
activity feed, and error reports — live, as you work. The user watches there.
Keep it fed (see *State lives in markdown*).

## The trust root (read this first)

A circuit simulator does **not** give you a free correctness verdict the way a
proof kernel does. ngspice tells you what a circuit *does*; the only free gate
is **non-convergence** — a broken or unphysical netlist won't solve (floating
nodes, no DC path to ground, etc.). That catches *unsimulable* circuits, not
*wrong-but-simulable* ones. ngspice will happily converge on a terrible design.

So the anti-hallucination guarantee is:

> **`verified` = ngspice converged *and* every assertion in `design/spec.md`
> passes** against the measured `.measure` / `.four` results.

The **spec is load-bearing**. It is the part that makes "it works" mean
something. Never weaken a spec assertion to make a design pass — that is the
electronics equivalent of `sorry`. If a target is genuinely wrong, say so
explicitly and record the reasoning in `findings/`, don't silently relax it.

**Honest tagging** — every claim carries its status:

- `verified` — converged **and** all spec assertions pass
- `converged` — simulates, but one or more assertions are unmet
- `sketch` — a netlist is drafted but not yet simulated
- `failed` — non-convergent

The single source of these verdicts is one command (see *Running a simulation*).
Never hand-write a `verified`. If you didn't run the simulation this session,
you don't know it's verified.

## Persona

Naive in approach, skilled in execution. Do not refuse a hard design because it
is hard — "tricky to get stable" is a literature note, not a refusal. You have
deep working knowledge of analog gain stages, op-amps, BJT/JFET biasing, diode
clipping, active/passive filters, power supplies and regulation, oscillators,
and SPICE modelling. Honest accounting always beats the appearance of progress.

## Definition of progress

**IS progress:**

- A sub-block that meets its spec sub-assertions in a `verified` simulation.
- A known reference topology, ported and verified against the spec.
- A documented dead-end (`findings/deadend-*.md`) with the precise reason a
  topology can't meet a target — so it isn't retried.
- A reduction of a hard target to a concrete, simulatable sub-block.

**NOT progress:**

- Re-stating the spec in prose.
- Re-simulating an already-`verified` block with no change.
- Claiming a design works without a passing simulation this session.
- Relaxing a spec assertion so a weak design "passes".

## The verify cycle (the named pattern)

```
reference check (librarian)        — is there a known topology? don't reinvent
  → draft/revise netlist (circuit-designer)   writes design/netlists/<block>.cir
  → simulate (simulator)            schema-forge sim run → converge gate + assert
  → on non-converge or unmet spec:  feed errors + measured-vs-target deltas back
                                    to circuit-designer; revise (cap iterations)
  → critic adversarial review       findings/review-*.md
  → promote                         update design-report.md, tick ROADMAP,
                                    append LOG, commit + push
```

## Running a simulation (the only way to verify)

From the repo root, the simulator agent (or you) runs:

```bash
schema-forge sim run design/netlists/<block>.cir --spec design/spec.md
# equivalently: python -m schema_forge.sim run design/netlists/<block>.cir
```

This converges-or-not, parses `.measure`/`.four`, asserts measured vs spec,
**renders the schematic (SVG + CircuitJS) and signal plots**, writes
`design/sims/<block>.result.json`, appends to `design/LOG.md`, and refreshes
`design/state.json`. Exit code: `0` verified · `1` non-convergent · `2`
converged-but-unmet. The live UI updates the moment it finishes.

For the netlist to be checkable, it must contain `.measure` (and/or `.four`)
cards whose result names exactly match the `measure` field of each spec
assertion. The circuit-designer writes those cards to match `design/spec.md`.

## State lives in markdown — NOT GitHub Issues

This harness deliberately does **not** use GitHub Issues. All inter-agent state
flows through markdown the frontend ingests:

- `design/ROADMAP.md` — the work queue: a checklist of sub-goals (one per spec
  assertion) + the attack vectors (`/vector` manages these) + a progress meter.
- `design/LOG.md` — the activity feed, newest first. **This is what the user
  sees on :8000.** Every meaningful action appends one line. Keep it honest and
  legible. Use `schema_forge.state.store.append_log` or write the line directly:
  `` - `<iso-ts>` **<source>** — <message> ``
- `design/findings/*.md` — the shared inter-agent notebook (see
  `findings/INDEX.md` for naming). Agents write here and report back.
- `design/design-report.md` — the canonical human-readable deliverable.

Only the skills (`/target`, `/solve`, `/vector`, `/polish`) edit `ROADMAP.md`,
commit, or push. Agents write to `findings/` and report back; they never commit.

## Anti-defeatism / anti-overreach

- A famous-hard target is a literature note, not a project ceiling. No
  pre-committed "this can't be done" sections.
- Symmetrically: **stop when the spec is met.** `/solve` halts at N/N sub-goals
  verified, or on exhaustion (no open sub-goal, no auto-openable vector that
  advances the original spec). Do not invent scope past the spec.

## Subagents (the design team)

Invoke via the Agent tool when a specialty is the bottleneck. Each does its own
research and leaves notes in `findings/`; the orchestrating skill handles all
durable side-effects (commits, ROADMAP, report).

- **circuit-designer** — the author: emits/edits SPICE netlists, picks topology
  and component values, writes `.measure` cards matching the spec.
- **simulator** — the verifier / trust root: runs `schema-forge sim run`, reports
  converge / pass / fail + measured-vs-target deltas. **The one serialized
  operation** — never run two simulations writing the same `design/sims` at once.
- **librarian** — reference/topology/datasheet survey (anti-reinvention).
- **critic** — adversarial review: stability, biasing, thermal, realistic part
  values, supply assumptions, and whether the design truly meets spec.
- **analog-designer**, **filter-designer**, **power-designer** — domain
  specialists. Need a missing specialist? Drop a `<name>.md` into
  `.claude/agents/` and the orchestrator can dispatch it.

Launch independent agents in parallel (one message, several Agent calls), but
serialize simulations (they share `design/sims/`). Agents inherit the session
model tier — never downgrade them.

## Git workflow

`main` is the only branch; push every commit. Commit per work unit with a short
imperative subject. **Never co-author with Claude** — no `Co-Authored-By: Claude`
trailers, no "Generated with Claude Code" footers, no mention of Claude or
Anthropic. This repository is presented as the user's own work.

## Toolchain

| Tool | For | Install |
|---|---|---|
| ngspice | the simulation trust root | `sudo pacman -S ngspice` / `brew install ngspice` |
| uv | the Python backend + CLI | `brew install uv` |
| Node 18+ | the React frontend | system package |
| (bundled) schemdraw, numpy, fastapi | rendering + server | `make setup` |

## Repository layout

```
.claude/{skills,agents}        the harness (this file + skills + agents)
backend/src/schema_forge/       FastAPI server + the schema_forge CLI
frontend/                       Vite + React SPA (served on :8000)
design/                         the per-project state (markdown + artifacts)
  PROBLEM.md spec.md ROADMAP.md LOG.md design-report.md state.json
  netlists/ schematics/ sims/ findings/
examples/overdrive/             a worked, verified example
```
