# Guardrail Recommendation and Validation — Coded Agents

This reference covers two workflows for Python coded agents (LangChain/LangGraph):
- **Recommend**: The agent has no guardrails (or insufficient ones) → which guardrails should be added?
- **Validate**: The agent already has guardrails → are they correctly configured and appropriate?

Both workflows are driven by live data — the catalog (`uip agent guardrails catalog`) for recommendation reasoning, the guardrails list (`uip agent guardrails list`) for tenant-availability and parameter/scope constraints, and the live UiPath Python SDK docs (`WebFetch`) for mapping catalog `validator_id` values to Python middleware/Validator class names. Do not hardcode assumptions about which guardrail fits which agent type, or which Python class implements which validator.

> **This file covers WHEN to add guardrails and WHY. For the exact Python writing patterns (middleware spread with `*`, decorator placement, factory refactors), always read [guardrails.md](guardrails.md) before editing the agent code.**

---

## Step 0 — Fetch Catalog, Available Validators, and SDK Docs (MANDATORY — do this before any analysis)

### Catalog (cacheable — 30-minute TTL)

The catalog is the same for all tenants (authored metadata, rarely changes). Cache it locally for 30 minutes to avoid redundant calls.

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

- **CACHE_HIT**: read `.guardrails-catalog-cache.json` directly.
- **CACHE_MISS**: fetch and save:
  ```bash
  uip agent guardrails catalog --output json > .guardrails-catalog-cache.json
  ```

Inspect the saved JSON. If the output contains `"Code": "GuardrailCatalogUnavailable"`, surface the message to the user and **stop** — do not fall back to guessing. Note: the CLI writes all structured output (both success and error JSON) to stdout, so the redirect captures error responses correctly — do not add `2>&1`.

The cache file is `.guardrails-catalog-cache.json` in the current working directory. Add it to `.gitignore` if one exists.

### Guardrails List (NEVER cached — tenant-specific)

This returns only guardrails available to the current tenant (filtered by entitlements and feature flags). Run it fresh every time:

```bash
uip agent guardrails list --output json
```

Build a lookup of `{ validatorId: status }` from the `Data` array. You will use this to filter recommendations.

> **Catalog vs. list — the key distinction:** The catalog lists all guardrails that exist on the platform (with rich metadata for reasoning). The guardrails list returns only those accessible to this tenant. Only recommend validators where `Status == "Available"` in the list.

### SDK Documentation (NEVER skipped — Python class names)

Coded agents reference guardrails by **Python class name** (e.g. `UiPathPIIDetectionMiddleware`, `PIIDetectionValidator`), not by `validator_id`. The catalog gives you the `validator_id`; the SDK docs give you the corresponding Python classes, import paths, scope/stage enums, and entity-type enums.

Call `WebFetch` twice — once per doc page:

1. **`https://uipath.github.io/uipath-python/langchain/guardrails/`**
   Extract: middleware classes (e.g. `UiPathPIIDetectionMiddleware`, `UiPathHarmfulContentMiddleware`), their supported scopes, stage support, extra parameters, and correct import paths from `uipath_langchain.guardrails`.

2. **`https://uipath.github.io/uipath-python/core/guardrails/`**
   Extract: built-in Validator classes (e.g. `PIIDetectionValidator`, `UserPromptAttacksValidator`), entity-type enums (e.g. `PIIDetectionEntityType.EMAIL`), `GuardrailScope` / `GuardrailExecutionStage` enums, available `Action` classes (`BlockAction`, `LogAction`, `FilterAction`), and decorator import path (`from uipath_langchain.guardrails import guardrail`).

**Use the fetched content as the sole source of truth.** Never rely on memory for class names, enum members, or import paths — the SDK evolves and the docs are the only reliable mapping.

Build a `{ validator_id → { middleware_class, validator_class, entity_enum, allowed_scopes, allowed_stages } }` lookup in working memory by joining catalog entries with SDK class names.

---

## Recommend Mode

Use when the agent has no guardrails or when the user asks which guardrails to add.

### Step 1 — Read Agent Code

Use `Glob` / `Grep` to locate the entrypoint Python file. Look for `create_agent`, `StateGraph`, or `@entrypoint`. Once found, read it to extract:

- **System prompt text** — what does the agent do? What domains and behaviors are described?
- **Input / output schemas** (`pydantic.BaseModel` classes or function signatures) — what data does the agent receive and produce?
- **`@tool` functions** — name, docstring, signature. These become the targets of Tool-scoped guardrails.
- **LLM factory** — is the LLM created inside a named function (e.g. `def create_llm(): return UiPathChat(...)`) or assigned directly at module level? Decorator-style LLM-scope guardrails require a factory.
- **Agent factory** — is `create_agent(...)` wrapped in a named function? Decorator-style Agent-scope guardrails require a factory.
- **Existing guardrails** — any `@guardrail(...)` decorators above functions, or `*UiPath…Middleware(...)` entries inside `middleware=[...]` in `create_agent(...)`. Note them to avoid duplicating.

### Step 2 — Catalog-Driven Recommendation Analysis

For **each entry** in the catalog (`guardrails[]` array from the cached JSON):

1. Read the entry's `when_to_use`, `use_cases`, `description`, and `security_risk_addressed`.
2. Compare against agent context (system prompt, schemas, tool docstrings) using semantic reasoning:
   - Does the agent's purpose align with the `when_to_use` scenario?
   - Do any `use_cases` items describe what this agent does or the data it handles?
   - Does the agent face the threat described in `security_risk_addressed`?
3. Also read `when_not_to_use`. If the agent matches a disqualifying condition, exclude this validator from recommendations (or mention it with an explanation).
4. Cross-reference with the guardrails list status lookup from Step 0:
   - `Available` → candidate for recommendation
   - `Unauthorised` → mention to the user ("this guardrail is not licensed for your tenant") but do NOT add it
   - Not in the list at all → skip silently (not available on this platform version)
5. If the validator is a candidate: use the catalog entry's `examples[].config` to determine the appropriate scope, stage, action, and parameters. Translate `validator_parameters` shape to the Python `Validator(...)` / `Middleware(...)` constructor arguments using the SDK docs from Step 0.

Do **not** apply predetermined knowledge about which guardrail maps to which schema field. Let the catalog entry's authored fields drive every recommendation decision.

### Step 3 — De-duplicate Overlapping Validators

Several catalog validators address the same threat. Recommending more than one of them at the same scope and stage is redundant — it doubles latency and cost on every call for marginal benefit (the canonical case is `prompt_injection` and `user_prompt_attacks`: both have `security_category: "adversarial_input"` and both run at LLM · PRE).

After Step 2 produces the candidate list, group candidates by **(`security_category`, scope, stage)**. For any group with more than one candidate:

1. **Drop deprecated or unavailable entries first.** If the catalog marks an entry deprecated (via its `status`, or a deprecation note in `notes` / `when_not_to_use`), remove it from the group. Never recommend a validator the catalog signals is being retired when an active alternative covers the same category.
2. **Keep the single best fit** for the agent's context — the one whose `when_to_use` / `use_cases` most closely match. Recommend only that one.
3. **Mention the alternative(s)** you dropped and why (e.g. "also recommending only User Prompt Attacks, not Prompt Injection — both cover adversarial input at LLM PRE and the catalog marks Prompt Injection deprecated").

Do **not** hardcode validator names or a fixed "prefer X over Y" rule in your reasoning — derive the grouping from each entry's `security_category`, scope, and stage, and derive deprecation from the catalog's own fields. This keeps the behavior correct as the catalog evolves.

### Step 4 — Style Choice

If the user has not specified **middleware** or **decorator**, ask before generating any code. Do not implement both unless explicitly asked.

Use the comparison table from the fetched `langchain/guardrails/` SDK doc (the "Choosing between patterns" section) to help the user decide if they ask.

### Step 5 — Scope and Tool Filtering

In coded agents, scopes map to concrete Python constructs, not selector strings:

| Catalog scope | Coded mapping |
|---------------|---------------|
| `Agent` | `GuardrailScope.AGENT` on middleware, or `@guardrail` above a named **agent factory function** that returns `create_agent(...)`. If `create_agent(...)` is called at module level, refactor it into a factory first. |
| `Llm` | `GuardrailScope.LLM` on middleware, or `@guardrail` above a named **LLM factory function** that returns `UiPathChat(...)`. If the LLM is assigned directly (`llm = UiPathChat(...)`), refactor into a factory first. |
| `Tool` | `GuardrailScope.TOOL` on middleware with `tools=[<tool_obj>]` (Python object, not string), or `@guardrail` placed directly above a `@tool` function. |

