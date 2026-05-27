# LLM & Agents 101

A short, hands-on intro to how LLMs and "agents" work through the API.
Three small Python scripts, about 30-45 minutes, no prior AI experience
needed. The model is **Anthropic's Claude**, called directly through the
Anthropic API.

**The one idea to take away:** an "agent" is not a smarter AI -- it is the
same LLM API call, wrapped in a loop, with tools.

## What's inside

| File | What it teaches |
|------|-----------------|
| `1_llm_basics.py`       | An LLM call is just a function: messages in, text out. |
| `2_expert_plan.py`      | A *system prompt* turns the model into a domain expert with a fixed output layout -- shown for materials science, chemistry, and physics. |
| `3_agent_with_tools.py` | *Tools + a loop = an agent.* The model picks the right microscopy analysis tool for each question. |
| `tools.py`              | The analysis tools used by Lesson 3. |
| `make_synthetic_data.py`| Regenerates the synthetic data files (already included). |
| `data/`                 | Synthetic sample data: a particle image and an EDS spectrum. |
| `check_setup.py`        | Run this first -- it confirms your setup works. |

Each script sets `MODEL` as a constant at the top -- change it in one place
per file if your workshop uses a different model id.

## Setup (about 10 minutes)

You need **VS Code**, **miniconda** (which provides Python), and an
**Anthropic API key** (ask the workshop organizer for one, or get your own
at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)).

Work through these steps in order -- all of them happen inside VS Code.

**1. Open the project.** In VS Code: File -> Open Folder, and choose the
`llm-agents-101-anthropic` folder *itself* -- not a folder above it. The
scripts use paths like `data/...` that are relative to this folder. When
VS Code offers the recommended **Python extension**, install it.

**2. Open the integrated terminal.** In the menu bar: Terminal -> New
Terminal. You'll run every command below in this terminal.

**3. Create the environment and install the packages:**

```
conda create -n agent-101 python=3.12
conda activate agent-101
pip install -r requirements.txt
```

**4. Select the interpreter.** Press Cmd+Shift+P (Ctrl+Shift+P on Windows),
run *Python: Select Interpreter*, and choose the `agent-101` environment.
This is the most common thing to get wrong -- a `ModuleNotFoundError` almost
always means the wrong interpreter is selected.

**5. Add your Anthropic API key.** Copy `.env.example` to `.env`, then open
`.env` in the editor and paste your key in:

```
cp .env.example .env                # Windows: copy .env.example .env
```

The `.env` file holds one value:

- `ANTHROPIC_API_KEY` -- your Anthropic API key (starts with `sk-ant-`).

**6. Check that everything works:**

```
python check_setup.py
```

You should see `SUCCESS: All set!`. If not, the message tells you what to fix.

## Run the lessons

In the same terminal, run the lessons in order -- each builds on the one
before:

```
python 1_llm_basics.py
python 2_expert_plan.py
python 3_agent_with_tools.py
```

If the prompt ever stops showing `(agent-101)`, run
`conda activate agent-101` to get the environment back.

Keep each script open in the editor while it runs: the files are short and
heavily commented, and **reading the code is the lesson.**
