# Track B — Curve fitting (analysis agent)

For **Group B** — curve fitting (SQUID magnetometry, SAXS/SANS, UV-Vis/DLS, Monte Carlo output).

SciLink's `analyze` mode on **1-D curves**: the agent proposes a physically-motivated
fitting model (via `lmfit`), fits it, iteratively refines until R² passes a quality
threshold, and reports parameters with uncertainties. Useful when the fitting model is
degenerate or you have many curves to fit consistently.

## Quick start

```bash
export SCILINK_MODEL="claude-opus-4-6"        # see ../README.md for credentials
python 01_curve_fit.py                         # default demo: mos2_pl
python 01_curve_fit.py --dataset raman_silicon
python 01_curve_fit.py --data my_curve.csv --info "SQUID M-T of a Co-doped ZnO film"
python 01_curve_fit.py --list                  # list demo curves
```

> **Alternative interactive flow:** `scilink analyze --data data/mos2_pl.csv --metadata data/mos2_pl_metadata.json` — uses the higher-level orchestrator with a chat shell (same underlying agent + one extra routing LLM call upfront).

## What you get

A timestamped folder under `curve_output/<dataset>/<timestamp>/` containing:

- **HTML report** — data, fit, residuals, the model.
- `analysis_results.json` — extracted parameters with uncertainties, R², model summary.
- The actual fitting script the agent generated and executed.
- `llm_trace.jsonl` — every LLM call (model, prompt, response, tokens, latency).

## The demo curves

- **mos2_pl** — Photoluminescence of monolayer MoS₂. The agent should converge on a
  3-peak Voigt model (B exciton ~615 nm, A exciton ~667 nm, defect emission ~740 nm)
  on a linear baseline.
- **raman_silicon** — Raman spectrum of silicon (single strong phonon peak near 520 cm⁻¹).

## Bring on Day 2

1–2 of your own curves as CSV (x, y columns) plus what physical parameters you're trying
to extract. Either point `--data my.csv --info "..."` at them, or add a new entry to
`PRESETS` and a small metadata JSON alongside the CSV.
