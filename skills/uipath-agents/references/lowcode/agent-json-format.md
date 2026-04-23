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
    "folderPath": "solution_folder",  // Always "solution_folder" — for both solution-internal and external
    "exampleCalls": []                // Required for external tools
  },
  "guardrail": {
    "policies": []
  },
  "id": "<uuid>",              // Stable; generate once, never change
  "referenceKey": "<release-key-guid>", // For external: the release Key (lowercase GUID from /odata/Releases API). For solution-internal: leave empty, validate resolves it.
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
| `api` | Calling an API workflow in Orchestrator |
| `processOrchestration` | Calling an agentic process (process orchestration / flow) in Orchestrator |

Note: MCP (Model Context Protocol) server resources use `$resourceType: "mcp"` — a separate resource type, not a `type` value inside a tool resource. See [MCP resource](#mcp-resource-resourcetype-mcp) below.

### Integration Service tool resource (`type: "integration"`)

Integration Service tools call connector activities (e.g., Slack Send Message, Web Search). They differ from Orchestrator-based tools:
- `type` is `"integration"` (not `"process"`, `"agent"`, etc.)
- `location` is `"external"`
- `properties` contains IS-specific fields: `toolPath`, `objectName`, `connection`, `parameters`, `bodyStructure`
- Additional top-level fields: `iconUrl`, `isPreview`
- No `referenceKey` or `argumentProperties`
- Solution-level resources use `connection/` (not `package/` + `process/`)

**Path:** `resources/{ToolName}/resource.json`

```jsonc
{
  "$resourceType": "tool",
  "id": "<uuid>",
  "type": "integration",
  "location": "external",
  "name": "<DisplayName from activity>",
  "description": "<full Description from activity — do not truncate>",
  "isEnabled": true,
  "inputSchema": {
    "type": "object",
    "properties": {
      "<fieldName>": {
        "type": "<type from requestField>",
        "title": "<displayName from requestField>",
        "description": "<description from requestField>"
      }
    },
    "additionalProperties": false,
    "required": ["<required field names>"]
  },
  "outputSchema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "<scalarField>": {
        "title": "<displayName from responseField>",
        "type": "<type from responseField>",
        "description": "<description from responseField>"
      },
      "results[*]": {                                   // ← literal key, keep the `[*]` suffix
        "title": "<displayName>",
        "type": "array",
        "items": { "$ref": "#/definitions/results[*]" } // ← same literal `[*]` in $ref
      }
    },
    "definitions": {
      "results[*]": {                                   // ← matches the $ref literally
        "type": "object",
        "properties": {
          "<nestedField>": {
            "title": "<displayName>",
            "type": "<type>",
            "description": "<description>"
          }
        }
      }
    }
  },
  "iconUrl": "<connector image URL — see rules below>",
  "settings": {},
  "guardrail": { "policies": [] },
  "isPreview": false,
  "properties": {
    "toolPath": "<path from metadata, e.g. /v2/webSearch>",
    "objectName": "<ObjectName from activity, e.g. v2::webSearch>",
    "toolDisplayName": "<DisplayName>",
    "toolDescription": "<full Description from activity — same text as top-level description>",
    "method": "<method from metadata, e.g. POST>",
    "bodyStructure": { "contentType": "json" },
    "connection": {
      "id": "<connection-id from uip is connections list>",
      "name": "<connection name>",
      "elementInstanceId": 0,
      "apiBaseUri": "",
      "state": "enabled",
      "isDefault": false,                    // ← always false on the tool's connection block
      "connector": {
        "key": "<connector-key>",
        "name": "<connector display name>",
        "image": "<same URL as top-level iconUrl>",
        "enabled": true,
        "isPreview": false
      },
      "folder": {
        "key": "<FolderKey from connection>",
        "path": "<same value as folder.key — NOT empty>"
      },
      "solutionProperties": {
        "resourceKey": "<connection-id>"
      }
    },
    "parameters": [
      {
        "name": "<field name>",
        "displayName": "<field displayName>",
        "type": "<field type>",
        "fieldLocation": "body",
        "value": "{{prompt}}",
        "description": "<field description>",
        "position": "primary",
        "sortOrder": 1,
        "required": true,
        "fieldVariant": "dynamic",
        "isCascading": false,
        "dynamic": true,
        "enumValues": null,
        "loadReferenceOptionsByDefault": null,
        "dynamicBehavior": [],
        "reference": null
      }
    ]
  }
}
```

**IMPORTANT rules for `outputSchema` (arrays of objects):**
- Response fields in the metadata named like `results[*].title` indicate an array of objects. Represent this as:
  - A property keyed **literally** `"results[*]"` (keep the `[*]` suffix in the JSON key) with `type: "array"` and `items: { "$ref": "#/definitions/results[*]" }`.
  - A `definitions` entry keyed with the exact same literal `"results[*]"` whose `properties` contain the nested fields (`title`, `snippet`, `url`, ...).
- Do NOT rename to `"results"` / `"resultItem"` / camelCase. Studio Web matches the literal key from the activity metadata — renaming causes the tool to be silently dropped from the agent UI.
- Preserve each response field's `description` from the metadata (both scalar and nested). Do not drop it.

**IMPORTANT rules for `iconUrl` and `connector.image`:**
- Both fields MUST be populated with the same URL in the tenant-scoped form: `{UIPATH_URL}/{organizationName}/{tenantName}/elements_/v3/element/elements/{connectorKey}/image`.
- Build it directly from the auth env vars (`UIPATH_URL`, `UIPATH_ORGANIZATION_NAME`, `UIPATH_TENANT_NAME`). No discovery call is needed — the tenant route resolves the scale unit server-side.
- Leaving `iconUrl` as `""` or omitting it does NOT produce a validation error, but Studio Web may silently drop the tool from the agent UI. Always populate it.

**IMPORTANT rules for `properties.connection`:**
- `connection.id` MUST be the actual IS connection ID (from `uip is connections list`). Studio Web validates tools by fetching the connection by this ID — a random UUID will cause "Connection is required" errors.
- `connection.folder.key` AND `connection.folder.path` MUST both be populated. `path` is the folder key string (same value as `key`) — never the empty string.
- `connection.isDefault` MUST be `false` on the tool's connection block, even if the connection is marked default in `uip is connections list`. The flag here is tool-scoped, not IS-scoped.
- `solutionProperties.resourceKey` MUST equal `connection.id`. This links the tool to the solution connection resource.
- All tools sharing the same connector MUST share the same `solutionProperties.resourceKey`.

**Parameter `fieldVariant` values:**
- `"dynamic"` — value filled by the LLM at runtime (`value: "{{prompt}}"`, `dynamic: true`, `enumValues: null`)
- `"static"` — pre-configured value (e.g., single-value enum default). Set `dynamic: false`, `value` to the chosen enum value, and `enumValues` to the object-array form below.

**Parameter `enumValues` format — MUST be an array of `{name, value}` objects, never bare strings:**
```jsonc
"enumValues": [
  { "name": "GoogleCustomSearch", "value": "GoogleCustomSearch" }
]
```
The activity metadata's `fields.<name>.enum` already has this exact shape — copy it through verbatim. A bare-string array like `["GoogleCustomSearch"]` passes `uip agent validate` but makes Studio Web silently drop the tool from the agent UI.

**Parameter `fieldLocation` values:**
- `"body"` — sent in request body (most `requestFields`)
- `"query"` — sent as query parameter (from metadata `parameters` with `type: "query"`)
- `"path"` — sent as path parameter

**Parameter `toolDescription` and top-level `description`:** both must be the full description from the activity metadata. Do not abbreviate either.

### Solution-level resources for Integration Service tools

Solution-level connection resources and `debug_overwrites.json` are **auto-generated** — do not create them manually. After creating the agent-level `resource.json`:

1. Run `uip agent validate` — generates `bindings_v2.json` in the agent project directory
2. Run `uip solution resource refresh` from the solution root — auto-generates `resources/solution_folder/connection/{connectorKey}/` files and `debug_overwrites.json`

**`location` and `folderPath`:**

| `location` | `folderPath` | Meaning |
|------------|-------------|---------|
| `"solution"` | `"solution_folder"` | Resource is another project within this same solution. Creating this agent-level resource.json is sufficient. |
| `"external"` | `"solution_folder"` | Resource is already deployed in Orchestrator, outside this solution. Creating this agent-level resource.json alone is NOT sufficient — you MUST also create solution-level resource files. |

**MANDATORY for `"location": "external"`:** This agent-level resource.json is only 1 of 4 files needed. Without the other 3 files, Studio Web will show "resource is missing in this environment". You MUST also create:
1. **Process declaration:** `resources/solution_folder/process/<type_dir>/<ToolName>.json` at the solution root (see type-to-directory mapping below)
2. **Package declaration:** `resources/solution_folder/package/<PackageName>.json` at the solution root
3. **debug_overwrites.json:** `userProfile/<userId>/debug_overwrites.json` at the solution root — maps `solution_folder` to the actual Orchestrator folder

**Type-to-directory mapping for process declarations:**

| `ProcessType` (from Releases API) | Agent resource `type` | `spec.type` | Process declaration directory |
|---|---|---|---|
| `Process` | `process` | `Process` | `process/process/` |
| `Agent` | `agent` | `Agent` | `process/agent/` |
| `Api` | `api` | `Api` | `process/api/` |
| `ProcessOrchestration` | `processOrchestration` | `ProcessOrchestration` | `process/processOrchestration/` |

See § Solution-Level Resource Files for External Tools below for the full format, or [agent-solution-guide.md](agent-solution-guide.md) § External process tool.

### Context resource (`$resourceType: "context"`)

**Path:** `resources/{ContextName}/resource.json`

Three context variants exist, discriminated by `contextType`. All enum values are **lowercase** — `"dataFabricEntitySet"`, `"deepRAG"`, or `"batchTransform"` (camelCase) will pass `uip agent validate` but Studio Web silently drops the resource from the agent UI.

| `contextType` | Use when | Solution-level auto-gen on `uip solution resource refresh` |
|---|---|---|
| `"index"` | Searches an ECS Context Grounding index with a query | **Yes** — creates `resources/solution_folder/index/<Name>.json` plus the dependent bucket, when the ECS index is backed by a StorageBucket data source |
| `"attachments"` | File-based, no solution resource binding (files are passed at runtime) | No — agent-level `resource.json` is sufficient |
| `"datafabricentityset"` | Backed by one or more DataFabric entity sets | No — not yet supported by refresh |

#### `contextType: "index"`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",                       // stable; generate once
  "referenceKey": null,                 // leave null; refresh resolves the ECS index GUID by indexName
  "name": "<ContextName>",              // display name; matches the folder under resources/
  "description": "",
  "contextType": "index",
  "folderPath": "solution_folder",
  "indexName": "<IndexName>",           // MUST match the ECS index Name exactly (case-sensitive)
  "settings": {
    "retrievalMode": "semantic",        // "semantic" | "structured" | "deeprag" | "batchtransform"
    "query": { "variant": "dynamic", "description": "Query for retrieval" },
    "folderPathPrefix": { "variant": "static" },
    "fileExtension": { "value": "All" },  // object, not string
    "threshold": 0,
    "resultCount": 3
  }
}
```

**`retrievalMode` values (all lowercase) and per-mode `fileExtension.value` + extra fields:**

| `retrievalMode` | Legal `fileExtension.value` | Extra required fields |
|---|---|---|
| `"semantic"` | `"All"`, `"pdf"`, `"csv"`, `"json"`, `"docx"`, `"xlsx"`, `"txt"` | none |
| `"structured"` | `"csv"` | none |
| `"deeprag"` | `"pdf"`, `"txt"` | `"citationMode": { "value": "Inline" }` (or `"Skip"`) |
| `"batchtransform"` | `"csv"` | `"webSearchGrounding": { "value": "Enabled" }` (or `"Disabled"`), `"outputColumns": [{ "name": "...", "description": "..." }, ...]` |

**`query.variant`:** `"dynamic"` (LLM supplies at runtime), `"argument"` (bound to an input field), or `"static"` (pre-set value).

**`folderPathPrefix.variant`:** `"static"` (no prefix) or `"argument"` (scope by a folder path provided at runtime).

#### `contextType: "attachments"`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",
  "referenceKey": null,
  "name": "<ContextName>",
  "description": "",
  "contextType": "attachments",
  "indexName": "<ContextName>",          // same as name for attachments
  "attachments": {
    "description": "Array of files, documents, images to process."
  },
  "settings": {
    "retrievalMode": "semantic",
    "query": { "variant": "dynamic" },
    "folderPathPrefix": { "variant": "static" },
    "fileExtension": { "value": "All" },
    "threshold": 0,
    "resultCount": 3
  }
}
```

