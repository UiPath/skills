# Agent Solution Integration Guide

How low-code agent projects integrate with UiPath solutions, including resource definitions,
bindings, package/process files, and the full deployment pipeline.

---

## Solution Architecture Overview

A solution is a container for multiple automation projects deployed together. For low-code agents:

```
MySolution/
├── Agent/             ← agent project (agent.json, project.uiproj, ...)
├── Agent2/            ← another agent project
├── resources/         ← solution-level Orchestrator resource definitions
│   └── solution_folder/
│       ├── package/   ← deployment packages (one per project)
│       ├── process/   ← runnable processes (agent/, process/, api/, processOrchestration/)
│       ├── connection/ ← IS connections needed by agents
│       ├── index/     ← semantic search indexes
│       └── bucket/    ← storage buckets for indexes
├── SolutionStorage.json
└── MySolution.uipx
```

The `resources/solution_folder/` directory contains JSON resource definitions. When a solution is deployed, these resources are **provisioned** in the target Orchestrator folder (called the "solution folder").

---

## Resource Definition Files

### Package definition

**Path:** `resources/solution_folder/package/{AgentName}.json`

Links an agent project to its deployable NuGet package.

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "Agent",                    // Must match project name
    "kind": "package",
    "apiVersion": "orchestrator.uipath.com/v1",
    "projectKey": "<uuid>",             // Must match SolutionStorage.json ProjectId
    "isOverridable": true,              // Can be overridden at deployment config
    "spec": {
      "fileName": null,                 // Set by packager at build time
      "fileReference": null,
      "name": "Agent"
    },
    "key": "<unique-uuid>"              // Stable UUID for this resource
  }
}
```

The `projectKey` MUST match the agent's `ProjectId` in `SolutionStorage.json`.
The package `name` becomes part of the package identifier: `{SolutionName}.agent.{Name}`.

### Agent process definition

**Path:** `resources/solution_folder/process/agent/{AgentName}.json`

Makes the agent available as a runnable process in Orchestrator. One file per agent project.

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "Agent",
    "kind": "process",
    "type": "agent",                    // "agent" for low-code; "process" for RPA XAML
    "apiVersion": "orchestrator.uipath.com/v1",
    "projectKey": "<uuid>",             // Same as package projectKey
    "isOverridable": true,
    "dependencies": [
      {
        "name": "Agent",                // Must match the package resource name
        "kind": "package",
        "key": "<package-resource-uuid>"
      }
    ],
    "spec": {
      "type": "Agent",
      "packageName": "MySolution.agent.Agent",   // {SolutionName}.agent.{AgentName}
      "package": {
        "name": "MySolution.agent.Agent",
        "key": "<package-resource-uuid>"
      },
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

**`packageName` convention:** `{SolutionName}.agent.{AgentName}` where `AgentName` has spaces replaced with `.`.

Example:
- Solution: `MySolution`
- Agent project: `Agent 2`
- packageName: `MySolution.agent.Agent.2`

### External process tool — process declaration

**Path:** `resources/solution_folder/process/<type_dir>/{ToolName}.json`

Registers an already-deployed Orchestrator process (RPA, agent, API workflow, or agentic process) as a solution resource. This file is REQUIRED when an agent has an external tool with `"location": "external"` — without it, the process cannot be found at runtime.

The directory and content vary by process type:

| ProcessType | `resource.type` | `spec.type` | Directory | Schema approach |
|---|---|---|---|---|
| `Process` (RPA) | `process` | `Process` | `process/process/` | `inputArgumentsSchema`/`outputArgumentsSchema` (raw .NET arrays) |
| `Agent` | `agent` | `Agent` | `process/agent/` | `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` (JSON Schema) |
| `Api` | `api` | `Api` | `process/api/` | `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` (JSON Schema) |
| `ProcessOrchestration` | `processOrchestration` | `ProcessOrchestration` | `process/processOrchestration/` | `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` (JSON Schema) |

Get the values from the Releases API and `GetPackageEntryPointsV2`. See [agent-json-format.md](agent-json-format.md) § How to get the values.

**Key differences:**
- **RPA**: Uses `inputArgumentsSchema`/`outputArgumentsSchema` (raw .NET type arrays from `Arguments.Input`/`Arguments.Output`). V2 schema fields and entry point fields are `null`. Has extra spec fields: `jobPriority`, `jobRecording`, `duration`, `frequency`, `quality`, `remoteControlAccess`.
- **Agent/API/Agentic**: Uses `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` (JSON Schema from `GetPackageEntryPointsV2`). Populates `entryPointUniqueId`, `entryPointName`, `entryPoints`. Old-style schema fields are `null`. Agent type adds `agentMemory`, `targetRuntime`, `environmentVariables`, `referencedAssets`.

#### Example: RPA Process

**Path:** `resources/solution_folder/process/process/TestRPA.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "TestRPA",
    "kind": "process",
    "type": "process",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [
      {
        "name": "TestRPA.process.TestRPA",
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
      "name": "TestRPA",
      "package": {
        "name": "TestRPA.process.TestRPA",
        "key": "TestRPA.process.TestRPA:1.0.0"
      },
      "packageName": "TestRPA.process.TestRPA",
      "packageVersion": "1.0.0",
      "entryPointUniqueId": null,
      "entryPointName": null,
      "inputArguments": null,
      "inputArgumentsSchema": "[\n  {\n    \"name\": \"name\",\n    \"type\": \"System.String, System.Private.CoreLib, Version=8.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e\",\n    \"required\": false,\n    \"hasDefault\": true\n  }\n]",
      "outputArgumentsSchema": "[\n  {\n    \"name\": \"greeting\",\n    \"type\": \"System.String, System.Private.CoreLib, Version=8.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e\"\n  }\n]",
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
    "key": "cc69568b-e686-4737-bf62-7ed6ddb0849b"
  }
}
```

#### Example: Agent

**Path:** `resources/solution_folder/process/agent/TestAgent.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "TestAgent",
    "kind": "process",
    "type": "agent",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [
      {
        "name": "TestAgentSolution.agent.TestAgent",
        "kind": "Package"
      }
    ],
    "runtimeDependencies": [],
    "files": [],
    "folders": [
      { "fullyQualifiedName": "solution_folder" }
    ],
    "spec": {
      "type": "Agent",
      "agentMemory": false,
      "targetRuntime": "pythonAgent",
      "environmentVariables": "",
      "referencedAssets": null,
      "name": "TestAgent",
      "package": {
        "name": "TestAgentSolution.agent.TestAgent",
        "key": "TestAgentSolution.agent.TestAgent:1.0.0"
      },
      "packageName": "TestAgentSolution.agent.TestAgent",
      "packageVersion": "1.0.0",
      "entryPointUniqueId": "02ff7040-604a-481f-8336-235de71e2b4b",
      "entryPointName": "content/agent.json",
      "inputArguments": null,
      "inputArgumentsSchema": null,
      "outputArgumentsSchema": null,
      "inputArgumentsSchemaV2": "{\n  \"type\": \"object\",\n  \"properties\": {}\n}",
      "outputArgumentsSchemaV2": "{\n  \"type\": \"object\",\n  \"properties\": {\n    \"content\": {\n      \"type\": \"string\",\n      \"description\": \"Output content\"\n    }\n  }\n}",
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
      "entryPoints": "[{\"UniqueId\":\"02ff7040-604a-481f-8336-235de71e2b4b\",\"Path\":\"content/agent.json\",\"DisplayName\":null,\"InputArguments\":\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {}\\n}\",\"OutputArguments\":\"{\\n  \\\"type\\\": \\\"object\\\",\\n  \\\"properties\\\": {\\n    \\\"content\\\": {\\n      \\\"type\\\": \\\"string\\\",\\n      \\\"description\\\": \\\"Output content\\\"\\n    }\\n  }\\n}\",\"Type\":4,\"TargetRuntime\":null,\"ContentRoot\":null,\"DataVariation\":null,\"Id\":790954}]",
      "connections": null,
      "tags": [],
      "description": null
    },
    "locks": [],
    "key": "f6084607-a81c-45f1-90e4-ffe8fed22c53"
  }
}
```

### External process tool — package declaration

**Path:** `resources/solution_folder/package/{PackageName}.json`

Declares the package for the external process. Also REQUIRED alongside the process declaration above. The format is **identical for all 4 process types** — only the package name and version change. **Important:** If the package is in a solution-specific feed (its `FeedId` from the Releases API differs from the tenant feed), append `?feedId=<FEED_ID>` to the download URL. Without this, Studio Web reports "Resource '...' is missing in this environment."

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "TestRPA.process.TestRPA",
    "kind": "package",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [],
    "runtimeDependencies": [],
    "files": [
      {
        "name": "TestRPA.process.TestRPA.1.0.0.nupkg",
        "kind": "Package",
        "version": "1.0.0",
        "url": "<orchestrator-download-url>",
        "key": "TestRPA.process.TestRPA_1_0_0"
      }
    ],
    "folders": [
      { "fullyQualifiedName": "solution_folder" }
    ],
    "spec": {
      "fileName": "TestRPA.process.TestRPA.1.0.0.nupkg",
      "fileReference": "TestRPA.process.TestRPA_1_0_0",
      "name": "TestRPA.process.TestRPA",
      "description": null
    },
    "locks": [],
    "key": "TestRPA.process.TestRPA:1.0.0"
  }
}
```

