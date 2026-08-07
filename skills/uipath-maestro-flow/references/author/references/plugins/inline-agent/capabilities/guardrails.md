# Guardrails Reference

## Overview

Guardrails are safeguards that inspect agent inputs and outputs for policy violations (PII, harmful content, prompt injection, intellectual property, custom rules). They are configured on the **agent node's `inputs.guardrails` array** in the `.flow` file — not on resource nodes, and never in any sidecar file.

Two types exist:
- **`custom`** — deterministic rules you define (word matching, number comparison, boolean checks, universal triggers)
- **`builtInValidator`** — UiPath Guardrails API validators (PII detection, harmful content, prompt injection, IP protection, user prompt attacks)

This plugin covers autonomous inline agents only; the guardrail array shape below is the autonomous contract. For standalone agent projects (including conversational agents and their guardrail restrictions), the `uipath-agents` skill is authoritative.

## Where Guardrails Live in the Flow

All guardrails — including Tool-scoped ones — are authored in ONE place: the `uipath.agent.autonomous` node's `inputs.guardrails[]`. The canvas exposes a guardrails editor on tool nodes too, but even that editor writes into the **agent node's** array.

```json
{
  "id": "disputeAnalyst",
  "type": "uipath.agent.autonomous",
  "typeVersion": "1.3",
  "inputs": {
    "source": "<UUID>",
    "systemPrompt": "…",
    "userPrompt": "…",
    "model": "<MODEL_ID>",
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
    "agentInputVariables": [],
    "agentOutputVariables": [ { "id": "answer", "type": "string" } ]
  }
}
```

### Derived artifacts — never author

