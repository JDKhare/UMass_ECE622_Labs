#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TITLE="${1:-jkhare_c3}"
SVG_OUT="${2:-graph_c3.svg}"
JPG_OUT="${3:-graph_c3.jpg}"

source "$SCRIPT_DIR/../../setups/env.sh"
cd "$SCRIPT_DIR"

if [ ! -f out_inv ] || [ ! -f out_reachable ]; then
  echo "Missing out_inv or out_reachable. Run ./run_c3.sh first." >&2
  exit 1
fi

graph -T svg -C -B -L "$TITLE" -q 0.1 out_inv -C -q 0.5 out_reachable > "$SVG_OUT"

if command -v convert >/dev/null 2>&1; then
  convert "$SVG_OUT" "$JPG_OUT"
  echo "Generated: $SVG_OUT, $JPG_OUT"
else
  echo "Generated: $SVG_OUT"
  echo "ImageMagick 'convert' not found; skipped JPG conversion."
fi
