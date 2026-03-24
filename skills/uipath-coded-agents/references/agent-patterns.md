# Agent Patterns

Common implementation patterns for building UiPath coded agents, from simple functions to multi-agent orchestrations.

> **Note:** These patterns are general architectural concepts. The code examples use **LangGraph** and the **UiPath Python SDK**. The same patterns apply to LlamaIndex and OpenAI Agents — see their respective integration references.

## ⚠️ Before You Start: Setup Required

**IMPORTANT:** Before implementing any agent pattern, you must first set up your project directory and install dependencies. This is a prerequisite for all agent types.

See the **[Project Setup Guide](setup.md)** for:
- Creating a new project directory
- Scaffolding with `uv run uipath new`
- Installing dependencies with `uv sync`
- Defining Input/Output Pydantic models
- Configuring your agent with `uv run uipath init`
- Testing your agent with `uv run uipath run`

## Pattern Overview

| Pattern | When to Use | Key Components |
|---------|-------------|----------------|
| [Simple Direct](#simple-direct-agent) | Deterministic logic, no external calls | `@traced()`, Pydantic models |
| [SDK Integration](#sdk-integration-agent) | Platform service calls (assets, queues, jobs) | `UiPath()` client, service methods |
| [LangGraph Workflow](#langgraph-workflow-agent) | Multi-step LLM reasoning with routing | `StateGraph`, conditional edges, LLM chains |
| [Human-in-the-Loop](#human-in-the-loop-agent) | Requires human approval or review | `interrupt()`, `CreateTask`, Action Center |
| [RAG](#rag-agent) | Knowledge retrieval and Q&A | `ContextGroundingVectorStore`, retrieval chains |
| [Chat](#chat-agent) | Conversational agents with tools | `create_agent()`, tool bindings |
| [Multi-Agent Supervisor](#multi-agent-supervisor) | Complex tasks needing specialized sub-agents | Supervisor node, worker agents, routing |

---

## Simple Direct Agent

Minimal agent with synchronous or async logic, no LLM calls or external services. Best for deterministic transformations, calculations, and data processing.

**When to use:** Pure computation, data validation, format conversion, rule-based decisions.

```python
from pydantic import BaseModel
from uipath.tracing import traced

class Input(BaseModel):
    a: float
    b: float
    operator: str

class Output(BaseModel):
    result: float

@traced(name="calculate", span_type="tool")
def calculate(operator: str, a: float, b: float) -> float:
    match operator:
        case "+": return a + b
        case "-": return a - b
        case "*": return a * b
        case "/": return a / b if b != 0 else 0.0
        case _: raise ValueError(f"Unknown operator: {operator}")

@traced()
async def main(input: Input) -> Output:
    result = calculate(input.operator, input.a, input.b)
    return Output(result=result)
```

**Key points:**
- `@traced()` on `main` is required for Orchestrator visibility
- Use `@traced(name=..., span_type="tool")` on helper functions for granular traces
- Use `@mockable()` on functions calling external services to enable evaluation mocking

---

## SDK Integration Agent

Uses the `UiPath()` client to interact with platform services like assets, queues, jobs, and buckets.

**When to use:** Reading/writing Orchestrator assets, managing queues, triggering processes, uploading attachments.

```python
import os
from pydantic import BaseModel
from uipath.platform import UiPath
from uipath.tracing import traced

class Input(BaseModel):
    asset_name: str
    folder_path: str

class Output(BaseModel):
    value: str
    status: str

@traced()
async def main(input: Input) -> Output:
    client = UiPath()

    asset = client.assets.retrieve(
        name=input.asset_name,
        folder_path=input.folder_path,
    )

    return Output(
        value=str(asset.value),
        status="retrieved",
    )
```

**Key points:**
- `UiPath()` reads credentials from environment variables by default
- All services support `folder_path` and `folder_key` for folder targeting
- Every service method has an async variant with `_async` suffix
- See [SDK Services](sdk-services.md) for the full API reference

---

## LangGraph Workflow Agent

Multi-step agent using LangGraph's `StateGraph` with nodes, edges, and conditional routing. Supports LLM-powered decisions.

> **Important:** LangGraph agents require `uipath-langchain` as a dependency and use a different project structure than simple agents. See the LangGraph integration reference for project setup, `langgraph.json` configuration, and troubleshooting.

**When to use:** Classification workflows, multi-step reasoning, conditional branching based on LLM output.

```python
from pydantic import BaseModel
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage
from uipath_langchain.chat.models import UiPathAzureChatOpenAI

class GraphInput(BaseModel):
    message: str

class GraphOutput(BaseModel):
    label: str
    confidence: float

class GraphState(MessagesState):
    message: str
    label: str | None = None
    confidence: float | None = None

async def classify(state: GraphState) -> Command:
    llm = UiPathAzureChatOpenAI(max_retries=3)
    result = await llm.ainvoke(state["messages"])
    return Command(update={"label": "urgent", "confidence": 0.95})

def route(state: GraphState) -> str:
    if (state.get("confidence") or 0) >= 0.8:
        return END
    return "review"

builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
builder.add_node("classify", classify)
builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route)
graph = builder.compile()
```

**Key points:**
- Use `MessagesState` for agents that need conversation history
- `Command(update={...})` to update state from nodes
- Conditional edges for routing based on state values
- LangGraph agents get tracing automatically — no `@traced()` needed on graph nodes

---

## Human-in-the-Loop Agent

Extends a LangGraph workflow with `interrupt()` to pause execution and create an Action Center task for human review.

**When to use:** Approval workflows, escalation paths, human review of LLM output, compliance checks.

```python
from pydantic import BaseModel
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from uipath.platform.common import CreateTask

class GraphState(MessagesState):
    label: str | None = None
    approved: bool = False

async def wait_for_human(state: GraphState) -> Command:
    action_data = interrupt(
        CreateTask(
            app_name="review_app",
            title="Review classification result",
            data={"label": state["label"]},
            assignee="reviewer@company.com",
        )
    )
    approved = isinstance(action_data.get("Answer"), bool) and action_data["Answer"]
    return Command(update={"approved": approved})

def route_after_review(state: GraphState) -> str:
    return END if state["approved"] else "escalate"

builder = StateGraph(GraphState)
builder.add_node("classify", classify_node)
builder.add_node("human_review", wait_for_human)
builder.add_node("escalate", escalate_node)
builder.add_edge(START, "classify")
builder.add_edge("classify", "human_review")
builder.add_conditional_edges("human_review", route_after_review)
graph = builder.compile(checkpointer=MemorySaver())
```

**Key points:**
- `interrupt()` pauses the graph and creates an Action Center task via `CreateTask`
- A `checkpointer` (e.g., `MemorySaver()`) is required for interrupt/resume to work
- `CreateTask` fields: `app_name`, `title`, `data` (dict shown to reviewer), `assignee` (optional)
- The graph resumes when the human completes the action — return value comes from `interrupt()`

---

## RAG Agent

Retrieval-Augmented Generation using UiPath Context Grounding as a vector store with an LLM for answer synthesis.

**When to use:** Knowledge base Q&A, document search, grounded answers with source citations.

```python
from pydantic import BaseModel
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from uipath_langchain.vectorstores.context_grounding_vectorstore import (
    ContextGroundingVectorStore,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

class Input(BaseModel):
    query: str
    index_name: str
    k: int = 3

class Output(BaseModel):
    answer: str
    sources: list[str]

async def main(input: Input) -> Output:
    vectorstore = ContextGroundingVectorStore(index_name=input.index_name)
    retriever = vectorstore.as_retriever(search_kwargs={"k": input.k})

    prompt = ChatPromptTemplate.from_template(
        "Answer based on this context:\n{context}\n\nQuestion: {question}"
    )
    llm = UiPathAzureChatOpenAI(max_retries=3)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    docs = await vectorstore.asimilarity_search_with_score(
        query=input.query, k=input.k
    )
    answer = await chain.ainvoke(input.query)

    return Output(
        answer=answer,
        sources=[doc.metadata.get("source", "") for doc, _ in docs],
    )
```

**Key points:**
- `ContextGroundingVectorStore` connects to UiPath Context Grounding indexes
- Use `.as_retriever()` to integrate with LangChain's LCEL chains
- `UiPathAzureChatOpenAI` routes through UiPath's LLM Gateway
- Supports both sync (`invoke`) and async (`ainvoke`) retrieval

---

## Chat Agent

Conversational agent with tool access, built using LangGraph's `create_agent()` helper. Minimal boilerplate for tool-using chat agents.

**When to use:** Conversational assistants, tool-augmented chat, agents that need web search or API access.

```python
from pydantic import BaseModel
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent

class GraphInput(BaseModel):
    question: str

class GraphOutput(BaseModel):
    answer: str

system_prompt = """You are a helpful assistant that answers questions.
Use the search tool to find current information when needed."""

llm = UiPathAzureChatOpenAI()
tools = [TavilySearch(max_results=3)]
graph = create_react_agent(llm, tools=tools, prompt=system_prompt)
```

**Key points:**
- `create_react_agent()` handles the agent loop (reason → act → observe) automatically
- Pass any LangChain-compatible tools in the `tools` list
- The `prompt` parameter guides agent behavior and tool usage
- Supports any LangChain chat model (OpenAI, Anthropic, Azure, etc.)

---

## Multi-Agent Supervisor

A supervisor agent routes tasks to specialized worker agents, then synthesizes results. Each worker is an independent agent with its own tools and prompt.

**When to use:** Complex tasks requiring different expertise, divide-and-conquer workflows, research + code generation.

```python
from typing import Literal
from pydantic import BaseModel
from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph, MessagesState
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

members = ["researcher", "coder"]
options = members + ["FINISH"]

class Router(TypedDict):
    next: str  # One of: "researcher", "coder", "FINISH"

class State(MessagesState):
    next: str
    answer: str

class GraphInput(BaseModel):
    question: str

class GraphOutput(BaseModel):
    answer: str

def make_supervisor(llm):
    router_llm = llm.with_structured_output(Router)
    async def supervisor(state: State) -> dict:
        response = await router_llm.ainvoke(state["messages"])
        return {"next": response["next"]}
    return supervisor

llm = UiPathAzureChatOpenAI()
research_agent = create_react_agent(llm, tools=[search_tool], prompt="You research.")
code_agent = create_react_agent(llm, tools=[repl_tool], prompt="You write code.")

async def research_node(state: State):
    result = await research_agent.ainvoke(state)
    return {"messages": [HumanMessage(content=result["messages"][-1].content, name="researcher")]}

async def code_node(state: State):
    result = await code_agent.ainvoke(state)
    return {"messages": [HumanMessage(content=result["messages"][-1].content, name="coder")]}

def route_supervisor(state: State) -> str:
    match state.get("next", "FINISH"):
        case "researcher": return "researcher"
        case "coder": return "coder"
        case _: return END

builder = StateGraph(State, input=GraphInput, output=GraphOutput)
builder.add_node("supervisor", make_supervisor(UiPathAzureChatOpenAI()))
builder.add_node("researcher", research_node)
builder.add_node("coder", code_node)
builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_supervisor)
builder.add_edge("researcher", "supervisor")
builder.add_edge("coder", "supervisor")
graph = builder.compile()
```

**Key points:**
- The supervisor uses `with_structured_output(Router)` to decide which worker to call
- Workers return results as `HumanMessage` with a `name` so the supervisor can track who responded
- Workers loop back to the supervisor, which decides the next step or finishes
- Each worker is a full `create_react_agent()` with its own tools and prompt

---

## Common Building Blocks

- **Pydantic models** — Every agent defines `Input`/`Output` (or `GraphInput`/`GraphOutput`) as `BaseModel` subclasses. Run `uv run uipath init` after changing them.
- **`@traced()`** — Apply to `main` and key helpers. LangGraph agents get tracing automatically.
- **`@mockable()`** — Wrap functions calling external services to enable evaluation mocking.
- **Async** — All patterns support `async def main(...)`. SDK methods have `_async` variants.
