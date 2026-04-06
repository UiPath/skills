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
| `uip or folders list` | List all folders |
| `uip or folders create <name>` | Create a folder (use `--parent <id>` for nesting) |
| `uip or folders get <id>` | Get folder details |
| `uip or folders edit <id>` | Edit folder properties |
| `uip or folders move <id> <parent-id>` | Move folder |
| `uip or folders delete <id>` | Delete a folder |

```bash
uip or folders list --output json
uip or folders create "Finance" --output json
uip or folders create "Invoicing" --parent 12345 -d "Invoice processing" --output json
```

---

## CLI Operations — Assets

> **Note:** Asset management is handled by the Resources tool, not the Orchestrator tool.
> Use `uip resources assets` commands instead. See [resources/resources-guide.md](resources/resources-guide.md) for full details.

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

uip resources assets create 12345 "ApiBaseUrl" "https://api.example.com" --output json
uip resources assets create 12345 "ApiKey" "sk-production-key" --type Secret --output json
uip resources assets create 12345 "MaxRetries" "3" --type Integer --output json

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

When CLI commands are insufficient or unavailable (e.g., asset management), use the Orchestrator REST API directly. Requires an access token (stored at `~/.uipath/.auth` after login).

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
