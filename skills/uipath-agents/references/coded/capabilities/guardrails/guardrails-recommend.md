# Guardrail Recommendation and Validation — Coded Agents

This reference covers two workflows for Python coded agents (LangChain/LangGraph):
- **Recommend**: identify guardrails to add.
- **Validate**: assess existing guardrails for correctness, actionability, and relevance.

Use live data: `uip agent guardrails catalog` for recommendation metadata, `uip agent guardrails list` for tenant availability and parameter/scope constraints, and live UiPath Python SDK docs (`WebFetch`) for mapping catalog `validator_id` values to Python middleware and Validator classes. Never hardcode validator fit, class names, enum members, or import paths.

> This file covers WHEN to add guardrails and WHY. For exact Python patterns (middleware spread with `*`, decorator placement, factory refactors), always read [guardrails.md](guardrails.md) before editing agent code.

## Step 0 — Fetch Catalog, Available Validators, and SDK Docs (MANDATORY — do this before any analysis)

In **Recommend mode**, run all three fetches. In **Validate mode**, SDK docs are authoritative and sufficient for an existing validator's scope/stage fix; still run catalog and list for relevance and entitlement cross-checks, though they are not a hard prerequisite for that fix.

**Required first operation in both modes:** run `WebFetch` on `https://uipath.github.io/uipath-python/core/guardrails/` before catalog calls, project inspection, analysis, or edits. Do not consider the work grounded until it completes.

SDK docs are authoritative for shape, never availability. Their `Platform Availability` notes are product-wide, including BYOG and LLM-as-judge rollout, not tenant facts. Only `uip agent guardrails list` determines tenant availability.

### Catalog (cacheable — 30-minute TTL)

Run:

```bash
python3 -c "
import os, time
cache = '.guardrails-catalog-cache.json'
if os.path.exists(cache) and (time.time() - os.path.getmtime(cache)) < 1800:
    print('CACHE_HIT')
else:
    print('CACHE_MISS')
"
```

On `CACHE_HIT`, read `.guardrails-catalog-cache.json`. On `CACHE_MISS`, run and save:

```bash
uip agent guardrails catalog --output json > .guardrails-catalog-cache.json
```

Inspect the saved JSON. If it contains `"Code": "GuardrailCatalogUnavailable"`, surface the message and stop; do not guess. The CLI writes structured success and error JSON to stdout, so the redirect captures errors; do not add `2>&1`. The cache is `.guardrails-catalog-cache.json` in the working directory; add it to `.gitignore` if one exists.

### Guardrails list (NEVER cached — tenant-specific)

Run fresh every time:

```bash
uip agent guardrails list --output json
```

Build `{ validatorId: status }` from the `Data` array, but disambiguate by `(Validator, IsByo)`, not `Validator` alone. Built-in and BYO entries can share `Validator`; BYO entries have `IsByo: true` and may carry `ByoValidatorName`, `ByoConnectionId`, and `ByoConfigurationId`. Recommend only entries whose `Status == "Available"`; mention `Unauthorised` entries but do not add them, and skip absent entries.

The catalog contains all platform guardrails and rich metadata; the list contains only tenant-accessible guardrails.

### SDK documentation (NEVER skipped)

Identify the framework by reading `pyproject.toml` and entrypoint imports. Always fetch the core page above. Extract Validator classes, entity-type enums, `GuardrailScope`, `GuardrailExecutionStage`, and Action classes.

For LangChain/LangGraph—detected by `uipath-langchain` in `pyproject.toml` or `from langchain...` / `from langgraph...` imports—also run `WebFetch` once on:

`https://uipath.github.io/uipath-python/langchain/guardrails/`

Extract middleware classes, supported scopes/stages, extra parameters, and `uipath_langchain.guardrails` import paths. For other frameworks (LlamaIndex, OpenAI Agents, plain Python, etc.), do not invent adapter URLs; use only the core page. No published framework adapter currently auto-wraps those objects, so direct validator invocation may be required.

Use fetched content as the sole source of truth. Join catalog entries to SDK documentation into `{ validator_id → { middleware_class, validator_class, entity_enum, allowed_scopes, allowed_stages } }`.

## Recommend Mode

Use when the agent lacks guardrails or the user asks which to add.

### Step 1 — Read Agent Code

Use `Glob` / `Grep` to find and read the entrypoint Python file. Identify:

