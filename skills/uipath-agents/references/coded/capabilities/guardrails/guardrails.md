# Guardrails for Coded Agents

Add guardrails to a Python coded agent (LangChain/LangGraph) in two styles: **middleware** or **decorator**.

> **The user tells you which guardrail to add. You derive the full list of available guardrails and their configuration from the official documentation — fetch it at the start of every task.**

---

## Step 0 — Fetch Official Documentation

**Do this FIRST — before reading any files, running any commands, or taking any other action.** Call `WebFetch` twice to retrieve current guardrail documentation:

1. **`https://uipath.github.io/uipath-python/langchain/guardrails/`**
   Extract: middleware classes, their supported scopes, stage support, extra parameters, and correct import paths.

2. **`https://uipath.github.io/uipath-python/core/guardrails/`**
   Extract: built-in validator names, entity types per validator, available actions, execution stage constraints.

**Use the fetched content as the sole source of truth.** Never rely on memory for:
- Which middleware classes exist
- Which scopes or stages a guardrail supports
- Entity type names or their allowed values
- Import paths

---

## Optional: Check Tenant Availability

For built-in AI validators (PII, harmful content, user prompt attacks, IP), optionally confirm the validator is enabled on this tenant:

```bash
uip agent guardrails list --output json
```

If the requested validator has `Status != "Available"` → tell the user and stop.

**Skip this step for deterministic guardrails** — they run locally with no backend dependency.

---

## Step 1 — Style Choice

If the user has not specified **middleware** or **decorator**, ask before generating any code. Do not implement both unless explicitly asked.

Use the comparison table from the fetched `langchain/guardrails/` docs (the "Choosing between patterns" section) to help the user decide if they ask.

---

## Step 2 — Read Agent Code

Use `Glob` / `Grep` to find the main Python file (look for `create_agent`, `StateGraph`, or `@entrypoint`). Read it to understand:

- Whether `create_agent()` is called directly or inside a factory function
- Which `@tool` functions exist (needed for Tool-scoped guardrails)
- Whether a separate LLM factory function exists (needed for LLM-scope decorator guardrails)
- Which guardrails are already present (avoid duplicating)

---

## Imports Pattern

### How adapter registration works (read first)

`uipath.platform.guardrails` ships the *low-level* `guardrail` decorator, `*Validator` / `*Middleware` classes, `*Action` classes, entity enums, and `GuardrailExecutionStage`. The decorator on its own only wraps the decorated function if a **framework adapter** is registered for the object the factory returns (a LangChain `UiPathChat`, a LlamaIndex agent, etc.). Without an adapter, the decorated factory returns the plain object, and **every guardrail silently no-ops — no error, no log.**

Today the only published framework adapter is the **LangChain** one. Importing `uipath_langchain.guardrails` registers it as a side effect; the import path is also a re-export of the same names available in `uipath.platform.guardrails`, so consumers see one set of symbols either way.

| Agent framework | Import guardrail symbols from | Detect by |
|---|---|---|
| **LangChain / LangGraph** (UiPathChat, `create_agent`) | `uipath_langchain.guardrails` | `uipath-langchain` in `pyproject.toml`, `from langchain...` / `from langgraph...` in source |
| **Anything else** (LlamaIndex, OpenAI Agents, plain Python, custom orchestration) | `uipath.platform.guardrails` — the framework-agnostic SDK | No `uipath-langchain` dep / no LangChain imports |

For a LangChain agent, **import from `uipath_langchain.guardrails`, not `uipath.platform.guardrails`.** Both modules expose the same names, so platform imports type-check, parse, and run with no error — but they bypass the LangChain adapter and the decorator/middleware never wraps the LLM/tool/agent, so every guardrail silently no-ops. This was the demo2 root cause for a LangGraph agent that imported from `uipath.platform.guardrails`.

For frameworks that have no UiPath adapter yet (LlamaIndex, OpenAI Agents, etc.), the platform module is the correct source for validators, the `guardrail` decorator, action classes, and enums — these are framework-agnostic. Be aware that without a framework adapter, the decorator/middleware mechanism cannot auto-wrap that framework's LLM/tool objects, so guardrails-via-decorator may silently no-op there too; for those frameworks you may need to invoke validators directly rather than rely on factory decoration. Check the platform SDK page for the framework-agnostic usage pattern.

