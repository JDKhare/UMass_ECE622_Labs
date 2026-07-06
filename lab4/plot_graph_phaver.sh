#!/usr/bin/env bash
# Course-style plotutils `graph` SVG from PHAVerLite dumps (vgs,vds columns only).
#
# PHAVerLite out_inv / out_reachable are 6 numbers per line (vgs vds w l vdsg ids).
# Native `graph` expects
# 2D x y sequences (see lab3/modeling_car/plot_c3.sh). This script extracts columns
# 1–2 as (vgs, vds) — a projection, not the full 5D reachable set.
#
# Usage (from lab4, after phaverlite nmos_model.pha):
#   bash plot_graph_phaver.sh [out_inv] [out_reachable] [output.svg] [title]
# Defaults: out_inv out_reachable nmos_graph_phaver_vgs_vds.svg in cwd.

set -euo pipefail
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB}/../setups/env.sh"
cd "$LAB"

INV="${1:-out_inv}"
REACH="${2:-out_reachable}"
OUT="${3:-nmos_graph_phaver_vgs_vds.svg}"
TITLE="${4:-NMOS vgs-vds projection (cols 1-2; higher-D state)}"

if [[ ! -f "$INV" || ! -f "$REACH" ]]; then
  echo "Need $INV and $REACH (run phaverlite nmos_model.pha first; dumps usually under plots/<stamp>/)." >&2
  exit 1
fi

TMP_INV="$(mktemp)"
TMP_RE="$(mktemp)"
trap 'rm -f "$TMP_INV" "$TMP_RE"' EXIT

awk '{print $1, $2}' "$INV" >"$TMP_INV"
awk '{print $1, $2}' "$REACH" >"$TMP_RE"

graph -T svg -C -B -L "$TITLE" -q 0.15 "$TMP_INV" -C -q 0.4 "$TMP_RE" >"$OUT"
if [[ "$OUT" = /* ]]; then
  echo "Wrote $OUT"
else
  echo "Wrote ${LAB}/$OUT"
fi