No solution-level file is produced — attachments are runtime-only.

#### `contextType: "datafabricentityset"`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",
  "referenceKey": null,
  "name": "<ContextName>",
  "description": "",
  "contextType": "datafabricentityset",
  "entitySet": [
    {
      "id": "<uuid>",
      "referenceKey": "<entity-key>",
      "name": "<EntityName>",
      "folderId": "<folder-uuid>",
      "folderDisplayName": "Shared",
      "description": null
    }
    // ...more entities
  ]
}
```

No `indexName` and no `settings` for DataFabric contexts. The shape is entirely different from index/attachments. Solution-level resource generation for DataFabric contexts is not yet supported by `uip solution resource refresh` — the agent-level `resource.json` is written, but you must hand-author any solution manifests needed.

#### Auto-generated solution-level files (index contexts only)

For `contextType: "index"` with a StorageBucket-backed ECS index, `uip agent validate` emits:

```json
{
  "resource": "index",
  "key": "<IndexName>",
  "value": { "name": { "defaultValue": "<IndexName>", "isExpression": false, "displayName": "Index Name" } },
  "metadata": { "bindingsVersion": "2.2", "solutionsSupport": "true" }
}
```

into `bindings_v2.json` at the agent project root. `uip solution resource refresh` then:

1. Calls ECS `GET ecs_/v2/indexes/AllAcrossFolders?$filter=Name eq '<IndexName>'&$expand=dataSource` — resolves the index GUID, folder key, and data source type.
2. If `dataSource.@odata.type` is not `#UiPath.Vdbs.Domain.Api.V20Models.StorageBucketDataSource`, warns + skips (other data sources — GoogleDrive, OneDrive, Dropbox, Confluence, Attachments — are not yet wired).
3. Calls Orchestrator `GET orchestrator_/odata/Buckets?$filter=Name eq '<BucketName>'` with the index's `folderKey` as `X-UIPATH-FolderKey` — gets the bucket `Identifier` GUID.
4. Registers the bucket as a solution resource via the resource-builder SDK — writes `resources/solution_folder/Bucket/OrchestratorBucket/<BucketName>.json`.
5. Hand-writes `resources/solution_folder/index/<IndexName>.json` with `kind: "index"`, `apiVersion: "ecs.uipath.com/v2"`, `dependencies: [{name: "<BucketName>", kind: "bucket"}]`, `spec.storageBucketReference: { name, key }`, `dataSourceType: "StorageBucket"`.
6. Appends two entries (`kind: "index"` + `kind: "bucket"`) to `userProfile/<userId>/debug_overwrites.json`.

