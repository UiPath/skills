# Agent Definition Reference

Schemas for `agent.json`, `entry-points.json`, and `project.uiproj`, plus `contentTokens`, message templates, resources, features, and common edits.

## Project Structure

After `uip agent init <name>`:

```text
<AgentName>/
├── agent.json              # Main agent configuration (edit this)
├── entry-points.json       # Entry point definition (must mirror agent.json schemas)
├── project.uiproj          # Project metadata
├── flow-layout.json        # UI layout — do not edit
├── evals/                  # Evaluation sets and evaluators
├── features/               # Agent features (memory spaces via uip agent memory)
└── resources/              # Agent resources
```

## `agent.json`

### Autonomous scaffold

```json
{
  "version": "1.1.0",
  "settings": {
    "model": "<MODEL_IDENTIFIER>",
    "maxTokens": 128000,
    "temperature": 0,
    "engine": "basic-v2",
    "maxIterations": 25,
    "mode": "standard"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "<FIELD_NAME>": {
        "type": "string",
        "description": "<FIELD_DESCRIPTION>"
      }
    },
    "required": ["<FIELD_NAME>"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "<FIELD_NAME>": {
        "type": "string",
        "description": "<FIELD_DESCRIPTION>"
      }
    }
  },
  "metadata": {
    "storageVersion": "50.0.0",
    "isConversational": false,
    "showProjectCreationExperience": false,
    "targetRuntime": "pythonAgent"
  },
  "type": "lowCode",
  "messages": [
    {
      "role": "system",
      "content": "<SYSTEM_PROMPT>",
      "contentTokens": [
        { "type": "simpleText", "rawString": "<SYSTEM_PROMPT>" }
      ]
    },
    {
      "role": "user",
      "content": "{{input.fieldName}}",
      "contentTokens": [
        { "type": "variable", "rawString": "input.fieldName" }
      ]
    }
  ],
  "guardrails": [],
  "projectId": "<AUTO_GENERATED_UUID>"
}
```

### Conversational scaffold

```json
{
  "version": "1.1.0",
  "settings": {
    "model": "<MODEL_IDENTIFIER>",
    "maxTokens": 64000,
    "temperature": 0,
    "engine": "conversational-v1",
    "mode": "standard"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "<FIELD_NAME>": {
        "type": "string",
        "description": "<FIELD_DESCRIPTION>"
      }
    },
    "required": ["<FIELD_NAME>"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {}
  },
  "metadata": {
    "storageVersion": "50.0.0",
    "isConversational": true,
    "showProjectCreationExperience": false,
    "targetRuntime": "pythonAgent"
  },
  "type": "lowCode",
  "messages": [
    {
      "role": "system",
      "content": "<SYSTEM_PROMPT>",
      "contentTokens": [
        { "type": "simpleText", "rawString": "<SYSTEM_PROMPT>" }
      ]
    },
    {
      "role": "user",
      "content": "",
      "contentTokens": []
    }
  ],
  "projectId": "<AUTO_GENERATED_UUID>"
}
```

`guardrails` is an array of guardrail objects that inspect agent inputs/outputs for policy violations. See [capabilities/guardrails/guardrails.md](capabilities/guardrails/guardrails.md) for the full schema, validator reference, and examples.

### Settings and fixed fields

| Field | Rule |
|---|---|
| `model` | Discover valid values with `uip agent model list`; select per [model-selection-guide.md](model-selection-guide.md). Override the scaffold default. Illustrative GA values include `"anthropic.claude-sonnet-4-6"` and `"gpt-5.4"`; verify against the tenant. |
| `maxTokens` | Do not exceed the selected model’s `MaxTokens` cap from `uip agent model list`. |
| `temperature` | `0` is deterministic; higher values are more creative. |
| `engine` | Use `"basic-v2"` for autonomous and `"conversational-v1"` for conversational. |
| `maxIterations` | Maximum autonomous loop iterations; default `25`. Omit for conversational. |
| `mode` | Use `"standard"`. |
| `version` | `"1.1.0"` — always scaffolded at this version. |
| `type` | `"lowCode"`. |
| `projectId` | Auto-generated UUID — do not edit. |
| `storageVersion` | Managed by `uip agent refresh` — do not edit. |
| `isConversational` | `false` for autonomous and `true` for conversational — do not edit. |
| `showProjectCreationExperience` | `false`. |
| `targetRuntime` | `"pythonAgent"` for autonomous; **`null` for conversational** because conversational agents are not yet in PROD and the runtime value is not finalized. |

