"""
Sketch of the NMOS (vgs, vds) voltage partition used in nmos_model.pha.
Educational only; PHAVerLite does not use this script.
"""

from __future__ import annotations

import matplotlib.pyplot as plt


def main() -> None:
    # Keep in sync with header literals in nmos_model.pha
    vdd = 1.8
    vth = 0.424

    fig, ax = plt.subplots(figsize=(6.5, 5.0))

    # Cutoff strip: 0 <= vgs <= Vth, 0 <= vds <= VDD
    ax.fill([0, vth, vth, 0], [0, 0, vdd, vdd], alpha=0.22, label="cutoff (vgs <= Vth)")

    # Triode: Vth <= vgs <= VDD, 0 <= vds <= vgs - Vth  => triangle under knee
    ax.fill(
        [vth, vdd, vdd],
        [0.0, 0.0, vdd - vth],
        alpha=0.22,
        label="linear_region (vds <= vgs - Vth)",
    )

    # Saturation: Vth <= vgs <= VDD, vgs - Vth <= vds <= VDD
    ax.fill(
        [vth, vdd, vdd, vth],
        [0.0, vdd - vth, vdd, vdd],
        alpha=0.22,
        label="saturation_region (vds >= vgs - Vth)",
    )

    ax.plot([vth, vdd], [0.0, vdd - vth], "k--", linewidth=1.0, label="knee: vds = vgs - Vth")

    ax.set_xlim(0, vdd)
    ax.set_ylim(0, vdd)
    ax.set_xlabel("vgs (V)")
    ax.set_ylabel("vds (V)")
    ax.set_title("NMOS voltage regions (GPDK045-style VDD/Vth literals)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.2)
    ax.set_aspect("equal", adjustable="box")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
