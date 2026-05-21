"""
Configuration space and objective for the active-learning DFT screening demo.

We screen point-defect configurations in **In-doped wurtzite ZnO** — a system that
recurs across the cohort (In:ZnO synthesis, ZnO microscopy, defect/dopant DFT). The two
design variables are the kind of thing you would actually sweep in a defect study:

    x1 = indium substitution level on the Zn sublattice   [at.%]   in [0, 12]
    x2 = oxygen-vacancy concentration                      [at.%]   in [0, 6]

The objective is the **defect formation energy** (eV) — lower is more stable, so we
*minimize*. In a real campaign each evaluation is a VASP relaxation costing hours of
HPC time; that is exactly why active learning is worth it — we want to find the
low-formation-energy region in as few DFT runs as possible.

For the workshop the formation energy is returned by a cheap synthetic surface
(`mock_formation_energy`) so the whole loop runs on a laptop with no API key and no
cluster. `02_active_learning_dft.py` shows where to swap in the real
DFTOrchestrator + VASP evaluation.
"""

from __future__ import annotations

import numpy as np

# --- Design space -----------------------------------------------------------
# (name, low, high, unit) for each variable, in the order the optimizer sees them.
DESIGN_VARIABLES = [
    ("In_at_pct", 0.0, 12.0, "at.% In on Zn site"),
    ("Ovac_at_pct", 0.0, 6.0, "at.% oxygen vacancies"),
]

INPUT_COLS = [v[0] for v in DESIGN_VARIABLES]
INPUT_BOUNDS = [[v[1], v[2]] for v in DESIGN_VARIABLES]
TARGET_COL = "formation_energy_eV"
TARGET_DIRECTION = "minimize"

# Synthetic ground-truth optimum, used only to report "how close did we get".
_TRUE_OPTIMUM = {"In_at_pct": 6.0, "Ovac_at_pct": 2.0, "formation_energy_eV": 1.55}


def mock_formation_energy(in_at_pct: float, ovac_at_pct: float, noise: float = 0.0,
                          rng: np.random.Generator | None = None) -> float:
    """Cheap stand-in for a DFT defect-formation-energy calculation.

    A smooth convex bowl (minimum near 6 at.% In, 2 at.% V_O) with a mild
    oscillation in the In direction so the surface isn't trivially quadratic.
    Returns energy in eV. Set ``noise`` > 0 to mimic finite-k-point / smearing
    scatter between nominally-equivalent runs.
    """
    e = (
        2.0
        + 0.040 * (in_at_pct - 6.0) ** 2
        + 0.090 * (ovac_at_pct - 2.0) ** 2
        - 0.150 * np.sin(0.5 * in_at_pct)
        + 0.020 * in_at_pct * ovac_at_pct * 0.0  # placeholder for an interaction term
    )
    if noise:
        rng = rng or np.random.default_rng()
        e += rng.normal(0.0, noise)
    return float(e)


def dft_request(in_at_pct: float, ovac_at_pct: float) -> str:
    """Natural-language structure request for the SciLink DFT structure agent.

    Translates a point in the design space into the kind of free-text description
    DFTOrchestrator.run_complete_workflow() expects. Concentrations are mapped to a
    concrete 3x3x2 wurtzite ZnO supercell (72 atoms: 36 Zn, 36 O) so the counts are
    unambiguous for the structure-generation agent.
    """
    n_cation = 36
    n_anion = 36
    n_in = max(0, round(in_at_pct / 100.0 * n_cation))
    n_vac = max(0, round(ovac_at_pct / 100.0 * n_anion))

    parts = ["3x3x2 wurtzite ZnO supercell (36 Zn, 36 O)"]
    if n_in:
        parts.append(f"with {n_in} In atom(s) substituting Zn ({in_at_pct:.1f} at.%)")
    if n_vac:
        joiner = "and" if n_in else "with"
        parts.append(f"{joiner} {n_vac} oxygen vacancy(ies) ({ovac_at_pct:.1f} at.%)")
    if not n_in and not n_vac:
        parts.append("(pristine reference cell)")
    return ", ".join(parts)


def true_optimum() -> dict:
    """Return the (synthetic) global optimum, for convergence reporting."""
    return dict(_TRUE_OPTIMUM)
