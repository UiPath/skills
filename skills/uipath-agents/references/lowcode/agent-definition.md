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
├── features/               # Agent features
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
| `model` | LLM identifier (e.g., `"anthropic.claude-sonnet-4-6"`, `"gpt-4.1-2025-04-14"`) |
| `maxTokens` | Max output tokens. Common: 16384, 32768. |
| `temperature` | 0 = deterministic, higher = creative |
| `engine` | Use `"basic-v2"` |
| `maxIterations` | Max agent loop iterations. Default 25. |
| `mode` | Use `"standard"` |

### Schema Types

| Type | Use For |
|------|---------|
| `"string"` | Text, JSON strings, formatted data |
| `"number"` | Numeric values with decimals |
| `"integer"` | Whole numbers |
| `"boolean"` | True/false flags |
| `"object"` | Nested structures |
| `"array"` | Lists |

### Top-level fields (do not modify)

| Field | Value |
|-------|-------|
| `version` | `"1.1.0"` — always scaffolded at this version |
| `type` | `"lowCode"` |
| `projectId` | Auto-generated UUID — do not edit |

### Metadata (do not modify)

| Field | Value |
|-------|-------|
| `storageVersion` | Managed by `uip agent validate` — do not edit |
| `isConversational` | `false` (autonomous agents) |
| `showProjectCreationExperience` | `false` |
| `targetRuntime` | `"pythonAgent"` |

## Messages

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

Templates input fields into the prompt using `{{input.fieldName}}`:

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

## Resources Convention (v1.1.0)

Resources are defined as individual files in the agent project's `resources/` directory — **not** inline in the root `agent.json`. Each resource gets its own subdirectory:

```
Agent/
├── agent.json                              # No resources field here
├── resources/
│   └── {ResourceName}/
│       └── resource.json                   # One file per resource
```

The `validate` command reads these files, resolves `referenceKey` for solution tools, and generates `.agent-builder/agent.json` which inlines all resources. The root `agent.json` should not contain a `resources` field.

### `folderPath` semantics by `location`

`folderPath` (or `channel.properties.folderPath` for escalations) carries a different value depending on whether the resource is solution-internal or external:

| `location` | `folderPath` value | Source |
|---|---|---|
| `"solution"` | `"solution_folder"` | Placeholder; resolved at deploy time |
| `"external"` | Literal Orchestrator folder, slash-separated (e.g., `"Shared/Sales"`) | `Folder` field from `uip solution resource list` |

The author writes the value into `resource.json`; `uip agent validate` propagates it verbatim into `bindings_v2.json`. Connection (Integration Service) resources are exempt — bound by `connection.id`, no `folderPath`. See [critical-rules.md](critical-rules.md) Rule 11 and [solution-resources.md](solution-resources.md) § Bindings.

For each resource type's full schema, see the relevant capability file:

- Tool resources (`$resourceType: "tool"`) — [capabilities/process/external.md](capabilities/process/external.md), [capabilities/process/solution-agent.md](capabilities/process/solution-agent.md), [capabilities/integration-service/integration-service.md](capabilities/integration-service/integration-service.md)
- Context resources (`$resourceType: "context"`) — [capabilities/context/context.md](capabilities/context/context.md)
- Escalation resources (`$resourceType: "escalation"`) — [capabilities/escalation/escalation.md](capabilities/escalation/escalation.md)

## Common Edits

### Change System Prompt

1. Edit `agent.json` → `messages[0].content`
2. Rebuild `messages[0].contentTokens` — single `simpleText` entry for prompts with no variables
3. Validate: `uip agent validate --output json`

### Change User Message Template

1. Edit `agent.json` → `messages[1].content`
2. Rebuild `messages[1].contentTokens` — tokenize `{{input.fieldName}}` as `variable`, surrounding text as `simpleText`
3. Validate

### Add an Input Field

1. Add to `agent.json` → `inputSchema.properties` (and `.required` if mandatory)
2. Mirror in `entry-points.json` → `entryPoints[0].input.properties` (and `.required`)
3. Update `messages[1].content` and `contentTokens` if the field should appear in the user message
4. Validate

### Add an Output Field

1. Add to `agent.json` → `outputSchema.properties`
2. Mirror in `entry-points.json` → `entryPoints[0].output.properties`
3. Validate

### Change Model Settings

1. Edit `agent.json` → `settings.model`, `.temperature`, `.maxTokens`, or `.maxIterations`
2. Current models: `anthropic.claude-sonnet-4-6`, `gpt-4.1-2025-04-14`, `gpt-5.2-2025-12-11`
3. Validate

### Capability-Adding Edits

For edits that add a new tool, context, or escalation, see the capability registry in [lowcode.md](lowcode.md).

## Auto-Generated Files (do not edit)

| File | Managed By |
|------|------------|
| `flow-layout.json` | Studio Web |
| `.agent-builder/*` | Generated by `uip agent validate` and Studio Web — do not edit by hand |
