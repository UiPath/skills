# UiPath CLI (`uip`) Command Reference

> **Quick reference index.** Use `--help` for full option details on any command.

**Global flags:**
- `--output json` — always use when calling programmatically
- `--output-filter <expr>` — JMESPath filter for JSON output
- `--verbose` — enable debug logging

Tenant-scoped commands use the active tenant from `uip login`. Switch tenants with `uip login tenant set <name>`. Do not pass per-command `--tenant`; legacy hidden overrides only exist for backwards compatibility and emit a deprecation warning.

**List command flags:**
- `--limit <N>` / `--offset <N>` — pagination. Check `Pagination.HasMore` in output.
- `--order-by <field>` — sort results (e.g., `Name asc`, `Id desc`)
- `--all-fields` — (Orchestrator tool only) return raw DTO instead of the
  curated PascalCase projection. Resource tool returns full DTO by default
  on every list/get and does not expose this flag.

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

Manage folders, jobs, processes, machines, users, packages, and more. See [`uipath-orchestrator`](orchestrator/orchestrator.md).

| Group | Key Commands | Workflow Guide |
|---|---|---|
| **Folders** | `list [--all]`, `get`, `create`, `edit`, `delete`, `move`, `runtimes` | [Setup Environment](orchestrator/setup-environment.md) |
| **Jobs** | `list`, `get`, `start`, `stop`, `restart`, `resume`, `logs [--export]`, `traces`, `healing-data`, `history` | [Run Jobs](orchestrator/run-jobs.md) |
| **Processes** | `list`, `get`, `resources`, `version-history`, `create`, `edit`, `update-version`, `rollback`, `delete` | [Run Jobs](orchestrator/run-jobs.md) |
| **Packages** | `list`, `get`, `versions`, `entry-points`, `upload`, `download` | [Run Jobs](orchestrator/run-jobs.md) |
| **Machines** | `list`, `get`, `create`, `edit`, `delete`, `assign`, `unassign` | [Setup Environment](orchestrator/setup-environment.md) |
| **Users** | `list`, `list-in-folder`, `list-available`, `get`, `create`, `edit`, `delete`, `current`, `assign`, `unassign`, `assign-roles` | [Setup Environment](orchestrator/setup-environment.md) |
| **Roles** | `list`, `permissions`, `get`, `create`, `edit`, `delete`, `users list`, `users set`, `user-roles list`, `user-permissions list`, `assign` | [Setup Environment](orchestrator/setup-environment.md) |
| **Sessions** | `attended list`, `unattended list`, `machines list <machine-key>`, `list-usernames`, `list-user-executors`, `toggle-debug-mode`, `delete-inactive`, `set-maintenance-mode` | [Manage Sessions](orchestrator/manage-sessions.md) |
| **Settings** | `list`, `get`, `update`, `execution`, `timezones` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Calendars** | `list`, `get`, `create`, `update`, `delete` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Licenses** | `list --type`, `toggle`, `info` | [Setup Environment](orchestrator/setup-environment.md) |
| **Audit Logs** | `list [--export]` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Credential Stores** | `list`, `get` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Feeds** | `list` | [Tenant Admin](orchestrator/tenant-admin.md) |
| **Attachments** | `list --job-key`, `download` | [Tenant Admin](orchestrator/tenant-admin.md) |

---

## Resource (`uip resource`)

Manage assets, queues, triggers, buckets, libraries, and webhooks. See [`uipath-resources`](resources/resources.md).

| Group | Key Commands | Workflow Guide |
|---|---|---|
| **Assets** | `list`, `get`, `create`, `update`, `delete`, `get-folders`, `share`, `unshare`, `get-asset-value` | [Manage Assets](resources/manage-assets.md) |
| **Queues** | `list`, `get`, `create`, `update`, `delete`, `get-folders`, `get-stats`, `share`, `unshare` | [Process Queues](resources/process-queues.md) |
| **Queue Items** | `list`, `get`, `add`, `bulk-add`, `update`, `set-progress`, `delete`, `delete-bulk`, `get-history`, `get-last-retry`, `has-video`, `set-review-status`, `set-reviewer`, `unset-reviewer`, `get-reviewers` | [Process Queues](resources/process-queues.md) |
| **Buckets** | `list`, `get`, `create`, `update`, `delete`, `share`, `unshare`, `list-folders` | [Work with Storage](resources/work-with-storage.md) |
| **Bucket Files** | `list`, `list-dirs`, `get`, `download`, `upload`, `delete`, `get-download-url`, `get-upload-url` | [Work with Storage](resources/work-with-storage.md) |
| **Triggers** | `list`, `get`, `create`, `update [--enabled\|--disabled]`, `delete`, `history` | [Triggers & Webhooks](resources/triggers-and-webhooks.md) |
| **Libraries** | `list`, `get`, `versions`, `upload`, `download`, `delete` | [Resources overview](resources/resources.md) |
| **Webhooks** | `list`, `get`, `create`, `update`, `delete`, `ping`, `event-types` | [Triggers & Webhooks](resources/triggers-and-webhooks.md) |

