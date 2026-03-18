# Resources

Unified management of platform resources — assets, queues, storage buckets, and more.

## Overview

The `resources` command group provides a unified interface for managing platform resources across Orchestrator, Data Fabric, Maestro, Action Center, and Integration Service. All commands support folder targeting and JSON output.

> **Note:** The `resources` commands are currently provided by the `@uipath/resources-tool` CLI package. This tooling is being replaced — command names and interfaces may change. The underlying capabilities and API patterns will remain.

> **Resources vs Orchestrator Commands:** `orch` commands (`uip or`) manage jobs, processes, releases, and logs — runtime operations on published automations. `resources` covers everything else — assets, queues, folders, storage buckets, Data Fabric, Maestro, Action Center, packages, and Integration Service connectors/connections.

## Available Resource Types

| Resource | Status | Documentation |
|---|---|---|
| **Assets** | Available | [assets.md](assets.md) |
| **Queues** | Available | [queues.md](queues.md) |
| **Storage Buckets** | Available | [storage-buckets.md](storage-buckets.md) |
| **Folders** | Available (via `uip or folders`) | [../orchestrator/orchestrator-guide.md](../orchestrator/orchestrator-guide.md) |
| **Connectors** | Available (via `uip is`) | [../integration-service/connectors.md](../integration-service/connectors.md) |
| **Connections** | Available (via `uip is`) | [../integration-service/connections.md](../integration-service/connections.md) |
| **Packages** | Partial | See below |
| **Data Fabric Entities** | Planned | See below |
| **Maestro Processes/Cases** | Planned | See below |
| **Action Center Tasks** | Planned | See below |
| **Health & Metrics** | Planned | See below |

## Common Options

All `resources` commands support:

| Option | Description |
|---|---|
| `--format json` | JSON output (always use for programmatic access) |
| `--folder-id <id>` | Target folder ID (required for most operations) |
| `--filter <odata>` | OData filter expression |
| `--count <n>` | Number of items to return |

## Solution Resource Declarations

Solutions declare resource dependencies in `solutionResourcesDefinition.json`. These map to platform resources that are provisioned during deployment:

```json
{
  "Resources": [
    { "Kind": "Asset", "Name": "ApiKey", "Type": "Secret" },
    { "Kind": "Queue", "Name": "InvoiceQueue" },
    { "Kind": "Connection", "ConnectorKey": "uipath-salesforce" },
    { "Kind": "StorageBucket", "Name": "ExportFiles" }
  ]
}
```

## Planned Resource Types

These resource types are proposed for future implementation:

### Packages
- `resources packages-search` — Search NuGet feed for packages (partial: available via `rpa-tool`)
- `resources packages-list` — List packages in Orchestrator feed
- `resources packages-upload` — Upload package to feed
- `resources packages-delete` — Delete package from feed

### Data Fabric Entities
CRUD operations on Data Fabric entities and records — list entities, get/insert/update/delete records, download attachments.

### Maestro (Process & Case Instances)
List, get, pause, resume, cancel process and case instances. View execution history, incidents, variables, and BPMN diagrams.

### Action Center Tasks
List, create, complete, assign, reassign, and unassign Action Center tasks. Get task details including form layouts.

### Health & Metrics
Runtime readiness checks, operational metrics, and alert rule management.
