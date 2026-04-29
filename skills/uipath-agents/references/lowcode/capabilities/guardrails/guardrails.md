# Guardrails Reference

## Overview

Guardrails are safeguards that inspect agent inputs and outputs for policy violations (PII, harmful content, prompt injection, intellectual property, custom rules). They are configured at the **agent.json root level** as a `guardrails` array.

Two types exist:
- **`custom`** — deterministic rules you define (word matching, number comparison, boolean checks, universal triggers)
- **`builtInValidator`** — UiPath Guardrails API validators (PII detection, harmful content, prompt injection, IP protection, user prompt attacks)

> **Tool-level `guardrail.policies`** is auto-populated by `uip agent validate` — it copies the root-level guardrails that target each tool (via `matchNames`) into the tool's `guardrail.policies` array. Do not manually edit `guardrail.policies` on tool resources. Always configure guardrails at the agent.json root `guardrails` array.

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

```json
"selector": {
  "scopes": ["Agent", "Llm", "Tool"],
  "matchNames": ["ToolName1", "ToolName2"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scopes` | string[] | Yes | Array of `"Agent"`, `"Llm"`, `"Tool"` — at least one required |
| `matchNames` | string[] | No | Target specific tools by name. |

### Scope Definitions

| Scope | Applies to | Stage: PreExecution | Stage: PostExecution |
|-------|-----------|--------------------|--------------------|
| `Agent` | Agent-level input/output | Yes | Yes |
| `Llm` | LLM request/response | Yes | Yes |
| `Tool` | Individual tool calls | Yes | Yes |

### Built-in Validator Scope Support

Not all validators support all scopes. Run the following command to get the authoritative list of validators, their allowed scopes, stages, and parameters:

```bash
uip agent guardrails list --output json
```

Each entry in the `Data` array contains:
- `Validator` — the `validatorType` string (e.g., `"pii_detection"`)
- `AllowedScopes` — array of valid scope values (e.g., `["Agent", "Llm", "Tool"]`)
- `GuardrailStages` — object mapping each scope to its valid stages (e.g., `{"Agent": ["PreExecution", "PostExecution"]}`)
- `Parameters` — array of parameter definitions with `Type`, `Id`, and `Required`

Use this output to determine which scopes and stages are valid for each validator. Do not hardcode assumptions about scope/stage support.

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

Creates a task in an Action Center app for human review.

```json
"action": {
  "$actionType": "escalate",
  "app": {
    "id": "<APP_ID>",
    "name": "<APP_NAME>",
    "version": "0",
    "folderId": "<FOLDER_ID>",
    "folderName": "solution_folder"
  },
  "recipient": {
    "type": 1,
    "value": "<USER_GUID>",
    "displayName": "<DISPLAY_NAME>"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$actionType` | `"escalate"` | Yes | Action discriminator |
| `app` | object | Yes | Action Center app reference |
| `app.id` | string | Yes | Deployed app ID |
| `app.name` | string | Yes | Deployed app name |
| `app.version` | string | Yes | App version (e.g., `"0"`) |
| `app.folderId` | string | Yes | Folder ID where the app is deployed |
| `app.folderName` | string | Yes | Use `"solution_folder"` |
| `recipient` | object | Yes | Task recipient |
| `recipient.type` | integer | Yes | Recipient type: 1=UserId, 2=GroupId, 3=Email, 4=AssetUserEmail, 5=StaticGroupName, 6=AssetGroupName |
| `recipient.value` | string | Yes | User GUID, group GUID, or email address (depends on `type`) |
| `recipient.displayName` | string | No | Human-readable name (omit for `type: 3` email recipients) |

## Custom Guardrails (`$guardrailType: "custom"`)

Custom guardrails use deterministic rules you define. They have a `rules` array containing one or more rule objects.

> **Critical discriminator fields:** Every rule needs `$ruleType`. Every field selector needs `$selectorType`. Every action needs `$actionType`. Missing any of these causes validation failure.

```json
{
  "$guardrailType": "custom",
  "id": "<uuid>",
  "name": "Block forbidden terms",
  "description": "Prevents agent from using blacklisted words",
  "enabledForEvals": true,
  "selector": { "scopes": ["Agent", "Llm"] },
  "action": { "$actionType": "block", "reason": "Forbidden term detected" },
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "all"
      },
      "operator": "contains",
      "value": "CONFIDENTIAL"
    }
  ]
}
```

