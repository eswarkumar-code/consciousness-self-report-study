#!/usr/bin/env bash
# Build manuscript/main.pdf from the LaTeX source and copy it to paper/manuscript.pdf.
# Requires: XeLaTeX and BibTeX (TeX Live 2023 or later), the TeX Gyre Termes/Heros fonts,
# and DejaVu Sans Mono. Optional regeneration steps need Python 3, matplotlib and pandoc.
#
#   bash manuscript/build.sh            # compile main.tex as it stands
#   bash manuscript/build.sh --regen    # first regenerate figures and main.tex from the
#                                       # frozen data and paper/manuscript_v8.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ "${1:-}" == "--regen" ]]; then
  python3 code/make_figures.py data manuscript/figures pdf
  python3 code/md_to_latex.py paper/manuscript_v8.md manuscript/main.tex
fi
cd manuscript
# Fixed timestamp so repeated builds of the same source give the same PDF.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1794873600}"   # 2026-11-17 00:00:00 UTC
export FORCE_SOURCE_DATE=1
rm -f main.aux main.bbl main.blg main.out main.toc
xelatex -interaction=nonstopmode -halt-on-error main.tex > build.log
bibtex main >> build.log
for pass in 1 2 3 4; do
  xelatex -interaction=nonstopmode -halt-on-error main.tex >> build.log
  grep -q "Rerun to get" main.log || [[ $pass -lt 2 ]] || break
done
if grep -q -E "undefined|Rerun to get" main.log; then
  echo "Unresolved references or citations remain; see manuscript/main.log" >&2
  exit 1
fi
if grep -q "Overfull" main.log; then
  echo "Warning: overfull boxes reported; see manuscript/main.log" >&2
fi
if [[ -d ../paper ]]; then cp main.pdf ../paper/manuscript.pdf; fi
echo "Built manuscript/main.pdf ($(grep -o 'Output written on main.pdf ([0-9]* pages' main.log | grep -o '[0-9]* pages'))"
