# External Orchestrator Process Tool

Walkthrough for adding a tool that calls a process **already deployed in Orchestrator** (outside the current solution). Supports all 4 external process types: RPA processes, agents, API workflows, and agentic processes (process orchestration). They share discovery, refresh flow, and resource shape — only `type`, the process declaration directory, and the schema-field flavor (raw .NET vs JSON Schema V2) differ.

For solution-internal agents (another project in the **same** solution), see [solution-agent.md](solution-agent.md).

## Sub-Variants

| `type` (resource.json) | Calls | Process declaration directory | Schema field flavor |
|---|---|---|---|
| `process` | RPA process (XAML) | `process/process/` | Raw .NET — `inputArgumentsSchema` / `outputArgumentsSchema` |
| `agent` | Low-code / coded agent | `process/agent/` | JSON Schema — `inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` |
| `api` | API workflow | `process/api/` | JSON Schema — V2 fields |
| `processOrchestration` | Agentic process / process orchestration | `process/processOrchestration/` | JSON Schema — V2 fields |

## Discovery

### 1. Find the process

```bash
uip solution resource list --kind Process --source remote --search "<TOOL_NAME>" --output json
```

Each entry returns:

| Field | Use as |
|-------|--------|
| `Key` | release Key (GUID) — used as `referenceKey` in the agent resource |
| `Name` | process display name. Refresh resolves processes by name only, so pick a name that is unique in the tenant; when multiple processes share a name across folders, refresh imports the first RCS match. |
| `Type` | maps 1:1 to the agent resource `type`: `"process"` / `"agent"` / `"api"` / `"processOrchestration"`. `"webApp"` entries are not runnable process tools — use the [escalation capability](../escalation/escalation.md) instead. |
| `Folder` | fully-qualified folder path |
| `FolderKey` | folder GUID — use as `X-UIPATH-FolderKey` header in steps 2-3 |

### 2. Get ProcessKey + ProcessVersion + FeedId via Releases API

> **SECURITY:** Never read `~/.uipath/.auth` directly — keep the token inside the shell. Always use a `bash -c` wrapper that sources the auth file and makes the API call in a single shell invocation, so Claude only sees the API response.

```bash
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Releases?\$filter=ProcessKey%20eq%20'\''<PROCESS_KEY>'\''&\$top=1&\$select=Key,Name,ProcessKey,ProcessVersion,ProcessType,FeedId,TargetRuntime,Description,Arguments,Id" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-FolderKey: <FOLDER_KEY_GUID>"'
```

Orchestrator's OData rejects `Key eq <guid>` (Edm.Guid mismatch); filter by the string `ProcessKey` or by `Name` instead. Use the `Key` value from `resource list` only as the `referenceKey` in the agent resource and `key` in the process declaration — not as an OData filter.

Extract from response:
- `ProcessKey` / `ProcessVersion` → build `"<ProcessKey>:<Version>"` package key for step 3
- `FeedId` → required for `GetPackageEntryPointsV2` query (step 3)
- `Arguments.Input` / `Arguments.Output` → raw .NET type arrays (only for RPA, `null` for others)

For full extraction logic and field mapping, see [solution-files.md](solution-files.md) § How to Get the Values.

### 3. Get argument schemas via `GetPackageEntryPointsV2`

```bash
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.GetPackageEntryPointsV2(key='\''<PROCESS_KEY>:<VERSION>'\'')?feedId=<FEED_ID>" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-FolderKey: <FOLDER_KEY_GUID>"'
```

JSON Schema `InputArguments`/`OutputArguments` work for all 4 types. Parse them for the agent-level `inputSchema`/`outputSchema`.

Extract from response (take first entry):
- `InputArguments` → JSON Schema string → agent-level `inputSchema` (parse JSON)
- `OutputArguments` → JSON Schema string → agent-level `outputSchema` (parse JSON)

## Agent-Level Resource Shape

**Path:** `<AGENT_NAME>/resources/{ToolName}/resource.json`

