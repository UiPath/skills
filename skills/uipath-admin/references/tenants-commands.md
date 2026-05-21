# Tenants CLI Command Reference

Complete reference for all `uip admin tenants` commands — tenant lifecycle and tenant-level service provisioning (Organization Management Service / OMS).

For organization commands, see [organizations-commands.md](organizations-commands.md). For workflow-level guidance, see [tenant-management.md](tenant-management.md).

## Global Flags

Every command accepts these flags (omitted from per-command tables):

| Flag | Description |
|------|-------------|
| `--output <format>` | Output format: `json`, `table`, `yaml`, `plain` (default: json) |
| `--output-filter <expression>` | JMESPath expression to filter output |
| `--log-level <level>` | Log level: `debug`, `info`, `warn`, `error` (default: info) |
| `--log-file <path>` | Write logs to file instead of stderr |
| `--login-validity <minutes>` | Override token validity — forces refresh if token expires within this window |

Organization is resolved automatically from the active login session.

## Prerequisites

```bash
uip login status --output json
```

If not logged in: `uip login`.

## Concepts

- **Async vs synchronous.** Tenant lifecycle (`create`, `update`, `delete`, `enable`, `disable`) is async — every mutation returns an `operationId`. `list` / `get` and all `services` subcommands are synchronous (200 OK with no body for service mutations).
- **Single poll endpoint.** All async OMS operations are polled through `uip admin organizations operation get <OPERATION_ID>` — there is no `tenants operation get`.
- **Soft-delete only.** `tenants delete` has no hard-delete flag. Reversible via the restore flow.
- **Login-tenant default.** `tenants get`, `update`, `delete`, `enable`, `disable` accept the tenant id positionally — omit it to target the login tenant. Convenient for read ops; **always pass an explicit `<TENANT_ID>` for `delete`, `disable`, and `services remove`** to avoid targeting the wrong tenant.
- **Region matters at create.** `tenants create` requires `--region`; run `organizations regions list` first to confirm acceptable values.
- **Tenant service catalog is region-aware.** `tenants services list-available --region <REGION>` returns a per-region catalog.
- **Service capability gaps — disable / remove are not universal.** Some services accept the call and return `Success` but the state never changes server-side:
  - **Disable not honored** (no-op): Integration Service (`connections`), Data Fabric (`dataservice`), Insights (`insights`).
  - **Remove not honored** (rejected or no-op): Orchestrator (`orchestrator`), Maestro (`maestro`), Integration Service (`connections`), Data Fabric (`dataservice`), Insights (`insights`), Test Manager (`testmanager`).

  **Pre-flight: warn the user before submitting.** Don't silently issue a no-op. Render: *"Service `<X>` cannot be {disabled|removed} via the CLI — it's pinned by the platform. The call will return Success but the service will stay {Enabled|provisioned}. To deprovision, revoke the org entitlement via the UiPath Portal. Continue anyway, or skip `<X>`?"* Skip → drop from the call. Continue → run AND warn in the post-state summary.

  Because the CLI returns 200 OK either way, the success code is never proof of state change. After any `services disable` / `services remove`, verify with `tenants get <TENANT_ID> --output-filter "tenantServiceInstances[?serviceType=='<SVC>']"` and inspect the `status` field on the returned instance.

---

## Tenant Lifecycle — `uip admin tenants`

### `tenants list`

List tenants in the caller's organization.

```bash
uip admin tenants list --output json
uip admin tenants list --filter "<NAME_FRAGMENT>" --output json
uip admin tenants list --status Enabled --service orchestrator --output json
uip admin tenants list --include-services --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--filter <fragment>` | No | Case-insensitive substring match on tenant name (client-side) |
| `--service <type>` | No | Only tenants with the given service provisioned |
| `--status <status>` | No | Exact match on lifecycle status (`Enabled`, `Disabled`, `Updating`, `Deleted`) |
| `--environment <env>` | No | Filter by environment tag (client-side) |
| `--include-services` | No | Return each tenant's `services` array inline (saves a second call) |

**Output code:** `OmsTenantsList`.

### `tenants get`

Fetch a tenant by id (or the login tenant if omitted).

```bash
uip admin tenants get <TENANT_ID> --output json
uip admin tenants get --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<TENANT_ID>` | No | Tenant UUID — defaults to login tenant |

**Output code:** `OmsTenantGet`.

### `tenants create`

Create a new tenant. **Async** — returns both the new `id` and an `operationId`.

> **`--file` is required in practice.** The server marks the `services` field required on `CreateTenantRequestDto`, but the inline path (`--name --region --environment`) does not populate it — a pure inline call returns `HTTP 400: The Services field is required.` Use a JSON file with the full body for any real create.

```bash
uip admin tenants create --file ./tenant.json --output json
```

`./tenant.json` (`CreateTenantRequestDto`):

