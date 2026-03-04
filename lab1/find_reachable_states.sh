#!/bin/bash

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <verilog_file> <num_state_bits> <k> <solver>"
    echo "Example: $0 top.v 4 15 minisat"
    exit 1
fi

VFILE=$1
BITS=$2
K=$3
SOLVER=$4

if [ ! -f "$VFILE" ]; then
    echo "Error: Verilog file '$VFILE' not found."
    exit 1
fi

MAX=$(( (1 << BITS) - 1 ))
echo "Checking all $BITS-bit states at transition $K using $SOLVER..."

for i in $(seq 0 $MAX); do
    # Convert index to a zero-padded binary string of length BITS
    # 'bc' is used to convert to base 2
    BIN_VAL=$(bc <<< "obase=2; $i")
    BIN_STR=$(printf "%0${BITS}d\n" "$BIN_VAL")
    
    OUT=$(./reachsat "$VFILE" "$BIN_STR" "$K" "$SOLVER")
    if echo "$OUT" | grep -q "^SAT$"; then
        echo "State $BIN_STR is REACHABLE"
    fi
done
