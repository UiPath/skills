# Guardrails Reference

## Overview

Guardrails inspect agent inputs and outputs for PII, harmful content, prompt injection, intellectual property, and custom rules. Configure them in the `guardrails` array at the **root of `agent.json`**.

Types:
- **`custom`** — deterministic `word`, `number`, `boolean`, or `always` rules.
- **`builtInValidator`** — UiPath Guardrails API validators.

**Autonomous agents:** use root `agent.json` `guardrails`.

**Conversational agents:** root `guardrails[]` is authoritative for Studio Web and both runtimes. Mirror each conversational Tool-scoped custom guardrail, with the same object and `id`, in `resources/<Tool>/resource.json` → `guardrail.policies[]`; the CLI does not auto-sync. A tool-only copy is invisible in Studio Web and does not run on the Unified (Python) runtime.

Conversational agents support only `$guardrailType: "custom"` deterministic rules (`word`, `number`, `boolean`, `always`) with `selector.scopes: ["Tool"]`. They support no built-in validators and no `"Agent"` or `"Llm"` scopes. If PII, harmful-content, or injection detection is requested, explain that built-in validators are autonomous-only and offer a Custom Tool guardrail or an autonomous agent.

After writing a conversational custom Tool guardrail, **run**:

```bash
uip agent refresh "<AGENT_NAME>" --output json
uip agent validate "<AGENT_NAME>" --output json
```

