"""
Track B — Fit a 1-D curve and extract parameters with one agent call.

The SciLink *analysis* agent (curve-fitting mode) takes a 1-D spectrum/curve (CSV with
x,y columns) plus what you know about the sample, and:
  1. proposes a physically reasonable fitting model (peaks + background, via lmfit),
  2. fits it, auto-retrying / refining until the fit quality (R^2) passes a threshold,
  3. reports the parameters with uncertainties and flags model degeneracy.

This is the "I have a curve and need parameters out, but the model is non-obvious or
degenerate (or I have many curves to fit consistently)" shape.

Usage
-----
    export SCILINK_MODEL="claude-opus-4-6"        # set once (see ../README.md)
    python 01_curve_fit.py                         # fit the default demo curve (mos2_pl)
    python 01_curve_fit.py --dataset raman_silicon
    python 01_curve_fit.py --data my_curve.csv --info "SQUID M-T of a Co-doped ZnO film"
    python 01_curve_fit.py --list                  # show the demo curves

Group B domains: SQUID M-H / M-T magnetometry, SAXS/SANS profiles, UV-Vis / DLS, Monte-Carlo
output. The presets below are proven demo curves (PL, Raman) so the example runs out of the
box; on Day 2 swap in your own CSV (x,y columns) with --data and describe the sample with
--info. Each run writes to a timestamped folder curve_output/<dataset>/<timestamp>/, so every
run is preserved (override with --output-dir).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# dataset -> (curve CSV, metadata JSON). The metadata becomes the agent's `system_info`
# (sample, technique, instrument settings) — it materially helps the model pick a sensible
# fitting function. Add your own here on Day 2.
PRESETS = {
    "mos2_pl":       (os.path.join(DATA, "mos2_pl.csv"),       os.path.join(DATA, "mos2_pl_metadata.json")),
    "raman_silicon": (os.path.join(DATA, "raman_silicon.csv"), os.path.join(DATA, "raman_silicon_metadata.json")),
}

DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")


def _slugify(text: str, maxlen: int = 40) -> str:
    """Filesystem-safe short folder name derived from a free-text label."""
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:maxlen].rstrip("_") or "curve"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=sorted(PRESETS), default="mos2_pl",
                    help="Named demo curve (default: mos2_pl).")
    ap.add_argument("--data", default=None,
                    help="Path to your own curve CSV (x,y columns); overrides --dataset.")
    ap.add_argument("--info", default=None,
                    help="Free-text sample/technique description (system_info) to pair with --data.")
    ap.add_argument("--output-dir", default=None,
                    help="Where to write outputs (default: curve_output/<dataset>/<timestamp>/).")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="LiteLLM model id (default: $SCILINK_MODEL).")
    ap.add_argument("--list", action="store_true", help="List demo curves and exit.")
    args = ap.parse_args()

    if args.list:
        print("Demo curves (--dataset):")
        for name, (csv, _meta) in sorted(PRESETS.items()):
            print(f"  {name:16s} {csv}")
        print("\nOr fit your own:  --data my_curve.csv --info \"...sample description...\"")
        return 0

    # Resolve the curve + its system_info.
    if args.data:
        csv = args.data
        if not os.path.isfile(csv):
            print(f"No such file: {csv}", file=sys.stderr)
            return 2
        system_info = args.info or {}
        label = _slugify(os.path.splitext(os.path.basename(csv))[0])
    else:
        csv, meta = PRESETS[args.dataset]
        system_info = json.load(open(meta)) if os.path.isfile(meta) else {}
        label = args.dataset

    out_dir = args.output_dir or os.path.join(
        HERE, "curve_output", label, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    # The analysis (curve-fitting / image) agents look for ANTHROPIC_API_KEY specifically;
    # unlike the simulation agents they don't fall back to SCILINK_API_KEY. Bridge it so the
    # example works with whichever the workshop env has set (the key value is the same).
    if not os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SCILINK_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = os.environ["SCILINK_API_KEY"]

    # Opt-in JSONL trace of every LLM call (model, prompt, response, tokens, latency).
    import scilink
    if hasattr(scilink, "enable_tracing"):
        scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))
    from scilink.agents.exp_agents.curve_fitting_agent import CurveFittingAgent

    print(f"\n📈 Curve fitting: {label}")
    print(f"   data: {csv}")
    print(f"   out:  {out_dir}/\n")

    # enable_human_feedback=False: run start-to-finish without pausing for an interactive
    # "accept the plan?" prompt — so this works in a notebook / non-interactive shell and
    # keeps the model's generated plan (the prompt EOFs otherwise, discarding the plan).
    agent = CurveFittingAgent(model_name=args.model, output_dir=out_dir,
                              enable_human_feedback=False)
    result = agent.analyze(csv, system_info=system_info)

    print("\n=== RESULT ===")
    print(f"status      : {result.get('status')}")
    print(f"model       : {result.get('model_type')}")
    print(f"R^2         : {(result.get('fit_quality') or {}).get('r_squared')}")
    params = result.get("fitting_parameters")
    if params:
        import pprint
        print("parameters  :")
        pprint.pprint(params, indent=2, width=100)
    print(f"\nArtifacts (fit, plot, script, trace) in: {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
