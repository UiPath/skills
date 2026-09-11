# Consumables Report

Report consumption of consumable license units (`AIU`, `AGU`, `RU`, `PLTU`, `HEAL`, `SPR`, `LU`, etc.) by organization account, day/service, or folder.

> Run `uip platform licenses consumables get --help` for full option details.

## Command and prerequisites

Run:

```bash
uip platform licenses consumables get [--mode <summary|daily|folders>] [flags] --output json
```

- Run `get`; `uip platform licenses consumables` alone prints group help.
- Use `summary`, `daily`, and `folders` only as `--mode` values, never as subcommands or positionals.
- Omit `--mode` for the default `summary`, or pass `--mode summary`.
- Run `uip login status`. If unauthenticated, ask the user to run `uip login` (interactive browser flow).
- Require organization-admin permission to read account product allocations.
- For `daily` and `folders`, obtain the exact target tenant name and consumable unit code.

Use these reports for tenant chargeback/cost allocation, bundle-renewal capacity planning, folder investigations, daily tenant/unit trends, and tenant-pool versus organization-pool comparisons.

## Modes

| Mode | Scope | Required flags | Output |
|---|---|---|---|
| `summary` (default) | All active consumables × all tenants, or one tenant with `--tenant` | None | One row per consumable × tenant, with allocation and pool-consumption columns |
| `daily` | One tenant × one unit, day by day | `--tenant`, `--unit`, `--start-date`, `--end-date` | One row per (date, service) |
| `folders` | One tenant × one unit, by folder | `--tenant`, `--unit`, `--start-date`, `--end-date` | One row per folder |

## Summary

Run:

```bash
uip platform licenses consumables get --output json
uip platform licenses consumables get --tenant "<TENANT_NAME>" --output json
uip platform licenses consumables get --start-date <ISO_START> --end-date <ISO_END> --output json
```

The default reports every active consumable. Without dates, each uses its own bundle window; a supplied date pair overrides every consumable's window.

Response fields are:

- `code` / `name`: product code and friendly name.
- `totalUnitsInAccount`: account purchase total.
- `allocated`: account-level allocation.
- `consumedFromOrgWithoutTenant`: consumption not attributable to a tenant; zero when `--tenant` is set.
- `startDate` / `endDate`: effective bundle window, or the override range.
- `tenantId` / `tenantName`: tenant breakdown.
- `consumedFromTenantPool`: consumption from the tenant's reserved allocation.
- `consumedFromOrgPool`: consumption from the remaining account pool (overflow).

Response shape:

```json
{
  "Result": "Success",
  "Code": "LicensesConsumablesSummary",
  "Data": [
    {
      "code": "<UNIT_CODE>",
      "name": "<UNIT_NAME>",
      "totalUnitsInAccount": 5000,
      "allocated": 1200,
      "consumedFromOrgWithoutTenant": 30,
      "startDate": "<START_DATE>",
      "endDate": "<END_DATE>",
      "tenantId": "<TENANT_ID>",
      "tenantName": "<TENANT_NAME>",
      "consumedFromTenantPool": 800,
      "consumedFromOrgPool": 150
    }
  ]
}
```

Row rules:

- Without `--tenant`, return one row per (consumable, tenant) when tenant consumption exists.
- Without `--tenant`, return one row for a consumable with no tenant consumption, using `tenantId: null`, `tenantName: ""`, and zeroed pool columns; `consumedFromOrgWithoutTenant` may be non-zero.
- With `--tenant`, return one row per consumable for that tenant, including zero-activity consumables with zeroed pool columns.

## Daily breakdown

Run the query as specified — pass the tenant name given by the user verbatim (e.g. `default`); if the CLI is not connected to a live tenant the command still runs and returns an auth/`Tenant not found` error, which is expected. Do not pre-check the tenant list and stop:

```bash
uip platform licenses consumables get \
  --mode daily \
  --tenant "default" \
  --unit AIU \
  --start-date 2026-04-01 \
  --end-date 2026-04-30 \
  --output json
```

Return `Result`, `Code: "LicensesConsumablesDaily"`, and `Data` rows containing:

```json
{
  "code": "AIU",
  "name": "AI Units",
  "tenantId": "296b7134-6691-43db-b48a-2d95ed3ab031",
  "tenantName": "default",
  "date": "2026-04-15",
  "service": "orchestrator",
  "consumedAmount": 24
}
```

