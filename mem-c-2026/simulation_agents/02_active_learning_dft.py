"""
Part 2 — Active-learning DFT screening: pick the next calculation, not all of them.

SciLink has a Bayesian-optimization engine (used by the `plan` agent for experiments)
and a `simulate` agent that generates DFT calculations. Neither, on its own, is an
"active-learning over DFT" loop — but you can wire them together, and that is exactly
the workflow several of you described (active-learning-guided DFT; managing many
DFT runs):

    seed DFT data ─▶ fit GP surrogate ─▶ propose next config(s)   [BO selector]
         ▲                                          │
         └──────── append result ◀── run DFT ◀──────┘            [DFT evaluator]

We screen defect configurations in In-doped ZnO (see al_objective.py for the design
space). The goal is to find the lowest-formation-energy configuration in as few DFT
calls as possible.

Two evaluator modes
-------------------
  --mock   (default)  formation energy from a cheap synthetic surface. Runs offline,
                      no API key, no cluster — this is what you run during the workshop
                      to *see the loop work and converge*.
  --dft               for each proposed config, call DFTOrchestrator to generate real
                      VASP inputs (needs credentials). The energy still comes from the
                      mock surface unless you actually run VASP and parse the OUTCAR —
                      see `evaluate_with_dft()` for the hook where you'd plug that in.

The BO core (`scilink ... bo_tools.get_optimizer`) needs no LLM, so --mock is fully
self-contained.

Usage
-----
    python 02_active_learning_dft.py                      # 8 seed + 12 AL iters, mock
    python 02_active_learning_dft.py --iters 20 --batch 1
    python 02_active_learning_dft.py --dft --iters 4      # also emit real VASP inputs
    python 02_active_learning_dft.py --plot               # save a convergence plot
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

from al_objective import (
    INPUT_COLS, INPUT_BOUNDS, TARGET_COL,
    mock_formation_energy, dft_request, true_optimum,
)

DEFAULT_MODEL = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")


def make_seed_data(n: int, seed: int, noise: float) -> pd.DataFrame:
    """Random initial DFT 'measurements' to start the surrogate from."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        x = [rng.uniform(lo, hi) for lo, hi in INPUT_BOUNDS]
        e = mock_formation_energy(*x, noise=noise, rng=rng)
        rows.append({**dict(zip(INPUT_COLS, x)), TARGET_COL: e})
    return pd.DataFrame(rows)


def propose_next(df: pd.DataFrame, batch: int) -> list[list[float]]:
    """Fit the GP on current data and recommend the next configuration(s).

    Uses SciLink's pure BoTorch optimizer (no LLM call). We minimize formation
    energy, and the optimizer maximizes internally, so we hand it the negated target.
    """
    from scilink.agents.planning_agents.bo_tools import get_optimizer

    X = df[INPUT_COLS].to_numpy(dtype=np.float64)
    y = df[[TARGET_COL]].to_numpy(dtype=np.float64)
    y_for_max = -y  # minimize formation energy -> maximize (-energy)
    bounds = np.array(INPUT_BOUNDS, dtype=np.float64)

    optimizer = get_optimizer(is_moo=False, device="cpu")
    optimizer.fit(X, y_for_max, bounds, {"kernel": "matern_2.5", "noise": "min_noise_low"}, INPUT_COLS)
    return optimizer.recommend(n_candidates=batch, strategy="log_ei", params={})