### Connection definition

**Path:** `resources/solution_folder/connection/{connectorKey}/{connectionName}.json`

Provisions an Integration Service connection as part of the solution.

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "my-connection",           // Connection identifier
    "kind": "connection",
    "type": "uipath-salesforce-slack", // Connector key from IS
    "apiVersion": "integrationservice.uipath.com/v1",
    "isOverridable": true,
    "spec": {
      "connectorName": "Slack",
      "authenticationType": "AuthenticateAfterDeployment",  // credentials provided post-deploy
      "connectorVersion": "2.13.8",
      "connectorKey": "uipath-salesforce-slack",
      "pollingInterval": 5
    },
    "key": "<unique-uuid>"
  }
}
```

`authenticationType: "AuthenticateAfterDeployment"` means the connection credentials are provided by the user after deployment (not bundled in the solution).

### Connection definition (Integration Service)

**Path:** `resources/solution_folder/connection/{connectorKey}/{connectionName}.json`

Provisions an Integration Service connection as part of the solution. Required when an agent has an integration tool (`type: "integration"`). One per connector — all tools using the same connector share this connection resource.

**Auto-generated:** Do not create these files manually. After creating the agent-level integration tool `resource.json`, run `uip agent validate` (generates `bindings_v2.json`) then `uip solution resource refresh` (auto-generates connection resources and `debug_overwrites.json` from `bindings_v2.json`).

**Cross-reference:** The connection resource `key` matches the `solutionProperties.resourceKey` in integration tool resources that use this connector.

### Index definition (RAG semantic search)

**Path:** `resources/solution_folder/index/{IndexName}.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "MyIndex",
    "kind": "index",
    "apiVersion": "ecs.uipath.com/v2",
    "isOverridable": true,
    "dependencies": [
      {
        "name": "my_storage_bucket",
        "kind": "bucket",
        "key": "<bucket-resource-uuid>"
      }
    ],
    "spec": {
      "name": "MyIndex",
      "description": "",
      "storageBucketReference": {
        "name": "my_storage_bucket",
        "key": "<bucket-resource-uuid>"
      },
      "fileNameGlob": "All",
      "dataSourceType": "StorageBucket",
      "includeSubfolders": true,
      "ingestionType": "Advanced"
    },
    "key": "<unique-uuid>"
  }
}
```

### Storage bucket definition

**Path:** `resources/solution_folder/bucket/orchestratorBucket/{BucketName}.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "my_storage_bucket",
    "kind": "bucket",
    "type": "orchestratorBucket",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "spec": {
      "type": "Orchestrator",
      "description": null,
      "tags": []
    },
    "key": "<unique-uuid>"
  }
}
```

---

## Resource Key Cross-References

Resources must reference each other correctly:

```
SolutionStorage.json
  └── Projects[].ProjectId  ──────┐
                                  │
