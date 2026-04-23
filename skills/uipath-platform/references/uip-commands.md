# UiPath CLI (`uip`) Command Reference

> **Quick reference index.** Use `--help` for full option details on any command.

**Global flags:**
- `--output json` — always use when calling programmatically
- `--output-filter <expr>` — JMESPath filter for JSON output
- `--tenant <name>` — tenant override (defaults to authenticated tenant)
- `--verbose` — enable debug logging

**List command flags:**
- `--limit <N>` / `--offset <N>` — pagination. Check `Pagination.HasMore` in output.
- `--order-by <field>` — sort results (e.g., `Name asc`, `Id desc`)
- `--all-fields` — (Orchestrator tool + libraries only) return full API response

---

## Authentication

| Command | Description |
|---|---|
| `uip login` | Authenticate with UiPath Cloud |
| `uip login status` | Show current login status |
| `uip login tenant list` | List available tenants |
| `uip login tenant set <name>` | Set active tenant |
| `uip logout` | End session and clear tokens |

---

## Orchestrator (`uip or`)

Manage folders, jobs, processes, machines, users, packages, and more. See [orchestrator/](orchestrator/orchestrator.md).

| Group | Key Commands | Workflow Guide |
|---|---|---|
| **Folders** | `list [--all]`, `get`, `create`, `edit`, `delete`, `move`, `runtimes` | [Setup Environment](orchestrator/setup-environment.md) |
| **Jobs** | `list`, `get`, `start`, `stop`, `restart`, `resume`, `logs [--export]`, `traces`, `healing-data`, `history` | [Run Jobs](orchestrator/run-jobs.md) |
| **Processes** | `list`, `get`, `create`, `edit`, `update-version`, `rollback` | [Run Jobs](orchestrator/run-jobs.md) |
| **Packages** | `list`, `get`, `versions`, `entry-points`, `upload`, `download` | [Run Jobs](orchestrator/run-jobs.md) |
| **Machines** | `list`, `get`, `create`, `edit`, `delete`, `assign`, `unassign` | [Setup Environment](orchestrator/setup-environment.md) |
| **Users** | `list`, `list-in-folder`, `list-available`, `get`, `create`, `edit`, `delete`, `current`, `assign`, `unassign`, `assign-roles` | [Setup Environment](orchestrator/setup-environment.md) |
| **Roles** | `list-roles`, `list-permissions`, `get-role`, `create-role`, `edit-role`, `delete-role`, `list-role-users`, `set-role-users`, `list-user-roles`, `assign` | [Setup Environment](orchestrator/setup-environment.md) |
| **Sessions** | `list-attended-sessions`, `list-unattended-sessions`, `list-machines-sessions`, `list-usernames`, `list-user-executors`, `toggle-debug-mode`, `delete-inactive`, `set-maintenance-mode` | [Manage Sessions](orchestrator/manage-sessions.md) |
| **Settings** | `list`, `get`, `update`, `execution`, `timezones` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Calendars** | `list`, `get`, `create`, `update`, `delete` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Licenses** | `list --type`, `toggle`, `info` | [Setup Environment](orchestrator/setup-environment.md) |
| **Audit Logs** | `list [--export]` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Credential Stores** | `list`, `get` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Feeds** | `list` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Attachments** | `list --job-key`, `download` | [Tenant Admin](orchestrator/tenant-admin.md) |

---

## Resource (`uip resource`)

Manage assets, queues, triggers, buckets, libraries, and webhooks. See [resources/](resources/resources.md).

| Group | Key Commands | Workflow Guide |
|---|---|---|
| **Assets** | `list`, `get`, `create`, `update`, `delete`, `get-folders`, `share`, `unshare`, `get-asset-value` | [Manage Assets](resources/manage-assets.md) |
| **Queues** | `list`, `get`, `create`, `update`, `delete`, `get-folders`, `share`, `unshare` | [Process Queues](resources/process-queues.md) |
| **Queue Items** | `list`, `get`, `add`, `bulk-add`, `update`, `set-progress`, `delete`, `delete-bulk`, `get-history`, `get-last-retry`, `has-video`, `set-review-status`, `set-reviewer`, `unset-reviewer`, `get-reviewers` | [Process Queues](resources/process-queues.md) |
| **Buckets** | `list`, `get`, `create`, `update`, `delete`, `share`, `unshare`, `list-folders` | [Work with Storage](resources/work-with-storage.md) |
| **Bucket Files** | `list`, `list-dirs`, `get`, `read`, `write`, `delete`, `get-download-url`, `get-upload-url` | [Work with Storage](resources/work-with-storage.md) |
| **Triggers** | `list`, `get`, `create`, `update`, `delete`, `enable`, `disable`, `history` | [Triggers & Webhooks](resources/triggers-and-webhooks.md) |
| **Libraries** | `list`, `get`, `versions`, `upload`, `download`, `delete` | [Resources overview](resources/resources.md) |
| **Webhooks** | `list`, `get`, `create`, `update`, `delete`, `ping`, `event-types` | [Triggers & Webhooks](resources/triggers-and-webhooks.md) |

---

## Solution (`uip solution`)

Create, pack, publish, and deploy solutions. See [solution/](solution/solution.md).

| Group | Key Commands | Workflow Guide |
|---|---|---|
| **Lifecycle** | `new`, `delete`, `upload` | [Develop Solution](solution/develop-solution.md) |
| **Project** | `add`, `remove`, `import` | [Develop Solution](solution/develop-solution.md) |
| **Resource** | `list`, `refresh` | [Develop Solution](solution/develop-solution.md) |
| **Pack/Publish** | `pack`, `publish` | [Pack & Deploy](solution/pack-and-deploy.md) |
| **Deploy** | `run`, `status`, `list`, `activate`, `uninstall` | [Pack & Deploy](solution/pack-and-deploy.md) |
| **Deploy Config** | `config get`, `config set`, `config link`, `config unlink` | [Pack & Deploy](solution/pack-and-deploy.md) |
| **Packages** | `list`, `delete` | [Activate & Manage](solution/activate-and-manage.md) |

---

## Traces (`uip traces`)

LLM execution trace observability. See [traces.md](traces.md).

| Command | Description |
|---|---|
| `uip traces spans get [trace-id]` | Get spans by trace ID or `--job-key` |

---

## Other Tool Groups

| Group | Command | Description |
|---|---|---|
| **Integration Service** | `uip is --help` | Connectors, connections, activities |
| **Test Manager** | `uip tm --help` | Test projects, sets, cases, executions |
| **RPA** | `uip rpa --help` | RPA workflow management |
| **MCP** | `uip mcp serve` | Start Model Context Protocol server |
| **Coded Agents** | `uip codedagent --help` | Python agent development |
| **Tools** | `uip tools list/search/install` | CLI tool management |
