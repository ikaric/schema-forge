# Example: Fuzz Face — the harness go-to test

The classic two-transistor fuzz pedal: minimal, but genuinely nonlinear
(DC-coupled feedback pair driven hard into clipping). This is a **target-only**
example — it ships the problem and spec but *no netlist*. The point is to watch
schema-forge **design** it:

```bash
make seed-fuzzface     # loads the problem + spec into design/ (no netlist)
make dev               # http://127.0.0.1:8000
/solve                 # in Claude Code — watch it design + tune the Fuzz Face
```

The harness will have the librarian fetch the reference topology
(<https://fuzzcentral.ssguitar.com/fuzzface.php>, ElectroSmash), the
analog-designer + circuit-designer draft a netlist, and the simulator verify it
against `spec.md` — biasing for headroom, high gain, and heavy clipping/THD.

Files:

- `PROBLEM.md` — the problem statement + scope tier (T1, a known reference design)
- `spec.md` — the machine-checkable acceptance criteria (bias, gain, THD, swing)
