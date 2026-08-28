# LlamaIndex Integration Guide

Build LlamaIndex agents for UiPath, including scaffolding, entrypoints, models, workflows, and platform integrations.

## Scaffolding and Project Structure

If no agent code exists, run:

```bash
mkdir my-agent && cd my-agent
uip codedagent new my-agent
```

The generated project includes `main.py` (workflow definition exporting `agent`), `llama_index.json` (workflow configuration), `pyproject.toml`, `.env`, and generated files. `pyproject.toml` must include `uipath-llamaindex`.

`llama_index.json` maps an entrypoint name to `file:variable`:

```json
{
  "workflows": {
    "agent": "main.py:workflow"
  }
}
```

The key is used with `uip codedagent run agent`; the file and variable must match exactly. The variable may have any name but must be an instantiated `Workflow`.

## Dependencies

Use:

```toml
[project]
name = "my-agent"
version = "0.1.0"
description = "My LlamaIndex agent"
requires-python = ">=3.11"

dependencies = [
    "uipath-llamaindex",
]

[dependency-groups]
dev = [
    "uipath-dev",
]
```

Add provider dependencies as needed:

```toml
dependencies = [
    "uipath-llamaindex",
    "llama-index-llms-openai>=0.6.10",
    "llama-index-llms-bedrock>=0.3.0",
    "llama-index-llms-google-genai>=0.8.0",
]
```

`uipath-llamaindex` registers the runtime factory required by `uip codedagent run`, `uip codedagent init`, and deployment.

## LLM Models

Use UiPath wrappers, not raw `OpenAI()`, so calls use the UiPath LLM Gateway for model management and billing. Instantiate clients inside a `@step`, or through an instance-level lazy property—not at module level or as `Workflow` class attributes, which evaluate during import before authentication is configured.

```python
from uipath_llamaindex.llms import UiPathOpenAI, OpenAIModel

# Inside a @step:
llm = UiPathOpenAI(model=OpenAIModel.GPT_4O_2024_11_20)
```

`UiPathOpenAI` uses UiPath authentication and the passthrough endpoint (Azure OpenAI API format), so no API key is needed. Use singular `OpenAIModel`; `GeminiModel` and `BedrockModel` are also available from `uipath_llamaindex.llms`. Run `uip codedagent list-models` to list tenant-available models. See [../lifecycle/build.md](../lifecycle/build.md) § Additional Instructions for the full instantiation rule.

## Workflow Definition

Use typed `StartEvent` and `StopEvent` subclasses for input and output, and `Event` subclasses for intermediate data. A `StartEvent` subclass defines the input schema; a `StopEvent` subclass defines the output schema. Async `@step` methods receive one event and return another. LlamaIndex connects steps by event type, starts on a `StartEvent`, and ends on a returned `StopEvent`.

```python
from llama_index.core.workflow import StartEvent, StopEvent, Event, Workflow, step
from uipath_llamaindex.llms import UiPathOpenAI

class QueryEvent(StartEvent):
    query: str

class AnswerEvent(StopEvent):
    answer: str

class IntermediateEvent(Event):
    processed_query: str

class MyAgent(Workflow):
    @step
    async def process_query(self, ev: QueryEvent) -> IntermediateEvent:
        return IntermediateEvent(processed_query=ev.query.strip().lower())

    @step
    async def generate_answer(self, ev: IntermediateEvent) -> AnswerEvent:
        response = await UiPathOpenAI().acomplete(
            f"Answer this question: {ev.processed_query}"
        )
        return AnswerEvent(answer=str(response))

workflow = MyAgent(timeout=60, verbose=False)
```

Export an instantiated `Workflow`, and make its variable match `llama_index.json` (for example, `main.py:workflow`).

## Tracing

`uipath-llamaindex` includes `openinference-instrumentation-llama-index`, which automatically traces workflow steps. Do not add `@traced()` to steps. Use it only for helpers outside the workflow:

```python
from uipath.tracing import traced

@traced(name="postprocess", span_type="tool")
async def postprocess(text: str) -> str:
    return text.strip().lower()
```

## Initialization and Running

Run:

```bash
uv sync
uip codedagent init
```

Initialization loads registered middleware through Python entry points. The `uipath-llamaindex` middleware detects `llama_index.json`, imports the configured Python file, validates the workflow variable, and extracts schemas from `StartEvent`/`StopEvent` subclasses.

Troubleshoot:

- **"No function entrypoints found":** ensure `llama_index.json` exists, its `"workflows"` mapping is correct (for example, `"main.py:agent"`), and `uipath-llamaindex` is installed; run `uv sync`.
- **Import errors:** initialization imports the file. Avoid module-level side effects such as API calls or heavy initialization. Instantiate LLMs inside each `@step` or through an instance-level lazy property, never as a class attribute.
- **Schema not detected:** use typed custom `StartEvent` and `StopEvent` subclasses. Plain `StartEvent`/`StopEvent` use default schemas.

Run the agent with:

```bash
uip codedagent run agent '{"query": "What is Python?"}'
```

The entrypoint name comes from the `"workflows"` key.

## Conversational Agents

For the cross-framework contract, including `isConversational` and local-run options, see `../capabilities/conversational-agents.md`.

The workflow input must be a `StartEvent` with one `user_msg: str` field. The runtime extracts inline text from the wire envelope's `contentParts` and passes `user_msg`; the workflow does not process `role` or `contentParts`:

```python
from llama_index.core.workflow import StartEvent

class ChatStartEvent(StartEvent):
    user_msg: str
```

Choose one:

