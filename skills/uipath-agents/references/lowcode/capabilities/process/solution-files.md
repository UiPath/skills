# Solution-Level Files for External Process Tools — Hand-Authoring Reference

When `uip solution resources refresh` cannot produce solution-level files (offline, missing RCS match, custom deployment), hand-author them with this reference. For the standard path, see [process.md](process.md). This also covers the Releases API + `GetPackageEntryPointsV2` + JWT decoding path when `uip solution resources get` is unavailable (older builds, RCS unreachable, custom deployments). For standard CLI extraction, see [process.md § Discovery](process.md#discovery).

> **`folders[].fullyQualifiedName` carries the literal `Folder`** returned by `uip solution resources list` (for example, `"Shared"` or `"Shared/Sales"`). Use the same value in agent-level `resource.json` `properties.folderPath` and `bindings_v2.json`. Templates use `<Folder>`. Auto-generated declarations for **solution-internal projects** use `"solution_folder"` because they have no fixed Orchestrator folder until deploy. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Rule 11.

## Directory Structure

```text
<SolutionName>/
├── <SolutionName>.uipx
├── <AgentName>/
│   ├── agent.json
│   └── resources/<ToolName>/resource.json
├── resources/
│   └── solution_folder/
│       ├── package/
│       │   ├── <AgentName>.json
│       │   └── <PackageName>.json
│       └── process/
│           ├── agent/<AgentName>.json
│           ├── process/                 # RPA processes
│           ├── api/                     # API workflows
│           └── processOrchestration/    # Agentic processes
└── userProfile/
    └── <userId>/debug_overwrites.json
```

Place declarations under the directory matching `ProcessType`: `process/` for RPA, `agent/` for agents, `api/` for API workflows, and `processOrchestration/` for agentic processes.

## Process Declaration

**Path:** `resources/solution_folder/process/<type_dir>/<ToolName>.json`

| ProcessType | `resource.type` | `spec.type` | Directory | Schemas |
|---|---|---|---|---|
| `Process` | `process` | `Process` | `process/process/` | `inputArgumentsSchema`/`outputArgumentsSchema` raw .NET arrays |
| `Agent` | `agent` | `Agent` | `process/agent/` | `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` JSON Schema |
| `Api` | `api` | `Api` | `process/api/` | `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` JSON Schema |
| `ProcessOrchestration` | `processOrchestration` | `ProcessOrchestration` | `process/processOrchestration/` | `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` JSON Schema |

RPA declarations set V2 schemas and entry-point fields to `null`, use raw `Arguments.Input`/`Arguments.Output`, and include `jobPriority`, `jobRecording`, `duration`, `frequency`, `quality`, and `remoteControlAccess`. Other types set old-style schemas to `null`, populate `entryPointUniqueId`, `entryPointName`, and `entryPoints`, and use `GetPackageEntryPointsV2`. Agent declarations additionally include `agentMemory`, `targetRuntime`, `environmentVariables`, and `referencedAssets`.

### Template A — RPA Process (`type: "process"`)

**Path:** `resources/solution_folder/process/process/<ToolName>.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<ToolName>",
    "kind": "process",
    "type": "process",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [{ "name": "<PackageName>", "kind": "Package" }],
    "runtimeDependencies": [],
    "files": [],
    "folders": [{ "fullyQualifiedName": "<Folder>" }],
    "spec": {
      "type": "Process",
      "jobPriority": "Medium",
      "jobRecording": "Disabled",
      "duration": 40,
      "frequency": 500,
      "quality": 100,
      "remoteControlAccess": "None",
      "name": "<ToolName>",
      "package": { "name": "<PackageName>", "key": "<PackageName>:<Version>" },
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

### Template B — Agent, API Workflow, or Agentic Process

**Path:** `resources/solution_folder/process/<type_dir>/<ToolName>.json`, where `<type_dir>` is `agent/`, `api/`, or `processOrchestration/`. Include `agentMemory`, `targetRuntime`, `environmentVariables`, and `referencedAssets` only when `type` is `agent`.

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<ToolName>",
    "kind": "process",
    "type": "<type>",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [{ "name": "<PackageName>", "kind": "Package" }],
    "runtimeDependencies": [],
    "files": [],
    "folders": [{ "fullyQualifiedName": "<Folder>" }],
    "spec": {
      "type": "<Type>",
      "agentMemory": false,
      "targetRuntime": "pythonAgent",
      "environmentVariables": "",
      "referencedAssets": null,
      "name": "<ToolName>",
      "package": { "name": "<PackageName>", "key": "<PackageName>:<Version>" },
      "packageName": "<PackageName>",
      "packageVersion": "<Version>",
      "entryPointUniqueId": "<UniqueId from GetPackageEntryPointsV2>",
      "entryPointName": "<Path from GetPackageEntryPointsV2>",
      "inputArguments": null,
      "inputArgumentsSchema": null,
      "outputArgumentsSchema": null,
      "inputArgumentsSchemaV2": "<InputArguments JSON Schema string>",
      "outputArgumentsSchemaV2": "<OutputArguments JSON Schema string>",
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
      "entryPoints": "<serialized JSON array>",
      "connections": null,
      "tags": [],
      "description": null
    },
    "locks": [],
    "key": "<release-key-guid>"
  }
}
```

Use PascalCase `spec.type`: `Agent`, `Api`, or `ProcessOrchestration`. Serialize `entryPoints` as:

```jsonc
[{
  "UniqueId": "<UniqueId>",
  "Path": "<Path>",
  "DisplayName": null,
  "InputArguments": "<InputArguments string>",
  "OutputArguments": "<OutputArguments string>",
  "Type": <numeric_type>,
  "TargetRuntime": null,
  "ContentRoot": null,
  "DataVariation": null,
  "Id": <Id>
}]
```

`Type` values are `1=Process`, `2=ProcessOrchestration`, `4=Agent`, and `6=Api`. `InputArguments` and `OutputArguments` must equal the corresponding V2 schema strings.

## Package Declaration

**Path:** `resources/solution_folder/package/<PackageName>.json`

Use `ProcessKey` from `/odata/Releases` as `<PackageName>` for all four process types. If `FeedId` differs from the tenant feed, append `?feedId=<FEED_ID>` to every process type's download URL; otherwise Studio Web reports `Resource '...' is missing in this environment.`

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
    "files": [{
      "name": "<PackageName>.<Version>.nupkg",
      "kind": "Package",
      "version": "<Version>",
      "url": "<orchBase>/odata/Processes/UiPath.Server.Configuration.OData.DownloadPackage(key='<URL_ENCODED_PACKAGE_KEY>')",
      "key": "<PackageName>_<Version_underscores>"
    }],
    "folders": [{ "fullyQualifiedName": "<Folder>" }],
    "spec": {
      "fileName": "<PackageName>.<Version>.nupkg",
      "fileReference": "<PackageName>_<Version_underscores>",
      "name": "<PackageName>",
      "description": null
    },
    "locks": [],
    "key": "<PackageName>:<Version>"
  }
}
```

Construct URLs as follows:

- `<orchBase>` = `${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_`
- URL-encode `<PackageName>:<Version>` for `<URL_ENCODED_PACKAGE_KEY>`.
- Replace dots with underscores in `<Version_underscores>`.
- Append `?feedId=<FEED_ID>` for solution-feed packages, for all four process types.

## debug_overwrites.json (process kind)

**Path:** `userProfile/<userId>/debug_overwrites.json`

Create this file for every external tool so Studio Web can resolve references during import and debugging; otherwise it reports `resource is missing in this environment`.

```jsonc
{
  "docVersion": "1.0.0",
  "tenants": [{
    "tenantKey": "<UIPATH_TENANT_ID>",
    "resources": [{
      "solutionResourceKey": "<release-key-guid>",
      "reprovisioningIndex": 0,
      "overwrite": {
        "resourceKey": "<release-key-guid>",
        "resourceName": "<ToolName>",
        "folderKey": "<folder-key-guid>",
        "folderFullyQualifiedName": "<folder-path>",
        "folderPath": "<parent-key>.<folder-key>",
        "type": "Reference",
        "kind": "process"
      }
    }]
  }]
}
```

Use `folderPath` as `parentKey.folderKey` for a child folder or `folderKey` for a root folder. Add one `resources` entry per tool and replace an existing entry with the same `solutionResourceKey`. For the generic debug_overwrites shape, see [../../solution-resources.md](../../solution-resources.md) § Debug Overwrites.

## How to Get the Values

> **Fallback path.** When `uip solution resources get` is available, use it instead — see [process.md § Discovery](process.md#discovery). Use these steps for older builds, RCS-unreachable environments, or custom deployments where the CLI cannot supply the full configuration.

> **SECURITY: Never read `~/.uipath/.auth` directly** — the access token must not appear in Claude's context. Always use a `bash -c` wrapper that sources the auth file and makes the API call in a single shell invocation, so Claude only sees the API response.

### Step 1: Discover the process and folder

Run:

```bash
uip solution resources list --kind Process --source remote --search "<NAME>" --output json
```

Use each result's `Key` as the release-key GUID, `Type` to select the agent-resource type and process directory, `Folder` as the literal folder path in all declarations, and `FolderKey` as the `X-UIPATH-FolderKey` value and `debug_overwrites.json` `folderKey`.

Type mappings: `process` → `process/process/`; `agent` → `process/agent/`; `api` → `process/api/`; `processOrchestration` → `process/processOrchestration/`.

### Step 2: Query `/odata/Releases`

Run this command, filtering by `ProcessKey` or `Name`, never by the GUID `Key`:

```bash
bash -c 'A="$HOME/.uipath/.auth"; [ -f "$A" ] || A="/.uipath/.auth"; set -a; source "$A"; set +a; curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Releases?\$filter=ProcessKey%20eq%20'\''<PROCESS_KEY>'\''&\$top=1&\$select=Key,Name,ProcessKey,ProcessVersion,ProcessType,FeedId,TargetRuntime,Description,Arguments,Id" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-FolderKey: <FOLDER_KEY_GUID>"'
```

Orchestrator rejects `Key eq <guid>` because of an `Edm.Guid` mismatch. Use `ProcessKey` (string) or `Name` instead. Map response fields as follows:

- `ProcessKey` and `ProcessVersion`: package key `<ProcessKey>:<Version>`.
- `FeedId`: required by Step 3.
- `TargetRuntime`: `"pythonAgent"` for agents and `null` otherwise.
- `Arguments.Input` and `Arguments.Output`: raw .NET arrays for RPA; `null` otherwise.

### Step 3: Query `GetPackageEntryPointsV2`

Run this command for all four process types and always pass `feedId`:

```bash
bash -c 'A="$HOME/.uipath/.auth"; [ -f "$A" ] || A="/.uipath/.auth"; set -a; source "$A"; set +a; curl -s "${UIPATH_URL}/${UIPATH_ORGANIZATION_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/Processes/UiPath.Server.Configuration.OData.GetPackageEntryPointsV2(key='\''<PROCESS_KEY>:<VERSION>'\'')?feedId=<FEED_ID>" \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UIPATH-FolderKey: <FOLDER_KEY_GUID>"'
```

Take the first returned entry. Map `UniqueId` to `entryPointUniqueId`, `Path` to `entryPointName`, `InputArguments` and `OutputArguments` to the V2 schemas and agent-level schemas, `Type` to serialized `entryPoints.Type`, and `Id` to serialized `entryPoints.Id`.

### Step 4: Build agent-level schemas

Parse the Step 3 `InputArguments` and `OutputArguments` JSON Schema strings and use them directly as `inputSchema` and `outputSchema` in the agent-level `resource.json` for all four types.

If `GetPackageEntryPointsV2` is unavailable, use this RPA-only fallback: parse `Arguments.Input` and `Arguments.Output`, extract the short type name by splitting at `,` and then `.`, and map:

| .NET Type | JSON Schema type |
|---|---|
| `System.String` | `"string"` |
| `System.Int32`, `System.Int64`, `System.Decimal`, `System.Double` | `"number"` |
| `System.Boolean` | `"boolean"` |
| Unknown | `"string"` |

### Step 5: Extract `userId` from the JWT

Decode the JWT access-token payload using base64 and read the `sub` claim. Use that value as `userId` in `debug_overwrites.json`.

## References

- [process.md](process.md) — capability overview + happy-path walkthrough using refresh
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics, § Debug Overwrites