#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_FILE="${1:-jkhare_C3.pha}"
LOG_FILE="${2:-phaver_run_C3.log}"
TIMEOUT_SEC="${3:-150}"

if [ ! -f "$SCRIPT_DIR/$MODEL_FILE" ]; then
  echo "Model file not found: $SCRIPT_DIR/$MODEL_FILE" >&2
  exit 1
fi

source "$SCRIPT_DIR/../../setups/env.sh"
cd "$SCRIPT_DIR"

set +e
timeout "$TIMEOUT_SEC" phaverlite "$MODEL_FILE" | tee "$LOG_FILE"
RC=$?
set -e

if [ "$RC" -eq 124 ]; then
  echo ""
  echo "PHAVerLite timed out after ${TIMEOUT_SEC}s (inconclusive run)."
  exit 124
fi

if [ "$RC" -ne 0 ]; then
  echo ""
  echo "PHAVerLite failed with exit code $RC."
  exit "$RC"
fi

echo ""
echo "Generated files:"
ls -1 out_inv out_reachable "$LOG_FILE"

echo ""
echo "Key C3 query lines:"
awk '/^p[1-3]_bad /{print}' "$LOG_FILE"
