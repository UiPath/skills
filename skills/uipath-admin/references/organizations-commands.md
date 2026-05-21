# Organizations CLI Command Reference

Complete reference for all `uip admin organizations` commands — caller's organization read + update, async-operation polling (for tenant lifecycle ops), region catalog, and org-level service catalog (read-only). Part of the Organization Management Service (OMS).

For tenant commands, see [tenants-commands.md](tenants-commands.md). For workflow-level guidance, see [organization-management.md](organization-management.md).

## Global Flags

Every command accepts these flags (omitted from per-command tables):

| Flag | Description |
|------|-------------|
| `--output <format>` | Output format: `json`, `table`, `yaml`, `plain` (default: json) |
| `--output-filter <expression>` | JMESPath expression to filter output |
| `--log-level <level>` | Log level: `debug`, `info`, `warn`, `error` (default: info) |
| `--log-file <path>` | Write logs to file instead of stderr |
| `--login-validity <minutes>` | Override token validity — forces refresh if token expires within this window |

Organization is resolved automatically from the active login session — no `--organization` flag.

## Prerequisites

```bash
uip login status --output json
```

If not logged in: `uip login`.

## Concepts

### OMS sync vs async — quick reference

| Operation | Sync/Async | Confirm completion |
|---|---|---|
| `organizations get`, `update` | **Sync** | Response. No CLI `create` / `delete` — Portal / support flow only. |
| `tenants create / update / delete / enable / disable` | **Async** — returns `operationId` | Poll `organizations operation get <OP_ID>` (single endpoint for all OMS async ops) |
| `tenants services add / enable / disable / remove` | **Sync** | Response — except `disable` (Integration Service, Data Fabric, Insights) and `remove` (Orchestrator, Maestro, Integration Service, Data Fabric, Insights, Test Manager), which return Success but no-op. Re-list. |
| All `*list*`, `get`, `regions list`, `services list-available` | **Sync** | — |

### Notes

- **Org surface is read + update only.** This command tree exposes `get`, `update`, `regions list`, `services list / list-available`, and `operation get`. **There is no `organizations create` or `organizations delete` in the CLI** — those are not exposed; org creation/deletion goes through the UiPath Portal / support flow.
- **All org verbs are synchronous.** `update`, `get`, `regions list`, and all `services` reads complete in a single round-trip and carry the final state in the response.
- **Single poll endpoint for the platform.** `operation get` lives here for historical reasons, but it polls async **tenant** lifecycle ops (`tenants create / update / delete / enable / disable`). Use it whenever those return an `operationId`.
- **No login-tenant default here.** Org commands always operate on the caller's organization (resolved from the active login).
- **Region is required for tenant create.** Run `regions list` here, then pass `--region` to `tenants create` (see [tenants-commands.md](tenants-commands.md)).

---

## Organization — `uip admin organizations`

### `organizations get`

Fetch the caller's organization record.

```bash
uip admin organizations get --output json
uip admin organizations get --full --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--full` | No | Return bundle: org + tenants + service catalog in one call |

**Output code:** `OmsOrganizationGet`

### `organizations update`

Patch editable fields on the caller's organization. **Synchronous** — response carries the final state.

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

At least one field flag (or `--file`) is required. **Output code:** `OmsOrganizationUpdated`.

> **No `create` / `delete` here.** The CLI does not expose `organizations create` or `organizations delete`; both return `ValidationError: unknown command`. For org provisioning or removal, use the UiPath Portal or the support flow.

---

## Async Operations — `uip admin organizations operation`

### `operation get`

Poll the status of an async OMS operation (tenant lifecycle today; org create/delete are not exposed by the CLI).

```bash
uip admin organizations operation get <OPERATION_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<OPERATION_ID>` | Yes | Operation UUID returned by a `tenants` lifecycle command (`create`, `update`, `delete`, `enable`, `disable`) |

The response carries a `status` field. Treat `Pending` / `Running` / `InProgress` as in-progress; anything else (`Succeeded`, `Failed`, `Cancelled`) as terminal.

**Polling cadence — auto-poll up to 3× at 5-second intervals, then ask the user.** Surface each intermediate status; never loop silently and never auto-poll indefinitely. For the full procedure (including the numbered next-step menu the agent presents after the 3-poll auto-window), see [organization-management.md — Polling procedure](organization-management.md#polling-procedure-auto-poll-then-hand-off).

**Output code:** `OmsOperationGet`.

---

## Regions — `uip admin organizations regions`

### `regions list`

List provisioning regions in which Portal can stand up tenants (and orgs via the Portal). Run before `tenants create` to confirm `--region` accepts the desired value.

```bash
uip admin organizations regions list --output json
```

Returned region names go directly into `--region` on `tenants create`.

**Output code:** `OmsRegionsList`.

---

## Org-Level Services — `uip admin organizations services`

> **Read-only at the org surface.** Only `list` and `list-available` exist here — there is no `add` / `enable` / `disable` / `remove` at the org level. To provision / mutate services on a specific tenant, use [`tenants services` →](tenants-commands.md#tenant-level-services--uip-admin-tenants-services).

> **`list` vs `list-available` are different sets — never merge them.** `services list` returns the **currently provisioned** org-level instances (each with a `status`: `Enabled` / `Disabled` / `Deleted`). `services list-available` returns the **catalog** of provisionable service types (no status — catalog entries are not provisioned). Always present them as two clearly labeled sections when surfacing results to the user. See [organization-management.md — List Org-Level Services](organization-management.md#workflow-list-org-level-services--provisioned-vs-available).

### `services list`

List **currently provisioned** org-level service instances. Each row carries a lifecycle `status` — `Enabled`, `Disabled`, or `Deleted` (soft-deleted). Surface the status field in any presentation; flag `Deleted` entries explicitly.

```bash
uip admin organizations services list --output json
uip admin organizations services list --service orchestrator --output json
uip admin organizations services list --status Enabled --output json
uip admin organizations services list --region "<REGION>" --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--service <type>` | No | Filter by service type (client-side) |
| `--status <state>` | No | Filter by lifecycle status, e.g. `Enabled`, `Disabled` (client-side) |
| `--region <region>` | No | Filter by region (client-side) |

All filters are client-side after the API call (no server-side filters).

**Output code:** `OmsOrgServicesList`.

### `services list-available`

List the **catalog** of services that can be provisioned at the org level. Catalog only — entries are not provisioned and have no lifecycle status. Do not show a status column when surfacing results.

```bash
uip admin organizations services list-available --output json
```

**Output code:** `OmsOrgServicesAvailable`.

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `region not allowed` | `--region` value not in available regions (only relevant via `tenants create`) | Run `regions list` and use a returned value |
| Operation never completes | Async op stuck or failed | Inspect `Data` from `operation get <OPERATION_ID>`; retry or escalate |
| Empty service list | Filter mismatch (all filters client-side) | Drop a filter or try a different value |
| Auth error | Login expired | `uip login status`, then `uip login` |
