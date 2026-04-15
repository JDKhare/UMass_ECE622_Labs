# PHAVerLite Usage (PS3)

This folder uses a local toolchain installed at `../setups` (no sudo needed).

## Files used

- Model file: `ps3_jkhare.pha` (PHAVer model file extension is `.pha`, not `.phx`)
- Generated PHAVer outputs:
  - `out_inv`
  - `out_reachable`
- Generated graph files:
  - `graph_jkhare.svg`
  - `graph_jkhare.jpg`

## 1) Activate local environment

From repo root:

```bash
source setups/env.sh
```

Or from this folder (`problem-set3`):

```bash
source ../setups/env.sh
```

## 2) Run PHAVerLite on the PS3 model

```bash
cd problem-set3
phaverlite ps3_jkhare.pha | tee phaver_run_jkhare.log
```

This generates `out_inv` and `out_reachable` in the current directory.

## 3) Generate the graph

Professor-style plotting command adapted to SVG output:

```bash
graph -T svg -C -B -L jkhare -q 0.1 out_inv -C -q 0.5 out_reachable > graph_jkhare.svg
```

Optional JPG conversion:

```bash
convert graph_jkhare.svg graph_jkhare.jpg
```

## 4) Quick rerun (all-in-one)

```bash
cd problem-set3
source ../setups/env.sh
phaverlite ps3_jkhare.pha > phaver_run_jkhare.log 2>&1
graph -T svg -C -B -L jkhare -q 0.1 out_inv -C -q 0.5 out_reachable > graph_jkhare.svg
convert graph_jkhare.svg graph_jkhare.jpg
```
