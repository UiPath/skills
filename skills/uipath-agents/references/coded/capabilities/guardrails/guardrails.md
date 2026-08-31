# Guardrails for Coded Agents

Add guardrails to a Python coded agent (LangChain/LangGraph) in two styles: **middleware** or **decorator**.

> **The user tells you which guardrail to add. You derive the full list of available guardrails and their configuration from the official documentation — fetch it at the start of every task.**

> **Validating or fixing an EXISTING guardrail? Start elsewhere.** If the task is to check / diagnose whether a guardrail is configured correctly, or to fix a misplaced / misconfigured one (even if you will also edit code), follow [guardrails-recommend.md § Validate Mode](guardrails-recommend.md) FIRST — that workflow is mandatory for diagnosis. This page covers adding a **new** guardrail.

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

> **That authority covers shape, not availability.** These pages carry `Platform Availability` notes for features still rolling out (BYOG, LLM-as-judge). Those notes are product-wide, never a statement about the tenant in front of you — [Check Tenant Availability](#check-tenant-availability-mandatory-for-built-in-ai-validators) below is the only authority for that. A validator the docs describe as "not enabled on every tenant yet" can still be `Available` here; author it.

When available, the `langchain/guardrails/` page documents three actions — **`LogAction`**, **`BlockAction`**, and
**`EscalateAction`** (human-in-the-loop). Treat the fetched page as the source of truth for `EscalateAction`'s
parameters, supported scopes, and stages; the operational wiring it doesn't cover (the suspend->resume UX, the
Action-App prerequisite, `bindings.json`, recipient routing) is in [Escalation action (HITL)](#escalation-action-human-in-the-loop) below.

If the fetched SDK docs do **not** expose `EscalateAction` or its constructor parameters, stop and report that the
installed/published SDK documentation does not currently support HITL guardrail escalation. Do not generate
`EscalateAction` code from memory or from this operational section alone.

---

## Check Tenant Availability (mandatory for built-in AI validators)

For built-in AI validators (PII, harmful content, user prompt attacks, IP, LLM as Judge), confirm the validator is enabled on this tenant **before authoring** — run:

```bash
uip agent guardrails list --output json
```

If the requested validator has `Status != "Available"` → tell the user and stop. Actually adding one that is not entitled produces a guardrail that always fails.

**Skip this step only for deterministic guardrails** — they run locally with no backend dependency.

> **LLM as Judge also requires LLM Gateway.** If the target is `llm_as_judge`, discover the models available on this tenant — run:
>
> ```bash
> uip agent guardrails llm-as-judge-models --output json
> ```
>
> Use a `ModelId` from the returned list for the `model` parameter. Prefer a non-preview model; a small, fast model (Haiku / mini class) is a sound judge default. If the command returns no models or fails (no LLM Gateway access), tell the user and ask them to configure a model in their LLM Gateway or supply a model ID.

---

## BYO (bring-your-own) validators

A validator can be fulfilled by a tenant-registered **external** provider (a "BYOG" configuration — e.g. Azure AI Content Safety, Databricks AI Guardrails) instead of UiPath's own built-in implementation. Registration is admin-side — Admin → AI Trust Layer → Guardrails Configurations, or `uip guardrails byo-configurations create` (see [uipath-platform § BYO Guardrail Configurations](/uipath:uipath-platform)); this section covers wiring an already-registered BYOG configuration into agent code.

**Same rule as [Step 0](#step-0--fetch-official-documentation): confirm the constructor signature against the fetched SDK docs before writing code, and never invent arguments.** The two constructs below exist today; if a future fetch shows one missing or renamed, follow the fetched page and say so rather than writing what's here from memory.

### Which construct exists where

| Construct | Style | Ships in | Notes |
|---|---|---|---|
| `UiPathByoGuardrailMiddleware` | middleware | `uipath_langchain.guardrails` **only** | LangChain/LangGraph agents only — there is no framework-agnostic middleware. |
| `ByoValidator` | decorator | `uipath.platform.guardrails` (**core**), re-exported by `uipath_langchain.guardrails` | Framework-agnostic class, so BYO is **not** LangChain-only. |

> **BYO is not LangChain-only** — a common wrong inference, because the core SDK docs page historically omitted `ByoValidator`. The class is in core. What *is* LangChain-only is the middleware.
>
> The usual [Imports Pattern](#imports-pattern) rule still governs which module you import from: a LangChain agent imports from `uipath_langchain.guardrails` (adapter registration — see Critical Rule 8), everything else from `uipath.platform.guardrails`. And on a framework with no published adapter, the decorator carries the same silent-no-op risk it does for every other validator — that caveat belongs to the decorator *mechanism*, not to BYO.

**Wire format** — both coded styles emit `validatorType: "byo"` plus `byoValidatorName: "<name>"`. The only field shared with low-code is `byoValidatorName`: a low-code `agent.json` pins the same BYOG configuration by adding `byoValidatorName` while keeping `validatorType` = the real validator id (e.g. `pii_detection`). `validatorType: "byo"` is the coded SDK wire format — never write it in a low-code `agent.json`.

Discovery steps (in addition to the fetched docs):

1. Confirm a BYOG configuration exists for the desired validator and get its identifying value:
   ```bash
   uip agent guardrails list --byo --output json
   ```
   Read `ByoValidatorName` from the matching entry — the validator name is the **only** value the code passes; it is unique across the tenant, and the platform resolves the underlying connection server-side from the stored configuration. Do not pass a connection id, and never guess or fabricate the name.
2. Before wiring it in, cross-check the configuration's health on the admin side:
   ```bash
   uip guardrails byo-configurations list --output json
   ```
   Confirm `Enabled: true` and `ValidConnection: true` for the matching `ValidatorName`. A disabled configuration or a broken connection means the guardrail will fail at runtime (or silently fall back, depending on `FallbackOnUiPath`) — tell the user rather than wiring it in anyway. The admin-side fix (re-enable via `update <id> --enabled`, repoint the connection via `update <id> --connection-id`) is covered by [uipath-platform § BYO Guardrail Configurations](/uipath:uipath-platform).

### BYO middleware (LangChain only)

`validator_name`, `scopes`, and `action` are all required. `validator_parameters` is optional passthrough — BYO parameter schemas are connector-defined, so read the ids and allowed values from that entry's `Parameters` array in the discovery output rather than guessing. Spread with `*` like every other middleware.

```python
from uipath_langchain.guardrails import (
    BlockAction,
    UiPathByoGuardrailMiddleware,
)
from uipath.core.guardrails import GuardrailScope

*UiPathByoGuardrailMiddleware(
    validator_name="my-pii-guardrail",   # ByoValidatorName from `guardrails list --byo`
    scopes=[GuardrailScope.AGENT],
    action=BlockAction(),
),
```

For Tool scope, pass the tool objects as usual:

```python
*UiPathByoGuardrailMiddleware(
    validator_name="my-pii-guardrail",
    scopes=[GuardrailScope.TOOL],
    action=BlockAction(),
    tools=[lookup_account_info],   # required whenever TOOL is in scopes
),
```

### BYO decorator (any framework)

The validator name is the **first positional argument**; `parameters` is keyword-only. Scope comes from the decorated target (`@tool` → Tool, LLM factory → Llm, agent factory → Agent), exactly as for the built-in validators.

```python
from uipath_langchain.guardrails import BlockAction, ByoValidator, guardrail

byog_pii = ByoValidator("my-pii-guardrail")

@guardrail(validator=byog_pii, action=BlockAction())
def create_support_agent():
    return create_agent(model=llm, tools=[lookup_account_info])
```

On a non-LangChain framework the same code works with `from uipath.platform.guardrails import BlockAction, ByoValidator, guardrail` — subject to the adapter caveat above.

**Stages:** BYO validator capabilities are connector-defined and can't be known statically, so no stage restriction is applied — all stages are supported, and the middleware defaults to `PRE_AND_POST`.

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
    BlockAction, LogAction, EscalateAction,
    PIIValidator, PIIDetectionEntity, PIIDetectionEntityType,
    HarmfulContentValidator, HarmfulContentEntity, HarmfulContentEntityType,
    UserPromptAttacksValidator,
    GuardrailExecutionStage,
    # ...only the names you actually use
)
from uipath.core.guardrails import GuardrailScope
# Only when routing an EscalateAction task to a specific reviewer:
from uipath.platform.action_center.tasks import TaskRecipient, TaskRecipientType
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

### LLM- / Agent-scoped middleware

Pass `scopes=[GuardrailScope.LLM]` or `[GuardrailScope.AGENT]`. No `tools=`.

```python
*SomeMiddlewareClass(
    name="...",
    scopes=[GuardrailScope.LLM],   # or GuardrailScope.AGENT
    action=...,
),
```

`scopes` is required on most middleware. Exceptions: LLM-only validators (`UiPathUserPromptAttacksMiddleware`, `UiPathPromptInjectionMiddleware`) make `scopes` optional — it defaults to LLM. Passing `scopes=[GuardrailScope.LLM]` and omitting it are equivalent; AGENT/TOOL are rejected.

### Stage is fixed by the validator — no `stage=` on middleware

Middleware classes for the **fixed-stage** validators take no `stage` argument: `UiPathUserPromptAttacksMiddleware`, `UiPathPromptInjectionMiddleware` (both PRE-only) and `UiPathIntellectualPropertyMiddleware` (POST-only). Passing `stage=` to those raises `TypeError` — their stage is a property of the validator, not a choice.

> Validators whose stage genuinely varies **do** accept `stage=` on the middleware (defaulting to `PRE_AND_POST`) — PII, harmful content, LLM-as-judge, deterministic, and BYO. Confirm against the fetched `langchain/guardrails/` page for the validator you're wiring rather than assuming either way.

For BYO middleware specifically, see [BYO (bring-your-own) validators](#byo-bring-your-own-validators).

### Intellectual property (output-only) middleware

> **`scopes=` is REQUIRED** on `UiPathIntellectualPropertyMiddleware` (and on PII / harmful-content middleware). It has no default — omitting it raises `TypeError: missing 1 required positional argument: 'scopes'`. Always pass `scopes=[GuardrailScope.LLM]` or `[GuardrailScope.AGENT]` (Tool not supported).

```python
from uipath_langchain.guardrails import (
    BlockAction,
    UiPathIntellectualPropertyMiddleware,
    IntellectualPropertyEntityType,
)
from uipath.core.guardrails import GuardrailScope

*UiPathIntellectualPropertyMiddleware(
    name="Intellectual property",
    scopes=[GuardrailScope.LLM],   # REQUIRED — LLM or AGENT; Tool not supported
    action=BlockAction(),
    entities=[
        IntellectualPropertyEntityType.TEXT,
        IntellectualPropertyEntityType.CODE,
    ],
),
```

Runs at POST (checks the LLM's output) — fixed by the validator, not a parameter.

---

## Decorator Style — Code Patterns

Full documentation and examples: [Core Guardrails](https://uipath.github.io/uipath-python/core/guardrails/)

For a bring-your-own (BYOG) validator, see [BYO (bring-your-own) validators](#byo-bring-your-own-validators) — `ByoValidator` slots into the same `@guardrail(validator=..., action=...)` shape as the built-ins.

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

## Escalation action (human-in-the-loop)

`EscalateAction` is a third action (beside `LogAction` / `BlockAction`) that turns a violation into a **human
review step**: it suspends the run via `interrupt(CreateEscalation(...))`, creates a review task in a UiPath
**Action App**, and resumes when a human **Approves** (optionally editing the flagged content — the reviewer's
`ReviewedInputs` at PRE / `ReviewedOutputs` at POST is substituted back) or **Rejects** (raises → terminates,
like `BlockAction`). Get the exact parameters / supported scopes / stages from the fetched
`langchain/guardrails/` page; this section is the operational wiring that page doesn't cover.

**The same `EscalateAction` works in both styles** — pass it as the `action`:

```python
# Middleware (no stage= — fixed by the validator)
*UiPathPIIDetectionMiddleware(
    name="PII escalation",
    scopes=[GuardrailScope.AGENT],
    action=EscalateAction(
        app_name="Guardrail.Escalation.Action.App",
        app_folder_path="Shared",
        # optional — route the task; default assignment otherwise
        recipient=TaskRecipient(type=TaskRecipientType.EMAIL, value="reviewer@example.com"),
    ),
    entities=[PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5)],
),

# Decorator — identical action, on a @tool / LLM factory / agent factory
@guardrail(
    validator=PIIValidator(entities=[PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5)]),
    action=EscalateAction(app_name="Guardrail.Escalation.Action.App", app_folder_path="Shared"),
    name="PII escalation",
    stage=GuardrailExecutionStage.PRE,
)
def create_my_agent(): ...
```

`EscalateAction` is **action-only** — it works with any validator, including deterministic
`CustomValidator(...)` rules (no AI-validator / tenant dependency for the validator itself).

### Prerequisite — the Action App must exist and be declared in `bindings.json`

Unlike Block/Log, escalation needs a **deployed Action App** in the tenant, referenced by `app_name` +
`app_folder_path`. This is the **correct design** (not env vars):

1. Discover the deployed app: `uip solution resources list --kind App --search "<app-name>" --output json`
   (filter `"Type": "Workflow Action"`); note its `Name` and `Folder`. If it isn't deployed, tell the user — the
   escalation fails at runtime otherwise. If multiple deployed Workflow Action apps share the same `Name` in
   different folders, ask which folder to use.
2. Pass those literal values to `EscalateAction(app_name=..., app_folder_path=...)`.
3. Verify the app exposes the guardrail escalation action-schema contract before claiming it is runtime-ready:
   inputs `GuardrailName`, `GuardrailDescription`, `TenantName`, `AgentTrace`, `Tool`, `ExecutionStage`,
   `ToolInputs`, `ToolOutputs`; outputs `ReviewedInputs`, `ReviewedOutputs`, `Reason`; outcomes `Approve`,
   `Reject`. If tenant/API access is unavailable in a local smoke task, author the structural code only when the
   user supplied the exact app name/folder, and report that the deployed app schema was not verified.
4. Sync the project's **`bindings.json`** with the code using
   [../../lifecycle/bindings-reference.md](../../lifecycle/bindings-reference.md). Coded-agent bindings are derived
   from resource-bearing code and must not be hand-authored ad hoc. The result must include a `resource: "app"`
   entry so Studio/deploy can resolve and override the Action App (locally the literals are used). Canonical
   examples: `samples/joke-agent/` (middleware) and `samples/joke-agent-decorator/` (decorator) in the
   uipath-langchain repo — each ships a `bindings.json` with the escalation app and the literal
   `app_name`/`app_folder_path` in code.

### Escalation Action UX

`EscalateAction` does **not** raise on violation (unlike `BlockAction`) — it **suspends** the run. Under local
`uip codedagent run` a violation prints a `CreateEscalation` interrupt and the run pauses (no traceback); resume after
acting on the task in Action Center:

```bash
uip codedagent run <ENTRYPOINT> --resume
```

On resume: **Approve** continues (with the reviewer's optional edit applied); **Reject** raises
`AgentRuntimeError` and terminates the run. This is expected — distinct from `BlockAction` (immediate raise) and
`LogAction` (logs, no control-flow change).

---

## Verify Guardrails Are Actually Wired (mandatory after writing for LangChain ML guardrails)

> **Skip this entire section for deterministic guardrails** (`UiPathDeterministicGuardrailMiddleware` / `CustomValidator`). They run inline with no adapter registration and no LLM wrapping. For deterministic guardrails, grep-verify the class name and rule keyword are present in the file — that is sufficient.

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
>
> **For an `EscalateAction` guardrail the outcome differs:** a violating input **suspends** the run with a `CreateEscalation` interrupt — it does not block. Verify by confirming the run suspends and a review task is created, then that `uip codedagent run <ENTRYPOINT> --resume` continues after Approve / terminates after Reject. Don't expect a block/traceback.

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
9. **Verify wiring at runtime after writing (LangChain only)** — confirm the LangChain adapter is registered (`len(_adapters) >= 1`) and the decorated object is wrapped (`type(llm).__name__ == "_GuardedLLM"`, or `_GuardedTool` for tools). `ast.parse` is not enough; a silently-unwrapped guardrail passes syntax but never fires. For frameworks without an adapter, this wrap-check does not apply — invoke the validator directly to confirm it runs. **For `UiPathDeterministicGuardrailMiddleware` / `CustomValidator`, skip both runtime checks — grep-verify the class name and rule keyword are present in the file instead.** See [Verify Guardrails Are Actually Wired](#verify-guardrails-are-actually-wired-mandatory-after-writing-for-langchain-ml-guardrails).
10. **Entity/threshold values must match the docs exactly** — use enum member names, not raw strings; use only allowed threshold values.
11. **Deterministic guardrails run locally** — no backend API call, no tenant availability check needed.
12. **Do not duplicate existing guardrails** — read the agent code first and skip if the same guardrail is already configured.
13. **Do not delegate the import-source decision (or guardrail authoring) to a subagent.** A dispatched subagent does not carry this skill's context and will report the module where the symbols physically live (`uipath.platform.guardrails`) — the no-op path for LangChain agents (Rule 8). It looks authoritative and silently overrides the correct `uipath_langchain.guardrails` choice. Fetch the docs and write the imports inline, where this skill's import rule still applies.
14. **`EscalateAction` must come from the fetched SDK docs** — if the docs do not expose the class or constructor parameters, stop and report that HITL guardrail escalation is not available in the current SDK docs/runtime. Never invent the class, import path, or arguments.
15. **`EscalateAction` requires a deployed Action App** referenced by `app_name` + `app_folder_path` and declared as an `app` resource in **`bindings.json`** — discover it with `uip solution resources list --kind App`, resolve duplicate names by folder, pass the literal name/folder in code (not env vars), and sync bindings with [../../lifecycle/bindings-reference.md](../../lifecycle/bindings-reference.md). Route the task with `TaskRecipient` when the user names a reviewer. See [Escalation action (HITL)](#escalation-action-human-in-the-loop).
16. **Verify the escalation app schema when tenant access is available** — the app must expose the guardrail review inputs/outputs/outcomes listed in the prerequisite section. If the schema cannot be verified in a local smoke task, say that runtime readiness is unverified.
17. **A HITL guardrail suspends, it doesn't block.** On violation `EscalateAction` suspends via `interrupt(CreateEscalation(...))`; it terminates **only on Reject** (Approve resumes). Verify by confirming the run suspends + a task is created — never expect a "block" for an escalation guardrail (Rule for the [verification step](#verify-guardrails-are-actually-wired-mandatory-after-writing-for-langchain-ml-guardrails)).
18. **BYO: pass the validator name and nothing else, and get that name from discovery — never from memory.** `ByoValidatorName` comes from `uip agent guardrails list --byo`; there is **no connection-id argument** in either construct (the platform resolves the connection server-side from the configuration). Pick the construct by style, not by framework: `UiPathByoGuardrailMiddleware` is LangChain-only, while `ByoValidator` is a **core** class (`uipath.platform.guardrails`) re-exported by `uipath_langchain.guardrails` — so **BYO is not LangChain-only**, and a subagent or stale doc claiming otherwise is wrong. Import per Rule 8 regardless. Cross-check `Enabled`/`ValidConnection` via `uip guardrails byo-configurations list` before wiring one in. See [BYO (bring-your-own) validators](#byo-bring-your-own-validators).
