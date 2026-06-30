---
name: vector
description: Manage the design's attack vectors (topology strategies) — add a new one, retire a stuck one, or pivot to a different approach. Run between /solve sessions when the strategy should change.
argument-hint: "[add|retire|pivot]"
---

# /vector — manage topology strategies

Attack vectors are the live candidate approaches to meeting the spec (e.g.
"silicon BJT feedback pair", "op-amp + diode clipper", "JFET gain stage").
`/solve` works *within* the current vectors; `/vector` adjusts *which* are live.
They are the `## Attack vectors` checklist in `design/ROADMAP.md`. Read
`CLAUDE.md` first. This skill is interactive — use **AskUserQuestion** when the
user's intent is unclear.

## Modes

- **add** — seed a new vector. Append `- [ ] V<n>: <name> — <one-line idea>` to
  the `## Attack vectors` section of `design/ROADMAP.md`. If it came from a
  reference, note the source in `findings/lit-*.md`.
- **retire** — a vector is a dead end. Move its line to a `## Retired vectors`
  section with a one-line reason, and write `findings/deadend-<vector>-<date>.md`
  capturing *why* (so `/solve` never retries it).
- **pivot** — retire one or more vectors and seed replacements in one ceremony.
  Write `findings/pivot-<date>.md` explaining the strategic change, update both
  sections of `ROADMAP.md`, and append a LOG line.

## After any mode

- Refresh the rollup: `uv run schema-forge state --write > /dev/null`.
- Commit `vector: <add|retire|pivot> <summary>` (no Claude co-author) and push.
- Tell the user to resume with `/solve`.
