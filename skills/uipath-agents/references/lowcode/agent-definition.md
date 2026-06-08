# Agent Definition Reference

Schemas for the core agent definition files: `agent.json`, `entry-points.json`, `project.uiproj`. Plus contentTokens construction, message templates, and Common Edits.

## Project Directory Structure

After `uip agent init <name>`:

```
<AgentName>/
├── agent.json              # Main agent configuration (edit this)
├── entry-points.json       # Entry point definition (must mirror agent.json schemas)
├── project.uiproj          # Project metadata
├── flow-layout.json        # UI layout — do not edit
├── evals/                  # Evaluation sets and evaluators
├── features/               # Agent features (memory spaces via uip agent memory)
└── resources/              # Agent resources
```

## agent.json

Primary configuration file. Edit directly.

```json
{
  "version": "1.1.0",
  "settings": {
    "model": "<MODEL_IDENTIFIER>",
    "maxTokens": 16384,
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

> **`guardrails`** — array of guardrail objects that inspect agent inputs/outputs for policy violations. See [capabilities/guardrails/guardrails.md](capabilities/guardrails/guardrails.md) for the full schema, validator reference, and examples.

### Settings

| Field | Description |
|-------|-------------|
| `model` | LLM identifier. Discover valid values with `uip agent model list` and select per [model-selection-guide.md](model-selection-guide.md) — **override the scaffold default `gpt-4o-2024-11-20`** (illustrative GA: `"anthropic.claude-sonnet-4-6"`, `"gpt-5.4"` — verify against the tenant). |
| `maxTokens` | Max output tokens. Must not exceed the chosen model's `MaxTokens` cap (from `uip agent model list`). |
| `temperature` | 0 = deterministic, higher = creative |
| `engine` | Use `"basic-v2"` |
| `maxIterations` | Max agent loop iterations. Default 25. |
| `mode` | Use `"standard"` |

> Prompt **quality** (system/user prompt structure, tool-call criteria, output contract) lives in [agent-prompting-guide.md](agent-prompting-guide.md). This file owns the **mechanics** (schema, `contentTokens` sync).

### Schema Types

| Type | Use For |
|------|---------|
| `"string"` | Text, JSON strings, formatted data |
| `"number"` | Numeric values with decimals |
| `"integer"` | Whole numbers |
| `"boolean"` | True/false flags |
| `"object"` | Nested structures |
| `"array"` | Lists |
| `$ref: "#/definitions/job-attachment"` | File attachments (input or output). See § File Attachments. |

### File Attachments (`job-attachment`)

To accept or return a file, declare the field as `$ref: "#/definitions/job-attachment"` and add the canonical `job-attachment` block to `inputSchema.definitions` (or `outputSchema.definitions`). Schema is fixed — copy verbatim. `x-uipath-resource-kind: "JobAttachment"` is required.

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

| Field | Required | Notes |
|---|---|---|
| `ID` | Yes | Orchestrator attachment key. Runtime injects this. |
| `FullName` | No | File name with extension. |
| `MimeType` | No | Drives multimodal handling in built-in tools. |
| `Metadata` | No | `Dictionary<string, string>`. |

`{{input.<file-field>}}` in a message template renders **metadata only** (ID, FullName, MimeType, Metadata). The agent does not see file contents from this token. To read contents, configure a file-handling built-in tool (e.g. `analyze-attachments`) — see [capabilities/built-in-tools/built-in-tools.md](capabilities/built-in-tools/built-in-tools.md).

Output side: declare an output field the same way; the agent emits a `job-attachment` describing a file it produced.

Runtime note: attachments cannot be supplied via `uip` CLI. Test from Studio Web or via Orchestrator job invocation.

### Top-level fields (do not modify)

| Field | Value |
|-------|-------|
| `version` | `"1.1.0"` — always scaffolded at this version |
| `type` | `"lowCode"` |
| `projectId` | Auto-generated UUID — do not edit |

### Metadata (do not modify)

| Field | Value |
|-------|-------|
| `storageVersion` | Managed by `uip agent refresh` — do not edit |
| `isConversational` | `false` (autonomous agents) |
| `showProjectCreationExperience` | `false` |
| `targetRuntime` | `"pythonAgent"` |

## Messages

This section covers message **structure** and `contentTokens` mechanics. For prompt **quality** — system-prompt skeleton, tool-call criteria, output contract, worked examples — see [agent-prompting-guide.md](agent-prompting-guide.md).

### System Message

Sets the agent's role and behavior. Typically plain text with no variables:

```json
{
  "role": "system",
  "content": "You are a classifier. Categorize the input and explain your reasoning.",
  "contentTokens": [
    { "type": "simpleText", "rawString": "You are a classifier. Categorize the input and explain your reasoning." }
  ]
}
```

### User Message

Templates input fields into the prompt using `{{input.fieldName}}`. For `job-attachment` fields the token renders metadata only (see § File Attachments).

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

## contentTokens Construction

Every message needs both `content` (string) and `contentTokens` (array). Keep them in sync.

**Rules:**
1. Text outside `{{ }}` → `{ "type": "simpleText", "rawString": "<text>" }`
2. Text inside `{{ }}` → `{ "type": "variable", "rawString": "input.fieldName" }` (strip delimiters)
3. Every segment including whitespace gets its own entry

**Example — adjacent variables:**

Content: `"{{input.field1}} {{input.field2}}"`

```json
"contentTokens": [
  { "type": "variable", "rawString": "input.field1" },
  { "type": "simpleText", "rawString": " " },
  { "type": "variable", "rawString": "input.field2" }
]
```

**Common mistakes:**
- Forgetting to update contentTokens after editing content
- Including `{{` or `}}` in the variable rawString
- Missing whitespace tokens between adjacent variables

## entry-points.json

Defines how the agent is invoked. Schemas must exactly mirror agent.json.

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

### Sync Rule

| agent.json | entry-points.json |
|-----------|-------------------|
| `inputSchema.properties.<field>` | `entryPoints[0].input.properties.<field>` |
| `inputSchema.required` | `entryPoints[0].input.required` |
| `outputSchema.properties.<field>` | `entryPoints[0].output.properties.<field>` |

Do not modify `filePath`, `uniqueId`, or `type`.

## project.uiproj

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

Features are defined as individual files in the agent project's `features/` directory. Today this is used for memory spaces. Do not hand-author memory feature files for routine changes; use `uip agent memory`.

```
Agent/
├── agent.json                              # No manually-authored memory features here
├── features/
│   └── {FeatureName}/
│       └── feature.json                    # Written by uip agent memory
```

The `memory` command updates `features/{FeatureName}/feature.json`. Run `uip agent refresh --output json`, then `uip agent validate --output json` after memory changes so generated bindings stay current.

For the full memory workflow and generated shape, see [capabilities/memory/memory.md](capabilities/memory/memory.md).

## Resources Convention (v1.1.0)

Resources are defined as individual files in the agent project's `resources/` directory — **not** inline in the root `agent.json`. Each resource gets its own subdirectory:

```
Agent/
├── agent.json                              # No resources field here
├── resources/
│   └── {ResourceName}/
│       └── resource.json                   # One file per resource
```

The `validate` command reads these files and resolves `referenceKey` for solution tools. The root `agent.json` should not contain a `resources` field.

### `folderPath` semantics

`folderPath` (or `channel.properties.folderName` for escalations / `action.app.folderName` for guardrail escalations) carries the literal `Folder` field returned by `uip solution resource list` — the same rule for both local (`Source: "Local"`) and external (`Source: "Remote"`) resources:

| `location` | `folderPath` value | Source |
|---|---|---|
| `"solution"` | Typically `"solution_folder"` (the in-solution declared folder) | `Folder` field from `uip solution resource list` |
| `"external"` | Literal Orchestrator folder, slash-separated (e.g., `"Shared/Sales"`) | `Folder` field from `uip solution resource list` |

The author writes the value verbatim into `resource.json` (or into the guardrail action under `agent.json`); `uip agent refresh` propagates it into `bindings_v2.json` as `folderPath` (App resources translate `folderName` → binding `folderPath`). Connection (Integration Service) resources are exempt — bound by `connection.id`, no `folderPath`. See [critical-rules.md](critical-rules.md) Rule 11 and [solution-resources.md](solution-resources.md) § Bindings.

For each resource type's full schema, see the relevant capability file:

- Tool resources (`$resourceType: "tool"`) — [capabilities/process/process.md](capabilities/process/process.md), [capabilities/integration-service/integration-service.md](capabilities/integration-service/integration-service.md)
- Context resources (`$resourceType: "context"`) — [capabilities/context/context.md](capabilities/context/context.md)
- Escalation resources (`$resourceType: "escalation"`) — [capabilities/escalation/escalation.md](capabilities/escalation/escalation.md)
- MCP server resources (`$resourceType: "mcp"`) — [capabilities/mcp/mcp.md](capabilities/mcp/mcp.md)

## Common Edits

### Change System Prompt

1. Edit `agent.json` → `messages[0].content`
2. Rebuild `messages[0].contentTokens` — single `simpleText` entry for prompts with no variables
3. Refresh: `uip agent refresh --output json`
4. Validate: `uip agent validate --output json`

### Change User Message Template

1. Edit `agent.json` → `messages[1].content`
2. Rebuild `messages[1].contentTokens` — tokenize `{{input.fieldName}}` as `variable`, surrounding text as `simpleText`
3. Refresh, then validate

### Add an Input Field

1. Add to `agent.json` → `inputSchema.properties` (and `.required` if mandatory)
2. Mirror in `entry-points.json` → `entryPoints[0].input.properties` (and `.required`)
3. Update `messages[1].content` and `contentTokens` if the field should appear in the user message
4. Refresh, then validate

### Add a File Input Field (`job-attachment`)

1. Add the field as `{ "$ref": "#/definitions/job-attachment" }` in `agent.json` → `inputSchema.properties`
2. Add the canonical `job-attachment` block to `inputSchema.definitions` (copy from § File Attachments — do not edit)
3. Mirror both in `entry-points.json` → `entryPoints[0].input.properties` and `.definitions`
4. Reference in the user message with `{{input.<fieldName>}}` if the agent should see file metadata
5. To let the agent **read contents**, add a file-handling built-in tool — see [capabilities/built-in-tools/built-in-tools.md](capabilities/built-in-tools/built-in-tools.md)
6. Refresh, then validate

### Add an Output Field

1. Add to `agent.json` → `outputSchema.properties`
2. Mirror in `entry-points.json` → `entryPoints[0].output.properties`
3. Refresh, then validate

### Add a File Output Field (`job-attachment`)

1. Add the field as `{ "$ref": "#/definitions/job-attachment" }` in `agent.json` → `outputSchema.properties`
2. Add the canonical `job-attachment` block to `outputSchema.definitions`
3. Mirror both in `entry-points.json` → `entryPoints[0].output.properties` and `.definitions`
4. Refresh, then validate

### Change Model Settings

1. Edit `agent.json` → `settings.model`, `.temperature`, `.maxTokens`, or `.maxIterations`
2. Discover valid model identifiers with `uip agent model list` and select per [model-selection-guide.md](model-selection-guide.md) — the tenant is the source of truth (availability and GA/preview status vary per tenant). Keep `maxTokens` ≤ the model's `MaxTokens` cap.
3. Refresh, then validate

### Capability-Adding Edits

For edits that add a new tool, context, or escalation, see the capability registry in [lowcode.md](lowcode.md).

## Auto-Generated Files (do not edit)

| File | Managed By |
|------|------------|
| `flow-layout.json` | Studio Web |
| `entry-points.json`, `bindings_v2.json` | Regenerated by `uip agent refresh` and Studio Web — do not edit by hand |
