"""
Quantum ESPRESSO companion to 01_dft_defect.py — generate pw.x inputs from a structure,
for fellows without VASP access.

Structure generation is engine-agnostic, so reuse a POSCAR built by 01_dft_defect.py
(or any POSCAR / CIF / xyz) and this produces a `pw.in` via SciLink's periodic-DFT agent
with the `qe` skill. The exchange-correlation functional comes from the pseudopotentials,
so set pseudo_dir / the ATOMIC_SPECIES UPF files for your library before running pw.x.

Uses SciLink's `qe` skill bundle (in upstream/main; ships with v0.0.31+ via PR #198).
On older releases you can point at the bundle out-of-tree:
    export SCILINK_SKILLS_PATH=/path/to/SciLink/scilink/skills

Usage
-----
    export SCILINK_MODEL="claude-opus-4-6"
    python qe_inputs.py --structure dft_output/zno_in_ovac/<timestamp>/POSCAR
    python qe_inputs.py --structure my.cif --request "vc-relax of a metal, PBE"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime

DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")
DEFAULT_REQUEST = ("Generate a Quantum ESPRESSO pw.x relaxation input; choose the "
                   "calculation type and parameters appropriate to the system.")


def _slug(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:maxlen].rstrip("_") or "structure"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--structure", required=True, help="Structure file (POSCAR / CIF / xyz / ...).")
    ap.add_argument("--request", default=DEFAULT_REQUEST, help="Free-text description of the calculation.")
    ap.add_argument("--output-dir", default=None,
                    help="Output dir (default: qe_output/<structure>/<timestamp>/).")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="LiteLLM model id (default: $SCILINK_MODEL).")
    args = ap.parse_args()

    if not os.path.isfile(args.structure):
        sys.exit(f"Structure file not found: {args.structure}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = args.output_dir or os.path.join(
        "qe_output", _slug(os.path.splitext(os.path.basename(args.structure))[0]), stamp)
    os.makedirs(out_dir, exist_ok=True)

    from scilink.agents.sim_agents.periodic_dft_agent import PeriodicDFTAgent
    import scilink
    scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))  # trace the LLM call

    print(f"Model       : {args.model}")
    print(f"Structure   : {args.structure}")
    print(f"Output dir  : {out_dir}")
    print(f"Request     : {args.request}\n")
    print("Generating Quantum ESPRESSO inputs ...\n")

    agent = PeriodicDFTAgent(model_name=args.model)
    result = agent.generate_inputs(structure_file=args.structure, request=args.request, software="qe")

    if result.get("status") != "success":
        print(f"⚠️  status: {result.get('status')} — {result.get('message') or result.get('notes')}")
        return 1

    agent.save_inputs(result, out_dir)
    files = ", ".join((result.get("input_files") or {}).keys())
    print(f"✅ QE inputs written to '{out_dir}/': {files}")
    if result.get("notes"):
        print(f"\nNotes: {result['notes']}")
    print("\nNext: set pseudo_dir and the ATOMIC_SPECIES UPF files for your pseudopotential "
          "library, then run `pw.x -in pw.in`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
