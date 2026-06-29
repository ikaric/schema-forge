---
name: feedback
description: Ingest a markdown file of design feedback (yours or a review), record each note in design/feedback.md (shown live in the Feedback panel), then run a focused /solve pass that addresses each note and closes it — never relaxing a spec assertion. Usage: /feedback <path-to-notes.md>.
argument-hint: "<path-to-notes.md>"
---

# /feedback — ingest notes, then iterate

The interactive builder-buddy loop: you (or a reviewer) write notes in a
markdown file, `/feedback <file>` records them in the **Feedback** panel on
:8000, and then it **iterates** — a focused `/solve` pass that addresses each
note and closes it. Read `CLAUDE.md` first. This skill is **autonomous** (no
AskUserQuestion) and runs the design loop, so the trust-root rules apply: you
only ever write to `design/`; **never edit the `schema_forge` backend** (the
runner/parsers/assertions could be made to fake a pass). Verified still means
ngspice converged **and** every `design/spec.md` assertion passes.

## Step 0 — preconditions

- The argument (`$ARGUMENTS`) must be a path to a readable markdown file. If
  missing/unreadable → print `Usage: /feedback <path-to-notes.md>` and stop.
- If `design/.schemaforge-template` exists → not targeted; tell the user to run
  `/target`, stop.
- There must be a design to act on (a `design/netlists/*.cir`). If none exists
  yet, tell the user to run `/solve` first, then stop.
- Ensure the UI is up on :8000 (background `make dev` if not).

## Step 1 — ingest the notes

Read the file at `$ARGUMENTS`. Split it into **discrete notes** (each top-level
bullet or paragraph is one note; keep them concrete and self-contained). Append
each to **`design/feedback.md`** (create it with a `# Feedback` header if
absent) as:

```
- [ ] **user** — <the note, one line> · open
```

Do **not** put ` · ` inside the note text — that separates the status. Refresh
the rollup (`uv run schema-forge state > /dev/null`) so the notes appear in the
Feedback panel immediately, append a `/feedback` LOG line, and commit
`feedback: ingest <n> note(s)` (no Claude co-author) + push.

## Step 2 — iterate (a focused /solve pass)

Work the **open** notes, highest-impact first. For each:

1. **Reference check** — consult `design/research.md`; if the note needs a
   topology you haven't grounded, dispatch **librarian** (`findings/lit-*.md`).
2. **Design** — dispatch **circuit-designer** (+ the relevant domain specialist)
   to revise `design/netlists/<block>.cir` toward the note **while keeping every
   spec assertion passing**. Keep `.measure`/`.four` names matching the spec.
3. **Simulate** — dispatch **simulator** to run
   `uv run schema-forge sim run design/netlists/<block>.cir --spec design/spec.md`.
   The trust root. Only ever **one** simulation at a time. It refreshes the UI.
4. **Feedback loop** — on non-converge or a regressed assertion, hand the deltas
   back to circuit-designer and revise. Cap ~6 revisions per note.
5. **Review** — dispatch **critic** to confirm the note is genuinely addressed
   and nothing else regressed (`findings/review-*.md`).

**Never relax a `design/spec.md` assertion to satisfy a note** — that is the
electronics `sorry`. If a note genuinely conflicts with the spec, do not silently
comply: write `findings/decision-<topic>-<date>.md` with the reasoning, leave the
note as `· conflicts-with-spec`, and surface it to the user.

## Step 3 — close + promote

When a note is addressed, flip its line in `design/feedback.md`:

```
- [x] **user** — <the note> · addressed
```

Update `design/design-report.md` to reflect the change, append a LOG line,
refresh the rollup, and commit + push per note (`feedback: address — <short>`).
When all notes are resolved (or blocked with a recorded decision), recompute the
`ROADMAP.md` progress meter, commit `status: <summary>`, push, and report what
changed. Halt — do not reschedule unless invoked with `/solve`-style pacing args.
