#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./run_sat.sh <verilog> <target> <k> <init> <outdir> <minisat> [-print] [-print-state-only] [-summary]

if [ "$#" -lt 6 ]; then
  echo "Usage: $0 <verilog> <target> <k> <init> <outdir> <minisat> [-print] [-print-state-only] [-summary]"
  exit 1
fi

VERILOG="$1"
TARGET="$2"
K="$3"
INIT="$4"
OUTDIR="$5"
MINISAT="$6"
shift 6

PRINT_NODES=false
PRINT_STATE_ONLY=false
SUMMARY=false

# Parse optional flags
while [ "$#" -gt 0 ]; do
  case "$1" in
    -print) PRINT_NODES=true ;;
    -print-state-only) PRINT_STATE_ONLY=true ;;
    -summary) SUMMARY=true ;;
    *)
      echo "Unknown option: $1"
      echo "Valid: -print | -print-state-only | -summary"
      exit 1
      ;;
  esac
  shift
done

# If both requested, prefer full nodes
if [ "$PRINT_NODES" = true ] && [ "$PRINT_STATE_ONLY" = true ]; then
  PRINT_STATE_ONLY=false
fi

BASE=$(basename "$VERILOG")
BASE="${BASE%.*}"

TS=$(date +'%Y%m%d_%H%M%S')

LOGDIR="${OUTDIR%/}/logs"
mkdir -p "$LOGDIR"

LOGFILE="${LOGDIR}/${BASE}_init${INIT}_target${TARGET}_k${K}_${TS}.txt"

DIMACS_PATH="${OUTDIR%/}/out.dimacs"
NODES_PATH="${OUTDIR%/}/out.nodes"
SAT_PATH="${OUTDIR%/}/out.sat"
MODEL_PATH="${OUTDIR%/}/out.model"

{
  echo "=== RUN @ ${TS} ==="
  echo "Verilog  : ${VERILOG}"
  echo "Init     : ${INIT}"
  echo "Target   : ${TARGET}"
  echo "Unroll k : ${K}"
  echo "Outdir   : ${OUTDIR}"
  echo "MiniSat  : ${MINISAT}"
  echo "Flags    : print=${PRINT_NODES} state_only=${PRINT_STATE_ONLY} summary=${SUMMARY}"
  echo

  ./lab1_parser "${VERILOG}" "${TARGET}" "${K}" "${INIT}" "${OUTDIR}" "${MINISAT}"

  STATUS="(missing)"
  if [ -f "$SAT_PATH" ]; then
    STATUS=$(head -n 1 "$SAT_PATH" || true)
  fi

  if [ "$SUMMARY" = true ]; then
    echo "=== SUMMARY ==="
    echo "Status   : $STATUS"
    echo "DIMACS   : $DIMACS_PATH"
    echo "SAT file : $SAT_PATH"
    echo "Nodes    : $NODES_PATH"
    echo "Model    : $MODEL_PATH"
    if [ -f "$DIMACS_PATH" ]; then
      echo "Clauses  : $(grep -m1 '^p cnf ' "$DIMACS_PATH" | awk '{print $4}')"
      echo "Vars     : $(grep -m1 '^p cnf ' "$DIMACS_PATH" | awk '{print $3}')"
    fi
    echo "=== END SUMMARY ==="
    echo "=== END RUN ==="
    exit 0
  fi

  echo "=== Full SAT Output ==="
  if [ -f "$SAT_PATH" ]; then
    cat "$SAT_PATH"
  else
    echo "ERROR: $SAT_PATH not found"
  fi
  echo

  if [ "$STATUS" = "SAT" ]; then
    if [ "$PRINT_STATE_ONLY" = true ]; then
      echo "=== State bits at time k (from out.model) ==="
      if [ -f "$MODEL_PATH" ]; then
        # Prints only lines like S0@k=..., S1@k=..., etc.
        # This assumes your program uses state names starting with 'S' (e.g., S0,S1,S2...)
        grep -E "^S[0-9]+@${K}=" "$MODEL_PATH" || echo "(No matching state lines found)"
      else
        echo "ERROR: $MODEL_PATH not found (model is only written when SAT)"
      fi
    elif [ "$PRINT_NODES" = true ]; then
      echo "=== Node Mapping (full out.nodes) ==="
      if [ -f "$NODES_PATH" ]; then
        cat "$NODES_PATH"
      else
        echo "ERROR: $NODES_PATH not found"
      fi
    else
      echo "=== SAT (nodes suppressed; use -print or -print-state-only) ==="
    fi
  else
    echo "=== UNSAT: Skipping nodes/model printing ==="
  fi

  echo
  echo "=== END RUN ==="
} | tee "$LOGFILE"

echo
echo "Saved log: $LOGFILE"
