# Track A — Analysis agent (imaging)

> 🚧 **Scaffold — example not built yet.** Planned next; the `simulation_agents/` track is
> the finished reference for structure/quality.

For **Group A** — image analysis (SEM defects, STEM, AFM moiré domains).

SciLink's `analyze` mode ingests image data and runs segmentation / feature extraction
(denoising, FFT phase mapping, semantic segmentation of atomic- and meso-scale images),
then can hand findings to the planning or simulation agents.

**Planned example:** semantic segmentation of an SEM/AFM image to locate defects / domains,
themed on ZnO microscopy and moiré AFM.

**Reuse in the meantime:** the existing image-analysis tutorials in
`Hackathon/tutorials/ImageAnalysis/` (GrainBoundarySegmentation, ImageCleaning, PhaseMapping)
and `mrs-2026/analysis_agent/` (the EELS hyperspectral example).

**Bring on Day 2:** 1–2 of your own images (SEM/STEM/AFM) plus pixel size / instrument metadata.
