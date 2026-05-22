# Track D — Simulation agents (DFT)

For **Group D** and any of the strongly computational fellows
 whose work is simulation-first.

SciLink's `simulate` mode turns a natural-language description of a material into a
built, validated structure and ready-to-run VASP inputs, with a self-refinement loop
around the actual engine run. This track has two parts:

| Script | What it shows | Needs |
|---|---|---|
| `01_dft_defect.py` | One agent call: defect description → structure → **VASP inputs** | credentials; **no cluster** |
| `02_active_learning_dft.py` | An **active-learning loop** that uses a GP surrogate to choose which DFT calc to run next | runs offline in `--mock`; credentials only for `--dft` |

Both are themed around **In-doped wurtzite ZnO** point defects — a system shared across
the cohort (In:ZnO synthesis, ZnO microscopy, defect/dopant DFT) — but every request is
free text, so you can retarget them to your own system in one line (a preset for a
Yb-doped MOF node is also included).

## Files

```
simulation_agents/
├── 01_dft_defect.py          # Part 1 — single structure → VASP inputs
├── 02_active_learning_dft.py # Part 2 — BO-driven DFT screening loop
├── al_objective.py           # design space + (mock) formation-energy surface
└── data/
    └── seed_configs.csv       # 8 example "DFT" points to start the surrogate
```

## Setup

See [`../README.md`](../README.md) for the conda env and API-key setup. Set the model once:

```bash
export SCILINK_MODEL="claude-opus-4-6"   # or whichever model you're given
```

The Bayesian-optimization core (`scilink.agents.planning_agents.bo_tools.get_optimizer`)
makes **no LLM calls**, so Part 2 in `--mock` mode runs with no credentials at all — a good
first thing to run on Day 1.

## Part 1 — generate a calculation

`01_dft_defect.py` turns a natural-language description of a structure into VASP inputs. You
describe the structure in **one of two ways** — both feed the same agent, they just differ in
where the text comes from:

- **`--system <name>`** — use a built-in **preset** (vetted, cohort-relevant). Run `--list` to
  see them: `zno_in`, `zno_in_ovac` (default), `zno_n_sub`, `mof_yb_node`.
- **`--request "<text>"`** — supply your **own free-text** description of any structure. If you
  pass both, `--request` wins.

```bash
python 01_dft_defect.py --list                 # show the preset systems
python 01_dft_defect.py --system zno_in_ovac   # a preset: In:ZnO with an O vacancy
python 01_dft_defect.py --request "5x5 MoS2 monolayer, 2H phase, with one S vacancy"
```

Either way it writes `POSCAR`/`INCAR`/`KPOINTS` into a timestamped folder
`dft_output/<system-or-request>/<YYYYMMDD_HHMMSS>/`, so every run is preserved — handy for model
comparisons and variability tests. Override the path entirely with `--output-dir`. Each run folder
also gets an `llm_trace.jsonl` — every LLM call (model, prompt, response, token usage, latency).
The agent builds the structure with an ASE script, validates it, and auto-refines if the script
errors (up to `--max-cycles`). You then run VASP on HPC.

> 💡 On Day 2, the quickest path to your own system is `--request "..."`; if you'll reuse it,
> add a named entry to the `PRESETS` dict at the top of `01_dft_defect.py`.

## Part 2 — active-learning DFT screening

The idea: each DFT relaxation is expensive, so instead of a brute-force grid we fit a
Gaussian-process surrogate to the data we have, let it propose the most promising next
configuration, "compute" it, and repeat — converging on the low-formation-energy region
in far fewer calls.

```bash
python 02_active_learning_dft.py --plot              # offline; saves convergence.png
python 02_active_learning_dft.py --iters 20 --batch 2
python 02_active_learning_dft.py --dft --iters 4     # also emits real VASP inputs per proposal
```

**Closing the loop with real DFT.** In `--mock` the formation energy comes from a cheap
synthetic surface (`al_objective.mock_formation_energy`) so you can watch the loop converge
immediately. To make it real, run the VASP inputs that `--dft` generates, parse the relaxed
energies, compute the formation energy, and feed that back in place of the mock value — the
hook is marked in `evaluate_with_dft()`.

## Make it yours (Day 2)

- **New system:** edit the `PRESETS` dict in `01_dft_defect.py`, or pass `--request`.
- **New design space:** edit `DESIGN_VARIABLES` in `al_objective.py` (e.g., swap In→Yb for
  the MOF work, or add a second dopant). `INPUT_COLS`/`INPUT_BOUNDS` update automatically.
- **Your own seed data:** replace `data/seed_configs.csv` with your real DFT results (same
  columns) and start the surrogate from genuine calculations.
