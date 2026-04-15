#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_FILE="${1:-jkhare_C3.pha}"
LOG_FILE="${2:-phaver_run_C3.log}"
TIMEOUT_SEC="${3:-180}"

cd "$SCRIPT_DIR"

./run_c3.sh "$MODEL_FILE" "$LOG_FILE" "$TIMEOUT_SEC"

echo ""
echo "C3 property interpretation (bad-state reachability):"
echo "  P1 bad: x >= 500 and v > 0 (crossing second intersection while moving)"
echo "  P2 bad: Brake and v >= 46.5"
echo "  P3 bad: Brake and v >= 40.0"
echo ""
awk '/^p[1-3]_bad /{print "  " $0}' "$LOG_FILE"
echo ""
echo "Rule: only 'unreachable' is a formal proof in this over-approximate setting."