- system prompt and domain/behavior;
- input/output schemas (`pydantic.BaseModel` or function signatures);
- `@tool` functions, including name, docstring, and signature;
- LLM factory versus direct `UiPathChat(...)` assignment;
- agent factory versus module-level `create_agent(...)`;
- existing `@guardrail(...)` decorators and `*UiPath…Middleware(...)` entries.

### Step 2 — Catalog-Driven Recommendation Analysis

For **each entry** in the catalog (`guardrails[]` array from the cached JSON):

1. Read the entry's `when_to_use`, `use_cases`, `description`, and `security_risk_addressed`.
2. Compare against agent context (system prompt, schemas, tool docstrings): does the agent's purpose align with `when_to_use`, do any `use_cases` describe what it does or the data it handles, does it face the `security_risk_addressed` threat?
3. Read `when_not_to_use`; if the agent matches a disqualifying condition, exclude the validator (or mention it with an explanation).
4. Cross-reference the Step 0 list status: `Available` → candidate; `Unauthorised` → mention as unlicensed but do NOT add; absent → skip silently.
5. For a candidate, use `examples[].config` for scope, stage, action, and parameters; translate `validator_parameters` to Python `Validator(...)` / `Middleware(...)` arguments using the Step 0 SDK docs. Do not use predetermined mappings.

