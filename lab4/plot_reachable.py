#!/usr/bin/env python3
"""
Plot (vgs, vds) projection of PHAVerLite out_reachable over the ideal NMOS regions.

For the **partitioned region** in the voltage plane (union of `out_inv` cell projections),
see `plot_reachable_regions.py` → `nmos_phas_vgs_vds_regions.png` (or pass `-o`).

For the course **`graph`** SVG (2-column projection), run `bash plot_graph_phaver.sh`.

Default: matplotlib PNG (requires matplotlib).
Optional: --svg PATH for a second export (or automatic SVG fallback if matplotlib is missing).

Run after:  phaverlite nmos_model.pha
Input:     out_reachable (columns: vgs vds w l vdsg [ids])
"""

import argparse
import math
import sys
from pathlib import Path

# Match nmos_model.pha (VDD_N, VTH0_N, IDS_*); initial (vgs,vds) for star marker
VDD = 1.8
VTH = 0.424
IDS_LEAK = 1e-9
IDS_MAX = 0.15
VGS0, VDS0 = 0.25, 0.55
EPS = 1e-9


def parse_out_reachable_rows(path):
    """Return list of (vgs, vds, w, l, vdsg, ids) from PHAVerLite raw vertex lines."""
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            base = tuple(float(x) for x in parts[:5])
            ids = float(parts[5]) if len(parts) >= 6 else 0.0
            rows.append(base + (ids,))
        except ValueError:
            continue
    return rows


def parse_out_reachable(path):
    """Backward-compatible (vgs, vds) only."""
    rows = parse_out_reachable_rows(path)
    return [r[0] for r in rows], [r[1] for r in rows]


def classify_vertex(vgs, vds, vdsg):
    """
    Classify a raw vertex by voltage inequalities (matches automaton invariants).
    PHAVerLite does not print location names on each line; we infer from (vgs, vdsg).
    """
    if vgs < VTH - EPS:
        return "cutoff"
    if vdsg <= -VTH + 1e-6:
        return "linear"
    return "saturation"


def _xy(vg, vd, w, h, pad):
    sx = pad + (vg / VDD) * (w - 2 * pad)
    sy = h - pad - (vd / VDD) * (h - 2 * pad)
    return sx, sy


def write_svg(path, vgs, vds, w=640, h=560, pad=48):
    """Minimal SVG fallback when matplotlib is not available."""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
        % (w, h, w, h)
    )
    lines.append(
        '<rect width="100%" height="100%" fill="white"/>'
        '<style>text{font-family:system-ui,sans-serif;font-size:12px}</style>'
    )

    def poly(points, fill, stroke, opacity=0.25):
        pts = " ".join("%.1f,%.1f" % (px, py) for px, py in points)
        lines.append(
            '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1" fill-opacity="%.2f"/>'
            % (pts, fill, stroke, opacity)
        )

    p_cut = [
        _xy(0, 0, w, h, pad),
        _xy(VTH, 0, w, h, pad),
        _xy(VTH, VDD, w, h, pad),
        _xy(0, VDD, w, h, pad),
    ]
    poly(p_cut, "#a6c8ff", "#3366aa", 0.28)
    p_lin = [
        _xy(VTH, 0, w, h, pad),
        _xy(VDD, 0, w, h, pad),
        _xy(VDD, VDD - VTH, w, h, pad),
    ]
    poly(p_lin, "#ffd4a6", "#aa6633", 0.28)
    p_sat = [
        _xy(VTH, 0, w, h, pad),
        _xy(VDD, VDD - VTH, w, h, pad),
        _xy(VDD, VDD, w, h, pad),
        _xy(VTH, VDD, w, h, pad),
    ]
    poly(p_sat, "#c8ffc8", "#33aa33", 0.28)

    k0, k1 = _xy(VTH, 0, w, h, pad), _xy(VDD, VDD - VTH, w, h, pad)
    lines.append(
        '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="black" '
        'stroke-dasharray="6,4" stroke-width="1.2"/>' % (k0[0], k0[1], k1[0], k1[1])
    )

    for vg, vd in zip(vgs, vds):
        if not (math.isfinite(vg) and math.isfinite(vd)):
            continue
        x, y = _xy(vg, vd, w, h, pad)
        lines.append('<circle cx="%.2f" cy="%.2f" r="2.5" fill="black" opacity="0.35"/>' % (x, y))

    ix, iy = _xy(VGS0, VDS0, w, h, pad)
    lines.append(
        '<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="red" stroke="darkred" stroke-width="1"/>'
        % (ix, iy - 8, ix - 7, iy + 6, ix + 7, iy + 6)
    )

    lines.append('<text x="%d" y="%d">reachable (vgs,vds) vs ideal regions</text>' % (pad, pad - 12))
    lines.append(
        '<text x="%d" y="%d">N=%d samples from out_reachable</text>' % (pad, h - 18, len(vgs))
    )
    lines.append("</svg>")
    path.write_text("\n".join(lines))