At sidecar derivation ([impl.md § Derived Sidecar](../impl.md#10-derived-sidecar--reference)) the array projects **verbatim** into the derived `agent.json` `guardrails[]`. Additionally, each Tool-scoped guardrail is filtered per tool into the derived tool resource's `guardrail.policies[]` (matched by tool name). Both are derived — never write `guardrail.policies` anywhere, never create sidecar files.

### `flow validate` does NOT check guardrails

> **`uip maestro flow validate` is silent on `inputs.guardrails` — malformed guardrails pass validation.** Missing discriminators, lowercase scopes, unknown validator types, wrong parameter shapes, `matchNames` naming a non-existent tool — even a non-array `guardrails` value — all validate as `Valid`. Correctness comes ONLY from following this reference plus `uip agent guardrails list` output. A guardrail that is wrong in the `.flow` fails at runtime, not at validate.

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
| `scopes` | string[] | Yes | Array of `"Agent"`, `"Llm"`, `"Tool"` — at least one required. |
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

### matchNames — the Tool Node's `inputs.name`

`matchNames` entries must equal the target tool node's **`inputs.name`** — the name authority. For **tool** nodes specifically, the projection falls back to the node label / `display.label` when `inputs.name` is absent — keep them aligned (other resource kinds resolve by `inputs.name` only, but they are not guardrail targets). This is the same name the derived-sidecar filter matches when populating the tool's `guardrail.policies`.

Only the following tool kinds support guardrails:

| Tool kind | Capability doc |
|-----------|----------------|
| Process-family tool (RPA / agent / API / process orchestration) | [process.md](process.md) |
| Built-in tool | [built-in-tools.md](built-in-tools.md) |
| IS connector tool | [integration-service.md](integration-service.md) |
| IXP tool | (node type `…tool.ixp.*`) |

Do not generate guardrails targeting anything else (context, escalation, or MCP nodes are not guardrail targets).

**Canvas cross-writes — keep `matchNames` in sync yourself when editing by hand:**

- Renaming a tool (its `inputs.name`) in the canvas rewrites every guardrail's `matchNames` entry. When YOU rename a tool node, apply the same rewrite.
- Deleting a tool removes its name from each `matchNames`; a guardrail whose `matchNames` becomes empty loses its `Tool` scope, and is deleted entirely when no scopes remain. Mirror this cleanup when you remove a tool node.

### matchNames — "All Tools" Behavior

When targeting all tools, `matchNames` must **explicitly list every tool node's `inputs.name`**.

1. Enumerate the resource nodes wired to the agent's `tool` handle (artifact edges `sourcePort: "tool"`).
2. If the agent has **no wired tool nodes**, do not add the guardrail — inform the user: *"No tools are wired to this agent. Cannot add a tool-scoped guardrail."*
3. Populate `matchNames` with every wired tool's `inputs.name`.

Canvas-authored flows may carry a Tool-scoped guardrail with empty/absent `matchNames` — the projection treats that as a wildcard (applies to ALL tools). Recognize it when editing; do not author it (an explicit list keeps intent visible and survives tool additions predictably).

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
    "id": "<Key from uip solution resources list --kind App>",
    "name": "<APP_NAME>",
    "version": "0",
    "folderName": "<Folder from uip solution resources list --kind App>"
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
| `app.id` | string | Yes | App deployment ID — the `Key` field from `uip solution resources list --kind App` |
| `app.name` | string | Yes | Action Center app name — the `Name` field from `uip solution resources list --kind App` |
| `app.version` | string | Yes | Always `"0"` for solution-embedded apps |
| `app.folderId` | string | No | Omit |
| `app.folderName` | string | Yes | Literal Orchestrator folder — the `Folder` field from `uip solution resources list --kind App` (e.g., `"Shared"`, `"Shared/Approvals"`) |
| `app.appProcessKey` | string | No | Omit — only used in advanced scenarios |
| `recipient.type` | integer | Yes | Recipient kind — see shapes below: 1=UserId, 2=GroupId, 3=UserEmail, 4=AssetUserEmail, 5=GroupName, 6=AssetGroupName, 7=ArgumentEmail, 8=ArgumentGroupName |
| `recipient.*` | — | — | Remaining fields depend on `type` — see recipient shapes below |

> The guardrail escalate `app` object is NOT the escalation node's `app` object — different field names (`id`/`name`/`version` here vs `resourceKey`/`appName`/`appVersion` on the [escalation node](escalation.md)). Do not mix the shapes.

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

**Scaffolding gate (MANDATORY):** when the request includes creating a solution
or flow, run `uip solution init` and `uip maestro flow init` before app discovery.
An incompatible or missing escalation app rejects only the guardrail; it does
not cancel the requested local scaffolding.

**Step 0 — Discover available validators** (MANDATORY for `builtInValidator` guardrails; skip for purely custom ones): run the [Step 0 validator fetch](#step-0--fetch-available-validators-mandatory-first-step) and record the exact parameter `id` values and `$parameterType` tags — these must match precisely in the guardrail JSON.

**Step 1 — Discover the app** using `--kind App` from the solution root:

```bash
uip solution resources list --kind App --source remote --search "<APP_NAME>" --output json
```

Keep only Action app entries — `Type` `"Workflow Action"` or `"JS Action"` (VB Action / Coded app types cannot back a guardrail escalation). Use these three fields from the result:

| Resource list field | Maps to `app.*` field |
|---------------------|----------------------|
| `Key` | `app.id` |
| `Name` | `app.name` |
| `Folder` | `app.folderName` (literal, e.g., `"Shared"`) |

`app.version` is always `"0"` — that's a fixed value, not derived from the `resource list` row. Do not use `FolderKey` for any `app.*` field.

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

**Step 1 completion gate — both branches MUST run `resources get`:**

- Exact app row found: immediately run
  `uip solution resources get "<Key from the row>" --output json`.
- No exact app row/key found: immediately run
  `uip solution resources get "<requested app name>" --output json` once and
  treat its failure as `GET_ERROR`.

Do not edit files, validate, or respond to the user between `resources list`
and this required `resources get` attempt. A missing catalog row is not a
completed schema check and is never permission to skip the command.

**Step 2 — Verify the app exposes the guardrail action-schema contract** (do this **before** writing the guardrail JSON — an incompatible app must be rejected, not authored).

**Required command gate:** execute
`uip solution resources get "<Key from Step 1>" --output json` for the selected
app before deciding whether it is compatible. The `resources list` row is not
an action schema and cannot replace this command. Do not write or reject the
guardrail until the returned action schema has been checked.

A guardrail escalation app must expose a specific action-schema contract. If verification fails, stop and report to the user: `<APP_NAME> does not have the required action schema configuration for tool guardrails.` (replace `<APP_NAME>` with the app's `Name` from Step 1). Do NOT write the guardrail.

`uip solution resources get` returns the app's action schema in one CLI-native call — no auth handling, no Apps API endpoints. Pipe its output into a verifier that confirms every required argument name. The CLI handles authentication, so Claude never touches the auth file or the token.

```bash
cat > /tmp/verify_escalation_app.py <<'PY'
import sys, json
data = json.load(sys.stdin)
if data.get("Result") != "Success":
    sys.exit("GET_ERROR: uip solution resources get failed: " + str(data.get("Message", "unknown error")))
raw = data.get("Data", {}).get("Spec", {}).get("ActionSchema")
if not raw:
    sys.exit("NO_SCHEMA: app spec has no ActionSchema — not a deployed Action app")
sch = json.loads(raw)
need = {"inputs": {"GuardrailName", "GuardrailDescription", "TenantName", "AgentTrace", "Tool", "ExecutionStage", "ToolInputs", "ToolOutputs"},
        "outputs": {"ReviewedInputs", "ReviewedOutputs", "Reason"},
        "outcomes": {"Approve", "Reject"}}
miss = {k: sorted(v - {x["name"] for x in sch.get(k, [])}) for k, v in need.items() if v - {x["name"] for x in sch.get(k, [])}}
print("OK" if not miss else "MISSING: " + json.dumps(miss))
sys.exit(0 if not miss else 1)
PY
uip solution resources get "<Key from Step 1>" --output json | python3 /tmp/verify_escalation_app.py
```

Decision rule — the verifier exits 0 (`OK`) or 1 (with a tagged reason). All exit-1 cases mean **do NOT write the guardrail**:

| Verifier output | Meaning | Action |
|-----------------|---------|--------|
| exit 0, `OK` | Contract satisfied | Proceed to Step 3 |
| exit 1, `MISSING: {...}` | App exists but its action schema is missing required argument names | Stop. Report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` |
| exit 1, `NO_SCHEMA: ...` | The resource has no action schema — not a deployed Action app | Stop. Report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` |
| exit 1, `GET_ERROR: ...` | `uip solution resources get` failed (app not found, no access, or CLI error) | Stop. Report `<APP_NAME> could not be verified for the required action schema configuration.` **Do NOT re-authenticate or try alternate endpoints** — a single failed verifier call is terminal for this run |

The check is **name-only** (types, `required` flags, `isList` are not checked); the app may carry extra arguments beyond these:

| Category | Required names |
|----------|---------------|
| `inputs` (8) | `GuardrailName`, `GuardrailDescription`, `TenantName`, `AgentTrace`, `Tool`, `ExecutionStage`, `ToolInputs`, `ToolOutputs` |
| `outputs` (3) | `ReviewedInputs`, `ReviewedOutputs`, `Reason` |
| `outcomes` (2) | `Approve`, `Reject` |

**Step 3 — Construct and add the escalate action** in the agent node's `inputs.guardrails` array (only after Step 2 passed):

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

**Step 4 — Format and validate:**

```bash
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

No refresh step and no `bindings[]` rows exist for guardrail escalation apps — the app reference lives entirely in the embedded `action.app` object. Remember validate is silent on guardrails (§ above): a passing validate confirms the flow, not the guardrail — re-read the written object against this reference before reporting done.

## Custom Guardrails (`$guardrailType: "custom"`)

Custom guardrails use deterministic rules you define. They have a `rules` array containing one or more rule objects.

> **Rule combination logic is AND.** Multiple rules in a single guardrail are evaluated with AND — all rules must match for the guardrail to trigger. Multiple fields selected within a single rule (via `$selectorType: "specific"` with multiple `fields` entries) are also AND — every listed field must satisfy the operator.
>
> Example with two rules and a multi-field selector (note the array-wildcard `[*]` paths):
> ```json
> "rules": [
>   {
>     "$ruleType": "word",
>     "fieldSelector": {
>       "$selectorType": "specific",
>       "fields": [
>         { "path": "editPermissions[*].project.archivedBy.applicationRoles.items[*].groups[*]", "source": "output", "title": "Edit permissions project archived by application roles items groups" },
>         { "path": "editPermissions[*].project.archivedBy.applicationRoles.items[*].key", "source": "output", "title": "Edit permissions project archived by application roles items key" }
>       ]
>     },
>     "operator": "doesNotStartWith",
>     "value": "AL"
>   },
>   {
>     "$ruleType": "word",
>     "fieldSelector": {
>       "$selectorType": "specific",
>       "fields": [
>         { "path": "description", "source": "output", "title": "Description" }
>       ]
>     },
>     "operator": "isNotEmpty",
>     "value": ""
>   }
> ]
> ```
> Evaluation: `(groups doesNotStartWith "AL" AND key doesNotStartWith "AL") AND (description isNotEmpty)` — all three conditions must be true for the guardrail to trigger.
>
> **OR logic is not supported.** To achieve OR behavior, create separate guardrails — one per condition branch. Each guardrail triggers independently.

> **Critical discriminator fields:** Every rule needs `$ruleType`. Every field selector needs `$selectorType`. Every action needs `$actionType`. Missing any of these causes runtime failure — and `flow validate` will NOT catch it.

```json
{
  "$guardrailType": "custom",
  "id": "<UUID>",
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
| `fields[].path` | string | Yes | Field path from the tool's input/output schema |
| `fields[].source` | `"input"` \| `"output"` | Yes | Which side to inspect |
| `fields[].title` | string | No | Human-readable label |

## Step 0 — Fetch Available Validators (Mandatory First Step)

Before adding any built-in validator guardrail, run:

```bash
uip agent guardrails list --output json
```

Tenant-level command — works from the flow project directory (no agent project needed; this and its `catalog` / `llm-as-judge-models` siblings join `uip agent model list` as the only sanctioned `uip agent` verbs for inline work).

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
  "id": "<UUID>",
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

| Validator | Scopes | Stages | Supported Actions |
|-----------|--------|--------|-------------------|
| `pii_detection` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `prompt_injection` | Llm | Pre only | Block, Log, Escalate |
| `harmful_content` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `intellectual_property` | Llm, Agent | Post only | Block, Log, Escalate |
| `user_prompt_attacks` | Llm | Pre only | Block, Log, Escalate |
| `llm_as_judge` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |

> **`llm_as_judge` needs an LLM Gateway model.** Its `model` parameter comes back with an **empty** `Options` list from `uip agent guardrails list` — the valid values live in LLM Gateway, not the catalog. Run `uip agent guardrails llm-as-judge-models --output json` and use a `ModelId` from the result for the `model` parameter (prefer a non-preview model; a small/fast model such as a Haiku / mini class is a sound judge default). If the command returns no models or fails (no LLM Gateway access), tell the user and ask them to configure a model in their LLM Gateway or supply a model ID. Its other parameters are `guardrailText` (`text`, required), `positiveExamples` / `negativeExamples` (`text-list`, optional), and `threshold` (`number`, optional).

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

Each example is one entry in the agent node's `inputs.guardrails[]`.

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

### Example 8: Escalate PII Violations to Action Center

Escalates to an Action Center app when email or credit card PII is detected at the agent level. `app.id`, `app.name`, and `app.folderName` come from `uip solution resources list --kind App`.

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

## What NOT to Do

> Canonical inline-agent anti-patterns (never author sidecar files or `guardrail.policies`, discriminator omission, UUID reuse) live in [../critical-rules.md](../critical-rules.md). The guardrail-specific anti-patterns below extend (do not repeat) that list.

1. **Do not use snake_case for PII entity names** — use PascalCase: `"Email"` not `"email_address"`, `"PhoneNumber"` not `"phone_number"`, `"USSocialSecurityNumber"` not `"us_ssn"`.
2. **Do not add `prompt_injection` to Tool or Agent scope** — it only works with `"Llm"` scope, PreExecution stage.
3. **Do not add `user_prompt_attacks` to Tool or Agent scope** — Llm only, PreExecution only.
4. **Do not add `intellectual_property` to Tool scope** — only `"Llm"` and `"Agent"` scopes are supported.
5. **Do not add `intellectual_property` to PreExecution stage** — PostExecution only.
6. **Do not omit `matchNames` when `Tool` is in `scopes`** — always explicitly list the target tool names (each tool node's `inputs.name`). See [matchNames — "All Tools" Behavior](#matchnames--all-tools-behavior).
7. **Do not use `filter` action on built-in validators** — `"$actionType": "filter"` is only supported on deterministic (`custom`) rules. Every built-in validator (`$guardrailType: "builtInValidator"`) supports only `block`, `log`, and `escalate` (see the [Validators Quick Reference](#validators-quick-reference) § Supported Actions).
8. **Do not use odd numbers or floats for `harmfulContentEntityThresholds`** — only `0`, `2`, `4`, `6` are valid severity values. Values like `3` or `2.5` cause runtime rejection.
9. **Do not add a built-in validator without first running `uip agent guardrails list --output json`** — always fetch the list, verify the validator exists, and confirm `Status` is `"Available"`. Adding an `Unauthorised` or non-existent validator causes runtime failures.
10. **Do not use Action Center apps with `Type: "VB Action"` or `Type: "Coded"` as escalation targets** — only `Type: "Workflow Action"` or `"JS Action"` entries can back a guardrail escalation. Always filter `uip solution resources list --kind App` results by type.
11. **Do not use `--kind Process` (Type: `"webApp"`) to find escalation apps** — those entries are code-behind processes, not app deployments. Their `Key` values are process release GUIDs, not app IDs. Always use `--kind App`.
12. **Do not put `"solution_folder"` into the escalate action's `app.folderName`** — set it to the literal `Folder` from `uip solution resources list --kind App` (e.g., `"Shared/Approvals"`). Omit `app.folderId`; `FolderKey` from `resource list` is NOT used in any `app.*` field.
13. **Do not add a Tool-scoped guardrail before the tool node is wired to the agent** — every name in `selector.matchNames` must match the `inputs.name` of a resource node connected to the agent's `tool` handle. `flow validate` will NOT catch a ghost reference (unlike `uip agent validate` for standalone agents) — the guardrail silently never fires. Enumerate the wired tool nodes first and confirm targets are present; add missing tools per their capability doc before the guardrail.
14. **Do not skip action schema validation for escalation apps** — before writing a guardrail with `"$actionType": "escalate"`, fetch the app's action schema and verify all required inputs (8), outputs (3), and outcomes (2) are present by name. If any are missing, report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` and do not proceed. See [§ Adding an escalation guardrail — Step 2](#adding-an-escalation-guardrail--step-by-step).
15. **Do not use `Agent` or `Llm` scopes on custom guardrails** — custom guardrails (`$guardrailType: "custom"`) only support `"Tool"` scope with exactly one tool in `matchNames`. Custom rules depend on the tool's input/output schema, so they cannot target multiple tools. Create a separate custom guardrail per tool.
16. **Do not auto-generate a custom guardrail as fallback** — when a built-in validator is unavailable, unsupported for the requested scope, or unauthorized, inform the user and stop. Do not silently generate a custom guardrail as a workaround. You may suggest a custom guardrail alternative (for `Tool` scope only), but only generate it after explicit user confirmation.
17. **Do not create separate guardrails per scope** — when a guardrail applies to multiple scopes (e.g., `Agent` and `Tool`), combine them into a single guardrail with `"scopes": ["Agent", "Tool"]`. Do not create two separate guardrail objects with identical configuration differing only in scope.
18. **Do not attempt OR logic within a single guardrail** — all rules and all fields within a guardrail are combined with AND. OR is not supported. To achieve OR behavior, create separate guardrails — one per condition branch.
19. **Do not write guardrails into resource node `inputs` or any derived file** — the ONLY authored location is the agent node's `inputs.guardrails[]`. `guardrail.policies` on derived tool resources is projection output.
20. **Do not treat a passing `flow validate` as guardrail confirmation** — validate is silent on guardrails (§ [`flow validate` does NOT check guardrails](#flow-validate-does-not-check-guardrails)). Re-read the written objects against this reference (discriminators, PascalCase, parameter `id`s from `guardrails list`) before reporting done.

## Walkthrough

Use when adding input/output safeguards (PII detection, harmful content blocking, custom word rules) to an inline agent. Guardrails are configured on the agent node's `inputs.guardrails` array.

> **MANDATORY: Read this file BEFORE writing any guardrail JSON.** The guardrail schema uses discriminator fields (`$actionType`, `$parameterType`, `$ruleType`, `$selectorType`) that cannot be guessed. PII detection uses `$guardrailType: "builtInValidator"` with `validatorType: "pii_detection"` — NOT `$guardrailType: "pii"`. Parameters use `id` (not `name`) and require `$parameterType`. Actions use `$actionType` (not `type`). PII entities are PascalCase (`"Email"`, not `"email_address"`). There is no `pattern`, `target`, or `message` field.
>
> **MANDATORY for `builtInValidator` guardrails: run `uip agent guardrails list --output json` before writing one.** The command gives you the exact `$parameterType` values, parameter `id` names, and allowed scopes — values you cannot safely derive from the type name alone. Skipping it leads to invalid parameter shapes that fail at runtime (validate will not catch them). **Custom guardrails (`$guardrailType: "custom"`) do NOT need this step** — their rules (word/number/boolean/always), operators, and actions are fully specified here in this reference and use no validator catalog. Only run `guardrails list` for a custom guardrail if you are unsure whether the request should instead use a built-in validator.

### Step 1 — Verify the embedded agent

Ensure the `.flow` has a self-contained `uipath.agent.autonomous` node ([impl.md § 2](../impl.md#2-agent-node-inputs-spec)). A legacy shell must be migrated first ([impl.md § 11](../impl.md#11-legacy-flows--detect-and-migrate)).

### Step 2 — Verify target tools exist (required for Tool-scoped guardrails)

**Skip this step if the guardrail targets only `"Agent"` or `"Llm"` scope with no `matchNames`.**

If the guardrail will use `selector.scopes: ["Tool"]` with `selector.matchNames`, enumerate the resource nodes wired to the agent's `tool` handle and collect their `inputs.name` values.

For each tool name you plan to put in `matchNames`:
- **Wired** — proceed.
- **Not wired** — **STOP.** Do not add the guardrail yet. Add the tool first, then return here:
  - Process tool — RPA / agent / API / process orchestration: [process.md](process.md)
  - Built-in tool: [built-in-tools.md](built-in-tools.md)
  - Integration Service tool: [integration-service.md](integration-service.md)
  - IXP tool: no dedicated capability doc — pin its `inputs` shape from the `registry get` manifest's `inputDefaults` ([impl.md § 7](../impl.md#7-resource-nodes))

> `flow validate` does NOT enforce this — a ghost `matchNames` entry passes validation and silently never fires. The enumeration above is the only gate.

### Step 3 — Fetch and verify available validators (mandatory for built-in validators)

```bash
uip agent guardrails list --output json
```

Apply the four-outcome decision rule from [Step 0](#step-0--fetch-available-validators-mandatory-first-step). Only add guardrails for validators with `Status: "Available"`. Use the output to determine `validatorType` values, allowed scopes, stages, and required parameters. Do not hardcode assumptions.

### Step 4 — Add the guardrail to the agent node

Append the object to `inputs.guardrails[]` on the `uipath.agent.autonomous` node (a `guardrails: []` placeholder is appended into; create the array if absent).

For built-in validators, see [Built-in Validator Guardrails](#built-in-validator-guardrails-guardrailtype-builtinvalidator) (Examples 1–5, 8). For custom rules, see [Custom Guardrails](#custom-guardrails-guardrailtype-custom) (Examples 6, 7, 9, 10). Generate a fresh UUID for each guardrail `id`.

### Step 5 — Format and validate

```bash
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

Validate confirms the flow structure only — it is **silent on guardrail content**. As the final gate, re-read the written guardrail objects and check: every discriminator present, PascalCase entities/scopes, parameter `id`s matching `guardrails list`, `matchNames` matching wired tools' `inputs.name`.

## References

- [../critical-rules.md](../critical-rules.md) — canonical inline-agent rules (sidecar prohibition, UUID minting, validation ladder)
- [guardrails-recommend.md](guardrails-recommend.md) — WHEN to add guardrails and WHY (catalog-driven recommendation + validation of existing guardrails)
- [../impl.md § 2](../impl.md#2-agent-node-inputs-spec) — `guardrails` in the agent node `inputs` field table
- [../impl.md § 10](../impl.md#10-derived-sidecar--reference) — how `inputs.guardrails` projects into derived artifacts
