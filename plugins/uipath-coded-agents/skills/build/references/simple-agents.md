# Creating UiPath Agents

Guide to creating new UiPath agents with AI-powered business logic implementation.

## Initial Setup

Follow the [Project Setup Guide](setup.md) to create your project directory, scaffold with `uipath new`, install dependencies, and authenticate. All subsequent commands use `uv run` to run within the project's virtual environment.

## Workflow

### Step 1: Define Agent Schema

Specify:
- **Agent Description**: What does this agent do?
- **Input Fields**: Name, type, description for each input parameter
- **Output Fields**: Name, type, description for each output

The schemas should be written as pydantic types.

### Step 2: Choose Agent Type

#### Simple Function Agent (no LLM framework)

For agents with deterministic logic, SDK calls, or simple processing — use `main.py` with a traced function:

```python
from pydantic import BaseModel, Field
from uipath.tracing import traced

class Input(BaseModel):
    # Generated fields based on your inputs
    pass

class Output(BaseModel):
    # Generated fields based on your outputs
    pass

@traced()
async def main(input: Input) -> Output:
    """Your agent's business logic implementation."""
    # AI-implemented logic will go here
    pass
```

#### LangGraph Agent

For multi-step LLM reasoning, conditional routing, or tool-calling with LangChain — use `graph.py` + `langgraph.json`. See the **[LangGraph Integration Guide](/uipath-coded-agents:langgraph)** for project structure, dependencies, LLM models, and complete examples.

#### LlamaIndex Agent

For LlamaIndex-based workflows using `StartEvent`/`StopEvent` events and the `@step` decorator — use `main.py` + `llama_index.json`. See the **[LlamaIndex Integration Guide](/uipath-coded-agents:llamaindex)** for project structure, dependencies, LLM models, and complete examples.

#### OpenAI Agents Agent

For lightweight agents using the OpenAI Agents SDK with tool calling and handoffs — use `main.py` + `openai_agents.json`. See the **[OpenAI Agents Integration Guide](/uipath-coded-agents:openai-agents)** for project structure, dependencies, LLM models, and complete examples.

> **Note:** Each integration guide is self-contained. It covers everything from pyproject.toml to running the agent. You don't need to read this page for integration agents — go directly to the relevant guide.

### Step 3: Implement Business Logic

Describe your agent's functionality, then implement the main function (or graph nodes) with:
- Proper error handling
- UiPath SDK method calls (see [SDK Services](sdk-services.md))
- Input validation
- Output formatting

### Step 4: Generate Entry Points

Run `uv run uipath init` to generate `entry-points.json`, `uipath.json`, `bindings.json`, and documentation files. See the [Running uipath init](setup.md#running-uipath-init) section in Project Setup for details on entrypoint registration, auto-detection, and troubleshooting.

### Step 5: Create Smoke Evaluation Set

**This step is required.** Every agent must have a basic smoke evaluation set to verify it works. Create `evaluations/eval-sets/smoke-test.json` with 2-3 simple test cases covering the happy path.

See [Evaluation Sets](evaluations/evaluation-sets.md) for the file format and [Evaluators Guide](evaluations/evaluators/README.md) for available evaluators. Choose evaluators based on agent type:
- **Deterministic agents** → `ExactMatchEvaluator`
- **LLM/Natural language agents** → `LLMJudgeOutputEvaluator` or `ContainsEvaluator`

### Step 6: Run Evaluations

Run the smoke evaluation set to verify the agent works:

```bash
uv run uipath eval
```

All test cases should pass before proceeding. If any fail, fix the agent and re-run.

### Step 7: Deploy

When the user requests deployment:

1. **Add author** to `pyproject.toml` if not already present. Ask the user for their name and email:
   ```toml
   [project]
   authors = [{ name = "User Name", email = "user@example.com" }]
   ```

2. **Bump version** in `pyproject.toml`. Increment the patch version (e.g. `0.0.1` → `0.0.2`), or ask the user what version to set.

3. **Deploy**:
   ```bash
   uv run uipath deploy
   ```

See [Deployment](deployment.md) for details on pack, publish, and invoke workflows.

## Generated Template Details

The created agent will include:
- Pydantic models for Input and Output based on your schema
- UiPath SDK initialization
- `@traced()` decorator for monitoring
- Function signature with type hints

## Important Notes

- All agents are automatically traced for monitoring and debugging
- Input/output fields are strongly typed with Pydantic
- The agent works globally and can call any UiPath SDK services
- Generated `entry-points.json` enables integration with UiPath Cloud
- If you require authentication at any point, use `uv run uipath auth` to authenticate with UiPath. See the [Authentication guide](/uipath-coded-agents:authentication) for details.
