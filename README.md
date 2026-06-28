# schema-forge

**An LLM harness for designing electronic schematics that are verified by SPICE
simulation — with a live web UI you watch while it works.**

schema-forge is a GitHub **template**. You clone it once per circuit, point it at
a design problem (a guitar overdrive, a filter, a power supply — any analog or
mixed-signal circuit), and run an autonomous design loop whose trust root is
**ngspice**: nothing is marked `verified` unless the simulation *converges* and
every machine-checkable assertion in your spec passes. It is the electronics
analogue of a Lean-4 proof harness — convergence is the "it compiles" gate, and
the spec-as-assertions is what actually guarantees the circuit does what you
asked.

Unlike a pure CLI harness, schema-forge ships a **monolith web app**. A FastAPI
backend + React frontend stays up on **http://127.0.0.1:8000** and refreshes
itself as the harness works: the problem, the current schematic (rendered two
ways), live signal-simulation plots, spec pass/fail, the activity feed, and
error reports. You watch the design happen instead of reading tickets — all
inter-agent state flows through markdown the UI ingests, not GitHub Issues.

```
LLM ──▶ SPICE netlist ──▶ ngspice -b ──▶ parse .measure ──▶ assert vs spec
  ▲                                                              │
  └──────────────── revise (convergence errors + deltas) ◀───────┘
                              │ on pass
                              ▼
        render schematic (SVG + CircuitJS) + signal plots ──▶ live UI
```

## Quick start

**Prerequisites:** [`ngspice`](https://ngspice.sourceforge.io/),
[`uv`](https://docs.astral.sh/uv/), Node.js 18+, and `git` + the `gh` CLI.
On Arch/CachyOS: `sudo pacman -S ngspice`. On macOS: `brew install ngspice`.

```bash
# 1. Clone the template into your own repo
gh repo create <your-username>/<circuit-name> \
  --template <GH_USERNAME>/schema-forge --private --clone
cd <circuit-name>

# 2. One-time per-clone setup (git identity + dependencies)
make init        # substitutes your name/email/username; sets git author
make setup       # installs backend (uv) + frontend (npm) dependencies

# 3. Open the always-on UI, then define the problem
make dev         # serves the app on http://127.0.0.1:8000

# 4. In Claude Code:
/target          # describe the circuit + target spec; scaffolds design/
/solve           # autonomous design loop — watch it on :8000
```

`/solve` runs unattended and self-paces (`/solve once`, `/solve every 30m`,
`/solve n=5`, `/solve pause|resume`). When every spec sub-goal is met it halts;
`/polish` then writes the final datasheet-style design report. `/vector` lets you
add, retire, or pivot topology strategies between sessions.

### Go-to test: design a Fuzz Face

The reference test is the classic two-transistor **Fuzz Face** — minimal, but
genuinely nonlinear (a DC-coupled feedback pair driven hard into clipping).
Clone fresh, `/target` it, and watch the harness design and tune it:

```text
/target   # describe a 9 V NPN Fuzz Face and its spec:
          #   output biased ~mid-supply, gain ≥ 25 dB, THD ≥ 10 %, hard clipping
/solve    # watch schema-forge design + tune the circuit on :8000
```

Nothing is bundled — the template ships empty, like a fresh project should.

## How verification works (the trust root)

A circuit simulator does **not** hand you a free correctness verdict the way a
proof kernel does. ngspice tells you what a circuit *does*; the only free gate is
**non-convergence** (a broken/unphysical netlist won't solve). So the harness's
guarantee is:

> **`verified` = ngspice converged *and* every assertion in `design/spec.md`
> passes** against the measured `.measure` results.

Everything is honestly tagged: `verified` · `converged` (simulates but a spec is
unmet) · `sketch` (netlist drafted, unsimulated) · `failed` (non-convergent).
The spec you supply at `/target` is therefore load-bearing — it is the part that
makes "it works" mean something.

## Layout (monolith)

```
schema-forge/
├── .claude/            # the harness: skills (/target /solve /vector /polish) + agents
├── backend/            # FastAPI server + the schema_forge package (also the agent CLI)
│   └── src/schema_forge/{sim,render,state,api}/
├── frontend/           # Vite + React + TS SPA (served by the backend on :8000)
├── design/             # PER-PROJECT STATE (markdown-driven; the "issues" replacement)
│   ├── PROBLEM.md  spec.md  ROADMAP.md  LOG.md  design-report.md  state.json
│   └── netlists/  schematics/  sims/  findings/
└── CLAUDE.md           # operating instructions loaded every session
```

The same `schema_forge` package powers two things: an **agent-facing CLI**
(`uv run schema-forge sim run <netlist> --spec design/spec.md`) that runs the
verify cycle and writes artifacts into `design/`, and the **human-facing server**
that reads `design/` and streams it to the UI over a WebSocket.

## License

MIT © 2026 Ilhan Karić. Built on the
[python-template](https://github.com/<GH_USERNAME>/python-template) scaffold and
modelled on the [formalia](https://github.com/<GH_USERNAME>/formalia) proof harness.
