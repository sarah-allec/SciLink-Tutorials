"""
Part 1 — Build a defect supercell and generate VASP inputs with one agent call.

The SciLink *simulation* agent turns a natural-language description of a structure into:
  1. an ASE script that builds the atoms (validated + auto-refined if it errors),
  2. ready-to-run VASP inputs (POSCAR / INCAR / KPOINTS).

No cluster is needed for this step — it produces the input files; you run VASP later
on HPC. This is the "I'm done deciding what to compute, prepare the calculation" shape.

Usage
-----
    export SCILINK_MODEL="bedrock/<model-id>"      # set once (see ../README.md)
    python 01_dft_defect.py                        # build the default In:ZnO defect
    python 01_dft_defect.py --system zno_in_ovac   # pick a preset
    python 01_dft_defect.py --request "5x5 MoS2 monolayer, 2H, with one S vacancy"
    python 01_dft_defect.py --list                 # show all presets

The presets are seeded from the cohort's systems; swap in your own on Day 2.
"""

from __future__ import annotations

import argparse
import os
import sys

# Cohort-tailored structure requests. Add your own here on Day 2.
PRESETS = {
    "zno_in":        "3x3x2 wurtzite ZnO supercell (36 Zn, 36 O), with 2 In atoms substituting Zn",
    "zno_in_ovac":   "3x3x2 wurtzite ZnO supercell (36 Zn, 36 O), with 2 In atoms substituting Zn "
                     "and a single oxygen vacancy adjacent to one In",
    "zno_n_sub":     "3x3x2 wurtzite ZnO supercell (36 Zn, 36 O), with a single N atom substituting O",
    "mof_yb_node":   "A 1x1x1 conventional cell of a Zr-oxo-cluster MOF node (UiO-66 secondary "
                     "building unit) with one Zr substituted by Yb",   # Kubra / Zhang
    "crps4_vac":     "4x4x1 monolayer CrPS4 supercell with a single sulfur vacancy",  # Nguyen
}

DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "bedrock/anthropic.claude-3-5-sonnet")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", choices=sorted(PRESETS), default="zno_in_ovac",
                    help="Named preset structure request (default: zno_in_ovac).")
    ap.add_argument("--request", default=None,
                    help="Free-text structure request (overrides --system).")
    ap.add_argument("--output-dir", default="dft_output", help="Where to write the VASP inputs.")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="LiteLLM model id (default: $SCILINK_MODEL).")
    ap.add_argument("--max-cycles", type=int, default=3, help="Max structure-refinement attempts.")
    ap.add_argument("--list", action="store_true", help="List presets and exit.")
    args = ap.parse_args()

    if args.list:
        print("Available presets:\n")
        for name, req in sorted(PRESETS.items()):
            print(f"  {name:14s} {req}")
        return 0

    request = args.request or PRESETS[args.system]

    # Imported here so --list / --help work without scilink installed.
    from scilink.agents.sim_agents.dft_orchestrator import DFTOrchestrator

    print(f"Model        : {args.model}")
    print(f"Output dir   : {args.output_dir}")
    print(f"Request      : {request}\n")
    print("Starting DFT structure + input generation ...\n")

    orch = DFTOrchestrator(
        generator_model=args.model,
        validator_model=args.model,
        output_dir=args.output_dir,
        max_refinement_cycles=args.max_cycles,
    )
    result = orch.run_complete_workflow(request)

    print("\n--- Workflow summary ---")
    print(orch.get_summary(result))

    manifest = result.get("final_manifest", {})
    if manifest.get("ready_for_vasp"):
        files = manifest.get("final_files", {})
        print(f"\n✅ VASP inputs ready in '{args.output_dir}/':")
        for kind, path in files.items():
            print(f"   {kind:10s} {path}")
        print("\nNext: copy this folder to HPC and submit a VASP relaxation.")
    else:
        print(f"\n⚠️  Final status: {result.get('final_status')}. "
              "See the logs in the output directory; try increasing --max-cycles "
              "or simplifying the request.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
