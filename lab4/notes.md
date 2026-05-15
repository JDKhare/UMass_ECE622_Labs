# Notes: NMOS voltage-only PHAVerLite model

## Assumptions

1. Only one NFET; no PMOS, no amplifier, no small-signal gain; no BSIM-style \(I_d\) surface (only the bounded auxiliary **`ids`**).
2. Region boundaries use a **fixed threshold voltage** `VTH0_N` (order of nominal BSIM `VTH0` for 45nm-style cards), not a function of `vbs` or L.
3. **`vdsg = vds - vgs`** is an explicit continuous variable with **`vdsg' = vds' - vgs'`**, so the triode/saturation interface **`vds = vgs - VTH0_N`** is written as **`vdsg = -VTH0_N`** without multiplying state variables in guards.
4. **`w` and `l`** use a **minimum drawn** story in [`nmos_model.pha`](nmos_model.pha): **`w`** ranges up to **`W_MULT_MAX_N`×** minimum width; **`l`** is pinned near **`L_MIN_N`** (tiny `[L_MIN_N, L_HI_N]` interval for PHAVerLite). They do not enter the voltage-region logic beyond these boxes.
5. **`ids`** follows **piecewise-constant `ids'`** tied to the **drain ramp** **`vds' == VDS_RAMP`**: larger **`IDS_PRIME_LIN`** in triode, smaller **`IDS_PRIME_SAT`** in saturation, **`ids'==0`** in cutoff, with halfspace caps **`IDS_LEAK_N`** / **`IDS_MAX_N`**. This yields a reachable **Id–Vds** “shape” per **DC Vgs** strip, not a calibrated BSIM \(I_d(V_{ds})\) curve.

## Ramps and DC bias steps

- **`VDS_RAMP`** sets an illustrative **drain slew** \(\mathrm{d}v_{ds}/\mathrm{d}t\) while **`vgs'==0`** (gate on a **narrow strip** \([\) `VGS_LO_N`, `VGS_HI_N` \(]\) ≈ one of **six** `VGS_OP` values from **`run_vgs_id_vds_sweep.sh`**).
- **`vdsg' = vds' - vgs' = VDS_RAMP`** on each run, so the knee **`vdsg = -VTH0_N`** is crossed as **`vds`** moves relative to fixed **`vgs`**.
- The **six `VGS_OP` steps** (default `0.15 … 1.15` V) are **design choices** for overlaying **`nmos_phas_id_vds_family.png`**, not a measured bias schedule.

## Width / length grid vs PHAVerLite state

On a real process, drawn **W** and **L** are often chosen as **integer multiples** of minimum grid rules. PHAVerLite uses **real-valued** continuous variables; enforcing **`w = k \cdot W_{\min}`** with **integer `k`** would introduce **non-linear** equalities. This lab uses a **continuous interval** **`[W_{\min}, W_{\max}]`** with **`W_{\max} = 100\,W_{\min}`** as a standard **over-approximation** of the discrete set **`\{k W_{\min} : 1 \le k \le 100\}`** for reachability. **Length** defaults to **minimum** only; to explore up to **20×** minimum length later, widen **`L_HI_N`** (see comments in `nmos_model.pha`) and relax **`pc_l`**.

## Mapping to MOS intuition

- **Cutoff:** `vgs` below threshold.
- **Triode (linear):** channel strongly inverted (`vgs` above threshold) and **`vds` small compared to `vgs - VTH0_N`**.
- **Saturation:** channel inverted and **`vds` large enough** that the knee condition holds.

## PHAVerLite fit

- Invariants and guards are **affine**; **`w`**, **`l`** static (**`w'`, `l'`, `vgs'`** zero).
- **`vds'`** is a constant ramp; **`ids'`** is **location-dependent** and constant, so **`dI_d/dV_{ds} \approx I_d' / v_{ds}'`** is a fixed ratio in each region (crude triode vs saturation slope).

## Limitations

1. **`ids`** is a **linear hybrid** caricature only: not BSIM \(I_d(V_{gs},V_{ds})\); no **`g_m`** from a small-signal linearization of this **`ids`**.
2. **Body effect, DIBL, and velocity saturation** are not represented; `VTH0_N` is a single knob.
3. Overlap at **`vdsg = -VTH0_N`** is intentional: both triode and saturation invariants can meet on the knee, which is standard for coarse hybrid abstractions.

