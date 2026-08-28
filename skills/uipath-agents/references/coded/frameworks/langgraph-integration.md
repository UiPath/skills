# LangGraph Integration Guide

Build LangGraph agents for UiPath. This guide covers scaffolding, structure, entrypoints, models, schemas, runtime behavior, and pitfalls.

## Scaffold and Structure

If no agent code exists, run:

```bash
mkdir my-agent && cd my-agent
uip codedagent new my-agent
```

Modify the generated `main.py`. For the LangGraph template, install `uipath-langchain`; install it first if a base template was generated.

Use `langgraph.json` for new or multi-graph projects:

```text
my-agent/
├── main.py               # Exports graph
├── langgraph.json        # Maps names to graph variables
├── pyproject.toml        # Includes uipath-langchain
├── .env
└── ...
```

```json
{
  "graphs": {
    "agent": "./main.py:graph"
  }
}
```

The key (`agent`) is used by `uip codedagent run agent`; the value is `file:variable`. The file may be `main.py` or `graph.py`, but the path must match.

For an existing UiPath project, use `uipath.json` with `functions`:

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/uipath",
  "runtimeOptions": {
    "isConversational": false
  },
  "packOptions": {
    "includeUvLock": true
  },
  "functions": {
    "graph": "main.py:graph"
  }
}
```

Both patterns require `graph` to be a compiled `StateGraph` or `CompiledStateGraph`.

## Dependencies

Every project needs:

```toml
[project]
name = "my-agent"
version = "0.0.1"
description = "My LangGraph agent"
requires-python = ">=3.11"
dependencies = [
    "uipath",
    "uipath-langchain",
]

[dependency-groups]
dev = [
    "uipath-dev",
]
```

Add model and tool dependencies as needed:

```toml
dependencies = [
    "uipath",
    "uipath-langchain",
    "langgraph>=1.0.4",
    "langchain-community",
]
```

`uipath-langchain` registers the LangGraph runtime factory used by `uip codedagent run`, `uip codedagent init`, and deployment.

## LLM Models

Use UiPath LLM classes instead of raw `langchain_openai.ChatOpenAI`; they route through the UiPath LLM Gateway for centralized management and billing. Instantiate them inside graph nodes or functions, never at module level: module-level construction can authenticate during `uip codedagent init` and fail. See [../lifecycle/build.md](../lifecycle/build.md) § Additional Instructions.

### `UiPathAzureChatOpenAI`

Use this `ChatOpenAI`-compatible Azure OpenAI passthrough client with UiPath authentication and Agent Units; no API key is needed:

```python
from uipath_langchain.chat.models import UiPathAzureChatOpenAI

# Inside a graph node:
llm = UiPathAzureChatOpenAI(
    model="gpt-4o-mini-2024-07-18",
    temperature=0.7,
    max_tokens=4000,
    timeout=30,
    max_retries=2
)
```

Pass the model identifier as a string. Run `uip codedagent list-models` to list tenant-available models. The class supports streaming, structured output, tool calling, LangChain agents, and RAG.

### `UiPathChat`

Use this normalized gateway client for multiple vendors:

```python
from uipath_langchain.chat.models import UiPathChat

llm = UiPathChat(
    model="gpt-4o-2024-11-20",
    temperature=0.5,
    max_tokens=2000
)
```

Supported examples include OpenAI (`gpt-4o-2024-11-20`, `o3-mini-2025-01-31`), Anthropic (`anthropic.claude-3-5-sonnet-20240620-v1:0`), and Google (`gemini-2.0-flash-001`). Availability depends on region and account; data residency can affect regional availability. `UiPathChat` supports multiple providers, custom streaming headers, and model switching.

Both classes support `temperature` (0-1, default 0.7), `max_tokens`, `timeout`, `max_retries` (default 2), `top_p`, `frequency_penalty`, and `presence_penalty`, plus `with_structured_output()` with Pydantic schemas:

```python
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    confidence: float

llm = UiPathAzureChatOpenAI()
structured_llm = llm.with_structured_output(Analysis)
raw_dict: dict = await structured_llm.ainvoke("Analyze: I love this product!")
result: Analysis = Analysis.model_validate(raw_dict)
```

Choose `UiPathAzureChatOpenAI` for cost-conscious general work; choose `UiPathChat` or `UiPathAzureChatOpenAI` for complex reasoning; choose `UiPathChat` for multi-vendor or specialized-domain models. Run `uip codedagent list-models` and pass the exact `model_name` available in the tenant.

## Define the Graph

Define Pydantic input and output models for `uip codedagent init` and deployment:

```python
from pydantic import BaseModel, Field

class GraphInput(BaseModel):
    query: str = Field(description="The user's question")
    max_results: int = Field(default=5, description="Max results to return")

