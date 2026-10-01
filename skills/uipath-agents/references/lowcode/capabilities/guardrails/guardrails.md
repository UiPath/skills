# Guardrails Reference

## Overview

Guardrails are safeguards that inspect agent inputs and outputs for policy violations (PII, harmful content, prompt injection, intellectual property, custom rules). They are configured at the **agent.json root level** as a `guardrails` array.

Two types exist:
- **`custom`** — deterministic rules you define (word matching, number comparison, boolean checks, universal triggers)
- **`builtInValidator`** — UiPath Guardrails API validators (PII detection, harmful content, prompt injection, IP protection, user prompt attacks)

> **Autonomous agents:** All guardrails are configured at the `agent.json` root `guardrails` array. **Conversational agents:** the `agent.json` root `guardrails[]` is **authoritative** (source for the Studio Web UI and both runtimes); each Tool-scoped guardrail is also mirrored into the tool's `resources/<Tool>/resource.json` → `guardrail.policies[]` — see § Conversational Support below.

> **This reference is the schema authority — do not inspect CLI internals.** The JSON shapes and examples in this file are authoritative and complete. Do NOT reverse-engineer guardrail schemas from the CLI installation: never grep `/usr/lib/node_modules/@uipath/**/dist/*.js`, read bundled/minified sources, or import-probe SDK packages to "confirm" a field. Copy the complete example for your guardrail type, adapt the values, then run `uip agent refresh "<AGENT_NAME>" --output json` and `uip agent validate "<AGENT_NAME>" --output json` — validate is the only schema check needed, and its errors name the offending field. Write the guardrail first and let validate correct you; do not spend turns pre-verifying a schema this file already gives you.

## Walkthrough

Use when adding input/output safeguards (PII detection, harmful content blocking, custom word rules) to a low-code agent. Guardrails are configured at the agent.json root `guardrails` array.

> **Read only what the task needs.** For guardrail work this file (plus [escalation-guide.md](escalation-guide.md) or [custom-rules-guide.md](custom-rules-guide.md) when those types apply) is sufficient — do not read the model-selection, prompting, or evals references for a guardrail task. Run `uip agent guardrails list` directly: the CLI handles authentication, so never preflight with `uip auth`, `uip config`, or `uip login` — react only to an actual auth error from the command itself.

> **MANDATORY: Read this file BEFORE writing any guardrail JSON.** The guardrail schema uses discriminator fields (`$actionType`, `$parameterType`, `$ruleType`, `$selectorType`) that cannot be guessed. PII detection uses `$guardrailType: "builtInValidator"` with `validatorType: "pii_detection"` — NOT `$guardrailType: "pii"`. Parameters use `id` (not `name`) and require `$parameterType`. Actions use `$actionType` (not `type`). PII entities are PascalCase (`"Email"`, not `"email_address"`). There is no `pattern`, `target`, or `message` field.
>
> **MANDATORY for `builtInValidator` guardrails: run `uip agent guardrails list --output json` before writing one.** The command gives you the exact `$parameterType` values, parameter `id` names, and allowed scopes — values you cannot safely derive from the type name alone. Skipping it leads to invalid parameter shapes that fail schema validation. **Custom guardrails (`$guardrailType: "custom"`) do NOT need this step** — their rules (word/number/boolean/always), operators, and actions are fully specified in [custom-rules-guide.md](custom-rules-guide.md) and use no validator catalog. Only run `guardrails list` for a custom guardrail if you are unsure whether the request should instead use a built-in validator.

### Step 0 — Fetch available validators (mandatory for `builtInValidator` guardrails; skip for custom-only)