```jsonc
{
  "$resourceType": "tool",
  "name": "MyProcess",
  "description": "What this tool does (shown to LLM for tool selection)",
  "location": "external",
  "type": "process",           // "process" | "agent" | "api" | "processOrchestration"
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

Set `inputSchema`/`outputSchema` from the parsed `GetPackageEntryPointsV2` JSON Schema strings (Step 3).

Note: MCP (Model Context Protocol) server resources use `$resourceType: "mcp"` — a separate resource type, not a `type` value inside a tool resource. End-to-end MCP authoring is not yet documented in this skill.

## Solution-Level Files

**Auto-generated by refresh.** After creating the agent-level `resource.json`:

1. Run `uip agent validate` — emits `bindings_v2.json` with a `resource: "process"` binding.
2. Run `uip solution resource refresh` — for each Process binding, looks up the matching release in RCS and writes:
   - `resources/solution_folder/process/<type_dir>/<ToolName>.json` (declaration)
   - `resources/solution_folder/package/<PackageName>.json` (package declaration)
   - an entry in `userProfile/<userId>/debug_overwrites.json` with real `folderKey`, `folderFullyQualifiedName`, and `folderPath` so Studio Web can resolve the process at runtime. An entry missing `folderFullyQualifiedName` or `folderPath` will cause "Could not find process for tool '<name>'" — refresh from current uipcli populates both correctly.

**Type-to-directory mapping for process declarations:**

| `ProcessType` (from Releases API) | Agent resource `type` | `spec.type` | Process declaration directory |
|---|---|---|---|
| `Process` | `process` | `Process` | `process/process/` |
| `Agent` | `agent` | `Agent` | `process/agent/` |
| `Api` | `api` | `Api` | `process/api/` |
| `ProcessOrchestration` | `processOrchestration` | `ProcessOrchestration` | `process/processOrchestration/` |

**Hand-authoring fallback** — when refresh cannot run (offline, missing RCS match, custom deployment), see [solution-files.md](solution-files.md) for the full Templates A (RPA) and B (Agent / API / Agentic), package declaration, and debug_overwrites templates.

## Walkthrough

```bash
# 1. Scaffold solution + agent per [project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

# 2. Discover the process via the Resource Catalog Service
uip solution resource list --kind Process --source remote --search "<TOOL_NAME>" --output json
# Each entry returns:
#   Key       → release Key (GUID) — used as referenceKey in the agent resource
#   Name      → process display name. Refresh resolves processes by name only,
#               so pick a name that is unique in the tenant; when multiple
#               processes share a name across folders, refresh imports the
#               first RCS match.
#   Type      → maps 1:1 to the agent resource type:
#                  "process" → RPA (XAML)
#                  "agent" → low-code / coded agent
#                  "api" → API workflow
#                  "processOrchestration" → agentic process
#                  "webApp" → skip; use the escalation capability (App kind)
#   Folder    → fully-qualified folder path
#   FolderKey → folder GUID — use as X-UIPATH-FolderKey header in steps 3-4

# 3. Query Releases API for ProcessKey, ProcessVersion, FeedId, and raw .NET arg schemas (RPA only)
# SECURITY: Never read ~/.uipath/.auth directly — keep the token inside the shell.
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Releases?\$filter=ProcessKey%20eq%20'\''<PROCESS_KEY>'\''&\$top=1&\$select=Key,Name,ProcessKey,ProcessVersion,ProcessType,FeedId,TargetRuntime,Description,Arguments,Id" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-FolderKey: <FOLDER_KEY_GUID>"'
# Orchestrator's OData rejects `Key eq <guid>` (Edm.Guid mismatch); filter
# by the string ProcessKey or by Name instead.
# Extract from response:
#   ProcessKey/ProcessVersion → build "<ProcessKey>:<Version>" key for step 4
#   FeedId                    → needed for GetPackageEntryPointsV2 query (step 4)
#   Arguments.Input/Output    → raw .NET type arrays (only for RPA, null for others)

# 4. Query GetPackageEntryPointsV2 for JSON Schema arguments and entry point data
bash -c 'source <(grep = ~/.uipath/.auth) && curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.GetPackageEntryPointsV2(key='\''<PROCESS_KEY>:<VERSION>'\'')?feedId=<FEED_ID>" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-FolderKey: <FOLDER_KEY_GUID>"'
# Extract from response (take first entry):
#   InputArguments  → JSON Schema string → agent-level inputSchema (parse JSON)
#   OutputArguments → JSON Schema string → agent-level outputSchema (parse JSON)
```

Then create the agent-level resource file:

**Agent-level resource** — `<AGENT_NAME>/resources/<TOOL_NAME>/resource.json`

Set `"location": "external"`, `"type"` directly from `resource list`'s `Type` field (`"process"`, `"agent"`, `"api"`, or `"processOrchestration"`), `"folderPath": "solution_folder"`, `"referenceKey"` to the release Key. Set `inputSchema`/`outputSchema` from the parsed `GetPackageEntryPointsV2` JSON Schema strings. Include `"exampleCalls": []` in `properties`. See § Agent-Level Resource Shape above for the full template.

```bash
# 5. Configure agent.json (system prompt, model, schemas)

# 6. Validate — generates bindings_v2.json in the agent project directory
uip agent validate "<AGENT_NAME>" --output json

# 7. Refresh solution resources — resolves each Process binding against the
#    Resource Catalog Service and produces the full solution-level declaration
#    per kind: `resources/solution_folder/process/<type>/<Name>.json`,
#    `resources/solution_folder/package/<PackageName>.json`, and an entry in
#    `userProfile/<userId>/debug_overwrites.json`. No hand-authoring needed.
uip solution resource refresh --output json

# 8. Bundle + upload
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rules 11, 12, 13. Anti-pattern 7 (don't forget refresh) and Anti-pattern 8 (use Releases + GetPackageEntryPointsV2) apply directly.

## References

- [process.md](process.md) — capability overview and variant decision table
- [solution-files.md](solution-files.md) — hand-authored Templates A/B + package + debug_overwrites + How to Get the Values
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
