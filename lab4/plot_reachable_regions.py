#!/usr/bin/env python3
"""
Project PHAVerLite partition cells (out_inv) onto the (vgs, vds) plane and draw their union.

Each blank-line-separated block in out_inv is treated as a set of vertices; we take
min/max of vgs and vds over that block → axis-aligned rectangle in the voltage plane
(exact projection for an axis-aligned box; safe over-approximation if the block is
only a subset of corners). Lines may list 5 or 6 numbers per row (vgs vds w l vdsg [ids]);
only the first two columns are used for this projection.

Overlay out_reachable vertices (optional) for comparison.

Run after: phaverlite nmos_model.pha
"""

import argparse
import sys
from pathlib import Path

from plot_reachable import parse_out_reachable_rows

# Match nmos_model.pha (VDD_N, VTH0_N)
VDD = 1.8
VTH = 0.424
VGS0, VDS0 = 0.25, 0.55


def parse_out_inv_vgs_vds_boxes(path):
    """
    Split out_inv on blank lines; each non-empty block yields one (vgs_lo, vgs_hi, vds_lo, vds_hi).
    """
    text = path.read_text()
    blocks = text.split("\n\n")
    boxes = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        vgs_vals, vds_vals = [], []
        for ln in lines:
            parts = ln.split()
            if len(parts) < 5:
                continue
            try:
                vgs_vals.append(float(parts[0]))
                vds_vals.append(float(parts[1]))
            except ValueError:
                continue
        if len(vgs_vals) < 1:
            continue
        boxes.append(
            (min(vgs_vals), max(vgs_vals), min(vds_vals), max(vds_vals))
        )
    return boxes


def plot_regions(out_path, boxes, rows, show_vertices, show_ideal):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, Rectangle

    fig, ax = plt.subplots(figsize=(8.0, 6.2))
    legend_handles = []

    if show_ideal:
        ax.fill([0, VTH, VTH, 0], [0, 0, VDD, VDD], alpha=0.08, color="C0")
        ax.fill([VTH, VDD, VDD], [0, 0, VDD - VTH], alpha=0.08, color="C1")
        ax.fill(
            [VTH, VDD, VDD, VTH],
            [0, VDD - VTH, VDD, VDD],
            alpha=0.08,
            color="C2",
        )
        ax.plot([VTH, VDD], [0, VDD - VTH], "k--", linewidth=0.7, alpha=0.6)
        legend_handles.extend(
            [
                Patch(facecolor="C0", alpha=0.35, label="ideal cutoff"),
                Patch(facecolor="C1", alpha=0.35, label="ideal linear"),
                Patch(facecolor="C2", alpha=0.35, label="ideal saturation"),
            ]
        )

    for vg0, vg1, vd0, vd1 in boxes:
        w = vg1 - vg0
        h = vd1 - vd0
        if w <= 0 or h <= 0:
            continue
        ax.add_patch(
            Rectangle(
                (vg0, vd0),
                w,
                h,
                facecolor="purple",
                edgecolor="indigo",
                linewidth=0.25,
                alpha=0.12,
                zorder=1,
            )
        )
    legend_handles.append(
        Patch(
            facecolor="purple",
            edgecolor="indigo",
            alpha=0.35,
            label="out_inv → (vgs,vds) bbox (n=%d)" % len(boxes),
        )
    )

    if show_vertices and rows:
        vgs = [r[0] for r in rows]
        vds = [r[1] for r in rows]
        ax.scatter(vgs, vds, s=6, c="0.15", alpha=0.35, zorder=3)
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="0.25",
                markersize=5,
                alpha=0.6,
                linestyle="None",
                label="out_reachable (n=%d)" % len(rows),
            )
        )

    ax.scatter([VGS0], [VDS0], s=140, c="cyan", marker="*", edgecolors="navy", linewidths=0.5, zorder=5)
    legend_handles.append(
        Line2D(
            [0],
            [0],
            marker="*",
            color="cyan",
            markeredgecolor="navy",
            markersize=12,
            linestyle="None",
            label="initial",
        )
    )

    ax.set_xlim(0, VDD)
    ax.set_ylim(0, VDD)
    ax.set_xlabel("vgs (V)")
    ax.set_ylabel("vds (V)")
    ax.set_title(
        "PHAVerLite invariant partition projected to (vgs, vds)\n"
        "Union of axis-aligned bounding boxes from each out_inv vertex block"
    )
    ax.legend(handles=legend_handles, loc="upper left", fontsize=7)
    ax.grid(alpha=0.2)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inv", type=Path, default=Path("out_inv"))
    ap.add_argument("--reachable", type=Path, default=Path("out_reachable"))
    ap.add_argument("-o", "--output", type=Path, default=Path("nmos_phas_vgs_vds_regions.png"))
    ap.add_argument("--no-vertices", action="store_true", help="Do not overlay out_reachable")
    ap.add_argument("--no-ideal", action="store_true", help="Do not draw ideal NMOS regions")
    args = ap.parse_args()

    if not args.inv.is_file():
        print("Missing %s — run phaverlite nmos_model.pha first (or use --inv PATH)." % args.inv, file=sys.stderr)
        return 1

    boxes = parse_out_inv_vgs_vds_boxes(args.inv)
    if not boxes:
        print("No boxes parsed from out_inv.", file=sys.stderr)
        return 1

    rows = []
    if not args.no_vertices and args.reachable.is_file():
        rows = parse_out_reachable_rows(args.reachable)

    try:
        plot_regions(args.output, boxes, rows, not args.no_vertices, not args.no_ideal)
    except ImportError:
        print("matplotlib required for plot_reachable_regions.py", file=sys.stderr)
        return 1

    print("Wrote %s (%d projected cells)" % (args.output.resolve(), len(boxes)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
