# Built-in Validator Guardrails

Walkthrough for adding `$guardrailType: "builtInValidator"` guardrails. Built-in validators call the UiPath Guardrails API — they enforce PII detection, harmful content, prompt injection, intellectual property, and user prompt attacks.

For custom deterministic rules, see [custom-rules.md](custom-rules.md). For shared base schema (selector, actions, agent.json placement), see [guardrails.md](guardrails.md).

## Schema

Built-in validators have a `validatorType` string and a `validatorParameters` array.

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

## Parameter Types

| `$parameterType` | Use for | `value` type |
|-------------------|---------|-------------|
| `"enum-list"` | Array parameters (e.g., `entities`, `harmfulContentEntities`, `ipEntities`) | string[] |
| `"map-enum"` | Threshold maps (e.g., `entityThresholds`, `harmfulContentEntityThresholds`) | object (keys = entity names, values = numbers) |
| `"number"` | Scalar numbers (e.g., `threshold` for prompt injection) | number |

## Validators Quick Reference

| Validator | Scopes | Stages | Supported Actions |
|-----------|--------|--------|-------------------|
| `pii_detection` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `prompt_injection` | Llm | Pre only | Block, Log, Escalate |
| `harmful_content` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `intellectual_property` | Llm, Agent | Post only | Block, Log, Escalate |
| `user_prompt_attacks` | Llm | Pre only | Block, Log, Escalate |

Run `uip agent guardrails list --output json` to get the authoritative list. Use the output to populate `validatorType`, `selector.scopes`, and `validatorParameters` fields.

## Mapping CLI Output to Guardrail JSON

| CLI field | Maps to |
|-----------|---------|
| `Validator` | `validatorType` value |
| `AllowedScopes` | Valid values for `selector.scopes` |
| `GuardrailStages[scope]` | Valid execution stages for that scope |
| `Parameters[].Id` | `validatorParameters[].id` |
| `Parameters[].Type` | `validatorParameters[].$parameterType` |

> **Important:** PII entity names use PascalCase (`"Email"`, not `"email_address"`). Harmful content categories use PascalCase (`"Hate"`, not `"hate"`). Scope values use PascalCase (`"Agent"`, `"Llm"`, `"Tool"`).

## Examples

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

### Example 6: Escalate PII Violations to Action Center — Multiple Tool Targets

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

## Gotchas

Validator-specific gotchas (each from a real validation failure):

- **Do not use snake_case for PII entity names** — use PascalCase: `"Email"` not `"email_address"`, `"PhoneNumber"` not `"phone_number"`, `"USSocialSecurityNumber"` not `"us_ssn"`.
- **Do not add `prompt_injection` to Tool or Agent scope** — it only works with `"Llm"` scope, PreExecution stage.
- **Do not add `user_prompt_attacks` to Tool or Agent scope** — Llm only, PreExecution only.
- **Do not add `intellectual_property` to Tool scope** — only `"Llm"` and `"Agent"` scopes are supported.
- **Do not add `intellectual_property` to PreExecution stage** — PostExecution only.
- **Do not use `filter` action on built-in validators** — `"$actionType": "filter"` is only supported on deterministic rules. All built-in validators (`pii_detection`, `intellectual_property`, `prompt_injection`, `user_prompt_attacks`, `harmful_content`) support only `block`, `log`, and `escalate`.
- **Do not use odd numbers or floats for `harmfulContentEntityThresholds`** — only `0`, `2`, `4`, `6` are valid severity values. Values like `3` or `2.5` cause validation errors.

For canonical guardrail rules (discriminator omission, lowercase scopes, manual `guardrail.policies` edits), see [../../critical-rules.md](../../critical-rules.md).

## References

- [guardrails.md](guardrails.md) — capability overview, base schema, selector, actions, walkthrough
- [custom-rules.md](custom-rules.md) — custom deterministic rules variant
- [../../critical-rules.md](../../critical-rules.md) — canonical guardrail rules and anti-patterns
- [../../project-lifecycle.md](../../project-lifecycle.md) § `uip agent guardrails list` — CLI reference
