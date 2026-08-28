# Process Tool Capability

Tools that call runnable processes—RPA workflows, agents, API workflows, or agentic processes. All use the `$resourceType: "tool"` envelope; `type` selects the subtype.

For Integration Service connector tools, see [../integration-service/integration-service.md](../integration-service/integration-service.md). For built-in tools such as `analyze-attachments`, see [../built-in-tools/built-in-tools.md](../built-in-tools/built-in-tools.md); these use `type: "internal"` and require no solution-level files.

## When to Use

Use this capability when an agent invokes an RPA process, another agent, an API workflow, or an agentic process in the same solution (`Source: "Local"`) or deployed in Orchestrator (`Source: "Remote"`). Both use the same discovery, declaration, validation, and refresh flow; only `resource.json.location` differs: `"solution"` for local and `"external"` for remote.

## Subtypes

| `resource.json` `type` | Calls | Declaration directory | Schema fields |
|---|---|---|---|
| `process` | RPA process (XAML) | `process/process/` | Raw .NET: `inputArgumentsSchema` / `outputArgumentsSchema` |
| `agent` | Low-code autonomous or coded agent | `process/agent/` | JSON Schema: `inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` |
| `api` | API workflow | `process/api/` | JSON Schema V2 fields |
| `processOrchestration` | Agentic process / process orchestration | `process/processOrchestration/` | JSON Schema V2 fields |

## Discovery

Use two `uip` calls: obtain identity with `resource list`, then configuration with `resource get`.

For local resources, run:

```bash
uip solution resources list --source local --output json
```

For remote Orchestrator/RCS resources, run:

```bash
uip solution resources list --source remote --kind Process --search "<NAME>" --output json
```

`--kind` and `--search` work only with `--source remote`. With `--source local` or `--source all` (the default), omit both flags, list everything, and filter `.Data[]` client-side by `Kind` and `Name`. The response is `{Result, Code: "ResourceList", Data: [...]}`; parse `.Data[]`.

`--source` values:

- `local`: solution resources; no `--kind` or `--search`.
- `remote`: Orchestrator/RCS resources; supports `--kind` and `--search`.
- `all`: local and remote; no `--kind` or `--search`.

Map results as follows:

| Result field | Use |
|---|---|
| `Source` | `"Local"` → `location: "solution"`; `"Remote"` → `location: "external"`. |
| `Key` | Release Key GUID; lowercase it as `referenceKey` and pass it to `resource get`. |
| `Name` | Display name; use as `properties.processName` and binding `name`. |
| `Type` | Lowercase; maps 1:1 to `process`, `agent`, `api`, or `processOrchestration`. |
| `Folder` | Literal folder path; use as `properties.folderPath` and binding `folderPath`. Local resources typically return `solution_folder`; remote resources return the literal Orchestrator folder. Refresh resolves RCS by `(name, folderPath)`, disambiguating same-named processes. |
| `FolderKey` | Folder GUID; refresh resolves it, so do not pass it yourself. |

When a name repeats in one folder, select by `Key`.

Run:

```bash
uip solution resources get <KEY> --output json
```

The response is `{Result, Code: "ResourceConfiguration", Data: {...}}`; `Data` is the solution-level declaration. With dependencies, run:

```bash
uip solution resources get <KEY> --include-dependencies --output json
```

This returns `Code: "ResourceConfigurations"` and `Data.resources[]`, containing the process and each dependency, including the package with `kind: "package"`.

From `Data.spec`, use:

