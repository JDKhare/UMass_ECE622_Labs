#!/usr/bin/env bash
# PHAVerLite: Vgs DC sweep (6 bins) + Id–Vds family plot; logs under logs/<stamp>/.
set -euo pipefail
LAB4="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB4}/../setups/env.sh"
cd "$LAB4"

STAMP="nmos_$(date +%Y-%m-%d_%H%M%S)"
PLOTDIR="${LAB4}/plots/${STAMP}"
LOGDIR="${LAB4}/logs/${STAMP}"
mkdir -p "$PLOTDIR" "$LOGDIR"

SWEEP_LOG="${LOGDIR}/phaverlite_vgs_sweep.log"
bash "${LAB4}/run_vgs_id_vds_sweep.sh" "$LAB4" "$PLOTDIR" "$SWEEP_LOG"

python3 "${LAB4}/plot_nmos_id_vds_family.py" -d "$PLOTDIR" -o "${PLOTDIR}/nmos_phas_id_vds_family.png"

bash "${LAB4}/plot_phaver_graph_all_bins.sh" "$PLOTDIR"

FIRST_VG="$(find "$PLOTDIR" -maxdepth 1 -type d -name 'vg_*' | sort | head -1)"
if [[ -n "$FIRST_VG" && -f "${FIRST_VG}/out_inv" && -f "${FIRST_VG}/out_reachable" ]]; then
  bash "${LAB4}/plot_graph_id_vds.sh" "${FIRST_VG}/out_inv" "${FIRST_VG}/out_reachable" "${PLOTDIR}/nmos_graph_id_vds_firstbin.svg" \
    "First Vgs bin: invariant vs reachable, I_D vs V_DS"
  python3 "${LAB4}/plot_reachable.py" --reachable "${FIRST_VG}/out_reachable" \
    -o "${PLOTDIR}/firstbin_nmos_phas_vgs_vds.png" --svg "${PLOTDIR}/firstbin_nmos_phas_vgs_vds.svg"
  python3 "${LAB4}/plot_reachable_regions.py" --inv "${FIRST_VG}/out_inv" --reachable "${FIRST_VG}/out_reachable" \
    -o "${PLOTDIR}/firstbin_nmos_phas_vgs_vds_regions.png"
  python3 "${LAB4}/plot_lab4_dashboard.py" --reachable "${FIRST_VG}/out_reachable" --inv "${FIRST_VG}/out_inv" \
    -o "${PLOTDIR}/firstbin_nmos_phas_dashboard.png"
fi

python3 "${LAB4}/write_analysis_report.py" -d "$PLOTDIR" --log "$SWEEP_LOG"

echo "Log:  ${SWEEP_LOG}"
echo "Plots: ${PLOTDIR}/"
echo "  ANALYSIS_REPORT.txt  (summary: states, sweep bins, figure list, log excerpt)"
echo "  phaver_graph_id_vds_all_vgs.svg  (plotutils: all Vgs bins, I_D vs V_DS, labeled axes)"
echo "  phaver_graph_vg_*_vds_ids.svg  (per bin: inv vs reachable, I_D vs V_DS)"
echo "  nmos_phas_id_vds_family.png  (Id vs Vds, one color per Vgs step)"
echo "  nmos_graph_id_vds_firstbin.svg  (graph on first vg_* bin, if present)"
echo "  firstbin_nmos_phas_*.png/svg  (first Vgs bin: vgs–vds, regions, dashboard)"
echo "  vg_* / out_reachable out_inv meta.txt per Vgs bin"
