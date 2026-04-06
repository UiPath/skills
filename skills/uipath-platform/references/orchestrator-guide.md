# Orchestrator Guide

UiPath Orchestrator concepts and CLI operations for managing automation infrastructure.

## Organization Model

```
Organization (cloud.uipath.com)
  └── Tenant                  ← Isolated environment (dev, staging, prod)
        └── Folder            ← Logical container for resources
              ├── Processes, Jobs, Assets, Queues, Triggers
              ├── Schedules, Storage Buckets, Machines, Robots
```

**Tenants** provide complete isolation. Common setup: Development, Staging, Production.

**Folders** are the primary organizational unit — hierarchical, with fine-grained permissions and resource isolation.

## Domain Guides

| Domain | Guide | CLI Prefix |
|---|---|---|
| Jobs | [jobs-guide.md](jobs-guide.md) | `uip or jobs` |
| Processes | [processes-guide.md](processes-guide.md) | `uip or processes` |
| Packages & Feeds | [packages-guide.md](packages-guide.md) | `uip or packages`, `uip or feeds` |
| Machines | [machines-guide.md](machines-guide.md) | `uip or machines` |
| Users & Roles | [access-control-guide.md](access-control-guide.md) | `uip or users`, `uip or roles` |
| Licenses | [licenses-guide.md](licenses-guide.md) | `uip or licenses` |
| Assets & Queues | [resources/resources-guide.md](resources/resources-guide.md) | `uip resources` |

---

## Folder Commands

| Command | Description |
|---|---|
| `uip or folders list` | List all folders. `--name` filters by DisplayName only (not path). |
| `uip or folders create <name>` | Create (`--parent <key>` for nesting). Response has numeric ID but not GUID key — run `folders get` to retrieve the key. |
| `uip or folders get <key-or-path>` | Get details |
| `uip or folders edit <key-or-path>` | Edit properties |
| `uip or folders move <key-or-path>` | Move to new parent (`--root` for top level) |
| `uip or folders delete <key-or-path>` | Delete |
| `uip or folders runtimes <key-or-path>` | Runtime slot capacity |

---

## UI-Only Operations (No CLI Support)

Construct deep links for features only available in the web UI:

```bash
source ~/.uipath/.auth
echo "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/#/<PAGE_PATH>"
```

### Triggers

| Type | UI Path |
|---|---|
| Time triggers | `triggers/time` |
| Queue triggers | `triggers/queue` |
| Event triggers | `triggers/event` |
| API triggers | `triggers/api` |
| Create | `triggers/<TYPE>/add` |

### Webhooks

| UI Path | Description |
|---|---|
| `webhooks` | List all |
| `webhooks/add` | Create (select events like `job.faulted`, `job.completed`) |

### CLI vs UI Coverage

| CLI Available | UI Only |
|---|---|
| Folders, Jobs, Processes, Packages, Machines, Users, Roles, Licenses, Assets, Queues, Buckets | Triggers, Webhooks, Audit logs, Settings |

---

## REST API (Fallback)

When CLI is insufficient, use the REST API with the token from `~/.uipath/.auth`:

```bash
source ~/.uipath/.auth
BASE="${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata"
```

All requests need: `Authorization: Bearer <UIPATH_ACCESS_TOKEN>` and `X-UIPATH-OrganizationUnitId: <FOLDER_ID>`.

### Upload Package

```bash
curl -X POST "${BASE}/Processes/UiPath.Server.Configuration.OData.UploadPackage" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -F "file=@./MyProject.1.0.0.nupkg"
```

### Create Process

```bash
curl -X POST "${BASE}/Releases" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{"Name":"MyProcess","ProcessKey":"MyProject","ProcessVersion":"1.0.0"}'
```

### Start Job

```bash
curl -X POST "${BASE}/Jobs/UiPath.Server.Configuration.OData.StartJobs" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{"startInfo":{"ReleaseKey":"<RELEASE_KEY>","Strategy":"ModernJobsCount","JobsCount":1,"RuntimeType":"Unattended","InputArguments":"{}"}}'
```

**RuntimeType options:** `Unattended`, `Development`, `Attended`, `NonProduction`

---

## Accessing Assets/Queues from Code

```csharp
// Assets
string apiUrl = system.GetAsset("ApiBaseUrl").ToString();
var cred = system.GetCredential("ServiceAccount");

// Queues
system.AddQueueItem("InvoiceQueue", new Dictionary<string, object>
{
    { "InvoiceId", "INV-001" }, { "Amount", 1500.00 }
});
var item = system.GetQueueItem("InvoiceQueue");
```