Return one row per (date, service) in the range. `service` identifies the emitting service, such as `orchestrator`, `aicenter`, or `dataservice`.

## Folder breakdown

Run:

```bash
uip platform licenses consumables get \
  --mode folders --tenant "<TENANT_NAME>" --unit <UNIT_CODE> \
  --start-date <ISO_START> --end-date <ISO_END> --output json
```

Return `Result`, `Code: "LicensesConsumablesFolders"`, and `Data` rows containing:

```json
{
  "code": "<UNIT_CODE>",
  "name": "<UNIT_NAME>",
  "tenantId": "<TENANT_ID>",
  "tenantName": "<TENANT_NAME>",
  "folderKey": "<FOLDER_ID>",
  "folderName": "<FOLDER_NAME>",
  "parentFolderKey": null,
  "consumedBySelf": 42,
  "processCountSelf": 3
}
```

- `folderKey` / `folderName`: folder GUID and display name.
- `parentFolderKey`: parent GUID, or `null` at the root.
- `consumedBySelf`: consumption attributed only to this folder; descendants are excluded.
- `processCountSelf`: distinct contributing processes in this folder.
- The API returns non-recursive per-folder rows. Aggregate descendants client-side for rolled-up totals.

## Flags and dates

| Flag | Required in | Default | Notes |
|---|---|---|---|
| `--mode <summary\|daily\|folders>` | All modes | `summary` | Determines output shape |
| `--tenant <name>` | `daily`, `folders` | All tenants | Matched by exact tenant name |
| `--unit <code>` | `daily`, `folders` | All consumables | Case-insensitive product code (`AIU`, `aiu`, `Aiu` all match) |
| `--start-date <iso>` | `daily`, `folders` | Bundle window | ISO 8601, such as `2026-04-01` or `2026-04-01T00:00:00Z` |
| `--end-date <iso>` | `daily`, `folders` | Bundle window | ISO 8601; must be strictly after `--start-date` |

- Pass `--start-date` and `--end-date` together; passing only one is rejected.
- Both must be valid ISO 8601.
- `startDate >= endDate` is rejected.
- In `summary`, the pair overrides each consumable's bundle window.
- In `daily` and `folders`, the pair is required.

## Error conditions

| Error | Cause | Resolution |
|---|---|---|
| `Invalid --mode '<value>'.` | Mode is not `summary`, `daily`, or `folders` | Use an allowed value |
| `--mode daily requires: --tenant, --unit, --start-date, --end-date.` | Required flag missing | Pass all four flags |
| `--start-date and --end-date must be provided together.` | Only one date supplied | Pass both or omit both |
| `Invalid --start-date: '<value>'.` | Date is not ISO 8601 | Use `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` |
| `--start-date must be strictly before --end-date.` | Empty or inverted range | Provide a non-empty forward range |
| `Tenant '<name>' not found in the current organization.` | Exact tenant name not found | Check spelling with `uip login tenant list`; available tenants are listed in the error |
| `Unit '<code>' is not an active consumable in this organization.` | Code is not consumable or its bundle window is inactive | Choose an available code listed in the error |

## Gotchas

- `summary` reports every active consumable and can be heavy on large accounts; scope with `--tenant` or `--unit` when iterating.
- Without an override range, summary rows can have different bundle windows.
- With `--tenant`, `consumedFromOrgWithoutTenant` is zero; only `consumedFromTenantPool` and `consumedFromOrgPool` are populated.
- `consumedAmount` and `consumedBySelf` are point-in-time totals over the requested range, not running totals. Once the window closes, repeating the query returns the same value.
- `--unit` is case-insensitive, but other code references (`tenant licenses set`) are exact-case; do not carry the assumption over.
- There is no pagination. `daily` and `folders` return all rows in one response; use narrower ranges for very large windows or folder counts.
- `folders` is non-recursive: `consumedBySelf` excludes child folders. Reconstruct the tree for rolled-up totals.
- `PLTU` is dual-purpose: it appears in runtime allocation (`tenants licenses get`) and consumables reporting, which have different reporting axes.

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [Tenant Allocations](tenant-allocations.md) — set the allocations these reports consume from
- [User & Group Licenses](user-licenses-allocations.md) — user-bundle allocation (separate license type)
- [Full CLI command reference](../uip-commands.md)