### Rule Types

#### Word Rules (`$ruleType: "word"`)

String matching against field values.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"word"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector — see [Field Selectors](#field-selectors) |
| `operator` | string | Yes | Match operator |
| `value` | string | Yes | Value to match against |

**Operators:**

| Operator | Behavior |
|----------|----------|
| `contains` | Field value contains the string |
| `equals` | Field value exactly equals the string |
| `startsWith` | Field value starts with the string |
| `endsWith` | Field value ends with the string |
| `matchesRegex` | Field value matches the regular expression |
| `doesNotContain` | Field value does not contain the string |
| `doesNotEqual` | Field value does not equal the string |
| `doesNotStartWith` | Field value does not start with the string |
| `doesNotEndWith` | Field value does not end with the string |
| `isEmpty` | Field value is empty (no `value` needed) |
| `isNotEmpty` | Field value is not empty (no `value` needed) |

#### Number Rules (`$ruleType: "number"`)

Numeric comparison against field values.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"number"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector |
| `operator` | string | Yes | Comparison operator |
| `value` | number | Yes | Value to compare against |

**Operators:** `equals`, `doesNotEqual`, `greaterThan`, `greaterThanOrEqual`, `lessThan`, `lessThanOrEqual`

#### Boolean Rules (`$ruleType: "boolean"`)

Boolean equality check.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"boolean"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector |
| `operator` | `"equals"` | Yes | Only `equals` is supported |
| `value` | boolean | Yes | `true` or `false` |

#### Always / Universal Rules (`$ruleType: "always"`)

Fires on every input/output — no condition check. Use `applyTo` to control whether it runs on input, output, or inputAndOutput.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"always"` | Yes | Rule type discriminator |
| `applyTo` | `"input"` \| `"output"` \| `"inputAndOutput"` | Yes | When the rule fires |

### Field Selectors

Each rule (except `always`) has a `fieldSelector` object with a `$selectorType` discriminator.

**All fields:**
```json
"fieldSelector": {
  "$selectorType": "all"
}
```

**Specific fields:**
```json
"fieldSelector": {
  "$selectorType": "specific",
  "fields": [
    { "path": "content", "source": "output" },
    { "path": "email", "source": "input", "title": "Email Address" }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|-------------|-------------|
| `$selectorType` | `"all"` \| `"specific"` | Yes | Discriminator — match all fields or named fields |
| `fields` | array | Yes (when `"specific"`) | Array of field references |
| `fields[].path` | string | Yes | Field path from the agent's input/output schema |
| `fields[].source` | `"input"` \| `"output"` | Yes | Which side to inspect |
| `fields[].title` | string | No | Human-readable label |

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
  "selector": { "scopes": ["Tool"] },
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
| `"number"` | Scalar numbers (e.g., `threshold` for prompt injection) | number |

### Validators Quick Reference

| Validator | Scopes | Stages | Supported Actions |
|-----------|--------|--------|-------------------|
| `pii_detection` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `prompt_injection` | Llm | Pre only | Block, Log, Escalate |
| `harmful_content` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `intellectual_property` | Llm, Agent | Post only | Block, Log, Escalate |
| `user_prompt_attacks` | Llm | Pre only | Block, Log, Escalate |

Run `uip agent guardrails list --output json` to get the authoritative list. Use the output to populate `validatorType`, `selector.scopes`, and `validatorParameters` fields.

**How to map `uip agent guardrails list` output to guardrail JSON:**

| CLI field | Maps to |
|-----------|---------|
| `Validator` | `validatorType` value |
| `AllowedScopes` | Valid values for `selector.scopes` |
| `GuardrailStages[scope]` | Valid execution stages for that scope |
| `Parameters[].Id` | `validatorParameters[].id` |
| `Parameters[].Type` | `validatorParameters[].$parameterType` |

> **Important:** PII entity names use PascalCase (`"Email"`, not `"email_address"`). Harmful content categories use PascalCase (`"Hate"`, not `"hate"`). Scope values use PascalCase (`"Agent"`, `"Llm"`, `"Tool"`).

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
    "scopes": ["Agent", "Tool"]
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

### Example 6: Custom Word Rule — Block Forbidden Terms in Specific Tool Output

```json
{
  "$guardrailType": "custom",
  "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "name": "Block forbidden output",
  "description": "",
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "specific",
        "fields": [
          {
            "path": "content",
            "source": "output"
          }
        ]
      },
      "operator": "contains",
      "value": "CONFIDENTIAL"
    }
  ],
  "action": {
    "$actionType": "block",
    "reason": "Forbidden term detected in tool output."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Tool"],
    "matchNames": ["MyToolName"]
  }
}
```

### Example 7: Custom Word Rule — Log on All Fields

```json
{
  "$guardrailType": "custom",
  "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "name": "Log sensitive terms",
  "description": "",
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "all"
      },
      "operator": "contains",
      "value": "password"
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Warning"
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Agent", "Llm"]
  }
}
```

### Example 8: Escalate PII Violations to Action Center — Multiple Tool Targets

Escalates to an Action Center app when PII is detected in output from specific tools. Uses `matchNames` to target multiple tools and `escalate` action with `app` and `recipient`.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "10d5f10f-da4e-4bf1-ace9-dd880e33d9be",
  "name": "PII detection guardrail",
  "description": "This validator is designed to detect personally identifiable information using Azure Cognitive Services",
  "validatorType": "pii_detection",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "entities",
      "value": ["Email", "Address"]
    },
    {
      "$parameterType": "map-enum",
      "id": "entityThresholds",
      "value": {
        "Email": 0.5,
        "Address": 0.5
      }
    }
  ],
  "action": {
    "$actionType": "escalate",
    "app": {
      "id": "<APP_ID>",
      "name": "<APP_NAME>",
      "version": "0",
      "folderId": "<FOLDER_ID>",
      "folderName": "solution_folder"
    },
    "recipient": {
      "type": 1,
      "value": "<USER_GUID>",
      "displayName": "<DISPLAY_NAME>"
    }
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Agent", "Tool"],
    "matchNames": ["Agent", "Get Instance Details"]
  }
}
```

### Example 9: Custom Word Rule — Specific Fields with Titles on a Named Tool

Inspects specific output fields (with human-readable `title`) of an Integration Service tool. Logs a violation when the field value contains a forbidden string.

```json
{
  "$guardrailType": "custom",
  "id": "68005ea0-9d46-4094-8113-d497f53fd17f",
  "name": "Log sensitive URLs in Jira output",
  "description": "",
  "rules": [
    {
      "$ruleType": "word",
      "fieldSelector": {
        "$selectorType": "specific",
        "fields": [
          {
            "path": "baseUrl",
            "source": "output",
            "title": "Base url"
          },
          {
            "path": "scmInfo",
            "source": "output",
            "title": "Scm info"
          }
        ]
      },
      "operator": "contains",
      "value": "internal.corp"
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Info"
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Tool"],
    "matchNames": ["Get Instance Details"]
  }
}
```

### Example 10: Filter — Redact Fields from Tool Output

Redacts specific fields from a tool's output instead of blocking or logging. Use when you want the agent to continue but with sensitive data removed.

```json
{
  "$guardrailType": "custom",
  "id": "f6a7b8c9-d0e1-2345-abcd-678901234567",
  "name": "Redact SSN from output",
  "description": "Removes SSN field from tool output before returning to user",
  "rules": [
    {
      "$ruleType": "always",
      "applyTo": "output"
    }
  ],
  "action": {
    "$actionType": "filter",
    "fields": [
      { "path": "ssn", "source": "output", "title": "SSN" },
      { "path": "taxId", "source": "output", "title": "Tax ID" }
    ]
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Tool"],
    "matchNames": ["GetCustomerProfile"]
  }
}
```

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

> Canonical guardrail anti-patterns — discriminator omission (`$actionType` / `$parameterType` / `$ruleType` / `$selectorType`), lowercase scope values, manual `guardrail.policies` edits on tool resources, and UUID reuse — live in [../../critical-rules.md](../../critical-rules.md) § What NOT to Do. The validator-specific anti-patterns below extend (do not repeat) that canonical list.

1. **Do not use snake_case for PII entity names** — use PascalCase: `"Email"` not `"email_address"`, `"PhoneNumber"` not `"phone_number"`, `"USSocialSecurityNumber"` not `"us_ssn"`.
2. **Do not add `prompt_injection` to Tool or Agent scope** — it only works with `"Llm"` scope, PreExecution stage.
3. **Do not add `user_prompt_attacks` to Tool or Agent scope** — Llm only, PreExecution only.
4. **Do not add `intellectual_property` to Tool scope** — only `"Llm"` and `"Agent"` scopes are supported.
5. **Do not add `intellectual_property` to PreExecution stage** — PostExecution only.
6. **Do not forget `matchNames` when targeting a specific tool** — without it, the guardrail applies to all tools in the scope.
7. **Do not use `filter` action on built-in validators** — `"$actionType": "filter"` is only supported on deterministic rules. All built-in validators (`pii_detection`, `intellectual_property`, `prompt_injection`, `user_prompt_attacks`, `harmful_content`) support only `block`, `log`, and `escalate`.
8. **Do not use odd numbers or floats for `harmfulContentEntityThresholds`** — only `0`, `2`, `4`, `6` are valid severity values. Values like `3` or `2.5` cause validation errors.

## Walkthrough

Use when adding input/output safeguards (PII detection, harmful content blocking, custom word rules) to a low-code agent. Guardrails are configured at the agent.json root `guardrails` array.

> **MANDATORY: Read this file BEFORE writing any guardrail JSON.** The guardrail schema uses discriminator fields (`$actionType`, `$parameterType`, `$ruleType`, `$selectorType`) that cannot be guessed. PII detection uses `$guardrailType: "builtInValidator"` with `validatorType: "pii_detection"` — NOT `$guardrailType: "pii"`. Parameters use `id` (not `name`) and require `$parameterType`. Actions use `$actionType` (not `type`). PII entities are PascalCase (`"Email"`, not `"email_address"`). There is no `pattern`, `target`, or `message` field.

### Step 1 — Verify existing agent

Ensure the agent project exists and has a valid `agent.json`. If starting fresh, follow [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent) first.

### Step 2 — Discover available validators

```bash
uip agent guardrails list --output json
```

Use the output to determine which `validatorType` values exist, their allowed scopes, stages, and required parameters. Do not hardcode assumptions — always check the CLI output for the authoritative list.

### Step 3 — Add a guardrail to agent.json

For built-in validators, see [Built-in Validator Guardrails](#built-in-validator-guardrails-guardrailtype-builtinvalidator) for the full schema and worked examples (Examples 1–5, 8).

For custom rules (word/number/boolean/always), see [Custom Guardrails](#custom-guardrails-guardrailtype-custom) for the full schema and worked examples (Examples 6, 7, 9, 10).

Quick template — built-in PII validator:

```json
"guardrails": [
  {
    "$guardrailType": "builtInValidator",
    "id": "<GENERATE_UUID>",
    "name": "PII detection guardrail",
    "description": "Detects personally identifiable information using Azure Cognitive Services",
    "validatorType": "pii_detection",
    "validatorParameters": [
      {
        "$parameterType": "enum-list",
        "id": "entities",
        "value": ["Email", "PhoneNumber", "CreditCardNumber"]
      },
      {
        "$parameterType": "map-enum",
        "id": "entityThresholds",
        "value": {
          "Email": 0.5,
          "PhoneNumber": 0.5,
          "CreditCardNumber": 0.5
        }
      }
    ],
    "action": {
      "$actionType": "block",
      "reason": "PII detected in output."
    },
    "enabledForEvals": true,
    "selector": {
      "scopes": ["Agent"]
    }
  }
]
```

### Step 4 — Validate

```bash
uip agent validate "<AGENT_NAME>" --output json
```

Confirm the guardrails appear in the validated output without errors.

## References

- [../../critical-rules.md](../../critical-rules.md) — canonical low-code rules and guardrail anti-patterns (discriminators, scope casing, manual `guardrail.policies` edits, UUID reuse)
- [../../project-lifecycle.md](../../project-lifecycle.md) § `uip agent guardrails list` — CLI reference for validator discovery
- [../../agent-definition.md](../../agent-definition.md) § Guardrails — root-level placement in `agent.json`