Prompt quality belongs in [prompting/agent-prompting-guide.md](prompting/agent-prompting-guide.md); this file owns schema and `contentTokens` mechanics.

### Schemas

Use `"string"`, `"number"`, `"integer"`, `"boolean"`, `"object"`, and `"array"` for corresponding values. Use `$ref: "#/definitions/job-attachment"` for file attachments.

For autonomous agents, `inputSchema` defines fields available to system and user templates, and `outputSchema` defines agent outputs.

For conversational agents, each run is one exchange: the runtime supplies reserved implicit **`messages`**, containing conversation history and the latest user message. Never declare `messages`, conversation-history fields, or fields representing the user input message in `inputSchema`, per [critical-rules/conversational-critical-rules.md](critical-rules/conversational-critical-rules.md) anti-pattern 4. Declare custom input fields only for genuine per-exchange context variables. Leave `inputSchema` blank otherwise. Leave conversational `outputSchema` empty and do not modify it, per anti-pattern 1 in that reference.

### File Attachments (`job-attachment`)

For an input or output file, declare `$ref: "#/definitions/job-attachment"` and add this fixed block verbatim to `inputSchema.definitions` or `outputSchema.definitions`; `x-uipath-resource-kind: "JobAttachment"` is required.

```jsonc
{
  "inputSchema": {
    "type": "object",
    "properties": {
      "fileIn": { "$ref": "#/definitions/job-attachment" }
    },
    "definitions": {
      "job-attachment": {
        "type": "object",
        "properties": {
          "ID":       { "type": "string", "description": "Orchestrator attachment key" },
          "FullName": { "type": "string", "description": "File name" },
          "MimeType": { "type": "string", "description": "MIME type, e.g. \"application/pdf\", \"image/png\"" },
          "Metadata": {
            "type": "object",
            "description": "Dictionary<string, string> of metadata",
            "additionalProperties": { "type": "string" }
          }
        },
        "required": ["ID"],
        "x-uipath-resource-kind": "JobAttachment"
      }
    }
  }
}
```

| Field | Required | Rule |
|---|---|---|
| `ID` | Yes | Orchestrator attachment key; runtime injects it. |
| `FullName` | No | File name with extension. |
| `MimeType` | No | Drives multimodal handling in built-in tools. |
| `Metadata` | No | `Dictionary<string, string>`. |

`{{input.<file-field>}}` renders metadata only (`ID`, `FullName`, `MimeType`, `Metadata`); it does not expose file contents. Configure a file-handling built-in tool such as `analyze-attachments` to read contents; see [capabilities/built-in-tools/built-in-tools.md](capabilities/built-in-tools/built-in-tools.md). For output, declare the same reference and emit a `job-attachment` describing the produced file. Attachments cannot be supplied via `uip` CLI; test from Studio Web or via Orchestrator job invocation.

## Messages and `contentTokens`

Use [prompting/agent-prompting-guide.md](prompting/agent-prompting-guide.md) for system-prompt structure, tool-call criteria, output contracts, and examples.

Every message requires synchronized `content` and `contentTokens`. Token types are `simpleText`, `variable`, and `expression`:

