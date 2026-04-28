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
| `matchNames` | string[] | No | Target specific tools by name. Omit to apply to all tools in the selected scopes |

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

Removes or masks specific fields from the input/output.

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

**Minimum required from user:** app name + recipient (email is the simplest form).

```json
"action": {
  "$actionType": "escalate",
  "app": {
    "id": "<Key from uip solution resource list --kind App>",
    "name": "<app Name>",
    "version": "<deployVersion as string from Apps API>",
    "folderId": "<FolderKey from uip solution resource list --kind App>",
    "folderName": "<Folder from uip solution resource list --kind App>"
  },
  "recipient": {
    "type": 3,
    "value": "reviewer@example.com"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$actionType` | `"escalate"` | Yes | Action discriminator |
| `app.id` | string | Yes | App deployment ID — the `Key` field from `uip solution resource list --kind App` |
| `app.name` | string | Yes | Action Center app name — the `Name` field from `uip solution resource list --kind App` |
| `app.version` | string | Yes | `deployVersion` from the Apps API as a string (e.g., `"1"`) — **never use `"0"`** |
| `app.folderId` | string | No | Deployment folder GUID — the `FolderKey` field from `uip solution resource list --kind App` |
| `app.folderName` | string | No | Deployment folder path — the `Folder` field from `uip solution resource list --kind App` (e.g., `"Shared"`) |
| `app.appProcessKey` | string | No | Omit — only used in advanced scenarios |
| `recipient.type` | integer | Yes | 1=UserId (GUID), 2=GroupId (GUID), 3=UserEmail, 4=AssetUserEmail, 5=StaticGroupName, 6=AssetGroupName |
| `recipient.value` | string | Yes | Depends on `type` — see recipient types table below |
| `recipient.displayName` | string | No | Omit for `type: 3` (email); include for `type: 1` (user GUID) |

**Recipient types:**

| `type` | `value` format | `displayName` | Example |
|--------|---------------|---------------|---------|
| 1 (UserId) | UiPath user GUID | Recommended | `{ "type": 1, "value": "5ed432f8-76d3-4ed3-80f1-6ce371501574", "displayName": "Jane Doe" }` |
| 2 (GroupId) | UiPath group GUID | Optional | `{ "type": 2, "value": "<group-uuid>" }` |
| 3 (UserEmail) | Email address | Omit | `{ "type": 3, "value": "reviewer@example.com" }` |
| 4 (AssetUserEmail) | UiPath asset name | Optional | `{ "type": 4, "value": "ReviewerEmailAsset" }` |
| 5 (StaticGroupName) | Group name string | Optional | `{ "type": 5, "value": "Reviewers" }` |
| 6 (AssetGroupName) | UiPath asset name | Optional | `{ "type": 6, "value": "ReviewGroupAsset" }` |

Prefer `type: 3` (email) when adding manually — it requires no GUID lookup. Studio Web uses `type: 1` (UserId) when the user is selected via the UI.

#### Adding an escalation guardrail — step-by-step

**Step 1 — Discover the app** using `--kind App` from the solution root:

```bash
uip solution resource list --kind App --source remote --search "<app-name>" --output json
```

Filter results for `"Type": "Workflow Action"` (skip `"VB Action"` and `"Coded"` entries — they cannot back a guardrail escalation). Each matching entry directly provides all fields you need:

| Resource list field | Maps to `app.*` field |
|---------------------|----------------------|
| `Key` | `app.id` |
| `Name` | `app.name` |
| `FolderKey` | `app.folderId` |
| `Folder` | `app.folderName` |

If multiple entries share the same name in different folders, ask the user which deployment to target. Prefer the entry in `"Shared"` when no preference is stated.

Example entry:
```json
{
  "Source": "Remote",
  "Key": "8137af9d-8dd3-4454-84d7-e0d93ce80c7e",
  "Name": "Tool.Guardrail.Escalation.Action.App",
  "Kind": "app",
  "Type": "Workflow Action",
  "Folder": "Shared",
  "FolderKey": "627fe423-5c73-464a-abff-41fdaad6ac19"
}
```

