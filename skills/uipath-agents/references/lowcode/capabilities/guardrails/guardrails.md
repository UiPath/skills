# Guardrails

Guardrails are safeguards that inspect agent inputs and outputs for policy violations (PII, harmful content, prompt injection, intellectual property, custom rules). They are configured at the **agent.json root level** as a `guardrails` array.

Two variants exist:
- **`custom`** — deterministic rules you define (word matching, number comparison, boolean checks, universal triggers). See [custom-rules.md](custom-rules.md).
- **`builtInValidator`** — UiPath Guardrails API validators (PII detection, harmful content, prompt injection, IP protection, user prompt attacks). See [builtin-validators.md](builtin-validators.md).

> **Tool-level `guardrail.policies`** is auto-populated by `uip agent validate` — it copies the root-level guardrails that target each tool (via `matchNames`) into the tool's `guardrail.policies` array. Do not manually edit `guardrail.policies` on tool resources. Always configure guardrails at the agent.json root `guardrails` array.

## When to Use

- Detect PII (email, phone, SSN, credit card) in agent or tool outputs
- Block harmful content (hate, violence, self-harm, sexual)
- Detect prompt injection or user prompt attacks before the LLM processes input
- Detect copyrighted text or licensed code in LLM output
- Apply custom word, number, or boolean rules to inputs/outputs
- Filter (redact) sensitive fields from tool output without blocking

## Variants

| `$guardrailType` | Use when | Walkthrough |
|---|---|---|
| `"builtInValidator"` | Need a UiPath Guardrails API validator (PII, harmful content, prompt injection, IP, user prompt attacks) | [builtin-validators.md](builtin-validators.md) |
| `"custom"` | Need a deterministic rule (word/number/boolean match, universal trigger) | [custom-rules.md](custom-rules.md) |

## Base Schema (shared by both variants)

Every guardrail object in the `guardrails` array shares these base fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$guardrailType` | string | Yes | Discriminator: `"custom"` or `"builtInValidator"` |
| `id` | string (UUID) | Yes | Unique identifier — generate a fresh UUID for each guardrail |
| `name` | string | Yes | Human-readable name |
| `description` | string | Yes | What this guardrail checks (can be empty `""`) |
| `action` | object | Yes | What happens on violation — see § Actions |
| `enabledForEvals` | boolean | Yes | Whether this guardrail runs during evaluations |
| `selector` | object | Yes | Which scopes and tools this guardrail targets — see § Selector |

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

## Discovery

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

> **`filter` is custom-only.** Built-in validators (`pii_detection`, `intellectual_property`, `prompt_injection`, `user_prompt_attacks`, `harmful_content`) support only `block`, `log`, and `escalate` — never `filter`. See [builtin-validators.md](builtin-validators.md) § Gotchas.

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

## Agent-Level Schema

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

## Solution-Level Files

None. Guardrails do not emit `bindings_v2.json` entries, do not create `resources/solution_folder/` files, and `uip solution resource refresh` is not involved. They are pure `agent.json` schema.

## Walkthrough

Use when adding input/output safeguards (PII detection, harmful content blocking, custom word rules) to a low-code agent. Guardrails are configured at the agent.json root `guardrails` array.

> **MANDATORY: Read this file (and the variant sibling, [builtin-validators.md](builtin-validators.md) or [custom-rules.md](custom-rules.md)) BEFORE writing any guardrail JSON.** The guardrail schema uses discriminator fields (`$actionType`, `$parameterType`, `$ruleType`, `$selectorType`) that cannot be guessed. PII detection uses `$guardrailType: "builtInValidator"` with `validatorType: "pii_detection"` — NOT `$guardrailType: "pii"`. Parameters use `id` (not `name`) and require `$parameterType`. Actions use `$actionType` (not `type`). PII entities are PascalCase (`"Email"`, not `"email_address"`). There is no `pattern`, `target`, or `message` field.

### Step 1 — Verify existing agent

Ensure the agent project exists and has a valid `agent.json`. If starting fresh, follow [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent) first.

### Step 2 — Discover available validators

```bash
uip agent guardrails list --output json
```

Use the output to determine which `validatorType` values exist, their allowed scopes, stages, and required parameters. Do not hardcode assumptions — always check the CLI output for the authoritative list.

### Step 3 — Add a guardrail to agent.json

For built-in validators, see [builtin-validators.md](builtin-validators.md) for the full schema and 6 worked examples.

For custom rules (word/number/boolean/always), see [custom-rules.md](custom-rules.md) for the full schema and 4 worked examples.

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

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) for the canonical guardrail anti-patterns (discriminator omission, lowercase scopes, manual `guardrail.policies` edits). Capability-spanning gotcha:

- **Forget `matchNames` when targeting a specific tool** — without it, the guardrail applies to all tools in the scope.

For variant-specific gotchas (validator scopes, parameter types, PII entity casing) see [builtin-validators.md](builtin-validators.md) § Gotchas.

## References

- [builtin-validators.md](builtin-validators.md) — `$guardrailType: "builtInValidator"` walkthrough
- [custom-rules.md](custom-rules.md) — `$guardrailType: "custom"` walkthrough
- [../../critical-rules.md](../../critical-rules.md) — canonical guardrail rules and anti-patterns
- [../../project-lifecycle.md](../../project-lifecycle.md) § `uip agent guardrails list` — CLI reference
- [../../agent-definition.md](../../agent-definition.md) § Guardrails — root-level placement in `agent.json`
