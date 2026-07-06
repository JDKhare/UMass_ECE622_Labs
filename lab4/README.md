# PHAVerLite Lab 4: NMOS hybrid (Id vs Vds family at DC Vgs steps)

## Scope

Single **NMOS** hybrid: cutoff, triode, saturation. **`vgs`** is held on a **narrow DC strip** (one of **six** gate bias steps). **`vds`** sweeps **`0 … VDD`** with constant **`vds'`** (illustrative drain ramp). **`ids'`** is **piecewise constant** (steeper in triode, shallow in saturation, zero in cutoff) so reachable **`(vds, ids)`** mimics a coarse **output characteristic**, not BSIM.

## Model objective

- **`vdsg = vds - vgs`**, **`vdsg' = vds' - vgs'`** with **`vgs'==0`**, so **`vdsg' == vds' == VDS_RAMP`**.
- Region guards unchanged: knee **`vdsg == -VTH0_N`**.
- **`ids`**: bounded by **`IDS_LEAK_N`** (cutoff) and **`IDS_MAX_N`** (on); derivatives **`IDS_PRIME_LIN`** / **`IDS_PRIME_SAT`** vs time while **`vds`** ramps.

## Parameter table (see `nmos_model.pha`)

| Name | Role |
|------|------|
| `VDD_N`, `VTH0_N` | Supply and threshold scale |
| `VDS_RAMP` | Illustrative **d**`vds`/d`t` magnitude (V/s order) |
| `VGS_LO_N`, `VGS_HI_N` | DC **Vgs** strip (set by `patch_nmos_for_vgs.py` per sweep) |
| `IDS_PRIME_LIN`, `IDS_PRIME_SAT` | **d**`ids`/d`t** in triode vs saturation (A/s) |
| `IDS_LEAK_N`, `IDS_MAX_N` | Current caps |
| `W_*`, `L_*` | Sizing bounds (static) |

## Default pipeline

```bash
bash run_with_log_and_plot.sh
```

Produces **`plots/nmos_<date>_<time>/`** with **`vg_*`** subfolders (each **`phaverlite`** run + **`meta.txt`**), merged **`nmos_phas_id_vds_family.png`**, log **`logs/.../phaverlite_vgs_sweep.log`**, and optional **`nmos_graph_id_vds_firstbin.svg`**.

## Files

- `nmos_model.pha` — hybrid + export block
- `patch_nmos_for_vgs.py` — patch strip + consistent `initially` for one `VGS_OP`
- `run_vgs_id_vds_sweep.sh` — six `VGS_OP` values, six PHAVerLite runs
- `plot_nmos_id_vds_family.py` — overlay **Id vs Vds** colored by **Vgs** step
- `plot_graph_id_vds.sh` — plotutils **`graph`** on columns **vds, ids**
- `run_with_log_and_plot.sh` — dated **`logs/`** + **`plots/`** + sweep + family figure
- `plot_reachable.py`, `plot_reachable_regions.py`, `plot_lab4_dashboard.py`, `plot_graph_phaver.sh` — optional extra views if you run **`phaverlite`** once on the base `nmos_model.pha` in a stamp dir
- `run_phaverlite.sh` / `run_phaverlite.csh` — single-file run (writes **`out_*`** in cwd)
- `notes.md`, `run_commands.md`
