#!/usr/bin/env python3
"""Patch pmos_model.pha for one VGS_OP sweep (gate strip + consistent initial location)."""
import pathlib
import re
import sys


def main():
    if len(sys.argv) != 6:
        print(
            "usage: patch_pmos_for_vgs.py SRC.pha OUT.pha VGS_OP EPS VDD",
            file=sys.stderr,
        )
        return 1
    src, dst, op_s, eps_s, vdd_s = sys.argv[1:6]
    op = float(op_s)
    eps = float(eps_s)
    vdd = float(vdd_s)
    vth_p = -0.424
    vds0 = -0.01
    lo = max(-vdd, op - eps)
    hi = min(0.0, op + eps)
    mid = 0.5 * (lo + hi)
    vdsg = vds0 - mid
    if mid > vth_p + 1e-9:
        loc = "cutoff"
    else:
        loc = (
            "linear_region"
            if vdsg >= -vth_p - 1e-9
            else "saturation_region"
        )

    lo_c = max(lo, vth_p)
    hi_c = min(hi, 0.0)
    if lo_c > hi_c + 1e-12:
        lo_c = hi_c = vth_p

    text = pathlib.Path(src).read_text()
    lines = text.splitlines(True)
    out = []
    for ln in lines:
        if re.match(r"^VGS_LO_P:=", ln):
            out.append("VGS_LO_P:=%.6f;\n" % lo)
        elif re.match(r"^VGS_HI_P:=", ln):
            out.append("VGS_HI_P:=%.6f;\n" % hi)
        elif re.match(r"^VGS_CUTOFF_LO_P:=", ln):
            out.append("VGS_CUTOFF_LO_P:=%.6f;\n" % lo_c)
        elif re.match(r"^VGS_CUTOFF_HI_P:=", ln):
            out.append("VGS_CUTOFF_HI_P:=%.6f;\n" % hi_c)
        elif re.match(r"^\s*initially:", ln):
            out.append(
                "    initially: %s & vgs == %.6f & vds == %.6f & vdsg == %.6f &\n"
                % (loc, mid, vds0, vdsg)
            )
        else:
            out.append(ln)
    pathlib.Path(dst).write_text("".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
