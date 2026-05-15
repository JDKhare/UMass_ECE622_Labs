#!/usr/bin/env python3
"""Write ANALYSIS_REPORT.txt in a stamped plot directory (figures + hybrid states)."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

VDD = 1.8
VTH = 0.424


def _count_reachable_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    n = 0
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 5:
                n += 1
    return n


def _grep_log_summary(log: Path) -> str:
    if not log.is_file():
        return "(no log file)\n"
    lines = log.read_text().splitlines()
    hits = [ln for ln in lines if "reachable" in ln.lower()]
    if not hits:
        return "(no reachability summary lines found in log)\n"
    return "\n".join(hits[-20:]) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--plot-dir", type=Path, required=True)
    ap.add_argument("--log", type=Path, default=None, help="phaverlite_vgs_sweep.log path")
    args = ap.parse_args()
    root = args.plot_dir.resolve()
    if not root.is_dir():
        print("Not a directory: %s" % root, file=sys.stderr)
        return 1

    bins = []
    for sub in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("vg_")):
        meta = sub / "meta.txt"
        vop = None
        if meta.is_file():
            for ln in meta.read_text().splitlines():
                if ln.startswith("VGS_OP="):
                    vop = float(ln.split("=", 1)[1].strip())
        nreach = _count_reachable_lines(sub / "out_reachable")
        bins.append((sub.name, vop, nreach))

    imgs = sorted(root.glob("*.png")) + sorted(root.glob("*.svg"))

    lines = []
    lines.append("NMOS PHAVerLite — analysis summary")
    lines.append("Generated: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("Run folder: %s" % root.name)
    lines.append("")
    lines.append("=" * 72)
    lines.append("1. Hybrid automaton states (locations)")
    lines.append("=" * 72)
    lines.append(
        "The model in nmos_model.pha uses one automaton `nmos` with three locations "
        "(MOS operating regions):"
    )
    lines.append("")
    lines.append(
        "  cutoff           — vgs on the cutoff gate interval (VGS_CUTOFF_*; see note below) "
        "with vgs <= VTH0_N; ids bounded by IDS_LEAK_N; ids'==0 while vds ramps."
    )
    lines.append(
        "  linear_region    — vgs strip above threshold; triode side vdsg <= -VTH0_N "
        "(vds <= vgs - Vth knee); ids'==IDS_PRIME_LIN (steeper Id vs Vds caricature)."
    )
    lines.append(
        "  saturation_region — vgs strip above threshold; vdsg >= -VTH0_N; "
        "ids'==IDS_PRIME_SAT (shallow Id vs Vds, finite-output-resistance style)."
    )
    lines.append("")
    lines.append(
        "Discrete sync label: tau (mode jumps when linear guard predicates cross)."
    )
    lines.append("")
    lines.append(
        "Implementation note: loc cutoff uses VGS_CUTOFF_LO_N / VGS_CUTOFF_HI_N "
        "(intersection of the swept gate strip with vgs <= VTH0_N, or a degenerate point at "
        "VTH0_N when the strip is entirely above threshold) so the location stays well-formed "
        "for PHAVerLite; linear_region and saturation_region use the full VGS_LO_N / VGS_HI_N strip."
    )
    lines.append("")
    lines.append("=" * 72)
    lines.append("2. Continuous state (per PHAVerLite contr_var)")
    lines.append("=" * 72)
    lines.append("  vgs   — gate-source voltage (V); held on a narrow DC strip per sweep bin.")
    lines.append("  vds   — drain-source voltage (V); swept along [0, VDD_N] with vds'==VDS_RAMP.")
    lines.append("  w, l  — drawn width/length bounds (static: w'==0, l'==0).")
    lines.append("  vdsg  — vds - vgs; with vgs'==0, vdsg'==vds'==VDS_RAMP on continuous flow.")
    lines.append("  ids   — drain current proxy (A); piecewise ids' and caps IDS_LEAK_N / IDS_MAX_N.")
    lines.append("")
    lines.append("Nominal parameters (see nmos_model.pha): VDD_N=%.1f V, VTH0_N=%.3f V." % (VDD, VTH))
    lines.append("")
    lines.append("=" * 72)
    lines.append("3. Vgs DC sweep bins (six runs)")
    lines.append("=" * 72)
    if not bins:
        lines.append("(no vg_* subdirectories found)")
    else:
        lines.append("%-28s  %12s  %14s" % ("Subdirectory", "VGS_OP (V)", "out_reachable rows"))
        lines.append("-" * 56)
        for name, vop, nreach in bins:
            vo = "%.2f" % vop if vop is not None else "?"
            lines.append("%-28s  %12s  %14d" % (name, vo, nreach))
    lines.append("")
    lines.append("Each bin writes: out_reachable, out_inv, meta.txt (VGS_OP, EPS).")
    lines.append("")
    lines.append("=" * 72)
    lines.append("4. Figures in this folder (paths relative to this report)")
    lines.append("=" * 72)
    if not imgs:
        lines.append("(no PNG/SVG at stamp root — check subfolders)")
    else:
        for p in imgs:
            lines.append("  %s" % p.name)
    lines.append("")
    lines.append(
        "Primary deliverable: nmos_phas_id_vds_family.png — reachable I_D vs V_DS "
        "(matplotlib); axes labeled V_DS, I_D; color encodes each DC V_GS bin."
    )
    lines.append(
        "Optional: nmos_graph_id_vds_firstbin.svg — plotutils graph, I_D vs V_DS (cols 2,6), "
        "invariant vs reachable for the first vg_* bin only."
    )
    lines.append(
        "Optional first-bin matplotlib views (if generated by the pipeline): "
        "firstbin_nmos_phas_vgs_vds*.png/svg, firstbin_nmos_phas_vgs_vds_regions.png, "
        "firstbin_nmos_phas_dashboard.png — (vgs,vds) and partition views for one Vgs step only."
    )
    lines.append("")
    lines.append(
        "PHAVer / plotutils drain I-V graphs: phaver_graph_id_vds_all_vgs.svg overlays "
        "reachable (V_DS, I_D) for every vg_* bin on one figure (axes: V_DS (V), I_D (A)). "
        "Per bin, phaver_graph_<vgdir>_vds_ids.svg shows invariant vs reachable in the same plane. "
        "Same workflow as README_PHAVERLITE.md: plotutils `graph` on floating-point vertex dumps. "
        "This toolchain does not ship a separate PHAVer GUI."
    )
    lines.append("")
    lines.append(
        "Unreachability: boolean queries in the .pha file (e.g. sat_set, lin_set, invalid_*) "
        "prove (under the PHAVerLite abstraction) that those sets are not reachable. "
        "A 2D graph projection only shows which vertices lie inside the invariant enclosure "
        "versus the reachable enclosure in that projection; it is not, by itself, a "
        "full-dimensional certificate that a state is 'absolutely' unreachable."
    )
    lines.append("")
    lines.append("=" * 72)
    lines.append("5. How to read the Id–Vds family plot")
    lines.append("=" * 72)
    lines.append(
        "Each colored cloud is the projection of reachable polyhedron vertices for one "
        "fixed gate strip. Steeper motion of ids versus vds in triode and shallower in "
        "saturation come from IDS_PRIME_LIN vs IDS_PRIME_SAT, not from BSIM equations."
    )
    lines.append(
        "This is a hybrid reachability abstraction: it answers what (vds, ids) pairs are "
        "compatible with the piecewise-linear dynamics and guards, not a single measured trace."
    )
    lines.append("")
    lines.append("=" * 72)
    lines.append("6. PHAVerLite log excerpt (reachability lines)")
    lines.append("=" * 72)
    if args.log:
        lines.append(_grep_log_summary(args.log))
    else:
        lines.append("(no --log passed)\n")

    out_path = root / "ANALYSIS_REPORT.txt"
    out_path.write_text("\n".join(lines) + "\n")
    print("Wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
