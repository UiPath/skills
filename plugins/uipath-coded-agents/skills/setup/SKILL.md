---
name: setup
description: Scaffold and initialize UiPath coded agent projects. Handles project creation, dependency installation, and entry point generation with uipath new, uv sync, and uipath init. Use when the user says "set up a new agent", "scaffold a project", "initialize a UiPath project", or "create a new coded agent project".
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# Setup UiPath Agent Project

Scaffold a new project or initialize an existing one for UiPath agent development.

## Quick Reference

```bash
# New project from scratch
mkdir my-agent && cd my-agent
# Copy pyproject.toml template, add framework dep if needed, then:
uv sync
uv run uipath new my-agent       # name is REQUIRED
uv run uipath init && rm -rf CLAUDE.md .agent .claude CLI_REFERENCE.md SDK_REFERENCE.md AGENTS.md REQUIRED_STRUCTURE.md

# Existing project — just generate entry points
uv run uipath init
```

## Documentation

- **[Project Setup Guide](references/setup.md)** — Complete setup walkthrough
  - Prerequisites (Python 3.11+, uv)
  - Choosing agent type (Simple, LangGraph, LlamaIndex, OpenAI Agents)
  - Creating and scaffolding projects
  - Running `uipath init` and what it generates
  - `uipath.json` structure and configuration
  - Simple function agent details (Input/Output models, project structure)

## Template

A `pyproject.toml` template is available in [assets/templates/pyproject.toml](assets/templates/pyproject.toml). Replace `{AGENT_NAME}` and `{AGENT_DESCRIPTION}` after copying.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `No entrypoints found in uipath.json` | Framework package not installed or config file missing | Ensure `uipath-langchain` (or equivalent) is in deps and `langgraph.json` exists |
| `NameError: name 'StateGraph' is not defined` | `uipath init` imports `main.py` but `langgraph` not installed | Run `uv sync` to install all dependencies before `uipath init` |
| `No solution found` for Python 3.10 | `requires-python` set too low | Set `requires-python = ">=3.11"` — UiPath SDK requires Python 3.11+ |
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |

## Additional Instructions

- **STOP: You must know which framework to use before running setup.** If no framework has been selected yet, ask the user to choose (Simple Function, LangGraph, LlamaIndex, or OpenAI Agents). The framework determines which dependency to add and what `uipath new` scaffolds.
- Read the [setup reference](references/setup.md) before making assumptions about project structure.
- **Use lazy LLM initialization** so `uipath init` works without auth. Never instantiate LLM clients at module level — create them inside functions/nodes.
- After changing Input/Output models, re-run `uv run uipath init` to regenerate schemas.
