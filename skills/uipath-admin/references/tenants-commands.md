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

```bash
uip admin tenants create \
  --name "<TENANT_NAME>" \
  --region "<REGION>" \
  --environment "<ENV>" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | Yes (inline) | Tenant display name |
| `--region <region>` | Yes (inline) | Provisioning region — resolve via `organizations regions list` |
| `--environment <env>` | No | Environment tag (e.g., `Production`, `Development`) |
| `--file <path>` | Alternative | Full `CreateTenantRequestDto` body (required for `services[]`, `customProperties`, `color`, `isDefaultTenant`) |

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

### `services list`

List provisioned tenant-level service instances.

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

List the catalog of services that can be provisioned for a tenant in a given region. **Region-aware** — the catalog varies by region.

```bash
uip admin tenants services list-available --region "<REGION>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--region <region>` | Yes | Provisioning region — required |

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
| Auth error | Login expired | `uip login status`, then `uip login` |
