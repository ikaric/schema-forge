#!/usr/bin/env bash
# build-report.sh — compile design/design-report.tex into design-report.pdf
# in the canonical schema-forge "Design & Build Guide" style.
#
# Usage:  bash .claude/skills/polish/assets/build-report.sh
# Run from the repo root. Idempotent; leaves the PDF at design/design-report.pdf.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ASSETS="$ROOT/.claude/skills/polish/assets"
DESIGN="$ROOT/design"
TEX="$DESIGN/design-report.tex"

[ -f "$TEX" ] || { echo "error: $TEX not found — author it first"; exit 1; }
command -v lualatex >/dev/null || { echo "error: lualatex not found"; exit 1; }

# 1. Make the class visible to lualatex (copy next to the source).
cp "$ASSETS/schemaforge-report.cls" "$DESIGN/schemaforge-report.cls"

# 2. Rasterless SVG -> PDF for every figure the report references.
#    schema-forge renders schematics/plots as SVG; LaTeX wants PDF.
if command -v rsvg-convert >/dev/null; then
  shopt -s nullglob
  for svg in "$DESIGN"/schematics/*.svg "$DESIGN"/sims/*.svg; do
    pdf="${svg%.svg}.pdf"
    [ "$svg" -nt "$pdf" ] && rsvg-convert -f pdf -o "$pdf" "$svg"
  done
  shopt -u nullglob
else
  echo "warn: rsvg-convert missing — embed PDF/PNG figures directly or install librsvg"
fi

# 3. Compile twice (TOC, lastpage, references settle on the second pass).
cd "$DESIGN"
for pass in 1 2; do
  lualatex -interaction=nonstopmode -halt-on-error design-report.tex \
    >/tmp/sf-report-pass$pass.log 2>&1 || {
      echo "error: lualatex pass $pass failed — see /tmp/sf-report-pass$pass.log"
      grep -iE '^!|fatal|undefined' /tmp/sf-report-pass$pass.log | head -20 || true
      exit 1
    }
done

# 4. Tidy aux files; keep only the deliverable.
rm -f design-report.aux design-report.log design-report.out design-report.toc \
      schemaforge-report.cls
echo "ok: design/design-report.pdf"
