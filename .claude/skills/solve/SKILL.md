---
name: solve
description: Resume autonomous design work on this clone — pick a sub-goal, design + simulate + assert against the spec, promote on a verified pass, commit and push. Self-looping; halts when the spec is met. Watch it live on http://127.0.0.1:8000.
argument-hint: "[every <dur>] [n=<int>] [once] [pause|resume]"
---

# /solve — autonomous design loop

Resume and advance the design. Runs unattended; the user watches on
**http://127.0.0.1:8000**. Read `CLAUDE.md` first. **Never call AskUserQuestion**
here — make the most reasonable decision from the spec + repo precedent and
record non-obvious choices in `findings/decision-*.md`.

## Pacing (self-looping — no `/loop` wrapper)

- bare `/solve` — run an iteration, then schedule the next with a 60 s gap.
- `/solve every 30m` — gap between iterations. `/solve n=5` — at most 5
  iterations. `/solve once` — a single pass, no reschedule.
- `/solve pause` — write `.claude/local/solve-paused` and stop. `/solve resume`
  — delete it and continue.
- Reschedule the next iteration with **ScheduleWakeup** for gaps ≤ 1 h, or a
  one-shot durable **CronCreate** for gaps > 1 h. State lives in git + `design/`,
  so a restart just re-runs `/solve`. On any halt, do **not** reschedule.

## Step 0 — halt checks (before any work)

- If `.claude/local/solve-paused` exists → stop, no reschedule.
- If `design/.schemaforge-template` exists → tell the user to run `/target`, stop.
- If `design/ROADMAP.md` shows **N/N** sub-goals verified → target reached;
  emit a halt message suggesting `/polish`; do not reschedule.

## Step 1 — resume context

- Ensure the UI is up (start `make dev` / uvicorn on :8000 in the background if
  not), so the user sees this session live.
- Read `design/PROBLEM.md`, `design/spec.md`, `design/ROADMAP.md`,
  `design/LOG.md`, `design/findings/INDEX.md`, and `git log --oneline -n 15`.
  Summarise where things stand in 2–3 sentences and append a `/solve` LOG line.

## Step 2 — work loop (the verify cycle)

Pick the highest-value **open** sub-goal from `ROADMAP.md` (one whose assertion
is not yet passing). Then:

1. **Reference check** — if this needs a topology you haven't grounded, dispatch
   **librarian** (known designs, datasheets, app notes; anti-reinvention). Notes
   land in `findings/lit-*.md`.
2. **Design** — dispatch **circuit-designer** (and the relevant domain
   specialist) to write or revise `design/netlists/<block>.cir`. The netlist
   **must** include `.measure`/`.four` cards whose names match the spec
   assertions' `measure` fields.
3. **Simulate** — dispatch **simulator** to run
   `uv run schema-forge sim run design/netlists/<block>.cir --spec design/spec.md`.
   This is the trust root. It writes the schematic, plots, result JSON, and LOG,
   so the UI updates immediately. Only ever run **one** simulation at a time.
4. **Feedback** — if non-convergent or an assertion is unmet, hand the simulator's
   errors + measured-vs-target deltas back to circuit-designer and revise. Cap at
   ~6 revisions or ~30 min per sub-goal; if still stuck, write
   `findings/deadend-*.md` and move on (or open a vector via `/vector`).
5. **Review** — on a `verified` pass, dispatch **critic** for an adversarial read
   (stability, biasing, thermal, realistic parts, does it truly meet spec).
   Report → `findings/review-*.md`. A credible objection blocks promotion.
6. **Promote** — update `design/design-report.md` (fold the block in with its
   measured results), tick the sub-goal in `ROADMAP.md`, append a LOG line, and
   commit + push per work unit. Then pick the next sub-goal.

## Step 3 — session end

Refresh the rollup (`uv run schema-forge state > /dev/null`), recompute the `ROADMAP.md`
progress meter, update `STATUS.md` (focus + blocker), commit `status: <summary>`,
and push.

## Halt cases (no reschedule)

- **Target reached** (N/N verified) → suggest `/polish`.
- **Exhaustion** — no open sub-goal and no vector that advances the spec → write
  `findings/decision-exhausted-*.md`, suggest `/vector`.
- **Count** — `n` iterations done. **Pause** — sentinel present.

Everything is in markdown and git — **no `gh issue` anywhere**.
