# Organization Management

Multi-step workflows for managing the caller's organization via `uip admin organizations`. For per-command flag tables, output codes, and single-command examples, see [organizations-commands.md](organizations-commands.md).

## Concept

The Organization Management Service (OMS) owns the org record, async lifecycle operations, the region catalog, and org-level service provisioning.

- **Async operations.** `create` and `delete` return an `operationId`. Poll via `organizations operation get <OPERATION_ID>` until terminal status before treating the change as done.
- **Soft-delete only.** No hard-delete flag. Reversible via support flow.
- **Login-tenant default** does NOT apply to org commands — they always operate on the caller's organization.

## Workflow: Inspect the Organization

The common read-side scenario — show the caller their org record.

### Compact view (just the org record)

```bash
uip admin organizations get --output json
```

Returns the organization name, id, region, country, language, lifecycle state, and timestamps.

### Bundled view (org + tenants + service catalog in one call)

```bash
uip admin organizations get --full --output json
```

Use `--full` when you need to answer a follow-up about tenants or services in the same response — it avoids the second round-trip to `tenants list` or `services list`.

### Discover provisioning regions for follow-up create commands

```bash
uip admin organizations regions list --output json
```

The returned region names go directly into `--region` on `organizations create` and `tenants create`.

## Workflow: Create a New Organization

1. Resolve target region:
   ```bash
   uip admin organizations regions list --output json
   ```
2. Resolve owner user UUID:
   ```bash
   uip admin users list --search "<OWNER_EMAIL>" --output json
   ```
3. Create inline (common fields):
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
   For advanced fields (`type`, `customProperties`, `isCreatorNonAdmin`), use `--file ./org.json` with the full `CreateOrganizationCommand` body instead.
4. Response includes `operationId`. Poll until done — see "Workflow: Poll an Async Operation".

## Workflow: Update the Organization

Two shapes:

- **Inline** for one or two simple fields (`--name`, `--logical-name`, `--language`).
- **File** for the full `UpdateOrganizationCommand` body when changing multiple structured fields.

See [organizations-commands.md — `organizations update`](organizations-commands.md#organizations-update).

## Workflow: Soft-Delete the Organization

Severe, organization-wide action — affects every tenant under the org.

1. Confirm with user explicitly.
2. Run `organizations delete`.
3. Capture `operationId` and poll until complete.

Restoration goes through the support flow (no CLI path).

## Workflow: Poll an Async Operation

Canonical poll endpoint for **all** OMS async operations — both `organizations` and `tenants`:

```bash
uip admin organizations operation get <OPERATION_ID> --output json
```

Repeat until the response indicates a terminal status. Show the user the current status between polls; do not loop silently.
