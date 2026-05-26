"""
Planning agent — knowledge-grounded experiment planning, programmatic mode.

`PlanningOrchestratorAgent.run_task()` runs end-to-end (no user prompts) and
returns a structured summary dict — good for scripted / notebook use. Same
agent the `scilink plan` CLI invokes; this is the headless entry point.

Default demo: a technoeconomic analysis of produced-water ICP-MS data against
the DOE Critical Materials Assessment + PWS database (see ./README.md).

Usage
-----
    export SCILINK_MODEL="claude-opus-4-6"          # see ../README.md
    python 01_plan.py                                # default task
    python 01_plan.py --task "..."                  # your own objective
    python 01_plan.py --autonomy autopilot          # pause for human at decisions
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import scilink
from scilink.agents.planning_agents.planning_orchestrator import (
    PlanningOrchestratorAgent,
    AutonomyLevel,
)

HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "data", "planning_produced_water"))
DEFAULT_DATA_DIR = os.path.join(_DATA_ROOT, "experimental_data")
DEFAULT_KNOWLEDGE_DIR = os.path.join(_DATA_ROOT, "knowledge_folder")
DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")

# Default technoeconomic objective — analyzes the ICP-MS measurements against
# the bundled DOE / PWS reference materials to surface candidates for recovery.
DEFAULT_TASK = (
    "Using the DOE assessment report, the PWS database, and the provided "
    "criticality-matrix image as context, analyze the ICP-MS results to determine "
    "which measured critical materials show concentrations that might be "
    "economically interesting for recovery, considering their market value."
)

DEFAULT_OBJECTIVE = "Critical material recovery from produced water"

# string → AutonomyLevel for the --autonomy flag.
AUTONOMY = {
    "co_pilot":   AutonomyLevel.CO_PILOT,
    "autopilot":  AutonomyLevel.AUTOPILOT,
    "autonomous": AutonomyLevel.AUTONOMOUS,
}


def _trunc(s: str, n: int) -> str:
    """Truncate a long string for display."""
    return s if len(s) <= n else s[:n] + "..."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", default=DEFAULT_TASK,
                    help="Free-text objective the agent should pursue (default: technoeconomic ICP-MS analysis).")
    ap.add_argument("--objective", default=DEFAULT_OBJECTIVE,
                    help="High-level campaign label for this run (shown in the orchestrator's logs / state).")
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                    help="Folder of experimental measurements (default: ./experimental_data/).")
    ap.add_argument("--knowledge-dir", default=DEFAULT_KNOWLEDGE_DIR,
                    help="Folder of reference knowledge — PDFs, spreadsheets, images (default: ./knowledge_folder/).")
    ap.add_argument("--output-dir", default=None,
                    help="Where to write campaign artifacts (default: plan_output/<timestamp>/).")
    ap.add_argument("--autonomy", default="autonomous", choices=sorted(AUTONOMY),
                    help="Autonomy level (default: autonomous — runs end-to-end with no human prompts).")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="LiteLLM model id (default: $SCILINK_MODEL).")
    args = ap.parse_args()

    out_dir = args.output_dir or os.path.join(
        HERE, "plan_output", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)
    scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))

    print(f"\n🧭 Planning campaign: {args.objective}")
    print(f"   model        : {args.model}")
    print(f"   data dir     : {args.data_dir}")
    print(f"   knowledge dir: {args.knowledge_dir}")
    print(f"   out dir      : {out_dir}")
    print(f"   autonomy     : {args.autonomy}\n")

    orch = PlanningOrchestratorAgent(
        objective=args.objective,
        base_dir=out_dir,
        model_name=args.model,
        autonomy_level=AUTONOMY[args.autonomy],
        data_dir=args.data_dir,
        knowledge_dir=args.knowledge_dir,
    )

    result = orch.run_task(args.task)

    # `result` keys we surface below:
    #   status              'success' | 'error'
    #   summary             the agent's final reply (the report)
    #   files_produced      absolute paths of campaign artifacts created
    #   key_findings        campaign-state highlights (objective, targets, ...)
    #   suggested_followups list of next-step suggestions
    #   warnings            any non-fatal issues encountered
    print("\n=== RESULT ===")
    print(f"status     : {result.get('status')}")
    files = result.get("files_produced") or []
    print(f"files      : {len(files)} produced")
    for f in files[:6]:
        print(f"   - {f}")
    if len(files) > 6:
        print(f"   ... ({len(files) - 6} more)")
    findings = result.get("key_findings") or []
    if findings:
        print(f"findings   : {len(findings)}")
        for i, f in enumerate(findings[:3], 1):
            print(f"   [{i}] {_trunc(str(f), 200)}")
    followups = result.get("suggested_followups") or []
    if followups:
        print(f"\nsuggested follow-ups:")
        for fu in followups[:3]:
            print(f"   - {_trunc(str(fu), 200)}")
    warnings = result.get("warnings") or []
    if warnings:
        print(f"\nwarnings:")
        for w in warnings[:3]:
            print(f"   ⚠️  {_trunc(str(w), 200)}")
    summary = result.get("summary") or ""
    if summary:
        print(f"\nsummary (first ~600 chars):\n{_trunc(summary, 600)}")
    print(f"\nArtifacts (sessions, scripts, traces) in: {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