1. Text outside `{{ }}` and `@{ }` becomes `{ "type": "simpleText", "rawString": "<text>" }`.
2. Text inside `{{ }}` becomes `{ "type": "variable", "rawString": "input.fieldName" }`; strip delimiters and reference only `inputSchema` fields.
3. Text inside `@{ }` becomes `{ "type": "expression", "rawString": "<expr>" }`; strip delimiters and preserve the inner text verbatim.
4. Give every segment, including whitespace, its own entry.

`@{ }` targets runtime resources or outputs by family and name: `tools.<Name>`, `contexts.<Name>`, `escalations.<Name>`, or `output.<path>`. Never declare these targets under `inputSchema.properties`.

A variable-free prompt has one `simpleText` token. Autonomous user messages template input fields with `{{input.fieldName}}` and resources/outputs with `@{ }` expressions. Conversational agents must leave the user message blank after initialization; runtime conversation messages replace it.

Example:

```json
{
  "role": "user",
  "content": "Document: {{input.documentText}} Category options: {{input.categories}}",
  "contentTokens": [
    { "type": "simpleText", "rawString": "Document: " },
    { "type": "variable", "rawString": "input.documentText" },
    { "type": "simpleText", "rawString": " Category options: " },
    { "type": "variable", "rawString": "input.categories" }
  ]
}
```

Adjacent variables such as `"{{input.field1}} {{input.field2}}"` require a separate `simpleText` whitespace token. Do not leave `contentTokens` stale, include delimiters in `rawString`, or omit whitespace tokens.

## `entry-points.json`

Schemas must mirror `agent.json`:

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    {
      "filePath": "/content/agent.json",
      "uniqueId": "<AUTO_GENERATED_UUID>",
      "type": "agent",
      "input": {
        "type": "object",
        "properties": { },
        "required": []
      },
      "output": {
        "type": "object",
        "properties": { }
      }
    }
  ]
}
```

Mirror `agent.json` `inputSchema.properties.<field>` and `.required` in `entryPoints[0].input`, and `outputSchema.properties.<field>` in `entryPoints[0].output`. Do not modify `filePath`, `uniqueId`, or `type`.

## `project.uiproj`

```json
{
  "ProjectType": "Agent",
  "Name": "<AGENT_NAME>",
  "Description": null,
  "MainFile": null
}
```

Only `Name` and `Description` are editable. `ProjectType` and `MainFile` are fixed.

## Features Convention (v1.1.0)

Features are individual files under `features/`; currently this means memory spaces. Do not hand-author routine memory feature files; run `uip agent memory`.

```text
Agent/
├── agent.json
└── features/
    └── {FeatureName}/
        └── feature.json
```

The memory command writes `features/{FeatureName}/feature.json`. Run `uip agent refresh --output json`, then run `uip agent validate --output json` after memory changes. See [capabilities/memory/memory.md](capabilities/memory/memory.md).

## Resources Convention (v1.1.0)

Resources are separate files under `resources/`, not inline in root `agent.json`; do not add a root `resources` field.

```text
Agent/
├── agent.json
└── resources/
    └── {ResourceName}/
        └── resource.json
