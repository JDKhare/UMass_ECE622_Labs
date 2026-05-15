#!/usr/bin/env python3
"""
Multi-panel lab4 figure: several views of the same reachable vertices.

Run after: phaverlite nmos_model.pha (from plots/<stamp>/ or with paths to out_*)
  python3 plot_lab4_dashboard.py --reachable .../out_reachable --inv .../out_inv -o .../nmos_phas_dashboard.png
  python3 plot_lab4_dashboard.py --also-split   # also nmos_phas_vgs_vdsg.png, nmos_phas_id_vds.png, nmos_phas_w_l.png beside -o
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from plot_reachable import (
    VDD,
    VTH,
    VGS0,
    VDS0,
    IDS_LEAK,
    IDS_MAX,
    classify_vertex,
    parse_out_reachable_rows,
)
from plot_reachable_regions import parse_out_inv_vgs_vds_boxes


def _scatter_by_mode(ax, rows, xidx, yidx, xlabel, ylabel, title, xlim=None, ylim=None, hline_specs=None):
    if hline_specs:
        for y, color, ls, lab in hline_specs:
            ax.axhline(y, color=color, ls=ls, lw=0.9, label=lab)
    by = {"cutoff": ([], []), "linear": ([], []), "saturation": ([], [])}
    for r in rows:
        lab = classify_vertex(r[0], r[1], r[4])
        by[lab][0].append(r[xidx])
        by[lab][1].append(r[yidx])
    colors = {"cutoff": "#1f77b4", "linear": "#ff7f0e", "saturation": "#2ca02c"}
    for lab in ("cutoff", "linear", "saturation"):
        xs, ys = by[lab]
        if xs:
            ax.scatter(
                xs,
                ys,
                s=12,
                c=colors[lab],
                alpha=0.6,
                label="%s (n=%d)" % (lab, len(xs)),
                edgecolors="none",
                zorder=5,
            )
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10)
    ax.legend(loc="best", fontsize=7)
    ax.grid(alpha=0.25)


def build_dashboard(rows, boxes):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 10.0))
    vgs = [r[0] for r in rows]
    vds = [r[1] for r in rows]
    vdsg = [r[4] for r in rows]

    # (0,0) vgs–vds: ideal regions + hexbin + mode scatter
    ax = axes[0, 0]
    ax.fill([0, VTH, VTH, 0], [0, 0, VDD, VDD], alpha=0.1, color="C0")
    ax.fill([VTH, VDD, VDD], [0, 0, VDD - VTH], alpha=0.1, color="C1")
    ax.fill([VTH, VDD, VDD, VTH], [0, VDD - VTH, VDD, VDD], alpha=0.1, color="C2")
    ax.plot([VTH, VDD], [0, VDD - VTH], "k--", linewidth=0.7, alpha=0.7)
    ax.hexbin(
        vgs,
        vds,
        gridsize=28,
        extent=(0, VDD, 0, VDD),
        mincnt=1,
        cmap="Greys",
        alpha=0.45,
        linewidths=0,
        zorder=2,
    )
    _scatter_by_mode(
        ax,
        rows,
        0,
        1,
        "vgs (V)",
        "vds (V)",
        "(A) vgs–vds vs ideal regions + density",
        xlim=(0, VDD),
        ylim=(0, VDD),
    )
    ax.scatter([VGS0], [VDS0], s=100, c="cyan", marker="*", zorder=6, edgecolors="navy", linewidths=0.4)
    ax.set_aspect("equal", adjustable="box")

    # (0,1) vgs–vdsg: knee is vdsg = -Vth
    ax = axes[0, 1]
    ax.axhline(-VTH, color="black", linestyle="--", linewidth=1.0, label="vdsg = -Vth (knee)")
    ax.axvline(VTH, color="gray", linestyle=":", linewidth=0.9, label="vgs = Vth")
    ylo = min(min(vdsg), -VDD) - 0.1
    yhi = max(max(vdsg), VDD) + 0.1
    _scatter_by_mode(
        ax,
        rows,
        0,
        4,
        "vgs (V)",
        "vdsg = vds - vgs (V)",
        "(B) vgs–vdsg (knee is horizontal)",
        xlim=(0, VDD),
        ylim=(ylo, yhi),
    )
    ax.scatter([VGS0], [VDS0 - VGS0], s=100, c="cyan", marker="*", zorder=6, edgecolors="navy", linewidths=0.4)

    # (1,0) vds–ids (drain sweep at fixed Vgs strip)
    ax = axes[1, 0]
    ids_vals = [r[5] for r in rows]
    ymax = max(max(ids_vals), IDS_MAX) * 1.05
    _scatter_by_mode(
        ax,
        rows,
        1,
        5,
        "vds (V)",
        "ids (A)",
        "(C) vds–ids (piecewise ids' vs Vds ramp)",
        xlim=(0, VDD),
        ylim=(0, ymax),
        hline_specs=[
            (IDS_MAX, "darkred", "--", "IDS_MAX_N"),
            (IDS_LEAK, "gray", ":", "IDS_LEAK_N (cutoff cap)"),
        ],
    )
    ax.scatter([VDS0], [0.0], s=100, c="cyan", marker="*", zorder=6, edgecolors="navy", linewidths=0.4)

    # (1,1) partition footprint + vertices
    ax = axes[1, 1]
    for vg0, vg1, vd0, vd1 in boxes:
        ww, hh = vg1 - vg0, vd1 - vd0
        if ww <= 0 or hh <= 0:
            continue
        ax.add_patch(
            Rectangle(
                (vg0, vd0),
                ww,
                hh,
                facecolor="mediumpurple",
                edgecolor="indigo",
                linewidth=0.2,
                alpha=0.14,
            )
        )
    ax.scatter(vgs, vds, s=5, c="0.2", alpha=0.35, zorder=3)
    ax.set_xlim(0, VDD)
    ax.set_ylim(0, VDD)
    ax.set_xlabel("vgs (V)")
    ax.set_ylabel("vds (V)")
    ax.set_title("(D) out_inv (vgs,vds) boxes + vertices")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2)

    cnt = Counter(classify_vertex(r[0], r[1], r[4]) for r in rows)
    summary = "  ".join("%s=%d" % (k, cnt[k]) for k in ("cutoff", "linear", "saturation"))
    fig.suptitle(
        "Lab4 NMOS hybrid — VDD=%.2f V, Vth=%.3f V  |  %s  |  N=%d vertices, %d inv cells"
        % (VDD, VTH, summary, len(rows), len(boxes)),
        fontsize=11,
        y=1.02,
    )
    fig.tight_layout()
    return fig


def write_split_plots(rows, out_dir: Path):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.axhline(-VTH, color="k", ls="--", label="vdsg = -Vth")
    ax.axvline(VTH, color="gray", ls=":", label="vgs = Vth")
    _scatter_by_mode(
        ax,
        rows,
        0,
        4,
        "vgs (V)",
        "vdsg (V)",
        "vgs–vdsg (reachable vertices)",
    )
    fig.tight_layout()
    p = out_dir / "nmos_phas_vgs_vdsg.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Wrote %s" % p.resolve())

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ids_vals = [r[5] for r in rows]
    ymax = max(max(ids_vals), IDS_MAX) * 1.05
    _scatter_by_mode(
        ax,
        rows,
        1,
        5,
        "vds (V)",
        "ids (A)",
        "vds–ids (reachable vertices)",
        xlim=(0, VDD),
        ylim=(0, ymax),
        hline_specs=[
            (IDS_MAX, "darkred", "--", "IDS_MAX_N"),
            (IDS_LEAK, "gray", ":", "IDS_LEAK_N"),
        ],
    )
    fig.tight_layout()
    p = out_dir / "nmos_phas_id_vds.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Wrote %s" % p.resolve())

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.scatter([r[2] for r in rows], [r[3] for r in rows], s=12, c="teal", alpha=0.5, edgecolors="none")
    ax.set_xlabel("w")
    ax.set_ylabel("l")
    ax.set_title("w vs l (reachable vertices; L ≈ L_MIN)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    p = out_dir / "nmos_phas_w_l.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Wrote %s" % p.resolve())


def main():
    ap = argparse.ArgumentParser(description="Multi-panel lab4 plots from out_reachable / out_inv.")
    ap.add_argument("--reachable", type=Path, default=Path("out_reachable"))
    ap.add_argument("--inv", type=Path, default=Path("out_inv"))
    ap.add_argument("-o", "--output", type=Path, default=Path("nmos_phas_dashboard.png"))
    ap.add_argument(
        "--also-split",
        action="store_true",
        help="Also write nmos_phas_vgs_vdsg.png, nmos_phas_id_vds.png, nmos_phas_w_l.png next to -o",
    )
    args = ap.parse_args()

    if not args.reachable.is_file():
        print("Missing %s" % args.reachable, file=sys.stderr)
        return 1
    rows = parse_out_reachable_rows(args.reachable)
    if not rows:
        print("No rows in out_reachable.", file=sys.stderr)
        return 1

    boxes = parse_out_inv_vgs_vds_boxes(args.inv) if args.inv.is_file() else []

    try:
        import matplotlib.pyplot as plt

        fig = build_dashboard(rows, boxes)
        fig.savefig(args.output, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print("Wrote %s" % args.output.resolve())
    except ImportError:
        print("matplotlib required.", file=sys.stderr)
        return 1

    if args.also_split:
        write_split_plots(rows, args.output.parent)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
