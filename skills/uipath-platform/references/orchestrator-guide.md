# Orchestrator Guide

Guide to UiPath Orchestrator concepts, architecture, and CLI operations for managing automation infrastructure.

> For full option details on any command, use `--help` (e.g., `uip or folders list --help`)

## Concepts

### What is Orchestrator?

UiPath Orchestrator is a web application that manages the deployment, monitoring, scheduling, and execution of automation processes. It serves as the central hub for:

- **Deployment** — Publishing automation packages and managing their versions
- **Execution** — Starting, stopping, and monitoring automation jobs
- **Configuration** — Managing assets, queues, and environment settings
- **Scheduling** — Defining triggers and schedules for unattended execution
- **Monitoring** — Tracking job status, execution logs, and system health

### Organization Model

```
Organization (cloud.uipath.com)
  └── Tenant                        ← Isolated environment (dev, staging, prod)
        └── Folder                  ← Logical container for resources
              ├── Processes         ← Published .nupkg automation packages
              ├── Jobs              ← Running or completed executions
              ├── Assets            ← Key-value configuration store
              ├── Queues            ← Distributed work item queues
              ├── Triggers          ← Event/queue-based job triggers
              ├── Schedules         ← Cron-based job scheduling
              ├── Storage Buckets   ← File storage for automation data
              ├── Machines          ← Robot execution environments
              └── Robots            ← Attended/Unattended agents
```

### Tenants

Tenants provide complete isolation of all Orchestrator entities. Each tenant has its own set of folders, robots, assets, queues, etc. Common setup:

| Tenant | Purpose |
|---|---|
| **Development** | Building and testing automations |
| **Staging / UAT** | Pre-production validation |
| **Production** | Live automation execution |

### Folders

Modern folders are the primary organizational unit within a tenant. They support:

- **Hierarchical structure** — Nested folders for department/team organization
- **Fine-grained permissions** — Role-based access per folder
- **Automatic robot provisioning** — Robots auto-assigned based on folder membership
- **Resource isolation** — Each folder has its own processes, assets, queues

For assets, queues, and storage buckets, see [resources-guide.md](resources/resources-guide.md)

### Processes

A process is a published automation package (.nupkg) deployed to a folder. It represents an executable automation that can be triggered manually, on schedule, or via triggers.

### Jobs

A job is a single execution of a process. Jobs have states:

| State | Description |
|---|---|
| Pending | Waiting for an available robot |
| Running | Currently executing |
| Successful | Completed without errors |
| Faulted | Failed with an error |
| Stopped | Manually stopped |
| Suspended | Paused (awaiting input or approval) |

### Robots

| Type | Description |
|---|---|
| **Attended** | Works alongside a human user, triggered via UiPath Assistant. For front-office tasks needing human decisions. |
| **Unattended** | Runs autonomously in virtual environments. Managed by Orchestrator, ideal for back-office 24/7 processing. |

---

## CLI Operations — Folders

> Use `uip or folders --help` for full option details.

| Command | Description |
|---------|-------------|
| `uip or folders list` | List folders the current user has access to |
| `uip or folders list --all` | List all folders in tenant (Standard + Solution). Supports `--type`, `--name`, `--path`, `--top-level`, `--order-by` |
| `uip or folders create <name>` | Create a folder (use `--parent <key-or-path>` for nesting) |
| `uip or folders get <key>` | Get folder details by key (GUID) or path |
| `uip or folders edit <key>` | Edit folder properties |
| `uip or folders move <key>` | Move folder (use `--parent` or `--root`) |
| `uip or folders delete <key>` | Delete a folder |
| `uip or folders runtimes <key>` | List available runtimes in folder |

> **`folders list` vs `folders list --all`:** By default, `list` returns only folders the current user is assigned to. Use `--all` to see all folders in the tenant (requires appropriate permissions). `--all` enables filtering: `--type standard|solution|personal`, `--name`, `--path`, `--top-level`, `--order-by`.
>
> **Personal Workspaces:** Use `--type personal` to list personal workspaces. This returns a different shape (Key, Name, OwnerName, OwnerKey, LastLogin). `--path` and `--top-level` are not supported with `--type personal` (workspaces are flat).

