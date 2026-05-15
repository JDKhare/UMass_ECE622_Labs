# CMOS inverter hybrid — joint modes and reachability

Two PHAVerLite files are generated from [`_generate_cmos_inverter_pha.py`](_generate_cmos_inverter_pha.py):

- [`cmos_inverter_vin_low.pha`](cmos_inverter_vin_low.pha) — **NMOS cutoff** only, with **PMOS on** (triode/sat). Valid for a **low** DC `Vin` strip (NMOS weak, PMOS strong).
- [`cmos_inverter_vin_high.pha`](cmos_inverter_vin_high.pha) — **NMOS on** (triode/sat), with **PMOS weak/cut or on** as allowed by the strip. Valid for a **high** DC `Vin` strip.

## Impossible joint mode (9th of 3×3)

**`n_cut_p_cut` (NMOS cutoff + PMOS cutoff)** is omitted everywhere: on one DC gate strip you cannot have both **Vin low enough** that the NMOS is in cutoff **and** **Vin high enough** that the PMOS is in cutoff (`Vgs,p = Vin − VDD` in the weak band). So the literal 3×3 product is **8** joint modes, not 9.

## Location name map (short `m*` identifiers)

| id  | NMOS | PMOS | In `vin_low` | In `vin_high` |
|-----|------|------|--------------|----------------|
| m0  | cut  | lin  | yes          | no (reused index in other file) |
| m1  | cut  | sat  | yes          | no |
| m0  | lin  | cut  | —            | yes (first mode in high file) |
| m1  | lin  | lin  | —            | yes |
| m2  | lin  | sat  | —            | yes |
| m3  | sat  | cut  | —            | yes |
| m4  | sat  | lin  | —            | yes |
| m5  | sat  | sat  | —            | yes |

**Note:** `m0`/`m1` in the **low** file are **not** the same physical pair as `m0`…`m5` in the **high** file; each file has its own local `m*` numbering.

## I/O checks encoded in the `.pha` files

- **Low `Vin` file:** `t_hi_m0` / `t_hi_m1` — reach `vout >= VOH` from `m0` / `m1`.
- **High `Vin` file:** `t_lo_m0` … `t_lo_m5` — reach `vout <= VOL` from each discrete joint mode.

## Logs and printed reachability checks

Run:

```bash
bash lab4/run_inverter_reach.sh
```

That script:

1. Prints a short header and **each `is_reachable` result** (`reach_*`, `t_hi_*`, `t_lo_*`) to the terminal.
2. Writes a **timestamped summary** under [`lab4/logs/`](logs/) (e.g. `inverter_reach_summary_<date>_<time>.txt`).
3. Writes the **full PHAVerLite transcript** for each patched run (e.g. `inverter_vin_low_<stamp>.log`, `inverter_vin_high_<stamp>.log`).
4. Updates symlinks **`lab4/logs/inverter_*_last.log`** and **`inverter_reach_summary_last.txt`** to the latest run.

## Example run (defaults in repo + optional patch)

```bash
bash lab4/run_inverter_reach.sh
```

With default numerics after `python3 lab4/_generate_cmos_inverter_pha.py` (no patch), a typical transcript is:

**`Vin` low fragment**

- `reach_m0` (N cut, P lin): **reachable**
- `reach_m1` (N cut, P sat): not reachable (from default initial / dynamics on that strip)
- `t_hi_m0` (high `Vout` from `m0`): **reachable**
- `t_hi_m1`: not reachable

**`Vin` high fragment**

- Only **`reach_m0`** (N lin, P cut) is **reachable** from the default initial; other joint modes are not entered with `vin' = 0` on that strip from that seed.
- **`t_lo_m0`** (low `Vout` from `m0`): **reachable**; `t_lo_m1`…`t_lo_m5` not reachable from those seeds.

So for this coarse hybrid: **low input ⇒ can reach a high output band**; **high input ⇒ can reach a low output band** from the principal joint mode (`N` off/`P` on vs `N` on/`P` weak).

Re-run with your own strips via [`patch_inverter_for_vin.py`](patch_inverter_for_vin.py).
