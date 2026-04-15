#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_FILE="${1:-jkhare_C4.pha}"
LOG_FILE="${2:-phaver_run_C4.log}"
TIMEOUT_SEC="${3:-180}"

source "$SCRIPT_DIR/../../../setups/env.sh"
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
echo "Key C4 query lines:"
awk '/^q_before /{print} /^q_after /{print}' "$LOG_FILE"
