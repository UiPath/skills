# Solution Resources Internals

Solution architecture, UUID cross-references, bindings, `debug_overwrites`, and `uip solution resources refresh` mechanics. These patterns apply to every capability producing solution-level files.

## Architecture and Project Resources

A solution deploys multiple automation projects:

```text
MySolution/
├── Agent/                         # agent.json, project.uiproj, ...
├── Agent2/
├── resources/solution_folder/
│   ├── package/                   # one package per project
│   ├── process/                   # agent/, process/, api/, processOrchestration/
│   ├── connection/
│   ├── index/
│   └── bucket/
├── SolutionStorage.json
└── MySolution.uipx
```

`resources/solution_folder/` contains JSON definitions provisioned in the target Orchestrator solution folder.

Register the agent project with its solution to generate its package and process files. Run `uip agent init` inside a solution to register with the parent `.uipx`; outside one, it auto-scaffolds `<Name>Solution/` and registers the project. Run `uip solution projects add` as a fallback.

Package path: `resources/solution_folder/package/{AgentName}.json`.

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "Agent",
    "kind": "package",
    "apiVersion": "orchestrator.uipath.com/v1",
    "projectKey": "<uuid>",
    "isOverridable": true,
    "spec": { "fileName": null, "fileReference": null, "name": "Agent" },
    "key": "<unique-uuid>"
  }
}
```

Require `projectKey` to equal the agent `ProjectId` in `SolutionStorage.json`. The package name is `{SolutionName}.agent.{Name}` (spaces in the name become dots: `Agent 2` → `{SolutionName}.agent.Agent.2`).

Agent process path: `resources/solution_folder/process/agent/{AgentName}.json`.

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "Agent",
    "kind": "process",
    "type": "agent",
    "apiVersion": "orchestrator.uipath.com/v1",
    "projectKey": "<uuid>",
    "isOverridable": true,
    "dependencies": [{ "name": "Agent", "kind": "package", "key": "<package-resource-uuid>" }],
    "spec": {
      "type": "Agent",
      "packageName": "MySolution.agent.Agent",
      "package": { "name": "MySolution.agent.Agent", "key": "<package-resource-uuid>" },
      "agentMemory": false,
      "retentionAction": "Delete",
      "retentionPeriod": 30,
      "staleRetentionPeriod": 180,
      "targetFrameworkValue": "Portable"
    },
    "key": "<unique-uuid>"
  }
}
```

Require the process `projectKey` to equal the package `projectKey`. Require dependency and `spec.package` names to match the package resource and their `key` values to equal its `resource.key`. Use `type: "agent"` for low-code agents and `type: "process"` for RPA XAML. Set `packageName` to `{SolutionName}.agent.{AgentName}`, replacing spaces in `AgentName` with `.`.

## UUID Cross-References

Maintain these relationships:

```text
SolutionStorage.json Projects[].ProjectId
  = package/{Agent}.json resource.projectKey
  = process/agent/{Agent}.json resource.projectKey

process/agent/{Agent}.json resource.dependencies[].key
  = process/agent/{Agent}.json resource.spec.package.key
  = package/{Agent}.json resource.key

index/{Index}.json resource.dependencies[].key
  = index/{Index}.json resource.spec.storageBucket.key
  = bucket/orchestratorBucket/... resource.key
```

## Bindings

`uip agent refresh` reads `resources/{Name}/resource.json` and `features/{Name}/feature.json`, then writes one `bindings_v2.json` entry per external dependency. `uip agent validate` performs the same read-only check and fails with `AgentValidationOutdated` when the file is behind.

Every binding carries `name`. `Process`, `Index`, `App`, and `MemorySpace` bindings also carry `folderPath`. Copy it verbatim from the agent resource or feature. Connection bindings omit it and bind by `connection.id`.

| Kind | `name` source | `folderPath` source and rule |
|---|---|---|
| `process` local or external | `properties.processName` | `properties.folderPath`, the literal `Folder` from `uip solution resources list`; locally typically `"solution_folder"`; one per process tool |
| `index` | `indexName` | top-level `folderPath`, the literal `Folder`; StorageBucket-backed only |
| `app` escalation | `channel.properties.appName` | `channel.properties.folderName`, translated to binding `folderPath`; one per Action Center channel |
| `app` guardrail escalation | `action.app.name` | `action.app.folderName`, translated to binding `folderPath`; one per `$actionType: "escalate"` guardrail action |
| `memorySpace` | `memorySpaceName` | `folderPath` from `features/{FeatureName}/feature.json`; deduplicate by memory-space name plus folder |
| `connection` | `properties.connection.name` | omitted; bind by `connection.id` |

Binding values use this form:

