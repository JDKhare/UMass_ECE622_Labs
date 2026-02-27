et -euo pipefail

# Usage:
# ./run_sat.sh <verilog> <target> <k> <init> <outdir> <minisat>

if [ "$#" -ne 6 ]; then
  echo "Usage: $0 <verilog> <target> <k> <init> <outdir> <minisat>"
  exit 1
fi

VERILOG="$1"
TARGET="$2"
K="$3"
INIT="$4"
OUTDIR="$5"
MINISAT="$6"

# Extract base verilog name without path and extension
BASE=$(basename "$VERILOG")
BASE="${BASE%.*}"

TS=$(date +'%Y%m%d_%H%M%S')

LOGDIR="${OUTDIR%/}/logs"
mkdir -p "$LOGDIR"

LOGFILE="${LOGDIR}/${BASE}_init${INIT}_target${TARGET}_k${K}_${TS}.txt"

{
  echo "=== RUN @ ${TS} ==="
  echo "Verilog  : ${VERILOG}"
  echo "Init     : ${INIT}"
  echo "Target   : ${TARGET}"
  echo "Unroll k : ${K}"
  echo

  ./lab1_parser "${VERILOG}" "${TARGET}" "${K}" "${INIT}" "${OUTDIR}" "${MINISAT}"

  echo
  echo "=== Minisat Status ==="
  head -n 1 "${OUTDIR}/out.sat"

  echo
  echo "=== Full SAT Output ==="
  cat "${OUTDIR}/out.sat"

  echo
  echo "=== Node Mapping ==="
  cat "${OUTDIR}/out.nodes"

  echo
  echo "=== END RUN ==="
} | tee "$LOGFILE"

echo
echo "Saved log: $LOGFILE"
