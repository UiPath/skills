# `agent.json` File Format Reference

> **Agent type: Low-code agents only.** Coded agents define their schema in Python (`Input`/`Output` Pydantic models or `StartEvent`/`StopEvent` subclasses) — see the framework guides in [references/frameworks/](../frameworks/).
>
> **Audience:** AI coding assistants (e.g., Claude Code) that create or edit UiPath low-code agent definition files.
> **Source of truth:** Real `agent.json` files from UiPath Studio projects.

---

## Overview

`agent.json` is the declarative definition file for a UiPath low-code agent. It describes:

- The agent's identity and version metadata
- The LLM prompt (system + user messages, with optional variable interpolation)
- Input and output data schemas
- LLM model settings and runtime engine
- Resources the agent can use (tools, context sources, HITL escalations, MCP servers, other agents)
- Guardrails (content moderation, PII detection, injection prevention)

Every agent project has exactly one `agent.json` at its root.

---

## Top-Level Structure

```json
{
  "id": "<uuid>",
  "version": "1.1.0",
  "name": "My Agent",
  "metadata": { ... },
  "messages": [ ... ],
  "inputSchema": { ... },
  "outputSchema": { ... },
  "settings": { ... },
  "resources": [ ... ],
  "features": [],
  "guardrails": [ ... ]
}
```

### Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` (UUID) | No | Stable unique identifier for the agent. Omit when creating new files; UiPath Studio assigns it. |
| `version` | `string` | **Yes** | Schema version. Use `"1.1.0"` for all new agents. `"1.0.0"` is a legacy schema used by older Studio projects. |
| `name` | `string` | Recommended | Human-readable display name shown in Studio Web and traces. Defaults to the project folder name if omitted. |
| `metadata` | `object` | **Yes** | Runtime and storage metadata (see [Metadata](#metadata)). |
| `messages` | `array` | **Yes** | Exactly two prompt messages: one `system` and one `user` (see [Messages](#messages)). |
| `inputSchema` | `object` | **Yes** | JSON Schema describing the agent's input variables (see [Schemas](#inputschema-and-outputschema)). |
| `outputSchema` | `object` | **Yes** | JSON Schema describing the agent's output variables (see [Schemas](#inputschema-and-outputschema)). |
| `settings` | `object` | **Yes** | LLM model and runtime engine configuration (see [Settings](#settings)). |
| `resources` | `array` | No | Tools, context sources, escalations, and integrations available to the agent (see [Resources](#resources)). Omit or use `[]` when none. |
| `features` | `array` | No | Feature flags. Currently always `[]`; include it for forward compatibility. |
| `guardrails` | `array` | No | Content moderation and safety policies (see [Guardrails](#guardrails)). Omit or use `[]` when none. |

---

## Metadata

```json
"metadata": {
  "storageVersion": "44.0.0",
  "isConversational": false
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `storageVersion` | `string` | **Yes** | Internal storage format version used by UiPath Studio. Use `"44.0.0"` for current Studio Web projects (older projects may use `"31.0.0"`). |
| `isConversational` | `boolean` | **Yes** | `true` for conversational agents (multi-turn dialogue); `false` for single-turn / task agents. Must be consistent with `settings.engine`. |
| `targetRuntime` | `string` | No | Set to `"pythonAgent"` by Studio Web. Optional for hand-crafted files. |
| `showProjectCreationExperience` | `boolean` | No | Studio Web UI hint. Optional; omit for hand-crafted files. |

---

## Messages

The `messages` array must contain **exactly two** entries, in this order:

1. A **system** message — sets the agent's persona, role, and global instructions.
2. A **user** message — the task prompt sent at runtime, typically containing variable references.

### Message Object Structure

```json
{
  "role": "system" | "user",
  "content": "Plain text with optional {{variable}} placeholders",
  "contentTokens": [ ... ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `role` | `string` | **Yes** | `"system"` or `"user"`. |
| `content` | `string` | **Yes** | The prompt text. May use `{{variableName}}` legacy interpolation syntax for input variables. |
| `contentTokens` | `array` | No | Structured token representation of `content`. Required by Studio; always include it when creating files programmatically (see [Content Tokens](#content-tokens)). |

### Content Tokens

`contentTokens` breaks the `content` string into typed segments. Studio uses this for visual editing; it must stay in sync with `content`.

#### Token Types

| `type` | Description | Key field |
|---|---|---|
| `simpleText` | A literal text segment. | `rawString` — the literal text. |
| `variable` | A reference to an input variable. | `rawString` — `"input.<variableName>"`. |
| `expression` | A computed expression. | `rawString` — the expression source. |

#### Example — User message with three input variables

```json
{
  "role": "user",
  "content": "Calculate: {{a}} {{operator}} {{b}}",
  "contentTokens": [
    { "type": "simpleText",  "rawString": "Calculate: " },
    { "type": "variable",    "rawString": "input.a" },
    { "type": "simpleText",  "rawString": " " },
    { "type": "variable",    "rawString": "input.operator" },
    { "type": "simpleText",  "rawString": " " },
    { "type": "variable",    "rawString": "input.b" }
  ]
}
```

> **Rule:** Every `{{variableName}}` in `content` must map to a `variable` token with `rawString: "input.<variableName>"`. Surrounding literal text becomes `simpleText` tokens. The concatenation of all `rawString` values (substituting variable names with their `{{}}` form) must reproduce `content` exactly.

> **Studio Web convention:** Studio Web appends an empty trailing `{"type": "simpleText", "rawString": ""}` token to messages containing variables. This is harmless — include or omit it freely.

---

## `inputSchema` and `outputSchema`

Both fields follow [JSON Schema draft-07](https://json-schema.org/draft-07/json-schema-release-notes.html) with `type: "object"` at the root.

```json
"inputSchema": {
  "type": "object",
  "properties": {
    "a":        { "type": "number" },
    "b":        { "type": "number" },
    "operator": { "type": "string" }
  },
  "required": ["a", "b", "operator"]
},
"outputSchema": {
  "type": "object",
  "properties": {
    "result": { "type": "number" }
  }
}
```

### Supported JSON Schema Property Types

| JSON Schema type | Use for |
|---|---|
| `"string"` | Text values |
| `"number"` | Integers and floats |
| `"boolean"` | True/false flags |
| `"array"` | Lists (add `"items": { ... }` to define element type) |
| `"object"` | Nested structures (add nested `"properties"`) |

### Rules

- Always set `"type": "object"` at the root level of both schemas.
- List all mandatory input variables in `"required"`.
- `outputSchema` rarely needs `"required"` — the LLM may not always produce every field.
- Variables declared in `inputSchema.properties` are what you reference as `{{variableName}}` in `messages[].content`.

---

## Settings

```json
"settings": {
  "model":         "gpt-4.1-2025-04-14",
  "maxTokens":     16384,
  "temperature":   0,
  "engine":        "basic-v2",
  "maxIterations": 25
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `model` | `string` | **Yes** | The LLM model identifier (see [Supported Models](#supported-models)). |
| `maxTokens` | `integer` | **Yes** | Maximum tokens for the LLM response. Typical values: `4096`, `8192`, `16384`, `32768`. |
| `temperature` | `number` | **Yes** | Sampling temperature. Range `0`–`1`. Use `0` for deterministic/task agents; `0.7`–`1` for creative/conversational agents. |
| `engine` | `string` | **Yes** | Agent runtime engine (see [Engine Values](#engine-values)). |
| `maxIterations` | `integer` | No | Maximum tool-call iterations before the agent stops. Default: `25`. Increase only for complex multi-step workflows. |
| `byomProperties` | `object` | No | Bring-Your-Own-Model properties for custom model endpoints (see [BYOM](#byom-properties)). |

### Engine Values

| Value | Description |
|---|---|
| `"basic-v2"` | Standard single-turn agent. Use for most non-conversational agents. (**Preferred**) |
| `"basic-v1"` | Legacy single-turn engine. Use only when targeting older deployments. |
| `"conversational-v1"` | Multi-turn conversational agent. Requires `metadata.isConversational: true`. |

### Supported Models

Use the exact model string as shown. UiPath routes the call to the appropriate provider.

| Model string | Provider |
|---|---|
| `"gpt-4.1-2025-04-14"` | OpenAI |
| `"gpt-4o-2024-11-20"` | OpenAI |
| `"anthropic.claude-sonnet-4-20250514-v1:0"` | Anthropic (via AWS Bedrock) |
| `"gemini-2.5-pro"` | Google |

> Any model string supported by the UiPath AI Gateway can be used. Match the string exactly as provided by the platform or user.

### BYOM Properties

Used when the agent connects to a custom or self-hosted model endpoint.

```json
"byomProperties": {
  "endpointUrl": "https://my-llm.example.com/v1/chat",
  "modelAlias":  "my-custom-model"
}
```

Include `byomProperties` only when explicitly required; omit it for standard platform models.

---

## Resources

`resources` is an array of objects, each representing a capability the agent can invoke at runtime. Each resource has a `$resourceType` discriminator field.

```json
"resources": [
  { "$resourceType": "tool",       ... },
  { "$resourceType": "context",    ... },
  { "$resourceType": "escalation", ... },
  { "$resourceType": "mcp",        ... },
  { "$resourceType": "a2a",        ... }
]
```

Use `"resources": []` (or omit the field) when the agent needs no external capabilities.

---

### Resource Type: `tool`

Exposes a UiPath process, API workflow, or integration as a callable function to the agent.

```json
{
  "$resourceType": "tool",
  "name":        "API Workflow",
  "type":        "api",
  "location":    "solution",
  "isEnabled":   true,
  "inputSchema": {
    "type": "object",
    "properties": {
      "number1": { "type": "number" },
      "number2": { "type": "number" }
    },
    "required": ["number1", "number2"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "result": { "type": "number" }
    }
  },
  "properties": {
    "folderPath":  "solution_folder",
    "processName": "API Workflow"
  },
  "guardrail":           { "policies": [] },
  "settings":            {},
  "argumentProperties":  {}
}
```

#### Tool Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `$resourceType` | `"tool"` | **Yes** | Discriminator. |
| `name` | `string` | **Yes** | Display name shown to the LLM as the tool's function name. |
| `type` | `string` | **Yes** | Tool subtype (see [Tool Subtypes](#tool-subtypes)). |
| `location` | `string` | No | Where the tool is located. `"solution"` for same-solution workflows; may also be `"tenant"` or a folder path. |
| `isEnabled` | `boolean` | **Yes** | Whether the tool is active. Set to `true` to enable; `false` to disable without removing. |
| `inputSchema` | `object` | **Yes** | JSON Schema for the arguments the agent passes to the tool. |
| `outputSchema` | `object` | **Yes** | JSON Schema for the values the tool returns to the agent. |
| `properties` | `object` | **Yes** | Runtime routing properties (see [Tool Properties](#tool-properties)). |
| `guardrail` | `object` | No | Per-tool guardrail policies. Use `{ "policies": [] }` for none. |
| `settings` | `object` | No | Additional tool-level settings. Use `{}` unless needed. |
| `argumentProperties` | `object` | No | Metadata overrides for individual arguments. Use `{}` unless needed. |

#### Tool Subtypes

| `type` value | Invokes |
|---|---|
| `"api"` | An API workflow in the same solution or a UiPath process exposed via API trigger. |
| `"process"` | A UiPath automation process (job). |
| `"agent"` | Another UiPath agent (sub-agent invocation — use `"a2a"` resource type for cross-tenant). |
| `"integration"` | A UiPath Integration Service connector action. |
| `"internal"` | An internal platform function. |
| `"ixp"` | An IXP (Integration eXperience Platform) workflow. |

#### Tool Properties

| Property | Description |
|---|---|
| `folderPath` | Orchestrator folder containing the process/workflow. Use `"solution_folder"` for co-located solution items. |
| `processName` | Exact name of the process or workflow in Orchestrator. |

---

### Resource Type: `context`

Provides the agent with read access to a knowledge source (document index, file attachments, or Data Fabric entities).

```json
{
  "$resourceType": "context",
  "name": "Product Knowledge Base",
  "description": "Search product documentation for relevant information.",
  "contextType": "index",
  "folderPath": "MyFolder",
  "indexName": "products-index",
  "settings": {
    "resultCount": 5,
    "retrievalMode": "Semantic",
    "threshold": 0.7,
    "query": { "variant": "dynamic" }
  }
}
```

#### Context Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `$resourceType` | `"context"` | **Yes** | Discriminator. |
| `name` | `string` | **Yes** | Display name for the knowledge source. |
| `contextType` | `string` | No | Context subtype: `"index"`, `"attachments"`, or `"datafabricentityset"`. |
| `folderPath` | `string` | No | Orchestrator folder containing the index. |
| `indexName` | `string` | No | Name of the Context Grounding index (when `contextType` is `"index"`). |
| `settings.resultCount` | `integer` | No | Number of results to retrieve (default varies). |
| `settings.retrievalMode` | `string` | No | How documents are retrieved (see [Retrieval Modes](#retrieval-modes)). |
| `settings.threshold` | `float` | No | Minimum similarity score (0–1, default `0`). |
| `settings.query.variant` | `string` | No | Query strategy. Use `"dynamic"` for agent-determined queries. |
| `description` | `string` | No | Explains to the LLM what this knowledge source contains and when to query it. Write as a directive to the model, e.g. *"Search this whenever the user asks about product specs or pricing."* |
| `isEnabled` | `boolean` | No | Whether this context resource is active. Defaults to `true`. Set to `false` to temporarily disable without removing it. |

#### Retrieval Modes

| Value | Description |
|---|---|
| `"Semantic"` | Vector similarity search. Best for natural language Q&A. |
| `"Structured"` | Keyword / structured query. Best for exact lookups. |
| `"DeepRAG"` | Multi-hop retrieval with reasoning. Best for complex questions. |
| `"BatchTransform"` | Bulk document processing. |
| `"DataFabric"` | Used when `contextType` is `"datafabricentityset"`. |

---

### Resource Type: `escalation`

Pauses the agent and routes a Human-in-the-Loop (HITL) task to Action Center for human review or decision-making.

```json
{
  "$resourceType": "escalation",
  "name":                   "color",
  "description":            "Ask color confirmation",
  "isAgentMemoryEnabled":   false,
  "escalationType":         0,
  "channels": [
    {
      "name": "Channel",
      "type": "actionCenter",
      "inputSchema": {
        "type": "object",
        "properties": {
          "Content": { "type": "string" },
          "Comment": { "type": "string" }
        }
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "Comment": { "type": "string" }
        }
      },
      "outcomeMapping": {
        "approve": "continue",
        "reject":  "continue"
      },
      "recipients": [
        {
          "type":        1,
          "value":       "<user-or-group-id>",
          "displayName": "Team"
        }
      ],
      "properties": {
        "appName":                    "HITL App",
        "appVersion":                 1,
        "resourceKey":                "<uuid>",
        "isActionableMessageEnabled": false
      }
    }
  ]
}
```

#### Escalation Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `$resourceType` | `"escalation"` | **Yes** | Discriminator. |
| `name` | `string` | **Yes** | Identifier used by the agent when invoking this escalation. |
| `description` | `string` | No | Human-readable description of when/why to escalate. Shown to the LLM. |
| `isAgentMemoryEnabled` | `boolean` | No | Whether the agent retains context across the escalation pause. Default: `false`. |
| `escalationType` | `integer` | No | Escalation variant. `0` = standard Action Center task. |
| `channels` | `array` | **Yes** | One or more delivery channels for the HITL task (see [Channel Object](#channel-object)). |

#### Channel Object

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Channel display name. |
| `description` | `string` | Human-readable description of what this escalation channel does and when it is triggered. |
| `type` | `string` | Channel type. Currently `"actionCenter"`. |
| `inputSchema` | `object` | JSON Schema for data sent to the human reviewer. |
| `outputSchema` | `object` | JSON Schema for data returned by the human reviewer. |
| `outcomeMapping` | `object` | Maps human decisions (`"approve"`, `"reject"`) to agent actions (`"continue"`, `"abort"`). |
| `recipients` | `array` | List of recipient objects (`type`, `value`, `displayName`). `type: 1` = user; `type: 2` = group; `type: 3` = user email. |
| `properties` | `object` | Action Center app binding: `appName`, `appVersion`, `resourceKey` (UUID), `isActionableMessageEnabled`. |

---

### Resource Type: `mcp`

Connects the agent to an external Model Context Protocol (MCP) server, exposing its tools.

```json
{
  "$resourceType": "mcp",
  "name":          "My MCP Server",
  "description":   "Provides weather and location tools via MCP.",
  "isEnabled":     true,
  "folderPath":    "MyFolder",
  "slug":          "my-mcp-server",
  "availableTools": [
    {
      "name":        "get_weather",
      "description": "Returns current weather for a location.",
      "inputSchema":  { "type": "object", "properties": { "location": { "type": "string" } } },
      "outputSchema": { "type": "object", "properties": { "temperature": { "type": "number" } } }
    }
  ],
  "dynamicTools": "none"
}
```

| Field | Type | Description |
|---|---|---|
| `$resourceType` | `"mcp"` | Discriminator. |
| `name` | `string` | Display name for the MCP server. |
| `description` | `string` | Human-readable description shown to the LLM. |
| `isEnabled` | `boolean` | Enables or disables the MCP connection. |
| `folderPath` | `string` | Orchestrator folder containing the MCP server registration. |
| `slug` | `string` | URL-safe identifier for the MCP server. |
| `availableTools` | `array` | List of tools exposed by this MCP server. Each entry has `name`, `description`, `inputSchema`, and `outputSchema`. |
| `dynamicTools` | `string` | Controls runtime tool discovery: `"none"` (static list only), `"schema"` (fetch schemas at runtime), `"all"` (discover all tools at runtime). |

---

### Resource Type: `a2a`

Invokes another UiPath agent as a sub-agent (Agent-to-Agent). Use instead of `tool` type `"agent"` for cross-solution or cross-tenant agent calls.

```json
{
  "$resourceType":   "a2a",
  "name":            "Summarizer Agent",
  "description":     "Summarizes long documents into concise paragraphs.",
  "isEnabled":       true,
  "id":              "<target-agent-uuid>",
  "slug":            "summarizer-agent",
  "agentCardUrl":    "https://platform.uipath.com/agents/summarizer-agent/card",
  "isActive":        true,
  "cachedAgentCard": {}
}
```

| Field | Type | Description |
|---|---|---|
| `$resourceType` | `"a2a"` | Discriminator. |
| `name` | `string` | Display name for the target agent. |
| `description` | `string` | Human-readable description shown to the LLM. |
| `isEnabled` | `boolean` | Enables or disables this A2A connection. |
| `id` | `string` (UUID) | Stable identifier of the target agent. Omit when creating manually; Studio assigns it. |
| `slug` | `string` | URL-safe identifier for the target agent. |
| `agentCardUrl` | `string` | URL to the agent's A2A card descriptor (capabilities, schemas). |
| `isActive` | `boolean` | Whether the target agent is currently active and reachable. |
| `cachedAgentCard` | `object` | Cached copy of the agent card fetched from `agentCardUrl`. Use `{}` if not yet populated. |

---

## Guardrails

Guardrails are content-moderation and safety policies applied to LLM inputs and/or outputs. Defined at the top level of `agent.json` (not inside a resource).

```json
"guardrails": [
  { ... },
  { ... }
]
```

Each guardrail has a `$guardrailType` discriminator: `"builtInValidator"` or `"custom"`.

---

### Guardrail Type: `builtInValidator`

Uses a platform-provided ML validator.

```json
{
  "name":            "PII Detection",
  "$guardrailType":  "builtInValidator",
  "validatorType":   "pii_detection",
  "action": {
    "$actionType":   "log",
    "severityLevel": "Warning"
  },
  "selector": {
    "scopes": ["Agent", "Llm"]
  },
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id":             "entities",
      "value":          ["Email", "Address", "PhoneNumber", "Person"]
    },
    {
      "$parameterType": "map-enum",
      "id":             "entityThresholds",
      "value": {
        "Email":   0.5,
        "Address": 0.7
      }
    }
  ]
}
```

#### Built-In Validator Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | **Yes** | Display name for the guardrail rule. |
| `$guardrailType` | `"builtInValidator"` | **Yes** | Discriminator. |
| `validatorType` | `string` | **Yes** | Which built-in validator to use (see [Validator Types](#validator-types)). |
| `action` | `object` | **Yes** | What to do when the validator triggers (see [Guardrail Actions](#guardrail-actions)). |
| `selector` | `object` | **Yes** | Where to apply the guardrail — `scopes` array (see [Scopes](#scopes)). |
| `validatorParameters` | `array` | No | Typed parameter objects that configure the validator (see [Validator Parameters](#validator-parameters)). |

> **Additional fields from Studio Web:** Studio-generated guardrails may include `id` (UUID, auto-assigned), `description` (human-readable explanation), and `enabledForEvals` (boolean, default `true` — controls whether the guardrail runs during evaluations). These are optional when creating files manually.

#### Validator Types

| `validatorType` | Description |
|---|---|
| `"pii_detection"` | Detects Personally Identifiable Information (names, emails, phone numbers, addresses, etc.). |
| `"prompt_injection"` | Detects prompt injection attacks in user inputs. |

#### Scopes

| Scope | Description |
|---|---|
| `"Agent"` | Applied to the agent's own outputs / reasoning. |
| `"Llm"` | Applied to LLM inputs and outputs. |
| `"Tool"` | Applied to tool call arguments and results. |

#### Guardrail Actions

| `$actionType` | Description | Extra fields |
|---|---|---|
| `"log"` | Record a log entry but allow execution to continue. | `severityLevel`: `"Info"`, `"Warning"`, or `"Error"`. |
| `"block"` | Halts execution with an error. **Requires `"reason": "string"`.** | `reason`: string explaining why execution was blocked. |
| `"filter"` | Remove or redact the offending content and continue. | — |
| `"escalate"` | Route the event to an escalation channel. | `escalationName`: name of the escalation resource to invoke. |

#### Validator Parameters

Each entry in `validatorParameters` is a typed object:

| `$parameterType` | `id` (for `pii_detection`) | `value` type | Description |
|---|---|---|---|
| `"enum-list"` | `"entities"` | `string[]` | List of PII entity types to detect: `"Email"`, `"Address"`, `"PhoneNumber"`, `"Person"`, `"Organization"`, `"CreditCardNumber"`, etc. |
| `"map-enum"` | `"entityThresholds"` | `{ [entity]: number }` | Confidence threshold (0–1) per entity type. Detections below this score are ignored. |
| `"number"` | `"threshold"` | `number` | Single numeric threshold (used by `prompt_injection`). |
| `"boolean"` | `"<flag-id>"` | `boolean` | A true/false configuration flag. |
| `"string"` | `"<string-id>"` | `string` | A free-text configuration value. |

---

### Guardrail Type: `custom`

Defines a rule using simple value comparisons (no ML model required).

```json
{
  "name":           "Block empty output",
  "$guardrailType": "custom",
  "action": {
    "$actionType": "block",
    "reason": "Output must not be empty."
  },
  "selector": {
    "scopes": ["Agent"]
  },
  "rules": [
    {
      "field":    "output.result",
      "operator": "equals",
      "value":    ""
    }
  ]
}
```

Custom guardrail `rules` entries support `"equals"`, `"notEquals"`, `"contains"`, `"greaterThan"`, `"lessThan"` operators on string, number, and boolean fields.

---

## Complete Minimal Example

A task agent with two numeric inputs and one numeric output, no resources, no guardrails:

```json
{
  "version": "1.0.0",
  "name": "Calculator Agent",
  "metadata": {
    "storageVersion": "44.0.0",
    "isConversational": false
  },
  "messages": [
    {
      "role": "system",
      "content": "You are a calculator agent. Perform arithmetic operations precisely.",
      "contentTokens": [
        { "type": "simpleText", "rawString": "You are a calculator agent. Perform arithmetic operations precisely." }
      ]
    },
    {
      "role": "user",
      "content": "Calculate: {{a}} {{operator}} {{b}}",
      "contentTokens": [
        { "type": "simpleText", "rawString": "Calculate: " },
        { "type": "variable",   "rawString": "input.a" },
        { "type": "simpleText", "rawString": " " },
        { "type": "variable",   "rawString": "input.operator" },
        { "type": "simpleText", "rawString": " " },
        { "type": "variable",   "rawString": "input.b" }
      ]
    }
  ],
  "inputSchema": {
    "type": "object",
    "properties": {
      "a":        { "type": "number" },
      "b":        { "type": "number" },
      "operator": { "type": "string" }
    },
    "required": ["a", "b", "operator"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "result": { "type": "number" }
    }
  },
  "settings": {
    "model":         "gpt-4.1-2025-04-14",
    "maxTokens":     16384,
    "temperature":   0,
    "engine":        "basic-v2",
    "maxIterations": 25
  },
  "resources": [],
  "features":  []
}
```

---

## Complete Full-Featured Example

An agent with an API tool, an Action Center escalation, and guardrails:

```json
{
  "id":      "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "version": "1.0.0",
  "name":    "Order Review Agent",
  "metadata": {
    "storageVersion":  "31.0.0",
    "isConversational": false
  },
  "messages": [
    {
      "role":    "system",
      "content": "You are an order review agent. Use the available tools to validate orders and escalate when uncertain.",
      "contentTokens": [
        { "type": "simpleText", "rawString": "You are an order review agent. Use the available tools to validate orders and escalate when uncertain." }
      ]
    },
    {
      "role":    "user",
      "content": "Review order {{orderId}} for customer {{customerName}}.",
      "contentTokens": [
        { "type": "simpleText", "rawString": "Review order " },
        { "type": "variable",   "rawString": "input.orderId" },
        { "type": "simpleText", "rawString": " for customer " },
        { "type": "variable",   "rawString": "input.customerName" },
        { "type": "simpleText", "rawString": "." }
      ]
    }
  ],
  "inputSchema": {
    "type": "object",
    "properties": {
      "orderId":      { "type": "string" },
      "customerName": { "type": "string" }
    },
    "required": ["orderId", "customerName"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "decision": { "type": "string" },
      "reason":   { "type": "string" }
    }
  },
  "settings": {
    "model":         "gpt-4o-2024-11-20",
    "maxTokens":     8192,
    "temperature":   0,
    "engine":        "basic-v2",
    "maxIterations": 25
  },
  "resources": [
    {
      "$resourceType": "tool",
      "name":          "Validate Order",
      "type":          "api",
      "location":      "solution",
      "isEnabled":     true,
      "inputSchema": {
        "type": "object",
        "properties": {
          "orderId": { "type": "string" }
        },
        "required": ["orderId"]
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "isValid":    { "type": "boolean" },
          "totalValue": { "type": "number" }
        }
      },
      "properties": {
        "folderPath":  "solution_folder",
        "processName": "Validate Order"
      },
      "guardrail":          { "policies": [] },
      "settings":           {},
      "argumentProperties": {}
    },
    {
      "$resourceType":        "escalation",
      "name":                 "managerApproval",
      "description":          "Escalate to a manager for high-value or ambiguous orders",
      "isAgentMemoryEnabled": false,
      "escalationType":       0,
      "channels": [
        {
          "name": "Channel",
          "type": "actionCenter",
          "inputSchema": {
            "type": "object",
            "properties": {
              "Content": { "type": "string" },
              "Comment": { "type": "string" }
            }
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "Comment":  { "type": "string" }
            }
          },
          "outcomeMapping": {
            "approve": "continue",
            "reject":  "continue"
          },
          "recipients": [
            { "type": 2, "value": "managers-group-id", "displayName": "Managers" }
          ],
          "properties": {
            "appName":                    "Order Review HITL",
            "appVersion":                 1,
            "resourceKey":                "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            "isActionableMessageEnabled": false
          }
        }
      ]
    }
  ],
  "features": [],
  "guardrails": [
    {
      "name":           "PII Detection",
      "$guardrailType": "builtInValidator",
      "validatorType":  "pii_detection",
      "action": {
        "$actionType":   "log",
        "severityLevel": "Warning"
      },
      "selector": {
        "scopes": ["Agent", "Llm"]
      },
      "validatorParameters": [
        {
          "$parameterType": "enum-list",
          "id":             "entities",
          "value":          ["Email", "PhoneNumber", "CreditCardNumber"]
        },
        {
          "$parameterType": "map-enum",
          "id":             "entityThresholds",
          "value": {
            "Email":           0.5,
            "PhoneNumber":     0.6,
            "CreditCardNumber": 0.8
          }
        }
      ]
    },
    {
      "name":           "Prompt Injection Guard",
      "$guardrailType": "builtInValidator",
      "validatorType":  "prompt_injection",
      "action": {
        "$actionType":   "block",
        "reason": "Prompt injection detected."
      },
      "selector": {
        "scopes": ["Llm"]
      },
      "validatorParameters": [
        { "$parameterType": "number", "id": "threshold", "value": 0.5 }
      ]
    }
  ]
}
```

---

## Studio Web Generated Fields

When you pull an `agent.json` from Studio Web, it may contain additional fields not documented above:

- **Escalation channels:** `id`, `description`, `inputSchemaDotnetTypeMapping`, `outputSchemaDotnetTypeMapping`, `actionableMessageMetaData`
- **Escalation top-level:** `governanceProperties`, `properties`
- **Tool resources:** `id`, `referenceKey`, `location`
- **Top-level:** `projectId`, `type: "lowCode"`

These fields are auto-assigned by Studio Web. They are **not required** when creating `agent.json` manually — the runtime fills in defaults where needed. Do not fabricate UUIDs for `id` or `referenceKey` fields; omit them instead.

---

## Authoring Rules and Conventions

Follow these rules when creating or editing `agent.json` files:

1. **Always include all required fields** — `messages`, `inputSchema`, `outputSchema`, `settings`, and `metadata` must be present.

2. **Keep `messages` to exactly two entries** — `system` first, `user` second. Never add a third.

3. **Sync `content` and `contentTokens`** — every `{{variable}}` in `content` needs a matching `variable` token in `contentTokens`. Every literal text segment becomes a `simpleText` token.

4. **Variable references use `input.` prefix in tokens** — `"rawString": "input.myVar"` corresponds to `{{myVar}}` in `content`.

5. **Match `inputSchema.properties` to message variables** — every `{{variable}}` in the user message must appear as a property in `inputSchema.properties`.

6. **Use `"engine": "basic-v2"`** for new non-conversational agents unless a specific requirement calls for another engine.

7. **Set `"temperature": 0`** for task/automation agents; use higher values only for creative or conversational agents.

8. **Use `"resources": []` and `"features": []`** (not omit the fields) for consistency and forward compatibility.

9. **Do not generate `id`** when creating new files — UiPath Studio will assign it on first save.

10. **`storageVersion`** should match the Studio version generating the file; default to `"44.0.0"` for new agents.

11. **Resource `name` fields are seen by the LLM** — use clear, verb-phrase names for tools (e.g., `"Get Customer Profile"`, `"Submit Order"`) so the model knows when to call them.

12. **Guardrails at the top level apply to the whole agent** — per-tool guardrails go inside the tool's `guardrail.policies` array.