### Detect the framework before writing imports

Before writing the import line, identify the framework by reading the agent code and `pyproject.toml`:

1. Read `pyproject.toml` `dependencies` for `uipath-langchain`, `llama-index*`, `openai-agents`, etc.
2. Read the entrypoint file's existing imports (`from langchain...`, `from llama_index...`, `from agents...`).
3. Pick the matching row from the table above. If none match (rare — plain Python with no adapter), use `uipath.platform.guardrails`.

### Worked example — LangChain / LangGraph

```python
from uipath_langchain.guardrails import (
    guardrail,
    BlockAction, LogAction,
    PIIValidator, PIIDetectionEntity, PIIDetectionEntityType,
    HarmfulContentValidator, HarmfulContentEntity, HarmfulContentEntityType,
    UserPromptAttacksValidator,
    GuardrailExecutionStage,
    # ...only the names you actually use
)
```

❌ `from uipath.platform.guardrails import guardrail, PIIValidator, ...` in a LangChain agent — type-checks but the LangChain adapter never registers; guardrails silently no-op.
❌ Importing only `from uipath_langchain.chat import UiPathChat` without ever importing `uipath_langchain.guardrails`.

> **Doc-source note:** the `core/guardrails/` SDK page shows `uipath.platform.guardrails.*` paths — that is the canonical *platform* layer, correct only for the no-framework case. For framework agents, use the framework's own SDK guardrails page (`langchain/guardrails/`, `llamaindex/guardrails/`, etc.) as the import source and trust the table above.

Only add the imports you actually use. Merge new names into any existing `from uipath_<framework>.guardrails import (...)` block — do not duplicate the import statement.

---

## Middleware Style — Code Patterns

### Adding to `create_agent()`

Each middleware class is **iterable** — unpack it with `*` into the `middleware=[...]` list:

```python
agent = create_agent(
    model=llm,
    tools=[my_tool],
    middleware=[
        *SomeMiddlewareClass(
            name="...",
            action=...,
            # class-specific params from docs
        ),
    ],
)
```

If `create_agent()` already has a `middleware=[...]` argument, add new entries to the existing list. If there is no `middleware` argument yet, add `middleware=[...]` as a new keyword argument.

### TOOL-scoped middleware

When the fetched docs show a middleware supports TOOL scope, it requires passing `tools=[...]`:

```python
*SomeMiddlewareClass(
    name="...",
    scopes=[GuardrailScope.TOOL],
    action=...,
    tools=[my_tool],  # required for TOOL scope — Python object, not string
),
```

---

## Decorator Style — Code Patterns