```json
{
  "name": "<TENANT_NAME>",
  "region": "<REGION>",
  "environment": "<ENV>",
  "services": ["<SERVICE_NAME>", "<SERVICE_NAME>", "..."]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Tenant display name. Alphanumeric, 2–32 chars, starts with a letter. |
| `region` | Yes | Provisioning region — resolve via `organizations regions list`. |
| `environment` | No | Environment tag: `Production`, `NonProduction`, or `Development`. |
| `services` | **Yes** | **Plain string array of service names** to provision (catalog `name` field, e.g. `taskmining`, `du`). NOT a `{name: true}` map — that's the `services add` shape; OMS rejects it on create. Resolve via the **Default-provision filter** in the `services list-available` section below — the catalog is region-aware, never hardcode names. Platform-pinned services (`isAlwaysProvision === true`) are added automatically regardless. |
| `customProperties` | No | Free-form key/value bag carried with the tenant. |
| `color` | No | UI color tag. |
| `isDefaultTenant` | No | Mark as the org's default tenant. |

**Output code:** `OmsTenantCreated`.

### `tenants update`

Patch editable fields on a tenant. **Async** — returns `operationId`.

```bash
uip admin tenants update <TENANT_ID> \
  --name "<NEW_NAME>" \
  --region "<NEW_REGION>" \
  --environment "<NEW_ENV>" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<TENANT_ID>` | No | Tenant UUID — defaults to login tenant |
| `--name <name>` | No | New display name |
| `--region <region>` | No | New region |
| `--environment <env>` | No | New environment tag |
| `--file <path>` | Alternative | Full `TenantUpdateDto` body (required for `services{}`, `customProperties`, `color`) |

At least one field flag (or `--file`) is required. **Output code:** `OmsTenantUpdated`.

### `tenants delete`

Soft-delete a tenant. **Async** — returns `operationId`. No hard-delete flag.

```bash
uip admin tenants delete <TENANT_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<TENANT_ID>` | No | Tenant UUID — defaults to login tenant. **Always pass explicitly for delete.** |

Confirm with user. Restoration goes through the support / restore flow.

**Output code:** `OmsTenantDeleted`.

### `tenants enable`

Activate a tenant. **Async** — returns `operationId`.

```bash
uip admin tenants enable <TENANT_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<TENANT_ID>` | No | Tenant UUID — defaults to login tenant |

**Output code:** `OmsTenantEnabled`.

### `tenants disable`

Disable a tenant. **Async** — returns `operationId`.

```bash
uip admin tenants disable <TENANT_ID> --reason "<FREE_TEXT_REASON>" --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<TENANT_ID>` | No | Tenant UUID — defaults to login tenant. **Always pass explicitly for disable.** |
| `--reason <text>` | No | Free-text reason — recorded with the action for audit |

**Output code:** `OmsTenantDisabled`.

---

## Tenant-Level Services — `uip admin tenants services`

All service subcommands are **synchronous** (200 OK with no body, no polling).

> **`list` vs `list-available` are different sets — never merge them.** `services list` returns the **currently provisioned** tenant instances (each with a `status`: `Enabled` / `Disabled` / `Deleted`). `services list-available --region <R>` returns the **region-aware catalog** of provisionable service types (no status). Always present them as two clearly labeled sections. See [tenant-management.md — List Tenant Services](tenant-management.md#workflow-list-tenant-services--provisioned-vs-available).

> **Always name the tenant before any service mutation.** `services add/enable/disable/remove` default `--tenant-id` to the **login tenant** — silently. Resolve `<TENANT_ID>` to a name (`tenants get <ID> --output json`) and echo it to the user before running the command, especially for `remove`.

### `services list`

List **currently provisioned** tenant-level service instances. Each row carries a lifecycle `status` — `Enabled`, `Disabled`, or `Deleted` (soft-deleted). Surface the status field in any presentation; flag `Deleted` entries explicitly.

```bash
uip admin tenants services list --output json
uip admin tenants services list --tenant-id <TENANT_ID> --output json
uip admin tenants services list --service orchestrator --output json
uip admin tenants services list --region "<REGION>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Tenant UUID — defaults to login tenant |
| `--service <type>` | No | Filter by service type (client-side) |
| `--region <region>` | No | Filter by region (client-side) |

All filters are client-side. **Output code:** `OmsTenantServicesList`.

### `services list-available`

List the **catalog** of services that can be provisioned for a tenant in a given region. **Region-aware** — the catalog varies by region. Catalog only: entries are not provisioned and have no lifecycle status. Do not show a status column when surfacing results.

```bash
uip admin tenants services list-available --region "<REGION>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--region <region>` | Yes | Provisioning region — required |

Each catalog entry carries provisioning metadata. The agent uses these fields to decide what to propose by default on `tenants create`:

