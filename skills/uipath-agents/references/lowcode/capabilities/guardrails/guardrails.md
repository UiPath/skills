# Guardrails Reference

## Overview

Guardrails inspect agent inputs/outputs—text and, for built-in validators with `detectionScope`, attached or produced files—for PII, harmful content, prompt injection, intellectual property, and custom-rule violations. Configure them in the **`agent.json` root `guardrails` array**.

Types: **`custom`** deterministic word, number, boolean, or universal-trigger rules; **`builtInValidator`** UiPath Guardrails API validators for PII, harmful content, prompt injection, IP protection, user prompt attacks, and LLM-as-judge.

**Autonomous agents:** use root `guardrails`. **Conversational agents:** root `guardrails[]` is authoritative for Studio Web and both runtimes; mirror each Tool-scoped guardrail in `resources/<Tool>/resource.json` → `guardrail.policies[]` (see [Conversational Support](#conversational-support)).

**Schema authority:** do not inspect CLI internals or SDKs. Never grep `/usr/lib/node_modules/@uipath/**/dist/*.js`, read bundled/minified sources, or import-probe packages. Copy the complete applicable example, adapt values, then run `uip agent refresh "<AGENT_NAME>" --output json` and `uip agent validate "<AGENT_NAME>" --output json`; validation is the only schema check needed. Write first and let validation identify offending fields.

## Walkthrough

Use this file plus [escalation-guide.md](escalation-guide.md), [custom-rules-guide.md](custom-rules-guide.md), or [files-guide.md](files-guide.md) as applicable. Read [files-guide.md](files-guide.md) whenever the agent has a `job-attachment` input/output, an Analyze Files or Create File tool, or the request mentions files/attachments. Do not read model-selection, prompting, or eval references. Run `uip agent guardrails list` directly; never run login/auth/config preflight commands, and react only to an actual authentication error.

**MANDATORY: read this file before writing guardrail JSON.** Use `$guardrailType: "builtInValidator"` and `validatorType: "pii_detection"` for PII, not `$guardrailType: "pii"`; parameters use `id` and `$parameterType`, actions use `$actionType`, and PII entities are PascalCase (`"Email"`, not `"email_address"`). There is no `pattern`, `target`, or `message` field.

**MANDATORY for `builtInValidator`: run `uip agent guardrails list --output json` before writing it.** Use its exact `$parameterType`, parameter `id`, and allowed scopes. Skipping it leads to invalid parameter shapes that fail schema validation. Custom guardrails skip this catalog step; their rules are defined in [custom-rules-guide.md](custom-rules-guide.md). Only run `guardrails list` for a custom guardrail if unsure whether the request should instead use a built-in validator.

### Step 0 — Fetch available validators (mandatory for `builtInValidator` guardrails; skip for custom-only)

Before any built-in, run:

```bash
uip agent guardrails list --output json
```

Apply [Step 0 — Fetch Available Validators (Mandatory First Step)](#step-0--fetch-available-validators-mandatory-first-step). Skip for purely custom rules.

### Step 1 — Verify existing agent

Ensure the project and valid `agent.json` exist. For a new project, follow [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

### Step 2 — Verify target tools exist (required for Tool-scoped guardrails)

Skip if the guardrail targets only `"Agent"` or `"Llm"` with no `matchNames`. Otherwise run:

```bash
uip agent tool list --output json
```

Every planned `matchNames` value must be found in `Data`. If absent, **STOP**; add the tool first, then return:
- Process tool (RPA / agent / API / agentic, local or external): [../process/process.md](../process/process.md)
- Integration Service tool: [../integration-service/integration-service.md](../integration-service/integration-service.md)

`uip agent validate` fails when a Tool-scoped guardrail names an unadded tool.

### Step 3 — Add a guardrail to agent.json

For built-ins, use [Built-in Validator Guardrails](#built-in-validator-guardrails-guardrailtype-builtinvalidator) and [Full Examples](#full-examples) (Examples 1–6); for escalation, use [escalation-guide.md](escalation-guide.md); for custom rules, use [custom-rules-guide.md](custom-rules-guide.md). Copy the complete example that matches the request and adapt the values — e.g., [Example 1](#example-1-block-pii-in-agent-and-tool-outputs) for a built-in PII block guardrail. Then generate a fresh UUID, and place it as shown in [agent.json with Guardrails](#agentjson-with-guardrails).

### Step 4 — Refresh and validate

Run:

```bash
uip agent refresh "<AGENT_NAME>" --output json
uip agent validate "<AGENT_NAME>" --output json
```

Confirm validated output has the guardrails without errors. Refresh regenerates `entry-points.json` and `bindings_v2.json` for Studio Web.

## Conversational Support

**Only custom deterministic Tool-scoped guardrails run.** No `builtInValidator` runs on conversational agents at any scope; `"Agent"` and `"Llm"` are unavailable. Write each custom Tool guardrail as the **same object with the same `id`** in root `agent.json` `guardrails[]` (authoritative for Studio Web and both runtimes) and the tool's `resources/<Tool>/resource.json` → `guardrail.policies[]` (mirror). The CLI does not auto-sync. A tool-only copy is invisible in Studio Web and does not run on the Unified (Python) runtime. For PII, harmful-content, or injection detection, explain built-ins are autonomous-only and offer a Custom Tool guardrail or autonomous agent.

This is [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1.

**Required completion gate:** after writing a conversational custom Tool guardrail, run `uip agent refresh "<AGENT_NAME>" --output json`, then execute `uip agent validate "<AGENT_NAME>" --output json`. Do not report completion until validation has been attempted.

## Guardrail Schema (Base Fields)

Every root `guardrails` object requires:

| Field | Type | Meaning |
|---|---|---|
| `$guardrailType` | string | Required discriminator: `"custom"` or `"builtInValidator"` |
| `id` | UUID string | Required fresh unique UUID |
| `name` | string | Required human-readable name |
| `description` | string | Required description; may be `""` |
| `action` | object | Required; see [Actions](#actions) |
| `enabledForEvals` | boolean | Required; whether the guardrail runs during evaluations |
| `selector` | object | Required scope/tool selection; see [Selector](#selector-scoping) |

## Selector (Scoping)

```json
"selector": { "scopes": ["Agent", "Llm", "Tool"], "matchNames": ["ToolName1", "ToolName2"] }
```

`scopes` is required and contains one or more of `"Agent"`, `"Llm"`, `"Tool"`; conversational agents use `["Tool"]` ONLY — DO NOT use `"Agent"`/`"Llm"`. `matchNames` is required whenever `"Tool"` is present and must explicitly name tools.

### Scope Definitions

| Scope | Applies to | PreExecution | PostExecution |
|---|---|---|---|
| `Agent` | Agent input/output | Yes | Yes |
| `Llm` | LLM request/response | Yes | Yes |
| `Tool` | Individual tool calls | Yes | Yes |

Custom rules support only `"Tool"` with exactly one `matchNames` tool; built-ins may use `Agent`, `Llm`, and `Tool` according to catalog output.

### Combining Multiple Scopes

Combine scopes in one guardrail, e.g. `"selector": { "scopes": ["Agent", "Tool"], "matchNames": ["MyTool"] }`; do not duplicate the object per scope.

### matchNames — Supported Tool Types

Supported Tool types for `matchNames`: `agent` (low-code or coded agent), `process` (RPA XAML workflow), `activity` (activity-based tool), `builtInTool` (built-in platform tool), `ixpTool` (IXP tool), and Integration Service connector (IS connector tool). Do not target other types.

### matchNames — "All Tools" Behavior

Read the agent's `resources/` directory and explicitly list every tool resource name; never omit `matchNames`. If no tool resources exist, do not add the guardrail; inform the user: *"No tool resources found in this agent. Cannot add a tool-scoped guardrail."*

### Built-in Validator Scope Support

Run `uip agent guardrails list --output json`; do not hardcode availability or scope/stage support. Each `Data` entry has `Status`: `"Available"` or `"Unauthorised"` (use only `"Available"`), `Validator`: `validatorType`, `AllowedScopes`, `GuardrailStages`, and `Parameters` definitions with `Type`, `Id`, and `Required`.

Conversational override: `AllowedScopes` describes schema acceptance only; built-ins remain unusable there. Do NOT author any `builtInValidator` guardrail for a conversational agent, at any scope. Use custom deterministic Tool rules only. See [../../critical-rules/conversational-critical-rules.md](../../critical-rules/conversational-critical-rules.md) Critical Rule 1.

## Actions

Each guardrail has exactly one `action`; `$actionType` is required.

### block — Stop Execution

`{ "$actionType": "block", "reason": "PII detected in output — cannot proceed." }`; halts the run; `reason` is required and user-facing.

### log — Log Violation

`{ "$actionType": "log", "severityLevel": "Info" }`; `severityLevel` is required: `"Info"`, `"Warning"`, or `"Error"`; logging does not stop execution.

### filter — Redact Fields

`{ "$actionType": "filter", "fields": [{ "path": "ssn", "source": "output", "title": "SSN" }] }`; `fields` and each item's `path` (for example `"ssn"` or `"address.zip"`), `source` (`"input"` or `"output"`), and `title` are required.

### escalate — Hand Off to Action Center

Creates an Action Center task and requires app discovery (`uip solution resources list --kind App`), action-schema compatibility verification, and a recipient. Do not author it without [escalation-guide.md](escalation-guide.md), which contains the schema, recipient shapes, workflow, and example.

## Custom Guardrails (`$guardrailType: "custom"`)

Custom guardrails use a `rules` array for word/number/boolean/always deterministic rules. They support only Tool scope with exactly one tool in `matchNames` and are the only type executed conversationally. See [custom-rules-guide.md](custom-rules-guide.md) for schema, operators, selectors, and examples.

## Step 0 — Fetch Available Validators (Mandatory First Step)

Before any built-in, run:

```bash
uip agent guardrails list --output json
```

Find the requested `Validator` in `Data`:

1. **Missing:** inform the user: *"The built-in validator `<name>` is not available on your tenant. Check the validator name or contact your UiPath administrator."* Do not add it, generate a custom fallback, or continue; stop.
2. **`Status: "Available"`:** proceed.
3. **`Status: "Unauthorised"`:** inform the user: *"You are not entitled to use the `<name>` guardrail. You can view the configuration but cannot apply it to agents. Contact your UiPath administrator to enable guardrail entitlements."* Do not add it.
4. **Requested scope absent from `AllowedScopes`:** tell the user supported scopes. Do not auto-generate custom; suggest it only with explicit confirmation, and only for Tool scope.

Configure only `"Available"` validators.

## Built-in Validator Guardrails (`$guardrailType: "builtInValidator"`)

Built-ins call the UiPath Guardrails API and require `validatorType` and `validatorParameters`. Parameter objects require `$parameterType` and `id`, never `name`.

```json
{
  "$guardrailType": "builtInValidator", "id": "<uuid>", "name": "PII Detection", "description": "Detects PII in tool outputs",
  "enabledForEvals": true, "selector": { "scopes": ["Tool"], "matchNames": ["MyToolName"] },
  "action": { "$actionType": "block", "reason": "PII detected" }, "validatorType": "pii_detection",
  "validatorParameters": [{ "$parameterType": "enum-list", "id": "entities", "value": ["Email", "PhoneNumber"] }]
}
```

### Parameter Types

| `$parameterType` | Use | `value` |
|---|---|---|
| `"enum-list"` | arrays such as `entities`, `harmfulContentEntities`, `ipEntities` | string[] |
| `"map-enum"` | threshold maps such as `entityThresholds`, `harmfulContentEntityThresholds` | object of entity names to numbers |
| `"number"` | scalar numbers such as `threshold` | number |
| `"enum"` | one choice, including `model` and `detectionScope` | string |
| `"text"` | free text such as `guardrailText` | string |
| `"text-list"` | arrays such as `positiveExamples`, `negativeExamples` | string[] |

### Validators Quick Reference

All are autonomous-only; none are usable conversationally. Supported actions are `Block`, `Log`, `Escalate` (action types `block`, `log`, `escalate`).

| Validator | Autonomous scopes | Conversational | Stages |
|---|---|---|---|
| `pii_detection` | Agent, Llm, Tool | **Not usable** | Pre + Post |
| `prompt_injection` | Llm | **Not usable** | Pre only |
| `harmful_content` | Agent, Llm, Tool | **Not usable** | Pre + Post |
| `intellectual_property` | Llm, Agent | **Not usable** | Post only |
| `user_prompt_attacks` | Llm | **Not usable** | Pre only |
| `llm_as_judge` | Agent, Llm, Tool | **Not usable** | Pre + Post |

Run `uip agent guardrails list --output json` and use only `Status: "Available"`. Map `Status`→gate, `Validator`→`validatorType`, `AllowedScopes`→`selector.scopes`, `GuardrailStages[scope]`→stage validity, `Parameters[].Id`→`validatorParameters[].id`, and `Parameters[].Type`→`validatorParameters[].$parameterType`. `IsByo` identifies BYO entries (it is not itself a JSON field); `ByoValidatorName` maps to `byoValidatorName` and is required when multiple entries share a `Validator`.

Use PascalCase scope values (`"Agent"`, `"Llm"`, `"Tool"`), PII entities (`"Email"`, `"PhoneNumber"`, `"USSocialSecurityNumber"`), and harmful categories (`"Hate"`, not lowercase).

`llm_as_judge` requires an LLM Gateway model. Its catalog `model` `Options` is empty; run:

```bash
uip agent guardrails llm-as-judge-models --output json
```

Use a returned `ModelId` (prefer non-preview; a small/fast Haiku / mini class is a sound default). If no models or access, tell the user to configure LLM Gateway or supply a model ID. Other parameters are required `guardrailText` (`text`), optional `positiveExamples`/`negativeExamples` (`text-list`), and optional `threshold` (`number`).

### Files and attachments (`detectionScope`)

If `uip agent guardrails list --output json` contains `Parameters` `Id: "detectionScope"`, add it when the agent handles files: `{ "$parameterType": "enum", "id": "detectionScope", "value": "Text" | "Files" | "Both" }`; otherwise do not add it. Omitted always means `"Text"`; scope/stage support is unchanged. `"Files"` evaluates run files (including `job-attachment` inputs, files returned by tools, and produced files); `"Both"` evaluates text and files.

Guard attached inputs with Agent PreExecution + `Files`; guard produced output with Agent PostExecution + `Files`. Custom rules never read file contents; `always` selects input/output only. BYO has no file support. For scope × stage coverage, supported types/caps, Analyze Files Tool scope, output-file recipe, Flow inline agents, testing, and degradation, see [files-guide.md](files-guide.md). A file input requires [../../agent-definition.md](../../agent-definition.md) § File Attachments.

## BYO (bring-your-own) guardrails

A tenant may register an external provider (for example Azure AI Content Safety or Databricks AI Guardrails) through Admin → AI Trust Layer → Guardrails Configurations or `uip guardrails byo-configurations create`; lifecycle commands are documented at [uipath-platform § BYO Guardrail Configurations](/uipath:uipath-platform): `uip guardrails byo-configurations list|create|update|delete`.

- BYO has no `detectionScope`; provider receives text only. Never set `"Files"`/`"Both"` with `byoValidatorName`.
- `Validator` is not unique. Use `IsByo`; a built-in and BYO may share a name.
- For BYO-only results, run `uip agent guardrails list --byo --output json`.
- BYO entries include `ByoValidatorName`, `ByoConnectionId`, `ByoConfigurationId`, `ByoConnectorName`, `ByoConnectorKey`, and `FolderKey`, plus normal `Parameters`/`AllowedScopes`/`GuardrailStages`/`Status`.
- To target one, use the same built-in schema and add `byoValidatorName` equal to `ByoValidatorName`; omit it for built-in. `ByoConfigurationId` is admin-side only and is not carried in guardrail JSON.
- Do not author a guardrail against a BYO entry with `Status: "Disabled"`; treat it like `Unauthorised` (skip and tell the user).

## Full Examples

### Example 1: Block PII in Agent and Tool Outputs

```json
{
  "$guardrailType": "builtInValidator", "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "name": "PII detection guardrail",
  "description": "This validator is designed to detect personally identifiable information using Azure Cognitive Services",
  "validatorType": "pii_detection",
  "validatorParameters": [
    { "$parameterType": "enum-list", "id": "entities", "value": ["Email", "PhoneNumber", "CreditCardNumber", "USSocialSecurityNumber"] },
    { "$parameterType": "map-enum", "id": "entityThresholds", "value": { "Email": 0.8, "PhoneNumber": 0.7, "CreditCardNumber": 0.9, "USSocialSecurityNumber": 0.9 } }
  ],
  "action": { "$actionType": "block", "reason": "PII detected in output — execution blocked." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Agent", "Tool"], "matchNames": ["MyToolName"] }
}
```

### Example 2: Log Harmful Content at Agent Level

```json
{
  "$guardrailType": "builtInValidator", "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901", "name": "Harmful content guardrail",
  "description": "Logs harmful content violations at agent level without blocking",
  "validatorType": "harmful_content",
  "validatorParameters": [
    { "$parameterType": "enum-list", "id": "harmfulContentEntities", "value": ["Hate", "SelfHarm", "Sexual", "Violence"] },
    { "$parameterType": "map-enum", "id": "harmfulContentEntityThresholds", "value": { "Hate": 2, "SelfHarm": 2, "Sexual": 4, "Violence": 2 } }
  ],
  "action": { "$actionType": "log", "severityLevel": "Warning" },
  "enabledForEvals": false,
  "selector": { "scopes": ["Agent"] }
}
```

### Example 3: Prompt Injection Detection

```json
{
  "$guardrailType": "builtInValidator", "id": "e5f6a7b8-c9d0-1234-efab-567890123456", "name": "Prompt injection guardrail",
  "description": "This validator is provided by Noma Security and is built to detect malicious attack attempts (e.g. prompt injection, jailbreak) in LLM calls.",
  "validatorType": "prompt_injection",
  "validatorParameters": [{ "$parameterType": "number", "id": "threshold", "value": 0.5 }],
  "action": { "$actionType": "log", "severityLevel": "Info" },
  "enabledForEvals": true,
  "selector": { "scopes": ["Llm"] }
}
```

### Example 4: User Prompt Attack Detection — Block Jailbreaks

No required parameters — binary detection via Azure Prompt Shield; `detectionScope` is the only optional one (see [Files and attachments](#files-and-attachments-detectionscope)). Llm PreExecution only.

```json
{
  "$guardrailType": "builtInValidator", "id": "f1a2b3c4-d5e6-7890-abcd-ef0123456789", "name": "User prompt attack guardrail",
  "description": "Detects jailbreak attempts and indirect prompt injection via Azure Prompt Shield",
  "validatorType": "user_prompt_attacks",
  "validatorParameters": [],
  "action": { "$actionType": "block", "reason": "Adversarial input detected — execution blocked." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Llm"] }
}
```

### Example 5: Intellectual Property Detection — Block Copyrighted Text and Code

PostExecution only — no content exists to check before the LLM generates output. To check a file the agent produces instead of its text, see [files-guide.md § Recipe 3](files-guide.md#recipe-3--guard-a-file-the-agent-produces).

```json
{
  "$guardrailType": "builtInValidator", "id": "a2b3c4d5-e6f7-8901-bcde-f01234567890", "name": "IP detection guardrail",
  "description": "Detects copyrighted text and licensed GitHub code in LLM output",
  "validatorType": "intellectual_property",
  "validatorParameters": [{ "$parameterType": "enum-list", "id": "ipEntities", "value": ["Text", "Code"] }],
  "action": { "$actionType": "block", "reason": "Protected material detected in output — execution blocked." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Llm"] }
}
```

### Example 6: Block PII Inside Attached Files

`detectionScope: "Files"` evaluates attachments only and Agent PreExecution blocks before the model. Requires a `job-attachment` input; see [../../agent-definition.md](../../agent-definition.md) § File Attachments and [files-guide.md](files-guide.md).

```json
{
  "$guardrailType":"builtInValidator","id":"<UUID>","name":"PII in uploaded documents","description":"Blocks runs whose attached files contain customer identifiers","validatorType":"pii_detection",
  "validatorParameters":[{"$parameterType":"enum-list","id":"entities","value":["Email","CreditCardNumber"]},{"$parameterType":"enum","id":"detectionScope","value":"Files"}],
  "action":{"$actionType":"block","reason":"An attached file contains personal data."},"enabledForEvals":true,"selector":{"scopes":["Agent"]}
}
```

### Custom-rule, filter, and escalation examples

Custom word rules, filter redaction, and escalation examples are in [custom-rules-guide.md § Examples](custom-rules-guide.md#examples) and [escalation-guide.md](escalation-guide.md#example-escalate-pii-violations-to-action-center--multiple-tool-targets).

## agent.json with Guardrails

Put root `guardrails` alongside `settings`, `messages`, etc.:

```json
{
  "version":"1.1.0","settings":{"...":"..."},"inputSchema":{"...":"..."},"outputSchema":{"...":"..."},"metadata":{"...":"..."},"type":"lowCode",
  "guardrails":[{"$guardrailType":"builtInValidator","id":"<UUID>","name":"PII detection guardrail","description":"Detects PII","validatorType":"pii_detection","validatorParameters":[{"$parameterType":"enum-list","id":"entities","value":["Email","PhoneNumber"]},{"$parameterType":"map-enum","id":"entityThresholds","value":{"Email":0.5,"PhoneNumber":0.5}}],"action":{"$actionType":"block","reason":"PII detected"},"enabledForEvals":true,"selector":{"scopes":["Agent"]}}],
  "messages":["..."],"projectId":"<UUID>"
}
```

## What NOT to Do

Canonical discriminator, scope-casing, resource-policy, and UUID rules are in [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) § What NOT to Do. Also:

1. Use PascalCase PII names: `"Email"` not `"email_address"`, `"PhoneNumber"` not `"phone_number"`, `"USSocialSecurityNumber"` not `"us_ssn"`; never snake_case.
2. Do not use `prompt_injection` on Tool/Agent; it is Llm PreExecution only.
3. Do not use `user_prompt_attacks` on Tool/Agent; it is Llm PreExecution only.
4. Do not use `intellectual_property` on Tool; only Llm and Agent.
5. Do not use `intellectual_property` PreExecution; it is PostExecution only.
6. Do not omit `matchNames` when Tool is in `scopes`; list names explicitly ([matchNames — "All Tools" Behavior](#matchnames--all-tools-behavior)).
7. Do not use `filter` with built-ins; built-ins support only `block`, `log`, `escalate`.
8. `harmfulContentEntityThresholds` accepts only `0`, `2`, `4`, `6`; reject odd numbers and floats such as `3` or `2.5`.
9. Do not add a built-in without first running `uip agent guardrails list --output json` and confirming existence and `Status: "Available"`.
10. Do not use Action Center `Type: "VB Action"` or `Type: "Coded"`; only `Type: "Workflow Action"` can back a guardrail escalation. Always filter `uip solution resources list --kind App` results by this type.
11. Do not use `--kind Process` (`Type: "webApp"`) to find escalation apps; use `--kind App` with `Type: "Workflow Action"`.
12. Never put `"solution_folder"` in `app.folderName`; use literal `Folder` from `uip solution resources list --kind App` (for example `"Shared/Approvals"`), omit `app.folderId`, and do not use `FolderKey` in `app.*`. `uip agent refresh` translates `folderName` to `folderPath` in `bindings_v2.json`; `FolderKey` belongs in `debug_overwrites.json`.
13. Do not add a Tool guardrail before its tool exists. Run `uip agent tool list` first; every name must match `<AGENT_NAME>/resources/<ToolName>/resource.json`.
14. Do not skip escalation action-schema validation. Fetch the schema and verify required inputs (8), outputs (3), and outcomes (2) by name; if missing, report `<APP_NAME> does not have the required action schema configuration for tool guardrails.` and stop. See [escalation-guide.md § Adding an escalation guardrail](escalation-guide.md#adding-an-escalation-guardrail--step-by-step).
15. Do not use Agent/Llm on custom; custom is Tool only with exactly one `matchNames` tool. Create one custom guardrail per tool.
16. Do not auto-generate custom fallback for unavailable, unsupported, or unauthorized built-ins. Inform and stop; suggest custom only with explicit confirmation and only for Tool.
17. Do not create separate objects per scope; combine scopes, e.g. `"scopes": ["Agent", "Tool"]`.
18. Do not attempt OR inside one guardrail; all rules/fields combine with AND. For OR, create separate guardrails, one per condition branch.
19. Do not target unsupported tool types; allowed types are `agent`, `process`, `activity`, `builtInTool`, `ixpTool`, and Integration Service connector.
20. Do not omit `matchNames` for all tools; read `resources/`, list every resource, and if none exist do not add the guardrail.
21. Do not assume `Validator` is unique. Check `IsByo` and set `byoValidatorName` for a selected BYO entry.
22. Every `map-enum` threshold key must exactly match its entities list—no extra or missing keys. `uip agent validate` does not catch this; prune stale keys when editing entities.
23. Do not reverse-engineer schemas from CLI/SDK internals; use this reference and validation.
24. Do not add `detectionScope` when catalog `Parameters` lacks it, to custom, or to `byoValidatorName` guardrails; validate may pass, but the runtime ignores it and the guardrail checks text only. See [files-guide.md](files-guide.md).
25. Do not expect default `Text` to inspect attachments; use `Files` or `Both`.
26. Do not confuse `detectionScope` (`Text` / `Files` / `Both`, what a built-in reads) with `selector.scopes` (`Agent` / `Llm` / `Tool`, where it runs).

## References

- [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) — canonical low-code rules and guardrail anti-patterns
- [../../project-lifecycle.md](../../project-lifecycle.md) § `uip agent guardrails list` — validator discovery
- [../../agent-definition.md](../../agent-definition.md) § Guardrails — root placement
- [escalation-guide.md](escalation-guide.md) — escalation schema, verification, example
- [custom-rules-guide.md](custom-rules-guide.md) — custom schema and examples
- [files-guide.md](files-guide.md) — `detectionScope`, file coverage, recipes
- [../../agent-definition.md](../../agent-definition.md) § File Attachments — `job-attachment`
- [../built-in-tools/analyze-attachments.md](../built-in-tools/analyze-attachments.md) — Tool-scoped file guardrails
