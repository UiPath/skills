# Guardrails for Coded Agents

Add guardrails to a Python coded agent (LangChain/LangGraph) in two styles: **middleware** or **decorator**. This reference is the authoritative source for what the `uipath_langchain` package supports — scope and stage constraints are compiled from the package source, not from the CLI.

> **The user tells you which guardrail to add. This file tells you how to add it correctly.**

---

## Available Guardrails

| Guardrail | Middleware class | Decorator validator | Middleware scopes | Stage | Key parameters |
|---|---|---|---|---|---|
| PII Detection | `UiPathPIIDetectionMiddleware` | `PIIValidator` | AGENT, LLM, TOOL | PRE + POST | `entities` (required); `tools` (required for TOOL scope) |
| Harmful Content | `UiPathHarmfulContentMiddleware` | `HarmfulContentValidator` | AGENT, LLM, TOOL | PRE + POST | `entities` (required); `tools` (required for TOOL scope) |
| Prompt Injection | `UiPathPromptInjectionMiddleware` | `PromptInjectionValidator` | **LLM only** | **PRE only** | `threshold: float = 0.5` (optional) |
| User Prompt Attacks | `UiPathUserPromptAttacksMiddleware` | `UserPromptAttacksValidator` | **LLM only** | **PRE only** | none |
| Intellectual Property | `UiPathIntellectualPropertyMiddleware` | `IntellectualPropertyValidator` | **AGENT, LLM only** | **POST only** | `entities` (list of `IntellectualPropertyEntityType`) |
| Deterministic | `UiPathDeterministicGuardrailMiddleware` | `CustomValidator` | **TOOL only** | PRE, POST, PRE_AND_POST | `tools` (required), `rules` (list of callables) |

---

## Optional: Check Tenant Availability

For built-in AI validators (PII, harmful content, prompt injection, IP, user prompt attacks), optionally confirm the validator is enabled on this tenant:

```bash
uip agent guardrails list --output json
```

If the requested validator has `Status != "Available"` → tell the user and stop.

**Skip this step for deterministic guardrails** — they run locally with no backend dependency.

---

## Step 1 — Style Choice

If the user has not specified **middleware** or **decorator**, ask before generating any code. Do not implement both unless explicitly asked.

---

## Step 2 — Read Agent Code

Use `Glob` / `Grep` to find the main Python file (look for `create_agent`, `StateGraph`, or `@entrypoint`). Read it to understand:

- Whether `create_agent()` is called directly or inside a factory function
- Which `@tool` functions exist (needed for Tool-scoped guardrails)
- Whether a separate LLM factory function exists (needed for LLM-scope decorator guardrails)
- Which guardrails are already present (avoid duplicating)

---

## Imports Reference

Only add the imports you actually use. Merge with existing imports from the same package.

### Middleware imports

```python
from uipath_langchain.guardrails import (
    UiPathPIIDetectionMiddleware,
    UiPathHarmfulContentMiddleware,
    UiPathIntellectualPropertyMiddleware,
    UiPathPromptInjectionMiddleware,
    UiPathUserPromptAttacksMiddleware,
    UiPathDeterministicGuardrailMiddleware,
    BlockAction,
    LogAction,
    GuardrailExecutionStage,
    PIIDetectionEntity,
    HarmfulContentEntity,
)
from uipath_langchain.guardrails.actions import LoggingSeverityLevel
from uipath_langchain.guardrails.enums import (
    PIIDetectionEntityType,
    HarmfulContentEntityType,
    IntellectualPropertyEntityType,
)
from uipath.core.guardrails import GuardrailScope
```

### Decorator imports

```python
from uipath_langchain.guardrails import (
    guardrail,
    CustomValidator,
    PIIValidator,
    HarmfulContentValidator,
    IntellectualPropertyValidator,
    PromptInjectionValidator,
    UserPromptAttacksValidator,
    BlockAction,
    LogAction,
    GuardrailExecutionStage,
    PIIDetectionEntity,
    HarmfulContentEntity,
)
from uipath_langchain.guardrails.actions import LoggingSeverityLevel
from uipath_langchain.guardrails.enums import (
    PIIDetectionEntityType,
    HarmfulContentEntityType,
    IntellectualPropertyEntityType,
)
```

