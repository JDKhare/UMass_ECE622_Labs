#!/usr/bin/env bash
# Six DC Vgs bins (narrow strips, negative Vgs): run phaverlite per bin into PLOTDIR/vg_XX_*.
# Usage: bash run_vgs_id_vds_sweep_pmos.sh LAB4_DIR PLOTDIR [LOG_APPEND_PATH]
set -euo pipefail
LAB4="${1:?}"
PLOTDIR="${2:?}"
LOG_APPEND="${3:-}"
MODEL="${LAB4}/pmos_model.pha"
# shellcheck source=/dev/null
source "${LAB4}/../setups/env.sh"

VDD=1.8
EPS=0.006
VGS_OPS=(-0.15 -0.28 -0.40 -0.52 -0.70 -1.15)

if [[ -n "$LOG_APPEND" ]]; then
  {
    echo "=== vgs_id_vds PMOS sweep $(date -Iseconds) ==="
  } >>"$LOG_APPEND"
fi

i=0
for op in "${VGS_OPS[@]}"; do
  label=$(printf "vg_%02d_%.2fV" "$i" "$op" | tr '.' 'p')
  sub="${PLOTDIR}/${label}"
  mkdir -p "$sub"
  tmp="$(mktemp)"
  meta="${sub}/meta.txt"
  python3 "${LAB4}/patch_pmos_for_vgs.py" "$MODEL" "$tmp" "$op" "$EPS" "$VDD"
  {
    echo "VGS_OP=${op}"
    echo "EPS=${EPS}"
  } >"$meta"
  if [[ -n "$LOG_APPEND" ]]; then
    echo "--- ${label} VGS_OP=${op} ---" >>"$LOG_APPEND"
    ( cd "$sub" && phaverlite "$tmp" ) 2>&1 | tee -a "$LOG_APPEND"
  else
    ( cd "$sub" && phaverlite "$tmp" )
  fi
  rm -f "$tmp"
  i=$((i + 1))
done