| Field | Use |
|---|---|
| `name` | Display name. |
| `type` | PascalCase (`Process`, `Agent`, `Api`, or `ProcessOrchestration`); lowercase it for agent-level `resource.json`. |
| `package.name` / `package.key` | Package identity; refresh writes the package declaration. |
| `entryPointUniqueId` / `entryPointName` | Entry-point IDs; refresh embeds them in the solution declaration. |
| `inputArgumentsSchemaV2` / `outputArgumentsSchemaV2` | Parse JSON Schema strings into agent-level `inputSchema` / `outputSchema` for Agent, API, and Agentic resources. |
| `inputArgumentsSchema` / `outputArgumentsSchema` | Raw .NET type arrays for RPA; map them to JSON Schema per [solution-files.md § How to Get the Values](solution-files.md#how-to-get-the-values). |
| `entryPoints` | Already-serialized JSON array string; refresh writes it verbatim. |
| RPA-only: `jobPriority`, `jobRecording`, `duration`, `frequency`, `quality`, `remoteControlAccess`, `targetFrameworkValue` | Refresh copies these into the RPA declaration. |
| Agent-only: `agentMemory`, `targetRuntime`, `environmentVariables` | Refresh copies these into the agent declaration. |

If both V2 and raw schemas are absent, use empty objects for the agent-level schemas.

## Tool `resource.json`

Create `<AGENT_NAME>/resources/{ToolName}/resource.json`:

```jsonc
{
  "$resourceType": "tool",
  "name": "MyProcess",
  "description": "What this tool does (shown to LLM for tool selection)",
  "location": "external",       // "solution" for Source: "Local"
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
    "policies": []              // Must always be present and empty
  },
  "properties": {
    "processName": "MyProcess",
    "folderPath": "Shared/Sales",     // Literal Folder; local typically "solution_folder"
    "exampleCalls": []                // Required
  },
  "id": "<uuid>",               // Stable; generate once and never change
  "referenceKey": "<release-key-guid>", // Lowercase Key GUID
  "isEnabled": true,
  "argumentProperties": {}
}
```

For local and remote resources, use lowercase `Type` for `type`, lowercase `Key` for `referenceKey`, literal `Folder` for `properties.folderPath`, parsed V2 schemas or .NET-mapped RPA schemas for `inputSchema` and `outputSchema`, and required `properties.exampleCalls` (which may be `[]`). Only `location` differs.

## Solution-Level Files and Required Flow

After creating the agent-level resource file:

1. Run `uip agent refresh` to regenerate `entry-points.json` and `bindings_v2.json` with a `resource: "process"` binding.
2. Run `uip agent validate`; it is read-only and fails with `AgentValidationOutdated` when refresh is required.
3. Run `uip solution resources refresh`; for each Process binding it resolves the resource (RCS for remote, solution for local) and writes:
   - `resources/solution_folder/process/<type_dir>/<ToolName>.json` (declaration)
   - `resources/solution_folder/package/<PackageName>.json` (package declaration)
   - an entry in `userProfile/<userId>/debug_overwrites.json` containing real `folderKey`, `folderFullyQualifiedName`, and `folderPath` for Studio Web runtime resolution. Missing `folderFullyQualifiedName` or `folderPath` causes `Could not find process for tool '<name>'`.

For in-solution agents registered with the parent solution, run `uip agent init` inside a solution directory; it auto-registers. Verify `Data.SolutionRegistration.Status` is `Registered` or `AlreadyRegistered`. Run `uip solution projects add` only as the fallback for `NotInSolution`, `Skipped`, or `Failed`; do not use it for `OptedOut`, which indicates intentional `--skip-solution-registration`. Package and process declarations are then pre-existing, and refresh resolves the binding.

Declaration directories map as follows:

| `Data.spec.type` | Agent `type` | Declaration `spec.type` | Directory |
|---|---|---|---|
| `Process` | `process` | `Process` | `process/process/` |
| `Agent` | `agent` | `Agent` | `process/agent/` |
| `Api` | `api` | `Api` | `process/api/` |
| `ProcessOrchestration` | `processOrchestration` | `ProcessOrchestration` | `process/processOrchestration/` |

If refresh cannot run because of offline operation, a missing RCS match, or custom deployment, use the full Templates A (RPA) and B (Agent / API / Agentic), package declaration, and `debug_overwrites` templates in [solution-files.md](solution-files.md).

## Walkthrough

1. Scaffold the solution and agent per [project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).
2. Discover the process by running either:

```bash
uip solution resources list --source remote --kind Process --search "<NAME>" --output json
uip solution resources list --source local --output json
```

For local discovery, omit `--kind` and `--search` and filter `.Data[]` client-side. Map `Source`, `Key`, `Name`, `Kind`, `Type`, `Folder`, and `FolderKey` as described above.
3. Run:

```bash
uip solution resources get <KEY> --output json
```

Parse `Data.spec` for V2 or raw schemas, package identity, and entry-point fields. Create the agent-level resource file with `location` from `Source`, lowercase `type` from `Type`, `folderPath` from `Folder`, `referenceKey` from `Key`, and the appropriate schemas.
4. Configure `agent.json` with the system prompt, model, and schemas.
5. Run:

```bash
uip agent refresh "<AGENT_NAME>" --output json
```

6. Run:

```bash
uip agent validate "<AGENT_NAME>" --output json
```

7. Run:

```bash
uip solution resources refresh --output json
```

8. Bundle and upload by running:

```bash
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

## Multi-Agent Solution Example

For two agents in one solution where a parent calls a child:

1. Scaffold the solution per `project-lifecycle.md`.
2. Add the child agent by running:

```bash
uip agent init "ToolAgent" --output json
```

Run this inside the solution directory and confirm `Data.SolutionRegistration.Status` is `Registered` or `AlreadyRegistered`. If it is `NotInSolution`, `Skipped`, or `Failed`, run the fallback:

```bash
uip solution projects add "ToolAgent" --output json
```

Do not use the fallback for `OptedOut`. Either path creates `resources/solution_folder/package/ToolAgent.json` and `resources/solution_folder/process/agent/ToolAgent.json`.
3. From the parent agent, discover the child by running:

```bash
uip solution resources list --source local --output json
```

Filter client-side for `Kind="Process"` and `Name="ToolAgent"`, then run:

```bash
uip solution resources get <KEY> --output json
```

Create `ParentAgent/resources/ToolAgent/resource.json` with `location: "solution"`.
4. Refresh and validate both agents by running:

```bash
uip agent refresh  ParentAgent --output json
uip agent validate ParentAgent --output json
uip agent refresh  ToolAgent --output json
uip agent validate ToolAgent --output json
```

Bundle and upload as usual. Do not hand-edit UUID cross-references among `SolutionStorage.Projects[].ProjectId`, `package/<ToolAgent>.json.projectKey`, and `process/agent/<ToolAgent>.json.projectKey`; project registration and `uip agent refresh` manage them. See [../../solution-resources.md](../../solution-resources.md) § UUID Cross-References.

## Gotchas

See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Critical Rules 11, 12, 13. Anti-patterns 7, 8, 18, and 24 also apply.

## References

- [solution-files.md](solution-files.md) — hand-authored Templates A/B, package, `debug_overwrites`, and How to Get the Values
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics, § UUID Cross-References
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
- [../../agent-definition.md](../../agent-definition.md) § Resources Convention