All failures (index not found, ambiguous name match, non-StorageBucket data source, bucket missing in Orchestrator) warn + continue — the command never aborts.

### Escalation resource (`$resourceType: "escalation"`)

**Path:** `resources/{EscalationName}/resource.json`

Escalations hand off agent control to a human via a channel. The only channel type currently supported end-to-end by `uip solution resource refresh` is `actionCenter` — it targets a deployed Action Center app (a UiPath web app of kind `workflow Action`). Other channel types (`email`, `slack`, `teams`) are recognised by the runtime but have no automatic solution-level resource generation and are out of scope for this skill.

**Minimum shape** — values the agent must populate. Fields marked `// derived` are copied from the Action Center app's `action-schema` response (see Scenario 6 for the discovery commands).

```jsonc
{
  "$resourceType": "escalation",
  "id": "<uuid-v4>",                                // stable; generate once, never change
  "name": "MyEscalation",                           // folder name & resource name must match
  "description": "Escalate to a human assistant for approval",
  "escalationType": 0,                              // 0 = Escalation, 1 = VsEscalation
  "isAgentMemoryEnabled": false,
  "ixpToolId": null,                                // only used when escalationType = 1
  "storageBucketName": null,                        // only used when escalationType = 1
  "properties": {},
  "governanceProperties": { "isEscalatedAtRuntime": false },
  "channels": [
    {
      "id": "<uuid-v4>",                            // channel id — generate a new one per channel
      "name": "Channel",
      "description": "Channel description",
      "type": "actionCenter",                       // lowercase. Other values: "email", "slack", "teams"
      "inputSchema": {                              // derived from action-schema.inputs + action-schema.inOuts
        "type": "object",
        "properties": {
          "<argName>": { "type": "<jsonSchemaType>", "description": "<desc>" }
        }
      },
      "inputSchemaDotnetTypeMapping": {             // { argName: "System.String" | "System.Int32" | ... }
        "<argName>": "System.String"
      },
      "outputSchema": {                             // derived from action-schema.inOuts + action-schema.outputs
        "type": "object",
        "properties": {
          "<argName>": { "type": "<jsonSchemaType>", "description": "<desc>" }
        }
      },
      "outputSchemaDotnetTypeMapping": {
        "<argName>": "System.String"
      },
      "outcomeMapping": {                           // one key per action-schema.outcomes[].name
        "<outcomeName>": "continue"                 // "continue" (agent resumes) | "end" (agent stops)
      },
      "properties": {
        "resourceKey": "<appId-guid>",              // from `action-apps?state=deployed` → `id`
        "appName": "<deploymentTitle>",             // from the same response → `deploymentTitle`
        "folderName": null,                         // MUST be null — setting "solution_folder" or anything else causes Studio Web "Resource provisioning failed (#100)" on solution import
        "appVersion": 1,                            // from the same response → `deployVersion` (integer)
        "isActionableMessageEnabled": false,
        "actionableMessageMetaData": null
      },
      "recipients": [                               // REQUIRED — at least one. Empty array uploads but Studio Web shows the escalation with no assignee.
        {
          "type": 3,                                // RecipientType: 1=UserId, 2=GroupId, 3=UserEmail (preferred — simplest),
                                                    //   4=AssetUserEmail, 5=StaticGroupName, 6=AssetGroupName
          "value": "user@example.com"               // for type 3, the email string. For type 1/2, a user/group GUID.
                                                    // `displayName` is NOT required for type 3 — omit it.
        }
      ],
      "taskTitle": "Approval request",              // deprecated but still written for back-compat
      "taskTitleV2": {
        "type": "textBuilder",                      // or "dynamic" (single string) — see contentTokens rules
        "tokens": [
          { "type": "simpleText", "rawString": "Approval request" }
        ]
      },
      "labels": []                                  // optional string tags
    }
  ]
}
```

