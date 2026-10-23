#!/usr/bin/env bash
# Run the invented demo end to end and fail unless every balance checks and
# every month reconciles ("unexplained is 0 in every month").
# Needs beancount: pip install beancount
# Usage: tools/test-demo.sh [OUT_DIR]   (default: a temporary folder)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ $# -gt 0 ]; then
  OUT="$1"; mkdir -p "$OUT"
else
  OUT="$(mktemp -d)"; trap 'rm -rf "$OUT"' EXIT
fi
LOG="$OUT/run.log"
(cd "$OUT" && bash "$ROOT/skills/dashboard-finanze/examples/demo/run.sh" "$OUT/demo") 2>&1 | tee "$LOG"
grep -q "unexplained is 0 in every month" "$LOG"
test -s "$OUT/demo/finanze-demo.html"
echo "demo OK"