---

## Middleware Style

### Usage pattern

```python
agent = create_agent(
    model=llm,
    tools=[my_tool],
    middleware=[
        # PII — AGENT + LLM scope
        *UiPathPIIDetectionMiddleware(
            name="Agent PII Detection",
            scopes=[GuardrailScope.AGENT, GuardrailScope.LLM],
            action=LogAction(severity_level=LoggingSeverityLevel.WARNING),
            entities=[
                PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5),
                PIIDetectionEntity(PIIDetectionEntityType.PHONE_NUMBER, 0.5),
            ],
        ),
        # PII — TOOL scope (must pass tools=[...])
        *UiPathPIIDetectionMiddleware(
            name="Tool PII Detection",
            scopes=[GuardrailScope.TOOL],
            action=LogAction(severity_level=LoggingSeverityLevel.WARNING),
            entities=[PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5)],
            tools=[my_tool],
        ),
        # Prompt Injection — LLM scope only (no scopes parameter)
        *UiPathPromptInjectionMiddleware(
            name="Prompt Injection Detection",
            action=BlockAction(),
            threshold=0.5,
        ),
        # User Prompt Attacks — LLM scope only (no scopes parameter)
        *UiPathUserPromptAttacksMiddleware(
            name="User Prompt Attacks Detection",
            action=BlockAction(),
        ),
        # Harmful Content — AGENT + LLM scope
        *UiPathHarmfulContentMiddleware(
            name="Harmful Content Detection",
            scopes=[GuardrailScope.AGENT, GuardrailScope.LLM],
            action=BlockAction(),
            entities=[
                HarmfulContentEntity(HarmfulContentEntityType.VIOLENCE, threshold=2),
                HarmfulContentEntity(HarmfulContentEntityType.HATE, threshold=2),
            ],
        ),
        # Intellectual Property — AGENT + LLM scope, POST only
        *UiPathIntellectualPropertyMiddleware(
            name="IP Detection",
            scopes=[GuardrailScope.AGENT, GuardrailScope.LLM],
            action=LogAction(severity_level=LoggingSeverityLevel.WARNING),
            entities=[IntellectualPropertyEntityType.TEXT],
        ),
    ],
)
```

If `create_agent()` already has a `middleware=[...]` argument, add the new entries to the existing list. If there is no `middleware` argument yet, add `middleware=[...]` as a new keyword argument.

### Deterministic middleware

```python
# Rule-based: trigger when lambda returns True
*UiPathDeterministicGuardrailMiddleware(
    tools=[my_tool],
    rules=[lambda input_data: "forbidden" in input_data.get("text", "").lower()],
    action=BlockAction(),
    stage=GuardrailExecutionStage.PRE,
    name="Custom Word Block",
),
# Unconditional (always trigger): use empty rules list
*UiPathDeterministicGuardrailMiddleware(
    tools=[my_tool],
    rules=[],
    action=BlockAction(),
    stage=GuardrailExecutionStage.POST,
    name="Always Block Post",
),
```

---

## Decorator Style

> See also: https://uipath.github.io/uipath-python/core/guardrails/ for additional decorator examples.

### Tool scope — decorate the @tool function

Place `@guardrail` **above** `@tool`. Multiple decorators stack outermost-first (the topmost `@guardrail` in source runs first when the function is called).

```python
@guardrail(
    validator=PIIValidator(
        entities=[
            PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5),
            PIIDetectionEntity(PIIDetectionEntityType.PHONE_NUMBER, 0.5),
        ]
    ),
    action=LogAction(severity_level=LoggingSeverityLevel.WARNING),
    name="Tool PII Detection",
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
    validator=PromptInjectionValidator(threshold=0.5),  # threshold optional, default 0.5
    action=BlockAction(),
    name="LLM Prompt Injection Detection",
    stage=GuardrailExecutionStage.PRE,
)
def create_llm():
    return UiPathChat(model="gpt-4o-2024-08-06", temperature=0.7)

llm = create_llm()
```

