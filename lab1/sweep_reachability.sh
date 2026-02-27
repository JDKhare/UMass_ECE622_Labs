et -euo pipefail

# Usage:
# ./sweep_reach.sh <verilog> <target> <init> <outroot> <minisat>
#
# Example:
# ./sweep_reach.sh ./verilog_src/stoplight1.v 0100 0000 results_stoplight minisat

if [ "$#" -ne 5 ]; then
  echo "Usage: $0 <verilog> <target> <init> <outroot> <minisat>"
  exit 1
fi

VERILOG="$1"
TARGET="$2"
INIT="$3"
OUTROOT="$4"
MINISAT="$5"

mkdir -p "$OUTROOT"

REACHABLE=()

echo "Sweeping k=1..32 for:"
echo "  verilog=$VERILOG target=$TARGET init=$INIT outroot=$OUTROOT solver=$MINISAT"
echo

for k in $(seq 1 32); do
  OUTDIR="${OUTROOT}/k_${k}"
  mkdir -p "$OUTDIR"

  # Run your program for this k
  ./lab1_parser "$VERILOG" "$TARGET" "$k" "$INIT" "$OUTDIR" "$MINISAT" >/dev/null

  # Read SAT/UNSAT from first line of out.sat
  STATUS=$(head -n 1 "${OUTDIR}/out.sat" || true)

  if [ "$STATUS" = "SAT" ]; then
    REACHABLE+=("$k")
    printf "k=%2d : SAT  (reachable)\n" "$k"
  else
    printf "k=%2d : UNSAT\n" "$k"
  fi
done

echo
if [ "${#REACHABLE[@]}" -eq 0 ]; then
  echo "Reachable i values: (none in 1..32)"
else
  echo -n "Reachable i values: "
  (IFS=,; echo "${REACHABLE[*]}")
fi
