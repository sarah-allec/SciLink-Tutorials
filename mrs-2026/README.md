# MRS Tutorial — MT01

Hands-on materials for [SciLink](https://github.com/ziatdinovmax/SciLink), an open-source agentic platform for materials sciences developed at PNNL. Three tracks, run in this order during the demo:

| # | Folder | Track |
|---|---|---|
| 1 | `planning_agent/` | Knowledge-grounded experiment planning (PFAS / critical-materials) |
| 2 | `BOAgent/` | UV-Vis closed-loop Bayesian optimization |
| 3 | `analysis_agent/` | Spectroscopy → curve-fit → DFT input generation |

## Setup

```bash
pip install 'scilink[ui]'              # required (version 0.0.28)
pip install ase                  # required for the DFT step in track 3
```

For `vasp_generator_method="atomate2"` (track 3, optional), also `pip install pymatgen atomate2`.

## Run

```bash
scilink-ui
```

In the sidebar: paste the API key, tick the code-execution consent checkbox, **Start Session**.

## Data

**Track 1 — planning**
- `planning_agent/knowledge_folder/` — PFAS criticality matrix, DOE critical-material assessment (PDF), PWS contaminant database.
- `planning_agent/experimental_data/prowater_icpms.{xlsx,json}` — ICP-MS measurements on produced-water samples.
- **Sample technoeconomic objective**: "Using the DOE assessment report, the PWS database, and the provided criticality matrix image as context, analyze the ICP-MS results to determine which "measured critical materials show concentrations that might be economically interesting for recovery, considering their market value."
- **Sample research objective**: "Based on the ICP-MS results and the prior TEA identifying valuable materials, a simple chemical process (like precipitation) to selectively recover the most promising material from the water sample. Use only reagents that are simple commodity chemicals. In your proposal specifically identify a range of conditions for concentrations, ratios, solubilities, or other variable for testing optimal recovery. Put these conditions in a table for a 96 well plate and using an opentrons. The experiment should cover a wide range of conditions which may span into the non-recovery regime, so as to provide the most data. Rather than measure pH estimate required amounts of acid or base. Prefer additional conditions spread over the columns and rows rather than replicate trials. Target a maximum 360 μL total volume, and prefer to use concentrations at most 1M. Provide corresponding Opentrons code."
- **Advanced**: To connect to an external server via model context protocol (MCP), click on `Tools` and fill out the `MCP Server` section as shown below:
  - *Transport*: Select stdio   
  - *Server name*: OpentronsAI
  - *Command*: npx mcp-remote https://opentrons-opentronsai-mcp-server.hf.space/gradio_api/mcp/ 

**Track 2 — BO**
- Generate the initial 3×3 grid: `python BOAgent/simulate_spectra.py init --output_dir BOAgent/spectra --grid` — produces 9 UV-Vis spectra over (temperature, pH) plus per-spectrum metadata sidecars.
- After each BO suggestion, append the suggested point: `python BOAgent/simulate_spectra.py run --output_dir BOAgent/spectra --params '{"temperature_C": xx.x, "pH": x.x}'`.
- Ground-truth optimum: T ≈ 55 °C, pH ≈ 8.5. Full simulator interface in `BOAgent/README.md`.

**Track 3 — analysis**
- `analysis_agent/data/mos2_pl.csv` (+ `_metadata.json`) — primary demo. Synthetic monolayer MoS₂ photoluminescence (RT). Exercises the full curve-fit → defect identification → DFT-input chain.
- `analysis_agent/data/raman_silicon.csv` (+ `_metadata.json`) — Si Raman 520 cm⁻¹ peak; simpler single-component fit.
- `analysis_agent/data/eels_plasmons.{npy,json}` — low-loss EELS hyperspectral data (uses a different analysis agent).