> **Important:** Do NOT use `--kind Process` with `Type: "webApp"` to find Action Center apps. Those entries are the code-behind processes — their `Key` values are process release GUIDs, not app deployment IDs. Using them as `app.id` will cause runtime resolution failures.

**Step 2 — Get `deployVersion`** from the Apps API (the only field `resource list` does not return):

```bash
bash -c 'set -a; source ~/.uipath/.auth; set +a && curl -s \
  "${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/apps_/default/api/v1/default/action-apps?state=deployed&pageNumber=0&limit=100" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-Uipath-Tenantid: $UIPATH_TENANT_ID" \
  -H "Accept: application/json"' | python3 -c "
import sys, json
for a in json.load(sys.stdin).get('deployed', []):
    if a.get('id') == '<KEY_FROM_STEP_1>':
        print('version:', str(a['deployVersion']))
"
```

Use `str(deployVersion)` as the `app.version` string (e.g., `1` → `"1"`).

> **Auth note:** Use `set -a; source ~/.uipath/.auth; set +a` — the `source <(grep = ~/.uipath/.auth)` pattern used in other docs fails here because process substitution does not export variables to the surrounding shell in all environments.

**Step 3 — Construct and add the escalate action** in `agent.json`'s `guardrails` array:

```json
{
  "$actionType": "escalate",
  "app": {
    "id": "8137af9d-8dd3-4454-84d7-e0d93ce80c7e",
    "name": "Tool.Guardrail.Escalation.Action.App",
    "version": "1",
    "folderId": "627fe423-5c73-464a-abff-41fdaad6ac19",
    "folderName": "Shared"
  },
  "recipient": { "type": 3, "value": "reviewer@example.com" }
}
```

**Step 4 — Validate and refresh:**

```bash
uip agent validate <AgentName> --output json
uip solution resource refresh --output json
```

`resource refresh` uses the escalation resource file (if present) to auto-generate the four solution-level app files under `resources/solution_folder/`:
`app/workflow Action/<AppName>.json`, `appVersion/<AppName>.json`, `package/<AppName>.json`, `process/webApp/<AppName>.json`.

**Step 5 — Upload:**

```bash
uip solution upload . --output json
```

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
| `notContains` | Field value does not contain the string |
| `notEquals` | Field value does not equal the string |

#### Number Rules (`$ruleType: "number"`)

Numeric comparison against field values.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"number"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector |
| `operator` | string | Yes | Comparison operator |
| `value` | number | Yes | Value to compare against |

**Operators:** `equals`, `notEquals`, `greaterThan`, `greaterThanOrEqual`, `lessThan`, `lessThanOrEqual`

#### Boolean Rules (`$ruleType: "boolean"`)

Boolean equality check.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"boolean"` | Yes | Rule type discriminator |
| `fieldSelector` | object | Yes | Field selector |
| `operator` | `"equals"` | Yes | Only `equals` is supported |
| `value` | boolean | Yes | `true` or `false` |

#### Always / Universal Rules (`$ruleType: "always"`)

Fires on every input/output — no condition check. Use `applyTo` to control whether it runs on input, output, or both.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$ruleType` | `"always"` | Yes | Rule type discriminator |
| `applyTo` | `"input"` \| `"output"` \| `"both"` | Yes | When the rule fires |

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

### Validators Reference

Run `uip agent guardrails list --output json` to get the full list of available validators with their allowed scopes, stages, and parameters. Use the output to populate `validatorType`, `selector.scopes`, and `validatorParameters` fields.

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
        "Hate": 3,
        "SelfHarm": 2,
        "Sexual": 4,
        "Violence": 3
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

### Example 4: Custom Word Rule — Block Forbidden Terms in Specific Tool Output

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

### Example 5: Custom Word Rule — Log on All Fields

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

### Example 6: Escalate PII Violations to Action Center — Agent Level

