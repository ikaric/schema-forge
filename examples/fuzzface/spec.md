# Target spec — Fuzz Face

The acceptance criteria for a 9 V NPN-silicon Fuzz Face driven by a ~50 mV,
1 kHz input. The harness must produce a netlist whose `.measure` / `.four`
results meet every assertion below. (These are deliberately the *behaviours* of
a Fuzz Face, not a component list — the harness chooses the topology and values.)

| Metric | Measure | Target | Why |
|---|---|---|---|
| Output bias | `bias_out` | 3.5–5.5 V | Output near mid-supply for symmetric headroom |
| Gain | `gain_db` | ≥ 25 dB | High-gain two-stage feedback amplifier |
| Distortion | `thd` | ≥ 10 % | Heavy fuzz — hard clipping of both stages |
| Output swing | `vout_pp` | ≥ 2.0 V | Large, hard-clipped output |

```json
{
  "title": "Fuzz Face",
  "analyses": {
    "op": "operating point for bias_out",
    "ac": ".ac dec 50 10 100k for gain_db",
    "tran": ".tran for vout_pp",
    "four": ".four 1000 v(out) for thd"
  },
  "assertions": [
    {"id": "output_bias", "measure": "bias_out", "op": "between", "target": [3.5, 5.5], "unit": "V", "desc": "Output (Q2 collector) biased near mid-supply for symmetric headroom"},
    {"id": "high_gain", "measure": "gain_db", "op": ">=", "target": 25, "unit": "dB", "desc": "High small-signal gain from the two-stage feedback amplifier"},
    {"id": "heavy_fuzz", "measure": "thd", "op": ">=", "target": 10.0, "unit": "%", "desc": "Heavy harmonic distortion at 1 kHz (hard clipping)"},
    {"id": "output_swing", "measure": "vout_pp", "op": ">=", "target": 2.0, "unit": "V", "desc": "Large, hard-clipped output swing"}
  ]
}
```