```

Validation reads these files and resolves `referenceKey` for solution tools. `folderPath` (or `channel.properties.folderName` for escalations, or `action.app.folderName` for guardrail escalations) must contain the literal `Folder` from `uip solution resources list`, for both local (`Source: "Local"`) and external (`Source: "Remote"`) resources:

| `location` | `folderPath` value | Source |
|---|---|---|
| `"solution"` | Typically `"solution_folder"` (the in-solution declared folder) | `Folder` field from `uip solution resources list` |
| `"external"` | Literal slash-separated Orchestrator folder, such as `"Shared/Sales"` | `Folder` field from `uip solution resources list` |

Write the value verbatim into `resource.json` or the guardrail action. `uip agent refresh` propagates it to `bindings_v2.json`; App resources translate `folderName` to binding `folderPath`. Connection (Integration Service) resources are exempt and bind by `connection.id`. See [critical-rules/critical-rules.md](critical-rules/critical-rules.md) Rule 11 and [solution-resources.md](solution-resources.md) § Bindings.

Resource schemas:

- Tool: `$resourceType: "tool"` — [capabilities/process/process.md](capabilities/process/process.md), [capabilities/integration-service/integration-service.md](capabilities/integration-service/integration-service.md)
- Context: `$resourceType: "context"` — [capabilities/context/context.md](capabilities/context/context.md)
- Escalation: `$resourceType: "escalation"` — [capabilities/escalation/escalation.md](capabilities/escalation/escalation.md)
- MCP server: `$resourceType: "mcp"` — [capabilities/mcp/mcp.md](capabilities/mcp/mcp.md)

## Common Edits

For every edit that changes schemas, messages, resources, or memory, run `uip agent refresh --output json`, then run `uip agent validate --output json` unless a step below specifies the sequence explicitly.

### Change System Prompt

1. Edit `agent.json` → `messages[0].content`.
2. Rebuild `messages[0].contentTokens`; use one `simpleText` entry when there are no variables.
3. Run `uip agent refresh --output json`.
4. Run `uip agent validate --output json`.

### Change User Message Template

1. Edit `agent.json` → `messages[1].content`.
2. Rebuild `messages[1].contentTokens`, tokenizing `{{input.fieldName}}` as `variable` and surrounding text as `simpleText`.
3. Run `uip agent refresh --output json`, then run `uip agent validate --output json`.

### Add an Input Field

1. Add the field to `agent.json` → `inputSchema.properties` and to `.required` when mandatory.
2. Mirror it in `entry-points.json` → `entryPoints[0].input.properties` and `.required`.
3. Update `messages[1].content` and `contentTokens` when the field belongs in the user message.
4. Run `uip agent refresh --output json`, then run `uip agent validate --output json`.

### Add a File Input Field (`job-attachment`)

1. Add `{ "$ref": "#/definitions/job-attachment" }` to `agent.json` → `inputSchema.properties`.
2. Add the canonical `job-attachment` block from § File Attachments to `inputSchema.definitions`; do not edit it.
3. Mirror both in `entry-points.json` → `entryPoints[0].input.properties` and `.definitions`.
4. Reference it with `{{input.<fieldName>}}` when the agent should see file metadata.
5. Add a file-handling built-in tool to let the agent read contents; see [capabilities/built-in-tools/built-in-tools.md](capabilities/built-in-tools/built-in-tools.md).
6. Run `uip agent refresh --output json`, then run `uip agent validate --output json`.

### Add an Output Field

1. Add it to `agent.json` → `outputSchema.properties`.
2. Mirror it in `entry-points.json` → `entryPoints[0].output.properties`.
3. Run `uip agent refresh --output json`, then run `uip agent validate --output json`.

### Add a File Output Field (`job-attachment`)

1. Add `{ "$ref": "#/definitions/job-attachment" }` to `agent.json` → `outputSchema.properties`.
2. Add the canonical `job-attachment` block from § File Attachments to `outputSchema.definitions`.
3. Mirror both in `entry-points.json` → `entryPoints[0].output.properties` and `.definitions`.
4. Run `uip agent refresh --output json`, then run `uip agent validate --output json`.

### Change Model Settings

1. Edit `agent.json` → `settings.model`, `.temperature`, `.maxTokens`, or `.maxIterations`.
2. Discover valid identifiers with `uip agent model list`; select per [model-selection-guide.md](model-selection-guide.md), because tenant availability and GA/preview status vary. Keep `maxTokens` ≤ the model’s `MaxTokens` cap.
3. Run `uip agent refresh --output json`, then run `uip agent validate --output json`.

### Capability-Adding Edits

For a new tool, context, or escalation, see the capability registry in [lowcode.md](lowcode.md).

## Auto-Generated Files

| File | Managed by |
|---|---|
| `flow-layout.json` | Studio Web |
| `entry-points.json`, `bindings_v2.json` | Regenerated by `uip agent refresh` and Studio Web — do not edit by hand |
