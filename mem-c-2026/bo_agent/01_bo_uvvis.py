"""
Track C — Bayesian optimization of synthesis conditions toward a target spectrum.

Reads a grid of UV-Vis spectra collected at known (temperature, pH) conditions,
scalarizes each spectrum into a peak-absorbance value, fits a Gaussian-process
surrogate via SciLink's BOAgent, and recommends the next batch of conditions to
try. The agent picks the kernel / acquisition / noise strategy and writes
`bo_artifacts/batch_step_N.csv` with the recommended next experiments.

This mirrors the mrs-2026 BO demo programmatically (no UI). The mrs `bo_agent/`
folder provides a 3x3 (T, pH) starter grid of synthetic spectra; close the loop
by generating new spectra for the recommended conditions with that folder's
`simulate_spectra.py` and re-running this script — the agent picks up where it
left off via the persisted history file.

Usage
-----
    export SCILINK_MODEL="claude-opus-4-6"        # set once (see ../README.md)
    python 01_bo_uvvis.py                          # default: mrs starter grid
    python 01_bo_uvvis.py --batch-size 3 --budget 5
    python 01_bo_uvvis.py --spectra ./my_runs --conditions ./my_runs/conditions.json

Group C domains: doped-oxide / MOF synthesis, intercalant screening, cluster
optimization — same engine, different (inputs, target). Bring on Day 2 a CSV
of your own experiments and the parameter ranges you can actually access.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
# Default to the mrs UV-Vis starter grid (3x3 over T, pH) — same data, programmatic flow.
DEFAULT_SPECTRA = os.path.normpath(os.path.join(HERE, "..", "..", "mrs-2026", "bo_agent", "spectra"))
DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")

# Synthesis-parameter bounds (mirrors mrs simulate_spectra.py). Edit on Day 2 to match
# the conditions you can actually run.
INPUT_BOUNDS = {"temperature_C": (5.0, 100.0), "pH": (1.0, 14.0)}


def scalarize_spectra(spectra_dir: str, conditions_path: str) -> pd.DataFrame:
    """Build a tidy (inputs, target) table from a directory of per-condition spectra.

    Each row of `conditions.json` maps a spectrum CSV (wavelength, absorbance) to its
    (temperature_C, pH); we collapse each spectrum to its peak absorbance — the same
    scalarizer the mrs UI flow uses by default. Swap in your own scalarizer (area under
    a band, fitted peak height, color coordinate, ...) on Day 2 if your target needs it.
    """
    with open(conditions_path) as f:
        conditions = json.load(f)
    rows = []
    for csv_name, params in conditions.items():
        csv_path = os.path.join(spectra_dir, csv_name)
        if not os.path.isfile(csv_path):
            print(f"  ⚠️  skipping (missing): {csv_name}", file=sys.stderr)
            continue
        df = pd.read_csv(csv_path)
        # columns: wavelength_nm, absorbance
        peak_absorbance = float(df["absorbance"].max())
        rows.append({**params, "peak_absorbance": peak_absorbance})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spectra", default=DEFAULT_SPECTRA,
                    help="Directory of per-condition spectrum CSVs (default: mrs starter grid).")
    ap.add_argument("--conditions", default=None,
                    help="Path to conditions.json (default: <spectra>/conditions.json).")
    ap.add_argument("--output-dir", default=None,
                    help="Where to write the tidy data + BO artifacts (default: bo_output/<timestamp>/).")
    ap.add_argument("--batch-size", type=int, default=2,
                    help="How many new experiments to recommend this round (default: 2).")
    ap.add_argument("--budget", type=int, default=None,
                    help="Optional remaining-iteration budget (sharpens exploit vs explore).")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="LiteLLM model id (default: $SCILINK_MODEL).")
    args = ap.parse_args()

    spectra_dir = args.spectra
    conditions_path = args.conditions or os.path.join(spectra_dir, "conditions.json")
    if not os.path.isdir(spectra_dir) or not os.path.isfile(conditions_path):
        print(f"Could not find spectra dir / conditions file: {spectra_dir} / {conditions_path}",
              file=sys.stderr)
        return 2

    out_dir = args.output_dir or os.path.join(
        HERE, "bo_output", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    # 1. Scalarize the spectra into a tidy table (rows = experiments, cols = inputs + target).
    print(f"\n🧪 Reading spectra from: {spectra_dir}")
    table = scalarize_spectra(spectra_dir, conditions_path)
    if table.empty:
        print("No spectra found to scalarize.", file=sys.stderr)
        return 2
    print(f"   {len(table)} experiments scalarized; peak_absorbance range = "
          f"{table['peak_absorbance'].min():.3f}..{table['peak_absorbance'].max():.3f}")
    data_csv = os.path.join(out_dir, "experiments.csv")
    table.to_csv(data_csv, index=False)
    print(f"   tidy table: {data_csv}")

    # 2. Opt-in JSONL trace of every LLM call (model, prompt, response, tokens, latency).
    import scilink
    scilink.enable_tracing(os.path.join(out_dir, "llm_trace.jsonl"))
    from scilink.agents.planning_agents.bo_agent import BOAgent

    # 3. Hand the table to BOAgent and ask for the next batch of conditions.
    inputs = list(INPUT_BOUNDS)                       # ['temperature_C', 'pH']
    bounds = [list(INPUT_BOUNDS[k]) for k in inputs]  # [[5,100], [1,14]]
    objective = ("Maximize UV-Vis absorption peak intensity by tuning the "
                 "synthesis temperature and pH.")
    print(f"\n🤖 Running BO loop (batch_size={args.batch_size}"
          + (f", budget={args.budget}" if args.budget else "") + ")")
    agent = BOAgent(model_name=args.model, output_dir=out_dir)
    result = agent.run_optimization_loop(
        data_path=data_csv,
        objective_text=objective,
        input_cols=inputs,
        input_bounds=bounds,
        target_cols=["peak_absorbance"],
        batch_size=args.batch_size,
        experimental_budget=args.budget,
        output_dir=out_dir,
    )

    print("\n=== RESULT ===")
    print(f"status          : {result.get('status')}")
    strat = result.get("strategy") or {}
    mc = strat.get("model_config") or {}
    print(f"surrogate       : {mc.get('surrogate')}")
    print(f"kernel          : {mc.get('kernel')}")
    print(f"noise           : {mc.get('noise')}")
    print(f"acquisition     : {strat.get('acquisition_strategy')}")
    rationale = strat.get("rationale") or ""
    if rationale:
        print(f"rationale       : {rationale[:300]}{'...' if len(rationale) > 300 else ''}")
    # next_parameters is a dict for batch_size=1, a list of dicts otherwise.
    recs = result.get("next_parameters") or []
    if isinstance(recs, dict):
        recs = [recs]
    print(f"recommendations : {len(recs)} next experiment(s) to run")
    for i, r in enumerate(recs, 1):
        pretty = ", ".join(f"{k}={v:.2f}" if isinstance(v, (int, float)) else f"{k}={v}"
                           for k, v in r.items())
        print(f"   [{i}] {pretty}")
    print(f"\nArtifacts (acquisition plot, history, batch CSV, trace) in: {out_dir}/")
    print("\nNext step: generate spectra for these recommendations and re-run, e.g.")
    if recs:
        params_json = json.dumps(recs[0])
        print(f"  python ../../mrs-2026/bo_agent/simulate_spectra.py run \\")
        print(f"      --output_dir {spectra_dir} --params '{params_json}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
