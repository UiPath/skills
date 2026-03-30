# Low-Code Agent Setup Guide

> **Agent type: Low-code agents only.** Coded agents are set up with `pyproject.toml`, `uv sync`, and `uip codedagents new` — see [lifecycle/setup.md](../lifecycle/setup.md).

This guide explains how to set up a UiPath low-code agent project for local development, testing, and deployment using the `uip` CLI.

---

## Prerequisites

Before you begin, ensure the following tools are installed:

- **Python 3.11 or higher** — The agent runtime is Python-based even for low-code agents. Python must be available on your `PATH`.
- **`uip` CLI** — The UiPath CLI used for pulling, running, evaluating, and publishing agents. Install it via npm:
  ```bash
  npm install -g @uipath/cli
  ```
  Verify the installation:
  ```bash
  uip --version
  ```
  > **Note:** The Python `uipath` package (the agent runtime) is **not** installed manually. It is installed automatically when you run `uip codedagents setup`.
- **UiPath account credentials** — You need access to a UiPath Automation Cloud tenant. Authentication tokens are stored in `.env`.

---

## Two Paths to Get an `agent.json`

Every low-code agent is defined by a single `agent.json` file. There are two ways to obtain one.

### Path 1: Pull from Studio Web (Recommended)

Use this path when you have already designed an agent in **UiPath Studio Web Agent Builder** and want to work with it locally.

1. Open Studio Web and navigate to your agent in Agent Builder.
2. Publish or save the agent so it has a registered identity in Automation Cloud.
3. In your terminal, create a local directory and pull the agent definition:
   ```bash
   mkdir my-agent && cd my-agent
   uip codedagents pull
   ```
   The CLI will prompt you to select the tenant, folder, and agent. It downloads `agent.json` and an optional `bindings.json` into the current directory.
4. Verify the files were created:
   ```bash
   ls -1
   # agent.json
   # bindings.json   (if the agent has deployed resource bindings)
   ```

> **Note:** `uip codedagents pull` keeps your local `agent.json` in sync with Studio Web. Re-run it whenever the cloud definition changes.

---

### Path 2: Create `agent.json` from Scratch

Use this path when you want to author a brand-new agent entirely in code without using Studio Web first.

1. Create a project directory:
   ```bash
   mkdir my-agent && cd my-agent
   ```
2. Create `agent.json` manually. See the **Minimal Template** section below for a starting point, and consult [agent-json-reference.md](./agent-json-reference.md) for the full schema.
3. Optionally create a `.env` file with your credentials (see **Authentication** below).

---

## Minimal `agent.json` Template

The following is a minimal, working `agent.json` that you can copy and customise. All fields shown are required unless marked optional.

```json
{
  "version": "1.1.0",
  "name": "My Agent",
  "metadata": {
    "storageVersion": "44.0.0",
    "isConversational": false
  },
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant. Answer the user's request clearly and concisely.",
      "contentTokens": [
        { "type": "simpleText", "rawString": "You are a helpful assistant. Answer the user's request clearly and concisely." }
      ]
    },
    {
      "role": "user",
      "content": "{{task}}",
      "contentTokens": [
        { "type": "variable", "rawString": "input.task" }
      ]
    }
  ],
  "inputSchema": {
    "type": "object",
    "properties": {
      "task": { "type": "string", "description": "The task or question for the agent." }
    },
    "required": ["task"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "result": { "type": "string", "description": "The agent's response." }
    }
  },
  "settings": {
    "engine": "basic-v2",
    "model": "gpt-4.1-2025-04-14",
    "maxTokens": 16384,
    "temperature": 0,
    "maxIterations": 25
  },
  "resources": [],
  "features": []
}
```

For production agents with tools, context, or escalation, see [resources-reference.md](./resources-reference.md).

---

## No Virtual Environment Needed for Editing

Low-code agents do **not** require you to create or activate a Python virtual environment just to edit `agent.json`. You can open and modify the file in any editor directly.

However, a virtual environment **is** created automatically when you run the agent locally. The `uip codedagents setup` command bootstraps the Python runtime environment required to execute the agent:

```bash
uip codedagents setup --format json
```

Run this once per project (or after updating dependencies). It creates a `.venv` directory in your project folder with all necessary runtime packages.

> You do **not** need to call `uip codedagents setup` merely to edit `agent.json`. However, it **is** required before running the agent locally (`uip codedagents run`) or running evaluations (`uip codedagents eval`).

---

## `uip codedagents init` Generates Supporting Files

Running `uip codedagents init` on a low-code project reads `agent.json` and generates:
- **`entry-points.json`** — Mirrors `inputSchema`/`outputSchema` from `agent.json` in the standard entrypoint format used by Orchestrator and Studio Web.
- **`bindings.json`** — If not already present, creates an empty bindings file.

