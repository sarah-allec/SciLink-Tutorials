"""
Part 1 — Build a structure and generate VASP or Quantum ESPRESSO inputs.

A single agent-driven pipeline that turns a natural-language description into:
  1. an ASE script that builds the atoms (validated + auto-refined if it errors),
  2. ready-to-run input files for your DFT engine of choice (VASP or QE).

No cluster is needed for this step — it produces the input files; you run the
calculation on HPC later. This is the "I'm done deciding what to compute, prepare
the calculation" shape.

Usage
-----
    export SCILINK_MODEL="claude-opus-4-6"   # set once (see ../README.md)
    python 01_dft.py                                 # default In:ZnO defect → VASP
    python 01_dft.py --engine qe                     # same structure → QE pw.in
    python 01_dft.py --system mof_yb_node            # pick a preset
    python 01_dft.py --request "5x5 MoS2 monolayer, 2H, with one S vacancy"
    python 01_dft.py --structure my.poscar --engine qe  # skip build, reuse a POSCAR
    python 01_dft.py --list                          # show presets and exit

The presets are seeded from the cohort's systems; swap in your own on Day 2.
Each run writes to a timestamped folder
``dft_output/<system-or-request>/<engine>/<timestamp>/`` so every run is preserved
(handy for model comparisons and variability tests). Override the whole path with
``--output-dir``.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime

# Cohort-tailored structure requests. Add your own here on Day 2.
# TODO (upstream PR): a monolayer-CrPS4 preset was dropped — SciLink's structure agent can't yet
# reliably extract a monoclinic 2D monolayer from bulk (it diverged and produced a non-stoichiometric,
# non-sandwiched layer). Revisit once the structure agent handles layered/monoclinic monolayers; until
# then, build such structures by hand and pass them via --structure.
PRESETS = {
    "zno_in":        "3x3x2 wurtzite ZnO supercell (36 Zn, 36 O), with 2 In atoms substituting Zn",
    "zno_in_ovac":   "3x3x2 wurtzite ZnO supercell (36 Zn, 36 O), with 2 In atoms substituting Zn "
                     "and a single oxygen vacancy adjacent to one In",
    "zno_n_sub":     "3x3x2 wurtzite ZnO supercell (36 Zn, 36 O), with a single N atom substituting O",
    "mof_yb_node":   "A 1x1x1 conventional cell of a Zr-oxo-cluster MOF node (UiO-66 secondary "
                     "building unit) with one Zr substituted by Yb",   # Yb-doped MOF node
}

ENGINES = ("vasp", "qe")

DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")

# Per-engine default for the input-generation request (only used if
# --input-request isn't passed). Both ask for a relaxation tuned to the
# system; the PeriodicDFTAgent's per-engine skill bundle fills in the details.
DEFAULT_INPUT_REQUEST = {
    "vasp": "Generate VASP relaxation inputs (POSCAR, INCAR, KPOINTS); choose "
            "parameters appropriate to the system.",
    "qe":   "Generate a Quantum ESPRESSO pw.x relaxation input; choose the "
            "calculation type and parameters appropriate to the system.",
}

# Engine-specific next-step hint printed at the end. Both engines produce a
# directory of inputs ready to be run on a cluster.
NEXT_STEP_HINT = {
    "vasp": "Next: copy this folder to HPC and submit a VASP relaxation.",
    "qe":   "Next: set pseudo_dir and the ATOMIC_SPECIES UPF files for your "
            "pseudopotential library, then run `pw.x -in pw.in`.",
}


def _slugify(text: str, maxlen: int = 40) -> str:
    """Filesystem-safe short folder name derived from a free-text request."""
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:maxlen].rstrip("_") or "request"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", choices=ENGINES, default="vasp",
                    help="Which DFT engine inputs to generate (default: vasp).")
    ap.add_argument("--system", choices=sorted(PRESETS), default="zno_in_ovac",
                    help="Named preset structure request (default: zno_in_ovac).")
    ap.add_argument("--request", default=None,
                    help="Free-text structure request (overrides --system; ignored if --structure is set).")
    ap.add_argument("--structure", default=None,
                    help="Existing structure file (POSCAR / CIF / xyz). When set, skip structure "
                         "generation and use this file directly.")
    ap.add_argument("--input-request", default=None,
                    help="Free-text description of the calculation to set up "
                         "(default: relaxation appropriate to the engine).")
    ap.add_argument("--output-dir", default=None,
                    help="Where to write outputs (default: dft_output/<system-or-request>/<engine>/<timestamp>/).")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="LiteLLM model id (default: $SCILINK_MODEL).")
    ap.add_argument("--max-cycles", type=int, default=3,
                    help="Max structure-refinement cycles (ignored when --structure is set).")
    ap.add_argument("--list", action="store_true", help="List presets and exit.")
    args = ap.parse_args()

    if args.list:
        print("Available presets:\n")
        for name, req in sorted(PRESETS.items()):
            print(f"  {name:14s} {req}")
        return 0

    # ── Output directory ─────────────────────────────────────────────────
    # Each run nests under the system/request dir, then the engine, in a
    # timestamped folder — repeated runs are all preserved, and VASP vs. QE
    # outputs from the same structure don't collide.
    if args.output_dir:
        out_dir = args.output_dir
    else:
        if args.structure:
            base = _slugify(os.path.splitext(os.path.basename(args.structure))[0])
        elif args.request:
            base = _slugify(args.request)
        else:
            base = args.system
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join("dft_output", base, args.engine, stamp)
    os.makedirs(out_dir, exist_ok=True)

    # Imported here so --list / --help don't require scilink to be installed.
    import scilink
    scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))

    print(f"Model        : {args.model}")
    print(f"Engine       : {args.engine.upper()}")
    print(f"Output dir   : {out_dir}")

    # ── Step 1: structure (skip if user supplied one) ────────────────────
    if args.structure:
        if not os.path.isfile(args.structure):
            sys.exit(f"Structure file not found: {args.structure}")
        structure_path = os.path.abspath(args.structure)
        print(f"Structure    : (provided) {structure_path}\n")
    else:
        struct_request = args.request or PRESETS[args.system]
        print(f"Request      : {struct_request}\n")
        print("🏗️  Step 1: structure generation\n")

        from scilink.agents.sim_agents.structure_orchestrator import StructureOrchestrator
        struct = StructureOrchestrator(
            generator_model=args.model,
            validator_model=args.model,
            output_dir=out_dir,
            max_refinement_cycles=args.max_cycles,
        )
        struct_result = struct.generate_and_validate(struct_request, structure_class="crystal")
        if struct_result.get("status") != "success":
            print(f"❌ Structure generation failed: {struct_result.get('message', 'Unknown error')}")
            return 1
        structure_path = struct_result["final_structure_path"]
        print(f"\n✅ Structure : {os.path.basename(structure_path)}")
        if struct_result.get("warning"):
            print(f"⚠️  {struct_result['warning']}")

    # ── Step 2: engine-specific inputs ───────────────────────────────────
    input_request = args.input_request or DEFAULT_INPUT_REQUEST[args.engine]
    print(f"\n⚛️  Step 2: {args.engine.upper()} input generation")
    print(f"  Request: {input_request}\n")

    from scilink.agents.sim_agents.periodic_dft_agent import PeriodicDFTAgent
    agent = PeriodicDFTAgent(model_name=args.model)
    result = agent.generate_inputs(
        structure_file=structure_path,
        request=input_request,
        software=args.engine,
    )
    if result.get("status") != "success":
        msg = result.get("message") or result.get("notes") or "(no message)"
        print(f"❌ {args.engine.upper()} input generation failed: {msg}")
        return 1

    agent.save_inputs(result, out_dir)
    files = ", ".join((result.get("input_files") or {}).keys())
    print(f"✅ {args.engine.upper()} inputs in '{out_dir}/': {files}")
    if result.get("notes"):
        print(f"\nNotes: {result['notes']}")
    print(f"\n{NEXT_STEP_HINT[args.engine]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
