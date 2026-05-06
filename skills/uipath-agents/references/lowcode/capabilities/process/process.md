# Process Tool Capability

Tools that call a runnable process — RPA workflows, agents, API workflows, or agentic processes (process orchestration). All process tools share the `$resourceType: "tool"` envelope; the `type` field selects the subtype.

For Integration Service connector tools (separate capability), see [../integration-service/integration-service.md](../integration-service/integration-service.md).

## When to Use

- Agent needs to invoke an RPA process, another agent, an API workflow, or an agentic process
- Target lives in the **same solution** (`Source: "Local"` from discovery) or is **already deployed in Orchestrator** (`Source: "Remote"`)

## Subtypes

| `type` (resource.json) | Calls | Process declaration directory | Schema flavor |
|---|---|---|---|
| `process` | RPA process (XAML) | `process/process/` | Raw .NET — `inputArgumentsSchema` / `outputArgumentsSchema` |
| `agent` | Low-code / coded agent | `process/agent/` | JSON Schema — `inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` |
| `api` | API workflow | `process/api/` | JSON Schema — V2 fields |
| `processOrchestration` | Agentic process / process orchestration | `process/processOrchestration/` | JSON Schema — V2 fields |

**Local and external resources follow the same flow.** Discovery, `resource.json` shape, validation, and refresh are identical. The only difference is the `location` value written into `resource.json`: `"solution"` for local (in-solution) resources, `"external"` for resources already deployed in Orchestrator.

## Discovery

Two `uip` calls — identity from `resource list`, full configuration from `resource get`.

### 1. Find the process

Two supported invocations — pick one based on where you're looking:

**Local (in-solution):**

```bash
uip solution resource list --source local --output json
```

**Remote (Orchestrator / RCS):**

```bash
uip solution resource list --source remote --kind Process --search "<NAME>" --output json
```

> **`--kind` and `--search` only work with `--source remote`.** With `--source local` or `--source all` (default), both flags must be omitted — list everything and filter `.Data[]` client-side by `Kind` and `Name`.

Response wrapper: `{Result, Code: "ResourceList", Data: [...]}` — parse `.Data[]`.

`--source` selects where the resource lives:

- `local` — resources already in the solution. No `--kind` / `--search`.
- `remote` — only Orchestrator / RCS. Supports `--kind` / `--search`.
- `all` (default) — both local and remote. No `--kind` / `--search`.

The row's `Source` field (`"Local"` or `"Remote"`) determines the `location` value for `resource.json`.

Per entry:

| Field | Use as |
|-------|--------|
| `Source` | `"Local"` → `location: "solution"`. `"Remote"` → `location: "external"`. |
| `Key` | Release Key GUID. Used as `referenceKey` in the agent resource and as the argument to step 2. |
| `Name` | Process display name → `properties.processName` and binding `name`. |
| `Type` | Lowercase. Maps 1:1 to the agent resource `type`: `"process"` / `"agent"` / `"api"` / `"processOrchestration"`. |
| `Folder` | Literal folder path → `properties.folderPath` and binding `folderPath`. Local resources typically return `"solution_folder"` (their declared folder in the solution); external resources return the literal Orchestrator folder (e.g., `"Shared/Sales"`). Refresh resolves RCS by `(name, folderPath)`, so this disambiguates same-named processes. |
| `FolderKey` | Folder GUID. Refresh handles folder resolution; you don't pass it yourself. |

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
  "location": "external",       // "solution" if Source: "Local", "external" if Source: "Remote"
  "type": "process",            // "process" | "agent" | "api" | "processOrchestration"
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
    "folderPath": "Shared/Sales",     // Literal Folder from `resource list`. Local: typically "solution_folder". External: literal Orchestrator folder.
    "exampleCalls": []                // Required
  },
  "id": "<uuid>",               // Stable; generate once, never change
  "referenceKey": "<release-key-guid>", // Lowercase `Key` GUID from `resource list`
  "isEnabled": true,
  "argumentProperties": {}
}
```

**Only `location` differs between local and external tools.** All other fields follow the same rules:

| Field | Source | Same rule for local & external |
|---|---|---|
| `type` | lowercase `Type` from `resource list` | yes |
| `referenceKey` | lowercase `Key` GUID from `resource list` | yes |
| `properties.folderPath` | literal `Folder` from `resource list` | yes |
| `properties.exampleCalls` | required (can be `[]`) | yes |
| `inputSchema` / `outputSchema` | parsed from `Data.spec.inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` (or .NET-mapped raw schemas for RPA) | yes |

## Solution-Level Files

**Auto-generated by `uip agent validate` + `uip solution resource refresh`.** After creating the agent-level `resource.json`:

1. Run `uip agent validate` — emits `bindings_v2.json` with a `resource: "process"` binding.
2. Run `uip solution resource refresh` — for each Process binding, looks up the matching resource (in RCS for remote, in the solution for local) and writes:
   - `resources/solution_folder/process/<type_dir>/<ToolName>.json` (declaration)
   - `resources/solution_folder/package/<PackageName>.json` (package declaration)
   - an entry in `userProfile/<userId>/debug_overwrites.json` with real `folderKey`, `folderFullyQualifiedName`, and `folderPath` so Studio Web can resolve the process at runtime. An entry missing `folderFullyQualifiedName` or `folderPath` will cause "Could not find process for tool '<name>'" — refresh from current uipcli populates both correctly.

For in-solution agents already registered with `uip solution project add`, the package + process declarations are pre-existing; refresh resolves the binding against them.

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

# 2. Discover the process
# Remote: --kind / --search supported server-side.
uip solution resource list --source remote --kind Process --search "<NAME>" --output json
# Local: --kind and --search NOT supported — list, then filter .Data[] client-side.
uip solution resource list --source local --output json
# Parse .Data[]. Each entry: Source, Key, Name, Kind, Type (lowercase), Folder, FolderKey.
# Source: "Local" → location: "solution". "Remote" → location: "external".
# Use Key as referenceKey, Name as processName, Type for the agent-level type,
# Folder as properties.folderPath.

# 3. Pull the full configuration
uip solution resource get <KEY> --output json
# Parse .Data.spec for:
#   inputArgumentsSchemaV2 / outputArgumentsSchemaV2  → JSON Schema strings (Agent / API / Agentic)
#   inputArgumentsSchema   / outputArgumentsSchema    → raw .NET arrays (RPA)
#   package.name / package.key, entryPointUniqueId / entryPointName
```

