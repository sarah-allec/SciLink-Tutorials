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

> **Heads up if your work is simulation-first:** even if your group is A or B, the
> [`simulation_agents/`](simulation_agents/) track is the closest fit to day-to-day computational
> work, so feel free to tackle that one as well.

## Agenda at a glance

**Day 1** — Setup → [*LLM Agents 101*](../llm-agents-101/aws-bedrock/)  → Overview of SciLink
→ work through the example tracks above.

**Day 2** — Recap → split into Groups A–D and apply SciLink to **your own data** (bring 1–2 datasets).

## Setup

Do these steps **before** the workshop — some downloads are large. The SciLink version and your
API key are provided on Day 1, so you only need the prerequisites below now.

> ⚠️ Don't install SciLink itself ahead of time — the correct version is handed out on Day 1.
> The `requirements.txt` here installs only its dependencies.

### 1. Install VS Code

The recommended editor (integrated terminal, Python debugging, Jupyter):
<https://code.visualstudio.com/download>. Then add the **Python** and **Jupyter** extensions from
the Extensions sidebar.

### 2. Install Miniconda

A lightweight Python environment manager: <https://docs.anaconda.com/miniconda/install/>. Then
create the workshop environment:

```bash
conda create -n scilink python=3.12 -y
conda activate scilink
pip install 'scilink[sim]' # or pip install 'scilink[sim,ui]' to use the ui
```

### 3. Install dependencies

From the `mem-c-2026/` folder, with the `scilink` env active:

```bash
pip install -r requirements.txt
```

💡 Some packages (PyTorch, AtomAI) are large and can take 5–10 minutes — use a stable connection
and do this before you arrive.

### 4. Docker (optional)

Optional but handy for a reproducible environment:
<https://www.docker.com/products/docker-desktop/>. Have Docker Desktop running before Day 1
(a pre-built image will be provided).

### Pre-workshop checklist

- [ ] VS Code installed with the Python extension
- [ ] Miniconda installed; `scilink` environment created with Python 3.12
- [ ] `pip install -r requirements.txt` completed without errors
- [ ] (optional) Docker Desktop installed and running
- [ ] Bring 1–2 of your own datasets to work with on Day 2

### LLM provider / API key

SciLink routes every model call through [LiteLLM](https://docs.litellm.ai/): set an API key for your
provider as an environment variable, and choose the model via `SCILINK_MODEL` (the provider is
inferred from the model name, so Claude / GPT / Gemini work as bare names). You'll be given a key
on Day 1. For example, with Anthropic:

```bash
export ANTHROPIC_API_KEY=...                       # provided on-site
export SCILINK_MODEL="claude-opus-4-6"   # or whichever model you're given
```

Other providers work the same way — set the matching key and model name:

```bash
export OPENAI_API_KEY=...   ; export SCILINK_MODEL="gpt-4o"
export GEMINI_API_KEY=...   ; export SCILINK_MODEL="gemini-2.5-pro"
```

Or with **AWS Bedrock** (one credential covers both Claude LLMs and Titan/Cohere
embeddings — handy if your `planning_agent/` track uses a different embedding
provider than the rest):

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION_NAME=us-east-1
export SCILINK_MODEL="bedrock/anthropic.claude-opus-4-20250514-v1:0"
```

> Only models SciLink can't auto-detect (e.g. Mistral, Cohere, Ollama, Azure, or an
> OpenAI-compatible proxy) need an explicit `provider/model` prefix like `mistral/mistral-large`.
> Bedrock falls in this category — the `bedrock/...` prefix above is what routes through AWS.

Every script here reads the model from `SCILINK_MODEL`, so you only set it once.

Quick check that your environment + credentials are set up (this only inspects env vars,
it doesn't make an LLM call):

```bash
python - <<'PY'
import os, scilink, litellm
model = os.environ.get("SCILINK_MODEL", "claude-opus-4-6")
env = litellm.validate_environment(model)
status = "READY" if env["keys_in_environment"] else f"MISSING {env['missing_keys']}"
print(f"scilink OK | model={model} | credentials: {status}")
PY
```

If you see `MISSING [...]`, export the named env var (e.g. `ANTHROPIC_API_KEY`) and re-run.

### Troubleshooting

- **`conda` not found** — close and reopen your terminal after installing Miniconda (on Windows, use the Anaconda Prompt).
- **`pip install` permission error** — make sure the environment is active: `conda activate scilink`.
- **PyTorch install is very slow** — normal (~2 GB); use a stable connection and be patient.

## Running

Each track folder has its own `README.md` with step-by-step instructions. Recommended Day-1 order:

1. `simulation_agents/` — start with `01_dft.py` (no cluster needed; generates inputs only — VASP by default, `--engine qe` for Quantum ESPRESSO)
2. your group's track (`analysis_agent/`, `curvefit_agent/`, or `bo_agent/`)

The active-learning loop in `simulation_agents/02_active_learning_dft.py` runs **fully offline**
(its Bayesian-optimization core needs no API key), so it's a safe place to start even before
credentials are handed out.