package/Agent.json                │
  └── resource.projectKey  ───────┤ same UUID
                                  │
process/agent/Agent.json          │
  └── resource.projectKey  ───────┘

process/agent/Agent.json
  └── resource.dependencies[].key  ──┐
  └── resource.spec.package.key   ───┤ same UUID
                                     │
package/Agent.json                   │
  └── resource.key              ─────┘

index/MyIndex.json
  └── resource.dependencies[].key  ──┐
  └── resource.spec.storageBucket.key┤ same UUID
                                     │
bucket/orchestratorBucket/...        │
  └── resource.key              ─────┘
```

---

## Bindings: How Agents Connect to Resources

### Solution-level binding (`.agent-builder/bindings.json`)

When Studio Web or uipcli generates bindings for a solution-aware agent, resources that are part of the solution get `folderPath: "solution_folder"`:

```jsonc
// Tool that is inside the solution
{
  "resource": "process",
  "key": "Agent2",
  "value": {
    "name": { "defaultValue": "Agent2", "isExpression": false },
    "folderPath": { "defaultValue": "solution_folder", "isExpression": false }
  },
  "metadata": {
    "subType": "Agent",
    "bindingsVersion": "2.2",
    "solutionsSupport": "true"
  }
}
```

```jsonc
// External tool registered as a solution resource (via resources/solution_folder/ files)
{
  "resource": "process",
  "key": "TestRPA",
  "value": {
    "name": { "defaultValue": "TestRPA", "isExpression": false },
    "folderPath": { "defaultValue": "solution_folder", "isExpression": false }
  },
  "metadata": {
    "subType": "process",
    "bindingsVersion": "2.2",
    "solutionsSupport": "true"
  }
}
```

The `solutionsSupport: "true"` metadata flag signals to the deployment engine that this resource participates in the solution deployment and the folder path should be resolved dynamically. External tools use `"solution_folder"` because they are registered as solution resources via the process and package declaration files under `resources/solution_folder/`.

### Debug overwrites (`userProfile/{userId}/debug_overwrites.json`)

Each developer can have personal resource overrides for debug sessions. This avoids reprovisioning existing resources.

```jsonc
{
  "docVersion": "1.0.0",
  "tenants": [
    {
      "tenantKey": "<tenant-uuid>",
      "resources": [
        {
          "solutionResourceKey": "<resource-uuid-from-resources/solution_folder>",
          "reprovisioningIndex": 0,
          "overwrite": {
            "resourceKey": "<existing-orchestrator-resource-key>",
            "resourceName": "ExistingResourceName",
            "folderKey": "<orchestrator-folder-uuid>",
            "folderFullyQualifiedName": "Shared",
            "folderPath": "Shared",
            "type": "Reference",   // "Reference" = link to existing; "New" = provision new
            "kind": "index"        // resource kind
          }
        }
      ]
    }
  ]
}
```

---

## Solution Lifecycle Commands

All solution lifecycle operations are performed via `uip solution` CLI commands. Never call Automation.Solutions REST endpoints directly.

### Create and scaffold

```bash
# Create the solution skeleton
uip solution new "MySolution" --output json
# → MySolution.uipx + SolutionStorage.json

