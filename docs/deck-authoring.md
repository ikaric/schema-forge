# Writing a checkable ngspice deck

A netlist is **checkable** when the harness can read a scalar named exactly like
each spec assertion's `measure` field out of the ngspice run. This page is the
short, battle-tested guide to doing that without tripping ngspice's batch-mode
footguns. Read it before hand-authoring a non-trivial deck; copy a template
below and adapt it.

## The two-pass model (why this matters)

`schema-forge sim run` runs ngspice **twice** on your deck:

1. **Measurement pass** — `ngspice -b <deck>` (no `-r`). This is the **trust
   root**: convergence and every `.measure`/`.four`/`print` scalar come from here.
2. **Rawfile pass** — `ngspice -b -r <deck>.raw <deck>`. This only feeds the
   **signal plots**. ngspice *disables* `.measure` under `-r`, and writes **only
   dot-card analyses** (`.tran`/`.ac`/`.op`) to the rawfile — `.control`-block
   `tran`/`ac` are **not** captured.

Consequences you must design around:

- **A `.control`-only deck is fine.** It converges and measures normally; it just
  produces no rawfile, so it renders no plots. That is *not* a failure.
- **Plots come from dot-cards.** If you do your analysis inside `.control`, add a
  dot-card `.tran`/`.ac` *as well* so the plots have data (Template 2).
- **Dot-cards run after `.control`,** inheriting its final source state. If you
  `alter` the stimulus inside `.control` (e.g. to read DC bias with the drive
  off), **restore it** before the deck ends or the plotted transient is flat.

## Batch-mode footguns (each one bites silently)

- **`.measure` binds to ONE analysis.** With both `.tran` *and* `.ac` dot-cards,
  a dot-card `.measure tran …` consumes the transient and the AC analysis reports
  *"no data saved for A.C. … run aborted"* — the **whole run fails**. So: put at
  most **one** analysis kind alongside dot-card `.measure` cards. Need measures
  from *both* AC and transient? Use a `.control` block (Template 2).
- **`db()`/`abs()` parse only inside `.control`.** `.measure ac … find vdb(out)`
  won't parse, and `.measure … find par('db(...)')` is a **fatal** error
  (`no such function 'db'`). Inside `.control`, `let g = db(v(out))` then
  `meas ac … find g …` works.
- **`avg`/`rms` of an expression** works in a dot-card (`.measure tran isup avg
  par('abs(i(vcc))')`) but inside `.control` needs the vector first
  (`let isup = abs(i(vcc))` then `meas tran … avg isup`).
- **`meas` and `print` emit `name = value`** lines — that is exactly what the
  harness parses, so a name like `gain_db` becomes the `gain_db` measure. Names
  with parentheses (`v(out) = …`) are *not* parsed (by design — avoids noise), so
  always assign a bare name: `let gain_db = db(v(out))`.
- **Rails are dropped from plots automatically.** A node held constant across the
  sweep (a supply) is excluded from the signal plots, so you don't need a `.save`
  allowlist just to keep a `-9 V` trace from crushing the Bode autoscale.

## Matching the spec

For every assertion `{ "measure": "gain_db", … }`, the deck must emit a scalar
**named exactly `gain_db`** (case-insensitive) in the measurement pass — via a
`.measure`/`.four` card or a `.control` `meas`/`print`. THD from `.four` is read
as `thd`.

---

## Template 1 — single-analysis dot-card deck

The common case: all your measures come from **one** analysis kind. Plots come
for free from the dot-card. (Here: transient swing + THD.)

```spice
* <title> — single-analysis transient deck
Vcc vcc 0 dc 9
V1 in 0 SIN(0 0.1 1k)
R1 in b 100k
R2 vcc b 470k
Q1 c b 0 QNPN
Rc vcc c 4.7k
Cout c out 1u
Rload out 0 100k
.model QNPN NPN(Bf=200)
.tran 5u 20m
.measure tran vpp_out PP v(out) FROM=5m TO=20m
.four 1k v(out)
.end
```

Swap `.tran`/`.measure tran`/`.four` for `.ac`/`.measure ac` if your spec is a
frequency-response one — just keep it to a **single analysis kind**.

## Template 2 — multi-analysis `.control` deck

When the spec needs measures from **both** AC and transient (e.g. mid-band gain
*and* output swing), do the measuring inside `.control`, then add dot-card
analyses purely so the rawfile (and thus the plots) has data.

```spice
* <title> — multi-analysis .control deck (AC gain + transient swing)
Vcc vcc 0 dc 9
V1 in 0 dc 0 ac 1 SIN(0 0.1 1k)
R1 in b 100k
R2 vcc b 470k
Q1 c b 0 QNPN
Rc vcc c 4.7k
Cout c out 1u
Rload out 0 100k
.model QNPN NPN(Bf=200)
.control
  ac dec 20 10 100k
  let gain_db = db(v(out))
  meas ac gain_mid find gain_db at=1k
  tran 5u 20m
  meas tran vpp_out PP v(out) from=5m to=20m
.endc
* dot-card analyses below exist only to populate the -r rawfile for the plots
.ac dec 20 10 100k
.tran 5u 20m
.end
```

`meas` prints its own `name = value`, so no trailing `print` is needed (a
cross-plot `print` after switching analyses just warns). If `.control` alters the
stimulus, restore it before the `.endc` so the dot-card transient below isn't
captured drive-off.

> Both templates above are verified to run clean on ngspice 46 (measurement pass
> emits the named scalars; rawfile pass captures the dot-card analyses for plots).
