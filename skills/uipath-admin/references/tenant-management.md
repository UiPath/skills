# Tenant Management

Multi-step workflows for managing tenants and their services via `uip admin tenants`. For per-command flag tables, output codes, and single-command examples, see [tenants-commands.md](tenants-commands.md).

## Concept

A tenant lives inside an organization. Each tenant has its own lifecycle status (`Enabled`, `Disabled`, `Updating`, `Deleted`) and its own service provisioning surface.

> **Two `status` fields, don't confuse them.** Tenant *lifecycle* status (`Enabled` / `Disabled` / `Updating` / `Deleted`) lives on the tenant record. Async *operation* status (`Pending` / `Running` / `InProgress` / `Succeeded` / `Failed` / `Cancelled`) lives on the `operationId` response. The poll endpoint reports operation status; the tenant `status` only flips after the operation reaches `Succeeded`.

- **Tenant lifecycle is async.** `create`, `update`, `delete`, `enable`, `disable` all return an `operationId`. Auto-poll per the [shared Polling procedure](organization-management.md#polling-procedure-auto-poll-then-hand-off) (3 × 5 s, then ask the user). Every async workflow below assumes this procedure — `(poll)` in a step means "follow the shared procedure".
- **Service provisioning is synchronous.** `services add`, `enable`, `disable`, `remove` return immediately. No polling required.
- **Soft-delete only.** No hard-delete flag. Reversible via the restore flow.
- **Positional tenant id defaults to the login tenant.** Convenient for read ops; dangerous for destructive ops — always pass the explicit `<TENANT_ID>` for `delete`, `disable`, and `services remove`.

## Workflow: Resolve a Tenant UUID by Name

Standard pattern across `uip admin`:

```bash
uip admin tenants list --filter "<NAME>" --output json
```

Extract `id` from the result before calling `get`, `update`, `delete`, `enable`, `disable`, or `services` commands that take an explicit tenant id.

## Workflow: List Tenants — Surface Lifecycle Status

When showing tenants to the user, always include each tenant's `status` (`Enabled`, `Disabled`, `Updating`, or `Deleted`). A `Deleted` tenant is soft-deleted and still visible until purged — call this out so the user knows it is recoverable but not active.

```bash
uip admin tenants list --output json
uip admin tenants list --status Enabled --output json
```

For each row: tenant name, UUID (so the user can copy it into the next command), region, status. If the user asked "what tenants exist?" do not silently filter out `Disabled` or `Deleted` tenants — show all and label them.

## Workflow: List Tenant Services — Provisioned vs. Available

Two distinct surfaces — never merge them:

| Verb | Returns | Has lifecycle status? |
|---|---|---|
| `tenants services list` | **Provisioned** service instances on the tenant (what currently exists) | Yes — `Enabled`, `Disabled`, or `Deleted` (soft-deleted) |
| `tenants services list-available --region <R>` | **Catalog** of service types that *can* be provisioned in that region | No — catalog entries are not provisioned |

### Currently provisioned on a tenant (with status)

```bash
uip admin tenants services list --tenant-id <TENANT_ID> --output json
```

Surface to the user as **"Provisioned services on tenant `<TENANT_NAME>`"**. Per row: service type, **status** (`Enabled` / `Disabled` / `Deleted`), region. Flag any soft-deleted (`Deleted`) entries explicitly — they are removed but still recoverable.

If the result is empty, say so explicitly. Do not show an empty table.

Optional filters (client-side):

```bash
uip admin tenants services list --tenant-id <TENANT_ID> --service orchestrator --output json
uip admin tenants services list --tenant-id <TENANT_ID> --region "<REGION>" --output json
```

If `--tenant-id` is omitted, the CLI uses the **login tenant**. Always resolve and state which tenant the listing covers so the user is not guessing.

### Available to provision on a tenant (catalog only)

```bash
uip admin tenants services list-available --region "<REGION>" --output json
```

Surface to the user as **"Available service catalog for region `<REGION>`"**. Do NOT add a status column — catalog entries have no lifecycle state. The catalog is **region-aware**: a service can appear in one region's catalog and not another's.

### When the user's intent is ambiguous

If the user says "show services on this tenant" without specifying, run both `services list` and `services list-available --region <TENANT_REGION>` and present them in two clearly labeled sections.

## Before Mutating a Tenant or Tenant Service — Name the Target

Before any tenant lifecycle or tenant-service mutation, echo the resolved target back so the user knows exactly which resource will change:

| Mutation | Echo this |
|---|---|
| `tenants create` | `Organization: <ORG_NAME>` + `New tenant name: <NAME>` + `Region: <REGION>` |
| `tenants update / enable / disable / delete` | `Tenant: <TENANT_NAME> (<TENANT_UUID>)` + the action. If `<TENANT_ID>` was omitted and the CLI defaults to the login tenant, state: `Tenant: <LOGIN_TENANT_NAME> (login-tenant default)` and confirm with the user before any destructive verb. |
| `services add / enable / disable / remove` | `Tenant: <TENANT_NAME>` + `Service: <SERVICE_TYPE>` + (for `add`) `Region: <TENANT_REGION>`. For multi-service `--file` payloads, list every service. |

Resolve UUIDs to names — never leave a raw `tenantId` in the echo. `tenants get <TENANT_ID> --output json` gives you both name and region.

## Workflow: Create a Tenant

1. Confirm available regions:
   ```bash
   uip admin organizations regions list --output json
   ```
2. **Validate the tenant name client-side.** OMS rejects display names with `-`, `_`, spaces, or special chars — must start with a letter, be 2–32 chars, alphanumeric only. Reject hyphenated names before sending.
3. **Propose default services to provision.** Query the regional catalog, then filter to the default-provision set — services with `provisioningMode === "Implicit"` AND `isVisible === true` AND `isAlwaysProvision === false`. Services with `isAlwaysProvision === true` are auto-provisioned by the platform (don't list as a choice); `isVisible === false` are platform-internal (don't surface); `provisioningMode === "Explicit"` are optional opt-ins (offer separately on request).
   ```bash
   uip admin tenants services list-available --region "<REGION>" --output json \
     --output-filter "Data[?provisioningMode=='Implicit' && isVisible==\`true\` && isAlwaysProvision==\`false\`].{id:id,name:name}"
   ```
   Render this list to the user; let them remove any they don't want before submitting. Build the `services{}` map in the create body from the confirmed set.
4. Create from a file (recommended once a services list is involved):
   ```bash
   uip admin tenants create --file ./tenant.json --output json
   ```
   Where `./tenant.json` is a `CreateTenantRequestDto`:
   ```json
   {
     "name": "<TENANT_NAME>",
     "region": "<REGION>",
     "environment": "<ENV>",
     "services": { "orchestrator": true, "du": true, "actions": true, "automationhub": true, "processes": true, "taskmining": true }
   }
   ```
   For the bare no-services case use inline: `uip admin tenants create --name "<NAME>" --region "<REGION>" --environment "<ENV>"` (the platform still auto-provisions every `isAlwaysProvision === true` service).
5. Response includes both the new `id` and an `operationId`. `(poll)`

## Workflow: Update a Tenant

Two shapes:

- **Inline** for simple fields (`--name`, `--region`, `--environment`).
- **File** for `services{}`, `customProperties`, `color` — pass `--file ./tenant-patch.json` (TenantUpdateDto).

Response includes `operationId`. `(poll)`

## Workflow: Enable or Disable a Tenant

Tenant activation toggle. Both verbs are **async** — capture the `operationId`. `(poll)`

### Enable

```bash
uip admin tenants enable <TENANT_ID> --output json
```

Activates a `Disabled` tenant. Idempotent — calling on an already-`Enabled` tenant is a safe no-op.

### Disable

Disabling a tenant blocks all access to its services until re-enabled. **Confirm with the user before running.**

1. Resolve the tenant id explicitly. Do not rely on the login-tenant default for disable.
2. Confirm with user. State explicitly: *"This will block all access to tenant `<NAME>` until re-enabled."*
3. Disable, recording an audit reason:
   ```bash
   uip admin tenants disable <TENANT_ID> --reason "<FREE_TEXT_REASON>" --output json
   ```
4. Capture `operationId`. `(poll)`

`--reason` is optional but recommended — it lands in the audit trail.

## Workflow: Soft-Delete a Tenant

1. Resolve the tenant id explicitly. Do not rely on the login-tenant default.
2. Confirm with user.
3. Run `tenants delete <TENANT_ID>`.
4. Capture `operationId`. `(poll)` Reversible via the restore flow.

## Workflow: Add Tenant Services

Synchronous — no polling.

### Single service (inline)

```bash
uip admin tenants services add \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

### Multiple services (`--file`)

`add-services.json`:

```json
{ "services": { "orchestrator": true, "studio": true } }
```

All file entries must be `true` (use `services remove` for `false`).

```bash
uip admin tenants services add --tenant-id <TENANT_ID> --file ./add-services.json --output json
```

## After a Service Mutation — Verify Post-State

`services add / enable / disable / remove` return 200 OK / `Success` regardless of whether server-side state actually changed. After every mutation, re-list and confirm:

```bash
uip admin tenants services list --tenant-id <TENANT_ID> --output json
```

Or, when you need a single service's status, filter the tenant record:

```bash
uip admin tenants get <TENANT_ID> --output-filter "tenantServiceInstances[?serviceType=='<SVC>']" --output json
```

Surface the resulting `status` to the user. For `disable`, confirm the row now reads `Disabled`; for `remove`, confirm it reads `Disabled` / `Deleted` rather than disappearing silently. See [tenants-commands.md — Concepts](tenants-commands.md#concepts) for the list of services where `disable` / `remove` is a no-op despite the Success code.

## Workflow: Soft-Remove Tenant Services

Synchronous. Server-side soft-delete (no hard-delete option).

> **Pre-flight: prompt the user if the target service cannot actually be removed.** The CLI returns Success on every `services remove` call, but for a fixed set of services the server-side state never changes (`isAlwaysProvision === true` or otherwise platform-pinned). **Before sending the call, check the target list against this set and tell the user — do not silently submit a no-op.**
>
> **Cannot be removed (any call is a server-side no-op):**
> - Orchestrator (`orchestrator`)
> - Maestro (`maestro`)
> - Integration Service (`connections`)
> - Data Fabric (`dataservice`)
> - Insights (`insights`)
> - Test Manager (`testmanager`)
>
> If any of those appears in the user's request, render: *"Service `<X>` cannot be removed via the CLI — it's pinned by the platform. The call will return Success but the service will stay provisioned. To deprovision, revoke the org entitlement via the UiPath Portal. Continue anyway, or skip `<X>`?"* On "skip", drop it from the file/flag; on "continue anyway", run the call AND warn in the post-state summary that the verification will show the service still present.

### Single service

```bash
uip admin tenants services remove \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```

### Multiple services

`remove-services.json`:

```json
{ "services": { "orchestrator": false, "studio": false } }
```

All file entries must be `false`.

```bash
uip admin tenants services remove --tenant-id <TENANT_ID> --file ./remove-services.json --output json
```

## Workflow: Disable Tenant Services

Synchronous. **Pre-flight: prompt the user if the target service cannot actually be disabled.** Same pattern as `remove`: the CLI returns Success but the server-side `status` never flips.

> **Cannot be disabled (any call is a server-side no-op):**
> - Integration Service (`connections`)
> - Data Fabric (`dataservice`)
> - Insights (`insights`)
>
> If any of those appears in the user's request, render: *"Service `<X>` cannot be disabled via the CLI — it's pinned by the platform. The call will return Success but the service will stay `Enabled`. To deprovision, revoke the org entitlement via the UiPath Portal. Continue anyway, or skip `<X>`?"* On "skip", drop it; on "continue anyway", proceed and warn in the post-state summary.

```bash
uip admin tenants services disable \
  --tenant-id <TENANT_ID> \
  --service <SERVICE_TYPE> \
  --output json
```