If the user asks for recommendations for a **specific tool** (e.g., "for the lookup_account_info tool"):
- Tool scope only. Confirm the tool exists as a `@tool` function in the agent code before writing.
- Pass the Python object (e.g. `lookup_account_info`) into `tools=[...]` — never a string name.

If the user asks for recommendations for a **specific scope** (e.g., "only for Llm"):
- Keep only candidates whose `allowed_scopes` (from the catalog entry and/or SDK class) include that scope.
- Discard candidates that do not support that scope.

#### Block as early as possible — default scope selection

When a validator supports **more than one scope** (e.g. `pii_detection` allows Agent / Llm / Tool), pick the scope that stops a violation at the **outermost boundary the validator allows**, so a bad run is halted with the least wasted work:

| Guardrail intent | Prefer | Why |
|---|---|---|
| **Input protection** (block bad/sensitive input: PII, jailbreak, injection) | broadest **PRE** scope allowed → **Agent** > Llm > Tool | Agent · PRE fires once, before the agent reaches the LLM or any tool. Catching PII or an attack at Agent · PRE blocks the whole run immediately instead of after the model has already been called. |
| **Output protection** (block bad output the caller sees: harmful content, IP) | **Agent · POST** when allowed | Agent · POST inspects the agent's final answer — the thing the user actually receives. |
| **Tool I/O protection** (a specific tool's input/output) | **Tool** scope on that tool | Only narrow to Tool when the concern is genuinely that one tool, or the user scoped it there. |

Concretely: **PII detection meant to stop the agent handling personal data belongs at `GuardrailScope.AGENT` · PRE, not `GuardrailScope.LLM` · PRE** — both are allowed by the catalog, but Agent · PRE blocks the run earlier (before the LLM call) and covers the whole agent, not just one model invocation. Only drop to a narrower scope when the validator does not support the broader one (`prompt_injection` and `user_prompt_attacks` are Llm-only, so Llm · PRE is the earliest available for them) or when the user explicitly asks for a narrower scope.

Always confirm the chosen scope is in the validator's `allowed_scopes` from the guardrails list — never assume a scope the catalog/SDK does not permit.

### Step 6 — Choose the Action

The action (`BlockAction` vs `LogAction`) is **not** a free choice — default to the `action_type` in the catalog entry's representative `examples[].config`. For security-critical guardrails (`adversarial_input` — prompt injection / user prompt attacks; `content_safety` — harmful content / IP) the catalog examples use **Block**, because a logged-but-allowed violation provides no actual protection.

Rules:

1. **Default to the catalog example's `action_type`.** If it is `Block`, generate `BlockAction(...)`. Do not substitute `LogAction` for a security-critical guardrail on your own initiative.
2. **Never silently downgrade Block → Log.** A guardrail set to log-only when the user expected blocking is the dangerous failure mode — the agent looks protected but isn't. If you use `LogAction` for any guardrail whose catalog default is `Block`, you **must** state it explicitly in the report and give the reason.
3. **Legitimate reasons to use Log instead of Block** (state which applies):
   - The user explicitly asked for observe-only / audit / "log first, block later" rollout.
   - A high false-positive risk where blocking would break normal operation (e.g. PII `PERSON` entity flagging ordinary words) — log so the user can tune thresholds before enforcing.
4. **When ambiguous, ask once.** If the user gave no action preference and the guardrail is security-critical, you may apply the Block default and report it, or ask "block on violation, or log-only to start?" — but do not quietly pick Log.

### Step 7 — Generate Code

For each recommended guardrail, the catalog entry's `examples[].config` gives the scope/stage/action/parameter intent. Translate it to Python using the writing patterns in [guardrails.md](guardrails.md):

- **Middleware** — spread the class with `*` into `create_agent(middleware=[...])`. For Tool scope, pass `tools=[<tool_obj>]`.
- **Decorator** — place `@guardrail(validator=..., action=..., stage=...)` above the target (`@tool` function for Tool scope, LLM factory for LLM scope, agent factory for Agent scope).

Use the action chosen in Step 6.

Map catalog parameter shapes to Python:

| Catalog `$parameterType` | Python representation |
|--------------------------|----------------------|
| `enum-list` (e.g. `entities`) | List of enum members (e.g. `[PIIDetectionEntityType.EMAIL, PIIDetectionEntityType.PHONE_NUMBER]`) — names taken from SDK docs |
| `map-enum` (e.g. `entityThresholds`) | Dict from enum member → number (e.g. `{PIIDetectionEntityType.EMAIL: 0.5}`) — keys must exactly match the `enum-list` parameter's values |
| `number` (e.g. `threshold`) | Plain `float` / `int` constructor argument |

Use `BlockAction(...)`, `LogAction(severity_level=...)`, or other actions exposed by the SDK docs. Never invent action class names.

> Read [guardrails.md](guardrails.md) before writing any Python. The middleware spread, decorator stacking, and factory refactor rules cannot be safely inferred.

### Step 8 — Apply and Verify

Write the recommended guardrails into the Python file using the patterns from [guardrails.md](guardrails.md). Then verify — in two stages, because syntax-valid does **not** mean active:

1. **Syntax** — the file still parses:
   ```bash
   python3 -c "import ast; ast.parse(open('graph.py').read())"
   ```
2. **Runtime wiring (mandatory)** — the guardrails are actually attached. A guardrail whose symbols were imported from the wrong module parses fine but **silently never fires**. Run the adapter-registration and `_GuardedLLM` / `_GuardedTool` wrap checks from [guardrails.md § Verify Guardrails Are Actually Wired](guardrails.md#verify-guardrails-are-actually-wired-mandatory-after-writing). Do not report the guardrails as added until these pass.

(Replace `graph.py` with the actual entrypoint file from Step 1.)

Report to the user:
- What was added (by validator name and Python class)
- Why it was recommended (cite the catalog's `when_to_use` or a specific `use_cases` item that matched the agent's context)
- Which scope and action were chosen and why. If you dropped an overlapping validator in Step 3, name it and the reason. If you used `LogAction` for a guardrail whose catalog default is `Block` (Step 6), call it out explicitly with the reason.
- Which parameters were set and their meaning
- Which style was used (middleware or decorator) and any refactor performed (e.g. wrapped LLM in a factory)

---

## Validate Mode

Use when the agent already has guardrails and the user asks whether they are correctly configured or appropriate.

**Before any validation, run all three Step 0 fetches** (catalog with cache, guardrails list without cache, SDK docs via WebFetch). The SDK docs are the authoritative source for which Python class corresponds to which `validator_id` and which scopes/stages each class supports.

For each existing guardrail discovered in the Python file (Step 1 from Recommend Mode):

### Correctness Check

From the SDK docs and the catalog, look up the validator class referenced in the code:

| Aspect | What to check |
|--------|---------------|
| Class import | Class is imported from the path the SDK docs specify (e.g. `from uipath_langchain.guardrails import UiPathPIIDetectionMiddleware`) — typos and stale imports fail at runtime |
| Entity enums | Every entity/category passed (e.g. `PIIDetectionEntityType.EMAIL`) is a member listed in the SDK doc enum |
| Threshold keys (`map-enum` parameters) | Every key in the threshold dict matches a member of the corresponding entity list — no extras, no missing |
| Threshold values | Within the range and step the catalog parameter declares (e.g. harmful content severities must be `0`, `2`, `4`, or `6`) |
| Action class | Action constructor (`BlockAction`, `LogAction`, ...) is one the SDK docs expose for this validator |
| Required parameters | Any catalog parameter with `Required: true` is present in the constructor call |

### Actionability Check

1. From the catalog entry, read `allowed_scopes` and the per-scope allowed stages.
2. Confirm the in-code scope is permitted:
   - Middleware — every `GuardrailScope` in the `scopes=[...]` argument is in `allowed_scopes`.
   - Decorator — the function the `@guardrail` decorates matches the implied scope: `@tool` for Tool scope, LLM factory for LLM scope, agent factory for Agent scope.
3. Confirm the stage is permitted: `GuardrailExecutionStage.PRE` only where catalog allows pre-execution; `POST` only where catalog allows post-execution.
4. For Tool-scoped middleware: `tools=[...]` must contain the actual `@tool` Python objects discovered in Step 1 — not strings, not undefined names.
5. For decorator-style LLM/Agent scope: the decorated function must actually return a `UiPathChat(...)` / `create_agent(...)` — decorating an unrelated function silently no-ops.

### Relevance Check

1. Read the catalog entry's `when_not_to_use`.
2. Compare against the agent's current context (system prompt, schemas, tool docstrings).
3. If the agent matches a `when_not_to_use` condition, flag the guardrail as potentially misapplied and explain why.

### Report and Fix

Report per guardrail:
- **OK** — no issues found
- **Correctness issue** — describe the problem (e.g., "`harmfulContentEntityThresholds` has key `Sexual` but `Sexual` is not in `harmfulContentEntities` — keys must match the entity list") and the fix
- **Actionability issue** — describe the problem (e.g., "`UserPromptAttacksValidator` is decorating `@tool def lookup_account_info` — the SDK docs say this validator only supports LLM scope; move the `@guardrail` above the LLM factory") and the fix
- **Relevance issue** — describe why the guardrail may not be appropriate and what to consider instead

If the user asks to fix identified issues: apply corrections to the Python file, then verify:

```bash
python3 -c "import ast; ast.parse(open('graph.py').read())"
```

---

## Critical Rules

1. **Always fetch catalog first** (use cache if fresh); **always fetch guardrails list second** (no cache); **always fetch the two SDK doc pages via WebFetch third** (no cache). All three are required before any analysis or code edit.
2. **If `GuardrailCatalogUnavailable`** → surface the message and stop. Do not fall back to guessing or hardcoded recommendations.
3. **Only recommend `Available` validators**. Mention `Unauthorised` ones to the user so they can contact their administrator.
4. **Every recommendation must cite** the catalog entry's `when_to_use` or a specific `use_cases` item that matched the agent's context. Do not recommend a guardrail without explaining why it applies.
5. **Never recommend two validators with the same `security_category` at the same scope and stage** (e.g. `prompt_injection` + `user_prompt_attacks` at LLM PRE). De-duplicate per Step 3: drop catalog-deprecated entries, keep the best fit, mention the alternative. Derive the grouping and deprecation from the catalog's own fields — do not hardcode validator names.
6. **Default the action to the catalog example's `action_type`; never silently downgrade Block → Log.** Security-critical guardrails (`adversarial_input`, `content_safety`) default to `Block`. If you use `LogAction` for a guardrail whose catalog default is `Block`, state it and the reason in the report (Step 6).
7. **Block as early as possible — pick the outermost scope the validator allows.** For input protection (PII, jailbreak, injection) prefer `GuardrailScope.AGENT` · PRE over Llm over Tool, so the run halts before the LLM call. PII meant to stop the agent handling personal data goes at **Agent**, not Llm. Only narrow when the validator is scope-restricted (e.g. `prompt_injection` / `user_prompt_attacks` are Llm-only) or the user asks for a narrower scope. See Step 5.
8. **Import guardrail symbols only from `uipath_langchain.guardrails`** — never `uipath.platform.guardrails`. The former registers the LangChain adapter; the latter silently no-ops. After writing, verify runtime wiring (adapter registered + `_GuardedLLM`/`_GuardedTool` wrap), not just `ast.parse`. See [guardrails.md § Imports Pattern](guardrails.md#imports-pattern) and [§ Verify Guardrails Are Actually Wired](guardrails.md#verify-guardrails-are-actually-wired-mandatory-after-writing).
9. **For Tool scope**: verify the tool exists as a `@tool` function in the agent code before adding the guardrail. If the agent has no tools, do not add a Tool-scoped guardrail.
10. **For LLM-scope decorator**: the LLM must be inside a named factory function. If it is assigned directly (`llm = UiPathChat(...)`), refactor into a factory first — never decorate a module-level assignment.
11. **For Agent-scope decorator**: `create_agent(...)` must be inside a named factory function. If it is called at module level, refactor into a factory first.
12. **The cache file is `.guardrails-catalog-cache.json`** in the working directory. Add it to `.gitignore` if one exists.
13. **Class names and enum names come from the SDK docs** — never invent them. The SDK evolves; relying on memory produces stale code. For **import paths**, the `langchain/guardrails/` page is authoritative — use `uipath_langchain.guardrails` even when the `core/guardrails/` page shows `uipath.platform.guardrails` (see Rule 8).
14. **Read [guardrails.md](guardrails.md) before writing any Python** — the middleware spread (`*`), decorator placement above `@tool` / factory, factory refactor, and import-source rules are specified there and cannot be safely inferred.