Then create the agent-level resource file at `<AGENT_NAME>/resources/<TOOL_NAME>/resource.json` per § Tool resource.json Shape. Set `location` from the row's `Source`, `type` from `Type` (lowercase), `folderPath` from `Folder`, `referenceKey` from `Key`, schemas from `Data.spec.inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` (or raw .NET arrays for RPA).

```bash
# 4. Configure agent.json (system prompt, model, schemas)

# 5. Validate — generates bindings_v2.json in the agent project directory
uip agent validate "<AGENT_NAME>" --output json

# 6. Refresh solution resources — resolves each Process binding and produces
#    `resources/solution_folder/process/<type>/<Name>.json`,
#    `resources/solution_folder/package/<PackageName>.json`, and an entry in
#    `userProfile/<userId>/debug_overwrites.json`. No hand-authoring needed.
uip solution resource refresh --output json

# 7. Bundle + upload
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

## Multi-Agent Solution Example

When two agent projects in the same solution call each other (parent-tool topology), use the unified flow with a `--source local` discovery:

```bash
# 1. Scaffold the solution per project-lifecycle.md.
# 2. Add a second agent and register it as a solution project:
uip agent init "ToolAgent" --output json
uip solution project add "ToolAgent" --output json
# This creates resources/solution_folder/package/ToolAgent.json and
# resources/solution_folder/process/agent/ToolAgent.json automatically.

# 3. From ParentAgent, add ToolAgent as a tool — discovery via the unified flow.
# `--source local` accepts neither --kind nor --search; list then filter client-side.
uip solution resource list --source local --output json
# Pick the row with Kind="Process" and Name="ToolAgent", then:
uip solution resource get <KEY> --output json
# Then create ParentAgent/resources/ToolAgent/resource.json with location: "solution".

# 4. Validate both agents and bundle/upload as usual.
uip agent validate ParentAgent --output json
uip agent validate ToolAgent --output json
```

UUID cross-references between `SolutionStorage.Projects[].ProjectId`, `package/<ToolAgent>.json.projectKey`, and `process/agent/<ToolAgent>.json.projectKey` are auto-managed by `uip solution project add` and `uip agent validate` — do not hand-edit. See [../../solution-resources.md](../../solution-resources.md) § UUID Cross-References.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rules 11, 12, 13. Anti-patterns 7, 8, 19 also apply.

## References

- [solution-files.md](solution-files.md) — hand-authored Templates A/B + package + debug_overwrites + How to Get the Values
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics, § UUID Cross-References
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
- [../../agent-definition.md](../../agent-definition.md) § Resources Convention
