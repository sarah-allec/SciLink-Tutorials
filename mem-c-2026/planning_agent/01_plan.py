"""
Planning agent — knowledge-grounded TEA + experimental planning.

Calls `PlanningAgent` to  chain a
knowledge-grounded technoeconomic analysis with experimental-plan generation
in two focused LLM steps. 

Default demo: produced-water ICP-MS analyzed against the DOE Critical
Materials Assessment + PWS database, then a 96-well precipitation screen
proposal with Opentrons code (see ./README.md).

Usage
-----
    export SCILINK_MODEL="claude-opus-4-6"          # see ../README.md
    python 01_plan.py                                # TEA + plan
    python 01_plan.py --tea-only                     # TEA only (faster)
    python 01_plan.py --research-objective "..."     # custom plan-step goal
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import scilink
from scilink.agents.planning_agents.planning_agent import PlanningAgent

HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "data", "planning_produced_water"))
DEFAULT_DATA_DIR = os.path.join(_DATA_ROOT, "experimental_data")
DEFAULT_KNOWLEDGE_DIR = os.path.join(_DATA_ROOT, "knowledge_folder")
DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")
# Embedding model for the planning agent's RAG knowledge base. Default is
# Gemini (free key at https://aistudio.google.com/apikey). Override with
# --embedding-model to route through your existing provider — e.g.
# `bedrock/amazon.titan-embed-text-v2:0` (uses AWS_ACCESS_KEY_ID +
# AWS_SECRET_ACCESS_KEY) or `openai/text-embedding-3-small` (uses
# OPENAI_API_KEY).
DEFAULT_EMBEDDING_MODEL = os.environ.get("SCILINK_EMBEDDING_MODEL", "gemini-embedding-001")

# Two-step planning objectives
DEFAULT_TEA_OBJECTIVE = "Critical material recovery from produced water"

DEFAULT_RESEARCH_OBJECTIVE = (
    "Based on the ICP-MS results and the prior TEA identifying valuable materials, "
    "propose a simple chemical process (like precipitation) to selectively recover "
    "the most promising material from the water sample. Use only reagents that are "
    "simple commodity chemicals. Identify a range of conditions (concentrations, "
    "ratios, solubilities, or other variables) for testing optimal recovery. Put "
    "these conditions in a table for a 96-well plate (Opentrons). Provide corresponding "
    "Opentrons code."
)


def _trunc(s: str, n: int) -> str:
    """Truncate a long string for display."""
    return s if len(s) <= n else s[:n] + "..."


def _format_tea_context(tea: dict) -> str:
    """Compact JSON summary of TEA results, injected as `additional_context`."""
    return _trunc(json.dumps(tea, indent=2, default=str), 8000)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tea-objective", default=DEFAULT_TEA_OBJECTIVE,
                    help="One-line economic objective (default: critical-material recovery).")
    ap.add_argument("--research-objective", default=DEFAULT_RESEARCH_OBJECTIVE,
                    help="Free-text experimental-planning goal (default: 96-well precipitation screen with Opentrons code).")
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                    help="Folder of experimental measurements (default: bundled produced-water ICP-MS).")
    ap.add_argument("--knowledge-dir", default=DEFAULT_KNOWLEDGE_DIR,
                    help="Folder of reference knowledge — PDFs, spreadsheets, images (default: DOE/PWS bundle).")
    ap.add_argument("--output-dir", default=None,
                    help="Where to write campaign artifacts (default: plan_output/<timestamp>/).")
    ap.add_argument("--tea-only", action="store_true",
                    help="Run only the TEA step; skip experimental plan generation.")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="LiteLLM model id (default: $SCILINK_MODEL).")
    ap.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL,
                    help="Embedding model for the RAG knowledge base "
                         "(default: $SCILINK_EMBEDDING_MODEL or gemini-embedding-001). "
                         "For Bedrock: 'bedrock/amazon.titan-embed-text-v2:0'.")
    ap.add_argument("--embedding-api-key", default=None,
                    help="Explicit API key for the embedding provider; usually "
                         "discoverable from env (GEMINI_API_KEY, OPENAI_API_KEY, "
                         "or AWS_ACCESS_KEY_ID for Bedrock).")
    args = ap.parse_args()

    out_dir = args.output_dir or os.path.join(
        HERE, "plan_output", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)
    scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))

    # Resolve the primary ICP-MS dataset + the criticality-matrix image (if present).
    icpms = os.path.join(args.data_dir, "prowater_icpms.xlsx")
    icpms_meta = os.path.join(args.data_dir, "prowater_icpms.json")
    crit_img = os.path.join(args.knowledge_dir, "criticality_matrix.jpg")

    primary_dataset = {"file_path": icpms}
    if os.path.isfile(icpms_meta):
        primary_dataset["metadata_path"] = icpms_meta

    images, image_descs = [], []
    if os.path.isfile(crit_img):
        images.append(crit_img)
        image_descs.append("DOE criticality matrix — supply risk vs. importance for critical materials.")

    print(f"\n🧭 Planning campaign")
    print(f"   model        : {args.model}")
    print(f"   data dir     : {args.data_dir}")
    print(f"   knowledge dir: {args.knowledge_dir}")
    print(f"   out dir      : {out_dir}")
    print(f"   mode         : {'TEA only' if args.tea_only else 'TEA + experimental plan'}\n")

    agent = PlanningAgent(
        model_name=args.model,
        embedding_model=args.embedding_model,
        embedding_api_key=args.embedding_api_key,
        output_dir=out_dir,
    )

    # --- Step 1: TEA ---
    print(f"💰 Step 1: technoeconomic analysis — {args.tea_objective!r}\n")
    tea = agent.perform_technoeconomic_analysis(
        objective=args.tea_objective,
        knowledge_paths=[args.knowledge_dir],
        primary_data_set=primary_dataset,
        image_paths=images or None,
        image_descriptions=image_descs or None,
        output_json_path=os.path.join(out_dir, "tea_analysis.json"),
    )
    print(f"  ✅ TEA done — tea_analysis.json (+ .html report)\n")

    plan = None
    if not args.tea_only:
        # --- Step 2: experimental plan, conditioned on TEA results ---
        print(f"🧪 Step 2: experimental plan (using TEA findings as additional context)\n")
        plan = agent.propose_experiments(
            objective=args.research_objective,
            knowledge_paths=[args.knowledge_dir],
            primary_data_set=primary_dataset,
            additional_context={"Prior TEA findings": _format_tea_context(tea)},
            enable_human_feedback=False,
            output_json_path=os.path.join(out_dir, "plan.json"),
        )
        print(f"  ✅ plan done — plan.json\n")

    # --- Report ---
    print("=== RESULT ===")
    if isinstance(tea, dict):
        print(f"TEA      : status={tea.get('status', 'n/a')}")
        for key in ("executive_summary", "summary", "key_findings"):
            v = tea.get(key)
            if v:
                print(f"  {key}: {_trunc(str(v), 400)}")
                break
    if plan is not None and isinstance(plan, dict):
        n_exp = len(plan.get("proposed_experiments") or [])
        print(f"Plan     : {n_exp} proposed experiment(s)")
        for i, exp in enumerate((plan.get("proposed_experiments") or [])[:3], 1):
            if isinstance(exp, dict):
                h = exp.get("hypothesis") or exp.get("title") or str(exp)[:200]
                print(f"  [{i}] {_trunc(str(h), 200)}")
    print(f"\nArtifacts (TEA JSON + HTML, plan JSON, traces) in: {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