```bash
uip or folders list --output json
uip or folders list --all --output json
uip or folders list --all --type standard --top-level --output json
uip or folders list --all --type personal --output json
uip or folders create "Finance" --output json
uip or folders create "Invoicing" --parent "Finance" -d "Invoice processing" --output json
```

---

## CLI Operations — Machines

> Use `uip or machines --help` for full option details.

| Command | Description |
|---------|-------------|
| `uip or machines list` | List machines — tenant-wide by default, or **per-folder** with `--folder-path`/`--folder-key` |
| `uip or machines get <key>` | Get machine details by key (GUID) |
| `uip or machines create <name>` | Create a machine template |
| `uip or machines edit <key>` | Edit machine properties |
| `uip or machines delete <key>` | Delete a machine |
| `uip or machines assign <key>` | Assign machine to folder (`--folder-path` or `--folder-key` required) |
| `uip or machines unassign <key>` | Remove machine from folder |

> Use `--all-fields` on list/get to return the full API response. Use `--limit`/`--offset` for pagination — check `Pagination.HasMore` in output.

> **Folder-scoped listing:** `uip or machines list --folder-path "Production" --output json` returns only machines assigned to that folder.

---

## CLI Operations — Processes

> Use `uip or processes --help` for full option details.

| Command | Description |
|---------|-------------|
| `uip or processes list` | List processes in folder (`--folder-path` or `--folder-key` required) |
| `uip or processes get <key>` | Get process details by key (GUID) |
| `uip or processes create <name>` | Create process binding in folder |
| `uip or processes edit <key>` | Update process properties |
| `uip or processes update-version <key>` | Update process to newer package version |
| `uip or processes rollback <key>` | Rollback process to previous version |
| `uip or processes delete <key>` | Delete a process |

> `processes create` requires `--folder-path`, `--package-key`, `--package-version`, `--runtime-type`, `--job-priority`. Optional: `--entry-point`, `--input-arguments`, `--tags`, `--auto-update`.

> Use `--all-fields` on list/get to return the full API response. Use `--limit`/`--offset` for pagination — check `Pagination.HasMore` in output.

---

## CLI Operations — Jobs

> Use `uip or jobs --help` for full option details.

| Command | Description |
|---------|-------------|
| `uip or jobs list` | List jobs (filter by `--folder-path`, `--state`, `--process-name`, date ranges) |
| `uip or jobs get <key>` | Get job details |
| `uip or jobs start <process-key>` | Start job from process (`--folder-path` required, `--input-arguments` for params) |
| `uip or jobs stop <key>` | Stop running job(s) |
| `uip or jobs restart <key>` | Restart suspended job |
| `uip or jobs resume <key>` | Resume suspended job with new input |
| `uip or jobs logs <key>` | Get execution logs |
| `uip or jobs traces <key>` | Get diagnostic traces |
| `uip or jobs history <key>` | Get status change history |

> `jobs start` supports `--input-arguments` (JSON), `--input-file` (path), `--runtime-type`, `--wait-for-completion`, `--timeout`, `--attachment`. `jobs stop` requires `--strategy` (Kill or Graceful).

> Use `--all-fields` on list/get to return the full API response. Use `--limit`/`--offset` for pagination — check `Pagination.HasMore` in output.

---

## CLI Operations — Packages

> Use `uip or packages --help` for full option details.

| Command | Description |
|---------|-------------|
| `uip or packages list` | List automation packages in feed |
| `uip or packages get <key>` | Get package details |
| `uip or packages versions <package-id>` | List all versions of a package |
| `uip or packages entry-points <key>` | List entry points in package |
| `uip or packages upload <file>` | Upload .nupkg to feed |
| `uip or packages download <key>` | Download .nupkg from feed (`--destination` required, key format: `PackageId:Version`) |

> Use `--all-fields` on list/get to return the full API response. Use `--limit`/`--offset` for pagination — check `Pagination.HasMore` in output.

---

## CLI Operations — Users

> Use `uip or users --help` for full option details.

