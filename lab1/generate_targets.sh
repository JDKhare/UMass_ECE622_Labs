OUTDIR=out_partc_dimacs

mkdir -p $OUTDIR

for i in $(seq 1 20)
do
    BASE="partc_ex5/base_${i}.dimacs"
    NODES="partc_ex5/nodes_${i}.txt"
    TARGET=$(printf "%09d" "$(echo "obase=2;$t" | bc)")
    K=$((i-1))
    for t in $(seq 0 511)
    do

        ./add_target_clause \
            --base $BASE \
            --nodes $NODES \
            --k $K \
            --n 9 \
            --target $TARGET \
            --outdir $OUTDIR
    done
done

