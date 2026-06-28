# Target spec — Diode Clipping Overdrive Stage

Human-readable targets with the machine-checkable form below. The harness reads
the fenced `json` block and asserts each `measure` (an ngspice `.measure` /
`.four` result) against its target. A circuit is `verified` only when ngspice
converges **and** every assertion here passes.

| Metric | Measure | Target | Why |
|---|---|---|---|
| Clipping present | `vout_pp` | ≤ 1.4 V | Clip node clamped below the 1.4 V open-circuit input swing |
| Diode clamp | `vout_max` | ≤ 0.75 V | Positive clamp set by the diode forward drop |
| Distortion | `thd` | ≥ 3 % | Harmonic distortion at 1 kHz — the overdrive signature |
| Tone corner | `f_corner` | 45–110 Hz | High-pass −3 dB corner from C2/RL |
| Passband gain | `gain_db` | −1.5 … 0.5 dB | Near-unity gain above the corner |

```json
{
  "title": "Diode Clipping Overdrive Stage",
  "analyses": {
    "tran": ".tran 20u 10m",
    "ac": ".ac dec 50 10 100k",
    "four": ".four 1000 v(clip)"
  },
  "assertions": [
    {"id": "clipping", "measure": "vout_pp", "op": "<=", "target": 1.4, "unit": "V", "desc": "Clip node clamped below the 1.4 V open-circuit input swing (soft clipping present)"},
    {"id": "clamp", "measure": "vout_max", "op": "<=", "target": 0.75, "unit": "V", "desc": "Positive clamp set by the diode forward drop"},
    {"id": "distortion", "measure": "thd", "op": ">=", "target": 3.0, "unit": "%", "desc": "Total harmonic distortion at 1 kHz"},
    {"id": "corner", "measure": "f_corner", "op": "between", "target": [45, 110], "unit": "Hz", "desc": "High-pass -3 dB tone corner from C2/RL"},
    {"id": "passband", "measure": "gain_db", "op": "between", "target": [-1.5, 0.5], "unit": "dB", "desc": "Near-unity passband gain above the corner"}
  ]
}
```