# Scaffold agent projects (creates ONLY agent project files)
uip agent init ./MySolution/Agent --model gpt-4o-2024-11-20 --output json
uip agent init ./MySolution/Agent2 --model gpt-4o-2024-11-20 --output json

# Link agent projects to solution
uip solution project add ./MySolution/Agent ./MySolution/MySolution.uipx --output json
uip solution project add ./MySolution/Agent2 ./MySolution/MySolution.uipx --output json
```

### Upload to Studio Web

```bash
uip solution upload ./MySolution --output json
```

### Pack and publish

```bash
# Pack to .zip for Orchestrator
uip solution pack ./MySolution ./output -v "1.0.0" --output json
# → ./output/MySolution.1.0.0.zip

# Publish to Orchestrator package feed
uip solution publish ./output/MySolution.1.0.0.zip --output json
# → { PackageVersionKey, PackageName, PackageVersion }
```

### Deploy

```bash
# Deploy (install + auto-activate); polls until terminal state
uip solution deploy run \
  --name "MySolution-Production" \
  --package-name "MySolution" \
  --package-version "1.0.0" \
  --folder-name "MySolution" \
  --folder-path "Shared" \
  --output json
# Terminal states: DeploymentSucceeded, DeploymentFailed, ValidationFailed

# Activate an already-installed deployment
uip solution deploy activate "MySolution-Production" --output json
# Terminal states: SuccessfulActivate, FailedActivate