---

## Solution (`uip solution`)

Create, pack, publish, and deploy solutions. See [`uipath-solution`](solution/solution.md).

| Group | Key Commands | Workflow Guide |
|---|---|---|
| **Lifecycle** | `new`, `delete`, `upload`, `download` | [Develop Solution](solution/develop-solution.md) |
| **Project** | `add`, `remove`, `import`, `list` | [Develop Solution](solution/develop-solution.md) |
| **Resource** | `list`, `refresh`, `get` | [Develop Solution](solution/develop-solution.md) |
| **Pack/Publish** | `pack`, `publish` | [Pack & Deploy](solution/pack-and-deploy.md) |
| **Deploy** | `run`, `status`, `list`, `activate`, `uninstall` | [Pack & Deploy](solution/pack-and-deploy.md) |
| **Deploy Config** | `config get`, `config set`, `config link`, `config unlink` | [Pack & Deploy](solution/pack-and-deploy.md) |
| **Packages** | `list`, `delete`, `download` | [Activate & Manage](solution/activate-and-manage.md) |

---

## Platform Tool (`uip platform`)

Manage organization-level licensing — tenant allocations, user/group bundle assignments, and consumables reporting. See [`licensing/licensing.md`](licensing/licensing.md).

| Group | Key Commands | Workflow Guide |
|---|---|---|
| **Tenants Licenses** | `tenants licenses get <tenant-key>`, `tenants licenses set <tenant-key> --input <path>` | [Tenant Allocations](licensing/tenant-allocations.md) |
| **Users Licenses** | `users licenses available`, `users licenses get <user>`, `users licenses set <user> --input <path>` | [User & Group Licenses](licensing/user-licenses-allocations.md) |
| **Groups Rules** | `groups rules get [--limit --offset --sort-by --sort-order]`, `groups rules details <group>`, `groups rules set <group> --input <path>` | [User & Group Licenses](licensing/user-licenses-allocations.md) |
| **Consumables** | `licenses consumables get --mode {summary\|daily\|folders} [--tenant --unit --start-date --end-date]` | [Consumables Report](licensing/consumables-report.md) |

All `uip platform` commands accept `--organization <account-id>` to override the org from the current login.

---

## Traces (`uip traces`)

LLM execution trace observability and feedback annotation. See [traces/traces.md](traces/traces.md) (spans) and [traces/feedback.md](traces/feedback.md) (feedback).

| Command | Description |
|---|---|
| `uip traces spans get [trace-id]` | Get spans by trace ID or `--job-key` |
| `uip traces feedback create` | Add positive/negative feedback to a trace |
| `uip traces feedback get <id>` | Fetch one feedback record |
| `uip traces feedback list` | List feedback for a trace |
| `uip traces feedback list detailed` | Cross-trace feedback with span context |
| `uip traces feedback update <id>` | Change sentiment, comment, or categories |
| `uip traces feedback delete <id>` | Remove feedback |

---

## Other Tool Groups

| Group | Command | Description |
|---|---|---|
| **Integration Service** | `uip is --help` | See [`uipath-integration-service`](integration-service/integration-service.md) |
| **Traces** | `uip traces spans get [trace-id]` | LLM execution trace observability (`--job-key` to scope) |
| **Test Manager** | `uip tm --help` | Test projects, sets, cases, executions |
| **RPA** | `uip rpa --help` | RPA workflow management |
| **MCP** | `uip mcp serve` | Start Model Context Protocol server |
| **Coded Agents** | `uip codedagent --help` | Python agent development |
| **Tools** | `uip tools list/search/install` | CLI tool management |

---

## Naming gotchas

- Resource sub-nouns are **plural and hyphenated where shown**: `buckets`, `queues`, `assets`, `libraries`, `queue-items`, `bucket-files`. Never singular, never `queueitems`/`bucketfiles`.
- The Orchestrator group prefix is `or`, not `orchestrator` (`uip orchestrator` does not exist).
