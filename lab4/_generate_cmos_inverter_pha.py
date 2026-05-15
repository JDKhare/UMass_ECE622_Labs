#!/usr/bin/env python3
"""
Emit CMOS inverter PHAVerLite models (closed product subsets per DC input band).

- cmos_inverter_vin_low.pha: NMOS cutoff only x PMOS on — (cut,lin), (cut,sat).
- cmos_inverter_vin_high.pha: NMOS on x PMOS — six (lin|sat) x (cut|lin|sat) pairs.

The full 3x3 joint includes n_cut_p_cut, which is empty for a tied CMOS inverter on any
single Vin strip; it is omitted everywhere.

Run: python3 lab4/_generate_cmos_inverter_pha.py
"""

NMODES = ("cut", "lin", "sat")
PMODES = ("cut", "lin", "sat")


def skip_pair(n, p):
    return (n, p) == ("cut", "cut")


def loc(n, p, ordered):
    return "m%d" % ordered.index((n, p))


def n_inv(n):
    if n == "cut":
        return (
            "vin >= VIN_LO & vin <= VIN_HI &\n"
            "              vin >= 0 & vin <= VTH0_N &\n"
            "              vout >= 0 & vout <= VDD &\n"
            "              vdsg >= -VDD & vdsg <= VDD &\n"
            "              vgp >= -VDD & vgp <= 0"
        )
    if n == "lin":
        return (
            "vin >= VIN_LO & vin <= VIN_HI &\n"
            "              vin >= VTH0_N & vin <= VDD &\n"
            "              vout >= 0 & vout <= VDD &\n"
            "              vdsg <= -VTH0_N &\n"
            "              vdsg >= -VDD & vdsg <= VDD &\n"
            "              vgp >= -VDD & vgp <= 0"
        )
    if n == "sat":
        return (
            "vin >= VIN_LO & vin <= VIN_HI &\n"
            "              vin >= VTH0_N & vin <= VDD &\n"
            "              vout >= 0 & vout <= VDD &\n"
            "              vdsg >= -VTH0_N &\n"
            "              vdsg >= -VDD & vdsg <= VDD &\n"
            "              vgp >= -VDD & vgp <= 0"
        )
    raise ValueError(n)


def p_inv(p):
    if p == "cut":
        return (
            "vgp >= VGP_CUTOFF_LO_P & vgp <= VGP_CUTOFF_HI_P &\n"
            "              vgp >= VTH0_P & vgp <= 0 &\n"
            "              vout >= 0 & vout <= VDD"
        )
    if p == "lin":
        return (
            "vgp >= VGP_LO_P & vgp <= VGP_HI_P &\n"
            "              vgp <= VTH0_P & vgp >= -VDD &\n"
            "              vout >= 0 & vout <= VDD &\n"
            "              vdsg >= -VTH0_P &\n"
            "              vdsg >= -VDD & vdsg <= VDD"
        )
    if p == "sat":
        return (
            "vgp >= VGP_LO_P & vgp <= VGP_HI_P &\n"
            "              vgp <= VTH0_P & vgp >= -VDD &\n"
            "              vout >= 0 & vout <= VDD &\n"
            "              vdsg <= -VTH0_P &\n"
            "              vdsg >= -VDD & vdsg <= VDD"
        )
    raise ValueError(p)


def vout_prime(n, p):
    n_on = n in ("lin", "sat")
    p_on = p in ("lin", "sat")
    if n_on and p_on:
        return "0"
    if n_on and not p_on:
        return "-VOUT_RAMP"
    if p_on and not n_on:
        return "VOUT_RAMP"
    return "0"


def n_edges(n):
    if n == "cut":
        return [
            ("vin >= VTH0_N & vdsg <= -VTH0_N", "lin"),
            ("vin >= VTH0_N & vdsg >= -VTH0_N", "sat"),
        ]
    if n == "lin":
        return [
            ("vdsg >= -VTH0_N", "sat"),
            ("vin <= VTH0_N", "cut"),
        ]
    if n == "sat":
        return [
            ("vdsg <= -VTH0_N", "lin"),
            ("vin <= VTH0_N", "cut"),
        ]
    raise ValueError(n)


def p_edges(p):
    if p == "cut":
        return [
            ("vgp <= VTH0_P & vdsg >= -VTH0_P", "lin"),
            ("vgp <= VTH0_P & vdsg <= -VTH0_P", "sat"),
        ]
    if p == "lin":
        return [
            ("vdsg <= -VTH0_P", "sat"),
            ("vgp >= VTH0_P", "cut"),
        ]
    if p == "sat":
        return [
            ("vdsg >= -VTH0_P", "lin"),
            ("vgp >= VTH0_P", "cut"),
        ]
    raise ValueError(p)


def combined_inv(n, p):
    parts = []
    for ln in n_inv(n).splitlines():
        t = ln.strip().rstrip("&").strip()
        if t:
            parts.append(t)
    for ln in p_inv(p).splitlines():
        t = ln.strip().rstrip("&").strip()
        if t:
            parts.append(t)
    return " &\n              ".join(parts)


