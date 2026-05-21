# Organization Management

Multi-step workflows for managing the caller's organization via `uip admin organizations`. For per-command flag tables, output codes, and single-command examples, see [organizations-commands.md](organizations-commands.md).

## Concept

The Organization Management Service (OMS) owns the org record, the region catalog, org-level service catalog (read-only), and the shared async-operation poll endpoint that tenant lifecycle ops use.

- **Org surface is read + update only.** `uip admin organizations` exposes `get`, `update`, `regions list`, `services list / list-available`, and `operation get`. **No `create` / `delete`** — those are not exposed by the CLI; org creation/deletion goes through the UiPath Portal or support flow.
- **All org commands are synchronous.** Async polling on this command tree is for *tenant* lifecycle ops (see [tenant-management.md](tenant-management.md)) — the poll endpoint just happens to live under `organizations operation get`. See [Polling procedure](#polling-procedure-auto-poll-then-hand-off).
- **Login-tenant default** does NOT apply to org commands — they always operate on the caller's organization.

## Workflow: Inspect the Organization

The common read-side scenario — show the caller their org record.

### Compact view (just the org record)

```bash
uip admin organizations get --output json
```

Returns the organization name, id, region, country, language, lifecycle state, and timestamps.

When surfacing the result to the user, lead with **`Organization: <ORG_NAME> (region: <REGION>)`** so they see at a glance which org the session is on. Do not show the raw `id` field alone — pair it with the name.

### Bundled view (org + tenants + service catalog in one call)

```bash
uip admin organizations get --full --output json
```

Use `--full` when you need to answer a follow-up about tenants or services in the same response — it avoids the second round-trip to `tenants list` or `services list`.

### Discover provisioning regions for `tenants create`

```bash
uip admin organizations regions list --output json
```

The returned region names go directly into `--region` on `tenants create`.

## Workflow: Update the Organization

Two shapes:

- **Inline** for one or two simple fields (`--name`, `--logical-name`, `--language`).
- **File** for the full `UpdateOrganizationCommand` body when changing multiple structured fields.

See [organizations-commands.md — `organizations update`](organizations-commands.md#organizations-update). Synchronous — the response carries the final state.

> **No CLI `organizations create` / `delete`.** If a user asks to create or delete an organization, redirect them to the UiPath Portal or support flow — the CLI does not expose those verbs.

## Workflow: Poll an Async Operation

Canonical poll endpoint for OMS async operations. Today every async op comes from a `tenants` lifecycle verb (`create / update / delete / enable / disable`); the endpoint lives under `organizations operation get` and works for any future async ops as well:

```bash
uip admin organizations operation get <OPERATION_ID> --output json
```

### Polling procedure (auto-poll then hand off)

Auto-poll briefly, then hand control back to the user. Bounded — never indefinite.

1. **Echo the operationId and the resume command** so the user can always pick up later:
   ```bash
   uip admin organizations operation get <OPERATION_ID> --output json
   ```
2. **Auto-poll up to 3 times at 5-second intervals** (≈15 s total). Between polls, sleep 5 s. After each call, surface the current status — e.g. *"Poll 2/3: status=`Running`"*. Never loop silently.
3. **Stop polling on any terminal status.** Treat anything that is not `Pending` / `Running` / `InProgress` as terminal (`Succeeded`, `Failed`, `Cancelled`). On terminal, report final state and re-fetch the affected resource (`organizations get` / `tenants get <ID>`).
4. **Still non-terminal after 3 polls → hand off with a numbered menu** (`<ROUND>` starts at 1; increment each time the user picks `1`):
   ```
   Operation <OP_ID> is still `<STATUS>` after round <ROUND> (3 × 5 s polls). Choose:
     1. Keep polling (another 3 × 5 s)
     2. Poll once more
     3. Stop and return the operationId for later
   ```
   - `1` → resume one more auto-poll cycle; increment `<ROUND>`. After **round 2 (≈30 s total)**, drop option `1` from the menu — only `2` and `3` remain. The user cannot extend auto-polling beyond ~30 s.
   - `2` → one more `operation get` call, then re-prompt with the same menu (option `1` still gated by the round cap).
   - `3` → print the resume command and exit; the user can come back and run `operation get <OP_ID>` later.
5. **Never auto-poll indefinitely.** Total auto-poll window is capped at ~30 s (2 rounds). Beyond that the user must drive every additional poll via option `2` or walk away via `3`.

### Status vocabulary

The response's `status` field uses these values (treat case-insensitively in match logic, but show the user the exact case from the response):

| Family | Examples | Action |
|---|---|---|
| In-progress | `Pending`, `Running`, `InProgress` | Continue polling (within the 3-poll cap) |
| Terminal — success | `Succeeded` | Stop, re-fetch the resource, report success |
| Terminal — failure | `Failed`, `Cancelled` | Stop, surface the error payload (`Data.error` / `Data.message`), do NOT retry the original mutation automatically — ask the user |

If the response lacks a `status` field altogether, treat the operation as in-progress for that poll and try once more; if the field is missing across all 3 polls, surface the raw response to the user and stop.

## Workflow: List Org-Level Services — Provisioned vs. Available

Two distinct surfaces — never merge them:

| Verb | Returns | Has lifecycle status? |
|---|---|---|
| `organizations services list` | **Provisioned** org-level service instances (what currently exists on this org) | Yes — `Enabled`, `Disabled`, or `Deleted` (soft-deleted) |
| `organizations services list-available` | **Catalog** of service types that *can* be provisioned at the org level | No — catalog entries are not provisioned |

### Currently provisioned (with status)

```bash
uip admin organizations services list --output json
```

Surface to the user as **"Provisioned services on `<ORG_NAME>`"**. For each row, show: service type, **status** (`Enabled` / `Disabled` / `Deleted`), region. Flag any soft-deleted (`Deleted`) entries explicitly so the user knows they were removed but are still recoverable.

If the result is empty, say so explicitly: *"No org-level services are currently provisioned."* — do not show an empty table.

Optional filters (client-side, applied after the API call):

```bash
uip admin organizations services list --status Enabled --output json
uip admin organizations services list --service orchestrator --output json
uip admin organizations services list --region "<REGION>" --output json
```

### Available to provision (catalog only)

```bash
uip admin organizations services list-available --output json
```

Surface to the user as **"Available service catalog (org-level)"**. Do NOT add a status column — catalog entries have no lifecycle state. Visually separate this from the provisioned list (different header, ideally a different table).

### When the user's intent is ambiguous

If the user says "show me the services" without specifying provisioned vs. available, run both and present them in two clearly labeled sections so they can pick.

## Before Mutating the Organization — Name the Target

Before `organizations update`, echo the resolved target back so the user knows exactly which organization will change:

```
Organization: <ORG_NAME> (region: <REGION>, id: <ORG_ID>)
Action: update
```

`organizations get --output json` returns the name and region — resolve them up-front; do not run the mutation against just the active login session implicitly.

> The CLI does not expose `organizations delete`, so this echo only ever covers `update`. If the user asks to delete the org, redirect to the Portal / support flow.
