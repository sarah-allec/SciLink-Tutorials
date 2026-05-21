# MEM-C 2026: SciLink Tutorials

Hands-on materials for [SciLink](https://github.com/ziatdinovmax/SciLink), an open-source agentic
platform for the materials sciences developed at PNNL. These tracks are tailored to the Phase 1
fellows' research areas (microscopy, scattering/magnetometry, autonomous synthesis, and
first-principles simulation).

SciLink's capabilities fall into three "modes," and the tracks below map onto them plus the four
hackathon groups:

| Track (folder) | Group | SciLink mode | What you'll do |
|---|---|---|---|
| [`analysis_agent/`](analysis_agent/) | **A — Image Analysis** | `analyze` | Segment / interpret SEM, STEM, and AFM images |
| [`curvefit_agent/`](curvefit_agent/) | **B — Curve Fitting** | `analyze` | Fit SQUID, SAXS/SANS, UV-Vis curves and extract parameters |
| [`bo_agent/`](bo_agent/) | **C — Bayesian Optimization** | `plan` | Drive closed-loop synthesis optimization |
| [`simulation_agents/`](simulation_agents/) | **D — DFT / Simulation** | `simulate` | Build defect supercells, generate VASP inputs, run an active-learning DFT loop |

> **Heads up for the strongly computational fellows** (Zeiger, Nguyen, Peralta, Kubra, Zhang):
> even if your group is A or B, the [`simulation_agents/`](simulation_agents/) track is the closest
> fit to your day-to-day work, so feel free to tackle that one as well.

## Agenda at a glance

**Day 1** — Setup → *Hello Agent* (call an LLM via API, give it a custom tool) → Overview of SciLink
→ work through the example tracks above.
**Day 2** — Recap → split into Groups A–D and apply SciLink to **your own data** (bring 1–2 datasets).

## Setup

Follow `Pre-workshop_instructions.docx` first (VS Code + Miniconda + `requirements.txt`). In short:

```bash
conda create -n scilink python=3.12 -y
conda activate scilink
pip install -r requirements.txt        # the workshop requirements.txt (pins scilink deps)
```

### LLM provider / credentials

SciLink routes every model call through [LiteLLM](https://docs.litellm.ai/), so the provider is
selected by the **model-name prefix** and credentials come from environment variables. The workshop
distributes **short-lived AWS session tokens** (no personal account needed), so we use AWS Bedrock:

```bash
export AWS_ACCESS_KEY_ID=...           # provided on-site
export AWS_SECRET_ACCESS_KEY=...       # provided on-site
export AWS_SESSION_TOKEN=...           # provided on-site (expires end of day)
export AWS_REGION_NAME=us-east-1       # confirm region on-site
export SCILINK_MODEL="bedrock/<model-id-provided-on-site>"
```

> ⚠️ The exact Bedrock model id and region will be given to you at the start of Day 1. Every script
> here reads the model from `SCILINK_MODEL` (falling back to a default) so you only set it once.
> If the organizers instead hand out an internal-proxy key, set `SCILINK_API_KEY=...` and pass
> `base_url=...` — ask a helper which path your cohort is using.

Quick check that your environment + credentials work:

```bash
python -c "from scilink.agents.planning_agents.bo_tools import get_optimizer; print('scilink OK')"
```

## Running

Each track folder has its own `README.md` with step-by-step instructions. Recommended Day-1 order:

1. `simulation_agents/` — start with `01_dft_defect.py` (no cluster needed; generates inputs only)
2. your group's track (`analysis_agent/`, `curvefit_agent/`, or `bo_agent/`)

The active-learning loop in `simulation_agents/02_active_learning_dft.py` runs **fully offline**
(its Bayesian-optimization core needs no API key), so it's a safe place to start even before
credentials are handed out.
