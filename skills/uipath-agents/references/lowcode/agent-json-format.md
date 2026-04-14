# Agent JSON Format Reference

Schemas for the core agent definition files.

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
  "projectId": "<AUTO_GENERATED_UUID>"
}
```

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

## Resources (v1.1.0)

Resources are defined as individual files in the agent project's `resources/` directory — **not** inline in the root `agent.json`. Each resource gets its own subdirectory:

```
Agent/
├── agent.json                              # No resources field here
├── resources/
│   └── {ResourceName}/
│       └── resource.json                   # One file per resource
```

The `validate` command reads these files, resolves `referenceKey` for solution tools, and generates `.agent-builder/agent.json` which inlines all resources. The root `agent.json` should not contain a `resources` field.

### Tool resource (`$resourceType: "tool"`)

**Path:** `resources/{ToolName}/resource.json`

```jsonc
{
  "$resourceType": "tool",
  "name": "MyProcess",
  "description": "What this tool does (shown to LLM for tool selection)",
  "location": "external",      // "external" | "solution"
  "type": "process",           // See type table below
  "inputSchema": {
    "type": "object",
    "properties": { "param1": { "type": "string" } },
    "required": ["param1"]
  },
  "outputSchema": {
    "type": "object",
    "properties": { "result": { "type": "string" } }
  },
  "settings": {},
  "properties": {
    "processName": "MyProcess",
    "folderPath": "Shared"      // "solution_folder" for solution-internal; actual path for external
  },
  "guardrail": {
    "policies": []
  },
  "id": "<uuid>",              // Stable; generate once, never change
  "referenceKey": "",           // Leave empty; validate resolves it and writes it back to disk
  "isEnabled": true,
  "argumentProperties": {}
}
```

**`type` values:**

| Value | Use when |
|-------|----------|
| `process` | Calling an RPA process (XAML workflow) in Orchestrator |
| `agent` | Calling another low-code agent |
| `integration` | Calling an Integration Service connector activity |
| `api` | Direct REST API call |

Note: MCP (Model Context Protocol) server resources use `$resourceType: "mcp"` — a separate resource type, not a `type` value inside a tool resource. See [MCP resource](#mcp-resource-resourcetype-mcp) below.

**`location` and `folderPath`:**

| `location` | `folderPath` | Meaning |
|------------|-------------|---------|
| `"solution"` | `"solution_folder"` | Resource is another project within this same solution |
| `"external"` | `"Shared"` (or actual path) | Resource lives in Orchestrator, outside this solution |

### Context resource (`$resourceType: "context"`)

**Path:** `resources/{ContextName}/resource.json`

```jsonc
{
  "$resourceType": "context",
  "contextType": "index",       // "index" | "attachments" | "dataFabricEntitySet"
  "indexName": "MyIndex",
  "folderPath": "solution_folder",
  "settings": {
    "query": { "variant": "dynamic" },
    "retrievalMode": "semantic", // "semantic" | "structured" | "deepRAG" | "batchTransform"
    "resultCount": 3,
    "threshold": 0,
    "fileExtension": "All"
  }
}
```

### Escalation resource (`$resourceType: "escalation"`)

**Path:** `resources/{EscalationName}/resource.json`

```jsonc
{
  "$resourceType": "escalation",
  "id": "<uuid>",
  "name": "Human Review",
  "description": "Escalate to a human reviewer when uncertain",
  "isEnabled": true,
  "channels": [
    {
      "name": "ActionCenter",
      "type": "ActionCenter",
      "inputSchema": { ... },
      "properties": { ... }
    }
  ]
}
```

### MCP resource (`$resourceType: "mcp"`)

**Path:** `resources/{McpServerName}/resource.json`

MCP resources are a distinct resource type — they use `$resourceType: "mcp"`, not `$resourceType: "tool"`.

```jsonc
{
  "$resourceType": "mcp",
  "id": "<uuid>",
  "name": "MyMcpServer",
  "description": "What this MCP server provides",
  "isEnabled": true,
  "tools": []  // MCP tool definitions — populated at runtime
}
```

### v1.1.0 agent.json template

The root `agent.json` does not contain a `resources` field. Resources are defined as separate files in the `resources/` directory.

```jsonc
{
  "version": "1.1.0",
  "type": "lowCode",
  "projectId": "<uuid>",
  "settings": {
    "model": "anthropic.claude-sonnet-4-6",
    "maxTokens": 16384,
    "temperature": 0,
    "engine": "basic-v2",
    "maxIterations": 25,
    "mode": "standard"
  },
  "metadata": {
    "storageVersion": "50.0.0",
    "isConversational": false,
    "targetRuntime": "pythonAgent",
    "showProjectCreationExperience": false
  },
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant.",
      "contentTokens": [
        { "type": "simpleText", "rawString": "You are a helpful assistant." }
      ]
    },
    {
      "role": "user",
      "content": "{{input.userInput}}",
      "contentTokens": [
        { "type": "variable", "rawString": "input.userInput" }
      ]
    }
  ],
  "inputSchema": {
    "type": "object",
    "required": ["userInput"],
    "properties": {
      "userInput": { "type": "string", "description": "User input" }
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "content": { "type": "string", "description": "Agent response" }
    }
  }
}
```

### Example: resource.json for a solution agent tool

**Path:** `ParentAgent/resources/ToolAgent/resource.json`

```jsonc
{
  "$resourceType": "tool",
  "name": "ToolAgent",
  "description": "Calls ToolAgent for specialized tasks",
  "location": "solution",
  "type": "agent",
  "inputSchema": {
    "type": "object",
    "properties": {
      "userInput": { "type": "string", "description": "Input for the tool agent" }
    }
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "content": { "type": "string", "description": "Output content" }
    }
  },
  "settings": {},
  "properties": {
    "processName": "ToolAgent",
    "folderPath": "solution_folder"
  },
  "guardrail": {
    "policies": []
  },
  "id": "<uuid>",
  "referenceKey": "",           // Leave empty; validate resolves it and writes it back to disk
  "isEnabled": true,
  "argumentProperties": {}
}
```

## Auto-Generated Files (do not edit)

| File | Managed By |
|------|------------|
| `flow-layout.json` | Studio Web |
| `.agent-builder/*` | Generated by `uip agent validate` and Studio Web — do not edit by hand |
