#!/usr/bin/env python3
"""Patch cmos_inverter_vin_{low,high}.pha for one VIN_OP strip + consistent initial discrete mode."""
import pathlib
import re
import sys

VTH_N = 0.424
VTH_P = -0.424


def _pick_initial_low(mid, vdd):
    """Only Q0=(cut,lin) and Q1=(cut,sat) exist."""
    vout0 = 0.9
    vdsg0 = vout0 - mid
    vgp0 = mid - vdd
    if vdsg0 >= -VTH_P - 1e-9:
        return "m0", vout0, vdsg0, vgp0
    return "m1", vout0, vdsg0, vgp0


def _pick_initial_high(mid, vdd):
    order = [
        ("lin", "cut"),
        ("lin", "lin"),
        ("lin", "sat"),
        ("sat", "cut"),
        ("sat", "lin"),
        ("sat", "sat"),
    ]
    vout0 = 0.2
    vdsg0 = vout0 - mid
    vgp0 = mid - vdd
    if mid <= VTH_N + 1e-9:
        raise ValueError("Vin high model: mid must exceed VTH_N")
    nst = "lin" if vdsg0 <= -VTH_N + 1e-9 else "sat"
    if VTH_P - 1e-9 <= vgp0 <= 0.0 + 1e-9:
        pst = "cut"
    else:
        pst = "lin" if vdsg0 >= -VTH_P - 1e-9 else "sat"
    if (nst, pst) not in order:
        vout0 = 0.05
        vdsg0 = vout0 - mid
        nst = "lin" if vdsg0 <= -VTH_N + 1e-9 else "sat"
        pst = "cut" if (VTH_P - 1e-9 <= vgp0 <= 0.0 + 1e-9) else (
            "lin" if vdsg0 >= -VTH_P - 1e-9 else "sat"
        )
    return "m%d" % order.index((nst, pst)), vout0, vdsg0, vgp0


def main():
    if len(sys.argv) != 6:
        print(
            "usage: patch_inverter_for_vin.py SRC.pha OUT.pha VIN_OP EPS VDD",
            file=sys.stderr,
        )
        return 1
    src, dst, op_s, eps_s, vdd_s = sys.argv[1:6]
    op = float(op_s)
    eps = float(eps_s)
    vdd = float(vdd_s)
    lo = max(0.0, op - eps)
    hi = min(vdd, op + eps)
    mid = 0.5 * (lo + hi)
    vgp_lo = lo - vdd
    vgp_hi = hi - vdd
    lo_gp = max(vgp_lo, VTH_P)
    hi_gp = min(vgp_hi, 0.0)
    if lo_gp > hi_gp + 1e-12:
        lo_gp = hi_gp = VTH_P

    src_path = pathlib.Path(src)
    is_low = "vin_low" in src_path.name
    if is_low:
        init_loc, vout0, vdsg0, vgp0 = _pick_initial_low(mid, vdd)
    else:
        init_loc, vout0, vdsg0, vgp0 = _pick_initial_high(mid, vdd)

    text = pathlib.Path(src).read_text()
    lines = text.splitlines(True)
    out = []
    for ln in lines:
        if re.match(r"^VIN_LO:=", ln):
            out.append("VIN_LO:=%.6f;\n" % lo)
        elif re.match(r"^VIN_HI:=", ln):
            out.append("VIN_HI:=%.6f;\n" % hi)
        elif re.match(r"^VGP_LO_P:=", ln):
            out.append("VGP_LO_P:=%.6f;\n" % vgp_lo)
        elif re.match(r"^VGP_HI_P:=", ln):
            out.append("VGP_HI_P:=%.6f;\n" % vgp_hi)
        elif re.match(r"^VGP_CUTOFF_LO_P:=", ln):
            out.append("VGP_CUTOFF_LO_P:=%.6f;\n" % lo_gp)
        elif re.match(r"^VGP_CUTOFF_HI_P:=", ln):
            out.append("VGP_CUTOFF_HI_P:=%.6f;\n" % hi_gp)
        elif re.match(r"^\s*initially:", ln):
            out.append(
                "    initially: %s & vin == %.6f & vout == %.6f & vdsg == %.6f & vgp == %.6f;\n"
                % (init_loc, mid, vout0, vdsg0, vgp0)
            )
        else:
            out.append(ln)
    pathlib.Path(dst).write_text("".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
