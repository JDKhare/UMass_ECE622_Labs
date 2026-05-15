#!/usr/bin/env bash
# Single plotutils `graph` SVG: I_D vs V_DS for every vg_* bin on one figure (reachable only).
# Each bin uses a different pen color (-C toggles). Axis labels are set for drain I–V curves.
#
# Usage:
#   bash plot_graph_id_vds_family_phaver.sh PLOTDIR [output.svg]
# Default output: PLOTDIR/phaver_graph_id_vds_all_vgs.svg
#
# For inv vs reachable per bin, use plot_graph_id_vds.sh on each vg_* folder separately.

set -euo pipefail
LAB4="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB4}/../setups/env.sh"

PLOTDIR="${1:?usage: plot_graph_id_vds_family_phaver.sh PLOTDIR [output.svg]}"
PLOTDIR="$(cd "$PLOTDIR" && pwd)"
OUT="${2:-${PLOTDIR}/phaver_graph_id_vds_all_vgs.svg}"
if [[ "$OUT" != /* ]]; then
  OUT="${PLOTDIR}/${OUT}"
fi

shopt -s nullglob
mapfile -t dirs < <(printf '%s\n' "$PLOTDIR"/vg_*/ | sed 's|/$||' | sort)

temps=()
cleanup() { rm -f "${temps[@]}"; }
trap cleanup EXIT

graph_args=(
  -T svg -C -B
  -L "NMOS drain I-V: reachable (all Vgs bins; PHAVerLite vertices)"
  -X "V_DS (V)"
  -Y "I_D (A)"
)

i=0
for d in "${dirs[@]}"; do
  [[ -f "$d/out_reachable" ]] || continue
  t="$(mktemp)"
  temps+=("$t")
  awk '{print $2, $6}' "$d/out_reachable" >"$t"
  if [[ "$i" -eq 0 ]]; then
    graph_args+=( -q 0.14 "$t" )
  else
    graph_args+=( -C -q 0.14 "$t" )
  fi
  i=$((i + 1))
done

if [[ "$i" -eq 0 ]]; then
  echo "No vg_*/out_reachable under $PLOTDIR" >&2
  exit 1
fi

graph "${graph_args[@]}" >"$OUT"
echo "Wrote $OUT (${i} series)"
