# Tenants CLI Command Reference

Reference for `uip admin tenants` tenant lifecycle and tenant-level service provisioning (Organization Management Service / OMS).

For organization commands, see [organizations-commands.md](organizations-commands.md). For workflow-level guidance, see [tenant-management.md](tenant-management.md).

## Global Flags and Prerequisites

Every command accepts:

| Flag | Description |
|------|-------------|
| `--output <format>` | `json`, `table`, `yaml`, `plain` (default: json) |
| `--output-filter <expression>` | JMESPath output filter |
| `--log-level <level>` | `debug`, `info`, `warn`, `error` (default: info) |
| `--log-file <path>` | Write logs instead of stderr |
| `--login-validity <minutes>` | Force token refresh when expiry is within this window |

Organization is resolved from the active login session. Run:

```bash
uip login status --output json
```

If not logged in, run `uip login`.

## Concepts and Safety Rules

- `create`, `update`, `delete`, `enable`, and `disable` are asynchronous and return an `operationId`. Poll each with `uip admin organizations operation get <OPERATION_ID>`; there is no `tenants operation get`. `list`, `get`, and all `services` commands are synchronous; service mutations return 200 OK with no body.
- `delete` is soft-delete only and has no hard-delete flag. Restore through the support / restore flow.
- `get`, `update`, `delete`, `enable`, and `disable` accept a positional tenant id and default to the login tenant. Always pass an explicit `<TENANT_ID>` to `delete`, `disable`, and `services remove`.
- `create` requires `--region`. Run `organizations regions list`, then run `tenants services list-available --region <REGION>` because the catalog is region-aware.
- Before `services add`, `enable`, `disable`, or `remove`, run `tenants get <ID> --output json`, resolve `<TENANT_ID>`, and echo the tenant name, especially for `remove`. These commands silently default `--tenant-id` to the login tenant.
- Disable is not honored for Integration Service (`connections`), Data Fabric (`dataservice`), or Insights (`insights`). Remove is rejected or not honored for Orchestrator (`orchestrator`), Maestro (`maestro`), Integration Service (`connections`), Data Fabric (`dataservice`), Insights (`insights`), or Test Manager (`testmanager`).
- Before submitting an unsupported disable/remove, warn: *"Service `<X>` cannot be {disabled|removed} via the CLI — it's pinned by the platform. The call will return Success but the service will stay {Enabled|provisioned}. To deprovision, revoke the org entitlement via the UiPath Portal. Continue anyway, or skip `<X>`?"* Skip it or continue only with the user's choice. If continuing, warn again in the post-state summary.
- After every `services disable` or `services remove`, run `tenants get <TENANT_ID> --output-filter "tenantServiceInstances[?serviceType=='<SVC>']"` and inspect the instance `status`; HTTP 200 or `Success` does not prove a state change.

## Tenant Lifecycle — `uip admin tenants`

### `tenants list`

Run:

```bash
uip admin tenants list --output json
uip admin tenants list --filter "<NAME_FRAGMENT>" --output json
uip admin tenants list --status Enabled --service orchestrator --output json
uip admin tenants list --include-services --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--filter <fragment>` | No | Case-insensitive substring match on tenant name (client-side) |
| `--service <type>` | No | Tenants with the service provisioned |
| `--status <status>` | No | Exact status: `Enabled`, `Disabled`, `Updating`, `Deleted` |
| `--environment <env>` | No | Environment tag filter (client-side) |
| `--include-services` | No | Include each tenant's `services` array |

Output code: `OmsTenantsList`.

### `tenants get`

Run:

```bash
uip admin tenants get <TENANT_ID> --output json
uip admin tenants get --output json
```

`<TENANT_ID>` is optional and defaults to the login tenant. Output code: `OmsTenantGet`.

### `tenants create`

Run `organizations regions list`, run `tenants services list-available --region <REGION>`, and create asynchronously with:

