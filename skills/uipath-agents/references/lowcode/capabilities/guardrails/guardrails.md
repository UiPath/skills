# Guardrails Reference

## Overview

Guardrails are safeguards that inspect agent inputs and outputs for policy violations (PII, harmful content, prompt injection, intellectual property, custom rules). They are configured at the **agent.json root level** as a `guardrails` array.

Two types exist:
- **`custom`** — deterministic rules you define (word matching, number comparison, boolean checks, universal triggers)
- **`builtInValidator`** — UiPath Guardrails API validators (PII detection, harmful content, prompt injection, IP protection, user prompt attacks)

> **All guardrails are configured at the agent.json root `guardrails` array.** The `selector.scopes` and `selector.matchNames` fields on each guardrail determine which tools and scopes it applies to.

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

**Minimum required from user:** app name + recipient (email is the simplest form).

```json
"action": {
  "$actionType": "escalate",
  "app": {
    "id": "<Key from uip solution resource list --kind App>",
    "name": "<app Name>",
    "version": "0",
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
| `app.version` | string | Yes | Always `"0"` for solution-embedded apps |
| `app.folderId` | string | No | Omit — not used by validate |
| `app.folderName` | string | Yes | Literal Orchestrator folder — the `Folder` field from `uip solution resource list --kind App` (e.g., `"Shared"`, `"Shared/Approvals"`). `uip agent validate` translates it to `folderPath` in the App binding inside `bindings_v2.json`. |
| `app.appProcessKey` | string | No | Omit — only used in advanced scenarios |
| `recipient.type` | integer | Yes | Recipient kind — see shapes below: 1=UserId, 2=GroupId, 3=UserEmail, 4=AssetUserEmail, 5=GroupName, 6=AssetGroupName, 7=ArgumentEmail, 8=ArgumentGroupName |
| `recipient.*` | — | — | Remaining fields depend on `type` — see recipient shapes below |

**Recipient shapes (discriminated by `type`):**

**Types 1, 2, 3, 5 — StandardRecipient** (UserId, GroupId, UserEmail, GroupName)

```json
{ "type": 3, "value": "reviewer@example.com" }
{ "type": 1, "value": "<user-guid>", "displayName": "Jane Doe" }
{ "type": 5, "value": "ReviewersGroup" }
```

| Field | Required | Description |
|-------|----------|-------------|
| `value` | Yes | User GUID (type 1), group GUID (type 2), email address (type 3), group name string (type 5) |
| `displayName` | No | Recommended for type 1 (UserId); omit for types 2, 3, 5 |

**Types 4, 6 — AssetRecipient** (AssetUserEmail, AssetGroupName)

Resolves the email or group name from an Orchestrator asset at runtime — do NOT use `value`.

```json
{ "type": 4, "assetName": "ReviewerEmailAsset", "folderPath": "Shared" }
{ "type": 6, "assetName": "ReviewGroupAsset", "folderPath": "Shared/MyTeam" }
```

| Field | Required | Description |
|-------|----------|-------------|
| `assetName` | Yes | Name of the Orchestrator asset holding the email or group value |
| `folderPath` | Yes | Fully-qualified Orchestrator folder path where the asset lives |

**Types 7, 8 — ArgumentRecipient** (ArgumentEmail, ArgumentGroupName)

Resolves the email or group name from the agent's input arguments at runtime — do NOT use `value`.

```json
{ "type": 7, "argumentName": "user.email" }
{ "type": 8, "argumentName": "team.groupName" }
```

| Field | Required | Description |
|-------|----------|-------------|
| `argumentName` | Yes | Dot-path into the agent's input schema (e.g. `"user.email"`, `"reviewerEmail"`) |

Prefer `type: 3` (UserEmail) when adding manually — it requires no GUID or asset lookup. Studio Web uses `type: 1` (UserId) when a user is selected via the UI.

#### Adding an escalation guardrail — step-by-step

**Step 0 — Discover available validators (MANDATORY — do not skip even when validator type is already known):**

```bash
uip agent guardrails list --output json
```

Confirm the target validator is listed. Record the exact parameter `id` values and `$parameterType` tags from the output — these must match precisely in the guardrail JSON. Skipping this step leads to invalid parameter shapes.

**Step 1 — Discover the app** using `--kind App` from the solution root:

```bash
uip solution resource list --kind App --source remote --search "<app-name>" --output json
```

Filter results for `"Type": "Workflow Action"`. Use these three fields from the result:

| Resource list field | Maps to `app.*` field |
|---------------------|----------------------|
| `Key` | `app.id` |
| `Name` | `app.name` |
| `Folder` | `app.folderName` (literal, e.g., `"Shared"`) |

`app.version` is always `"0"` — that's a fixed value, not derived from the `resource list` row. `app.folderName` carries the literal `Folder` and `uip agent validate` translates it to `folderPath` in the App binding inside `bindings_v2.json`. Do not use `FolderKey` for any `app.*` field.

If multiple entries share the same name in different folders, ask the user which deployment to use.

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

**Step 2 — Validate the app's action schema**

A guardrail escalation app must expose a specific action schema contract. Validate **before** writing the guardrail JSON. If any check below fails, stop and report to the user: `<APP_NAME> does not have the required action schema configuration for tool guardrails.` (replace `<APP_NAME>` with the app's `Name` from Step 1).

**SECURITY:** Never read `~/.uipath/.auth` directly — keep the token inside the shell. Always use a `bash -c` wrapper that sources the auth file and makes the API call in a single shell invocation, so Claude only sees the API response.

2a. Look up `systemName` and `deployVersion` from the Apps API (use `Key` from Step 1 to filter client-side by `id`):

```bash
bash -c 'set -a; source ~/.uipath/.auth; set +a; curl -s \
  "${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/apps_/default/api/v1/default/action-apps?state=deployed&pageNumber=0&limit=100" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-Uipath-Tenantid: $UIPATH_TENANT_ID" \
  -H "Accept: application/json"'
