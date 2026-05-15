Lab 4 project report: hybrid automaton models of MOSFETs and a CMOS inverter in PHAVerLite

HOW TO COPY INTO GOOGLE DOCS
Select from “REPORT BODY” through the end of the file, paste into a blank Doc. If formatting looks odd, use Paste without formatting (or Docs: Format → Clear formatting), then apply Heading 1 to numbered main sections and Heading 2 to subsection titles. Figures: use Insert → Image → Upload from computer and open the SVG files listed (or export PNG from a viewer), using the paths under each figure caption.

================================================================================
REPORT BODY
================================================================================

Course context: ECE hybrid / formal methods lab work (reachability on hybrid automata).

This report summarizes the lab 4 artifact chain: transistor hybrid automata in PHAVerLite, Python tooling for parameterized sweeps and plots, and forward reachability queries for Id-Vds families and CMOS inverter output bands. More detail on modes and scripts is in lab4/README.md and lab4/INVERTER_REACHABILITY.md.


1. Proposed project and connection to course topics

Project aim. We model NMOS and PMOS devices as hybrid automata: discrete locations correspond to coarse operating regions (cutoff, triode or linear, saturation). Continuous variables include gate-source and drain-source voltages and a bounded drain current proxy ids. Guards on quantities such as vdsg = vds - vgs (relative to a threshold parameter) trigger discrete jumps on a sync label tau, while flows hold vgs on a narrow DC strip per experiment and ramp vds at a constant rate so that reachable (vds, ids) sets approximate a stylized output characteristic; not a BSIM or SPICE deck.

We then compose the devices into a CMOS inverter model (generated from Python; file lab4/_generate_cmos_inverter_pha.py) with joint discrete modes (pairs of NMOS and PMOS regions). The lab asks reachability questions: which joint modes are reachable from a stated initial set, and can the output voltage enter strong high or strong low bands (compared to VOH and VOL)?

Connection to course topics:

• Hybrid systems: mixing continuous dynamics per location with discrete transitions.

• Reachability and safety-style analysis: PHAVerLite is_reachable targets encode whether the system can evolve into a set of interest.

• Abstraction: the automaton is a deliberate caricature of transistor physics to keep the formal model small; conclusions are about this model, with validation against SPICE left as a separate engineering step (see Section 4).


2. Tools

Formal hybrid model checker: PHAVerLite on .pha sources (nmos_model.pha, pmos_model.pha, cmos_inverter_vin_low.pha, cmos_inverter_vin_high.pha). Outputs include out_reachable and out_inv under per-run plot directories.

Batch sweeps (shell): run_vgs_id_vds_sweep.sh, run_vgs_id_vds_sweep_pmos.sh, run_with_log_and_plot.sh, run_with_log_and_plot_pmos.sh, run_inverter_reach.sh (under lab4/).

Parameter patching (Python): patch_nmos_for_vgs.py, patch_pmos_for_vgs.py, patch_inverter_for_vin.py (narrow strips, consistent initially blocks).

Visualization and narrative (Python): plot_nmos_id_vds_family.py, plot_pmos_id_vds_family.py, plot_lab4_dashboard.py, write_analysis_report.py (NMOS analysis text example: lab4/plots/nmos_2026-05-13_164116/ANALYSIS_REPORT.txt).


3. Data and results

3.1 NMOS and PMOS: Id versus Vds

Setup (nominal). Both devices use VDD = 1.8 V, absolute threshold scale about 0.424 V, illustrative vds ramp magnitude VDS_RAMP = 0.12 (V/s order in the model comments), and piecewise dids/dt constants IDS_PRIME_LIN and IDS_PRIME_SAT with caps IDS_LEAK_* and IDS_MAX_* (see nmos_model.pha and pmos_model.pha in lab4/).

Procedure. For each of six DC Vgs bins, the sweep patches the gate strip, runs PHAVerLite, and stores out_reachable rows and metadata under a timestamped folder (for example lab4/plots/nmos_2026-05-13_164116/ and lab4/plots/pmos_2026-05-13_171359/). Scripts overlay Id vs Vds families across bins.

Figure 1 — NMOS Id vs Vds (six Vgs bins, merged PHAVerLite graph output). Insert this image in your Doc:
  lab4/plots/nmos_2026-05-13_164116/phaver_graph_id_vds_all_vgs.svg
Full path (this machine):
  /home/ece558_658_2025/jkhare/UMass_ECE622_Labs/lab4/plots/nmos_2026-05-13_164116/phaver_graph_id_vds_all_vgs.svg

Figure 2 — PMOS Id vs Vds (six Vgs bins). Insert this image in your Doc:
  lab4/plots/pmos_2026-05-13_171359/phaver_graph_id_vds_all_vgs.svg
