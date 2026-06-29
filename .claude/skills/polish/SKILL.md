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
3. **Render the PDF deliverable** — `design/design-report.pdf`, the canonical
   "Design & Build Guide" the user expects. **Always produce this PDF in the
   exact house style** — do not improvise a layout.
   - Author `design/design-report.tex` using the shipped document class
     `\documentclass{schemaforge-report}` (it lives in
     `.claude/skills/polish/assets/`; the build copies it next to the source).
     **Start from the worked reference
     `.claude/skills/polish/assets/example-report.tex`** — copy its skeleton,
     keep its section order, and swap in this circuit's content. Read both it
     and the class before writing the `.tex`. Use the class API, do not restyle:
     - **Cover** — set the fields with `\setcovereyebrow`, `\setcovertitle`,
       `\setcoversubtitle`, `\setcovertopics`, `\setcoverstatus`,
       `\setcovermeta` (rows of `\metalabel{Label} & value\\`), then call
       `\sfmaketitle` as the first thing in the document.
     - **Running head/foot** — `\setdoctitle`, `\setguidekind`, `\setfootleft`
       (tagline), `\setfootstatus` (the green `verified N/N · SPICE` stamp).
     - **Callouts** — `\begin{callout}{blue|green|olive}{Header}…\end{callout}`.
       Blue = framing/intro, green = the honesty/verified contract, olive = a
       load-bearing modelling caveat.
     - **Tables** — wrap a `tabular` in `\rowcolors{2}{white}{sfZebra}`; header
       row via `\sfhead`/`\sfheadcell`; BOM section dividers via
       `\sfgrouprow{<ncols>}{Group}`. Colour PASS with `\textcolor{sfGreen}`.
     - **Schematic** — `\schematicpage{<schematic.pdf>}{<caption>}` for the
       full rotated schematic page. Always use this macro, never a hand-rolled
       `landscape`+`figure`: it vertically centres the image and bounds it so it
       cannot spill past the running header/footer.
   - Mirror the reference structure: cover → "what you are holding" callout →
     what-it-is / how-it-works → research & prior art → design decisions →
     specification (spec table) → schematic (landscape) → how-it-was-verified →
     simulated results (plots) → BOM → build notes → appendix.
   - Build it: `bash .claude/skills/polish/assets/build-report.sh` (converts the
     design SVGs to PDF with `rsvg-convert`, runs `lualatex` twice, leaves
     `design/design-report.pdf` and tidies aux files). The class targets
     **lualatex** — its Latin Modern fonts and CM math are the house style; do
     not switch engines or fonts. If `lualatex`/`rsvg-convert` are missing,
     report it (a `findings/` note) rather than substituting a different style.
4. **Adversarial critic** — dispatch **critic** over the finished report and
   design; record `findings/review-final-<date>.md`. Address credible issues.
5. **Commit** — `polish: final design report` (no Claude co-author) and push.
   Update `STATUS.md` to "complete". Commit `design/design-report.tex` and
   `design/design-report.pdf` alongside the markdown.
