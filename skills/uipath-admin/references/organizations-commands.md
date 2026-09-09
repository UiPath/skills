# Organizations CLI Command Reference

Reference for `uip admin organizations`: caller-organization read/update, tenant-lifecycle operation polling, regions, and read-only org-level services. For tenant commands, see [tenants-commands.md](tenants-commands.md). For workflow guidance, see [organization-management.md](organization-management.md).

## Global Flags

Every command accepts:

| Flag | Description |
|------|-------------|
| `--output <format>` | `json`, `table`, `yaml`, `plain` (default: json) |
| `--output-filter <expression>` | JMESPath output filter |
| `--log-level <level>` | `debug`, `info`, `warn`, `error` (default: info) |
| `--log-file <path>` | Write logs instead of stderr |
| `--login-validity <minutes>` | Force token refresh when expiry is within this window |

Resolve the organization from the active login; no `--organization` flag exists. Run `uip login status --output json`; if not logged in, run `uip login`.

## Concepts

- `organizations get` and `update` are synchronous and return final state.
- `tenants create / update / delete / enable / disable` are asynchronous, return `operationId`, and require polling with `organizations operation get <OP_ID>`.
- `tenants services add / enable / disable / remove` are synchronous, except `disable` (Integration Service, Data Fabric, Insights) and `remove` (Orchestrator, Maestro, Integration Service, Data Fabric, Insights, Test Manager), which return Success but no-op. Re-list.
- All `*list*`, `get`, `regions list`, and `services list-available` commands are synchronous.
- The organization surface is read/update only: `get`, `update`, `regions list`, `services list / list-available`, and `operation get`. There is no CLI `organizations create` or `organizations delete`; use the UiPath Portal / support flow.
- Organization commands use the caller's organization, not a login-tenant default.
- Region is required for tenant create. Run `regions list`, then pass `--region` to `tenants create`; see [tenants-commands.md](tenants-commands.md).

## Organization — `uip admin organizations`

### `organizations get`

Fetch the caller's organization record:

```bash
uip admin organizations get --output json
uip admin organizations get --full --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--full` | No | Return org, tenants, and service catalog in one call |

**Output code:** `OmsOrganizationGet`

### `organizations update`

Patch editable organization fields synchronously; the response contains final state. Pass at least one field flag or `--file`:

```bash
uip admin organizations update --name "<NEW_NAME>" --output json
uip admin organizations update --logical-name "<NEW_SLUG>" --output json
uip admin organizations update --language "<LANGUAGE_CODE>" --output json
uip admin organizations update --file ./org-update.json --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | No | New display name |
| `--logical-name <slug>` | No | New URL slug |
| `--language <code>` | No | New language code |
| `--file <path>` | Alternative | Full `UpdateOrganizationCommand` body |

**Output code:** `OmsOrganizationUpdated`. Do not use `organizations create` or `organizations delete`; the CLI does not expose them and returns `ValidationError: unknown command`. Use the UiPath Portal or support flow.

## Async Operations — `uip admin organizations operation`

### `operation get`

Poll a tenant lifecycle operation returned by `tenants create`, `update`, `delete`, `enable`, or `disable`:

```bash
uip admin organizations operation get <OPERATION_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<OPERATION_ID>` | Yes | Operation UUID returned by a tenant lifecycle command |

Treat `Pending`, `Running`, and `InProgress` as in-progress; treat every other status, including `Succeeded`, `Failed`, and `Cancelled`, as terminal. Auto-poll up to 3× at 5-second intervals, surface every intermediate status, never loop silently or indefinitely, then ask the user. Follow [organization-management.md — Polling procedure](organization-management.md#polling-procedure-auto-poll-then-hand-off) for the numbered next-step menu after the 3-poll window.

**Output code:** `OmsOperationGet`

## Regions — `uip admin organizations regions`

### `regions list`

Run this before `tenants create` to validate `--region`, then pass a returned region name directly to `--region`:

```bash
uip admin organizations regions list --output json
```

This lists provisioning regions in which Portal can stand up tenants and orgs.

**Output code:** `OmsRegionsList`

## Org-Level Services — `uip admin organizations services`

This surface is read-only: only `list` and `list-available` exist. Do not use org-level `add`, `enable`, `disable`, or `remove`; mutate services on a tenant with [`tenants services` →](tenants-commands.md#tenant-level-services--uip-admin-tenants-services).

Keep result sets separate: `services list` returns currently provisioned org-level instances with status `Enabled`, `Disabled`, or `Deleted`; `services list-available` returns provisionable catalog types with no status. Present them as clearly labeled sections. See [organization-management.md — List Org-Level Services](organization-management.md#list-org-level-services).

### `services list`

List provisioned instances, surface `status`, and explicitly flag `Deleted` entries. All filters run client-side after the API call:

```bash
uip admin organizations services list --output json
uip admin organizations services list --service orchestrator --output json
uip admin organizations services list --status Enabled --output json
uip admin organizations services list --region "<REGION>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--service <type>` | No | Client-side service-type filter |
| `--status <state>` | No | Client-side lifecycle filter, e.g. `Enabled`, `Disabled` |
| `--region <region>` | No | Client-side region filter |

**Output code:** `OmsOrgServicesList`

### `services list-available`

List the org-level service catalog. Entries are not provisioned and have no lifecycle status; do not show a status column:

```bash
uip admin organizations services list-available --output json
```

**Output code:** `OmsOrgServicesAvailable`

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `region not allowed` | `--region` is not available; relevant via `tenants create` | Run `regions list` and use a returned value |
| Operation never completes | Async operation is stuck or failed | Inspect `Data` from `operation get <OPERATION_ID>`; retry or escalate |
| Empty service list | Client-side filter mismatch | Drop a filter or try another value |
| Auth error | Login expired | Run `uip login status`, then run `uip login` |
