# Track C — Bayesian optimization (planning agent)

For **Group C** — Bayesian optimization of synthesis (e.g. doped-oxide and MOF
synthesis, cluster and intercalant screening).

SciLink's `BOAgent` runs closed-loop Bayesian optimization over experimental
parameters: read your past runs, fit a Gaussian-process surrogate, and recommend the
next batch of conditions. The LLM picks the kernel / acquisition / noise strategy and
respects the remaining experimental budget.

## Quick start

```bash
export SCILINK_MODEL="claude-opus-4-6"        # see ../README.md for credentials
python 01_bo_uvvis.py                          # default: mrs UV-Vis starter grid
python 01_bo_uvvis.py --batch-size 3 --budget 5
python 01_bo_uvvis.py --spectra ./my_runs --conditions ./my_runs/conditions.json
```

## What you get

A timestamped folder under `bo_output/<timestamp>/` containing:

- `experiments.csv` — the tidy `(temperature_C, pH, peak_absorbance)` table the
  script built from the input spectra.
- `batch_step_N.csv` — the next batch of conditions the agent recommends.
- Acquisition-function plot (`acq_step_N.png`) + GP-fit plot (`step_N.png`) +
  acquisition data array (`acq_data_step_N.npz`).
- `bo_history.json` + `bo_state.json` — persist the campaign across runs (just
  append new rows to your data CSV and re-run; the agent picks up where it left off).
- `llm_trace.jsonl` — every LLM call (model, prompt, response, tokens, latency).

## How the demo works

The default starter grid lives in `../../mrs-2026/bo_agent/spectra/` — 9 simulated
UV-Vis spectra over a 3×3 (temperature, pH) grid. The script scalarizes each
spectrum to its peak absorbance and hands the `(T, pH) → peak` table to `BOAgent`.
Ground-truth optimum is in the interior at **T ≈ 55 °C, pH ≈ 8.5**, and from this
seed grid the agent typically lands its first batch right on top of it.

To **close the loop**, generate spectra for the recommended conditions with the mrs
simulator and re-run — the agent reads the appended rows and picks up the campaign:

```bash
python ../../mrs-2026/bo_agent/simulate_spectra.py run \
    --output_dir ../../mrs-2026/bo_agent/spectra \
    --params '{"temperature_C": 55.0, "pH": 8.5}'
python 01_bo_uvvis.py                          # re-run; uses the larger grid
```

> The same `BOAgent` / `get_optimizer` engine drives the active-learning loop in
> `../simulation_agents/02_active_learning_dft.py` — Group C and Group D are two
> faces of the same machinery (experiments vs. calculations).

## Bring on Day 2

A table of your past experiments (inputs + measured target) as CSV/XLSX plus the
parameter ranges you can actually access. The script's `scalarize_spectra` helper
shows where to plug in your own scalarizer (peak area, fitted height, color
coordinate, yield, ...) if your target isn't simply "max of the curve".
