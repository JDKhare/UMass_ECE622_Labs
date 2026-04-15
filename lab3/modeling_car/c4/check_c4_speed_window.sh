#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${1:-phaver_run_C3.log}"

cd "$SCRIPT_DIR"

if [ ! -f "$LOG_FILE" ]; then
  echo "Missing log file: $LOG_FILE" >&2
  echo "Run ./run_c3.sh first."
  exit 1
fi

echo "C.4 speed-window probes from $LOG_FILE"
echo "-------------------------------------"
awk '/probe_window_reach|probe_60_before4_reach|cond[123]/{print}' "$LOG_FILE"
