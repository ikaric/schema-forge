# Example: Diode Clipping Overdrive Stage

A worked example that proves the harness end to end — a symmetric soft clipper
that converges easily, shows real nonlinearity (clipping + THD), and has an
assertable small-signal corner.

```bash
make seed-overdrive                                 # copies these files into design/
schema-forge sim run design/netlists/overdrive.cir  # simulate + assert vs spec
make dev                                             # watch it on http://127.0.0.1:8000
```

Files:

- `overdrive.cir` — the SPICE netlist (the source of truth ngspice consumes)
- `spec.md` — the machine-checkable target spec (clipping, clamp, THD, corner, gain)
- `PROBLEM.md` — the problem statement + scope tier

`schema-forge sim run` writes the schematic (`design/schematics/`), signal plots
(`design/sims/*.plot.json`), and a result (`design/sims/overdrive.result.json`)
that the live UI renders.