When both built-in and `Available` BYO entries exist, default to the built-in SDK validator/middleware and mention the BYO alternative. Wire a specific BYO configuration only when requested; see [guardrails.md § BYO (bring-your-own) validators](guardrails.md#byo-bring-your-own-validators).

### Step 3 — De-duplicate Overlapping Validators

Group candidates by (`security_category`, scope, stage). For any group with more than one candidate:

1. **Drop deprecated or unavailable entries first** — if the catalog marks an entry deprecated (`status`, or a note in `notes` / `when_not_to_use`), remove it; never recommend a retiring validator when an active alternative covers the category.
2. **Keep the single best fit** for the agent's context (closest `when_to_use` / `use_cases` match) and recommend only that one.
3. **Mention the dropped alternative(s)** and why (e.g. "recommending only User Prompt Attacks, not Prompt Injection — both cover adversarial input at LLM · PRE and the catalog marks Prompt Injection deprecated").

Do not hardcode validator names or a fixed "prefer X over Y" rule; derive grouping and deprecation from the catalog's own fields.

### Step 4 — Style Choice

If the user has not specified **middleware** or **decorator**, ask before generating code; do not implement both unless explicitly requested. Use the comparison table in the fetched `langchain/guardrails/` SDK doc, the “Choosing between patterns” section, when helping choose.

### Step 5 — Scope and Tool Filtering

Map catalog scopes as follows:

| Catalog scope | Coded mapping |
|---|---|
| `Agent` | `GuardrailScope.AGENT` middleware, or `@guardrail` above a named agent factory returning `create_agent(...)`; refactor a module-level call first. |
| `Llm` | `GuardrailScope.LLM` middleware, or `@guardrail` above a named LLM factory returning `UiPathChat(...)`; refactor a direct assignment first. |
| `Tool` | `GuardrailScope.TOOL` middleware with `tools=[<tool_obj>]`, or `@guardrail` directly above a `@tool` function. Use Python objects, never strings. |

For a named tool, verify it exists as a `@tool` function and use Tool scope only. For a requested scope, retain only candidates whose SDK/catalog `allowed_scopes` include it. If there are no tools, do not add Tool-scoped guardrails.

Choose the outermost permitted scope:

| Intent | Preferred scope | Reason |
|---|---|---|
| Input protection (PII, jailbreak, injection) | broadest permitted PRE scope: Agent > Llm > Tool | stop the run before model/tool work |
| Output protection (harmful content, IP) | Agent · POST when allowed | inspect the final caller-visible answer |
| Tool I/O protection | Tool on the relevant tool | narrow only when the concern is tool-specific or requested |

PII intended to stop personal-data handling belongs at `GuardrailScope.AGENT` · PRE rather than LLM · PRE when allowed. Use a narrower scope only when unsupported or explicitly requested; `prompt_injection` and `user_prompt_attacks` are Llm-only examples. Confirm the selected scope is allowed.

### Step 6 — Choose the Action

Default to `action_type` in the catalog representative `examples[].config`. Security-critical `security_category` values `adversarial_input` and `content_safety` use catalog `Block` defaults because log-only enforcement does not protect.

Use `EscalateAction` only when the user wants human review/approval, fetched SDK docs expose it, and a deployed Action App is declared in `bindings.json` through the coded-agent bindings sync workflow; see [guardrails.md § Escalation action (HITL)](guardrails.md#escalation-action-human-in-the-loop). It suspends for review, resumes on Approve, and terminates on Reject. If docs, app, or binding are unavailable, say so and fall back to Block/Log; never silently remove escalation.

1. Generate `BlockAction(...)` when the catalog default is `Block`; do not substitute `LogAction` for security-critical guardrails without explanation.
2. Never silently downgrade Block → Log or requested escalation → Log/Block. State the downgrade and reason.
3. Use Log instead of Block only for explicit observe-only/audit/log-first requests or high false-positive risk, such as PII `PERSON` flagging ordinary words; state which reason applies.
4. When action preference is ambiguous, ask once or apply the catalog Block default and report it.

### Step 7 — Generate Code

Read [guardrails.md](guardrails.md) before writing Python. Use middleware spread with `*` inside `create_agent(middleware=[...])`; Tool middleware receives `tools=[<tool_obj>]`. For decorators, use `@guardrail(validator=..., action=..., stage=...)` above the `@tool` function, LLM factory, or agent factory as appropriate.

Translate catalog parameter types using names from SDK docs:

| Catalog `$parameterType` | Python representation |
|---|---|
| `enum-list` | list of enum members, e.g. `[PIIDetectionEntityType.EMAIL, PIIDetectionEntityType.PHONE_NUMBER]` |
| `map-enum` | dict from enum member to number; keys must exactly match the `enum-list` values, e.g. `{PIIDetectionEntityType.EMAIL: 0.5}` |
| `number` | plain `float` / `int` |
| `text` | plain `str` |
| `enum` | allowed `str`; if options are empty, run `uip agent guardrails llm-as-judge-models --output json` and use a `ModelId`; ask the user only if it returns nothing or fails |
| `text-list` | `List[str]` |

Use only Action classes exposed by SDK docs: `BlockAction(...)`, `LogAction(severity_level=...)`, `EscalateAction(app_name=..., app_folder_path=..., recipient=...)`, or other documented classes. Escalation requires the Action App to be deployed and declared in `bindings.json` using [../../lifecycle/bindings-reference.md](../../lifecycle/bindings-reference.md).

### Step 8 — Apply and Verify

Write changes using [guardrails.md](guardrails.md). Then run both checks; syntax alone is insufficient:

1. Run:
   ```bash
   python3 -c "import ast; ast.parse(open('graph.py').read())"
   ```
2. For LangChain, run the adapter-registration and `_GuardedLLM` / `_GuardedTool` wrap checks from [guardrails.md § Verify Guardrails Are Actually Wired](guardrails.md#verify-guardrails-are-actually-wired). Do not report success until runtime wiring passes.

Replace `graph.py` with the actual entrypoint file.

Report:
- validator name and Python class added;
- catalog `when_to_use` or matching `use_cases` justification;
- scope and action, including why; dropped overlapping validators and reasons;
- any LogAction use where catalog default was Block and its reason;
- parameter values and meanings;
- middleware/decorator style and factory refactors;
- verification results.

## Validate Mode

Use when existing guardrails are being assessed. Fetch SDK docs first. They are authoritative for Python class, scope, and placement. Also run catalog and list for relevance and entitlement checks; they are not a hard prerequisite once SDK docs settle a scope fix.

Discover existing decorators and middleware as in Step 1. For each, identify the referenced validator. If multiple list entries share its `Validator` name, determine whether code uses a BYO construct (`ByoValidator(...)` or `UiPathByoGuardrailMiddleware(...)`, identified by `validator_name`) or the plain SDK construct, then match `IsByo` before reading `Parameters` or scopes.

### Correctness Check

Using SDK docs and catalog, check:

- **Class import:** matches the documented path, such as `from uipath_langchain.guardrails import UiPathPIIDetectionMiddleware`.
- **Entity enums:** every passed entity/category is documented.
- **Threshold keys:** every `map-enum` key is in the corresponding entity list, with no extras or missing keys.
- **Threshold values:** satisfy catalog range and step; for example, harmful-content severities must be `0`, `2`, `4`, or `6`.
- **Action class:** is documented for the validator.
- **Required parameters:** every catalog parameter with `Required: true` is supplied.

### Actionability Check

1. Read allowed scopes and per-scope stages from SDK docs; cross-check catalog `allowed_scopes` when available.
2. Middleware `scopes=[...]` must contain only allowed scopes. Decorated functions must match scope: `@tool` for Tool, LLM factory for LLM, agent factory for Agent.
3. Middleware takes no `stage=` argument; its validator fixes the stage, for example, `intellectual_property` POST or `user_prompt_attacks` PRE. Check stages only for decorator `stage=`: `GuardrailExecutionStage.PRE` or `POST` must be catalog-supported.
4. Tool middleware `tools=[...]` must contain actual discovered `@tool` Python objects, not strings or undefined names.
5. Decorated LLM/Agent functions must return `UiPathChat(...)` / `create_agent(...)`; unrelated functions silently no-op.

### Relevance Check

Read `when_not_to_use` and compare it with the prompt, schemas, and tool docstrings. Flag potentially misapplied guardrails and explain the conflict.

### Report and Fix

Report each guardrail as:

- **OK** — no issues.
- **Correctness issue** — problem and fix, such as a threshold key absent from the selected entity list.
- **Actionability issue** — problem and fix, such as an LLM-only validator decorating a Tool function.
- **Relevance issue** — why it may not apply and what to consider.

If the user requests fixes, apply them and run:

```bash
python3 -c "import ast; ast.parse(open('graph.py').read())"
```

## Critical Rules

1. **Recommend mode / net-new adds:** fetch catalog first (use cache if fresh), guardrails list second (no cache), and the two SDK doc pages via WebFetch third (no cache) — all three required before any analysis or code edit. **Validate mode of an existing guardrail:** SDK docs are authoritative and sufficient for a scope/placement fix; still fetch catalog + list for Relevance and entitlement checks, but they are not a hard prerequisite.
2. **If `GuardrailCatalogUnavailable`** → surface the message and stop. Never guess or use hardcoded recommendations.
3. Recommend only `Available` validators; mention `Unauthorised` ones.
4. Every recommendation must cite `when_to_use` or a matching `use_cases` item.
5. Never recommend two validators with the same `security_category` at the same scope and stage. Derive deprecation and the best fit from catalog fields; mention the dropped alternative.
6. Default action to catalog `examples[].config.action_type`; never silently downgrade Block → Log. Security-critical `adversarial_input` and `content_safety` default to Block. Explain any LogAction deviation.
7. Block input at the earliest permitted outer scope: Agent · PRE over Llm over Tool; PII intended to stop personal-data handling belongs at Agent, not Llm, unless unsupported or narrowed by the user. See Step 5.
8. For LangChain / LangGraph, import guardrail symbols from `uipath_langchain.guardrails`, not `uipath.platform.guardrails`; only the former registers the adapter. Other frameworks use `uipath.platform.guardrails` directly because no UiPath framework adapter is published. Verify adapter registration plus `_GuardedLLM`/`_GuardedTool` wrapping, not only `ast.parse`. See [guardrails.md § Imports Pattern](guardrails.md#imports-pattern) and [§ Verify Guardrails Are Actually Wired](guardrails.md#verify-guardrails-are-actually-wired).
9. For Tool scope, verify an existing `@tool` function; if none exists, do not add Tool-scoped guardrails.
10. LLM-scope decorators require a named factory containing the LLM; refactor direct `llm = UiPathChat(...)` assignments first.
11. Agent-scope decorators require a named factory containing `create_agent(...)`; refactor module-level calls first.
12. Cache catalog at `.guardrails-catalog-cache.json` in the working directory and add it to `.gitignore` if one exists.
13. Take class and enum names from SDK docs. For LangChain imports use `https://uipath.github.io/uipath-python/langchain/guardrails/` and `uipath_langchain.guardrails`; for other frameworks use the core page and `uipath.platform.guardrails`.
14. Read [guardrails.md](guardrails.md) before writing Python; it specifies middleware spread (`*`), decorator stacking, factory refactors, and import sources.
15. Use `EscalateAction` only when SDK docs expose it, the user wants human review, and a deployed Action App is declared in `bindings.json` via the coded-agent bindings sync workflow. Otherwise fall back to Block/Log and say so; never silently drop escalation. See [guardrails.md § Escalation action (HITL)](guardrails.md#escalation-action-human-in-the-loop).
16. `Validator` is not unique: disambiguate built-in versus BYO by `IsByo`. Key lookups on `(Validator, IsByo)`. Default to built-in unless the user names or requests BYO. Never fabricate a BYO construct; see [guardrails.md § BYO (bring-your-own) validators](guardrails.md#byo-bring-your-own-validators).