| Field | Meaning | Effect on tenant-create defaults |
|---|---|---|
| `provisioningMode` | `Implicit` (auto-provisioned when listed) or `Explicit` (must be deliberately added) | **Defaults set:** filter to `Implicit` only. `Explicit` services are optional opt-ins — offer only on user request. |
| `isVisible` | `true` if the service is end-user-facing | **Defaults set:** filter to `true`. `false` services are platform-internal (don't surface in any user-facing list). |
| `isAlwaysProvision` | `true` if the platform automatically provisions this service on every tenant | **Defaults set:** filter to `false`. `true` services are auto-provisioned by the platform — no need to include in the user's choice; they will be there regardless. |
| `supportedRegions[]`, `defaultRegion`, `entitlement`, `serviceLicenseStatus` | informational | — |

**Default-provision filter** (use for new-tenant proposals): `provisioningMode === "Implicit" && isVisible === true && isAlwaysProvision === false`. Run the filter command below for the target region to get the current set — the catalog is region-aware, never hardcode names. Render the result as the default services on `tenants create`; let the user remove unwanted entries and add Explicit services explicitly. Pass the confirmed catalog `name` values as a string array in the create body's `services` field (NOT the `id` field).

Filter command (note: filter root is the `Data` array itself — use `[?...]`, NOT `Data[?...]`):

```bash
uip admin tenants services list-available --region "<REGION>" --output json \
  --output-filter "[?provisioningMode=='Implicit' && isVisible==\`true\` && isAlwaysProvision==\`false\`].name"
```

**Output code:** `OmsTenantServicesAvailable`.

### `services add`

Provision one or more services on a tenant. **Synchronous.**

```bash
uip admin tenants services add \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Tenant UUID — defaults to login tenant. **Always pass explicitly for service mutations on non-login tenants.** |
| `--service <type>` | Yes (inline) | Single service type |
| `--file <path>` | Alternative | JSON body for multiple services |

`--file ./add-services.json`:

```json
{ "services": { "orchestrator": true, "studio": true } }
```

All file entries must be `true` (use `services remove` for `false`).

**Output code:** `OmsTenantServicesAdded`.

### `services enable`

Enable a single service instance on a tenant. **Synchronous.**

```bash
uip admin tenants services enable \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Tenant UUID — defaults to login tenant. **Always pass explicitly for non-login tenants.** |
| `--service <type>` | Yes | Service type |

**Output code:** `OmsTenantServiceEnabled`.

### `services disable`

Disable a single service instance on a tenant. **Synchronous.**

```bash
uip admin tenants services disable \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Tenant UUID — defaults to login tenant. **Always pass explicitly for non-login tenants.** |
| `--service <type>` | Yes | Service type |

**Output code:** `OmsTenantServiceDisabled`.

> **Not supported on every service.** Integration Service (`connections`), Data Fabric (`dataservice`), and Insights (`insights`) accept the call and return `OmsTenantServiceDisabled` / `Success`, but the service-side `status` never flips to `Disabled`. Verify with `tenants get <TENANT_ID> --output-filter "tenantServiceInstances[?serviceType=='<SVC>']"` and warn the user upfront if they target one of these services.

### `services remove`

Soft-remove one or more services from a tenant. **Synchronous.** Server-side soft-delete (no hard-delete option).

```bash
uip admin tenants services remove \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Tenant UUID — defaults to login tenant. **Always pass explicitly for service-remove on non-login tenants.** |
| `--service <type>` | Yes (inline) | Single service type |
| `--file <path>` | Alternative | JSON body for multiple services |

`--file ./remove-services.json`:

```json
{ "services": { "orchestrator": false, "studio": false } }
```

All file entries must be `false`.

**Output code:** `OmsTenantServicesRemoved`.

> **Not supported on every service.** Orchestrator (`orchestrator`), Maestro (`maestro`), Integration Service (`connections`), Data Fabric (`dataservice`), Insights (`insights`), and Test Manager (`testmanager`) cannot be soft-removed — the CLI may return `Success` but the service stays provisioned. Verify with `tenants get` and warn the user upfront if they target one of these services.

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `tenant not found` | Invalid tenant UUID | Resolve via `tenants list --filter <NAME>` |
| `region not allowed` | `--region` not in available regions | Run `organizations regions list` and use a returned value |
| `service not available in region` | Service type not in regional catalog | Run `tenants services list-available --region <REGION>` first |
| `service already provisioned` | Trying to `add` a service that exists | Use `enable` instead, or list current state with `services list` |
| Operation stuck `Updating` | Async op pending or failed | Poll `organizations operation get <OPERATION_ID>` for status / error |
| Destructive op targeted login tenant unintentionally | `<TENANT_ID>` omitted | Always pass an explicit tenant id for `delete`, `disable`, `services remove` |
| `services disable` returned `Success` but `status` still `Enabled` | Service does not support disable (Integration Service, Data Fabric, Insights) | Expected — service-side limitation, not a CLI bug. Inform the user the service cannot be disabled |
| `services remove` returned `Success` but instance still present | Service does not support remove (Orchestrator, Maestro, Integration Service, Data Fabric, Insights, Test Manager) | Expected — service-side limitation. Inform the user the service cannot be soft-removed |
| Auth error | Login expired | `uip login status`, then `uip login` |
