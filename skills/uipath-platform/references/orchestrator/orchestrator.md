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
| `--order-by <field>` | List commands | OData-style sort (e.g., `'Name asc'`, `'Id desc'`). |
| `--all-fields` | Most get/list commands | Return the full API DTO instead of the curated summary. Use when you need a field not in the default output. |
| `--output-filter <expr>` | All commands | JMESPath expression to filter/reshape JSON output (e.g., `--output-filter "Data[].Key"`). |

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

When the CLI does not cover an operation, use the Orchestrator REST API directly with a stored token from `~/.uipath/.auth`.

**Base URL pattern:**

```
${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/
```

**Auth header:**

```
Authorization: Bearer <UIPATH_ACCESS_TOKEN>
X-UIPATH-OrganizationUnitId: <FOLDER_ID>
```

Always check `uip or --help` and `uip resource --help` first -- most operations are covered by the CLI. Only fall back to REST when there is no CLI command for the operation you need.

**Example -- list triggers (no CLI command yet):**

```bash
ACCESS_TOKEN=$(cat ~/.uipath/.auth | jq -r '.access_token')
BASE_URL="https://cloud.uipath.com/myorg/mytenant/orchestrator_/odata"

curl -s -G "${BASE_URL}/ProcessSchedules" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" | jq .
```

Token expiry: re-run `uip login` if you get a 401.

---

## Related

- **Resources** (`uip resource`) -- Assets, queues, triggers, buckets, webhooks, libraries. See [resources.md](../resources/resources.md).
- **Solutions** (`uip solution`) -- Pack, publish, and deploy solution packages. See [solution.md](../solution/solution.md).
