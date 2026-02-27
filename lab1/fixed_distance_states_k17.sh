et -euo pipefail

# Usage:
# ./reachable_k17.sh <verilog> <n_state_bits> <init_bits> <outroot> <solver>
#
# For 5 state bits:
# ./reachable_k17.sh ./verilog_src/stoplight2.v 5 00000 results_stoplight2 minisat

if [ "$#" -ne 5 ]; then
  echo "Usage: $0 <verilog> <n_state_bits> <init_bits> <outroot> <solver>"
  exit 1
fi

VERILOG="$1"
N="$2"
INIT="$3"
OUTROOT="$4"
SOLVER="$5"

K=17
mkdir -p "$OUTROOT"

REACH=()

# loop through 0..(2^N - 1)
MAX=$(( (1<<N) - 1 ))

for x in $(seq 0 "$MAX"); do
  # format x as N-bit binary string
  TARGET=$(printf "%0${N}d" "$(echo "obase=2;$x" | bc)")
  OUTDIR="${OUTROOT}/k${K}_t${TARGET}"
  mkdir -p "$OUTDIR"

  ./lab1_parser "$VERILOG" "$TARGET" "$K" "$INIT" "$OUTDIR" "$SOLVER" >/dev/null

  STATUS=$(head -n 1 "${OUTDIR}/out.sat" || true)
  if [ "$STATUS" = "SAT" ]; then
    REACH+=("$TARGET")
    echo "reachable @17: $TARGET"
  fi
done

echo
echo "All states reachable at transition 17:"
if [ "${#REACH[@]}" -eq 0 ]; then
  echo "(none)"
else
  printf "%s\n" "${REACH[@]}"
fi
