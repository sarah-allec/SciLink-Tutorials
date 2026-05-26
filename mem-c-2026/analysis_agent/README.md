# Track A — Image analysis (analysis agent)

For **Group A** — image analysis (SEM defects, STEM atomic columns, AFM moiré
domains, optical microstructure).

SciLink's `analyze` mode on **2-D microscopy images**: the agent plans a pipeline
(denoising / FFT / segmentation / feature extraction), runs it, extracts features
(atoms, grains, domains, defects, ...), and reports scientific claims grounded in
those features.

## Quick start

```bash
export SCILINK_MODEL="claude-opus-4-6"        # see ../README.md for credentials
python 01_image_analysis.py                          # default demo: mos2_stem
python 01_image_analysis.py --dataset polycrystalline
python 01_image_analysis.py --data my.npy --info "..."  # your own image
python 01_image_analysis.py --list                    # list demo images
```

## What you get

A timestamped folder under `image_output/<dataset>/<timestamp>/` containing:

- Annotated figures (segmentation masks, atom/grain overlays, FFT panels).
- `analysis_results.json` — extracted features, scientific claims, the analysis approach.
- The actual analysis script the agent generated and executed.
- `llm_trace.jsonl` — every LLM call (model, prompt, response, tokens, latency).

## The demo images

Both presets are pulled from SciLink's own examples and ship with the metadata the
agent uses.

- **mos2_stem** — 1% V-doped MoS₂ monolayer, HAADF-STEM, 9 × 9 nm field of view.
  Atomic resolution; the agent should identify atomic columns, vanadium dopants, and
  sulfur vacancies. *Same material as Track B's photoluminescence demo — fellows fit
  a MoS₂ PL spectrum in Group B and analyze atomic-resolution MoS₂ in Group A.*
- **polycrystalline** — 304 stainless steel, bright-field optical microscopy,
  100 × 100 µm. No specific goal needed — the agent picks the analysis (grain
  segmentation + size statistics).

## Bring on Day 2

1–2 of your own images (SEM/STEM/AFM/optical) as `.npy` / `.png` / `.tif`, plus a
small JSON sidecar with `material_type`, `experiment_type`, and `spatial_info`
(field of view + units) — see `data/mos2_stem.json` for the shape. Either point
`--data my.npy --info my.json` at them, or add a new entry to `PRESETS`.