def write_matplotlib(out_path, rows):
    import matplotlib.pyplot as plt

    vgs = [r[0] for r in rows]
    vds = [r[1] for r in rows]
    n_raw = len(rows)
    uniq = len({(round(vg, 4), round(vd, 4)) for vg, vd in zip(vgs, vds)})

    by = {"cutoff": ([], []), "linear": ([], []), "saturation": ([], [])}
    for r in rows:
        vg, vd, vsg = r[0], r[1], r[4]
        lab = classify_vertex(vg, vd, vsg)
        by[lab][0].append(vg)
        by[lab][1].append(vd)
    n_cut, n_lin, n_sat = len(by["cutoff"][0]), len(by["linear"][0]), len(by["saturation"][0])

    fig, ax = plt.subplots(figsize=(7.5, 5.8))
    ax.fill([0, VTH, VTH, 0], [0, 0, VDD, VDD], alpha=0.12, color="C0", label="cutoff (ideal)")
    ax.fill([VTH, VDD, VDD], [0.0, 0.0, VDD - VTH], alpha=0.12, color="C1", label="linear (ideal)")
    ax.fill(
        [VTH, VDD, VDD, VTH],
        [0.0, VDD - VTH, VDD, VDD],
        alpha=0.12,
        color="C2",
        label="saturation (ideal)",
    )
    ax.plot([VTH, VDD], [0.0, VDD - VTH], "k--", linewidth=0.8, label="knee")

    hb = ax.hexbin(
        vgs,
        vds,
        gridsize=36,
        extent=(0, VDD, 0, VDD),
        mincnt=1,
        cmap="Greys",
        alpha=0.55,
        linewidths=0,
        zorder=3,
    )
    cb = fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("vertices / bin (all modes)")

    ax.scatter(
        by["cutoff"][0],
        by["cutoff"][1],
        s=14,
        c="#1f77b4",
        alpha=0.55,
        linewidths=0,
        zorder=5,
        label="vertices: cutoff (n=%d)" % n_cut,
    )
    ax.scatter(
        by["linear"][0],
        by["linear"][1],
        s=22,
        c="#ff7f0e",
        alpha=0.85,
        linewidths=0.2,
        edgecolors="darkred",
        zorder=6,
        label="vertices: linear / triode (n=%d)" % n_lin,
    )
    ax.scatter(
        by["saturation"][0],
        by["saturation"][1],
        s=12,
        c="#2ca02c",
        alpha=0.45,
        linewidths=0,
        zorder=4,
        label="vertices: saturation (n=%d)" % n_sat,
    )

    ax.scatter([VGS0], [VDS0], s=160, c="cyan", marker="*", edgecolors="darkblue", linewidths=0.6, zorder=7, label="initial")

    ax.set_xlim(0, VDD)
    ax.set_ylim(0, VDD)
    ax.set_xlabel("vgs (V)")
    ax.set_ylabel("vds (V)")
    ax.set_title(
        "PHAVerLite reachable (vgs, vds) — colored by voltage class (vdsg from file)\n"
        "%d vertices, %d distinct (vgs,vds); PHAVerLite: lin_set is reachable (often few triode vertices)"
        % (n_raw, uniq)
    )
    ax.legend(loc="upper left", fontsize=7)
    ax.grid(alpha=0.25)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description="Plot out_reachable in the vgs–vds plane.")
    p.add_argument("--reachable", type=Path, default=Path("out_reachable"))
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("nmos_phas_vgs_vds.png"),
        help="Matplotlib output image (default: nmos_phas_vgs_vds.png)",
    )
    p.add_argument(
        "--svg",
        type=Path,
        default=None,
        help="If set, also write this SVG path (vector copy)",
    )
    p.add_argument(
        "--svg-only",
        action="store_true",
        help="Skip matplotlib; write only SVG to --svg (default file: nmos_phas_vgs_vds.svg)",
    )
    args = p.parse_args()

    if not args.reachable.is_file():
        print("Missing %s — run phaverlite nmos_model.pha first (or use --reachable PATH)." % args.reachable, file=sys.stderr)
        return 1

    rows = parse_out_reachable_rows(args.reachable)
    if not rows:
        print("No sample points parsed from out_reachable.", file=sys.stderr)
        return 1

    vgs, vds = [r[0] for r in rows], [r[1] for r in rows]

    if args.svg_only:
        svg_path = args.svg if args.svg is not None else Path("nmos_phas_vgs_vds.svg")
        write_svg(svg_path, vgs, vds)
        print("Wrote %s (matplotlib skipped)" % svg_path.resolve())
        return 0

    try:
        write_matplotlib(args.output, rows)
        print("Wrote %s" % args.output.resolve())
    except ImportError:
        svg_path = args.svg if args.svg is not None else Path("nmos_phas_vgs_vds.svg")
        write_svg(svg_path, vgs, vds)
        print("matplotlib not found; wrote %s instead." % svg_path.resolve(), file=sys.stderr)
        return 0

    if args.svg is not None:
        write_svg(args.svg, vgs, vds)
        print("Wrote %s" % args.svg.resolve())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
