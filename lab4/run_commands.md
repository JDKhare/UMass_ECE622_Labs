# PHAVerLite run commands: NMOS (Id vs Vds @ DC Vgs steps)

## If `phaverlite` is “not found”

The tool is **`phaverlite`**, under **`UMass_ECE622_Labs/setups/bin`** after sourcing the course env.

**Easiest (from `lab4`):**

```bash
bash run_phaverlite.sh
```

**tcsh:**

```tcsh
tcsh run_phaverlite.csh
```

**Manual:**

```bash
source ~/UMass_ECE622_Labs/setups/env.sh
phaverlite ~/UMass_ECE622_Labs/lab4/nmos_model.pha
```

## Recommended pipeline (dated `logs/` + `plots/`)

```bash
cd ~/UMass_ECE622_Labs/lab4
bash run_with_log_and_plot.sh
```

This creates **`nmos_YYYY-MM-DD_HHMMSS`**:

- **`logs/<stamp>/phaverlite_vgs_sweep.log`** — concatenated PHAVerLite output from **six** `VGS_OP` bins (`0.15, 0.28, 0.40, 0.52, 0.70, 1.15` V by default in `run_vgs_id_vds_sweep.sh`).
- **`plots/<stamp>/vg_XX_*V/`** — each contains **`out_reachable`**, **`out_inv`**, **`meta.txt`** (`VGS_OP=...`).
- **`plots/<stamp>/nmos_phas_id_vds_family.png`** — overlay **reachable `ids` vs `vds`**, one color per **Vgs** step.
- **`plots/<stamp>/nmos_graph_id_vds_firstbin.svg`** — course **`graph`** on **columns 2 and 6** (`vds`, `ids`) for the first `vg_*` folder (if present).

**`phaverlite` dumps** are written to each subfolder’s cwd (not the lab4 root).

### Manual sweep (same as the script)

```bash
cd ~/UMass_ECE622_Labs/lab4
STAMP="nmos_$(date +%Y-%m-%d_%H%M%S)"
mkdir -p "plots/$STAMP" "logs/$STAMP"
bash run_vgs_id_vds_sweep.sh "$PWD" "$PWD/plots/$STAMP" "$PWD/logs/$STAMP/phaverlite_vgs_sweep.log"
python3 plot_nmos_id_vds_family.py -d "$PWD/plots/$STAMP"
```

### Runtime

Roughly **6×** one PHAVerLite job. Coarsen **`pc_vds`**, **`pc_vdsg`**, **`pc_ids`** in `nmos_model.pha` for faster runs (fewer vertices).

### Faster runs (boolean queries only)

Comment out the block from **`nmos.add_label`** through **`inv.print`** in `nmos_model.pha`.

## Built-in queries

`sat_reach`, `lin_reach`, `invalid_low_reach`, `invalid_high_reach` — inspect each line in the sweep log.

## Ad-hoc single run

```bash
source ~/UMass_ECE622_Labs/setups/env.sh
cd /tmp
phaverlite ~/UMass_ECE622_Labs/lab4/nmos_model.pha
```

Writes **`out_*`** in **`/tmp`**. Edit **`VGS_LO_N` / `VGS_HI_N`** and **`initially:`** for a different DC gate strip, or use **`patch_nmos_for_vgs.py`** to emit a temp `.pha`.