Run `uip agent guardrails list --output json` and apply the four availability outcomes in [Step 0 — Fetch Available Validators (Mandatory First Step)](#step-0--fetch-available-validators-mandatory-first-step) before configuring anything. Skip this step when the guardrail is purely custom (deterministic rules); the validator catalog does not apply to custom rules.

### Step 1 — Verify existing agent

Ensure the agent project exists and has a valid `agent.json`. If starting fresh, follow [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent) first.

### Step 2 — Verify target tools exist (required for Tool-scoped guardrails)

**Skip this step if the guardrail targets only `"Agent"` or `"Llm"` scope with no `matchNames`.**

If the guardrail will use `selector.scopes: ["Tool"]` with `selector.matchNames`, list the tools already added to the agent:

```bash
uip agent tool list --output json
```

For each tool name you plan to put in `matchNames`:
- **Found in `Data`** — proceed.
- **Not found** — **STOP.** Do not add the guardrail yet. Add the tool first, then return here:
  - Process tool — RPA / agent / API / agentic, local or external: [../process/process.md](../process/process.md)
  - Integration Service tool: [../integration-service/integration-service.md](../integration-service/integration-service.md)

> `uip agent validate` enforces this: it fails with an error if a Tool-scoped guardrail references a tool that has not been added to the agent.

### Step 3 — Add a guardrail to agent.json

For built-in validators, see [Built-in Validator Guardrails](#built-in-validator-guardrails-guardrailtype-builtinvalidator) for the full schema and worked examples (Examples 1–5). For the `escalate` action (Action Center app + recipient), follow [escalation-guide.md](escalation-guide.md).

For custom rules (word/number/boolean/always), see [custom-rules-guide.md](custom-rules-guide.md) for the full schema, rule types, field selectors, and worked examples.

Copy the complete example that matches the request and adapt the values — e.g., [Example 1](#example-1-block-pii-in-agent-and-tool-outputs) for a built-in PII block guardrail. Generate a fresh UUID for `id`. Placement in `agent.json` is shown in [agent.json with Guardrails](#agentjson-with-guardrails).

### Step 4 — Refresh and validate

```bash
uip agent refresh  "<AGENT_NAME>" --output json
uip agent validate "<AGENT_NAME>" --output json
```

Confirm the guardrails appear in the validated output without errors. Refresh regenerates `entry-points.json` and `bindings_v2.json` so Studio Web sees the updated guardrails.


## Conversational Support

**Status: Custom (deterministic) `Tool`-scoped guardrails ONLY. No built-in validators.** Built-in validators (any `$guardrailType: "builtInValidator"` — the validators returned by `uip agent guardrails list`; see the [Validators Quick Reference](#validators-quick-reference)) are autonomous-only — the conversational runtime never runs them, at any scope. The only guardrails that run are `$guardrailType: "custom"` deterministic rules (word/number/boolean/always) with `selector.scopes: ["Tool"]`. Write each as the **same object (same `id`) in two places** — the `agent.json` root `guardrails[]` is **authoritative** (source for the Studio Web UI and both runtimes); the tool's `resources/<Tool>/resource.json` → `guardrail.policies[]` is its **mirror**. Write both (the CLI doesn't auto-sync), but a guardrail present only in the tool resource is invisible in Studio Web and does not run on the Unified (Python) runtime. `"Agent"` and `"Llm"` scopes are not available. If asked for PII / harmful-content / injection detection, explain built-in validators are autonomous-only and offer a Custom Tool guardrail or an autonomous agent instead.

This restriction is enforced as [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1.

**Required completion gate:** after writing a conversational custom Tool
guardrail, run `uip agent refresh "<AGENT_NAME>" --output json`, then execute
`uip agent validate "<AGENT_NAME>" --output json`. Do not report the guardrail
task complete before the validation command has been attempted.

## Guardrail Schema (Base Fields)

Every guardrail object in the `guardrails` array shares these base fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$guardrailType` | string | Yes | Discriminator: `"custom"` or `"builtInValidator"` |
| `id` | string (UUID) | Yes | Unique identifier — generate a fresh UUID for each guardrail |
| `name` | string | Yes | Human-readable name |
| `description` | string | Yes | What this guardrail checks (can be empty `""`) |
| `action` | object | Yes | What happens on violation — see [Actions](#actions) |
| `enabledForEvals` | boolean | Yes | Whether this guardrail runs during evaluations |
| `selector` | object | Yes | Which scopes and tools this guardrail targets — see [Selector](#selector-scoping) |

## Selector (Scoping)

The `selector` field controls where the guardrail applies.

> **Conversational agents — Custom (deterministic) `Tool` guardrails ONLY; no `builtInValidator` at all. `"Agent"`/`"Llm"` scopes are NOT available.** (see [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Rule 1).

```json
"selector": {
  "scopes": ["Agent", "Llm", "Tool"],
  "matchNames": ["ToolName1", "ToolName2"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scopes` | string[] | Yes | Array of `"Agent"`, `"Llm"`, `"Tool"` — at least one required. **Conversational agents: use `["Tool"]` ONLY — `"Agent"`/`"Llm"` are NOT available, DO NOT use them**. |
| `matchNames` | string[] | Yes (when `Tool` in scopes) | Target tools by name. Required when `"Tool"` is in `scopes` — always list tool names explicitly. |

### Scope Definitions

| Scope | Applies to | Stage: PreExecution | Stage: PostExecution |
|-------|-----------|--------------------|--------------------|
| `Agent` | Agent-level input/output | Yes | Yes |
| `Llm` | LLM request/response | Yes | Yes |
| `Tool` | Individual tool calls | Yes | Yes |

> **Custom guardrails only support `Tool` scope with exactly one tool in `matchNames`.** `Agent` and `Llm` scopes are valid only for `builtInValidator` guardrails. Custom guardrail rules (word/number/boolean/always) depend on the specific tool's input/output schema, so `matchNames` must contain exactly one tool name. To apply the same custom rule to multiple tools, create a separate custom guardrail per tool.

### Combining Multiple Scopes

When a guardrail applies to more than one scope (e.g., both `Agent` and `Tool`), combine them into a **single guardrail** with multiple values in the `scopes` array — do NOT create separate guardrails per scope.

```json
"selector": { "scopes": ["Agent", "Tool"], "matchNames": ["MyTool"] }
```

### matchNames — Supported Tool Types

`matchNames` targets tools by their resource name in agent.json. Only the following tool types support guardrails:

| Tool type | Description |
|-----------|-------------|
| `agent` | Low-code or coded agent |
| `process` | RPA (XAML workflow) |
| `activity` | Activity-based tool |
| `builtInTool` | Built-in platform tool |
| `ixpTool` | IXP tool |
| Integration Service connector | IS connector tool |

Do not generate guardrails targeting tool types not in this list.

### matchNames — "All Tools" Behavior

When targeting all tools, `matchNames` must **explicitly list every tool resource name** from the agent's `resources/` directory. Do not omit `matchNames` to imply "all tools."

1. Read the agent's `resources/` directory to discover all tool resource names.
2. If the agent has **no tool resources**, do not add the guardrail — inform the user: *"No tool resources found in this agent. Cannot add a tool-scoped guardrail."*
3. Populate `matchNames` with every discovered tool name.

### Built-in Validator Scope Support

Not all validators support all scopes. Use the output from [Step 0](#step-0--fetch-available-validators-mandatory-first-step) (`uip agent guardrails list --output json`) to determine valid scopes and stages.

Each entry in the `Data` array contains:
- `Status` — `"Available"` or `"Unauthorised"` — only use validators with `"Available"` status
- `Validator` — the `validatorType` string (e.g., `"pii_detection"`)
- `AllowedScopes` — array of valid scope values (e.g., `["Agent", "Llm", "Tool"]`)
- `GuardrailStages` — object mapping each scope to its valid stages (e.g., `{"Agent": ["PreExecution", "PostExecution"]}`)
- `Parameters` — array of parameter definitions with `Type`, `Id`, and `Required`

Do not hardcode assumptions about scope/stage support or availability.

> **Conversational override** (see [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1)**.** `AllowedScopes` describes what a **built-in validator's** schema accepts — but built-in validators are **not usable at all** on conversational agents (they are autonomous-only). Do NOT author any `builtInValidator` guardrail for a conversational agent, at any scope. The only guardrails the conversational runtime runs are `$guardrailType: "custom"` deterministic rules scoped to `Tool`.

## Actions

Each guardrail has exactly one `action` object. The `$actionType` field is the **required discriminator** — it determines which other fields are valid.

### block — Stop Execution

Halts the agent run with an error message.

```json
"action": {
  "$actionType": "block",
  "reason": "PII detected in output — cannot proceed."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$actionType` | `"block"` | Yes | Action discriminator |
| `reason` | string | Yes | Error message shown to the user |

### log — Log Violation

Records the violation in logs without stopping execution.

```json
"action": {
  "$actionType": "log",
  "severityLevel": "Info"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$actionType` | `"log"` | Yes | Action discriminator |
| `severityLevel` | `"Info"` \| `"Warning"` \| `"Error"` | Yes | Log severity level |

### filter — Redact Fields

Removes specific fields from the input/output.

```json
"action": {
  "$actionType": "filter",
  "fields": [
    { "path": "ssn", "source": "output", "title": "SSN" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$actionType` | `"filter"` | Yes | Action discriminator |
| `fields` | array | Yes | Array of field references to redact |
| `fields[].path` | string | Yes | Field path (e.g., `"ssn"`, `"address.zip"`) |
| `fields[].source` | string | Yes | `"input"` or `"output"` |
| `fields[].title` | string | Yes | Human-readable field label |

### escalate — Hand Off to Action Center

Creates a task in an Action Center app for human review. Requires app discovery (`uip solution resources list --kind App`), a mandatory action-schema compatibility check, and a recipient — the complete action schema, recipient shapes, step-by-step workflow, and worked example are in [escalation-guide.md](escalation-guide.md). Do not author an `escalate` action without that guide.

## Custom Guardrails (`$guardrailType: "custom"`)

Deterministic rules you define — word matching, number comparison, boolean checks, universal triggers — with a `rules` array. `Tool` scope only, exactly one tool in `matchNames`; the only guardrail type the conversational runtime executes. Full schema, rule types, operators, field selectors, and worked examples: [custom-rules-guide.md](custom-rules-guide.md).

## Step 0 — Fetch Available Validators (Mandatory First Step)

Before adding any built-in validator guardrail, run:

```bash
uip agent guardrails list --output json
```

Before adding any built-in validator, check the `Data` array for the requested `Validator` value:

1. **Validator not found in list** — the validator does not exist on this tenant. Inform user: *"The built-in validator `<name>` is not available on your tenant. Check the validator name or contact your UiPath administrator."* Do not add the guardrail. Do NOT generate a custom guardrail as a fallback — inform the user and stop.
2. **`Status: "Available"`** — validator is licensed and ready. Proceed with configuration.
3. **`Status: "Unauthorised"`** — validator exists but the user is not entitled to use guardrails. Inform user: *"You are not entitled to use the `<name>` guardrail. You can view the configuration but cannot apply it to agents. Contact your UiPath administrator to enable guardrail entitlements."* Do not add the guardrail.
4. **Validator does not support the requested scope** — if the user requests a scope (e.g., `Agent`, `Llm`) not listed in `AllowedScopes` for that validator, inform the user which scopes are supported. Do NOT auto-generate a custom guardrail as a workaround. You may suggest a custom guardrail as an alternative, but only if the user explicitly confirms — and only for `Tool` scope (custom guardrails do not support `Agent` or `Llm` scopes).

Only configure guardrails for validators with `Status: "Available"`.

## Built-in Validator Guardrails (`$guardrailType: "builtInValidator"`)

Built-in validators call the UiPath Guardrails API. They have a `validatorType` string and a `validatorParameters` array.

> **Critical:** Each parameter object requires a `$parameterType` discriminator and uses `id` (not `name`) for the parameter identifier.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "<uuid>",
  "name": "PII Detection",
  "description": "Detects PII in tool outputs",
  "enabledForEvals": true,
  "selector": { "scopes": ["Tool"], "matchNames": ["MyToolName"] },
  "action": { "$actionType": "block", "reason": "PII detected" },
  "validatorType": "pii_detection",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "entities",
      "value": ["Email", "PhoneNumber"]
    }
  ]
}
```

### Parameter Types

| `$parameterType` | Use for | `value` type |
|-------------------|---------|-------------|
| `"enum-list"` | Array parameters (e.g., `entities`, `harmfulContentEntities`, `ipEntities`) | string[] |
| `"map-enum"` | Threshold maps (e.g., `entityThresholds`, `harmfulContentEntityThresholds`) | object (keys = entity names, values = numbers) |
| `"number"` | Scalar numbers (e.g., `threshold`) | number |
| `"enum"` | Scalar single-choice (e.g., `model` for `llm_as_judge`) | string |
| `"text"` | Free text (e.g., `guardrailText` for `llm_as_judge`) | string |
| `"text-list"` | Text arrays (e.g., `positiveExamples`, `negativeExamples` for `llm_as_judge`) | string[] |

### Validators Quick Reference

> **These are all `builtInValidator` guardrails — autonomous-only. NONE are usable on conversational agents** (see [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1); the conversational runtime runs only Custom deterministic `Tool` guardrails. The table below describes autonomous support.

| Validator | Scopes (autonomous) | Conversational | Stages | Supported Actions |
|-----------|---------------------|----------------|--------|-------------------|
| `pii_detection` | Agent, Llm, Tool | **Not usable** (autonomous-only) | Pre + Post | Block, Log, Escalate |
| `prompt_injection` | Llm | **Not usable** (autonomous-only) | Pre only | Block, Log, Escalate |
| `harmful_content` | Agent, Llm, Tool | **Not usable** (autonomous-only) | Pre + Post | Block, Log, Escalate |
| `intellectual_property` | Llm, Agent | **Not usable** (autonomous-only) | Post only | Block, Log, Escalate |
| `user_prompt_attacks` | Llm | **Not usable** (autonomous-only) | Pre only | Block, Log, Escalate |
| `llm_as_judge` | Agent, Llm, Tool | **Not usable** (autonomous-only) | Pre + Post | Block, Log, Escalate |

> **`llm_as_judge` needs an LLM Gateway model.** Its `model` parameter comes back with an **empty** `Options` list from `uip agent guardrails list` — the valid values live in LLM Gateway, not the catalog. Run `uip agent guardrails llm-as-judge-models --output json` and use a `ModelId` from the result for the `model` parameter (prefer a non-preview model; a small/fast model such as a Haiku / mini class is a sound judge default). If the command returns no models or fails (no LLM Gateway access), tell the user and ask them to configure a model in their LLM Gateway or supply a model ID. Its other parameters are `guardrailText` (`text`, required), `positiveExamples` / `negativeExamples` (`text-list`, optional), and `threshold` (`number`, optional).

Run `uip agent guardrails list --output json` to get the authoritative list. Only use validators where `Status` is `"Available"`. Use the output to populate `validatorType`, `selector.scopes`, and `validatorParameters` fields. **These built-in validators are autonomous-only — do NOT author any of them on a conversational agent (they will not run at any scope). Conversational agents use Custom deterministic `Tool` guardrails only.**
**How to map `uip agent guardrails list` output to guardrail JSON:**

| CLI field | Maps to |
|-----------|---------|
| `Status` | Gate check — only proceed if `"Available"` |
| `Validator` | `validatorType` value |
| `AllowedScopes` | Valid values for `selector.scopes` (autonomous only — built-in validators are not usable on conversational agents; see [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1). |
| `GuardrailStages[scope]` | Valid execution stages for that scope |
| `Parameters[].Id` | `validatorParameters[].id` |
| `Parameters[].Type` | `validatorParameters[].$parameterType` |
| `IsByo` | Disambiguates a bring-your-own (BYOG) entry from a built-in one — see [BYO (bring-your-own) guardrails](#byo-bring-your-own-guardrails) below. Not itself a JSON field. |
| `ByoValidatorName` | `byoValidatorName` value — include this field to pin the guardrail to this exact BYO configuration. Required whenever more than one entry shares this `Validator` name (a built-in plus one or more BYOG configurations). |

> **Important:** PII entity names use PascalCase (`"Email"`, not `"email_address"`). Harmful content categories use PascalCase (`"Hate"`, not `"hate"`). Scope values use PascalCase (`"Agent"`, `"Llm"`, `"Tool"`).

## BYO (bring-your-own) guardrails

A validator can be fulfilled by a tenant-registered **external** provider (a "BYOG" configuration — e.g. Azure AI Content Safety, Databricks AI Guardrails) instead of, or alongside, UiPath's own built-in implementation. A tenant admin registers these at Admin → AI Trust Layer → Guardrails Configurations or via `uip guardrails byo-configurations create`; see [uipath-platform § BYO Guardrail Configurations](/uipath:uipath-platform) for the admin-side lifecycle commands (`uip guardrails byo-configurations list|create|update|delete`).

- **`Validator` is not unique.** A tenant with a BYOG `harmful_content` configuration sees **two** entries named `harmful_content` in `uip agent guardrails list` output — one built-in, one BYO. Use `IsByo` to tell them apart; never assume a single match.
- **Filter to BYO-only entries** with `uip agent guardrails list --byo --output json` when the user specifically wants to see or target a BYO-backed validator.
- **BYO entries carry extra fields**: `ByoValidatorName`, `ByoConnectionId`, `ByoConfigurationId`, `ByoConnectorName`, `ByoConnectorKey`, `FolderKey` — alongside the same `Parameters`/`AllowedScopes`/`GuardrailStages`/`Status` shape a built-in entry has.
- **To author a guardrail against a specific BYO configuration**, build the `builtInValidator` guardrail exactly as for a built-in validator (same `validatorType`, same `validatorParameters` from that entry's `Parameters`), and add `byoValidatorName` set to that entry's `ByoValidatorName`. Omit it to use the built-in implementation. (`ByoConfigurationId` is the configuration's own admin-side id — useful for cross-referencing `uip guardrails byo-configurations list`, but it is not what the guardrail JSON carries; `ByoValidatorName` is unique per tenant and is the value that pins it.)
- **`Status: "Disabled"` on a BYO entry** means the tenant switched that specific configuration off — the entry still shows (it doesn't vanish), so a disabled BYOG configuration is distinguishable from one that was never set up. Do not author a guardrail against a `Disabled` BYO entry; treat it the same as `Unauthorised` (skip, tell the user).

## Full Examples

### Example 1: Block PII in Agent and Tool Outputs

```json
{
  "$guardrailType": "builtInValidator",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "PII detection guardrail",
  "description": "This validator is designed to detect personally identifiable information using Azure Cognitive Services",
  "validatorType": "pii_detection",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "entities",
      "value": ["Email", "PhoneNumber", "CreditCardNumber", "USSocialSecurityNumber"]
    },
    {
      "$parameterType": "map-enum",
      "id": "entityThresholds",
      "value": {
        "Email": 0.8,
        "PhoneNumber": 0.7,
        "CreditCardNumber": 0.9,
        "USSocialSecurityNumber": 0.9
      }
    }
  ],
  "action": {
    "$actionType": "block",
    "reason": "PII detected in output — execution blocked."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Agent", "Tool"],
    "matchNames": ["MyToolName"]
  }
}
```

### Example 2: Log Harmful Content at Agent Level

```json
{
  "$guardrailType": "builtInValidator",
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "name": "Harmful content guardrail",
  "description": "Logs harmful content violations at agent level without blocking",
  "validatorType": "harmful_content",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "harmfulContentEntities",
      "value": ["Hate", "SelfHarm", "Sexual", "Violence"]
    },
    {
      "$parameterType": "map-enum",
      "id": "harmfulContentEntityThresholds",
      "value": {
        "Hate": 2,
        "SelfHarm": 2,
        "Sexual": 4,
        "Violence": 2
      }
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Warning"
  },
  "enabledForEvals": false,
  "selector": {
    "scopes": ["Agent"]
  }
}
```

### Example 3: Prompt Injection Detection

```json
{
  "$guardrailType": "builtInValidator",
  "id": "e5f6a7b8-c9d0-1234-efab-567890123456",
  "name": "Prompt injection guardrail",
  "description": "This validator is provided by Noma Security and is built to detect malicious attack attempts (e.g. prompt injection, jailbreak) in LLM calls.",
  "validatorType": "prompt_injection",
  "validatorParameters": [
    {
      "$parameterType": "number",
      "id": "threshold",
      "value": 0.5
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Info"
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Llm"]
  }
}
```

### Example 4: User Prompt Attack Detection — Block Jailbreaks

No parameters required — binary detection via Azure Prompt Shield. Llm PreExecution only.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "f1a2b3c4-d5e6-7890-abcd-ef0123456789",
  "name": "User prompt attack guardrail",
  "description": "Detects jailbreak attempts and indirect prompt injection via Azure Prompt Shield",
  "validatorType": "user_prompt_attacks",
  "validatorParameters": [],
  "action": {
    "$actionType": "block",
    "reason": "Adversarial input detected — execution blocked."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Llm"]
  }
}
```

### Example 5: Intellectual Property Detection — Block Copyrighted Text and Code

PostExecution only — no content exists to check before the LLM generates output.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "a2b3c4d5-e6f7-8901-bcde-f01234567890",
  "name": "IP detection guardrail",
  "description": "Detects copyrighted text and licensed GitHub code in LLM output",
  "validatorType": "intellectual_property",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "ipEntities",
      "value": ["Text", "Code"]
    }
  ],
  "action": {
    "$actionType": "block",
    "reason": "Protected material detected in output — execution blocked."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Llm"]
  }
}
```

### Custom-rule, filter, and escalation examples

Moved to the owning guides:

- Custom word rules (block / log / specific fields with titles) and the filter redaction example → [custom-rules-guide.md § Examples](custom-rules-guide.md#examples)
- Escalate PII violations to Action Center → [escalation-guide.md](escalation-guide.md#example-escalate-pii-violations-to-action-center--multiple-tool-targets)

## agent.json with Guardrails

Add the `guardrails` array at the agent.json root level alongside `settings`, `messages`, etc.:

```json
{
  "version": "1.1.0",
  "settings": { "..." : "..." },
  "inputSchema": { "..." : "..." },
  "outputSchema": { "..." : "..." },
  "metadata": { "..." : "..." },
  "type": "lowCode",
  "guardrails": [
    {
      "$guardrailType": "builtInValidator",
      "id": "<UUID>",
      "name": "PII detection guardrail",
      "description": "Detects PII",
      "validatorType": "pii_detection",
      "validatorParameters": [
        { "$parameterType": "enum-list", "id": "entities", "value": ["Email", "PhoneNumber"] },
        { "$parameterType": "map-enum", "id": "entityThresholds", "value": { "Email": 0.5, "PhoneNumber": 0.5 } }
      ],
      "action": { "$actionType": "block", "reason": "PII detected" },
      "enabledForEvals": true,
      "selector": { "scopes": ["Agent"] }
    }
  ],
  "messages": [ "..." ],
  "projectId": "<UUID>"
}
```


## What NOT to Do

> Canonical guardrail anti-patterns — discriminator omission (`$actionType` / `$parameterType` / `$ruleType` / `$selectorType`), lowercase scope values, populating `guardrail.policies` on tool resources, and UUID reuse — live in [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) § What NOT to Do. The validator-specific anti-patterns below extend (do not repeat) that canonical list.

1. **Do not use snake_case for PII entity names** — use PascalCase: `"Email"` not `"email_address"`, `"PhoneNumber"` not `"phone_number"`, `"USSocialSecurityNumber"` not `"us_ssn"`.
2. **Do not add `prompt_injection` to Tool or Agent scope** — it only works with `"Llm"` scope, PreExecution stage.
3. **Do not add `user_prompt_attacks` to Tool or Agent scope** — Llm only, PreExecution only.
4. **Do not add `intellectual_property` to Tool scope** — only `"Llm"` and `"Agent"` scopes are supported.
5. **Do not add `intellectual_property` to PreExecution stage** — PostExecution only.
6. **Do not omit `matchNames` when `Tool` is in `scopes`** — always explicitly list the target tool names. See [matchNames — "All Tools" Behavior](#matchnames--all-tools-behavior).
7. **Do not use `filter` action on built-in validators** — `"$actionType": "filter"` is only supported on deterministic (`custom`) rules. Every built-in validator (`$guardrailType: "builtInValidator"`) supports only `block`, `log`, and `escalate` (see the [Validators Quick Reference](#validators-quick-reference) § Supported Actions).
8. **Do not use odd numbers or floats for `harmfulContentEntityThresholds`** — only `0`, `2`, `4`, `6` are valid severity values. Values like `3` or `2.5` cause validation errors.
9. **Do not add a built-in validator without first running `uip agent guardrails list --output json`** — always fetch the list, verify the validator exists, and confirm `Status` is `"Available"`. Adding an `Unauthorised` or non-existent validator causes runtime failures.
10. **Do not use Action Center apps with `Type: "VB Action"` or `Type: "Coded"` as escalation targets** — only entries with `Type: "Workflow Action"` can back a guardrail escalation. Always filter `uip solution resources list --kind App` results by this type.
11. **Do not use `--kind Process` (Type: `"webApp"`) to find escalation apps** — those entries are code-behind processes, not app deployments. Their `Key` values are process release GUIDs, not app IDs. Always use `--kind App` with `Type: "Workflow Action"`.
12. **Do not put `"solution_folder"` into `app.folderName`** — set it to the literal `Folder` from `uip solution resources list --kind App` (e.g., `"Shared/Approvals"`). `uip agent refresh` translates it to `folderPath` in the App binding inside `bindings_v2.json`. Omit `app.folderId`. `FolderKey` from `resource list` is NOT used in any `app.*` field — it IS correct in `debug_overwrites.json` entries, where it maps the solution-embedded resource to its real runtime location.
13. **Do not add a Tool-scoped guardrail before the tool is added to the agent** — every name in `selector.matchNames` must match an existing tool resource under `<AGENT_NAME>/resources/<ToolName>/resource.json`. A guardrail referencing a non-existent tool will be caught by `uip agent validate` and fail with an error. Always run `uip agent tool list` first (Step 2) and confirm target tools are present.
14. **Do not skip action schema validation for escalation apps** — before writing a guardrail with `"$actionType": "escalate"`, fetch the app's action schema and verify all required inputs (8), outputs (3), and outcomes (2) are present by name. If any are missing, report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` and do not proceed. See [escalation-guide.md § Adding an escalation guardrail](escalation-guide.md#adding-an-escalation-guardrail--step-by-step).
15. **Do not use `Agent` or `Llm` scopes on custom guardrails** — custom guardrails (`$guardrailType: "custom"`) only support `"Tool"` scope with exactly one tool in `matchNames`. Custom rules depend on the tool's input/output schema, so they cannot target multiple tools. Create a separate custom guardrail per tool.
16. **Do not auto-generate a custom guardrail as fallback** — when a built-in validator is unavailable, unsupported for the requested scope, or unauthorized, inform the user and stop. Do not silently generate a custom guardrail as a workaround. You may suggest a custom guardrail alternative (for `Tool` scope only), but only generate it after explicit user confirmation.
17. **Do not create separate guardrails per scope** — when a guardrail applies to multiple scopes (e.g., `Agent` and `Tool`), combine them into a single guardrail with `"scopes": ["Agent", "Tool"]`. Do not create two separate guardrail objects with identical configuration differing only in scope.
18. **Do not attempt OR logic within a single guardrail** — all rules and all fields within a guardrail are combined with AND. OR is not supported. To achieve OR behavior, create separate guardrails — one per condition branch.
19. **Do not generate guardrails targeting unsupported tool types** — `matchNames` can only reference tools of supported types: agent, process, activity, builtInTool, ixpTool, or Integration Service connector. Do not generate guardrails with `matchNames` targeting other tool types.
20. **Do not omit `matchNames` to target "all tools"** — always explicitly list every tool resource name in `matchNames`. Read the agent's `resources/` directory first. If the agent has no tool resources, do not add the guardrail.
21. **Do not assume `Validator` is unique** — a tenant can have both a built-in and one or more bring-your-own (BYOG) entries sharing the same `Validator` name. Always check `IsByo` before treating two same-named entries as a duplicate or conflict, and set `byoValidatorName` when targeting a specific BYO entry. See [BYO (bring-your-own) guardrails](#byo-bring-your-own-guardrails).
22. **Do not leave a key in `harmfulContentEntityThresholds` (or any `map-enum` threshold parameter, e.g. `entityThresholds`) that is not in the corresponding entities list** — threshold keys must exactly match the selected entities: no extra keys, no missing keys. `uip agent validate` does NOT flag the mismatch, so a stale extra key passes validation and silently misconfigures the guardrail. When editing the entities list, prune the thresholds map in the same edit.
23. **Do not reverse-engineer guardrail schemas from the CLI installation or SDK packages** — never grep `/usr/lib/node_modules/@uipath/**/dist/*.js`, read minified bundles, or import-probe packages to confirm a field. This reference is the schema authority (see [Overview](#overview)); write the guardrail from the complete examples here and let `uip agent validate` confirm the shape.

## References

- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) — canonical low-code rules and guardrail anti-patterns (discriminators, scope casing, populating `guardrail.policies` on tool resources, UUID reuse)
- [../../project-lifecycle.md](../../project-lifecycle.md) § `uip agent guardrails list` — CLI reference for validator discovery
- [../../agent-definition.md](../../agent-definition.md) § Guardrails — root-level placement in `agent.json`
- [escalation-guide.md](escalation-guide.md) — `escalate` action schema, app verification workflow, worked example
- [custom-rules-guide.md](custom-rules-guide.md) — custom (deterministic) guardrail schema, rule types, field selectors, worked examples
