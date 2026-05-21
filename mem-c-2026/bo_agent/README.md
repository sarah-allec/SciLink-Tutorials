# Track C — Bayesian optimization (planning agent)

> 🚧 **Scaffold — example not built yet.** Planned next; the `simulation_agents/` track is
> the finished reference for structure/quality.

For **Group C** — Bayesian optimization of synthesis (e.g. doped-oxide and MOF synthesis, cluster
and intercalant screening).

SciLink's `plan` mode runs closed-loop Bayesian optimization over experimental parameters:
read your past runs, fit a GP, and recommend the next batch of conditions (the LLM picks the
kernel / acquisition / noise strategy, budget-aware).

**Planned example:** re-theme the `mrs-2026/bo_agent/` UV-Vis closed-loop demo to a
**synthesis** objective (e.g., optimizing In:ZnO or MOF synthesis conditions toward a target
PL / yield), since this cohort is synthesis-driven rather than leaching-driven.

**Reuse in the meantime:** `mrs-2026/bo_agent/` is a complete BO loop —
`simulate_spectra.py` generates a 3×3 (temperature, pH) grid of UV-Vis spectra, you upload
them in a planning session, and the agent proposes the next point toward the optimum.

> The same Bayesian-optimization engine drives the active-learning loop in
> `../simulation_agents/02_active_learning_dft.py` — Group C and Group D are two faces of the
> same `BOAgent` / `get_optimizer` machinery (experiments vs. calculations).

**Bring on Day 2:** a table of past experiments (inputs + measured target) as CSV/XLSX, and
the parameter ranges you can actually access.