- **Prebuilt agent:** use `AgentWorkflow.from_tools_or_functions(...)` from `llama_index.core.agent.workflow`; `user_msg` is wired automatically and export the workflow instance from the entry point.
- **Custom workflow:** use any `Workflow` subclass whose first step accepts a `StartEvent` with `user_msg: str`; that step may deterministically validate or route before an LLM call.

For local execution, see `../capabilities/conversational-agents.md` § Running Locally for the `--keep-state-file` flag, required on every turn, and § Wire Envelope for the `turn1.json` shape.

## UiPath Platform Integration

### Context Grounding (RAG)

Use the supplied primitives rather than raw `sdk.context_grounding.search()` / `search_async()`. They return LlamaIndex `NodeWithScore` objects, integrate with synthesizers and tools, and declare `index_name` plus `folder_path` at one call site—the shape required by the `index` binding in [../lifecycle/bindings-reference.md](../lifecycle/bindings-reference.md). `index` bindings have no virtual fallback; the index must exist in Orchestrator before `uip codedagent push`.

| Primitive | Import | Use |
|---|---|---|
| `ContextGroundingQueryEngine` | `uipath_llamaindex.query_engines` | Retrieval plus LLM synthesis, or an index exposed as a `QueryEngineTool`; its constructor requires `response_synthesizer` and has no default. |
| `ContextGroundingRetriever` | `uipath_llamaindex.retrievers` | Deterministic RAG: retrieve passages in a `@step`, then synthesize with your own prompt and LLM. |

Both accept `index_name`, `folder_path` (or `folder_key`), and `number_of_results` (default `10`). Always pass `folder_path`, including for an index in the execution folder resolved from authentication; omitting it can prevent correct `index` binding. Instantiate them inside a `@step`, never at module level.

Construct a query engine's synthesizer explicitly:

```python
from llama_index.core.response_synthesizers import get_response_synthesizer
from uipath_llamaindex.llms import UiPathOpenAI
from uipath_llamaindex.query_engines import ContextGroundingQueryEngine

# Inside a @step:
query_engine = ContextGroundingQueryEngine(
    index_name="my_knowledge_base",
    folder_path="Shared",
    response_synthesizer=get_response_synthesizer(llm=UiPathOpenAI()),
)
response = await query_engine.aquery(ev.question)
```

Expose it as a tool when needed:

```python
from llama_index.core.tools import QueryEngineTool, ToolMetadata

tools = [QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="knowledge_base",
        description="Search the knowledge base for information",
    ),
)]
```

For deterministic RAG, retrieve in a step and synthesize with the UiPath LLM:

```python
from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step
from uipath_llamaindex.llms import UiPathOpenAI
from uipath_llamaindex.retrievers import ContextGroundingRetriever

class QuestionEvent(StartEvent):
    question: str

class AnswerEvent(StopEvent):
    answer: str

class RagAgent(Workflow):
    @step
    async def answer(self, ev: QuestionEvent) -> AnswerEvent:
        retriever = ContextGroundingRetriever(
            index_name="my_knowledge_base",
            folder_path="Shared",
            number_of_results=5,
        )
        nodes = await retriever.aretrieve(ev.question)
        if not nodes:
            return AnswerEvent(answer="No relevant passages found in the knowledge base.")
        passages = "\n\n".join(n.node.get_content() for n in nodes)
        response = await UiPathOpenAI().acomplete(
            "Answer the question using ONLY the passages below. "
            "If they do not answer it, say so.\n\n"
            f"Passages:\n{passages}\n\nQuestion: {ev.question}"
        )
        return AnswerEvent(answer=str(response))

workflow = RagAgent(timeout=60)
```

### Human-in-the-Loop

Use `Context.wait_for_event` with `HumanResponseEvent` and `InputRequiredEvent`:

```python
from llama_index.core.workflow import Context, HumanResponseEvent, InputRequiredEvent

@step
async def human_review(self, ctx: Context, ev: ReviewEvent) -> ApprovedEvent:
    response = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id="review_request",
        waiter_event=InputRequiredEvent(
            prefix="Please review this result. Approve? (yes/no)"
        ),
    )
    approved = response.response.strip().lower() == "yes"
    return ApprovedEvent(approved=approved)
```

### Process Invocation

```python
from uipath_llamaindex.models import InvokeProcessEvent, WaitJobEvent

@step
async def invoke_process(self, ev: TriggerEvent) -> WaitJobEvent:
    return InvokeProcessEvent(
        process_name="MyProcess",
        input_arguments={"data": ev.data},
    )
```

## FunctionAgent

For agents without custom workflow steps, use `FunctionAgent`:

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool
from uipath_llamaindex.llms import UiPathOpenAI

def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for information."""
    return f"Results for: {query}"

def build_workflow() -> FunctionAgent:
    tools = [FunctionTool.from_defaults(fn=search_knowledge_base)]
    return FunctionAgent(
        tools=tools,
        llm=UiPathOpenAI(),
        system_prompt="You are a helpful assistant. Use tools to find information.",
    )
```

`FunctionAgent` uses the default input `{"user_msg": "your question"}` and returns the agent's response string. Apply the same UiPath LLM lazy-initialization rule when adapting this pattern.

## Next Steps

- **[Agent Patterns](agent-patterns.md)** — Architecture patterns with full code examples
- **[SDK Services](../capabilities/sdk-services.md)** — Use UiPath platform services in workflow steps
- **[Tracing](../capabilities/tracing.md)** — Advanced tracing for helper functions outside the workflow
- **[Deployment](../lifecycle/deployment.md)** — Package and publish the LlamaIndex agent