**`outcomeMapping` rules:**
- One entry per outcome returned by the app's `action-schema` (e.g., `approve`, `reject`).
- Each value is `"continue"` (agent processes the outcome and continues) or `"end"` (agent stops when the outcome fires).
- Default every outcome to `"continue"` unless the user has specified otherwise.

**`inputSchema` / `outputSchema` derivation from the action schema response:**
- `channel.inputSchema.properties` = union of `action-schema.inputs[].name` and `action-schema.inOuts[].name` — these are what the human sees in the task form.
- `channel.outputSchema.properties` = union of `action-schema.inOuts[].name` and `action-schema.outputs[].name` — these are what the agent receives back.
- For each property, set `type` by mapping the dotnet type string in the same way as external RPA process tools (`System.String` → `"string"`, `System.Int32`/`Int64`/`Decimal`/`Double` → `"number"`, `System.Boolean` → `"boolean"`, everything else → `"string"`).
- Copy each arg's `description` verbatim when present.
- `inputSchemaDotnetTypeMapping` / `outputSchemaDotnetTypeMapping` preserve the raw dotnet type names keyed by arg name — Studio Web uses these when serialising task payloads.

**Solution-level files for Action Center escalations are auto-generated.** Unlike external process tools, you do NOT hand-write any solution-level files for an escalation. `uip solution resource refresh` scans agent projects for escalation resources, resolves each `properties.resourceKey` against the Apps API + `publish/versions` + Orchestrator `/odata/Releases` + `GetPackageEntryPointsV2`, and writes all four required files itself:

- `resources/solution_folder/app/workflow Action/<deploymentTitle>.json`
- `resources/solution_folder/appVersion/<title>.json`
- `resources/solution_folder/package/<title>.json`
- `resources/solution_folder/process/webApp/<deploymentTitle>.json`

The fourth file (`process/webApp/...`) backs the app resource's `dependencies[1]: {kind: "Process"}` — without it, Studio Web reports "Resource provisioning failed (#100)" on solution import. See Scenario 6 in [quickstart.md](quickstart.md) for the full flow.

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

## Solution-Level Resource Files for External Tools

When an agent uses an external tool (an RPA process, agent, or other resource already deployed in Orchestrator), the solution needs resource declarations so it can resolve the tool at deployment/runtime. These files live at the **solution root** level (not inside the agent project directory).

### Directory structure

```
<SolutionName>/
├── <SolutionName>.uipx
├── <AgentName>/
│   ├── agent.json
│   └── resources/
│       └── <ToolName>/
│           └── resource.json            # Agent-level resource (see § Tool resource above)
├── resources/
│   └── solution_folder/
│       ├── package/
│       │   ├── <AgentName>.json         # Agent package (auto-generated by uip solution project add)
│       │   └── <PackageName>.json       # External tool package declaration (YOU CREATE THIS)
│       └── process/
│           ├── agent/
│           │   └── <AgentName>.json     # Agent process (auto-generated by uip solution project add)
│           ├── process/                 # ← RPA processes (type: "process")
│           ├── api/                     # ← API workflows (type: "api")
│           └── processOrchestration/    # ← Agentic processes (type: "processOrchestration")
│               └── <ToolName>.json      # External tool process declaration (YOU CREATE THIS)
└── userProfile/
    └── <userId>/
        └── debug_overwrites.json        # Folder resolution for Studio Web (YOU CREATE THIS)
```

