# Lab 3 LaTeX report (Hybrid Systems / PHAVerLite)

This folder mirrors the Lab~2 `latex-build` workflow, reformatted for **Lab~3: Hybrid Systems Verification** (see `../Lab3.pdf` in the `lab3` directory).

## Contents

- `Lab3Report.tex` — report skeleton aligned with Parts A--C of the lab handout
- `figures/` — drop exported plots and screenshots here (or use `report-draft-1/snapshots/`). Part~C $(x,v)$ plot is expected as `figures/c2_car_reachable_x_v.jpg` when building with images.
- `Makefile` — convenience targets for `latexmk`

The report uses **TikZ** (automata + positioning) for the Part~C hybrid automaton; a standard TeX Live `pgf` install is sufficient.

## Build

From this directory:

```bash
cd /home/ece558_658_2025/jkhare/UMass_ECE622_Labs/lab3/latex-build
make
```

Build without embedding images (placeholders only):

```bash
make without-images
```

## Image layout

`\graphicspath` includes:

- `report-draft-1/snapshots/`
- `figures/`

Name files predictably (e.g.\ `a1_reachable_pc_overlay.png`, `b1_heating_reachable_t_x.png`) and update `\labfigure{...}` paths in `Lab3Report.tex`.

By default `Lab3Report.tex` sets `\showimagesfalse` so the project **builds without PNGs** (boxed placeholders). After you add images, set `\showimagestrue` in the preamble (or use `make without-images`, which forces placeholders via `\NOIMAGES`).

## Submission models (from handout)

Replace `<lastname>` with the submitter’s last name:

- `<lastname>_A3.pha`
- `<lastname>_B2.pha`
- `<lastname>_C3.pha`
- `<lastname>_C4.pha` (ECE~622 only, step C.4)