Full path (this machine):
  /home/ece558_658_2025/jkhare/UMass_ECE622_Labs/lab4/plots/pmos_2026-05-13_171359/phaver_graph_id_vds_all_vgs.svg

Longer automated narrative for the NMOS run (states, variables, bin table):
  lab4/plots/nmos_2026-05-13_164116/ANALYSIS_REPORT.txt


3.2 CMOS inverter: reachable joint modes and output bands

Setup (latest summarized run). Source file: lab4/logs/inverter_reach_summary_last.txt, generated 2026-05-13T18:08:54-04:00.

• VDD = 1.8 V; strip half-width EPS = 0.006 V
• Low Vin operating point VIN_low_op = 0.05 V; model file cmos_inverter_vin_low.pha
• High Vin operating point VIN_high_op = 1.75 V; model file cmos_inverter_vin_high.pha

Queries. Low Vin file: reach_m* asks whether joint mode m is reachable from the initial set; t_hi_m* asks whether vout is at least VOH is reachable from that mode. High Vin file: reach_m* same; t_lo_m* asks whether vout is at most VOL is reachable.

Observed results (that run).

Vin LOW strip (about 0.05 V):
• Reachable joint modes: reach_m0 yes; reach_m1 no.
• Strong output target: t_hi_m0 yes; t_hi_m1 no.

Vin HIGH strip (about 1.75 V):
• Reachable joint modes: reach_m0 yes; reach_m1 through reach_m5 no.
• Strong output target: t_lo_m0 yes; t_lo_m1 through t_lo_m5 no.

Interpretation in physical terms (principal joint mode under default seeds and vin' = 0 on the strip) is documented in lab4/INVERTER_REACHABILITY.md: low input can reach a strong high output band from the dominant reachable mode; high input can reach a strong low output band from the dominant reachable mode.

Full PHAVerLite transcripts for the cited run:
  lab4/logs/inverter_vin_low_2026-05-13_180854.log
  lab4/logs/inverter_vin_high_2026-05-13_180854.log

Symlinks lab4/logs/inverter_*_last.log and lab4/logs/inverter_reach_summary_last.txt point to the latest rerun after: bash lab4/run_inverter_reach.sh


4. Key risks and limitations

Model fidelity. Real transistors are not governed by a few piecewise-linear segments and constant ids' choices. The hybrid model is an engineering abstraction; reachable sets describe this automaton, not a foundry-certified device.

Input driving and large- versus small-signal interpretation. The default inverter reachability workflow fixes Vin on a narrow DC strip with no time-varying input trajectory in the documented scenario (vin' = 0 on that strip; see lab4/INVERTER_REACHABILITY.md). That choice does not by itself decide whether the experiment corresponds to a large-signal transfer sweep or a small-signal operating point around a bias. A practical knob for how hard the input is driven would be an explicit Vin ramp or piecewise waveform (steep slope suggesting faster or larger-signal transitions); any such extension should be checked against SPICE on corners to catch regimes where the hybrid caricature diverges.

Computation. Reachability cost grows with the number of discrete modes, the richness of continuous sets, and the time horizon implied by ramps and invariants. Tuning EPS, VDS_RAMP, current slopes, and PHAVerLite options is part of keeping runs tractable while preserving meaningful over-approximations.

Stating “legal ranges.” The tools support reasoning about reachable sets and target sets (for example VOH and VOL). Turning that into a certificate of all legal operating ranges for a shipped cell requires tighter alignment to measured or simulated behavior than this lab’s baseline caricature alone.


5. Future work

• Time-varying Vin: patch or generate models with finite slew families (slow vs fast ramps) and rerun reachability to relate dynamics to large-signal vs quasi-static interpretations.

• SPICE cross-check: automate comparison of Vout and Id-Vds traces for the same bias points and ramps; quantify error on worst-case corners.

• Reporting automation: mirror write_analysis_report.py for PMOS and inverter summaries so plot folders always ship a consistent text appendix.


Reproduction (commands)

From the repository root (if your shell is already in lab4/, drop the lab4/ prefix on the scripts):

bash lab4/run_with_log_and_plot.sh
bash lab4/run_with_log_and_plot_pmos.sh
bash lab4/run_inverter_reach.sh

First line: NMOS sweep, logs, plots. Second: PMOS sweep, logs, plots. Third: inverter is_reachable summary and logs.


References in this repository

lab4/README.md — NMOS model objective, parameter table, default pipeline

lab4/INVERTER_REACHABILITY.md — Joint modes, m* map, reachability query meanings

lab4/nmos_model.pha and lab4/pmos_model.pha — Hybrid automaton definitions

lab4/_generate_cmos_inverter_pha.py — Inverter .pha generation
