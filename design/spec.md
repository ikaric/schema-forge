# Target spec

No spec yet. `/target` writes the machine-checkable target spec here as a fenced
`json` block — the assertions that make `verified` mean something. Each assertion
is `{id, measure, op, target, unit, desc}`, where `measure` names an ngspice
`.measure`/`.four` result and `op` is one of `>=` `<=` `>` `<` `==` `~=` (with
`tol`) or `between` (`target: [lo, hi]`).
