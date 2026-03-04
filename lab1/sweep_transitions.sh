#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <verilog_file> <target_state_bitstring> <N> <solver>"
    echo "Example: $0 top.v 1010 20 minisat"
    exit 1
fi

VFILE=$1
TARGET=$2
N=$3
SOLVER=$4

if [ ! -f "$VFILE" ]; then
    echo "Error: Verilog file '$VFILE' not found."
    exit 1
fi

echo "Sweeping transitions 1 to $N for target state $TARGET using $SOLVER..."

for i in $(seq 1 "$N"); do
    OUT=$(./reachsat "$VFILE" "$TARGET" "$i" "$SOLVER")
    
    if echo "$OUT" | grep -q "^SAT$"; then
        echo "Target $TARGET is REACHABLE at transition $i"
    else
        echo "Target $TARGET is UNSAT at transition $i"
    fi
done