```bash
uip admin tenants create --file ./tenant.json --output json
```

`--file` is required in practice because the server requires `services` on `CreateTenantRequestDto`; the inline `--name --region --environment` path omits it and returns `HTTP 400: The Services field is required.` Use:

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
| `name` | Yes | Display name; alphanumeric, 2–32 chars, starts with a letter |
| `region` | Yes | Value from `organizations regions list` |
| `environment` | No | `Production`, `NonProduction`, or `Development` |
| `services` | **Yes** | Plain string array of catalog `name` values, not the `{name: true}` map used by `services add`; resolve names with the default-provision filter below and never hardcode them. `isAlwaysProvision === true` services are automatic. |
| `customProperties` | No | Free-form key/value bag |
| `color` | No | UI color tag |
| `isDefaultTenant` | No | Mark the organization's default tenant |

Output code: `OmsTenantCreated`.

### `tenants update`

Run:

```bash
uip admin tenants update <TENANT_ID> \
  --name "<NEW_NAME>" \
  --region "<NEW_REGION>" \
  --environment "<NEW_ENV>" \
  --output json
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `<TENANT_ID>` | No | Tenant UUID; defaults to login tenant |
| `--name <name>` | No | New display name |
| `--region <region>` | No | New region |
| `--environment <env>` | No | New environment tag |
| `--file <path>` | Alternative | Full `TenantUpdateDto`; required for `services{}`, `customProperties`, or `color` |

Require at least one field flag or `--file`. Output code: `OmsTenantUpdated`.

### `tenants delete`

Confirm with the user, then run:

```bash
uip admin tenants delete <TENANT_ID> --output json
```

Always pass the tenant id. This is asynchronous, returns `operationId`, and has no hard-delete flag. Output code: `OmsTenantDeleted`.

### `tenants enable`

Run:

```bash
uip admin tenants enable <TENANT_ID> --output json
```

This is asynchronous; `<TENANT_ID>` defaults to the login tenant. Output code: `OmsTenantEnabled`.

### `tenants disable`

Run:

```bash
uip admin tenants disable <TENANT_ID> --reason "<FREE_TEXT_REASON>" --output json
```

`<TENANT_ID>` is optional but defaults to the login tenant; always pass it explicitly. `--reason <text>` is optional free-text audit reason. This is asynchronous. Output code: `OmsTenantDisabled`.

## Tenant-Level Services — `uip admin tenants services`

`services list` reports provisioned instances and their `status`: `Enabled`, `Disabled`, or `Deleted`; surface the status and explicitly flag `Deleted`. `services list-available --region <R>` reports the region-aware provisionable catalog without lifecycle status. Keep these as separate, clearly labeled sections; see [tenant-management.md — List Tenant Services](tenant-management.md#workflow-list-tenant-services--provisioned-vs-available).

### `services list`

Run:

```bash
uip admin tenants services list --output json
uip admin tenants services list --tenant-id <TENANT_ID> --output json
uip admin tenants services list --service orchestrator --output json
uip admin tenants services list --region "<REGION>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Tenant UUID; defaults to login tenant |
| `--service <type>` | No | Service-type filter (client-side) |
| `--region <region>` | No | Region filter (client-side) |

All filters are client-side. Output code: `OmsTenantServicesList`.

### `services list-available`

Run:

```bash
uip admin tenants services list-available --region "<REGION>" --output json
```

`--region <region>` is required. Catalog entries have no lifecycle status. Use:

| Field | Meaning | Default behavior |
|---|---|---|
| `provisioningMode` | `Implicit` or `Explicit` | Include only `Implicit`; offer `Explicit` as opt-in |
| `isVisible` | `true` for end-user-facing services | Include only `true`; do not surface `false` platform-internal services |
| `isAlwaysProvision` | `true` for platform-auto-provisioned services | Exclude `true`; they appear automatically |
| `supportedRegions[]`, `defaultRegion`, `entitlement`, `serviceLicenseStatus` | Informational | — |

