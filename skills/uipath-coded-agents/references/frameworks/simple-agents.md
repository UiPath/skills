# Creating UiPath Agents

Guide to creating new UiPath agents with AI-powered business logic implementation.

## Initial Setup

Follow the [Project Setup Guide](setup.md) to create your project directory, scaffold with `uip codedagents new`, install dependencies, and authenticate. All subsequent commands use the `uip codedagents` CLI wrapper.

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

For multi-step LLM reasoning, conditional routing, or tool-calling with LangChain — use `graph.py` + `langgraph.json`. See `langgraph-integration.md`.

#### LlamaIndex Agent

For LlamaIndex-based workflows using `StartEvent`/`StopEvent` events and the `@step` decorator — use `main.py` + `llama_index.json`. See `llamaindex-integration.md`.

#### OpenAI Agents Agent

For lightweight agents using the OpenAI Agents SDK with tool calling and handoffs — use `main.py` + `openai_agents.json`. See `openai-agents-integration.md`.

## LLM Usage

The **UiPath LLM Gateway** provides access to Large Language Model capabilities for conversational AI, structured data extraction, and semantic search. It supports both OpenAI-compatible and UiPath's normalized API formats.

### Service Options

**UiPathOpenAIService** — For direct OpenAI API compatibility:
```python
from uipath.llm_gateway import UiPathOpenAIService

service = UiPathOpenAIService()
response = await service.chat_completions(messages=[
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "What is AI?"}
])
```

**UiPathLlmChatService** — For advanced enterprise features (tool calling, function calling):
```python
from uipath.llm_gateway import UiPathLlmChatService

service = UiPathLlmChatService()
response = await service.chat_completions(messages=messages)
```

### Structured Output with Pydantic

Extract structured data using Pydantic models:

```python
from pydantic import BaseModel

class Country(BaseModel):
    name: str
    capital: str

response = await service.chat_completions(
    messages=messages,
    response_format=Country
)
```

### Text Embeddings

Generate embeddings for semantic search:

```python
embedding = await service.embeddings("Hello, world!")
```

### Configuration

Control LLM behavior with these parameters:
- `temperature` (0-1): Controls randomness vs. determinism
- `max_tokens`: Response length limit (default: 4096)
- `top_p` and `top_k`: Diversity controls
- `frequency_penalty` and `presence_penalty`: Token repetition management

For detailed information, see the [UiPath LLM Gateway documentation](https://uipath.github.io/uipath-python/core/llm_gateway/).

### Step 3: Implement Business Logic

Describe your agent's functionality, then implement the main function (or graph nodes) with:
- Proper error handling
- UiPath SDK method calls (see [SDK Services](sdk-services.md))
- Input validation
- Output formatting

### Step 4: Generate Entry Points

Run `uip codedagents init` to generate `entry-points.json`, `uipath.json`, `bindings.json`, and documentation files. See the [Running uipath init](setup.md#running-uipath-init) section in Project Setup for details on entrypoint registration, auto-detection, and troubleshooting.

### Step 5: Create Smoke Evaluation Set

**Required.** Create `evaluations/eval-sets/smoke-test.json` with 2-3 basic test cases, then run `uip codedagents eval`. Use `ExactMatchEvaluator` for deterministic agents or `LLMJudgeOutputEvaluator` for LLM agents.

### Step 6: Deploy

When deploying: add author to `pyproject.toml`, bump version if re-deploying, then run `uip codedagents deploy --my-workspace`.

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
- If you require authentication, run `uip login --output json` then `uip login tenant set "<TENANT>" --output json`.
