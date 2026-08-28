# Guardrails for Coded Agents

Add a **new** guardrail to a Python coded agent (LangChain/LangGraph) using **middleware** or **decorator** style. Derive its complete configuration from official documentation. If validating, diagnosing, or fixing an existing or misplaced guardrail, follow [guardrails-recommend.md § Validate Mode](guardrails-recommend.md) FIRST; this skill covers adding a new guardrail.

## Step 0 — Fetch Official Documentation

Do this FIRST—before reading files, running commands, or taking any other action. Call `WebFetch` twice:

1. Fetch `https://uipath.github.io/uipath-python/langchain/guardrails/`. Extract middleware classes, supported scopes, stage support, extra parameters, import paths, the “Choosing between patterns” comparison, and, when documented, `EscalateAction` parameters, scopes, and stages.
2. Fetch `https://uipath.github.io/uipath-python/core/guardrails/`. Extract built-in validator names, entity types per validator, available actions, and execution-stage constraints.

Use fetched documentation as the sole source of truth. Never rely on memory for middleware classes, scopes, stages, entity names or allowed values, or import paths. `Platform Availability` describes product-wide rollout, not tenant availability; use [Check Tenant Availability](#check-tenant-availability-mandatory-for-built-in-ai-validators).

Use the fetched LangChain page for `LogAction`, `BlockAction`, and `EscalateAction`, including the latter’s signature, scopes, and stages. If the fetched SDK docs do not expose `EscalateAction` or its constructor parameters, stop and report that the installed/published SDK documentation does not currently support HITL guardrail escalation. Never generate it from memory or this skill alone.

## Check Tenant Availability (mandatory for built-in AI validators)

For built-in AI validators—PII, harmful content, user prompt attacks, IP, and LLM as Judge—run:

```bash
uip agent guardrails list --output json
```

If the requested validator has `Status != "Available"`, tell the user and stop. Skip this check only for deterministic guardrails, which run locally without a backend dependency.

For `llm_as_judge`, also run:

```bash
uip agent guardrails llm-as-judge-models --output json
```

Use a returned `ModelId` for `model`; prefer a non-preview, small, fast model (Haiku / mini class). If no models are returned or the command fails because LLM Gateway access is unavailable, tell the user to configure a model in LLM Gateway or supply a model ID.

## BYO (bring-your-own) validators

A tenant-registered external provider (BYOG), such as Azure AI Content Safety or Databricks AI Guardrails, fulfills a validator. Registration is admin-side through Admin → AI Trust Layer → Guardrails Configurations or `uip guardrails byo-configurations create`; this skill wires an existing configuration into code.

Confirm every constructor signature against fetched SDK docs; do not invent arguments.

| Construct | Style | Ships in | Constraint |
|---|---|---|---|
| `UiPathByoGuardrailMiddleware` | middleware | `uipath_langchain.guardrails` only | LangChain/LangGraph only |
| `ByoValidator` | decorator | `uipath.platform.guardrails` (core), re-exported by `uipath_langchain.guardrails` | Framework-agnostic class |

BYO is not LangChain-only: the middleware is LangChain-only, while `ByoValidator` is core. Import according to [Imports Pattern](#imports-pattern). On frameworks without a published adapter, decorator/middleware use may silently no-op; invoke validators directly if needed.

Both coded styles emit `validatorType: "byo"` and `byoValidatorName: "<name>"`. Low-code `agent.json` instead keeps `validatorType` as the real validator id, such as `pii_detection`, and adds `byoValidatorName`; never put `validatorType: "byo"` in low-code `agent.json`.

Before wiring BYO:

1. Run:
   ```bash
   uip agent guardrails list --byo --output json
   ```
   Match the requested validator and use its `ByoValidatorName`. This is the only value code passes; never pass a connection id or guess the name.
2. Run:
   ```bash
   uip guardrails byo-configurations list --output json
   ```
   Confirm matching `ValidatorName` has `Enabled: true` and `ValidConnection: true`. Otherwise tell the user rather than wiring it. Runtime behavior may fail or silently fall back depending on `FallbackOnUiPath`. Admin remediation is covered by [uipath-platform § BYO Guardrail Configurations](/uipath:uipath-platform).
3. For middleware, read ids and allowed values from the matching discovery entry’s `Parameters` array. `validator_parameters` is optional connector-defined passthrough.

BYO middleware requires `validator_name`, `scopes`, and `action`; spread it with `*`:

```python
*UiPathByoGuardrailMiddleware(
    validator_name="<ByoValidatorName>",
    scopes=[GuardrailScope.AGENT],
    action=BlockAction(),
),
```

If `GuardrailScope.TOOL` is used, also pass `tools=[<tool object>]`. BYO has connector-defined capabilities, no static stage restriction, supports all stages, and middleware defaults to `PRE_AND_POST`.

BYO decorator usage:

```python
byog = ByoValidator("<ByoValidatorName>")

@guardrail(validator=byog, action=BlockAction())
def create_support_agent():
    return create_agent(model=llm, tools=[lookup_account_info])
```

For LangChain import from `uipath_langchain.guardrails`; otherwise import `BlockAction`, `ByoValidator`, and `guardrail` from `uipath.platform.guardrails`.

## Step 1 — Style Choice

If the user has not specified middleware or decorator, ask before generating code. Do not implement both unless explicitly requested. If asked to choose, use the “Choosing between patterns” table from the fetched `langchain/guardrails/` documentation.

## Step 2 — Read Agent Code

Use `Glob` / `Grep` to find the main Python file, looking for `create_agent`, `StateGraph`, or `@entrypoint`. Read it before editing. Determine:

- Whether `create_agent()` is direct or inside a factory.
- Available `@tool` functions for Tool scope.
- Whether an LLM factory exists for LLM-scope decorators.
- Existing guardrails, to avoid duplication.

## Imports Pattern

`uipath.platform.guardrails` provides the low-level `guardrail` decorator, `*Validator` / `*Middleware`, `*Action`, entity enums, and `GuardrailExecutionStage`. The decorator only wraps objects when a framework adapter is registered; without one it silently no-ops.

Importing `uipath_langchain.guardrails` registers the LangChain adapter as a side effect and re-exports relevant symbols:

| Agent framework | Import from | Detect by |
|---|---|---|
| LangChain / LangGraph | `uipath_langchain.guardrails` | `uipath-langchain` in `pyproject.toml`, or `from langchain...` / `from langgraph...` |
| Anything else | `uipath.platform.guardrails` | No `uipath-langchain` dependency or LangChain imports |

Before writing imports, read `pyproject.toml` dependencies and entrypoint imports. Detect `uipath-langchain`, `llama-index*`, `openai-agents`, and LangChain/LangGraph imports. If no framework matches, use `uipath.platform.guardrails`.

For LangChain/LangGraph, never import guardrail symbols only from `uipath.platform.guardrails`: they type-check but bypass adapter registration and silently no-op. Import `uipath_langchain.guardrails` even when importing `UiPathChat` from `uipath_langchain.chat`. For frameworks without an adapter, use the platform module, but check the SDK usage pattern and invoke validators directly if necessary.

Use only needed imports and merge them into the existing guardrail import block. Typical LangChain imports are from `uipath_langchain.guardrails`, with `GuardrailScope` from `uipath.core.guardrails`. Import `TaskRecipient` and `TaskRecipientType` from `uipath.platform.action_center.tasks` only when routing an escalation task.

## Middleware Style

Middleware classes are iterable; always spread each instance with `*` into `create_agent(..., middleware=[...])`. Add to an existing list or create one:

```python
agent = create_agent(
    model=llm,
    tools=[my_tool],
    middleware=[
        *SomeMiddlewareClass(name="...", action=...),
    ],
)
```

Follow fetched docs for class-specific parameters:

- TOOL scope requires `scopes=[GuardrailScope.TOOL]` and `tools=[<tool object>]`; never use a string.
- LLM or Agent scope uses `scopes=[GuardrailScope.LLM]` or `[GuardrailScope.AGENT]` and no `tools=`.
- Respect each class’s documented scope and stage.
- Fixed-stage middleware takes no `stage=`: `UiPathUserPromptAttacksMiddleware` and `UiPathPromptInjectionMiddleware` are PRE-only; `UiPathIntellectualPropertyMiddleware` is POST-only.
- Variable-stage middleware accepts `stage=` and defaults to `PRE_AND_POST` where documented: PII, harmful content, LLM-as-judge, deterministic, and BYO. Confirm this in fetched docs.
- `UiPathUserPromptAttacksMiddleware` and `UiPathPromptInjectionMiddleware` may omit `scopes`; they default to LLM and reject AGENT/TOOL.
- `scopes=` is required (omitting raises `TypeError: missing 1 required positional argument: 'scopes'`) for `UiPathIntellectualPropertyMiddleware`, PII, and harmful-content middleware. Intellectual property supports only LLM or AGENT, not Tool, and runs at POST.

Use only entity enum members and threshold values allowed by fetched documentation.

## Decorator Style

See [Core Guardrails](https://uipath.github.io/uipath-python/core/guardrails/) for full documentation. Respect documented scopes, stages, entities, thresholds, and parameters.

For Tool scope, place `@guardrail` above `@tool`; the topmost `@guardrail` runs first:

```python
@guardrail(
    validator=SomeValidator(...),
    action=BlockAction(),
    name="...",
    stage=GuardrailExecutionStage.PRE,
)
@tool
def my_tool(text: str) -> str:
    """Tool docstring."""
    ...
```

For LLM scope, create the LLM inside a named factory and decorate that factory. For Agent scope, put `create_agent(...)` inside a named factory and decorate the factory. Refactor direct module-level assignments or calls before decorating.

## Escalation action (human-in-the-loop)

`EscalateAction` is an action beside `LogAction` and `BlockAction`. On violation it suspends via `interrupt(CreateEscalation(...))`, creates a review task in a UiPath Action App, and resumes after a human Approves or Rejects. At PRE, approved `ReviewedInputs` may replace flagged content; at POST, `ReviewedOutputs` may replace it. Reject raises and terminates like `BlockAction`. Use fetched LangChain docs for exact parameters, scopes, and stages.

Use the same action in middleware or decorator style. The validator may be any supported validator, including deterministic `CustomValidator(...)`; only the validator—not `EscalateAction`—then requires AI-validator tenant availability.

### Action App prerequisite

Escalation requires a deployed Action App referenced by `app_name` and `app_folder_path`, and declared in `bindings.json`.

1. Run:
   ```bash
   uip solution resources list --kind App --search "<app-name>" --output json
   ```
   Filter `"Type": "Workflow Action"`; use `Name` and `Folder`. If absent, tell the user. If duplicate names occur across folders, ask which folder.
2. Pass the literal name and folder to `EscalateAction`; do not use environment variables.
3. When tenant/API access exists, verify the app contract. Required inputs are `GuardrailName`, `GuardrailDescription`, `TenantName`, `AgentTrace`, `Tool`, `ExecutionStage`, `ToolInputs`, `ToolOutputs`; outputs are `ReviewedInputs`, `ReviewedOutputs`, `Reason`; outcomes are `Approve`, `Reject`. If unavailable in a local smoke task, author structural code only when the user supplied the exact app name/folder and report that the deployed schema was not verified.
4. Sync `bindings.json` with [../../lifecycle/bindings-reference.md](../../lifecycle/bindings-reference.md). Do not hand-author coded-agent bindings ad hoc. The result must contain a `resource: "app"` entry. Reference examples are `samples/joke-agent/` and `samples/joke-agent-decorator/` in the uipath-langchain repo.

### Escalation UX

Under local `uip codedagent run`, a violation prints a `CreateEscalation` interrupt and pauses without a traceback. Resume with:

```bash
uip codedagent run <ENTRYPOINT> --resume
```

Approve resumes and applies optional reviewer edits; Reject raises `AgentRuntimeError` and terminates. Do not expect a block/traceback on the initial escalation violation.

## Verify Guardrails Are Actually Wired

Verification is mandatory after writing LangChain ML guardrails. Skip the entire section for deterministic guardrails (`UiPathDeterministicGuardrailMiddleware` / `CustomValidator`); grep-verify the class name and rule keyword are present.

After importing the agent module, run:

```bash
uv run python -c "import graph; from uipath.platform.guardrails.decorators._registry import _adapters; assert len(_adapters) >= 1, 'NO ADAPTER REGISTERED — guardrails will silently no-op; import from uipath_<framework>.guardrails (e.g. uipath_langchain.guardrails for LangChain agents)'; print('adapters:', len(_adapters))"
```

For a correctly decorated LangChain object, run an appropriate wrap check, such as:

```bash
uv run python -c "import graph; n = type(graph.llm).__name__; assert n == '_GuardedLLM', f'LLM is {n}, not _GuardedLLM — guardrail did not wrap it'; print('wrapped:', n)"
```

Tools should be `_GuardedTool`. If checks fail, first fix imports to `uipath_langchain.guardrails` or ensure that module is imported, then re-verify. Do not report the guardrail as added until wiring is confirmed.

For frameworks without an adapter, invoke the validator directly on a known-violating input and confirm it raises or logs. An authenticated smoke run is strongest: trigger a violation and confirm behavior. For `EscalateAction`, confirm suspension, `CreateEscalation`, task creation, and resume behavior—Approve continues, Reject terminates; do not expect a block.

## Block Action UX

`BlockAction` raises `AgentRuntimeError` on violation. Local `uip codedagent run` shows a traceback; deployed UiPath runtime renders the same guardrail-violation error. This is expected.

## Critical Rules

1. Always spread middleware with `*` into the list—never pass the object itself.
2. `@guardrail` must be above `@tool`; the topmost `@guardrail` runs first.
3. Tool-scoped middleware requires `tools=[<tool_reference>]`; pass the Python object, not a string.
4. Create LLM-scope decorator LLMs inside a factory function and decorate the factory.
5. Put Agent-scope `create_agent()` inside a factory function and decorate the factory.
6. Respect documentation scope and stage constraints; never use unsupported scopes or stages.
7. Add only used imports and merge them into existing guardrail imports.
8. LangChain / LangGraph imports must come from `uipath_langchain.guardrails`, not `uipath.platform.guardrails`; the former registers the adapter and the latter silently no-ops. See [Imports Pattern](#imports-pattern).
9. Verify wiring after writing: LangChain must have non-empty `_adapters` and decorated objects must be `_GuardedLLM` or `_GuardedTool`; frameworks without adapters require direct validator invocation. For `UiPathDeterministicGuardrailMiddleware` / `CustomValidator`, skip runtime checks and grep-verify the class name and rule keyword. See [Verify Guardrails Are Actually Wired](#verify-guardrails-are-actually-wired).
10. Entity and threshold values must match docs exactly; use enum members, not raw strings, and only allowed thresholds.
11. Deterministic guardrails run locally; no backend API call or tenant availability check is needed.
12. Read the agent code first and do not duplicate existing guardrails.
13. Do not delegate import-source decisions or guardrail authoring to a subagent. Fetch docs and write imports inline; subagents may select the no-op `uipath.platform.guardrails` path for LangChain agents.
14. `EscalateAction` must come from fetched SDK docs. If its class or constructor parameters are absent, stop and report that HITL escalation is unsupported by the current SDK docs/runtime.
15. `EscalateAction` requires a deployed Action App referenced by `app_name` and `app_folder_path`, declared as an `app` resource in `bindings.json`; discover it with `uip solution resources list --kind App`, resolve duplicate names by folder, use literal code values, and sync bindings with [../../lifecycle/bindings-reference.md](../../lifecycle/bindings-reference.md).
16. Verify the escalation app schema when tenant access is available using the inputs, outputs, and outcomes listed in [Action App prerequisite](#action-app-prerequisite). Otherwise report runtime readiness as unverified.
17. A HITL guardrail suspends; it does not block. It suspends via `interrupt(CreateEscalation(...))`; only Reject terminates. Verify suspension and task creation, not an immediate block.
18. BYO: pass the validator name and nothing else, and get that name from discovery—never memory. Use `ByoValidatorName` from `uip agent guardrails list --byo`; never pass a connection id. `ByoValidator` is a core class re-exported by `uipath_langchain.guardrails`, so BYO is not LangChain-only. Cross-check `Enabled` and `ValidConnection` with `uip guardrails byo-configurations list --output json` before wiring. See [BYO (bring-your-own) validators](#byo-bring-your-own-validators).