This step is **optional for local `run`** (the runtime reads schemas directly from `agent.json`), but **required before push/deploy** so that Orchestrator and Studio Web know the agent's I/O contract.

```bash
uip codedagents init
```

> **Note:** Studio Web generates `entry-points.json` automatically when you pull. You only need to run `uip codedagents init` manually if you created `agent.json` from scratch.

---

## No `pyproject.toml` Needed

Low-code agents do **not** use Python packaging. There is no `pyproject.toml`, no `setup.py`, and no need to define Python dependencies manually. The runtime dependencies are managed entirely by the `uip` toolchain.

If you see a `pyproject.toml` in a project, it likely belongs to a **coded agent** (Python-based). For low-code agents, ignore or delete it.

---

## No Framework Selection

Low-code agents use UiPath's built-in **ReAct engine** (`"engine": "basic-v2"`), which is powered by LangGraph under the hood. There is no framework selection step — the platform automatically builds a LangGraph StateGraph from your `agent.json` definition. You never interact with LangGraph directly.

---

## Directory Structure

A complete low-code agent project looks like this:

```
my-agent/
├── agent.json              ← Agent definition (THE agent — edit this file)
├── entry-points.json       ← I/O schema for Orchestrator (generated by init or Studio Web)
├── bindings.json           ← Resource bindings (maps resource names to Orchestrator paths)
├── project.uiproj          ← Project metadata (generated by init or Studio Web)
├── flow-layout.json        ← Visual canvas layout (Studio Web only, runtime ignores it)
├── .env                    ← Authentication tokens (never commit to source control)
├── .agent-builder/         ← Execution contract (auto-managed, do not edit)
├── resources/              ← Individual resource definition files (Studio Web only)
└── evaluations/            ← Evaluation datasets and custom evaluators
    ├── eval-sets/
    └── evaluators/
```

### File Descriptions

| File / Directory | Purpose |
|---|---|
| `agent.json` | The complete agent definition: model, prompts, input/output schemas, resources, features. This is the primary file to edit. |
| `entry-points.json` | I/O schema contract consumed by Orchestrator and Studio Web. Generated by `uip codedagents init` or Studio Web. |
| `bindings.json` | Maps logical resource names to actual Orchestrator folder paths and process names. Used for environment-specific overrides. |
| `project.uiproj` | Project type metadata (`ProjectType: "Agent"`). Generated by `uip codedagents pull` (from Studio Web) or by `uip codedagents init` when creating from scratch. |
| `flow-layout.json` | Visual node positions from the Studio Web canvas. Ignored by the runtime. |
| `.agent-builder/` | Copies of `agent.json`, `bindings.json`, `entry-points.json` used by the execution runtime. Auto-populated — do not edit directly. |
| `resources/` | Individual resource JSON files generated by Studio Web. The runtime reads resources from `agent.json`, not from this directory. |
| `.env` | Stores `UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, and other secrets. Never commit this file. |
| `evaluations/eval-sets/` | Evaluation input/expected-output pairs for `uip codedagents eval`. |
| `evaluations/evaluators/` | Evaluator configuration files (LLM judge, exact match, etc.). |

---

## Authentication

Create a `.env` file in the project root with the following variables:

```dotenv
UIPATH_URL=https://cloud.uipath.com/{org}/{tenant}
UIPATH_ACCESS_TOKEN=<your-personal-access-token>
UIPATH_FOLDER_PATH=<your-orchestrator-folder>
```

You can generate a Personal Access Token in **UiPath Automation Cloud → Preferences → Privacy and Security**.

---

## Running the Agent Locally

Once `agent.json` is in place and `.env` is configured:

```bash
# First-time runtime setup (only needed once)
uip codedagents setup --format json

# Generate entry-points.json (optional for local run, required before push/deploy)
uip codedagents init

# Run the agent with a test input
uip codedagents run agent.json '{"task": "Summarise the quarterly report."}'
```

---

## Publishing to Automation Cloud

Before deploying for the first time, register the agent in Studio Web and link your local project to it:

1. Open Studio Web at `https://cloud.uipath.com/{orgName}/studio_/projects` and create a new **Agent** project.
2. Copy the project ID from the URL or project settings.
3. Add `UIPATH_PROJECT_ID=<project-id>` to your `.env` file.
4. Push the local files to Studio Web:
   ```bash
   uip codedagents push
   ```
5. Then deploy to Orchestrator:
   ```bash
   uip codedagents deploy --my-workspace
   ```

This packages and uploads the agent to your personal workspace, making it available in Studio Web and for API invocation.

---

## Next Steps

- **Add tools and context:** See [resources-reference.md](./resources-reference.md) for all resource types.
- **Full schema reference:** See [agent-json-reference.md](./agent-json-reference.md) for every field.
- **Starter template:** Copy [../../assets/templates/agent.json](../../assets/templates/agent.json) as a project starting point.