## Interpreting the `(vgs, vds)` plot

`reg.print` lists **polyhedron vertices** in **six** dimensions (`vgs`, `vds`, `w`, `l`, `vdsg`, `ids`).

## Region vs hull

**`plot_reachable_regions.py`** draws the union of **axis-aligned bounding boxes** obtained from each blank-separated **vertex block** in `out_inv`: for each block, take \(\min/\max\) of `vgs` and `vds` over all listed 6D vertices. For PHAVerLite’s axis-aligned partition cells, this matches the **exact** \((v_{gs},v_{ds})\) projection of that cell; if a block ever listed only a subset of corners, the rectangle would be a **conservative over-approximation** of the projection. A **convex hull** of `out_reachable` points in the plane is different: it can **inflate** the true projected reachable set when the union is not convex, so we prefer the **`out_inv`** box union for “where did exploration cover in voltage space?”.

## Outputs: `logs/` and `plots/`

Use **`bash run_with_log_and_plot.sh`** for **`logs/<stamp>/phaverlite_vgs_sweep.log`** and **`plots/<stamp>/`** with **`vg_*`** subfolders plus **`nmos_phas_id_vds_family.png`**.


## NMOS theory in the numbers used here

With **\(V_{DD} = 1.8\,\mathrm{V}\)** and **\(V_{th} \approx 0.424\,\mathrm{V}\)** (fixed `VTH0_N`, long-channel style):

- **Strong inversion** is abstracted as **\(v_{gs} \ge V_{th}\)**; below that the device is in **cutoff** (no channel in this voltage-only story).
- The **triode / saturation boundary** is **\(v_{ds} = v_{gs} - V_{th}\)**. With **`vdsg = vds - vgs`**, that line is **\(\mathrm{vdsg} = -V_{th} \approx -0.424\,\mathrm{V}\)** — a **horizontal** knee in the \((v_{gs}, \mathrm{vdsg})\) plane (see panel B in `plot_lab4_dashboard.py` / `nmos_phas_dashboard.png`).
- **Triode (linear):** \(v_{gs} \ge V_{th}\) and **\(\mathrm{vdsg} \le -V_{th}\)** (small \(v_{ds}\) relative to overdrive \(v_{gs}-V_{th}\)).
- **Saturation:** \(v_{gs} \ge V_{th}\) and **\(\mathrm{vdsg} \ge -V_{th}\)** (drain voltage “past” the knee).
- The **default pipeline** overlays **six** **`(v_{ds}, I_d)`** reachable clouds at different **DC \(V_{gs}\)** strips (`plot_nmos_id_vds_family.py`), not a single measured output characteristic.

## Advantages and disadvantages of this model

**Advantages**

- **Decidable hybrid reachability** in PHAVerLite: dynamics and guards are **linear** (halfspaces, boxes); introducing **`vdsg`** avoids products like \(v_{gs}\cdot v_{ds}\) in guards.
- **Clear operating-mode structure** aligned with first-order MOS region plots; easy to **parameterize** `VDD_N`, `VTH0_N`, and W/L bounds from a technology story.
- **Interval / polyhedral abstractions** mesh with course tooling (`reg.print`, `inv.print`, `graph` on projections).
- **Sizing knobs** (`w`, `l`) stay in the state so future labs can tie regions to aspect ratio without leaving the hybrid framework.

**Disadvantages**

- **No SPICE fidelity:** **`ids`** is not BSIM \(I_d\); subthreshold, **body effect**, DIBL, and **velocity saturation** are absent; \(V_{th}\) is fixed.
- **Coarse flows:** **`vds'`** ramp and piecewise **`ids'`** are illustrative, not a specific load line or BSIM Jacobian.
- **Partition / projection artifacts:** `out_reachable` lists **vertices** of a **6D** set; many rows can share the same \((v_{ds}, ids)\) while other coordinates differ.
- **Knee overlap:** triode and saturation invariants can both be active on **\(\mathrm{vdsg} = -V_{th}\)** — fine for a conservative hybrid model, wrong if you need a unique mode for every bias.
