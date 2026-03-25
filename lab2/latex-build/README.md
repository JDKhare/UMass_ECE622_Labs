# Lab 2 LaTeX Report Workflow

This directory now contains a standalone Lab 2 report source:

- `Lab2Report.tex` (new Lab 2 report)
- `figures/` (renamed, ordered screenshots for the report)
- `Makefile` (build helper commands)

## Environment note

This server already has LaTeX build tools installed and available in PATH:

- `latexmk`
- `pdflatex`
- `xelatex`
- `lualatex`

So no `sudo` install is required to compile this report here.

## Compile commands

Run from:

```bash
cd /home/ece558_658_2025/jkhare/UMass_ECE622_Labs/lab2/latex-build
```

Build with images (default):

```bash
make
# or
make with-images
```

Build without images (keeps figure captions/placeholders):

```bash
make without-images
```

Watch mode (auto-rebuild on save):

```bash
make watch
```

Clean aux files:

```bash
make clean
```

## Direct latexmk equivalents

With images:

```bash
latexmk -pdf -interaction=nonstopmode -file-line-error Lab2Report.tex
```

Without images:

```bash
latexmk -pdf -interaction=nonstopmode -file-line-error \
  -jobname=Lab2Report-noimg \
  -pdflatex='pdflatex %O "\\def\\NOIMAGES{1}\\input{%S}"' \
  Lab2Report.tex
```

## Screenshot naming convention

To keep LaTeX references stable and readable, images were copied into `figures/` with ordered names like:

- `01_a1_query_and_trace.png`
- `02_a2_model_changes.png`
- ...
- `11_b5_safe_recheck.png`

This avoids ambiguous names like `image1.png`, `image2.png`, etc.
