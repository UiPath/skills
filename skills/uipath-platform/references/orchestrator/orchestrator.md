# Orchestrator (`uip or`)

Manage Orchestrator infrastructure -- folders, users, machines, jobs, processes, and more.

> For full option details on any command, use `--help` (e.g., `uip or folders list --help`).

---

## Common Flags

All `uip or` commands share a set of cross-cutting options:

| Flag | Scope | Purpose |
|------|-------|---------|
| `--tenant <name>` | All commands | Override the default tenant (set during `uip login tenant set`). |
| `--output json` | All commands | Emit structured JSON instead of table output. Always use this when parsing output programmatically. |
| `--limit <n>` | List commands | Number of items to return (default 50). |
| `--offset <n>` | List commands | Number of items to skip for pagination. |
| `--sort-by <field>` | List commands | OData-style sort (e.g., `'Name asc'`, `'Id desc'`). |
| `--all-fields` | Most get/list commands | Return the full API DTO instead of the curated summary. Use when you need a field the curated view drops. Note: curated keys are PascalCase, raw DTO keys are camelCase — the shapes do not share casing. |
| `--output-filter <expr>` | All commands | JMESPath expression to filter/reshape JSON output (e.g., `--output-filter "Data[].Key"`). |
| `-y, --yes` | Delete commands | Confirm the irreversible operation. Required — the CLI never prompts; without it the command fails with "Confirmation required". Where a command also has `--force` (e.g. non-empty `queues`/`buckets` delete), `--force` implies `--yes`. |

**Pagination pattern.** List responses include a `Pagination` block with `Returned`, `Limit`, `Offset`, and `HasMore`. When `HasMore` is `true`, increment `--offset` by `--limit` and fetch again. Continue until `HasMore` is `false` or `Returned < Limit`.

---

## Workflow References

Each workflow doc covers a multi-command choreography for a specific goal. Load the one that matches your task.

| Workflow | File | Covers |
|----------|------|--------|
| Setup Environment | [setup-environment.md](setup-environment.md) | Folders, users, roles, machines, licenses |
| Run Jobs | [run-jobs.md](run-jobs.md) | Packages, processes, jobs, logs, traces |
| Manage Sessions | [manage-sessions.md](manage-sessions.md) | Sessions, runtimes, maintenance mode |
| Tenant Admin | [tenant-admin.md](tenant-admin.md) | Settings, calendars, audit logs, credential stores, feeds, attachments |

---

## Key Concepts

### Platform Hierarchy

```
Organization (cloud.uipath.com)
  +-- Tenant              Isolated environment (dev, staging, prod)
        +-- Folder         Logical container for resources
              +-- Processes, Jobs, Assets, Queues, Machines, etc.
```

All CLI operations happen within a **tenant** context (set via `uip login tenant set` or `--tenant`). Most resource operations also require a **folder** context (`--folder-path` or `--folder-key`).

Tenants provide complete isolation of all Orchestrator entities. Each tenant has its own folders, users, machines, packages, and configuration. A typical setup uses separate tenants for Development, Staging/UAT, and Production.

### Folder Types

| Type | Description |
|------|-------------|
| **Standard** | Regular folder for organizing resources. Supports nesting. |
| **Personal** | Per-user workspace. Flat (no hierarchy). |
| **Solution** | Created by solution deployments. Managed by the solution framework. |
| **DebugSolution** | Created for debugging solution-deployed processes. |
| **Virtual** | Virtual folders (legacy). |

### Process vs Release

In the CLI, a "process" is what the Orchestrator API calls a "Release" -- a published automation package bound to a folder with runtime configuration. The CLI uses "process" consistently; the API uses "Release" in endpoint names and DTOs.

### Job State Machine

```
Pending --> Running --> Successful
                   --> Faulted
                   --> Stopped

Running --> Stopping --> Stopped
Running --> Terminating --> Stopped
Running --> Suspended <--> Resumed --> Running
```

Final states (`Successful`, `Faulted`, `Stopped`) are immutable. A stopped or faulted job cannot be restarted -- start a new job instead.

### Folder-Scoped vs Tenant-Scoped Resources

Some resources are **tenant-scoped** (machines, users, roles, packages, settings) -- they exist once per tenant and can be referenced from any folder. Others are **folder-scoped** (processes, jobs, assets, queues, triggers) -- they belong to a specific folder and require `--folder-path` or `--folder-key` on most operations.

### Identifiers

The CLI uses GUID keys for all entity references. Numeric IDs are never exposed to users. Folder arguments accept either a GUID key or a path string (e.g., `"Finance"` or `"Finance/Invoicing"`) -- the CLI resolves paths to keys internally.

---

## REST API Fallback

When the CLI does not cover an operation, you can fall back to the Orchestrator REST API using the access token stored in `~/.uipath/.auth`. Always check `uip or --help` first — most operations are covered by the CLI, and a command is safer and more consistent than hand-rolled REST. Only reach for REST when there is genuinely no command for what you need (and consider reporting the gap so the CLI can cover it).

---

## Related

- **Resources** (`uip or`) — assets, queues, triggers, buckets, webhooks, libraries → [resources.md](resources.md)
- **Solutions** (`uip solution`) — pack, publish, deploy solution packages → [`uipath-solution`](/uipath:uipath-solution)
