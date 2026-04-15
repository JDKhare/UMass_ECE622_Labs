#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_FILE="${1:-jkhare_C4_quick.pha}"
LOG_FILE="${2:-phaver_run_C4_quick.log}"

source "$SCRIPT_DIR/../../../setups/env.sh"
cd "$SCRIPT_DIR"

phaverlite "$MODEL_FILE" | tee "$LOG_FILE"

echo ""
echo "Key C4 probe lines:"
awk '/^p[1-4] /{print}' "$LOG_FILE"
