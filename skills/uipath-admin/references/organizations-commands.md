# Organizations CLI Command Reference

Complete reference for all `uip admin organizations` commands — caller's organization lifecycle, async operation polling, region catalog, and org-level service provisioning (Organization Management Service / OMS).

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

- **Async vs synchronous.** `organizations create` and `delete` are async — they return an `operationId`. `update`, `regions list`, and all `services` reads are synchronous.
- **Single poll endpoint.** All async OMS operations — both `organizations` and `tenants` — are polled through `uip admin organizations operation get <OPERATION_ID>`. There is no separate `tenants operation get`.
- **Soft-delete only.** `organizations delete` has no hard-delete flag. Reversible via the support flow.
- **No login-tenant default here.** Org commands always operate on the caller's organization (resolved from the active login).
- **Region is required at create.** Run `regions list` first to confirm acceptable values.

---

## Organization Lifecycle — `uip admin organizations`

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

### `organizations create`

Create a new organization. **Async** — returns `operationId`.

```bash
uip admin organizations create \
  --name "<ORG_NAME>" \
  --email "<COMPANY_EMAIL>" \
  --owner "<OWNER_USER_ID>" \
  --country "<COUNTRY_CODE>" \
  --language "<LANGUAGE_CODE>" \
  --region "<REGION>" \
  --first-name "<FIRST>" \
  --last-name "<LAST>" \
  --output json
```

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | Yes (inline) | Organization display name |
| `--email <email>` | Yes (inline) | Company contact email |
| `--owner <user-id>` | Yes (inline) | Owner user UUID — resolve via `uip admin users list --search <EMAIL>` |
| `--country <code>` | Yes (inline) | ISO country code |
| `--language <code>` | Yes (inline) | Language code (e.g., `en`) |
| `--region <region>` | Yes (inline) | Provisioning region — resolve via `organizations regions list` |
| `--first-name <name>` | No | Owner first name |
| `--last-name <name>` | No | Owner last name |
| `--file <path>` | Alternative | Full `CreateOrganizationCommand` body (required for `type`, `customProperties`, `isCreatorNonAdmin`) |

**Output code:** `OmsOrganizationCreated`. Returned body includes `operationId` — poll via `operation get`.

### `organizations update`

Patch editable fields on the caller's organization.

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

### `organizations delete`

Soft-delete the caller's organization. **Async** — returns `operationId`. **Severe org-wide action — confirm with user first.**

```bash
uip admin organizations delete --output json
```

No hard-delete flag. Restoration goes through the support flow.

**Output code:** `OmsOrganizationDeleted`.

---

## Async Operations — `uip admin organizations operation`

### `operation get`

Poll the status of any async OMS operation (organization or tenant).

```bash
uip admin organizations operation get <OPERATION_ID> --output json
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<OPERATION_ID>` | Yes | Operation UUID returned by `organizations create/delete` or any `tenants` lifecycle command |

Repeat until the response indicates a terminal status. Show the user the current status between polls; do not loop silently.

**Output code:** `OmsOperationGet`.

---

## Regions — `uip admin organizations regions`

### `regions list`

List provisioning regions in which Portal can stand up organizations or tenants. Run before `organizations create` or `tenants create` to confirm `--region` accepts the desired value.

```bash
uip admin organizations regions list --output json
```

Returned region names go directly into `--region` on create.

**Output code:** `OmsRegionsList`.

---

## Org-Level Services — `uip admin organizations services`

> **Read-only at the org surface.** Only `list` and `list-available` exist here — there is no `add` / `enable` / `disable` / `remove` at the org level. To provision / mutate services on a specific tenant, use [`tenants services` →](tenants-commands.md#tenant-level-services--uip-admin-tenants-services).

### `services list`

List provisioned org-level service instances.

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

List the catalog of services that can be provisioned at the org level.

```bash
uip admin organizations services list-available --output json
```

**Output code:** `OmsOrgServicesAvailable`.

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `region not allowed` | `--region` value not in available regions | Run `regions list` and use a returned value |
| `owner not found` | Invalid `--owner` UUID | Resolve via `uip admin users list --search <EMAIL>` |
| Operation never completes | Async op stuck or failed | Inspect `Data` from `operation get <OPERATION_ID>`; retry or escalate |
| Empty service list | Filter mismatch (all filters client-side) | Drop a filter or try a different value |
| Auth error | Login expired | `uip login status`, then `uip login` |
