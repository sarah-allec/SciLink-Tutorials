# SciLink-Tutorials

Hands-on materials for **[SciLink](https://github.com/ziatdinovmax/SciLink)**,
an open-source multi-agent platform for the physical sciences.

SciLink coordinates AI agents for **experiment planning**, **data analysis**,
and **simulation** — letting domain scientists compose closed-loop workflows
from literature-informed design through Bayesian-optimization-driven
next-experiment selection, all in a single Python environment.

## Tutorials

| Folder | Event | Topics |
|--------|-------|--------|
| [`mrs-2026/`](mrs-2026/) | MRS Spring 2026 — MT01 | Knowledge-grounded planning · UV-Vis Bayesian optimization · Spectroscopy analysis → DFT |
<!-- | [`example/`](example/) | — | Description | -->

Each folder is self-contained with its own README, data, and notebooks.

## Quick start

### Requirements

- Python ≥ 3.12
- An API key for a supported LLM provider (OpenAI, Anthropic, etc.)

### Install

```bash
pip install 'scilink[ui]'        # core + browser UI
```

Individual tutorials may list additional dependencies — check their READMEs.
