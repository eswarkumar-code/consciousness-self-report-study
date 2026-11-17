#!/usr/bin/env bash
# Run every analysis check in the repository. Exit code is non-zero if any check fails.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
status=0
run() { echo "== $1"; shift; "$@" | tail -1; [[ ${PIPESTATUS[0]} -eq 0 ]] || status=1; }
run "Manuscript tables (code/reproduce_tables.py)"     python3 code/reproduce_tables.py
run "Independent cross-check (tests/independent_checks.py)" python3 tests/independent_checks.py
run "Integrity targets (tests/integrity_targets.py)"   python3 tests/integrity_targets.py
if command -v pdftotext >/dev/null; then
  run "Abstract numbers vs PDF (tests/check_abstract.py)" python3 tests/check_abstract.py
else
  echo "== Abstract numbers vs PDF: NOT RUN (pdftotext not installed)"
fi
exit $status
