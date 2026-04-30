# Solution-Internal Process Tool

Walkthrough for adding a tool that calls a process **inside the same solution** (another project sibling to the parent agent). Supports all 4 solution-internal process types: RPA processes, agents, API workflows, and agentic processes (process orchestration). They share discovery, schema source, and resource shape — only `type` and the auto-generated process declaration directory differ.

For Orchestrator-deployed processes outside the solution, see [external.md](external.md). The multi-agent topology (parent agent invokes a tool agent in the same solution) is the agent sub-variant of this guide — see [§ When the tool is another agent](#when-the-tool-is-another-agent).

## Sub-Variants

| `type` (resource.json) | Calls | `entry-points.json` `type` | Auto-generated process declaration directory |
|---|---|---|---|
| `process` | RPA process (XAML) | `Process` | `process/process/` |
| `agent` | Low-code / coded agent | `agent` | `process/agent/` |
| `api` | API workflow | `Api` | `process/api/` |
| `processOrchestration` | Agentic process / process orchestration | `ProcessOrchestration` | `process/processOrchestration/` |

`entry-points.json` `type` casing is mixed across project kinds (`Process`, `agent`, `Api`, `ProcessOrchestration`). Match it case-sensitive when reading.

## Discovery

### 1. List solution-internal processes

```bash
uip solution resource list --kind Process --source local --output json
```

Run from the solution root. Each entry returns:

| Field | Use as |
|-------|--------|
| `Key` | release Key (GUID) — used as `referenceKey` in the agent resource. Matches the top-level `resource.key` in the auto-generated `resources/solution_folder/process/<type_dir>/<Name>.json`. |
| `Name` | project folder name — used as the tool `name` and `processName`. |
| `Type` | maps 1:1 to the agent resource `type`: `"process"` / `"agent"` / `"api"` / `"processOrchestration"`. |
| `Folder` | always `"solution_folder"` for source `Local` — used as `folderPath`. |
| `Source` | `"Local"` for solution-internal processes. |

The local listing reads `SolutionStorage.json` plus each project's `entry-points.json` and `project.uiproj`. There is no Orchestrator API call — discovery is fully offline.

### 2. Read the schema from `entry-points.json`

Every solution project has an `entry-points.json` at its root. The schemas live directly on the entry point — no Orchestrator API, no JWT, no curl.

```bash
cat "<ProjectName>/entry-points.json"
```

Take `entryPoints[0].input` and `entryPoints[0].output` and use them as `inputSchema` / `outputSchema` in the agent-level resource:

- For `agent`, `Api`, and `ProcessOrchestration` projects, `input` and `output` are JSON Schema objects ready to copy.
- For RPA (`Process`) projects, `input` and `output` are typically `null`. Fall back to `{ "type": "object", "properties": {} }`. To expose real arguments, declare them in the RPA project's `entry-points.json` first, then re-run discovery.

#### Example — Agent project entry-points.json

```jsonc
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    {
      "filePath": "/content/agent.json",
      "type": "agent",
      "uniqueId": "<uuid>",
      "input": { "type": "object", "properties": {} },
      "output": {
        "type": "object",
        "properties": { "content": { "type": "string", "description": "Output content" } }
      }
    }
  ]
}
```

#### Example — RPA project entry-points.json (null schemas)

```jsonc
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    { "filePath": "Main.xaml", "uniqueId": "<uuid>", "type": "Process", "input": null, "output": null }
  ]
}
```

## Agent-Level Resource Shape

**Path:** `<AGENT_NAME>/resources/<ToolName>/resource.json`

```jsonc
{
  "$resourceType": "tool",
  "name": "MyTool",
  "description": "What this tool does (shown to LLM for tool selection)",
  "location": "solution",
  "type": "process",           // "process" | "agent" | "api" | "processOrchestration"
  "inputSchema": {             // copy from entry-points.json entryPoints[0].input (empty object if null)
    "type": "object",
    "properties": {}
  },
  "outputSchema": {            // copy from entry-points.json entryPoints[0].output (empty object if null)
    "type": "object",
    "properties": {}
  },
  "settings": {},
  "properties": {
    "processName": "MyTool",          // project folder name (matches Name from resource list)
    "folderPath": "solution_folder"   // always "solution_folder" for solution-internal tools
  },
  "guardrail": {
    "policies": []              // Auto-populated by `uip agent validate` from root-level guardrails. Do not edit manually. See ../guardrails/guardrails.md.
  },
  "id": "<uuid>",              // Stable; generate once, never change
  "referenceKey": "<release-key-guid>", // Key from `uip solution resource list --source local`. For the agent sub-variant, an empty string `""` is also accepted — validate resolves it by name.
  "isEnabled": true,
  "argumentProperties": {}
}
```

Differences from the [external](external.md) shape:

- `location` is `"solution"` (not `"external"`).
- No `exampleCalls` in `properties` — only external tools require it.
- Schema source is `entry-points.json` (not `GetPackageEntryPointsV2`).
- No `userProfile/<userId>/debug_overwrites.json` is required — `solution_folder` resolves locally.

## Solution-Level Files

**Auto-generated.** When the sibling project is registered with the solution (`uip solution project add` for new projects, `uip solution resource refresh` after editing), the solution-level files are written under `resources/solution_folder/`:

| Sub-variant | Auto-generated files |
|---|---|
| `process` (RPA) | `process/process/<Name>.json` + `package/<Name>.json` |
| `agent` | `process/agent/<Name>.json` + `package/<Name>.json` |
| `api` | `process/api/<Name>.json` + `package/<Name>.json` |
| `processOrchestration` | `process/processOrchestration/<Name>.json` + `package/<Name>.json` |

Do NOT hand-author these. `uip agent validate` plus `uip solution resource refresh` keep them in sync. The hand-authoring fallback in [solution-files.md](solution-files.md) is for **external** tools only.

The top-level `resource.key` GUID in the generated `process/<type_dir>/<Name>.json` is what `uip solution resource list --source local` reports as `Key` and what you put in the agent resource's `referenceKey`. The match is a useful sanity check.

## Walkthrough

```bash
# 1. Scaffold solution + parent agent per
#    [project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

# 2. Add the sibling project (or scaffold a new one) and register it with the solution.
#    Examples:
uip agent init "MyToolAgent" --output json && uip solution project add "MyToolAgent" --output json
# Or for an existing RPA / API / agentic project, just register it:
uip solution project add "<ProjectName>" --output json

# 3. Discover solution-internal processes.
uip solution resource list --kind Process --source local --output json
#   Key       → referenceKey for the agent resource
#   Name      → tool name + processName
#   Type      → agent resource `type` (process | agent | api | processOrchestration)
#   Folder    → folderPath ("solution_folder")

# 4. Read schemas from the sibling project's entry-points.json.
cat "<ProjectName>/entry-points.json"
#   entryPoints[0].input  → inputSchema
#   entryPoints[0].output → outputSchema
#   When null (typical for RPA), use { "type": "object", "properties": {} }.

# 5. Author the agent-level resource:
#    <ParentAgent>/resources/<ToolName>/resource.json
#    Set: location: "solution", type: <Type from step 3>, processName: <Name>,
#         folderPath: "solution_folder", referenceKey: <Key from step 3>,
#         inputSchema/outputSchema from step 4. See § Agent-Level Resource Shape.

# 6. Configure the parent agent.json (system prompt, model, schemas).

# 7. Validate — generates bindings_v2.json in the parent agent's project.
uip agent validate "<ParentAgent>" --output json

# 8. Refresh solution resources — keeps the auto-generated solution-level files
#    aligned with the resource list. Re-run after any sibling project edit.
uip solution resource refresh --output json

# 9. Bundle + upload.
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SolutionName>.uis --output json
```

## When the tool is another agent

The agent sub-variant is also the building block of the **multi-agent solution topology**: a parent agent that orchestrates one or more tool agents shipped together. The flow above already covers it — `type: "agent"`, `location: "solution"`, schemas copied from the tool agent's `entry-points.json`. Two extras worth knowing:

### Empty `referenceKey` for the agent sub-variant

For `type: "agent"` only, leaving `referenceKey: ""` is supported — `uip agent validate` resolves it by name from `resources/solution_folder/process/agent/<Name>.json` and writes the GUID back to disk. Populating it explicitly from `uip solution resource list --source local` works for all four sub-variants and is the symmetric path.

### Generated `bindings_v2.json` (by validate)

After validate, the parent agent's `.agent-builder/bindings.json` carries the binding for each agent-typed tool:

```jsonc
{
  "resource": "process",
  "key": "<ToolAgentName>",
  "value": {
    "name": { "defaultValue": "<ToolAgentName>", "isExpression": false, "displayName": "Process name" }
  },
  "metadata": {
    "subType": "agent",
    "bindingsVersion": "2.2",
    "solutionsSupport": "true"
  }
}
```

`subType` reflects the sub-variant (`process` / `agent` / `api` / `processOrchestration`).

### UUID cross-references in multi-agent solutions

The UUID chain (`SolutionStorage.json.Projects[].ProjectId` ↔ `package/<Name>.json.projectKey` ↔ `process/<type_dir>/<Name>.json.projectKey`) is the same one documented in [../../solution-resources.md](../../solution-resources.md) § UUID Cross-References. Auto-managed by `uip solution project add` and `uip agent validate` — do not hand-edit. Critical Rule 9 (don't modify `projectId`) is especially important here.

## Anti-Patterns

1. **Don't hand-author `resources/solution_folder/process/<type_dir>/<Name>.json` or `resources/solution_folder/package/<Name>.json` for solution-internal tools.** They are auto-generated. The hand-authoring templates in [solution-files.md](solution-files.md) are for external tools only.
2. **Don't query `/odata/Releases` or `GetPackageEntryPointsV2` for solution-internal schemas.** The sibling project's `entry-points.json` is the source of truth.
3. **Don't write a `userProfile/<userId>/debug_overwrites.json` for solution-internal tools.** `solution_folder` resolves locally; no folder remap is needed.
4. **Don't copy schemas from the tool's `agent.json` if `entry-points.json` and `agent.json` have drifted.** `entry-points.json` is the binding contract — fix the drift in the sibling project (run `uip agent validate <ProjectName>`) before reading.

## Gotchas

See [../../critical-rules.md](../../critical-rules.md) Critical Rules 11, 12. Anti-pattern 7 (don't forget refresh) applies; Anti-pattern 8 (Releases + GetPackageEntryPointsV2) is **external-only** — solution-internal uses `entry-points.json`.

## References

- [process.md](process.md) — capability overview and variant decision table
- [external.md](external.md) — Orchestrator-deployed counterpart (4 variants)
- [solution-files.md](solution-files.md) — hand-authoring fallback for external tools (not used for solution-internal)
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics, § UUID Cross-References
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
