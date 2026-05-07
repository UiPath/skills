# Integration Service

Connector platform that provides pre-built integrations with third-party services (Salesforce, Outlook, SAP, Slack, etc.). Manages OAuth connections, exposes activities for use in automations and BPMN processes, and provides event-based triggers.

Integration Service is used by both Orchestrator (standalone automations) and Maestro (BPMN service tasks). Connection failures here surface as errors in whichever product initiated the call.

## Organization Model

```
Organization (cloud.uipath.com)
  └── Tenant
        └── Connectors             ← Pre-built integration templates (Salesforce, Outlook, etc.)
              └── Connections      ← Authenticated instances of a connector (folder-scoped)
                    ├── Activities ← Operations available on the connector
                    ├── Resources  ← Objects the connector can interact with
                    └── Triggers   ← Event subscriptions (CREATED, UPDATED, DELETED)
```

## Dependencies

- **Identity Server** — OAuth token management and user/robot identity resolution
- **Orchestrator** — folder-scoped permissions, robot account access to connections
- **Maestro** — BPMN processes invoke IS connections via service tasks; trigger events start BPMN instances
- **External Services** — the third-party APIs that connectors wrap (Salesforce, O365, etc.)

## Features

- **Connectors** — pre-built integration templates for third-party services
- **Connections** — authenticated instances of a connector, scoped to a tenant (optionally folder-scoped)
- **Activities** — operations exposed by connectors for use in workflows and BPMN processes
- **Resources** — objects and records within the external service (list, get, create, update, delete)
- **Triggers** — event-based subscriptions that can start Orchestrator jobs or Maestro instances
- **OAuth Management** — create, re-authenticate, and ping connections via OAuth flows

## Connection Resource File

Projects and solutions store connection references as JSON files. The location depends on whether the project is standalone or part of a solution — **always check both layouts**:

| Layout | Path pattern |
|--------|--------------|
| Standalone project | `<project-root>/connection/<connector-key>/<owner>.json` |
| Solution (single folder) | `<project-root>/resources/solution_folder/connection/<connector-key>/<owner>.json` |
| Solution (multi-folder) | `<project-root>/resources/<folder-name>/connection/<connector-key>/<owner>.json` |

Each `<connector-key>` subfolder contains one JSON file per connection, named after the connection's `resource.name` (typically the owner's email or username).

**When investigating, glob `**/connection/<connector-key>/*.json` from the project root** — that catches all three layouts in one read. Do NOT assume the standalone path; solutions are common and the resource file may be several directories deep under `resources/`.

Key fields:

| Field | What it is | Use for |
|-------|-----------|---------|
| `spec.connectorName` | Human-readable connector display name (e.g., "Microsoft OneDrive & SharePoint") | **Always use this as the display name.** Do NOT guess from activity package names — they differ. |
| `spec.connectorKey` | Connector key (e.g., `uipath-microsoft-onedrive`) | CLI queries: `uip is connectors get <key>`, `uip is connections list <key>` |
| `resource.key` | Connection ID (UUID) | Match against connection IDs in workflow XAML |
| `resource.name` | Connection owner (usually an email) | Identify who created the connection |
| `spec.authenticationType` | How the connection authenticates | "AuthenticateAfterDeployment" means the user must authenticate after creating the connection |
| `resource.folders` | Folder bindings | Which folder the connection is scoped to |

## CLI

```
uip is connectors list|get              — browse available connectors
uip is connections list|create|ping|edit — manage authenticated connections
uip is activities list <connector-key>   — list connector activities (--triggers for trigger-only)
uip is resources list|describe|execute   — interact with connector resources
uip is triggers objects|describe         — explore trigger metadata
```

Key commands for diagnostics:
- `uip is connections list [connector-key] --folder-key <key>` — list connections in a folder
- `uip is connections ping <connection-id>` — check if a connection is active and enabled
- `uip is connections list --connection-id <id>` — get details for a specific connection
