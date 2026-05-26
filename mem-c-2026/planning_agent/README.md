# Planning agent — knowledge-grounded experiment planning

SciLink's `PlanningAgent` chains a **knowledge-grounded technoeconomic analysis**
with **experimental-plan generation** in two focused LLM steps. This is the
"I have measurements + reference knowledge — tell me what's worth pursuing
and how to test it" shape.

The bundled demo combines produced-water ICP-MS data with the DOE Critical
Materials Assessment + PWS database to identify recoverable elements and
propose a 96-well precipitation screen (with Opentrons code).

## Quick start

```bash
export SCILINK_MODEL="claude-opus-4-6"   # see ../README.md for credentials
python 01_plan.py                              # TEA + plan
python 01_plan.py --tea-only                   # TEA only (faster)
python 01_plan.py --research-objective "..."   # your own plan-step goal
```

> **Embedding model.** The RAG knowledge base needs a separate embedding
> model — defaults to `gemini-embedding-001` (free key at
> <https://aistudio.google.com/apikey>; set `GEMINI_API_KEY`). Override with
> `--embedding-model` (or `$SCILINK_EMBEDDING_MODEL`) to route through your
> existing provider — e.g. `bedrock/amazon.titan-embed-text-v2:0` (uses your
> AWS creds, no extra key needed) or `openai/text-embedding-3-small` (uses
> `OPENAI_API_KEY`).

> **Alternative interactive flow with MCP/Opentrons tools:**
> `scilink plan --autonomy autopilot --data-dir ../../data/planning_produced_water/experimental_data --knowledge-dir ../../data/planning_produced_water/knowledge_folder --mcp stdio:OpentronsAI:npx,mcp-remote,https://opentrons-opentronsai-mcp-server.hf.space/gradio_api/mcp/`
> — uses the higher-level orchestrator in a chat shell; lets the agent call live Opentrons MCP tools alongside the standard plan-generation flow (the script above stays predictable / no MCP).

## What you get

A timestamped folder under `plan_output/<timestamp>/` containing:

- `tea_analysis.json` — TEA results (cost breakdowns, market analysis, viability).
- `tea_analysis.json.html` — rendered TEA report.
- `plan.json` — proposed experiments (hypotheses, steps, justifications,
  expected outcomes; includes Opentrons code when the research objective
  asks for it).
- `llm_trace.jsonl` — every LLM call (model, prompt, response, tokens, latency).

## The demo data

The bundled data (under
[`../../data/planning_produced_water/`](../../data/planning_produced_water/))
lets the agent do a technoeconomic analysis of produced water:

- `experimental_data/prowater_icpms.{xlsx,json}` — ICP-MS measurements on
  produced-water samples from the Permian Basin.
- `knowledge_folder/doe-critical-material-assessment_07312023.pdf` — DOE 2023
  Critical Materials Assessment report.
- `knowledge_folder/PWSdatabase.{xlsx,json}` — Public Water Systems contaminant
  database.
- `knowledge_folder/criticality_matrix.jpg` — DOE supply-risk × importance
  matrix image (passed to the multimodal LLM).

## Bring on Day 2

- Your own measurements (CSV / XLSX / JSON) — point `--data-dir` at them.
- Reference knowledge (PDFs, databases, images) — point `--knowledge-dir` at them.
- Edit `DEFAULT_TEA_OBJECTIVE` / `DEFAULT_RESEARCH_OBJECTIVE` in `01_plan.py`
  (or pass `--tea-objective` / `--research-objective` from the command line).
- For live tool integration (Opentrons protocol generation via MCP, etc.),
  use the `scilink plan --mcp …` CLI flow shown above instead.