```

From the entry whose `id` matches the `Key` from Step 1, extract `systemName` and `deployVersion`. If no entry matches → report error and stop.

2b. Fetch the action schema:

```bash
bash -c 'set -a; source ~/.uipath/.auth; set +a; curl -s \
  "${UIPATH_URL}/${UIPATH_ORGANIZATION_ID}/apps_/default/api/v1/default/action-schema?appSystemName=<SYSTEM_NAME>&version=<DEPLOY_VERSION>" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-Uipath-Tenantid: $UIPATH_TENANT_ID" \
  -H "Accept: application/json"'
```

If the response is empty, not valid JSON, or missing the `inputs`/`outputs`/`outcomes` arrays → report error and stop.

2c. Check required arguments by name. All three categories must pass — the app may have extra arguments beyond these, but must have at least:

| Category | Required Names |
|----------|---------------|
| `inputs` (8) | `GuardrailName`, `GuardrailDescription`, `TenantName`, `AgentTrace`, `Tool`, `ExecutionStage`, `ToolInputs`, `ToolOutputs` |
| `outputs` (3) | `ReviewedInputs`, `ReviewedOutputs`, `Reason` |
| `outcomes` (2) | `Approve`, `Reject` |

Validation is **name-only** — types, `required` flags, and `isList` are not checked. Verify every required name appears in the corresponding array's `name` fields. If any required name is missing → report error and stop.

**Step 3 — Construct and add the escalate action** in `agent.json`'s `guardrails` array:

```json
{
  "$actionType": "escalate",
  "app": {
    "id": "8137af9d-8dd3-4454-84d7-e0d93ce80c7e",
    "name": "Tool.Guardrail.Escalation.Action.App",
    "version": "0",
    "folderName": "Shared"
  },
  "recipient": { "type": 3, "value": "reviewer@example.com" }
}
```

`app.id`, `app.name`, and `app.folderName` come from Step 1 (`Key`, `Name`, `Folder` respectively). `app.version` is always `"0"` — fixed value for solution-embedded apps.

**Step 4 — Generate solution resource files**

Run these two commands from the solution root:

```bash
uip agent validate <AgentName> --output json
uip solution resource refresh --output json
```

- `validate` generates `bindings_v2.json` with a `resource: "app"` binding for the escalation app. The binding carries both `name` (from `app.name`) and `folderPath` (translated from `app.folderName`).
- `refresh` reads `bindings_v2.json`, fetches the app from the Resource Catalog Service using the joint `(name, folderPath)` key, and generates all 4 solution-level resource files (`app/workflow Action/`, `appVersion/`, `package/`, `process/webApp/`) plus the `debug_overwrites.json` entries for both the app and its code-behind process.

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
  "selector": { "scopes": ["Tool"], "matchNames": ["MyToolName"] },
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
| `"number"` | Scalar numbers (e.g., `threshold` for prompt injection) | number |

### Validators Quick Reference

| Validator | Scopes | Stages | Supported Actions |
|-----------|--------|--------|-------------------|
| `pii_detection` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `prompt_injection` | Llm | Pre only | Block, Log, Escalate |
| `harmful_content` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `intellectual_property` | Llm, Agent | Post only | Block, Log, Escalate |
| `user_prompt_attacks` | Llm | Pre only | Block, Log, Escalate |

Run `uip agent guardrails list --output json` to get the authoritative list. Only use validators where `Status` is `"Available"`. Use the output to populate `validatorType`, `selector.scopes`, and `validatorParameters` fields.
**How to map `uip agent guardrails list` output to guardrail JSON:**

| CLI field | Maps to |
|-----------|---------|
| `Status` | Gate check — only proceed if `"Available"` |
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

### Example 7: Custom Word Rule — Log on All Tool Fields

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
    "scopes": ["Tool"],
    "matchNames": ["MyToolName"]
  }
}
```