Do not report completion before validation has been attempted. This restriction is enforced by [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1.

## Base schema

Every guardrail requires:

| Field | Type | Required | Description |
|---|---|---:|---|
| `$guardrailType` | string | Yes | `"custom"` or `"builtInValidator"` |
| `id` | UUID string | Yes | Generate a fresh UUID for every guardrail. |
| `name` | string | Yes | Human-readable name. |
| `description` | string | Yes | May be `""`. |
| `action` | object | Yes | Exactly one action. |
| `enabledForEvals` | boolean | Yes | Whether it runs during evaluations. |
| `selector` | object | Yes | Scope and tool targeting. |

## Selectors and scope

```json
"selector": {
  "scopes": ["Agent", "Llm", "Tool"],
  "matchNames": ["<ToolName>"]
}
```

`scopes` is required and contains one or more of `"Agent"`, `"Llm"`, and `"Tool"`. `matchNames` is required whenever `"Tool"` is present and must explicitly name tools.

| Scope | Applies to | PreExecution | PostExecution |
|---|---|---:|---:|
| `Agent` | Agent-level input/output | Yes | Yes |
| `Llm` | LLM request/response | Yes | Yes |
| `Tool` | Individual tool calls | Yes | Yes |

Custom guardrails support only `"Tool"` and exactly one tool in `matchNames`; create one custom guardrail per tool. Built-in validators may use other scopes only when the validator catalog permits them. Combine multiple scopes in one guardrail; do not create separate copies. Conversational agents must use exactly `"Tool"`; `"Agent"`, `"Llm"`, and all `builtInValidator` guardrails are unavailable.

Supported `matchNames` tool types are `agent`, `process`, `activity`, `builtInTool`, `ixpTool`, and Integration Service connector. Every named tool must already exist under `<AGENT_NAME>/resources/<ToolName>/resource.json`.

To target all tools, read `resources/` and explicitly list every tool resource name. If none exist, do not add the guardrail; inform the user: *"No tool resources found in this agent. Cannot add a tool-scoped guardrail."*

For built-in validators, **run** `uip agent guardrails list --output json` and use returned `AllowedScopes` and `GuardrailStages`, not assumptions. Each `Data` entry contains `Status` (`"Available"` or `"Unauthorised"`), `Validator` (`validatorType`), `AllowedScopes`, `GuardrailStages`, and `Parameters` with `Type`, `Id`, and `Required`.

These catalog scopes describe only built-in-validator schemas; do not author built-in validators on conversational agents.

## Actions

Every action requires `$actionType`.

### `block`

Stops execution:

```json
{ "$actionType": "block", "reason": "<message>" }
```

`reason` is required and must be a string.

### `log`

Continues execution and records the violation:

```json
{ "$actionType": "log", "severityLevel": "Warning" }
```

`severityLevel` is required: `"Info"`, `"Warning"`, or `"Error"`.

### `filter`

Custom-only; redacts fields:

```json
{
  "$actionType": "filter",
  "fields": [{ "path": "<field.path>", "source": "output", "title": "<label>" }]
}
```

`fields` is required. Each entry requires string `path`, `source` (`"input"` or `"output"`), and `title`.

### `escalate`

Creates an Action Center task. Minimum user information is app name and recipient; email (`type: 3`) is simplest.

```json
{
  "$actionType": "escalate",
  "app": { "id": "<Key>", "name": "<Name>", "version": "0", "folderName": "<Folder>" },
  "recipient": { "type": 3, "value": "<email>" }
}
```

Required app fields are `id`, `name`, `version`, and `folderName`. Use `Key`, `Name`, and literal `Folder` from `uip solution resources list --kind App`; `version` is always `"0"`. Omit `folderId` and normally omit `appProcessKey`. `uip agent refresh` translates `folderName` to `folderPath` in the App binding in `bindings_v2.json`.

Recipient `type` values:

- `1=UserId`, `2=GroupId`, `3=UserEmail`, `4=AssetUserEmail`, `5=GroupName`, `6=AssetGroupName`, `7=ArgumentEmail`, `8=ArgumentGroupName`.
- Types `1`, `2`, `3`, and `5` require `value`; `displayName` is optional and recommended for type `1`.
- Types `4` and `6` require `assetName` and `folderPath`, not `value`.
- Types `7` and `8` require `argumentName`, a dot-path into the agent input schema.

Examples:

```json
{ "type": 3, "value": "<email>" }
{ "type": 1, "value": "<user-guid>", "displayName": "<name>" }
{ "type": 4, "assetName": "<asset>", "folderPath": "<folder>" }
{ "type": 7, "argumentName": "<input.path>" }
```

Prefer `type: 3`; Studio Web uses `type: 1` when a user is selected through the UI.

## Adding an escalation guardrail

If creating a solution or agent, **run** both `uip solution init` and `uip agent init` before app discovery. An incompatible or missing app rejects only the guardrail, not local scaffolding.

1. **Run** `uip agent guardrails list --output json` even when the validator type is known. Confirm the validator and exact parameter `id` and `$parameterType` values.
2. From the solution root, **run**:

```bash
uip solution resources list --kind App --source remote --search "<app-name>" --output json
```

Filter for `"Type": "Workflow Action"`. Map `Key` → `app.id`, `Name` → `app.name`, and `Folder` → `app.folderName`. Never use `FolderKey` in `app.*`. If duplicate names occur in different folders, ask which deployment to use.

Immediately after listing, both branches must **run** `resources get` before editing, refreshing, validating, or responding:

- Exact row: **run** `uip solution resources get "<Key from the row>" --output json`.
- No exact row/key: **run** `uip solution resources get "<requested app name>" --output json` once; treat failure as `GET_ERROR`.

Do not use `--kind Process` with `Type: "webApp"`; these are code-behind processes and their `Key` values are process release GUIDs, not app deployment IDs.

3. Verify the action schema before writing JSON. Pipe the required `resources get` result to a verifier that checks these names:

- Inputs: `GuardrailName`, `GuardrailDescription`, `TenantName`, `AgentTrace`, `Tool`, `ExecutionStage`, `ToolInputs`, `ToolOutputs`.
- Outputs: `ReviewedInputs`, `ReviewedOutputs`, `Reason`.
- Outcomes: `Approve`, `Reject`.

A name-only verifier may use:

```bash
cat > /tmp/verify_escalation_app.py <<'PY'
import sys, json
data = json.load(sys.stdin)
if data.get("Result") != "Success":
    sys.exit("GET_ERROR: uip solution resources get failed: " + str(data.get("Message", "unknown error")))
raw = data.get("Data", {}).get("Spec", {}).get("ActionSchema")
if not raw:
    sys.exit("NO_SCHEMA: app spec has no ActionSchema — not a deployed Workflow Action app")
sch = json.loads(raw)
need = {"inputs": {"GuardrailName", "GuardrailDescription", "TenantName", "AgentTrace", "Tool", "ExecutionStage", "ToolInputs", "ToolOutputs"}, "outputs": {"ReviewedInputs", "ReviewedOutputs", "Reason"}, "outcomes": {"Approve", "Reject"}}
miss = {k: sorted(v - {x["name"] for x in sch.get(k, [])}) for k, v in need.items() if v - {x["name"] for x in sch.get(k, [])}}
print("OK" if not miss else "MISSING: " + json.dumps(miss))
sys.exit(0 if not miss else 1)
PY
uip solution resources get "<Key from Step 1>" --output json | python3 /tmp/verify_escalation_app.py
```

Decision rules:

- `OK`: proceed.
- `MISSING: {...}` or `NO_SCHEMA: ...`: report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` and do not write the guardrail.
- `GET_ERROR: ...`: report `<APP_NAME> could not be verified for the required action schema configuration.` Do not re-authenticate or try alternate endpoints; one failed verifier call is terminal for this run.

4. After verification succeeds, add `escalate` using the selected `Key`, `Name`, and `Folder`.
5. From the solution root, **run**:

```bash
uip agent refresh <AgentName> --output json
uip agent validate <AgentName> --output json
uip solution resources refresh --output json
```

`refresh` regenerates `entry-points.json` and `bindings_v2.json`, including an `resource: "app"` binding with `name` and translated `folderPath`. `validate` is read-only and fails with `AgentValidationOutdated` when refresh is needed. `solution resources refresh` reads `bindings_v2.json`, resolves the app by `(name, folderPath)`, and generates the four solution-level resource files (`app/workflow Action/`, `appVersion/`, `package/`, `process/webApp/`) plus `debug_overwrites.json` entries for the app and code-behind process.
6. To upload, **run**:

```bash
uip solution upload . --output json
```

## Custom guardrails

Custom guardrails contain a `rules` array. Every rule requires `$ruleType`; every field selector requires `$selectorType`; every action requires `$actionType`.

All rules in one guardrail are combined with **AND**. Multiple fields in one `specific` selector are also AND. OR is unsupported; create separate guardrails, one per branch.

```json
{
  "$guardrailType": "custom",
  "id": "<UUID>",
  "name": "<name>",
  "description": "<description>",
  "enabledForEvals": true,
  "selector": { "scopes": ["Tool"], "matchNames": ["<one tool>"] },
  "action": { "$actionType": "block", "reason": "<message>" },
  "rules": [{ "$ruleType": "word", "fieldSelector": { "$selectorType": "all" }, "operator": "contains", "value": "<text>" }]
}
```

### Rule types

- **Word:** `$ruleType: "word"`, `fieldSelector`, `operator`, and string `value`. Operators: `contains`, `equals`, `startsWith`, `endsWith`, `matchesRegex`, `doesNotContain`, `doesNotEqual`, `doesNotStartWith`, `doesNotEndWith`, `isEmpty`, `isNotEmpty`. `isEmpty` and `isNotEmpty` need no `value`.
- **Number:** `$ruleType: "number"`, `fieldSelector`, one of `equals`, `doesNotEqual`, `greaterThan`, `greaterThanOrEqual`, `lessThan`, `lessThanOrEqual`, and numeric `value`.
- **Boolean:** `$ruleType: "boolean"`, `fieldSelector`, `operator: "equals"`, and boolean `value` (`true` or `false`).
- **Always:** `$ruleType: "always"`, `applyTo: "input"`, `"output"`, or `"inputAndOutput"`; no condition or field selector.

Field selectors:

```json
{ "$selectorType": "all" }
```

```json
{
  "$selectorType": "specific",
  "fields": [
    { "path": "<field.path>", "source": "input" },
    { "path": "<other.path>", "source": "output", "title": "<label>" }
  ]
}
```

`$selectorType` is required and is `"all"` or `"specific"`. Specific selectors require `fields`; each field requires string `path` and `source` (`"input"` or `"output"`), with optional `title`.

## Built-in validators

Before adding any built-in validator, **run**:

```bash
uip agent guardrails list --output json
```

Check `Data`:

1. Missing validator: report *"The built-in validator `<name>` is not available on your tenant. Check the validator name or contact your UiPath administrator."* Stop; do not create a custom fallback.
2. `Status: "Available"`: proceed.
3. `Status: "Unauthorised"`: report *"You are not entitled to use the `<name>` guardrail. You can view the configuration but cannot apply it to agents. Contact your UiPath administrator to enable guardrail entitlements."* Stop.
4. Unsupported requested scope: tell the user the supported scopes. Do not auto-generate a custom fallback; suggest one only with explicit confirmation and only for `Tool` scope.

Built-ins use `validatorType` and `validatorParameters`. Every parameter requires `$parameterType`, `id` (not `name`), and `value` where applicable.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "<UUID>",
  "name": "<name>",
  "description": "<description>",
  "enabledForEvals": true,
  "selector": { "scopes": ["<catalog-supported scope>"] },
  "action": { "$actionType": "block", "reason": "<message>" },
  "validatorType": "<Validator>",
  "validatorParameters": [{ "$parameterType": "enum-list", "id": "<Id>", "value": ["<value>"] }]
}
```

**`user_prompt_attacks` takes NO parameters — set `validatorParameters: []`** (Llm-scope, PreExecution only, `block`/`log`/`escalate`; binary detection via Azure Prompt Shield). `prompt_injection` is NOT parameter-less — it takes a `threshold` number, e.g. `{ "$parameterType": "number", "id": "threshold", "value": 0.5 }`. Example `user_prompt_attacks`:

```json
{
  "$guardrailType": "builtInValidator",
  "id": "<UUID>",
  "name": "User prompt attack guardrail",
  "description": "Blocks adversarial user-prompt attacks (Azure Prompt Shield).",
  "validatorType": "user_prompt_attacks",
  "validatorParameters": [],
  "action": { "$actionType": "block", "reason": "Adversarial input detected — execution blocked." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Llm"] }
}
```

Parameter types:

| `$parameterType` | Value |
|---|---|
| `enum-list` | string[]; e.g. `entities`, `harmfulContentEntities`, `ipEntities` |
| `map-enum` | object of entity names to numbers; e.g. `entityThresholds`, `harmfulContentEntityThresholds` |
| `number` | number; e.g. `threshold` |
| `enum` | string; e.g. `model` |
| `text` | string; e.g. `guardrailText` |
| `text-list` | string[]; e.g. `positiveExamples`, `negativeExamples` |

Authoritative CLI mapping:

| CLI field | JSON field or use |
|---|---|
| `Status` | Proceed only with `"Available"`; `"Unauthorised"` and `"Disabled"` are not usable. |
| `Validator` | `validatorType` |
| `AllowedScopes` | `selector.scopes` |
| `GuardrailStages[scope]` | Valid execution stages |
| `Parameters[].Id` | `validatorParameters[].id` |
| `Parameters[].Type` | `validatorParameters[].$parameterType` |
| `IsByo` | Distinguishes BYO from built-in; not a JSON field. |
| `ByoValidatorName` | `byoValidatorName` when pinning a BYO configuration. |

Scope values and entity names are case-sensitive: use `"Agent"`, `"Llm"`, `"Tool"`; PII names such as `"Email"`, `"PhoneNumber"`, `"CreditCardNumber"`, `"USSocialSecurityNumber"`; harmful-content categories such as `"Hate"`, `"SelfHarm"`, `"Sexual"`, `"Violence"`; and IP entities such as `"Text"`, `"Code"`.

Quick reference for autonomous agents; all are unusable on conversational agents:

| Validator | Scopes | Stages | Actions |
|---|---|---|---|
| `pii_detection` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `prompt_injection` | Llm | Pre only | Block, Log, Escalate |
| `harmful_content` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |
| `intellectual_property` | Llm, Agent | Post only | Block, Log, Escalate |
| `user_prompt_attacks` | Llm | Pre only | Block, Log, Escalate |
| `llm_as_judge` | Agent, Llm, Tool | Pre + Post | Block, Log, Escalate |

Built-in validators support only `block`, `log`, and `escalate`; `filter` is custom-only.

`llm_as_judge` requires an LLM Gateway model. Its `model` `Options` list may be empty. **Run**:

```bash
uip agent guardrails llm-as-judge-models --output json
```

Use a returned `ModelId`, preferably a non-preview small/fast model. If no models are returned or the command fails, tell the user to configure LLM Gateway access or provide a model ID. Other parameters are required `guardrailText` (`text`) and optional `positiveExamples` / `negativeExamples` (`text-list`) and `threshold` (`number`).

## BYO (bring-your-own) guardrails

Tenants may register external providers such as Azure AI Content Safety or Databricks AI Guardrails through Admin → AI Trust Layer → Guardrails Configurations or `uip guardrails byo-configurations create`; lifecycle commands are `uip guardrails byo-configurations list|create|update|delete`. See [uipath-platform § BYO Guardrail Configurations](/uipath:uipath-platform).

`Validator` is not unique: built-in and BYO entries may share a name. Use `IsByo`; **run** `uip agent guardrails list --byo --output json` when specifically targeting BYO. BYO entries may contain `ByoValidatorName`, `ByoConnectionId`, `ByoConfigurationId`, `ByoConnectorName`, `ByoConnectorKey`, and `FolderKey`. To target one, use the same `builtInValidator` structure and set `byoValidatorName` to its `ByoValidatorName`; do not put `ByoConfigurationId` in guardrail JSON. A BYO entry with `Status: "Disabled"` is unusable and must be treated like `Unauthorised`.

## Required workflow

1. Read this reference before writing JSON; do not guess `$guardrailType`, `$actionType`, `$parameterType`, `$ruleType`, `$selectorType`, parameter `id`, scope casing, or entity casing. PII detection uses `$guardrailType: "builtInValidator"` + `validatorType: "pii_detection"` — never `$guardrailType: "pii"`; there is no `pattern`, `target`, or `message` field.
2. Verify the agent project and `agent.json`; for a fresh project follow [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).
3. For Tool scope, **run**:

```bash
uip agent tool list --output json
```

Stop if the target tool is absent; add it first using [../process/process.md](../process/process.md) or [../integration-service/integration-service.md](../integration-service/integration-service.md).
4. For built-ins, **run** `uip agent guardrails list --output json`; verify availability, scope, stages, and exact parameters. Skip catalog discovery for custom-only guardrails.
5. **Write the guardrail object into the root `agent.json` `guardrails[]` array — this is mandatory; discovery via `uip agent guardrails list` alone does NOT satisfy the task, the `guardrails` array must be non-empty.** Mirror conversational custom Tool guardrails in the tool resource's `guardrail.policies[]`.
6. **Run**:

```bash
uip agent refresh "<AGENT_NAME>" --output json
uip agent validate "<AGENT_NAME>" --output json
```

Confirm validation succeeds and the guardrail appears in validated output. For escalation, complete the app-discovery and action-schema gates before writing JSON, then **run** `uip solution resources refresh --output json` and **run** `uip solution upload . --output json` as required.

## What NOT to do

1. Do not use snake_case PII names: use `"Email"`, `"PhoneNumber"`, and `"USSocialSecurityNumber"`, not `"email_address"`, `"phone_number"`, or `"us_ssn"`.
2. Do not use `prompt_injection` on Tool or Agent; it is Llm PreExecution only.
3. Do not use `user_prompt_attacks` on Tool or Agent; it is Llm PreExecution only.
4. Do not use `intellectual_property` on Tool; use only Llm or Agent, PostExecution only.
5. Do not omit `matchNames` for Tool scope.
6. Do not use `filter` with built-in validators.
7. Do not use odd numbers or floats for `harmfulContentEntityThresholds`; only `0`, `2`, `4`, and `6` are valid.
8. Do not add a built-in without first running `uip agent guardrails list --output json` and confirming `Status: "Available"`.
9. Do not use Action Center apps with `Type: "VB Action"` or `Type: "Coded"`; use only `Type: "Workflow Action"`.
10. Do not use `--kind Process` / `Type: "webApp"` to find escalation apps.
11. Do not put `"solution_folder"` in `app.folderName`; use literal `Folder`, omit `app.folderId`, and never use `FolderKey` in `app.*`. `FolderKey` belongs in `debug_overwrites.json` mappings.
12. Do not add a Tool guardrail before its tool exists; **run** `uip agent tool list` first.
13. Do not skip escalation action-schema validation. Verify 8 inputs, 3 outputs, and 2 outcomes by name before writing the guardrail.
14. Do not use `Agent` or `Llm` on custom guardrails; use exactly one Tool in `matchNames`.
15. Do not auto-generate a custom fallback when a built-in is unavailable, unsupported, unauthorized, or disabled. Suggest it only for Tool scope and generate it only after explicit confirmation.
16. Do not create separate guardrails for combined scopes; use one guardrail with multiple `scopes` values.
17. Do not attempt OR logic inside one guardrail; rules and fields are AND. Create separate guardrails for OR branches.
18. Do not target unsupported tool types; allowed types are `agent`, `process`, `activity`, `builtInTool`, `ixpTool`, and Integration Service connector.
19. Do not omit `matchNames` to imply all tools; enumerate every resource name, and do not add the guardrail when none exist.
20. Do not assume `Validator` is unique; inspect `IsByo` and set `byoValidatorName` for a selected BYO entry.
21. Do not reuse UUIDs.
22. Do not omit `$actionType`, `$parameterType`, `$ruleType`, or `$selectorType`.
23. Do not use lowercase scope values.
24. Do not populate tool-resource `guardrail.policies[]` as the authoritative source; for conversational custom Tool guardrails, root `guardrails[]` is authoritative and the tool resource is only its required mirror.

Canonical anti-pattern guidance is also in [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) § What NOT to Do and [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) § Guardrails. Conversational restrictions are in [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1.

## Root placement

Place `guardrails` alongside `settings`, `messages`, schemas, and metadata in `agent.json`:

```json
{
  "version": "1.1.0",
  "settings": { "...": "..." },
  "inputSchema": { "...": "..." },
  "outputSchema": { "...": "..." },
  "metadata": { "...": "..." },
  "type": "lowCode",
  "guardrails": [
    {
      "$guardrailType": "custom",
      "id": "<UUID>",
      "name": "<name>",
      "description": "<description>",
      "rules": [{ "$ruleType": "always", "applyTo": "output" }],
      "action": { "$actionType": "block", "reason": "<message>" },
      "enabledForEvals": true,
      "selector": { "scopes": ["Tool"], "matchNames": ["<ToolName>"] }
    }
  ],
  "messages": ["..."],
  "projectId": "<UUID>"
}
```

## References

- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) — canonical low-code rules and guardrail anti-patterns (discriminators, scope casing, populating `guardrail.policies` on tool resources, UUID reuse)
- [../../project-lifecycle.md](../../project-lifecycle.md) § `uip agent guardrails list` — CLI reference for validator discovery
- [../../agent-definition.md](../../agent-definition.md) § Guardrails — root-level placement in `agent.json`
