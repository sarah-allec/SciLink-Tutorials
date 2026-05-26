# Planning agent — knowledge-grounded experiment planning

SciLink's `plan` mode runs an interactive planning orchestrator that combines
your experimental measurements (`data_dir`) with reference knowledge
(`knowledge_folder` — PDFs, spreadsheets, images) to reason about what to do
next: technoeconomic analyses, knowledge-grounded literature queries,
recommended next experiments, even full Opentrons / well-plate protocols.

## Quick start

```bash
export SCILINK_MODEL="claude-opus-4-6"   # see ../README.md for credentials
python 01_plan.py                              # default technoeconomic ICP-MS task
python 01_plan.py --task "..."                 # your own objective
python 01_plan.py --autonomy autopilot         # pause for human review at decisions
```

> **Alternative interactive flow:** `scilink plan --autonomy autopilot --data-dir ../../data/planning_produced_water/experimental_data --knowledge-dir ../../data/planning_produced_water/knowledge_folder` — same orchestrator as `01_plan.py`, just launched via the chat-shell CLI instead of one-shot Python.

## What you get

A timestamped folder under `plan_output/<timestamp>/` containing:

- Campaign artifacts (knowledge-query scripts, scalarizer outputs, generated
  protocols, planning-session state).
- The agent's final report / summary.
- `llm_trace.jsonl` — every LLM call (model, prompt, response, tokens, latency).

## The demo data

The bundled data (under [`../../data/planning_produced_water/`](../../data/planning_produced_water/))
lets the agent do a technoeconomic analysis of produced water:

- `experimental_data/prowater_icpms.{xlsx,json}` — ICP-MS measurements on
  produced-water samples from the Permian Basin.
- `knowledge_folder/doe-critical-material-assessment_07312023.pdf` — DOE 2023
  Critical Materials Assessment report.
- `knowledge_folder/PWSdatabase.{xlsx,json}` — Public Water Systems contaminant
  database.
- `knowledge_folder/criticality_matrix.jpg` — DOE supply-risk × importance
  matrix image.

The default task in `01_plan.py`:

> Using the DOE assessment report, the PWS database, and the provided
> criticality-matrix image as context, analyze the ICP-MS results to determine
> which measured critical materials show concentrations that might be
> economically interesting for recovery, considering their market value.

## Bring on Day 2

- Your own measurements (CSV / XLSX / JSON) — point `--data-dir` at them.
- Reference knowledge (PDFs, databases, images) — point `--knowledge-dir` at them.
- Edit the task string in `01_plan.py` (or pass `--task "..."` from the
  command line) to describe what you want the agent to do.