def evaluate_with_dft(x: list[float], model: str, run_idx: int, campaign_dir: str) -> None:
    """Generate real VASP inputs for a proposed configuration (no energy returned).

    This is the integration point with the simulate agent. It writes a ready-to-run
    VASP input set per configuration; to close the loop with *real* energies you would
    submit these on HPC, parse the relaxed total energies, and compute the formation
    energy to feed back into the surrogate (replacing the mock value below).
    """
    from scilink.agents.sim_agents.dft_orchestrator import DFTOrchestrator

    request = dft_request(*x)
    out = os.path.join(campaign_dir, f"cfg_{run_idx:02d}")
    print(f"    → generating VASP inputs in {out}/  ({request})")
    orch = DFTOrchestrator(generator_model=model, validator_model=model,
                           output_dir=out, max_refinement_cycles=3)
    res = orch.run_complete_workflow(request)
    status = "ready" if res.get("final_manifest", {}).get("ready_for_vasp") else res.get("final_status")
    print(f"      inputs: {status}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-points", type=int, default=8, help="Initial random DFT points.")
    ap.add_argument("--iters", type=int, default=12, help="Active-learning iterations.")
    ap.add_argument("--batch", type=int, default=1, help="Configs proposed per iteration.")
    ap.add_argument("--noise", type=float, default=0.0, help="Synthetic eV noise on the mock surface.")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed.")
    ap.add_argument("--dft", action="store_true", help="Also emit real VASP inputs per proposal.")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="LiteLLM model id for --dft.")
    ap.add_argument("--plot", action="store_true", help="Save convergence.png.")
    ap.add_argument("--out", default="al_history.csv", help="Where to write the run history.")
    args = ap.parse_args()

    # In --dft mode, each AL campaign gets its own timestamped subdir under al_dft_runs/
    # so re-runs don't overwrite each other, and the per-campaign LLM trace lives alongside.
    campaign_dir = None
    if args.dft:
        campaign_dir = os.path.join("al_dft_runs", datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(campaign_dir, exist_ok=True)
        import scilink
        scilink.enable_tracing(os.path.join(campaign_dir, "llm_trace.jsonl"))
        print(f"AL DFT inputs + LLM trace: {campaign_dir}/")

    df = make_seed_data(args.seed_points, args.seed, args.noise)
    best0 = df[TARGET_COL].min()
    print(f"Seeded with {len(df)} random DFT points. Best formation energy so far: {best0:.3f} eV\n")

    best_trace = [df[TARGET_COL].min()]
    run_idx = 0
    rng = np.random.default_rng(args.seed + 1)

    for it in range(1, args.iters + 1):
        candidates = propose_next(df, args.batch)
        for x in candidates:
            x = [float(v) for v in x]
            if args.dft:
                evaluate_with_dft(x, args.model, run_idx, campaign_dir)
            energy = mock_formation_energy(*x, noise=args.noise, rng=rng)
            df = pd.concat([df, pd.DataFrame([{**dict(zip(INPUT_COLS, x)), TARGET_COL: energy}])],
                           ignore_index=True)
            run_idx += 1
        best = df[TARGET_COL].min()
        best_trace.append(best)
        coords = ", ".join(f"{c}={v:.2f}" for c, v in zip(INPUT_COLS, candidates[-1]))
        print(f"iter {it:2d}: proposed [{coords}]  best-so-far = {best:.3f} eV")

    opt = true_optimum()
    best_row = df.loc[df[TARGET_COL].idxmin()]
    print("\n--- Result ---")
    print(f"Best configuration found : " +
          ", ".join(f"{c}={best_row[c]:.2f}" for c in INPUT_COLS) +
          f"  ->  {best_row[TARGET_COL]:.3f} eV")
    print(f"(synthetic optimum       : " +
          ", ".join(f"{c}={opt[c]:.2f}" for c in INPUT_COLS) +
          f"  ->  {opt[TARGET_COL]:.3f} eV)")
    print(f"DFT calls used           : {args.seed_points} seed + {run_idx} active = {args.seed_points + run_idx}")

    df.to_csv(args.out, index=False)
    print(f"History written to {args.out}")

    if args.plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            plt.figure(figsize=(5, 3.5))
            plt.plot(range(len(best_trace)), best_trace, "o-")
            plt.axhline(opt[TARGET_COL], ls="--", c="grey", label="synthetic optimum")
            plt.xlabel("active-learning iteration")
            plt.ylabel("best formation energy (eV)")
            plt.title("Active-learning DFT screening")
            plt.legend()
            plt.tight_layout()
            plt.savefig("convergence.png", dpi=150)
            print("Saved convergence.png")
        except Exception as e:  # noqa: BLE001 — plotting is optional
            print(f"(plot skipped: {e})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