If the code assigns the LLM directly (e.g. `llm = UiPathChat(...)`), refactor it into a factory function first, then decorate.

### Agent scope — decorate the agent factory function

Wrap `create_agent(...)` in a named factory function, then decorate it:

```python
@guardrail(
    validator=PIIValidator(
        entities=[PIIDetectionEntity(PIIDetectionEntityType.PERSON, 0.5)]
    ),
    action=BlockAction(),
    name="Agent PII Detection",
    stage=GuardrailExecutionStage.PRE,
)
def create_my_agent():
    return create_agent(model=llm, tools=[my_tool], system_prompt=SYSTEM_PROMPT)

agent = create_my_agent()
```

If `create_agent()` is called directly at module level (not in a function), wrap it in a factory function first.

### Deterministic decorator

```python
@guardrail(
    validator=CustomValidator(
        lambda args: "forbidden" in args.get("text", "").lower()
    ),
    action=BlockAction(),
    stage=GuardrailExecutionStage.PRE,
    name="Custom Word Block",
)
@tool
def my_tool(text: str) -> str:
    """Tool docstring."""
    ...
```

---

## Entity Names Reference

**PII** (`PIIDetectionEntityType`): `EMAIL`, `PHONE_NUMBER`, `PERSON`, `ADDRESS`, `DATE`, `CREDIT_CARD_NUMBER`, `US_SOCIAL_SECURITY_NUMBER`, `INTERNATIONAL_BANKING_ACCOUNT_NUMBER`, `ABA_ROUTING_NUMBER`, `US_BANK_ACCOUNT_NUMBER`, `US_DRIVERS_LICENSE_NUMBER`, `UK_DRIVERS_LICENSE_NUMBER`, `USUK_PASSPORT_NUMBER`, `US_INDIVIDUAL_TAXPAYER_IDENTIFICATION`, `UK_UNIQUE_TAXPAYER_NUMBER`, `SWIFT_CODE`, `EUGPS_COORDINATES`, `IP_ADDRESS`, `URL`

**Harmful Content** (`HarmfulContentEntityType`): `HATE`, `VIOLENCE`, `SEXUAL`, `SELF_HARM`
Thresholds: **0, 2, 4, or 6 only** (step 2).

**Intellectual Property** (`IntellectualPropertyEntityType`): `TEXT`, `CODE`

---

## Critical Rules

1. **Always spread middleware with `*`** into the list — never pass the object itself.
2. **Decorator order matters**: `@guardrail` must be above `@tool`; the **topmost** `@guardrail` (first in source) runs first when the function is called.
3. **Tool-scoped middleware requires `tools=[<tool_reference>]`** — pass the Python object, not a string.
4. **LLM-scope decorator**: LLM must be inside a factory function; decorate the factory.
5. **Agent-scope decorator**: `create_agent()` must be inside a factory function; decorate the factory.
6. **IntellectualProperty is POST-only** — always use `GuardrailExecutionStage.POST`; no TOOL scope.
7. **PromptInjection and UserPromptAttacks: LLM scope only** — these middleware classes have no `scopes` parameter and always target the LLM. Do not attempt AGENT or TOOL scope.
8. **Deterministic: TOOL scope only** — `UiPathDeterministicGuardrailMiddleware` has no `scopes` parameter and always requires `tools=[...]`. No AGENT or LLM scope.
9. **Only add imports you use** — merge new names into any existing `from uipath_langchain.guardrails import (...)` block.
10. **PII entity names are PascalCase Python enums** — `PIIDetectionEntityType.EMAIL`, never string literals.
11. **HarmfulContent thresholds must be 0, 2, 4, or 6** — no other values accepted.
