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
│       ├── process/   ← runnable processes (agent/ or process/)
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

### RPA process definition (external process in solution)

**Path:** `resources/solution_folder/process/process/{ProcessName}.json`

Includes an external RPA process as a solution resource (pinned version).

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "TestRPA.process.TestRPA",
    "kind": "package",
    "apiVersion": "orchestrator.uipath.com/v1",
    "files": [
      {
        "name": "TestRPA.process.TestRPA.1.0.0.nupkg",
        "kind": "Package",
        "version": "1.0.0",
        "url": "<orchestrator-download-url>",
        "key": "TestRPA.process.TestRPA:1.0.0"
      }
    ],
    "spec": {
      "fileName": "TestRPA.process.TestRPA.1.0.0.nupkg",
      "fileReference": "TestRPA.process.TestRPA:1.0.0"
    },
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
// External tool NOT in the solution (real folder path)
{
  "resource": "process",
  "key": "SomeExternalProcess",
  "value": {
    "name": { "defaultValue": "SomeExternalProcess", "isExpression": false },
    "folderPath": { "defaultValue": "Shared", "isExpression": false }
  },
  "metadata": {
    "subType": "process",
    "bindingsVersion": "2.2",
    "solutionsSupport": "false"
  }
}
```

The `solutionsSupport: "true"` metadata flag signals to the deployment engine that this resource participates in the solution deployment and the folder path should be resolved dynamically.

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

Always bundle first, then upload the `.uis` file. Do not pass a directory path directly to `uip solution upload`.

```bash
# Step 1: Bundle to .uis
uip solution bundle ./MySolution -d ./output --output json

# Step 2: Upload the .uis file
uip solution upload ./output/MySolution.uis --output json
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