| Command | Description |
|---------|-------------|
| `uip or users list` | List users (filter by `--username`, `--email`, `--key`) |
| `uip or users get <key>` | Get user details |
| `uip or users create <username>` | Create user |
| `uip or users edit <key>` | Edit user properties |
| `uip or users delete <key>` | Delete user |
| `uip or users assign-roles <key>` | Assign tenant/folder roles to user |
| `uip or users set-session-flags <key>` | Configure session capabilities (attended/unattended/login) |
| `uip or users set-unattended-execution <key>` | Configure unattended robot for user |
| `uip or users list-in-folder` | List users assigned to a folder with their folder-level roles (`--folder-path` or `--folder-key` required) |
| `uip or users list-available` | List users available to assign to folders |
| `uip or users current` | Get current user details |
| `uip or users assign <key>` | Assign user to folder with roles |
| `uip or users unassign <key>` | Remove user from folder |

> Use `--all-fields` on list/get to return the full API response. Use `--limit`/`--offset` for pagination — check `Pagination.HasMore` in output.

> **Credential stores:** When setting `--unattended-password` on a user whose credential store is read-only, the CLI automatically treats the value as `credentialExternalName` (external secret reference) instead of a literal password. No separate flag is needed.

---

## CLI Operations — Other

| Group | Key Commands |
|-------|-------------|
| **Settings** | `uip or settings list`, `update <key> <value>`, `get <key>`, `execution`, `timezones` |
| **Roles** | `uip or roles list-roles`, `list-permissions`, `get-role <key>`, `create-role`, `edit-role <key>`, `delete-role <key>`, `list-role-users <key>`, `set-role-users <key>`, `assign` |
| **Sessions** | `uip or sessions list-attended-sessions`, `list-machines-sessions`, `list-unattended-sessions`, `list-usernames`, `list-user-executors`, `toggle-debug-mode`, `delete-inactive`, `set-maintenance-mode` |
| **Licenses** | `uip or licenses list --type <type>`, `toggle`, `info` |
| **Calendars** | `uip or calendars list`, `create`, `add-excluded-dates`, `remove-excluded-dates` |
| **Audit Logs** | `uip or audit-logs list` (filter by `--component`, `--action`, `--user`, date range) |
| **Feeds** | `uip or feeds list` |
| **Credential Stores** | `uip or credential-stores list`, `get <key>` |
| **Attachments** | `uip or attachments list <job-key>`, `download <attachment-id>` |

---

## CLI Operations — Assets, Queues, Triggers (Resource Tool)

> **Note:** Assets, queues, triggers, storage buckets, libraries, and webhooks are managed by the Resource tool.
> Use `uip resource <command>` instead. See [resources/resources-guide.md](resources/resources-guide.md) for full details.

---

## CLI Output Behavior

### Pagination

All list commands return a `Pagination` block in their output:

```json
{
  "Result": "Success",
  "Code": "PackageList",
  "Pagination": { "Returned": 50, "Limit": 50, "Offset": 0, "HasMore": true },
  "Data": [...]
}
```

**When `HasMore` is `true`, there are more results.** Increase `--offset` by `--limit` to fetch the next page. Continue until `HasMore` is `false` or `Returned < Limit`.

### All Fields (`--all-fields`)

Orchestrator tool list/get commands return a curated subset of fields by default. Use `--all-fields` to get the complete raw API response:

```bash
# Default — curated fields (Key, Title, Version, etc.)
uip or packages list --output json

# Full DTO — all fields from the API
uip or packages list --all-fields --output json
```

Available on: `packages`, `processes`, `jobs`, `machines`, `users` (list and get).

> **When to use:** If you need a field that's not in the default output (e.g., creation date, video recording setting, detailed privilege info), add `--all-fields`.

---

## Agent Best Practices

### Before Creating Resources or Starting Jobs

Before running destructive or side-effect commands, **ask the user** to confirm details:

- **`jobs start`**: Check if the process has input arguments (use `packages entry-points <key>` to inspect). Ask the user for parameter values. Always specify `--folder-path` and `--input-arguments` explicitly.
- **`storage-buckets create`**: Ask about storage type and configuration — don't just create with defaults.
- **`triggers create`**: Confirm trigger type (time/queue/api), cron expression, timezone, and target process.
- **Package uploads/deployments**: Confirm the target folder or tenant. Don't silently upload to tenant level when the user asked for a specific folder.

### Handling Pagination

When listing resources, always check the `Pagination.HasMore` field. If true, fetch additional pages. Don't assume the first page contains all results.

### Handling 403 Errors

