# UV-Vis Spectrum Simulator for BO Loop Testing

Synthetic UV-Vis spectra with temperature/pH-dependent peak shifts. Use with SciLink's `analyze_batch` + `run_optimization` loop.

## Quick Start

```bash
# 1. Generate initial spectra (9 = 3x3 grid over temperature and pH)
python simulate_spectra.py init --output_dir ./spectra --grid

# 2. Upload ./spectra/ to SciLink (Plan mode, Data section)
#    Set objective: "Maximize UV-Vis absorption peak intensity by tuning temperature and pH"

# 3. SciLink runs analyze_batch → run_optimization → suggests next params

# 4. Generate new spectra from BO suggestions
python simulate_spectra.py run --output_dir ./spectra \
    --params '{"temperature_C": 55.0, "pH": 8.5}'

# 5. Upload new file(s) to SciLink → repeat from step 3
```

## Commands

| Command | What it does |
|---------|-------------|
| `init --output_dir DIR` | Generate 9 initial spectra (random) |
| `init --output_dir DIR --grid` | Generate 9 initial spectra (3x3 even grid) |
| `init --output_dir DIR --n 16 --grid` | Custom count (4x4 grid) |
| `run --output_dir DIR --params '{...}'` | Generate spectrum for one set of params |
| `run --output_dir DIR --params '[{...}, {...}]'` | Generate batch from BO suggestions |

Each spectrum generates a CSV (`wavelength_nm, absorbance`) + sidecar JSON (`temperature_C, pH`).

## Ground Truth

Peak absorbance is maximized at **T~55°C, pH~8.5** (interior of parameter space). The optimizer should converge toward this region.
