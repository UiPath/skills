# Tenant Management

Multi-step workflows for managing tenants and their services via `uip admin tenants`. For per-command flag tables, output codes, and single-command examples, see [tenants-commands.md](tenants-commands.md).

## Concept

A tenant lives inside an organization. Each tenant has its own lifecycle status (`Enabled`, `Disabled`, `Updating`, `Deleted`) and its own service provisioning surface.

- **Tenant lifecycle is async.** `create`, `update`, `delete`, `enable`, `disable` all return an `operationId`. Poll via [organizations-commands.md — `operation get`](organizations-commands.md#operation-get).
- **Service provisioning is synchronous.** `services add`, `enable`, `disable`, `remove` return immediately. No polling required.
- **Soft-delete only.** No hard-delete flag. Reversible via the restore flow.
- **Positional tenant id defaults to the login tenant.** Convenient for read ops; dangerous for destructive ops — always pass the explicit `<TENANT_ID>` for `delete`, `disable`, and `services remove`.

## Workflow: Resolve a Tenant UUID by Name

Standard pattern across `uip admin`:

```bash
uip admin tenants list --filter "<NAME>" --output json
```

Extract `id` from the result before calling `get`, `update`, `delete`, `enable`, `disable`, or `services` commands that take an explicit tenant id.

## Workflow: Create a Tenant

1. Confirm available regions:
   ```bash
   uip admin organizations regions list --output json
   ```
2. Create inline:
   ```bash
   uip admin tenants create \
     --name "<TENANT_NAME>" \
     --region "<REGION>" \
     --environment "<ENV>" \
     --output json
   ```
   For `services[]`, `customProperties`, `color`, `isDefaultTenant`, use `--file ./tenant.json` (CreateTenantRequestDto) instead.
3. Response includes both the new `id` and an `operationId`. Poll via [organizations-commands.md — `operation get`](organizations-commands.md#operation-get).

## Workflow: Update a Tenant

Two shapes:

- **Inline** for simple fields (`--name`, `--region`, `--environment`).
- **File** for `services{}`, `customProperties`, `color` — pass `--file ./tenant-patch.json` (TenantUpdateDto).

Response includes `operationId` — poll until done.

## Workflow: Enable or Disable a Tenant

Tenant activation toggle. Both verbs are **async** — capture the `operationId` and poll until terminal.

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
4. Capture `operationId` and poll until done via [organizations-commands.md — `operation get`](organizations-commands.md#operation-get).

`--reason` is optional but recommended — it lands in the audit trail.

## Workflow: Soft-Delete a Tenant

1. Resolve the tenant id explicitly. Do not rely on the login-tenant default.
2. Confirm with user.
3. Run `tenants delete <TENANT_ID>`.
4. Capture `operationId` and poll until done. Reversible via the restore flow.

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

## Workflow: Soft-Remove Tenant Services

Synchronous. Server-side soft-delete (no hard-delete option).

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