Full documentation and examples: [Core Guardrails](https://uipath.github.io/uipath-python/core/guardrails/)

### Tool scope — decorate the `@tool` function

Place `@guardrail` **above** `@tool`:

```python
@guardrail(
    validator=SomeValidator(...),
    action=...,
    name="...",
    stage=GuardrailExecutionStage.PRE,
)
@tool
def my_tool(text: str) -> str:
    """Tool docstring."""
    ...
```

### LLM scope — decorate the LLM factory function

The LLM **must** be created inside a named factory function. Decorate the factory:

```python
@guardrail(
    validator=SomeValidator(...),
    action=...,
    name="...",
    stage=GuardrailExecutionStage.PRE,
)
def create_llm():
    return UiPathChat(model="gpt-4o-2024-08-06")

llm = create_llm()
```

If the code assigns the LLM directly (e.g. `llm = UiPathChat(...)`), refactor it into a factory function first, then decorate.

### Agent scope — decorate the agent factory function

Wrap `create_agent(...)` in a named factory function, then decorate it:

```python
@guardrail(
    validator=SomeValidator(...),
    action=...,
    name="...",
    stage=GuardrailExecutionStage.PRE,
)
def create_my_agent():
    return create_agent(model=llm, tools=[my_tool], system_prompt=SYSTEM_PROMPT)

agent = create_my_agent()
```

If `create_agent()` is called directly at module level (not in a function), wrap it in a factory function first.

---

## Verify Guardrails Are Actually Wired (mandatory after writing)

**Syntactically valid ≠ active.** Because importing from the wrong module bypasses the framework adapter and makes guardrails silently no-op (see [Imports Pattern](#imports-pattern)), `ast.parse` passing tells you nothing about whether a single guardrail will ever fire. After writing, prove the wiring at runtime.

**1. An adapter is registered for the framework.** Each framework's `uipath_<framework>.guardrails` module registers its adapter as an import side effect. After importing the agent module, the registry must be non-empty:

```bash
uv run python -c "import graph; from uipath.platform.guardrails.decorators._registry import _adapters; assert len(_adapters) >= 1, 'NO ADAPTER REGISTERED — guardrails will silently no-op; import from uipath_<framework>.guardrails (e.g. uipath_langchain.guardrails for LangChain agents)'; print('adapters:', len(_adapters))"
```

**2. The decorated object is actually wrapped.** For a LangChain agent, a correctly-wired LLM factory returns a `_GuardedLLM`, and a `@tool` decoration returns a `_GuardedTool`:

```bash
uv run python -c "import graph; n = type(graph.llm).__name__; assert n == '_GuardedLLM', f'LLM is {n}, not _GuardedLLM — guardrail did not wrap it'; print('wrapped:', n)"
```

If either check fails, the most likely cause is importing guardrail symbols from `uipath.platform.guardrails` instead of `uipath_langchain.guardrails`, or never importing `uipath_langchain.guardrails` at all. Fix the import source and re-verify — do not report the guardrail as added until both checks pass.

For non-LangChain frameworks, there is no published adapter yet, so the decorator/middleware mechanism does not produce a `_Guarded*` wrap. Verify by invoking the validator directly on a known-violating input and confirming it raises / logs.

> A smoke run that deliberately triggers a violation (e.g. feed a PII-bearing input and confirm it blocks) is the strongest verification when the environment is authenticated against the tenant.

---

## Block Action UX

`BlockAction` enforces a violation by **raising** `AgentRuntimeError` (surfaced from the adapter's `_apply_*` hooks). Under local `uipath run` this appears as a Python traceback ending in e.g. `AgentRuntimeError: PII detected: Email: ... (total: 1 detections)`. When deployed, the UiPath runtime renders the same exception as a guardrail-violation error. This is expected behavior, not a bug.

---

## Critical Rules

1. **Always spread middleware with `*`** into the list — never pass the object itself.
2. **Decorator order matters**: `@guardrail` must be above `@tool`; the **topmost** `@guardrail` (first in source) runs first when the function is called.
3. **Tool-scoped middleware requires `tools=[<tool_reference>]`** — pass the Python object, not a string.
4. **LLM-scope decorator**: LLM must be inside a factory function; decorate the factory.
5. **Agent-scope decorator**: `create_agent()` must be inside a factory function; decorate the factory.
6. **Respect scope and stage constraints from the docs** — each middleware class has specific allowed scopes and stages; never apply a guardrail at a scope or stage the docs say it doesn't support.
7. **Only add imports you use** — merge new names into any existing `from uipath_langchain.guardrails import (...)` block (LangChain) or `from uipath.platform.guardrails import (...)` block (every other framework).
8. **For LangChain / LangGraph agents, import guardrail symbols from `uipath_langchain.guardrails`, not `uipath.platform.guardrails`.** Both expose the same names, but only `uipath_langchain.guardrails` registers the LangChain adapter as an import side effect; without it the decorator/middleware never wraps the LLM/tool/agent and every guardrail silently no-ops with no error or log. For any other framework (LlamaIndex, OpenAI Agents, plain Python), import from `uipath.platform.guardrails` — no framework adapter is published yet. See [Imports Pattern](#imports-pattern).
9. **Verify wiring at runtime after writing (LangChain only)** — confirm the LangChain adapter is registered (`len(_adapters) >= 1`) and the decorated object is wrapped (`type(llm).__name__ == "_GuardedLLM"`, or `_GuardedTool` for tools). `ast.parse` is not enough; a silently-unwrapped guardrail passes syntax but never fires. For frameworks without an adapter, this wrap-check does not apply — invoke the validator directly to confirm it runs. See [Verify Guardrails Are Actually Wired](#verify-guardrails-are-actually-wired-mandatory-after-writing).
10. **Entity/threshold values must match the docs exactly** — use enum member names, not raw strings; use only allowed threshold values.
11. **Deterministic guardrails run locally** — no backend API call, no tenant availability check needed.
12. **Do not duplicate existing guardrails** — read the agent code first and skip if the same guardrail is already configured.
