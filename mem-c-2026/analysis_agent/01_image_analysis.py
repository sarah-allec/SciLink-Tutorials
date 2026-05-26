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
    python 01_image_analysis.py                          # the bundled polycrystalline demo
    python 01_image_analysis.py --data my.npy --info "..."  # your own image
    python 01_image_analysis.py --list                   # list the demo presets
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

import scilink
from scilink.agents.exp_agents.image_analysis_agent import ImageAnalysisAgent

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data", "images"))

# Demo images. Each entry maps a short name to (image file, metadata JSON). The JSON
# sidecar describes the sample (material, technique, field-of-view, ...) and is passed
# to the agent as `system_info` — it materially helps the agent plan + interpret.
#   polycrystalline — 304 stainless steel, optical bright-field, 100x100 µm. A general-
#                     purpose microstructure example: no specific goal needed, the agent
#                     picks the analysis (grain segmentation + size statistics).
PRESETS = {
    "polycrystalline": (os.path.join(DATA, "polycrystalline.npy"), os.path.join(DATA, "polycrystalline.json")),
}

DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")


def _slugify(text: str, maxlen: int = 40) -> str:
    """Filesystem-safe short folder name derived from a free-text label."""
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:maxlen].rstrip("_") or "image"


def _trunc(s: str, n: int) -> str:
    """Truncate a long string for display."""
    return s if len(s) <= n else s[:n] + "..."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=sorted(PRESETS), default="polycrystalline",
                    help="Named demo image (default: polycrystalline).")
    ap.add_argument("--data", default=None,
                    help="Path to your own image (.npy/.png/.tif); overrides --dataset.")
    ap.add_argument("--info", default=None,
                    help="Free-text sample/technique description (system_info) to pair with --data.")
    ap.add_argument("--objective", default=None,
                    help="Optional high-level scientific question (e.g. 'find sulfur vacancies'). "
                         "Leave unset to let the agent pick the analysis goal from the data + system_info.")
    ap.add_argument("--output-dir", default=None,
                    help="Where to write outputs (default: image_output/<dataset>/<timestamp>/).")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="LiteLLM model id (default: $SCILINK_MODEL).")
    ap.add_argument("--list", action="store_true", help="List demo images and exit.")
    args = ap.parse_args()

    if args.list:
        print("Demo images (--dataset):")
        for name, (img, _) in sorted(PRESETS.items()):
            print(f"  {name:18s} {img}")
        print("\nOr analyze your own:  --data my_image.npy --info \"...sample description...\"")
        return 0

    # Resolve the image + its system_info. --data wins over --dataset; for a preset, the
    # metadata comes from the JSON sidecar that ships with the demo.
    if args.data:
        img = args.data
        if not os.path.isfile(img):
            print(f"No such file: {img}", file=sys.stderr)
            return 2
        system_info = args.info or {}
        label = _slugify(os.path.splitext(os.path.basename(img))[0])
    else:
        img, meta = PRESETS[args.dataset]
        system_info = json.load(open(meta)) if os.path.isfile(meta) else {}
        label = args.dataset

    # Each run lands in its own timestamped folder so re-runs (different prompts, models,
    # objectives) don't overwrite each other. Override the whole path with --output-dir.
    out_dir = args.output_dir or os.path.join(
        HERE, "image_output", label, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    # Opt-in JSONL trace of every LLM call (model, prompt, response, tokens, latency).
    # Lands in the run folder — useful for inspecting *what the agent actually asked the
    # model* after the fact (and what it cost in tokens / time).
    scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))

    print(f"\n🔬 Image analysis: {label}")
    print(f"   image: {img}")
    print(f"   out:   {out_dir}/\n")

    # enable_human_feedback=False: run start-to-finish, no interactive "accept the plan?"
    # prompt — so this works in a notebook or any non-interactive shell.
    agent = ImageAnalysisAgent(model_name=args.model, output_dir=out_dir,
                               enable_human_feedback=False)
    result = agent.analyze(img, system_info=system_info, objective=args.objective)

    print("\n=== RESULT ===")
    print(f"status     : {result.get('status')}")
    if approach := result.get("analysis_approach"):
        print(f"approach   : {_trunc(approach, 240)}")
    feats = result.get("extracted_features") or {}
    if isinstance(feats, dict) and feats:
        keys = ", ".join(list(feats.keys())[:6]) + ("..." if len(feats) > 6 else "")
        print(f"features   : {len(feats)} extracted ({keys})")
    claims = result.get("scientific_claims") or []
    print(f"claims     : {len(claims)}")
    for i, c in enumerate(claims[:3], 1):
        text = (c.get("claim") or c.get("description") or str(c)) if isinstance(c, dict) else str(c)
        print(f"   [{i}] {_trunc(text, 200)}")
    if detail := result.get("detailed_analysis"):
        print(f"\nanalysis (first ~600 chars):\n{_trunc(detail, 600)}")
    print(f"\nArtifacts (figures, masks, scripts, trace) in: {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