The process declaration directory depends on the tool type. Place the file in the subdirectory matching the `ProcessType` from the Releases API: `process/` for RPA, `agent/` for agents, `api/` for API workflows, `processOrchestration/` for agentic processes.

### Process declaration

**Path:** `resources/solution_folder/process/<type_dir>/<ToolName>.json`

Declares the external process as a solution resource. The structure differs between RPA processes and all other types (Agent, API, Agentic Process). Get the values from the Releases API and `GetPackageEntryPointsV2` (see § How to get the values).

#### Template A — RPA Process (`type: "process"`)

**Path:** `resources/solution_folder/process/process/<ToolName>.json`

Uses `inputArgumentsSchema`/`outputArgumentsSchema` (raw .NET type arrays from `Arguments.Input`/`Arguments.Output`). Entry point fields and V2 schema fields are `null`.

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<ToolName>",
    "kind": "process",
    "type": "process",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [
      {
        "name": "<PackageName>",
        "kind": "Package"
      }
    ],
    "runtimeDependencies": [],
    "files": [],
    "folders": [
      { "fullyQualifiedName": "solution_folder" }
    ],
    "spec": {
      "type": "Process",
      "jobPriority": "Medium",
      "jobRecording": "Disabled",
      "duration": 40,
      "frequency": 500,
      "quality": 100,
      "remoteControlAccess": "None",
      "name": "<ToolName>",
      "package": {
        "name": "<PackageName>",
        "key": "<PackageName>:<Version>"
      },
      "packageName": "<PackageName>",
      "packageVersion": "<Version>",
      "entryPointUniqueId": null,
      "entryPointName": null,
      "inputArguments": null,
      "inputArgumentsSchema": "<raw Arguments.Input string from Releases API>",
      "outputArgumentsSchema": "<raw Arguments.Output string from Releases API>",
      "inputArgumentsSchemaV2": null,
      "outputArgumentsSchemaV2": null,
      "hiddenForAttendedUser": false,
      "alwaysRunning": false,
      "autoStartProcess": false,
      "targetFrameworkValue": "Portable",
      "retentionAction": "Delete",
      "retentionPeriod": 30,
      "retentionBucketRef": null,
      "staleRetentionAction": "Delete",
      "staleRetentionPeriod": 180,
      "staleRetentionBucketRef": null,
      "entryPoints": null,
      "connections": null,
      "tags": [],
      "description": null
    },
    "locks": [],
    "key": "<release-key-guid>"
  }
}
```

#### Template B — Agent / API Workflow / Agentic Process

**Path:** `resources/solution_folder/process/<type_dir>/<ToolName>.json` where `<type_dir>` is `agent/`, `api/`, or `processOrchestration/`.

Uses `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` (JSON Schema strings from `GetPackageEntryPointsV2`). Populates `entryPointUniqueId`, `entryPointName`, and `entryPoints`. Old-style schema fields are `null`. No RPA-specific spec fields (`jobPriority`, `jobRecording`, etc.).

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<ToolName>",
    "kind": "process",
    "type": "<type>",                       // "agent", "api", or "processOrchestration"
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [
      {
        "name": "<PackageName>",
        "kind": "Package"
      }
    ],
    "runtimeDependencies": [],
    "files": [],
    "folders": [
      { "fullyQualifiedName": "solution_folder" }
    ],
    "spec": {
      "type": "<Type>",                     // "Agent", "Api", or "ProcessOrchestration" (PascalCase)
      // Agent-only fields (include ONLY when type = "agent"):
      // "agentMemory": false,
      // "targetRuntime": "pythonAgent",
      // "environmentVariables": "",
      // "referencedAssets": null,
      "name": "<ToolName>",
      "package": {
        "name": "<PackageName>",
        "key": "<PackageName>:<Version>"
      },
      "packageName": "<PackageName>",
      "packageVersion": "<Version>",
      "entryPointUniqueId": "<UniqueId from GetPackageEntryPointsV2>",
      "entryPointName": "<Path from GetPackageEntryPointsV2>",
      "inputArguments": null,
      "inputArgumentsSchema": null,
      "outputArgumentsSchema": null,
      "inputArgumentsSchemaV2": "<InputArguments JSON Schema string from GetPackageEntryPointsV2>",
      "outputArgumentsSchemaV2": "<OutputArguments JSON Schema string from GetPackageEntryPointsV2>",
      "hiddenForAttendedUser": false,
      "alwaysRunning": false,
      "autoStartProcess": false,
      "targetFrameworkValue": "Portable",
      "retentionAction": "Delete",
      "retentionPeriod": 30,
      "retentionBucketRef": null,
      "staleRetentionAction": "Delete",
      "staleRetentionPeriod": 180,
      "staleRetentionBucketRef": null,
      "entryPoints": "<serialized JSON array — see below>",
      "connections": null,
      "tags": [],
      "description": null
    },
    "locks": [],
    "key": "<release-key-guid>"
  }
}
```

