#!/usr/bin/env python3
"""
UV-Vis Spectrum Simulator v3 — realistic noise for meaningful GP residuals.

Same interior optimum as v2 (T~55C, pH~8.5), but with:
  1. Higher spectral noise (0.02 vs 0.005) — noisier raw spectra
  2. Run-to-run variability — peak height varies ±5% between measurements
     at the same conditions (mimics sample prep, instrument drift)
  3. Slight nonlinearity — a sin(T) interaction term that the GP's
     stationary kernel can't perfectly capture

This produces GP residuals of ~0.01-0.05 (vs 1e-5 in v2), making the
residuals panel and uncertainty bands visually informative.

Usage:
  python simulate_spectra_v3.py init --output_dir ./spectra --n 8
  python simulate_spectra_v3.py run  --output_dir ./spectra \
      --params '{"temperature_C": 55, "pH": 8.5}'
"""

import argparse
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path


WAVELENGTHS = np.linspace(350, 600, 251)

BOUNDS = {
    "temperature_C": (5.0, 100.0),
    "pH": (1.0, 14.0),
}

OPT_TEMP = 55.0
OPT_PH = 8.5


def generate_spectrum(temp: float, ph: float, noise_level: float = 0.008) -> np.ndarray:
    """Generate a synthetic UV-Vis spectrum with a single clean peak.

    Designed for tutorial use: one dominant Gaussian peak that's easy for
    automated peak-finding to extract. Run-to-run variability (±3%) provides
    meaningful GP residuals without confusing the scalarizer.
    """
    peak_center = 450 + 0.3 * (temp - 25) - 5.0 * (ph - 7.0)
    peak_width = 30 + 0.15 * (temp - 25)

    # Peak height: Gaussian hill + nonlinear interaction term
    # Length scales chosen so both parameters contribute meaningfully:
    #   temperature: ±10°C from optimum halves the response
    #   pH: ±2.5 from optimum halves the response
    base_height = (
        1.4 * np.exp(
            -0.5 * ((temp - OPT_TEMP) / 10) ** 2
            - 0.5 * ((ph - OPT_PH) / 2.5) ** 2
        )
        + 0.15
    )
    # Nonlinear interaction: sin term the GP can't perfectly fit
    interaction = 0.03 * np.sin(0.08 * temp) * np.cos(0.3 * ph)

    # Run-to-run variability (±3% multiplicative noise on peak height)
    run_variability = 1.0 + np.random.normal(0, 0.03)

    peak_height = max((base_height + interaction) * run_variability, 0.1)

    # Single clean peak — no shoulder
    absorbance = peak_height * np.exp(
        -0.5 * ((WAVELENGTHS - peak_center) / peak_width) ** 2
    )
    # Gentle baseline only
    baseline = 0.01 + 0.00005 * (WAVELENGTHS - 350)
    noise = np.random.normal(0, noise_level, len(WAVELENGTHS))

    return np.clip(absorbance + baseline + noise, 0, None)


def save_spectrum(temp: float, ph: float, output_dir: Path, label: str = None):
    absorbance = generate_spectrum(temp, ph)
    if label is None:
        label = f"spectrum_T{temp:.1f}_pH{ph:.1f}"
    label = label.replace(" ", "_")

    csv_path = output_dir / f"{label}.csv"
    json_path = output_dir / f"{label}.json"

    df = pd.DataFrame({"wavelength_nm": WAVELENGTHS, "absorbance": absorbance})
    df.to_csv(csv_path, index=False)

    conditions = {"temperature_C": round(temp, 2), "pH": round(ph, 2)}
    with open(json_path, "w") as f:
        json.dump(conditions, f, indent=2)

    return csv_path.name


def cmd_init(args):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n = args.n
    if args.grid:
        # Ensure at least 3 temperature levels so the GP can detect
        # the interior optimum (2 symmetric levels cancel out)
        n_temp = max(3, int(np.sqrt(n)))
        n_ph = max(2, n // n_temp)
        temps = np.linspace(25, 85, n_temp)
        phs = np.linspace(4, 12, n_ph)
        conditions = [
            {"temperature_C": float(t), "pH": float(p)}
            for t in temps for p in phs
        ][:n]
    else:
        np.random.seed(args.seed)
        conditions = [
            {
                "temperature_C": round(np.random.uniform(20, 90), 1),
                "pH": round(np.random.uniform(3, 12), 1),
            }
            for _ in range(n)
        ]

    global_conditions = {}
    for cond in conditions:
        fname = save_spectrum(cond["temperature_C"], cond["pH"], output_dir)
        global_conditions[fname] = cond
        print(f"  Generated: {fname}")

    with open(output_dir / "conditions.json", "w") as f:
        json.dump(global_conditions, f, indent=2)

    print(f"\nGenerated {len(conditions)} initial spectra in {output_dir}/")
    print(f"Ground truth optimum: T={OPT_TEMP}C, pH={OPT_PH}")


def cmd_run(args):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Error: could not parse --params JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(params, dict):
        params = [params]

    conditions_path = output_dir / "conditions.json"
    if conditions_path.exists():
        with open(conditions_path) as f:
            global_conditions = json.load(f)
    else:
        global_conditions = {}

    generated = []
    for i, p in enumerate(params):
        temp = p.get("temperature_C")
        ph = p.get("pH")
        if temp is None or ph is None:
            print(f"Error: entry {i} missing 'temperature_C' or 'pH': {p}", file=sys.stderr)
            continue

        temp = float(np.clip(temp, *BOUNDS["temperature_C"]))
        ph = float(np.clip(ph, *BOUNDS["pH"]))

        label = f"spectrum_T{temp:.1f}_pH{ph:.1f}"
        fname = save_spectrum(temp, ph, output_dir, label=label)
        global_conditions[fname] = {"temperature_C": round(temp, 2), "pH": round(ph, 2)}
        generated.append(fname)
        print(f"  Generated: {fname}  (T={temp:.1f}C, pH={ph:.1f})")

    with open(conditions_path, "w") as f:
        json.dump(global_conditions, f, indent=2)

    print(f"\nGenerated {len(generated)} new spectra in {output_dir}/")
    if generated:
        print(f"\nFiles to analyze:")
        for fname in generated:
            print(f"  {output_dir / fname}")


def main():
    parser = argparse.ArgumentParser(
        description="UV-Vis Spectrum Simulator v3 (realistic noise)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Generate initial batch")
    p_init.add_argument("--output_dir", required=True)
    p_init.add_argument("--n", type=int, default=9, help="Number of spectra (default: 9, use with --grid for 3x3)")
    p_init.add_argument("--grid", action="store_true")
    p_init.add_argument("--seed", type=int, default=42)

    p_run = sub.add_parser("run", help="Generate spectra for BO-suggested params")
    p_run.add_argument("--output_dir", required=True)
    p_run.add_argument("--params", required=True)

    args = parser.parse_args()
    if args.command == "init":
        cmd_init(args)
    elif args.command == "run":
        cmd_run(args)


if __name__ == "__main__":
    main()
