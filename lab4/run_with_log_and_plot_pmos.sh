#!/usr/bin/env bash
# PHAVerLite: PMOS Vgs DC sweep (6 bins) + Id–Vds family plot; logs under logs/<stamp>/.
set -euo pipefail
LAB4="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB4}/../setups/env.sh"
cd "$LAB4"

STAMP="pmos_$(date +%Y-%m-%d_%H%M%S)"
PLOTDIR="${LAB4}/plots/${STAMP}"
LOGDIR="${LAB4}/logs/${STAMP}"
mkdir -p "$PLOTDIR" "$LOGDIR"

SWEEP_LOG="${LOGDIR}/phaverlite_vgs_sweep.log"
bash "${LAB4}/run_vgs_id_vds_sweep_pmos.sh" "$LAB4" "$PLOTDIR" "$SWEEP_LOG"

python3 "${LAB4}/plot_pmos_id_vds_family.py" -d "$PLOTDIR" -o "${PLOTDIR}/pmos_phas_id_vds_family.png"

bash "${LAB4}/plot_phaver_graph_all_bins.sh" "$PLOTDIR"

FIRST_VG="$(find "$PLOTDIR" -maxdepth 1 -type d -name 'vg_*' | sort | head -1)"
if [[ -n "$FIRST_VG" && -f "${FIRST_VG}/out_inv" && -f "${FIRST_VG}/out_reachable" ]]; then
  bash "${LAB4}/plot_graph_id_vds.sh" "${FIRST_VG}/out_inv" "${FIRST_VG}/out_reachable" "${PLOTDIR}/pmos_graph_id_vds_firstbin.svg" \
    "First Vgs bin (PMOS): invariant vs reachable, I_D vs V_DS"
  python3 "${LAB4}/plot_reachable.py" --reachable "${FIRST_VG}/out_reachable" \
    -o "${PLOTDIR}/firstbin_pmos_phas_vgs_vds.png" --svg "${PLOTDIR}/firstbin_pmos_phas_vgs_vds.svg"
  python3 "${LAB4}/plot_reachable_regions.py" --inv "${FIRST_VG}/out_inv" --reachable "${FIRST_VG}/out_reachable" \
    -o "${PLOTDIR}/firstbin_pmos_phas_vgs_vds_regions.png"
  python3 "${LAB4}/plot_lab4_dashboard.py" --reachable "${FIRST_VG}/out_reachable" --inv "${FIRST_VG}/out_inv" \
    -o "${PLOTDIR}/firstbin_pmos_phas_dashboard.png"
fi

echo "Log:  ${SWEEP_LOG}"
echo "Plots: ${PLOTDIR}/"
echo "  phaver_graph_id_vds_all_vgs.svg  (plotutils: all Vgs bins, I_D vs V_DS)"
echo "  phaver_graph_vg_*_vds_ids.svg  (per bin: inv vs reachable, I_D vs V_DS)"
echo "  pmos_phas_id_vds_family.png  (Id vs Vds, one color per Vgs step)"
echo "  pmos_graph_id_vds_firstbin.svg  (graph on first vg_* bin, if present)"
echo "  firstbin_pmos_phas_*.png/svg  (first Vgs bin: vgs–vds, regions, dashboard)"
echo "  vg_* / out_reachable out_inv meta.txt per Vgs bin"
