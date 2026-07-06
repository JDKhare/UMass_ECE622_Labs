#!/usr/bin/env python3
"""
Overlay reachable (vds, ids) from each vg_* sweep subdirectory (meta.txt has VGS_OP).

Run after: bash run_vgs_id_vds_sweep_pmos.sh LAB4 plots/<stamp>
"""

import argparse
import sys
from pathlib import Path

from plot_reachable import parse_out_reachable_rows


def _read_vgs_op(meta: Path):
    for line in meta.read_text().splitlines():
        if line.startswith("VGS_OP="):
            return float(line.split("=", 1)[1].strip())
    return None


def main():
    ap = argparse.ArgumentParser(description="PMOS Id vs Vds family from vg_* sweep dirs.")
    ap.add_argument(
        "-d",
        "--plot-dir",
        type=Path,
        required=True,
        help="Stamped plots directory containing vg_* subfolders",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PNG (default: <plot-dir>/pmos_phas_id_vds_family.png)",
    )
    args = ap.parse_args()
    root = args.plot_dir
    if not root.is_dir():
        print("Not a directory: %s" % root, file=sys.stderr)
        return 1
    out = args.output or (root / "pmos_phas_id_vds_family.png")

    series = []
    for sub in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("vg_")):
        meta = sub / "meta.txt"
        reach = sub / "out_reachable"
        if not reach.is_file():
            continue
        vop = _read_vgs_op(meta) if meta.is_file() else None
        rows = parse_out_reachable_rows(reach)
        if not rows:
            continue
        vds = [r[1] for r in rows]
        ids = [r[5] for r in rows]
        series.append((sub.name, vop, vds, ids))

    if not series:
        print("No vg_* subdirs with out_reachable under %s" % root, file=sys.stderr)
        return 1

    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
    except ImportError:
        print("matplotlib required", file=sys.stderr)
        return 1

    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    try:
        from matplotlib import colormaps

        cmap = colormaps["viridis"]
    except Exception:
        cmap = cm.get_cmap("viridis")
    ops = [s[1] for s in series if s[1] is not None]
    lo, hi = min(ops), max(ops)

    for _name, vop, vds, ids in series:
        col = cmap((vop - lo) / (hi - lo + 1e-9)) if vop is not None else (0.4, 0.4, 0.4)
        lab = r"$V_{\mathrm{GS}}$ = %.2f V" % vop if vop is not None else _name
        ax.scatter(vds, ids, s=14, c=[col] * len(vds), alpha=0.5, label=lab, edgecolors="none")

    ax.set_xlabel(r"$V_{\mathrm{DS}}$ (V)")
    ax.set_ylabel(r"$I_{\mathrm{D}}$ (A)")
    ax.set_title(
        r"PMOS reachable drain I–V: $I_{\mathrm{D}}$ vs $V_{\mathrm{DS}}$ "
        r"(one series per $V_{\mathrm{GS}}$ bin)"
    )
    ax.legend(loc="best", fontsize=8, title=r"$V_{\mathrm{GS}}$")
    ax.grid(alpha=0.25)
    all_vds = [x for _, _, vs, _ in series for x in vs]
    vmin, vmax = min(all_vds), max(all_vds)
    pad = 0.05
    ax.set_xlim(vmin - pad, vmax + pad)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Wrote %s" % out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
