# Track B — Curve fitting (analysis agent)

> 🚧 **Scaffold — example not built yet.** Planned next; the `simulation_agents/` track is
> the finished reference for structure/quality.

For **Group B** — curve fitting (SQUID magnetometry, SAXS/SANS, UV-Vis/DLS, Monte Carlo output).

This uses the same SciLink `analyze` mode as Track A, but on **1-D curves** rather than
images: the agent proposes a fitting model (via `lmfit`), fits it, and reports parameters
with uncertainties — useful when the fitting model is degenerate or you have many curves.

**Planned example:** fit a SQUID M–H / M–T curve and a SAXS profile, extract parameters,
and flag model-degeneracy — mirroring `mrs-2026/analysis_agent/` (PL/Raman peak fitting).

**Reuse in the meantime:** `mrs-2026/analysis_agent/` (`mos2_pl.csv`, `raman_silicon.csv`)
shows the curve-fit → parameter-extraction chain end to end.

**Bring on Day 2:** 1–2 of your own curves as CSV (x, y columns) plus what physical
parameters you're trying to extract.
