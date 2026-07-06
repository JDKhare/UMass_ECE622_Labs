#!/usr/bin/env bash
# plotutils graph: (V_DS, I_D) = columns 2 and 6 from PHAVerLite out_* (6 columns).
# Draws invariant (out_inv) then reachable (out_reachable) with axis labels V_DS (V), I_D (A).
#
# Usage (from lab4):
#   bash plot_graph_id_vds.sh [out_inv] [out_reachable] [output.svg] [title]
# Defaults: out_inv out_reachable nmos_graph_id_vds.svg

set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB}/../setups/env.sh"
cd "$LAB"

INV="${1:-out_inv}"
REACH="${2:-out_reachable}"
OUT="${3:-nmos_graph_id_vds.svg}"
TITLE="${4:-NMOS I_D vs V_DS (inv vs reachable; cols 2,6)}"

if [[ ! -f "$INV" || ! -f "$REACH" ]]; then
  echo "Need $INV and $REACH." >&2
  exit 1
fi

TMP_INV="$(mktemp)"
TMP_RE="$(mktemp)"
trap 'rm -f "$TMP_INV" "$TMP_RE"' EXIT

awk '{print $2, $6}' "$INV" >"$TMP_INV"
awk '{print $2, $6}' "$REACH" >"$TMP_RE"

graph -T svg -C -B -L "$TITLE" \
  -X "V_DS (V)" -Y "I_D (A)" \
  -q 0.12 "$TMP_INV" -C -q 0.35 "$TMP_RE" >"$OUT"
if [[ "$OUT" = /* ]]; then
  echo "Wrote $OUT"
else
  echo "Wrote ${LAB}/$OUT"
fi