### Example 8: Escalate PII Violations to Action Center — Multiple Tool Targets

Escalates to an Action Center app when email or credit card PII is detected at the agent level. `app.id`, `app.name`, and `app.folderName` come from `uip solution resource list --kind App`.

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
      "version": "0",
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

`app.id`, `app.name`, and `app.folderName` are sourced from Step 1 (`resource list` → `Key`, `Name`, `Folder`). `app.version` is always `"0"`.

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

> Canonical guardrail anti-patterns — discriminator omission (`$actionType` / `$parameterType` / `$ruleType` / `$selectorType`), lowercase scope values, populating `guardrail.policies` on tool resources, and UUID reuse — live in [../../critical-rules.md](../../critical-rules.md) § What NOT to Do. The validator-specific anti-patterns below extend (do not repeat) that canonical list.

1. **Do not use snake_case for PII entity names** — use PascalCase: `"Email"` not `"email_address"`, `"PhoneNumber"` not `"phone_number"`, `"USSocialSecurityNumber"` not `"us_ssn"`.
2. **Do not add `prompt_injection` to Tool or Agent scope** — it only works with `"Llm"` scope, PreExecution stage.
3. **Do not add `user_prompt_attacks` to Tool or Agent scope** — Llm only, PreExecution only.
4. **Do not add `intellectual_property` to Tool scope** — only `"Llm"` and `"Agent"` scopes are supported.
5. **Do not add `intellectual_property` to PreExecution stage** — PostExecution only.
6. **Do not omit `matchNames` when `Tool` is in `scopes`** — always explicitly list the target tool names. See [matchNames — "All Tools" Behavior](#matchnames--all-tools-behavior).
7. **Do not use `filter` action on built-in validators** — `"$actionType": "filter"` is only supported on deterministic rules. All built-in validators (`pii_detection`, `intellectual_property`, `prompt_injection`, `user_prompt_attacks`, `harmful_content`) support only `block`, `log`, and `escalate`.
8. **Do not use odd numbers or floats for `harmfulContentEntityThresholds`** — only `0`, `2`, `4`, `6` are valid severity values. Values like `3` or `2.5` cause validation errors.
9. **Do not add a built-in validator without first running `uip agent guardrails list --output json`** — always fetch the list, verify the validator exists, and confirm `Status` is `"Available"`. Adding an `Unauthorised` or non-existent validator causes runtime failures.
10. **Do not use Action Center apps with `Type: "VB Action"` or `Type: "Coded"` as escalation targets** — only entries with `Type: "Workflow Action"` can back a guardrail escalation. Always filter `uip solution resource list --kind App` results by this type.
11. **Do not use `--kind Process` (Type: `"webApp"`) to find escalation apps** — those entries are code-behind processes, not app deployments. Their `Key` values are process release GUIDs, not app IDs. Always use `--kind App` with `Type: "Workflow Action"`.
12. **Do not put `"solution_folder"` into `app.folderName`** — set it to the literal `Folder` from `uip solution resource list --kind App` (e.g., `"Shared/Approvals"`). `uip agent validate` translates it to `folderPath` in the App binding inside `bindings_v2.json`. Omit `app.folderId`. `FolderKey` from `resource list` is NOT used in any `app.*` field — it IS correct in `debug_overwrites.json` entries, where it maps the solution-embedded resource to its real runtime location.
13. **Do not use `source <(grep = ~/.uipath/.auth)` for Apps API calls in guardrail setup** — it fails to export variables to the surrounding shell in some environments. Use `set -a; source ~/.uipath/.auth; set +a` instead.
14. **Do not add a Tool-scoped guardrail before the tool is added to the agent** — every name in `selector.matchNames` must match an existing tool resource under `<AGENT_NAME>/resources/<ToolName>/resource.json`. A guardrail referencing a non-existent tool will be caught by `uip agent validate` and fail with an error. Always run `uip agent tool list` first (Step 2) and confirm target tools are present.
15. **Do not skip action schema validation for escalation apps** — before writing a guardrail with `"$actionType": "escalate"`, fetch the app's action schema and verify all required inputs (8), outputs (3), and outcomes (2) are present by name. If any are missing, report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` and do not proceed. See [§ Adding an escalation guardrail — Step 2](#adding-an-escalation-guardrail--step-by-step).
16. **Do not use `Agent` or `Llm` scopes on custom guardrails** — custom guardrails (`$guardrailType: "custom"`) only support `"Tool"` scope with exactly one tool in `matchNames`. Custom rules depend on the tool's input/output schema, so they cannot target multiple tools. Create a separate custom guardrail per tool.
17. **Do not auto-generate a custom guardrail as fallback** — when a built-in validator is unavailable, unsupported for the requested scope, or unauthorized, inform the user and stop. Do not silently generate a custom guardrail as a workaround. You may suggest a custom guardrail alternative (for `Tool` scope only), but only generate it after explicit user confirmation.
18. **Do not create separate guardrails per scope** — when a guardrail applies to multiple scopes (e.g., `Agent` and `Tool`), combine them into a single guardrail with `"scopes": ["Agent", "Tool"]`. Do not create two separate guardrail objects with identical configuration differing only in scope.
19. **Do not generate guardrails targeting unsupported tool types** — `matchNames` can only reference tools of supported types: agent, process, activity, builtInTool, ixpTool, or Integration Service connector. Do not generate guardrails with `matchNames` targeting other tool types.
20. **Do not omit `matchNames` to target "all tools"** — always explicitly list every tool resource name in `matchNames`. Read the agent's `resources/` directory first. If the agent has no tool resources, do not add the guardrail.

## Walkthrough

Use when adding input/output safeguards (PII detection, harmful content blocking, custom word rules) to a low-code agent. Guardrails are configured at the agent.json root `guardrails` array.

> **MANDATORY: Read this file BEFORE writing any guardrail JSON.** The guardrail schema uses discriminator fields (`$actionType`, `$parameterType`, `$ruleType`, `$selectorType`) that cannot be guessed. PII detection uses `$guardrailType: "builtInValidator"` with `validatorType: "pii_detection"` — NOT `$guardrailType: "pii"`. Parameters use `id` (not `name`) and require `$parameterType`. Actions use `$actionType` (not `type`). PII entities are PascalCase (`"Email"`, not `"email_address"`). There is no `pattern`, `target`, or `message` field.
>
> **MANDATORY: Run `uip agent guardrails list --output json` before writing any `builtInValidator` guardrail**, even when you already know the `validatorType`. The command gives you the exact `$parameterType` values, parameter `id` names, and allowed scopes for that validator — values you cannot safely derive from the type name alone. Skipping it leads to invalid parameter shapes that fail schema validation.

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
  - External Orchestrator process (RPA / agent / API / agentic): [../process/external.md](../process/external.md)
  - Solution-internal agent: [../process/solution-agent.md](../process/solution-agent.md)
  - Integration Service tool: [../integration-service/integration-service.md](../integration-service/integration-service.md)

> `uip agent validate` enforces this: it fails with an error if a Tool-scoped guardrail references a tool that has not been added to the agent.

### Step 3 — Fetch and verify available validators (mandatory)

```bash
uip agent guardrails list --output json
```

Before adding any built-in validator, check the `Data` array for the requested validator:

1. **Not found in list** — validator does not exist on this tenant. Inform user and stop. Do NOT generate a custom guardrail as a fallback.
2. **`Status: "Available"`** — proceed with configuration.
3. **`Status: "Unauthorised"`** — user is not entitled to use guardrails. Inform user they can view the configuration but cannot apply it to agents. Stop.
4. **Scope not supported** — if the requested scope is not in `AllowedScopes`, inform the user which scopes are valid. Do NOT auto-generate a custom guardrail as a workaround (custom guardrails only support `Tool` scope). You may suggest a custom guardrail alternative, but only generate it after explicit user confirmation.

Only add guardrails for validators with `Status: "Available"`. Use the output to determine `validatorType` values, allowed scopes, stages, and required parameters. Do not hardcode assumptions.

### Step 4 — Add a guardrail to agent.json

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

### Step 5 — Validate

```bash
uip agent validate "<AGENT_NAME>" --output json
```

Confirm the guardrails appear in the validated output without errors.

## References

- [../../critical-rules.md](../../critical-rules.md) — canonical low-code rules and guardrail anti-patterns (discriminators, scope casing, populating `guardrail.policies` on tool resources, UUID reuse)
- [../../project-lifecycle.md](../../project-lifecycle.md) § `uip agent guardrails list` — CLI reference for validator discovery
- [../../agent-definition.md](../../agent-definition.md) § Guardrails — root-level placement in `agent.json`