class GraphOutput(BaseModel):
    answer: str = Field(description="The answer")
    sources: list[str] = Field(default_factory=list, description="Sources used")
```

Use `MessagesState` for conversation history, or `TypedDict`/`BaseModel` for simpler workflows:

```python
from langgraph.graph import MessagesState

class GraphState(MessagesState):
    query: str
    answer: str | None = None
    sources: list[str] | None = None
```

Build and export a variable named `graph` containing the compiled graph:

```python
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command

async def search(state: GraphState) -> Command:
    # ... your logic ...
    return Command(update={"answer": "result", "sources": ["url1"]})

builder = StateGraph(GraphState, input_schema=GraphInput, output_schema=GraphOutput)
builder.add_node("search", search)
builder.add_edge(START, "search")
builder.add_edge("search", END)
graph = builder.compile()
```

### Output Reducer Constraint

The UiPath runtime streams `updates` and overwrites final output with the last node’s update delta (`runtime.py`). Reducers accumulate state internally but do not make accumulated values appear in `--output-file` JSON or eval trajectories. Carry aggregates forward explicitly:

```python
return {"items": [*state.get("items", []), new_item]}
```

Alternatively, have the terminal node compute and emit the full aggregate.

## Tracing

The UiPath LangGraph runtime automatically traces graph nodes, LLM calls, and tool invocations. Do not add `@traced()` to graph nodes. Use it only for monitored helpers outside the graph:

```python
from uipath.tracing import traced

@traced(name="postprocess", span_type="tool")
async def postprocess(text: str) -> str:
    return text.strip().lower()
```

## Initialize and Run

Run:

```bash
uv sync
uip codedagent init
```

Initialization loads registered middleware, including the `uipath-langchain` LangGraph middleware. It checks `langgraph.json` first; without it, standard initialization checks `uipath.json` `functions`. The runtime imports the configured file, validates `graph`, and extracts schemas from the graph’s `input`/`output` annotations.

Troubleshoot as follows:

- **No function entrypoints found:** ensure `langgraph.json` has the correct `graphs` mapping, or `uipath.json` has a `functions` entry. Match the file path and variable exactly, such as `"./main.py:graph"`.
- **Import or authentication errors:** move `UiPathAzureChatOpenAI()` or `UiPathChat()` from module scope into a node or function:

  ```python
  # BAD — fails during uip codedagent init:
  llm = UiPathAzureChatOpenAI()

  # GOOD — lazy initialization inside a node:
  async def my_node(state):
      llm = UiPathAzureChatOpenAI()
      return await llm.ainvoke(state["messages"])
  ```

- **Schema not detected:** specify `input_schema=GraphInput, output_schema=GraphOutput` on `StateGraph`, and make both classes Pydantic `BaseModel` subclasses.

Run the configured entrypoint key:

```bash
# With langgraph.json
uip codedagent run agent '{"query": "What is Python?"}'

# With uipath.json functions (using the function name)
uip codedagent run graph '{"query": "What is Python?"}'
```

## Conversational Agents

For the cross-framework contract, `isConversational`, and local-run options, see `../capabilities/conversational-agents.md`.

Type the in-process `messages` field as `list[AnyMessage]` with the `add_messages` reducer:

```python
from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel

class State(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages] = []
```

`langgraph.graph.MessagesState` is equivalent. The wire envelope in `../capabilities/conversational-agents.md` § Wire Envelope becomes `messages`; the `uipath-langchain` runtime converts each `UiPathConversationMessage` dict to a LangChain `HumanMessage` before execution.

Use either:

- **Prebuilt ReAct:** import `create_agent` from `langchain.agents`; its input contract is already wired, so export its compiled graph.
- **Custom graph:** build any `StateGraph` consuming `messages`; its first node may perform deterministic validation or routing before an LLM call.

For local execution, see `../capabilities/conversational-agents.md` § Running Locally. Use `--keep-state-file` on every turn and follow § Wire Envelope for the `turn1.json` shape.

## Available Tools

| Tool | Import | Purpose |
|------|--------|---------|
| Process invocation | `uipath_langchain.agent.tools import create_process_tool` | Trigger UiPath processes |
| Escalation (HITL) | `uipath_langchain.agent.tools import create_escalation_tool` | Send to a human reviewer |
| Context search | `uipath_langchain.retrievers import ContextGroundingRetriever` | Search Context Grounding indexes |
| MCP tools | `uipath_langchain.agent.tools import open_mcp_tools` | Connect to MCP servers |

For Context Grounding in LangGraph, always use `ContextGroundingRetriever` from `uipath_langchain.retrievers`, not `sdk.context_grounding.search()` or `search_async()`. The LangChain retriever integrates with the graph pipeline and automatically generates the correct `index` binding. See [../capabilities/context-grounding.md](../capabilities/context-grounding.md) for examples.