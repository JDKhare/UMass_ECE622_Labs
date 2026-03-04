#!/usr/bin/env bash
#set -euo pipefail
kdir -p partc_ex5

for i in $(seq 1 20)
do
  ./lab1_parser verilog_src/ex5.v - $i 000000000 partc_ex5 minisat
  mv partc_ex5/out.dimacs partc_ex5/base_${i}.dimacs
  mv partc_ex5/out.nodes  partc_ex5/nodes_${i}.txt
done

./partc --mode B \
  --minisat minisat \
  --dimacs "partc_ex5/base_{i}.dimacs" \
  --nodes  "partc_ex5/nodes_{i}.txt" \
  --nbits 2 \
  --imax 20 \
  --namefmt "S{b}@{k}" \
  --matrix
