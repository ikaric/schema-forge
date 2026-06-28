---
name: polish
description: Final pass — turn the verified design into a datasheet-style design report (spec table, schematic, BOM, measured-vs-target results, simulation appendix), regenerate the artifacts, run an adversarial critic, and commit. Run after /solve reports the spec is met.
argument-hint: ""
---

# /polish — finalize the design report

Run after `/solve` halts at N/N sub-goals verified. Produces the polished,
human-readable deliverable. Read `CLAUDE.md` first. This skill is autonomous —
do not ask the user questions.

## Steps

1. **Refresh artifacts** — re-run the verified design once so every artifact is
   current: `uv run schema-forge sim run design/netlists/<final>.cir --spec
   design/spec.md`. Confirm it is still `verified` (exit 0). If it regressed,
   stop and report — do not polish a failing design.
2. **Assemble `design/design-report.md`** — a datasheet-style document:
   - Title + one-paragraph summary of what the circuit does.
   - **Spec table** — each assertion with its target and the measured value
     (from the latest `design/sims/<final>.result.json`), all passing.
   - **Schematic** — embed/link `design/schematics/<final>.svg`.
   - **Bill of materials** — every element from the netlist (reference, type,
     value, nets).
   - **Simulation results** — link the signal plots; summarise the transient /
     Bode / THD behaviour in prose.
   - **Notes** — design rationale, assumptions (supply, load), and any caveats.
   - No scaffolding: roadmap/log/findings stay in their own files.
3. **Adversarial critic** — dispatch **critic** over the finished report and
   design; record `findings/review-final-<date>.md`. Address credible issues.
4. **Commit** — `polish: final design report` (no Claude co-author) and push.
   Update `STATUS.md` to "complete".
