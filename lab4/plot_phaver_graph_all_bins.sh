#!/usr/bin/env bash
# Course PHAVer-style polyhedral plots: plotutils `graph` on PHAVerLite out_inv / out_reachable.
# Produces one combined I_D vs V_DS figure for all bins plus per-bin inv vs reachable I–V graphs.
#
# Usage:
#   source setups/env.sh   # from repo root
#   bash lab4/plot_phaver_graph_all_bins.sh /path/to/plots/nmos_STAMP
#
# Writes into PLOTDIR:
#   phaver_graph_id_vds_all_vgs.svg    — one graph: I_D vs V_DS, all bins (reachable)
#   phaver_graph_<vgdir>_vds_ids.svg  — per bin: inv vs reachable, columns 2,6 (V_DS, I_D)
#
# Semantics: both files are vertex dumps from PHAVerLite (floating-point raw).
# out_inv is an overapproximate invariant enclosure; out_reachable is the computed
# reachable union. The graph overlays them in 2D (a projection from 6D).

set -euo pipefail
LAB4="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB4}/../setups/env.sh"

PLOTDIR="${1:?usage: plot_phaver_graph_all_bins.sh PLOTDIR}"
PLOTDIR="$(cd "$PLOTDIR" && pwd)"

shopt -s nullglob
mapfile -t dirs < <(printf '%s\n' "$PLOTDIR"/vg_*/ | sed 's|/$||' | sort)

n=0
for d in "${dirs[@]}"; do
  [[ -d "$d" ]] || continue
  base="$(basename "$d")"
  if [[ -f "$d/out_inv" && -f "$d/out_reachable" ]]; then
    bash "${LAB4}/plot_graph_id_vds.sh" "$d/out_inv" "$d/out_reachable" \
      "${PLOTDIR}/phaver_graph_${base}_vds_ids.svg" \
      "PHAVer ${base}: invariant vs reachable, I_D vs V_DS"
    n=$((n + 1))
  fi
done

bash "${LAB4}/plot_graph_id_vds_family_phaver.sh" "$PLOTDIR"

echo "Wrote combined I-V SVG + ${n} per-bin inv/reach SVG(s) under ${PLOTDIR}/"