**`entryPoints` serialized JSON format** (for Agent/API/Agentic Process only):

Construct a JSON array, then serialize it as a string. Use data from `GetPackageEntryPointsV2`:

```jsonc
[{
  "UniqueId": "<UniqueId>",
  "Path": "<Path>",
  "DisplayName": null,
  "InputArguments": "<InputArguments string>",   // Same as inputArgumentsSchemaV2
  "OutputArguments": "<OutputArguments string>", // Same as outputArgumentsSchemaV2
  "Type": <numeric_type>,                       // 1=Process, 2=ProcessOrchestration, 4=Agent, 6=Api
  "TargetRuntime": null,
  "ContentRoot": null,
  "DataVariation": null,
  "Id": <Id>
}]
```

### Package declaration

**Path:** `resources/solution_folder/package/<PackageName>.json`

Declares the package for the external process. The `<PackageName>` is the `ProcessKey` from `uip or processes list` (e.g., `MyProcess.process.MyProcess`).

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<PackageName>",
    "kind": "package",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [],
    "runtimeDependencies": [],
    "files": [
      {
        "name": "<PackageName>.<Version>.nupkg",
        "kind": "Package",
        "version": "<Version>",
        "url": "<orchBase>/odata/Processes/UiPath.Server.Configuration.OData.DownloadPackage(key='<URL_ENCODED_PACKAGE_KEY>')",
        "key": "<PackageName>_<Version_underscores>"   // Dots replaced with underscores: "MyProcess.process.MyProcess_1_0_0"
      }
    ],
    "folders": [
      {
        "fullyQualifiedName": "solution_folder"
      }
    ],
    "spec": {
      "fileName": "<PackageName>.<Version>.nupkg",
      "fileReference": "<PackageName>_<Version_underscores>",  // Same as files[0].key
      "name": "<PackageName>",
      "description": null
    },
    "locks": [],
    "key": "<PackageName>:<Version>"       // e.g., "MyProcess.process.MyProcess:1.0.0" (colon separator)
  }
}
```

**URL construction:**
- `<orchBase>` = `${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_`
- `<URL_ENCODED_PACKAGE_KEY>` = URL-encode `<PackageName>:<Version>` (e.g., `MyProcess.process.MyProcess%3A1.0.0`)
- `<Version_underscores>` = version with dots replaced by underscores (e.g., `1.0.0` → `1_0_0`)
- **Solution-feed packages:** If the external tool was deployed from a solution (its `FeedId` from the Releases API differs from the tenant-level feed), append `?feedId=<FEED_ID>` to the download URL. This applies to **all** process types (agents, API workflows, agentic processes, RPA), not just agents. Without this, Studio Web reports "Resource '...' is missing in this environment."

### How to get the values

**SECURITY: Never read `~/.uipath/.auth` directly** — the access token must not appear in Claude's context. Always use a `bash -c` wrapper that sources the auth file and makes the API call in a single shell invocation, so Claude only sees the API response.

**Step 1: Discover the folder**

```bash
uip or folders list --output json
```

Returns `ID` (numeric, used as `X-UIPATH-OrganizationUnitId` header), `Key` (GUID, used in `debug_overwrites.json`), `Path` (FullyQualifiedName). Note the parent folder's Key if the folder is nested.

**Step 2: Query `/odata/Releases` for release metadata and type**

Use a shell wrapper to query the Releases API — this keeps the access token inside the shell:

```bash
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Releases?\$filter=ProcessKey%20eq%20'\''<PROCESS_KEY>'\''&\$top=1&\$select=Key,Name,ProcessKey,ProcessVersion,ProcessType,FeedId,TargetRuntime,Description,Arguments,Id" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>"'
```

Returns:
- `Key` → release Key (GUID) — used as `referenceKey` in agent resource and `key` in process declaration
- `ProcessVersion` → package version
- `ProcessType` → determines the tool type: `"Process"` (RPA), `"Agent"`, `"Api"`, `"ProcessOrchestration"` — maps to agent resource `type` and process declaration directory
- `FeedId` → package feed ID — needed for `GetPackageEntryPointsV2` query (Step 3)
- `TargetRuntime` → `"pythonAgent"` for agents, `null` for others — used in agent process declarations
- `Arguments.Input` → raw .NET type array string (only populated for RPA processes, `null` for others) — used as `inputArgumentsSchema` in RPA process declarations
- `Arguments.Output` → raw .NET type array string (only populated for RPA processes, `null` for others) — used as `outputArgumentsSchema` in RPA process declarations

**Step 3: Query `GetPackageEntryPointsV2` for schemas and entry point data**

This API returns JSON Schema format input/output arguments and entry point metadata. It works for **all 4 process types**.

```bash
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.GetPackageEntryPointsV2(key='\''<PROCESS_KEY>:<VERSION>'\'')?feedId=<FEED_ID>" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>"'
```

- `<PROCESS_KEY>:<VERSION>` — e.g., `TestRPA.process.TestRPA:1.0.0` (from Step 2: `ProcessKey` + `ProcessVersion`)
- `feedId` — from Step 2 `FeedId`. Always pass it; required for agents published via solution feeds.

Returns (array — take the first entry):
- `UniqueId` → `entryPointUniqueId` in process declaration (non-RPA types)
- `Path` → `entryPointName` in process declaration (non-RPA types)
- `InputArguments` → JSON Schema string — use for agent-level `inputSchema` (parse the JSON) and `inputArgumentsSchemaV2` in process declaration (non-RPA types)
- `OutputArguments` → JSON Schema string — use for agent-level `outputSchema` (parse the JSON) and `outputArgumentsSchemaV2` in process declaration (non-RPA types)
- `Type` → numeric entry point type (1=Process, 2=ProcessOrchestration, 4=Agent, 6=Api) — used in `entryPoints` serialized array
- `Id` → entry point ID — used in `entryPoints` serialized array

**Step 4: Build agent-level inputSchema/outputSchema**

Parse the `InputArguments`/`OutputArguments` JSON Schema strings from Step 3 and use them directly as the `inputSchema`/`outputSchema` in the agent-level `resource.json`. This works for all 4 types.

**Fallback for RPA only:** If `GetPackageEntryPointsV2` is unavailable, parse `Arguments.Input`/`Arguments.Output` from Step 2 using this .NET type mapping:

| .NET Type | JSON Schema Type |
|-----------|-----------------|
| `System.String` | `"string"` |
| `System.Int32`, `System.Int64`, `System.Decimal`, `System.Double` | `"number"` |
| `System.Boolean` | `"boolean"` |
| Unknown | `"string"` (default) |

Extract the short type name: split by `,` → take first part → split by `.` → take last part. Example: `"System.String, System.Private.CoreLib, ..."` → `"String"` → `"string"`.

**Step 5: Extract userId from JWT**

Decode the JWT access token payload (base64) and read the `sub` claim. This is the userId for `debug_overwrites.json`.

### debug_overwrites.json

**Path:** `userProfile/<userId>/debug_overwrites.json`

Maps `solution_folder` to the actual Orchestrator folder so Studio Web can resolve external tool references during import and debugging. **Required for external tools** — without this file, Studio Web will show "resource is missing in this environment".

```jsonc
{
  "docVersion": "1.0.0",
  "tenants": [
    {
      "tenantKey": "<UIPATH_TENANT_ID>",   // From ~/.uipath/.auth
      "resources": [
        {
          "solutionResourceKey": "<release-key-guid>",  // Same as referenceKey in agent resource
          "reprovisioningIndex": 0,
          "overwrite": {
            "resourceKey": "<release-key-guid>",
            "resourceName": "<ToolName>",
            "folderKey": "<folder-key-guid>",            // Key from uip or folders list
            "folderFullyQualifiedName": "<folder-path>", // Path from uip or folders list (e.g., "Shared/MyFolder")
            "folderPath": "<parent-key>.<folder-key>",   // If folder has parent: "parentKey.folderKey". If no parent: just "folderKey"
            "type": "Reference",
            "kind": "process"
          }
        }
      ]
    }
  ]
}
```

**Multiple external tools:** Add one entry per tool to the `resources` array. If a resource with the same `solutionResourceKey` already exists, replace it.

## Auto-Generated Files (do not edit)

| File | Managed By |
|------|------------|
| `flow-layout.json` | Studio Web |
| `.agent-builder/*` | Generated by `uip agent validate` and Studio Web — do not edit by hand |
