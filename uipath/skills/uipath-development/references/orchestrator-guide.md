# Orchestrator Guide

Guide to UiPath Orchestrator concepts, architecture, and CLI operations for managing automation infrastructure.

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

**Folder types:**

| Type | Description |
|---|---|
| Standard | Default folder type for organizing automations |
| Personal | User-specific workspace |
| Virtual | Logical grouping without physical separation |
| Solution | Created automatically by solution deployment |
| DebugSolution | Debug variant of a solution folder |

### Assets

Assets are key-value pairs stored in Orchestrator that automations can read at runtime. They externalize configuration so the same automation package works across environments.

**Asset types:**

| Type | Description | Example |
|---|---|---|
| Text | Plain text string | API URL, file path |
| Bool | Boolean value | Feature flag |
| Integer | Numeric value | Retry count, timeout |
| Credential | Username + password | Service account |
| Secret | Encrypted value | API key, token |
| DBConnectionString | Database connection | SQL Server connection |
| HttpConnectionString | HTTP endpoint | REST API base URL |
| WindowsCredential | Windows credential pair | Domain login |

**Asset scope:**

| Scope | Description |
|---|---|
| Global | Same value for all robots |
| PerRobot | Different value per robot (allows overrides) |

### Queues

Queues enable distributed processing of work items across multiple robots:

1. **Dispatcher** automation adds items to a queue
2. **Performer** automation(s) process items from the queue
3. Orchestrator handles distribution, retries, and status tracking

Each queue item has:
- **Specific Content** — JSON payload with the data to process
- **Status** — New, InProgress, Successful, Failed, Abandoned, Deleted
- **Priority** — High, Normal, Low
- **Retry** — Automatic retry on failure (configurable)

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

### List Folders

```bash
uip or folders list --format json
```

With OData filter:
```bash
uip or folders list --filter "DisplayName eq 'Finance'" --format json
```

### Create a Folder

```bash
# Top-level folder
uip or folders create "Finance" --format json

# Nested folder
uip or folders create "Invoicing" --parent 12345 --description "Invoice processing" --format json
```

### Get Folder Details

```bash
uip or folders get 12345 --format json
```

### Get All Folders for Current User

```bash
uip or folders get-all-for-current-user --take 100 --format json
```

### Edit a Folder

```bash
uip or folders edit 12345 --name "Finance Team" --description "Updated description" --format json
```

### Move a Folder

```bash
uip or folders move 12345 67890 --format json
```

### Delete a Folder

```bash
uip or folders delete 12345 --format json
```

---

## CLI Operations — Assets

### List Assets in a Folder

```bash
uip or assets list 12345 --format json
```

With OData filter:
```bash
uip or assets list 12345 --filter "Name eq 'ApiKey'" --count 100 --format json
```

### Get Asset by ID

```bash
uip or assets get 12345 67890 --format json
```

### Create Assets

```bash
# Text asset
uip or assets create 12345 "ApiBaseUrl" "https://api.example.com" --format json

# Secret asset
uip or assets create 12345 "ApiKey" "sk-abc123" --type Secret --format json

# Integer asset
uip or assets create 12345 "MaxRetries" "3" --type Integer --description "Max retry attempts" --format json

# Credential asset
uip or assets create 12345 "ServiceAccount" "user:password" --type Credential --format json

# Asset with tags
uip or assets create 12345 "Timeout" "30" --type Integer --tags "config,performance" --format json
```

### Delete an Asset

```bash
uip or assets delete 12345 67890 --format json
```

---

## Common Patterns

### Environment Setup Workflow

Set up a new environment from scratch using the CLI:

```bash
# 1. Login
uip login --format json

# 2. Select tenant
uip login tenant set "Production" --format json

# 3. Create folder structure
uip or folders create "Finance" --format json
# Note the folder ID from the response, e.g., 12345

uip or folders create "Invoicing" --parent 12345 --format json
uip or folders create "Reporting" --parent 12345 --format json

# 4. Create assets in the folder
uip or assets create 12345 "ApiBaseUrl" "https://api.example.com" --format json
uip or assets create 12345 "ApiKey" "sk-production-key" --type Secret --format json
uip or assets create 12345 "MaxRetries" "3" --type Integer --format json

# 5. Pack and publish solution
uip solution pack ./MySolution ./output --version "1.0.0" --format json
uip solution publish ./output/MySolution.1.0.0.zip --format json
```

### Multi-Tenant Promotion

Promote an automation from development to production:

```bash
# 1. Pack in dev
uip solution pack ./MySolution ./output --version "1.0.0" --format json

# 2. Publish to staging
uip login tenant set "Staging" --format json
uip solution publish ./output/MySolution.1.0.0.zip --format json

# 3. After validation, publish to production
uip login tenant set "Production" --format json
uip solution publish ./output/MySolution.1.0.0.zip --format json
```

### Accessing Assets from Code

In coded workflows, assets are accessed via the `system` service:

```csharp
// Read a text asset
string apiUrl = system.GetAsset("ApiBaseUrl").ToString();

// Read a credential asset
var credential = system.GetCredential("ServiceAccount");
string username = credential.Username;
string password = credential.Password;
```

### Using Queues from Code

```csharp
// Add item to queue
system.AddQueueItem("InvoiceQueue", new Dictionary<string, object>
{
    { "InvoiceId", "INV-001" },
    { "Amount", 1500.00 },
    { "CustomerName", "Acme Corp" }
});

// Get next queue item
var item = system.GetQueueItem("InvoiceQueue");
string invoiceId = item.SpecificContent["InvoiceId"].ToString();
```

---

## REST API Reference

When CLI commands are insufficient or unavailable (e.g., asset management), use the Orchestrator REST API directly. Requires an access token (stored at `~/.uipcli/.env` after login).

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
| Token expired | Access token from `~/.uipcli/.env` has expired | Re-run `uip login` |