def emit_one(ordered, meta, vin_block, tail_queries):
    lines = []
    lines.append(meta)
    lines.append(vin_block)
    lines.append(
        """
automaton cmos_inv

  contr_var: vin, vout, vdsg, vgp;
  synclabs: tau;
"""
    )
    allowed = set(ordered)
    for n, p in ordered:
        lname = loc(n, p, ordered)
        inv = combined_inv(n, p)
        vp = vout_prime(n, p)
        lines.append("  loc %s:\n" % lname)
        lines.append("        while %s\n\n" % inv)
        lines.append(
            "        wait {vin'==0 & vgp'==0 & vout'==%s & vdsg'==vout'};\n\n" % vp
        )
        for g, nn in n_edges(n):
            if skip_pair(nn, p) or (nn, p) not in allowed:
                continue
            dest = loc(nn, p, ordered)
            lines.append(
                "        when %s\n        sync tau\n"
                "        do{vin'==vin & vout'==vout & vdsg'==vdsg & vgp'==vgp}\n"
                "        goto %s;\n\n" % (g, dest)
            )
        for g, pp in p_edges(p):
            if skip_pair(n, pp) or (n, pp) not in allowed:
                continue
            dest = loc(n, pp, ordered)
            lines.append(
                "        when %s\n        sync tau\n"
                "        do{vin'==vin & vout'==vout & vdsg'==vdsg & vgp'==vgp}\n"
                "        goto %s;\n\n" % (g, dest)
            )
    lines.append(tail_queries)
    return "".join(lines)


def main():
    from pathlib import Path

    root = Path(__file__).resolve().parent

    low_order = [("cut", "lin"), ("cut", "sat")]
    high_order = [
        ("lin", "cut"),
        ("lin", "lin"),
        ("lin", "sat"),
        ("sat", "cut"),
        ("sat", "lin"),
        ("sat", "sat"),
    ]

    common_head = """// PHAVerLite: CMOS inverter fragment (see lab4/_generate_cmos_inverter_pha.py).
// vgp'==0 tracks Vin-VDD; vdsg'==vout' when Vin'==0. vout': pull-up / pull-down / contention heuristic.
// patch_inverter_for_vin.py overwrites VIN_*, VGP_*_P, and initially for each run.

VDD:=1.8;
VTH0_N:=0.424;
VTH0_P:=-0.424;
VOUT_RAMP:=0.12;
VOH:=1.62;
VOL:=0.18;
"""

    low_vin = """VIN_LO:=0.044;
VIN_HI:=0.056;
VGP_LO_P:=-1.756;
VGP_HI_P:=-1.744;
VGP_CUTOFF_LO_P:=-0.424;
VGP_CUTOFF_HI_P:=-0.424;
"""
    low_tail = (
        "    initially: %s & vin == 0.05 & vout == 0.9 & vdsg == 0.85 & vgp == -1.75;\n"
        "  end\n\n"
        "cmos_inv.add_label(tau);\n"
        "pc_vin:=0.008;\n"
        "pc_vout:=0.45;\n"
        "pc_vdsg:=0.45;\n"
        "pc_vgp:=0.008;\n"
        "cmos_inv.set_refine_constraints((vin,pc_vin),(vout,pc_vout),(vdsg,pc_vdsg),(vgp,pc_vgp),tau);\n\n"
        "// --- Reachability (this file: Vin low band; joint n_cut+p_cut omitted globally) ---\n"
        % loc("cut", "lin", low_order)
    )
    for n, p in low_order:
        q = loc(n, p, low_order)
        low_tail += "reach_%s=cmos_inv.{%s & vout >= 0};\n" % (q, q)
        low_tail += "reach_%s_ok=cmos_inv.is_reachable(reach_%s);\n\n" % (q, q)
    low_tail += (
        "t_hi_m0=cmos_inv.{m0 & vout >= VOH};\n"
        "t_hi_m0_ok=cmos_inv.is_reachable(t_hi_m0);\n"
        "t_hi_m1=cmos_inv.{m1 & vout >= VOH};\n"
        "t_hi_m1_ok=cmos_inv.is_reachable(t_hi_m1);\n"
    )

    high_vin = """VIN_LO:=1.744;
VIN_HI:=1.756;
VGP_LO_P:=-0.056;
VGP_HI_P:=-0.044;
VGP_CUTOFF_LO_P:=-0.056;
VGP_CUTOFF_HI_P:=-0.044;
"""
    high_tail = (
        "    initially: %s & vin == 1.75 & vout == 0.2 & vdsg == -1.55 & vgp == -0.05;\n"
        "  end\n\n"
        "cmos_inv.add_label(tau);\n"
        "pc_vin:=0.008;\n"
        "pc_vout:=0.45;\n"
        "pc_vdsg:=0.45;\n"
        "pc_vgp:=0.008;\n"
        "cmos_inv.set_refine_constraints((vin,pc_vin),(vout,pc_vout),(vdsg,pc_vdsg),(vgp,pc_vgp),tau);\n\n"
        "// --- Reachability (this file: Vin high band) ---\n"
        % loc("lin", "cut", high_order)
    )
    for n, p in high_order:
        q = loc(n, p, high_order)
        high_tail += "reach_%s=cmos_inv.{%s & vout >= 0};\n" % (q, q)
        high_tail += "reach_%s_ok=cmos_inv.is_reachable(reach_%s);\n\n" % (q, q)
    for i in range(6):
        high_tail += (
            "t_lo_m%d=cmos_inv.{m%d & vout <= VOL};\n"
            "t_lo_m%d_ok=cmos_inv.is_reachable(t_lo_m%d);\n" % (i, i, i, i)
        )

    (root / "cmos_inverter_vin_low.pha").write_text(
        emit_one(low_order, common_head, low_vin, low_tail)
    )
    (root / "cmos_inverter_vin_high.pha").write_text(
        emit_one(high_order, common_head, high_vin, high_tail)
    )


if __name__ == "__main__":
    main()
