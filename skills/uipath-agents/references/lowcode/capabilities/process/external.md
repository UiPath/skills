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

Two `uip` calls — identity from `resource list`, full configuration from `resource get`.

### 1. Find the process

```bash
uip solution resource list --kind Process --source remote --search "<NAME>" --output json
```

Response wrapper: `{Result, Code: "ResourceList", Data: [...]}` — parse `.Data[]`.

Per entry:

| Field | Use as |
|-------|--------|
| `Key` | Release Key GUID. Used as `referenceKey` in the agent resource and as the argument to step 2. |
| `Name` | Process display name → `properties.processName` and binding `name`. |
| `Type` | Lowercase. Maps 1:1 to the agent resource `type`: `"process"` / `"agent"` / `"api"` / `"processOrchestration"`. |
| `Folder` | Literal Orchestrator folder (e.g. `"Shared/Sales"`) → `properties.folderPath` and binding `folderPath`. Refresh resolves RCS by `(name, folderPath)`, so this disambiguates same-named processes in different folders. |
| `FolderKey` | Folder GUID. You don't need to pass it yourself; refresh handles folder resolution. |

When the same `Name` repeats in one folder, pick by `Key`.

### 2. Get the resource configuration

```bash
uip solution resource get <KEY> --output json
```

Response wrapper: `{Result, Code: "ResourceConfiguration", Data: {...}}`. `Data` is the solution-level resource declaration.

#### `Data.spec` — process declaration

| Field | Use as |
|-------|--------|
| `name` | Display name. |
| `type` | PascalCase here (`Process` / `Agent` / `Api` / `ProcessOrchestration`); lowercase it when copying into the agent-level `resource.json`. |
| `package.name` / `package.key` | Package identity. Refresh writes the package decl from this. |
| `entryPointUniqueId` / `entryPointName` | Entry point IDs. Refresh embeds these in the solution-level decl. |
| `inputArgumentsSchemaV2` | JSON Schema string (Agent / API / Agentic). Parse → agent-level `inputSchema`. |
| `outputArgumentsSchemaV2` | JSON Schema string. Parse → agent-level `outputSchema`. |
| `inputArgumentsSchema` / `outputArgumentsSchema` | Raw .NET type arrays for RPA. Map .NET types to JSON Schema per [solution-files.md § How to Get the Values](solution-files.md#how-to-get-the-values). |
| `entryPoints` | Already-serialized JSON array string. Refresh writes it verbatim. |
| RPA-only spec: `jobPriority`, `jobRecording`, `duration`, `frequency`, `quality`, `remoteControlAccess`, `targetFrameworkValue` | Refresh copies into the RPA decl. |
| Agent-only spec: `agentMemory`, `targetRuntime`, `environmentVariables` | Refresh copies into the agent decl. |

If both V2 and raw schemas are absent, the deployed process truly has no arguments — leave the agent-level schemas as empty objects.

#### Optional: `--include-dependencies`

```bash
uip solution resource get <KEY> --include-dependencies --output json
```

Wrapper changes to `Code: "ResourceConfigurations"` with `Data.resources[]` containing the process plus each dependency (the package, `kind: "package"`).

## Tool resource.json Shape

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
  "guardrail": {
    "policies": []              // Must always be present and empty — required for backward-compatible solution loading
  },
  "properties": {
    "processName": "MyProcess",
    "folderPath": "Shared/Sales",     // External: literal Folder from `uip solution resource list`. Solution-internal: "solution_folder".
    "exampleCalls": []                // Required for external tools
  },
  "id": "<uuid>",              // Stable; generate once, never change
  "referenceKey": "<release-key-guid>", // For external: the `Key` from `uip solution resource list` (lowercase GUID). For solution-internal: leave empty, validate resolves it.
  "isEnabled": true,
  "argumentProperties": {}
}
```

Set `inputSchema` / `outputSchema` from the parsed `Data.spec.inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` strings returned by `uip solution resource get` (Step 2). For RPA processes that only expose raw .NET schemas, see the .NET → JSON Schema mapping in [solution-files.md § How to Get the Values](solution-files.md#how-to-get-the-values).

## Solution-Level Files

**Auto-generated by refresh.** After creating the agent-level `resource.json`:

1. Run `uip agent validate` — emits `bindings_v2.json` with a `resource: "process"` binding.
2. Run `uip solution resource refresh` — for each Process binding, looks up the matching release in RCS and writes:
   - `resources/solution_folder/process/<type_dir>/<ToolName>.json` (declaration)
   - `resources/solution_folder/package/<PackageName>.json` (package declaration)
   - an entry in `userProfile/<userId>/debug_overwrites.json` with real `folderKey`, `folderFullyQualifiedName`, and `folderPath` so Studio Web can resolve the process at runtime. An entry missing `folderFullyQualifiedName` or `folderPath` will cause "Could not find process for tool '<name>'" — refresh from current uipcli populates both correctly.

**Type-to-directory mapping for process declarations:**

| `Data.spec.type` (from `resource get`) | Agent resource `type` | `spec.type` | Process declaration directory |
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
uip solution resource list --kind Process --source remote --search "<NAME>" --output json
# Parse .Data[]. Each entry: Key, Name, Type (lowercase), Folder, FolderKey.
# Use Key as referenceKey, Name as processName, Type for the agent-level type,
# Folder as properties.folderPath.

# 3. Pull the full configuration
uip solution resource get <KEY> --output json
# Parse .Data.spec for:
#   inputArgumentsSchemaV2 / outputArgumentsSchemaV2  → JSON Schema strings (Agent / API / Agentic)
#   inputArgumentsSchema   / outputArgumentsSchema    → raw .NET arrays (RPA)
#   package.name / package.key, entryPointUniqueId / entryPointName
```

Then create the agent-level resource file:

**Agent-level resource** — `<AGENT_NAME>/resources/<TOOL_NAME>/resource.json`

Set `"location": "external"`, `"type"` to the lowercase `Type` from `resource list` (`"process"` / `"agent"` / `"api"` / `"processOrchestration"`), `"folderPath"` to the literal `Folder` (e.g., `"Shared/Sales"`), `"referenceKey"` to the `Key`. Set `inputSchema` / `outputSchema` from the parsed `Data.spec.inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` strings (or the .NET-mapped raw schemas for RPA). Include `"exampleCalls": []` in `properties`. See § Tool resource.json Shape above for the full template.

```bash
# 4. Configure agent.json (system prompt, model, schemas)

# 5. Validate — generates bindings_v2.json in the agent project directory
uip agent validate "<AGENT_NAME>" --output json

# 6. Refresh solution resources — resolves each Process binding against the
#    Resource Catalog Service and produces the full solution-level declaration
#    per kind: `resources/solution_folder/process/<type>/<Name>.json`,
#    `resources/solution_folder/package/<PackageName>.json`, and an entry in
#    `userProfile/<userId>/debug_overwrites.json`. No hand-authoring needed.
uip solution resource refresh --output json

# 7. Bundle + upload
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rules 11, 12, 13. Anti-pattern 7 (don't forget refresh) and Anti-pattern 8 (`resource list` is identity-only — use `resource get` for schemas) apply directly.

## References

- [process.md](process.md) — capability overview and variant decision table
- [solution-files.md](solution-files.md) — hand-authored Templates A/B + package + debug_overwrites + How to Get the Values
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
