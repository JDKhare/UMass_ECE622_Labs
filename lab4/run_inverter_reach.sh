#!/usr/bin/env bash
# Regenerate CMOS inverter fragments, patch Vin low/high strips, run phaverlite,
# print reachability checks to the terminal and save full PHAVerLite logs + summary under lab4/logs/.
set -euo pipefail
LAB4="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${LAB4}/../setups/env.sh"

LOGDIR="${LAB4}/logs"
mkdir -p "$LOGDIR"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
LOW_FULL="${LOGDIR}/inverter_vin_low_${STAMP}.log"
HIGH_FULL="${LOGDIR}/inverter_vin_high_${STAMP}.log"
SUMMARY="${LOGDIR}/inverter_reach_summary_${STAMP}.txt"
# stable “last run” symlinks for quick open
LOW_LAST="${LOGDIR}/inverter_vin_low_last.log"
HIGH_LAST="${LOGDIR}/inverter_vin_high_last.log"
SUM_LAST="${LOGDIR}/inverter_reach_summary_last.txt"

python3 "${LAB4}/_generate_cmos_inverter_pha.py"

VDD=1.8
EPS=0.006
VIN_LOW_OP=0.05
VIN_HIGH_OP=1.75
TMP1="$(mktemp)"
TMP2="$(mktemp)"
python3 "${LAB4}/patch_inverter_for_vin.py" "${LAB4}/cmos_inverter_vin_low.pha" "$TMP1" "$VIN_LOW_OP" "$EPS" "$VDD"
python3 "${LAB4}/patch_inverter_for_vin.py" "${LAB4}/cmos_inverter_vin_high.pha" "$TMP2" "$VIN_HIGH_OP" "$EPS" "$VDD"

run_one() {
  local title="$1"
  local tmp="$2"
  local full="$3"
  echo ""
  echo "============================================================================"
  echo "$title"
  echo "============================================================================"
  echo "(Full PHAVerLite transcript -> ${full})"
  phaverlite "$tmp" 2>&1 | tee "$full" | grep -E '^(reach_|t_hi_|t_lo_).*reachable' || true
}

{
  echo "CMOS inverter — reachability checks"
  echo "Generated: $(date -Iseconds)"
  echo "VDD=${VDD} V  EPS=${EPS} V  VIN_low_op=${VIN_LOW_OP} V  VIN_high_op=${VIN_HIGH_OP} V"
  echo ""
  echo "Joint modes: see lab4/INVERTER_REACHABILITY.md (m* id map per file)."
  echo ""
  echo "--- Interpretation (low Vin file) ---"
  echo "  reach_m* : discrete joint mode reachable from initial set"
  echo "  t_hi_m*  : can reach strong high output (vout >= VOH) from that mode"
  echo ""
  echo "--- Interpretation (high Vin file) ---"
  echo "  reach_m* : joint mode reachable from initial set"
  echo "  t_lo_m*  : can reach strong low output (vout <= VOL) from that mode"
  echo ""

  run_one "Vin LOW strip (~${VIN_LOW_OP} V) — lab4/cmos_inverter_vin_low.pha" "$TMP1" "$LOW_FULL"
  run_one "Vin HIGH strip (~${VIN_HIGH_OP} V) — lab4/cmos_inverter_vin_high.pha" "$TMP2" "$HIGH_FULL"

  echo ""
  echo "============================================================================"
  echo "Log files written:"
  echo "  ${LOW_FULL}"
  echo "  ${HIGH_FULL}"
  echo "============================================================================"
} | tee "$SUMMARY"

ln -sf "$LOW_FULL" "$LOW_LAST"
ln -sf "$HIGH_FULL" "$HIGH_LAST"
ln -sf "$SUMMARY" "$SUM_LAST"

rm -f "$TMP1" "$TMP2"

echo ""
echo "Quick paths (relative to lab4):"
echo "  logs/$(basename "$SUMMARY")"
echo "  logs/$(basename "$LOW_FULL")"
echo "  logs/$(basename "$HIGH_FULL")"
echo "  logs/inverter_reach_summary_last.txt  -> latest summary"