A 403 doesn't always mean insufficient permissions. It can also mean a **Governance Policy** is blocking the action. When you get a 403:
1. Report the exact error message to the user
2. Don't assume it's a permission issue — it may be a policy restriction
3. Suggest the user check Governance Policies in the Orchestrator UI

---

## Common Patterns

### Environment Setup Workflow

Set up a new environment from scratch using the CLI:

```bash
uip login --output json
uip login tenant set "Production" --output json

uip or folders create "Finance" --output json
# Use the folder ID from the response (e.g., 12345) for nested folders
uip or folders create "Invoicing" --parent 12345 --output json
uip or folders create "Reporting" --parent 12345 --output json

uip resource assets create 12345 "ApiBaseUrl" "https://api.example.com" --output json
uip resource assets create 12345 "ApiKey" "sk-production-key" --type Secret --output json
uip resource assets create 12345 "MaxRetries" "3" --type Integer --output json

uip solution pack ./MySolution ./output --version "1.0.0" --output json
uip solution publish ./output/MySolution.1.0.0.zip --output json
```

### Multi-Tenant Promotion

Promote an automation from development to production:

```bash
uip solution pack ./MySolution ./output --version "1.0.0" --output json

uip login tenant set "Staging" --output json
uip solution publish ./output/MySolution.1.0.0.zip --output json

# After validation, promote to production
uip login tenant set "Production" --output json
uip solution publish ./output/MySolution.1.0.0.zip --output json
```

### Accessing Assets from Code

In coded workflows, assets are accessed via the `system` service:

```csharp
string apiUrl = system.GetAsset("ApiBaseUrl").ToString();

var credential = system.GetCredential("ServiceAccount");
string username = credential.Username;
string password = credential.Password;
```

### Using Queues from Code

```csharp
system.AddQueueItem("InvoiceQueue", new Dictionary<string, object>
{
    { "InvoiceId", "INV-001" },
    { "Amount", 1500.00 },
    { "CustomerName", "Acme Corp" }
});

var item = system.GetQueueItem("InvoiceQueue");
string invoiceId = item.SpecificContent["InvoiceId"].ToString();
```

---

## REST API Reference

When CLI commands are insufficient, use the Orchestrator REST API directly. **Always check `uip or --help` and `uip resource --help` first** — most operations are covered by the CLI. Requires an access token (stored at `~/.uipath/.auth` after login).

### Authentication Header

All requests need:
```
Authorization: Bearer <UIPATH_ACCESS_TOKEN>
X-UIPATH-OrganizationUnitId: <FOLDER_ID>
```

### Base URL Pattern

```
${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/
```

### Upload Package

```bash
curl -X POST "${BASE}/Processes/UiPath.Server.Configuration.OData.UploadPackage" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -F "file=@./MyProject.1.0.0.nupkg"
```

### Create Process (Release)

```bash
curl -X POST "${BASE}/Releases" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{"Name":"MyProcess","ProcessKey":"MyProject","ProcessVersion":"1.0.0"}'
```

Response includes `Key` (release key) needed to start jobs.

### Start Job

```bash
curl -X POST "${BASE}/Jobs/UiPath.Server.Configuration.OData.StartJobs" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{"startInfo":{"ReleaseKey":"<RELEASE_KEY>","Strategy":"ModernJobsCount","JobsCount":1,"RuntimeType":"Unattended","InputArguments":"{}"}}'
```

**RuntimeType options:** `Unattended`, `Development`, `Attended`, `NonProduction`

> **Common error:** "No runtimes configured" (error 2818) means the target folder has no machine templates with the selected runtime type assigned. Fix: assign machines to the folder in Orchestrator UI.

### List Processes

```bash
curl -G "${BASE}/Releases" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  --data-urlencode "\$filter=ProcessKey eq 'MyProject'"
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| "project is already opened in another Studio instance" | Studio has the project DB locked | `rpa-tool close-project` before packing |
| "No runtimes configured" (error 2818) | Target folder has no robot machines assigned | Assign machine templates in Orchestrator > Folder Settings > Machines |
| "Azure CLI is not installed" during `solution pack` | Pack command needs Azure CLI for NuGet feed auth | Install Azure CLI |
| Token expired | Access token from `~/.uipath/.auth` has expired | Re-run `uip login` |
