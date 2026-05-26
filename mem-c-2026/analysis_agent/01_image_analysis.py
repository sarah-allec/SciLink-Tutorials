"""
Track A — Analyze a microscopy image with one agent call.

The SciLink *analysis* agent (image mode) takes an image (.npy / .png / .tif) plus
what you know about the sample, and:
  1. plans an analysis approach (denoising / FFT / segmentation / feature extraction),
  2. runs that pipeline and extracts features (atoms, grains, domains, defects, ...),
  3. reports scientific claims grounded in the extracted features.

This is the "I have an image and want a structured readout — atoms, grains, defects,
phases — without writing a custom segmentation pipeline" shape.

Usage
-----
    export SCILINK_MODEL="claude-opus-4-6"        # set once (see ../README.md)
    python 01_image_analysis.py                          # default: mos2_stem
    python 01_image_analysis.py --dataset polycrystalline
    python 01_image_analysis.py --data my.npy --info "..."  # your own image
    python 01_image_analysis.py --list                   # show the demo images

Group A domains: SEM defects, STEM atomic columns, AFM moiré domains, optical
microstructure. The presets below are proven demo images from SciLink's own examples
so the agent has good coverage; on Day 2 swap in your own image (.npy/.png/.tif) with
--data and describe the sample with --info.
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

# dataset -> (image, metadata json, optional objective).
#   mos2_stem        — 1% V-doped MoS2 monolayer, HAADF-STEM, 9 x 9 nm field of view.
#                       Atomic-resolution image: agent should identify atoms / dopants /
#                       defects (sulfur vacancies, antisites).
#   polycrystalline — 304 stainless steel, optical bright-field, 100 x 100 um. No
#                       specific goal needed — the agent picks the analysis (grain
#                       segmentation + size statistics).
PRESETS = {
    "mos2_stem":       (os.path.join(DATA, "mos2_stem.npy"),       os.path.join(DATA, "mos2_stem.json"),       None),
    "polycrystalline": (os.path.join(DATA, "polycrystalline.npy"), os.path.join(DATA, "polycrystalline.json"), None),
}

DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")


def _slugify(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:maxlen].rstrip("_") or "image"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=sorted(PRESETS), default="mos2_stem",
                    help="Named demo image (default: mos2_stem).")
    ap.add_argument("--data", default=None,
                    help="Path to your own image (.npy/.png/.tif); overrides --dataset.")
    ap.add_argument("--info", default=None,
                    help="Free-text sample/technique description (system_info) to pair with --data.")
    ap.add_argument("--objective", default=None,
                    help="Optional high-level scientific question (e.g., 'find sulfur vacancies').")
    ap.add_argument("--output-dir", default=None,
                    help="Where to write outputs (default: image_output/<dataset>/<timestamp>/).")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="LiteLLM model id (default: $SCILINK_MODEL).")
    ap.add_argument("--list", action="store_true", help="List demo images and exit.")
    args = ap.parse_args()

    if args.list:
        print("Demo images (--dataset):")
        for name, (img, _meta, _obj) in sorted(PRESETS.items()):
            print(f"  {name:18s} {img}")
        print("\nOr analyze your own:  --data my_image.npy --info \"...sample description...\"")
        return 0

    # Resolve the image + its system_info + any preset objective.
    preset_objective = None
    if args.data:
        img = args.data
        if not os.path.isfile(img):
            print(f"No such file: {img}", file=sys.stderr)
            return 2
        system_info = args.info or {}
        label = _slugify(os.path.splitext(os.path.basename(img))[0])
    else:
        img, meta, preset_objective = PRESETS[args.dataset]
        system_info = json.load(open(meta)) if os.path.isfile(meta) else {}
        label = args.dataset

    out_dir = args.output_dir or os.path.join(
        HERE, "image_output", label, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    # The experiment agents (image / curve / hyperspectral) look for ANTHROPIC_API_KEY
    # specifically; unlike the simulation agents they don't fall back to SCILINK_API_KEY.
    # Bridge it so the example works with whichever the workshop env has set.
    if not os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SCILINK_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = os.environ["SCILINK_API_KEY"]

    # Opt-in JSONL trace of every LLM call (model, prompt, response, tokens, latency).
    import scilink
    if hasattr(scilink, "enable_tracing"):
        scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))
    from scilink.agents.exp_agents.image_analysis_agent import ImageAnalysisAgent

    print(f"\n🔬 Image analysis: {label}")
    print(f"   image: {img}")
    print(f"   out:   {out_dir}/\n")

    # enable_human_feedback=False: run start-to-finish without pausing for an interactive
    # "accept the plan?" prompt — so this works in a notebook / non-interactive shell
    # and keeps the model's generated plan.
    agent = ImageAnalysisAgent(model_name=args.model, output_dir=out_dir,
                               enable_human_feedback=False)
    result = agent.analyze(img, system_info=system_info,
                           objective=args.objective or preset_objective)

    print("\n=== RESULT ===")
    print(f"status     : {result.get('status')}")
    approach = result.get("analysis_approach") or ""
    if approach:
        print(f"approach   : {approach[:240]}{'...' if len(approach) > 240 else ''}")
    feats = result.get("extracted_features") or {}
    if isinstance(feats, dict) and feats:
        print(f"features   : {len(feats)} extracted "
              f"({', '.join(list(feats.keys())[:6])}"
              f"{'...' if len(feats) > 6 else ''})")
    claims = result.get("scientific_claims") or []
    print(f"claims     : {len(claims)}")
    for i, c in enumerate(claims[:3], 1):
        # Each claim is typically {"claim": "...", "evidence": "...", ...}
        if isinstance(c, dict):
            print(f"   [{i}] {c.get('claim') or c.get('description') or str(c)[:200]}")
        else:
            print(f"   [{i}] {str(c)[:200]}")
    detail = result.get("detailed_analysis") or ""
    if detail:
        print(f"\nanalysis (first ~600 chars):\n{detail[:600]}{'...' if len(detail) > 600 else ''}")
    print(f"\nArtifacts (figures, masks, scripts, trace) in: {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
