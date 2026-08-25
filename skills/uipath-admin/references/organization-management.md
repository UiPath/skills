# Organization Management

Manage the caller's organization with `uip admin organizations`. For per-command flag tables, output codes, and single-command examples, see [organizations-commands.md](organizations-commands.md).

## Scope

The Organization Management Service (OMS) owns the organization record, region catalog, read-only org-level service catalog, and shared async-operation poll endpoint for tenant lifecycle operations.

- The org surface is read/update only: `get`, `update`, `regions list`, `services list / list-available`, and `operation get`. There is no CLI `create` or `delete`; redirect organization creation/deletion to the UiPath Portal or support flow.
- Organization commands are synchronous. `organizations operation get` polls tenant lifecycle operations (`create / update / delete / enable / disable`) and may support future async operations.
- The login-tenant default does not apply; always target the caller's organization.

## Inspect and Update

Run the compact organization view:

```bash
uip admin organizations get --output json
```

Report it beginning with **`Organization: <ORG_NAME> (region: <REGION>)`**. It includes organization name, id, region, country, language, lifecycle state, and timestamps; never show the raw `id` alone—pair it with the name.

Run the bundled view **only** when tenants or services are also needed:

```bash
uip admin organizations get --full --output json
```

`--full` returns a **nested `{Organization, Tenants, Logos}` envelope — NOT the flat org record** (it has no top-level `Id`). For "show / save the organization record" requests, use the plain compact `organizations get` above and save that `Data` object (name + top-level `Id`).

Run this to discover regions for `tenants create`, and use returned region names directly with `--region` on `tenants create`:

```bash
uip admin organizations regions list --output json
```

Before `organizations update`, run `organizations get --output json` to resolve the target, then echo:

```
Organization: <ORG_NAME> (region: <REGION>, id: <ORG_ID>)
Action: update
```

Use inline flags for one or two simple fields (`--name`, `--logical-name`, `--language`); use a file for the full `UpdateOrganizationCommand` body when changing multiple structured fields. See [organizations-commands.md — `organizations update`](organizations-commands.md#organizations-update). The operation is synchronous and its response contains the final state. Do not run the mutation against only the active login session implicitly.

Do not attempt `organizations create` or `organizations delete`; redirect those requests to the UiPath Portal or support flow.

## Poll an Async Operation

Run:

```bash
uip admin organizations operation get <OPERATION_ID> --output json
```

### Polling procedure (auto-poll then hand off)

1. Echo the operationId and this resume command:
   ```bash
   uip admin organizations operation get <OPERATION_ID> --output json
   ```
2. Auto-poll up to 3 times at 5-second intervals (about 15 s total). Sleep 5 s between calls and surface each status, for example *"Poll 2/3: status=`Running`"*. Never loop silently.
3. Stop on any terminal status. Treat anything other than `Pending`, `Running`, or `InProgress` as terminal (`Succeeded`, `Failed`, `Cancelled`). Report the final state and re-fetch the affected resource with `organizations get` or `tenants get <ID>`.
4. If still non-terminal after 3 polls, show this numbered menu; `<ROUND>` starts at 1 and increments whenever the user selects `1`:
   ```
   Operation <OP_ID> is still `<STATUS>` after round <ROUND> (3 × 5 s polls). Choose:
     1. Keep polling (another 3 × 5 s)
     2. Poll once more
     3. Stop and return the operationId for later
   ```
   - Select `1` to run another 3 × 5 s cycle and increment `<ROUND>`. After round 2 (about 30 s total), remove option `1`; only `2` and `3` remain. Do not extend auto-polling beyond about 30 s.
   - Select `2` to make one `operation get` call, then show the same menu; option `1` remains subject to the round cap.
   - Select `3` to print the resume command and exit; the user can run `operation get <OP_ID>` later.
5. Never auto-poll indefinitely. The total auto-poll window is capped at about 30 s (2 rounds); afterward, the user must drive each poll with option `2` or select option `3`.

### Status vocabulary

Match case-insensitively but display the exact response case:

| Family | Examples | Action |
|---|---|---|
| In-progress | `Pending`, `Running`, `InProgress` | Continue within the 3-poll cap |
| Terminal — success | `Succeeded` | Stop, re-fetch the resource, and report success |
| Terminal — failure | `Failed`, `Cancelled` | Surface `Data.error` / `Data.message`; do not automatically retry the original mutation—ask the user |

If `status` is absent, treat that poll as in-progress and try once more. If it is absent across all 3 polls, surface the raw response and stop.

## List Org-Level Services

Do not merge these surfaces:

| Verb | Returns | Lifecycle status? |
|---|---|---|
| `organizations services list` | Provisioned org-level service instances | Yes: `Enabled`, `Disabled`, or `Deleted` (soft-deleted) |
| `organizations services list-available` | Catalog of service types available for org-level provisioning | No |

### Provisioned services

Run:

```bash
uip admin organizations services list --output json
```

Report under **"Provisioned services on `<ORG_NAME>`"**. For each row, show service type, **status** (`Enabled` / `Disabled` / `Deleted`), and region. Explicitly flag `Deleted` entries as removed but recoverable. If empty, say: *"No org-level services are currently provisioned."* Do not show an empty table.

Apply optional client-side filters after the API call:

```bash
uip admin organizations services list --status Enabled --output json
uip admin organizations services list --service orchestrator --output json
uip admin organizations services list --region "<REGION>" --output json
```

### Available service catalog

Run:

```bash
uip admin organizations services list-available --output json
```

Report under **"Available service catalog (org-level)"**. Do not add a status column: catalog entries have no lifecycle state. Visually separate this from provisioned services, preferably with a different table.

If the user asks to "show me the services" without distinguishing provisioned from available, run both commands and present two clearly labeled sections.