# Uninstall a deployment
uip solution deploy uninstall "MySolution-Production" --output json
# Terminal states: SuccessfulUninstall, FailedUninstall

# Check deployment status
uip solution deploy status <pipeline-deployment-id> --output json

# List deployments
uip solution deploy list --output json
```

---

## Agent-to-Agent Calls Within a Solution

When Agent A needs to call Agent B in the same solution:

### In Agent A's `resources/Agent B/resource.json`:

Create a tool resource file at `AgentA/resources/Agent B/resource.json`:

```jsonc
{
  "$resourceType": "tool",
  "id": "<uuid>",
  "referenceKey": "",                // ← leave empty; validate resolves it and writes it back to disk
  "name": "Agent B",
  "type": "agent",
  "location": "solution",           // ← key: marks as solution-internal
  "description": "Calls Agent B for specialized tasks",
  "inputSchema": {
    // Copy from Agent B's inputSchema
    "type": "object",
    "properties": {
      "agent2Input": { "type": "string" }
    }
  },
  "outputSchema": {
    // Copy from Agent B's outputSchema
    "type": "object",
    "properties": {
      "content2": { "type": "string" }
    }
  },
  "isEnabled": true,
  "settings": {},
  "properties": {
    "processName": "Agent B",
    "folderPath": "solution_folder"  // ← always solution_folder for solution resources
  },
  "guardrail": {
    // Tool-level placeholder. Use agent.json guardrails[] for manual guardrail authoring.
    "policies": []
  },
  "argumentProperties": {}
}
```

**Do NOT add resources inline in Agent A's root `agent.json`.** The `validate` command reads `resources/{name}/resource.json` files, resolves `referenceKey` from the solution process definitions, and generates `.agent-builder/agent.json` with resources inlined.

### Generated `.agent-builder/bindings.json` (by validate):

```jsonc
{
  "resource": "process",
  "key": "Agent B",
  "value": {
    "name": { "defaultValue": "Agent B", "isExpression": false, "displayName": "Process name" }
  },
  "metadata": {
    "subType": "agent",
    "bindingsVersion": "2.2",
    "solutionsSupport": "true"
  }
}
```

### In `resources/solution_folder/process/agent/Agent_B.json`:

A process definition must exist for Agent B (created automatically by `uip solution project add`).

---

## Versioning

Solutions use semantic versioning: `MAJOR.MINOR.PATCH`

```bash
# Pack with specific version
uip solution pack ./MySolution ./output -v "1.2.0" --output json

# Publish the versioned package to Orchestrator
uip solution publish ./output/MySolution.1.2.0.zip --output json

# Check published packages
uip solution packages list --output json
```

Version strategy:
- `PATCH`: bug fixes, prompt tweaks
- `MINOR`: new tools, new agents added
- `MAJOR`: breaking changes to I/O schema

---

## Environment Promotion

To promote from dev to production:

```bash
# 1. Pack solution
uip solution pack ./MySolution ./output -v "2.0.0"

# 2. Publish to Orchestrator
uip solution publish ./output/MySolution.2.0.0.zip

# 3. Deploy to production folder
uip solution deploy run \
  --name "MySolution-Prod" \
  --package-name "MySolution" \
  --package-version "2.0.0" \
  --folder-name "MySolution" \
  --folder-path "Production"
```