```jsonc
{
  "resource": "process|index|app|memorySpace|connection",
  "key": "<binding-key>",
  "value": {
    "name": { "defaultValue": "<name>", "isExpression": false },
    "folderPath": { "defaultValue": "<folder>", "isExpression": false }  // omit for connection bindings (bind by connection.id)
  },
  "metadata": { "bindingsVersion": "2.2", "solutionsSupport": "true" }
}
```

For index names that need display text, include `displayName` in the `name` value. Memory-space bindings may include `displayName` in both `name` and `folderPath`. Connection bindings contain only `name` in `value`, and their `key` is `<connection-id>`. A solution-internal process uses `resource: "process"`, `key: "Agent2"`, `name.defaultValue: "Agent2"`, `folderPath.defaultValue: "solution_folder"`, and metadata `subType: "Agent"`; an external process uses `subType: "process"`. Keep `metadata.solutionsSupport` as the stringified boolean `"true"`, not JSON boolean `true`; `uip agent refresh` and `uip solution resources refresh` emit the string form.

Do not hand-edit `bindings_v2.json`. Edit `resource.json`, or use `uip agent memory` for memory features, then run `uip agent refresh`; never patch the binding directly. See [critical-rules/critical-rules.md](critical-rules/critical-rules.md) Anti-pattern 19 and [critical-rules/autonomous-critical-rules.md](critical-rules/autonomous-critical-rules.md) Anti-pattern 2.

## Debug Overwrites

Store per-developer overrides at `userProfile/<userId>/debug_overwrites.json`:

```jsonc
{
  "docVersion": "1.0.0",
  "tenants": [{
    "tenantKey": "<tenant-uuid>",
    "resources": [{
      "solutionResourceKey": "<resource-uuid-from-resources/solution_folder>",
      "reprovisioningIndex": 0,
      "overwrite": {
        "resourceKey": "<existing-orchestrator-resource-key>",
        "resourceName": "ExistingResourceName",
        "folderKey": "<orchestrator-folder-uuid>",
        "folderFullyQualifiedName": "Shared",
        "folderPath": "Shared",
        "type": "Reference",
        "kind": "index"
      }
    }]
  }]
}
```

Use `type: "Reference"` to link an existing resource and `type: "New"` to provision one. For capability-specific process, connection, index, and app entries, see [capabilities/process/solution-files.md](capabilities/process/solution-files.md). For external process tools, use its canonical template.

## Refresh Mechanics

Run:

```bash
uip solution resources refresh [solutionPath] --output json
```

Run it after `uip agent refresh` whenever external tools, memory spaces, index contexts, app escalations, or connections are added or changed.

Refresh rescans all solution projects and syncs declarations from `bindings_v2.json`. For each external binding, look up the joint key `(name, kind, folderPath)` in the appropriate catalog: Resource Catalog Service for `Process`, `App`, and `MemorySpace`; ECS for `Index`; and the local IS connection cache for `Connection`. Use the folder dimension to disambiguate equal names. If no match exists, create a virtual placeholder and warn. Skip solution-internal bindings with `folderPath: "solution_folder"`; resolve them at deploy time against the solution folder.

| Binding kind | Solution-level files | `debug_overwrites.json` |
|---|---|---|
| `Queue`, `Asset`, `Bucket` | Virtual resource | None required |
| `Process` (RPA / agent / api / processOrchestration) | `process/<type>/<Name>.json` + `package/<Name>.json` | `kind: "process"`; populate real `folderKey`, `folderFullyQualifiedName`, and `folderPath` from the RCS match |
| `Connection` | `connection/<connectorKey>/<Name>.json` | `kind: "connection"` |
| `Index` (StorageBucket-backed only) | `index/<Name>.json` + `bucket/orchestratorBucket/<BucketName>.json` | Two entries: `kind: "index"` and `kind: "bucket"` |
| `MemorySpace` | `memorySpace/<Name>.json` | `kind: "memorySpace"` when imported from RCS |
| `App` (guardrail escalation via `agent.json`) | `app/workflow Action/<Name>.json` + `appVersion/<Name>.json` + `package/<Name>.json` + `process/webApp/<Name>.json` | Two entries: `kind: "app"` and `kind: "process"` |

Do not expect refresh to handle these cases; write their solution-level files and `debug_overwrites.json` entries by hand. See [capabilities/process/solution-files.md](capabilities/process/solution-files.md):

- `Index` bindings whose data source is not `StorageBucket` (`GoogleDrive`, `OneDrive`, `Dropbox`, `Confluence`, or `Attachments`); refresh warns and skips them.
- `Context` resources of type `datafabricentityset`.
- Escalation resource channels of type `email`, `slack`, or `teams`; the runtime recognizes them, but refresh does not generate solution-level files for these channel types.