Escalates to an Action Center app when email or credit card PII is detected at the agent level. All `app.*` fields are populated from `uip solution resource list --kind App` (Step 1) and the Apps API `deployVersion` (Step 2) — no guessing required.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "10d5f10f-da4e-4bf1-ace9-dd880e33d9be",
  "name": "PII Email and Credit Card escalation guardrail",
  "description": "Detects email addresses and credit card numbers, escalates to human review",
  "validatorType": "pii_detection",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "entities",
      "value": ["Email", "CreditCardNumber"]
    },
    {
      "$parameterType": "map-enum",
      "id": "entityThresholds",
      "value": {
        "Email": 0.5,
        "CreditCardNumber": 0.5
      }
    }
  ],
  "action": {
    "$actionType": "escalate",
    "app": {
      "id": "8137af9d-8dd3-4454-84d7-e0d93ce80c7e",
      "name": "Tool.Guardrail.Escalation.Action.App",
      "version": "1",
      "folderId": "627fe423-5c73-464a-abff-41fdaad6ac19",
      "folderName": "Shared"
    },
    "recipient": {
      "type": 3,
      "value": "reviewer@example.com"
    }
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Agent"]
  }
}
```

Where the `app` field values come from:

| `app.*` field | Source | Value in example |
|---|---|---|
| `id` | `resource list --kind App` → `Key` | `8137af9d-...` |
| `name` | `resource list --kind App` → `Name` | `Tool.Guardrail.Escalation.Action.App` |
| `version` | Apps API `deployVersion` as string | `"1"` |
| `folderId` | `resource list --kind App` → `FolderKey` | `627fe423-...` |
| `folderName` | `resource list --kind App` → `Folder` | `"Shared"` |

### Example 7: Custom Word Rule — Specific Fields with Titles on a Named Tool

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

### Example 8: Filter — Redact Fields from Tool Output

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

1. **Do not omit `$actionType` from action objects** — every action requires `$actionType` as the discriminator (`"block"`, `"log"`, `"filter"`, `"escalate"`). Using `"type"` instead of `"$actionType"` causes validation failure.
2. **Do not omit `$parameterType` from validator parameters** — every entry in `validatorParameters` requires `$parameterType` (`"enum-list"`, `"map-enum"`, or `"number"`). Using `"name"` instead of `"id"` causes validation failure.
3. **Do not omit `$ruleType` from custom rules** — every rule requires `$ruleType` (`"word"`, `"number"`, `"boolean"`, `"always"`).
4. **Do not omit `$selectorType` from field selectors** — use `fieldSelector` with `$selectorType` (`"all"` or `"specific"`), not `field` with `type`.
5. **Do not use snake_case for PII entity names** — use PascalCase: `"Email"` not `"email_address"`, `"PhoneNumber"` not `"phone_number"`, `"USSocialSecurityNumber"` not `"us_ssn"`.
6. **Do not use lowercase for scope values** — use `"Agent"`, `"Llm"`, `"Tool"` (PascalCase). `"agent"`, `"llm"`, `"tool"` are invalid.
7. **Do not add `prompt_injection` to Tool or Agent scope** — it only works with `"Llm"` scope, PreExecution stage.
8. **Do not add `user_prompt_attacks` to Tool or Agent scope** — Llm only, PreExecution only.
9. **Do not add `intellectual_property` to Tool scope** — only `"Llm"` and `"Agent"` scopes are supported.
10. **Do not add `intellectual_property` to PreExecution stage** — PostExecution only.
11. **Do not forget `matchNames` when targeting a specific tool** — without it, the guardrail applies to all tools in the scope.
12. **Do not manually edit `guardrail.policies` on tool resources** — it is auto-populated by `uip agent validate` from root-level guardrails. Always configure guardrails at the agent.json root `guardrails` array.
13. **Do not reuse UUIDs across guardrails** — each guardrail needs a unique `id`.
14. **Do not use `--kind Process` (Type: `"webApp"`) to find escalation apps** — those entries are code-behind processes, not app deployments. Their `Key` values are process release GUIDs, not app IDs. Always use `--kind App` with `Type: "Workflow Action"`.
15. **Do not use `"version": "0"` or `"folderName": "solution_folder"` in a guardrail escalate action** — `version` must be the `deployVersion` string from the Apps API (e.g., `"1"`), and `folderName` must be the actual deployment folder (e.g., `"Shared"`), not the placeholder `"solution_folder"`.
16. **Do not use `source <(grep = ~/.uipath/.auth)` for Apps API calls in guardrail setup** — it fails to export variables to the surrounding shell in some environments. Use `set -a; source ~/.uipath/.auth; set +a` instead.