Run this default-provision filter for the target region. The root is the `Data` array, so use `[?... ]`, not `Data[?... ]`:

```bash
uip admin tenants services list-available --region "<REGION>" --output json \
  --output-filter "[?provisioningMode=='Implicit' && isVisible==\`true\` && isAlwaysProvision==\`false\`].name"
```

Render results as create defaults, let the user remove unwanted entries or explicitly add services, and pass confirmed catalog `name` values—not `id` values—as the create body's string-array `services` field. Output code: `OmsTenantServicesAvailable`.

### `services add`

Provision synchronously. Before submission, resolve and echo the tenant as required above. Run:

```bash
uip admin tenants services add \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Defaults to login tenant; always explicit for non-login tenants |
| `--service <type>` | Yes (inline) | Single service type |
| `--file <path>` | Alternative | Multiple-service JSON body |

```json
{ "services": { "orchestrator": true, "studio": true } }
```

All file entries must be `true`; use `services remove` for `false`. Output code: `OmsTenantServicesAdded`.

### `services enable`

Before submission, resolve and echo the tenant. Run:

```bash
uip admin tenants services enable \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

`--tenant-id <id>` is optional, defaults to the login tenant, and is always explicit for non-login tenants. `--service <type>` is required. Output code: `OmsTenantServiceEnabled`.

### `services disable`

Before submission, resolve and echo the tenant; apply the unsupported-service warning and post-state verification rules. Run:

```bash
uip admin tenants services disable \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

`--tenant-id <id>` is optional, defaults to the login tenant, and is always explicit for non-login tenants. `--service <type>` is required. Integration Service (`connections`), Data Fabric (`dataservice`), and Insights (`insights`) may return `OmsTenantServiceDisabled` / `Success` without changing `status` to `Disabled`. Output code: `OmsTenantServiceDisabled`.

### `services remove`

Soft-remove synchronously; there is no hard-delete option. Before submission, resolve and echo the tenant, require explicit `<TENANT_ID>`, and apply the unsupported-service warning and post-state verification rules. Run:

```bash
uip admin tenants services remove \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--tenant-id <id>` | No | Defaults to login tenant; always explicit for service-remove on non-login tenants |
| `--service <type>` | Yes (inline) | Single service type |
| `--file <path>` | Alternative | Multiple-service JSON body |

```json
{ "services": { "orchestrator": false, "studio": false } }
```

All file entries must be `false`. Orchestrator (`orchestrator`), Maestro (`maestro`), Integration Service (`connections`), Data Fabric (`dataservice`), Insights (`insights`), and Test Manager (`testmanager`) cannot be soft-removed; the CLI may return `Success` while the service remains provisioned. Output code: `OmsTenantServicesRemoved`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `tenant not found` | Invalid tenant UUID | Resolve via `tenants list --filter <NAME>` |
| `region not allowed` | `--region` unavailable | Run `organizations regions list` and use a returned value |
| `service not available in region` | Service absent from regional catalog | Run `tenants services list-available --region <REGION>` first |
| `service already provisioned` | `add` targets an existing service | Use `enable`, or run `services list` |
| Operation stuck `Updating` | Async operation pending or failed | Poll `organizations operation get <OPERATION_ID>` for status / error |
| Destructive op targeted login tenant unintentionally | `<TENANT_ID>` omitted | Always pass an explicit tenant id to `delete`, `disable`, and `services remove` |
| `services disable` returned `Success` but `status` still `Enabled` | Service does not support disable: Integration Service, Data Fabric, or Insights | Expected service-side limitation; inform the user it cannot be disabled |
| `services remove` returned `Success` but instance still present | Service does not support remove: Orchestrator, Maestro, Integration Service, Data Fabric, Insights, or Test Manager | Expected service-side limitation; inform the user it cannot be soft-removed |
| Auth error | Login expired | Run `uip login status`, then `uip login` |
